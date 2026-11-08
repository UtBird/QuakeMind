from pathlib import Path
import math

import cv2
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd


APP_DIR = Path(__file__).resolve().parents[1]
OSM_DATA_DIR = APP_DIR / "data" / "osm"
SAFETY_AREAS_PATH = OSM_DATA_DIR / "safety_areas.geojson"
ROADS_PATH = OSM_DATA_DIR / "roads.gpkg"


def has_local_safety_dataset():
    return SAFETY_AREAS_PATH.exists()


def has_local_roads_dataset():
    return ROADS_PATH.exists()


def _clean_value(value):
    if value is None:
        return ""
    try:
        is_missing = pd.isna(value)
        if isinstance(is_missing, bool) and is_missing:
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _category_from_row(row):
    category = _clean_value(row.get("category"))
    if category:
        priority_val = row.get("priority")
        priority = int(priority_val) if priority_val is not None and not pd.isna(priority_val) else 1
        return category, priority

    emergency = _clean_value(row.get("emergency"))
    leisure = _clean_value(row.get("leisure"))
    landuse = _clean_value(row.get("landuse"))

    if "assembly_point" in emergency:
        return "OSM resmi toplanma alanı", 0
    if "park" in leisure or "garden" in leisure:
        return "Aday park/bahçe", 1
    if "recreation_ground" in landuse or "village_green" in landuse or "grass" in landuse:
        return "Aday açık alan", 2
    return "Aday açık alan", 2


def load_local_safety_areas(bbox=None, include_candidate_open_areas=True):
    if not SAFETY_AREAS_PATH.exists():
        return []

    gdf = gpd.read_file(SAFETY_AREAS_PATH, bbox=bbox)
    if gdf.empty or "geometry" not in gdf:
        return []

    records = []
    seen = set()
    for _, row in gdf[gdf.geometry.notna()].iterrows():
        category, priority = _category_from_row(row)
        if not include_candidate_open_areas and priority != 0:
            continue

        point = row.geometry.representative_point()
        lat = float(point.y)
        lon = float(point.x)
        name = (
            _clean_value(row.get("toplanma_alani"))
            or _clean_value(row.get("name"))
            or category
        )
        source = _clean_value(row.get("source")) or "Local OSM dataset"
        note = _clean_value(row.get("note"))

        dedupe_key = (round(lat, 6), round(lon, 6), name, category)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        records.append({
            "toplanma_alani": name,
            "lat": lat,
            "lon": lon,
            "display_lat": lat,
            "display_lon": lon,
            "category": category,
            "source": source,
            "note": note,
            "priority": priority,
        })

    records.sort(key=lambda item: (item["priority"], item["toplanma_alani"]))
    return records


def draw_local_road_mask(bounds, width, height, thickness=4):
    if not ROADS_PATH.exists():
        return None

    west, south, east, north = bounds
    road_img = np.zeros((height, width), dtype=np.uint8)
    try:
        roads = gpd.read_file(ROADS_PATH, bbox=(west, south, east, north))
    except Exception:
        return None

    if roads.empty or "geometry" not in roads:
        return road_img

    def project(lon, lat):
        px = int((lon - west) / (east - west) * width)
        py = int((north - lat) / (north - south) * height)
        return [px, py]

    for geom in roads.geometry.dropna():
        lines = []
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)

        for line in lines:
            pts = [project(lon, lat) for lon, lat in line.coords]
            if len(pts) >= 2:
                pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                cv2.polylines(road_img, [pts], False, 1, thickness=thickness)

    return road_img


def _haversine_m(lat1, lon1, lat2, lon2):
    radius_m = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bbox_from_points(user_lat, user_lon, dest_lat, dest_lon):
    lon_span = abs(user_lon - dest_lon)
    lat_span = abs(user_lat - dest_lat)
    padding = max(0.01, lon_span * 0.35, lat_span * 0.35)
    return (
        min(user_lon, dest_lon) - padding,
        min(user_lat, dest_lat) - padding,
        max(user_lon, dest_lon) + padding,
        max(user_lat, dest_lat) + padding,
    )


def _nearest_graph_node(graph, lat, lon, k_candidates=8):
    """En yakin graf dugumunu bulur (Backend perf madde 17 / _nearest_graph_node
    O(n) duzeltmesi). scipy cKDTree ile aday kume kuculttukten sonra sadece o
    adaylar icin tam haversine mesafesi hesaplanir -- sonuc O(n) taramayla
    birebir ayni (haversine ile secilen en yakin node), sadece cok daha hizli.
    Kucuk bir yerel alan (birkac km) icin derece-uzayi Oklit yakinligi ile
    gercek en yakin komsu arasindaki fark ihmal edilebilir; k_candidates>1
    kullanmak bu yaklaşıksama hatasina karsi ek guvenlik payi saglar."""
    nodes = list(graph.nodes(data=True))
    if not nodes:
        return None, float("inf")

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        best_node = None
        best_distance = float("inf")
        for node, data in nodes:
            distance = _haversine_m(lat, lon, data["lat"], data["lon"])
            if distance < best_distance:
                best_node = node
                best_distance = distance
        return best_node, best_distance

    node_ids = [n for n, _ in nodes]
    coords = np.array([[d["lat"], d["lon"]] for _, d in nodes])
    tree = cKDTree(coords)
    k = min(k_candidates, len(node_ids))
    _, idx = tree.query([lat, lon], k=k)
    idx = np.atleast_1d(idx)

    best_node = None
    best_distance = float("inf")
    for i in idx:
        node = node_ids[int(i)]
        data = graph.nodes[node]
        distance = _haversine_m(lat, lon, data["lat"], data["lon"])
        if distance < best_distance:
            best_node = node
            best_distance = distance
    return best_node, best_distance


def shortest_route_from_local_roads(user_lat, user_lon, dest_lat, dest_lon):
    if not ROADS_PATH.exists():
        return None, None, "Local yol dataset bulunamadı."

    bbox = _bbox_from_points(user_lat, user_lon, dest_lat, dest_lon)
    try:
        roads = gpd.read_file(ROADS_PATH, bbox=bbox)
    except Exception as exc:
        return None, None, str(exc)

    if roads.empty or "geometry" not in roads:
        return None, None, "Local yol dataset içinde bu alan için yol bulunamadı."

    graph = nx.Graph()

    def node_id(lon, lat):
        return (round(float(lon), 7), round(float(lat), 7))

    for geom in roads.geometry.dropna():
        lines = []
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)

        for line in lines:
            coords = list(line.coords)
            for start, end in zip(coords[:-1], coords[1:]):
                lon1, lat1 = start
                lon2, lat2 = end
                u = node_id(lon1, lat1)
                v = node_id(lon2, lat2)
                length = _haversine_m(lat1, lon1, lat2, lon2)
                graph.add_node(u, lat=float(lat1), lon=float(lon1))
                graph.add_node(v, lat=float(lat2), lon=float(lon2))
                if length > 0:
                    graph.add_edge(u, v, length=length)

    if graph.number_of_edges() == 0:
        return None, None, "Local yol graph boş."

    origin, origin_distance = _nearest_graph_node(graph, user_lat, user_lon)
    target, target_distance = _nearest_graph_node(graph, dest_lat, dest_lon)
    if origin is None or target is None:
        return None, None, "Başlangıç/hedef için en yakın yol düğümü bulunamadı."
    if origin_distance > 1000 or target_distance > 1000:
        return None, None, "Başlangıç veya hedef local yol ağına 1 km'den uzak."

    try:
        route = nx.shortest_path(graph, origin, target, weight="length")
    except Exception as exc:
        return None, None, str(exc)

    route_coords = [(graph.nodes[node]["lat"], graph.nodes[node]["lon"]) for node in route]
    route_length = 0.0
    for u, v in zip(route[:-1], route[1:]):
        route_length += graph.edges[u, v].get("length", 0)

    route_length += origin_distance + target_distance
    return route_coords, route_length, None
