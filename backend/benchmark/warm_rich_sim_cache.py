"""rich_simulation.py'nin kullanacagi radiusKm=3.0 sinirlarini onceden
pyrosm ile yerel PBF'ten cikarip cache'ler -- boylece canli calisirken
Overpass'a hic gidilmez (bkz. warm_local_graph_cache.py, ayni desen).

network_type='walk': /api/road_damage/simulate_closures artik 'walk'
kullaniyor (arac-yollari-disi -- yaya sokagi/ara yol -- kapsamini da
almak icin, bkz. fastapi_app.py::simulate_road_closures)."""
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from apps.road_damage.utils.assembly import bbox_from_center
from apps.road_damage.utils.network import build_local_graph_from_pbf, load_local_graph_from_cache

CENTERS = {
    "kahramanmaras": (37.5756, 36.9207),
    "hatay": (36.194057, 36.146939),
}
RADIUS_KM = 3.0

for name, (lat, lon) in CENTERS.items():
    bbox = bbox_from_center(lat, lon, RADIUS_KM)
    print(f"[{name}] bbox={bbox}")
    existing = load_local_graph_from_cache(bbox, network_type="walk")
    if existing is not None:
        print(f"  zaten cache'te -- {existing.number_of_nodes()} dugum.")
        continue
    t0 = time.time()
    print("  PBF'ten cikariliyor (dakikalar surebilir)...")
    G = build_local_graph_from_pbf(bbox, network_type="walk", cache=True)
    print(f"  OK -- {G.number_of_nodes()} dugum, {G.number_of_edges()} kenar cache'lendi ({time.time()-t0:.0f}s).")
