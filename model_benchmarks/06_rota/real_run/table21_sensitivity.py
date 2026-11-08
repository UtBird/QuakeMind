"""
Tablo 21, satir 4-5 (Sert kapatma yaricapi r_h, Ceza basamaklari lambda(d))
icin parametre duyarlilik taramasi.

Uretim kodundaki (backend/apps/road_damage/utils/network.py)
apply_risk_penalties/risk_weight fonksiyonlarini BIREBIR kullanir; hasar
noktalari olarak H-Z1 (Antakya) bolgesindeki gercek EMSR648 (orta kural)
kapali kenarlarinin orta noktalari verilir (make_figure10.py ile ayni
kapanma kumesi). 6 OD cifti x 3 tohum (42, 43, 44) icin ortalama ulasim
suresi (v_ort=15 km/sa, Tablo 12'deki varsayimla) raporlanir.

r_h taramasi: varsayilan lambda(d) ile r_h in {10, 25, 50, 100} m.
lambda(d) taramasi: varsayilan r_h=25m ile, adim fonksiyonunun 1.0'in
  USTUNDEKI kismi bir ölçek çarpanıyla küçültülüp büyütülür:
  agirlik(d) = 1 + olcek * (risk_weight(d) - 1), olcek in {0.5, 1, 2}.
  (olcek=1 -> uretim kodundaki degerlerle birebir ayni: 3.0/1.5/1.1/1.0)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))

from scenario import load_district
from emsr648_closures import closed_osm_edges
from assignment import build_victims_and_teams, run_algorithm3

from apps.road_damage.utils.network import risk_weight, haversine

CODE = "H-Z1"
AOI = "AOI11"
RULE = "medium"
SEEDS = [42, 43, 44]
V_ORT_KMH = 15.0
OUT_PATH = Path(__file__).resolve().parent / "results" / "table21_sensitivity.json"


def edge_midpoint(G, u, v, data):
    if "geometry" in data:
        coords = list(data["geometry"].coords)
        mid_lon, mid_lat = coords[len(coords) // 2]
        return mid_lat, mid_lon
    return (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2.0, (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2.0


def build_damage_points(G, closed_set):
    pts = []
    for (u, v, k) in closed_set:
        if G.has_edge(u, v, k):
            data = G[u][v][k]
            pts.append(edge_midpoint(G, u, v, data))
    return pts


def apply_penalties(G, damage_points, *, hard_r=25.0, scale=1.0):
    """apply_risk_penalties'in ayni mantigi, r_h ve olcek parametreli."""
    import networkx as nx
    H = G.copy()
    to_remove = []
    for u, v, k, data in H.edges(keys=True, data=True):
        mid_lat, mid_lon = edge_midpoint(H, u, v, data)
        min_dist = min((haversine(mid_lat, mid_lon, dlat, dlon) for dlat, dlon in damage_points),
                       default=float("inf"))
        if min_dist <= hard_r:
            to_remove.append((u, v, k))
            continue
        length = data.get("length", 0.0)
        w = risk_weight(min_dist)
        w_scaled = 1.0 + scale * (w - 1.0)
        data["risk_cost"] = length * w_scaled
    for (u, v, k) in to_remove:
        if H.has_edge(u, v, k):
            H.remove_edge(u, v, k)
    return H


def route_time_min(H, s, t):
    import networkx as nx
    try:
        path = nx.shortest_path(H, s, t, weight="risk_cost")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    dist_m = 0.0
    for u, v in zip(path[:-1], path[1:]):
        key = min(H[u][v], key=lambda kk: H[u][v][kk].get("length", float("inf")))
        dist_m += H[u][v][key].get("length", 0.0)
    return dist_m / (V_ORT_KMH * 1000.0 / 60.0)


def mean_std(xs):
    import numpy as np
    a = np.array(xs, dtype=float)
    return float(a.mean()), float(a.std())


def main():
    dg = load_district(CODE)
    G = dg.G
    closed_set = closed_osm_edges(G, AOI, RULE)
    damage_points = build_damage_points(G, closed_set)
    print(f"graf: {G.number_of_nodes()} dugum; kapali kenar: {len(closed_set)}; "
          f"hasar noktasi: {len(damage_points)}")

    od_pairs_by_seed = {}
    for seed in SEEDS:
        victims, teams = build_victims_and_teams(G, 6, seed)
        assignments, _lock = run_algorithm3(G, victims, teams)
        od_pairs_by_seed[seed] = [(t["hq_node"], v["node"]) for (t, v, _r) in assignments]

    results = {"r_h_sweep": {}, "lambda_sweep": {}}

    for hard_r in (10.0, 25.0, 50.0, 100.0):
        times, n_unreachable, n_removed = [], 0, None
        for seed in SEEDS:
            H = apply_penalties(G, damage_points, hard_r=hard_r, scale=1.0)
            if n_removed is None:
                n_removed = G.number_of_edges() - H.number_of_edges()
            for (s, t) in od_pairs_by_seed[seed]:
                tmin = route_time_min(H, s, t)
                if tmin is None:
                    n_unreachable += 1
                else:
                    times.append(tmin)
        mean_t, std_t = mean_std(times) if times else (float("nan"), float("nan"))
        results["r_h_sweep"][hard_r] = {
            "mean_time_min": mean_t, "std_time_min": std_t,
            "n_unreachable": n_unreachable, "n_total": len(SEEDS) * 6,
            "n_edges_removed": n_removed,
        }
        print(f"r_h={hard_r:>5.0f} m: T={mean_t:.2f}±{std_t:.2f} dk, "
              f"ulasilamayan={n_unreachable}/{len(SEEDS)*6}, kaldirilan_kenar={n_removed}")

    for scale in (0.5, 1.0, 2.0):
        times, n_unreachable = [], 0
        for seed in SEEDS:
            H = apply_penalties(G, damage_points, hard_r=25.0, scale=scale)
            for (s, t) in od_pairs_by_seed[seed]:
                tmin = route_time_min(H, s, t)
                if tmin is None:
                    n_unreachable += 1
                else:
                    times.append(tmin)
        mean_t, std_t = mean_std(times) if times else (float("nan"), float("nan"))
        results["lambda_sweep"][scale] = {
            "mean_time_min": mean_t, "std_time_min": std_t,
            "n_unreachable": n_unreachable, "n_total": len(SEEDS) * 6,
        }
        print(f"lambda_olcek={scale:.1f}: T={mean_t:.2f}±{std_t:.2f} dk, "
              f"ulasilamayan={n_unreachable}/{len(SEEDS)*6}")

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"yazildi -> {OUT_PATH}")


if __name__ == "__main__":
    main()
