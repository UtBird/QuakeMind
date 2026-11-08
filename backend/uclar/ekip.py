"""Ekip gorev (claim) uclari.

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

# Bu uclar yetki denetimi olmadan calisiyordu: adresi bilen herkes bir hedefi
# 'kilitleyebiliyor' ya da baskasinin kilidini birakabiliyordu (J-119). Yalniz
# eski web ve benchmark betikleri kullaniyor; yeni konsol kullanmiyor. Diger eski
# uclar gibi varsayilan olarak KAPALIDIR (kimlik.eski_uc, J-53); gerekirse
# QUAKEMIND_ESKI_UCLAR=1 ile acilir.


@yonlendirici.post("/api/team/claim")
def claim_team_target(req: ck.TeamClaimRequest, _eski: None = Depends(kimlik.eski_uc)):
    with ck.team_claims_lock:
        existing = ck.team_claims.get(req.targetId)
        if existing is not None and existing["status"] == "active" and existing["teamId"] != req.teamId:
            raise HTTPException(
                status_code=409,
                detail=f"Bu hedefe zaten {existing['teamId']} ekibi mudahale ediyor.",
            )
        claim = {
            "targetId": req.targetId,
            "teamId": req.teamId,
            "targetType": req.targetType,
            "lat": req.lat,
            "lon": req.lon,
            "status": "active",
            "claimedAt": datetime.now(timezone.utc).isoformat(),
        }
        ck.team_claims[req.targetId] = claim
    return claim


@yonlendirici.get("/api/team/claims")
def list_team_claims(_eski: None = Depends(kimlik.eski_uc)):
    with ck.team_claims_lock:
        claims = list(ck.team_claims.values())
    return {"claims": claims, "totalClaims": len(claims)}


@yonlendirici.post("/api/team/claim/{target_id}/route")
def attach_team_route(target_id: str, req: ck.TeamRouteAttachRequest,
                      _eski: None = Depends(kimlik.eski_uc)):
    """Bir claim'e gercek GNN rotasini ekler -- canli simulasyonda frontend
    bu rota + startedAt zaman damgasini kullanarak ekip pozisyonunu istemci
    tarafinda zaman-bazli interpolasyonla hesaplar (ayrica bir 'pozisyon
    guncelle' donguisune gerek kalmadan)."""
    with ck.team_claims_lock:
        claim = ck.team_claims.get(target_id)
        if claim is None:
            raise HTTPException(status_code=404, detail="Bu hedef icin aktif bir claim bulunamadi.")
        claim["routeCoords"] = req.routeCoords
        claim["distanceMeters"] = req.distanceMeters
        claim["assumedSpeedKmh"] = req.assumedSpeedKmh
        claim["startedAt"] = datetime.now(timezone.utc).isoformat()
        claim["naiveRouteCoords"] = req.naiveRouteCoords
        claim["naiveDistanceMeters"] = req.naiveDistanceMeters
        claim["naiveReachable"] = req.naiveReachable
    return claim


@yonlendirici.post("/api/team/claim/{target_id}/release")
def release_team_claim(target_id: str, _eski: None = Depends(kimlik.eski_uc)):
    with ck.team_claims_lock:
        claim = ck.team_claims.get(target_id)
        if claim is None:
            raise HTTPException(status_code=404, detail="Bu hedef icin aktif bir claim bulunamadi.")
        claim["status"] = "completed"
        claim["releasedAt"] = datetime.now(timezone.utc).isoformat()
    return claim
