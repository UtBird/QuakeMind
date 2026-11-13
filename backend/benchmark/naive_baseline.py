"""'Bizim motorumuz olmasaydi' karsilastirmasi: naive ajan simulasyonu.

pipeline_runner.py bir calismayi (run) gercek API'lere karsi calistirip
benchmark/runs/<run_id>/summary.json'a yazdiktan sonra bu script:

  1. Her mahalle icin GERCEK bir OSMnx yol grafi kurar (ayni
     apps/road_damage/utils/network.py::analyze_road_network_graph'in
     kullandigi ox.graph_from_bbox cagrisi).
  2. Copernicus EMSR648 gercek hasar zemin dogrulamasindaki (senaryonun
     closedRoadGroundTruth listesi) kapali yollari bu grafta en yakin
     kenarlara esler ve "gercekte kapali" olarak isaretler.
  3. Her ekip-hedef atamasi icin bir "naive ajan" simule eder: kapali
     yolu SADECE oraya varinca kesfeder (bilmeden en kisa yoldan gitmeye
     calisir), kesfedince bir onceki kavsaktan bilinen kapali yollari
     eleyerek yeniden en kisa yolu hesaplar -- bu, sahadaki gercek
     "yani gidip donme" davranisinin sadelestirilmis ama savunulabilir bir
     modeli (kesif anindaki israf edilen mesafe sifir kabul edilir --
     yani naive ajanin lehine bir varsayim, karsilastirmayi abartmiyoruz).
  4. Naive mesafeyi, pipeline_runner'in ZATEN GERCEK GNN motorundan aldigi
     distanceMeters ile karsilastirir -- "bizim motor" tarafi icin ayrica
     bir simulasyon YAPILMAZ, gercek canli sonuc kullanilir.

Sure tahmini icin sabit bir ortalama saha hizi varsayilir (asagida
AVERAGE_SPEED_KMH) -- bu acikca belirtilen, tartisilabilir bir varsayimdir,
rapor bunu acikca not eder.

Kullanim:
  python benchmark/naive_baseline.py benchmark/runs/<run_id>
"""

import argparse
import json
import sys
from pathlib import Path

import networkx as nx
import osmnx as ox

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = Path(__file__).resolve().parent / "data"

ox.settings.use_cache = True
ox.settings.requests_timeout = 30

EDGE_MATCH_RADIUS_M = 60.0  # copernicus hasarli yol noktasi <-> osmnx kenari eslestirme esigi
AVERAGE_SPEED_KMH = 15.0    # afet sonrasi molozlu sokakta ortalama saha ilerleme hizi varsayimi
MAX_NAIVE_ITERATIONS = 60

# Naive ajan kapali bir yola VARDIGINDA kaybettigi sure. AVERAGE_SPEED_KMH
# gibi ACIKCA BELIRTILEN, tartisilabilir bir varsayimdir ve raporda oyle
# gosterilir. Sadece yol uzunlugundan gelen fark, sahadaki gercek maliyeti
# eksik anlatiyor: ekip molozla karsilasinca duruyor, durumu degerlendiriyor,
# arac cevirecek yer ariyor ve telsizle merkeze bildiriyor. Senaryo
# spesifikasyonunda bu 15-25 dk araligi olarak veriliyor; ortasi alindi.
#
# ONEMLI: bu ceza SADECE naive (klasik navigasyon) tarafina uygulanir --
# bizim motorumuz kapali yola hic varmadigi icin boyle bir kaybi yoktur.
# Cezayi 0 yaparak kapatmak, karsilastirmayi salt mesafe farkina indirger.
U_TURN_PENALTY_MIN = 20.0


def naive_time_minutes(distance_m: float, discoveries: int | None) -> float:
    """Klasik navigasyonun toplam intikal suresi: yol suresi + her kapali-yol
    kesfi icin U-donusu cezasi."""
    travel_min = distance_m / 1000.0 / AVERAGE_SPEED_KMH * 60.0
    return travel_min + (discoveries or 0) * U_TURN_PENALTY_MIN


def _haversine_m(lat1, lon1, lat2, lon2):
    import math
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_graph(bounds: dict) -> "nx.MultiDiGraph":
    bbox = (bounds["west"], bounds["south"], bounds["east"], bounds["north"])
    G = ox.graph_from_bbox(bbox=bbox, network_type="drive", simplify=True)
    return G


def _edge_midpoint(G, u, v, key):
    data = G[u][v][key]
    if "geometry" in data:
        pt = data["geometry"].interpolate(0.5, normalized=True)
        return pt.y, pt.x
    n1, n2 = G.nodes[u], G.nodes[v]
    return (n1["y"] + n2["y"]) / 2, (n1["x"] + n2["x"]) / 2


def mark_ground_truth_closures(G, closed_roads: list[dict]) -> set:
    """Copernicus hasarli yol noktalarina EDGE_MATCH_RADIUS_M icinde olan
    kenarlari 'gercekte kapali' olarak isaretler, (u,v,key) kumesi doner."""
    closed_points = [(r["lat"], r["lon"]) for r in closed_roads]
    if not closed_points:
        return set()

    closed_edges = set()
    for u, v, key in G.edges(keys=True):
        mlat, mlon = _edge_midpoint(G, u, v, key)
        for clat, clon in closed_points:
            if _haversine_m(mlat, mlon, clat, clon) <= EDGE_MATCH_RADIUS_M:
                closed_edges.add((u, v, key))
                closed_edges.add((v, u, key))
                break
    return closed_edges


# simulate_naive_agent artik apps/road_damage/utils/network.py'de tanimli --
# backend'in KENDI SURECINDE (session'daki gercek G ile) cagirabilmesi icin
# tasindi (bkz. o dosyadaki fonksiyonun docstring'i: ayri surecler arasi
# simulate_random_closures determinizm sorunu). Burada geriye-donuk uyumluluk
# icin import ediliyor.
from apps.road_damage.utils.network import simulate_naive_agent  # noqa: E402,F401


def run_for_run_dir(run_dir: Path) -> dict:
    with open(run_dir / "summary.json", encoding="utf-8") as f:
        summary = json.load(f)

    region = summary["region"]
    road_damage_results = summary["roadDamageResults"]

    graph_cache: dict[str, "nx.MultiDiGraph"] = {}
    closed_edges_cache: dict[str, set] = {}

    comparisons = {}
    for severity, sev_data in summary["severities"].items():
        closed_roads = sev_data["closedRoadGroundTruth"]
        rows = []
        for assignment in sev_data["assignments"]:
            mahalle = assignment["mahalle"]
            rd = road_damage_results.get(mahalle)
            if rd is None or assignment.get("distanceMeters") is None:
                continue

            if mahalle not in graph_cache:
                print(f"  [{mahalle}] OSMnx grafi kuruluyor...")
                graph_cache[mahalle] = build_graph(rd["bounds"])
                closed_edges_cache[mahalle] = mark_ground_truth_closures(graph_cache[mahalle], closed_roads)
                print(f"  [{mahalle}] {len(closed_edges_cache[mahalle])//2} gercek kapali kenar eslesti.")

            G = graph_cache[mahalle]
            real_closed = closed_edges_cache[mahalle]

            route_coords = assignment["routeCoords"] or []
            if not route_coords:
                continue
            start_lat, start_lon = route_coords[0]
            end_lat, end_lon = route_coords[-1]

            naive = simulate_naive_agent(G, real_closed, start_lat, start_lon, end_lat, end_lon)
            our_distance = assignment["distanceMeters"]

            row = {
                "teamId": assignment["teamId"], "victimId": assignment["victimId"], "mahalle": mahalle,
                "ourEngineDistanceMeters": our_distance,
                "naiveDistanceMeters": naive["distanceMeters"] if naive else None,
                "naiveDiscoveries": naive["discoveries"] if naive else None,
                "naiveUnreachable": naive is None,
                "ourEngineTimeMin": round(our_distance / 1000 / AVERAGE_SPEED_KMH * 60, 1),
            }
            if naive is not None:
                row["distanceSavedMeters"] = round(naive["distanceMeters"] - our_distance, 1)
                row["naiveTravelOnlyTimeMin"] = round(
                    naive["distanceMeters"] / 1000 / AVERAGE_SPEED_KMH * 60, 1)
                row["naiveUTurnPenaltyMin"] = round(
                    (naive["discoveries"] or 0) * U_TURN_PENALTY_MIN, 1)
                row["naiveTimeMin"] = round(
                    naive_time_minutes(naive["distanceMeters"], naive["discoveries"]), 1)
                row["timeSavedMin"] = round(row["naiveTimeMin"] - row["ourEngineTimeMin"], 1)
            rows.append(row)

        # Iki ayri kategori var, birbirine karistirilmamali:
        #  - "reachable": naive ajan da (daha yavas/dolambacli da olsa) hedefe
        #    ulasabildi -- burada dakika cinsinden bir "kazanc" karsilastirmasi
        #    anlamli.
        #  - "naive_stuck": naive ajan, gercekte kapali yollari bilmeden
        #    ilerlerken mahalle olcekli yol grafiginde COZULEMEYEN bir noktaya
        #    sikisti (grafik gercek kapanmalarla parcalandi). Bu ortalamadan
        #    sessizce cikarilacak bir "eksik veri" degil -- bizim sistemin
        #    hedefe ULASTIGI, naive yaklasimin ise HIC ULASAMADIGI acik bir
        #    basari vakasi. Ayri ve one cikan bir kategori olarak raporlanir.
        reachable = [r for r in rows if not r["naiveUnreachable"]]
        naive_stuck = [r for r in rows if r["naiveUnreachable"]]
        total_saved_min = sum(r["timeSavedMin"] for r in reachable)
        comparisons[severity] = {
            "assignmentCount": len(rows),
            "reachableByNaiveCount": len(reachable),
            "naiveStuckCount": len(naive_stuck),
            "naiveStuckOurEngineTimeMin": [r["ourEngineTimeMin"] for r in naive_stuck],
            "totalTimeSavedMin": round(total_saved_min, 1),
            "avgTimeSavedMinPerTeam": round(total_saved_min / len(reachable), 1) if reachable else None,
            "rows": rows,
        }

    result = {
        "runId": summary["runId"], "region": region,
        "averageSpeedKmhAssumption": AVERAGE_SPEED_KMH,
        "uTurnPenaltyMinAssumption": U_TURN_PENALTY_MIN,
        "edgeMatchRadiusM": EDGE_MATCH_RADIUS_M,
        "comparisons": comparisons,
    }
    out_path = run_dir / "naive_baseline_comparison.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"-> {out_path}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_for_run_dir(args.run_dir)


if __name__ == "__main__":
    main()
