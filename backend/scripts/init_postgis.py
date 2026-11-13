"""PostGIS Initializer & AFAD Dataset Ingestion Script

Run this script after starting your PostgreSQL/PostGIS server to automatically:
1. Enable PostGIS spatial extensions.
2. Create GIST spatial indexed tables.
3. Ingest all 72,232 official AFAD assembly points.
"""

import sys
from pathlib import Path

# Add parent dir to sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from utils.postgis_manager import postgis_engine

def main():
    print("QuakeMind PostGIS Mekansal Veritabani Kurulumu Baslatiliyor...")
    
    if not postgis_engine.check_connection():
        print("X PostgreSQL/PostGIS veritabanina baglanilamadi!")
        print("Ipucu: Docker Desktop uygulamasini baslatin veya PostgreSQL servisinin 5432 portunda acik oldugundan emin olun.")
        print(f"Baglanti URL: {postgis_engine.db_url}")
        sys.exit(1)

    print("1. Mekansal Tablolar & GIST Indeksleri Olusturuluyor...")
    success = postgis_engine.init_spatial_tables()
    if not success:
        print("X PostGIS tablo kurulumu basarisiz!")
        sys.exit(1)

    print("2. 72.232 Adet AFAD Resmi Toplanma Alani PostGIS'e Aktariliyor...")
    afad_json = BACKEND_DIR / "apps" / "road_damage" / "data" / "tum_turkiye_toplanma_alanlari.json"
    inserted = postgis_engine.seed_afad_dataset_to_postgis(afad_json)
    
    print(f"TEBRIKLER! PostGIS Kurulumu Tamamlandi! Toplam {inserted} nokta mekanik indekslendi.")

if __name__ == "__main__":
    main()
