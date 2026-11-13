"""Kullanicinin kendi sisteminde zaten test ettigi, bilinen-iyi calisan
gercek OpenAerialMap goruntuleri. Otomatik Wayback/Maxar secimi yerine bu
liste kullanilir -- cozunurluk/kalite garantili, kullanici ekran
goruntuleriyle dogruladi (bkz. oturum notlari, 12 Agustos 2026).

Her girdi /api/road_damage/oam_search sonuclarindan `oamTitleMatch` ile
eslestirilip taze bir `tms_url` cekilir (OAM linkleri zamanla degisebilir,
bu yuzden sabit URL yerine baslik-eslestirmesi kullaniliyor).

Yeni konum eklemek icin: kullanicidan ekran goruntusu + /command/road-damage
sayfasindaki secili goruntunun basligi al, KNOWN_LOCATIONS'a bir girdi ekle.
"""

KNOWN_LOCATIONS = [
    {
        "region": "kahramanmaras",
        "mahalleName": "EKMEKÇİ",  # gercek AFAD mahalle adiyla eslesiyor
        "oamTitleMatch": "Şubat Stadyumu",
        "provider": "Help.NGO",
        "date": "2023-02-09",
        "bbox": {"west": 36.917486, "south": 37.573071, "east": 36.923946, "north": 37.578173},
    },
    {
        "region": "hatay",
        "mahalleName": "ELEKTRİK",
        "oamTitleMatch": "Defne - Elektrik",
        "provider": "Help.NGO",
        "date": "2023-02-09",
        "bbox": {"west": 36.146753, "south": 36.195466, "east": 36.15189, "north": 36.199922},
    },
    {
        "region": "hatay",
        "mahalleName": "ARMUTLU",
        "oamTitleMatch": "Turinclu - Akdeniz",
        "provider": "Help.NGO, Portugese GRU",
        "date": "2023-02-09",
        "bbox": {"west": 36.142957, "south": 36.192684, "east": 36.15092, "north": 36.19543},
    },
]


def bbox_center(bbox: dict) -> tuple[float, float]:
    lat = (bbox["south"] + bbox["north"]) / 2
    lon = (bbox["west"] + bbox["east"]) / 2
    return lat, lon


def locations_for_region(region_key: str) -> list[dict]:
    return [loc for loc in KNOWN_LOCATIONS if loc["region"] == region_key]
