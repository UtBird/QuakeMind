from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import site
import importlib
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR / "apps"
NLP_ROOT = APPS_DIR / "disaster_nlp"
ROAD_ROOT = APPS_DIR / "road_damage"
RISK_ROOT = APPS_DIR / "earthquake_risk"
CAMERA_ROOT = APPS_DIR / "camera_detection"
MOBILE_TOOL_ROOT = BASE_DIR.parent / "quakemind" / "tool"

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

# Initialize engines
nlp_pipeline = None
risk_engine = None
road_runtime = None
road_runtime_error = None
road_runtime_lock = Lock()

print("Loading models...", flush=True)

try:
    clear_module_cache(["src"])
    with temporary_sys_path(NLP_ROOT), temporary_cwd(NLP_ROOT):
        from src.pipeline import DisasterPipeline
        nlp_pipeline = DisasterPipeline()
    print("NLP Pipeline loaded.", flush=True)
except Exception as e:
    print(f"Failed to load NLP: {e}", flush=True)

try:
    clear_module_cache(["risk_engine"])
    with temporary_sys_path(RISK_ROOT), temporary_cwd(RISK_ROOT):
        risk_module = importlib.import_module("risk_engine")
        RISK_CSV = RISK_ROOT / "data" / "query.csv"
        risk_engine = risk_module.EarthquakeRiskEngine(csv_path=str(RISK_CSV.resolve()))
    print("Risk Engine loaded.", flush=True)
except Exception as e:
    print(f"Failed to load Risk Engine: {e}", flush=True)


def _load_road_runtime():
    with temporary_sys_path(ROAD_ROOT), temporary_cwd(ROAD_ROOT):
        from utils.fetcher import (
            fetch_satellite_area,
            get_osm_roads_overpass,
            get_wayback_versions,
            search_oam_images,
        )
        from utils.inference import load_simple_model, run_inference
        from utils.network import analyze_road_network_graph

        model_path = str(ROAD_ROOT / "models" / "optimized_mitb4_focal_dice30.pth")
        model, device = load_simple_model(model_path)
        if model is None:
            raise RuntimeError("Segformer modeli yuklenemedi.")

        return {
            "fetch_satellite_area": fetch_satellite_area,
            "get_osm_roads_overpass": get_osm_roads_overpass,
            "get_wayback_versions": get_wayback_versions,
            "search_oam_images": search_oam_images,
            "run_inference": run_inference,
            "analyze_road_network_graph": analyze_road_network_graph,
            "model": model,
            "device": device,
        }


def _get_road_runtime():
    global road_runtime, road_runtime_error
    if road_runtime is not None:
        return road_runtime

    with road_runtime_lock:
        if road_runtime is not None:
            return road_runtime
        try:
            road_runtime = _load_road_runtime()
            road_runtime_error = None
            print("Road Damage runtime loaded.", flush=True)
        except Exception as e:
            road_runtime = None
            road_runtime_error = str(e)
            print(f"Failed to load Road Damage runtime: {e}", flush=True)
            raise
    return road_runtime


try:
    _get_road_runtime()
except Exception:
    pass

app = FastAPI(title="QuakeMind API", version="1.0.0")

class NLPRequest(BaseModel):
    text: str

class RiskRequest(BaseModel):
    city: str
    manualLatitude: float | None = None
    manualLongitude: float | None = None
    refreshData: bool = False

class RoadDamageRequest(BaseModel):
    city: str
    latitude: float
    longitude: float
    source: str = "google"
    damageBooster: float = 3.5
    threshold: float = 0.40
    useImagenetNorm: bool = True
    postProcessLevel: int = 2
    bboxWest: Optional[float] = None
    bboxSouth: Optional[float] = None
    bboxEast: Optional[float] = None
    bboxNorth: Optional[float] = None
    oamPreferredTitle: Optional[str] = None


def _compact_segment_coords(line, max_points=28):
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


def _serialize_segments(edges, max_segments=500):
    if not edges:
        return []
    serialized = []
    for _, _, _, line in edges[:max_segments]:
        compact = _compact_segment_coords(line)
        if compact:
            serialized.append(compact)
    return serialized

@app.get("/")
def health_check():
    return {"status": "ok", "message": "QuakeMind API is running!"}

@app.post("/api/nlp/analyze")
def analyze_nlp(req: NLPRequest):
    if not nlp_pipeline:
        raise HTTPException(status_code=503, detail="NLP model is not loaded.")
    
    try:
        with temporary_sys_path(NLP_ROOT), temporary_cwd(NLP_ROOT):
            result = nlp_pipeline.process_tweet(req.text)
        return result if result else {"status": "ignored", "reason": "Not related to disaster"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/risk/predict")
def predict_risk(req: RiskRequest):
    if not risk_engine:
        raise HTTPException(status_code=503, detail="Risk model is not loaded.")
    
    try:
        manual_coords = None
        if req.manualLatitude is not None and req.manualLongitude is not None:
            manual_coords = (req.manualLatitude, req.manualLongitude)
        
        with temporary_sys_path(RISK_ROOT, MOBILE_TOOL_ROOT), temporary_cwd(RISK_ROOT):
            if req.refreshData:
                from data_manager import fetch_and_update_data
                fetch_and_update_data()
            
            risk_engine.predict_city_risk(req.city, manual_coords=manual_coords)

            # Since the frontend parser currently expects fields matching risk_bridge logic:
            from risk_bridge import build_payload
            payload = build_payload(
                city=req.city,
                manual_coords=manual_coords,
                refresh_data=req.refreshData,
            )
            return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/road_damage/analyze")
def analyze_road_damage(req: RoadDamageRequest):
    try:
        import numpy as np
        import cv2

        try:
            runtime = _get_road_runtime()
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=f"Road Damage runtime yuklenemedi: {road_runtime_error or 'bilinmeyen hata'}",
            )

        fetch_satellite_area = runtime["fetch_satellite_area"]
        get_osm_roads_overpass = runtime["get_osm_roads_overpass"]
        get_wayback_versions = runtime["get_wayback_versions"]
        search_oam_images = runtime["search_oam_images"]
        run_inference = runtime["run_inference"]
        analyze_road_network_graph = runtime["analyze_road_network_graph"]
        model = runtime["model"]
        device = runtime["device"]

        started_at = time.perf_counter()
        t0 = started_at

        bbox = None
        if req.bboxWest is not None and req.bboxSouth is not None and req.bboxEast is not None and req.bboxNorth is not None:
            bbox = (req.bboxWest, req.bboxSouth, req.bboxEast, req.bboxNorth)

        source_text = (req.source or "").lower()
        prov_code = "google"
        wayback_id = None
        custom_url = None
        source_note = "Google uydu katmani kullanildi."
        satellite_tile_url = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        satellite_attribution = "Google"
        source_label = "Google Maps (Latest / High Res)"

        if "esri" in source_text or "wayback" in source_text:
            versions = get_wayback_versions()
            if versions:
                prov_code = "esri"
                wayback_id = versions[0].get("id")
                source_note = f"Esri Wayback secildi (id={wayback_id})."
                satellite_tile_url = f"https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{wayback_id}/{{z}}/{{y}}/{{x}}"
                satellite_attribution = "Esri"
                source_label = "Esri Wayback (Historical)"
            else:
                source_note = "Esri Wayback surumu bulunamadi, Google'a geri donuldu."
        elif "oam" in source_text or "openaerial" in source_text:
            oam_bbox = bbox if bbox is not None else (
                req.longitude - 0.03,
                req.latitude - 0.03,
                req.longitude + 0.03,
                req.latitude + 0.03,
            )
            oam_images = search_oam_images(oam_bbox, limit=25)
            if oam_images:
                preferred_title = (req.oamPreferredTitle or "").strip().lower()
                selected_oam = None

                def _bbox_center(item):
                    raw_bbox = item.get("bbox")
                    if not isinstance(raw_bbox, (list, tuple)) or len(raw_bbox) < 4:
                        return None
                    try:
                        west = float(raw_bbox[0])
                        south = float(raw_bbox[1])
                        east = float(raw_bbox[2])
                        north = float(raw_bbox[3])
                        return ((south + north) / 2.0, (west + east) / 2.0)
                    except Exception:
                        return None

                def _pick_closest(items):
                    if not items:
                        return None
                    with_center = []
                    for item in items:
                        center = _bbox_center(item)
                        if center is None:
                            continue
                        dlat = center[0] - req.latitude
                        dlon = center[1] - req.longitude
                        with_center.append((dlat * dlat + dlon * dlon, item))
                    if with_center:
                        with_center.sort(key=lambda x: x[0])
                        return with_center[0][1]
                    return items[0]

                if preferred_title:
                    preferred_matches = [
                        item
                        for item in oam_images
                        if preferred_title in (item.get("title", "").lower())
                    ]
                    selected_oam = _pick_closest(preferred_matches)

                # Known stable Antakya sample used in Streamlit UI.
                if selected_oam is None:
                    known_matches = [
                        item
                        for item in oam_images
                        if "2023-02-09" in item.get("title", "")
                        and "help.ngo" in item.get("title", "").lower()
                    ]
                    selected_oam = _pick_closest(known_matches)

                if selected_oam is None:
                    selected_oam = _pick_closest(oam_images)

                tms_url = (selected_oam.get("tms_url") or "").strip()
                oam_result_bbox = selected_oam.get("bbox")
                if (
                    isinstance(oam_result_bbox, (list, tuple))
                    and len(oam_result_bbox) >= 4
                ):
                    try:
                        bbox = (
                            float(oam_result_bbox[0]),
                            float(oam_result_bbox[1]),
                            float(oam_result_bbox[2]),
                            float(oam_result_bbox[3]),
                        )
                    except Exception:
                        pass

                if "{x}" in tms_url and "{y}" in tms_url:
                    prov_code = "custom"
                    custom_url = tms_url
                    source_note = f"OpenAerialMap secildi: {selected_oam.get('title', 'isimsiz goruntu')}"
                    satellite_tile_url = tms_url
                    satellite_attribution = "OpenAerialMap"
                    source_label = "OpenAerialMap (Event Specific)"
                else:
                    source_note = "OpenAerialMap tms URL formati uyumsuz, Google'a geri donuldu."
            else:
                source_note = "OpenAerialMap kaydi bulunamadi, Google'a geri donuldu."

        img, bounds = fetch_satellite_area(
            lat=req.latitude,
            lon=req.longitude,
            bbox=bbox,
            zoom_level=18,
            wayback_id=wayback_id,
            provider=prov_code,
            custom_url=custom_url,
        )
        satellite_fetch_ms = (time.perf_counter() - t0) * 1000.0
        t1 = time.perf_counter()

        if img is None:
            raise HTTPException(status_code=422, detail="Uydu goruntusu indirilemedi. Farkli bir kaynak veya konum deneyin.")

        w, h = img.size
        line_width = 6
        road_mask = get_osm_roads_overpass(bounds, w, h, thickness=line_width)
        road_mask_binary = (road_mask > 0).astype(np.uint8)
        overpass_ms = (time.perf_counter() - t1) * 1000.0
        t2 = time.perf_counter()

        raw_probs, boosted_probs, pred_mask_binary, intersection, img_np = run_inference(
            img, road_mask_binary, model, device,
            req.damageBooster, req.threshold,
            req.useImagenetNorm, req.postProcessLevel,
        )
        inference_ms = (time.perf_counter() - t2) * 1000.0
        t3 = time.perf_counter()

        total_pixels = pred_mask_binary.size
        damage_pixels = int(np.sum(pred_mask_binary))
        damage_rate = damage_pixels / total_pixels if total_pixels > 0 else 0

        road_pixels = int(np.sum(road_mask_binary))
        blocked_pixels = int(np.sum(intersection))
        open_road_pixels = road_pixels - blocked_pixels

        blocked_road_pct = blocked_pixels / road_pixels if road_pixels > 0 else 0
        open_road_pct = 1.0 - blocked_road_pct

        log_lines = [
            "1/4 Uydu goruntusu indirildi",
            source_note,
            f"2/4 OSM yol agi cikarildi ({road_pixels} piksel)",
            "3/4 Segformer modeli ile inference tamamlandi",
            f"4/4 Analiz tamamlandi - hasar orani: %{damage_rate * 100:.1f}",
        ]

        safe_count = 0
        blocked_count = 0
        safe_segments = []
        blocked_segments = []
        try:
            G, safe_edges, blocked_edges = analyze_road_network_graph(bounds, w, h, intersection)
            if G is not None:
                safe_count = len(safe_edges) if safe_edges else 0
                blocked_count = len(blocked_edges) if blocked_edges else 0
                safe_segments = _serialize_segments(safe_edges)
                blocked_segments = _serialize_segments(blocked_edges)
                log_lines.append(f"Lojistik: {safe_count} acik, {blocked_count} kapali sokak")
        except Exception:
            log_lines.append("Lojistik analiz opsiyonel - OSMnx mevcut degil veya hata olustu")
        logistics_ms = (time.perf_counter() - t3) * 1000.0
        total_ms = (time.perf_counter() - started_at) * 1000.0
        log_lines.append(
            f"Sureler (sn): uydu={satellite_fetch_ms / 1000:.1f}, yol={overpass_ms / 1000:.1f}, AI={inference_ms / 1000:.1f}, lojistik={logistics_ms / 1000:.1f}, toplam={total_ms / 1000:.1f}"
        )

        recommended = "Analiz basarili."
        if blocked_road_pct > 0.5:
            recommended = "Kritik: Yollarin buyuk kismi kapali. Alternatif rotalar planlanmali."
        elif blocked_road_pct > 0.2:
            recommended = "Dikkat: Bazi yollar kapali. Ekipler icin alternatif guzergah onerilir."
        elif damage_rate > 0.3:
            recommended = "Yuksek hasar orani. Bolgeye dikkatli erisim saglanmali."
        else:
            recommended = "Bolge genel olarak erisilebilir durumda."

        return {
            "city": req.city,
            "damageRate": round(damage_rate, 4),
            "openRoads": safe_count,
            "blockedRoads": blocked_count,
            "openRoadPct": round(open_road_pct, 4),
            "blockedRoadPct": round(blocked_road_pct, 4),
            "logLines": log_lines,
            "recommendedAction": recommended,
            "bounds": {
                "west": bounds[0],
                "south": bounds[1],
                "east": bounds[2],
                "north": bounds[3],
            },
            "imageWidth": w,
            "imageHeight": h,
            "damageBooster": req.damageBooster,
            "threshold": req.threshold,
            "safeRoadSegments": safe_segments,
            "blockedRoadSegments": blocked_segments,
            "satelliteSource": source_label,
            "satelliteTileUrl": satellite_tile_url,
            "satelliteAttribution": satellite_attribution,
            "timingsMs": {
                "satellite": round(satellite_fetch_ms, 1),
                "roads": round(overpass_ms, 1),
                "inference": round(inference_ms, 1),
                "logistics": round(logistics_ms, 1),
                "total": round(total_ms, 1),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
def server_status():
    return {
        "status": "ok",
        "modules": {
            "nlp": nlp_pipeline is not None,
            "risk": risk_engine is not None,
            "road_damage": road_runtime is not None,
        },
    }


if __name__ == "__main__":
    import socket
    import uvicorn

    host = "0.0.0.0"
    port = 8000

    def _get_local_ip() -> str:
        """Returns the LAN IP that other devices on the same network can reach."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # No packet is sent; this is a common way to learn the outbound interface IP.
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            sock.close()

    local_ip = _get_local_ip()
    print("\n" + "=" * 60)
    print("FastAPI sunucusu baslatiliyor...")
    print(f"Bu cihazdan: http://127.0.0.1:{port}")
    print(f"Diger cihazlardan (ayni ag): http://{local_ip}:{port}")
    print("=" * 60 + "\n")

    uvicorn.run("fastapi_app:app", host=host, port=port, reload=True)
