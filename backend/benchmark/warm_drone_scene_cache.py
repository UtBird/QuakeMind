"""Drone sahneleri senaryosunun yol grafi onbellegini hazirlar.

Her sahnenin grafi, ust bolgesinin (Senaryo v2: H-Z1 / K-Z1) onbellekteki
3 km'lik YAYA grafinin sahne kapsama kutusuna kirpilmis halidir -- yeni bir
OSM cikarimi yapilmaz, Overpass'a gidilmez; iki senaryo birebir ayni OSM
verisini kullanir. Kirpilmis graf, /closures_from_mask ve /simulate_closures
uc noktalarinin sahne kutusu (bbox) icin arayacagi anahtarla yazilir.

    python benchmark/warm_drone_scene_cache.py
"""
import pickle
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "benchmark"))

import networkx as nx  # noqa: E402

from apps.road_damage.utils.assembly import bbox_from_center  # noqa: E402
from apps.road_damage.utils.network import (  # noqa: E402
    LOCAL_GRAPH_CACHE_DIR, _local_graph_cache_path, load_local_graph_from_cache,
)
import scenario_dataset as V2  # noqa: E402
import scenario_dataset_drone as DRONE  # noqa: E402

NETWORK_TYPE = "walk"   # Senaryo v2 ile ayni ag turu


def main():
    parents = {}
    ok = True
    for zone in DRONE.ZONES:
        pid = zone["parentZoneId"]
        if pid not in parents:
            pz = V2.ZONES_BY_ID[pid]
            pbox = bbox_from_center(pz["center"][0], pz["center"][1], pz["radiusKm"])
            G = load_local_graph_from_cache(pbox, NETWORK_TYPE)
            if G is None:
                print(f"HATA: ust bolge {pid} grafi onbellekte yok -- once "
                      f"benchmark/warm_scenario_v2_cache.py calistirin.")
                ok = False
                continue
            parents[pid] = (G, pbox)
        G, pbox = parents[pid]

        w, s, e, n = zone["bbox"]
        if not (pbox[0] <= w and e <= pbox[2] and pbox[1] <= s and n <= pbox[3]):
            print(f"HATA: {zone['id']} sahnesi ust bolge {pid} grafinin disina tasiyor.")
            ok = False
            continue

        keep = [u for u, d in G.nodes(data=True) if w <= d["x"] <= e and s <= d["y"] <= n]
        H = G.subgraph(keep).copy()
        scc = max(nx.strongly_connected_components(H), key=len) if H.number_of_nodes() else ()

        path = _local_graph_cache_path(tuple(zone["bbox"]), NETWORK_TYPE)
        LOCAL_GRAPH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(H, f)
        print(f"{zone['id']:5} {zone['label']:44} {H.number_of_nodes():4d} dugum / "
              f"{H.number_of_edges():4d} kenar (guclu-bagli cekirdek {len(scc)}) -> {path.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
