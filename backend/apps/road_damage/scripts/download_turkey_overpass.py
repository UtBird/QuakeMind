import requests
import json
from pathlib import Path
import time

APP_DIR = Path(__file__).resolve().parents[1]
OSM_DATA_DIR = APP_DIR / "data" / "osm"
OSM_DATA_DIR.mkdir(parents=True, exist_ok=True)
GEOJSON_FILE = OSM_DATA_DIR / "safety_areas.geojson"

def download_turkey_safety_areas():
    print("🌍 Sadece Türkiye'deki toplanma alanları ve parklar indiriliyor (Tahmini boyut: 3-5 MB)...")
    print("⏳ Overpass API sorgulanıyor, lütfen 1-2 dakika bekleyin...")
    
    # We use 'out center;' to get only the center point for polygons, saving massive amounts of data
    overpass_query = """
    [out:json][timeout:900];
    area["ISO3166-1"="TR"][admin_level="2"]->.searchArea;
    (
      node["emergency"="assembly_point"](area.searchArea);
      way["emergency"="assembly_point"](area.searchArea);
      relation["emergency"="assembly_point"](area.searchArea);
      
      node["leisure"~"park|garden"](area.searchArea);
      way["leisure"~"park|garden"](area.searchArea);
      relation["leisure"~"park|garden"](area.searchArea);
      
      node["landuse"~"recreation_ground|village_green|grass"](area.searchArea);
      way["landuse"~"recreation_ground|village_green|grass"](area.searchArea);
      relation["landuse"~"recreation_ground|village_green|grass"](area.searchArea);
    );
    out center;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    headers = {
        "User-Agent": "QuakeMind-App/1.0",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, data={'data': overpass_query}, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ API Hatası: {e}")
        if 'response' in locals() and response:
            print(response.text)
        return
        
    data = response.json()
    elements = data.get("elements", [])
    print(f"✅ Başarılı! {len(elements)} adet park/alan bulundu. (Süre: {time.time() - start_time:.1f} saniye)")
    
    features = []
    for el in elements:
        tags = el.get("tags", {})
        
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            center = el.get("center")
            if not center:
                continue
            lat, lon = center["lat"], center["lon"]
            
        emergency = tags.get('emergency', '')
        leisure = tags.get('leisure', '')
        landuse = tags.get('landuse', '')
        
        if "assembly_point" in emergency:
            category, priority = "OSM resmi toplanma alanı", 0
        elif "park" in leisure or "garden" in leisure:
            category, priority = "Aday park/bahçe", 1
        elif "recreation_ground" in landuse or "village_green" in landuse or "grass" in landuse:
            category, priority = "Aday açık alan", 2
        else:
            continue
            
        name = tags.get('name', category)
        access = tags.get('access', '').lower()
        if access in ('no', 'private'):
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "toplanma_alani": name,
                "name": name,
                "category": category,
                "priority": priority,
                "source": "OSM Turkey Overpass API",
                "emergency": emergency,
                "leisure": leisure,
                "landuse": landuse,
                "access": access
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
        
    file_size_mb = GEOJSON_FILE.stat().st_size / (1024 * 1024)
    print(f"💾 Tüm Türkiye'nin yerel haritası kaydedildi: {GEOJSON_FILE} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    download_turkey_safety_areas()
