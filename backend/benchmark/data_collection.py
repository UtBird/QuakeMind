"""Gercek cografi veri toplama: Kahramanmaras ve Hatay icin toplanma alanlari,
itfaiye/hastane/AFAD-UMKE noktalari ve mahalle listesi.

Toplanma alanlari zaten repo icinde resmi AFAD veriseti olarak var
(apps/road_damage/data/tum_turkiye_toplanma_alanlari.json, 72.232 nokta) --
bunu OSM'den yeniden cekmek yerine dogrudan filtreleyip kullaniyoruz. Itfaiye/
hastane/AFAD-UMKE binalari icin ise Overpass API'ye, mevcut
apps/road_damage/utils/fetcher.py::get_osm_roads_overpass ile ayni
cok-ayna (multi-mirror) fallback desenini kullanarak sorgu atiyoruz.

Not: Kaynak JSON'daki bazi Turkce karakterler (I, S, G, O, U, C) dataset
uretilirken zaten bozulmus (U+FFFD replacement char olarak saklanmis) --
bu bizim eklentimiz degil, kaynak veride onceden var. Il/ilce eslestirmesini
bu yuzden bozulmadan etkilenmeyen ASCII alt-dizgilerle yapiyoruz.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = Path(__file__).resolve().parent / "data"
AFAD_JSON = BACKEND_DIR / "apps" / "road_damage" / "data" / "tum_turkiye_toplanma_alanlari.json"

BBOX_BUFFER_DEG = 0.01  # ~1.1 km buffer around matched points

REGIONS = {
    "kahramanmaras": {
        "label": "Kahramanmaras (merkez)",
        "il_prefix": "KAHRAMANMARA",
        # "ON�K��UBAT" (Onikisubat) ve "DULKAD�RO�LU" (Dulkadiroglu) -- il
        # merkezini olusturan iki merkez ilce. Bozulmayan ASCII parcalarla
        # esleniyor: "UBAT" sadece Onikisubat'ta gecer, "DULKAD" ise
        # Dulkadiroglu'nda.
        "ilce_markers": ["UBAT", "DULKAD"],
    },
    "hatay": {
        "label": "Hatay / Antakya (merkez)",
        "il_prefix": "HATAY",
        "ilce_markers": ["ANTAKYA"],
    },
}

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {"User-Agent": "QuakeMindBenchmark/1.0"}


def load_afad_points() -> list[dict]:
    with open(AFAD_JSON, encoding="utf-8") as f:
        return json.load(f)


def filter_region_points(points: list[dict], region_cfg: dict) -> list[dict]:
    il_prefix = region_cfg["il_prefix"]
    markers = region_cfg["ilce_markers"]
    matched = [
        p for p in points
        if p["il"].startswith(il_prefix) and any(m in p["ilce"] for m in markers)
    ]
    out = []
    for p in matched:
        try:
            lat = float(p["enlem"])
            lon = float(p["boylam"])
        except (TypeError, ValueError):
            continue
        out.append({**p, "lat": lat, "lon": lon})
    return out


def compute_bbox(points: list[dict], buffer_deg: float = BBOX_BUFFER_DEG):
    lats = [p["lat"] for p in points]
    lons = [p["lon"] for p in points]
    west = min(lons) - buffer_deg
    east = max(lons) + buffer_deg
    south = min(lats) - buffer_deg
    north = max(lats) + buffer_deg
    return {"west": west, "south": south, "east": east, "north": north}


def filter_urban_core(points: list[dict], radius_deg: float = 0.12) -> list[dict]:
    """Kirsal/uzak koylerden gelen aykiri noktalari eler: buyuksehir ilcesi
    sinirlari sehir merkezinden onlarca km uzagi da kapsayabildigi icin
    (2014 buyuksehir reformu), medyan merkeze yakin noktalari tutuyoruz."""
    lats = sorted(p["lat"] for p in points)
    lons = sorted(p["lon"] for p in points)
    med_lat = lats[len(lats) // 2]
    med_lon = lons[len(lons) // 2]
    return [
        p for p in points
        if abs(p["lat"] - med_lat) < radius_deg and abs(p["lon"] - med_lon) < radius_deg
    ]


def pick_top_mahalleler(points: list[dict], n: int = 3) -> list[dict]:
    # Ayni mahalle adi farkli ilcelerde (dolayisiyla farkli fiziksel
    # konumlarda) tekrar edebiliyor -- (ilce, mahalle) ciftiyle grupluyoruz,
    # yoksa iki ayri mahalle tek "mahalle" olarak birlesip bbox'u sacmalar.
    by_key: dict[tuple[str, str], list[dict]] = {}
    for p in points:
        by_key.setdefault((p["ilce"], p["mahalle"]), []).append(p)
    ranked = sorted(by_key.items(), key=lambda kv: len(kv[1]), reverse=True)
    result = []
    for (ilce, name), pts in ranked[:n]:
        result.append({
            "name": name,
            "ilce": ilce,
            "toplanmaAlaniCount": len(pts),
            "bbox": compute_bbox(pts, buffer_deg=0.005),
            "toplanmaAlanlari": [
                {"name": p["toplanma_alani"], "lat": p["lat"], "lon": p["lon"]}
                for p in pts
            ],
        })
    return result


def _overpass_query(query: str) -> dict | None:
    def _fetch_one(url: str):
        try:
            resp = requests.post(url, data=query, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=len(OVERPASS_MIRRORS)) as pool:
        futures = {pool.submit(_fetch_one, url): url for url in OVERPASS_MIRRORS}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                for f in futures:
                    f.cancel()
                return result
    return None


def fetch_infra(bbox: dict) -> dict:
    south, west, north, east = bbox["south"], bbox["west"], bbox["north"], bbox["east"]
    query = f'''
    [out:json][timeout:30];
    (
      node["amenity"="fire_station"]({south},{west},{north},{east});
      way["amenity"="fire_station"]({south},{west},{north},{east});
      node["amenity"="hospital"]({south},{west},{north},{east});
      way["amenity"="hospital"]({south},{west},{north},{east});
      node["name"~"AFAD",i]({south},{west},{north},{east});
      node["name"~"UMKE",i]({south},{west},{north},{east});
    );
    out center;
    '''
    data = _overpass_query(query)
    infra = {"itfaiye": [], "hastane": [], "afadUmke": []}
    if not data:
        return infra

    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        name = tags.get("name", "Isimsiz")
        entry = {"name": name, "lat": lat, "lon": lon}
        amenity = tags.get("amenity")
        upper_name = name.upper()
        if amenity == "fire_station":
            infra["itfaiye"].append(entry)
        elif amenity == "hospital":
            infra["hastane"].append(entry)
        elif "AFAD" in upper_name or "UMKE" in upper_name:
            # "AFAD ... istasyonu" OSM'de neredeyse hep sismik/yer-hareketi
            # sensorudur, operasyonel bir saha noktasi degil -- bunlari
            # disla. "UMKE istasyonu" ise UMKE'nin gercek operasyonel birim
            # adidir (sismik degil) -- disleme.
            is_seismic = "AFAD" in upper_name and any(
                k in upper_name for k in ("SISMO", "YER HAREKET", "DEPREM", "GOZLEM")
            )
            if not is_seismic:
                infra["afadUmke"].append(entry)
    return infra


def collect_region(region_key: str) -> dict:
    region_cfg = REGIONS[region_key]
    points = load_afad_points()
    matched = filter_region_points(points, region_cfg)
    if not matched:
        raise RuntimeError(f"{region_key} icin eslesen toplanma alani bulunamadi.")

    urban = filter_urban_core(matched)
    if len(urban) < 5:
        urban = matched  # guvenlik agi: cok az nokta kalirsa filtreyi gevset

    bbox = compute_bbox(urban)
    # Genis bir aday havuzu tutuyoruz (sadece 3 degil) -- asil 3 mahalle
    # secimi scenario_generator.py'de gercek Copernicus hasar yakinligina
    # gore yapiliyor (bazi adaylar sehir disinda kalip hic gercek hasar
    # icermeyebiliyor, bkz. Hatay/Acikdere ve Hatay/Akcurun bulgusu).
    mahalleler = pick_top_mahalleler(urban, n=12)
    infra = fetch_infra(bbox)

    result = {
        "region": region_key,
        "label": region_cfg["label"],
        "bbox": bbox,
        "toplanmaAlaniCount": len(matched),
        "toplanmaAlaniUrbanCoreCount": len(urban),
        "mahalleler": mahalleler,
        "infra": infra,
    }
    return result


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for region_key in REGIONS:
        print(f"[{region_key}] AFAD toplanma alanlari filtreleniyor...")
        result = collect_region(region_key)
        out_path = DATA_DIR / f"{region_key}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(
            f"[{region_key}] {result['toplanmaAlaniCount']} toplanma alani, "
            f"{len(result['mahalleler'])} mahalle secildi, "
            f"itfaiye={len(result['infra']['itfaiye'])} "
            f"hastane={len(result['infra']['hastane'])} "
            f"afadUmke={len(result['infra']['afadUmke'])} -> {out_path}"
        )


if __name__ == "__main__":
    main()
