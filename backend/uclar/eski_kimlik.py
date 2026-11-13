"""ESKI kimlik uclari (/api/auth/*). Eski web icin oldugu gibi duruyor;
konsol devralinca kaldirilacak (TASIMA_PLANI.md Faz 2). Yeni akis: uclar/oturum.py

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

# ROL ISTEMCIDEN GELMEZ (CLAUDE.md kural 5, J-119). Eski kayit ve giris uclari
# istemcinin gonderdigi `role` alanini (ve giriste bilinmeyen e-posta icin
# varsayilan "responder"i) aynen yaziyordu: herkes kendini ekip olarak
# kaydedebiliyordu. Artik bu uclardan acilan her hesap afetzededir; yetki
# yukseltme yalniz yeni akista (uclar/oturum.py) yonetici eliyle yapilir. Uclar
# ayrica diger eski uclar gibi varsayilan olarak KAPALIDIR (kimlik.eski_uc, J-53).
ESKI_VARSAYILAN_ROL = "survivor"


@yonlendirici.post("/api/auth/register")
def auth_register(req: ck.UserRegisterRequest, _eski: None = Depends(kimlik.eski_uc)):
    email = req.email.lower().strip()
    rol = ESKI_VARSAYILAN_ROL  # req.role yok sayilir

    # Check PostgreSQL database first
    existing = postgis_engine.get_user_by_email_db(email)
    if existing or email in ck.USER_DATABASE:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayitli.")

    user_id = f"usr-{uuid.uuid4().hex[:6]}"
    token = f"token-{uuid.uuid4().hex[:12]}"
    new_user = {
        "id": user_id,
        "name": req.name,
        "email": email,
        "password": ck._hash_password(req.password),
        "role": rol,
        "city": req.city or "Hatay",
        "unit": "Sivil Afetzede",
        "token": token
    }
    ck.USER_DATABASE[email] = new_user

    # Save permanently to PostgreSQL / PostGIS Database
    saved_to_db = postgis_engine.save_user_db(new_user)
    db_status_text = "PostgreSQL DB'ye Kaydedildi" if saved_to_db else "Hafızaya Kaydedildi"

    user_profile = dict(new_user)
    user_profile.pop("password", None)
    return {
        "status": "success",
        "message": f"Hesabiniz basariyla olusturuldu ({rol.upper()} yetkisi ile - {db_status_text}).",
        "token": token,
        "user": user_profile,
        "savedToPostgres": saved_to_db
    }


@yonlendirici.post("/api/auth/login")
def auth_login(req: ck.UserLoginRequest, _eski: None = Depends(kimlik.eski_uc)):
    email = req.email.lower().strip()

    # Check PostgreSQL database first
    db_user = postgis_engine.get_user_by_email_db(email)
    user = db_user or ck.USER_DATABASE.get(email)

    if not user:
        # Auto-register demo account for smooth instant testing
        user_id = f"usr-{uuid.uuid4().hex[:6]}"
        token = f"token-{uuid.uuid4().hex[:12]}"
        user_role = ESKI_VARSAYILAN_ROL  # req.role yok sayilir (kural 5)
        user = {
            "id": user_id,
            "name": email.split("@")[0].capitalize(),
            "email": email,
            "password": ck._hash_password(req.password),
            "role": user_role,
            "city": "Hatay",
            "unit": "Sivil Afetzede",
            "token": token
        }
        ck.USER_DATABASE[email] = user
        postgis_engine.save_user_db(user)
    else:
        stored_hash = user.get("password_hash") or user.get("password") or ""
        if not ck._verify_password(req.password, stored_hash):
            raise HTTPException(status_code=401, detail="E-posta veya sifre hatali.")

    user_profile = dict(user)
    user_profile.pop("password", None)
    user_profile.pop("password_hash", None)
    return {
        "status": "success",
        "message": "Giris basarili.",
        "token": user["token"],
        "user": user_profile
    }


@yonlendirici.get("/api/auth/me")
def auth_me(token: Optional[str] = None, _eski: None = Depends(kimlik.eski_uc)):
    if token:
        db_user = postgis_engine.get_user_by_token_db(token)
        if db_user:
            user_profile = dict(db_user)
            user_profile.pop("password_hash", None)
            return {"status": "success", "user": user_profile}

    for email, u in ck.USER_DATABASE.items():
        if u.get("token") == token or token == "demo-token":
            user_profile = dict(u)
            user_profile.pop("password", None)
            return {
                "status": "success",
                "user": user_profile
            }
    return {
        "status": "guest",
        "user": {
            "id": "usr-guest",
            "name": "Afet Saha Ekibi",
            "email": "saha@quakemind.gov.tr",
            "role": "responder",
            "city": "Hatay",
            "unit": "Arama Kurtarma Lideri"
        }
    }
