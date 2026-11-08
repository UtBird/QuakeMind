"""Senaryo v2 -- sabit veri seti (18 afetzede / 11 karargah / 18 ekip / 8 bolge).

Bu modul SADECE VERIDIR: hicbir HTTP cagrisi, hicbir hesaplama yapmaz.
Orkestrator (full_scenario.py), on-isitma script'i (warm_scenario_v2_cache.py)
ve raporlayici (scenario_v2_report.py) ayni tanimlari buradan okur -- boylece
"raporda yazan sey ile kosulan sey" arasinda tek bir dogruluk kaynagi olur.

TASARIM KISITI (neden "bolge" var):
  Senaryo il genelini kapsiyor (Iskenderun Antakya'ya 44 km, Elbistan Maras'a
  74 km). Rota motoru tek bir gercek OSM yol grafigi uzerinde
  calisiyor ve 3 km yaricapli bir graf bile ~20.600 dugum / ~49.700 kenar.
  Tum ili tek grafa almak (~7.000 km^2) milyonlarca kenar demek -- ne
  on-isitilabilir ne de interaktif rota hesaplanabilir. Bu yuzden her ilce
  KENDI grafini, KENDI rastgele kapanma setini ve KENDI analysisId'sini alir;
  ekipler kendi bolgeleri icinde rota alir. GET /api/road_damage/recent zaten
  liste dondurdugu icin harita hepsini ayni anda gosterir.

VERI DURUSTLUGU:
  - Yol kapanmalari TEMSILI/rastgeledir (kullanicinin acik karari; SegFormer
    bu kosuda calistirilmaz, dogrulugu ayrica Kate-PD ile kanitlandi).
  - Cihaz durumu alanlari (pil, guc modu, siren, haberlesme) de TEMSILIDIR --
    gercek bir donanim sensoru/BLE yiginimiz yok. Ama gercek SOS pipeline'indan
    gecer, saklanir ve haritada gosterilir.
  - Rota, graf, mesafeler, model cikarimlari (YOLOv8 + BERTurk) ve naive
    karsilastirma GERCEKTEN hesaplanir.
"""

# --------------------------------------------------------------------------
# Bolgeler
# --------------------------------------------------------------------------
# graphSource:
#   "mevcut-cache" -> benchmark/warm_rich_sim_cache.py ile zaten isitilmis,
#                     yeniden cikarim gerekmez (ayni merkez + ayni yaricap).
#   "yeni"         -> warm_scenario_v2_cache.py ile PBF'ten cikarilacak.
# emsrPackage (varsa): bolgenin EMSR648 Grading yer gercegi paketi --
#   --closure-source emsr ile kapanmalar buradan gelir. Paketi olmayan
#   bolgelerde EMSR'in yol yer gercegi YOK: H-Z2/H-Z4/H-Z5 icin hic AOI yok;
#   K-Z3 Pazarcik (AOI08) yol katmaninin tamami "Not Analysed". H-Z3
#   Kirikhan icin yalniz PRODUCT gecisi var (MONIT01 yayinlanmamis).
RADIUS_KM = 3.0

ZONES = [
    # --- HATAY ---
    {
        "id": "H-Z1", "city": "hatay", "label": "Antakya - Defne",
        "center": (36.194057, 36.146939), "radiusKm": RADIUS_KM, "graphSource": "mevcut-cache",
        "emsrPackage": "EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip",
    },
    {
        "id": "H-Z2", "city": "hatay", "label": "Iskenderun",
        "center": (36.5875, 36.1700), "radiusKm": RADIUS_KM, "graphSource": "yeni",
    },
    {
        "id": "H-Z3", "city": "hatay", "label": "Kirikhan",
        "center": (36.4986, 36.3606), "radiusKm": RADIUS_KM, "graphSource": "yeni",
        "emsrPackage": "EMSR648_AOI18_GRA_PRODUCT_r1_RTP01_v1_vector.zip",
    },
    {
        "id": "H-Z4", "city": "hatay", "label": "Samandag",
        "center": (36.0850, 35.9800), "radiusKm": RADIUS_KM, "graphSource": "yeni",
    },
    {
        "id": "H-Z5", "city": "hatay", "label": "Belen",
        "center": (36.4900, 36.2000), "radiusKm": RADIUS_KM, "graphSource": "yeni",
    },
    # --- KAHRAMANMARAS ---
    {
        "id": "K-Z1", "city": "kahramanmaras", "label": "Merkez (Onikisubat - Dulkadiroglu)",
        "center": (37.5756, 36.9207), "radiusKm": RADIUS_KM, "graphSource": "mevcut-cache",
        "emsrPackage": "EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1_vector.zip",
    },
    {
        "id": "K-Z2", "city": "kahramanmaras", "label": "Elbistan",
        "center": (38.2050, 37.1950), "radiusKm": RADIUS_KM, "graphSource": "yeni",
        "emsrPackage": "EMSR648_AOI20_GRA_MONIT01_r1_RTP01_v1_vector.zip",
    },
    {
        "id": "K-Z3", "city": "kahramanmaras", "label": "Pazarcik",
        "center": (37.4890, 37.3000), "radiusKm": RADIUS_KM, "graphSource": "yeni",
    },
    # K-Z4 Goksun SENARYODAN CIKARILDI (16 Eylul 2026, kullanici karari):
    # bolge icin HIC deprem sonrasi goruntu yok -- OpenAerialMap'te 2023-02-06
    # ile 2023-06-30 arasinda Maxar dahil tek bir sahne bulunamadi (bkz.
    # EKSIKLER_VE_SORUNLAR.md J-24). Kapanmalar artik modelden uretilecegi
    # icin goruntusuz bir bolge ya sentetik kalacakti ya da hic kapanma
    # uretmeyecekti; ikisi de kabul edilmedi. Afetzedesi ve ekibi K-Z1'e
    # tasindi (relocatedFrom ile kayitli), il basina 3/3/3 kanal dagilimi
    # ve 18 afetzede korunuyor.
]

ZONES_BY_ID = {z["id"]: z for z in ZONES}

CITY_LABELS = {
    "hatay": "Hatay",
    "kahramanmaras": "Kahramanmaras",
}


# --------------------------------------------------------------------------
# Karargahlar (12)
# --------------------------------------------------------------------------
# coordSource, koordinatin NEREDEN geldigini durustce isaretler:
#   "gercek-osm-altyapi" -> benchmark/data/<il>.json icindeki gercek OSM
#                           itfaiye/hastane noktasina snap edildi.
#   "ilce-merkezi"       -> o ilce icin yerel altyapi verimiz yok; karargah
#                           ilce merkezine yerlestirildi (senaryo kurgusu).
# Karargah, grafta CIKMAZ (tek komsulu) bir dugume dusmemelidir: o tek kenar
# kapaninca karargah agdan kopmus gorunur -- gercekte ekip yan sokaga yurur.
# Bu yuzden karargahlar en yakin gercek kavsaga (derece >= 3) yerlestirilir.
# Orkestrator calisirken, koordinat bolgenin GRAF SINIRLARI icinde mi diye
# ayrica dogrular (bkz. rich_simulation.select_team_bases'teki ayni ders:
# graf disindaki bir nokta en yakin dugume yanlislikla "kilitleniyor").
HEADQUARTERS = [
    # --- HATAY ---
    {"id": "HQ-H1", "zoneId": "H-Z1", "name": "Antakya AFAD Ana Koordinasyon Merkezi",
     "lat": 36.2145, "lon": 36.1368, "coordSource": "gercek-osm-altyapi",
     "coordNote": "Antakya Devlet Hastanesi (OSM) noktasina snap edildi"},
    {"id": "HQ-H2", "zoneId": "H-Z1", "name": "Defne Sahra Hastanesi",
     "lat": 36.1967, "lon": 36.1638, "coordSource": "gercek-osm-altyapi",
     "coordNote": "Ozel Mozaik Kadin Hastaliklari ve Dogum Merkezi (OSM) noktasina snap edildi"},
    {"id": "HQ-H3", "zoneId": "H-Z2", "name": "Iskenderun Itfaiye Grup Amirligi",
     "lat": 36.5875, "lon": 36.1700, "coordSource": "ilce-merkezi", "coordNote": ""},
    {"id": "HQ-H4", "zoneId": "H-Z3", "name": "Kirikhan Acil Mudahale Istasyonu",
     "lat": 36.4986, "lon": 36.3606, "coordSource": "ilce-merkezi", "coordNote": ""},
    {"id": "HQ-H5", "zoneId": "H-Z4", "name": "Samandag Kizilay Afet Deposu",
     "lat": 36.0850, "lon": 35.9800, "coordSource": "ilce-merkezi", "coordNote": ""},
    {"id": "HQ-H6", "zoneId": "H-Z5", "name": "Belen Gecidi Taktik Lojistik Ussu",
     "lat": 36.4900, "lon": 36.2000, "coordSource": "ilce-merkezi", "coordNote": ""},
    # --- KAHRAMANMARAS ---
    {"id": "HQ-K1", "zoneId": "K-Z1", "name": "Maras Fuar Alani AFAD Cadirkenti",
     "lat": 37.578485, "lon": 36.931489, "coordSource": "gercek-osm-altyapi",
     "coordNote": "Yenisehir Devlet Hastanesi (OSM) noktasina snap edildi; 16 Eylul 2026'da "
                  "43 m otedeki kavsaga (Sehit Mucahit Simsek Sk.) tasindi -- eski nokta "
                  "12 m'lik cikmaz bir baglanti yoluna dusuyordu ve o tek parca kapaninca "
                  "karargah agdan kopmus gorunuyordu (eski konum 37.5781, 36.9315)"},
    {"id": "HQ-K2", "zoneId": "K-Z1", "name": "Onikisubat Itfaiye Merkezi",
     "lat": 37.5891, "lon": 36.9423, "coordSource": "gercek-osm-altyapi",
     "coordNote": "OSM itfaiye noktasi"},
    {"id": "HQ-K3", "zoneId": "K-Z1", "name": "Dulkadiroglu Sahra Hastanesi",
     "lat": 37.5655, "lon": 36.9296, "coordSource": "gercek-osm-altyapi",
     "coordNote": "Sular Akademi Hastanesi (OSM) noktasina snap edildi"},
    {"id": "HQ-K4", "zoneId": "K-Z2", "name": "Elbistan Kriz Koordinasyon Ussu",
     "lat": 38.2050, "lon": 37.1950, "coordSource": "ilce-merkezi", "coordNote": ""},
    {"id": "HQ-K5", "zoneId": "K-Z3", "name": "Pazarcik Kizilay Acil Destek",
     "lat": 37.4890, "lon": 37.3000, "coordSource": "ilce-merkezi", "coordNote": ""},
]

HEADQUARTERS_BY_ID = {h["id"]: h for h in HEADQUARTERS}


# --------------------------------------------------------------------------
# Ekipler (18) -- her ekip bir karargahtan cikar, kendi bolgesinde rota alir
# --------------------------------------------------------------------------
# role: frontend'in teamDivIcon rengini de suruyor (bkz. LeafletContainer.tsx).
TEAM_ROLE_LABELS = {
    "arama-kurtarma": "Arama-Kurtarma",
    "medikal": "Medikal",
    "lojistik": "Lojistik",
}

TEAMS = [
    # --- HATAY (9) ---
    {"id": "HATAY-AK1", "city": "hatay", "zoneId": "H-Z1", "hqId": "HQ-H1", "role": "arama-kurtarma", "unit": "Itfaiye Arama Kurtarma"},
    {"id": "HATAY-AK2", "city": "hatay", "zoneId": "H-Z1", "hqId": "HQ-H1", "role": "arama-kurtarma", "unit": "AKUT Saha Ekibi"},
    {"id": "HATAY-LOJ1", "city": "hatay", "zoneId": "H-Z1", "hqId": "HQ-H2", "role": "lojistik", "unit": "Kizilay Lojistik Ekibi"},
    {"id": "HATAY-AK3", "city": "hatay", "zoneId": "H-Z2", "hqId": "HQ-H3", "role": "arama-kurtarma", "unit": "Itfaiye Arama Kurtarma"},
    {"id": "HATAY-MED1", "city": "hatay", "zoneId": "H-Z2", "hqId": "HQ-H3", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "HATAY-AK4", "city": "hatay", "zoneId": "H-Z3", "hqId": "HQ-H4", "role": "arama-kurtarma", "unit": "Jandarma Arama Kurtarma"},
    {"id": "HATAY-LOJ2", "city": "hatay", "zoneId": "H-Z3", "hqId": "HQ-H4", "role": "lojistik", "unit": "AFAD Lojistik Ekibi"},
    {"id": "HATAY-MED2", "city": "hatay", "zoneId": "H-Z4", "hqId": "HQ-H5", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "HATAY-AK5", "city": "hatay", "zoneId": "H-Z5", "hqId": "HQ-H6", "role": "arama-kurtarma", "unit": "AKUT Saha Ekibi"},
    # --- KAHRAMANMARAS (9) ---
    {"id": "MARAS-AK1", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K2", "role": "arama-kurtarma", "unit": "Itfaiye Arama Kurtarma"},
    {"id": "MARAS-AK2", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K2", "role": "arama-kurtarma", "unit": "AKUT Saha Ekibi"},
    {"id": "MARAS-MED1", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K3", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "MARAS-MED2", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K3", "role": "medikal", "unit": "UMKE Sahra Saglik"},
    {"id": "MARAS-LOJ1", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K1", "role": "lojistik", "unit": "Kizilay Lojistik Ekibi"},
    {"id": "MARAS-LOJ2", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K1", "role": "lojistik", "unit": "AFAD Lojistik Ekibi"},
    {"id": "MARAS-AK3", "city": "kahramanmaras", "zoneId": "K-Z2", "hqId": "HQ-K4", "role": "arama-kurtarma", "unit": "Jandarma Arama Kurtarma"},
    {"id": "MARAS-AK4", "city": "kahramanmaras", "zoneId": "K-Z3", "hqId": "HQ-K5", "role": "arama-kurtarma", "unit": "Itfaiye Arama Kurtarma"},
    # MARAS-AK5: K-Z4 Goksun cikarilinca afetzedesiyle birlikte K-Z1'e tasindi.
    {"id": "MARAS-AK5", "city": "kahramanmaras", "zoneId": "K-Z1", "hqId": "HQ-K2", "role": "arama-kurtarma", "unit": "AKUT Saha Ekibi"},
]


# --------------------------------------------------------------------------
# Cihaz otonom davranis kurallari (senaryo spesifikasyonundan)
# --------------------------------------------------------------------------
LOW_BATTERY_THRESHOLD = 20      # < %20 -> tasarruf modu (ekran karartma, Edge AI uyutma)
SAVER_GPS_POLLING_SEC = 10      # tasarruf modunda GPS polling araligi
NORMAL_GPS_POLLING_SEC = 2      # normal modda

# 2. seviye fallback (sebeke yok) icin BLE mesh uzerinden gonderilen hafif
# paketin ALANLARI. Byte uzunlugu orkestratorde gercekten serilestirilerek
# olculur -- "150 byte" iddiasi tahmin degil, olcum olsun diye.
MESH_PACKET_FIELDS = ("id", "lat", "lon", "type", "risk", "batt")

COMMS_LABELS = {
    "online": "HTTPS/REST API (tam veri)",
    "mesh": "P2P BLE Mesh (hafif JSON)",
    "offline": "Lokal SQLite kuyrugu (izole)",
}


def derive_power_mode(battery_percent: int) -> str:
    return "tasarruf" if battery_percent < LOW_BATTERY_THRESHOLD else "normal"


def derive_gps_polling_sec(battery_percent: int) -> int:
    return SAVER_GPS_POLLING_SEC if battery_percent < LOW_BATTERY_THRESHOLD else NORMAL_GPS_POLLING_SEC


# --------------------------------------------------------------------------
# Afetzede profilleri (18)
# --------------------------------------------------------------------------
# channel:
#   "yolo" -> gercek gorsel POST /api/camera/analyze (gercek bina.pt cikarimi)
#   "nlp"  -> gercek metin POST /api/nlp/analyze (gercek BERTurk) + SOS
#   "sos"  -> tek dokunus POST /api/sos/alert (metin yok, cihaz durumu var)
#
# durum: onceliklendirme icin (pipeline_runner.DURUM_PRIORITY ile ayni sozluk).
# preferredRole: rol-farkinda atamanin girdisi (ihtiyac -> ekip rolu).
# relocatedFrom: kullanicinin onayladigi yeniden dagitimla tasinan profiller --
#   raporda acikca gosterilir, sessizce degistirilmis gibi durmasin.
VICTIMS = [
    # ================= HATAY =================
    {
        "id": "HTY-01", "name": "Selim Kaya", "city": "hatay", "zoneId": "H-Z1",
        "locationLabel": "Antakya, Inonu Cad.", "channel": "yolo",
        "batteryPercent": 65, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "damageNote": "5 katli binada kolon cokmesi",
    },
    {
        "id": "HTY-02", "name": "Elif Demir", "city": "hatay", "zoneId": "H-Z3",
        "locationLabel": "Kirikhan, Cumhuriyet Meydani", "channel": "yolo",
        "batteryPercent": 18, "commsStatus": "online",
        "durum": "hafif", "preferredRole": "lojistik",
        "damageNote": "Tasiyici kolon catlagi (zayif 3G uzerinden yuklendi)",
    },
    {
        "id": "HTY-03", "name": "Caner Yildiz", "city": "hatay", "zoneId": "H-Z2",
        "locationLabel": "Iskenderun, Liman Cad.", "channel": "yolo",
        "batteryPercent": 75, "commsStatus": "online",
        "durum": "hafif", "preferredRole": "medikal",
        "damageNote": "Orta hasarli duvar gocugu",
    },
    {
        "id": "HTY-04", "name": "Ahmet Yilmaz", "city": "hatay", "zoneId": "H-Z1",
        "locationLabel": "Defne, Armutlu Mah.", "channel": "nlp",
        "batteryPercent": 55, "commsStatus": "online",
        "durum": "hafif", "preferredRole": "lojistik",
        "needText": "Hatay Defne Armutlu Mahallesi'nde sokakta toplandik, bebekler var, temiz su ve battaniye lazim, cadde tas dolu.",
    },
    {
        "id": "HTY-05", "name": "Merve Sen", "city": "hatay", "zoneId": "H-Z4",
        "locationLabel": "Samandag, Ataturk Cad.", "channel": "nlp",
        "batteryPercent": 40, "commsStatus": "online",
        "durum": "kritik", "preferredRole": "medikal",
        "needText": "Hatay Samandag Ataturk Caddesi'nde apartman boslugunda kanamali kazazede var, acil doktor ve ambulans!",
    },
    {
        "id": "HTY-06", "name": "Ali Ozturk", "city": "hatay", "zoneId": "H-Z1",
        "locationLabel": "Antakya, Cebrail Mah.", "channel": "nlp",
        "batteryPercent": 47, "commsStatus": "mesh",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        "needText": "Hatay Antakya Cebrail Mahallesi'nde bina yan yatti, iceride 3 kisi var, ses veriyorlar, hilti ve jenerator lazim.",
    },
    {
        "id": "HTY-07", "name": "Burak Sahin", "city": "hatay", "zoneId": "H-Z2",
        "locationLabel": "Iskenderun, Cay Mah.", "channel": "sos",
        "batteryPercent": 14, "commsStatus": "mesh",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        "sirenActive": True,
        "situationNote": "Enkaz alti, otonom hayatta kalma modu aktif, BLE sinyali",
    },
    {
        "id": "HTY-08", "name": "Emre Aydin", "city": "hatay", "zoneId": "H-Z3",
        "locationLabel": "Kirikhan, Pasali Cad.", "channel": "sos",
        "batteryPercent": 35, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "situationNote": "Merdiven boslugunda sikisma, Mesh P2P",
    },
    {
        "id": "HTY-09", "name": "Sevgi Kaya", "city": "hatay", "zoneId": "H-Z5",
        "locationLabel": "Belen, Fatih Mah.", "channel": "sos",
        "batteryPercent": 50, "commsStatus": "online",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "situationNote": "Yikinti yani mahsur, AFAD REST API",
        "relocatedFrom": "Antakya, Harbiye Cad.",
    },
    # ================= KAHRAMANMARAS =================
    {
        "id": "KMS-01", "name": "Mustafa Yildiz", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Onikisubat, Trabzon Bulvari", "channel": "yolo",
        "batteryPercent": 82, "commsStatus": "online",
        "durum": "hafif", "preferredRole": "lojistik",
        "damageNote": "Kismi cati ve duvar yikimi",
    },
    {
        "id": "KMS-02", "name": "Aylin Kurt", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Dulkadiroglu, Ismetpasa Mah.", "channel": "yolo",
        "batteryPercent": 22, "commsStatus": "online",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        "damageNote": "Toptan gocme / agir enkaz (zayif Edge baglantisi)",
    },
    {
        "id": "KMS-03", "name": "Tolga Erdem", "city": "kahramanmaras", "zoneId": "K-Z2",
        "locationLabel": "Elbistan, Gunesli Mah.", "channel": "yolo",
        "batteryPercent": 60, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "damageNote": "Kolon patlamasi",
    },
    {
        "id": "KMS-04", "name": "Zeynep Celik", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Dulkadiroglu, Azerbaycan Bulvari", "channel": "nlp",
        "batteryPercent": 38, "commsStatus": "online",
        "durum": "kritik", "preferredRole": "medikal",
        "needText": "Kahramanmaras Dulkadiroglu Azerbaycan Bulvari'nda girste 2 kisi sikisti, yasli teyzemize oksijen tupu ve sedye lazim acil!",
    },
    {
        "id": "KMS-05", "name": "Hakan Koc", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Onikisubat, Haydarbey Mah.", "channel": "nlp",
        "batteryPercent": 71, "commsStatus": "online",
        "durum": "hafif", "preferredRole": "lojistik",
        "needText": "Kahramanmaras Onikisubat Haydarbey Mahallesi'nde park alaninda 50 kisi var, bebek bezi, cadir ve kuru gida bekliyoruz.",
    },
    {
        "id": "KMS-06", "name": "Fatma Arslan", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Merkez, Azerbaycan Blv.", "channel": "nlp",
        "batteryPercent": 29, "commsStatus": "mesh",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        # Azerbaycan Bulvari, K-Z1'in kendi OSM grafinda dogrulandi
        # (osm_graph_cache, 20 643 dugumlu Merkez grafi) -- metin, afetzedenin
        # bulundugu bolgeyle cografi olarak tutarli kalsin diye.
        "needText": "Kahramanmaras merkez Azerbaycan Bulvari'nda enkazin arkasindaki depoda yangin basladi, itfaiye ve su tankeri acil!",
        # Tasima gecmisi: once Afsin -> Goksun, sonra Goksun cikarilinca -> K-Z1.
        "relocatedFrom": "Goksun, Ataturk Cad. (ilk: Afsin)",
    },
    {
        "id": "KMS-07", "name": "Fatma Dogan", "city": "kahramanmaras", "zoneId": "K-Z3",
        "locationLabel": "Pazarcik, Merkez Mah.", "channel": "sos",
        "batteryPercent": 11, "commsStatus": "mesh",
        "durum": "kritik", "preferredRole": "arama-kurtarma",
        "sirenActive": True,
        "situationNote": "Agir enkaz altinda, otonom hayatta kalma modu aktif",
    },
    {
        "id": "KMS-08", "name": "Serkan Tan", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Dulkadiroglu, Istasyon Mah.", "channel": "sos",
        "batteryPercent": 42, "commsStatus": "mesh",
        "durum": "mahsur", "preferredRole": "arama-kurtarma",
        "situationNote": "Merdiven cokmesi sonucu mahsur, BLE Mesh",
        "relocatedFrom": "Turkoglu, Istasyon Mah.",
    },
    {
        "id": "KMS-09", "name": "Derya Uysal", "city": "kahramanmaras", "zoneId": "K-Z1",
        "locationLabel": "Onikisubat, Binevler Mah.", "channel": "sos",
        "batteryPercent": 68, "commsStatus": "online",
        "durum": "mahsur", "preferredRole": "medikal",
        "situationNote": "Kismi gocuk, 4.5G",
    },
]


# --------------------------------------------------------------------------
# Harita pin standardi (senaryo spesifikasyonu -> frontend marker tipi)
# --------------------------------------------------------------------------
PIN_STANDARD = {
    "yolo": {"markerType": "debris", "color": "#f97316", "label": "YOLOv8 Hasar Ihbari (turuncu)"},
    "nlp": {"markerType": "nlp", "color": "#eab308", "label": "NLP Ihtiyac Ihbari (sari)"},
    "sos": {"markerType": "sos", "color": "#ef4444", "label": "Acil SOS Cagrisi (kirmizi flasor)"},
    "hq": {"markerType": "hq", "color": "#2563eb", "label": "Karargah (sabit mavi us)"},
    "team": {"markerType": "team", "color": "rol-bazli", "label": "Ekip (rol rengiyle canli konum)"},
}


# --------------------------------------------------------------------------
# Yardimcilar (saf, HTTP yok)
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
    """Veri setinin ic tutarliligini kontrol eder -- orkestrator baslarken
    cagirir, boylece bir profil yanlis bolgeye yazildiysa kosunun ORTASINDA
    degil BASINDA anlasilir."""
    problems = []

    for v in VICTIMS:
        if v["zoneId"] not in ZONES_BY_ID:
            problems.append(f"{v['id']}: bilinmeyen zoneId {v['zoneId']}")
        elif ZONES_BY_ID[v["zoneId"]]["city"] != v["city"]:
            problems.append(f"{v['id']}: sehir/bolge uyusmazligi ({v['city']} vs {v['zoneId']})")
        if v["channel"] not in ("yolo", "nlp", "sos"):
            problems.append(f"{v['id']}: gecersiz kanal {v['channel']}")
        if v["channel"] == "nlp" and not v.get("needText"):
            problems.append(f"{v['id']}: nlp kanali icin needText yok")

    for t in TEAMS:
        if t["hqId"] not in HEADQUARTERS_BY_ID:
            problems.append(f"{t['id']}: bilinmeyen hqId {t['hqId']}")
        elif HEADQUARTERS_BY_ID[t["hqId"]]["zoneId"] != t["zoneId"]:
            problems.append(f"{t['id']}: karargah bolgesi ekip bolgesiyle uyusmuyor")

    # Her bolgede ekip sayisi >= afetzede sayisi olmali ki 1:1 atama yapilabilsin.
    for z in ZONES:
        n_v = len(victims_in_zone(z["id"]))
        n_t = len(teams_in_zone(z["id"]))
        if n_v != n_t:
            problems.append(f"{z['id']}: {n_v} afetzede ama {n_t} ekip (1:1 olmali)")
        if n_v and not headquarters_in_zone(z["id"]):
            problems.append(f"{z['id']}: afetzede var ama karargah yok")

    # Kanal dagilimi: her ilde 3/3/3 bekleniyor.
    for city in CITY_LABELS:
        for channel in ("yolo", "nlp", "sos"):
            n = len([v for v in VICTIMS if v["city"] == city and v["channel"] == channel])
            if n != 3:
                problems.append(f"{city}: {channel} kanalinda {n} ihbar (3 bekleniyor)")

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
        print(f"  {z['id']:6s} {z['label']:36s} afetzede={len(victims_in_zone(z['id']))} "
              f"ekip={len(teams_in_zone(z['id']))} karargah={len(headquarters_in_zone(z['id']))} "
              f"graf={z['graphSource']}")
