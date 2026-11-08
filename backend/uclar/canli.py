"""Tek canli akis (SSE) -- MIMARI.md 6.

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
from fastapi import APIRouter, Cookie
import kimlik
from depo import aktif_depo

yonlendirici = APIRouter()


def _kendi_olayi(hedef_tur: str, hedef_id: str, kullanici_id: str) -> bool:
    depo = aktif_depo()
    kayit = depo.sos_bul(hedef_id) if hedef_tur == "sos" else depo.ihbar_bul(hedef_id)
    return bool(kayit) and kayit.get("kullanici_id") == kullanici_id


def _afetzede_icin(mesaj: dict, kullanici_id: str):
    """Afetzedeye giden akis (J-42): yalniz KENDI cagrisinin ve ihbarinin durum
    degisikligi ve acil bildirimler. Baskasinin cagri konumu ve analiz olaylari
    hic gitmez.

    Ekip (J-54, kullanici karari): afetzede kendi olayina giden ekibin gorev
    durumunu ve o ekip yoldayken konum degisikligini alir. Baska ekiplerin
    konumu gitmez. Mesajda koordinat yok; istemci kendi cagrisini yeniden
    ister, ekibin konumu oradan (yalniz gorev acikken) gelir."""
    if mesaj["tip"] == "bildirim":
        return mesaj
    if mesaj["tip"] == "gorev":
        if _kendi_olayi(mesaj.get("hedefTur", ""), mesaj.get("hedefId", ""), kullanici_id):
            return {
                "tip": "gorev",
                "zaman": mesaj["zaman"],
                "hedefTur": mesaj["hedefTur"],
                "hedefId": mesaj["hedefId"],
                "durum": mesaj.get("durum"),
            }
        return None
    if mesaj["tip"] == "ekip-konumu":
        gorev = aktif_depo().ekibin_acik_gorevi(mesaj.get("ekipId", ""))
        if gorev and _kendi_olayi(gorev["hedef_tur"], gorev["hedef_id"], kullanici_id):
            return {
                "tip": "ekip-konumu",
                "zaman": mesaj["zaman"],
                "hedefTur": gorev["hedef_tur"],
                "hedefId": gorev["hedef_id"],
            }
        return None
    if mesaj["tip"] == "yeni-sos":
        kayit = aktif_depo().sos_bul(mesaj.get("id", ""))
        if kayit and kayit.get("kullanici_id") == kullanici_id:
            return {"tip": "yeni-sos", "zaman": mesaj["zaman"], "id": kayit["id"], "durum": kayit["durum"]}
    if mesaj["tip"] == "ihbar":
        # Kendi ihbarinin durumu (J-51): "goruldu", "kapandi". Baskasinin
        # ihbari ve konumu gitmez.
        kayit = aktif_depo().ihbar_bul(mesaj.get("id", ""))
        if kayit and kayit.get("kullanici_id") == kullanici_id:
            return {"tip": "ihbar", "zaman": mesaj["zaman"], "id": kayit["id"], "tur": kayit["tur"], "durum": kayit["durum"]}
    return None


@yonlendirici.get("/api/live")
async def canli_akis(
    request: Request,
    cerez: Optional[str] = Cookie(default=None, alias=kimlik.YENILEME_CEREZI),
):
    """TEK canli akis (SSE) -- MIMARI 6.

    Sunucu YALNIZCA degisiklik oldugunda mesaj gonderir; istemci hicbir ucu
    yoklamaz. Mesaj tipleri: yeni-sos, is-durumu, yeni-analiz, isi-surumu,
    ekip-konumu, bildirim, ihbar, gorev. Sessiz gecen surelerde 20 saniyede bir `nabiz`
    olayi gider; bu veri degil, canlilik isaretidir: vekil sunucular bos
    baglantiyi kapatmasin ve istemci olmus baglantiyi fark etsin. Eskiden
    yorum satiriydi (": ping"); EventSource yorumlari JavaScript'e iletmedigi
    icin istemci sessizce olen akisi goremiyor, ekran "canli" derken mesaj
    kaciriyordu (J-45 sinamasi).

    Kimlik (J-42): akis eskiden herkese acikti -- giris yapmamis biri de her
    SOS cagrisinin konumunu ve ekiplerin konumunu aliyordu. EventSource baslik
    gonderemedigi icin kimlik, ayni kokenden giden httpOnly yenileme cereziyle
    kanitlanir (jeton dondurulmez). Afetzede yalniz kendi cagrilarini ve acil
    bildirimleri alir.
    """
    kul = kimlik.cerezden_kullanici(cerez)
    if kul is None:
        raise HTTPException(status_code=401, detail="Oturum acilmamis.")
    afetzede = kul["rol"] == "afetzede"
    kuyruk = canli_yayin.abone_ol()

    async def uret():
        try:
            # Akis acilir acilmaz bir kare gonderilir: istemci "bagli" durumuna
            # boylece hemen gecer, ilk olayi beklemez.
            yield ": akis acildi\n\n"
            while True:
                if await request.is_disconnected():
                    return
                try:
                    mesaj = await asyncio.wait_for(kuyruk.get(), timeout=20.0)
                except asyncio.TimeoutError:
                    yield 'event: nabiz\ndata: {"tip":"nabiz"}\n\n'
                    continue
                if afetzede:
                    mesaj = _afetzede_icin(mesaj, kul["id"])
                    if mesaj is None:
                        continue
                yield canli_yayin.sse_bicimle(mesaj)
        finally:
            canli_yayin.abonelik_bitir(kuyruk)

    return StreamingResponse(
        uret(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            # nginx gibi vekiller akisi tamponlamasin.
            "X-Accel-Buffering": "no",
        },
    )
