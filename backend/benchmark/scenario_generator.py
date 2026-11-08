"""4 senaryo JSON'u uretir: {kahramanmaras, hatay} x {orta, agir} hasar.

Girdi olarak data_collection.py ve copernicus_ground_truth.py'nin urettigi
dosyalari kullanir:
  benchmark/data/<region>.json                        (gercek toplanma alani/mahalle/altyapi)
  benchmark/data/<region>_copernicus_ground_truth.json (gercek hasarli yol/bina)

Mahalle secimi: data_collection.py 12 aday mahalle birakiyor (siralamasi
sadece toplanma alani sayisina gore, cogu zaten 1'de esit -- yani rastgele).
Burada gercek Copernicus hasar yogunluguna gore yeniden siralayip en
anlamli 3 mahalleyi seciyoruz (bkz. Hatay/Acikdere bulgusu: bazi adaylarin
yakininda hic gercek hasar yok).

Afetzede konumlari: mumkunse gercek Copernicus hasarli bina noktalarindan
orneklenir (max gercekcilik) -- mahallede yeterli hasarli bina yoksa
mahalle bbox'i icinde rastgele bir noktaya duser.

Siddet ekseni: hem "orta" hem "agir" senaryo AYNI 3 gercek mahalleyi
kullanir (karsilastirilabilirlik icin); fark, hangi damage_gra
derecelerinin "kapali yol" sayildigi -- orta: Destroyed+Damaged,
agir: Destroyed+Damaged+Possibly damaged.
"""

import json
import random
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = Path(__file__).resolve().parent / "data"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"

REGIONS = ["kahramanmaras", "hatay"]

# Siddet ekseni iki boyutlu: (a) mahalle merkezinden ne kadar uzaktaki
# gercek hasarli yollar "kapali" sayilsin (agir senaryoda daha genis bir
# alan etkilenmis kabul edilir), (b) hangi damage_gra dereceleri dahil
# edilsin. Sadece dereceyle ayirmak yetersiz kaldi -- yollarda "Possibly
# damaged" derecesi cok nadir (Kahramanmaras'ta hic yok), bu yuzden yaricap
# asil ayirt edici boyut.
SEVERITY_GRADES = {
    "orta": {"Destroyed", "Damaged"},
    "agir": {"Destroyed", "Damaged", "Possibly damaged"},
}
SEVERITY_RADIUS_DEG = {
    "orta": 0.015,  # ~1.6 km -- mahallenin hemen cevresi
    "agir": 0.035,  # ~3.9 km -- genisce bir sehir kesimi
}

MAHALLE_MATCH_RADIUS_DEG = max(SEVERITY_RADIUS_DEG.values())  # secim + tum siddet duzeyleri icin yeterli

VICTIMS_PER_MAHALLE = 6
TEAMS_PER_REGION = 6

DURUM_WEIGHTS = [("kritik", 0.15), ("yarali", 0.30), ("mahsur", 0.25), ("hafif", 0.30)]

NEED_TEMPLATES = {
    "kritik": [
        "Enkazın altındayım, hareket edemiyorum, lütfen yardım gönderin {mahalle}",
        "Ailemle birlikte enkaz altında kaldık, sesimizi duyan var mı {mahalle}",
        "Ağır yaralı var burada, kan kaybediyor, acil ekip lazım {mahalle}",
        "Bina üstümüze çöktü, arama kurtarma ekibi bekliyoruz {mahalle}",
    ],
    "yarali": [
        "Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var {mahalle}",
        "Yaralılar var evde, ambulans gelemedi henüz {mahalle}",
        "Düşen enkazdan yaralandım, kanama var {mahalle}",
        "Yaşlı annem yaralı, yürüyemiyor, sağlık ekibi lazım {mahalle}",
    ],
    "mahsur": [
        "Binada mahsur kaldık, kapı açılmıyor, çıkamıyoruz {mahalle}",
        "Merdivenler çöktü, üst katta mahsuruz {mahalle}",
        "Enkazın arasında sıkıştık ama bilinç açık, çıkış yolu bulamıyoruz {mahalle}",
    ],
    "hafif": [
        "Suyumuz bitti, temiz suya ihtiyacımız var {mahalle}",
        "Çadıra ihtiyacımız var, çok soğukta kaldık {mahalle}",
        "Yiyecek sıkıntısı var, birkaç gündür erzak gelmedi {mahalle}",
        "Evimiz hasar gördü ama içerideyiz, battaniye ve giysi lazım {mahalle}",
    ],
}

EKIP_ROLES = {
    "arama-kurtarma": ["İtfaiye Arama Kurtarma", "AKUT Saha Ekibi", "Jandarma Arama Kurtarma"],
    "lojistik-ilk-yardim": ["UMKE Sahra Sağlık", "Kızılay Lojistik Ekibi", "AFAD Lojistik Ekibi"],
}


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _score_mahalle(mahalle: dict, ground_truth: dict, radius_deg: float = MAHALLE_MATCH_RADIUS_DEG) -> dict:
    b = mahalle["bbox"]
    center_lat = (b["south"] + b["north"]) / 2
    center_lon = (b["west"] + b["east"]) / 2

    def _chebyshev(d):
        return max(abs(d["lat"] - center_lat), abs(d["lon"] - center_lon))

    nearby_roads = [
        {**d, "distDeg": _chebyshev(d)}
        for d in ground_truth["damagedRoadSegments"]
        if _chebyshev(d) < radius_deg
    ]
    nearby_bld = [
        {**d, "distDeg": _chebyshev(d)}
        for d in ground_truth["damagedBuildings"]
        if _chebyshev(d) < radius_deg
    ]
    return {
        **mahalle,
        "centerLat": center_lat,
        "centerLon": center_lon,
        "damageScore": len(nearby_roads) * 3 + len(nearby_bld),
        "nearbyDamagedRoads": nearby_roads,
        "nearbyDamagedBuildings": nearby_bld,
    }


def select_damage_grounded_mahalleler(region_data: dict, ground_truth: dict, n: int = 3) -> list[dict]:
    scored = [_score_mahalle(m, ground_truth) for m in region_data["mahalleler"]]
    scored.sort(key=lambda m: m["damageScore"], reverse=True)
    return scored[:n]


def _toplanma_alanlari_near(region_data: dict, center_lat: float, center_lon: float, radius_deg: float = 0.02) -> list[dict]:
    result = []
    for m in region_data["mahalleler"]:
        for t in m.get("toplanmaAlanlari", []):
            if abs(t["lat"] - center_lat) < radius_deg and abs(t["lon"] - center_lon) < radius_deg:
                result.append(t)
    return result


# pipeline_runner.py / live_simulation.py, bilinen konumlar icin
# fetch_satellite_area'ya radiusKm=0.4 + zoom=18 gonderiyor -- bu, dogal
# 8x8 tile penceresiyle ~1.1km x ~1.0km'lik SABIT bir alan uretiyor
# (olcup dogruladik: bkz. oturum notlari, EKMEKÇİ bounds). Afetzede/bina
# ornekleme yaricapi bundan GENIS olursa (eskiden 0.02deg ~2.2km idi),
# afetzedeler analiz edilen -- dolayisiyla rotalanabilir -- yol agi
# grafiginin TAMAMEN DISINA dusebiliyordu; ekipler o zaman gercekte
# ulasamadiklari bir noktaya "rota" cizmis gibi gorunuyordu (nearest_nodes
# en yakin dugume kilitliyor, gercek hedefe degil). 0.004deg (~450m)
# gercek kapsamanin guvenli bir ic parcasi.
KNOWN_LOCATION_SAMPLE_RADIUS_DEG = 0.004


def known_location_mahalleler(region_key: str, region_data: dict, ground_truth: dict) -> list[dict]:
    """known_locations.py'deki, kullanicinin kendi sisteminde dogruladigi
    gercek OAM goruntulerini mahalle-sekiline cevirir. Bunlar otomatik
    Wayback/Maxar secimine kiyasla bilinen-iyi cozunurluktedir (bkz. Kate-PD
    dogrulamasi + EKMEKÇİ'nin bu goruntuyle 6 gercek hasar bulmus olmasi)."""
    from known_locations import locations_for_region

    mahalleler = []
    for loc in locations_for_region(region_key):
        b = loc["bbox"]
        base = {
            "name": loc["mahalleName"],
            "ilce": region_data["label"],
            "bbox": b,
            "toplanmaAlanlari": [],
        }
        scored = _score_mahalle(base, ground_truth, radius_deg=KNOWN_LOCATION_SAMPLE_RADIUS_DEG)
        scored["toplanmaAlanlari"] = _toplanma_alanlari_near(region_data, scored["centerLat"], scored["centerLon"])
        scored["oamTitleMatch"] = loc["oamTitleMatch"]
        mahalleler.append(scored)
    return mahalleler


def _pick_durum(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for durum, weight in DURUM_WEIGHTS:
        acc += weight
        if r <= acc:
            return durum
    return DURUM_WEIGHTS[-1][0]


def _victim_location(mahalle: dict, rng: random.Random) -> tuple[float, float]:
    bld = mahalle["nearbyDamagedBuildings"]
    if bld:
        base = rng.choice(bld)
        jitter = 0.0008  # ~80m -- ayni binada birden fazla afetzede olmasin diye kucuk sapma
        return base["lat"] + rng.uniform(-jitter, jitter), base["lon"] + rng.uniform(-jitter, jitter)
    b = mahalle["bbox"]
    return rng.uniform(b["south"], b["north"]), rng.uniform(b["west"], b["east"])


def generate_afetzedeler(mahalleler: list[dict], rng: random.Random) -> list[dict]:
    afetzedeler = []
    for mahalle in mahalleler:
        for i in range(VICTIMS_PER_MAHALLE):
            durum = _pick_durum(rng)
            lat, lon = _victim_location(mahalle, rng)
            template = rng.choice(NEED_TEMPLATES[durum])
            need_text = template.format(mahalle=mahalle["name"].title())
            sos = durum in ("kritik", "mahsur") or (durum == "yarali" and rng.random() < 0.5)
            afetzedeler.append({
                "id": f"{mahalle['name']}-{i+1}",
                "mahalle": mahalle["name"],
                "ilce": mahalle["ilce"],
                "lat": lat,
                "lon": lon,
                "durum": durum,
                "needText": need_text,
                "sos": sos,
            })
    return afetzedeler


def generate_ekipler(region_data: dict, rng: random.Random) -> list[dict]:
    infra = region_data["infra"]
    bases = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "kind": "itfaiye"} for p in infra["itfaiye"]]
    bases += [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "kind": "hastane"} for p in infra["hastane"]]
    if not bases:
        # guvenlik agi: gercek itfaiye/hastane hic bulunamazsa bolge merkezini kullan
        b = region_data["bbox"]
        bases = [{"name": "Bolge merkezi", "lat": (b["south"] + b["north"]) / 2,
                  "lon": (b["west"] + b["east"]) / 2, "kind": "fallback"}]

    ekipler = []
    roles = list(EKIP_ROLES.keys())
    for i in range(TEAMS_PER_REGION):
        role = roles[i % len(roles)]
        unit = rng.choice(EKIP_ROLES[role])
        base = rng.choice(bases)
        ekipler.append({
            "id": f"ekip-{i+1}",
            "role": role,
            "unit": unit,
            "startName": base["name"],
            "startKind": base["kind"],
            "startLat": base["lat"],
            "startLon": base["lon"],
        })
    return ekipler


def build_closed_roads(mahalleler: list[dict], severity: str) -> list[dict]:
    allowed_grades = SEVERITY_GRADES[severity]
    radius = SEVERITY_RADIUS_DEG[severity]
    seen_names = set()
    closed = []
    for mahalle in mahalleler:
        for road in mahalle["nearbyDamagedRoads"]:
            if road["damageGrade"] not in allowed_grades or road["distDeg"] >= radius:
                continue
            key = (road["name"], round(road["lat"], 5), round(road["lon"], 5))
            if key in seen_names:
                continue
            seen_names.add(key)
            closed.append(road)
    return closed


def build_scenario(region_key: str, severity: str, rng: random.Random) -> dict:
    region_data = _load_json(DATA_DIR / f"{region_key}.json")
    ground_truth = _load_json(DATA_DIR / f"{region_key}_copernicus_ground_truth.json")

    known = known_location_mahalleler(region_key, region_data, ground_truth)
    if known:
        mahalleler = known
    else:
        mahalleler = select_damage_grounded_mahalleler(region_data, ground_truth, n=3)
    afetzedeler = generate_afetzedeler(mahalleler, rng)
    ekipler = generate_ekipler(region_data, rng)
    closed_roads = build_closed_roads(mahalleler, severity)

    return {
        "scenarioId": f"{region_key}_{severity}",
        "region": region_key,
        "regionLabel": region_data["label"],
        "severity": severity,
        "bbox": region_data["bbox"],
        "mahalleler": [
            {
                "name": m["name"], "ilce": m["ilce"], "bbox": m["bbox"],
                "centerLat": m["centerLat"], "centerLon": m["centerLon"],
                "damageScore": m["damageScore"],
                "toplanmaAlanlari": m["toplanmaAlanlari"],
                "oamTitleMatch": m.get("oamTitleMatch"),
            }
            for m in mahalleler
        ],
        "afetzedeler": afetzedeler,
        "ekipler": ekipler,
        "closedRoadGroundTruth": closed_roads,
        "meta": {
            "copernicusSource": ground_truth["source"],
            "victimCount": len(afetzedeler),
            "teamCount": len(ekipler),
            "closedRoadCount": len(closed_roads),
        },
    }


def main():
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    for region_key in REGIONS:
        for severity in SEVERITY_GRADES:
            rng = random.Random(f"{region_key}-{severity}-quakemind")
            scenario = build_scenario(region_key, severity, rng)
            out_path = SCENARIOS_DIR / f"{scenario['scenarioId']}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(scenario, f, ensure_ascii=False, indent=2)
            print(
                f"[{scenario['scenarioId']}] mahalle={[m['name'] for m in scenario['mahalleler']]} "
                f"afetzede={scenario['meta']['victimCount']} ekip={scenario['meta']['teamCount']} "
                f"kapali_yol={scenario['meta']['closedRoadCount']} -> {out_path}"
            )


if __name__ == "__main__":
    main()
