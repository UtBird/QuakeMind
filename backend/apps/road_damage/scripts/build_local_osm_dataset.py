#!/usr/bin/env python3
"""
Build local OSM datasets for the road damage app.

Input:
  data/osm/turkey-latest.osm.pbf or a custom .osm.pbf path

Outputs:
  data/osm/safety_areas.geojson
  data/osm/roads.gpkg
"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


APP_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = APP_DIR / "data" / "osm"


def clean_value(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def classify_area(row):
    emergency = clean_value(row.get("emergency"))
    leisure = clean_value(row.get("leisure"))
    landuse = clean_value(row.get("landuse"))

    if emergency == "assembly_point":
        return "OSM resmi toplanma alanı", 0
    if leisure in {"park", "garden"}:
        return "Aday park/bahçe", 1
    if landuse in {"recreation_ground", "village_green", "grass"}:
        return "Aday açık alan", 2
    return None, None


def build_safety_areas(osm, output_dir):
    custom_filter = {
        "emergency": ["assembly_point"],
        "leisure": ["park", "garden"],
        "landuse": ["recreation_ground", "village_green", "grass"],
    }
    pois = osm.get_pois(custom_filter=custom_filter)
    if pois is None or pois.empty:
        raise RuntimeError("No safety/open-area features found in the PBF.")

    rows = []
    for _, row in pois.iterrows():
        category, priority = classify_area(row)
        if category is None:
            continue

        access = clean_value(row.get("access")).lower()
        if access in {"private", "no"}:
            continue

        name = clean_value(row.get("name")) or category
        note_parts = []
        for tag in ("emergency", "leisure", "landuse", "access", "operator"):
            value = clean_value(row.get(tag))
            if value:
                note_parts.append(f"{tag}={value}")

        rows.append({
            "toplanma_alani": name,
            "name": name,
            "category": category,
            "priority": priority,
            "source": "Local OSM dataset",
            "note": " | ".join(note_parts),
            "emergency": clean_value(row.get("emergency")),
            "leisure": clean_value(row.get("leisure")),
            "landuse": clean_value(row.get("landuse")),
            "access": clean_value(row.get("access")),
            "geometry": row.geometry,
        })

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=pois.crs or "EPSG:4326")
    gdf = gdf[gdf.geometry.notna()].to_crs("EPSG:4326")
    output_path = output_dir / "safety_areas.geojson"
    gdf.to_file(output_path, driver="GeoJSON")
    return output_path, len(gdf)


def build_roads(osm, output_dir):
    roads = osm.get_network(network_type="walking", nodes=False)
    if roads is None or roads.empty:
        raise RuntimeError("No walking road network found in the PBF.")

    keep_columns = [
        col for col in [
            "id",
            "osm_type",
            "highway",
            "name",
            "oneway",
            "surface",
            "access",
            "foot",
            "sidewalk",
            "geometry",
        ]
        if col in roads.columns
    ]
    roads = roads[keep_columns].copy()
    roads = roads[roads.geometry.notna()].to_crs("EPSG:4326")
    output_path = output_dir / "roads.gpkg"
    roads.to_file(output_path, layer="roads", driver="GPKG")
    return output_path, len(roads)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pbf", help="Path to .osm.pbf file, e.g. data/osm/turkey-latest.osm.pbf")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    try:
        from pyrosm import OSM
    except ImportError as exc:
        raise SystemExit(
            "pyrosm is required to build local datasets. Install it with: "
            "pip install pyrosm"
        ) from exc

    pbf_path = Path(args.pbf).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    osm = OSM(str(pbf_path))
    safety_path, safety_count = build_safety_areas(osm, output_dir)
    roads_path, roads_count = build_roads(osm, output_dir)

    print(f"Wrote {safety_count} safety/open-area features to {safety_path}")
    print(f"Wrote {roads_count} walking road features to {roads_path}")


if __name__ == "__main__":
    main()
