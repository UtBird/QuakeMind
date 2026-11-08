"""known_locations.py'deki her bolge icin, gercek pipeline'in kullanacagi
TAM bounds'u (fetch_satellite_area ile) hesaplayip, o bounds icin yerel
PBF'ten (D:/quakemind_osm_data/turkey-latest.osm.pbf) bir yol grafigi
cikarip pickle olarak cache'ler (apps/road_damage/data/osm_graph_cache/).

Bu ONCEDEN calistirilir (dakikalar surebilir, PBF taranir) -- canli istek
sirasinda worker.py'nin 45sn'lik timeout'u icinde SADECE bu cache'ten hizli
okuma yapilir, hicbir zaman canli PBF taramasi baslatilmaz.

Kullanim:
  python benchmark/warm_local_graph_cache.py
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apps.road_damage.utils.fetcher import fetch_satellite_area
from apps.road_damage.utils.tiling import zoom_for_radius
from apps.road_damage.utils.network import build_local_graph_from_pbf, load_local_graph_from_cache
from known_locations import KNOWN_LOCATIONS, bbox_center


def resolve_oam_tms_url(loc: dict) -> str | None:
    import requests
    lat, lon = bbox_center(loc["bbox"])
    resp = requests.get("http://127.0.0.1:8000/api/road_damage/oam_search", params={
        "latitude": lat, "longitude": lon, "radiusKm": 5,
        "dateStart": "2023-02-06", "dateEnd": "2023-02-28",
    }, timeout=30)
    for img in resp.json().get("images", []):
        if loc["oamTitleMatch"].lower() in (img.get("title") or "").lower():
            return img["tms_url"]
    return None


def main():
    for loc in KNOWN_LOCATIONS:
        lat, lon = bbox_center(loc["bbox"])
        print(f"[{loc['region']}/{loc['mahalleName']}] gercek bounds hesaplaniyor...")
        tms_url = resolve_oam_tms_url(loc)
        if not tms_url:
            print(f"  UYARI: OAM goruntusu bulunamadi ({loc['oamTitleMatch']}), atlaniyor.")
            continue

        img, bounds = fetch_satellite_area(
            lat=lat, lon=lon, bbox=None, zoom_level=zoom_for_radius(0.4),
            provider="custom", custom_url=tms_url,
        )
        if bounds is None:
            print("  UYARI: goruntu/bounds alinamadi, atlaniyor.")
            continue
        print(f"  bounds: {bounds}")

        cached = load_local_graph_from_cache(bounds)
        if cached is not None:
            print(f"  zaten cache'de ({cached.number_of_nodes()} dugum), atlaniyor.")
            continue

        print("  yerel PBF'ten cikariliyor (dakikalar surebilir)...")
        try:
            G = build_local_graph_from_pbf(bounds)
            print(f"  OK -- {G.number_of_nodes()} dugum, {G.number_of_edges()} kenar cache'lendi.")
        except Exception as e:
            print(f"  HATA: {e}")


if __name__ == "__main__":
    main()
