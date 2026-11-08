"""Deprem riski uclari (CatBoost; model dosyadan yuklenir, istek yolunda egitim yok).

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
import json
import kimlik

yonlendirici = APIRouter()


@yonlendirici.post("/api/risk/predict")
def predict_risk(req: ck.RiskRequest):
    if not ck.risk_engine:
        raise HTTPException(status_code=503, detail="Risk model is not loaded.")
    
    try:
        manual_coords = None
        if req.manualLatitude is not None and req.manualLongitude is not None:
            manual_coords = (req.manualLatitude, req.manualLongitude)
        
        with ck.temporary_sys_path(ck.RISK_ROOT), ck.temporary_cwd(ck.RISK_ROOT):
            if req.refreshData:
                from data_manager import fetch_and_update_data
                fetch_and_update_data()
            
            # Tek hesap: build_payload ayni motoru kullanir. Onceden burada
            # predict_city_risk bir kez, build_payload icinde YENI bir motorla
            # bir kez daha kosuyordu (olculen: istek basina ~20 sn).
            from risk_bridge import build_payload
            payload = build_payload(
                city=req.city,
                manual_coords=manual_coords,
                refresh_data=req.refreshData,
                motor=ck.risk_engine,
            )
            return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


IL_MERKEZLERI = Path(__file__).resolve().parents[1] / "veri" / "il_merkezleri.json"


@yonlendirici.get("/api/risk/iller")
def risk_illeri(_kul: dict = Depends(kimlik.kullanici)):
    """81 ilin merkez koordinati ve kaynak kunyesi (araclar_il_merkezleri_uret.py).

    Risk istegi koordinatla gider; sunucu konumu dis servisten aramaz."""
    if not IL_MERKEZLERI.exists():
        return {"iller": [], "kaynak": None,
                "not": "Il merkezleri uretilmedi: python araclar_il_merkezleri_uret.py"}
    return json.loads(IL_MERKEZLERI.read_text(encoding="utf-8"))


@yonlendirici.get("/api/risk/fault_lines")
def risk_fault_lines():
    lines = ck._get_turkey_fault_lines()
    return {"faultLines": lines, "count": len(lines)}


@yonlendirici.get("/api/risk/all_quakes")
def risk_all_quakes(
    minMagnitude: float = 0.0,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    limit: int = 500,
    sortBy: str = "time",
):
    """Rasathane view: the full national catalog (query.csv, ~20k events back to
    1933), independent of any selected city — unlike /predict's 150km-around-one-city
    slice. Filterable/sortable/paginated so a browser never has to render 20k markers
    at once."""
    if not ck.risk_engine:
        raise HTTPException(status_code=503, detail="Risk model is not loaded.")

    try:
        import pandas as pd

        with ck.temporary_sys_path(ck.RISK_ROOT), ck.temporary_cwd(ck.RISK_ROOT):
            ck.risk_engine._prepare_frames()
            df = ck.risk_engine.df_full.copy()

        df = df[df["mag"] >= minMagnitude]
        if startDate:
            start_ts = pd.Timestamp(startDate)
            if start_ts.tzinfo is None:
                start_ts = start_ts.tz_localize("UTC")
            df = df[df["time"] >= start_ts]
        if endDate:
            end_ts = pd.Timestamp(endDate)
            if end_ts.tzinfo is None:
                end_ts = end_ts.tz_localize("UTC")
            df = df[df["time"] <= end_ts]

        total_matched = int(len(df))

        if sortBy == "magnitude":
            df = df.sort_values(["mag", "time"], ascending=[False, False])
        else:
            df = df.sort_values("time", ascending=False)

        capped_limit = max(1, min(int(limit), 2000))
        df = df.head(capped_limit)

        quakes = [
            {
                "time": str(row["time"]),
                "place": row.get("place") or "Bilinmeyen konum",
                "magnitude": float(row["mag"]),
                "depth": float(row["depth"]) if pd.notna(row.get("depth")) else None,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "status": row.get("status") or "reviewed",
            }
            for _, row in df.iterrows()
        ]

        full_range = ck.risk_engine.df_full["time"]
        return {
            "quakes": quakes,
            "totalMatched": total_matched,
            "returned": len(quakes),
            "datasetStart": str(full_range.min()),
            "datasetEnd": str(full_range.max()),
            "datasetTotal": int(len(ck.risk_engine.df_full)),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@yonlendirici.post("/api/risk/refresh_live_data")
def risk_refresh_live_data():
    """Pulls fresh Kandilli (+ USGS gap-fill) data into query.csv and invalidates
    the risk engine's in-memory frames/model so the next request re-reads it."""
    if not ck.risk_engine:
        raise HTTPException(status_code=503, detail="Risk model is not loaded.")

    try:
        with ck.temporary_sys_path(ck.RISK_ROOT), ck.temporary_cwd(ck.RISK_ROOT):
            from data_manager import fetch_and_update_data
            message = fetch_and_update_data()

        ck.risk_engine.df_full = None
        ck.risk_engine.df_main = None
        ck.risk_engine.model = None

        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
