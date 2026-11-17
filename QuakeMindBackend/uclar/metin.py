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
def analyze_nlp(req: ck.NLPRequest, kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Konsoldan metin analizi (J-170). Kayit acmaz, haritaya yazmaz.

    Model API surecinde degil, metin iscisinde (metin_analizi/isci.py). Adres
    yerel dizinden cozulur; metin disari gitmez (Nominatim kaldirildi).
    Eskiden bu uc sonucu bellekteki eski konum listesine ve PostGIS hasar
    tablosuna da yaziyordu: bir deneme analizi isi haritasina nokta birakiyordu."""
    import hiz_siniri
    import islem_kaydi
    from metin_analizi import isci

    hiz_siniri.metin_kontrol(kul["id"])
    try:
        sonuc = isci.coz(req.text)
    except isci.MetinModeliYok as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    islem_kaydi.kaydet(
        kul,
        "metin_analizi",
        f"Metin analizi: {sonuc['kategori']}"
        + (f", aciliyet {sonuc['aciliyet']}" if sonuc.get("aciliyet") is not None else "")
        + (f", konum: {sonuc['konumMetin']} ({sonuc['konumDuzeyi']})" if sonuc.get("konumMetin") else ", konum bulunamadı"),
        ayrinti={
            "metin": req.text[:500],
            "ilgili": sonuc["ilgili"],
            "kategori": sonuc["kategori"],
            "kategoriKaynagi": sonuc.get("kategoriKaynagi"),
            "aciliyet": sonuc.get("aciliyet"),
            "guven": sonuc.get("guven"),
            "konumMetin": sonuc.get("konumMetin"),
            "konumDuzeyi": sonuc.get("konumDuzeyi"),
            "konum": sonuc.get("konum"),
            "sinyaller": [x["sinyal"] for x in sonuc.get("sinyaller", [])],
            "sureMs": sonuc.get("sureMs"),
        },
    )
    return sonuc


@yonlendirici.get("/api/nlp/locations")
def list_nlp_locations(_eski: None = Depends(kimlik.eski_uc)):
    with ck.nlp_locations_lock:
        locations = list(ck.nlp_locations)
    return {"locations": locations, "totalLocations": len(locations)}
