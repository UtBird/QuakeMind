"""J-30 / Tablo 18: modelin kapanmalariyla PLANLA, EMSR648'in gercek kapanmalarinda YURU.

Onceki model kosularinda (full_scenario --closure-source model) klasik ekip de
modelin kapanmalarini "gercek" sayiyordu; modelin hatalari hic olculmuyordu.
Burada dunya -- gercekten kapali kenarlar -- her zaman EMSR648 Grading hasarli
yol cizgilerinden cikarilan kumedir (closures_from_lines, kural + tampon).
Ayni dunyada uc ekip turu yurur; hepsi kapali kenara girmez, kapanmayi kavsakta
ogrenir ve kesif basina t_u oder (Algoritma 1):

  R3 -- kusursuz bilgi: yola dunyanin kapanmalarini bilerek cikar (kesif yok).
  M  -- model bilgili QuakeMind: yola SegFormer'in kapanmalarini bilerek cikar.
        Yanlis alarmlari hic sorgulamaz (o yollara girmez); modelin kacirdigi
        gercek kapanmaya varinca kesfeder. Yanlis alarmlar hedefi baglantisiz
        birakirsa ("rota bulunamadi") modeli birakip R0 gibi devam eder
        (sayisi "model rota bulamadi" sutununda).
        Ayrica yumusak kullanim (MODES): kenar silinmez, planlamada uzunlugu
        x3 / x10 pahalilasir -- ag hic kopmaz.
  R0 -- klasik: yola hicbir bilgiyle cikmaz.

Model kapanmalari canli /analyze ve /closures_from_mask ile ayni kuralla
(dilate_mask_by_metres + _classify_edges) hazir maskelerden uretilir:
benchmark/data/model_masks/<sahne>-z<zoom>/. Gorevler (ekip baslangici,
afetzede konumu) runs/multi_seed/drone-emsr-loose-s<tohum>-<il> kosularindan
alinir -- afetzedeler EMSR dunyasinda ulasilabilir secilmistir. 10 tohum.

Backend gerektirmez; graf, EMSR paketi ve maskeler dosyadan okunur.

    python benchmark/model_in_real_world.py
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

BENCH = Path(__file__).resolve().parent
BACKEND = BENCH.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BENCH))

from apps.road_damage.utils.network import (  # noqa: E402
    closures_from_damage_mask, closures_from_lines, fetch_osm_road_graph, simulate_reference_fleet,
)
from benchmark.copernicus_ground_truth import aoi_rings, damaged_road_lines  # noqa: E402
from naive_baseline import AVERAGE_SPEED_KMH, U_TURN_PENALTY_MIN  # noqa: E402
import scenario_dataset_drone as DS  # noqa: E402

RUNS = BENCH / "runs"
SOURCE_SWEEP = RUNS / "multi_seed"
OUT_DIR = RUNS / "model_gercek_dunya"
MODEL_MASK_ROOT = BENCH / "data" / "model_masks"

SEEDS = list(range(42, 52))
ZOOMS = [18, 19, 20]
RADII_M = [0.0, 5.0, 10.0, 15.0, 25.0]
EMSR_RULE = "loose"
EMSR_BUFFER_M = 8.0
T_U_SWEEP = [0.0, 5.0, 10.0, 20.0, 30.0]
# Modelin kapanmalari nasil kullanilir: "sert" = kenar silinir (bugunku sistem);
# yumusak = kenar kalir, planlamada uzunlugu carpanla pahalilasir (makale Denklem 8;
# 3 = Denklem 9'un en yuksek carpani). Yumusak kullanimda ag hic kopmaz.
MODES = {"": None, "-y3": 3.0, "-y10": 10.0}
CITY_OF = {z["id"]: z["city"] for z in DS.ZONES}


def load_mask(mask_id: str):
    """fastapi_app._load_model_mask ile ayni okuma (HTTP'siz)."""
    d = MODEL_MASK_ROOT / mask_id
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    damage = (np.array(Image.open(d / "damage_mask.png").convert("L")) > 0).astype(np.uint8)
    valid = None
    if (d / "valid_mask.png").exists():
        valid = (np.array(Image.open(d / "valid_mask.png").convert("L")) > 0).astype(np.uint8)
    if (damage.shape[1], damage.shape[0]) != (meta.get("width"), meta.get("height")):
        raise ValueError(f"{mask_id}: maske boyutu meta.json ile uyusmuyor")
    return meta, damage, valid


def physical(keys) -> set:
    """Yonlu kenar anahtari -> fiziksel yol kesimi (iki yon tek kesim)."""
    return {(min(u, v), max(u, v), k) for (u, v, k) in keys}


def both_directions(keys) -> set:
    out = set()
    for (u, v, k) in keys:
        out.add((u, v, k))
        out.add((v, u, k))
    return out


def confusion(model_keys, world_keys, all_keys) -> dict:
    m, e, n = physical(model_keys), physical(world_keys), physical(all_keys)
    tp, fp, fn = len(m & e), len(m - e), len(e - m)
    return {"segments": len(n), "modelClosed": len(m), "worldClosed": len(e),
            "tp": tp, "fp": fp, "fn": fn, "tn": len(n) - tp - fp - fn}


def rates(c: dict) -> dict:
    tp, fp, fn = c["tp"], c["fp"], c["fn"]
    return {
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "iou": tp / (tp + fp + fn) if tp + fp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None,
    }


def travel_min(d: float) -> float:
    return d / 1000.0 / AVERAGE_SPEED_KMH * 60.0


def task_time(r: dict, tu: float) -> float:
    # compute_comparison ile ayni yuvarlama (gorev basina 0,1 dk)
    return round(travel_min(r["distanceMeters"]) + r["discoveries"] * tu, 1)


def describe(values: list) -> dict | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    n = len(vals)
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
    return {"n": n, "mean": mean, "sd": sd, "min": min(vals), "max": max(vals)}


def variant_names() -> list[str]:
    return (["R3"] + [f"M-z{z}-r{int(r)}{m}" for m in MODES for z in ZOOMS for r in RADII_M]
            + ["R0"])


def split_variant(name: str) -> tuple[str, float | None]:
    """'M-z19-r15-y3' -> ('M-z19-r15', 3.0)"""
    for suffix, factor in MODES.items():
        if suffix and name.endswith(suffix):
            return name[: -len(suffix)], factor
    return name, None


def prepare_zone(zone: dict) -> dict:
    """Sahne grafi, EMSR dunyasi ve tum model kapanma kumeleri (tohumdan bagimsiz)."""
    bbox = tuple(zone["bbox"])
    G, err = fetch_osm_road_graph(bbox, network_type="walk")
    if G is None:
        raise RuntimeError(f"{zone['id']}: graf yok ({err})")
    lines = damaged_road_lines(zone["emsrPackage"], EMSR_RULE, bbox)
    _, _, world_keys, wstats = closures_from_lines(
        G, lines, buffer_m=EMSR_BUFFER_M, min_overlap=0.5, observed_polygons=aoi_rings(zone["emsrPackage"]))
    all_keys = set(G.edges(keys=True))
    models = {}
    for zoom in ZOOMS:
        meta, damage, valid = load_mask(f"{zone['id']}-z{zoom}")
        mb = meta["bounds"]
        bounds = (mb["west"], mb["south"], mb["east"], mb["north"])
        for r in RADII_M:
            _, _, keys, coverage = closures_from_damage_mask(G, bounds, damage, valid, r)
            c = confusion(keys, world_keys, all_keys)
            models[f"M-z{zoom}-r{int(r)}"] = {
                "keys": set(keys), "zoom": zoom, "radiusM": r, "directedClosed": len(keys),
                "edgesObservedFraction": (coverage or {}).get("edgesObservedFraction"),
                "confusion": c, **rates(c),
            }
    return {"zone": zone, "G": G, "worldKeys": set(world_keys), "worldStats": wstats,
            "allKeys": all_keys, "models": models}


def zone_tasks(seed: int, zone_id: str) -> tuple[list, list]:
    city = CITY_OF[zone_id]
    s = json.loads((SOURCE_SWEEP / f"drone-emsr-loose-s{seed}-{city}" / "summary.json").read_text(encoding="utf-8"))
    z = next(z for z in s["zones"] if z["zoneId"] == zone_id)
    teams = {t["id"]: t for t in z["teams"]}
    victims = {v["id"]: v for v in z["victims"]}
    tasks, runrefs = [], []
    for a in z["assignments"]:
        if a.get("distanceMeters") is None:
            continue
        t, v = teams[a["teamId"]], victims[a["victimId"]]
        tasks.append({"id": a["victimId"], "startLat": t["startLat"], "startLon": t["startLon"],
                      "endLat": v["lat"], "endLon": v["lon"]})
        runrefs.append({"closedEdgeCount": z["closedEdgeCount"], "distanceMeters": a["distanceMeters"],
                        "naiveReachable": a["naiveReachable"], "naiveDistanceMeters": a["naiveDistanceMeters"],
                        "naiveDiscoveries": a["naiveDiscoveries"]})
    return tasks, runrefs


def model_run_counts() -> dict:
    """Onceki model kosularinin kapanma sayilari (ayni kural -> ayni sayi olmali)."""
    out = {}
    for name, key in (("drone-model-z18-r0", "M-z18-r0"), ("drone-model-z19-r15", "M-z19-r15")):
        for city in ("hatay", "kahramanmaras"):
            p = SOURCE_SWEEP / f"{name}-s42-{city}" / "summary.json"
            if p.exists():
                s = json.loads(p.read_text(encoding="utf-8"))
                for z in s["zones"]:
                    out[(z["zoneId"], key)] = z["closedEdgeCount"]
    return out


def run() -> dict:
    t0 = time.perf_counter()
    names = variant_names()
    prepared = {z["id"]: prepare_zone(z) for z in DS.ZONES}
    print(f"sahneler hazir ({time.perf_counter() - t0:.1f} sn)", flush=True)

    checks = {"worldCountMismatch": [], "modelCountMismatch": [], "r0Checked": 0, "r0Mismatch": [],
              "r3MaxAbsDiffM": 0.0, "r3Checked": 0}
    prior_counts = model_run_counts()
    for zid, p in prepared.items():
        for (pz, key), n in prior_counts.items():
            if pz == zid and p["models"][key]["directedClosed"] != n:
                checks["modelCountMismatch"].append({"zone": zid, "variant": key,
                                                     "here": p["models"][key]["directedClosed"], "run": n})

    per_seed = []   # {seed, zone, variant, tasks: [...]}
    for seed in SEEDS:
        for zid, p in prepared.items():
            tasks, runrefs = zone_tasks(seed, zid)
            if not tasks:
                continue
            if runrefs[0]["closedEdgeCount"] != len(p["worldKeys"]):
                checks["worldCountMismatch"].append({"seed": seed, "zone": zid, "here": len(p["worldKeys"]),
                                                     "run": runrefs[0]["closedEdgeCount"]})
            world = both_directions(p["worldKeys"])
            for name in names:
                if name == "R0":
                    res = simulate_reference_fleet(p["G"], world, tasks, speed_kmh=AVERAGE_SPEED_KMH)
                    for r, ref in zip(res, runrefs):
                        checks["r0Checked"] += 1
                        got = (r is not None, r and r["distanceMeters"], r and r["discoveries"])
                        exp = (ref["naiveReachable"], ref["naiveDistanceMeters"], ref["naiveDiscoveries"])
                        if got != exp:
                            checks["r0Mismatch"].append({"seed": seed, "zone": zid, "got": got, "run": exp})
                elif name == "R3":
                    res = simulate_reference_fleet(p["G"], world, tasks, speed_kmh=AVERAGE_SPEED_KMH,
                                                   prior_closed=p["worldKeys"])
                    for r, ref in zip(res, runrefs):
                        if r is not None:
                            checks["r3Checked"] += 1
                            checks["r3MaxAbsDiffM"] = max(checks["r3MaxAbsDiffM"],
                                                          abs(r["distanceMeters"] - ref["distanceMeters"]))
                else:
                    base, factor = split_variant(name)
                    res = simulate_reference_fleet(p["G"], world, tasks, speed_kmh=AVERAGE_SPEED_KMH,
                                                   prior_closed=p["models"][base]["keys"],
                                                   prior_penalty_factor=factor)
                per_seed.append({"seed": seed, "zone": zid, "variant": name,
                                 "tasks": [dict(r, id=t["id"]) if r else {"id": t["id"], "unreachable": True}
                                           for t, r in zip(tasks, res)]})
    print(f"simulasyon bitti ({time.perf_counter() - t0:.1f} sn)", flush=True)
    return {"prepared": prepared, "perSeed": per_seed, "checks": checks, "names": names,
            "elapsedSec": round(time.perf_counter() - t0, 1)}


def summarize(res: dict) -> dict:
    names, prepared, per_seed = res["names"], res["prepared"], res["perSeed"]
    zones = list(prepared)
    real_zone = [z for z in zones if prepared[z]["worldKeys"]]

    def collect(name, zone_filter=None):
        by_seed = {}
        for row in per_seed:
            if row["variant"] != name or (zone_filter and row["zone"] not in zone_filter):
                continue
            by_seed.setdefault(row["seed"], []).extend(row["tasks"])
        return by_seed

    def stats(name, zone_filter=None):
        by_seed = collect(name, zone_filter)
        mean_time = {tu: [] for tu in T_U_SWEEP}
        disc, fallbacks, unreach, travel = [], [], [], []
        for seed in sorted(by_seed):
            ts = by_seed[seed]
            ok = [t for t in ts if not t.get("unreachable")]
            for tu in T_U_SWEEP:
                mean_time[tu].append(sum(task_time(t, tu) for t in ok) / len(ok) if ok else None)
            travel.append(sum(round(travel_min(t["distanceMeters"]), 1) for t in ok) / len(ok) if ok else None)
            disc.append(sum(t["discoveries"] for t in ok))
            fallbacks.append(sum(1 for t in ok if t.get("fallback")))
            unreach.append(sum(1 for t in ts if t.get("unreachable")))
        return {
            "tasksPerSeed": describe([len(v) for v in by_seed.values()]),
            "meanTimeMin": describe(mean_time[U_TURN_PENALTY_MIN]),
            "meanTimeByTu": {f"{tu:g}": describe(mean_time[tu]) for tu in T_U_SWEEP},
            "meanTravelMin": describe(travel),
            "discoveries": describe(disc),
            "modelFallbacks": describe(fallbacks),
            "unreachable": describe(unreach),
            "_meanTimeSeries": mean_time[U_TURN_PENALTY_MIN],
        }

    out = {"variants": {}, "zones": {}}
    for name in names:
        entry = {"all": stats(name), "realDamageZones": stats(name, real_zone),
                 "noRealDamageZones": stats(name, [z for z in zones if z not in real_zone])}
        if name.startswith("M-"):
            base, factor = split_variant(name)
            entry["mode"] = "sert" if factor is None else f"yumusak x{factor:g}"
            entry["penaltyFactor"] = factor
            tot = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "segments": 0, "modelClosed": 0, "worldClosed": 0}
            for z in zones:
                c = prepared[z]["models"][base]["confusion"]
                for k in tot:
                    tot[k] += c[k]
            entry["confusion"] = tot
            entry.update(rates(tot))
            entry["zoom"] = prepared[zones[0]]["models"][base]["zoom"]
            entry["radiusM"] = prepared[zones[0]]["models"][base]["radiusM"]
            entry["perZone"] = {z: {k: prepared[z]["models"][base][k]
                                    for k in ("directedClosed", "edgesObservedFraction", "confusion",
                                              "precision", "recall", "iou", "f1")} for z in zones}
        out["variants"][name] = entry
    # kazanc payi: (R0 - M) / (R0 - R3), tohum basina
    r0 = out["variants"]["R0"]["all"]["_meanTimeSeries"]
    r3 = out["variants"]["R3"]["all"]["_meanTimeSeries"]
    for name in names:
        m = out["variants"][name]["all"]["_meanTimeSeries"]
        out["variants"][name]["captureOfR0toR3Gain"] = describe([
            (a - b) / (a - c) if a is not None and b is not None and c is not None and a - c > 1e-9 else None
            for a, b, c in zip(r0, m, r3)])
        out["variants"][name]["extraVsR3Min"] = describe([
            b - c if b is not None and c is not None else None for b, c in zip(m, r3)])
    for z in zones:
        p = prepared[z]
        out["zones"][z] = {"segments": len(physical(p["allKeys"])),
                           "worldClosedSegments": len(physical(p["worldKeys"])),
                           "worldDirectedClosed": len(p["worldKeys"]),
                           "edgesInsideEmsrAoiFraction": p["worldStats"].get("edgesInsideObservedFraction")}
    for name in names:
        for part in ("all", "realDamageZones", "noRealDamageZones"):
            out["variants"][name][part].pop("_meanTimeSeries", None)
    return out


def tr(x, d=1):
    if x is None:
        return "—"
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def pm(s, d=1):
    return "—" if not s else f"{tr(s['mean'], d)} ± {tr(s['sd'], d)}"


def label(name: str, v: dict) -> str:
    if name == "R3":
        return "R3 — kusursuz bilgi (EMSR648)"
    if name == "R0":
        return "R0 — naif ajan"
    tag = " (uygulamanın kuralı)" if v["zoom"] == 18 and v["radiusM"] == 0 and v["penaltyFactor"] is None else ""
    mode = "" if v["penaltyFactor"] is None else f", yumuşak ×{tr(v['penaltyFactor'], 0)}"
    return f"SegFormer, z{v['zoom']}, r_h = {tr(v['radiusM'], 0)} m{mode}{tag}"


def write_markdown(summary: dict, checks: dict, path: Path) -> None:
    V, Z = summary["variants"], summary["zones"]
    L = ["# Model bilgili planlama, gerçek (EMSR648) dünyada yürüyüş — J-30 / Tablo 18\n"]
    L.append(f"Dünya: EMSR648 {EMSR_RULE} kuralı, tampon {tr(EMSR_BUFFER_M, 0)} m. Sahneler: "
             + ", ".join(f"{z} ({Z[z]['worldClosedSegments']}/{Z[z]['segments']} kesim gerçekte kapalı)" for z in Z)
             + f". Görevler: drone-emsr-loose koşularının atamaları, tohum {SEEDS[0]}–{SEEDS[-1]}. "
             f"v_ort = {tr(AVERAGE_SPEED_KMH)} km/sa, t_u = {tr(U_TURN_PENALTY_MIN, 0)} dk. "
             "Süreler görev başına ortalamanın tohumlar üzerinden ortalama ± ss'sidir. "
             "Üretici: `benchmark/model_in_real_world.py` (backend gerektirmez).\n")
    L.append("**Okuma.** Hücrelerdeki IoU / duyarlılık / kesinlik, piksel IoU_hasar DEĞİL; modelin kapattığı "
             "yol kesimleriyle EMSR648'in kapattığı kesimlerin **kesim düzeyinde** örtüşmesidir (üç sahne "
             "toplamı). \"Kaçırılan\" = gerçekte kapalı olup modelin açık bıraktığı kesim; \"yanlış\" = modelin "
             "kapattığı ama gerçekte açık kesim. \"Model rota bulamadı\" = yanlış alarmlar hedefi bağlantısız "
             "bıraktı, ekip modeli bırakıp klasik devam etti (süre bu davranışla hesaplandı). Yalnız SegFormer "
             "maskesi var; diğer beş model eğitilmedi.\n")
    L.append("## Tablo 18 (drone sahneleri, 10 tohum)\n")
    L.append("| Kapanma kümesi kaynağı | IoU (kesim) | Duyarlılık | Kesinlik | Kaçırılan kapanma (kesim) | Yanlış kapanma (kesim) | Ortalama ulaşım süresi (dk) | Model rota bulamadı (görev / tohum) | Keşif sayısı (tohum başına) | R0→R3 kazancının yakalanan payı |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")

    def is_soft(v):
        return v.get("penaltyFactor") is not None

    for name, v in V.items():
        if is_soft(v):
            continue
        a = v["all"]
        cap = v["captureOfR0toR3Gain"]
        cap_s = "—" if not cap else f"%{tr(100 * cap['mean'], 0)} ± {tr(100 * cap['sd'], 0)}"
        if name.startswith("M-"):
            c = v["confusion"]
            L.append(f"| {label(name, v)} | {tr(v['iou'], 3)} | {tr(v['recall'], 3)} | {tr(v['precision'], 3)} | "
                     f"{c['fn']} | {c['fp']} | {pm(a['meanTimeMin'], 2)} | {pm(a['modelFallbacks'])} | "
                     f"{pm(a['discoveries'])} | {cap_s} |")
        elif name == "R3":
            L.append(f"| {label(name, v)} | — | — | — | 0 | 0 | {pm(a['meanTimeMin'], 2)} | 0 | "
                     f"{pm(a['discoveries'])} | %100 |")
        else:
            total_world = sum(z["worldClosedSegments"] for z in Z.values())
            L.append(f"| {label(name, v)} | — | 0,000 | — | {total_world} (tümü) | 0 | {pm(a['meanTimeMin'], 2)} | "
                     f"0 | {pm(a['discoveries'])} | %0 |")

    L.append("\n## Modelin kapanmalarını yumuşak ceza olarak kullanmak (duyarlılık)\n")
    L.append("Bugünkü sistem modelin kapattığı kenarı çizgeden siler (yukarıdaki tablo). Burada kenar "
             "silinmez; planlamada uzunluğu ×3 (Denklem 9'un en yüksek çarpanı) ya da ×10 pahalılaşır, "
             "böylece yanlış alarm ağı koparamaz. Dünya ve görevler aynı.\n")
    L.append("| Kaynak | Ortalama ulaşım süresi (dk) | K-D1 süre (dk) | H-D1+H-D2 süre (dk) | Keşif sayısı (tohum başına) | R0→R3 kazancının yakalanan payı |")
    L.append("|---|---|---|---|---|---|")
    for name, v in V.items():
        if not (is_soft(v) or name in ("R3", "R0")):
            continue
        cap = v["captureOfR0toR3Gain"]
        cap_s = "—" if not cap else f"%{tr(100 * cap['mean'], 0)} ± {tr(100 * cap['sd'], 0)}"
        L.append(f"| {label(name, v)} | {pm(v['all']['meanTimeMin'], 2)} | "
                 f"{pm(v['realDamageZones']['meanTimeMin'], 2)} | {pm(v['noRealDamageZones']['meanTimeMin'], 2)} | "
                 f"{pm(v['all']['discoveries'])} | {cap_s} |")

    L.append("\n## Gerçek hasarlı sahne (K-D1) ve hasarsız sahneler (H-D1, H-D2) ayrı\n")
    L.append("H-D1 ve H-D2'de EMSR648 hiç yol hasarı işaretlememiş: orada modelin her kapanması yanlış alarmdır "
             "ve maliyeti yalnız dolanmadır. K-D1'de hem kaçırma hem yanlış alarm vardır.\n")
    L.append("| Kaynak | K-D1: süre (dk) | K-D1: keşif | K-D1: kesinlik / duyarlılık | H-D1+H-D2: süre (dk) | H-D1+H-D2: yanlış kapanma (kesim) | H-D1+H-D2: model rota bulamadı |")
    L.append("|---|---|---|---|---|---|---|")
    for name, v in V.items():
        if is_soft(v):
            continue
        r, n = v["realDamageZones"], v["noRealDamageZones"]
        if name.startswith("M-"):
            pz = v["perZone"]
            real = [z for z in pz if Z[z]["worldClosedSegments"]]
            none = [z for z in pz if not Z[z]["worldClosedSegments"]]
            pr = " / ".join(f"{tr(pz[z]['precision'], 2)} / {tr(pz[z]['recall'], 2)}" for z in real)
            fp_none = sum(pz[z]["confusion"]["fp"] for z in none)
        else:
            pr, fp_none = "—", 0
        L.append(f"| {label(name, v)} | {pm(r['meanTimeMin'], 2)} | {pm(r['discoveries'])} | {pr} | "
                 f"{pm(n['meanTimeMin'], 2)} | {fp_none} | {pm(n['modelFallbacks'])} |")

    L.append("\n## t_u duyarlılığı (görev başına ortalama süre, dk)\n")
    keys = [f"{tu:g}" for tu in T_U_SWEEP]
    L.append("| Kaynak | " + " | ".join(f"t_u = {k} dk" for k in keys) + " |")
    L.append("|---|" + "---|" * len(keys))
    for name, v in V.items():
        if is_soft(v):
            continue
        L.append(f"| {label(name, v)} | " + " | ".join(pm(v['all']['meanTimeByTu'][k], 2) for k in keys) + " |")

    L.append("\n## Doğrulama\n")
    L.append(f"- R0 (yeni simülatör) = önceki koşunun naive_compare sonucu: "
             f"{checks['r0Checked'] - len(checks['r0Mismatch'])} / {checks['r0Checked']} görev birebir.")
    L.append(f"- R3 mesafesi = önceki koşunun QuakeMind rotası (A*): {checks['r3Checked']} görev, en büyük fark "
             f"{tr(checks['r3MaxAbsDiffM'], 2)} m.")
    L.append(f"- EMSR dünyası kapanma sayısı koşularla uyuşmayan: {len(checks['worldCountMismatch'])}; "
             f"model kapanma sayısı (z18 r0, z19 r15) koşularla uyuşmayan: {len(checks['modelCountMismatch'])}.")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    res = run()
    summary = summarize(res)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "design": {"world": f"EMSR648 {EMSR_RULE}, tampon {EMSR_BUFFER_M} m", "seeds": SEEDS,
                   "zooms": ZOOMS, "radiiM": RADII_M, "tuSweep": T_U_SWEEP,
                   "speedKmh": AVERAGE_SPEED_KMH, "uTurnPenaltyMin": U_TURN_PENALTY_MIN,
                   "taskSource": "runs/multi_seed/drone-emsr-loose-s<tohum>-<il>"},
        "checks": res["checks"], "elapsedSec": res["elapsedSec"], **summary,
        "perSeed": res["perSeed"],
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(summary, res["checks"], OUT_DIR / "tablo18.md")
    c = res["checks"]
    print(f"R0 birebir: {c['r0Checked'] - len(c['r0Mismatch'])}/{c['r0Checked']} | R3 en buyuk fark "
          f"{c['r3MaxAbsDiffM']:.2f} m | kapanma sayisi uyusmazligi: dunya {len(c['worldCountMismatch'])}, "
          f"model {len(c['modelCountMismatch'])}")
    print(f"{'kaynak':14} {'IoU':>6} {'duyar.':>6} {'kesin.':>6} {'sure dk':>13} {'kesif':>9} {'rota yok':>9} {'pay':>6}")
    for name, v in summary["variants"].items():
        a = v["all"]
        f = lambda s, d=2: f"{s['mean']:.{d}f}±{s['sd']:.{d}f}" if s else "-"  # noqa: E731
        cap = v["captureOfR0toR3Gain"]
        print(f"{name:14} {('%.3f' % v['iou']) if v.get('iou') is not None else '-':>6} "
              f"{('%.3f' % v['recall']) if v.get('recall') is not None else '-':>6} "
              f"{('%.3f' % v['precision']) if v.get('precision') is not None else '-':>6} "
              f"{f(a['meanTimeMin']):>13} {f(a['discoveries'], 1):>9} {f(a['modelFallbacks'], 1):>9} "
              f"{(str(round(100 * cap['mean'])) + '%') if cap else '-':>6}")
    print(f"-> {OUT_DIR / 'tablo18.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
