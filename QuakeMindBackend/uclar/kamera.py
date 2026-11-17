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


# Bina modelinin siniflari hasar derecesi tasir; catlak modelinin tek sinifi
# ("crack") tasimaz. Catlagin derinligi ya da tasiyici elemanda olup olmadigi
# modelden cikmaz: guven orani siddet degildir (J-165). Eskiden guven %45'i
# gecince "KRITIK, binayi derhal bosaltin" deniyordu.
BINA_SINIFI = {
    "2_VeryHeavyDamage": ("Ağır yapı hasarı", "agir"),
    "1_ModerateDamage": ("Orta yapı hasarı", "orta"),
    "0_NoDamage": ("Hasarsız sınıfı", "yok"),
}


def yolo_tespit(img, model_type: str) -> tuple[list, list, bool]:
    """Secilen YOLO modellerini goruntude kosar.

    `model_type`: catlak | bina | hybrid. Donus: (tespitler, calisan modeller,
    agir/orta yapi hasari var mi). Kamera ucu ve afetzede ihbari (J-51) ayni
    kodu kullanir.

    Her tespitte `siddet`: agir | orta | yok (bina modeli) ya da belirsiz
    (catlak modeli). `severity` eski istemciler icin: CRITICAL yalniz agir ve
    orta yapi hasarinda; catlak UNRATED.
    """
    model_type = model_type.lower()
    active_models = []
    detections = []
    has_critical = False

    catlak_modeli = ck.get_yolo("catlak") if model_type in ["catlak", "crack", "hybrid"] else None
    if catlak_modeli and img is not None:
        active_models.append("catlak.pt (Çatlak Tespiti)")
        for r in catlak_modeli(img, verbose=False):
            for box in r.boxes:
                conf = float(box.conf[0].cpu().numpy())
                if conf < 0.20:
                    continue
                cls_name = catlak_modeli.names.get(int(box.cls[0].cpu().numpy()), "crack")
                detections.append({
                    "label": "Çatlak",
                    "sinif": cls_name,
                    "confidence": round(conf * 100, 1),
                    "model": "catlak.pt",
                    "box": [round(c, 1) for c in box.xyxy[0].cpu().numpy().tolist()],
                    "siddet": "belirsiz",
                    "severity": "UNRATED",
                })

    bina_modeli = ck.get_yolo("bina") if model_type in ["bina", "building", "hybrid"] else None
    if bina_modeli and img is not None:
        active_models.append("bina.pt (Bina Yapısal Hasar)")
        for r in bina_modeli(img, verbose=False):
            for box in r.boxes:
                conf = float(box.conf[0].cpu().numpy())
                if conf < 0.20:
                    continue
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = bina_modeli.names.get(cls_id, f"damage_{cls_id}")
                ad, siddet = BINA_SINIFI.get(cls_name, (cls_name, "belirsiz"))
                kritik = siddet in ("agir", "orta")
                has_critical = has_critical or kritik
                detections.append({
                    "label": ad,
                    "sinif": cls_name,
                    "confidence": round(conf * 100, 1),
                    "model": "bina.pt",
                    "box": [round(c, 1) for c in box.xyxy[0].cpu().numpy().tolist()],
                    "siddet": siddet,
                    "severity": "CRITICAL" if kritik else "SAFE",
                })

    # Guvene gore sirali: konsoldaki numara, resimdeki numarayla ayni.
    detections.sort(key=lambda d: -d["confidence"])
    return detections, active_models, has_critical


def _ascii_etiket(i: int, d: dict) -> str:
    """OpenCV'nin yazi tipi Turkce harf cizemez ("Çatlak" -> "??atlak"). Resme
    numara + model sinifi yazilir; Turkce ad konsoldaki listededir."""
    return f"{i} {d['sinif']} {round(d['confidence'])}%"


def kamera_tavsiyesi(detections: list) -> tuple[str, str]:
    """(durum, tavsiye). Model fotografi siniflandirir; binanin guvenligine
    karar vermez. Metin bunu soyler, bosaltma emri vermez."""
    siddetler = {d["siddet"] for d in detections}
    if "agir" in siddetler:
        return (
            "CRITICAL_EVACUATE",
            "Ağır yapı hasarı sınıfı bulundu. Model fotoğrafı sınıflandırır, binanın güvenli olup "
            "olmadığına karar vermez: binaya girilmeden yerinde uzman değerlendirmesi gerekir.",
        )
    if "orta" in siddetler:
        return (
            "CRITICAL_EVACUATE",
            "Orta yapı hasarı sınıfı bulundu. Yerinde uzman değerlendirmesi gerekir; model "
            "binanın güvenli olup olmadığına karar vermez.",
        )
    if "belirsiz" in siddetler:
        return (
            "CRACK_FOUND",
            "Çatlak bulundu. Çatlak modeli derinliği ve taşıyıcı elemanda (kolon, kiriş) olup "
            "olmadığını ayırt etmez; önemi yerinde değerlendirilmelidir.",
        )
    if detections:
        return (
            "SAFE_SURFACE",
            "Yalnız hasarsız sınıfı bulundu. Bu, binanın güvenli olduğu anlamına gelmez; "
            "model yalnız fotoğrafta görüneni sınıflandırır.",
        )
    return (
        "NO_DETECTION",
        "Seçilen modeller bu fotoğrafta çatlak ya da yapı hasarı bulmadı. Fotoğrafın açısı, "
        "ışığı ve uzaklığı sonucu etkiler.",
    )


@yonlendirici.post("/api/camera/analyze")
def analyze_camera_frame(req: ck.CameraAnalysisRequest, kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    import base64
    import cv2

    import islem_kaydi

    model_type = req.modelType.lower()
    annotated_b64 = None
    img = goruntu_coz(req.imageBase64)
    boy, en = (img.shape[:2] if img is not None else (None, None))
    if img is None:
        raise HTTPException(status_code=422, detail="Fotoğraf çözülemedi; JPEG ya da PNG gönder.")
    t0 = time.perf_counter()
    detections, active_models, has_critical = yolo_tespit(img, model_type)
    sure_ms = round((time.perf_counter() - t0) * 1000)
    if not active_models:
        # Model dosyasi yoksa "tespit yok" demek yalan olurdu (CLAUDE.md 1).
        raise HTTPException(status_code=503, detail="Seçilen model sunucuda yüklü değil.")

    # Eski istemciler (eski web, Flutter) icin isaretli resim. Konsol kutulari
    # kendi cizer; numaralar listedeki sirayla ayni.
    if img is not None and detections:
        for i, d in enumerate(detections, start=1):
            x1, y1, x2, y2 = [int(v) for v in d["box"]]
            color = (0, 0, 255) if d["severity"] == "CRITICAL" else (0, 165, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            cv2.putText(img, _ascii_etiket(i, d), (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        _, buffer = cv2.imencode(".jpg", img)
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")

    status, advice = kamera_tavsiyesi(detections)

    # Haritaya yalniz HASAR tespiti yazilir (J-50). Eskiden en guclu tespit
    # "Bina Hasarsiz" olsa bile hasar noktasi olarak yaziliyordu: hasarsiz
    # binanin fotografi ekiplerin isi haritasinda hasar gibi gorunuyordu.
    hasar_tespitleri = [d for d in detections if d["siddet"] != "yok"]

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
        # Yalniz gercekten kosan modeller (J-167 S-3).
        "activeModels": active_models,
        "detections": detections,
        "annotatedImage": annotated_b64,
        "advice": advice,
        "imageWidth": en,
        "imageHeight": boy,
        "sureMs": sure_ms,
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

    # Islem kaydi (J-165): fotograf saklanmaz, yalniz sonucun ozeti.
    sayilar: dict[str, int] = {}
    for d in detections:
        sayilar[d["label"]] = sayilar.get(d["label"], 0) + 1
    en_yuksek = max((d["confidence"] for d in detections), default=None)
    parca = ", ".join(f"{n} {ad.lower()}" for ad, n in sayilar.items()) or "tespit yok"
    islem_kaydi.kaydet(
        kul,
        "kamera_analizi",
        f"Kamera analizi: {parca}"
        + (f" (en yüksek güven {islem_kaydi.yuzde(en_yuksek)})" if en_yuksek is not None else ""),
        ayrinti={
            "model": model_type,
            "modeller": active_models,
            "tespitSayisi": len(detections),
            "siniflar": sayilar,
            "enYuksekGuven": en_yuksek,
            "durum": status,
            "en": en,
            "boy": boy,
            "sureMs": sure_ms,
            "konumVar": req.latitude is not None and req.longitude is not None,
            "tespitler": [
                {"sinif": d["sinif"], "guven": d["confidence"], "kutu": d["box"], "siddet": d["siddet"]}
                for d in detections[:50]
            ],
        },
    )
    return result
