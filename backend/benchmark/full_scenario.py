"""Senaryo v2 orkestratoru -- ucdan uca cift tarafli afet simulasyonu.

rich_simulation.py'nin kanitlanmis akisini korur ama uc yerde genisletir:

  1. BOLGE (zone) dongusu: senaryo il genelini kapsadigi icin (Iskenderun
     Antakya'ya 44 km, Elbistan Maras'a 74 km) her ilce KENDI gercek OSM
     grafini, KENDI rastgele kapanma setini ve KENDI analysisId'sini alir.
     Ekipler kendi bolgeleri icinde rota alir. Bkz. scenario_dataset.py.

  2. UC AYRI VERI URETIM KANALI (tek "NLP+SOS" kanali yerine):
       yolo -> gercek gorsel POST /api/camera/analyze (gercek bina.pt cikarimi)
       nlp  -> gercek metin  POST /api/nlp/analyze (gercek BERTurk) + SOS
       sos  -> tek dokunus   POST /api/sos/alert + cihaz otonom durumu
     Her kanal haritada kendi pin standardiyla gorunur.

  3. ROL-FARKINDA ATAMA + BILINCLI CAKISMA TESTI: ihtiyac kategorisi ekip
     roluyle eslestirilir; atamadan sonra IKINCI bir ekip ayni hedefi claim
     etmeyi dener ve gercek 409 alir -- "mukerrer sevk engellendi" iddiasinin
     olculmus kaniti.

YOL KAPANMALARININ UC KAYNAGI (--closure-source; her cikti kaynagini yazar):
  synthetic -- rastgele kapanma (rng.sample). Varsayilan; Senaryo v2'nin
               makalede raporlanan ilk sonuclari bununla uretildi.
  model     -- SegFormer'in deprem sonrasi goruntudeki hasar maskesi
               (benchmark/colab/make_model_masks.py).
  emsr      -- Copernicus EMSR648 Grading yer gercegi (hasarli yol cizgileri).
Uc kaynakta da afetzede/ekip/karargah, rota motoru, atama, BERTurk, YOLOv8 ve
naif karsilastirma AYNIDIR ve GERCEKTEN hesaplanir; degisen tek sey hangi
yollarin kapali oldugudur. Bu, algilama katmaninin katkisini karar/rota
katmaninin katkisindan ayirmayi saglar.

On kosul: python benchmark/warm_scenario_v2_cache.py (8 bolgenin grafi
cache'te olmali) ve backend'in ayakta olmasi.

ARA KARSILASTIRMA REFERANSLARI (--references; varsayilan kapali): R0'a ek olarak
R1 gorus mesafeli ajan ve R2 bilgi paylasan filo ayni oturumda hesaplanir
(makale Bolum 3.8, Tablo 16); R0 her kosuda naive_compare ile birebir kontrol edilir.

Kullanim:
  python benchmark/full_scenario.py all
  python benchmark/full_scenario.py hatay --speed 3
  python benchmark/full_scenario.py kahramanmaras --run-id senaryo-v2-maras
  python benchmark/full_scenario.py all --references --closure-source emsr --zones H-Z1 H-Z3 K-Z1 K-Z2
"""

import argparse
import base64
import json
import random
import sys
import time
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_runner import API_BASE, RunLogger, RUNS_DIR, DURUM_PRIORITY, _haversine_m  # noqa: E402
from naive_baseline import AVERAGE_SPEED_KMH, U_TURN_PENALTY_MIN, naive_time_minutes  # noqa: E402
import importlib  # noqa: E402

import scenario_dataset as DS  # noqa: E402

# --dataset ile secilebilen veri setleri; ikisi de ayni arayuzu sunar.
DATASETS = {
    "v2": "scenario_dataset",              # Senaryo v2: 8 ilce, Maxar
    "drone": "scenario_dataset_drone",     # Help.NGO drone sahneleri: 3 mahalle, ~3,5 cm/px
}

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

CLOSURE_RATIO = 0.18

# Insan-izlenebilir hiz -- /command sayfasi "SIMULASYON MODU" acikken adim adim
# izlenebilsin diye. --speed ile hizlandirilir.
CHANNEL_STEP_DELAY_SEC = 1.6
CLAIM_STEP_DELAY_SEC = 2.2
ZONE_STEP_DELAY_SEC = 1.0

# YOLOv8 kanalinin kullanacagi GERCEK hasar gorselleri. Klasor glob'lanir --
# kullanici benchmark/reports/ icine yeni dogrulanmis gorsel birakirsa kod
# otomatik alir, kod degisikligi gerekmez.
DEBRIS_IMAGE_GLOB = "kate_pd_*_image.png"


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)


# --------------------------------------------------------------------------
# Konum ornekleme
# --------------------------------------------------------------------------
MIN_INCIDENT_SEPARATION_M = 700
MAX_SEPARATION_ATTEMPTS = 60


def sample_point_in_bounds(bounds: dict, rng: random.Random, margin_frac: float = 0.15) -> tuple:
    lat_span = bounds["north"] - bounds["south"]
    lon_span = bounds["east"] - bounds["west"]
    lat = rng.uniform(bounds["south"] + lat_span * margin_frac, bounds["north"] - lat_span * margin_frac)
    lon = rng.uniform(bounds["west"] + lon_span * margin_frac, bounds["east"] - lon_span * margin_frac)
    return lat, lon


def sample_spread_point(bounds: dict, rng: random.Random, existing: list[tuple]) -> tuple:
    """Ayni bbox icinde kalarak noktalari birbirinden ayirir -- saf rastgele
    ornekleme kucuk N ile sans eseri ust uste noktalar uretebiliyor."""
    candidate = sample_point_in_bounds(bounds, rng)
    for _ in range(MAX_SEPARATION_ATTEMPTS):
        if all(_haversine_m(candidate[0], candidate[1], la, lo) >= MIN_INCIDENT_SEPARATION_M
               for la, lo in existing):
            return candidate
        candidate = sample_point_in_bounds(bounds, rng)
    return candidate


MAX_REACHABILITY_ATTEMPTS = 12


def _is_reachable_from(hq: dict, lat: float, lon: float, analysis_id: str) -> bool:
    """Kapanmalar uygulanmis GERCEK graf uzerinde, karargahtan bu noktaya
    rota var mi (backend'in kendi rota motoruna sorulur)."""
    try:
        resp = requests.post(f"{API_BASE}/api/road_damage/route", json={
            "analysisId": analysis_id,
            "startLat": hq["lat"], "startLon": hq["lon"],
            "endLat": lat, "endLon": lon,
        }, timeout=60)
        return resp.status_code == 200
    except Exception:
        return False


def _sample_reachable_point(logger: RunLogger, bounds: dict, rng: random.Random,
                            existing: list[tuple], hqs: list[dict],
                            analysis_id: str, victim_id: str) -> tuple:
    """Bolgedeki TUM karargahlardan ulasilabilen, digerlerinden yeterince uzak
    bir nokta bulur. Bulunamazsa son adayla devam eder (kosuyu bloklamaz) ve
    durumu loglar -- sessizce kabul edilmez."""
    candidate = sample_spread_point(bounds, rng, existing)
    for attempt in range(MAX_REACHABILITY_ATTEMPTS):
        if all(_is_reachable_from(hq, candidate[0], candidate[1], analysis_id) for hq in hqs):
            if attempt:
                logger.log("victim_point_resampled", victimId=victim_id, attempts=attempt + 1)
            return candidate
        candidate = sample_spread_point(bounds, rng, existing)
    logger.log("victim_point_unreachable", victimId=victim_id,
               attempts=MAX_REACHABILITY_ATTEMPTS,
               note="tum karargahlardan ulasilabilir nokta bulunamadi, son adayla devam")
    return candidate


def _clamp_into_bounds(lat: float, lon: float, bounds: dict, margin_frac: float = 0.06) -> tuple:
    """Karargah koordinatini grafin gercekten kapsadigi alanin icine ceker.

    Neden gerekli: graf disindaki bir baslangic noktasi, osmnx'in
    nearest_nodes'u tarafindan sinirdaki rastgele bir dugume "kilitleniyor" --
    rota o dugumden basliyor ve mesafe anlamsiz cikiyor (bu sinif hata daha
    once afetzede konumlari icin yasandi ve duzeltildi, bkz. oturum notlari).
    Karargah zaten ilce merkezine yerlestirildigi icin normalde iceride kalir;
    bu sadece guvenlik agi."""
    lat_span = bounds["north"] - bounds["south"]
    lon_span = bounds["east"] - bounds["west"]
    lat_lo, lat_hi = bounds["south"] + lat_span * margin_frac, bounds["north"] - lat_span * margin_frac
    lon_lo, lon_hi = bounds["west"] + lon_span * margin_frac, bounds["east"] - lon_span * margin_frac
    return min(max(lat, lat_lo), lat_hi), min(max(lon, lon_lo), lon_hi)


# --------------------------------------------------------------------------
# Cihaz durumu -> BLE mesh paketi (gercekten olculur)
# --------------------------------------------------------------------------
def build_mesh_packet(victim: dict, lat: float, lon: float) -> tuple[str, int]:
    """2. seviye fallback'te (sebeke yok) BLE mesh uzerinden birakilan hafif
    JSON paketini GERCEKTEN serilestirir ve byte uzunlugunu olcer.

    Senaryodaki "150 byte'lik paket" iddiasi boylece tahmin degil olcum olur;
    rapor bu sayiyi oldugu gibi yazar (150'nin altinda/ustunde ciksa bile)."""
    packet = {
        "id": victim["id"],
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "type": victim["channel"],
        "risk": victim["durum"],
        "batt": victim["batteryPercent"],
    }
    raw = json.dumps(packet, separators=(",", ":"), ensure_ascii=False)
    return raw, len(raw.encode("utf-8"))


def device_state(victim: dict, lat: float, lon: float) -> dict:
    """Akis diyagramindaki cihaz otonom davranis dalini somut alanlara cevirir."""
    battery = victim["batteryPercent"]
    packet_raw, packet_bytes = build_mesh_packet(victim, lat, lon)
    return {
        "batteryPercent": battery,
        "commsStatus": victim["commsStatus"],
        "powerMode": DS.derive_power_mode(battery),
        "sirenActive": bool(victim.get("sirenActive", False)),
        "gpsPollingSec": DS.derive_gps_polling_sec(battery),
        "payloadBytes": packet_bytes,
        "meshPacketRaw": packet_raw,
        "channel": victim["channel"],
    }


# --------------------------------------------------------------------------
# Kanal 1: YOLOv8 goruntu analizi (GERCEK model cikarimi)
# --------------------------------------------------------------------------
def _debris_images() -> list[Path]:
    return sorted(REPORTS_DIR.glob(DEBRIS_IMAGE_GLOB))


def run_yolo_channel(logger: RunLogger, victim: dict, lat: float, lon: float,
                     images: list[Path], image_index: int) -> dict:
    """Afetzede bina/catlak fotografi cekiyor -> gercek bina.pt cikarimi ->
    haritada turuncu enkaz pini. Model gercekten calisir (mock yok)."""
    state = device_state(victim, lat, lon)
    result: dict = {"channel": "yolo", "deviceState": state}

    if not images:
        logger.log("yolo_no_image", victimId=victim["id"])
        result["error"] = "gorsel havuzu bos"
        return result

    img_path = images[image_index % len(images)]
    data_url = "data:image/png;base64," + base64.b64encode(img_path.read_bytes()).decode("ascii")

    t0 = time.perf_counter()
    try:
        resp = requests.post(f"{API_BASE}/api/camera/analyze", json={
            "modelType": "bina", "imageBase64": data_url,
            "latitude": lat, "longitude": lon,
        }, timeout=120)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        payload = resp.json()
        detections = payload.get("detections", [])
        result.update({
            "imageFile": img_path.name,
            "latencyMs": round(latency_ms, 1),
            "status": payload.get("status"),
            "detections": detections,
            "detectionCount": len(detections),
            "topLabel": detections[0]["label"] if detections else None,
            "topConfidence": detections[0]["confidence"] if detections else None,
            "debrisReportId": payload.get("debrisReportId"),
        })
        logger.log("yolo_analyze", victimId=victim["id"], file=img_path.name,
                   latencyMs=result["latencyMs"], detectionCount=len(detections),
                   status=payload.get("status"))
    except Exception as e:
        logger.log("yolo_analyze_error", victimId=victim["id"], error=str(e))
        result["error"] = str(e)
        return result

    # Hasar ihbari ayni zamanda ekiplerin sevk listesine dussun diye SOS
    # kaydina da yazilir -- aksi halde harita uzerinde enkaz pini gorunur ama
    # hicbir ekip atanamaz (kanal farki, ihbar olmadigi anlamina gelmez).
    alert_id = _post_sos(logger, victim, lat, lon, state,
                         message=f"[YOLOv8] {victim.get('damageNote', 'Yapisal hasar tespiti')} "
                                 f"({result.get('topLabel') or 'tespit yok'})")
    result["alertId"] = alert_id
    return result


# --------------------------------------------------------------------------
# Kanal 2: BERTurk NLP (GERCEK model cikarimi)
# --------------------------------------------------------------------------
# Modelin GERCEK ust kategorileri (bkz. apps/disaster_nlp/src/classification.py
# CATEGORY_MAPPING) ile senaryonun operasyonel ihtiyac etiketleri birebir ayni
# degil. Modelin kendi ciktisi ASLA gizlenmez -- rapor her iki sutunu da
# gosterir; bu sadece "hangi ekip rolu gitmeli" sorusuna cevap veren ince bir
# esleme katmanidir.
NLP_CATEGORY_TO_ROLE = {
    "Enkaz Bildirimi": "arama-kurtarma",
    "Acil Yardim Ihtiyaci": "medikal",
    "Acil Yardım İhtiyacı": "medikal",
    "Lojistik Ihtiyac Bildirimi": "lojistik",
    "Lojistik İhtiyaç Bildirimi": "lojistik",
    "Yol Kapanma Bilgisi / Lojistik": "lojistik",
}

ACILIYET_LABELS = {1: "DUSUK", 2: "DUSUK", 3: "ORTA", 4: "YUKSEK", 5: "KRITIK"}


def run_nlp_channel(logger: RunLogger, victim: dict, lat: float, lon: float) -> dict:
    """Afetzede serbest metin yaziyor -> gercek BERTurk siniflandirma + NER
    konum cikarimi -> haritada sari ihtiyac pini + SOS kaydi."""
    state = device_state(victim, lat, lon)
    result: dict = {"channel": "nlp", "deviceState": state}

    t0 = time.perf_counter()
    try:
        resp = requests.post(f"{API_BASE}/api/nlp/analyze",
                             json={"text": victim["needText"]}, timeout=180)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        nlp = resp.json()
        # Model metni afetle ILISKISIZ bulursa endpoint siniflandirma yerine
        # {"status":"ignored"} donuyor. Bu bir HATA DEGIL, modelin gercek
        # karari -- ve olculdu ki her zaman dogru degil: "apartman boslugunda
        # kanamali kazazede var, acil doktor ve ambulans!" gibi acikca afet
        # ici bir metin de elenebiliyor. Sessizce None birakmak yerine acikca
        # kaydedilir; rapor bunu yanlis-negatif olarak gosterir.
        result["modelStatus"] = nlp.get("status") or "classified"
        result["modelIgnoredReason"] = nlp.get("reason")
        result.update({
            "latencyMs": round(latency_ms, 1),
            "modelKategori": nlp.get("kategori"),
            "modelAciliyet": nlp.get("aciliyet"),
            "modelAciliyetLabel": ACILIYET_LABELS.get(nlp.get("aciliyet"), "?"),
            "modelGuvenSkoru": nlp.get("guven_skoru"),
            "modelKonum": nlp.get("konum"),
            "modelKonumMetin": nlp.get("konum_metin"),
            "derivedRole": NLP_CATEGORY_TO_ROLE.get(nlp.get("kategori")),
        })
        logger.log("nlp_analyze", victimId=victim["id"], latencyMs=result["latencyMs"],
                   kategori=nlp.get("kategori"), aciliyet=nlp.get("aciliyet"),
                   guven=nlp.get("guven_skoru"))
    except Exception as e:
        logger.log("nlp_analyze_error", victimId=victim["id"], error=str(e))
        result["error"] = str(e)

    result["alertId"] = _post_sos(logger, victim, lat, lon, state, message=victim["needText"])
    return result


# --------------------------------------------------------------------------
# Kanal 3: Tek dokunus acil SOS
# --------------------------------------------------------------------------
def run_sos_channel(logger: RunLogger, victim: dict, lat: float, lon: float) -> dict:
    """Ekrana tek dokunus -> metin yok, cihaz otonom durumu var (pil, guc modu,
    siren, mesh paketi) -> haritada kirmizi (siren aktifse flasor) pin."""
    state = device_state(victim, lat, lon)
    message = f"[SOS] {victim.get('situationNote', 'Acil yardim cagrisi')}"
    alert_id = _post_sos(logger, victim, lat, lon, state, message=message)
    return {"channel": "sos", "deviceState": state, "alertId": alert_id, "latencyMs": None}


def _post_sos(logger: RunLogger, victim: dict, lat: float, lon: float,
              state: dict, message: str) -> str | None:
    """Uc kanalin da ortak cikis noktasi: gercek SOS pipeline'i."""
    try:
        resp = requests.post(f"{API_BASE}/api/sos/alert", json={
            "latitude": lat, "longitude": lon,
            "message": message, "userId": victim["id"],
            "batteryPercent": state["batteryPercent"],
            "commsStatus": state["commsStatus"],
            "powerMode": state["powerMode"],
            "sirenActive": state["sirenActive"],
            "gpsPollingSec": state["gpsPollingSec"],
            "payloadBytes": state["payloadBytes"],
            "channel": state["channel"],
        }, timeout=30)
        resp.raise_for_status()
        alert = resp.json()
        logger.log("sos_alert", victimId=victim["id"], alertId=alert.get("id"),
                   channel=state["channel"], durum=victim["durum"],
                   batteryPercent=state["batteryPercent"], powerMode=state["powerMode"],
                   sirenActive=state["sirenActive"], payloadBytes=state["payloadBytes"])
        return alert.get("id")
    except Exception as e:
        logger.log("sos_alert_error", victimId=victim["id"], error=str(e))
        return None


CHANNEL_RUNNERS = {"yolo": run_yolo_channel, "nlp": run_nlp_channel, "sos": run_sos_channel}


# --------------------------------------------------------------------------
# Rol-farkinda atama + gercek kilit + gercek rota
# --------------------------------------------------------------------------
def _priority_key(victim: dict) -> tuple:
    return (DURUM_PRIORITY.get(victim["durum"], 9), 0 if victim["channel"] == "sos" else 1)


def assign_zone(logger: RunLogger, zone: dict, victims: list[dict], teams: list[dict],
                analysis_id: str, speed: float) -> list[dict]:
    """Bir bolgedeki afetzedeleri ekiplere atar.

    Eski (rich_simulation) davranis SAF MESAFE acgozlusuydu: en yakin ekip
    gider. Burada once ROL uyumu aranir (medikal ihtiyaca medikal ekip),
    uyan rol yoksa mesafeye dusulur -- "9 ekip 9 farkli kritik noktaya
    dagilir" iddiasinin gercek mekanizmasi budur."""
    ordered = sorted(victims, key=_priority_key)
    available = list(teams)
    assignments = []

    for victim in ordered:
        if not available:
            break

        # Rol secimi: NLP modelinin cikardigi kategori IHTIYAC TIPINI anlatir,
        # vakanin HAYATI ACILIYETINI degil. Ornek: "bina yan yatti, iceride 3
        # kisi var, hilti ve jenerator lazim" metnini model (dogru bicimde)
        # lojistik/ekipman ihtiyaci sayar -- ama oraya gitmesi gereken ekip
        # arama-kurtarmadir. Bu yuzden:
        #   kritik/mahsur -> profilin preferredRole'u (hayat kurtarma onceligi)
        #   digerleri     -> modelin cikardigi rol, yoksa preferredRole
        # Model ciktisi hicbir zaman GIZLENMEZ; raporda kendi sutununda durur.
        if victim["durum"] in ("kritik", "mahsur"):
            preferred = victim.get("preferredRole")
        else:
            preferred = victim.get("derivedRole") or victim.get("preferredRole")
        pool = [t for t in available if t["role"] == preferred] or available
        victim["assignedByRole"] = preferred
        team = min(pool, key=lambda t: _haversine_m(
            victim["lat"], victim["lon"], t["startLat"], t["startLon"]))
        available.remove(team)

        target_id = victim.get("alertId") or victim["id"]
        claim_body = {"teamId": team["id"], "targetId": target_id, "targetType": "sos",
                      "lat": victim["lat"], "lon": victim["lon"]}
        try:
            resp = requests.post(f"{API_BASE}/api/team/claim", json=claim_body, timeout=15)
            logger.log("team_claim", teamId=team["id"], victimId=victim["id"],
                       statusCode=resp.status_code, result=resp.json())
            if resp.status_code not in (200, 201):
                continue
        except Exception as e:
            logger.log("team_claim_error", teamId=team["id"], victimId=victim["id"], error=str(e))
            continue

        # --- Bilincli cakisma testi: ikinci bir ekip ayni hedefi almaya calisir.
        # Bu, "mukerrer sevk engellendi" iddiasinin OLCULMUS kanitidir; sonuc
        # 409 degilse kilit mekanizmasi bozulmus demektir ve raporda oyle gorunur.
        conflict = None
        if available:
            rival = available[0]
            try:
                rival_resp = requests.post(f"{API_BASE}/api/team/claim", json={
                    "teamId": rival["id"], "targetId": target_id, "targetType": "sos",
                    "lat": victim["lat"], "lon": victim["lon"],
                }, timeout=15)
                conflict = {"rivalTeamId": rival["id"], "statusCode": rival_resp.status_code,
                            "blocked": rival_resp.status_code == 409}
                logger.log("team_claim_conflict", teamId=rival["id"], victimId=victim["id"],
                           statusCode=rival_resp.status_code, blocked=conflict["blocked"])
            except Exception as e:
                logger.log("team_claim_conflict_error", teamId=rival["id"],
                           victimId=victim["id"], error=str(e))

        route_result = None
        naive_result = None
        try:
            route_resp = requests.post(f"{API_BASE}/api/road_damage/route", json={
                "analysisId": analysis_id,
                "startLat": team["startLat"], "startLon": team["startLon"],
                "endLat": victim["lat"], "endLon": victim["lon"],
            }, timeout=60)
            if route_resp.status_code == 200:
                route_result = route_resp.json()

                # "Biz soylemeseydik nereden giderdi": ayni istek dongusu icinde,
                # AYNI surecteki AYNI kapanma kumesiyle. (Surecler arasi tekrar
                # sorgulama farkli kapanma kumesi uretip matematiksel olarak
                # imkansiz sonuclara yol aciyordu -- bkz. rich_simulation notlari.)
                try:
                    naive_resp = requests.post(f"{API_BASE}/api/road_damage/naive_compare", json={
                        "analysisId": analysis_id,
                        "startLat": team["startLat"], "startLon": team["startLon"],
                        "endLat": victim["lat"], "endLon": victim["lon"],
                    }, timeout=120)
                    naive_resp.raise_for_status()
                    naive_result = naive_resp.json()
                except Exception as e:
                    logger.log("naive_compare_error", teamId=team["id"], victimId=victim["id"], error=str(e))
                    naive_result = {"reachable": False, "distanceMeters": None,
                                    "discoveries": None, "routeCoords": None}

                requests.post(f"{API_BASE}/api/team/claim/{target_id}/route", json={
                    "routeCoords": route_result["routeCoords"],
                    "distanceMeters": route_result["distanceMeters"],
                    "naiveRouteCoords": naive_result.get("routeCoords") if naive_result.get("reachable") else None,
                    "naiveDistanceMeters": naive_result.get("distanceMeters"),
                    "naiveReachable": naive_result.get("reachable"),
                }, timeout=15)
                logger.log("team_route", teamId=team["id"], victimId=victim["id"],
                           distanceMeters=route_result["distanceMeters"],
                           naiveDistanceMeters=naive_result.get("distanceMeters"),
                           naiveReachable=naive_result.get("reachable"),
                           naiveDiscoveries=naive_result.get("discoveries"))
                _safe_print(f"    [EKIP] {team['id']} ({team['unit']}) -> {victim['name']} "
                            f"({route_result['distanceMeters']:.0f}m)")
            else:
                logger.log("team_route_failed", teamId=team["id"], victimId=victim["id"],
                           statusCode=route_resp.status_code, body=route_resp.text[:300])
        except Exception as e:
            logger.log("team_route_error", teamId=team["id"], victimId=victim["id"], error=str(e))

        try:
            requests.post(f"{API_BASE}/api/sos/alert/{target_id}/status",
                          json={"status": "EN_ROUTE"}, timeout=15)
        except Exception:
            pass

        assignments.append({
            "zoneId": zone["id"], "zoneLabel": zone["label"],
            "teamId": team["id"], "teamUnit": team["unit"], "teamRole": team["role"],
            "hqId": team["hqId"], "hqName": team["hqName"],
            # Referans karsilastirmasi (R1/R2) ayni baslangic-hedef ciftini kullanir.
            "startLat": team["startLat"], "startLon": team["startLon"],
            "endLat": victim["lat"], "endLon": victim["lon"],
            "victimId": victim["id"], "victimName": victim["name"],
            "victimLocationLabel": victim["locationLabel"], "channel": victim["channel"],
            "durum": victim["durum"], "alertId": target_id,
            "claimConflict": conflict,
            "distanceMeters": route_result.get("distanceMeters") if route_result else None,
            "routeCoords": route_result.get("routeCoords") if route_result else None,
            "naiveDistanceMeters": naive_result.get("distanceMeters") if naive_result else None,
            "naiveReachable": naive_result.get("reachable") if naive_result else None,
            "naiveDiscoveries": naive_result.get("discoveries") if naive_result else None,
            "evacuationTarget": _nearest_assembly(logger, victim),
        })
        time.sleep(CLAIM_STEP_DELAY_SEC / speed)

    return assignments


def _nearest_assembly(logger: RunLogger, victim: dict) -> dict | None:
    """Afetzedenin tahliye hedefi -- GERCEK AFAD toplanma alani verisi
    (/api/road_damage/assembly zaten dist_m'e gore sirali donduruyor)."""
    try:
        resp = requests.get(f"{API_BASE}/api/road_damage/assembly", params={
            "latitude": victim["lat"], "longitude": victim["lon"], "radiusKm": 5.0,
        }, timeout=30)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        if not records:
            return None
        nearest = records[0]
        return {"name": nearest.get("name") or nearest.get("ad") or "Toplanma alani",
                "distanceM": nearest.get("dist_m"),
                "lat": nearest.get("lat"), "lon": nearest.get("lon")}
    except Exception as e:
        logger.log("assembly_lookup_error", victimId=victim["id"], error=str(e))
        return None


# --------------------------------------------------------------------------
# Ara karsilastirma referanslari (makale Bolum 3.8)
# --------------------------------------------------------------------------
# R0 burada da bir kez hesaplanir: yeni simulatorun R0 modu naive_compare ile
# birebir ayni cikmali (her kosuda kontrol edilir, summary.json -> referenceCheck).
REFERENCE_VARIANTS = [
    {"name": "R0", "sightM": 0.0, "share": False},
    {"name": "R1", "sightM": 100.0, "share": False},   # gorus mesafeli ajan, d_g = 100 m
    {"name": "R2", "sightM": 0.0, "share": True},      # bilgi paylasan filo (kafile kurali)
    {"name": "R1R2", "sightM": 100.0, "share": True},  # ikisi birlikte -- makalede tanimli degil, ek
    # Duyarlilik: ayni anda varan her ekip kapanmayi kendisi kesfeder (kafilede paylasim yok).
    {"name": "R2e", "sightM": 0.0, "share": True, "simultaneousKnown": False},
]
# Ilki raporlanan deger. R2'de sonuc t_u'ya bagli (kim once ogrenir), bu yuzden
# duyarlilik degerleri ayrica simule edilir.
REFERENCE_T_U_VALUES = [U_TURN_PENALTY_MIN, 0.0, 5.0, 10.0, 30.0]
REFERENCE_KEY = f"{U_TURN_PENALTY_MIN:g}"


def run_references(logger: RunLogger, zone: dict, analysis_id: str, assignments: list[dict]) -> dict | None:
    """Bolgenin rotalanan tum atamalari icin R0/R1/R2/R1R2'yi ayni oturumda
    hesaplatir ve sonucu atamalara yazar. R2'de bilgi bu atamalar arasinda
    paylasilir (bolge ici filo). Basarisizlik kosuyu durdurur -- eksik
    referansla ozet sessizce yanlis olurdu."""
    routed = [a for a in assignments if a.get("distanceMeters") is not None]
    if not routed:
        return None
    tasks = [{"id": a["victimId"], "startLat": a["startLat"], "startLon": a["startLon"],
              "endLat": a["endLat"], "endLon": a["endLon"]} for a in routed]
    t0 = time.perf_counter()
    try:
        resp = requests.post(f"{API_BASE}/api/road_damage/reference_compare", json={
            "analysisId": analysis_id, "tasks": tasks, "variants": REFERENCE_VARIANTS,
            "speedKmh": AVERAGE_SPEED_KMH, "uTurnPenaltyMinValues": REFERENCE_T_U_VALUES,
        }, timeout=3600)
        resp.raise_for_status()
        body = resp.json()
    except Exception as e:
        logger.log("reference_compare_error", zoneId=zone["id"], error=str(e))
        raise RuntimeError(f"{zone['id']} reference_compare basarisiz: {e}") from e

    by_id: dict = {}
    for var in body["variants"]:
        for tu, rows in var["byUTurnPenalty"].items():
            for row in rows:
                by_id.setdefault(row["id"], {}).setdefault(var["name"], {})[tu] = {
                    k: v for k, v in row.items() if k != "id"}
    for a in routed:
        a["references"] = by_id.get(a["victimId"])
    elapsed = round(time.perf_counter() - t0, 1)
    variant_sec = {var["name"]: var["elapsedSec"] for var in body["variants"]}
    logger.log("reference_compare", zoneId=zone["id"], taskCount=len(tasks),
               elapsedSec=elapsed, variantSec=variant_sec)
    _safe_print(f"    [REFERANS] R0/R1/R2/R1R2, {len(tasks)} gorev ({elapsed:.0f} sn)")
    return {"elapsedSec": elapsed, "variantSec": variant_sec}


def reference_check(assignments: list[dict]) -> dict:
    """Yeni simulatorun R0 modu, naive_compare'in sonucunu birebir veriyor mu."""
    checked, mismatches = 0, []
    for a in assignments:
        refs = a.get("references")
        if not refs or "R0" not in refs:
            continue
        r = refs["R0"][REFERENCE_KEY]
        checked += 1
        if a.get("naiveReachable"):
            same = (r.get("reachable") and r["distanceMeters"] == a["naiveDistanceMeters"]
                    and r["discoveries"] == a["naiveDiscoveries"])
        else:
            same = not r.get("reachable")
        if not same:
            mismatches.append({"victimId": a["victimId"], "zoneId": a["zoneId"],
                               "naive": [a.get("naiveReachable"), a.get("naiveDistanceMeters"),
                                         a.get("naiveDiscoveries")],
                               "R0": r})
    return {"checked": checked, "identical": checked - len(mismatches), "mismatches": mismatches}


# --------------------------------------------------------------------------
# Karsilastirma ozeti
# --------------------------------------------------------------------------
def compute_comparison(assignments: list[dict]) -> dict:
    """Tablo 4'un ham verisi. Naive sure ARTIK sadece mesafe/hiz degil --
    her kapali-yol kesfi icin U-donusu cezasi da eklenir (bkz.
    naive_baseline.U_TURN_PENALTY_MIN, acikca belirtilmis varsayim)."""
    rows = []
    for a in assignments:
        if a.get("distanceMeters") is None:
            continue
        our_time = a["distanceMeters"] / 1000.0 / AVERAGE_SPEED_KMH * 60.0
        row = {
            "teamId": a["teamId"], "victimId": a["victimId"], "victimName": a["victimName"],
            "zoneId": a["zoneId"], "durum": a["durum"],
            "ourEngineDistanceMeters": round(a["distanceMeters"], 1),
            "ourEngineTimeMin": round(our_time, 1),
            "naiveUnreachable": not a.get("naiveReachable"),
            "naiveDiscoveries": a.get("naiveDiscoveries"),
        }
        if a.get("references"):
            # Ham sonuc (varyant -> t_u -> mesafe/olay); sure ozetleyicide hesaplanir.
            row["references"] = a["references"]
        if a.get("naiveReachable") and a.get("naiveDistanceMeters") is not None:
            naive_time = naive_time_minutes(a["naiveDistanceMeters"], a.get("naiveDiscoveries"))
            row.update({
                "naiveDistanceMeters": round(a["naiveDistanceMeters"], 1),
                "naiveTravelOnlyTimeMin": round(
                    a["naiveDistanceMeters"] / 1000.0 / AVERAGE_SPEED_KMH * 60.0, 1),
                "naiveUTurnPenaltyMin": round((a.get("naiveDiscoveries") or 0) * U_TURN_PENALTY_MIN, 1),
                "naiveTimeMin": round(naive_time, 1),
                "distanceSavedMeters": round(a["naiveDistanceMeters"] - a["distanceMeters"], 1),
                "timeSavedMin": round(naive_time - our_time, 1),
            })
        rows.append(row)

    reachable = [r for r in rows if not r["naiveUnreachable"]]
    stuck = [r for r in rows if r["naiveUnreachable"]]
    total_saved = sum(r["timeSavedMin"] for r in reachable)
    total_our = sum(r["ourEngineTimeMin"] for r in rows)
    total_naive = sum(r["naiveTimeMin"] for r in reachable)
    return {
        "assignmentCount": len(rows),
        "reachableByNaiveCount": len(reachable),
        "naiveStuckCount": len(stuck),
        "totalOurEngineTimeMin": round(total_our, 1),
        "totalNaiveTimeMinReachableOnly": round(total_naive, 1),
        "totalTimeSavedMin": round(total_saved, 1),
        "avgTimeSavedMinPerTeam": round(total_saved / len(reachable), 1) if reachable else None,
        "totalUTurnsAvoided": sum((r.get("naiveDiscoveries") or 0) for r in rows),
        "assumptions": {
            "averageSpeedKmh": AVERAGE_SPEED_KMH,
            "uTurnPenaltyMin": U_TURN_PENALTY_MIN,
        },
        "rows": rows,
    }


# --------------------------------------------------------------------------
# Bolge kosusu
# --------------------------------------------------------------------------
def run_zone(logger: RunLogger, zone: dict, rng: random.Random, speed: float,
             closure_ratio: float, images: list[Path], image_counter: list[int],
             closure_source: str = "synthetic", blockage_radius_m: float = 25.0,
             mask_suffix: str = "", emsr_rule: str = "loose", emsr_buffer_m: float = 8.0,
             references: bool = False) -> dict:
    _safe_print(f"\n  --- {zone['id']} {zone['label']} ---")

    # Drone bolgeleri grafi ve maskeyi sahnenin KENDI kutusunda kullanir.
    bbox_fields = {}
    if zone.get("bbox"):
        w, s_, e, n = zone["bbox"]
        bbox_fields = {"bboxWest": w, "bboxSouth": s_, "bboxEast": e, "bboxNorth": n}

    # Tohum IKI kaynakta da cekilir: rng dizisi kaynaktan bagimsiz kalsin ki
    # afetzede yerlesimi gibi sonraki rastgele adimlar, kapanma kaynagi
    # degistiginde kaymasin (iki kaynagin karsilastirilabilirligi icin).
    closure_seed = rng.randint(1, 10_000_000)
    if closure_source == "model":
        # Kapanmalar Colab'da SegFormer ile uretilmis hazir maskeden gelir
        # (benchmark/colab/). Maske yoksa KOSU DURUR -- sessizce sentetige
        # dusmek, "model tabanli" sanilan sentetik sonuc demek olurdu.
        resp = requests.post(f"{API_BASE}/api/road_damage/closures_from_mask", json={
            "maskId": f"{zone['id']}{mask_suffix}",
            "latitude": zone["center"][0], "longitude": zone["center"][1],
            "radiusKm": zone["radiusKm"], "blockageRadiusM": blockage_radius_m,
            **bbox_fields,
        }, timeout=600)
        endpoint = "closures_from_mask"
    elif closure_source == "emsr":
        # YER GERCEGI: Copernicus EMSR648 Grading hasarli yol cizgileri.
        # Paketi olmayan bolgede KOSU DURUR -- sessizce sentetige dusulmez.
        if not zone.get("emsrPackage"):
            raise RuntimeError(
                f"{zone['id']} icin EMSR648 yol yer gercegi yok. EMSR kapsamindaki "
                f"bolgelerle kosun (orn. --zones H-Z1 H-Z3 K-Z1 K-Z2).")
        resp = requests.post(f"{API_BASE}/api/road_damage/closures_from_emsr", json={
            "emsrPackage": zone["emsrPackage"],
            "latitude": zone["center"][0], "longitude": zone["center"][1],
            "radiusKm": zone["radiusKm"], "gradeRule": emsr_rule, "bufferM": emsr_buffer_m,
            **bbox_fields,
        }, timeout=600)
        endpoint = "closures_from_emsr"
    else:
        resp = requests.post(f"{API_BASE}/api/road_damage/simulate_closures", json={
            "latitude": zone["center"][0], "longitude": zone["center"][1],
            "radiusKm": zone["radiusKm"], "closureRatio": closure_ratio,
            "seed": closure_seed,
            **bbox_fields,
        }, timeout=180)
        endpoint = "simulate_closures"
    if resp.status_code != 200:
        raise RuntimeError(f"{zone['id']} {endpoint} basarisiz: "
                           f"{resp.status_code} {resp.text[:300]}")
    closure = resp.json()
    analysis_id = closure["analysisId"]
    bounds = closure["bounds"]
    blocked = closure["blockedRoadSegments"]
    safe = closure["safeRoadSegments"]
    actual_source = closure.get("closureSource", "synthetic")
    logger.log(endpoint, zoneId=zone["id"], analysisId=analysis_id,
               bounds=bounds, blockedCount=len(blocked), safeCount=len(safe),
               closureSource=actual_source,
               closedEdgeCount=closure.get("closedEdgeCount"),
               edgeCount=closure.get("edgeCount"),
               coverage=closure.get("coverage"),
               stats=closure.get("stats"))
    _safe_print(f"    Yol agi [{actual_source.upper()}]: {len(blocked)} kapali / {len(safe)} acik segment")
    if closure.get("coverage"):
        cov = closure["coverage"]
        _safe_print(f"    Goruntu kapsamasi: kenarlarin %{100 * cov['edgesObservedFraction']:.1f}'i goruldu")
    if closure.get("stats") and "edgesInsideObservedFraction" in closure["stats"]:
        st = closure["stats"]
        _safe_print(f"    EMSR: {closure['closedEdgeCount']}/{closure['edgeCount']} kenar kapali "
                    f"(kural {closure['gradeRule']}), AOI icinde kenarlarin %{100 * st['edgesInsideObservedFraction']:.1f}'i")

    # Karargahlar -- graf sinirlarina cekilir (guvenlik agi, bkz. _clamp_into_bounds).
    hqs = []
    for hq in DS.headquarters_in_zone(zone["id"]):
        lat, lon = _clamp_into_bounds(hq["lat"], hq["lon"], bounds)
        hqs.append({**hq, "lat": lat, "lon": lon,
                    "clamped": (lat, lon) != (hq["lat"], hq["lon"])})
        _safe_print(f"    [KARARGAH] {hq['name']}")
    hq_by_id = {h["id"]: h for h in hqs}

    teams = []
    for t in DS.teams_in_zone(zone["id"]):
        hq = hq_by_id[t["hqId"]]
        teams.append({**t, "hqName": hq["name"], "startLat": hq["lat"], "startLon": hq["lon"]})

    # Afetzede konumlari: bolgenin GERCEK graf sinirlari icinde, birbirinden
    # ayrik VE karargahlardan ULASILABILIR.
    #
    # Ulasilabilirlik kontrolu neden gerekli: gercek yaya yol aglari, ozellikle
    # kucuk daglik ilcelerde, bbox icinde birbirine hic baglanmayan parcalar
    # icerir (izole mezralar, kesik patikalar). Rastgele ornekleme afetzedeyi
    # boyle bir parcaya dusurunce ekip fiziksel olarak yola cikamiyor ve
    # /route 422 donuyor -- olculdu: Goksun'da MARAS-AK5 hedefine hic
    # ulasamadi. Bu bir SISTEM hatasi degil, VERI URETIMI kusuru; dolayisiyle
    # nokta, kapanma uygulanmis GERCEK graf uzerinde sinanip yeniden
    # orneklenir. Kapanmalar da hesaba katildigi icin secilen nokta gercekten
    # mudahale edilebilir bir yerdir.
    victims = []
    placed: list[tuple] = []
    for v in DS.victims_in_zone(zone["id"]):
        lat, lon = _sample_reachable_point(logger, bounds, rng, placed, hqs, analysis_id, v["id"])
        placed.append((lat, lon))
        victims.append({**v, "lat": lat, "lon": lon})

    # --- Uc kanal, ihbarlar sirayla haritada belirir ---
    for victim in victims:
        runner = CHANNEL_RUNNERS[victim["channel"]]
        if victim["channel"] == "yolo":
            outcome = runner(logger, victim, victim["lat"], victim["lon"], images, image_counter[0])
            image_counter[0] += 1
        else:
            outcome = runner(logger, victim, victim["lat"], victim["lon"])
        victim["channelResult"] = outcome
        victim["alertId"] = outcome.get("alertId")
        if outcome.get("derivedRole"):
            victim["derivedRole"] = outcome["derivedRole"]

        state = outcome["deviceState"]
        _safe_print(f"    [{victim['channel'].upper():4s}] {victim['name']:14s} "
                    f"{victim['locationLabel']:32s} pil=%{state['batteryPercent']:<3d} "
                    f"{state['powerMode']:8s} {state['commsStatus']:7s} "
                    f"{state['payloadBytes']}B"
                    + ("  SIREN" if state["sirenActive"] else ""))
        time.sleep(CHANNEL_STEP_DELAY_SEC / speed)

    assignments = assign_zone(logger, zone, victims, teams, analysis_id, speed)
    reference_timing = run_references(logger, zone, analysis_id, assignments) if references else None

    return {
        "zoneId": zone["id"], "zoneLabel": zone["label"], "city": zone["city"],
        "center": {"lat": zone["center"][0], "lon": zone["center"][1]},
        "radiusKm": zone["radiusKm"], "analysisId": analysis_id, "bounds": bounds,
        "closureSource": actual_source,
        "closureRatio": closure_ratio if actual_source == "synthetic" else None,
        "blockageRadiusM": closure.get("blockageRadiusM"),
        "closedEdgeCount": closure.get("closedEdgeCount"),
        "edgeCount": closure.get("edgeCount"),
        "coverage": closure.get("coverage"),
        "maskId": closure.get("maskId"),
        "maskMeta": closure.get("maskMeta"),
        "emsrPackage": closure.get("emsrPackage"),
        "gradeRule": closure.get("gradeRule"),
        "emsrRoadGradesInBbox": closure.get("emsrRoadGradesInBbox"),
        "closureStats": closure.get("stats"),
        "blockedSegmentCount": len(blocked), "safeSegmentCount": len(safe),
        "blockedRoadSegments": blocked,
        "referenceTiming": reference_timing,
        "headquarters": hqs,
        "teams": teams,
        "victims": victims,
        "assignments": assignments,
    }


def run_city(city: str, run_id: str | None, seed: int, speed: float, closure_ratio: float,
             closure_source: str = "synthetic", blockage_radius_m: float = 25.0,
             mask_suffix: str = "", dataset: str = "v2", emsr_rule: str = "loose",
             emsr_buffer_m: float = 8.0, zone_filter: list | None = None,
             references: bool = False) -> Path:
    prefix = "senaryo-v2" if dataset == "v2" else f"senaryo-{dataset}"
    run_id = run_id or f"{prefix}-{city}-{int(time.time())}"
    run_dir = RUNS_DIR / run_id
    logger = RunLogger(run_dir)
    rng = random.Random(seed)
    images = _debris_images()
    image_counter = [0]

    zones = DS.zones_for_city(city)
    if zone_filter:
        zones = [z for z in zones if z["id"] in zone_filter]
        if not zones:
            _safe_print(f"  ({DS.CITY_LABELS[city]}: --zones ile secilen bolge yok, atlandi)")
            return None
    title = "SENARYO v2" if dataset == "v2" else f"SENARYO {dataset.upper()}"
    _safe_print(f"\n=== {title}: {DS.CITY_LABELS[city]} "
                f"({len(zones)} bolge, {len([v for v in DS.VICTIMS if v['city'] == city])} afetzede, "
                f"{len([t for t in DS.TEAMS if t['city'] == city])} ekip) ===")
    _safe_print("/command sayfasini 'SIMULASYON MODU' acik halde izleyin.")
    if not images:
        _safe_print(f"  UYARI: {REPORTS_DIR}/{DEBRIS_IMAGE_GLOB} ile eslesen gorsel yok -- "
                    "YOLOv8 kanali gercek cikarim yapamayacak.")

    zone_results = []
    for zone in zones:
        zone_results.append(run_zone(logger, zone, rng, speed, closure_ratio, images, image_counter,
                                     closure_source, blockage_radius_m, mask_suffix,
                                     emsr_rule, emsr_buffer_m, references))
        time.sleep(ZONE_STEP_DELAY_SEC / speed)

    all_assignments = [a for z in zone_results for a in z["assignments"]]
    comparison = compute_comparison(all_assignments)

    conflicts = [a["claimConflict"] for a in all_assignments if a.get("claimConflict")]
    blocked_conflicts = [c for c in conflicts if c.get("blocked")]

    summary = {
        "runId": run_id, "city": city, "cityLabel": DS.CITY_LABELS[city],
        "seed": seed,
        # Makale sayilari bu alana gore okunmali: "synthetic" = rastgele
        # kapanma, "model" = SegFormer'in deprem sonrasi goruntude gordugu hasar.
        "dataset": dataset,
        "datasetModule": DS.__name__,
        "closureSource": closure_source,
        "maskSuffix": mask_suffix if closure_source == "model" else None,
        "emsrRule": emsr_rule if closure_source == "emsr" else None,
        "emsrBufferM": emsr_buffer_m if closure_source == "emsr" else None,
        "zoneFilter": zone_filter or None,
        "closureRatio": closure_ratio if closure_source == "synthetic" else None,
        "blockageRadiusM": blockage_radius_m if closure_source == "model" else None,
        "generatedAt": time.time(),
        "zones": zone_results,
        "assignments": all_assignments,
        "comparison": comparison,
        "concurrency": {
            "attemptedConflicts": len(conflicts),
            "blockedByLock": len(blocked_conflicts),
            "allBlocked": len(conflicts) == len(blocked_conflicts),
        },
        "references": {
            "variants": REFERENCE_VARIANTS,
            "uTurnPenaltyMinValues": REFERENCE_T_U_VALUES,
            "reportedUTurnPenaltyMin": U_TURN_PENALTY_MIN,
            "check": reference_check(all_assignments),
        } if references else None,
        "debrisImagePool": [p.name for p in images],
    }
    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    _safe_print(f"\n--- {DS.CITY_LABELS[city]} OZET  [kapanma kaynagi: {closure_source.upper()}] ---")
    _safe_print(f"  Bolge: {len(zone_results)} | Atama: {len(all_assignments)}")
    _safe_print(f"  Mukerrer sevk denemesi: {len(conflicts)}, 409 ile engellenen: {len(blocked_conflicts)}")
    if comparison["rows"]:
        _safe_print(f"  QuakeMind toplam: {comparison['totalOurEngineTimeMin']} dk | "
                    f"Klasik (ulasabilenler): {comparison['totalNaiveTimeMinReachableOnly']} dk")
        _safe_print(f"  Kazanilan: {comparison['totalTimeSavedMin']} dk "
                    f"(ort. {comparison['avgTimeSavedMinPerTeam']} dk/ekip), "
                    f"naive hic ulasamadi: {comparison['naiveStuckCount']} ekip")
    if summary["references"]:
        chk = summary["references"]["check"]
        _safe_print(f"  R0 kontrolu (yeni simulator = naive_compare): {chk['identical']}/{chk['checked']}")
    _safe_print(f"  -> {run_dir}\n")
    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("city", choices=["hatay", "kahramanmaras", "all"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--speed", type=float, default=1.0, help="Zaman hizlandirma carpani")
    parser.add_argument("--closure-ratio", type=float, default=CLOSURE_RATIO,
                        help="Yalniz --closure-source synthetic icin")
    # GECICI VARSAYILAN: synthetic. Colab maskeleri (benchmark/colab/)
    # benchmark/data/model_masks/ altina konunca varsayilan "model" yapilacak;
    # o zamana kadar demo betikleri (hocaya_hazirla_*.bat) calismaya devam etsin.
    # Her kosu kaynagini summary.json'a ve ekrana yazar.
    parser.add_argument("--closure-source", choices=["synthetic", "model", "emsr"], default="synthetic",
                        help="synthetic = rastgele kapanma (rng.sample); "
                             "model = SegFormer hasar maskesi (benchmark/colab/); "
                             "emsr = Copernicus EMSR648 yer gercegi")
    parser.add_argument("--emsr-rule", choices=["strict", "medium", "loose"], default="loose",
                        help="Hangi EMSR dereceleri yolu kapatir (yalniz --closure-source emsr)")
    parser.add_argument("--emsr-buffer-m", type=float, default=8.0,
                        help="EMSR cizgisi <-> OSM kenari eslestirme tamponu (yalniz emsr)")
    parser.add_argument("--zones", nargs="*", default=None,
                        help="Yalniz bu bolgeleri kos (orn. --zones H-Z1 K-Z1)")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default="v2",
                        help="v2 = Senaryo v2 (8 ilce); drone = Help.NGO drone sahneleri (3 mahalle)")
    parser.add_argument("--mask-suffix", default="",
                        help="Model maskesi soneki (orn. =-z20 -> maskId H-D1-z20). "
                             "Tire ile basladigi icin --mask-suffix=-z20 bicimini kullanin.")
    parser.add_argument("--blockage-radius-m", type=float, default=25.0,
                        help="r_h -- yalniz --closure-source model icin (bkz. J-19, J-22)")
    # Varsayilan KAPALI: canli gosterim betikleri (hocaya_hazirla_*.bat) eskisi
    # kadar hizli kalsin. multi_seed.py bunu acik gecirir.
    parser.add_argument("--references", action="store_true",
                        help="Ara karsilastirma referanslarini da hesapla: R1 gorus mesafeli ajan, "
                             "R2 bilgi paylasan filo (makale Bolum 3.8, Tablo 16)")
    args = parser.parse_args()

    global DS
    DS = importlib.import_module(DATASETS[args.dataset])
    problems = DS.validate()
    if problems:
        _safe_print("VERI SETI TUTARSIZ -- kosu baslatilmadi:")
        for p in problems:
            _safe_print(f"  - {p}")
        return 1

    cities = ["hatay", "kahramanmaras"] if args.city == "all" else [args.city]
    for city in cities:
        run_id = args.run_id if args.city != "all" else (
            f"{args.run_id}-{city}" if args.run_id else None)
        run_city(city, run_id, args.seed, args.speed, args.closure_ratio,
                 args.closure_source, args.blockage_radius_m, args.mask_suffix, args.dataset,
                 args.emsr_rule, args.emsr_buffer_m, args.zones, args.references)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
