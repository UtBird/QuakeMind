"""Zengin, cok-sayfali senaryo orkestratoru (REVIZYON 2).

Akis diyagramlarindaki (afetzede: SOS/hasar-bildirimi/ihtiyac/yol-durumu +
backend NLP/SegFormer fuzyon/GNN rota; ekip: hedef kilitleme/mudahale)
BUTUN adimlarini gercek backend API'lerine karsi, tek bir sehir senaryosunda
bir araya getirir:

  - Gercek merkez nokta + POST /api/road_damage/simulate_closures: GERCEK
    OSM yol grafigi (yerel PBF cache'inden, Overpass'a hic gidilmeden),
    kenarlarin rastgele bir kismi "kapali" isaretlenir (kullanicinin
    onayladigi basitlestirme -- CV modelinin dogrulugu ayrica Kate-PD ile
    kanitlandi, burada asil gosterilen sey rota motorunun kendisi).
  - 5 ekip, gercek itfaiye/hastane konumlarindan (benchmark/data/<region>.json).
  - 5 aktif + 5 bekleyen ihbar (toplam 10): her biri gercek NLP siniflandirmasindan
    gecer, SOS olarak gonderilir; en yuksek oncelikli 5'i ekiplere atanir
    (aktif = EN_ROUTE), kalan 5'i bekler (acik).
  - Her atama icin gercek GNN/Dijkstra rotasi (POST /api/road_damage/route +
    attachTeamRoute) VE ayni rastgele kapanmayi "gercek" kabul eden bir
    naive-ajan karsilastirmasi (naive_baseline.py'nin mantigi yeniden
    kullanilir) -- "biz tespit edip soylemeseydik ne kadar kaybederdiniz" sayisi.
  - Birkac GERCEK YOLO enkaz tespiti (Kate-PD dogrulanmis ornek gorseller,
    /api/camera/analyze uzerinden -- mock degil, gercek model cikarimi).

Insan-izlenebilir hizda calisir (bkz. live_simulation.py) -- /command
sayfasini "SIMULASYON MODU" acik halde izleyerek adim adim gozlemlenebilir.

Kullanim:
  python benchmark/rich_simulation.py kahramanmaras
  python benchmark/rich_simulation.py hatay
  python benchmark/rich_simulation.py all --speed 2
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
from naive_baseline import AVERAGE_SPEED_KMH  # noqa: E402
from scenario_generator import NEED_TEMPLATES, EKIP_ROLES, _pick_durum  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

CITY_CONFIG = {
    "kahramanmaras": {
        "label": "Kahramanmaraş (merkez)", "center": (37.5756, 36.9207), "dataFile": "kahramanmaras.json",
        # apps/disaster_nlp/src/tr_locations.py::PROVINCE_TO_DISTRICTS ile ayni --
        # NLP'nin il/ilce sozluk-eslestirmesinin (+ Nominatim geocoding) GERCEKTEN
        # bir konum cikarabilmesi icin ihbar metinlerine gercek yer adi eklenir.
        "province": "Kahramanmaraş", "districts": ["Dulkadiroğlu", "Onikişubat", "Elbistan", "Pazarcık"],
    },
    "hatay": {
        "label": "Hatay / Antakya", "center": (36.194057, 36.146939), "dataFile": "hatay.json",
        "province": "Hatay", "districts": ["Antakya", "Defne", "Arsuz", "İskenderun"],
    },
}

RADIUS_KM = 3.0  # benchmark/warm_rich_sim_cache.py ile ayni -- cache hit garantisi icin
TEAMS_PER_CITY = 5
ACTIVE_PLUS_WAITING = 10  # 5 aktif (ekip atanmis) + 5 bekleyen
CLOSURE_RATIO = 0.18
DEBRIS_SAMPLE_IMAGES = ["kate_pd_0_image.png", "kate_pd_1_image.png"]  # Kate-PD dogrulanmis gercek hasar gorselleri

SOS_STEP_DELAY_SEC = 1.8
CLAIM_STEP_DELAY_SEC = 2.5
DEBRIS_STEP_DELAY_SEC = 1.5


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def load_region_data(city_key: str) -> dict:
    with open(DATA_DIR / CITY_CONFIG[city_key]["dataFile"], encoding="utf-8") as f:
        return json.load(f)


def select_team_bases(region_data: dict, center: tuple, radius_km: float, margin_frac: float = 0.95) -> list[dict]:
    """Analiz edilen grafın gercekten kapsadigi alanin icinde kalan gercek
    itfaiye/hastane noktalarini secer -- disaridaki bir nokta rota
    hesaplamasinda en yakin dugume yanlislikla "kilitlenir" (bkz. oturum
    notlari: afetzede-konumu icin daha once cozulen ayni sinif hata)."""
    clat, clon = center
    infra = region_data.get("infra", {})
    all_pts = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "kind": "itfaiye"} for p in infra.get("itfaiye", [])]
    all_pts += [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "kind": "hastane"} for p in infra.get("hastane", [])]
    for p in all_pts:
        p["distM"] = _haversine_m(clat, clon, p["lat"], p["lon"])
    all_pts.sort(key=lambda p: p["distM"])

    threshold_m = radius_km * 1000.0 * margin_frac
    inside = [p for p in all_pts if p["distM"] <= threshold_m]
    if inside:
        return inside
    if all_pts:
        return all_pts[:5]
    # guvenlik agi: gercek altyapi hic yoksa merkezi kullan
    return [{"name": "Bölge merkezi", "lat": clat, "lon": clon, "kind": "fallback", "distM": 0.0}]


def generate_teams(bases: list[dict], rng: random.Random, n: int = TEAMS_PER_CITY) -> list[dict]:
    roles = list(EKIP_ROLES.keys())
    teams = []
    # Ekipler farkli gercek itfaiye/hastane noktalarindan CIKSIN diye
    # IADESIZ (tekrarsiz) dagitilir -- eskiden her ekip icin bagimsiz
    # rng.choice(bases) yapiliyordu, bu da (ozellikle bases az sayidaysa,
    # orn. Hatay'da merkeze yakin sadece 3 gercek nokta var) birden fazla
    # ekibin AYNI binadan cikmasina yol aciyordu ("hepsi tek noktadan
    # dagiliyor" diye kullanicinin bildirdigi sorun). Havuz tukenirse
    # (ekip sayisi > farkli nokta sayisi) YENIDEN karistirilip devam edilir,
    # boylece hicbir zaman ust uste ayni nokta secilmez.
    base_pool: list[dict] = []
    for i in range(n):
        if not base_pool:
            base_pool = list(bases)
            rng.shuffle(base_pool)
        base = base_pool.pop()

        role = roles[i % len(roles)]
        unit = rng.choice(EKIP_ROLES[role])
        teams.append({
            "id": f"rich-ekip-{i+1}", "role": role, "unit": unit,
            "startName": base["name"], "startLat": base["lat"], "startLon": base["lon"],
        })
    return teams


def sample_point_in_bounds(bounds: dict, rng: random.Random, margin_frac: float = 0.12) -> tuple:
    lat_span = bounds["north"] - bounds["south"]
    lon_span = bounds["east"] - bounds["west"]
    lat = rng.uniform(bounds["south"] + lat_span * margin_frac, bounds["north"] - lat_span * margin_frac)
    lon = rng.uniform(bounds["west"] + lon_span * margin_frac, bounds["east"] - lon_span * margin_frac)
    return lat, lon


# Ihbarlar arasi minimum mesafe -- SADECE saf rastgele ornekleme kucuk N ile
# (10 nokta) sans eseri birbirine cok yakin cikabildigi (bazi ciftler
# ~600m'ye kadar dusuyordu, haritada "ust uste" gibi gorunuyordu) icin
# eklendi. Alanin KENDISI (bounds/margin_frac) DEGISMEZ -- sadece ayni alan
# icinde daha esit/seyrek bir dagilim zorlanir (kullanicinin istedigi: "cok
# genis tutma, mevcut sekil icinde kalsin").
MIN_INCIDENT_SEPARATION_M = 900
MAX_SEPARATION_ATTEMPTS = 60


def sample_spread_point(bounds: dict, rng: random.Random, existing_points: list[tuple]) -> tuple:
    candidate = sample_point_in_bounds(bounds, rng)
    for _ in range(MAX_SEPARATION_ATTEMPTS):
        if all(_haversine_m(candidate[0], candidate[1], elat, elon) >= MIN_INCIDENT_SEPARATION_M
               for elat, elon in existing_points):
            return candidate
        candidate = sample_point_in_bounds(bounds, rng)
    return candidate  # 60 denemede bulunamadiysa son adayla devam et (sonsuz donguye girme)


# Diyagramlarda tarif edilen "pil durumu" ve "haberlesme durumu" (mesh/BLE
# fallback) icin gercek bir donanim sensoru/BLE yiginimiz yok (bkz.
# AKIS_DIYAGRAM_KOD_ESLESTIRME_RAPORU.md, Bolum 01/06) -- rastgele yol
# kapanmasinda oldugu gibi TEMSILI deger uretilip gercek SOS pipeline'ina
# (POST /api/sos/alert) verilir, saklanir ve haritada/ihbar listesinde
# gosterilir. kritik/mahsur durumlar enkaz altinda GECEN SUREYI temsil
# ettigi icin pil daha dusuk araliktan secilir (telefon uzun suredir acik).
BATTERY_RANGE_BY_DURUM = {
    "kritik": (2, 30),
    "mahsur": (2, 30),
    "yarali": (15, 65),
    "hafif": (35, 100),
}
# Sehir sebekesi depremde kismen coktugu icin bir kismi hucresel/wifi yerine
# BLE mesh uzerinden (yakindaki telefonlar rolelerken) ya da hic ("offline",
# ekip sahaya varana kadar hicbir bildirim gitmez) ulasiyor.
COMMS_STATUS_WEIGHTS = [("online", 0.6), ("mesh", 0.28), ("offline", 0.12)]


def _pick_comms_status(rng: random.Random) -> str:
    r = rng.random()
    cumulative = 0.0
    for status, weight in COMMS_STATUS_WEIGHTS:
        cumulative += weight
        if r < cumulative:
            return status
    return COMMS_STATUS_WEIGHTS[-1][0]


def generate_incidents(bounds: dict, rng: random.Random, city_key: str, n: int = ACTIVE_PLUS_WAITING) -> list[dict]:
    config = CITY_CONFIG[city_key]
    incidents = []
    placed_points: list[tuple] = []
    for i in range(n):
        durum = _pick_durum(rng)
        lat, lon = sample_spread_point(bounds, rng, placed_points)
        placed_points.append((lat, lon))
        battery_lo, battery_hi = BATTERY_RANGE_BY_DURUM[durum]
        battery_percent = rng.randint(battery_lo, battery_hi)
        comms_status = _pick_comms_status(rng)
        template = rng.choice(NEED_TEMPLATES[durum])
        # NLP'nin metinden GERCEKTEN bir konum cikarabilmesi (NER + il/ilce
        # sozluk-eslestirmesi + Nominatim geocoding) icin somut bir yer adi
        # gerekiyor -- "bölgenizde" gibi genel bir kelimeyle hicbir entity
        # bulunamiyordu (konum: null). Gercek ilce adi NLP'nin haritada
        # kendi cikardigi (ve SOS'un kendi GPS'inden AYRI) bir nokta olarak
        # gorunmesini saglar.
        district = rng.choice(config["districts"])
        yer_adi = f"{config['province']} {district}"
        need_text = template.format(mahalle=yer_adi)
        sos = durum in ("kritik", "mahsur") or (durum == "yarali" and rng.random() < 0.5)
        incidents.append({
            "id": f"rich-ihbar-{i+1}", "lat": lat, "lon": lon,
            "durum": durum, "needText": need_text, "sos": sos,
            "batteryPercent": battery_percent, "commsStatus": comms_status,
        })
    return incidents


def select_priority_targets(incidents: list[dict], n: int) -> list[dict]:
    ranked = sorted(incidents, key=lambda v: (DURUM_PRIORITY.get(v["durum"], 9), 0 if v.get("sos") else 1))
    return ranked[:n]


def run_nlp_and_sos(logger: RunLogger, incidents: list[dict], speed: float) -> None:
    """Akis diyagramindaki 'ihtiyac-bildirimi -> NLP -> haritada isaretle'
    adiminin gercek karsiligi: her ihbar once BERTurk NLP'den gecer, sonra
    gercek koordinatlarla /api/sos/alert'e gonderilir (ekipler bunu haritada
    ve SOS sevk sayfasinda gorur)."""
    for inc in incidents:
        try:
            resp = requests.post(f"{API_BASE}/api/nlp/analyze", json={"text": inc["needText"]}, timeout=180)
            nlp_result = resp.json()
            logger.log("nlp_analyze", incidentId=inc["id"], result=nlp_result)
        except Exception as e:
            logger.log("nlp_analyze_error", incidentId=inc["id"], error=str(e))
            nlp_result = {}

        try:
            resp = requests.post(f"{API_BASE}/api/sos/alert", json={
                "latitude": inc["lat"], "longitude": inc["lon"],
                "message": inc["needText"], "userId": inc["id"],
                "batteryPercent": inc.get("batteryPercent"),
                "commsStatus": inc.get("commsStatus"),
            }, timeout=30)
            result = resp.json()
            inc["alertId"] = result.get("id")
            logger.log("sos_alert", incidentId=inc["id"], alertId=inc["alertId"], durum=inc["durum"], result=result)
            _safe_print(
                f"  [IHBAR] {inc['id']} ({inc['durum']}, kategori={nlp_result.get('kategori', '?')}, "
                f"pil=%{inc.get('batteryPercent')}, haberlesme={inc.get('commsStatus')}) haritada belirdi."
            )
        except Exception as e:
            logger.log("sos_alert_error", incidentId=inc["id"], error=str(e))

        time.sleep(SOS_STEP_DELAY_SEC / speed)


def assign_teams_and_route(
    logger: RunLogger, teams: list[dict], incidents: list[dict], analysis_id: str, speed: float,
) -> list[dict]:
    """5 en oncelikli ihbari 5 ekibe (en yakin ekip - acgozlu esleme) atar,
    gercek rota hesaplar ve haritaya (attachTeamRoute) yansitir -- akis
    diyagramindaki 'ekip hedef kilitler, digerleri gormez' adiminin
    gercek karsiligi (409 ile cakisma onlenir)."""
    targets = select_priority_targets(incidents, n=len(teams))
    available = list(teams)
    assignments = []

    for victim in targets:
        if not available:
            break
        team = min(available, key=lambda t: _haversine_m(victim["lat"], victim["lon"], t["startLat"], t["startLon"]))
        available.remove(team)

        target_id = victim.get("alertId") or victim["id"]
        claim_body = {"teamId": team["id"], "targetId": target_id, "targetType": "sos",
                      "lat": victim["lat"], "lon": victim["lon"]}
        try:
            resp = requests.post(f"{API_BASE}/api/team/claim", json=claim_body, timeout=15)
            logger.log("team_claim", teamId=team["id"], incidentId=victim["id"], statusCode=resp.status_code, result=resp.json())
        except Exception as e:
            logger.log("team_claim_error", teamId=team["id"], incidentId=victim["id"], error=str(e))
            continue

        route_result = None
        naive_result = None
        try:
            route_resp = requests.post(f"{API_BASE}/api/road_damage/route", json={
                "analysisId": analysis_id,
                "startLat": team["startLat"], "startLon": team["startLon"],
                "endLat": victim["lat"], "endLon": victim["lon"],
            }, timeout=30)
            if route_resp.status_code == 200:
                route_result = route_resp.json()

                # "Biz olmasaydik nereden giderdi" -- ayni baslangic/bitis icin
                # naif ajan simulasyonu HEMEN ARDINDAN cagirilir (aynen bizim
                # rotamiz gibi taze/senkron), boylece hem raporlama hem harita
                # (asagida TEK bir attachTeamRoute cagrisiyla) ayni veriyi kullanir.
                try:
                    naive_resp = requests.post(f"{API_BASE}/api/road_damage/naive_compare", json={
                        "analysisId": analysis_id,
                        "startLat": team["startLat"], "startLon": team["startLon"],
                        "endLat": victim["lat"], "endLon": victim["lon"],
                    }, timeout=60)
                    naive_resp.raise_for_status()
                    naive_result = naive_resp.json()
                except Exception as e:
                    logger.log("naive_compare_error", teamId=team["id"], incidentId=victim["id"], error=str(e))
                    naive_result = {"reachable": False, "distanceMeters": None, "discoveries": None, "routeCoords": None}

                requests.post(f"{API_BASE}/api/team/claim/{target_id}/route", json={
                    "routeCoords": route_result["routeCoords"],
                    "distanceMeters": route_result["distanceMeters"],
                    "naiveRouteCoords": naive_result.get("routeCoords") if naive_result.get("reachable") else None,
                    "naiveDistanceMeters": naive_result.get("distanceMeters"),
                    "naiveReachable": naive_result.get("reachable"),
                }, timeout=15)
                logger.log("team_route", teamId=team["id"], incidentId=victim["id"],
                          distanceMeters=route_result["distanceMeters"],
                          naiveDistanceMeters=naive_result.get("distanceMeters"),
                          naiveReachable=naive_result.get("reachable"))
                _safe_print(f"  [EKIP] {team['id']} ({team['unit']}) -> {victim['id']} icin yola cikti "
                            f"({route_result['distanceMeters']:.0f}m, harita uzerinde ilerliyor).")
            else:
                logger.log("team_route_failed", teamId=team["id"], incidentId=victim["id"],
                          statusCode=route_resp.status_code, body=route_resp.text[:300])
        except Exception as e:
            logger.log("team_route_error", teamId=team["id"], incidentId=victim["id"], error=str(e))

        try:
            requests.post(f"{API_BASE}/api/sos/alert/{target_id}/status", json={"status": "EN_ROUTE"}, timeout=15)
        except Exception:
            pass

        assignments.append({
            "teamId": team["id"], "teamUnit": team["unit"], "incidentId": victim["id"], "alertId": target_id,
            "durum": victim["durum"],
            "distanceMeters": route_result.get("distanceMeters") if route_result else None,
            "routeCoords": route_result.get("routeCoords") if route_result else None,
            "naiveDistanceMeters": naive_result.get("distanceMeters") if naive_result else None,
            "naiveReachable": naive_result.get("reachable") if naive_result else None,
            "naiveDiscoveries": naive_result.get("discoveries") if naive_result else None,
        })
        time.sleep(CLAIM_STEP_DELAY_SEC / speed)

    return assignments


def compute_naive_comparison(analysis_id: str, assignments: list[dict]) -> dict:
    """'Biz tespit edip soylemeseydik ne kadar kaybederdiniz' karsilastirmasi.

    Naif-ajan sonucu ARTIK burada AYRICA sorulmuyor -- assign_teams_and_route
    her atamadan hemen sonra /naive_compare'i zaten cagirip sonucu
    assignments listesine ekliyor (bkz. o fonksiyonun docstring'i: bunun
    NEDENI, iki tarafin da AYNI surecteki AYNI G/kapanma kumesini kullanmasi
    gerektigiydi -- surec-arasi tekrar sorgulama matematiksel olarak imkansiz
    sonuclara yol aciyordu). Burada sadece rapor icin ozetlenir.

    ONEMLI (kok neden bulunup duzeltildi, tarihce): bu hesaplama once AYRI bir
    Python surecinde (bu script), simulate_random_closures'i backend'le AYNI
    parametrelerle TEKRAR cagirarak yapiliyordu; surecler arasi FARKLI bir
    kapanma kumesi uretebildigi (nx.strongly_connected_components'in ic
    davranisi surece ozgu oldugu icin) gorulunce naif-ajan sorgusu backend'in
    KENDI SURECINE tasindi. Simdi ise assign_teams_and_route icinde, /route
    cagrisinin hemen ardindan, AYNI istek dongisu icinde calisiyor."""
    rows = []
    for a in assignments:
        if a.get("distanceMeters") is None:
            continue
        naive = {
            "reachable": a.get("naiveReachable"),
            "distanceMeters": a.get("naiveDistanceMeters"),
            "discoveries": a.get("naiveDiscoveries"),
        }
        our_distance = a["distanceMeters"]
        row = {
            "teamId": a["teamId"], "incidentId": a["incidentId"],
            "ourEngineDistanceMeters": round(our_distance, 1),
            "ourEngineTimeMin": round(our_distance / 1000 / AVERAGE_SPEED_KMH * 60, 1),
            "naiveDistanceMeters": round(naive["distanceMeters"], 1) if naive.get("reachable") else None,
            "naiveUnreachable": not naive.get("reachable"),
        }
        if naive.get("reachable"):
            row["naiveTimeMin"] = round(naive["distanceMeters"] / 1000 / AVERAGE_SPEED_KMH * 60, 1)
            row["distanceSavedMeters"] = round(naive["distanceMeters"] - our_distance, 1)
            row["timeSavedMin"] = round(row["naiveTimeMin"] - row["ourEngineTimeMin"], 1)
            row["naiveDiscoveries"] = naive["discoveries"]
        rows.append(row)

    reachable = [r for r in rows if not r["naiveUnreachable"]]
    naive_stuck = [r for r in rows if r["naiveUnreachable"]]
    total_saved = sum(r["timeSavedMin"] for r in reachable)
    return {
        "assignmentCount": len(rows),
        "reachableByNaiveCount": len(reachable),
        "naiveStuckCount": len(naive_stuck),
        "totalTimeSavedMin": round(total_saved, 1),
        "avgTimeSavedMinPerTeam": round(total_saved / len(reachable), 1) if reachable else None,
        "rows": rows,
    }


def post_debris_samples(logger: RunLogger, bounds: dict, rng: random.Random, speed: float) -> list[dict]:
    """Akis diyagramindaki 'goruntu -> YOLO -> haritada enkaz isaretle'
    adiminin gercek karsiligi: Kate-PD ile dogrulanmis (bkz. oturum notlari,
    %99.7 guven) GERCEK hasarli bina gorselleri, gercek konumlarla
    /api/camera/analyze'e gonderilir -- mock tespit degil, gercek YOLO
    cikarimi."""
    results = []
    for img_name in DEBRIS_SAMPLE_IMAGES:
        img_path = REPORTS_DIR / img_name
        if not img_path.exists():
            logger.log("debris_sample_missing", file=img_name)
            continue
        lat, lon = sample_point_in_bounds(bounds, rng, margin_frac=0.2)
        data_url = "data:image/png;base64," + base64.b64encode(img_path.read_bytes()).decode("ascii")
        try:
            resp = requests.post(f"{API_BASE}/api/camera/analyze", json={
                "modelType": "bina", "imageBase64": data_url, "latitude": lat, "longitude": lon,
            }, timeout=60)
            result = resp.json()
            logger.log("debris_detected", file=img_name, lat=lat, lon=lon,
                      status=result.get("status"), detectionCount=len(result.get("detections", [])),
                      debrisReportId=result.get("debrisReportId"))
            _safe_print(f"  [ENKAZ] {img_name}: {result.get('status')} "
                        f"({len(result.get('detections', []))} tespit) haritada isaretlendi.")
            results.append({"file": img_name, "lat": lat, "lon": lon, "result": result})
        except Exception as e:
            logger.log("debris_detect_error", file=img_name, error=str(e))
        time.sleep(DEBRIS_STEP_DELAY_SEC / speed)
    return results


def run_city(city_key: str, run_id: str | None, seed: int, speed: float, closure_ratio: float) -> Path:
    config = CITY_CONFIG[city_key]
    run_id = run_id or f"rich-{city_key}-{int(time.time())}"
    run_dir = RUNS_DIR / run_id
    logger = RunLogger(run_dir)
    rng = random.Random(seed)

    _safe_print(f"\n=== ZENGIN SENARYO: {config['label']} ===")
    _safe_print("/command sayfasini 'SIMULASYON MODU' acik halde izleyin.\n")

    region_data = load_region_data(city_key)
    clat, clon = config["center"]

    _safe_print("[1/5] Gercek OSM yol grafigi cekiliyor + rastgele kapanma uygulaniyor...")
    resp = requests.post(f"{API_BASE}/api/road_damage/simulate_closures", json={
        "latitude": clat, "longitude": clon, "radiusKm": RADIUS_KM,
        "closureRatio": closure_ratio, "seed": seed,
    }, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"simulate_closures basarisiz: {resp.status_code} {resp.text[:300]}")
    closure_data = resp.json()
    analysis_id = closure_data["analysisId"]
    bounds = closure_data["bounds"]
    blocked_segments = closure_data["blockedRoadSegments"]
    safe_segments = closure_data["safeRoadSegments"]
    logger.log("simulate_closures", analysisId=analysis_id, bounds=bounds,
              blockedCount=len(blocked_segments), safeCount=len(safe_segments))
    _safe_print(f"  Tamam -- {len(blocked_segments)} kapali, {len(safe_segments)} acik yol segmenti (analysisId={analysis_id}).")

    _safe_print(f"[2/5] {TEAMS_PER_CITY} ekip gercek itfaiye/hastane noktalarindan olusturuluyor...")
    bases = select_team_bases(region_data, (clat, clon), RADIUS_KM)
    teams = generate_teams(bases, rng, n=TEAMS_PER_CITY)
    for t in teams:
        _safe_print(f"  [EKIP] {t['id']} ({t['unit']}) -- baslangic: {t['startName']}")

    _safe_print(f"[3/5] {ACTIVE_PLUS_WAITING} ihbar olusturuluyor (NLP + SOS, sirayla haritada belirecek)...")
    incidents = generate_incidents(bounds, rng, city_key, n=ACTIVE_PLUS_WAITING)
    run_nlp_and_sos(logger, incidents, speed)

    _safe_print("[4/5] Oncelikli ihbarlara ekip atamasi + gercek GNN rotasi...")
    assignments = assign_teams_and_route(logger, teams, incidents, analysis_id, speed)
    waiting = [i for i in incidents if i["id"] not in {a["incidentId"] for a in assignments}]
    _safe_print(f"  {len(assignments)} aktif (ekip yolda), {len(waiting)} bekleyen ihbar.")

    _safe_print("[5/5] Naive-ajan karsilastirmasi + gercek YOLO enkaz tespitleri...")
    naive_comparison = compute_naive_comparison(analysis_id, assignments)
    debris = post_debris_samples(logger, bounds, rng, speed)

    summary = {
        "runId": run_id, "city": city_key, "label": config["label"], "seed": seed,
        "center": {"lat": clat, "lon": clon}, "radiusKm": RADIUS_KM, "closureRatio": closure_ratio,
        "analysisId": analysis_id, "bounds": bounds,
        "blockedSegmentCount": len(blocked_segments), "safeSegmentCount": len(safe_segments),
        "teams": teams,
        "incidents": [{"id": i["id"], "durum": i["durum"], "sos": i["sos"], "lat": i["lat"], "lon": i["lon"],
                       "needText": i["needText"], "alertId": i.get("alertId"),
                       "batteryPercent": i.get("batteryPercent"), "commsStatus": i.get("commsStatus"),
                       "status": "active" if i["id"] in {a["incidentId"] for a in assignments} else "waiting"}
                      for i in incidents],
        "assignments": assignments,
        "naiveComparison": naive_comparison,
        "debrisDetections": [{"file": d["file"], "lat": d["lat"], "lon": d["lon"],
                              "status": d["result"].get("status"),
                              "detectionCount": len(d["result"].get("detections", []))} for d in debris],
    }
    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    _safe_print(f"\n--- {config['label']} OZET ---")
    _safe_print(f"  Ekip: {len(teams)} | Ihbar: {len(incidents)} (aktif={len(assignments)}, bekleyen={len(waiting)})")
    _safe_print(f"  Kapali yol segmenti: {len(blocked_segments)} | Gercek YOLO enkaz tespiti: {len(debris)}")
    if naive_comparison.get("rows"):
        _safe_print(f"  Naive-ajan karsilastirmasi: {naive_comparison['reachableByNaiveCount']} ekip icin "
                    f"toplam {naive_comparison['totalTimeSavedMin']} dk kazanildi "
                    f"(ort. {naive_comparison['avgTimeSavedMinPerTeam']} dk/ekip), "
                    f"{naive_comparison['naiveStuckCount']} ekip icin naive yaklasim HEDEFE HIC ULASAMADI.")
        for r in naive_comparison["rows"]:
            if r["naiveUnreachable"]:
                _safe_print(f"    - {r['teamId']} -> {r['incidentId']}: naive AJAN SIKISTI, "
                            f"biz {r['ourEngineTimeMin']} dk'da ulastik.")
            else:
                _safe_print(f"    - {r['teamId']} -> {r['incidentId']}: naive {r['naiveTimeMin']} dk / "
                            f"{r['naiveDistanceMeters']:.0f}m, biz {r['ourEngineTimeMin']} dk / "
                            f"{r['ourEngineDistanceMeters']:.0f}m -> {r['timeSavedMin']} dk, "
                            f"{r['distanceSavedMeters']:.0f}m kazandirdik.")
    _safe_print(f"  -> {run_dir}\n")

    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("city", choices=["kahramanmaras", "hatay", "all"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--speed", type=float, default=1.0, help="Zaman hizlandirma carpani (2 = 2x hizli)")
    parser.add_argument("--closure-ratio", type=float, default=CLOSURE_RATIO)
    args = parser.parse_args()

    cities = ["kahramanmaras", "hatay"] if args.city == "all" else [args.city]
    for city_key in cities:
        run_city(city_key, args.run_id, args.seed, args.speed, args.closure_ratio)


if __name__ == "__main__":
    main()
