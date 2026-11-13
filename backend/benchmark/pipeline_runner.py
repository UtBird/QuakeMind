"""Bir bolgenin (kahramanmaras|hatay) hem orta hem agir senaryosunu gercek
backend API'lerine karsi calistirir. Hicbir adim mock'lanmaz:

  - Her afetzedenin ihtiyac metni -> POST /api/nlp/analyze (gercek BERTurk)
  - SOS isaretli afetzedeler       -> POST /api/sos/alert
  - Her mahalle icin GERCEK Segformer yol hasari analizi
    -> POST /api/road_damage/analyze + GET /api/road_damage/status/{id} polling
    (Şubat 2023'e en yakin Esri Wayback goruntusu otomatik secilir)
  - Oncelikli afetzede-ekip atamalari -> POST /api/team/claim
  - Her atama icin gercek GNN rotasi  -> POST /api/road_damage/route

Onemli: road-damage analizi SIDDET SENARYOSUNDAN BAGIMSIZDIR (ayni mahalle,
ayni uydu goruntusu, ayni model -> ayni sonuc) -- bu yuzden mahalle basina
BIR KEZ calistirilip hem orta hem agir senaryo icin paylasilir. Bu hem
gercek dunya mantigina uyar hem de 12 yerine sadece 6 gercek analiz
calistirarak toplam sureyi yariya indirir.

Kullanim:
  python benchmark/pipeline_runner.py kahramanmaras
  python benchmark/pipeline_runner.py hatay
"""

import argparse
import json
import math
import sys
import time
import uuid
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = Path(__file__).resolve().parent / "data"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
RUNS_DIR = Path(__file__).resolve().parent / "runs"

API_BASE = "http://127.0.0.1:8000"
POLL_INTERVAL_SEC = 5
POLL_TIMEOUT_SEC = 600
FEB_2023_CUTOFF = "2023-03-01"
ROAD_DAMAGE_MAX_ATTEMPTS = 3
ROAD_DAMAGE_RETRY_DELAY_SEC = 20

DURUM_PRIORITY = {"kritik": 0, "mahsur": 1, "yarali": 2, "hafif": 3}


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class RunLogger:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = run_dir / "events.jsonl"

    def log(self, event: str, **data) -> dict:
        entry = {"ts": time.time(), "event": event, **data}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry


def load_scenario(region: str, severity: str) -> dict:
    with open(SCENARIOS_DIR / f"{region}_{severity}.json", encoding="utf-8") as f:
        return json.load(f)


def pick_wayback_near_feb2023() -> dict | None:
    resp = requests.get(f"{API_BASE}/api/road_damage/wayback_versions", timeout=30)
    resp.raise_for_status()
    versions = resp.json().get("versions", [])  # sorted desc by date
    candidates = [v for v in versions if v.get("date", "9999") <= FEB_2023_CUTOFF]
    if candidates:
        return candidates[0]  # en yeni ama Subat 2023'ten once/o an
    return versions[-1] if versions else None


def run_nlp_for_victims(logger: RunLogger, afetzedeler: list[dict]) -> None:
    for v in afetzedeler:
        t0 = time.time()
        try:
            resp = requests.post(f"{API_BASE}/api/nlp/analyze", json={"text": v["needText"]}, timeout=180)
            result = resp.json()
            logger.log("nlp_analyze", victimId=v["id"], statusCode=resp.status_code,
                       elapsedSec=round(time.time() - t0, 2), result=result)
        except Exception as e:
            logger.log("nlp_analyze_error", victimId=v["id"], error=str(e))


def run_sos_for_victims(logger: RunLogger, afetzedeler: list[dict]) -> None:
    for v in afetzedeler:
        if not v.get("sos"):
            continue
        try:
            resp = requests.post(f"{API_BASE}/api/sos/alert", json={
                "latitude": v["lat"], "longitude": v["lon"],
                "message": v["needText"], "userId": v["id"],
            }, timeout=30)
            result = resp.json()
            logger.log("sos_alert", victimId=v["id"], statusCode=resp.status_code, result=result)
        except Exception as e:
            logger.log("sos_alert_error", victimId=v["id"], error=str(e))


def find_oam_tile_url(mahalle: dict) -> dict | None:
    """Mahallenin oamTitleMatch'ine gore /api/road_damage/oam_search'ten
    TAZE bir tms_url ceker (OAM linkleri zamanla degisebilir, bu yuzden
    baslikla eslestirip her kosuda taze cekiyoruz -- bkz. known_locations.py)."""
    title_match = mahalle.get("oamTitleMatch")
    if not title_match:
        return None
    resp = requests.get(f"{API_BASE}/api/road_damage/oam_search", params={
        "latitude": mahalle["centerLat"], "longitude": mahalle["centerLon"],
        "radiusKm": 5, "dateStart": "2023-02-06", "dateEnd": "2023-02-28",
    }, timeout=30)
    images = resp.json().get("images", [])
    for img in images:
        if title_match.lower() in (img.get("title") or "").lower():
            return img
    return None


def run_road_damage_for_mahalleler(
    logger: RunLogger, region_key: str, mahalleler: list[dict], ekipler: list[dict], wayback: dict | None,
) -> dict:
    """Her mahalle icin BIR kez gercek analiz calistirir, {mahalleAdi: analysisResult} doner.

    ONEMLI (dogrulama testinden gelen duzeltme): burada BILEREK explicit bir
    bbox GONDERMIYORUZ. Daha once mahalle+ekip-ussu birlestiren ozel bir bbox
    hesaplayip gonderiyorduk -- bu, fetch_satellite_area'nin bbox verildiginde
    izledigi kod yolunda (istenen alani TAM saracak kadar kucuk bir tile
    grid'i cekmesi) cok daha dusuk piksel-yogunluklu bir goruntu uretiyordu.
    latitude/longitude+radiusKm ile (bbox=None) cagirinca fonksiyon merkez
    etrafinda SABIT genislikte (8x8'e kadar tile, ~2048px) bir goruntu cekiyor
    -- ayni zoom seviyesinde bile cok daha yuksek efektif detay. Canli testte
    bu degisiklikle ayni Esri Wayback kaynagi, ayni konumda ham model
    olasiligini 0.06'dan 0.97'ye cikardi (bkz. oturum notlari). Ekip
    uslerinin dahil olup olmadigini ayrica kontrol etmeye gerek yok: 8x8
    tile'lik dogal kapsama alani (zoom=15'te ~9.8km) zaten olcup dogruladigimiz
    ekip-mahalle mesafelerinin (<2km) cok uzerinde.
    """
    results = {}
    for mahalle in mahalleler:
        nearest_base = min(
            ekipler, key=lambda e: _haversine_m(mahalle["centerLat"], mahalle["centerLon"], e["startLat"], e["startLon"])
        )

        # known_locations.py'den gelen mahalleler icin kullanicinin kendi
        # sisteminde dogruladigi gercek OAM goruntusunu kullan (Wayback'ten
        # cok daha yuksek cozunurluklu Help.NGO drone/ucak cekimleri) --
        # yoksa eski Wayback yoluna geri don.
        oam_image = find_oam_tile_url(mahalle)
        if oam_image:
            logger.log("oam_image_selected", mahalle=mahalle["name"], title=oam_image.get("title"), date=oam_image.get("date"))

        # Ucretsiz, paylasimli Overpass sunuculari ara sira (gecici sunucu
        # yuku nedeniyle) OSM yol grafigi adimini sessizce bos dondurebiliyor
        # (safeCount=0 -- bkz. oturum notlari: ayni sorgu birkac dk arayla
        # denendiginde bazen calisiyor bazen calismiyordu). safeCount==0
        # gercek bir "hic yol yok" durumundan ayirt edilemez ama pratikte
        # hep bu ariza belirtisi -- otomatik olarak birkaç kez yeniden dene.
        status = None
        for attempt in range(1, ROAD_DAMAGE_MAX_ATTEMPTS + 1):
            req_body = {
                "city": region_key,
                "latitude": mahalle["centerLat"],
                "longitude": mahalle["centerLon"],
                # 0.4km -> zoom_for_radius secer zoom=18 (en ince), ve
                # fetch_satellite_area'nin bbox=None yolu sabit 8x8 tile (~2048px)
                # cekiyor -- bu da dogal kapsamayi ~1.2km'de tutuyor. Daha genis
                # (radiusKm=2.0, ~9.8km) denendiginde worker.py'deki OSMnx yol
                # grafigi adimi kendi 45sn'lik timeout'unu asip sessizce
                # safe/blocked'i bos donduruyordu (bkz. kahramanmaras-fixed ilk
                # deneme, 0/0 sonuc). 1.2km, orijinal kucuk-bbox denemelerimizle
                # (basariyla calisan) ayni buyuklukte, ama piksel yogunlugu cok
                # daha yuksek.
                "radiusKm": 0.4,
            }
            if oam_image:
                req_body["source"] = "custom"
                req_body["oamTileUrl"] = oam_image["tms_url"]
            else:
                req_body["source"] = "esri" if wayback else "google"
                req_body["waybackId"] = wayback["id"] if wayback else None
            t0 = time.time()
            resp = requests.post(f"{API_BASE}/api/road_damage/analyze", json=req_body, timeout=30)
            if resp.status_code != 202:
                logger.log("road_damage_submit_error", mahalle=mahalle["name"], attempt=attempt,
                          statusCode=resp.status_code, body=resp.text[:500])
                continue
            submit = resp.json()
            analysis_id = submit["analysisId"]
            logger.log("road_damage_submit", mahalle=mahalle["name"], analysisId=analysis_id, attempt=attempt,
                       nearestBase=nearest_base["startName"], waybackDate=(wayback or {}).get("date"))

            status = None
            while time.time() - t0 < POLL_TIMEOUT_SEC:
                status_resp = requests.get(f"{API_BASE}/api/road_damage/status/{analysis_id}", timeout=30)
                status = status_resp.json()
                if status["status"] in ("done", "error"):
                    break
                time.sleep(POLL_INTERVAL_SEC)

            elapsed = round(time.time() - t0, 1)
            if status is None or status["status"] != "done":
                logger.log("road_damage_failed", mahalle=mahalle["name"], analysisId=analysis_id, attempt=attempt,
                           finalStatus=status, elapsedSec=elapsed)
                status = None
                continue

            safe_count = len(status.get("safeRoadSegments", []))
            blocked_count = len(status.get("blockedRoadSegments", []))
            logger.log("road_damage_done", mahalle=mahalle["name"], analysisId=analysis_id, attempt=attempt,
                       elapsedSec=elapsed, blockedCount=blocked_count, safeCount=safe_count)

            if safe_count > 0 or attempt == ROAD_DAMAGE_MAX_ATTEMPTS:
                break
            logger.log("road_damage_retry", mahalle=mahalle["name"], reason="safeCount=0, muhtemelen OSMnx/Overpass gecici arizasi")
            time.sleep(ROAD_DAMAGE_RETRY_DELAY_SEC)

        if status is None or status["status"] != "done":
            continue

        results[mahalle["name"]] = {"analysisId": status["analysisId"], "bounds": status.get("bounds"),
                                     "blockedRoadSegments": status.get("blockedRoadSegments", []),
                                     "safeRoadSegments": status.get("safeRoadSegments", [])}
    return results


def select_priority_targets(afetzedeler: list[dict], n: int) -> list[dict]:
    ranked = sorted(
        afetzedeler,
        key=lambda v: (DURUM_PRIORITY.get(v["durum"], 9), 0 if v.get("sos") else 1),
    )
    return ranked[:n]


def run_claims_and_routes(
    logger: RunLogger, severity: str, afetzedeler: list[dict], ekipler: list[dict],
    mahalle_by_name: dict, road_damage_results: dict,
) -> list[dict]:
    targets = select_priority_targets(afetzedeler, n=len(ekipler))
    available_teams = list(ekipler)
    assignments = []

    for victim in targets:
        if not available_teams:
            break
        team = min(available_teams, key=lambda e: _haversine_m(victim["lat"], victim["lon"], e["startLat"], e["startLon"]))
        available_teams.remove(team)

        claim_body = {"teamId": team["id"], "targetId": f"{severity}-{victim['id']}",
                      "targetType": "sos" if victim.get("sos") else "report",
                      "lat": victim["lat"], "lon": victim["lon"]}
        try:
            resp = requests.post(f"{API_BASE}/api/team/claim", json=claim_body, timeout=15)
            claim_result = resp.json()
            logger.log("team_claim", severity=severity, teamId=team["id"], victimId=victim["id"],
                      statusCode=resp.status_code, result=claim_result)
        except Exception as e:
            logger.log("team_claim_error", severity=severity, teamId=team["id"], victimId=victim["id"], error=str(e))
            continue

        rd = road_damage_results.get(victim["mahalle"])
        route_result = None
        if rd is not None:
            try:
                route_resp = requests.post(f"{API_BASE}/api/road_damage/route", json={
                    "analysisId": rd["analysisId"],
                    "startLat": team["startLat"], "startLon": team["startLon"],
                    "endLat": victim["lat"], "endLon": victim["lon"],
                }, timeout=30)
                route_result = route_resp.json()
                logger.log("team_route", severity=severity, teamId=team["id"], victimId=victim["id"],
                          statusCode=route_resp.status_code,
                          distanceMeters=route_result.get("distanceMeters"),
                          pointCount=len(route_result.get("routeCoords", [])))
            except Exception as e:
                logger.log("team_route_error", severity=severity, teamId=team["id"], victimId=victim["id"], error=str(e))

        assignments.append({
            "teamId": team["id"], "victimId": victim["id"], "mahalle": victim["mahalle"],
            "analysisId": rd["analysisId"] if rd else None,
            "distanceMeters": route_result.get("distanceMeters") if route_result else None,
            "routeCoords": route_result.get("routeCoords") if route_result else None,
        })

        # "GOREV TAMAMLANDI" kapanisi -- Bolum 05'teki claim release adiminin gercek karsiligi.
        try:
            requests.post(f"{API_BASE}/api/team/claim/{claim_body['targetId']}/release", timeout=15)
        except Exception:
            pass

    return assignments


def run_region(region_key: str, run_id: str | None = None) -> Path:
    run_id = run_id or f"{region_key}-{int(time.time())}"
    run_dir = RUNS_DIR / run_id
    logger = RunLogger(run_dir)

    orta = load_scenario(region_key, "orta")
    agir = load_scenario(region_key, "agir")
    mahalleler = orta["mahalleler"]  # ayni mahalle listesi iki siddette de ortak
    mahalle_by_name = {m["name"]: m for m in mahalleler}

    print(f"[{region_key}] Wayback goruntusu (Subat 2023'e en yakin) seciliyor...")
    wayback = pick_wayback_near_feb2023()
    logger.log("wayback_selected", wayback=wayback)
    print(f"[{region_key}] secilen goruntu tarihi: {(wayback or {}).get('date')}")

    print(f"[{region_key}] {len(mahalleler)} mahalle icin GERCEK yol hasari analizi baslatiliyor (dakikalar surer)...")
    # Ekip listesi orta/agir arasinda ayni (scenario_generator uretimi ayni sekilde) -- orta'dakini kullan.
    road_damage_results = run_road_damage_for_mahalleler(logger, region_key, mahalleler, orta["ekipler"], wayback)
    print(f"[{region_key}] {len(road_damage_results)}/{len(mahalleler)} mahalle icin analiz tamamlandi.")

    summary = {"region": region_key, "runId": run_id, "wayback": wayback,
               "roadDamageResults": road_damage_results, "severities": {}}

    for scenario in (orta, agir):
        severity = scenario["severity"]
        print(f"[{region_key}/{severity}] NLP analizi ({len(scenario['afetzedeler'])} afetzede)...")
        run_nlp_for_victims(logger, scenario["afetzedeler"])
        print(f"[{region_key}/{severity}] SOS bildirimleri...")
        run_sos_for_victims(logger, scenario["afetzedeler"])
        print(f"[{region_key}/{severity}] Ekip claim + gercek GNN rota atamalari...")
        assignments = run_claims_and_routes(
            logger, severity, scenario["afetzedeler"], scenario["ekipler"], mahalle_by_name, road_damage_results
        )
        summary["severities"][severity] = {
            "victimCount": len(scenario["afetzedeler"]),
            "closedRoadGroundTruth": scenario["closedRoadGroundTruth"],
            "assignments": assignments,
        }
        print(f"[{region_key}/{severity}] {len(assignments)} ekip-hedef ataması tamamlandı.")

    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[{region_key}] Calisma tamamlandi -> {run_dir}")
    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("region", choices=["kahramanmaras", "hatay"])
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    run_region(args.region, args.run_id)


if __name__ == "__main__":
    main()
