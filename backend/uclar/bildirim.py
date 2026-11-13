"""Acil bildirim ve ekip sohbeti uclari.

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
from fastapi import APIRouter, Depends, Query
from pydantic import Field
import kimlik
from depo import aktif_depo

yonlendirici = APIRouter()


# --- acil durum bildirimleri (J-45) ----------------------------------------
#
# Bildirimler depoda (`bildirimler` tablosu). Eskiden yalniz bellekteydi:
# sunucu yeniden baslayinca yayindaki bildirim kayboluyor, kimin gonderdigi
# tutulmuyor, yanlis gonderilen bildirim geri cekilemiyordu.
#
# Iki yazan var:
#   * POST /api/bildirimler      -- yeni kimlik; yalniz koordinator ve yonetici
#   * POST /api/notifications/send_emergency -- eski web; eski kimligi (kodda
#     sabit demo jetonlari dahil) kabul ediyor. Kayit 'eski' kaynagiyla tutulur,
#     konsolda ayri gorunur ve geri cekilebilir. Eski kimligin kapatilmasi
#     kullanici karari bekliyor (J-45 madde 2).

ONEMLER = ("acil", "uyari", "bilgi")
# Eski uc Ingilizce adlari kullaniyor; depo tek sozluk tutar.
ESKI_ONEM = {"critical": "acil", "warning": "uyari", "info": "bilgi"}
ESKI_ONEM_GERI = {v: k for k, v in ESKI_ONEM.items()}
YONETIM = ("koordinator", "yonetici")


class BildirimIstegi(BaseModel):
    baslik: str = Field(..., min_length=3, max_length=120)
    metin: str = Field(..., min_length=3, max_length=1000)
    onem: str = "uyari"
    konum: Optional[str] = Field(None, max_length=120)
    buyukluk: Optional[float] = Field(None, ge=0, le=10)


def _bildirim_cikti(k: dict, ayrintili: bool = False) -> dict:
    """Afetzedeye giden alanlar; `ayrintili` konsol icin kaynagi ve kisileri ekler."""
    cikti = {
        "id": k["id"],
        "baslik": k["baslik"],
        "metin": k["metin"],
        "onem": k["onem"],
        "konum": k.get("konum"),
        "buyukluk": k.get("buyukluk"),
        "zaman": round(k["zaman"] * 1000),
    }
    if ayrintili:
        cikti.update(
            kaynak=k["kaynak"],
            gonderen=k.get("gonderen_ad"),
            kaldirildi=round(k["kaldirildi"] * 1000) if k.get("kaldirildi") else None,
            kaldiran=k.get("kaldiran_ad"),
        )
    return cikti


def _eski_bicim(k: dict) -> dict:
    """Eski webin bandinin bekledigi alanlar (EmergencyNotificationBanner)."""
    return {
        "id": k["id"],
        "title": k["baslik"],
        "body": k["metin"],
        "severity": ESKI_ONEM_GERI.get(k["onem"], "warning"),
        "location": k.get("konum"),
        "magnitude": k.get("buyukluk"),
        "timestamp": datetime.fromtimestamp(k["zaman"], timezone.utc).strftime("%H:%M:%S"),
    }


def _yayinla(kayit: dict, durum: str) -> None:
    # Afetzede ekrani bildirimi canli akistan alir; yoklama yok (kural 4).
    canli_yayin.yayinla(
        "bildirim", id=kayit["id"], baslik=kayit["baslik"], onem=kayit["onem"], durum=durum
    )


@yonlendirici.post("/api/bildirimler", status_code=201)
def bildirim_yayinla(
    istek: BildirimIstegi, kul: dict = Depends(kimlik.rol_gerektir(*YONETIM))
):
    """Acil durum bildirimi yayinlar: depoya yazar, canli akisla herkese gider."""
    if istek.onem not in ONEMLER:
        raise HTTPException(status_code=422, detail="Onem: acil | uyari | bilgi")
    baslik, metin = istek.baslik.strip(), istek.metin.strip()
    if len(baslik) < 3 or len(metin) < 3:
        raise HTTPException(status_code=422, detail="Baslik ve metin bos olamaz.")
    kayit = aktif_depo().bildirim_ekle(
        baslik=baslik,
        metin=metin,
        onem=istek.onem,
        kaynak="konsol",
        konum=(istek.konum or "").strip() or None,
        buyukluk=istek.buyukluk,
        gonderen_id=kul["id"],
        gonderen_ad=kul.get("ad_soyad"),
    )
    _yayinla(kayit, "yayinda")
    return _bildirim_cikti(kayit, ayrintili=True)


@yonlendirici.post("/api/bildirimler/{bildirim_id}/kaldir")
def bildirim_kaldir(bildirim_id: str, kul: dict = Depends(kimlik.rol_gerektir(*YONETIM))):
    """Yanlis ya da tanimadik bildirimi geri ceker; kayit silinmez."""
    depo = aktif_depo()
    if depo.bildirim_bul(bildirim_id) is None:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadi.")
    if not depo.bildirim_kaldir(bildirim_id, kul["id"], kul.get("ad_soyad")):
        raise HTTPException(status_code=409, detail="Bildirim zaten geri cekilmis.")
    kayit = depo.bildirim_bul(bildirim_id)
    _yayinla(kayit, "kaldirildi")
    return _bildirim_cikti(kayit, ayrintili=True)


@yonlendirici.get("/api/bildirimler")
def bildirim_gecmisi(
    sinir: int = Query(default=20, ge=1, le=200),
    _kul: dict = Depends(kimlik.rol_gerektir("saha", *YONETIM)),
):
    """Konsol icin: yayindakiler ve geri cekilenler, gonderen ve kaynakla."""
    return [
        _bildirim_cikti(k, ayrintili=True)
        for k in aktif_depo().bildirim_listele(yalniz_yayinda=False, sinir=sinir)
    ]


@yonlendirici.get("/api/bildirimler/aktif")
def aktif_bildirimler(_kul: dict = Depends(kimlik.kullanici)):
    """Yayindaki en yeni 5 bildirim (afetzede ekraninin bandi, J-43).

    Gonderenin adi ve kaynagi afetzedeye gitmez. Buyukluk ve konum gonderen
    yazmadiysa bos gelir (eskiden 6,8 ve "Hatay" varsayilan olarak uyduruluyordu)."""
    return [_bildirim_cikti(k) for k in aktif_depo().bildirim_listele(yalniz_yayinda=True, sinir=5)]


@yonlendirici.post("/api/notifications/send_emergency")
def send_emergency_notification(req: ck.EmergencyNotificationRequest):
    kul = ck._require_role(req.token, {"responder", "admin"})
    kayit = aktif_depo().bildirim_ekle(
        baslik=req.title,
        metin=req.body,
        onem=ESKI_ONEM.get(req.severity, "uyari"),
        kaynak="eski",
        konum=req.location,
        buyukluk=req.magnitude,
        gonderen_id=kul.get("id"),
        gonderen_ad=kul.get("name"),
    )
    _yayinla(kayit, "yayinda")
    return {
        "status": "broadcasted",
        "message": "Acil durum push bildirimi tum cihazlara ve frontend'e yayinlandi.",
        "activeAlert": _eski_bicim(kayit),
    }


@yonlendirici.get("/api/notifications/active")
def get_active_emergency_notifications():
    """Eski web bandi (bicimi degismedi). Artik depodan okur: konsoldan
    yayinlanan bildirim eski webde de gorunur, geri cekilen gorunmez."""
    yayinda = aktif_depo().bildirim_listele(yalniz_yayinda=True, sinir=200)
    return {
        "activeAlert": _eski_bicim(yayinda[0]) if yayinda else None,
        "totalAlerts": len(yayinda),
    }


@yonlendirici.post("/api/chat/send")
def send_team_chat_message(req: ck.ChatMessageRequest):
    user = ck._require_role(req.token, {"responder", "admin"})
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")
    message = {
        "id": f"msg-{uuid.uuid4().hex[:10]}",
        "senderId": user.get("id"),
        "senderName": user.get("name") or user.get("email") or "Ekip Üyesi",
        "senderUnit": user.get("unit"),
        "text": text[:2000],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ck.team_chat_messages.append(message)
    if len(ck.team_chat_messages) > ck._TEAM_CHAT_LIMIT:
        del ck.team_chat_messages[: len(ck.team_chat_messages) - ck._TEAM_CHAT_LIMIT]
    return {"status": "sent", "message": message}


@yonlendirici.get("/api/chat/messages")
def get_team_chat_messages(token: Optional[str] = None, limit: int = 50):
    ck._require_role(token, {"responder", "admin"})
    capped_limit = max(1, min(limit, ck._TEAM_CHAT_LIMIT))
    return {"messages": ck.team_chat_messages[-capped_limit:]}
