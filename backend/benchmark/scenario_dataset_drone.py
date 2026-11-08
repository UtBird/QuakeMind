"""Drone sahneleri senaryosu -- sabit veri seti (9 afetzede / 3 karargah / 9 ekip / 3 bolge).

Senaryo v2 (scenario_dataset.py) ile AYNI arayuzu sunar; orkestrator
`full_scenario.py --dataset drone` ile bu modulu kullanir. Bu modul SADECE
VERIDIR: hicbir HTTP cagrisi, hicbir hesaplama yapmaz.

NEDEN BU UC ALAN
  Kullanicinin modeli uygulama icinde fiilen test ettigi, bildigi yerler
  (16 Eylul 2026, ekran goruntuleriyle). Uc alanin ortak ozellikleri:
  - Help.NGO drone goruntusu, deprem sonrasi 2023-02-09, dogal cozunurluk
    3,4-3,9 cm/piksel (Maxar'dan ~10 kat ince). OpenAerialMap'te acik.
  - EMSR648 yer gercegi ucunde de var (AOI11 Hatay, AOI04 Kahramanmaras):
    biri AGIR hasarli (K-D1: binalarin %93'u, yollarin %30'u), ikisi HAFIF
    (H-D1: binalarin %4'u, yol yok; H-D2: hasar yok). Model hem kacirdigi
    hem de uydurdugu hasarla sinanir.
  - Yol grafi, ust bolgenin (H-Z1 / K-Z1) onbellekteki 3 km yaya grafinin
    sahne sinirina kirpilmis halidir (benchmark/warm_drone_scene_cache.py);
    Overpass'a gidilmez, Senaryo v2 ile AYNI OSM verisi kullanilir.

KAPANMALAR (full_scenario.py --closure-source; ayni afetzede/ekip/karargah)
  emsr      -- EMSR648 Grading hasarli yol cizgileri (/closures_from_emsr).
               EMSR'e gore H-D1 ve H-D2'de yol hasari YOK; K-D1'de 23 "Damaged".
  model     -- SegFormer bu sahnelerin drone goruntusunde calistirilir
               (benchmark/colab/make_model_masks.py --dataset drone), kapanmalar
               /closures_from_mask ile hasar maskesinden cikarilir. Sahne
               SABITLENMISTIR (sceneIds) -- ayni maskeye Maxar karismaz.
  synthetic -- rastgele kapanma (karsilastirma icin).

BILINEN KISIT
  full_scenario.MIN_INCIDENT_SEPARATION_M = 700 m; sahneler 450-720 m
  genisliginde oldugu icin bu ayrim saglanamaz ve orkestrator son adayla
  devam eder -- afetzedeler birbirine yakin duser.

VERI DURUSTLUGU
  - Afetzede kisilikleri, ihtiyac metinleri ve cihaz durumu alanlari senaryo
    kurgusudur (Senaryo v2 ile ayni statu). Ihtiyac metinlerindeki sokaklar
    ise sahnenin kendi OSM grafinda DOGRULANMIS gercek sokaklardir.
  - Karargahlar, sahneye disaridan giren gercek bir ana yolun graftaki
    dugumudur (coordSource: "grafta-ana-yol-girisi"); ilgili kurumun gercek
    konumu degildir.
"""

try:  # benchmark/ klasoru sys.path'teyse (full_scenario.py)
    from scenario_dataset import (  # noqa: F401
        CITY_LABELS, derive_gps_polling_sec, derive_power_mode,
    )
except ImportError:  # depo koku sys.path'teyse (make_model_masks.py)
    from benchmark.scenario_dataset import (  # noqa: F401
        CITY_LABELS, derive_gps_polling_sec, derive_power_mode,
    )

# --------------------------------------------------------------------------
# Bolgeler (Help.NGO drone sahneleri)
# --------------------------------------------------------------------------
# bbox       : [bati, guney, dogu, kuzey] -- sahnenin OpenAerialMap kapsama kutusu.
#              Hem hasar maskesi hem yol grafi bu kutu uzerinde uretilir.
# sceneIds   : OpenAerialMap goruntu kimligi (sabitlenmis).
# sceneGsdM  : sahnenin dogal yer ornekleme mesafesi (metre/piksel).
# nativeZoom : sahnenin dogal cozunurlugune karsilik gelen karo zoom'u;
#              ustunde karo sunucusu yalnizca buyutme yapar.
# parentZoneId : yol grafinin kirpildigi Senaryo v2 bolgesi.
# emsrPackage  : yer gercegi (EMSR648 Grading) paketi -- --closure-source emsr.
ZONES = [
    {
        "id": "H-D1", "city": "hatay", "label": "Defne - Elektrik Mah.",
        "center": (36.197694, 36.149321), "radiusKm": 0.33,
        "bbox": [36.146753, 36.195466, 36.15189, 36.199922],
        "sceneIds": ["63eb78a0ca43600005f4d920"],
        "sceneTitle": "Hatay - Defne - Elektrik Mah.",
        "sceneProvider": "Help.NGO", "sceneDate": "2023-02-09",
        "sceneGsdM": 0.0341, "nativeZoom": 22,
        "parentZoneId": "H-Z1",
        "emsrPackage": "EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip",
    },
    {
        "id": "H-D2", "city": "hatay", "label": "Defne - Turunclu / Akdeniz / Armutlu Mah.",
        "center": (36.194057, 36.146939), "radiusKm": 0.39,
        "bbox": [36.142957, 36.192684, 36.15092, 36.19543],
        "sceneIds": ["63eb829fca43600005f4d927"],
        "sceneTitle": "Hatay - Turinclu - Akdeniz Mah - Armutlu Mah.",
        "sceneProvider": "Help.NGO, Portugese GRU", "sceneDate": "2023-02-09",
        "sceneGsdM": 0.0386, "nativeZoom": 22,
        "parentZoneId": "H-Z1",
        "emsrPackage": "EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip",
    },
    {
        "id": "K-D1", "city": "kahramanmaras", "label": "Merkez - 12 Subat Stadyumu cevresi",
        "center": (37.575622, 36.920716), "radiusKm": 0.40,
        "bbox": [36.917486, 37.573071, 36.923946, 37.578173],
        "sceneIds": ["63eb7f38ca43600005f4d924"],
        "sceneTitle": "12 Subat Stadyumu, Merkez/Kahramanmaras",
        "sceneProvider": "Help.NGO", "sceneDate": "2023-02-09",
        "sceneGsdM": 0.0376, "nativeZoom": 22,
        "parentZoneId": "K-Z1",
        "emsrPackage": "EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1_vector.zip",
    },
]
ZONES_BY_ID = {z["id"]: z for z in ZONES}

# --------------------------------------------------------------------------
# Karargahlar (3) -- sahneye disaridan giren ana yolun graftaki dugumu
# --------------------------------------------------------------------------
HEADQUARTERS = [
    {"id": "HQ-HD1", "zoneId": "H-D1", "name": "Cekmece Caddesi Toplanma Noktasi",
     "lat": 36.199281, "lon": 36.149453, "coordSource": "grafta-ana-yol-girisi",
     "coordNote": "Sahnenin kuzey kenari, Cekmece Caddesi (secondary)"},
    {"id": "HQ-HD2", "zoneId": "H-D2", "name": "Samandag Bulvari Mudahale Noktasi",
     "lat": 36.194995, "lon": 36.143351, "coordSource": "grafta-ana-yol-girisi",
     "coordNote": "Sahnenin bati kenari, Samandag Bulvari (trunk) -- Defne'ye giren ana arter. "
                  "Sahne sinirindaki kirpilma noktasi cikmaz dugum oldugu icin 42 m icerideki "
                  "kavsaga alindi (eski: 36.194746, 36.142999)"},
    {"id": "HQ-KD1", "zoneId": "K-D1", "name": "Ali Sezal Bulvari Koordinasyon Noktasi",
     "lat": 37.573811, "lon": 36.920129, "coordSource": "grafta-ana-yol-girisi",
     "coordNote": "Sahnenin guney kenari, Ali Sezal Bulvari (secondary)"},
]
HEADQUARTERS_BY_ID = {h["id"]: h for h in HEADQUARTERS}

# --------------------------------------------------------------------------
# Ekipler (9) -- bolge basina bir arama-kurtarma, bir medikal, bir lojistik
# --------------------------------------------------------------------------
# Kimlikler rolu tasir (-AK / -MED / -LOJ): harita rolu renk olarak buradan okur.
TEAMS = [
    {"id": "HD1-AK1", "city": "hatay", "zoneId": "H-D1", "hqId": "HQ-HD1", "role": "arama-kurtarma", "unit": "AKUT Saha Ekibi"},
    {"id": "HD1-MED1", "city": "hatay", "zoneId": "H-D1", "hqId": "HQ-HD1", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "HD1-LOJ1", "city": "hatay", "zoneId": "H-D1", "hqId": "HQ-HD1", "role": "lojistik", "unit": "Kizilay Lojistik Ekibi"},
    {"id": "HD2-AK1", "city": "hatay", "zoneId": "H-D2", "hqId": "HQ-HD2", "role": "arama-kurtarma", "unit": "Itfaiye Arama Kurtarma"},
    {"id": "HD2-MED1", "city": "hatay", "zoneId": "H-D2", "hqId": "HQ-HD2", "role": "medikal", "unit": "112 Acil Saglik"},
    {"id": "HD2-LOJ1", "city": "hatay", "zoneId": "H-D2", "hqId": "HQ-HD2", "role": "lojistik", "unit": "AFAD Lojistik Ekibi"},
    {"id": "KD1-AK1", "city": "kahramanmaras", "zoneId": "K-D1", "hqId": "HQ-KD1", "role": "arama-kurtarma", "unit": "Jandarma Arama Kurtarma"},
    {"id": "KD1-MED1", "city": "kahramanmaras", "zoneId": "K-D1", "hqId": "HQ-KD1", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "KD1-LOJ1", "city": "kahramanmaras", "zoneId": "K-D1", "hqId": "HQ-KD1", "role": "lojistik", "unit": "Kizilay Lojistik Ekibi"},
]

# --------------------------------------------------------------------------
# Afetzede profilleri (9) -- bolge basina bir yolo / bir nlp / bir sos
# --------------------------------------------------------------------------
# Alan anlamlari scenario_dataset.VICTIMS ile aynidir. Ihtiyac metinlerindeki
# sokaklar sahnenin kirpilmis OSM grafinda dogrulandi (16 Eylul 2026).
VICTIMS = [
    # ================= H-D1 Defne - Elektrik Mah. =================
    {
        "id": "HD1-01", "name": "Kemal Yilmaz", "city": "hatay", "zoneId": "H-D1",
        "locationLabel": "Defne, Kugulu Sk.", "channel": "yolo",
        "batteryPercent": 58, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "damageNote": "4 katli binanin on cephesi sokaga cokmus",
    },
    {
        "id": "HD1-02", "name": "Zehra Kilic", "city": "hatay", "zoneId": "H-D1",
        "locationLabel": "Defne, Oluk Sk.", "channel": "nlp",
        "batteryPercent": 34, "commsStatus": "online",
        "durum": "yarali", "preferredRole": "medikal",
        "needText": "Hatay Defne Elektrik Mahallesi Oluk Sokak'ta bacagi kirik yasli bir amca var, ambulans ve sedye lazim!",
    },
    {
        "id": "HD1-03", "name": "Murat Aksoy", "city": "hatay", "zoneId": "H-D1",
        "locationLabel": "Defne, Lale Sk.", "channel": "sos",
        "batteryPercent": 12, "commsStatus": "offline",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
    },
    # ================= H-D2 Defne - Turunclu / Akdeniz / Armutlu =================
    {
        "id": "HD2-01", "name": "Leyla Sahin", "city": "hatay", "zoneId": "H-D2",
        "locationLabel": "Defne, Samandag Blv.", "channel": "yolo",
        "batteryPercent": 71, "commsStatus": "online",
        "durum": "yarali", "preferredRole": "medikal",
        "damageNote": "Bulvar kenarinda kismi cokme, yaralilar var",
    },
    {
        "id": "HD2-02", "name": "Hasan Ozturk", "city": "hatay", "zoneId": "H-D2",
        "locationLabel": "Defne, Sukru Guclu Blv.", "channel": "nlp",
        "batteryPercent": 46, "commsStatus": "mesh",
        "durum": "hafif", "preferredRole": "lojistik",
        "needText": "Hatay Defne Sukru Guclu Bulvari uzerindeki parkta 30 kisi var, battaniye, su ve bebek mamasi gerekiyor.",
    },
    {
        "id": "HD2-03", "name": "Sibel Arslan", "city": "hatay", "zoneId": "H-D2",
        "locationLabel": "Defne, Ataturk 1 Cad.", "channel": "sos",
        "batteryPercent": 19, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
    },
    # ================= K-D1 Merkez - 12 Subat Stadyumu cevresi =================
    {
        "id": "KD1-01", "name": "Ahmet Celik", "city": "kahramanmaras", "zoneId": "K-D1",
        "locationLabel": "Merkez, Malik Ejder Cad.", "channel": "yolo",
        "batteryPercent": 40, "commsStatus": "mesh",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        "damageNote": "Cok katli bina tamamen cokmus, enkaz caddeyi kapatmis",
    },
    {
        "id": "KD1-02", "name": "Ayse Kurt", "city": "kahramanmaras", "zoneId": "K-D1",
        "locationLabel": "Merkez, Kuddusi Baba Blv.", "channel": "nlp",
        "batteryPercent": 27, "commsStatus": "online",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "needText": "Kahramanmaras merkez Kuddusi Baba Bulvari'nda enkaz altindan ses geliyor, en az iki kisi var, arama kurtarma acil!",
    },
    {
        "id": "KD1-03", "name": "Ibrahim Tas", "city": "kahramanmaras", "zoneId": "K-D1",
        "locationLabel": "Merkez, Onbasi Osman Cad.", "channel": "sos",
        "batteryPercent": 8, "commsStatus": "offline",
        "durum": "yarali", "preferredRole": "lojistik",
    },
]


# --------------------------------------------------------------------------
# Yardimcilar (scenario_dataset ile ayni imzalar)
# --------------------------------------------------------------------------
def zones_for_city(city: str) -> list[dict]:
    return [z for z in ZONES if z["city"] == city]


def victims_in_zone(zone_id: str) -> list[dict]:
    return [v for v in VICTIMS if v["zoneId"] == zone_id]


def teams_in_zone(zone_id: str) -> list[dict]:
    return [t for t in TEAMS if t["zoneId"] == zone_id]


def headquarters_in_zone(zone_id: str) -> list[dict]:
    return [h for h in HEADQUARTERS if h["zoneId"] == zone_id]


def validate() -> list[str]:
    problems = []
    for z in ZONES:
        w, s, e, n = z["bbox"]
        if not (w < e and s < n):
            problems.append(f"{z['id']}: gecersiz bbox")
        lat, lon = z["center"]
        if not (s <= lat <= n and w <= lon <= e):
            problems.append(f"{z['id']}: merkez bbox disinda")
        if not z.get("sceneIds"):
            problems.append(f"{z['id']}: sahne sabitlenmemis (sceneIds)")
        if z["city"] not in CITY_LABELS:
            problems.append(f"{z['id']}: bilinmeyen sehir {z['city']}")

    for h in HEADQUARTERS:
        z = ZONES_BY_ID.get(h["zoneId"])
        if z is None:
            problems.append(f"{h['id']}: bilinmeyen zoneId {h['zoneId']}")
            continue
        w, s, e, n = z["bbox"]
        if not (s <= h["lat"] <= n and w <= h["lon"] <= e):
            problems.append(f"{h['id']}: karargah sahne disinda")

    for v in VICTIMS:
        z = ZONES_BY_ID.get(v["zoneId"])
        if z is None:
            problems.append(f"{v['id']}: bilinmeyen zoneId {v['zoneId']}")
        elif z["city"] != v["city"]:
            problems.append(f"{v['id']}: sehir/bolge uyusmazligi")
        if v["channel"] not in ("yolo", "nlp", "sos"):
            problems.append(f"{v['id']}: gecersiz kanal {v['channel']}")
        if v["channel"] == "nlp" and not v.get("needText"):
            problems.append(f"{v['id']}: nlp kanali icin needText yok")

    for t in TEAMS:
        hq = HEADQUARTERS_BY_ID.get(t["hqId"])
        if hq is None:
            problems.append(f"{t['id']}: bilinmeyen hqId {t['hqId']}")
        elif hq["zoneId"] != t["zoneId"]:
            problems.append(f"{t['id']}: karargah bolgesi ekip bolgesiyle uyusmuyor")

    for z in ZONES:
        n_v, n_t = len(victims_in_zone(z["id"])), len(teams_in_zone(z["id"]))
        if n_v != n_t:
            problems.append(f"{z['id']}: {n_v} afetzede ama {n_t} ekip (1:1 olmali)")
        if n_v and not headquarters_in_zone(z["id"]):
            problems.append(f"{z['id']}: afetzede var ama karargah yok")
        channels = sorted(v["channel"] for v in victims_in_zone(z["id"]))
        if channels != ["nlp", "sos", "yolo"]:
            problems.append(f"{z['id']}: kanal dagilimi {channels} (bolge basina 1/1/1 bekleniyor)")
    return problems


if __name__ == "__main__":
    issues = validate()
    if issues:
        print("VERI SETI SORUNLARI:")
        for i in issues:
            print("  -", i)
        raise SystemExit(1)
    print(f"OK -- {len(ZONES)} bolge, {len(HEADQUARTERS)} karargah, "
          f"{len(TEAMS)} ekip, {len(VICTIMS)} afetzede; tutarli.")
    for z in ZONES:
        print(f"  {z['id']:5s} {z['label']:44s} {100 * z['sceneGsdM']:.1f} cm/px  "
              f"afetzede={len(victims_in_zone(z['id']))} ekip={len(teams_in_zone(z['id']))}")
