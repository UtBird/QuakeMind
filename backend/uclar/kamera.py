"""Kamera tespiti uclari (YOLO, tembel yukleme).

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


@yonlendirici.get("/api/camera/reports")
def list_debris_reports(_eski: None = Depends(kimlik.eski_uc)):
    with ck.debris_lock:
        reports = list(ck.debris_reports)
    return {"reports": reports, "totalReports": len(reports)}


def goruntu_coz(b64: Optional[str]):
    """data URL ya da duz base64 -> OpenCV goruntusu (BGR); okunamazsa None."""
    import base64
    import cv2
    import numpy as np

    if not b64:
        return None
    try:
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        nparr = np.frombuffer(base64.b64decode(b64), np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error decoding camera frame image: {e}")
        return None


def yolo_tespit(img, model_type: str) -> tuple[list, list, bool]:
    """Secilen YOLO modellerini goruntude kosar.

    `model_type`: catlak | bina | hybrid. Donus: (tespitler, calisan modeller,
    kritik var mi). Kamera ucu ve afetzede ihbari (J-51) ayni kodu kullanir.
    """
    model_type = model_type.lower()
    active_models = []
    detections = []
    has_critical = False

    # 1. Run yolo_catlak if requested or hybrid
    catlak_modeli = ck.get_yolo("catlak") if model_type in ["catlak", "crack", "hybrid"] else None
    if catlak_modeli and img is not None:
        active_models.append("catlak.pt (Çatlak Tespiti)")
        results = catlak_modeli(img, verbose=False)
        for r in results:
            for box in r.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = catlak_modeli.names.get(cls_id, "crack")
                if conf >= 0.20:
                    severity = "CRITICAL" if conf > 0.45 else "SAFE"
                    if severity == "CRITICAL":
                        has_critical = True
                    detections.append({
                        "label": f"Duvar/Kolon Çatlağı ({cls_name})",
                        "sinif": cls_name,
                        "confidence": round(conf * 100, 1),
                        "model": "catlak.pt",
                        "box": [round(c, 1) for c in coords],
                        "severity": severity
                    })

    # 2. Run yolo_bina if requested or hybrid
    bina_modeli = ck.get_yolo("bina") if model_type in ["bina", "building", "hybrid"] else None
    if bina_modeli and img is not None:
        active_models.append("bina.pt (Bina Yapısal Hasar)")
        results = bina_modeli(img, verbose=False)
        for r in results:
            for box in r.boxes:
                coords = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = bina_modeli.names.get(cls_id, f"damage_{cls_id}")
                if conf >= 0.20:
                    severity = "CRITICAL" if ("VeryHeavy" in cls_name or "Moderate" in cls_name) else "SAFE"
                    if severity == "CRITICAL":
                        has_critical = True
                    label_tr = "Bina Ağır Hasarlı" if "VeryHeavy" in cls_name else ("Bina Orta Hasarlı" if "Moderate" in cls_name else "Bina Hasarsız / Güvenli")
                    detections.append({
                        "label": f"{label_tr} ({cls_name})",
                        "sinif": cls_name,
                        "confidence": round(conf * 100, 1),
                        "model": "bina.pt",
                        "box": [round(c, 1) for c in coords],
                        "severity": severity
                    })

    return detections, active_models, has_critical


@yonlendirici.post("/api/camera/analyze")
def analyze_camera_frame(req: ck.CameraAnalysisRequest, _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    import base64
    import cv2

    model_type = req.modelType.lower()
    annotated_b64 = None
    img = goruntu_coz(req.imageBase64)
    detections, active_models, has_critical = yolo_tespit(img, model_type)

    # Draw bounding boxes on image if available
    if img is not None and detections:
        for d in detections:
            x1, y1, x2, y2 = [int(v) for v in d["box"]]
            color = (0, 0, 255) if d["severity"] == "CRITICAL" else (0, 255, 0)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            cv2.putText(img, f"{d['label']} %{d['confidence']}", (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        _, buffer = cv2.imencode(".jpg", img)
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")

    # Remove fake mock simulation — always return honest YOLO model output
    if detections:
        if has_critical:
            status = "CRITICAL_EVACUATE"
            advice = "⚠️ TAŞIYICI ELEMANDA DERİN YAPISAL ÇATLAK VEYA AĞIR HASAR TESPİT EDİLDİ! BİNAYI DERHAL BOŞALTIN VE EKİPLERE BİLDİRİN!"
        else:
            status = "SAFE_SURFACE"
            advice = "🟡 YÜZEYSEL ÇATLAK VEYA HASARSIZ YAPISAL DURUM TESPİT EDİLDİ. Taşıyıcı kolon/kirişlerde kritik tehlike görülmüyor."
    else:
        status = "NO_DETECTION"
        advice = "🟢 GÖRÜNTÜDE HERHANGİ BİR ÇATLAK VEYA BİNA HASARI SAPTANMADI. Modeller kamera karesinde riskli bir alan tespit etmedi."

    # Haritaya yalniz HASAR tespiti yazilir (J-50). Eskiden en guclu tespit
    # "Bina Hasarsiz" olsa bile hasar noktasi olarak yaziliyordu: hasarsiz
    # binanin fotografi ekiplerin isi haritasinda hasar gibi gorunuyordu.
    hasar_tespitleri = [d for d in detections if "Hasarsız" not in d["label"]]

    # Best-effort: persist detections as damage_points if the caller sent a
    # location, so the heatmap/route engine can eventually see them too.
    if req.latitude is not None and req.longitude is not None and hasar_tespitleri:
        try:
            catlak_dets = [d for d in hasar_tespitleri if d["model"] == "catlak.pt"]
            bina_dets = [d for d in hasar_tespitleri if d["model"] == "bina.pt"]
            if catlak_dets:
                top = max(catlak_dets, key=lambda d: d["confidence"])
                postgis_engine.insert_damage_point(
                    "crack", req.latitude, req.longitude,
                    severity=top["confidence"] / 100.0, label=top["label"],
                )
            if bina_dets:
                top = max(bina_dets, key=lambda d: d["confidence"])
                postgis_engine.insert_damage_point(
                    "destruction", req.latitude, req.longitude,
                    severity=top["confidence"] / 100.0, label=top["label"],
                )

            # Ortak sozlesmeye de yazilir: isi haritasinin "kamera" kanali ve
            # ozet sayilari buradan beslenir (TASIMA_PLANI Faz 3).
            from depo import aktif_depo

            en_iyi = max(hasar_tespitleri, key=lambda d: d["confidence"])
            aktif_depo().hasar_ekle(
                lon=req.longitude,
                lat=req.latitude,
                skor=min(1.0, en_iyi["confidence"] / 100.0),
                guven=min(1.0, en_iyi["confidence"] / 100.0),
                kaynak="kamera",
                etiket=en_iyi["label"],
            )
        except Exception as e:
            print(f"damage_points insert (camera) hatasi: {e}")

    result = {
        "status": status,
        "modelType": req.modelType,
        "activeModels": active_models or (["catlak.pt (Çatlak Tespiti)"] if model_type=="catlak" else (["bina.pt (Bina Hasar)"] if model_type=="bina" else ["catlak.pt", "bina.pt"])),
        "detections": detections,
        "annotatedImage": annotated_b64,
        "advice": advice,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Tespit varsa VE konum bilgisi geldiyse (telefon GPS'i), harita
    # uzerinde gorunur bir "enkaz/catlak" isareti olarak da sakla --
    # akis diyagramindaki "goruntu analizi -> haritada isaretle" adiminin
    # gercek karsiligi.
    if hasar_tespitleri and req.latitude is not None and req.longitude is not None:
        report = {
            "id": str(uuid.uuid4()),
            "latitude": req.latitude,
            "longitude": req.longitude,
            "status": status,
            "severity": "CRITICAL" if has_critical else "SAFE",
            "detectionCount": len(hasar_tespitleri),
            "topLabel": max(hasar_tespitleri, key=lambda d: d["confidence"])["label"],
            "receivedAt": datetime.now(timezone.utc).isoformat(),
        }
        with ck.debris_lock:
            ck.debris_reports.append(report)
        result["debrisReportId"] = report["id"]

    return result
