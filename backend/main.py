import base64
import datetime
import importlib
import io
import json
import math
import os
import site
import sys
import threading
import traceback
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from apps.sos_management.ui import render_sos_screen


BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR / "apps"
NLP_ROOT = APPS_DIR / "disaster_nlp"
ROAD_ROOT = APPS_DIR / "road_damage"
RISK_ROOT = APPS_DIR / "earthquake_risk"
CAMERA_ROOT = APPS_DIR / "camera_detection"

NLP_MODEL_DIR = NLP_ROOT / "models" / "2kveri"
RISK_CSV = RISK_ROOT / "data" / "query.csv"
ROAD_DEFAULT_MODEL = ROAD_ROOT / "models" / "optimized_mitb4_focal_dice30.pth"

TURKEY_PROVINCES = [
    "Adana", "Adiyaman", "Afyonkarahisar", "Agri", "Amasya", "Ankara", "Antalya",
    "Artvin", "Aydin", "Balikesir", "Bilecik", "Bingol", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Canakkale", "Cankiri", "Corum", "Denizli", "Diyarbakir",
    "Edirne", "Elazig", "Erzincan", "Erzurum", "Eskisehir", "Gaziantep", "Giresun",
    "Gumushane", "Hakkari", "Hatay", "Isparta", "Mersin", "Istanbul", "Izmir",
    "Kars", "Kastamonu", "Kayseri", "Kirklareli", "Kirsehir", "Kocaeli", "Konya",
    "Kutahya", "Malatya", "Manisa", "Kahramanmaras", "Mardin", "Mugla", "Mus",
    "Nevsehir", "Nigde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop",
    "Sivas", "Tekirdag", "Tokat", "Trabzon", "Tunceli", "Sanliurfa", "Usak",
    "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kirikkale",
    "Batman", "Sirnak", "Bartin", "Ardahan", "Igdir", "Yalova", "Karabuk",
    "Kilis", "Osmaniye", "Duzce",
]

RISK_CITY_DEFAULT_COORDS = {
    "Hatay": (36.20, 36.16),
    "Kahramanmaras": (37.57, 36.93),
    "Gaziantep": (37.06, 37.38),
    "Malatya": (38.35, 38.30),
    "Adiyaman": (37.76, 38.27),
    "Istanbul": (41.0082, 28.9784),
    "Izmir": (38.4237, 27.1428),
    "Ankara": (39.9334, 32.8597),
    "Bursa": (40.1885, 29.0610),
    "Antalya": (36.8969, 30.7133),
}

ROAD_CITIES = {
    "Antakya (Hatay)": [36.20, 36.16],
    "Kahramanmaras": [37.57, 36.93],
    "Gaziantep": [37.06, 37.38],
    "Malatya": [38.35, 38.30],
    "Adiyaman": [37.76, 38.27],
}

NLP_SAMPLE_TEXTS = [
    "Hatay antakya cebrail mahallesi yıkıldı, enkaz altında kalanlar var lütfen yardım edin ses geliyor!",
    "Gaziantep nurdağı yolu kapalı tırlar geçemiyor, toprak kayması var.",
    "Kahramanmaraş merkezde 50 çadır ve bol miktarda bebek maması ihtiyacı çok acil.",
    "İskenderun liman çevresinde ağır hasarlı binalar var, ekipler ulaşmakta zorlanıyor.",
    "Malatya battalgazide apartman çöktü, içeride yaşlı bir çift mahsur kaldı.",
    "Adıyaman merkezde acil kan, su ve battaniye ihtiyacı var.",
    "Diyarbakır yolu üzerinde köprü girişinde çatlak var, araç geçişi riskli.",
    "Şanlıurfa akçakale tarafında lojistik araçlar kapalı yol nedeniyle ilerleyemiyor.",
]


def add_project_site_packages(project_root):
    for env_name in [".venv", "venv"]:
        env_path = project_root / env_name
        if not env_path.exists():
            continue
        for site_path in env_path.glob("lib/python*/site-packages"):
            site.addsitedir(str(site_path))


for project_root in [NLP_ROOT, ROAD_ROOT, RISK_ROOT, CAMERA_ROOT]:
    add_project_site_packages(project_root)


@contextmanager
def temporary_sys_path(*paths):
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
def temporary_cwd(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def clear_module_cache(prefixes):
    for module_name in list(sys.modules.keys()):
        if any(module_name == prefix or module_name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(module_name, None)


def distance_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        math.radians, [lat1, lon1, lat2, lon2]
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

    if geometry_type == "LineString" or geometry_type == "MultiPoint":
        for coord in coordinates:
            if len(coord) >= 2:
                yield coord[1], coord[0]
        return

    if geometry_type == "MultiLineString" or geometry_type == "Polygon":
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


@st.cache_data(show_spinner=False)
def load_geojson_file(path_str):
    with open(path_str, "r", encoding="utf-8") as handle:
        return json.load(handle)


@st.cache_data(show_spinner=False)
def get_filtered_fault_geojson(path_str, center_lat, center_lon, radius_km=180.0):
    geojson_data = load_geojson_file(path_str)
    filtered_features = []

    for feature in geojson_data.get("features", []):
        if geometry_is_near_point(
            feature.get("geometry"),
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
        ):
            filtered_features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": filtered_features,
    }


def loading_screen_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #08101a 0%, #0d1724 100%);
        }
        .boot-wrap {
            max-width: 760px;
            margin: 8rem auto 2rem auto;
            padding: 2rem 2.2rem;
            border-radius: 24px;
            background: rgba(9, 18, 29, 0.94);
            border: 1px solid rgba(108, 229, 255, 0.14);
            box-shadow: 0 24px 70px rgba(2, 6, 23, 0.45);
            text-align: center;
        }
        .boot-title {
            color: #f4fbff;
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }
        .boot-copy {
            color: #aebfd1;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_boot_screen():
    loading_screen_css()
    st.markdown(
        """
        <div class="boot-wrap">
            <div class="boot-title">QuakeMind yukleniyor</div>
            <div class="boot-copy">
                Tum modeller, yardimci kutuphaneler ve veri motorlari ilk acilista hazirlaniyor.
                Islem tamamlaninca ana arayuz otomatik olarak acilacak.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_nlp_pipeline():
    clear_module_cache(["src"])
    with temporary_sys_path(NLP_ROOT), temporary_cwd(NLP_ROOT):
        from src.pipeline import DisasterPipeline

        return DisasterPipeline()


@st.cache_resource
def load_road_runtime():
    clear_module_cache(["utils"])
    with temporary_sys_path(ROAD_ROOT), temporary_cwd(ROAD_ROOT):
        from apps.road_damage.utils.fetcher import fetch_satellite_area, get_osm_roads_overpass, get_wayback_versions, search_oam_images
        from apps.road_damage.utils.inference import load_simple_model, run_inference
        from apps.road_damage.utils.network import analyze_road_network_graph, calculate_route
        from apps.road_damage.utils.local_osm import (
            OSM_DATA_DIR,
            has_local_roads_dataset,
            has_local_safety_dataset,
            load_local_safety_areas,
            shortest_route_from_local_roads,
        )

        return {
            "fetch_satellite_area": fetch_satellite_area,
            "get_osm_roads_overpass": get_osm_roads_overpass,
            "get_wayback_versions": get_wayback_versions,
            "search_oam_images": search_oam_images,
            "load_simple_model": load_simple_model,
            "run_inference": run_inference,
            "analyze_road_network_graph": analyze_road_network_graph,
            "calculate_route": calculate_route,
            "OSM_DATA_DIR": OSM_DATA_DIR,
            "has_local_roads_dataset": has_local_roads_dataset,
            "has_local_safety_dataset": has_local_safety_dataset,
            "load_local_safety_areas": load_local_safety_areas,
            "shortest_route_from_local_roads": shortest_route_from_local_roads,
        }


@st.cache_resource
def load_road_model(model_path):
    runtime = load_road_runtime()
    with temporary_cwd(ROAD_ROOT):
        model, device = runtime["load_simple_model"](model_path)
    return model, device


@st.cache_resource
def load_risk_bundle():
    clear_module_cache(["risk_engine"])
    with temporary_sys_path(RISK_ROOT), temporary_cwd(RISK_ROOT):
        risk_module = importlib.import_module("risk_engine")
        engine = risk_module.EarthquakeRiskEngine(csv_path=str(RISK_CSV.resolve()))
        return engine, risk_module


def boot_resources():
    if st.session_state.get("boot_complete"):
        return

    render_boot_screen()
    progress = st.progress(0)
    status = st.empty()
    errors = {}
    steps = [
        ("Disaster NLP modeli yukleniyor", load_nlp_pipeline),
        ("RoadDamage kutuphaneleri hazirlaniyor", load_road_runtime),
        ("RoadDamage modeli yukleniyor", lambda: load_road_model(str(ROAD_DEFAULT_MODEL.resolve()))),
        ("Deprem risk motoru yukleniyor", load_risk_bundle),
    ]

    total = len(steps)
    for index, (label, action) in enumerate(steps, start=1):
        status.info(label)
        try:
            action()
        except Exception:
            errors[label] = traceback.format_exc()
        progress.progress(index / total)

    st.session_state.boot_complete = True
    st.session_state.boot_errors = errors
    st.rerun()


def show_boot_errors():
    errors = st.session_state.get("boot_errors", {})
    if not errors:
        return
    with st.expander("Yukleme sirasinda yakalanan hatalar", expanded=False):
        for label, trace in errors.items():
            st.error(label)
            st.code(trace)


def get_b64_image(image_arr):
    from PIL import Image

    img = Image.fromarray(image_arr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def render_nlp_screen():
    st.title("🚨 P-5: Afet Metin & Multimodal Veri Füzyonu GUI")
    st.markdown(
        """
        Bu arayüz, sosyal medyadan elde edilen kentsel afet verisinin uçtan uca analizini simüle etmektedir.
        1. **Zeyrek** ile metni sadeleştirir.
        2. **BERTurk Sınıflandırma** ile P-5 kategorilerini belirler ve güven skoru ölçer.
        3. **BERTurk NER** ile metinden adres bilgisini çeker.
        4. **GeoPy** ile çekilen adresi harita koordinatlarına dönüştürür.
        5. Veriyi **Düşük Bant Genişliğine (JSON)** optimize eder.
        """
    )
    st.caption("Uygulama ilk açılışta model yüklediği için 20-60 saniye bekletebilir.")

    if "nlp_selected_sample" not in st.session_state:
        st.session_state.nlp_selected_sample = "Lütfen kendi metnini kullan..."
    if "nlp_user_input" not in st.session_state:
        st.session_state.nlp_user_input = ""
    if "nlp_analysis_result" not in st.session_state:
        st.session_state.nlp_analysis_result = None
    if "nlp_analysis_error" not in st.session_state:
        st.session_state.nlp_analysis_error = None

    def handle_sample_change():
        selected = st.session_state.nlp_selected_sample
        if selected == "Lütfen kendi metnini kullan...":
            return
        st.session_state.nlp_user_input = selected

    pipeline = None
    pipeline_error = None
    try:
        pipeline = load_nlp_pipeline()
    except Exception as exc:
        pipeline_error = exc

    if pipeline_error:
        st.error("Pipeline baslatilamadi. Hata detayi asagida.")
        st.exception(pipeline_error)
        return

    st.subheader("Simülasyon Verisi Gönder")
    sample_options = ["Lütfen kendi metnini kullan..."] + NLP_SAMPLE_TEXTS

    st.selectbox(
        "Örnek Test Verisi Seçin",
        sample_options,
        key="nlp_selected_sample",
        on_change=handle_sample_change,
    )

    st.text_area(
        "Veya Sosyal medya (X) metni girin:",
        key="nlp_user_input",
        height=180,
    )

    if st.button("Uçtan Uca Analizi Çalıştır", type="primary", key="nlp_run_btn"):
        if not st.session_state.nlp_user_input.strip():
            st.session_state.nlp_analysis_result = None
            st.session_state.nlp_analysis_error = "Lütfen analiz edilecek bir metin girin."
        else:
            with st.spinner("Metin işleniyor, konum çıkartılıyor..."):
                try:
                    result = pipeline.process_tweet(st.session_state.nlp_user_input)
                    st.session_state.nlp_analysis_result = result
                    st.session_state.nlp_analysis_error = None if result else "Bu girdi, afet yönetim çerçevesine uymadığı için (Alakasız) reddedildi."
                except Exception as exc:
                    st.session_state.nlp_analysis_result = None
                    st.session_state.nlp_analysis_error = str(exc)

    if st.session_state.nlp_analysis_error:
        st.warning(st.session_state.nlp_analysis_error)

    result = st.session_state.nlp_analysis_result
    if result:
        import folium
        from streamlit_folium import st_folium

        col1, col2 = st.columns([1, 1])
        with col1:
            st.success("✅ Veri İşleme Başarılı!")
            st.metric("Tespit Edilen Kategori", result["kategori"])
            st.metric("Model Güven Skoru", f"%{result['guven_skoru'] * 100:.1f}")

            aciliyet = result["aciliyet"]
            st.metric("P-5 Aciliyet Seviyesi (1-5)", aciliyet)
            if aciliyet >= 4:
                st.error("⚠️ KRİTİK ACİLİYET DURUMU. Önceliklendirme Gereklidir.")
            elif aciliyet == 3:
                st.warning("🚧 Rota Bildirimi. Lojistik ve Ulaşım Algoritmaları Tetiklenmelidir.")

        with col2:
            st.markdown("### 📡 Düşük Bant Genişliği İletim Formatı (P-5 JSON V1)")
            st.code(json.dumps(result, ensure_ascii=False, indent=4), language="json")

        st.markdown("### 🌍 Varlık Çıkarımı (NER) ve Uzamsal Haritalama")
        coords = result.get("konum")
        location_text = result.get("konum_metin")
        if coords:
            if location_text:
                st.caption(f"Geocoding sorgusu için kullanılan konum metni: `{location_text}`")
            st.info(f"Metin içerisinden otonom olarak konum çıkartıldı ve Geocoding çalıştırıldı: Enlem: {coords[0]}, Boylam: {coords[1]}")
            m = folium.Map(location=coords, zoom_start=15)
            folium.Marker(coords, popup=result["kategori"], tooltip="Tespit Edilen Konum").add_to(m)
            st_folium(m, height=400, use_container_width=True, key="nlp_map")
        else:
            st.info("Bu metin içerisinde açık bir konum bilgisine rastlanmadı veya algoritmalar spesifik bir koordinata çözümleyemedi.")

        location_candidates = result.get("konum_adaylari") or []
        if location_candidates:
            st.caption("Çıkarılan konum adayları: " + " | ".join(location_candidates))

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Mimari Bileşenler")
        st.caption("- Zemberek NLP Modülü (Zeyrek)")
        st.caption("- Sınıflandırma Modeli: Hugging Face / DISASTER_MODEL_NAME")
        st.caption("- HuggingFace: yhaslan/turkish-earthquake-tweets-ner")
        st.caption("- GeoPy & Folium (Harita)")


def road_haversine_m(lat1, lon1, lat2, lon2):
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


def road_bbox_from_center(lat, lon, radius_km):
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.2))
    return (
        lon - lon_delta,
        lat - lat_delta,
        lon + lon_delta,
        lat + lat_delta,
    )


def road_clean_osm_value(value):
    import pandas as pd

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
def get_road_osm_safety_areas(bbox, include_candidate_open_areas):
    import osmnx as ox

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
        access = road_clean_osm_value(row.get("access")).lower()
        if access in {"private", "no"}:
            continue

        emergency = road_clean_osm_value(row.get("emergency"))
        leisure = road_clean_osm_value(row.get("leisure"))
        landuse = road_clean_osm_value(row.get("landuse"))
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
        name = road_clean_osm_value(row.get("name")) or category
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


def find_road_nearest_assembly(user_lat, user_lon, records):
    nearest = None
    nearest_distance = float("inf")
    for item in records:
        lat = item.get("display_lat", item["lat"])
        lon = item.get("display_lon", item["lon"])
        distance = road_haversine_m(user_lat, user_lon, lat, lon)
        if distance < nearest_distance:
            nearest = item
            nearest_distance = distance
    return nearest, nearest_distance


@st.cache_data(ttl=1800, show_spinner=False)
def get_road_shortest_walk_route(user_lat, user_lon, dest_lat, dest_lon):
    import networkx as nx
    import osmnx as ox

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


def get_road_high_accuracy_geolocation(component_key="road_assembly_high_accuracy_geolocation"):
    from streamlit_js_eval import streamlit_js_eval

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


def render_road_screen():
    import cv2
    import folium
    import numpy as np
    from folium.plugins import Draw, MarkerCluster, SideBySideLayers
    from streamlit_folium import st_folium

    runtime = load_road_runtime()
    fetch_satellite_area = runtime["fetch_satellite_area"]
    get_osm_roads_overpass = runtime["get_osm_roads_overpass"]
    get_wayback_versions = runtime["get_wayback_versions"]
    search_oam_images = runtime["search_oam_images"]
    analyze_road_network_graph = runtime["analyze_road_network_graph"]
    run_inference = runtime["run_inference"]
    calculate_route = runtime["calculate_route"]
    OSM_DATA_DIR = runtime["OSM_DATA_DIR"]
    has_local_roads_dataset = runtime["has_local_roads_dataset"]
    has_local_safety_dataset = runtime["has_local_safety_dataset"]
    load_local_safety_areas = runtime["load_local_safety_areas"]
    shortest_route_from_local_roads = runtime["shortest_route_from_local_roads"]

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1rem; }
        h1 { color: #2E86C1; }
        .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
        .stProgress > div > div > div > div { background-color: #2E86C1; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "road_analysis_result" not in st.session_state:
        st.session_state.road_analysis_result = None
    if "road_logistic_data" not in st.session_state:
        st.session_state.road_logistic_data = None
    if "road_oam_results" not in st.session_state:
        st.session_state.road_oam_results = None
    if "road_last_clicked" not in st.session_state:
        st.session_state.road_last_clicked = None

    with st.sidebar:
        st.markdown("---")
        st.title("🛰️ RDA Control Panel")
        st.info("Analyze road damage using AI (Segformer).")

        offline_only = st.checkbox(
            "Offline OSM modu",
            value=False,
            help="Açıksa hasar analizindeki yol maskesi sadece local data/osm/roads.gpkg dosyasından üretilir.",
            key="road_offline_only",
        )
        os.environ["QUAKEMIND_OFFLINE_ONLY"] = "1" if offline_only else "0"
        if offline_only and not has_local_roads_dataset():
            st.warning("Offline mod açık ama local roads.gpkg bulunamadı.")

        st.header("1. Location & Data")
        selected_city_name = st.selectbox("📍 Jump to City", list(ROAD_CITIES.keys()), key="road_selected_city")
        city_coords = ROAD_CITIES[selected_city_name]

        st.markdown("---")

        wayback_versions = get_wayback_versions()
        opt_google = "Google Maps (Latest / High Res)"
        opt_oam = "OpenAerialMap (Event Specific)"
        wayback_options = []
        wayback_map = {}
        if wayback_versions:
            wayback_versions.sort(key=lambda item: item["date"], reverse=True)
            wayback_map = {f"Esri Wayback ({item['date']})": item for item in wayback_versions}
            wayback_options = list(wayback_map.keys())

        source_options = [opt_google, opt_oam] + wayback_options
        selected_source = st.selectbox("📡 Satellite Source", source_options, key="road_source")

        provider = "Esri Wayback" if "Wayback" in selected_source else "Google Maps"
        selected_wayback = wayback_map.get(selected_source)
        selected_oam_url = None

        if selected_source == opt_oam:
            provider = "OpenAerialMap"
            st.caption("Search for post-disaster imagery (e.g. Feb 2023)")
            c1, c2 = st.columns(2)
            d_start = c1.date_input("Start", datetime.date(2023, 2, 6), key="road_oam_start")
            d_end = c2.date_input("End", datetime.date(2023, 2, 28), key="road_oam_end")

            if st.button("🔎 Search Images", key="road_search_oam"):
                if st.session_state.road_last_clicked:
                    lat, lon = st.session_state.road_last_clicked
                    bbox = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)
                else:
                    lat, lon = city_coords
                    bbox = (lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05)

                with st.spinner("Searching OAM..."):
                    st.session_state.road_oam_results = search_oam_images(bbox, d_start, d_end)

            if st.session_state.road_oam_results:
                res_oam = st.session_state.road_oam_results
                st.success(f"Found {len(res_oam)} images.")
                oam_opts = {f"{item['date']} - {item['provider']}": item for item in res_oam}
                selected_oam = st.selectbox("Select Image", list(oam_opts.keys()), key="road_selected_oam")
                if selected_oam:
                    selected_oam_url = oam_opts[selected_oam]["tms_url"]

        st.header("2. Analysis Settings")
        with st.expander("⚙️ Fine-Tuning", expanded=True):
            zoom_level = 18
            st.markdown("#### Detection Parameters")
            damage_booster = st.slider("🔥 Damage Sensitivity Booster", 1.0, 10.0, 3.5, 0.5, key="road_damage_booster")
            threshold = st.slider("📉 Detection Threshold", 0.05, 0.95, 0.40, 0.05, key="road_threshold")
            line_width = 6

            st.markdown("#### Model Path")
            model_path = st.text_input("📁 Pytorch Weights (.pth)", value=str(ROAD_DEFAULT_MODEL), key="road_model_path")
            use_imagenet_norm = st.checkbox("🔬 ImageNet Normalizasyonu", value=True, key="road_imagenet")
            postprocess_label = st.selectbox("🧹 Post-Processing", ["Kapalı (0)", "Hafif (1)", "Güçlü (2)"], index=2, key="road_post")
            postprocess_level = int(postprocess_label.split("(")[1][0])

        analyze_btn = st.button("🚀 Start Analysis", type="primary", key="road_analyze")
        if st.button("🔄 Reset Analysis", key="road_reset"):
            st.session_state.road_analysis_result = None
            st.session_state.road_logistic_data = None
            st.rerun()

    st.title("Satellite Road Damage Assessment")

    damage_tab, assembly_tab = st.tabs(["🛰️ Hasar Analizi", "🗺️ Toplanma Alanları"])

    with damage_tab:
        m = folium.Map(location=city_coords, zoom_start=15)
        if provider == "Esri Wayback" and selected_wayback:
            url = f"https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{selected_wayback['id']}/{{z}}/{{y}}/{{x}}"
            folium.TileLayer(tiles=url, attr="Esri", name="Wayback").add_to(m)
        elif provider == "Google Maps":
            folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", name="Google Satellite").add_to(m)
        elif provider == "OpenAerialMap" and selected_oam_url:
            folium.TileLayer(tiles=selected_oam_url, attr="OAM", name="OAM Layer").add_to(m)

        draw = Draw(
            export=False,
            position="topleft",
            draw_options={
                "polyline": False,
                "polygon": True,
                "circle": False,
                "marker": False,
                "circlemarker": False,
                "rectangle": True,
            },
        )
        draw.add_to(m)
        m.add_child(folium.LatLngPopup())
        output = st_folium(m, height=450, width="100%", key="road_main_map")

        click_lat, click_lon = None, None
        draw_bbox = None
        if output.get("last_active_drawing"):
            geom = output["last_active_drawing"]["geometry"]
            if geom["type"] in ["Polygon", "Rectangle"]:
                coords = np.array(geom["coordinates"][0])
                lon_min, lat_min = coords.min(axis=0)
                lon_max, lat_max = coords.max(axis=0)
                draw_bbox = (lon_min, lat_min, lon_max, lat_max)
                click_lat = (lat_min + lat_max) / 2
                click_lon = (lon_min + lon_max) / 2
                st.session_state.road_last_clicked = (click_lat, click_lon)
                st.success("📌 Alan seçildi! Analizi başlatabilirsiniz.")
        elif output.get("last_clicked"):
            click_lat = output["last_clicked"]["lat"]
            click_lon = output["last_clicked"]["lng"]
            st.session_state.road_last_clicked = (click_lat, click_lon)
            st.caption(f"Selected: {click_lat:.5f}, {click_lon:.5f}")
        else:
            st.info("👆 Haritadan bir noktaya tıklayın veya soldaki çizim aracı ile özel bir alan seçin.")

        st.markdown("---")

        if analyze_btn:
            if st.session_state.road_logistic_data:
                st.session_state.road_logistic_data = None

            if not click_lat and not draw_bbox:
                st.warning("Lütfen önce haritadan bir alan seçin veya bir noktaya tıklayın.")
            else:
                progress_bar = st.progress(0, text="Starting Analysis...")
                status_text = st.empty()
                try:
                    status_text.text("1/4 Downloading Satellite Imagery...")
                    progress_bar.progress(10)

                    wayback_id = selected_wayback["id"] if selected_wayback else None
                    provider_code = "google" if provider == "Google Maps" else "custom" if provider == "OpenAerialMap" else "esri"
                    custom_url = selected_oam_url if provider == "OpenAerialMap" else None

                    img, bounds = fetch_satellite_area(
                        lat=click_lat,
                        lon=click_lon,
                        bbox=draw_bbox,
                        zoom_level=zoom_level,
                        wayback_id=wayback_id,
                        provider=provider_code,
                        custom_url=custom_url,
                    )

                    if img is None:
                        st.error("FAILED to download imagery. Try a different zoom level or provider.")
                        st.stop()

                    progress_bar.progress(30)
                    status_text.text("2/4 Fetching Road Network (OSM via Overpass)...")
                    w, h = img.size
                    road_mask = get_osm_roads_overpass(bounds, w, h, thickness=line_width)
                    road_mask_binary = (road_mask > 0).astype(np.uint8)

                    status_text.text("3/4 Preprocessing & Model Loading...")
                    progress_bar.progress(60)
                    resolved_model = Path(model_path)
                    if not resolved_model.is_absolute():
                        resolved_model = (ROAD_ROOT / resolved_model).resolve()
                    model, device = load_road_model(str(resolved_model))
                    if model is None:
                        st.error("Model yüklenemedi! Dosya yolunu kontrol edin.")
                        st.stop()

                    status_text.text("4/4 Running AI Inference (Segformer)...")
                    progress_bar.progress(70)
                    raw_probs, boosted_probs, pred_mask_binary, intersection, img_np = run_inference(
                        img,
                        road_mask_binary,
                        model,
                        device,
                        damage_booster,
                        threshold,
                        use_imagenet_norm,
                        postprocess_level,
                    )
                
                    status_text.text("5/5 Graph matrisi çıkarılıyor ve lojistik ağ hesaplanıyor...")
                    progress_bar.progress(90)
                
                    w, h = img.size
                    G, safe_G, safe_edges, blocked_edges = analyze_road_network_graph(bounds, w, h, intersection)
                
                    if G is not None:
                        st.session_state.road_logistic_data = {
                            "safe_G": safe_G,
                            "safe_edges": safe_edges,
                            "blocked_edges": blocked_edges,
                            "bounds": bounds,
                            "total": len(safe_edges) + len(blocked_edges),
                            "blocked_count": len(blocked_edges),
                        }

                    progress_bar.progress(100)
                    status_text.text("Analysis Complete!")
                    st.session_state.road_analysis_result = {
                        "original_img": img_np,
                        "road_mask": road_mask_binary,
                        "raw_probs": raw_probs,
                        "bounds": bounds,
                        "damage_booster": damage_booster,
                        "threshold": threshold,
                        "zoom_level": zoom_level,
                        "intersection": intersection,
                    }
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error during analysis: {exc}")
                    st.code(traceback.format_exc())
                    progress_bar.empty()

        if st.session_state.road_analysis_result:
            res = st.session_state.road_analysis_result
            current_probs = np.clip(res["raw_probs"] * res["damage_booster"], 0, 1)
            current_pred_mask = (current_probs > res["threshold"]).astype(np.uint8)
            current_intersection = cv2.bitwise_and(current_pred_mask, res["road_mask"])

            st.subheader("📝 Analysis Report")
            vis_img = res["original_img"].copy()

            yellow_overlay = np.zeros_like(vis_img)
            yellow_overlay[:] = [255, 255, 0]
            red_overlay = np.zeros_like(vis_img)
            red_overlay[:] = [255, 0, 0]
            cyan_overlay = np.zeros_like(vis_img)
            cyan_overlay[:] = [0, 255, 255]

            cyan_idx = (res["road_mask"] == 1) & (current_intersection == 0)
            blended_cyan = cv2.addWeighted(vis_img, 0.3, cyan_overlay, 0.7, 0)
            vis_img[cyan_idx] = blended_cyan[cyan_idx]

            mask_idx = (current_pred_mask == 1) & (current_intersection == 0)
            blended_yellow = cv2.addWeighted(vis_img, 0.5, yellow_overlay, 0.5, 0)
            vis_img[mask_idx] = blended_yellow[mask_idx]

            kernel = np.ones((9, 9), np.uint8)
            thick_intersection = cv2.dilate(current_intersection, kernel, iterations=2)
            intersection_idx = thick_intersection == 1
            blended_red = cv2.addWeighted(vis_img, 0.1, red_overlay, 0.9, 0)
            vis_img[intersection_idx] = blended_red[intersection_idx]

            st.markdown("### 🔍 Harita Üzerinde Kıyaslama (Öncesi / Sonrası)")
            center_lat = (res["bounds"][1] + res["bounds"][3]) / 2.0
            center_lon = (res["bounds"][0] + res["bounds"][2]) / 2.0
            cmp_map = folium.Map(location=[center_lat, center_lon], zoom_start=res["zoom_level"])
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
            SideBySideLayers(layer_left=left_layer, layer_right=right_layer).add_to(cmp_map)
            st_folium(cmp_map, width="100%", height=500, key="road_swipe_map")

            st.markdown(
                """
                <div style="background-color: #0E1117; padding: 15px; border-radius: 8px; border: 1px solid #333; display: flex; justify-content: space-around; margin-top: 10px;">
                    <span style="color: #00FFFF; font-weight: bold; font-size: 1.1em;">■ Açık Yol (OSM)</span>
                    <span style="color: #FFFF00; font-weight: bold; font-size: 1.1em;">■ Tespit Edilen Yıkıntı / Enkaz</span>
                    <span style="color: #FF0000; font-weight: bold; font-size: 1.1em;">■ Yol Üzerindeki Yıkıntı (Kapalı Yol)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### 🧩 Diagnostik")
            c1, c2, c3, c4 = st.columns(4)
            c1.image((current_pred_mask * 255).astype(np.uint8), caption="Model Yıkıntı Tahmini", use_container_width=True)
            c2.image((res["road_mask"] * 255).astype(np.uint8), caption="OSM Yol Maskesi", use_container_width=True)
            c3.image((current_intersection * 255).astype(np.uint8), caption="Yol & Yıkıntı Kesişimi", use_container_width=True)
            seg_overlay = res["original_img"].copy()
            damage_color = np.zeros_like(seg_overlay)
            damage_color[:] = [255, 50, 50]
            damage_idx = current_pred_mask == 1
            blended = cv2.addWeighted(seg_overlay, 0.4, damage_color, 0.6, 0)
            seg_overlay[damage_idx] = blended[damage_idx]
            c4.image(seg_overlay, caption="Uydu + Segmentasyon", use_container_width=True)

            st.markdown("---")
            st.markdown("### 🚑 Lojistik ve Rota Analizi")
            st.info("Bu modül, tespit edilen enkazları mevcut yol ağının üzerine bindirerek hangi sokakların kapalı olduğunu hesaplar.")

            # Lojistik analiz artık otomatik olarak yapılıyor

            if st.session_state.road_logistic_data:
                data = st.session_state.road_logistic_data
                st.success(f"Yol Ağı Analizi Tamamlandı! Toplam {data['total']} sokak incelendi. {data['blocked_count']} tanesi ulaşıma kapalı.")
                if "route_start" not in st.session_state:
                    st.session_state.route_start = None
                if "route_end" not in st.session_state:
                    st.session_state.route_end = None

                from folium.plugins import AntPath

                st.info("📍 Haritada iki farklı noktaya tıklayarak Başlangıç ve Hedef belirleyin. Sistem en kısa güvenli rotayı çizecektir.")

                center_lat = (data["bounds"][1] + data["bounds"][3]) / 2.0
                center_lon = (data["bounds"][0] + data["bounds"][2]) / 2.0
                route_map = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="CartoDB dark_matter")
            
                safe_lines = [[(lat, lon) for lon, lat in line.coords] for _, _, _, line in data["safe_edges"]]
                if safe_lines:
                    folium.PolyLine(safe_lines, color="#00FF00", weight=4, opacity=0.8, tooltip="Erişime Açık Yol").add_to(route_map)
                blocked_lines = [[(lat, lon) for lon, lat in line.coords] for _, _, _, line in data["blocked_edges"]]
                if blocked_lines:
                    folium.PolyLine(blocked_lines, color="#FF0000", weight=4, opacity=0.8, dash_array="5, 5", tooltip="ENKAZ NEDENİYLE KAPALI").add_to(route_map)
            
                if st.session_state.route_start:
                    folium.Marker(st.session_state.route_start, popup="Başlangıç", icon=folium.Icon(color="blue", icon="play")).add_to(route_map)
                if st.session_state.route_end:
                    folium.Marker(st.session_state.route_end, popup="Hedef", icon=folium.Icon(color="green", icon="flag")).add_to(route_map)
                
                if st.session_state.route_start and st.session_state.route_end:
                    with st.spinner("A* ve Dijkstra ile rota hesaplanıyor..."):
                        route_dijkstra, route_astar = calculate_route(
                            data["safe_G"],
                            st.session_state.route_start[0], st.session_state.route_start[1],
                            st.session_state.route_end[0], st.session_state.route_end[1]
                        )
                
                    if route_dijkstra:
                        st.success("A* ve Dijkstra rotaları başarıyla bulundu!")
                        AntPath(
                            route_dijkstra,
                            color="#00FFFF",
                            weight=6,
                            opacity=0.9,
                            tooltip="En Kısa Rota (Animasyonlu)",
                            delay=400
                        ).add_to(route_map)
                    else:
                        st.error("Bu iki nokta arasında açık yollar üzerinden bir rota bulunamadı!")
                    
                route_map_output = st_folium(route_map, width="100%", height=500, key="road_logistic_map_viz", returned_objects=["last_clicked"])
            
                if route_map_output.get("last_clicked"):
                    click = route_map_output["last_clicked"]
                    click_coord = (click["lat"], click["lng"])
                
                    if st.session_state.get("last_processed_click") != click_coord:
                        st.session_state.last_processed_click = click_coord
                    
                        if st.session_state.route_start is None:
                            st.session_state.route_start = click_coord
                        elif st.session_state.route_end is None:
                            st.session_state.route_end = click_coord
                        else:
                            st.session_state.route_start = click_coord
                            st.session_state.route_end = None
                        st.rerun()

    with assembly_tab:
        st.subheader("OSM Toplanma ve Aday Açık Alan Haritası")
        st.caption(
            "Bu sekmede JSON dosyası kullanılmıyor. Veriler OpenStreetMap üzerinden canlı olarak çekiliyor: "
            "önce `emergency=assembly_point`, istenirse park/bahçe gibi aday açık alanlar."
        )

        fallback_center = city_coords
        if "road_assembly_user_lat" not in st.session_state:
            st.session_state.road_assembly_user_lat = fallback_center[0]
        if "road_assembly_user_lon" not in st.session_state:
            st.session_state.road_assembly_user_lon = fallback_center[1]
        if "road_assembly_location_source" not in st.session_state:
            st.session_state.road_assembly_location_source = "Seçili şehir merkezi"

        st.markdown("### Konum")
        st.info("Tarayıcı konum izni verdiğinde yüksek doğruluk modu ile birkaç ölçüm alınır; OSM sorgusu ve rota bu konuma göre yapılır.")

        geolocation = get_road_high_accuracy_geolocation()
        auto_location_available = False

        if geolocation and geolocation.get("coords"):
            coords = geolocation["coords"]
            detected_lat = coords.get("latitude")
            detected_lon = coords.get("longitude")
            if detected_lat is not None and detected_lon is not None:
                auto_location_available = True
                if (
                    abs(detected_lat - st.session_state.road_assembly_user_lat) > 1e-7
                    or abs(detected_lon - st.session_state.road_assembly_user_lon) > 1e-7
                ):
                    st.session_state.road_assembly_user_lat = float(detected_lat)
                    st.session_state.road_assembly_user_lon = float(detected_lon)
                    st.session_state.road_assembly_location_source = "Tarayıcı GPS"
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
        loc_col1.metric("Aktif enlem", f"{st.session_state.road_assembly_user_lat:.6f}")
        loc_col2.metric("Aktif boylam", f"{st.session_state.road_assembly_user_lon:.6f}")
        loc_col3.metric("Konum kaynağı", st.session_state.road_assembly_location_source)

        manual_refresh = False
        with st.expander("Konum alınamazsa manuel düzeltme", expanded=not auto_location_available):
            manual_lat = st.number_input(
                "Bulunduğun enlem",
                min_value=-90.0,
                max_value=90.0,
                value=float(st.session_state.road_assembly_user_lat),
                format="%.7f",
                key="road_assembly_manual_lat",
            )
            manual_lon = st.number_input(
                "Bulunduğun boylam",
                min_value=-180.0,
                max_value=180.0,
                value=float(st.session_state.road_assembly_user_lon),
                format="%.7f",
                key="road_assembly_manual_lon",
            )
            st.caption("Haritaya tıklayarak da konumu güncelleyebilirsin.")
            manual_refresh = st.button("Manuel konumla OSM verisini yenile", key="road_assembly_manual_refresh")

        if manual_refresh:
            st.session_state.road_assembly_user_lat = float(manual_lat)
            st.session_state.road_assembly_user_lon = float(manual_lon)
            st.session_state.road_assembly_location_source = "Manuel"
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
                key="road_assembly_data_source",
            )
        with source_col2:
            search_radius_km = st.slider(
                "OSM arama yarıçapı (km)",
                min_value=1,
                max_value=30,
                value=8,
                step=1,
                help="Büyük yarıçaplar Overpass sorgusunu yavaşlatabilir.",
                key="road_assembly_search_radius",
            )
        with source_col3:
            include_candidate_open_areas = st.checkbox(
                "Park/bahçe aday açık alanları da dahil et",
                value=True,
                help="Bunlar resmi toplanma alanı değildir; resmi alan yoksa rota için aday alternatif olarak kullanılır.",
                key="road_assembly_include_candidates",
            )
        with source_col4:
            allow_online_route_fallback = st.checkbox(
                "Local rota olmazsa online fallback",
                value=data_source != "Sadece local dataset",
                help="Kapalıysa rota sadece local roads.gpkg ile denenir.",
                key="road_assembly_allow_fallback",
            )

        osm_bbox = road_bbox_from_center(
            st.session_state.road_assembly_user_lat,
            st.session_state.road_assembly_user_lon,
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
                display_records, osm_error = get_road_osm_safety_areas(osm_bbox, include_candidate_open_areas)
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

            nearest_item, nearest_air_m = find_road_nearest_assembly(
                st.session_state.road_assembly_user_lat,
                st.session_state.road_assembly_user_lon,
                route_pool,
            )
            if nearest_item:
                dest_lat = nearest_item.get("display_lat", nearest_item["lat"])
                dest_lon = nearest_item.get("display_lon", nearest_item["lon"])
                if nearest_air_m <= 30000:
                    if local_roads_ready:
                        with st.spinner("Local yol dataset üzerinden en kısa rota hesaplanıyor..."):
                            route_coords, route_length_m, route_error = shortest_route_from_local_roads(
                                st.session_state.road_assembly_user_lat,
                                st.session_state.road_assembly_user_lon,
                                dest_lat,
                                dest_lon,
                            )
                        if route_error:
                            st.caption(f"Local rota denenemedi, online OSM fallback deneniyor: {route_error}")

                    if route_coords is None and allow_online_route_fallback:
                        with st.spinner("OSM yaya yol ağı üzerinden en kısa rota hesaplanıyor..."):
                            route_coords, route_length_m, route_error = get_road_shortest_walk_route(
                                st.session_state.road_assembly_user_lat,
                                st.session_state.road_assembly_user_lon,
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

        map_center = [st.session_state.road_assembly_user_lat, st.session_state.road_assembly_user_lon]
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
                    icon=folium.Icon(color=icon_color, icon="info-sign"),
                ).add_to(cluster)
            cluster.add_to(assembly_map)

        folium.Marker(
            [st.session_state.road_assembly_user_lat, st.session_state.road_assembly_user_lon],
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
                        [st.session_state.road_assembly_user_lat, st.session_state.road_assembly_user_lon],
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
            key=f"road_osm_assembly_map_{search_radius_km}_{include_candidate_open_areas}_{len(display_records)}",
        )

        if map_output and map_output.get("last_clicked"):
            clicked_lat = map_output["last_clicked"]["lat"]
            clicked_lon = map_output["last_clicked"]["lng"]
            if (
                abs(clicked_lat - st.session_state.road_assembly_user_lat) > 1e-7
                or abs(clicked_lon - st.session_state.road_assembly_user_lon) > 1e-7
            ):
                st.session_state.road_assembly_user_lat = clicked_lat
                st.session_state.road_assembly_user_lon = clicked_lon
                st.session_state.road_assembly_location_source = "Harita tıklaması"
                st.rerun()


def render_risk_screen():
    import pandas as pd
    st.markdown(
        """
        <style>
        .risk-panel {
            background: linear-gradient(180deg, #0b1c2c 0%, #12283f 100%);
            color: #f2f5f7;
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="risk-panel"><h1>Deprem Risk Paneli</h1><p>Şehir bazlı kısa ve uzun vadeli deprem risklerini hesaplar ve fay hatlarıyla birlikte haritalar.</p></div>', unsafe_allow_html=True)

    if "risk_result" not in st.session_state:
        st.session_state.risk_result = None
    if "risk_coords" not in st.session_state:
        st.session_state.risk_coords = None
    if "risk_city_quakes" not in st.session_state:
        st.session_state.risk_city_quakes = None
    if "risk_status" not in st.session_state:
        st.session_state.risk_status = "Hazır"

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Deprem Paneli")
        selected_city = st.selectbox("Şehir", TURKEY_PROVINCES, key="risk_selected_city")
        use_manual = st.checkbox("Manuel koordinat kullan", value=False, key="risk_use_manual")
        lat_default, lon_default = RISK_CITY_DEFAULT_COORDS.get(selected_city, (39.0, 35.0))
        if use_manual:
            manual_lat = st.number_input("Enlem", value=float(lat_default), format="%.6f", key="risk_manual_lat")
            manual_lon = st.number_input("Boylam", value=float(lon_default), format="%.6f", key="risk_manual_lon")
            manual_coords = (manual_lat, manual_lon)
        else:
            manual_coords = None

        refresh_data = st.button("🔄 Veriyi Güncelle", key="risk_refresh_data")
        run_risk = st.button("🌍 Deprem Riskini Hesapla", type="primary", key="risk_run_btn")

    engine = None
    risk_module = None
    risk_error = None
    try:
        engine, risk_module = load_risk_bundle()
    except Exception as exc:
        risk_error = exc

    if risk_error:
        st.error("Risk motoru baslatilamadi.")
        st.exception(risk_error)
        return

    if refresh_data:
        try:
            with temporary_sys_path(RISK_ROOT), temporary_cwd(RISK_ROOT):
                from data_manager import fetch_and_update_data
                message = fetch_and_update_data()
            st.session_state.risk_status = message
            st.success(message)
            load_risk_bundle.clear()
            engine, risk_module = load_risk_bundle()
        except Exception as exc:
            st.error(f"Veri guncellenemedi: {exc}")

    if run_risk:
        with st.spinner(f"{selected_city} için risk hesaplanıyor..."):
            try:
                result = engine.predict_city_risk(selected_city, manual_coords=manual_coords)
                st.session_state.risk_result = result
                if manual_coords:
                    st.session_state.risk_coords = manual_coords
                else:
                    st.session_state.risk_coords = (engine.last_lat, engine.last_lon)
                full_df = engine.df_full.copy()
                dists = risk_module.haversine(
                    st.session_state.risk_coords[0],
                    st.session_state.risk_coords[1],
                    full_df["latitude"].values,
                    full_df["longitude"].values,
                )
                st.session_state.risk_city_quakes = full_df[dists <= 150.0].copy()
                st.session_state.risk_status = f"{selected_city} icin risk hesabi tamamlandi"
            except Exception as exc:
                st.session_state.risk_result = None
                st.error(str(exc))

    st.caption(f"Durum: {st.session_state.risk_status}")

    if st.session_state.risk_result:
        st.subheader("Analiz Sonuçları")
        st.code(st.session_state.risk_result)
        lat, lon = st.session_state.risk_coords
        import folium
        from streamlit_folium import st_folium
        from folium.plugins import HeatMap, MarkerCluster

        st.subheader("Harita")
        map_tabs = st.tabs(["Genel Harita", "Isi Haritasi", "Teknik Katmanlar"])

        city_quakes = st.session_state.risk_city_quakes
        geojson_paths = [
            RISK_ROOT / "data" / "fault_maps" / "fay_haritası" / "gem_active_faults.geojson",
            RISK_ROOT / "data" / "fault_maps" / "fay_haritası" / "gem_active_faults_harmonized.geojson",
        ]
        filtered_fault_layers = []
        for path in geojson_paths:
            if path.exists():
                filtered_fault_layers.append(
                    (
                        path,
                        get_filtered_fault_geojson(
                            str(path),
                            round(lat, 4),
                            round(lon, 4),
                            radius_km=180.0,
                        ),
                    )
                )

        risk_map = folium.Map(location=[lat, lon], zoom_start=8, tiles=None, prefer_canvas=True)
        folium.TileLayer("CartoDB dark_matter", name="Koyu Mod").add_to(risk_map)
        folium.TileLayer("OpenStreetMap", name="Aydinlik Mod").add_to(risk_map)
        folium.Marker([lat, lon], tooltip=selected_city, popup=selected_city, icon=folium.Icon(color="red", icon="info-sign")).add_to(risk_map)
        for line in getattr(risk_module, "FAULT_LINES", []):
            if any(distance_km(lat, lon, point_lat, point_lon) <= 180.0 for point_lat, point_lon in line):
                folium.PolyLine(line, color="#ff5722", weight=2, opacity=0.6, tooltip="Ana Fay Hatti").add_to(risk_map)

        if city_quakes is not None and not city_quakes.empty:
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
                    ["mag", "time"], ascending=[False, False]
                ).head(250)
            for _, row in significant_quakes.iterrows():
                mag = row["mag"]
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

        total_fault_features = 0
        for path, geo_data in filtered_fault_layers:
            if geo_data.get("features"):
                total_fault_features += len(geo_data["features"])
                name = path.stem.replace("_", " ").title()
                folium.GeoJson(
                    geo_data,
                    name=f"Detayli Faylar: {name}",
                    zoom_on_click=False,
                    style_function=lambda _: {"color": "#ff9800", "weight": 1.5, "opacity": 0.5},
                ).add_to(risk_map)

        folium.LayerControl(collapsed=False).add_to(risk_map)

        with map_tabs[0]:
            st.caption("Harita etkileşimleri artık sayfayı yeniden yüklemez; yakın çevredeki fay segmentleri filtrelenerek gösterilir.")
            st_folium(
                risk_map,
                width=None,
                height=520,
                key="risk_map_full",
                use_container_width=True,
                returned_objects=[],
            )

        with map_tabs[1]:
            if city_quakes is not None and not city_quakes.empty:
                info_cols = st.columns(3)
                info_cols[0].metric("150 km icindeki deprem", len(city_quakes))
                info_cols[1].metric("Maksimum buyukluk", f"{city_quakes['mag'].max():.2f}")
                info_cols[2].metric("Ortalama derinlik", f"{city_quakes['depth'].mean():.1f} km")
                st.caption(f"Isi katmani {len(heat_data)} deprem kaydinin optimize edilmis orneklemi ile cizildi.")
                st_folium(
                    risk_map,
                    width=None,
                    height=520,
                    key="risk_heat_map",
                    use_container_width=True,
                    returned_objects=[],
                )
            else:
                st.info("Bu bolge icin gosterilecek deprem kaydi bulunamadi.")

        with map_tabs[2]:
            st.write("GeoJSON fay katmanlari:")
            for path, geo_data in filtered_fault_layers:
                st.write(f"- {path} -> {len(geo_data.get('features', []))} yakin segment")
            st.write(f"Toplam gosterilen detayli fay segmenti: {total_fault_features}")
            if city_quakes is not None and not city_quakes.empty:
                st.dataframe(city_quakes.sort_values("mag", ascending=False).head(20), use_container_width=True)
            else:
                st.info("Bolgesel deprem tablosu hazir degil.")

        st.markdown("---")
        st.caption("Canli kamera algilama modulu artik apps/camera_detection altinda bagimsiz bir uygulama olarak yer aliyor.")


def render_camera_screen():
    st.markdown(
        """
        <style>
        .camera-panel {
            background: linear-gradient(180deg, #101c17 0%, #183126 100%);
            color: #f3f7f4;
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="camera-panel"><h1>Kamera Tespiti</h1><p>Bu uygulama canli kamera akisinda catlak ve bina durumu modellerini ayri pencerelerde calistirir. Deprem risk akisindan bagimsizdir ve apps/camera_detection altina ayrildi.</p></div>',
        unsafe_allow_html=True,
    )

    if "camera_feature_running" not in st.session_state:
        st.session_state.camera_feature_running = False
    if "camera_feature_status" not in st.session_state:
        st.session_state.camera_feature_status = "Hazır"

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Kamera Tespiti")
        launch_camera = st.button("📷 Kamera Tespitini Baslat", type="primary", key="camera_feature_launch")

    with temporary_sys_path(CAMERA_ROOT):
        from app import get_camera_model_paths

    model_paths = get_camera_model_paths()

    info_cols = st.columns(2)
    info_cols[0].metric("Crack model", model_paths["crack_detection"].name)
    info_cols[1].metric("Building model", model_paths["building_detection"].name)

    st.write("Kullanilan model dosyalari:")
    st.write(f"- `{model_paths['crack_detection']}`")
    st.write(f"- `{model_paths['building_detection']}`")
    st.caption("Uygulama OpenCV pencereleri acarak calisir. Cikmak icin kamera penceresinde `q` tusuna basin.")

    if launch_camera and not st.session_state.camera_feature_running:
        def run_camera_feature():
            try:
                with temporary_sys_path(CAMERA_ROOT), temporary_cwd(CAMERA_ROOT):
                    from app import launch_camera_detection

                    launch_camera_detection()
            finally:
                st.session_state.camera_feature_running = False
                st.session_state.camera_feature_status = "Hazır"

        st.session_state.camera_feature_running = True
        st.session_state.camera_feature_status = "Kamera tespiti baslatildi"
        threading.Thread(target=run_camera_feature, daemon=True).start()
        st.success("Kamera tespiti ayri pencerede baslatildi.")

    status_cols = st.columns(2)
    status_cols[0].caption(f"Durum: {st.session_state.camera_feature_status}")
    status_cols[1].caption(
        "Calisiyor" if st.session_state.camera_feature_running else "Beklemede"
    )


def main():
    st.set_page_config(page_title="QuakeMind Unified Console", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    boot_resources()

    with st.sidebar:
        st.title("QuakeMind")
        selected_module = st.radio(
            "Modul Secin",
            [
                "Afet Metin Analizi",
                "Uydu Yol Hasar Analizi",
                "Deprem Risk Paneli",
                "Kamera Tespiti",
                "SOS Yönetimi",
            ],
            key="selected_module",
        )
        st.caption("Tum alt projeler tek Streamlit arayuzunde birlestirildi.")

    show_boot_errors()

    if selected_module == "Afet Metin Analizi":
        render_nlp_screen()
    elif selected_module == "Uydu Yol Hasar Analizi":
        render_road_screen()
    elif selected_module == "Deprem Risk Paneli":
        render_risk_screen()
    elif selected_module == "Kamera Tespiti":
        render_camera_screen()
    else:
        render_sos_screen()


if __name__ == "__main__":
    main()
