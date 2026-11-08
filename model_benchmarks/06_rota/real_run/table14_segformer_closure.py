# -*- coding: utf-8 -*-
"""
Tablo 14: EMSR648 kesim-duzeyi (cut-level) degerlendirme -- COKLU MIMARI.

Kullanim (5 mimarinin tamami icin, checkpoint indirildikce):
    python table14_segformer_closure.py --label segformer --arch Segformer --encoder mit_b4 \
        --checkpoint .../optimized_mitb4_focal_dice30.pth   # varsayilan, arguman gerekmez
    python table14_segformer_closure.py --label unet --arch Unet --encoder mit_b4 \
        --checkpoint .../unet_mitb4.pth   # Kaggle furkanemrence/quakemind-modeller
    python table14_segformer_closure.py --label fpn --arch FPN --encoder mit_b4 \
        --checkpoint .../fpn_mitb4.pth    # ayni veri seti
    python table14_segformer_closure.py --label deeplabv3p --arch DeepLabV3Plus --encoder resnet101 \
        --checkpoint .../deeplabv3plus_resnet101.pth   # ayni veri seti
    python table14_segformer_closure.py --label linknet --arch Linknet --encoder resnet34 \
        --checkpoint .../linknet_r34_s42.pth
    python table14_segformer_closure.py --label pspnet --arch PSPNet --encoder resnet34 \
        --checkpoint .../pspnet_r34_s42.pth

Her calistirma kendi sonucunu results/table14_closure_{label}.json'a yazar (mevcut
segformer sonucu table14_segformer_closure.json adinda ayrica korunur, uzeirne
yazilmaz). Ayni sahneler/orneklem/tau taramasi/olcut tanimi TUM mimariler icin
birebir aynidir (bkz. asagidaki sabitler) -- yalniz model ve checkpoint degisir.

Varsayilan (arguman verilmezse): SegFormer MiT-B4, uretimde aktif checkpoint.
Zemin gercegi: emsr648_closures.closed_osm_edges (katı/orta/gevsek, M-76
esleme kurali -- degistirilmedi).
Bolgeler: scenario.DISTRICTS["H-Z1"] (Antakya, AOI11) ve ["K-Z1"]
(Onikisubat, AOI04) -- Sekil 9'da kullanilan, EMSR648 kapsamindaki ayni
bolgeler; metodolojik tutarlilik icin secildi (bkz. scenario.py DISTRICTS
yorumu, "H-Z1, H-Z3, K-Z1, K-Z2" EMSR648 kesisimi).

Her bolgede, ox.geocode ile bulunan merkezden sabit tohumla N adet ~800m
capinda ornek nokta uretilir (scenario.py'nin "seffaf, tekrarlanabilir"
felsefesiyle ayni ruhta -- elle secilmis nokta yok). Her ornekte:
  1. fetch_satellite_area (Esri Wayback, id=57965, 2023-02-23, +17 gun) -> goruntu
  2. get_osm_roads_overpass -> yol maskesi
  3. run_inference -> boosted_probs (surekli olasilik rasteri, esik uygulanmamis --
     run_inference'in dahili threshold/postprocess parametreleri boosted_probs'u
     ETKILEMEZ, o yuzden tau'yu sweep etmek icin cikarimi tekrar tekrar
     calistirmaya gerek yok)
  4. ox.graph_from_bbox -> G (4 deneme + 10sn bekleme, _j22_calibration.py'deki
     dogru bbox sirasiyla: west, south, east, north)

Tum orneklerin kenarlari BIRLESTIRILIP tau basina TEK confusion matrix'e
toplanir (DP/YN/YP/DN), boylece n buyur ve J-22'nin "tek orneklemle ayirt
edilemez" sorunu kismen azalir.
"""
import sys
import time
import json
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import cv2
import osmnx as ox
import geopandas as gpd
from shapely.geometry import LineString

from apps.road_damage.utils.fetcher import fetch_satellite_area, get_osm_roads_overpass
from apps.road_damage.utils.inference import load_simple_model, run_inference
from emsr648_closures import closed_osm_edges, _sample_points, METRIC_CRS
from scenario import DISTRICTS

WAYBACK_ID = "57965"  # 2023-02-23, deprem sonrasi +17 gun -- J-22 ile ayni
MODEL_PATH = REPO / "backend" / "apps" / "road_damage" / "models" / "optimized_mitb4_focal_dice30.pth"

RADIUS_M = 400.0  # -> ~800m x 800m karo (J-22 ile ayni)
N_SAMPLES_PER_DISTRICT = 4
OFFSET_M = 600.0
TAU_SWEEP = [round(float(x), 2) for x in np.arange(0.10, 0.61, 0.05)]
RULES = ("strict", "medium", "loose")
REGIONS = [("H-Z1", "AOI11"), ("K-Z1", "AOI04")]


ROADMASK_CACHE = Path(__file__).resolve().parent / "cache" / "table14_roadmask"


def cached_road_mask(bounds, w, h):
    """get_osm_roads_overpass sonucu (thickness=6) diske onbelleklenir; bos maske
    (Overpass erisilemedi) ONBELLEGE YAZILMAZ. Tum mimariler ayni maskeyi kullanir."""
    key = zlib.crc32(repr((tuple(round(float(b), 7) for b in bounds), int(w), int(h))).encode())
    f = ROADMASK_CACHE / f"{key:08x}.npy"
    if f.exists():
        return np.load(f)
    mask = get_osm_roads_overpass(bounds, w, h, thickness=6)
    if mask.mean() > 0:
        ROADMASK_CACHE.mkdir(parents=True, exist_ok=True)
        np.save(f, mask)
    return mask


def bbox_from_point(lat, lon, radius_m):
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * np.cos(np.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)  # west, south, east, north


def sample_points_around(center_lat, center_lon, n, offset_m, seed):
    """Merkezden sabit tohumla n nokta (rastgele aci + 0.3-1.0 x offset_m
    yaricap) -- tek merkeze cakisan degil, etrafa dagilmis karolar."""
    rng = np.random.default_rng(seed)
    angles = rng.uniform(0, 2 * np.pi, size=n)
    radii = rng.uniform(0.3, 1.0, size=n) * offset_m
    points = []
    for angle, r in zip(angles, radii):
        dlat = (r * np.sin(angle)) / 111320.0
        dlon = (r * np.cos(angle)) / (111320.0 * np.cos(np.radians(center_lat)))
        points.append((center_lat + dlat, center_lon + dlon))
    return points


def predicted_closed_edges(G, boosted_probs, road_mask, bounds, tau,
                            buffer_m=8.0, sample_step_m=2.0, coverage_fraction=0.5,
                            edge_crs="EPSG:4326"):
    """emsr648_closures.closed_osm_edges ile AYNI orneklem/coverage kurali
    (buffer_m=8, sample_step_m=2, coverage_fraction=0.5) ama kaynak EMSR648
    poligonu yerine modelin (boosted_probs > tau) & road_mask ikili maskesi --
    buffer_m'ye karsilik gelen piksel yaricapiyla dilate edilmis."""
    west, south, east, north = bounds
    h, w = boosted_probs.shape

    m_per_px_x = (east - west) * 111320.0 * np.cos(np.radians((south + north) / 2.0)) / w
    m_per_px_y = (north - south) * 111320.0 / h
    m_per_px = max((m_per_px_x + m_per_px_y) / 2.0, 1e-6)
    kernel_radius_px = max(1, int(round(buffer_m / m_per_px)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * kernel_radius_px + 1,) * 2)

    damage_binary = ((boosted_probs > tau) & (road_mask > 0)).astype(np.uint8)
    dilated = cv2.dilate(damage_binary, kernel)

    records = []
    for u, v, k, data in G.edges(keys=True, data=True):
        if "geometry" in data:
            line = data["geometry"]
        else:
            line = LineString([
                (G.nodes[u]["x"], G.nodes[u]["y"]),
                (G.nodes[v]["x"], G.nodes[v]["y"]),
            ])
        osmid = data.get("osmid")
        if isinstance(osmid, list):
            osmid = tuple(sorted(osmid))
        records.append({"u": u, "v": v, "k": k, "geometry": line, "osmid": osmid})

    if not records:
        return set()

    edges_gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=edge_crs)
    edges_m = edges_gdf.to_crs(METRIC_CRS)

    closed = set()
    for rec, line_m, line_deg in zip(records, edges_m.geometry, edges_gdf.geometry):
        pts_m = _sample_points(line_m, sample_step_m)
        if not pts_m:
            continue
        n = len(pts_m)
        pts_deg = [line_deg.interpolate(i / max(n - 1, 1), normalized=True) for i in range(n)]
        inside = 0
        for pt in pts_deg:
            px = int((pt.x - west) / (east - west) * w)
            py = int((north - pt.y) / (north - south) * h)
            if 0 <= px < w and 0 <= py < h and dilated[py, px] > 0:
                inside += 1
        if inside / n >= coverage_fraction:
            closed.add((rec["u"], rec["v"], rec["k"]))

    # fiziksel yol grubu: ayni (u,v) + ayni osmid -> her iki yon de kapat
    # (closed_osm_edges ile ayni kural)
    physical_keys = set()
    for (u, v, k) in closed:
        rec = next(r for r in records if r["u"] == u and r["v"] == v and r["k"] == k)
        physical_keys.add((frozenset((u, v)), rec["osmid"]))
    grouped = set()
    for rec in records:
        pk = (frozenset((rec["u"], rec["v"])), rec["osmid"])
        if pk in physical_keys:
            grouped.add((rec["u"], rec["v"], rec["k"]))
    return grouped


def run_sample(name, aoi_code, lat, lon, model, device):
    print(f"\n{'='*60}\n{name}  center=({lat:.5f},{lon:.5f})  AOI={aoi_code}\n{'='*60}", flush=True)
    t0 = time.time()
    bounds = bbox_from_point(lat, lon, RADIUS_M)

    img, real_bounds = fetch_satellite_area(lat, lon, bbox=bounds, zoom_level=18,
                                             wayback_id=WAYBACK_ID, provider="esri")
    if img is None:
        print(f"  GORUNTU ALINAMADI ({name}) - atlaniyor", flush=True)
        return None
    w, h = img.size
    print(f"  goruntu: {img.size}, bounds={real_bounds} ({time.time()-t0:.1f}s)", flush=True)

    road_mask = cached_road_mask(real_bounds, w, h)
    if road_mask.mean() == 0:
        print(f"  YOL MASKESI BOS ({name}) - atlaniyor", flush=True)
        return None
    print(f"  yol maskesi, pozitif oran={road_mask.mean():.4f} ({time.time()-t0:.1f}s)", flush=True)

    _, boosted_probs, _, _, _ = run_inference(
        img, road_mask, model, device, damage_booster=3.5, threshold=0.4,
        use_imagenet_norm=False, postprocess_level=0)
    print(f"  cikarim tamam ({time.time()-t0:.1f}s)", flush=True)

    west, south, east, north = real_bounds
    G = None
    last_exc = None
    for attempt in range(4):
        try:
            G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", simplify=True)
            break
        except Exception as exc:
            last_exc = exc
            print(f"  Overpass denemesi {attempt+1}/4 basarisiz: {exc}", flush=True)
            time.sleep(10)
    if G is None:
        print(f"  Overpass'a 4 denemede ulasilamadi, {name} atlaniyor: {last_exc}", flush=True)
        return None
    n_edges = G.number_of_edges()
    print(f"  OSM graf: {G.number_of_nodes()} dugum, {n_edges} kenar ({time.time()-t0:.1f}s)", flush=True)
    if n_edges == 0:
        print(f"  {name}: OSM yolu yok - atlaniyor", flush=True)
        return None

    all_edges = set(G.edges(keys=True))
    truth = {rule: closed_osm_edges(G, aoi_code, rule) for rule in RULES}
    for rule in RULES:
        print(f"  zemin gercegi ({rule}): {len(truth[rule])}/{n_edges} kenar kapali", flush=True)

    print(f"  {name} toplam sure: {time.time()-t0:.1f}s", flush=True)
    return {
        "name": name, "aoi": aoi_code, "G": G, "boosted_probs": boosted_probs,
        "road_mask": road_mask, "bounds": real_bounds, "n_edges": n_edges,
        "all_edges": all_edges, "truth": truth,
    }


def prefetch(max_rounds=24, wait_s=300):
    """Tum ornek karolarin OSM grafini (osmnx onbellegi, ./cache) modelsiz ceker.
    Overpass gecici olarak reddederse wait_s bekleyip eksikleri yeniden dener; boylece
    tum mimariler ayni, eksiksiz ornek kumesi uzerinde (onbellekten) degerlendirilir."""
    tiles = []
    for code, aoi in REGIONS:
        center = ox.geocode(DISTRICTS[code]["query"])
        seed = zlib.crc32(code.encode("utf-8"))
        for i, (lat, lon) in enumerate(sample_points_around(center[0], center[1], N_SAMPLES_PER_DISTRICT, OFFSET_M, seed)):
            img, real_bounds = fetch_satellite_area(lat, lon, bbox=bbox_from_point(lat, lon, RADIUS_M),
                                                    zoom_level=18, wayback_id=WAYBACK_ID, provider="esri")
            if img is None:
                print(f"{code}-{i+1}: GORUNTU ALINAMADI", flush=True)
                continue
            tiles.append((f"{code}-{i+1}", real_bounds, img.size))
    pending = list(tiles)
    for rnd in range(max_rounds):
        still = []
        for name, bounds, (w, h) in pending:
            west, south, east, north = bounds
            try:
                mask = cached_road_mask(bounds, w, h)
                if mask.mean() == 0:
                    raise ConnectionError("yol maskesi bos")
                G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", simplify=True)
                print(f"{name}: OK ({G.number_of_edges()} kenar, maske {mask.mean():.4f})", flush=True)
            except Exception as exc:
                print(f"{name}: basarisiz ({type(exc).__name__}: {str(exc)[:80]})", flush=True)
                still.append((name, bounds, (w, h)))
            time.sleep(5)
        pending = still
        print(f"tur {rnd+1}: {len(tiles)-len(pending)}/{len(tiles)} karo onbellekte", flush=True)
        if not pending:
            return
        time.sleep(wait_s)
    print(f"EKSIK KALDI: {[p[0] for p in pending]}", flush=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="segformer", help="cikti dosyasi ve rapor etiketi")
    ap.add_argument("--arch", default="Segformer", help="smp mimari sinifi (Segformer/Unet/FPN/DeepLabV3Plus/Linknet/PSPNet)")
    ap.add_argument("--encoder", default="mit_b4", help="kodlayici adi (mit_b4/resnet34/resnet101/...)")
    ap.add_argument("--checkpoint", default=str(MODEL_PATH), help="checkpoint (.pth) yolu")
    ap.add_argument("--prefetch", action="store_true",
                    help="model yuklemeden tum orneklerin OSM graflarini osmnx onbellegine al")
    args = ap.parse_args()

    if args.prefetch:
        return prefetch()

    print(f"Model yukleniyor: {args.checkpoint} (arch={args.arch}, encoder={args.encoder})", flush=True)
    model, device = load_simple_model(args.checkpoint, arch=args.arch, encoder=args.encoder)
    if model is None:
        print("MODEL YUKLENEMEDI - cikiliyor", flush=True)
        return
    print(f"Model yuklendi, device={device}", flush=True)

    all_samples = []
    for code, aoi in REGIONS:
        cfg = DISTRICTS[code]
        print(f"\n>>> {code} geocode ediliyor: {cfg['query']}", flush=True)
        center = ox.geocode(cfg["query"])
        print(f"    merkez: {center}", flush=True)
        # Deterministik tohum: hash(str) PYTHONHASHSEED ile her surecte degisir ve
        # her kosuda FARKLI ornek noktalari uretirdi (2026-09-26 duzeltmesi).
        seed = zlib.crc32(code.encode("utf-8"))
        points = sample_points_around(center[0], center[1], N_SAMPLES_PER_DISTRICT, OFFSET_M, seed)
        for i, (lat, lon) in enumerate(points):
            res = run_sample(f"{code}-{i+1}", aoi, lat, lon, model, device)
            if res:
                res["lat"], res["lon"] = lat, lon
                all_samples.append(res)

    if not all_samples:
        print("\nHICBIR ORNEK BASARILI OLMADI - cikiliyor", flush=True)
        return

    total_edges = sum(s["n_edges"] for s in all_samples)
    print(f"\n{'='*70}\nToplam {len(all_samples)} basarili ornek, {total_edges} kenar\n{'='*70}", flush=True)

    sweep_results = {}
    for tau in TAU_SWEEP:
        per_rule = {rule: {"DP": 0, "YN": 0, "YP": 0, "DN": 0} for rule in RULES}
        for s in all_samples:
            pred = predicted_closed_edges(s["G"], s["boosted_probs"], s["road_mask"], s["bounds"], tau)
            for rule in RULES:
                truth = s["truth"][rule]
                for e in s["all_edges"]:
                    t = e in truth
                    p = e in pred
                    key = "DP" if (t and p) else "YN" if (t and not p) else "YP" if (p and not t) else "DN"
                    per_rule[rule][key] += 1
        for rule in RULES:
            c = per_rule[rule]
            precision = c["DP"] / (c["DP"] + c["YP"]) if (c["DP"] + c["YP"]) else float("nan")
            recall = c["DP"] / (c["DP"] + c["YN"]) if (c["DP"] + c["YN"]) else float("nan")
            if precision == precision and recall == recall and (precision + recall) > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = float("nan")
            c["precision"] = precision
            c["recall"] = recall
            c["f1"] = f1
        sweep_results[tau] = per_rule
        m = per_rule["medium"]
        f1_str = f"{m['f1']:.3f}" if m["f1"] == m["f1"] else "nan"
        print(f"  tau={tau:.2f}  orta: DP={m['DP']:>4} YN={m['YN']:>4} YP={m['YP']:>4}  F1={f1_str}", flush=True)

    valid = {t: r for t, r in sweep_results.items() if r["medium"]["f1"] == r["medium"]["f1"]}
    best_tau = max(valid, key=lambda t: valid[t]["medium"]["f1"]) if valid else None

    print(f"\n{'='*70}\nEN IYI TAU (orta kural, F1 maksimize): {best_tau}\n{'='*70}", flush=True)
    if best_tau is not None:
        for rule in RULES:
            r = sweep_results[best_tau][rule]
            print(f"  {rule:>8}: DP={r['DP']} YN={r['YN']} YP={r['YP']} DN={r['DN']}  "
                  f"Kesinlik={r['precision']:.3f}  Duyarlilik={r['recall']:.3f}  F1={r['f1']:.3f}", flush=True)

    out = {
        "model": f"{args.arch} ({args.encoder}, {Path(args.checkpoint).name})",
        "label": args.label,
        "wayback_id": WAYBACK_ID,
        "samples": [{"name": s["name"], "aoi": s["aoi"], "n_edges": s["n_edges"],
                     "lat": round(s["lat"], 6), "lon": round(s["lon"], 6)} for s in all_samples],
        "total_edges": total_edges,
        "tau_sweep": {f"{t:.2f}": r for t, r in sweep_results.items()},
        "best_tau": best_tau,
        "best_tau_results": sweep_results.get(best_tau) if best_tau is not None else None,
    }
    out_name = "table14_segformer_closure.json" if args.label == "segformer" else f"table14_closure_{args.label}.json"
    out_path = Path(__file__).resolve().parent / "results" / out_name
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSonuc: {out_path}", flush=True)


if __name__ == "__main__":
    main()
