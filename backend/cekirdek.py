"""QuakeMind API cekirdegi: paylasilan durum, yardimcilar, veri modelleri ve
uygulama yasam dongusu (lifespan).

TASIMA_PLANI.md Faz 5: uclar bu dosyadan `uclar/` altindaki router modullerine
tasindi. Router'lar paylasilan duruma `ck.<isim>` ile erisir: boylece lifespan
ya da tembel yukleyiciler bir degiskeni sonradan degistirdiginde uclar guncel
degeri gorur (`from cekirdek import x` degeri import aninda dondururdu).
"""
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
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
from typing import Literal, Optional
from threading import Event, Lock, Thread
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError as FutureTimeoutError
import asyncio
import functools
import multiprocessing

# Windows' ProcessPoolExecutor (spawn) re-imports this module's top-level code
# inside every pool worker process, even when the worker's target function
# lives elsewhere. Empirically (verified via a diagnostic print on this
# machine): the initial `python fastapi_app.py` launch is named "MainProcess",
# uvicorn's own reload subprocess (the one that actually serves HTTP -- reload
# uses `multiprocessing` internally too) is named "SpawnProcess-1", and a
# ProcessPoolExecutor worker spawned from *that* process is named
# "SpawnProcess-1:1" (parent-name:index) -- i.e. pool workers are the only
# processes whose name contains ":". Guarding on that (not on "MainProcess",
# which only matches the launcher and would wrongly also skip loading in the
# real reload-managed server process) lets the eager, heavy model loads below
# skip themselves in pool workers without touching the real server process.
_IS_APP_PROCESS = ":" not in multiprocessing.current_process().name

BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR / "apps"
NLP_ROOT = APPS_DIR / "disaster_nlp"
ROAD_ROOT = APPS_DIR / "road_damage"

import canli_yayin
from depo import depo_ac
RISK_ROOT = APPS_DIR / "earthquake_risk"
CAMERA_ROOT = APPS_DIR / "camera_detection"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.postgis_manager import postgis_engine

def add_project_site_packages(project_root):
    for env_name in [".venv", "venv"]:
        env_path = project_root / env_name
        if not env_path.exists():
            continue
        for site_path in env_path.glob("lib/python*/site-packages"):
            site.addsitedir(str(site_path))

for project_root in [NLP_ROOT, ROAD_ROOT, RISK_ROOT, CAMERA_ROOT]:
    add_project_site_packages(project_root)

from apps.road_damage.utils.serialization import (
    compact_segment_coords as _compact_segment_coords,
    serialize_segments as _serialize_segments,
    haversine_m as _haversine_m,
)
from apps.road_damage.utils.imaging import (
    image_array_to_b64 as _image_array_to_b64,
    build_damage_overlay as _build_damage_overlay,
    build_segmentation_overlay as _build_segmentation_overlay,
)
from apps.road_damage.utils.tiling import zoom_for_radius as _zoom_for_radius

@contextmanager
def temporary_sys_path(*paths):
    old_sys_path = list(sys.path)
    normalized_paths = [str(path) for path in paths if path]
    for path in reversed(normalized_paths):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path[:] = old_sys_path

@contextmanager
def temporary_cwd(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)

def clear_module_cache(prefixes):
    for module_name in list(sys.modules.keys()):
        if any(module_name == prefix or module_name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(module_name, None)

# Initialize engines
nlp_pipeline = None
risk_engine = None
road_runtime = None
road_runtime_error = None
road_runtime_load_attempted = False
road_runtime_lock = Lock()
# Etkin uydu modelinin kunyesi (lifespan'de okunur, J-36).
uydu_kunyesi = None
uydu_kunyesi_hatasi = None

def _get_nlp_pipeline():
    global nlp_pipeline
    if nlp_pipeline is None:
        try:
            clear_module_cache(["src"])
            with temporary_sys_path(NLP_ROOT), temporary_cwd(NLP_ROOT):
                from src.pipeline import DisasterPipeline
                nlp_pipeline = DisasterPipeline()
            print("NLP Pipeline loaded lazily.", flush=True)
        except Exception as e:
            print(f"Failed to load NLP: {e}", flush=True)
    return nlp_pipeline

yolo_catlak = None
yolo_bina = None


def get_yolo(hangi: str):
    """YOLO modelleri TEMBEL yuklenir (MIMARI 4).

    Onceden ikisi de acilista API surecine yukleniyordu; kamera ucu hic
    kullanilmasa bile bellek isgal ediyorlardi. Artik ilk kamera isteginde
    yuklenir ve surecte kalir.
    """
    global yolo_catlak, yolo_bina
    if hangi == "catlak":
        if yolo_catlak is None:
            yol = CAMERA_ROOT / "models" / "catlak.pt"
            if yol.exists():
                from ultralytics import YOLO

                yolo_catlak = YOLO(str(yol.resolve()))
                print("YOLO Catlak modeli yuklendi (tembel).", flush=True)
        return yolo_catlak
    if hangi == "bina":
        if yolo_bina is None:
            yol = CAMERA_ROOT / "models" / "bina.pt"
            if yol.exists():
                from ultralytics import YOLO

                yolo_bina = YOLO(str(yol.resolve()))
                print("YOLO Bina modeli yuklendi (tembel).", flush=True)
        return yolo_bina
    return None

if _IS_APP_PROCESS:
    try:
        clear_module_cache(["risk_engine"])
        with temporary_sys_path(RISK_ROOT), temporary_cwd(RISK_ROOT):
            risk_module = importlib.import_module("risk_engine")
            RISK_CSV = RISK_ROOT / "data" / "query.csv"
            risk_engine = risk_module.EarthquakeRiskEngine(csv_path=str(RISK_CSV.resolve()))
        print("Risk Engine loaded.", flush=True)
    except Exception as e:
        print(f"Failed to load Risk Engine: {e}", flush=True)

    try:
        catlak_path = CAMERA_ROOT / "models" / "catlak.pt"
        bina_path = CAMERA_ROOT / "models" / "bina.pt"
        print(
            "YOLO modelleri tembel yuklenecek: "
            f"catlak={'var' if catlak_path.exists() else 'yok'}, "
            f"bina={'var' if bina_path.exists() else 'yok'}",
            flush=True,
        )
    except Exception as e:
        print(f"Failed to load YOLO Camera Models: {e}", flush=True)


def _load_road_runtime():
    # DIKKAT: SegFormer'i BU surece yuklemeyin. Gercek cikarim
    # apps/road_damage/worker.py icinde, AYRI bir surecte, o surecin KENDI
    # model kopyasiyla kosuyor (_init_worker -> model_kunyesi.model_yukle). Burada bir
    # zamanlar `load_simple_model` cagriliyor ve sonuc `model`/`device`
    # anahtarlarina konuyordu, ama bu anahtarlar bu dosyada HIC okunmuyordu --
    # olculdu: +618 MB RSS ve +5,3sn acilis, okunmayan bir sozluk girdisi
    # icin (ayrica `inference` modulunun kendisi transformers/SegFormer
    # yiginini da suruklerdi). `run_inference` ve
    # `analyze_road_network_graph` de ayni sekilde yalnizca worker'da
    # kullaniliyor. Streamlit tarafi (main.py, apps/road_damage/app.py)
    # bunlari kendi kopyalarinda yuklemeye devam eder -- oraya dokunulmadi.
    from apps.road_damage.utils.fetcher import (
        fetch_satellite_area,
        get_osm_roads_overpass,
        get_wayback_versions,
        search_oam_images,
    )
    from apps.road_damage.utils.network import calculate_route
    from apps.road_damage.utils.assembly import (
        bbox_from_center,
        fetch_osm_safety_areas,
        find_nearest_assembly,
        shortest_walk_route,
    )
    from apps.road_damage.utils.local_osm import (
        has_local_roads_dataset,
        has_local_safety_dataset,
        load_local_safety_areas,
        shortest_route_from_local_roads,
    )

    return {
        "fetch_satellite_area": fetch_satellite_area,
        "get_osm_roads_overpass": get_osm_roads_overpass,
        "get_wayback_versions": get_wayback_versions,
        "search_oam_images": search_oam_images,
        "calculate_route": calculate_route,
        "bbox_from_center": bbox_from_center,
        "fetch_osm_safety_areas": fetch_osm_safety_areas,
        "find_nearest_assembly": find_nearest_assembly,
        "shortest_walk_route": shortest_walk_route,
        "has_local_roads_dataset": has_local_roads_dataset,
        "has_local_safety_dataset": has_local_safety_dataset,
        "load_local_safety_areas": load_local_safety_areas,
        "shortest_route_from_local_roads": shortest_route_from_local_roads,
    }


def _get_road_runtime():
    global road_runtime, road_runtime_error, road_runtime_load_attempted
    if road_runtime is not None:
        return road_runtime
    if road_runtime_load_attempted:
        # Already tried and failed once this process lifetime -- don't retry the
        # (slow, osmnx/geopandas-importing) load on every single request. A server
        # restart is required to retry, matching the singleton-with-cached-failure
        # pattern used for the other lazily-loaded engines above.
        raise RuntimeError(road_runtime_error or "Road Damage runtime yuklenemedi.")

    with road_runtime_lock:
        if road_runtime is not None:
            return road_runtime
        if road_runtime_load_attempted:
            raise RuntimeError(road_runtime_error or "Road Damage runtime yuklenemedi.")
        road_runtime_load_attempted = True
        try:
            road_runtime = _load_road_runtime()
            road_runtime_error = None
            print("Road Damage runtime loaded.", flush=True)
        except Exception as e:
            road_runtime = None
            road_runtime_error = str(e)
            print(f"Failed to load Road Damage runtime: {e}", flush=True)
            raise
    return road_runtime


if _IS_APP_PROCESS:
    try:
        _get_road_runtime()
    except Exception:
        pass

# In-memory SOS alert store. Intentionally not persisted: alerts reset whenever
# the server restarts, matching the PoC requirement of session-only storage.
sos_alerts: list[dict] = []
sos_lock = Lock()

# In-memory debris/catlak report store -- POST /api/camera/analyze bir tespit
# + konum aldiginda buraya ekler; harita bunu ayri bir "debris" katmani
# olarak gosterir (akis diyagramindaki "goruntu analizi -> haritada isaretle").
debris_reports: "list[dict]" = []
debris_lock = Lock()

# In-memory NLP-cikarimli konum deposu -- POST /api/nlp/analyze serbest
# metinden gercek bir konum (NER + il/ilce sozlugu + Nominatim geocoding)
# cikarabildiginde buraya eklenir; harita bunu SOS pin'inden (afetzedenin
# kendi GPS'i) AYRI bir katman olarak gosterir -- boylece NLP'nin metinden
# konum cikarma yeteneginin kendisi gorunur/dogrulanabilir olur.
nlp_locations: "list[dict]" = []
nlp_locations_lock = Lock()

# In-memory team target-claim store: prevents two teams from being dispatched to
# the same target ("yigilma onleme" in the field-team flow). Keyed by targetId.
team_claims: "dict[str, dict]" = {}
team_claims_lock = Lock()

# In-memory road-damage analysis session store: keeps the routable "safe roads"
# graph around so a later /route call can compute a real path without re-running
# the whole satellite fetch + inference pipeline.
#
# Tahliye UC olcute birden bakar. Eskiden yalnizca sayi sinirlamasi vardi
# (20 oturum) ve bu iki soruna yol aciyordu:
#   1. Bellek tavani gorunmezdi. Olculdu: tek bir 3 km bolge grafi bellekte
#      130-137 MB (20 643 dugum / 49 666 kenar), yani 20 oturum ~2,7 GB
#      edebiliyordu -- 16,9 GB'lik makinede kabul edilemez.
#   2. Bellek HIC geri gelmiyordu: zaman asimi yoktu, bir graf ancak 20 yenisi
#      onu tasirana kadar tutuluyordu. Dokuz bolgeli bir senaryo kosumundan
#      sonra ~600 MB sunucu kapatilana kadar bosa duruyordu.
road_damage_sessions: "dict[str, dict]" = {}
road_damage_sessions_order: list = []
road_damage_sessions_lock = Lock()
ROAD_DAMAGE_SESSION_LIMIT = int(os.environ.get("QUAKEMIND_SESSION_LIMIT", "20"))
ROAD_DAMAGE_SESSION_TTL_SEC = float(os.environ.get("QUAKEMIND_SESSION_TTL_SEC", str(30 * 60)))
ROAD_DAMAGE_SESSION_BUDGET_MB = float(os.environ.get("QUAKEMIND_SESSION_BUDGET_MB", "1024"))

# Graf basina bellek tahmini icin OLCULMUS sabit. Bes gercek bolge grafinda
# (2 535 - 70 309 eleman) RSS artisi elemani basina 792 - 1 855 bayt cikti;
# oran graf buyudukce artiyor, bu yuzden butce hesabinda ORTALAMA degil UST
# deger kullanilir -- kucuk graflarda fazladan temkinli olmak, buyuklerde
# bellegi olduğundan az saymaktan iyidir.
_GRAPH_BYTES_PER_ELEMENT = 1900

# Referans: dokuz bolgeli Senaryo v2'nin TAMAMI ~97 300 dugum + 222 300 kenar
# = ~319 600 eleman ~ 607 MB. Yani 1024 MB'lik varsayilan butce tam bir senaryo
# kosumunu ~1,7x paylayla tasir; senaryo bu degisiklikten etkilenmez.


def _estimate_session_bytes(data) -> int:
    """Oturumun tuttugu grafin kaba bellek maliyeti.

    `simulate_closures` oturumlari hem `G` (gercek graf) hem `safe_G`
    (nx.restricted_view -- AYNI depolamayi paylasan salt-okunur gorunum)
    tutar; `/analyze` oturumlari da (J-34'ten beri) tam grafi `roadGraph`
    ve onun gorunumu `safe_G`'yi tutar. Ikisini de toplamak gorunumu iki kez
    saymak olurdu, bu yuzden en buyuk tek graf esas alinir. `closureProb`
    yalniz p > 0 kenarlari tasir (olculdu: kenarlarin ~%1,6'si), ihmal
    edilir."""
    biggest = 0
    for key in ("G", "safe_G", "roadGraph"):
        graph = data.get(key)
        if graph is None:
            continue
        try:
            biggest = max(biggest, graph.number_of_nodes() + graph.number_of_edges())
        except Exception:
            continue
    return biggest * _GRAPH_BYTES_PER_ELEMENT


def _evict_road_damage_sessions_locked(protect=None):
    """road_damage_sessions_lock TUTULUYORKEN cagrilir. Sirasiyla: suresi
    dolanlar, sayi sinirini asanlar, bellek butcesini asanlar.

    `protect`, hicbir kosulda atilmayacak analiz kimligi (yeni saklanan
    oturum). Onsuz, tek basina butceden buyuk bir graf saklandigi anda
    tahliye edilir ve /route hemen 422 dondururdu."""
    now = time.time()
    dropped = []

    def _drop(analysis_id):
        road_damage_sessions.pop(analysis_id, None)
        if analysis_id in road_damage_sessions_order:
            road_damage_sessions_order.remove(analysis_id)
        dropped.append(analysis_id)

    if ROAD_DAMAGE_SESSION_TTL_SEC > 0:
        for analysis_id in list(road_damage_sessions_order):
            if analysis_id == protect:
                continue
            stored_at = road_damage_sessions.get(analysis_id, {}).get("storedAt", now)
            if now - stored_at > ROAD_DAMAGE_SESSION_TTL_SEC:
                _drop(analysis_id)

    while len(road_damage_sessions_order) > ROAD_DAMAGE_SESSION_LIMIT:
        oldest = next((a for a in road_damage_sessions_order if a != protect), None)
        if oldest is None:
            break
        _drop(oldest)

    budget_bytes = ROAD_DAMAGE_SESSION_BUDGET_MB * 1e6
    def _total():
        return sum(s.get("estimatedBytes", 0) for s in road_damage_sessions.values())
    while _total() > budget_bytes:
        # Butce ASLA son oturumu dusurmez. Tek basina butceden buyuk bir graf
        # (cok genis yaricapli bir bolge) aksi halde saklandiktan hemen sonra,
        # ILK OKUMADA tahliye edilir ve /route 422 dondururdu -- `protect`
        # yalnizca saklama anini koruyor, okuma yolunu korumuyordu.
        if len(road_damage_sessions_order) <= 1:
            break
        oldest = next((a for a in road_damage_sessions_order if a != protect), None)
        if oldest is None:
            break
        _drop(oldest)

    if dropped:
        print(
            f"Road damage sessions evicted: {len(dropped)} "
            f"(kalan {len(road_damage_sessions)}, ~{_total()/1e6:.0f} MB)",
            flush=True,
        )
    return dropped


def _store_road_damage_session(analysis_id, data):
    with road_damage_sessions_lock:
        data["storedAt"] = time.time()
        data["estimatedBytes"] = _estimate_session_bytes(data)
        # Ayni kimlik ikinci kez saklanirsa sira listesinde MUKERRER girdi
        # olusur ve tahliye, hala gecerli bir oturumun kimligini dusurebilir.
        if analysis_id in road_damage_sessions_order:
            road_damage_sessions_order.remove(analysis_id)
        road_damage_sessions[analysis_id] = data
        road_damage_sessions_order.append(analysis_id)
        _evict_road_damage_sessions_locked(protect=analysis_id)


def _get_road_damage_session(analysis_id):
    """Oturumu okur ve bu firsatla suresi dolmuslari temizler. Suresi dolmus
    bir oturum None doner -- cagiranlarin zaten verdigi "oturum bulunamadi
    veya suresi doldu" hatasi bu durumu dogru anlatiyor."""
    with road_damage_sessions_lock:
        _evict_road_damage_sessions_locked()
        return road_damage_sessions.get(analysis_id)


def _sweep_road_damage_sessions(stop_event, interval_sec=60.0):
    """Arka plan temizleyicisi. Tahliyeyi SADECE saklama/okuma anlarina
    baglamak yetmiyordu: bir senaryo kosumu bittikten sonra baska istek
    gelmezse ~600 MB, sunucu kapanana kadar bosa duruyordu."""
    while not stop_event.wait(interval_sec):
        try:
            with road_damage_sessions_lock:
                _evict_road_damage_sessions_locked()
        except Exception:
            pass


# In-memory road-damage *job* store (separate from road_damage_sessions
# above, which only holds the routable graph for /route). Tracks the
# lifecycle of an /analyze call now that it runs on a background
# ProcessPoolExecutor worker instead of inline in the request handler:
# queued -> done (result attached) or error (message attached). Bounded
# FIFO eviction, same pattern as the session store.
road_damage_jobs: "dict[str, dict]" = {}
road_damage_jobs_order: list = []
road_damage_jobs_lock = Lock()
ROAD_DAMAGE_JOB_LIMIT = 20

# Tani gorselleri bellekte degil diskte durur: is basina ~16 MB base64, 20 islik
# tavan ~320 MB ediyordu (olculdu, J-32). Sonuc sozlugunde yalnizca dosya adlari
# kalir; eski web base64 isteyince dosyadan okunup kodlanir.
ANALIZ_GORSEL_DIZINI = Path(__file__).resolve().parent / "veri" / "analiz_gorselleri"
# Soft cap on concurrently *queued* jobs -- pool.submit() itself never
# blocks (unlike the old semaphore-gated thread-pool route), so this is
# just cheap backpressure against a client hammering /analyze.
ROAD_DAMAGE_MAX_QUEUED_JOBS = 5

road_damage_pool: "ProcessPoolExecutor | None" = None
# Worker -> main-process progress channel. A plain multiprocessing.Queue
# (not a Manager dict) on purpose: a Manager would spin up its own server
# process, and on Windows spawn that process re-imports this module and
# would redundantly reload every heavy model -- exactly what _IS_APP_PROCESS
# exists to prevent. A Queue needs no extra process, and handing it to the
# pool via initargs is the one path multiprocessing allows a Queue to cross
# a process boundary.
road_damage_progress_queue = None
road_damage_progress_thread = None
# Oturum temizleyicisi (bkz. _sweep_road_damage_sessions)
road_damage_sweeper_stop = None
road_damage_sweeper_thread = None


def _store_road_damage_job(analysis_id, data):
    with road_damage_jobs_lock:
        road_damage_jobs[analysis_id] = data
        road_damage_jobs_order.append(analysis_id)
        while len(road_damage_jobs_order) > ROAD_DAMAGE_JOB_LIMIT:
            oldest = road_damage_jobs_order.pop(0)
            road_damage_jobs.pop(oldest, None)
            _gorselleri_sil(oldest)


def _count_queued_road_damage_jobs():
    with road_damage_jobs_lock:
        return sum(1 for job in road_damage_jobs.values() if job.get("status") == "queued")


def _on_road_damage_job_done(analysis_id, future):
    """Runs in the main process (on the pool's management thread) once a
    submitted job finishes. Must only touch road_damage_jobs under its lock,
    matching the thread-safety pattern already used for sos_lock /
    road_damage_sessions_lock elsewhere in this file.
    """
    with road_damage_jobs_lock:
        job = road_damage_jobs.get(analysis_id)
        if job is None:
            return  # evicted from the bounded FIFO while still in flight
        exc = future.exception()
        if exc is not None:
            job["status"] = "error"
            job["error"] = str(exc)
            canli_yayin.yayinla(
                "is-durumu",
                isId=analysis_id,
                isTipi="hasar-analizi",
                durum="hata",
                hata=str(exc),
            )
        else:
            result = future.result()
            road_graph = result.pop("roadGraph", None)
            closed_edge_keys = result.pop("closedEdgeKeys", None)
            closure_prob = result.pop("closureProb", None)
            if road_graph is not None:
                import networkx as nx

                # Anahtarlar bilerek "G"/"closedEdgeKeys" DEGIL: o ikisi
                # /naive_compare ve /reference_compare'in "yer gercegi olan
                # oturum" isaretidir; burada kapanmalar modelin tahminidir.
                _store_road_damage_session(analysis_id, {
                    "safe_G": nx.restricted_view(road_graph, [], closed_edge_keys or set()),
                    "roadGraph": road_graph,
                    "closureProb": closure_prob,
                    "bounds": result.get("bounds"),
                })
            job["status"] = "done"
            job["gorseller"] = _gorselleri_diske_al(analysis_id, result)
            job["result"] = result
            _kapanmalari_depoya_yaz(analysis_id, result)
            job["progress"] = 100
            job["progressMessage"] = "Analiz tamamlandi."
            # Istemci "bitti" mesajini alinca sonucu TEK bir istekle ceker;
            # yoklama yok (MIMARI 6).
            canli_yayin.yayinla(
                "is-durumu",
                isId=analysis_id,
                isTipi="hasar-analizi",
                durum="bitti",
                ilerleme=100,
                mesaj="Analiz tamamlandi.",
            )
            canli_yayin.yayinla(
                "yeni-analiz",
                kaynak="uydu",
                isId=analysis_id,
                bolge=result.get("city"),
            )
        job["finishedAt"] = time.time()


def _gorselleri_diske_al(analysis_id, result):
    """Sonuctaki base64 gorselleri diske yazar ve sozlukten cikarir.

    Donus: {ad: dosya_yolu}. Eski istemciler base64 isteyince
    `_gorselleri_base64_oku` ile geri uretilir.
    """
    import base64

    adlar = [k for k in list(result.keys()) if k.endswith("B64")]
    if not adlar:
        return {}

    dizin = ANALIZ_GORSEL_DIZINI / analysis_id
    try:
        dizin.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"gorsel dizini acilamadi: {e}", flush=True)
        return {}

    yazilanlar = {}
    for ad in adlar:
        deger = result.pop(ad, None)
        if not deger:
            continue
        try:
            ham = deger.split(",", 1)[1] if deger.startswith("data:") else deger
            yol = dizin / f"{ad[:-3]}.png"
            yol.write_bytes(base64.b64decode(ham))
            yazilanlar[ad] = str(yol)
        except Exception as e:
            print(f"gorsel yazilamadi ({ad}): {e}", flush=True)
    return yazilanlar


def _gorselleri_base64_oku(gorseller):
    """Eski istemciler icin base64 alanlarini diskten geri uretir."""
    import base64

    sonuc = {}
    for ad, yol in (gorseller or {}).items():
        try:
            sonuc[ad] = base64.b64encode(Path(yol).read_bytes()).decode("ascii")
        except Exception:
            continue
    return sonuc


def _gorselleri_sil(analysis_id):
    import shutil

    try:
        shutil.rmtree(ANALIZ_GORSEL_DIZINI / analysis_id, ignore_errors=True)
    except Exception:
        pass


def _kapanmalari_depoya_yaz(analysis_id, result):
    """Analizden cikan kapali yol segmentlerini kalici depoya yazar.

    Boylece kapanmalar tek analizin sonucunda kalmaz; zaman penceresiyle
    suzulebilir ve ozet sayilarina girer (TASIMA_PLANI.md Faz 3).
    Not: segmentler [enlem, boylam] sirasiyla gelir.
    """
    segmentler = result.get("blockedRoadSegments") or []
    if not segmentler:
        return
    try:
        from depo import aktif_depo

        depo = aktif_depo()
        for yol in segmentler:
            if not yol:
                continue
            orta = yol[len(yol) // 2]
            depo.kapanma_ekle(
                lon=float(orta[1]),
                lat=float(orta[0]),
                derece=3,
                kaynak="uydu",
                analiz_id=analysis_id,
                # Parçanın kendi çizgisi de saklanır (J-58): harita kapanmayı
                # nokta olarak değil kırmızı çizgi olarak gösterir.
                cizgi=[[float(n[0]), float(n[1])] for n in yol],
            )
    except Exception as e:
        print(f"kapanmalari depoya yazma hatasi: {e}", flush=True)


def _drain_road_damage_progress(queue):
    """Main-process daemon thread: turns worker progress pings into job-store
    updates. Exits on the None sentinel pushed at shutdown.
    """
    while True:
        try:
            item = queue.get()
        except (EOFError, OSError):
            return
        if item is None:
            return
        try:
            analysis_id = item.get("analysisId")
            with road_damage_jobs_lock:
                job = road_damage_jobs.get(analysis_id)
                # Only advance a still-running job -- a late ping must never
                # drag a finished job's progress back below 100.
                if job is not None and job.get("status") == "queued":
                    job["progress"] = item.get("percent")
                    job["progressMessage"] = item.get("message")
                    yayinlanacak = True
                else:
                    yayinlanacak = False
            if yayinlanacak:
                canli_yayin.yayinla(
                    "is-durumu",
                    isId=analysis_id,
                    isTipi="hasar-analizi",
                    durum="calisiyor",
                    ilerleme=item.get("percent"),
                    mesaj=item.get("message"),
                )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    global road_damage_pool, road_damage_progress_queue, road_damage_progress_thread
    global road_damage_sweeper_stop, road_damage_sweeper_thread
    from apps.road_damage import worker as road_damage_worker

    # Canli akis: yayinci is parcaciklari olaylari bu donguye tasir.
    canli_yayin.dongu_ayarla(asyncio.get_running_loop())

    # Kalici depo (TASIMA_PLANI.md Faz 1). PostgreSQL yoksa yerel SQLite dosyasi;
    # kullanicilar, SOS cagrilari ve ekipler yeniden baslatmada kaybolmaz.
    depo = depo_ac()
    print(f"Depo hazir: {depo.yol} ({depo.kullanici_sayisi()} kullanici)", flush=True)

    # PostGIS yoklamasi 2 sn zaman asimina dusebiliyor; ilk kullanici bunu
    # beklemesin diye acilista ayri bir is parcaciginda yapilir ve sonuc
    # onbellege girer (postgis_manager.check_connection).
    Thread(target=lambda: postgis_engine.check_connection(zorla=True), daemon=True).start()

    # Etkin uydu modeli kunyeden okunur (J-36): mimari, agirlik izi ve karar
    # ayarlari tek dosyada. Okunamazsa isci kurulamaz; hata /api/road_damage/model
    # ucunda ve acilis gunlugunde yazar.
    global uydu_kunyesi, uydu_kunyesi_hatasi
    from apps.road_damage.utils import model_kunyesi

    try:
        uydu_kunyesi = model_kunyesi.kunye_oku()
        uydu_kunyesi_hatasi = None
        print(f"Uydu modeli: {uydu_kunyesi['ad']} ({uydu_kunyesi['agirlik']['sha256'][:12]})", flush=True)
    except Exception as e:
        uydu_kunyesi = None
        uydu_kunyesi_hatasi = str(e)
        print(f"Uydu modeli kunyesi okunamadi: {e}", flush=True)
    pool_size = int(os.environ.get("QUAKEMIND_ROAD_POOL_SIZE", "1"))
    road_damage_progress_queue = multiprocessing.Queue()
    road_damage_progress_thread = Thread(
        target=_drain_road_damage_progress,
        args=(road_damage_progress_queue,),
        daemon=True,
    )
    road_damage_progress_thread.start()

    road_damage_sweeper_stop = Event()
    road_damage_sweeper_thread = Thread(
        target=_sweep_road_damage_sessions,
        args=(road_damage_sweeper_stop,),
        daemon=True,
    )
    road_damage_sweeper_thread.start()

    road_damage_pool = ProcessPoolExecutor(
        max_workers=pool_size,
        initializer=road_damage_worker._init_worker,
        initargs=(uydu_kunyesi, road_damage_progress_queue),
    )
    # Pay the one-time "cold worker spawn" cost (Windows process creation +
    # module import, measured ~10-15s on this machine) now, during startup,
    # instead of during the first real user's analysis request.
    warm_up = road_damage_pool.submit(road_damage_worker._warm_up)
    try:
        warm_up.result(timeout=120)
        print(f"Road Damage pool warmed up ({pool_size} worker(s)).", flush=True)
    except Exception as e:
        print(f"Road Damage pool warm-up failed (will still lazy-init on first job): {e}", flush=True)

    yield

    if road_damage_sweeper_stop is not None:
        road_damage_sweeper_stop.set()
    road_damage_pool.shutdown(wait=False, cancel_futures=True)
    try:
        road_damage_progress_queue.put_nowait(None)
    except Exception:
        pass





class NLPRequest(BaseModel):
    text: str


class SOSAlertRequest(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    message: Optional[str] = None
    userId: Optional[str] = None
    # Akis diyagramindaki "pil durumu" ve "haberlesme durumu" (mesh/BLE
    # fallback) alanlari -- gercek bir donanim sensoru/BLE yiginimiz olmadigi
    # icin (bkz. AKIS_DIYAGRAM_KOD_ESLESTIRME_RAPORU.md) temsili/rastgele
    # deger olarak orkestratorden (benchmark/rich_simulation.py) veya mobil
    # istemciden gelir -- ama gercek SOS pipeline'indan gecer ve saklanir,
    # kurgusal bir katman degil.
    batteryPercent: Optional[int] = None
    commsStatus: Optional[str] = None  # "online" | "mesh" | "offline"
    # Cihazin OTONOM davranis durumu (akis diyagramindaki "pil < %20 ->
    # tasarruf modu / akustik siren dongusu / GPS polling seyreltme" dali).
    # batteryPercent/commsStatus ile ayni statude: temsili deger, gercek SOS
    # pipeline'indan gecer, saklanir, haritada ve ihbar listesinde gosterilir.
    powerMode: Optional[str] = None       # "normal" | "tasarruf"
    sirenActive: Optional[bool] = None    # 100 dB araliklarla siren + mikrofon dinleme
    gpsPollingSec: Optional[int] = None   # tasarruf modunda seyreltilir
    # 2. seviye fallback'te (sebeke yok, BLE mesh) gonderilen hafif JSON
    # paketinin GERCEKTEN olculmus byte uzunlugu -- tahmin degil, orkestrator
    # paketi serilestirip len() ile olcup gonderiyor.
    payloadBytes: Optional[int] = None
    # Ihbarin hangi uretim kanalindan geldigi -- haritadaki pin standardini
    # (turuncu YOLO / sari NLP / kirmizi flasor SOS) suren alan.
    channel: Optional[str] = None         # "yolo" | "nlp" | "sos"


class TeamClaimRequest(BaseModel):
    teamId: str
    targetId: str
    targetType: str  # "sos" | "report" | "evacuation"
    lat: float
    lon: float


class TeamRouteAttachRequest(BaseModel):
    routeCoords: list
    distanceMeters: float
    assumedSpeedKmh: float = 15.0
    # "Biz olmasaydik nereden giderdi" karsilastirmasi -- naif ajanin FIILEN
    # yurudugu rota + mesafesi, haritada bizim rotamizla yan yana cizilip
    # kazanci gorsel olarak da kanitlamak icin (rich_simulation.py bunu
    # /api/road_damage/naive_compare'den alip buraya iliştirir).
    naiveRouteCoords: list | None = None
    naiveDistanceMeters: float | None = None
    naiveReachable: bool | None = None

class RiskRequest(BaseModel):
    city: str
    manualLatitude: float | None = None
    manualLongitude: float | None = None
    refreshData: bool = False

class RoadDamageRequest(BaseModel):
    city: str
    latitude: float
    longitude: float
    source: str = "google"
    # Karar ayarlari: gonderilmezse etkin modelin kunyesinden gelir (J-36).
    # Bugunku modelin kunyesi eski sabitleri (3,5 / 0,40 / True / 2) tasir.
    damageBooster: Optional[float] = None
    threshold: Optional[float] = None
    useImagenetNorm: Optional[bool] = None
    postProcessLevel: Optional[int] = None
    bboxWest: Optional[float] = None
    bboxSouth: Optional[float] = None
    bboxEast: Optional[float] = None
    bboxNorth: Optional[float] = None
    oamPreferredTitle: Optional[str] = None
    # Hangi model koşsun (modeller/uydu/<ad>.json). Verilmezse havuzun etkin
    # modeli kullanılır — eski davranış değişmez.
    modelAdi: Optional[str] = None
    # Deprem ÖNCESİ görüntü de çekilsin mi (öncesi / sonrası / etiketli üçlüsü).
    oncesiGoruntusu: bool = True
    waybackId: Optional[str] = None
    oamTileUrl: Optional[str] = None
    networkType: Optional[str] = None
    # Half-width of the analysis area in km when no explicit bbox is given.
    # Previously the backend fell back to a tiny ~2-tile patch (a few hundred
    # meters) whenever the caller (mobile app) sent no bbox at all -- this
    # makes sure a real, requested-size area is always analyzed instead.
    radiusKm: float = 2.5
    # r_h -- sert kapatma yaricapi (metre). Bir yol, bu mesafe icinde
    # hasar tespit edilirse kapali sayilir. 0 = uygulamanin HER ZAMANKI kurali
    # (hasar, cizilmis yol maskesinin ustunde olmali).
    # VARSAYILAN 0: web uygulamasi bu alani gondermiyor; yaricap kurali
    # varsayilan yapildiginda uygulamanin yol hasari sonuclari kullaniciya
    # sorulmadan degismisti, ustelik drone sahnelerinde EMSR648'e karsi
    # olculen dogrulugu dusuk cikti (bkz. J-26). Yaricap kurali yalnizca
    # acikca istenirse (arastirma/duyarlilik) kullanilir.
    blockageRadiusM: float = 0.0


class SimulateClosuresRequest(BaseModel):
    latitude: float
    longitude: float
    radiusKm: float = 1.0
    closureRatio: float = 0.15
    seed: Optional[int] = None
    # Istege bagli ACIK sinir kutusu. Dordu de verilirse merkez+yaricaptan
    # turetilen kare yerine bu kutu kullanilir (drone sahneleri: graf ve
    # maske sahnenin kendi kapsama kutusu uzerinde, bkz. scenario_dataset_drone).
    bboxWest: Optional[float] = None
    bboxSouth: Optional[float] = None
    bboxEast: Optional[float] = None
    bboxNorth: Optional[float] = None


class RoadDamageRouteRequest(BaseModel):
    analysisId: str
    startLat: float
    startLon: float
    endLat: float
    endLon: float
    # Planlama maliyeti (J-34 bayragi). "hard" varsayilandir ve bugunku
    # kuraldir: model kapali dedigi kenar silinir. "soft": kenar silinmez,
    # maliyeti uzunluk x (1 + softLambda x p) olur; p, kenar boyunca
    # orneklerin hasarli piksele dusen orani. Kazanc iddia edilemez (bolgeler
    # arasi sinama %13,6 [-0,4; 22,2] ve %14,1 [0,8; 27,9]: biri sifiri
    # iceriyor, obururun alt siniri sifira cok yakin), bu yuzden varsayilan
    # degismez.
    costModel: Literal["hard", "soft"] = "hard"
    # 8: Kahramanmaras'ta secilip Hatay'da sinanan deger. Hatay'da secilen 16
    # lambda izgarasinin kenarina dayandigi icin daha az guvenilir.
    softLambda: float = Field(8.0, ge=0.0, le=64.0)








# Turkey-wide fault line overlay: independent of the selected city (unlike the
# per-prediction `faultLines`, which risk_bridge filters to ~180km of one city).
# Sourced from the real GEM active-faults dataset (not the 6-segment approximation
# in risk_engine.FAULT_LINES) and cached in memory since the source file is ~10MB.
_turkey_fault_lines_cache = None
_turkey_fault_lines_lock = Lock()
TURKEY_BBOX = (25.0, 34.0, 45.5, 43.0)  # west, south, east, north


def _iter_geometry_lines(geometry):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if geom_type == "LineString":
        line = [(c[0], c[1]) for c in coords if len(c) >= 2]
        if len(line) >= 2:
            yield line
    elif geom_type == "MultiLineString":
        for segment in coords:
            line = [(c[0], c[1]) for c in segment if len(c) >= 2]
            if len(line) >= 2:
                yield line


def _load_turkey_fault_lines():
    import json

    west, south, east, north = TURKEY_BBOX
    path = RISK_ROOT / "data" / "fault_maps" / "fay_haritası" / "gem_active_faults_harmonized.geojson"
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as handle:
        geojson_data = json.load(handle)

    lines = []
    for feature in geojson_data.get("features", []):
        geometry = feature.get("geometry") or {}
        name = (feature.get("properties") or {}).get("name") or "Fay Hatti"
        for line in _iter_geometry_lines(geometry):
            if not any(west <= lon <= east and south <= lat <= north for lon, lat in line):
                continue
            lines.append({
                "name": name,
                "points": [{"latitude": lat, "longitude": lon} for lon, lat in line],
            })
    return lines


def _get_turkey_fault_lines():
    global _turkey_fault_lines_cache
    if _turkey_fault_lines_cache is not None:
        return _turkey_fault_lines_cache
    with _turkey_fault_lines_lock:
        if _turkey_fault_lines_cache is None:
            _turkey_fault_lines_cache = _load_turkey_fault_lines()
    return _turkey_fault_lines_cache
























# Colab/GPU'da uretilen hasar maskeleri (benchmark/colab/make_model_masks.py).
# Kullanicinin bilgisayarinda GPU yok; tam bolge (3 km) z=18 cikarimi CPU'da
# bolge basina saatler suruyor (olculdu: 0,3 km yaricapta bile 306,8 sn). Bu
# yuzden cikarim Colab T4'te bir kez yapilir, maskeler dosya olarak buraya
# konur ve senaryo bu HAZIR maskelerle yerelde hizla kosar.
MODEL_MASK_ROOT = BASE_DIR / "benchmark" / "data" / "model_masks"
_MASK_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")


class ClosuresFromMaskRequest(BaseModel):
    maskId: str                    # MODEL_MASK_ROOT altindaki klasor adi (orn. "H-Z1")
    latitude: float
    longitude: float
    radiusKm: float = 3.0
    blockageRadiusM: float = 25.0  # r_h -- bkz. J-19 / J-22
    networkType: str = "walk"      # /simulate_closures ile ayni graf (onbellek anahtari)
    # Istege bagli ACIK sinir kutusu. Dordu de verilirse merkez+yaricaptan
    # turetilen kare yerine bu kutu kullanilir (drone sahneleri: graf ve
    # maske sahnenin kendi kapsama kutusu uzerinde, bkz. scenario_dataset_drone).
    bboxWest: Optional[float] = None
    bboxSouth: Optional[float] = None
    bboxEast: Optional[float] = None
    bboxNorth: Optional[float] = None


def _request_bbox(req):
    """Istek acik bir kutu tasiyorsa onu, yoksa merkez+yaricap karesini dondurur."""
    from apps.road_damage.utils.assembly import bbox_from_center

    explicit = (req.bboxWest, req.bboxSouth, req.bboxEast, req.bboxNorth)
    if all(v is not None for v in explicit):
        if not (explicit[0] < explicit[2] and explicit[1] < explicit[3]):
            raise HTTPException(status_code=422, detail="Gecersiz bbox (bati<dogu, guney<kuzey olmali).")
        return explicit
    return bbox_from_center(req.latitude, req.longitude, req.radiusKm)


def _load_model_mask(mask_id: str):
    """maskId'yi YALNIZCA MODEL_MASK_ROOT altinda cozer -- istemciden gelen
    bir degerle dosya sisteminde gezinilmesine izin verilmez."""
    import json as _json

    import numpy as _np
    from PIL import Image as _Image

    if not _MASK_ID_RE.fullmatch(mask_id or ""):
        raise HTTPException(status_code=422, detail="Gecersiz maskId.")
    mask_dir = (MODEL_MASK_ROOT / mask_id).resolve()
    if MODEL_MASK_ROOT.resolve() not in mask_dir.parents:
        raise HTTPException(status_code=422, detail="Gecersiz maskId.")
    meta_path = mask_dir / "meta.json"
    damage_path = mask_dir / "damage_mask.png"
    if not meta_path.exists() or not damage_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(f"'{mask_id}' icin hazir hasar maskesi yok. Once Colab defterini "
                    "(benchmark/colab/) calistirip ciktisini "
                    f"benchmark/data/model_masks/{mask_id}/ altina koyun."),
        )
    meta = _json.loads(meta_path.read_text(encoding="utf-8"))
    damage = (_np.array(_Image.open(damage_path).convert("L")) > 0).astype(_np.uint8)
    valid = None
    valid_path = mask_dir / "valid_mask.png"
    if valid_path.exists():
        valid = (_np.array(_Image.open(valid_path).convert("L")) > 0).astype(_np.uint8)
    if (damage.shape[1], damage.shape[0]) != (meta.get("width"), meta.get("height")):
        raise HTTPException(status_code=422, detail=f"'{mask_id}': maske boyutu meta.json ile uyusmuyor.")
    return meta, damage, valid




class ClosuresFromEmsrRequest(BaseModel):
    emsrPackage: str               # benchmark/data/copernicus/ altindaki EMSR648 Grading paketi
    latitude: float
    longitude: float
    radiusKm: float = 3.0
    gradeRule: str = "loose"       # strict | medium | loose (bkz. copernicus_ground_truth.ROAD_GRADE_RULES)
    bufferM: float = 8.0           # EMSR cizgisi <-> OSM kenari eslestirme tamponu
    minOverlap: float = 0.5        # kenarin tampon icinde kalmasi gereken orani
    networkType: str = "walk"
    bboxWest: Optional[float] = None
    bboxSouth: Optional[float] = None
    bboxEast: Optional[float] = None
    bboxNorth: Optional[float] = None




class NaiveCompareRequest(BaseModel):
    analysisId: str
    startLat: float
    startLon: float
    endLat: float
    endLon: float




class ReferenceTask(BaseModel):
    id: str
    startLat: float
    startLon: float
    endLat: float
    endLon: float


class ReferenceVariant(BaseModel):
    name: str
    sightM: float = 0.0
    share: bool = False
    # Paylasimda ayni anda ogrenilen kapanma bilinir mi (kafile kurali); bkz.
    # simulate_reference_fleet.
    simultaneousKnown: bool = True


class ReferenceCompareRequest(BaseModel):
    analysisId: str
    tasks: list[ReferenceTask]
    variants: list[ReferenceVariant]
    speedKmh: float = 15.0
    # Paylasimli (R2) varyantlarda sonuc t_u'ya bagli (kim once ogrenir), bu yuzden
    # her deger icin ayri simule edilir; paylasimsizlarda tek sonuc tum degerlere yazilir.
    uTurnPenaltyMinValues: list[float] = [20.0]


_REFERENCE_NAME_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")




class SafeRouteRequest(BaseModel):
    startLat: float
    startLon: float
    destLat: float
    destLon: float
    radiusKm: float = 3.0




def _fetch_osrm_street_route(u_lat: float, u_lon: float, d_lat: float, d_lon: float):
    import requests
    url = f"http://router.project-osrm.org/route/v1/foot/{u_lon},{u_lat};{d_lon},{d_lat}?overview=full&geometries=geojson"
    r = requests.get(url, timeout=6)
    if r.status_code == 200:
        data = r.json()
        if data.get("routes"):
            route = data["routes"][0]
            coords = [[float(lat), float(lon)] for lon, lat in route["geometry"]["coordinates"]]
            return coords, float(route["distance"]), None
    return None, None, "OSRM routing service unavailable"






class CustomRouteRequest(BaseModel):
    startLat: float
    startLon: float
    destLat: float
    destLon: float
    allowOnlineFallback: bool = True


class RoadBlockageRequest(BaseModel):
    startLat: float
    startLon: float
    endLat: float
    endLon: float
    reason: str = "Uydu / İHA Tespitli Kapalı Yol"
    severity: str = "Ağır Hasarlı"

# Global in-memory road blockage registry
LIVE_ROAD_BLOCKAGES = [
    {
        "id": "blk-1",
        "coords": [[36.2050, 36.1640], [36.2040, 36.1670], [36.2020, 36.1690]],
        "reason": "Segformer AI Yapay Zeka - Bina Yıkıntısı ve Enkaz Tespiti",
        "severity": "🔴 Geçiş İmkânsız (Kapanmış)",
        "created_at": "2026-08-03T10:00:00Z"
    },
    {
        "id": "blk-2",
        "coords": [[36.2100, 36.1700], [36.2090, 36.1740]],
        "reason": "Uydu / İHA Fotoğraf Analizi - Ağır Yol Çatlağı",
        "severity": "⚠️ Tehlikeli Yol Segmenti",
        "created_at": "2026-08-03T10:15:00Z"
    }
]


_DAMAGE_SOURCE_LABELS = {
    "crack": "YOLO Çatlak Tespiti",
    "destruction": "YOLO Bina Yıkıntı Tespiti",
    "road_damage": "Segformer AI Uydu Analizi",
    "sos": "Saha İhbarı / SOS",
}


def _damage_point_severity_label(source_type: str, severity: Optional[float]) -> str:
    if source_type == "sos":
        return "🆘 SOS Alarmı"
    pct = round((severity or 0.0) * 100)
    if (severity or 0.0) >= 0.6:
        return f"🔴 Ağır Hasar (%{pct} Risk)"
    if (severity or 0.0) >= 0.3:
        return f"⚠️ Orta Hasar (%{pct} Risk)"
    return f"🟡 Hafif Hasar (%{pct} Risk)"








class SOSStatusUpdateRequest(BaseModel):
    status: str  # "OPEN" | "EN_ROUTE" | "RESOLVED"


















class CameraAnalysisRequest(BaseModel):
    modelType: str = "hybrid"  # "catlak", "bina", "hybrid"
    imageBase64: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# AUTHENTICATION & AUTHORIZATION MODELS & ENDPOINTS
class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "survivor"  # "survivor" | "responder"
    city: Optional[str] = "Hatay"
    unit: Optional[str] = "Sivil Afetzede"

class UserLoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
    except ValueError:
        # Legacy/pre-hash accounts had the raw password stored directly.
        # Accept a one-time plaintext match so existing accounts aren't locked out.
        return plain == stored


def _demo_user(id_suffix, name, email, role, unit, city="Hatay"):
    return {
        "id": f"usr-{id_suffix}",
        "name": name,
        "email": email,
        "password": _hash_password("password123"),
        "role": role,
        "city": city,
        "unit": unit,
        "token": f"token-{id_suffix}",
    }

# Demo accounts for development/testing -- multiple per role so team-chat and
# multi-user flows can be tried without needing real registrations. TODO:
# remove or gate behind an env flag before production.
USER_DATABASE = {
    u["email"]: u
    for u in [
        _demo_user("responder-101", "Afet Saha Ekibi", "saha@quakemind.gov.tr", "responder", "Arama Kurtarma Lideri"),
        _demo_user("responder-103", "Zeynep Arslan", "saha2@quakemind.gov.tr", "responder", "AKUT Arama Kurtarma Operatörü"),
        _demo_user("responder-104", "Mehmet Demir", "saha3@quakemind.gov.tr", "responder", "İHA & Uydu Operatörü"),
        _demo_user("responder-105", "Elif Kaya", "saha4@quakemind.gov.tr", "responder", "UMKE Sağlık Ekibi Lideri"),
        _demo_user("responder-106", "Burak Öztürk", "saha5@quakemind.gov.tr", "responder", "İtfaiye Arama Kurtarma"),
        _demo_user("survivor-102", "Afetzede Vatandaş", "afetzede@quakemind.gov.tr", "survivor", "Sivil"),
        _demo_user("survivor-103", "Ali Yıldız", "afetzede2@quakemind.gov.tr", "survivor", "Sivil"),
        _demo_user("survivor-104", "Ayşe Şahin", "afetzede3@quakemind.gov.tr", "survivor", "Sivil"),
    ]
}




def _authenticated_user(token: Optional[str]) -> Optional[dict]:
    """Resolves a token to its user record (PostgreSQL first, then the in-memory
    demo USER_DATABASE), or None if the token doesn't match any known user."""
    if not token:
        return None
    db_user = postgis_engine.get_user_by_token_db(token)
    if db_user:
        return dict(db_user)
    for u in USER_DATABASE.values():
        if u.get("token") == token:
            return dict(u)
    return None


def _require_role(token: Optional[str], allowed_roles: set[str]) -> dict:
    """Raises 401/403 unless token resolves to a user with one of allowed_roles."""
    user = _authenticated_user(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Gecerli bir kimlik dogrulama tokeni gerekli.")
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Bu islem icin yetkiniz yok.")
    return user


# EMERGENCY FCM PUSH NOTIFICATION DISPATCHER
class EmergencyNotificationRequest(BaseModel):
    title: str
    body: str
    severity: str = "critical"  # "critical" | "warning" | "info"
    # Varsayilan yok (kural 1): gonderen yazmadiysa bos kalir. Eskiden 6,8 ve
    # "Hatay" uyduruluyordu; her bildirim o deprem buyuklugunu tasiyordu.
    location: Optional[str] = None
    magnitude: Optional[float] = None
    token: Optional[str] = None

# Bildirimler artik depoda (`bildirimler` tablosu, J-45); bellekteki liste kalkti.




# TEAM CHAT (internal messaging between logged-in responder/admin accounts)
class ChatMessageRequest(BaseModel):
    token: Optional[str] = None
    text: str

team_chat_messages: list[dict] = []
_TEAM_CHAT_LIMIT = 200





if __name__ == "__main__":
    import socket
    import uvicorn

    host = "0.0.0.0"
    port = 8000

    def _get_local_ip() -> str:
        """Returns the LAN IP that other devices on the same network can reach."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # No packet is sent; this is a common way to learn the outbound interface IP.
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except Exception:
            return "127.0.0.1"
        finally:
            sock.close()

    local_ip = _get_local_ip()
    workers = int(os.environ.get("QUAKEMIND_WORKERS", "1"))
    print("\n" + "=" * 60)
    print("FastAPI sunucusu baslatiliyor...")
    print(f"Bu cihazdan: http://127.0.0.1:{port}")
    print(f"Diger cihazlardan (ayni ag): http://{local_ip}:{port}")
    if workers > 1:
        print(f"Worker sayisi: {workers} (her worker modelleri kendi hafizasina ayrica yukler)")
    print("=" * 60 + "\n")

    if workers > 1:
        # Multiple worker processes so one heavy CPU-bound request (e.g. road
        # damage Segformer inference) can't starve every other request in the
        # process via the GIL -- reload isn't compatible with workers>1.
        uvicorn.run("fastapi_app:app", host=host, port=port, workers=workers)
    else:
        # QUAKEMIND_RELOAD=0: --reload kapatma kacisi. Windows'ta bazi venv
        # kurulumlarinda uvicorn'un reloader'i sys.executable'i sistem
        # Python'a cozumleyip worker'i YANLIS interpreter'da baslatabiliyor
        # (bkz. oturum notlari) -- kod degisikligi sonrasi guvenilir sekilde
        # yeniden yuklenmedigi gozlemlendiginde bu bayrakla kapatilabilir.
        reload_enabled = os.environ.get("QUAKEMIND_RELOAD", "1") != "0"
        uvicorn.run("fastapi_app:app", host=host, port=port, reload=reload_enabled)
