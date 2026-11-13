"""Coklu tohum protokolu (E-06): ayni yapilandirmalari birden cok tohumla kosar
ve sonuclari ortalama +- standart sapma olarak ozetler.

Tohum neyi degistirir (full_scenario.py):
  - afetzede konumlari (bolge sinirlari icinde rastgele, birbirinden ayrik,
    karargahlardan ulasilabilir)             -> TUM kaynaklarda
  - sentetik kapanma kumesi (closure_seed)   -> yalniz sentetik kaynakta
EMSR648 ve model kapanmalari tohumdan BAGIMSIZDIR; bu kaynaklarda varyans
yalniz afetzede yerlesiminden gelir.

Ayni tohum farkli kaynaklarda ayni aday nokta dizisini uretir; ama bir aday
kapanmalar yuzunden ulasilamaz cikarsa yeniden orneklenir, yani yerlesim
kaynaklar arasinda ayrisabilir. Ozet bu yuzden "ayni yerlesim" oranini da yazar.

Kullanim (backend ayakta olmali):
  python benchmark/multi_seed.py run                   # 9 yapilandirma x 10 tohum
  python benchmark/multi_seed.py run --configs v2-emsr-loose --seeds 43 44
  python benchmark/multi_seed.py summarize
  # Ara referanslarla (R1 gorus mesafeli ajan, R2 bilgi paylasan filo; Tablo 16),
  # ayri klasore; R0/QuakeMind sonuclari eski taramayla birebir karsilastirilir:
  python benchmark/multi_seed.py run --references --out multi_seed_refs --compare-with multi_seed

Kosular runs/<out>/<yapilandirma>-s<tohum>-<il>/ altina yazilir (varsayilan out:
multi_seed). summary.json'i olan kosu atlanir; yarida kalan tarama kaldigi yerden surer.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from compare_closure_sources import CITIES, describe  # noqa: E402
from naive_baseline import AVERAGE_SPEED_KMH, U_TURN_PENALTY_MIN  # noqa: E402
from pipeline_runner import API_BASE  # noqa: E402

RUNS = HERE / "runs"
MS_DIR = RUNS / "multi_seed"
FULL_SCENARIO = HERE / "full_scenario.py"

DEFAULT_SEEDS = list(range(42, 52))
# Bekleme adimlari yalniz /command sayfasinda izlemek icin; sonucu etkilemez.
SPEED = "1000"

V2_EMSR_ZONES = ["H-Z1", "H-Z3", "K-Z1", "K-Z2"]
# J-28'deki tek tohumlu kosularla birebir ayni parametreler.
CONFIGS = {
    "v2-sentetik-8ilce": ["--dataset", "v2", "--closure-source", "synthetic"],
    "v2-sentetik-4ilce": ["--dataset", "v2", "--closure-source", "synthetic",
                          "--zones", *V2_EMSR_ZONES],
    "v2-emsr-strict": ["--dataset", "v2", "--closure-source", "emsr", "--emsr-rule", "strict",
                       "--zones", *V2_EMSR_ZONES],
    "v2-emsr-medium": ["--dataset", "v2", "--closure-source", "emsr", "--emsr-rule", "medium",
                       "--zones", *V2_EMSR_ZONES],
    "v2-emsr-loose": ["--dataset", "v2", "--closure-source", "emsr", "--emsr-rule", "loose",
                      "--zones", *V2_EMSR_ZONES],
    "drone-sentetik": ["--dataset", "drone", "--closure-source", "synthetic"],
    "drone-emsr-loose": ["--dataset", "drone", "--closure-source", "emsr", "--emsr-rule", "loose"],
    "drone-model-z18-r0": ["--dataset", "drone", "--closure-source", "model",
                           "--mask-suffix=-z18", "--blockage-radius-m", "0"],
    "drone-model-z19-r15": ["--dataset", "drone", "--closure-source", "model",
                            "--mask-suffix=-z19", "--blockage-radius-m", "15"],
}
# Eslestirilmis kaynak karsilastirmasinin referansi (ayni bolge kumesi).
PAIRED_REFERENCE = {
    "v2-emsr-strict": "v2-sentetik-4ilce",
    "v2-emsr-medium": "v2-sentetik-4ilce",
    "v2-emsr-loose": "v2-sentetik-4ilce",
    "drone-emsr-loose": "drone-sentetik",
    "drone-model-z18-r0": "drone-sentetik",
    "drone-model-z19-r15": "drone-sentetik",
}


def run_name(config: str, seed: int) -> str:
    return f"{config}-s{seed}"


def _city_dir(config: str, seed: int, city: str) -> Path:
    return MS_DIR / f"{run_name(config, seed)}-{city}"


def _is_done(config: str, seed: int) -> bool:
    return all((_city_dir(config, seed, c) / "summary.json").exists() for c in CITIES)


def _backend_up() -> bool:
    try:
        return requests.get(f"{API_BASE}/api/status", timeout=10).status_code == 200
    except Exception:
        return False


def _set_aside_partial(config: str, seed: int) -> None:
    """Yarida kalmis kosu klasoru silinmez, kenara alinir (RunLogger events.jsonl'e
    ekleme yaptigi icin ayni klasore yeniden yazmak kayitlari karistirirdi)."""
    for city in CITIES:
        d = _city_dir(config, seed, city)
        if d.exists() and not (d / "summary.json").exists():
            target = MS_DIR / "_yarida_kalan" / f"{d.name}-{int(time.time())}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(d), str(target))


def cmd_run(configs: list[str], seeds: list[int], references: bool = False) -> int:
    todo = [(c, s) for s in seeds for c in configs if not _is_done(c, s)]
    total = len(configs) * len(seeds)
    print(f"{total} kosudan {total - len(todo)} tanesi zaten var; {len(todo)} kosu yapilacak.", flush=True)
    log_dir = MS_DIR / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    t_start = time.perf_counter()
    for i, (config, seed) in enumerate(todo, 1):
        if not _backend_up():
            print("BACKEND YANIT VERMIYOR -- tarama durduruldu (kaldigi yerden surdurulebilir).", flush=True)
            failures.append((config, seed, "backend yok"))
            break
        _set_aside_partial(config, seed)
        cmd = [sys.executable, str(FULL_SCENARIO), "all",
               "--run-id", f"{MS_DIR.name}/{run_name(config, seed)}",
               "--seed", str(seed), "--speed", SPEED, *CONFIGS[config]]
        if references:
            cmd.append("--references")
        t0 = time.perf_counter()
        with open(log_dir / f"{run_name(config, seed)}.log", "w", encoding="utf-8") as log:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(HERE.parent),
                                  env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        dt = time.perf_counter() - t0
        if proc.returncode != 0 or not _is_done(config, seed):
            failures.append((config, seed, f"cikis kodu {proc.returncode}"))
            print(f"[{i}/{len(todo)}] {config} s{seed}: HATA (kod {proc.returncode}, {dt:.0f} sn) "
                  f"-> {log_dir / (run_name(config, seed) + '.log')}", flush=True)
            continue
        row = seed_row(config, seed)
        elapsed = time.perf_counter() - t_start
        eta = elapsed / i * (len(todo) - i)
        extra = ""
        if row.get("references"):
            ref = row["references"]
            v = ref["variants"]
            extra = (f" | R1 {v['R1']['timeMin']:.1f} R2 {v['R2']['timeMin']:.1f} R1R2 {v['R1R2']['timeMin']:.1f}"
                     f" | R0 kontrol {ref['check']['identical']}/{ref['check']['checked']}")
        print(f"[{i}/{len(todo)}] {config} s{seed}: rota {row['routed']}/{row['victims']}, "
              f"bizim {row['ourMin']:.1f} / klasik {row['naiveMin']:.1f} dk, "
              f"U-don {row['uTurns']}{extra} ({dt:.0f} sn; kalan ~{eta / 60:.0f} dk)", flush=True)
    if failures:
        print("\nBASARISIZ KOSULAR:", flush=True)
        for c, s, why in failures:
            print(f"  {c} s{s}: {why}", flush=True)
        return 1
    print(f"\nTarama bitti ({(time.perf_counter() - t_start) / 60:.1f} dk).", flush=True)
    return 0


# --------------------------------------------------------------------------
# Ozet
# --------------------------------------------------------------------------
def _load_parts(base: Path, name: str) -> list[dict]:
    parts = []
    for city in CITIES:
        p = base / f"{name}-{city}" / "summary.json"
        if p.exists():
            parts.append(json.loads(p.read_text(encoding="utf-8")))
    return parts


def _row_from_parts(parts: list[dict]) -> dict:
    zones, rows = [], []
    for s in parts:
        zones += s["zones"]
        rows += s["comparison"]["rows"]
    both = [r for r in rows if not r["naiveUnreachable"]]
    our = sum(r["ourEngineTimeMin"] for r in both)
    naive = sum(r["naiveTimeMin"] for r in both)
    naive_travel = sum(r["naiveTravelOnlyTimeMin"] for r in both)
    penalty = sum(r["naiveUTurnPenaltyMin"] for r in both)
    saved = naive - our
    closed = {}
    for z in zones:
        if z.get("closedEdgeCount") is not None and z.get("edgeCount"):
            closed[z["zoneId"]] = 100.0 * z["closedEdgeCount"] / z["edgeCount"]
    placements = {v["id"]: (round(v["lat"], 7), round(v["lon"], 7)) for z in zones for v in z["victims"]}
    return {
        "source": describe(parts[0]),
        "victims": sum(len(z["victims"]) for z in zones),
        "routed": len(rows),
        "naiveReached": len(both),
        "naiveStuck": sum(1 for r in rows if r["naiveUnreachable"]),
        "uTurns": sum((r.get("naiveDiscoveries") or 0) for r in rows),
        "ourMin": round(our, 1),
        "naiveMin": round(naive, 1),
        "savedMin": round(saved, 1),
        "savedFromDistanceMin": round(naive_travel - our, 1),
        "savedFromUTurnPenaltyMin": round(penalty, 1),
        "uTurnShareOfSaving": (penalty / saved) if saved > 0 else None,
        # Etki buyuklugu: klasik ekip yuzde kac daha uzun yol yuruyor (U-donusu cezasi haric).
        "naiveExtraDistancePct": 100.0 * (naive_travel - our) / our if our > 0 else None,
        "zoneClosedPct": closed,
        "placements": placements,
        "tasks": [{
            "victimId": r["victimId"], "zoneId": r["zoneId"],
            "ourMin": r["ourEngineTimeMin"], "naiveMin": r["naiveTimeMin"],
            "naiveTravelMin": r["naiveTravelOnlyTimeMin"],
            "discoveries": r.get("naiveDiscoveries") or 0,
        } for r in both],
    }


REF_ORDER = ["R0", "R1", "R2", "R1R2"]
# Kosuda varsa tablolara eklenen duyarlilik varyantlari (tablo sirasi: R2'nin hemen altinda).
REF_EXTRA = ["R2e"]
REF_LABELS = {
    "R0": "R0 — naif ajan",
    "R1": "R1 — görüş mesafeli (d_g = 100 m)",
    "R2": "R2 — bilgi paylaşan filo",
    "R2e": "↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık)",
    "R1R2": "R1 + R2 (ek, makalede tanımlı değil)",
}


def _present_variants(names) -> list[str]:
    order = ["R0", "R1", "R2", "R2e", "R1R2"]
    return [v for v in order if v in names and (v in REF_ORDER or v in REF_EXTRA)]


def _reference_metrics(parts: list[dict]) -> dict | None:
    """Ara referanslarin tohum basina toplamlari. Kume: klasik ajanin (R0) ve tum
    referans varyantlarinin her t_u degerinde ulasabildigi gorevler. Sureler
    compute_comparison ile ayni bicimde (gorev basina 0,1 dk'ya yuvarlanarak)
    hesaplanir; boylece R0 toplami taban taramanin klasik toplamina esit cikar."""
    if not all(s.get("references") for s in parts):
        return None
    meta = parts[0]["references"]
    tu_keys = [f"{x:g}" for x in meta["uTurnPenaltyMinValues"]]
    report_key = f"{meta['reportedUTurnPenaltyMin']:g}"
    speed = parts[0]["comparison"]["assumptions"]["averageSpeedKmh"]
    rows = [r for s in parts for r in s["comparison"]["rows"]]
    names = _present_variants([v["name"] for v in meta["variants"]])

    def usable(r):
        refs = r.get("references")
        if r["naiveUnreachable"] or not refs:
            return False
        return all(refs.get(v, {}).get(k, {}).get("reachable") for v in names for k in tu_keys)

    same = [r for r in rows if usable(r)]

    def travel(d):
        return d / 1000.0 / speed * 60.0

    variants = {}
    for v in names:
        rep = [r["references"][v][report_key] for r in same]
        variants[v] = {
            "timeByTu": {k: round(sum(round(travel(r["references"][v][k]["distanceMeters"])
                                            + r["references"][v][k]["penaltyEvents"] * float(k), 1)
                                      for r in same), 1) for k in tu_keys},
            "travelOnlyMin": round(sum(round(travel(x["distanceMeters"]), 1) for x in rep), 1),
            "penaltyEvents": sum(x["penaltyEvents"] for x in rep),
            "discoveries": sum(x["discoveries"] for x in rep),
            "stops": sum(x["stops"] for x in rep),
            "radioReplans": sum(x["radioReplans"] for x in rep),
        }
        variants[v]["timeMin"] = variants[v]["timeByTu"][report_key]
    # Sayim duyarliligi: R0 ayni kavsaktaki ardisik kesifleri tek durak sayarsa
    # (R1'in sayim kurali). R0'in yolu cezadan bagimsiz oldugu icin yeniden hesap yeter.
    r0 = [r["references"]["R0"][report_key] for r in same]
    variants["R0"]["timePerStopMin"] = round(sum(
        round(travel(x["distanceMeters"]) + x["stops"] * float(report_key), 1) for x in r0), 1)
    checked = sum(s["references"]["check"]["checked"] for s in parts)
    identical = sum(s["references"]["check"]["identical"] for s in parts)
    return {
        "taskCount": len(same),
        "excludedTasks": len(rows) - len(same),
        "ourMin": round(sum(r["ourEngineTimeMin"] for r in same), 1),
        "tuKeys": tu_keys,
        "reportKey": report_key,
        "variants": variants,
        "check": {"checked": checked, "identical": identical},
        "elapsedSec": round(sum((z.get("referenceTiming") or {}).get("elapsedSec", 0.0)
                                for s in parts for z in s["zones"]), 1),
    }


def seed_row(config: str, seed: int) -> dict:
    parts = _load_parts(MS_DIR, run_name(config, seed))
    if len(parts) != len(CITIES):
        raise FileNotFoundError(f"{config} s{seed}: iki ilin summary.json'i yok")
    return {"seed": seed, **_row_from_parts(parts), "references": _reference_metrics(parts)}


def describe_values(values: list[float]) -> dict | None:
    from scipy import stats as st
    vals = [v for v in values if v is not None]
    n = len(vals)
    if not n:
        return None
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
    half = float(st.t.ppf(0.975, n - 1)) * sd / math.sqrt(n) if n > 1 else 0.0
    return {"n": n, "mean": mean, "sd": sd, "min": min(vals), "max": max(vals),
            "ci95": [mean - half, mean + half]}


def _quantiles(values: list[float]) -> dict:
    import numpy as np
    arr = np.asarray(values, dtype=float)
    q1, med, q3 = np.percentile(arr, [25, 50, 75])
    return {"median": float(med), "q1": float(q1), "q3": float(q3), "mean": float(arr.mean())}


def signed_rank(diffs: list[float]) -> dict:
    """Tek yonlu Wilcoxon isaretli sira testi (H1: fark > 0) ve eslestirilmis
    sira-iki serili korelasyon (r = (W+ - W-) / (W+ + W-)). Sifir farklar atilir."""
    from scipy import stats as st
    nz = [d for d in diffs if abs(d) > 1e-9]
    out = {"n": len(diffs), "nNonZero": len(nz),
           "sharePositive": sum(1 for d in diffs if d > 1e-9) / len(diffs) if diffs else None,
           "shareZero": sum(1 for d in diffs if abs(d) <= 1e-9) / len(diffs) if diffs else None,
           "shareNegative": sum(1 for d in diffs if d < -1e-9) / len(diffs) if diffs else None,
           "p": None, "rankBiserial": None}
    if len(nz) < 2:
        return out
    ranks = st.rankdata([abs(d) for d in nz])
    w_pos = sum(r for r, d in zip(ranks, nz) if d > 0)
    w_neg = sum(r for r, d in zip(ranks, nz) if d < 0)
    out["rankBiserial"] = (w_pos - w_neg) / (w_pos + w_neg)
    out["p"] = float(st.wilcoxon(nz, alternative="greater").pvalue)
    return out


def _top_share(tasks: list[dict], frac: float) -> float | None:
    disc = sorted((t["discoveries"] for t in tasks), reverse=True)
    total = sum(disc)
    if not total:
        return None
    return sum(disc[:max(1, int(len(disc) * frac))]) / total


def _by_zone(tasks: list[dict]) -> dict:
    out: dict = {}
    for t in tasks:
        out[t["zoneId"]] = out.get(t["zoneId"], 0) + t["discoveries"]
    return out


METRICS = ["routed", "naiveStuck", "uTurns", "ourMin", "naiveMin", "savedMin",
           "savedFromDistanceMin", "savedFromUTurnPenaltyMin", "uTurnShareOfSaving",
           "naiveExtraDistancePct"]
# Ayni kosulardan turetilir (yeni kosu gerekmez): kazanc = yol farki + t_u x kesif.
T_U_SWEEP_MIN = [0, 5, 10, 20, 30]


def summarize_config(config: str, seeds: list[int]) -> dict | None:
    rows = []
    for s in seeds:
        try:
            rows.append(seed_row(config, s))
        except FileNotFoundError:
            pass
    if not rows:
        return None
    agg = {m: describe_values([r[m] for r in rows]) for m in METRICS}
    zone_ids = sorted({z for r in rows for z in r["zoneClosedPct"]})
    agg["zoneClosedPct"] = {z: describe_values([r["zoneClosedPct"].get(z) for r in rows]) for z in zone_ids}
    agg["savedByUTurnPenalty"] = {
        str(tu): describe_values([r["savedFromDistanceMin"] + tu * sum(t["discoveries"] for t in r["tasks"])
                                  for r in rows])
        for tu in T_U_SWEEP_MIN
    }
    tasks = [t for r in rows for t in r["tasks"]]
    total_diff = [t["naiveMin"] - t["ourMin"] for t in tasks]
    dist_diff = [t["naiveTravelMin"] - t["ourMin"] for t in tasks]
    extra_pct = [100.0 * (t["naiveTravelMin"] - t["ourMin"]) / t["ourMin"] for t in tasks if t["ourMin"] > 0]
    pooled = {
        "taskCount": len(tasks),
        "savedPerTask": {**_quantiles(total_diff), **signed_rank(total_diff)} if tasks else None,
        "distanceSavedPerTask": {**_quantiles(dist_diff), **signed_rank(dist_diff)} if tasks else None,
        "naiveExtraDistancePctPerTask": _quantiles(extra_pct) if extra_pct else None,
        "discoveriesPerTask": _quantiles([t["discoveries"] for t in tasks]) if tasks else None,
        "shareTasksWithDiscovery": (sum(1 for t in tasks if t["discoveries"] > 0) / len(tasks)) if tasks else None,
        # U-donusu cezasi birkac gorevde/bolgede mi toplaniyor?
        "discoveriesMaxPerTask": max((t["discoveries"] for t in tasks), default=0),
        "discoveriesTotal": sum(t["discoveries"] for t in tasks),
        "top10PctTasksShareOfDiscoveries": _top_share(tasks, 0.10),
        "discoveriesByZone": _by_zone(tasks),
        "note": "Gorevler tohumlar arasi havuzlandi; ayni ekip/karargahlari paylastiklari "
                "icin tam bagimsiz degiller -- birincil birim tohum basina toplamdir. "
                "Naif ajan yalniz acik kenarlarda yurudugu icin yolu, kapanmalari bilen "
                "en kisa yoldan kisa OLAMAZ: fark yapi geregi >= 0, bu yuzden Wilcoxon p ve "
                "r = 1 bilgi tasimaz (yalniz kayit icin tutuldu).",
    }
    # Tek tohumlu J-28 kosusuyla (runs/<config>-<il>) birebir tekrar kontrolu.
    repro = None
    if any(r["seed"] == 42 for r in rows):
        ref_parts = _load_parts(RUNS, config)
        if len(ref_parts) == len(CITIES):
            ref = _row_from_parts(ref_parts)
            mine = next(r for r in rows if r["seed"] == 42)
            keys = ["routed", "naiveStuck", "uTurns", "ourMin", "naiveMin"]
            repro = {"identical": all(ref[k] == mine[k] for k in keys) and ref["placements"] == mine["placements"],
                     "reference": {k: ref[k] for k in keys},
                     "seed42": {k: mine[k] for k in keys}}
    return {
        "config": config,
        "args": CONFIGS[config],
        "source": rows[0]["source"],
        "seeds": [r["seed"] for r in rows],
        "victims": rows[0]["victims"],
        "perSeed": [{k: v for k, v in r.items() if k not in ("tasks", "placements")} for r in rows],
        "aggregate": agg,
        "pooledTasks": pooled,
        "reproducesSingleSeedRun": repro,
        "references": aggregate_references(rows),
        "_rows": rows,
    }


def aggregate_references(rows: list[dict]) -> dict | None:
    refs = [r["references"] for r in rows if r.get("references")]
    if not refs or len(refs) != len(rows):
        return None
    tu_keys = refs[0]["tuKeys"]

    def gain_pct(total, ours):
        return 100.0 * (total - ours) / total if total > 0 else None

    out = {
        "seeds": len(refs),
        "reportKey": refs[0]["reportKey"],
        "tuKeys": tu_keys,
        "taskCount": describe_values([x["taskCount"] for x in refs]),
        "excludedTasks": sum(x["excludedTasks"] for x in refs),
        "ourMin": describe_values([x["ourMin"] for x in refs]),
        "check": {"checked": sum(x["check"]["checked"] for x in refs),
                  "identical": sum(x["check"]["identical"] for x in refs)},
        "elapsedSec": describe_values([x["elapsedSec"] for x in refs]),
        "variants": {},
    }
    names = [v for v in _present_variants(refs[0]["variants"]) if all(v in x["variants"] for x in refs)]
    out["variantOrder"] = names
    for v in names:
        vals = [(x["ourMin"], x["variants"][v]) for x in refs]
        out["variants"][v] = {
            "timeMin": describe_values([y["timeMin"] for _, y in vals]),
            "gainMin": describe_values([y["timeMin"] - o for o, y in vals]),
            "gainPct": describe_values([gain_pct(y["timeMin"], o) for o, y in vals]),
            "travelOnlyMin": describe_values([y["travelOnlyMin"] for _, y in vals]),
            "distanceGainMin": describe_values([y["travelOnlyMin"] - o for o, y in vals]),
            "penaltyEvents": describe_values([y["penaltyEvents"] for _, y in vals]),
            "discoveries": describe_values([y["discoveries"] for _, y in vals]),
            "stops": describe_values([y["stops"] for _, y in vals]),
            "radioReplans": describe_values([y["radioReplans"] for _, y in vals]),
            "gainByTu": {k: describe_values([y["timeByTu"][k] - o for o, y in vals]) for k in tu_keys},
            "gainPctByTu": {k: describe_values([gain_pct(y["timeByTu"][k], o) for o, y in vals])
                            for k in tu_keys},
        }
    out["r0PerStop"] = {
        "timeMin": describe_values([x["variants"]["R0"]["timePerStopMin"] for x in refs]),
        "gainMin": describe_values([x["variants"]["R0"]["timePerStopMin"] - x["ourMin"] for x in refs]),
        "gainPct": describe_values([gain_pct(x["variants"]["R0"]["timePerStopMin"], x["ourMin"]) for x in refs]),
        "stops": describe_values([x["variants"]["R0"]["stops"] for x in refs]),
    }
    # Ayni tohumda referansin R0'dan farki (negatif = R0'dan hizli).
    out["timeMinusR0"] = {
        v: describe_values([x["variants"][v]["timeMin"] - x["variants"]["R0"]["timeMin"] for x in refs])
        for v in names if v != "R0"
    }
    out["shareOfR0GainRemaining"] = {
        v: describe_values([(x["variants"][v]["timeMin"] - x["ourMin"]) / (x["variants"]["R0"]["timeMin"] - x["ourMin"])
                            if x["variants"]["R0"]["timeMin"] - x["ourMin"] > 0 else None for x in refs])
        for v in names if v != "R0"
    }
    return out


def compare_with_dir(config: str, seeds: list[int], other: str) -> dict:
    """Bu taramanin R0/QuakeMind sonuclari baska bir taramayla (orn. referanssiz
    ilk tarama) birebir ayni mi -- referans kodunun tabani bozmadiginin kaniti."""
    keys = ["routed", "naiveStuck", "uTurns", "ourMin", "naiveMin", "savedFromDistanceMin"]
    compared, identical, diffs = 0, 0, []
    for s in seeds:
        a = _load_parts(MS_DIR, run_name(config, s))
        b = _load_parts(RUNS / other, run_name(config, s))
        if len(a) != len(CITIES) or len(b) != len(CITIES):
            continue
        ra, rb = _row_from_parts(a), _row_from_parts(b)
        compared += 1
        same = all(ra[k] == rb[k] for k in keys) and ra["placements"] == rb["placements"]
        identical += int(same)
        if not same:
            diffs.append({"seed": s, "this": {k: ra[k] for k in keys}, "other": {k: rb[k] for k in keys}})
    return {"other": other, "compared": compared, "identical": identical, "diffs": diffs}


def paired_against_reference(result: dict, reference: dict) -> dict:
    """Ayni tohumda kaynak farki: kazanc ve yol farki (bu kaynak - referans)."""
    ref_by_seed = {r["seed"]: r for r in reference["_rows"]}
    diffs_saved, diffs_dist, same_place, placed = [], [], 0, 0
    routed_this, routed_ref = [], []
    for r in result["_rows"]:
        ref = ref_by_seed.get(r["seed"])
        if not ref:
            continue
        diffs_saved.append(r["savedMin"] - ref["savedMin"])
        diffs_dist.append(r["savedFromDistanceMin"] - ref["savedFromDistanceMin"])
        routed_this.append(r["naiveReached"])
        routed_ref.append(ref["naiveReached"])
        for vid, pos in r["placements"].items():
            placed += 1
            same_place += int(ref["placements"].get(vid) == pos)
    return {
        "reference": reference["config"],
        "seedsPaired": len(diffs_saved),
        "savedMinusReference": describe_values(diffs_saved),
        "distanceSavedMinusReference": describe_values(diffs_dist),
        # Kume buyuklukleri farkliysa (orn. ag kilitlenip gorev dusmusse) fark
        # kazanc farki degil, kume farkidir -- tabloda birlikte okunmali.
        "sameSetTasksThis": describe_values(routed_this),
        "sameSetTasksReference": describe_values(routed_ref),
        "samePlacementShare": same_place / placed if placed else None,
    }


def tr(x: float | None, d: int = 1) -> str:
    """Belgelerdeki bicim: binlik ayraci bosluk, ondalik virgul."""
    if x is None:
        return "—"
    s = f"{x:,.{d}f}"
    return s.replace(",", " ").replace(".", ",")


def pm(stat: dict | None, d: int = 1) -> str:
    if not stat:
        return "—"
    return f"{tr(stat['mean'], d)} ± {tr(stat['sd'], d)}"


def pct(x: float | None) -> str:
    return "—" if x is None else f"%{tr(100 * x, 0)}"


def write_markdown(results: list[dict], path: Path, seeds: list[int]) -> None:
    L = []
    has_refs = any(r.get("references") for r in results)
    L.append("# Çoklu tohum koşusu" + (" ve ara karşılaştırma referansları (E-06, M-25)\n" if has_refs else " (E-06)\n"))
    L.append(f"Tohumlar: {', '.join(map(str, seeds))} · v_ort = {tr(AVERAGE_SPEED_KMH)} km/sa ve "
             f"t_u = {tr(U_TURN_PENALTY_MIN, 0)} dk (değişmedi) · üretici: `benchmark/multi_seed.py`.\n")
    L.append("Tohum afetzede yerleşimini (tüm kaynaklarda) ve sentetik kapanma kümesini (yalnız sentetikte) "
             "değiştirir; EMSR648 ve model kapanmaları sabittir. Süreler **aynı küme** üzerinden "
             "(klasik ekibin de ulaşabildiği görevler), tohum başına toplamların ortalama ± standart sapmasıdır.\n")
    L.append("## Tohum başına toplamlar\n")
    L.append("| Yapılandırma | Kapanma | Afetzede | Rotalanan | Klasik ulaşamadı | QuakeMind (dk) | Klasik (dk) | Kazanç (dk) | Kazanç %95 GA | Yol farkı (dk) | Klasik ek yol (%) | U-dönüşü sayısı | U-dönüşü payı |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        a = r["aggregate"]
        ci = a["savedMin"]["ci95"] if a["savedMin"] else None
        share = a["uTurnShareOfSaving"]
        L.append(f"| {r['config']} | {r['source']} | {r['victims']} | {pm(a['routed'])} | {pm(a['naiveStuck'])} | "
                 f"{pm(a['ourMin'])} | "
                 f"{pm(a['naiveMin'])} | {pm(a['savedMin'])} | "
                 f"{'[' + tr(ci[0]) + '; ' + tr(ci[1]) + ']' if ci else '—'} | "
                 f"{pm(a['savedFromDistanceMin'])} | {pm(a['naiveExtraDistancePct'])} | {pm(a['uTurns'])} | "
                 f"{pct(share['mean']) if share else '—'} |")
    L.append("\n## Görev düzeyi (tohumlar havuzlanmış)\n")
    L.append("Klasik ekip yalnız açık yollarda yürüdüğü için yolu, kapanmaları bilen en kısa yoldan kısa "
             "**olamaz**: fark yapı gereği ≥ 0 (tabloda \"Yol farkı < 0\" her yerde %0). Bu yüzden işaretli "
             "sıra testi her zaman anlamlı ve etki büyüklüğü r = 1 çıkar; bilgi taşımadıkları için tabloda "
             "yoklar (JSON'da duruyor). Anlamlı olan büyüklük ve sıklıktır. Görevler aynı ekip ve karargâhları "
             "paylaştığı için tam bağımsız değildir; birincil birim yukarıdaki tohum başına toplamdır.\n")
    L.append("| Yapılandırma | Görev | Kapanmaya çarpılan görev | Kazanç medyan [Ç1; Ç3] (dk) | Kazanç > 0 | Yol farkı medyan [Ç1; Ç3] (dk) | Yol farkı > 0 | Yol farkı < 0 | Klasik ek yol % medyan [Ç1; Ç3] |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        p = r["pooledTasks"]
        s, dd, ex = p["savedPerTask"], p["distanceSavedPerTask"], p["naiveExtraDistancePctPerTask"]
        if not s:
            L.append(f"| {r['config']} | 0 | — | — | — | — | — | — | — |")
            continue
        L.append(f"| {r['config']} | {p['taskCount']} | {pct(p['shareTasksWithDiscovery'])} | "
                 f"{tr(s['median'])} [{tr(s['q1'])}; {tr(s['q3'])}] | {pct(s['sharePositive'])} | "
                 f"{tr(dd['median'])} [{tr(dd['q1'])}; {tr(dd['q3'])}] | {pct(dd['sharePositive'])} | "
                 f"{pct(dd['shareNegative'])} | "
                 + (f"{tr(ex['median'])} [{tr(ex['q1'])}; {tr(ex['q3'])}]" if ex else "—") + " |")
    L.append("\n## U-dönüşlerinin dağılımı (10 tohum toplamı)\n")
    L.append("| Yapılandırma | Toplam keşif | Görev başına en çok | En çok keşifli %10 görevin payı | Bölgelere göre keşif |")
    L.append("|---|---|---|---|---|")
    for r in results:
        p = r["pooledTasks"]
        zones = " · ".join(f"{z}: {n}" for z, n in sorted(p["discoveriesByZone"].items()) if n)
        L.append(f"| {r['config']} | {p['discoveriesTotal']} | {p['discoveriesMaxPerTask']} | "
                 f"{pct(p['top10PctTasksShareOfDiscoveries'])} | {zones or '—'} |")
    L.append("\n## Aynı tohumda kaynak farkı (eşleştirilmiş)\n")
    L.append("Fark = bu yapılandırma − referans, aynı tohumda. Karşılaştırılan görev sayıları farklıysa "
             "fark kazanç farkı değil küme farkıdır.\n")
    L.append("| Yapılandırma | Referans | Eşleşen tohum | Görev (bu / ref.) | Kazanç farkı (dk) | Yol farkı farkı (dk) | Aynı yerleşim |")
    L.append("|---|---|---|---|---|---|---|")
    for r in results:
        pr = r.get("pairedAgainstReference")
        if not pr:
            continue
        L.append(f"| {r['config']} | {pr['reference']} | {pr['seedsPaired']} | "
                 f"{tr(pr['sameSetTasksThis']['mean'])} / {tr(pr['sameSetTasksReference']['mean'])} | "
                 f"{pm(pr['savedMinusReference'])} | "
                 f"{pm(pr['distanceSavedMinusReference'])} | {pct(pr['samePlacementShare'])} |")
    L.append("\n## U-dönüşü cezasına duyarlılık (aynı koşulardan)\n")
    L.append("Kazanç = yol farkı + t_u × keşif sayısı; tohum başına toplamların ortalama ± ss'si (dk). "
             f"Raporlanan değer t_u = {tr(U_TURN_PENALTY_MIN, 0)} dk.\n")
    L.append("| Yapılandırma | " + " | ".join(f"t_u = {tu} dk" for tu in T_U_SWEEP_MIN) + " |")
    L.append("|---|" + "---|" * len(T_U_SWEEP_MIN))
    for r in results:
        sw = r["aggregate"]["savedByUTurnPenalty"]
        L.append(f"| {r['config']} | " + " | ".join(pm(sw[str(tu)]) for tu in T_U_SWEEP_MIN) + " |")
    L.append("\n## Bölge başına kapalı kenar oranı (%)\n")
    L.append("| Yapılandırma | Bölge: ortalama ± ss |")
    L.append("|---|---|")
    for r in results:
        zc = r["aggregate"]["zoneClosedPct"]
        L.append(f"| {r['config']} | " + " · ".join(f"{z}: {pm(v, 2)}" for z, v in zc.items()) + " |")
    L.append("\n## Tek tohumlu koşuyla (J-28, tohum 42) tekrar kontrolü\n")
    L.append("| Yapılandırma | Birebir aynı | J-28 (bizim / klasik / U-dön.) | Bu tarama, tohum 42 |")
    L.append("|---|---|---|---|")
    for r in results:
        rp = r["reproducesSingleSeedRun"]
        if not rp:
            continue
        a, b = rp["reference"], rp["seed42"]
        L.append(f"| {r['config']} | {'evet' if rp['identical'] else '**HAYIR**'} | "
                 f"{tr(a['ourMin'])} / {tr(a['naiveMin'])} / {a['uTurns']} | "
                 f"{tr(b['ourMin'])} / {tr(b['naiveMin'])} / {b['uTurns']} |")
    write_reference_sections(L, results)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_reference_sections(L: list[str], results: list[dict]) -> None:
    with_refs = [r for r in results if r.get("references")]
    if not with_refs:
        return
    L.append("\n## Ara karşılaştırma referansları (Tablo 16, M-25)\n")
    L.append("Aynı oturum, aynı kapanma kümesi, aynı atamalar; değişen yalnız ekibin kapanmayı nasıl "
             "öğrendiği. Küme: klasik ajanın ve tüm referansların her t_u değerinde ulaşabildiği görevler. "
             "t_u = 20 dk; tohum başına toplamların ortalama ± ss'si. **R0**: kapanmayı kavşakta, girmeden "
             "öğrenir; her keşif bir t_u (Algoritma 1). **R1**: her kavşakta planlı yolun önündeki 100 m'yi "
             "görür (yol boyunca; köşe dönüşleri görüşü kesmez — R1 için iyimser); aynı kavşaktaki "
             "gözlemler tek t_u. **R2**: bölgedeki ekipler aynı anda yola çıkar; bir ekibin öğrendiği "
             "kapanma o anda telsizle tüm ekiplere yayılır; telsizle öğrenilen kapanma cezasız yeniden "
             "planlanır, kendi keşfi R0 gibi cezalıdır. Aynı karargâhtan çıkan ekipler ortak yol başında "
             "kafile halinde ilerler: kapanmayı öndeki keşfeder, arkadakiler cezasız yön değiştirir "
             "(\"anında yayılır\"). **R2e** bu kafile kuralının duyarlılığıdır: aynı anda varan her ekip "
             "kendisi keşfeder. **R1 + R2** ikisini birleştirir (ek). "
             "Fark = referans − QuakeMind; kazanç % = fark / referans süresi (Tablo 16'nın paydası).\n")
    L.append("| Yapılandırma | Yaklaşım | Toplam süre (dk) | Fark (dk) | Kazanç (%) | Yalnız yol farkı (dk) | Ceza olayı | Görülen/keşfedilen kapanma | Telsizle yeniden planlama |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in with_refs:
        ref = r["references"]
        L.append(f"| {r['config']} | QuakeMind (kusursuz bilgi, R3) — {tr(ref['taskCount']['mean'])} görev | "
                 f"{pm(ref['ourMin'])} | — | — | — | — | — | — |")
        for v in ref["variantOrder"]:
            x = ref["variants"][v]
            L.append(f"| | {REF_LABELS[v]} | {pm(x['timeMin'])} | {pm(x['gainMin'])} | {pm(x['gainPct'])} | "
                     f"{pm(x['distanceGainMin'])} | {pm(x['penaltyEvents'])} | {pm(x['discoveries'])} | "
                     f"{pm(x['radioReplans']) if v in ('R2', 'R2e', 'R1R2') else '—'} |")
            if v == "R0":
                ps = ref["r0PerStop"]
                L.append(f"| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | {pm(ps['timeMin'])} | "
                         f"{pm(ps['gainMin'])} | {pm(ps['gainPct'])} | {pm(x['distanceGainMin'])} | "
                         f"{pm(ps['stops'])} | {pm(x['discoveries'])} | — |")

    L.append("\n## Referansların R0'a göre farkı (aynı tohum)\n")
    L.append("Süre farkı = referans − R0 (negatif: R0'dan hızlı). \"Kalan pay\" = (referans − QuakeMind) / "
             "(R0 − QuakeMind): R0'a karşı ölçülen kazancın o referansa karşı ne kadarının kaldığı.\n")
    others = [v for v in with_refs[0]["references"]["variantOrder"] if v != "R0"]
    short = {"R1": "R1", "R2": "R2", "R2e": "R2e", "R1R2": "R1+R2"}
    L.append("| Yapılandırma | " + " | ".join(f"{short[v]} − R0 (dk)" for v in others) + " | "
             + " | ".join(f"Kalan pay {short[v]}" for v in others) + " |")
    L.append("|---|" + "---|" * (2 * len(others)))
    for r in with_refs:
        ref = r["references"]
        d, sh = ref["timeMinusR0"], ref["shareOfR0GainRemaining"]
        L.append(f"| {r['config']} | " + " | ".join(pm(d.get(v)) for v in others) + " | "
                 + " | ".join(("%" + tr(100 * sh[v]['mean'], 0) + " ± " + tr(100 * sh[v]['sd'], 0))
                              if sh.get(v) else "—" for v in others) + " |")

    tu_keys = sorted(with_refs[0]["references"]["tuKeys"], key=float)
    L.append("\n## Referanslarda t_u duyarlılığı (kazanç, dk ve %)\n")
    L.append("R0 ve R1'de olaylar t_u'dan bağımsızdır (yeniden hesap); R2'de kimin önce öğrendiği t_u'ya "
             "bağlı olduğu için her t_u ayrıca simüle edildi.\n")
    L.append("| Yapılandırma | Yaklaşım | " + " | ".join(f"t_u = {k} dk" for k in tu_keys) + " |")
    L.append("|---|---|" + "---|" * len(tu_keys))
    for r in with_refs:
        ref = r["references"]
        for i, v in enumerate(ref["variantOrder"]):
            x = ref["variants"][v]
            cells = []
            for k in tu_keys:
                g, p = x["gainByTu"][k], x["gainPctByTu"][k]
                cells.append(f"{pm(g)} (%{tr(p['mean'], 0)})" if g and p else pm(g))
            L.append(f"| {r['config'] if i == 0 else ''} | {REF_LABELS[v]} | " + " | ".join(cells) + " |")

    L.append("\n## Doğrulama\n")
    L.append("\"R0 = naive_compare\": yeni simülatörün R0 modu, mevcut klasik ajanın sonucunu görev görev "
             "(mesafe ve keşif sayısı) birebir verdi mi. \"Eski tarama\": bu taramanın QuakeMind/R0 "
             "toplamları ve afetzede yerleşimleri, referanssız taramayla tohum tohum aynı mı.\n")
    L.append("| Yapılandırma | R0 = naive_compare (görev) | Eski taramayla aynı (tohum) | Referans hesabı (sn / tohum) |")
    L.append("|---|---|---|---|")
    for r in with_refs:
        ref = r["references"]
        cw = r.get("compareWith")
        L.append(f"| {r['config']} | {ref['check']['identical']} / {ref['check']['checked']} | "
                 f"{(str(cw['identical']) + ' / ' + str(cw['compared']) + ' (' + cw['other'] + ')') if cw else '—'} | "
                 f"{pm(ref['elapsedSec'])} |")


def cmd_summarize(configs: list[str], seeds: list[int], compare_with: str | None = None) -> int:
    results = [r for r in (summarize_config(c, seeds) for c in configs) if r]
    by_name = {r["config"]: r for r in results}
    for r in results:
        ref = by_name.get(PAIRED_REFERENCE.get(r["config"], ""))
        if ref:
            r["pairedAgainstReference"] = paired_against_reference(r, ref)
        if compare_with:
            r["compareWith"] = compare_with_dir(r["config"], seeds, compare_with)
    print(f"{'yapilandirma':22} {'tohum':>5} {'rota':>11} {'bizim':>15} {'klasik':>17} "
          f"{'kazanc':>17} {'yol farki':>13} {'U-don%':>6} {'tekrar':>6}")
    for r in results:
        a = r["aggregate"]
        share = a["uTurnShareOfSaving"]
        rp = r["reproducesSingleSeedRun"]
        f = lambda s: f"{s['mean']:.1f}±{s['sd']:.1f}" if s else "-"  # noqa: E731
        print(f"{r['config']:22} {len(r['seeds']):5d} {f(a['routed']) + '/' + str(r['victims']):>11} "
              f"{f(a['ourMin']):>15} {f(a['naiveMin']):>17} {f(a['savedMin']):>17} "
              f"{f(a['savedFromDistanceMin']):>13} "
              f"{(str(round(100 * share['mean'])) if share else '-'):>6} "
              f"{('-' if not rp else ('evet' if rp['identical'] else 'HAYIR')):>6}")
    with_refs = [r for r in results if r.get("references")]
    if with_refs:
        print(f"\n{'yapilandirma':22} {'bizim':>12} " + " ".join(f"{v:>21}" for v in REF_ORDER)
              + f" {'R0 kontrol':>12} {'eski tarama':>12}")
        for r in with_refs:
            ref = r["references"]
            f = lambda s: f"{s['mean']:.1f}±{s['sd']:.1f}" if s else "-"  # noqa: E731
            cw = r.get("compareWith")
            print(f"{r['config']:22} {f(ref['ourMin']):>12} "
                  + " ".join(f"{f(ref['variants'][v]['timeMin']) + ' (%' + format(ref['variants'][v]['gainPct']['mean'], '.0f') + ')':>21}"
                             if ref['variants'][v]['gainPct'] else f"{f(ref['variants'][v]['timeMin']):>21}"
                             for v in REF_ORDER)
                  + f" {str(ref['check']['identical']) + '/' + str(ref['check']['checked']):>12}"
                  + f" {(str(cw['identical']) + '/' + str(cw['compared'])) if cw else '-':>12}")
    out = MS_DIR / "multi_seed_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: v for k, v in r.items() if k != "_rows"} for r in results]
    out.write_text(json.dumps({"seeds": seeds, "uTurnPenaltyMin": U_TURN_PENALTY_MIN,
                               "results": clean}, ensure_ascii=False, indent=2), encoding="utf-8")
    md = MS_DIR / "multi_seed_tablo.md"
    write_markdown(results, md, seeds)
    print(f"-> {out}\n-> {md}")
    return 0


def main(argv=None) -> int:
    global MS_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run", "summarize"])
    parser.add_argument("--configs", nargs="*", default=list(CONFIGS), choices=list(CONFIGS))
    parser.add_argument("--seeds", nargs="*", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--out", default="multi_seed",
                        help="runs/ altindaki tarama klasoru (orn. multi_seed_refs)")
    parser.add_argument("--references", action="store_true",
                        help="full_scenario.py'ye --references gecir (R1/R2, Tablo 16)")
    parser.add_argument("--compare-with", default=None,
                        help="QuakeMind/R0 sonuclarini bu taramayla tohum tohum karsilastir (orn. multi_seed)")
    args = parser.parse_args(argv)
    if not args.out.replace("_", "").replace("-", "").isalnum():
        parser.error("--out yalniz harf, rakam, _ ve - icerebilir")
    MS_DIR = RUNS / args.out
    if args.command == "run":
        code = cmd_run(args.configs, args.seeds, args.references)
        cmd_summarize(args.configs, args.seeds, args.compare_with)
        return code
    return cmd_summarize(args.configs, args.seeds, args.compare_with)


if __name__ == "__main__":
    raise SystemExit(main())
