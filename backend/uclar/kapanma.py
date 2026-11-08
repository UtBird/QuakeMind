"""Kapanma uretimi ve karsilastirma uclari: kapanma simulasyonu, maskeden ve
EMSR'den kapanma, naif ajan ve referans karsilastirmalari (arastirma/benchmark).

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
from fastapi import APIRouter

yonlendirici = APIRouter()


@yonlendirici.post("/api/road_damage/simulate_closures")
def simulate_road_closures(req: ck.SimulateClosuresRequest):
    """Gercek senaryo kurgusu icin: CANLI SegFormer/uydu goruntusu
    calistirmadan, gercek bir OSM yol grafigi uzerinde rastgele yol
    kapanmalari atar. `/analyze`'in basarili sonuc seklinin BIREBIR ayni
    doner (analysisId + safe/blockedRoadSegments + bounds) -- boylece
    /route, /recent ve frontend hicbir fark gozetmeden kullanir. Senkron
    calisir (worker pool YOK) cunku SegFormer inference yok, sadece graf
    edinme var (fetch_osm_road_graph zaten cache-first, hizli)."""
    from apps.road_damage.utils.network import simulate_random_closures

    bbox = ck._request_bbox(req)
    # network_type='walk' (varsayilan 'drive' yerine): CARTO taban haritasi
    # yaya sokaklarini/ara yollari da ciziyor, 'drive' grafigi bunlari hic
    # icermedigi icin haritada "bos" (renksiz) kalan bir suru yol goruluyordu.
    # 'walk' arac + yaya gecebilen TUM yollari kapsadigi icin (arama-kurtarma
    # ekipleri zaten hem araclarla hem yaya ilerliyor), haritadaki neredeyse
    # her sokak acik/kapali olarak renklendirilir.
    G, safe_G, safe_edges, blocked_edges, error = simulate_random_closures(
        bbox, closure_ratio=req.closureRatio, seed=req.seed, network_type='walk',
    )
    if G is None:
        raise HTTPException(status_code=503, detail=f"Yol grafigi alinamadi: {error}")

    analysis_id = str(uuid.uuid4())
    bounds_dict = {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]}
    result = {
        "bounds": bounds_dict,
        "safeRoadSegments": _serialize_segments(safe_edges),
        "blockedRoadSegments": _serialize_segments(blocked_edges),
        "simulated": True,
        # Kapanmalarin KAYNAGI her ciktida acikca yazilir: bu uc rastgele
        # (rng.sample) kapanma uretir; model tabanli olan
        # /closures_from_mask ile karistirilmasin (bkz. J-12, J-23).
        "closureSource": "synthetic",
        "closedEdgeCount": len({(u, v, k) for u, v, k, _line in blocked_edges}),
        "edgeCount": G.number_of_edges(),
    }

    # G (kapatmasiz TAM graf) + kapali kenar (u,v,key) kumesi de saklanir --
    # /naive_compare bu ikisini KENDI SURECIMIZDE (baska bir Python surecinde
    # simulate_random_closures'i AYNI parametrelerle TEKRAR cagirmak yerine)
    # kullanarak "biz olmasaydik" karsilastirmasini calistirir. Surecler
    # arasi rastgele-ornekleme tutarsizligi (bkz. network.py'deki
    # simulate_naive_agent docstring'i) boylece tamamen ortadan kalkar.
    closed_edge_keys = {(u, v, k) for u, v, k, _line in blocked_edges}
    ck._store_road_damage_session(analysis_id, {
        "safe_G": safe_G, "G": G, "closedEdgeKeys": closed_edge_keys, "bounds": bounds_dict,
    })
    ck._store_road_damage_job(analysis_id, {
        "status": "done", "result": result, "progress": 100,
        "progressMessage": "Simulasyon tamamlandi.",
        "createdAt": time.time(), "finishedAt": time.time(),
    })
    return {"analysisId": analysis_id, "status": "done", **result}


@yonlendirici.post("/api/road_damage/closures_from_mask")
def closures_from_mask(req: ck.ClosuresFromMaskRequest):
    """MODEL TABANLI kapanmalar: Colab'da SegFormer ile uretilmis hazir bir
    hasar maskesinden, canli /analyze ile AYNI kuralla (r_h yaricapi) yol
    kapanmalari cikarir. Yanit /simulate_closures ile birebir ayni sekildedir;
    oturum da ayni alanlari (G, safe_G, closedEdgeKeys) tasidigi icin /route,
    /naive_compare, /recent ve harita hicbir fark gozetmeden calisir.

    /simulate_closures'tan farki: hangi yolun kapali oldugunu rastgele
    ornekleme DEGIL, modelin deprem sonrasi goruntude gordugu hasar belirler."""
    import networkx as _nx

    from apps.road_damage.utils.network import closures_from_damage_mask, fetch_osm_road_graph

    meta, damage, valid = ck._load_model_mask(req.maskId)
    bbox = ck._request_bbox(req)
    G, error = fetch_osm_road_graph(bbox, network_type=req.networkType)
    if G is None:
        raise HTTPException(status_code=503, detail=f"Yol grafigi alinamadi: {error}")

    mb = meta["bounds"]
    mask_bounds = (mb["west"], mb["south"], mb["east"], mb["north"])
    safe_edges, blocked_edges, closed_keys, coverage = closures_from_damage_mask(
        G, mask_bounds, damage, valid, req.blockageRadiusM,
    )
    # Kopya DEGIL gorunum -- /simulate_closures ile ayni desen (bkz. J-02, J-17).
    safe_G = _nx.restricted_view(G, [], closed_keys)

    analysis_id = str(uuid.uuid4())
    bounds_dict = {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]}
    mask_summary = {
        k: meta.get(k) for k in (
            "zoneId", "zoom", "metresPerPixel", "scenes", "model", "createdAt",
            "threshold", "damageBooster", "useImagenetNorm", "postProcessLevel",
            "damagePixelFraction", "validPixelFraction", "inferenceDevice",
        )
    }
    result = {
        "bounds": bounds_dict,
        "safeRoadSegments": _serialize_segments(safe_edges),
        "blockedRoadSegments": _serialize_segments(blocked_edges),
        "simulated": False,
        "closureSource": "model",
        "maskId": req.maskId,
        "blockageRadiusM": req.blockageRadiusM,
        "closedEdgeCount": len(closed_keys),
        "edgeCount": G.number_of_edges(),
        "coverage": coverage,
        "maskMeta": mask_summary,
    }
    ck._store_road_damage_session(analysis_id, {
        "safe_G": safe_G, "G": G, "closedEdgeKeys": closed_keys, "bounds": bounds_dict,
        "closureSource": "model",
    })
    ck._store_road_damage_job(analysis_id, {
        "status": "done", "result": result, "progress": 100,
        "progressMessage": "Model tabanli kapanmalar hazir.",
        "createdAt": time.time(), "finishedAt": time.time(),
    })
    return {"analysisId": analysis_id, "status": "done", **result}


@yonlendirici.post("/api/road_damage/closures_from_emsr")
def closures_from_emsr(req: ck.ClosuresFromEmsrRequest):
    """YER GERCEGI kapanmalar: Copernicus EMSR648 Grading'in hasarli yol
    cizgilerini OSM grafina esleyerek kapanma cikarir. Yanit ve oturum
    /simulate_closures ve /closures_from_mask ile ayni sekildedir; boylece
    ayni afetzede/ekip/rota/naif akisi uc farkli kapanma kaynagiyla
    (sentetik / model / yer gercegi) birebir karsilastirilabilir.

    EMSR'in incelemedigi (AOI disi) yollar hakkinda yer gercegi yoktur ve
    acik kabul edilir; bunlarin orani `stats.edgesInsideObservedFraction`
    ile raporlanir."""
    import networkx as _nx

    from apps.road_damage.utils.network import closures_from_lines, fetch_osm_road_graph
    from benchmark.copernicus_ground_truth import (
        ROAD_GRADE_RULES, aoi_rings, damaged_road_lines, road_grade_counts,
    )

    if req.gradeRule not in ROAD_GRADE_RULES:
        raise HTTPException(status_code=422, detail=f"gradeRule {sorted(ROAD_GRADE_RULES)} olmali.")
    if not (0 < req.bufferM <= 50) or not (0 < req.minOverlap <= 1):
        raise HTTPException(status_code=422, detail="bufferM (0,50] ve minOverlap (0,1] araliginda olmali.")
    bbox = ck._request_bbox(req)
    try:
        lines = damaged_road_lines(req.emsrPackage, req.gradeRule, bbox)
        rings = aoi_rings(req.emsrPackage)
        grades = road_grade_counts(req.emsrPackage, bbox)
    except ValueError:
        raise HTTPException(status_code=422, detail="Gecersiz emsrPackage.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"EMSR paketi bulunamadi: {req.emsrPackage}")

    G, error = fetch_osm_road_graph(bbox, network_type=req.networkType)
    if G is None:
        raise HTTPException(status_code=503, detail=f"Yol grafigi alinamadi: {error}")

    safe_edges, blocked_edges, closed_keys, stats = closures_from_lines(
        G, lines, buffer_m=req.bufferM, min_overlap=req.minOverlap, observed_polygons=rings,
    )
    safe_G = _nx.restricted_view(G, [], closed_keys)

    analysis_id = str(uuid.uuid4())
    bounds_dict = {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]}
    result = {
        "bounds": bounds_dict,
        "safeRoadSegments": _serialize_segments(safe_edges),
        "blockedRoadSegments": _serialize_segments(blocked_edges),
        "simulated": False,
        "closureSource": "emsr648",
        "emsrPackage": req.emsrPackage,
        "gradeRule": req.gradeRule,
        "closedEdgeCount": len(closed_keys),
        "edgeCount": G.number_of_edges(),
        "emsrRoadGradesInBbox": grades,
        "stats": stats,
    }
    ck._store_road_damage_session(analysis_id, {
        "safe_G": safe_G, "G": G, "closedEdgeKeys": closed_keys, "bounds": bounds_dict,
        "closureSource": "emsr648",
    })
    ck._store_road_damage_job(analysis_id, {
        "status": "done", "result": result, "progress": 100,
        "progressMessage": "EMSR648 yer gercegi kapanmalari hazir.",
        "createdAt": time.time(), "finishedAt": time.time(),
    })
    return {"analysisId": analysis_id, "status": "done", **result}


@yonlendirici.post("/api/road_damage/naive_compare")
def naive_compare(req: ck.NaiveCompareRequest):
    """'Biz tespit edip soylemeseydik ne kadar kaybederdiniz' karsilastirmasi
    -- SADECE simulate_closures ile olusturulmus (yani gercek bir G + kapali
    kenar kumesi tasiyan) session'lar icin calisir. Naif ajan simulasyonu
    BILEREK bu SURECTE (baska bir Python sureci -- benchmark script'i --
    DEGIL) calistirilir: /route'un fiilen kullandigi G/kapanma kumesiyle
    BIREBIR ayni nesneleri kullanir, boylece 'ayni kapanmayi biliyor/bilmiyor
    olma' matematiksel garantisi (naive >= bizim motor) hicbir surec-arasi
    farkla bozulmaz."""
    session = ck._get_road_damage_session(req.analysisId)
    if session is None or "G" not in session or "closedEdgeKeys" not in session:
        raise HTTPException(
            status_code=422,
            detail="Bu analiz oturumu naif-ajan karsilastirmasi icin gerekli veriyi tasimiyor "
                   "(sadece /simulate_closures ile olusturulan oturumlar desteklenir).",
        )

    from apps.road_damage.utils.network import simulate_naive_agent

    G = session["G"]
    real_closed_edges = set()
    for u, v, k in session["closedEdgeKeys"]:
        real_closed_edges.add((u, v, k))
        real_closed_edges.add((v, u, k))

    result = simulate_naive_agent(G, real_closed_edges, req.startLat, req.startLon, req.endLat, req.endLon)
    if result is None:
        return {"reachable": False, "distanceMeters": None, "discoveries": None, "routeCoords": None}
    return {
        "reachable": True,
        "distanceMeters": result["distanceMeters"],
        "discoveries": result["discoveries"],
        "routeCoords": [[float(lat), float(lon)] for lat, lon in result["routeCoords"]],
    }


@yonlendirici.post("/api/road_damage/reference_compare")
def reference_compare(req: ck.ReferenceCompareRequest):
    """Makalenin ara karsilastirma referanslari (Bolum 3.8): R1 gorus mesafeli
    ajan, R2 bilgi paylasan filo. naive_compare ile ayni gerekceyle ayni surecte,
    oturumdaki AYNI G ve kapanma kumesiyle calisir. Gorevler bir bolgenin tum
    atamalaridir -- R2'de bilgi bu gorevler arasinda paylasilir."""
    session = ck._get_road_damage_session(req.analysisId)
    if session is None or "G" not in session or "closedEdgeKeys" not in session:
        raise HTTPException(
            status_code=422,
            detail="Bu analiz oturumu referans karsilastirmasi icin gerekli veriyi tasimiyor.",
        )
    if not 1 <= len(req.tasks) <= 50:
        raise HTTPException(status_code=422, detail="Gorev sayisi 1-50 arasinda olmali.")
    if not 1 <= len(req.variants) <= 8:
        raise HTTPException(status_code=422, detail="Varyant sayisi 1-8 arasinda olmali.")
    if not 1 <= len(req.uTurnPenaltyMinValues) <= 8 or any(
            not 0.0 <= tu <= 120.0 for tu in req.uTurnPenaltyMinValues):
        raise HTTPException(status_code=422, detail="uTurnPenaltyMinValues 1-8 deger, her biri 0-120 dk.")
    if not 0.0 < req.speedKmh <= 200.0:
        raise HTTPException(status_code=422, detail="speedKmh 0-200 arasinda olmali.")
    names = [v.name for v in req.variants]
    if len(set(names)) != len(names) or not all(ck._REFERENCE_NAME_RE.fullmatch(n) for n in names):
        raise HTTPException(status_code=422, detail="Varyant adlari benzersiz ve [A-Za-z0-9_-] olmali.")
    if any(not 0.0 <= v.sightM <= 1000.0 for v in req.variants):
        raise HTTPException(status_code=422, detail="sightM 0-1000 m arasinda olmali.")

    from apps.road_damage.utils.network import simulate_reference_fleet

    G = session["G"]
    real_closed_edges = set()
    for u, v, k in session["closedEdgeKeys"]:
        real_closed_edges.add((u, v, k))
        real_closed_edges.add((v, u, k))
    tasks = [t.model_dump() for t in req.tasks]

    variants = []
    for var in req.variants:
        by_tu = {}
        t0 = time.perf_counter()
        if var.share:
            for tu in req.uTurnPenaltyMinValues:
                by_tu[f"{tu:g}"] = simulate_reference_fleet(
                    G, real_closed_edges, tasks, sight_m=var.sightM, share=True,
                    speed_kmh=req.speedKmh, u_turn_penalty_min=tu,
                    simultaneous_known=var.simultaneousKnown)
        else:
            once = simulate_reference_fleet(
                G, real_closed_edges, tasks, sight_m=var.sightM, share=False,
                speed_kmh=req.speedKmh, u_turn_penalty_min=req.uTurnPenaltyMinValues[0])
            by_tu = {f"{tu:g}": once for tu in req.uTurnPenaltyMinValues}
        variants.append({
            "name": var.name, "sightM": var.sightM, "share": var.share,
            "simultaneousKnown": var.simultaneousKnown,
            "tuDependent": var.share,
            "elapsedSec": round(time.perf_counter() - t0, 2),
            "byUTurnPenalty": {
                tu: [dict(r, id=task["id"], reachable=True) if r else {"id": task["id"], "reachable": False}
                     for task, r in zip(tasks, results)]
                for tu, results in by_tu.items()
            },
        })
    return {"analysisId": req.analysisId, "taskCount": len(tasks), "variants": variants}
