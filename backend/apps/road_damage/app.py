import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw, SideBySideLayers, FastMarkerCluster
import os
import math
import cv2
import numpy as np
import traceback
from PIL import Image
import datetime
import io
import base64
from pathlib import Path
import networkx as nx
import osmnx as ox
import pandas as pd
from streamlit_js_eval import streamlit_js_eval

# Import from utils
from utils.fetcher import fetch_satellite_area, get_osm_roads_overpass, get_wayback_versions, search_oam_images
from utils.network import analyze_road_network_graph, calculate_route
from utils.inference import load_simple_model, run_inference
from utils.local_osm import (
    OSM_DATA_DIR,
    has_local_roads_dataset,
    has_local_safety_dataset,
    load_local_safety_areas,
    shortest_route_from_local_roads,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "optimized_mitb4_focal_dice30.pth"
ox.settings.requests_timeout = 180

# -----------------------------------------------------------------------------
# Configuration & Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Satellite Road Damage Assessment",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    h1 { color: #2E86C1; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #2E86C1; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "logistic_routing_points" not in st.session_state:
    st.session_state.logistic_routing_points = []
if "logistic_calculated_route" not in st.session_state:
    st.session_state.logistic_calculated_route = None

def get_b64_image(image_arr):
    img = Image.fromarray(image_arr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

def build_assembly_points(records):
    return [
        [
            item.get("display_lat", item["lat"]),
            item.get("display_lon", item["lon"]),
            item["toplanma_alani"] or "Toplanma Alanı",
            item.get("category", "Toplanma Alanı"),
            item.get("source", "OSM"),
            item.get("note", ""),
        ]
        for item in records
    ]

def get_high_accuracy_geolocation(component_key="assembly_high_accuracy_geolocation"):
    js_expression = """
    (function () {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({error: {code: 0, message: "Browser does not support geolocation."}});
                return;
            }

            let best = null;
            let finished = false;
            const targetAccuracy = 15;
            const startedAt = Date.now();
            const maxWaitMs = 25000;

            function serialize(position) {
                return {
                    coords: {
                        accuracy: position.coords.accuracy,
                        altitude: position.coords.altitude,
                        altitudeAccuracy: position.coords.altitudeAccuracy,
                        heading: position.coords.heading,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        speed: position.coords.speed,
                    },
                    timestamp: position.timestamp,
                    source: "high_accuracy_watch",
                    elapsedMs: Date.now() - startedAt,
                };
            }

            function finish(value, watchId) {
                if (finished) return;
                finished = true;
                if (watchId !== null) navigator.geolocation.clearWatch(watchId);
                resolve(value);
            }

            const watchId = navigator.geolocation.watchPosition(
                (position) => {
                    const current = serialize(position);
                    if (!best || current.coords.accuracy < best.coords.accuracy) {
                        best = current;
                    }
                    if (current.coords.accuracy <= targetAccuracy) {
                        finish(current, watchId);
                    }
                },
                (error) => {
                    finish({error: {code: error.code, message: error.message}}, watchId);
                },
                {
                    enableHighAccuracy: true,
                    timeout: maxWaitMs,
                    maximumAge: 0,
                }
            );

            setTimeout(() => {
                finish(best || {error: {code: 3, message: "High accuracy location timed out."}}, watchId);
            }, maxWaitMs);
        });
    })()
    """
    return streamlit_js_eval(js_expressions=js_expression, key=component_key)

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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_osm_safety_areas(bbox, include_candidate_open_areas):
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
        features.geometry.geom_type.isin([
            "Point",
            "MultiPoint",
            "Polygon",
            "MultiPolygon",
        ])
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
            category = "OSM resmi toplanma alanı"
            priority = 0
        elif leisure in {"park", "garden"}:
            category = "Aday park/bahçe"
            priority = 1
        elif landuse in {"recreation_ground", "village_green", "grass"}:
            category = "Aday açık alan"
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

@st.cache_data(ttl=1800, show_spinner=False)
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

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🛰️ RDA Control Panel")
    st.info("Analyze road damage using AI (Segformer).")
    offline_only = st.checkbox(
        "Offline OSM modu",
        value=False,
        help="Açıksa hasar analizindeki yol maskesi sadece local data/osm/roads.gpkg dosyasından üretilir.",
    )
    os.environ["QUAKEMIND_OFFLINE_ONLY"] = "1" if offline_only else "0"
    if offline_only and not has_local_roads_dataset():
        st.warning("Offline mod açık ama local roads.gpkg bulunamadı.")
    
    st.header("1. Location & Data")
    
    CITIES = {
        "Antakya (Hatay)": [36.20, 36.16],
        "Kahramanmaraş": [37.57, 36.93],
        "Gaziantep": [37.06, 37.38],
        "Malatya": [38.35, 38.30],
        "Adıyaman": [37.76, 38.27]
    }
    selected_city_name = st.selectbox("📍 Jump to City", list(CITIES.keys()))
    city_coords = CITIES[selected_city_name]
    
    st.markdown("---")
    
    wayback_versions = get_wayback_versions()
    opt_google = "Google Maps (Latest / High Res)"
    opt_oam = "OpenAerialMap (Event Specific)"
    wayback_options = []
    wayback_map = {}
    if wayback_versions:
        wayback_versions.sort(key=lambda x: x['date'], reverse=True)
        wayback_map = {f"Esri Wayback ({v['date']})": v for v in wayback_versions}
        wayback_options = list(wayback_map.keys())
    
    source_options = [opt_google, opt_oam] + wayback_options
    selected_source = st.selectbox("📡 Satellite Source", source_options)
    
    provider = "Esri Wayback" if "Wayback" in selected_source else "Google Maps"
    selected_wayback = wayback_map.get(selected_source)
    selected_oam_url = None
    
    if selected_source == opt_oam:
        provider = "OpenAerialMap"
        st.caption("Search for post-disaster imagery (e.g. Feb 2023)")
        c1, c2 = st.columns(2)
        d_start = c1.date_input("Start", datetime.date(2023, 2, 6))
        d_end = c2.date_input("End", datetime.date(2023, 2, 28))
        
        if st.button("🔎 Search Images"):
            if 'last_clicked' in st.session_state and st.session_state['last_clicked']:
                lat, lon = st.session_state['last_clicked']
                bbox = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
            else:
                lat, lon = city_coords
                bbox = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
            
            with st.spinner("Searching OAM..."):
                st.session_state['oam_results'] = search_oam_images(bbox, d_start, d_end)
        
        if st.session_state.get('oam_results'):
            res_oam = st.session_state['oam_results']
            st.success(f"Found {len(res_oam)} images.")
            oam_opts = {f"{r['date']} - {r['provider']}": r for r in res_oam}
            sel_oam = st.selectbox("Select Image", list(oam_opts.keys()))
            if sel_oam:
                selected_oam_url = oam_opts[sel_oam]['tms_url']
    
    st.header("2. Analysis Settings")
    with st.expander("⚙️ Fine-Tuning", expanded=True):
        zoom_level = 18
        
        st.markdown("#### Detection Parameters")
        damage_booster = st.slider("🔥 Damage Sensitivity Booster", 1.0, 10.0, 3.5, 0.5, help="Modelin çıkardığı hasar olasılıklarını bu katsayı ile çarparak zayıf tahminleri belirginleştirir. Kaçırılan enkazları yakalamak için artırın.")
        threshold = st.slider("📉 Detection Threshold", 0.05, 0.95, 0.40, 0.05, help="Bir pikselin enkaz sayılması için gereken minimum güvenilirlik seviyesidir. Düşürürseniz hasar tespiti artar ancak hatalı alarmlar olabilir.")
        line_width = 6
        
        st.markdown("#### Model Path")
        model_path = st.text_input("📁 Pytorch Weights (.pth)", value=str(DEFAULT_MODEL_PATH), help="Kullanılacak yapay zeka modelinin dosya yoludur.")
        use_imagenet_norm = st.checkbox("🔬 ImageNet Normalizasyonu", value=True, help="Görüntü piksellerini modelin eğitildiği formata (normalize) çeker. Seçili yeni modelde daha doğru sonuç verir.")
        postprocess_level = st.selectbox("🧹 Post-Processing", ["Kapalı (0)", "Hafif (1)", "Güçlü (2)"], index=2,
            help="Tahminler üzerinde morfolojik işlemler yaparak ufak hatalı pikselleri (gürültüleri) temizler ve bölgeleri birleştirir.")
        postprocess_level = int(postprocess_level.split("(")[1][0])
    
    analyze_btn = st.button("🚀 Start Analysis", type="primary")
    if st.button("🔄 Reset Analysis"):
        st.session_state.analysis_result = None
        if "logistic_data" in st.session_state:
            del st.session_state["logistic_data"]
        st.rerun()

# -----------------------------------------------------------------------------
# Main Interface
# -----------------------------------------------------------------------------

st.title("Satellite Road Damage Assessment")

damage_tab, assembly_tab = st.tabs(["🛰️ Hasar Analizi", "🗺️ Toplanma Alanları"])

with damage_tab:
    # Map Display
    m = folium.Map(location=city_coords, zoom_start=15)

    # Add Base Layer
    if provider == "Esri Wayback" and selected_wayback:
        url = f"https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{selected_wayback['id']}/{{z}}/{{y}}/{{x}}"
        folium.TileLayer(tiles=url, attr=f"Esri", name="Wayback").add_to(m)
    elif provider == "Google Maps":
        folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", name="Google Satellite").add_to(m)
    elif provider == "OpenAerialMap" and selected_oam_url:
        folium.TileLayer(tiles=selected_oam_url, attr="OAM", name="OAM Layer").add_to(m)

    # Add Draw Tool
    draw = Draw(
        export=False,
        position='topleft',
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'rectangle': True
        }
    )
    draw.add_to(m)
    m.add_child(folium.LatLngPopup())
    output = st_folium(m, height=450, width="100%")

    click_lat, click_lon = None, None
    draw_bbox = None

    if output.get("last_active_drawing"):
        geom = output["last_active_drawing"]["geometry"]
        if geom["type"] in ["Polygon", "Rectangle"]:
            coords = np.array(geom["coordinates"][0])
            lon_min, lat_min = coords.min(axis=0)
            lon_max, lat_max = coords.max(axis=0)
            draw_bbox = (lon_min, lat_min, lon_max, lat_max)
            st.success(f"📌 Alan seçildi! Analizi başlatabilirsiniz.")
            click_lat = (lat_min + lat_max) / 2
            click_lon = (lon_min + lon_max) / 2
    elif output.get("last_clicked"):
        click_lat = output["last_clicked"]["lat"]
        click_lon = output["last_clicked"]["lng"]
        st.caption(f"Selected: {click_lat:.5f}, {click_lon:.5f}")
    else:
        st.info("👆 Haritadan bir noktaya tıklayın veya soldaki çizim aracı (Dörtgen/Çokgen) ile özel bir alan seçin.")

    st.markdown("---")

    # -----------------------------------------------------------------------------
    # Trigger Analysis
    # -----------------------------------------------------------------------------
    if analyze_btn:
        if "logistic_data" in st.session_state:
            del st.session_state["logistic_data"]
        if not click_lat and not draw_bbox:
            st.warning("Lütfen önce haritadan bir alan seçin veya bir noktaya tıklayın.")
        else:
            progress_bar = st.progress(0, text="Starting Analysis...")
            status_text = st.empty()
        
            try:
                # 1. Fetch Image based on clicked coordinate or drawn bbox
                status_text.text("1/4 Downloading Satellite Imagery...")
                progress_bar.progress(10)
            
                wayback_id = selected_wayback['id'] if selected_wayback else None
                prov_code = 'google' if provider == "Google Maps" else 'custom' if provider == "OpenAerialMap" else 'esri'
                custom_url = selected_oam_url if provider == "OpenAerialMap" else None
            
                img, bounds = fetch_satellite_area(
                    lat=click_lat,
                    lon=click_lon,
                    bbox=draw_bbox,
                    zoom_level=zoom_level,
                    wayback_id=wayback_id,
                    provider=prov_code,
                    custom_url=custom_url
                )
            
                if img is None:
                    st.error("FAILED to download imagery. Try a different zoom level or provider.")
                    st.stop()
                else:
                    progress_bar.progress(30)
                    status_text.text("2/4 Fetching Road Network (OSM)...")
                
                    # Image dims
                    w, h = img.size
                
                    # Overpass API road retrieval mapped onto exact bbox
                    status_text.text("2/4 Fetching Road Network (OSM via Overpass)...")
                    road_mask = get_osm_roads_overpass(bounds, w, h, thickness=line_width)
                    road_mask_binary = (road_mask > 0).astype(np.uint8)

                    status_text.text("3/4 Preprocessing & Model Loading...")
                    progress_bar.progress(60)
                
                    model, device = load_simple_model(model_path)
                    if model is None:
                        st.error("Model yüklenemedi! Dosya yolunu kontrol edin.")
                        st.stop()
                    
                    # 4. Inference
                    status_text.text("4/4 Running AI Inference (Segformer)...")
                    progress_bar.progress(80)
                
                    raw_probs, boosted_probs, pred_mask_binary, intersection, img_np = run_inference(
                        img, road_mask_binary, model, device, damage_booster, threshold,
                        use_imagenet_norm, postprocess_level)
                
                    progress_bar.progress(100)
                    status_text.text("Analysis Complete!")
                
                    st.session_state.analysis_result = {
                        "original_img": img_np,
                        "road_mask": road_mask_binary,
                        "raw_probs": raw_probs,
                        "bounds": bounds
                    }
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.code(traceback.format_exc())
                progress_bar.empty()

    # -----------------------------------------------------------------------------
    # Result Display
    # -----------------------------------------------------------------------------
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
    
        # -- Canlı Eşikleme (Live Thresholding & Boosting) --
        current_probs = np.clip(res["raw_probs"] * damage_booster, 0, 1)
        current_pred_mask = (current_probs > threshold).astype(np.uint8)
        current_intersection = cv2.bitwise_and(current_pred_mask, res["road_mask"])
    
        st.subheader("📝 Analysis Report")
    
        vis_img = res["original_img"].copy()
    
        # Color palettes
        yellow_overlay = np.zeros_like(vis_img)
        yellow_overlay[:] = [255, 255, 0] # Sarı (Genel Enkaz)
    
        red_overlay = np.zeros_like(vis_img)
        red_overlay[:] = [255, 0, 0] # Kırmızı (Yol üzeri Enkaz)
    
        cyan_overlay = np.zeros_like(vis_img)
        cyan_overlay[:] = [0, 255, 255] # Turkuaz (Açık yollar)
    
        # Saydam overlayleri resmin tamamı üzerinde oluşturup sonra maskeliyoruz
        cyan_idx = (res["road_mask"] == 1) & (current_intersection == 0)
        blended_cyan = cv2.addWeighted(vis_img, 0.3, cyan_overlay, 0.7, 0)
        vis_img[cyan_idx] = blended_cyan[cyan_idx]
    
        mask_idx = (current_pred_mask == 1) & (current_intersection == 0)
        blended_yellow = cv2.addWeighted(vis_img, 0.5, yellow_overlay, 0.5, 0)
        vis_img[mask_idx] = blended_yellow[mask_idx]
    
        # Yol Üzerindeki Enkaz (Kesişim)
        kernel = np.ones((9, 9), np.uint8)
        thick_intersection = cv2.dilate(current_intersection, kernel, iterations=2)
        intersection_idx = (thick_intersection == 1)
    
        blended_red = cv2.addWeighted(vis_img, 0.1, red_overlay, 0.9, 0)
        vis_img[intersection_idx] = blended_red[intersection_idx]

        st.markdown("### 🔍 Harita Üzerinde Kıyaslama (Öncesi / Sonrası)")
        # SIDE BY SIDE LAYERS MAP
        center_lat = (res["bounds"][1] + res["bounds"][3]) / 2.0
        center_lon = (res["bounds"][0] + res["bounds"][2]) / 2.0
    
        cmp_map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
        bounds_folium = [[res["bounds"][1], res["bounds"][0]], [res["bounds"][3], res["bounds"][2]]]
    
        left_layer = folium.raster_layers.ImageOverlay(
            name="Hasarsız Uydu",
            image=get_b64_image(res["original_img"]),
            bounds=bounds_folium,
            opacity=1,
            interactive=True,
            cross_origin=False,
            zindex=1,
        )
    
        right_layer = folium.raster_layers.ImageOverlay(
            name="Yapay Zeka Hasar Haritası",
            image=get_b64_image(vis_img),
            bounds=bounds_folium,
            opacity=1,
            interactive=True,
            cross_origin=False,
            zindex=1,
        )
    
        left_layer.add_to(cmp_map)
        right_layer.add_to(cmp_map)
    
        sbs = SideBySideLayers(layer_left=left_layer, layer_right=right_layer)
        sbs.add_to(cmp_map)
    
        st_folium(cmp_map, width="100%", height=500, key="swipe_map")

        st.markdown("""
        <div style="background-color: #0E1117; padding: 15px; border-radius: 8px; border: 1px solid #333; display: flex; justify-content: space-around; margin-top: 10px;">
            <span style="color: #00FFFF; font-weight: bold; font-size: 1.1em;">■ Açık Yol (OSM)</span>
            <span style="color: #FFFF00; font-weight: bold; font-size: 1.1em;">■ Tespit Edilen Yıkıntı / Enkaz</span>
            <span style="color: #FF0000; font-weight: bold; font-size: 1.1em;">■ Yol Üzerindeki Yıkıntı (Kapalı Yol)</span>
        </div>
        """, unsafe_allow_html=True)
    
        st.markdown("### 🧩 Diagnostik")
        c1, c2, c3, c4 = st.columns(4)
        c1.image((current_pred_mask * 255).astype(np.uint8), caption="Model Yıkıntı Tahmini", width="stretch")
        c2.image((res["road_mask"] * 255).astype(np.uint8), caption="OSM Yol Maskesi", width="stretch")
        c3.image((current_intersection * 255).astype(np.uint8), caption="Yol & Yıkıntı Kesişimi", width="stretch")
    
        # Segmentasyon overlay: uydu görüntüsü üzerine hasar bölgeleri
        seg_overlay = res["original_img"].copy()
        damage_color = np.zeros_like(seg_overlay)
        damage_color[:] = [255, 50, 50]  # Kırmızı
        damage_idx = current_pred_mask == 1
        blended = cv2.addWeighted(seg_overlay, 0.4, damage_color, 0.6, 0)
        seg_overlay[damage_idx] = blended[damage_idx]
        c4.image(seg_overlay, caption="Uydu + Segmentasyon", width="stretch")

        st.markdown("---")
        st.markdown("### 🚑 Lojistik ve Rota Analizi")
        st.info("Bu modül, tespit edilen enkazları mevcut yol ağının (Graph) üzerine bindirerek hangi sokakların kapalı olduğunu hesaplar ve acil durum ekipleri için erişilebilir (yeşil) güvenli bölgeleri haritalandırır.")
    
        if st.button("🗺️ Lojistik Ağı Hesapla"):
            with st.spinner("Graph matrisi çıkarılıyor ve kapanan yollar siliniyor..."):
                w, h = res["original_img"].shape[1], res["original_img"].shape[0]
                # Use the exact intersection as the blockage mask to precisely match diagnostic visuals
                G, safe_G, safe_edges, blocked_edges = analyze_road_network_graph(res["bounds"], w, h, current_intersection)
            
                if G is None:
                    st.error("Bu bölge için OSM yol ağı (Graph) bulunamadı.")
                else:
                    st.session_state.logistic_data = {
                        "safe_edges": safe_edges,
                        "blocked_edges": blocked_edges,
                        "bounds": res["bounds"],
                        "total": len(safe_edges) + len(blocked_edges),
                        "blocked_count": len(blocked_edges),
                        "safe_G": safe_G
                    }

        if st.session_state.get("logistic_data"):
            data = st.session_state.logistic_data
            st.success(f"Yol Ağı Analizi Tamamlandı! Toplam {data['total']} sokak incelendi. {data['blocked_count']} tanesi ulaşıma kapalı.")
            
            st.markdown("### 📍 Güvenli Rota Çizimi")
            st.info("Aşağıdaki lojistik haritasına tıklayarak Başlangıç ve Bitiş noktalarını seçebilir, enkazsız yeşil yollar üzerinden en stabil (Dijkstra) rotayı çizebilirsiniz.")
            
            # Kontrol Butonları
            c1, c2 = st.columns([1, 1])
            if c1.button("📌 Seçimleri Temizle"):
                st.session_state.logistic_routing_points = []
                st.session_state.logistic_calculated_route = None
                st.rerun()
                
            if len(st.session_state.logistic_routing_points) == 2:
                if c2.button("🚀 En Güvenli Rotayı Hesapla", type="primary"):
                    with st.spinner("Güvenli rota hesaplanıyor..."):
                        p1 = st.session_state.logistic_routing_points[0]
                        p2 = st.session_state.logistic_routing_points[1]
                        try:
                            # Her zaman analizden çıkan safe_G'yi kullanıyoruz
                            safe_G = data["safe_G"]
                            dijkstra_path, _ = calculate_route(safe_G, p1[0], p1[1], p2[0], p2[1])
                            if dijkstra_path:
                                st.session_state.logistic_calculated_route = dijkstra_path
                                st.success("En güvenli rota başarıyla oluşturuldu!")
                            else:
                                st.error("Bu iki nokta arasında güvenli bir bağlantı (rota) bulunamadı! Yol tamamen kapalı olabilir.")
                        except Exception as e:
                            st.error(f"Rota hesaplanırken hata oluştu: {e}")
        
            # Haritayı Çiz
            center_lat = (data["bounds"][1] + data["bounds"][3]) / 2.0
            center_lon = (data["bounds"][0] + data["bounds"][2]) / 2.0
            route_map = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="CartoDB dark_matter")
        
            # Açık Yollar
            for _, _, _, line in data["safe_edges"]:
                points = [(lat, lon) for lon, lat in line.coords]
                folium.PolyLine(points, color="#00FF00", weight=4, opacity=0.8, tooltip="Erişime Açık Yol").add_to(route_map)
            
            # Kapalı Yollar
            for _, _, _, line in data["blocked_edges"]:
                points = [(lat, lon) for lon, lat in line.coords]
                folium.PolyLine(points, color="#FF0000", weight=4, opacity=0.8, dash_array="5, 5", tooltip="ENKAZ NEDENİYLE KAPALI").add_to(route_map)
            
            # Kullanıcının Seçtiği Noktalar
            for i, pt in enumerate(st.session_state.logistic_routing_points):
                label = "Başlangıç" if i == 0 else "Hedef"
                color = "blue" if i == 0 else "orange"
                folium.Marker(location=pt, popup=label, tooltip=label, icon=folium.Icon(color=color)).add_to(route_map)
                
            # Hesaplanmış Rota (Dijkstra)
            if st.session_state.logistic_calculated_route:
                folium.PolyLine(
                    st.session_state.logistic_calculated_route,
                    color="#00FFFF",  # Cyan renk ile çok belirgin
                    weight=8,
                    opacity=0.9,
                    tooltip="En Güvenli Dijkstra Rotası"
                ).add_to(route_map)
            
            map_out = st_folium(route_map, width="100%", height=500, key="logistic_map_viz")
            
            # Tıklama Kontrolü
            if map_out and map_out.get("last_clicked"):
                lat = map_out["last_clicked"]["lat"]
                lng = map_out["last_clicked"]["lng"]
                if len(st.session_state.logistic_routing_points) < 2:
                    st.session_state.logistic_routing_points.append((lat, lng))
                    st.rerun()

with assembly_tab:
    st.subheader("OSM Toplanma ve Aday Açık Alan Haritası")
    st.caption(
        "Bu sekmede JSON dosyası kullanılmıyor. Veriler OpenStreetMap üzerinden canlı olarak çekiliyor: önce `emergency=assembly_point`, istenirse park/bahçe gibi aday açık alanlar."
    )

    fallback_center = city_coords
    if "assembly_user_lat" not in st.session_state:
        st.session_state.assembly_user_lat = fallback_center[0]
    if "assembly_user_lon" not in st.session_state:
        st.session_state.assembly_user_lon = fallback_center[1]
    if "assembly_location_source" not in st.session_state:
        st.session_state.assembly_location_source = "Seçili şehir merkezi"

    st.markdown("### Konum")
    st.info("Tarayıcı konum izni verdiğinde yüksek doğruluk modu ile birkaç ölçüm alınır; OSM sorgusu ve rota bu konuma göre yapılır.")

    geolocation = get_high_accuracy_geolocation()
    auto_location_available = False

    if geolocation and geolocation.get("coords"):
        coords = geolocation["coords"]
        detected_lat = coords.get("latitude")
        detected_lon = coords.get("longitude")
        if detected_lat is not None and detected_lon is not None:
            auto_location_available = True
            if (
                abs(detected_lat - st.session_state.assembly_user_lat) > 1e-7
                or abs(detected_lon - st.session_state.assembly_user_lon) > 1e-7
            ):
                st.session_state.assembly_user_lat = float(detected_lat)
                st.session_state.assembly_user_lon = float(detected_lon)
                st.session_state.assembly_location_source = "Tarayıcı GPS"
                st.rerun()
            accuracy = coords.get("accuracy")
            elapsed_ms = geolocation.get("elapsedMs")
            if accuracy is not None:
                if accuracy <= 25:
                    st.success(f"Yüksek doğruluklu konum alındı. Yaklaşık doğruluk: {accuracy:.0f} m")
                else:
                    st.warning(
                        f"Konum alındı ama doğruluk düşük: {accuracy:.0f} m. "
                        "Telefon GPS'i, açık gökyüzü ve HTTPS/localhost doğruluğu iyileştirir."
                    )
                if elapsed_ms is not None:
                    st.caption(f"Konum ölçümü yaklaşık {elapsed_ms / 1000:.1f} saniye sürdü.")
            else:
                st.success("Konum otomatik alındı.")
    elif geolocation and geolocation.get("error"):
        st.warning(
            "Tarayıcı konumu alınamadı: "
            f"{geolocation['error'].get('message', 'Konum izni reddedilmiş olabilir.')}"
        )
    else:
        st.caption("Konum izni penceresi görünürse izin ver; bazı tarayıcılarda birkaç saniye sürebilir.")

    loc_col1, loc_col2, loc_col3 = st.columns([1, 1, 1])
    loc_col1.metric("Aktif enlem", f"{st.session_state.assembly_user_lat:.6f}")
    loc_col2.metric("Aktif boylam", f"{st.session_state.assembly_user_lon:.6f}")
    loc_col3.metric("Konum kaynağı", st.session_state.assembly_location_source)

    manual_refresh = False
    with st.expander("Konum alınamazsa manuel düzeltme", expanded=not auto_location_available):
        manual_lat = st.number_input(
            "Bulunduğun enlem",
            min_value=-90.0,
            max_value=90.0,
            value=float(st.session_state.assembly_user_lat),
            format="%.7f",
            key="assembly_manual_lat",
        )
        manual_lon = st.number_input(
            "Bulunduğun boylam",
            min_value=-180.0,
            max_value=180.0,
            value=float(st.session_state.assembly_user_lon),
            format="%.7f",
            key="assembly_manual_lon",
        )
        st.caption("Haritaya tıklayarak da konumu güncelleyebilirsin.")
        manual_refresh = st.button("Manuel konumla OSM verisini yenile")

    if manual_refresh:
        st.session_state.assembly_user_lat = float(manual_lat)
        st.session_state.assembly_user_lon = float(manual_lon)
        st.session_state.assembly_location_source = "Manuel"
        st.rerun()

    st.markdown("### OSM Veri Kaynağı")
    local_safety_ready = has_local_safety_dataset()
    local_roads_ready = has_local_roads_dataset()
    st.caption(
        f"Local güvenli bölge dataset: {'hazır' if local_safety_ready else 'yok'} | "
        f"Local yol dataset: {'hazır' if local_roads_ready else 'yok'} | "
        f"Klasör: {OSM_DATA_DIR}"
    )

    source_col1, source_col2, source_col3, source_col4 = st.columns([1, 1, 1, 1])
    with source_col1:
        data_source = st.selectbox(
            "Güvenli bölge veri kaynağı",
            ["Otomatik (local varsa)", "Sadece local dataset", "Online OSM"],
            index=0,
            help="Local dataset varsa internet kullanmadan okur; yoksa online OSM'e düşer.",
        )
    with source_col2:
        search_radius_km = st.slider(
            "OSM arama yarıçapı (km)",
            min_value=1,
            max_value=30,
            value=8,
            step=1,
            help="Büyük yarıçaplar Overpass sorgusunu yavaşlatabilir.",
        )
    with source_col3:
        include_candidate_open_areas = st.checkbox(
            "Park/bahçe aday açık alanları da dahil et",
            value=True,
            help="Bunlar resmi toplanma alanı değildir; resmi alan yoksa rota için aday alternatif olarak kullanılır.",
        )
    with source_col4:
        allow_online_route_fallback = st.checkbox(
            "Local rota olmazsa online fallback",
            value=data_source != "Sadece local dataset",
            help="Kapalıysa rota sadece local roads.gpkg ile denenir.",
        )

    osm_bbox = bbox_from_center(
        st.session_state.assembly_user_lat,
        st.session_state.assembly_user_lon,
        search_radius_km,
    )

    should_use_local = data_source in {"Otomatik (local varsa)", "Sadece local dataset"} and local_safety_ready
    should_use_online = data_source == "Online OSM" or (
        data_source == "Otomatik (local varsa)" and not should_use_local
    )

    osm_error = None
    if should_use_local:
        with st.spinner("Local dataset üzerinden güvenli/açık alan verisi okunuyor..."):
            display_records = load_local_safety_areas(osm_bbox, include_candidate_open_areas)
        active_data_source = "Local dataset"
    elif should_use_online:
        with st.spinner("OSM üzerinden toplanma/açık alan verisi çekiliyor..."):
            display_records, osm_error = fetch_osm_safety_areas(osm_bbox, include_candidate_open_areas)
        active_data_source = "Online OSM"
    else:
        display_records = []
        active_data_source = "Local dataset bulunamadı"
        osm_error = f"Local dataset bulunamadı: {OSM_DATA_DIR / 'safety_areas.geojson'}"

    if osm_error:
        st.error(f"OSM verisi alınamadı: {osm_error}")
        display_records = []
    else:
        st.caption(f"Aktif güvenli bölge kaynağı: {active_data_source}")

    official_records = [item for item in display_records if item.get("priority") == 0]
    candidate_records = [item for item in display_records if item.get("priority") != 0]

    stats_left, stats_mid, stats_right = st.columns(3)
    stats_left.metric("OSM resmi alan", f"{len(official_records):,}".replace(",", "."))
    stats_mid.metric("Aday açık alan", f"{len(candidate_records):,}".replace(",", "."))
    stats_right.metric("Arama yarıçapı", f"{search_radius_km} km")

    route_coords = None
    route_length_m = None
    route_error = None
    nearest_item = None
    nearest_air_m = None
    route_pool = official_records or display_records

    if display_records:
        if not official_records and candidate_records:
            st.warning("Bu aralıkta OSM `emergency=assembly_point` bulunamadı; rota aday park/bahçe/açık alanlara göre hesaplanacak.")

        nearest_item, nearest_air_m = find_nearest_assembly(
            st.session_state.assembly_user_lat,
            st.session_state.assembly_user_lon,
            route_pool,
        )
        if nearest_item:
            dest_lat = nearest_item.get("display_lat", nearest_item["lat"])
            dest_lon = nearest_item.get("display_lon", nearest_item["lon"])
            if nearest_air_m <= 30000:
                if local_roads_ready:
                    with st.spinner("Local yol dataset üzerinden en kısa rota hesaplanıyor..."):
                        route_coords, route_length_m, route_error = shortest_route_from_local_roads(
                            st.session_state.assembly_user_lat,
                            st.session_state.assembly_user_lon,
                            dest_lat,
                            dest_lon,
                        )
                    if route_error:
                        st.caption(f"Local rota denenemedi, online OSM fallback deneniyor: {route_error}")

                if route_coords is None and allow_online_route_fallback:
                    with st.spinner("OSM yaya yol ağı üzerinden en kısa rota hesaplanıyor..."):
                        route_coords, route_length_m, route_error = shortest_walk_route(
                            st.session_state.assembly_user_lat,
                            st.session_state.assembly_user_lon,
                            dest_lat,
                            dest_lon,
                        )
                elif route_coords is None and route_error is None:
                    route_error = "Local rota bulunamadı ve online fallback kapalı."
            else:
                route_error = "En yakın alan 30 km'den uzak; devasa yol ağı sorgusunu önlemek için rota çizilmedi."

    if nearest_item:
        route_cols = st.columns(4)
        route_cols[0].metric("En yakın hedef", nearest_item["toplanma_alani"] or "OSM alanı")
        route_cols[1].metric("Tür", nearest_item.get("category", "OSM"))
        route_cols[2].metric("Kuş uçuşu", f"{nearest_air_m / 1000:.2f} km")
        if route_length_m:
            route_cols[3].metric("Yaya rotası", f"{route_length_m / 1000:.2f} km")
        else:
            route_cols[3].metric("Yaya rotası", "Hesaplanamadı")
        if route_error:
            st.warning(f"Rota notu: {route_error}")
    elif not display_records:
        st.warning("Seçili yarıçapta OSM üzerinde uygun toplanma/açık alan bulunamadı. Yarıçapı artırmayı deneyebilirsin.")

    map_center = [st.session_state.assembly_user_lat, st.session_state.assembly_user_lon]
    assembly_map = folium.Map(
        location=map_center,
        zoom_start=14 if search_radius_km <= 5 else 12,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
    ).add_to(assembly_map)

    if display_records:
        from folium.plugins import MarkerCluster
        cluster = MarkerCluster(name="OSM alanları")
        for item in display_records:
            lat = item.get("display_lat", item["lat"])
            lon = item.get("display_lon", item["lon"])
            name = item["toplanma_alani"] or "OSM Alanı"
            category = item.get("category", "Aday Alan")
            source = item.get("source", "OSM")
            note = item.get("note", "")
            
            popup_html = f"<strong>{name}</strong><br>{category}<br>Kaynak: {source}<br>{note}"
            icon_color = "green" if "resmi" in category.lower() else "orange"
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=name,
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(cluster)
        cluster.add_to(assembly_map)

    folium.Marker(
        [st.session_state.assembly_user_lat, st.session_state.assembly_user_lon],
        popup="Bulunduğun konum",
        tooltip="Bulunduğun konum",
        icon=folium.Icon(color="blue", icon="user"),
    ).add_to(assembly_map)

    if nearest_item:
        nearest_lat = nearest_item.get("display_lat", nearest_item["lat"])
        nearest_lon = nearest_item.get("display_lon", nearest_item["lon"])
        icon_color = "green" if nearest_item.get("priority") == 0 else "orange"
        folium.Marker(
            [nearest_lat, nearest_lon],
            popup=nearest_item["toplanma_alani"] or "En yakın OSM alanı",
            tooltip="En yakın hedef",
            icon=folium.Icon(color=icon_color, icon="flag"),
        ).add_to(assembly_map)

        if route_coords:
            folium.PolyLine(
                route_coords,
                color="#0077ff",
                weight=6,
                opacity=0.85,
                tooltip="En kısa yaya rotası",
            ).add_to(assembly_map)
        else:
            folium.PolyLine(
                [
                    [st.session_state.assembly_user_lat, st.session_state.assembly_user_lon],
                    [nearest_lat, nearest_lon],
                ],
                color="#ff7a00",
                weight=4,
                opacity=0.75,
                dash_array="8, 8",
                tooltip="Kuş uçuşu bağlantı",
            ).add_to(assembly_map)

    folium.LayerControl(collapsed=True).add_to(assembly_map)

    map_output = st_folium(
        assembly_map,
        width="100%",
        height=680,
        key=f"osm_assembly_map_{search_radius_km}_{include_candidate_open_areas}_{len(display_records)}",
    )

    if map_output and map_output.get("last_clicked"):
        clicked_lat = map_output["last_clicked"]["lat"]
        clicked_lon = map_output["last_clicked"]["lng"]
        if (
            abs(clicked_lat - st.session_state.assembly_user_lat) > 1e-7
            or abs(clicked_lon - st.session_state.assembly_user_lon) > 1e-7
        ):
            st.session_state.assembly_user_lat = clicked_lat
            st.session_state.assembly_user_lon = clicked_lon
            st.session_state.assembly_location_source = "Harita tıklaması"
            st.rerun()

