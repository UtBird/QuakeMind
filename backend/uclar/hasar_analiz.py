"""Uydu hasar analizi: is baslatma (202), durum, gorseller, segmentler, isi haritasi,
goruntu kaynaklari (Wayback, OpenAerialMap).

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
import kimlik

yonlendirici = APIRouter()


@yonlendirici.get("/api/road_damage/wayback_versions")
def road_damage_wayback_versions(_kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    try:
        runtime = ck._get_road_runtime()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail=f"Road Damage runtime yuklenemedi: {ck.road_runtime_error or 'bilinmeyen hata'}",
        )
    get_wayback_versions = runtime["get_wayback_versions"]
    versions = get_wayback_versions()
    versions.sort(key=lambda v: v.get("date", ""), reverse=True)
    return {"versions": versions}


@yonlendirici.get("/api/road_damage/wayback_goruntuler")
def road_damage_wayback_goruntuler(
    latitude: float = Query(..., ge=-85.0, le=85.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radiusKm: float = Query(2.5, gt=0.0, le=20.0),
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Bu konumda Wayback surumlerinin GERCEKTE gosterdigi goruntuler (J-35).

    Surum tarihi cekim tarihi degildir: guncellenmeyen karo eski surumden gelir
    ve goruntu surumden aylar once cekilmis olabilir. Yakinlastirma analizle
    ayni kuraldan (`zoom_for_radius`) secilir; cunku ayni surum farkli
    yakinlastirmada farkli goruntu gosterebilir. Soguk ilk cagri Esri'ye birkac
    istek atar (olculdu 1,4-5,7 sn), sonra onbellekten doner."""
    from apps.road_damage.utils import wayback

    try:
        return wayback.yerel_surumler(latitude, longitude, _zoom_for_radius(radiusKm))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Wayback arsivi okunamadi: {e}")


@yonlendirici.get("/api/road_damage/modeller")
def road_damage_modeller(_kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Analizde seçilebilecek BÜTÜN modeller (modeller/uydu/*.json).

    Her satır kendi künyesini taşır: mimari, eğitim protokolü, sınama IoU,
    ağırlık izi ve karar ayarı. Ağırlığı bulunmayan model `hazir: false` döner
    ve arayüzde seçilemez — uydurma seçenek gösterilmez (kural 1)."""
    from apps.road_damage.utils import model_kunyesi

    liste = []
    for yol in sorted(model_kunyesi.KUNYE_DIZINI.glob("*.json")):
        try:
            k = model_kunyesi.kunye_oku(yol.stem)
        except Exception as e:
            liste.append({"ad": yol.stem, "hazir": False, "hata": str(e)})
            continue
        olcum = k.get("olcum") or {}
        agirlik = model_kunyesi.BACKEND / k["agirlik"]["dosya"]
        liste.append({
            "ad": k["ad"],
            "etiket": k.get("etiket") or k["ad"],
            "mimari": f"{k['mimari']['sinif']} ({k['mimari']['kodlayici']})",
            "sinamaIoU": olcum.get("sinamaIoU"),
            "esik": k["karar"]["esik"],
            "guclendirme": k["karar"]["guclendirme"],
            "sonIsleme": k["karar"]["sonIsleme"],
            "egitimGsdM": k["girdi"]["egitimGsdM"],
            "ileriGecis512Sn": olcum.get("ileriGecis512Sn"),
            "agirlikSha256": k["agirlik"]["sha256"][:12],
            "hazir": agirlik.exists(),
            "etkin": k["ad"] == model_kunyesi.etkin_model_adi(),
        })
    return {"modeller": liste}


@yonlendirici.get("/api/road_damage/model")
def road_damage_model(_kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Etkin uydu modelinin kunye ozeti (J-36): konsol karar ayarlarinin
    varsayilanini buradan alir ve sonucun yaninda hangi modelin kostugunu yazar."""
    from apps.road_damage.utils import model_kunyesi

    if ck.uydu_kunyesi is None:
        raise HTTPException(status_code=503, detail=f"Uydu modeli kunyesi okunamadi: {ck.uydu_kunyesi_hatasi}")
    return model_kunyesi.ozet(ck.uydu_kunyesi)


@yonlendirici.get("/api/road_damage/oam_search")
def road_damage_oam_search(
    latitude: float,
    longitude: float,
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    radiusKm: float = 5.0,
    bboxWest: Optional[float] = None,
    bboxSouth: Optional[float] = None,
    bboxEast: Optional[float] = None,
    bboxNorth: Optional[float] = None,
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    try:
        runtime = ck._get_road_runtime()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail=f"Road Damage runtime yuklenemedi: {ck.road_runtime_error or 'bilinmeyen hata'}",
        )
    search_oam_images = runtime["search_oam_images"]

    if bboxWest is not None and bboxSouth is not None and bboxEast is not None and bboxNorth is not None:
        bbox = (bboxWest, bboxSouth, bboxEast, bboxNorth)
    else:
        bbox = runtime["bbox_from_center"](latitude, longitude, max(0.5, radiusKm))

    images = search_oam_images(bbox, date_start=dateStart, date_end=dateEnd, limit=25)
    return {"images": images}


@yonlendirici.post("/api/road_damage/analyze", status_code=202)
def analyze_road_damage(req: ck.RoadDamageRequest, _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Kicks off a road-damage analysis on the dedicated ProcessPoolExecutor
    and returns immediately with a job id -- the actual Segformer inference
    (CPU-bound, can take minutes) used to run inline here and freeze every
    other endpoint on this single-process server for its whole duration.
    Poll GET /api/road_damage/status/{analysisId} for the result.
    """
    if ck.road_damage_pool is None:
        raise HTTPException(status_code=503, detail="Road Damage worker havuzu henuz hazir degil.")
    if ck._count_queued_road_damage_jobs() >= ck.ROAD_DAMAGE_MAX_QUEUED_JOBS:
        raise HTTPException(
            status_code=503,
            detail="Sistem su anda cok sayida hasar analizi istegini isliyor. Lutfen birkac saniye sonra tekrar deneyin.",
        )

    from apps.road_damage import worker as road_damage_worker

    analysis_id = str(uuid.uuid4())
    req_dict = req.model_dump()
    req_dict["_analysisId"] = analysis_id
    ck._store_road_damage_job(analysis_id, {
        "status": "queued",
        "createdAt": time.time(),
        "progress": 0,
        "progressMessage": "Sirada bekliyor...",
    })

    future = ck.road_damage_pool.submit(road_damage_worker.run_analysis_job, req_dict)
    future.add_done_callback(functools.partial(ck._on_road_damage_job_done, analysis_id))

    return {"analysisId": analysis_id, "status": "queued"}


@yonlendirici.get("/api/road_damage/gorsel/{analysis_id}/{ad}")
def road_damage_gorsel(analysis_id: str, ad: str):
    """Analizin tani gorseli (PNG).

    Gorseller JSON icinde base64 tasinmaz (J-32): istemci hangisini isterse
    onu ayri ve onbelleklenebilir bir istekle alir.
    Ad ornekleri: imageOriginal, imageDamageOverlay, imageSegmentationOverlay,
    imageDamageMask, imageRoadMask, imageIntersection.
    """
    from fastapi.responses import FileResponse

    if not ad.replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="Gecersiz gorsel adi.")
    yol = ck.ANALIZ_GORSEL_DIZINI / analysis_id / f"{ad}.png"
    if not yol.exists():
        raise HTTPException(status_code=404, detail="Gorsel bulunamadi.")
    return FileResponse(
        yol,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@yonlendirici.get("/api/road_damage/status/{analysis_id}")
def get_road_damage_status(
    analysis_id: str,
    gorseller: bool = True,
    segmentler: bool = True,
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Analiz durumu ve bitmisse sonucu.

    Tam sonuc ~17 MB'dir ve bunun ~16 MB'i tani gorselleridir (base64). Yalnizca
    sayilari ve kunyeyi isteyen istemci `?gorseller=0&segmentler=0` ile ~1 KB'lik
    ozet alir; agir geometri ayri ve onbelleklenebilir uctan gelir:
    GET /api/road_damage/segments/{analysisId}. Varsayilan True'dur, boylece
    mevcut web istemcisi etkilenmez.
    """
    with ck.road_damage_jobs_lock:
        job = ck.road_damage_jobs.get(analysis_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Bilinmeyen ya da suresi dolmus analysisId.")
        status = job["status"]
        if status == "error":
            return {"analysisId": analysis_id, "status": "error", "error": job.get("error")}
        if status == "done":
            sonuc = job["result"]
            if gorseller:
                # Gorseller diskte durur; eski istemci base64 bekledigi icin
                # yalnizca istendiginde geri uretilir.
                sonuc = {**sonuc, **ck._gorselleri_base64_oku(job.get("gorseller"))}
            if not segmentler:
                sonuc = {k: v for k, v in sonuc.items() if not k.endswith("RoadSegments")}
            return {"analysisId": analysis_id, "status": "done", "progress": 100, **sonuc}
        return {
            "analysisId": analysis_id,
            "status": status,
            "progress": job.get("progress", 0),
            "progressMessage": job.get("progressMessage"),
        }


@yonlendirici.get("/api/road_damage/heatmap")
def road_damage_heatmap(
    latitude: float,
    longitude: float,
    radiusKm: float = 10.0,
    baslangic: float = None,
    bitis: float = None,
    referans: float = 3.0,
    kaynak: str = None,
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Rapor 2.4.3'teki Gaussian kernel yoğunluk ısı haritası: bir konumdan
    kaç "bildirim" geldiğini gösterir -- Twitter/NLP (geocoded tweet), kamera
    (çatlak/yıkım tespiti), SOS alarmı ve uydu/Segformer'ın tespit ettiği
    tekil hasar noktaları (damage_points, hepsi). Bilinçli olarak
    road_blockages (kapalı yol çizgileri) KULLANILMAZ -- o veri rota
    motorunun (safe_route) ceza katsayısı için ayrı bir katman, buradaki ısı
    haritası salt "bir yerden ne kadar bildirim geldi" sorusuna cevap verir.
    leaflet.heat uyumlu [lat, lon, intensity] listesi döner.
    """
    from apps.road_damage.utils.assembly import bbox_from_center
    from apps.road_damage.utils.heatmap import build_gaussian_heatmap

    bbox = bbox_from_center(latitude, longitude, radiusKm)
    west, south, east, north = bbox

    points: list[tuple[float, float, float]] = []
    by_source: dict[str, int] = {}
    is_postgis = postgis_engine.check_connection()

    if is_postgis:
        damage_rows = postgis_engine.query_damage_points_in_bbox(bbox)
        for row in damage_rows:
            weight = row.get("severity") or 0.5
            points.append((row["lat"], row["lon"], max(0.1, float(weight))))
            source_type = row.get("source_type") or "unknown"
            by_source[source_type] = by_source.get(source_type, 0) + 1
        kaynak_adi = "postgis"
    else:
        # PostGIS yoksa kalici yerel depo (TASIMA_PLANI Faz 1) kullanilir;
        # uydurma veri uretilmez, kayit yoksa isi bos doner.
        from depo import aktif_depo

        # Kanal basina ayri izgara istenebilir (MIMARI 5: her kanalin izgarasi
        # ayri uretilir, agirlikli karisim istemcide yapilir).
        kayitlar = aktif_depo().hasar_listele(
            baslangic=(baslangic / 1000.0) if baslangic else None,
            bitis=(bitis / 1000.0) if bitis else None,
            kutu=(west, south, east, north),
            kaynak=kaynak,
        )
        for kayit in kayitlar:
            agirlik = max(0.1, float(kayit["skor"]) * float(kayit["guven"]))
            points.append((kayit["lat"], kayit["lon"], agirlik))
            by_source[kayit["kaynak"]] = by_source.get(kayit["kaynak"], 0) + 1
        kaynak_adi = "yerel_depo"

    heat_points = build_gaussian_heatmap(
        points, bbox, grid_size=100, bandwidth_km=0.5, referans=referans
    )

    return {
        "points": heat_points,
        "bounds": {"west": west, "south": south, "east": east, "north": north},
        # Olcek MUTLAK: istek basina maksimuma gore normalize edilmez, bu yuzden
        # istemci hangi referansla boyandigini bilmeli (MIMARI 5).
        "olcek": {"tip": "mutlak", "referans": referans},
        "kaynak": kaynak,
        "izgara": {"boyut": 100, "bantGenisligiKm": 0.5},
        "generatedFrom": {
            "totalReports": len(points),
            "bySource": by_source,
            "source": kaynak_adi,
        },
    }


@yonlendirici.get("/api/road_damage/recent")
def recent_road_damage_analyses(minutes: float = 60.0, _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Canli simulasyon icin: son N dakikada tamamlanmis analizleri listeler
    -- frontend'in hangi analysisId'lerin haritada 'canli' gosterilecegini
    ayrica bir mekanizma icat etmeden bilmesini saglar.

    SADECE HAFIF OZET doner. Eskiden burada her analizin TUM safe/blocked
    segment dizileri vardi ve frontend bunu 20 saniyede bir cekip neredeyse
    tamamini atiyordu (yalnizca "kume degisti mi" imzasina bakiyordu).
    Olculdu: tek bolge 39.285 kenar = 2,10 MB JSON; dokuz bolgeli senaryoda
    her turda ~19 MB uretiliyor, serilestiriliyor (~5sn CPU, bu sure boyunca
    GIL tutuldugu icin TUM diger uc noktalar bekliyor), aga veriliyor ve
    tarayicida ayristiriliyordu. Segmentler artik /segments/{analysisId}
    ucundan analiz basina BIR KEZ cekilir -- segmentler uretildikten sonra
    hic degismedigi icin bu tamamen guvenlidir."""
    cutoff = time.time() - minutes * 60
    results = []
    with ck.road_damage_jobs_lock:
        for analysis_id, job in ck.road_damage_jobs.items():
            if job.get("status") != "done" or job.get("createdAt", 0) < cutoff:
                continue
            result = job.get("result", {})
            results.append({
                "analysisId": analysis_id,
                "createdAt": job.get("createdAt"),
                "bounds": result.get("bounds"),
                "safeSegmentCount": len(result.get("safeRoadSegments", [])),
                "blockedSegmentCount": len(result.get("blockedRoadSegments", [])),
            })
    results.sort(key=lambda r: r["createdAt"], reverse=True)
    return {"analyses": results}


@yonlendirici.get("/api/road_damage/segments/{analysis_id}")
def road_damage_segments(analysis_id: str, response: Response, _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Tek bir analizin agir safe/blocked segment dizileri. /recent'ten
    ayrilmistir (bkz. oradaki not): bu veri analiz uretildikten sonra ASLA
    degismez, bu yuzden istemci analiz basina bir kez ceker ve tarayici
    onbellegi de ETag ile calisir."""
    with ck.road_damage_jobs_lock:
        job = ck.road_damage_jobs.get(analysis_id)
        if job is None or job.get("status") != "done":
            raise HTTPException(status_code=404, detail="Analiz bulunamadi veya henuz tamamlanmadi.")
        result = job.get("result", {})
        payload = {
            "analysisId": analysis_id,
            "bounds": result.get("bounds"),
            "safeRoadSegments": result.get("safeRoadSegments", []),
            "blockedRoadSegments": result.get("blockedRoadSegments", []),
        }
    response.headers["Cache-Control"] = "private, max-age=3600"
    response.headers["ETag"] = f'"{analysis_id}"'
    return payload
