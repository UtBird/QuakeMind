"""En yakin aktif faya mesafe: GEM Global Active Faults veritabanindan.

Eskiden mesafe risk_engine.py'de elle yazilmis ~38 "yaklasik" noktaya
olculuyordu: yalniz KAF, DAF ve dort Ege grabeni vardi; Van'da en yakin fay
215 km cikiyordu. Bu modul ayni mesafeyi depodaki GEM verisinden (CC BY-SA 4.0,
haritadaki fay katmaniyla ayni dosya) cizgiye en kisa mesafe olarak verir.

Yontem: Turkiye ve cevresindeki fay cizgileri en fazla ADIM_KM aralikla
noktalara bolunur, noktalar haversine BallTree'ye konur. Mesafe hatasi
ADIM_KM / 2'yi gecmez. Hem urun (risk_engine.py) hem makale olcumu
(model_benchmarks/05_risk_skoru/common_preprocessing.py) bunu kullanir.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

GEM_DOSYASI = (Path(__file__).resolve().parent / "data" / "fault_maps" / "fay_haritası"
               / "gem_active_faults_harmonized.geojson")
# Turkiye kutusu + ~2 derece pay: sinira yakin yerin en yakin fayi komsu ulkede olabilir.
BOLGE = (24.0, 34.0, 47.0, 44.0)  # bati, guney, dogu, kuzey
ADIM_KM = 1.0
DUNYA_YARICAPI_KM = 6371.0088

# GEM `slip_type` -> Turkce. Veri setinde fay ADI bos; ad uydurulmaz, tur yazilir.
TUR = {
    "Normal": "normal", "Reverse": "ters", "Thrust": "bindirme", "Blind Thrust": "kör bindirme",
    "Dextral": "sağ yanal", "Sinistral": "sol yanal",
    "Dextral-Normal": "sağ yanal-normal", "Sinistral-Normal": "sol yanal-normal",
    "Dextral-Reverse": "sağ yanal-ters", "Sinistral-Reverse": "sol yanal-ters",
}

KAYNAK = {
    "ad": "GEM Global Active Faults Database",
    "lisans": "CC BY-SA 4.0",
    "dosya": GEM_DOSYASI.name,
}


def _sik_noktalar(cizgi):
    """Cizgiyi en fazla ADIM_KM aralikli (lat, lon) noktalara boler."""
    noktalar = []
    for (lon1, lat1), (lon2, lat2) in zip(cizgi, cizgi[1:]):
        dx = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
        dy = (lat2 - lat1) * 110.574
        n = max(1, math.ceil(math.hypot(dx, dy) / ADIM_KM))
        for i in range(n):
            t = i / n
            noktalar.append((lat1 + t * (lat2 - lat1), lon1 + t * (lon2 - lon1)))
    noktalar.append((cizgi[-1][1], cizgi[-1][0]))
    return noktalar


@lru_cache(maxsize=1)
def _agac():
    """BallTree, her noktanin ait oldugu fayin sirasi ve faylarin ozellikleri."""
    from sklearn.neighbors import BallTree

    if not GEM_DOSYASI.exists():
        raise FileNotFoundError(f"GEM fay dosyasi yok: {GEM_DOSYASI}")
    bati, guney, dogu, kuzey = BOLGE
    noktalar, sahip, ozellikler = [], [], []
    with open(GEM_DOSYASI, encoding="utf-8") as f:
        for ozellik in json.load(f)["features"]:
            cizgi = (ozellik.get("geometry") or {}).get("coordinates") or []
            if len(cizgi) < 2:
                continue
            if not any(bati <= x <= dogu and guney <= y <= kuzey for x, y, *_ in cizgi):
                continue
            yeni = _sik_noktalar([(x, y) for x, y, *_ in cizgi])
            noktalar.extend(yeni)
            sahip.extend([len(ozellikler)] * len(yeni))
            ozellikler.append(ozellik.get("properties") or {})
    agac = BallTree(np.radians(np.asarray(noktalar)), metric="haversine")
    return agac, np.asarray(sahip), ozellikler


def en_yakin_fay_km(lat, lon):
    """Tek nokta ya da dizi; en yakin GEM fay cizgisine km (hata <= ADIM_KM/2)."""
    lat_d = np.atleast_1d(np.asarray(lat, dtype=float))
    lon_d = np.atleast_1d(np.asarray(lon, dtype=float))
    uzaklik, _ = _agac()[0].query(np.radians(np.column_stack([lat_d, lon_d])), k=1)
    km = uzaklik[:, 0] * DUNYA_YARICAPI_KM
    return float(km[0]) if np.ndim(lat) == 0 else km


def yakin_faylar(lat, lon, adet=3):
    """En yakin `adet` ayri GEM fayi: km, Turkce tur, katalog ve kimlik."""
    agac, sahip, ozellikler = _agac()
    uzaklik, sira = agac.query(np.radians([[lat, lon]]), k=min(400, len(sahip)))
    sonuc, gorulen = [], set()
    for d, i in zip(uzaklik[0], sira[0]):
        fay = int(sahip[i])
        if fay in gorulen:
            continue
        gorulen.add(fay)
        p = ozellikler[fay]
        sonuc.append({
            "km": float(d * DUNYA_YARICAPI_KM),
            "tur": TUR.get(p.get("slip_type"), p.get("slip_type") or "türü bilinmeyen"),
            "katalog": p.get("catalog_name"),
            "kimlik": p.get("catalog_id"),
        })
        if len(sonuc) == adet:
            break
    return sonuc
