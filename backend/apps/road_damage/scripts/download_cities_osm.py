import os
import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
from pathlib import Path

# Configure osmnx
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.requests_timeout = 180

CITIES = {
    "Antakya (Hatay)": [36.20, 36.16],
    "Kahramanmaraş": [37.57, 36.93],
    "Gaziantep": [37.06, 37.38],
    "Malatya": [38.35, 38.30],
    "Adıyaman": [37.76, 38.27]
}

APP_DIR = Path(__file__).resolve().parents[1]
OSM_DATA_DIR = APP_DIR / "data" / "osm"
OSM_DATA_DIR.mkdir(parents=True, exist_ok=True)

def bbox_from_center(lat, lon, radius_km=10):
    # Roughly convert km to degrees
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(0.2, __import__('math').cos(__import__('math').radians(lat))))
    
    north = lat + lat_delta
    south = lat - lat_delta
    east = lon + lon_delta
    west = lon - lon_delta
    return (west, south, east, north)

all_roads = []
all_safety = []

tags = {
    "emergency": ["assembly_point"],
    "leisure": ["park", "garden"],
    "landuse": ["recreation_ground", "village_green", "grass"]
}

for city, (lat, lon) in CITIES.items():
    print(f"\n--- Downloading data for {city} ---")
    bbox = bbox_from_center(lat, lon, radius_km=15)
    
    try:
        print("Fetching road network...")
        G = ox.graph_from_bbox(bbox=bbox, network_type="walk", simplify=True)
        nodes, edges = ox.graph_to_gdfs(G)
        if not edges.empty:
            edges = edges.reset_index()
            all_roads.append(edges)
            print(f"Got {len(edges)} road segments.")
    except Exception as e:
        print(f"Failed to fetch roads for {city}: {e}")

    try:
        print("Fetching safety areas...")
        features = ox.features_from_bbox(bbox=bbox, tags=tags)
        if not features.empty:
            all_safety.append(features)
            print(f"Got {len(features)} safety areas.")
    except Exception as e:
        print(f"Failed to fetch safety areas for {city}: {e}")

print("\n--- Combining and saving data ---")

if all_roads:
    combined_roads = pd.concat(all_roads, ignore_index=True)
    expected_cols = ["osmid", "highway", "name", "oneway", "surface", "access", "foot", "geometry"]
    keep_cols = [c for c in expected_cols if c in combined_roads.columns]
    combined_roads = combined_roads[keep_cols]
    
    # Save to GPKG
    out_roads = OSM_DATA_DIR / "roads.gpkg"
    combined_roads.to_file(out_roads, layer="roads", driver="GPKG")
    print(f"Saved {len(combined_roads)} total road segments to {out_roads}")
else:
    print("No roads were downloaded.")

if all_safety:
    combined_safety = pd.concat(all_safety, ignore_index=True)
    combined_safety = combined_safety[combined_safety.geometry.notna()]
    
    expected_cols = ["osmid", "name", "emergency", "leisure", "landuse", "access", "operator", "geometry"]
    keep_cols = [c for c in expected_cols if c in combined_safety.columns]
    combined_safety = combined_safety[keep_cols]
    
    # Convert lists/dicts to strings for GeoJSON compatibility
    for col in combined_safety.columns:
        if combined_safety[col].apply(lambda x: isinstance(x, (list, dict))).any():
            combined_safety[col] = combined_safety[col].astype(str)
            
    out_safety = OSM_DATA_DIR / "safety_areas.geojson"
    combined_safety.to_file(out_safety, driver="GeoJSON")
    print(f"Saved {len(combined_safety)} total safety areas to {out_safety}")
else:
    print("No safety areas were downloaded.")
