"""
ALAN 06 - Kapanma-farkinda rota.  Burada MODEL degil, ALGORITMA kiyaslanir.

Bizim yontem: yerel OSM PBF grafi uzerinde A* / Dijkstra; hasar iki yoldan
girer -> (1) tikanikligin 25 m yaricapinda sert kapatma, (2) hasar
noktalarina yakinliga gore kenar agirligi cezasi. Kapanma yolun iki yonunu
birden kapatir. Taban: kapanmalari bilmeyen naif ajan.

Metrikler: seyahat suresi, mesafe, basarisiz rota orani, hesap suresi,
erisilebilirlik orani + 80/80 siniri + rota degisim orani.

VERI:
  - Geofabrik Turkiye OSM PBF        -> yol grafi (mevcut kaynagimiz)
  - Copernicus EMSR648 (depoda hazir) -> kapanma zemin dogrulugu
  - HOT OSM 2023 Turkiye             -> ucuncu kapanma kaynagi
"""
from pathlib import Path
import json
import time

import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"
REPO = HERE.parent.parent

CONFIG = {
    # PBF: Geofabrik'ten indir ya da depodaki backend yolunu goster
    "osm_pbf": str(REPO / "backend" / "apps" / "road_damage" / "data" / "osm" / "turkey.osm.pbf"),
    "place": "Antakya, Hatay, Turkey",       # veya "Kahramanmaras, Turkey"
    "closures_geojson": str(REPO / "backend" / "apps" / "road_damage" / "data" / "osm" / "safety_areas.geojson"),
    "emsr648_dir": None,                       # Copernicus EMSR648 vektor klasoru
    "hard_close_radius_m": 25.0,
    "penalty_radius_m": 150.0,
    "penalty_factor": 5.0,
    "n_od_pairs": 120,                         # senaryo: Antakya 126, Maras 35
    "seed": 42,
}


# --- Graf yukleme -------------------------------------------------

def load_graph(cfg=CONFIG):
    """OSM -> networkx DiGraph (osmnx tercih; yoksa pyrosm)."""
    place = cfg["place"]
    try:
        import osmnx as ox
        pbf = Path(cfg["osm_pbf"])
        if pbf.exists():
            # yerel PBF'den (offline)
            import pyrosm
            osm = pyrosm.OSM(str(pbf), bounding_box=None)
            nodes, edges = osm.get_network(nodes=True, network_type="driving")
            G = osm.to_graph(nodes, edges, graph_type="networkx")
        else:
            G = ox.graph_from_place(place, network_type="drive")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        return G
    except Exception as e:
        raise RuntimeError(
            f"Graf yuklenemedi ({e}). `pip install osmnx pyrosm` ve CONFIG['osm_pbf'] / place kontrol."
        )


def load_closures(cfg=CONFIG):
    """Kapanma noktalarini [(lat, lon), ...] olarak dondur."""
    p = Path(cfg["closures_geojson"])
    if not p.exists():
        raise FileNotFoundError(f"Kapanma dosyasi yok: {p}")
    gj = json.load(open(p))
    pts = []
    for feat in gj.get("features", []):
        g = feat.get("geometry", {})
        if g.get("type") == "Point":
            lon, lat = g["coordinates"][:2]
            pts.append((lat, lon))
        elif g.get("type") in ("Polygon", "MultiPolygon"):
            coords = np.array(g["coordinates"]).reshape(-1, 2)
            pts.append((coords[:, 1].mean(), coords[:, 0].mean()))
    return pts


# --- Hasar -> graf --------------------------------------------

def apply_damage(G, closures, cfg=CONFIG, mode="full"):
    """mode: 'none'(naif) | 'hard'(sadece kapatma) | 'soft'(sadece ceza) | 'full'(ikisi).
    Yeni bir kopyada calisir, kenarlarin 'weight' alanini gunceller.
    """
    import networkx as nx
    H = G.copy()
    for u, v, k, d in H.edges(keys=True, data=True):
        d["weight"] = d.get("travel_time", d.get("length", 1.0))

    if mode == "none" or not closures:
        return H

    from math import radians, sin, cos, asin, sqrt

    def hav(a, b):
        R = 6371000.0
        dlat, dlon = radians(b[0]-a[0]), radians(b[1]-a[1])
        h = sin(dlat/2)**2 + cos(radians(a[0]))*cos(radians(b[0]))*sin(dlon/2)**2
        return 2*R*asin(sqrt(h))

    hard_r, soft_r, fac = cfg["hard_close_radius_m"], cfg["penalty_radius_m"], cfg["penalty_factor"]
    for u, v, k, d in H.edges(keys=True, data=True):
        mid = (H.nodes[u]["y"]/2 + H.nodes[v]["y"]/2, H.nodes[u]["x"]/2 + H.nodes[v]["x"]/2)
        dmin = min((hav(mid, c) for c in closures), default=1e9)
        if mode in ("hard", "full") and dmin <= hard_r:
            d["weight"] = float("inf")
        elif mode in ("soft", "full") and dmin <= soft_r:
            d["weight"] *= 1 + (fac - 1) * (1 - dmin / soft_r)
    return H


# --- OD ciftleri + rota ------------------------------------------

def sample_od_pairs(G, n, seed=42):
    rng = np.random.default_rng(seed)
    nodes = list(G.nodes)
    return [(int(rng.choice(nodes)), int(rng.choice(nodes))) for _ in range(n)]


def route_once(G, s, t, algo="astar"):
    import networkx as nx
    try:
        t0 = time.perf_counter()
        if algo == "dijkstra":
            path = nx.dijkstra_path(G, s, t, weight="weight")
        elif algo == "bidirectional":
            _, path = nx.bidirectional_dijkstra(G, s, t, weight="weight")
        else:  # astar
            def h(a, b):
                return 0.0
            path = nx.astar_path(G, s, t, heuristic=h, weight="weight")
        dt = time.perf_counter() - t0
        tt = sum(G[u][v][0].get("travel_time", 0) for u, v in zip(path[:-1], path[1:]) if G.has_edge(u, v))
        dist = sum(G[u][v][0].get("length", 0) for u, v in zip(path[:-1], path[1:]) if G.has_edge(u, v))
        return {"ok": True, "path": path, "compute_s": dt, "travel_time_s": tt, "distance_m": dist}
    except Exception:
        return {"ok": False, "compute_s": None, "travel_time_s": None, "distance_m": None}


def evaluate_routes(G, od_pairs, algo="astar", baseline_paths=None):
    res = [route_once(G, s, t, algo) for s, t in od_pairs]
    ok = [r for r in res if r["ok"]]
    fail_rate = 1 - len(ok) / len(res)
    out = {
        "n_pairs": len(res),
        "failed_route_rate": fail_rate,
        "accessibility_ratio": len(ok) / len(res),
        "mean_travel_time_s": float(np.mean([r["travel_time_s"] for r in ok])) if ok else float("nan"),
        "mean_distance_m": float(np.mean([r["distance_m"] for r in ok])) if ok else float("nan"),
        "mean_compute_s": float(np.mean([r["compute_s"] for r in ok])) if ok else float("nan"),
        "p95_compute_s": float(np.percentile([r["compute_s"] for r in ok], 95)) if ok else float("nan"),
    }
    if baseline_paths is not None:
        changed = sum(1 for r, b in zip(res, baseline_paths)
                      if r["ok"] and b and r["path"] != b)
        out["route_change_rate"] = changed / max(1, len(res))
    return out, res


def accessibility_80_80(G, closures, od_pairs, cfg=CONFIG, levels=(0.0, 0.1, 0.2, 0.3, 0.5)):
    """Bozulma seviyesi arttikca erisilebilirligi olc. 80/80: olaylarin %80'ine
    erisimin %80 olasilikla korundugu bozulma seviyesi."""
    rng = np.random.default_rng(cfg["seed"])
    curve = []
    for lvl in levels:
        sub = closures if lvl == 0 else [c for c in closures if rng.random() < (0.2 + lvl)]
        H = apply_damage(G, sub, cfg, mode="full")
        m, _ = evaluate_routes(H, od_pairs, "astar")
        curve.append((lvl, m["accessibility_ratio"]))
    passed = [lvl for lvl, acc in curve if acc >= 0.8]
    return {"curve": curve, "max_disruption_at_80pct_access": max(passed) if passed else 0.0}


def save_result(name, metrics, extra=None):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    full = {"method": name, **metrics}
    if extra:
        full["extra"] = extra
    json.dump(full, open(RESULTS_DIR / f"{name}.json", "w"), indent=2)
    import pandas as pd
    rows = [json.load(open(f)) for f in sorted(RESULTS_DIR.glob("*.json"))]
    lb = pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, (dict, list))} for r in rows])
    lb.to_csv(RESULTS_DIR / "leaderboard.csv", index=False)
    return lb
