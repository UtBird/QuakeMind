"""Deprem riski hesabı (J-173): iş parçacığı güvenli, tek hesap, önbellekli.

Eski yol (`quakemind/tool/risk_bridge.build_payload` + `ck.temporary_cwd`):
  * Motor hesaplanan koordinatı ortak nesnede (`self.last_lat`) tutuyor, köprü
    oradan geri okuyordu. Eşzamanlı isteklerde yanıt BAŞKA ilin koordinatını
    taşıyordu: 8 paralel kullanıcıyla 40 istekte 35'i yanlış (ölçüldü).
  * Her istek bütün sürecin çalışma klasörünü (`os.chdir`) ve `sys.path`'i
    değiştiriyordu; aynı anda koşan başka uçları da etkiler.
  * Kısa ve uzun vadeli bileşenler iki kez hesaplanıyor, skor metinden
    ayrıştırılıyordu.

Burada:
  * Motor (`ck.risk_engine`, `apps/earthquake_risk/risk_engine.py`) yalnız
    OKUNUR; sonuç her istekte yerel değişkenlerden kurulur.
  * Veri tazelenince YENİ motor kurulur ve tek atamayla değiştirilir; koşan
    istek eski motoru bitirir (yarım veriyle hesap yok).
  * Sonuç veri sürümü değişmedikçe önbellekten (koordinat 4 ondalık).
  * Kısa vadeli model ve karar mantığı DEĞİŞMEDİ. Yanıt, kısa vadeli
    bileşenin yerel depremlerden mi ülke genelinden mi beslendiğini yazar
    (eskiden sessizce ülke geneline düşüyordu).
  * Uzun vadeli tehlike (10 yılda M≥6 olasılığı, Poisson): artçılar SAYILMAZ
    (motorun kendi kümeleme ayıklaması) ve oran KATALOĞUN süresine bölünür.
    Eskiden artçılar dahildi (2023 dizisinin M6+ artçıları oranı şişiriyordu)
    ve süre o çevredeki ilk ve son deprem arasından alınıyordu. Önce/sonra
    81 il için EKSIKLER J-173'te.
"""
from __future__ import annotations

import logging
import math
import sys
import threading
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

import cekirdek as ck

log = logging.getLogger("quakemind.risk")

AGIRLIK = {"kisa": 0.4, "uzun": 0.3, "fay": 0.3}  # uzman tanımlı [T], ölçülmedi
KISA_YARICAP_KM = 150.0
UZUN_YARICAP_KM = 200.0
UZUN_ESIK_M = 6.0
UZUN_UFUK_YIL = 10.0
YAKIN_DEPREM_KM = 150.0
ONBELLEK_BOYU = 512

_kilit = threading.Lock()
_onbellek: "OrderedDict[tuple, dict]" = OrderedDict()
_dizi_onbellek: dict[int, dict] = {}


class RiskHazirDegil(RuntimeError):
    """Model yüklenemedi ya da eğitilmemiş (503)."""


def _modul():
    """Motorun modülü (cekirdek onu `risk_engine` adıyla yükledi)."""
    return sys.modules[type(ck.risk_engine).__module__]


def _hazirla(motor) -> None:
    """Çerçeve ve model ilk kullanımda BİR KEZ yüklenir (kilitli)."""
    if motor.df_main is not None and motor.model is not None:
        return
    with _kilit:
        try:
            motor._prepare_frames()
            motor.modeli_yukle()
        except Exception as e:
            raise RiskHazirDegil(str(e)) from e


def _diziler(motor) -> dict:
    """Motor başına bir kez: uzun vadeli hesabın dizileri."""
    d = _dizi_onbellek.get(id(motor))
    if d is not None and d["motor"] is motor:
        return d
    df = motor.df_full
    mag = df["mag"].to_numpy()
    buyuk = np.nonzero(mag >= UZUN_ESIK_M)[0]
    ana = buyuk[_gardner_knopoff(
        df["latitude"].to_numpy()[buyuk], df["longitude"].to_numpy()[buyuk], mag[buyuk],
        df["time"].astype("int64").to_numpy()[buyuk] / 8.64e13,  # ns -> gun
    )]
    buyuk = np.zeros(len(df), bool)
    buyuk[ana] = True
    sure_yil = (df["time"].max() - df["time"].min()).days / 365.25
    d = {
        "motor": motor,
        "lat": df["latitude"].to_numpy(),
        "lon": df["longitude"].to_numpy(),
        "buyuk_lat": df["latitude"].to_numpy()[buyuk],
        "buyuk_lon": df["longitude"].to_numpy()[buyuk],
        "sure_yil": max(sure_yil, 1.0),
        "veri_basi": str(df["time"].min())[:10],
        "veri_sonu": str(df["time"].max())[:16].replace("T", " "),
    }
    _dizi_onbellek.clear()
    _dizi_onbellek[id(motor)] = d
    return d


def _gardner_knopoff(lat, lon, mag, gun) -> np.ndarray:
    """Ana şok maskesi: Gardner & Knopoff (1974) pencereleri [A]. Daha büyük
    (eşitse daha erken) bir depremin zaman ve mesafe penceresine düşen olay
    öncü ya da artçı sayılır. Pencere: L = 10^(0,1238 M + 0,983) km;
    T = 10^(0,032 M + 2,7389) gün (M ≥ 6,5), 10^(0,5409 M − 0,547) gün (altı).
    Motorun kendi ayıklaması 1 gün / 50 km'dir; M ≥ 6 için çok dar (2023'te
    14 gün sonraki M 6,4 ana şok sayılıyordu)."""
    n = len(mag)
    ana = np.ones(n, bool)
    sira = np.lexsort((gun, -mag))  # büyükten küçüğe, eşitse erken önce
    r = math.pi / 180.0
    for i in sira:
        if not ana[i]:
            continue
        m = mag[i]
        L = 10 ** (0.1238 * m + 0.983)
        T = 10 ** (0.032 * m + 2.7389) if m >= 6.5 else 10 ** (0.5409 * m - 0.547)
        h = (np.sin((lat - lat[i]) * r / 2) ** 2
             + np.cos(lat[i] * r) * np.cos(lat * r) * np.sin((lon - lon[i]) * r / 2) ** 2)
        km = 2 * 6371.0 * np.arcsin(np.sqrt(h))
        pencere = (np.abs(gun - gun[i]) <= T) & (km <= L) & (mag <= m)
        pencere[i] = False
        ana &= ~pencere
    return ana


def _uzun_vadeli(mod, d, lat, lon) -> tuple[float, int]:
    """10 yılda en az bir M≥6 ana şok olasılığı (Poisson), 200 km içinde."""
    yakin = mod.haversine(lat, lon, d["buyuk_lat"], d["buyuk_lon"]) <= UZUN_YARICAP_KM
    n = int(yakin.sum())
    lam = (n if n > 0 else 0.01) / d["sure_yil"]
    return max(0.0, min(1.0, 1 - math.exp(-lam * UZUN_UFUK_YIL))), n


def _kisa_vadeli_kaynak(motor, mod, lat, lon) -> tuple[str, int]:
    """Kısa vadeli bileşen hangi depremlerden beslendi (motorun kuralıyla aynı)."""
    df = motor.df_main
    son = df[df["time"] >= df["time"].max() - pd.Timedelta(days=365)]
    n = int((mod.haversine(lat, lon, son["latitude"].to_numpy(), son["longitude"].to_numpy())
             <= KISA_YARICAP_KM).sum())
    return ("yerel" if n >= 7 else "ulke"), n


def _seviye(skor: float) -> str:
    return "DÜŞÜK" if skor < 0.25 else "ORTA" if skor < 0.5 else "YÜKSEK" if skor < 0.75 else "ÇOK YÜKSEK"


def hesapla(ad: str, lat: float, lon: float) -> dict:
    motor = ck.risk_engine
    if motor is None:
        raise RiskHazirDegil("Risk motoru yüklenemedi.")
    _hazirla(motor)
    anahtar = (id(motor), id(motor.model), round(lat, 4), round(lon, 4))
    with _kilit:
        kayit = _onbellek.get(anahtar)
        if kayit is not None:
            _onbellek.move_to_end(anahtar)
            return {**kayit, "city": ad}

    mod = _modul()
    d = _diziler(motor)
    kisa = float(motor._compute_short_term_ml_risk(lat, lon))
    kisa_kaynak, kisa_yerel_n = _kisa_vadeli_kaynak(motor, mod, lat, lon)
    uzun, uzun_n = _uzun_vadeli(mod, d, lat, lon)
    fay_km = float(mod.nearest_fault_distance(lat, lon))
    fay = float(mod.fault_hazard_score(fay_km))
    skor = AGIRLIK["kisa"] * kisa + AGIRLIK["uzun"] * uzun + AGIRLIK["fay"] * fay

    df = motor.df_full
    uz = mod.haversine(lat, lon, d["lat"], d["lon"])
    yakin = df[uz <= YAKIN_DEPREM_KM].assign(distance_km=uz[uz <= YAKIN_DEPREM_KM])
    son5 = yakin.sort_values("time", ascending=False).head(5)
    buyukler = yakin.sort_values(["mag", "time"], ascending=[False, False])

    def olay(r) -> dict:
        return {"time": str(r.time), "place": r.place if isinstance(r.place, str) else "Bilinmeyen konum",
                "magnitude": float(r.mag), "depth": None if r.depth != r.depth else float(r.depth),
                "distanceKm": round(float(r.distance_km), 1), "latitude": float(r.latitude),
                "longitude": float(r.longitude)}

    yakin_faylar = [
        {"tur": f["tur"], "kimlik": f["kimlik"], "km": round(float(f["km"]), 1)}
        for f in mod.yakin_faylar(lat, lon, 3)
    ]
    sonuc = {
        "city": ad,
        "coordinates": {"lat": lat, "lon": lon},
        "riskScore": round(skor * 100, 2),
        "riskLevel": _seviye(skor),
        "lastUpdate": d["veri_sonu"],
        "factors": {"Kisa vadeli risk": kisa, "Uzun vadeli tehlike": uzun, "Fay etkisi": fay},
        "metrics": {
            "shortRisk": kisa,
            "longHazard": uzun,
            "faultScore": fay,
            "faultDistanceKm": fay_km,
            "nearbyQuakeCount": int(len(yakin)),
            "maxMagnitude": float(yakin["mag"].max()) if len(yakin) else 0.0,
            "averageDepth": float(yakin["depth"].mean()) if len(yakin) else 0.0,
        },
        # J-173: bileşenlerin dayanağı (ekran "neden bu sonuç" sorusunu bunlarla yanıtlar).
        "dayanak": {
            "kisaVadeKaynagi": kisa_kaynak,
            "kisaVadeYerelDeprem": kisa_yerel_n,
            "uzunVadeAnaSok": uzun_n,
            "katalogBasi": d["veri_basi"],
            "katalogSonu": d["veri_sonu"],
            "agirlik": AGIRLIK,
            "yaricapKm": {"kisa": KISA_YARICAP_KM, "uzun": UZUN_YARICAP_KM, "yakinDeprem": YAKIN_DEPREM_KM},
        },
        "nearbyFaults": [f"{f['tur'].capitalize()} fay · {f['kimlik']} ({f['km']:.1f} km)".replace(".", ",")
                         for f in yakin_faylar],
        "yakinFaylar": yakin_faylar,
        "recentEvents": [f"M{r.mag:.1f} - {r.distance_km:.0f} km - {str(r.time)[:10]}"
                         for r in son5.itertuples()],
        "sonDepremler": [olay(r) for r in son5.itertuples()],
        "technicalQuakes": [olay(r) for r in buyukler.head(20).itertuples()],
        "usedManualCoordinates": True,
        "source": "backend_exact",
    }
    with _kilit:
        _onbellek[anahtar] = sonuc
        while len(_onbellek) > ONBELLEK_BOYU:
            _onbellek.popitem(last=False)
    return sonuc


def veriyi_tazele() -> str:
    """Kandilli (+USGS) verisini çeker, YENİ motoru hazırlar ve tek atamayla
    değiştirir. Koşan istekler eski motoru bitirir."""
    mod = _modul()
    eski = ck.risk_engine
    from apps.earthquake_risk.data_manager import fetch_and_update_data

    mesaj = str(fetch_and_update_data())
    yeni = mod.EarthquakeRiskEngine(csv_path=str(eski.csv_path) if eski else None)
    yeni._prepare_frames()
    yeni.modeli_yukle()
    ck.risk_engine = yeni
    with _kilit:
        _onbellek.clear()
    return mesaj


def il_merkezi(ad: str) -> Optional[dict]:
    from uclar.risk import IL_MERKEZLERI
    import json

    if not IL_MERKEZLERI.exists():
        return None
    for il in json.loads(IL_MERKEZLERI.read_text(encoding="utf-8")).get("iller", []):
        if il["il"].casefold() == ad.strip().casefold():
            return il
    return None
