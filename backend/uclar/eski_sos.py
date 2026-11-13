"""ESKI SOS uclari (/api/sos/alert*). Yeni sozlesme uclari: uclar/sozlesme.py

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


@yonlendirici.post("/api/sos/alert")
def create_sos_alert(req: ck.SOSAlertRequest, _eski: None = Depends(kimlik.eski_uc)):
    if not (-90.0 <= req.latitude <= 90.0) or not (-180.0 <= req.longitude <= 180.0):
        raise HTTPException(status_code=422, detail="Gecersiz koordinat.")

    alert = {
        "id": str(uuid.uuid4()),
        "latitude": req.latitude,
        "longitude": req.longitude,
        "accuracy": req.accuracy,
        "message": req.message,
        "userId": req.userId,
        "batteryPercent": req.batteryPercent,
        "commsStatus": req.commsStatus,
        "powerMode": req.powerMode,
        "sirenActive": req.sirenActive,
        "gpsPollingSec": req.gpsPollingSec,
        "payloadBytes": req.payloadBytes,
        "channel": req.channel,
        "receivedAt": datetime.now(timezone.utc).isoformat(),
    }

    with ck.sos_lock:
        ck.sos_alerts.append(alert)
        total = len(ck.sos_alerts)

    try:
        postgis_engine.insert_damage_point(
            "sos", req.latitude, req.longitude,
            severity=1.0, label=req.message or "SOS Alarmi",
        )
    except Exception as e:
        print(f"damage_points insert (sos) hatasi: {e}")

    canli_yayin.yayinla(
        "yeni-sos",
        id=alert["id"],
        lon=req.longitude,
        lat=req.latitude,
        mesaj=req.message,
        kanal=req.channel,
    )

    return {**alert, "totalAlerts": total}


@yonlendirici.get("/api/sos/alerts")
def list_sos_alerts(_eski: None = Depends(kimlik.eski_uc)):
    with ck.sos_lock:
        alerts = list(ck.sos_alerts)
    return {"alerts": alerts, "totalAlerts": len(alerts)}


@yonlendirici.post("/api/sos/alert/{alert_id}/status")
def update_sos_status(alert_id: str, req: ck.SOSStatusUpdateRequest, _eski: None = Depends(kimlik.eski_uc)):
    with ck.sos_lock:
        for alert in ck.sos_alerts:
            if alert["id"] == alert_id:
                alert["status"] = req.status
                alert["statusUpdatedAt"] = datetime.now(timezone.utc).isoformat()
                return alert
    raise HTTPException(status_code=404, detail="Bilinmeyen SOS uyarisi.")
