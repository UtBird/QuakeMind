"""Pure helpers for turning road-network geometry into JSON-friendly shapes.

No torch/osmnx/cv2 imports here on purpose -- this module needs to stay
lightweight enough to import from apps/road_damage/worker.py (a
ProcessPoolExecutor worker entrypoint) without dragging in heavy deps.
"""
import math


def compact_segment_coords(line, max_points=28):
    """Serialize a shapely LineString to compact [[lat, lon], ...] payload."""
    coords = list(getattr(line, "coords", []))
    if len(coords) < 2:
        return None
    if len(coords) <= max_points:
        sampled = coords
    else:
        stride = max(1, len(coords) // max_points)
        sampled = coords[::stride]
        if sampled[-1] != coords[-1]:
            sampled.append(coords[-1])
    return [[float(lat), float(lon)] for lon, lat in sampled]


# Bir sehrin 3km yaricapli TAM yaya+arac yol agi ~50.000 kenar surer ve
# ~2.3MB JSON eder (olculdu: Kahramanmaras 49.666 kenar, Hatay 40.950) --
# yani tam kapsama tasinabilir bir yuk. Onceki 8000'lik sinir, grafin
# yalnizca ilk ~%16'sini gonderdigi icin haritada yollarin cogu HIC
# renklendirilmemis (ne yesil ne kirmizi) kaliyordu. Sinir yine de bir
# guvenlik supabi olarak duruyor, sadece gercek sehir grafiklerini
# kapsayacak kadar yuksek.
def serialize_segments(edges, max_segments=120000):
    if not edges:
        return []
    serialized = []
    for _, _, _, line in edges[:max_segments]:
        compact = compact_segment_coords(line)
        if compact:
            serialized.append(compact)
    return serialized


def haversine_m(lat1, lon1, lat2, lon2):
    radius_m = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
