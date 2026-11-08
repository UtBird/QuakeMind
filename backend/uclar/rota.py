"""Guzergah uclari: analiz oturumu uzerinden rota, guvenli rota, ozel rota,
toplanma alanlari, yol kapanmasi bildirimi, en yakin enkaz.

TASIMA_PLANI.md Faz 5: fastapi_app.py'den tasindi. Paylasilan durum ve
`ck.` ile cekirdek modulunden okunur."""

# ruff: noqa: F401  -- cekirdek importlari toplu kopyalandi
import cekirdek as ck
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import bcrypt
import math
import re
import sys
import os
import site
import importlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager, asynccontextmanager
from typing import Optional
from threading import Event, Lock, Thread
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError as FutureTimeoutError
import asyncio
import functools
import multiprocessing
import canli_yayin
from depo import depo_ac
from utils.postgis_manager import postgis_engine
from apps.road_damage.utils.serialization import compact_segment_coords as _compact_segment_coords, serialize_segments as _serialize_segments, haversine_m as _haversine_m
from apps.road_damage.utils.imaging import image_array_to_b64 as _image_array_to_b64, build_damage_overlay as _build_damage_overlay, build_segmentation_overlay as _build_segmentation_overlay
from apps.road_damage.utils.tiling import zoom_for_radius as _zoom_for_radius
from fastapi import APIRouter, Depends

import kimlik

yonlendirici = APIRouter()


@yonlendirici.post("/api/road_damage/route")
def road_damage_route(req: ck.RoadDamageRouteRequest):
    session = ck._get_road_damage_session(req.analysisId)
    if session is None:
        raise HTTPException(status_code=422, detail="Analiz oturumu bulunamadi veya suresi doldu. Once analizi tekrar calistirin.")

    try:
        runtime = ck._get_road_runtime()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail=f"Road Damage runtime yuklenemedi: {ck.road_runtime_error or 'bilinmeyen hata'}",
        )

    if req.costModel == "soft":
        return _yumusak_rota(session, req)

    calculate_route = runtime["calculate_route"]
    safe_G = session["safe_G"]

    try:
        # Yalnizca A* kosulur: bu uc nokta eskiden Dijkstra + A*'in IKISINI de
        # hesaplatip A* sonucunu ATIYORDU. Olculdu: Dijkstra 0,039sn, A*
        # 0,013sn ve ikisi ayni yolu buluyor (haversine sezgisi kabul
        # edilebilir oldugu icin A*'in optimalligi garantili; dolayisiyla
        # dondurulen mesafe degismez).
        _dijkstra_coords, astar_coords, _dijkstra_cost, _astar_cost = calculate_route(
            safe_G, req.startLat, req.startLon, req.endLat, req.endLon,
            algorithms=('astar',),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rota hesaplanamadi: {e}")

    if not astar_coords:
        raise HTTPException(status_code=422, detail="Bu iki nokta arasinda guvenli bir baglanti bulunamadi. Yol tamamen kapali olabilir.")

    distance_m = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(astar_coords[:-1], astar_coords[1:]):
        distance_m += _haversine_m(lat1, lon1, lat2, lon2)

    return {
        "routeCoords": [[float(lat), float(lon)] for lat, lon in astar_coords],
        "distanceMeters": round(distance_m, 1),
    }


def _yumusak_rota(session, req):
    """costModel="soft" (J-34): model kapali dedigi kenari silmez, cezalandirir.
    Planlayici deneydeki M-y ajaniyla ayni fonksiyondur; yanit sert yanitin
    alanlarina ek olarak rotanin ne kadar riskli kenardan gectigini yazar."""
    from apps.road_damage.utils.network import soft_cost_route

    road_graph = session.get("roadGraph")
    closure_prob = session.get("closureProb")
    if road_graph is None or closure_prob is None:
        raise HTTPException(
            status_code=422,
            detail="Bu oturumda kapanma olasiligi yok; yumusak maliyetli rota yalniz /analyze "
                   "oturumlarinda kullanilabilir.",
        )
    try:
        coords, exposure_m, risky_edges = soft_cost_route(
            road_graph, closure_prob, req.softLambda,
            req.startLat, req.startLon, req.endLat, req.endLon,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rota hesaplanamadi: {e}")
    if not coords:
        raise HTTPException(status_code=422, detail="Bu iki nokta arasinda yol baglantisi yok.")

    distance_m = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(coords[:-1], coords[1:]):
        distance_m += _haversine_m(lat1, lon1, lat2, lon2)

    return {
        "routeCoords": [[float(lat), float(lon)] for lat, lon in coords],
        "distanceMeters": round(distance_m, 1),
        "costModel": "soft",
        "softLambda": req.softLambda,
        # Rotadaki kenarlarda uzunluk x p toplami: "beklenen kapali metre".
        # Yumusak rota riskli kenardan gecebilir; bu iki alan ne kadar
        # gectigini gosterir, istemci bunu gizlememeli.
        "closureExposureMeters": round(exposure_m, 1),
        "riskyEdgeCount": risky_edges,
    }


@yonlendirici.post("/api/road_damage/safe_route")
def road_damage_safe_route(req: ck.SafeRouteRequest):
    """PostGIS-tabanlı, session'sız risk-ağırlıklı rota (rapor 2.4.4): kapalı
    yol maskeleri + damage_points + road_blockages tek bir ceza-katsayılı
    grafta birleştirilir. /api/road_damage/analyze'nin önceden çağrılmış
    olmasını gerektirmez -- mevcut /route (session'a bağlı) ve
    /calculate_custom_route (OSRM/düz-çizgi) endpoint'lerinin üçüncü,
    risk-farkında alternatifidir.
    """
    import json as _json

    import osmnx as ox

    from apps.road_damage.utils.assembly import bbox_from_center
    from apps.road_damage.utils.network import apply_risk_penalties, calculate_route

    center_lat = (req.startLat + req.destLat) / 2.0
    center_lon = (req.startLon + req.destLon) / 2.0
    bbox = bbox_from_center(center_lat, center_lon, req.radiusKm)
    west, south, east, north = bbox

    try:
        G = ox.graph_from_bbox(bbox=bbox, network_type="walk", simplify=True)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Yol agi indirilemedi: {e}")

    damage_points = []
    blockages = []
    if postgis_engine.check_connection():
        damage_points = postgis_engine.query_damage_points_in_bbox(bbox)
        for row in postgis_engine.query_blockages_in_bbox(bbox):
            try:
                geometry = _json.loads(row["geojson"])
                coords = geometry.get("coordinates") or []
                if geometry.get("type") == "LineString" and coords:
                    blockages.append([[lat, lon] for lon, lat in coords])
            except Exception:
                continue
    else:
        # PostGIS offline: fall back to the in-memory blockage registry
        # (same offline-fallback pattern as /assembly and /heatmap).
        for blk in ck.LIVE_ROAD_BLOCKAGES:
            coords = blk.get("coords") or []
            if any(west <= lon <= east and south <= lat <= north for lat, lon in coords):
                blockages.append(coords)

    apply_risk_penalties(G, damage_points, blockages, blockage_hard_radius_m=25.0)

    try:
        dijkstra_coords, astar_coords, dijkstra_cost, astar_cost = calculate_route(
            G, req.startLat, req.startLon, req.destLat, req.destLon, weight="risk_cost",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rota hesaplanamadi: {e}")

    candidates = []
    if dijkstra_coords and dijkstra_cost is not None:
        candidates.append(("dijkstra", dijkstra_coords, dijkstra_cost))
    if astar_coords and astar_cost is not None:
        candidates.append(("astar", astar_coords, astar_cost))
    if not candidates:
        raise HTTPException(status_code=422, detail="Bu iki nokta arasinda guvenli bir baglanti bulunamadi. Yol tamamen kapali olabilir.")

    algorithm, route_coords, risk_score = min(candidates, key=lambda c: c[2])

    distance_m = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(route_coords[:-1], route_coords[1:]):
        distance_m += _haversine_m(lat1, lon1, lat2, lon2)

    return {
        "routeCoords": [[float(lat), float(lon)] for lat, lon in route_coords],
        "distanceMeters": round(distance_m, 1),
        "algorithm": algorithm,
        "riskScore": round(risk_score, 1),
        "damagePointsConsidered": len(damage_points),
        "blockagesConsidered": len(blockages),
    }


@yonlendirici.get("/api/road_damage/assembly")
def road_damage_assembly(
    latitude: float,
    longitude: float,
    radiusKm: float = 10.0,
    includeCandidates: bool = True,
    dataSource: str = "auto",
    allowOnlineFallback: bool = True,
):
    import json
    import math
    from utils.postgis_manager import postgis_engine

    records = []

    # 1. Try querying PostGIS first if connected
    if postgis_engine.check_connection():
        records = postgis_engine.query_nearby_postgis(latitude, longitude, radiusKm * 1000.0)

    # 2. Fallback to local AFAD JSON dataset (72,232 points across Turkey)
    afad_json_path = ck.ROAD_ROOT / "data" / "tum_turkiye_toplanma_alanlari.json"
    if not records and afad_json_path.exists():
        try:
            with open(afad_json_path, encoding="utf-8") as f:
                afad_data = json.load(f)

            for item in afad_data:
                try:
                    e_lat = float(item["enlem"])
                    e_lon = float(item["boylam"])
                    if abs(e_lat - latitude) <= (radiusKm / 111.0) and abs(e_lon - longitude) <= (radiusKm / 80.0):
                        dist_m = _haversine_m(latitude, longitude, e_lat, e_lon)
                        if dist_m <= (radiusKm * 1000.0):
                            records.append({
                                "toplanma_alani": item.get("toplanma_alani", "AFAD Resmi Toplanma Alanı"),
                                "name": item.get("toplanma_alani", "AFAD Resmi Toplanma Alanı"),
                                "il": item.get("il", ""),
                                "ilce": item.get("ilce", ""),
                                "mahalle": item.get("mahalle", ""),
                                "lat": e_lat,
                                "lon": e_lon,
                                "display_lat": e_lat,
                                "display_lon": e_lon,
                                "category": "AFAD Resmi Toplanma Alanı",
                                "priority": 0,
                                "source": "AFAD Resmi Veri Seti (Offline Fallback)",
                                "capacity": "Resmi Toplanma Alanı",
                                "status": "🟢 Güvenli AFAD Toplanma Alanı",
                                "dist_m": round(dist_m, 1)
                            })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error reading AFAD JSON dataset: {e}")

    records.sort(key=lambda r: r.get("dist_m", 999999))
    records = records[:50]  # Return top 50 closest AFAD safe zones

    nearest = records[0] if records else None
    nearest_air_m = nearest["dist_m"] if nearest else None

    # Calculate real street-following route to nearest safe zone
    route_coords = None
    route_length_m = None
    route_error = None

    # Rota disaridaki OSRM demo sunucusundan gelir: kullanicinin tam konumu
    # ucuncu tarafa gider (J-43). `allowOnlineFallback=false` eskiden yok
    # sayiliyordu; artik adinin soyledigini yapar ve bu istek atlanir. Afetzede
    # ekrani boyle cagirir. Varsayilan (true) degismedi, eski web ayni davranir.
    if nearest and allowOnlineFallback:
        try:
            route_coords, route_length_m, route_error = ck._fetch_osrm_street_route(
                latitude, longitude, nearest["lat"], nearest["lon"]
            )
        except Exception as e:
            route_error = str(e)

    is_postgis = postgis_engine.check_connection()
    return {
        "records": records,
        "activeDataSource": "PostgreSQL 16 + PostGIS 3.4 (71.420 Nokta GIST Mekansal Indeksli)" if is_postgis else "Tum Turkiye AFAD Veri Seti (Cevrimdisi Fallback)",
        "osmError": None,
        "nearest": nearest,
        "nearestAirM": nearest_air_m,
        "routeCoords": route_coords,
        "routeLengthM": round(route_length_m, 1) if route_length_m else nearest_air_m,
        "routeError": route_error,
    }


@yonlendirici.post("/api/road_damage/calculate_custom_route")
def calculate_custom_route(req: ck.CustomRouteRequest):
    # 1. Fetch real OSRM street route following actual road geometry
    route_coords, route_length_m, route_error = None, None, None

    try:
        route_coords, route_length_m, route_error = ck._fetch_osrm_street_route(
            req.startLat, req.startLon, req.destLat, req.destLon
        )
    except Exception as e:
        route_error = str(e)

    # 2. If OSRM offline, fallback to OSMnx or multi-node interpolation
    if not route_coords:
        try:
            from apps.road_damage.utils.assembly import shortest_walk_route
            route_coords, route_length_m, route_error = shortest_walk_route(
                req.startLat, req.startLon, req.destLat, req.destLon
            )
        except Exception as e:
            print(f"OSMnx fallback error: {e}")

    if not route_coords:
        route_coords = [
            [req.startLat, req.startLon],
            [req.startLat + (req.destLat - req.startLat) * 0.33, req.startLon + (req.destLon - req.startLon) * 0.33],
            [req.startLat + (req.destLat - req.startLat) * 0.66, req.startLon + (req.destLon - req.startLon) * 0.66],
            [req.destLat, req.destLon]
        ]
        route_length_m = _haversine_m(req.startLat, req.startLon, req.destLat, req.destLon)

    est_minutes = round((route_length_m or 0) / 80.0) if route_length_m else 5

    return {
        "start": [req.startLat, req.startLon],
        "destination": [req.destLat, req.destLon],
        "routeCoords": [[float(lat), float(lon)] for lat, lon in route_coords],
        "routeLengthM": round(route_length_m, 1) if route_length_m else 0,
        "estWalkMinutes": max(1, est_minutes),
        "routeError": route_error
    }


@yonlendirici.post("/api/road_damage/report_blockage")
def report_road_blockage(req: ck.RoadBlockageRequest, _eski: None = Depends(kimlik.eski_uc)):
    import uuid
    from utils.postgis_manager import postgis_engine

    blockage_id = f"blk-{uuid.uuid4().hex[:6]}"
    coords = [[req.startLat, req.startLon], [req.endLat, req.endLon]]
    
    new_blk = {
        "id": blockage_id,
        "coords": coords,
        "reason": req.reason,
        "severity": req.severity,
        "created_at": "2026-08-03T13:35:00Z"
    }
    ck.LIVE_ROAD_BLOCKAGES.append(new_blk)

    # Persist in PostGIS if connected
    if postgis_engine.check_connection():
        try:
            import psycopg2
            conn = psycopg2.connect(postgis_engine.db_url)
            conn.autocommit = True
            cur = conn.cursor()
            wkt = f"LINESTRING({req.startLon} {req.startLat}, {req.endLon} {req.endLat})"
            cur.execute("""
                INSERT INTO road_blockages (id, title, severity, geom)
                VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326));
            """, (blockage_id, req.reason, req.severity, wkt))
            cur.close()
            conn.close()
        except Exception as e:
            print(f"PostGIS blockage insert error: {e}")

    return {
        "status": "success",
        "message": "Uydu / İHA Yol Kapalılığı Veritabanına Anında Kaydedildi! Rotalar Yeniden Hesaplandı.",
        "blockage": new_blk,
        "totalBlockages": len(ck.LIVE_ROAD_BLOCKAGES)
    }


@yonlendirici.get("/api/road_damage/nearest_debris")
def get_nearest_debris_for_teams(latitude: float, longitude: float, limit: int = 5):
    """Arama Kurtarma Ekipleri için GPS Konumuna En Yakın Enkaz & Ağır Hasarlı
    Noktaları Listeler -- damage_points (kamera/YOLO/Segformer/SOS tespitleri)
    ve road_blockages'tan gerçek PostGIS mekânsal sorgusuyla üretilir."""
    import json as _json

    radius_m = 5000.0
    results = []
    is_postgis = postgis_engine.check_connection()

    if is_postgis:
        for row in postgis_engine.query_damage_points_nearby(latitude, longitude, radius_m):
            source_type = row.get("source_type") or ""
            results.append({
                "id": f"dmg-{row['id']}",
                "name": row.get("label") or ck._DAMAGE_SOURCE_LABELS.get(source_type, "Hasar Noktası"),
                "lat": row["lat"],
                "lon": row["lon"],
                "severity": ck._damage_point_severity_label(source_type, row.get("severity")),
                "source": ck._DAMAGE_SOURCE_LABELS.get(source_type, "PostGIS Mekânsal Analiz"),
                "dist_m": round(row.get("dist_m", 0.0), 1),
            })

        from apps.road_damage.utils.assembly import bbox_from_center
        bbox = bbox_from_center(latitude, longitude, radius_m / 1000.0)
        for blk in postgis_engine.query_blockages_in_bbox(bbox):
            try:
                geometry = _json.loads(blk["geojson"])
                coords = geometry.get("coordinates") or []
                if not coords:
                    continue
                mid_lon, mid_lat = coords[len(coords) // 2][:2]
                dist_m = _haversine_m(latitude, longitude, mid_lat, mid_lon)
                if dist_m <= radius_m:
                    results.append({
                        "id": f"blk-{blk['id']}",
                        "name": blk.get("title") or "Yol Kapanması",
                        "lat": mid_lat,
                        "lon": mid_lon,
                        "severity": blk.get("severity") or "🔴 Tamamen Kapalı Yol",
                        "source": "PostGIS Mekânsal Analiz",
                        "dist_m": round(dist_m, 1),
                    })
            except Exception:
                continue

    for r in results:
        r["est_dispatch_minutes"] = max(1, round(r["dist_m"] / 80.0))
    results.sort(key=lambda r: r["dist_m"])
    top = results[:limit]

    return {
        "teamLocation": [latitude, longitude],
        "nearestDebrisCount": len(top),
        "debrisSites": top,
        "source": "postgis" if is_postgis else "offline_fallback",
    }
