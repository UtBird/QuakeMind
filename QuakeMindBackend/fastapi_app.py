from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import site
import importlib
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

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

        clear_module_cache(["utils", "utils.fetcher", "utils.inference", "utils.network"])
        with temporary_sys_path(ROAD_ROOT), temporary_cwd(ROAD_ROOT):
            from utils.fetcher import fetch_satellite_area, get_osm_roads_overpass, get_wayback_versions, search_oam_images
            from utils.inference import load_simple_model, run_inference
            from utils.network import analyze_road_network_graph

            model_path = str(ROAD_ROOT / "models" / "optimized_mitb4_focal_dice30.pth")

            bbox = None
            if req.bboxWest is not None and req.bboxSouth is not None and req.bboxEast is not None and req.bboxNorth is not None:
                bbox = (req.bboxWest, req.bboxSouth, req.bboxEast, req.bboxNorth)

            source_text = (req.source or "").lower()
            prov_code = "google"
            wayback_id = None
            custom_url = None
            source_note = "Google uydu katmani kullanildi."

            if "esri" in source_text or "wayback" in source_text:
                versions = get_wayback_versions()
                if versions:
                    prov_code = "esri"
                    wayback_id = versions[0].get("id")
                    source_note = f"Esri Wayback secildi (id={wayback_id})."
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

                    if preferred_title:
                        selected_oam = next(
                            (
                                item
                                for item in oam_images
                                if preferred_title in (item.get("title", "").lower())
                            ),
                            None,
                        )

                    # Known stable Antakya sample used in Streamlit UI.
                    if selected_oam is None:
                        selected_oam = next(
                            (
                                item
                                for item in oam_images
                                if "2023-02-09" in item.get("title", "")
                                and "help.ngo" in item.get("title", "").lower()
                            ),
                            None,
                        )

                    if selected_oam is None:
                        selected_oam = oam_images[0]

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

            if img is None:
                raise HTTPException(status_code=422, detail="Uydu goruntusu indirilemedi. Farkli bir kaynak veya konum deneyin.")

            w, h = img.size
            line_width = 6
            road_mask = get_osm_roads_overpass(bounds, w, h, thickness=line_width)
            road_mask_binary = (road_mask > 0).astype(np.uint8)

            model, device = load_simple_model(model_path)
            if model is None:
                raise HTTPException(status_code=503, detail="Segformer modeli yuklenemedi.")

            raw_probs, boosted_probs, pred_mask_binary, intersection, img_np = run_inference(
                img, road_mask_binary, model, device,
                req.damageBooster, req.threshold,
                req.useImagenetNorm, req.postProcessLevel,
            )

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
            "road_damage": True,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
