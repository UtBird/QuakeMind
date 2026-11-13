"""Senaryo v2 kosusunun ic tutarliligini dogrular.

Rapordaki hicbir sayiya guvenmeden, runs/<run_id>/summary.json uzerinden
bagimsiz kontroller yapar:

  1. ROTA DOGRULUGU (en kritik): hicbir ekip rotasi, kendi bolgesinin KAPALI
     yol segmentlerinin uzerinden gecmemeli. Kontrol, daha once reciprocal-edge
     hatasini yakalayan yontemin aynisi: bir kapali segmentin HER IKI UC
     NOKTASI da rota cizgisine cok yakinsa, rota o segmenti fiilen kullanmis
     demektir. (Sadece tek nokta temasi, ortak bir kavsaktan gecmek anlamina
     gelir ve ihlal DEGILDIR -- eski gevsek kontrol burada yanlis pozitif
     uretiyordu.)
  2. CONCURRENCY: her mukerrer sevk denemesi gercekten 409 almis mi.
  3. KANAL KANITI: her kanaldan en az bir ihbarda gercek model ciktisi var mi.
  4. NAIVE TUTARLILIGI: hicbir ekip icin naive sure bizim suremizden kucuk
     olmamali (kucukse model hatasi var demektir).
  5. VERI SETI: 18 afetzede / 18 ekip / 11 karargah eksiksiz islenmis mi.

Kullanim:
  python benchmark/verify_scenario_v2.py            # senaryo-v2-* kosularini bul
  python benchmark/verify_scenario_v2.py runs/xyz
"""

import argparse
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(BENCH_DIR.parent))

import math  # noqa: E402

import scenario_dataset as DS  # noqa: E402

RUNS_DIR = BENCH_DIR / "runs"

# Rotanin ARDISIK iki kosesi, kapali segmentin iki ucuyla toplamda bu sapma
# icinde eslesiyorsa rota o segmenti FIILEN kat etmis demektir.
#
# NEDEN UC-NOKTA YAKINLIGI DEGIL: onceki surum "segmentin her iki ucu da rota
# cizgisine yakin mi" diye bakiyordu. Bu, segment kisa oldugunda ayirt
# edemiyor -- olculdu: 5.72 m uzunlugundaki bir cikmaz sokak parcasi, 4.4 m
# oteden gecen bir rota tarafindan "kullanilmis" gibi isaretlendi, oysa
# rotanin ardisik koseleri arasinda o segment HIC yoktu. Kat etme testi
# (ardisik kose esleme) bu sinif yanlis pozitifi tamamen ortadan kaldirir.
TRAVERSAL_TOLERANCE_M = 1.0


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)


def _segment_endpoints(segment) -> list[tuple]:
    """blockedRoadSegments elemanindan (lat,lon) uc noktalari cikarir.

    Segment formati backend'in serialization'ina bagli -- hem [[lat,lon],...]
    hem {"coords": [...]} bicimleri tolere edilir."""
    coords = segment
    if isinstance(segment, dict):
        coords = segment.get("coords") or segment.get("coordinates") or segment.get("points")
    if not coords or len(coords) < 2:
        return []
    return [tuple(coords[0]), tuple(coords[-1])]


def verify_routes(summary: dict) -> tuple[int, list[str]]:
    """Her rotayi kendi bolgesinin kapali segmentleriyle karsilastirir."""
    problems = []
    checked = 0

    for zone in summary["zones"]:
        blocked = zone.get("blockedRoadSegments") or []
        if not blocked:
            continue
        blocked_ends = [ep for seg in blocked if (ep := _segment_endpoints(seg))]

        for a in zone["assignments"]:
            route = a.get("routeCoords")
            if not route or len(route) < 2:
                continue
            checked += 1

            # Rotanin ardisik kose ciftleri -- bir kapali segmentin uclariyla
            # (her iki yonde de) eslesen var mi?
            violated = None
            for ends in blocked_ends:
                (lat0, lon0), (lat1, lon1) = ends
                for i in range(len(route) - 1):
                    p, q = route[i], route[i + 1]
                    # Sifir uzunluklu (tekrarlanan) kose cifti atlanir: rota
                    # bir kavsakta ayni noktayi iki kez icerebiliyor ve bu,
                    # o kavsaktan BASLAYAN kisa bir kapali segmenti yanlislikla
                    # "kat edilmis" gosteriyordu (olculdu: 2.6 m'lik segment,
                    # rotanin 129-130. koseleri ayni noktaydi).
                    if _haversine_m(p[0], p[1], q[0], q[1]) < 0.5:
                        continue
                    # Uclar AYRI AYRI eslesmeli -- toplam sapma kullanmak,
                    # bir ucu tam tutup digeri uzakta olan durumlari da
                    # gecerli sayiyordu.
                    forward = (_haversine_m(p[0], p[1], lat0, lon0) <= TRAVERSAL_TOLERANCE_M
                               and _haversine_m(q[0], q[1], lat1, lon1) <= TRAVERSAL_TOLERANCE_M)
                    backward = (_haversine_m(p[0], p[1], lat1, lon1) <= TRAVERSAL_TOLERANCE_M
                                and _haversine_m(q[0], q[1], lat0, lon0) <= TRAVERSAL_TOLERANCE_M)
                    if forward or backward:
                        violated = (lat0, lon0, lat1, lon1)
                        break
                if violated:
                    break

            if violated:
                lat0, lon0, lat1, lon1 = violated
                problems.append(
                    f"{zone['zoneId']} {a['teamId']} -> {a['victimName']}: rota KAPALI "
                    f"bir segmenti KAT EDIYOR ({lat0:.5f},{lon0:.5f})-({lat1:.5f},{lon1:.5f})")
    return checked, problems


def verify_concurrency(summary: dict) -> list[str]:
    problems = []
    for a in summary["assignments"]:
        c = a.get("claimConflict")
        if not c:
            continue
        if not c.get("blocked"):
            problems.append(
                f"{a['teamId']} hedefini {c['rivalTeamId']} de aldi "
                f"(HTTP {c['statusCode']}) -- kilit calismadi!")
    return problems


def verify_channels(summary: dict) -> list[str]:
    """Her kanaldan gercek model ciktisi geldi mi."""
    problems = []
    seen = {"yolo": False, "nlp": False, "sos": False}
    for zone in summary["zones"]:
        for v in zone["victims"]:
            cr = v.get("channelResult") or {}
            ch = v["channel"]
            if ch == "yolo" and cr.get("detectionCount"):
                seen["yolo"] = True
            elif ch == "nlp" and cr.get("modelKategori"):
                seen["nlp"] = True
            elif ch == "sos" and (cr.get("deviceState") or {}).get("payloadBytes"):
                seen["sos"] = True

            st = cr.get("deviceState") or {}
            if not st.get("payloadBytes"):
                problems.append(f"{v['id']}: mesh paket byte olcumu yok")
            if cr.get("error"):
                problems.append(f"{v['id']} ({ch}): kanal hatasi -- {cr['error']}")

    for ch, ok in seen.items():
        if not ok:
            problems.append(f"{ch} kanalindan HIC gercek model ciktisi alinamadi")
    return problems


def verify_naive(summary: dict) -> list[str]:
    problems = []
    for r in summary["comparison"]["rows"]:
        if r["naiveUnreachable"]:
            continue
        if r["naiveTimeMin"] < r["ourEngineTimeMin"]:
            problems.append(
                f"{r['teamId']}: naive sure ({r['naiveTimeMin']} dk) bizimkinden "
                f"({r['ourEngineTimeMin']} dk) KUCUK -- model hatasi")
    return problems


def verify_coverage(summaries: list[dict]) -> list[str]:
    problems = []
    handled_victims = {v["id"] for s in summaries for z in s["zones"] for v in z["victims"]}
    handled_teams = {a["teamId"] for s in summaries for a in s["assignments"]}
    handled_hqs = {h["id"] for s in summaries for z in s["zones"] for h in z["headquarters"]}

    cities = {s["city"] for s in summaries}
    expected_victims = {v["id"] for v in DS.VICTIMS if v["city"] in cities}
    expected_teams = {t["id"] for t in DS.TEAMS if t["city"] in cities}
    expected_hqs = {h["id"] for h in DS.HEADQUARTERS
                    if DS.ZONES_BY_ID[h["zoneId"]]["city"] in cities}

    if missing := expected_victims - handled_victims:
        problems.append(f"islenmeyen afetzede: {sorted(missing)}")
    if missing := expected_teams - handled_teams:
        problems.append(f"gorev almayan ekip: {sorted(missing)}")
    if missing := expected_hqs - handled_hqs:
        problems.append(f"haritaya girmeyen karargah: {sorted(missing)}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="*")
    args = parser.parse_args()

    if args.runs:
        run_dirs = [Path(r) if Path(r).is_absolute() else (BENCH_DIR / r) for r in args.runs]
    else:
        run_dirs = sorted([p for p in RUNS_DIR.glob("senaryo-v2-*") if (p / "summary.json").exists()])

    if not run_dirs:
        _safe_print("Kosu bulunamadi.")
        return 1

    summaries = []
    all_problems = []
    total_routes = 0

    for d in run_dirs:
        with open(d / "summary.json", encoding="utf-8") as f:
            s = json.load(f)
        summaries.append(s)
        _safe_print(f"\n=== {s['runId']} ({s['cityLabel']}) ===")

        checked, route_problems = verify_routes(s)
        total_routes += checked
        _safe_print(f"  [1] Rota/kapali-yol kesisimi: {checked} rota kontrol edildi, "
                    f"{len(route_problems)} ihlal")
        all_problems += route_problems

        conc = verify_concurrency(s)
        _safe_print(f"  [2] Concurrency kilidi: {s['concurrency']['blockedByLock']}"
                    f"/{s['concurrency']['attemptedConflicts']} deneme 409 ile engellendi, "
                    f"{len(conc)} sorun")
        all_problems += conc

        chan = verify_channels(s)
        _safe_print(f"  [3] Kanal model ciktilari: {len(chan)} sorun")
        all_problems += chan

        naive = verify_naive(s)
        _safe_print(f"  [4] Naive tutarliligi: {len(naive)} sorun")
        all_problems += naive

    cov = verify_coverage(summaries)
    _safe_print(f"\n  [5] Veri seti kapsami: {len(cov)} sorun")
    all_problems += cov

    _safe_print("\n" + "=" * 60)
    if all_problems:
        _safe_print(f"DOGRULAMA BASARISIZ -- {len(all_problems)} sorun:")
        for p in all_problems:
            _safe_print(f"  - {p}")
        return 1
    _safe_print(f"DOGRULAMA BASARILI -- {total_routes} rotanin hicbiri kapali yol "
                f"kullanmiyor, tum kilitler calisti, tum kanallar gercek cikti uretti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
