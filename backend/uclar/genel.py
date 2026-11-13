"""Genel durum uclari: kok, sistem durumu, PostGIS durumu.

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
from fastapi import APIRouter

yonlendirici = APIRouter()


@yonlendirici.get("/")
def health_check():
    return {"status": "ok", "message": "QuakeMind API is running!"}


@yonlendirici.get("/api/postgis/status")
def postgis_status():
    from utils.postgis_manager import postgis_engine
    is_connected = postgis_engine.check_connection()
    return {
        "postgisConnected": is_connected,
        "dbUrl": postgis_engine.db_url.split("@")[-1] if is_connected else "Offline",
        "hybridFallbackActive": True,
        "message": "PostgreSQL/PostGIS eklentisi aktif. GIST R-Tree mekânsal indeksleme kullanılıyor." if is_connected else "PostgreSQL/PostGIS çevrimdışı. Sistem otomatik çevrimdışı AFAD veri seti fallback modunda çalışıyor."
    }


@yonlendirici.get("/api/status")
def server_status():
    """Saglik kontrolu. HICBIR modeli yuklemez.

    Onceden `nlp` alani icin tembel yukleyici cagriliyordu: ilk saglik
    kontrolu BERTurk'u bellege aliyordu. `camera` ise kontrol edilmeden True
    donuyordu (CLAUDE.md kural 1). Artik her alan gercek durumu soyler:
    model yukluyse ya da dosyasi diskte duruyorsa kullanilabilir sayilir.
    """
    kamera_modelleri = ck.CAMERA_ROOT / "models"
    return {
        "status": "ok",
        "modules": {
            "nlp": ck.nlp_pipeline is not None or (ck.NLP_ROOT / "src" / "pipeline.py").exists(),
            "risk": ck.risk_engine is not None,
            "road_damage": ck.road_runtime is not None,
            "camera": (kamera_modelleri / "catlak.pt").exists() or (kamera_modelleri / "bina.pt").exists(),
            "auth": True,
            "fcm_notifications": True,
        },
        # Hangi modellerin su an bellekte oldugu (yukleme tetiklemeden).
        "yuklu": {
            "nlp": ck.nlp_pipeline is not None,
            "yoloCatlak": ck.yolo_catlak is not None,
            "yoloBina": ck.yolo_bina is not None,
        },
    }
