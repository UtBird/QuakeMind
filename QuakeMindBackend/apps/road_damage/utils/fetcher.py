import math
import requests
import numpy as np
import cv2
from PIL import Image
import datetime
import logging

try:
    import streamlit as st
    _has_st = True
except ImportError:
    _has_st = False

_logger = logging.getLogger(__name__)


def _warn(msg):
    if _has_st:
        try:
            st.warning(msg)
        except Exception:
            pass
    _logger.warning(msg)


def _error(msg):
    if _has_st:
        try:
            st.error(msg)
        except Exception:
            pass
    _logger.error(msg)

def num2deg(xtile, ytile, zoom):
    """Google/OSM Tile to Lat/Lon conversion."""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def fetch_satellite_area(lat, lon, bbox=None, zoom_level=18, wayback_id=None, provider='google', custom_url=None):
    """Downloads tiles covering a bounding box or a single coordinate."""
    if not bbox:
        n = 2.0 ** zoom_level
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
        lat_n, lon_w = num2deg(xtile, ytile, zoom_level)
        lat_s, lon_e = num2deg(xtile + 2, ytile + 2, zoom_level)
        bbox = (lon_w, lat_s, lon_e, lat_n)
        
    lon_min, lat_min, lon_max, lat_max = bbox
    n = 2.0 ** zoom_level
    xtile_min = int((lon_min + 180.0) / 360.0 * n)
    xtile_max = int((lon_max + 180.0) / 360.0 * n)
    ytile_max = int((1.0 - math.asinh(math.tan(math.radians(lat_min))) / math.pi) / 2.0 * n)
    ytile_min = int((1.0 - math.asinh(math.tan(math.radians(lat_max))) / math.pi) / 2.0 * n)
    
    if (xtile_max - xtile_min + 1) * (ytile_max - ytile_min + 1) > 36:
        _warn("Seçilen alan çok büyük. Harita boyutu 6x6 tile ile sınırlandırıldı.")
        xt_c = (xtile_min + xtile_max) // 2
        yt_c = (ytile_min + ytile_max) // 2
        xtile_min = max(xtile_min, xt_c - 2); xtile_max = min(xtile_max, xt_c + 3)
        ytile_min = max(ytile_min, yt_c - 2); ytile_max = min(ytile_max, yt_c + 3)

    nx_tiles = xtile_max - xtile_min + 1
    ny_tiles = ytile_max - ytile_min + 1
    stitched_img = Image.new('RGB', (nx_tiles * 256, ny_tiles * 256))
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for x in range(xtile_min, xtile_max + 1):
        for y in range(ytile_min, ytile_max + 1):
            if provider == 'esri' and wayback_id:
                url = f"https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{wayback_id}/{zoom_level}/{y}/{x}"
            elif provider == 'google':
                url = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom_level}"
            elif provider == 'custom' and custom_url:
                url = custom_url.replace('{x}', str(x)).replace('{y}', str(y)).replace('{z}', str(zoom_level))
            else:
                return None, None
                
            px = (x - xtile_min) * 256
            py = (y - ytile_min) * 256
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code == 200:
                    from io import BytesIO
                    tile_img = Image.open(BytesIO(r.content)).convert('RGB')
                    stitched_img.paste(tile_img, (px, py))
            except Exception:
                pass

    real_lat_n, real_lon_w = num2deg(xtile_min, ytile_min, zoom_level)
    real_lat_s, real_lon_e = num2deg(xtile_max + 1, ytile_max + 1, zoom_level)
    return stitched_img, (real_lon_w, real_lat_s, real_lon_e, real_lat_n)


def get_osm_roads_overpass(bounds, w, h, thickness=4):
    """Fetches OSM roads via Overpass and draws perfectly aligned array."""
    west, south, east, north = bounds
    
    servers = [
        "http://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]
    
    query = f'''
    [out:json][timeout:30];
    way["highway"]({south},{west},{north},{east});
    out geom;
    '''
    
    road_img = np.zeros((h, w), dtype=np.uint8)
    data = None
    
    for url in servers:
        try:
            resp = requests.post(url, data=query, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                break # Success
        except Exception:
            continue
            
    if not data:
        _warn("All Overpass servers failed. Roads could not be fetched.")
        return road_img
        
    try:
        for element in data.get('elements', []):
            if 'geometry' in element:
                pts = []
                for pt in element['geometry']:
                    px = int((pt['lon'] - west) / (east - west) * w)
                    py = int((north - pt['lat']) / (north - south) * h)
                    pts.append([px, py])
                if len(pts) >= 2:
                    pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(road_img, [pts], False, 1, thickness=thickness)
    except Exception as e:
        _warn(f"OSM parse error: {e}")
        
    return road_img

def get_wayback_versions():
    """Fetch available Esri Wayback versions."""
    try:
        url = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer?f=json"
        data = requests.get(url, timeout=5).json()
        versions = []
        for item in data.get('Selection', []):
            name = item['Name']
            if "Wayback" in name:
                date_str = name.split("Wayback ")[-1].replace(")", "")
                versions.append({
                    "date": date_str, "id": item['M'], "label": f"{date_str}"
                })
        return versions
    except Exception:
        return []

def search_oam_images(bbox, date_start=None, date_end=None, limit=50):
    url = "https://api.openaerialmap.org/meta"
    params = {
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "limit": limit,
        "order_by": "acquisition_end",
        "sort": "desc"
    }
    
    if date_start and date_end:
        if isinstance(date_start, str): params["acquisition_from"] = date_start
        else: params["acquisition_from"] = date_start.strftime("%Y-%m-%d")
        if isinstance(date_end, str): params["acquisition_to"] = date_end
        else: params["acquisition_to"] = date_end.strftime("%Y-%m-%d")

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        results = []
        if 'results' in data:
            for item in data['results']:
                tms_url = item.get('tms') or item.get('properties', {}).get('tms')
                if not tms_url:
                    tms_url = item.get('wmts') or item.get('properties', {}).get('wmts')
                
                if tms_url:
                    results.append({
                        "id": item.get('_id') or item.get('uuid'),
                        "title": item.get('title', 'Unknown Image'),
                        "provider": item.get('provider', 'Unknown'),
                        "date": item.get('acquisition_end', item.get('acquisition_start', 'Unknown Date')),
                        "tms_url": tms_url,
                        "bbox": item.get('bbox')
                    })
        return results
    except Exception as e:
        _error(f"OAM Search failed: {e}")
        return []
