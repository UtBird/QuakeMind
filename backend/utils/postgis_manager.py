"""QuakeMind PostGIS Spatial Engine Manager

Provides ultra-fast PostGIS R-Tree spatial indexing (ST_DWithin, ST_Distance, pgRouting)
for AFAD safe assembly points, road blockages, and SOS alert persistence, with intelligent
offline fallback to in-memory dataset if PostgreSQL/PostGIS server is offline.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

POSTGIS_URL = os.getenv("POSTGIS_URL", "postgresql://postgres:postgres@localhost:5432/quakemind_db")

class PostGISManager:
    def __init__(self, db_url: str = POSTGIS_URL):
        self.db_url = db_url
        self.connected = False

    # Baglanti denemesi 2 sn zaman asimina dusuyor ve bazi uclar bunu istek
    # basina birkac kez cagiriyordu (olculen: isi haritasi ucu 4,0 sn). Sonuc
    # kisa sureligine saklanir; PostgreSQL acilinca en gec bu surede gorulur.
    _SONUC_OMRU_SN = 30.0
    _son_kontrol = 0.0
    _son_sonuc = None

    def check_connection(self, zorla: bool = False) -> bool:
        import time as _time

        if not zorla and self._son_sonuc is not None:
            if (_time.time() - self._son_kontrol) < self._SONUC_OMRU_SN:
                return self._son_sonuc

        sonuc = self._baglantiyi_dene()
        type(self)._son_kontrol = _time.time()
        type(self)._son_sonuc = sonuc
        self.connected = sonuc
        return sonuc

    def _baglantiyi_dene(self) -> bool:
        if not PSYCOPG2_AVAILABLE:
            self.connected = False
            return False
        try:
            conn = psycopg2.connect(self.db_url, connect_timeout=2)
            cur = conn.cursor()
            cur.execute("SELECT PostGIS_Version();")
            version = cur.fetchone()
            cur.close()
            conn.close()
            self.connected = True
            print(f"PostGIS veritabani aktif! Surum: {version[0]}")
            return True
        except Exception as e:
            self.connected = False
            return False

    def init_spatial_tables(self) -> bool:
        """PostGIS eklentisini ve varsayılan mekanik tabloları oluşturur."""
        if not PSYCOPG2_AVAILABLE:
            return False
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            cur = conn.cursor()

            # Enable PostGIS Spatial Extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            # 1. AFAD Assembly & Safe Zones Table with GIST Spatial Index
            cur.execute("""
                CREATE TABLE IF NOT EXISTS afad_assembly_points (
                    id SERIAL PRIMARY KEY,
                    toplanma_alani VARCHAR(255),
                    il VARCHAR(100),
                    ilce VARCHAR(100),
                    mahalle VARCHAR(100),
                    geom GEOMETRY(Point, 4326),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_afad_gist_geom ON afad_assembly_points USING GIST (geom);
            """)

            # 2. Road Blockages Spatial Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS road_blockages (
                    id VARCHAR(64) PRIMARY KEY,
                    title VARCHAR(255),
                    severity VARCHAR(50),
                    geom GEOMETRY(LineString, 4326),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_blockages_gist_geom ON road_blockages USING GIST (geom);
            """)

            # 3. SOS Alerts Spatial Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sos_alerts (
                    id VARCHAR(64) PRIMARY KEY,
                    message TEXT,
                    user_id VARCHAR(64),
                    urgency VARCHAR(50),
                    geom GEOMETRY(Point, 4326),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_sos_gist_geom ON sos_alerts USING GIST (geom);
            """)

            # 4. OSM Safety Polygons Table (Parks, Open Spaces, Stadiums)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS osm_safety_polygons (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    category VARCHAR(100),
                    geom GEOMETRY(Geometry, 4326),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_osm_poly_gist ON osm_safety_polygons USING GIST (geom);
            """)

            # 5. Damage Points Table (crack / destruction / road_damage / sos detections,
            # feeds the Gaussian heatmap and the risk-weighted route engine)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS damage_points (
                    id SERIAL PRIMARY KEY,
                    source_type VARCHAR(50) NOT NULL,
                    severity FLOAT,
                    label VARCHAR(255),
                    geom GEOMETRY(Point, 4326),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_damage_points_gist_geom ON damage_points USING GIST (geom);
            """)

            # 6. Users Authentication Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'survivor',
                    city VARCHAR(100) DEFAULT 'Hatay',
                    unit VARCHAR(150) DEFAULT 'Sivil',
                    token VARCHAR(128) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
                CREATE INDEX IF NOT EXISTS idx_users_token ON users (token);
            """)

            cur.close()
            conn.close()
            print("PostGIS GIST Mekansal indeksleri, kullanıcılar tablosu ve veritabanı hazırlandı.")
            return True
        except Exception as e:
            print(f"PostGIS tablo olusturma hatasi: {e}")
            return False

    def seed_afad_dataset_to_postgis(self, json_path: Path) -> int:
        """72.232 adet AFAD resmi toplanma alanını PostGIS veritabanına aktarır."""
        if not self.check_connection() or not json_path.exists():
            return 0

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            # Check existing count
            cur.execute("SELECT COUNT(*) FROM afad_assembly_points;")
            count = cur.fetchone()[0]
            if count >= 50000:
                print(f"PostGIS AFAD tablosunda zaten {count} kayit mevcut.")
                cur.close()
                conn.close()
                return count

            print("72.232 AFAD toplanma alani PostGIS'e yukleniyor...")
            from psycopg2.extras import execute_values
            
            insert_rows = []
            for item in data:
                try:
                    lat = float(item["enlem"])
                    lon = float(item["boylam"])
                    name = item.get("toplanma_alani", "AFAD Resmi Toplanma Alanı")
                    il = item.get("il", "")
                    ilce = item.get("ilce", "")
                    mahalle = item.get("mahalle", "")
                    insert_rows.append((name, il, ilce, mahalle, lon, lat))
                except Exception:
                    continue

            if insert_rows:
                query = """
                    INSERT INTO afad_assembly_points (toplanma_alani, il, ilce, mahalle, geom)
                    VALUES %s;
                """
                template = "(%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))"
                execute_values(cur, query, insert_rows, template=template, page_size=5000)

            conn.commit()
            inserted = len(insert_rows)
            cur.close()
            conn.close()
            print(f"TEBRIKLER! {inserted} adet AFAD resmi toplanma alani PostGIS'e aktarildi!")
            return inserted
        except Exception as e:
            print(f"PostGIS seed yukleme hatasi: {e}")
            return 0

    def query_nearby_postgis(self, lat: float, lon: float, radius_m: float = 10000.0) -> List[Dict[str, Any]]:
        """PostGIS ST_DWithin ve ST_Distance GIST spatial sorgusu çalıştırır."""
        if not self.check_connection():
            return []

        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT toplanma_alani AS name, toplanma_alani, il, ilce, mahalle,
                       ST_Y(geom) AS lat, ST_X(geom) AS lon, ST_Y(geom) AS display_lat, ST_X(geom) AS display_lon,
                       'AFAD Resmi Toplanma Alani' AS category, 0 AS priority,
                       'PostgreSQL/PostGIS' AS source, 'Guvenli AFAD Toplanma Alani' AS status,
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS dist_m
                FROM afad_assembly_points
                WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                ORDER BY dist_m ASC LIMIT 50;
            """
            cur.execute(query, (lon, lat, lon, lat, radius_m))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"PostGIS mekansal sorgu hatasi: {e}")
            return []

    def ingest_osm_data_to_postgis(self, lat: float, lon: float, radius_km: float = 10.0) -> int:
        """Ingests OpenStreetMap parks, stadiums, and open assembly polygons into PostGIS."""
        if not self.check_connection():
            return 0

        import requests
        print(f"OSM verileri PostGIS'e cekiliyor... Lat: {lat}, Lon: {lon}, Radius: {radius_km}km")
        
        # Calculate Bounding Box
        min_lat = lat - (radius_km / 111.0)
        max_lat = lat + (radius_km / 111.0)
        min_lon = lon - (radius_km / 80.0)
        max_lon = lon + (radius_km / 80.0)

        overpass_query = f'[out:json][timeout:25];(node["emergency"="assembly_point"]({min_lat},{min_lon},{max_lat},{max_lon});way["leisure"="park"]({min_lat},{min_lon},{max_lat},{max_lon});way["leisure"="stadium"]({min_lat},{min_lon},{max_lat},{max_lon}););out center;'

        headers = {"User-Agent": "QuakeMind-GIS-App/1.0 (https://quakemind.org)"}
        try:
            r = requests.post("https://overpass-api.de/api/interpreter", data={"data": overpass_query}, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"OSM Overpass HTTP Hata: {r.status_code}")
                return 0

            elements = r.json().get("elements", [])
            if not elements:
                return 0

            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            cur = conn.cursor()

            inserted = 0
            for item in elements:
                try:
                    p_lat = item.get("lat") or item.get("center", {}).get("lat")
                    p_lon = item.get("lon") or item.get("center", {}).get("lon")
                    if not p_lat or not p_lon:
                        continue

                    tags = item.get("tags", {})
                    name = tags.get("name") or tags.get("toplanma_alani") or "OSM Acik Alan / Park"
                    category = "OSM Park/Bahce" if tags.get("leisure") == "park" else "OSM Toplanma Alani"

                    cur.execute("INSERT INTO osm_safety_polygons (name, category, geom) VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));", (name, category, p_lon, p_lat))
                    inserted += 1
                except Exception:
                    continue

            cur.close()
            conn.close()
            print(f"TEBRIKLER! {inserted} adet OSM acik alan poligonu PostGIS'e aktarildi!")
            return inserted
        except Exception as e:
            print(f"OSM PostGIS ingest hatasi: {e}")
            return 0

    def save_user_db(self, user: Dict[str, Any]) -> bool:
        """Kullanıcı kaydını PostgreSQL/PostGIS veritabanına kalıcı kaydeder."""
        if not self.check_connection():
            return False
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (id, name, email, password_hash, role, city, unit, token)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    city = EXCLUDED.city,
                    unit = EXCLUDED.unit,
                    token = EXCLUDED.token;
            """, (
                user["id"],
                user["name"],
                user["email"],
                user.get("password", "password123"),
                user["role"],
                user.get("city", "Hatay"),
                user.get("unit", "Sivil"),
                user["token"]
            ))
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"PostgreSQL user save error: {e}")
            return False

    def get_user_by_email_db(self, email: str) -> Optional[Dict[str, Any]]:
        """E-posta ile PostgreSQL'den kullanıcı kaydını getirir."""
        if not self.check_connection():
            return None
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s);", (email.strip(),))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"PostgreSQL user query error: {e}")
            return None

    def get_user_by_token_db(self, token: str) -> Optional[Dict[str, Any]]:
        """Token ile PostgreSQL'den kullanıcı kaydını getirir."""
        if not self.check_connection():
            return None
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE token = %s;", (token.strip(),))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"PostgreSQL user query error: {e}")
            return None

    def insert_damage_point(self, source_type: str, lat: float, lon: float, severity: float = 0.0, label: str = "") -> bool:
        """Hasar/tehlike noktasını (çatlak, yıkım, yol hasarı, SOS) PostGIS'e kalıcı olarak yazar."""
        if not self.check_connection():
            return False
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO damage_points (source_type, severity, label, geom)
                VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));
            """, (source_type, severity, label, lon, lat))
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"PostGIS damage_points insert hatasi: {e}")
            return False

    def query_damage_points_nearby(self, lat: float, lon: float, radius_m: float = 5000.0) -> List[Dict[str, Any]]:
        """PostGIS ST_DWithin ile verilen konuma yakın hasar/tehlike noktalarını döndürür."""
        if not self.check_connection():
            return []
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, source_type, severity, label,
                       ST_Y(geom) AS lat, ST_X(geom) AS lon, created_at,
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) AS dist_m
                FROM damage_points
                WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
                ORDER BY dist_m ASC LIMIT 200;
            """, (lon, lat, lon, lat, radius_m))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"PostGIS damage_points nearby sorgu hatasi: {e}")
            return []

    def query_damage_points_in_bbox(self, bbox) -> List[Dict[str, Any]]:
        """bbox: (west, south, east, north). ST_MakeEnvelope ile o alandaki hasar/tehlike noktalarını döndürür."""
        if not self.check_connection():
            return []
        west, south, east, north = bbox
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, source_type, severity, label, ST_Y(geom) AS lat, ST_X(geom) AS lon, created_at
                FROM damage_points
                WHERE ST_Within(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326))
                LIMIT 5000;
            """, (west, south, east, north))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"PostGIS damage_points bbox sorgu hatasi: {e}")
            return []

    def query_blockages_in_bbox(self, bbox) -> List[Dict[str, Any]]:
        """bbox: (west, south, east, north). O alanla kesişen road_blockages kayıtlarını döndürür."""
        if not self.check_connection():
            return []
        west, south, east, north = bbox
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, title, severity, ST_AsGeoJSON(geom) AS geojson, created_at
                FROM road_blockages
                WHERE ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326));
            """, (west, south, east, north))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"PostGIS road_blockages bbox sorgu hatasi: {e}")
            return []


# Singleton Instance
postgis_engine = PostGISManager()
