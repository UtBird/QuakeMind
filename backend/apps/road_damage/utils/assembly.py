"""Assembly-area (toplanma alani) search + nearest-route helpers.

Pure-python port of the logic that used to live only in the Streamlit
prototype (`apps/road_damage/app.py`, assembly_tab). No Streamlit
dependency here so it can be called directly from the FastAPI backend.
"""
import math
from functools import lru_cache

import networkx as nx
import osmnx as ox
import pandas as pd


def haversine_m(lat1, lon1, lat2, lon2):
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


def bbox_from_center(lat, lon, radius_km):
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.2))
    return (
        lon - lon_delta,
        lat - lat_delta,
        lon + lon_delta,
        lat + lat_delta,
    )


def clean_osm_value(value):
    if value is None:
        return ""
    try:
        is_missing = pd.isna(value)
        if isinstance(is_missing, bool) and is_missing:
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


@lru_cache(maxsize=64)
def fetch_osm_safety_areas(bbox, include_candidate_open_areas):
    """bbox: (west, south, east, north) tuple. Returns (records, error)."""
    tags = {"emergency": "assembly_point"}
    if include_candidate_open_areas:
        tags.update({
            "leisure": ["park", "garden"],
            "landuse": ["recreation_ground", "village_green", "grass"],
        })

    try:
        features = ox.features_from_bbox(bbox, tags)
    except Exception as exc:
        return [], str(exc)

    if features is None or features.empty or "geometry" not in features:
        return [], None

    features = features[features.geometry.notna()].copy()
    features = features[
        features.geometry.geom_type.isin(["Point", "MultiPoint", "Polygon", "MultiPolygon"])
    ]

    records = []
    seen = set()
    for _, row in features.iterrows():
        access = clean_osm_value(row.get("access")).lower()
        if access in {"private", "no"}:
            continue

        emergency = clean_osm_value(row.get("emergency"))
        leisure = clean_osm_value(row.get("leisure"))
        landuse = clean_osm_value(row.get("landuse"))
        is_official = emergency == "assembly_point"

        if is_official:
            category = "OSM resmi toplanma alani"
            priority = 0
        elif leisure in {"park", "garden"}:
            category = "Aday park/bahce"
            priority = 1
        elif landuse in {"recreation_ground", "village_green", "grass"}:
            category = "Aday acik alan"
            priority = 2
        else:
            continue

        point = row.geometry.representative_point()
        lat = float(point.y)
        lon = float(point.x)
        name = clean_osm_value(row.get("name")) or category
        note_parts = []
        if emergency:
            note_parts.append(f"emergency={emergency}")
        if leisure:
            note_parts.append(f"leisure={leisure}")
        if landuse:
            note_parts.append(f"landuse={landuse}")

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
            "source": "OpenStreetMap",
            "note": " | ".join(note_parts),
            "priority": priority,
        })

    records.sort(key=lambda item: (item["priority"], item["toplanma_alani"]))
    return records, None


def find_nearest_assembly(user_lat, user_lon, records):
    nearest = None
    nearest_distance = float("inf")
    for item in records:
        lat = item.get("display_lat", item["lat"])
        lon = item.get("display_lon", item["lon"])
        distance = haversine_m(user_lat, user_lon, lat, lon)
        if distance < nearest_distance:
            nearest = item
            nearest_distance = distance
    return nearest, nearest_distance


def shortest_walk_route(user_lat, user_lon, dest_lat, dest_lon):
    lon_span = abs(user_lon - dest_lon)
    lat_span = abs(user_lat - dest_lat)
    padding = max(0.01, lon_span * 0.25, lat_span * 0.25)
    bbox = (
        min(user_lon, dest_lon) - padding,
        min(user_lat, dest_lat) - padding,
        max(user_lon, dest_lon) + padding,
        max(user_lat, dest_lat) + padding,
    )

    try:
        graph = ox.graph_from_bbox(bbox, network_type="walk", simplify=True)
        origin = ox.distance.nearest_nodes(graph, X=user_lon, Y=user_lat)
        target = ox.distance.nearest_nodes(graph, X=dest_lon, Y=dest_lat)
        route = nx.shortest_path(graph, origin, target, weight="length")
    except Exception as exc:
        return None, None, str(exc)

    route_coords = [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in route]
    route_length = 0.0
    for u, v in zip(route[:-1], route[1:]):
        edge_options = graph.get_edge_data(u, v, default={})
        if edge_options:
            route_length += min(edge.get("length", 0) for edge in edge_options.values())

    return route_coords, route_length, None
