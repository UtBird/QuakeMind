#!/usr/bin/env python3
import argparse
import json
import math
import os
import site
import sys
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "QuakeMindBackend"
RISK_ROOT = BACKEND_ROOT / "apps" / "earthquake_risk"
GEOJSON_PATHS = [
    RISK_ROOT / "data" / "fault_maps" / "fay_haritası" / "gem_active_faults.geojson",
    RISK_ROOT
    / "data"
    / "fault_maps"
    / "fay_haritası"
    / "gem_active_faults_harmonized.geojson",
]
FAULT_LINE_NAMES = [
    "Kuzey Anadolu Fayi",
    "Dogu Anadolu Fayi",
    "Edremit Fay Zonu",
    "Izmir Fay Zonu",
    "Aydin Fay Zonu",
    "Mugla Fay Zonu",
]


def add_site_packages(project_root: Path) -> None:
    for env_name in [".venv", "venv"]:
        env_path = project_root / env_name
        if not env_path.exists():
            continue
        for site_path in env_path.glob("lib/python*/site-packages"):
            site.addsitedir(str(site_path))


@contextmanager
def temporary_sys_path(*paths: Path):
    old_sys_path = list(sys.path)
    normalized_paths = [str(path) for path in paths if path]
    for path in reversed(normalized_paths):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path[:] = old_sys_path


@contextmanager
def temporary_cwd(path: Path):
    old_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        math.radians,
        [lat1, lon1, lat2, lon2],
    )
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


def iter_geometry_lat_lon(geometry):
    if not geometry:
        return

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Point":
        if len(coordinates) >= 2:
            yield coordinates[1], coordinates[0]
        return

    if geometry_type in {"LineString", "MultiPoint"}:
        for coord in coordinates:
            if len(coord) >= 2:
                yield coord[1], coord[0]
        return

    if geometry_type in {"MultiLineString", "Polygon"}:
        for segment in coordinates:
            for coord in segment:
                if len(coord) >= 2:
                    yield coord[1], coord[0]
        return

    if geometry_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                for coord in ring:
                    if len(coord) >= 2:
                        yield coord[1], coord[0]


def geometry_is_near_point(geometry, center_lat, center_lon, radius_km):
    coords = list(iter_geometry_lat_lon(geometry))
    if not coords:
        return False

    lat_margin = radius_km / 111.0
    lon_margin = radius_km / max(20.0, 111.0 * math.cos(math.radians(center_lat)))
    min_lat, max_lat = center_lat - lat_margin, center_lat + lat_margin
    min_lon, max_lon = center_lon - lon_margin, center_lon + lon_margin

    candidate_points = [
        (lat, lon)
        for lat, lon in coords
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
    ]
    if not candidate_points:
        return False

    stride = max(1, len(candidate_points) // 60)
    for lat, lon in candidate_points[::stride]:
        if distance_km(center_lat, center_lon, lat, lon) <= radius_km:
            return True
    return False


def get_filtered_fault_geojson(path: Path, center_lat, center_lon, radius_km=180.0):
    with path.open("r", encoding="utf-8") as handle:
        geojson_data = json.load(handle)

    filtered_features = []
    for feature in geojson_data.get("features", []):
        if geometry_is_near_point(
            feature.get("geometry"),
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
        ):
            filtered_features.append(feature)

    return {"type": "FeatureCollection", "features": filtered_features}


def parse_summary(summary: str) -> dict[str, object]:
    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    risk_level = ""
    risk_score = 0.0
    if lines:
        final_line = next(
            (line for line in reversed(lines) if line.startswith("Nihai Risk Skoru:")),
            lines[-1],
        )
        if "%" in final_line:
            try:
                risk_score = float(final_line.split(":", 1)[1].split("%", 1)[0].strip())
            except ValueError:
                risk_score = 0.0
        if "  " in final_line:
            risk_level = final_line.rsplit("  ", 1)[-1].strip()
    return {"riskLevel": risk_level, "riskScore": risk_score}


def build_nearby_faults(risk_module, lat: float, lon: float) -> list[str]:
    distances = []
    for index, line in enumerate(getattr(risk_module, "FAULT_LINES", [])):
        line_distance = min(
            risk_module.haversine(lat, lon, point_lat, point_lon)
            for point_lat, point_lon in line
        )
        name = FAULT_LINE_NAMES[index] if index < len(FAULT_LINE_NAMES) else f"Fay {index + 1}"
        distances.append((line_distance, name))
    distances.sort(key=lambda item: item[0])
    return [f"{name} ({distance:.1f} km)" for distance, name in distances[:3]]


def build_recent_events(city_quakes) -> tuple[list[str], str]:
    if city_quakes.empty:
        return [], "Veri bulunamadi"

    recent = city_quakes.sort_values("time", ascending=False).head(5)
    events = [
        f"M{row.mag:.1f} - {row.distance_km:.0f} km - {str(row.time)[:10]}"
        for row in recent.itertuples()
    ]
    last_update = str(city_quakes["time"].max())[:16].replace("T", " ")
    return events, last_update


def build_map_events(city_quakes):
    if city_quakes.empty:
        return []

    significant_quakes = city_quakes[city_quakes["mag"] >= 3.0].copy()
    if len(significant_quakes) > 250:
        significant_quakes = significant_quakes.sort_values(
            ["mag", "time"],
            ascending=[False, False],
        ).head(250)

    return [
        {
            "label": row.get("place") or "Bilinmeyen konum",
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "magnitude": float(row["mag"]),
            "timeLabel": str(row["time"]),
        }
        for _, row in significant_quakes.iterrows()
    ]


def build_heatmap_events(city_quakes):
    if city_quakes.empty:
        return []

    heat_source = city_quakes
    if len(heat_source) > 600:
        step = max(1, len(heat_source) // 600)
        heat_source = heat_source.iloc[::step].copy()

    return [
        {
            "label": row.get("place") or "Bilinmeyen konum",
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "magnitude": float(row["mag"]),
            "timeLabel": str(row["time"]),
        }
        for _, row in heat_source.iterrows()
    ]


def build_fault_lines(risk_module, lat: float, lon: float):
    visible_lines = []
    for index, line in enumerate(getattr(risk_module, "FAULT_LINES", [])):
        if any(distance_km(lat, lon, point_lat, point_lon) <= 180.0 for point_lat, point_lon in line):
            name = FAULT_LINE_NAMES[index] if index < len(FAULT_LINE_NAMES) else f"Fay {index + 1}"
            visible_lines.append(
                {
                    "name": name,
                    "points": [
                        {"latitude": float(point_lat), "longitude": float(point_lon)}
                        for point_lat, point_lon in line
                    ],
                }
            )
    return visible_lines


def build_technical_quakes(city_quakes):
    if city_quakes.empty:
        return []

    top_quakes = city_quakes.sort_values(["mag", "time"], ascending=[False, False]).head(20)
    return [
        {
            "time": str(row["time"]),
            "place": row.get("place") or "Bilinmeyen konum",
            "magnitude": float(row["mag"]),
            "depth": float(row["depth"]),
            "distanceKm": float(row["distance_km"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
        }
        for _, row in top_quakes.iterrows()
    ]


def build_map_html(selected_city, lat, lon, risk_module, city_quakes, filtered_fault_layers):
    import folium
    from folium.plugins import HeatMap, MarkerCluster

    risk_map = folium.Map(
        location=[lat, lon],
        zoom_start=8,
        tiles=None,
        prefer_canvas=True,
    )
    folium.TileLayer("CartoDB dark_matter", name="Koyu Mod").add_to(risk_map)
    folium.TileLayer("OpenStreetMap", name="Aydinlik Mod").add_to(risk_map)
    folium.Marker(
        [lat, lon],
        tooltip=selected_city,
        popup=selected_city,
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(risk_map)

    for line in getattr(risk_module, "FAULT_LINES", []):
        if any(distance_km(lat, lon, point_lat, point_lon) <= 180.0 for point_lat, point_lon in line):
            folium.PolyLine(
                line,
                color="#ff5722",
                weight=2,
                opacity=0.6,
                tooltip="Ana Fay Hatti",
            ).add_to(risk_map)

    heat_data = []
    if not city_quakes.empty:
        heat_source = city_quakes
        if len(heat_source) > 600:
            step = max(1, len(heat_source) // 600)
            heat_source = heat_source.iloc[::step].copy()
        heat_data = heat_source[["latitude", "longitude", "mag"]].values.tolist()
        HeatMap(
            heat_data,
            name="Deprem Yogunlugu",
            radius=15,
            max_zoom=10,
            min_opacity=0.4,
            gradient={0.4: "blue", 0.65: "lime", 1: "red"},
        ).add_to(risk_map)

        cluster = MarkerCluster(name="Bolgesel Depremler").add_to(risk_map)
        significant_quakes = city_quakes[city_quakes["mag"] >= 3.0]
        if len(significant_quakes) > 250:
            significant_quakes = significant_quakes.sort_values(
                ["mag", "time"],
                ascending=[False, False],
            ).head(250)

        for _, row in significant_quakes.iterrows():
            mag = float(row["mag"])
            color = "green"
            if mag >= 4.0:
                color = "orange"
            if mag >= 5.0:
                color = "red"
            if mag >= 6.0:
                color = "darkred"
            popup_html = (
                f"<b>Tarih:</b> {row['time']}<br>"
                f"<b>Buyukluk:</b> <span style='color:{color}; font-weight:bold;'>{mag}</span><br>"
                f"<b>Derinlik:</b> {row['depth']} km"
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(cluster)

    technical_layers = []
    total_fault_features = 0
    for path, geo_data in filtered_fault_layers:
        feature_count = len(geo_data.get("features", []))
        total_fault_features += feature_count
        layer_name = path.stem.replace("_", " ").title()
        technical_layers.append(
            {
                "name": layer_name,
                "path": str(path),
                "featureCount": feature_count,
            }
        )
        if feature_count:
            folium.GeoJson(
                geo_data,
                name=f"Detayli Faylar: {layer_name}",
                zoom_on_click=False,
                style_function=lambda _: {
                    "color": "#ff9800",
                    "weight": 1.5,
                    "opacity": 0.5,
                },
            ).add_to(risk_map)

    folium.LayerControl(collapsed=False).add_to(risk_map)
    return {
        "html": risk_map.get_root().render(),
        "technicalLayers": technical_layers,
        "totalFaultFeatures": total_fault_features,
        "heatSampleCount": len(heat_data),
    }


def run_refresh_data() -> str:
    with temporary_sys_path(RISK_ROOT), temporary_cwd(RISK_ROOT):
        from data_manager import fetch_and_update_data

        return str(fetch_and_update_data())


def build_payload(city: str, manual_coords=None, refresh_data=False) -> dict[str, object]:
    add_site_packages(RISK_ROOT)
    with temporary_sys_path(RISK_ROOT):
        import risk_engine

        if refresh_data:
            refresh_message = run_refresh_data()
        else:
            refresh_message = ""

        engine = risk_engine.EarthquakeRiskEngine(
            csv_path=str(RISK_ROOT / "data" / "query.csv"),
        )
        summary = engine.predict_city_risk(city, manual_coords=manual_coords)
        lat = float(engine.last_lat)
        lon = float(engine.last_lon)

        full_df = engine.df_full.copy()
        dists = risk_engine.haversine(
            lat,
            lon,
            full_df["latitude"].values,
            full_df["longitude"].values,
        )
        city_quakes = full_df[dists <= 150.0].copy()
        city_quakes["distance_km"] = dists[dists <= 150.0]

        filtered_fault_layers = []
        for path in GEOJSON_PATHS:
            if path.exists():
                filtered_fault_layers.append(
                    (
                        path,
                        get_filtered_fault_geojson(
                            path,
                            round(lat, 4),
                            round(lon, 4),
                            radius_km=180.0,
                        ),
                    )
                )

        parsed = parse_summary(summary)
        short_risk = float(engine._compute_short_term_ml_risk(lat, lon))
        long_hazard = float(
            engine._compute_long_term_hazard(
                lat,
                lon,
                radius_km=200.0,
                mag_threshold=6.0,
            )
        )
        fault_distance = float(risk_engine.nearest_fault_distance(lat, lon))
        fault_score = float(risk_engine.fault_hazard_score(fault_distance))
        map_payload = build_map_html(
            city,
            lat,
            lon,
            risk_engine,
            city_quakes,
            filtered_fault_layers,
        )
        recent_events, last_update = build_recent_events(city_quakes)

        return {
            "city": city,
            "coordinates": {"lat": lat, "lon": lon},
            "summary": summary,
            "riskScore": parsed["riskScore"],
            "riskLevel": parsed["riskLevel"],
            "lastUpdate": last_update,
            "nearbyFaults": build_nearby_faults(risk_engine, lat, lon),
            "recentEvents": recent_events,
            "factors": {
                "Kisa vadeli risk": short_risk,
                "Uzun vadeli tehlike": long_hazard,
                "Fay etkisi": fault_score,
            },
            "metrics": {
                "shortRisk": short_risk,
                "longHazard": long_hazard,
                "faultScore": fault_score,
                "faultDistanceKm": fault_distance,
                "nearbyQuakeCount": int(len(city_quakes)),
                "maxMagnitude": float(city_quakes["mag"].max()) if not city_quakes.empty else 0.0,
                "averageDepth": float(city_quakes["depth"].mean()) if not city_quakes.empty else 0.0,
                "heatSampleCount": int(map_payload["heatSampleCount"]),
                "totalFaultFeatures": int(map_payload["totalFaultFeatures"]),
            },
            "mapEvents": build_map_events(city_quakes),
            "heatmapEvents": build_heatmap_events(city_quakes),
            "faultLines": build_fault_lines(risk_engine, lat, lon),
            "technicalLayers": map_payload["technicalLayers"],
            "technicalQuakes": build_technical_quakes(city_quakes),
            "mapHtml": map_payload["html"],
            "usedManualCoordinates": manual_coords is not None,
            "refreshMessage": refresh_message,
            "source": "backend_exact",
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("city", nargs="?", default="Hatay")
    parser.add_argument("--manual-lat", type=float)
    parser.add_argument("--manual-lon", type=float)
    parser.add_argument("--refresh-data", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manual_coords = None
    if args.manual_lat is not None or args.manual_lon is not None:
        if args.manual_lat is None or args.manual_lon is None:
            print(json.dumps({"error": "Manuel koordinat icin hem enlem hem boylam gerekli."}))
            return 1
        manual_coords = (args.manual_lat, args.manual_lon)

    try:
        payload = build_payload(
            city=args.city,
            manual_coords=manual_coords,
            refresh_data=args.refresh_data,
        )
        print(json.dumps(payload, ensure_ascii=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
