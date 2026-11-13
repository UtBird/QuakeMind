"""Turkce metin analizi uclari (BERTurk).

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


@yonlendirici.post("/api/nlp/analyze")
def analyze_nlp(req: ck.NLPRequest, _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    pipeline = ck._get_nlp_pipeline()
    if not pipeline:
        raise HTTPException(status_code=503, detail="NLP model is not loaded.")

    try:
        with ck.temporary_sys_path(ck.NLP_ROOT), ck.temporary_cwd(ck.NLP_ROOT):
            result = pipeline.process_tweet(req.text)
        if not result:
            return {"status": "ignored", "reason": "Not related to disaster"}

        konum = result.get("konum")
        if konum and len(konum) == 2:
            entry = {
                "id": str(uuid.uuid4()),
                "latitude": konum[0],
                "longitude": konum[1],
                "konumMetin": result.get("konum_metin"),
                "kategori": result.get("kategori"),
                "aciliyet": result.get("aciliyet"),
                "sourceText": req.text,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
            }
            with ck.nlp_locations_lock:
                ck.nlp_locations.append(entry)
            result["nlpLocationId"] = entry["id"]

            # Best-effort: a geocoded tweet is a location-tagged "bildirim" just
            # like a camera detection or an SOS alert -- feeds the same
            # damage_points table so /heatmap can count report density per
            # source (Twitter/NLP, camera, SOS) instead of only satellite data.
            try:
                postgis_engine.insert_damage_point(
                    "twitter", konum[0], konum[1],
                    severity=result.get("guven_skoru") or 0.5,
                    label=result.get("kategori") or "Twitter/NLP Bildirimi",
                )
            except Exception as e:
                print(f"damage_points insert (twitter) hatasi: {e}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@yonlendirici.get("/api/nlp/locations")
def list_nlp_locations(_eski: None = Depends(kimlik.eski_uc)):
    with ck.nlp_locations_lock:
        locations = list(ck.nlp_locations)
    return {"locations": locations, "totalLocations": len(locations)}
