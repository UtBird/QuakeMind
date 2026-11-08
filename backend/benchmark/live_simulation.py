"""Canli simulasyon orkestratoru: bir bolgeyi (kahramanmaras|hatay) gercek
backend API'lerine karsi, INSAN-IZLENEBILIR bir hizda calistirir. `/command`
haritasi acikken (simulasyon modu ON) bu script calisirken SOS pin'lerinin
tek tek belirdigini, hasar overlay'inin cikmasini ve ekip isaretcilerinin
rotalari boyunca ilerlemesini CANLI izleyebilirsiniz.

pipeline_runner.py'den fark: hicbir API cagrisi mock degil (o da oyleydi)
ama burada adimlar arasina KASITLI bekleme konur (insan gozlemi icin), ve
her ekip-hedef atamasindan sonra POST /api/team/claim/{id}/route cagrilir
ki frontend rotayi gorup ekip isaretcisini interpolasyonla hareket ettirebilsin.

Kullanim:
  python benchmark/live_simulation.py kahramanmaras
  python benchmark/live_simulation.py hatay --speed 3   # 3x hizlandirilmis
"""

import argparse
import sys
import time
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_runner import (  # noqa: E402
    API_BASE, RunLogger, RUNS_DIR, DURUM_PRIORITY,
    load_scenario, pick_wayback_near_feb2023, run_road_damage_for_mahalleler,
    select_priority_targets, _haversine_m,
)

SOS_STEP_DELAY_SEC = 2.5   # her afetzede ihbari arasinda -- "art arda gelen ihbarlar" hissi
CLAIM_STEP_DELAY_SEC = 3.0  # her ekip atamasi arasinda


def _safe_print(text: str) -> None:
    """Windows konsolu (cp1254 vb.) bazi Unicode karakterlerde (orn. birlesik
    Turkce Ünlü + combining dot varyantlari) UnicodeEncodeError atabiliyor --
    bu SADECE konsol ciktisini etkilemeli, asla gercek bir API hatasi gibi
    islenmemeli (bkz. oturum notlari: daha once try/except'e karisip
    sahte 'sos_alert_error' loglamisti)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def run_nlp_and_sos_live(logger: RunLogger, afetzedeler: list[dict], speed: float) -> None:
    for v in afetzedeler:
        try:
            resp = requests.post(f"{API_BASE}/api/nlp/analyze", json={"text": v["needText"]}, timeout=180)
            result = resp.json()
            logger.log("nlp_analyze", victimId=v["id"], result=result)
        except Exception as e:
            logger.log("nlp_analyze_error", victimId=v["id"], error=str(e))

        if v.get("sos"):
            try:
                resp = requests.post(f"{API_BASE}/api/sos/alert", json={
                    "latitude": v["lat"], "longitude": v["lon"],
                    "message": v["needText"], "userId": v["id"],
                }, timeout=30)
                logger.log("sos_alert", victimId=v["id"], result=resp.json())
                _safe_print(f"  [SOS] {v['id']} ({v['durum']}) haritada belirdi -> {v['needText'][:50]}...")
            except Exception as e:
                logger.log("sos_alert_error", victimId=v["id"], error=str(e))

        time.sleep(SOS_STEP_DELAY_SEC / speed)


def run_claims_live(
    logger: RunLogger, severity: str, afetzedeler: list[dict], ekipler: list[dict],
    road_damage_results: dict, speed: float,
) -> list[dict]:
    targets = select_priority_targets(afetzedeler, n=len(ekipler))
    available_teams = list(ekipler)
    assignments = []

    for victim in targets:
        if not available_teams:
            break
        team = min(available_teams, key=lambda e: _haversine_m(victim["lat"], victim["lon"], e["startLat"], e["startLon"]))
        available_teams.remove(team)

        target_id = f"{severity}-{victim['id']}"
        claim_body = {"teamId": team["id"], "targetId": target_id,
                      "targetType": "sos" if victim.get("sos") else "report",
                      "lat": victim["lat"], "lon": victim["lon"]}
        try:
            resp = requests.post(f"{API_BASE}/api/team/claim", json=claim_body, timeout=15)
            logger.log("team_claim", teamId=team["id"], victimId=victim["id"], result=resp.json())
        except Exception as e:
            logger.log("team_claim_error", teamId=team["id"], victimId=victim["id"], error=str(e))
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
                if route_resp.status_code == 200:
                    route_result = route_resp.json()
                    # Rotayi claim'e ekle -- frontend bunu goruyor, ekip
                    # isaretcisi rota boyunca zaman-bazli interpolasyonla ilerlemeye baslar.
                    requests.post(f"{API_BASE}/api/team/claim/{target_id}/route", json={
                        "routeCoords": route_result["routeCoords"],
                        "distanceMeters": route_result["distanceMeters"],
                    }, timeout=15)
                    logger.log("team_route", teamId=team["id"], victimId=victim["id"],
                              distanceMeters=route_result["distanceMeters"])
                    _safe_print(f"  [EKİP] {team['id']} -> {victim['id']} hedefine yola çıktı "
                                f"({route_result['distanceMeters']:.0f}m, harita üzerinde ilerliyor)")
                else:
                    # Onceden sessizce yutuluyordu -- 200 disindaki durumlar (orn. safe_G
                    # olusturulamadigi icin 500) hicbir yere loglanmiyordu.
                    logger.log("team_route_failed", teamId=team["id"], victimId=victim["id"],
                              statusCode=route_resp.status_code, body=route_resp.text[:300])
            except Exception as e:
                logger.log("team_route_error", teamId=team["id"], victimId=victim["id"], error=str(e))

        assignments.append({
            "teamId": team["id"], "victimId": victim["id"], "mahalle": victim["mahalle"],
            "analysisId": rd["analysisId"] if rd else None,
            "distanceMeters": route_result.get("distanceMeters") if route_result else None,
            "routeCoords": route_result.get("routeCoords") if route_result else None,
        })

        time.sleep(CLAIM_STEP_DELAY_SEC / speed)

    return assignments


def run_region_live(region_key: str, run_id: str | None, speed: float) -> Path:
    run_id = run_id or f"{region_key}-live-{int(time.time())}"
    run_dir = RUNS_DIR / run_id
    logger = RunLogger(run_dir)

    print(f"\n=== CANLI SİMÜLASYON: {region_key} ===")
    print("/command sayfasını açıp 'SİMÜLASYON MODU'nu aktif edin, sonra bu ekranı izleyin.\n")

    orta = load_scenario(region_key, "orta")
    agir = load_scenario(region_key, "agir")
    mahalleler = orta["mahalleler"]

    print("[1/4] Uydu görüntüsü seçiliyor...")
    wayback = pick_wayback_near_feb2023()

    print(f"[2/4] {len(mahalleler)} mahalle için GERÇEK yol hasarı analizi (dakikalar sürer, biter bitmez haritada görünür)...")
    road_damage_results = run_road_damage_for_mahalleler(logger, region_key, mahalleler, orta["ekipler"], wayback)
    for name, rd in road_damage_results.items():
        print(f"  [HASAR] {name}: {len(rd['blockedRoadSegments'])} kapalı yol tespit edildi, haritada işaretlendi.")

    print("[3/4] Afetzede ihbarları sırayla gönderiliyor (SOS pin'leri tek tek haritada belirecek)...")
    scenario = agir  # gorsel olarak daha zengin (daha fazla kapali yol)
    run_nlp_and_sos_live(logger, scenario["afetzedeler"], speed)

    print("[4/4] Ekip görevlendirmeleri + gerçek GNN rotaları (ekip işaretçileri haritada ilerlemeye başlayacak)...")
    assignments = run_claims_live(logger, scenario["severity"], scenario["afetzedeler"], scenario["ekipler"], road_damage_results, speed)

    print(f"\nSimülasyon akışı tamamlandı -- {run_dir}")
    print("Ekipler rotalarında ilerlemeye devam edecek (harita üzerinde), tahmini varış sürelerine göre.")

    import json as _json
    summary = {
        "region": region_key, "runId": run_id, "wayback": wayback,
        "roadDamageResults": road_damage_results,
        "severities": {scenario["severity"]: {
            "victimCount": len(scenario["afetzedeler"]),
            "closedRoadGroundTruth": scenario["closedRoadGroundTruth"],
            "assignments": assignments,
        }},
    }
    with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
        _json.dump(summary, f, ensure_ascii=False, indent=2)

    return run_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("region", choices=["kahramanmaras", "hatay"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--speed", type=float, default=1.0, help="Zaman hizlandirma carpani (2 = 2x hizli)")
    args = parser.parse_args()
    run_region_live(args.region, args.run_id, args.speed)


if __name__ == "__main__":
    main()
