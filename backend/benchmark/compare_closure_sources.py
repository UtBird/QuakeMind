"""Ayni senaryonun farkli KAPANMA KAYNAKLARIYLA kosumlarini yan yana koyar.

Her kosum icin (il yarilari birlestirilerek):
  - kapanma kaynagi ve ayari (sentetik oran / model zoom+r_h / EMSR kurali)
  - bolge basina kapali kenar orani
  - rotalanabilen atama sayisi (ekip afetzedeye ulasabildi mi)
  - AYNI KUME uzerinden sure karsilastirmasi: yalniz naif ajanin da
    ulasabildigi atamalar (summary.json'daki totalOurEngineTimeMin tum
    atamalari topladigi icin dogrudan karsilastirilamaz -- bilinen asimetri)
  - kazancin ayrismasi: yol farki (gercek mesafe) + U-donusu cezasi
    (varsayim, naive_baseline.U_TURN_PENALTY_MIN; bkz. E-02)

    python benchmark/compare_closure_sources.py drone-emsr-loose drone-model-z18-r0 ...
"""
import json
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"
CITIES = ("hatay", "kahramanmaras")


def load_run(name):
    parts = []
    for city in CITIES:
        p = RUNS / f"{name}-{city}" / "summary.json"
        if p.exists():
            parts.append(json.loads(p.read_text(encoding="utf-8")))
    if not parts:
        p = RUNS / name / "summary.json"
        if p.exists():
            parts.append(json.loads(p.read_text(encoding="utf-8")))
    return parts


def describe(s):
    src = s.get("closureSource") or "synthetic"
    if src == "synthetic":
        return f"sentetik %{100 * (s.get('closureRatio') or 0):.0f}"
    if src == "model":
        return f"model {s.get('maskSuffix') or ''} r_h={s.get('blockageRadiusM')}"
    if src == "emsr":
        return f"EMSR648 {s.get('emsrRule')}"
    return src


def summarize(name):
    parts = load_run(name)
    if not parts:
        return None
    zones, rows, assignments = [], [], []
    for s in parts:
        zones += s["zones"]
        rows += s["comparison"]["rows"]
        assignments += s["assignments"]
    both = [r for r in rows if not r["naiveUnreachable"]]
    our = sum(r["ourEngineTimeMin"] for r in both)
    naive = sum(r["naiveTimeMin"] for r in both)
    naive_travel = sum(r["naiveTravelOnlyTimeMin"] for r in both)
    penalty = sum(r["naiveUTurnPenaltyMin"] for r in both)
    saved = naive - our
    zone_rates = {}
    for z in zones:
        if z.get("closedEdgeCount") is not None and z.get("edgeCount"):
            zone_rates[z["zoneId"]] = 100.0 * z["closedEdgeCount"] / z["edgeCount"]
        else:
            zone_rates[z["zoneId"]] = None
    return {
        "run": name,
        "source": describe(parts[0]),
        "zones": [z["zoneId"] for z in zones],
        "zoneClosedPct": zone_rates,
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
        "uTurnShareOfSaving": round(penalty / saved, 3) if saved > 0 else None,
    }


def main(names):
    rows = [r for r in (summarize(n) for n in names) if r]
    print(f"{'kosum':24} {'kaynak':26} | {'kapali kenar % (bolge)':34} | {'rota':>5} "
          f"| {'ayni kume: bizim':>16} {'naif':>7} {'kazanc':>7} | {'yol':>6} {'U-don':>6} {'U-don%':>6}")
    print("-" * 150)
    for r in rows:
        rates = " ".join(f"{z}:{v:.1f}" if v is not None else f"{z}:-" for z, v in r["zoneClosedPct"].items())
        share = f"{100 * r['uTurnShareOfSaving']:.0f}" if r["uTurnShareOfSaving"] is not None else "-"
        print(f"{r['run']:24} {r['source']:26} | {rates[:34]:34} | {r['routed']:2d}/{r['victims']:<2d} "
              f"| {r['ourMin']:16.1f} {r['naiveMin']:7.1f} {r['savedMin']:7.1f} "
              f"| {r['savedFromDistanceMin']:6.1f} {r['savedFromUTurnPenaltyMin']:6.1f} {share:>6}")
    print("\nrota = ekibin afetzedeye rotalanabildigi atama / afetzede sayisi")
    print("ayni kume = yalniz naif ajanin da ulasabildigi atamalar; kazanc = naif - bizim")
    print("yol = gercek mesafe farkindan gelen kazanc; U-don = U-donusu ceza varsayimindan gelen kazanc")
    out = RUNS / "closure_source_comparison.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
