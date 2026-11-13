"""Afetzede haritasi (J-50): yakindaki yerler, yurume rotasi (J-44) ve yedek sokak rotasi.

Kaynaklar:
  * Toplanma alanlari -- AFAD'in resmi listesi (tum Turkiye).
  * Hastane, saglik merkezi, eczane, itfaiye, polis -- yerel OSM kopyasi
    (`araclar_altlik_uret.py --hizmetler`, kopyanin tarihi kunyede); yalniz
    altligi uretilmis bolgeler.
Ikisi de birer kayittir: yerin su an acik, saglam ya da bos oldugunu
soylemez. Ekran bunu yazar (kural 1).

Veri ilk istekte bir kez bellege alinir. Eski /api/road_damage/assembly ucu
her istekte 15,7 MB'lik AFAD dosyasini yeniden ayristiriyordu (~122 ms, J-43).
"""

import json
import math
import threading
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import cekirdek as ck
import kimlik
import yol_agi

yonlendirici = APIRouter()

TURLER = ("toplanma", "hastane", "saglik", "eczane", "itfaiye", "polis")
ALTLIK = Path(__file__).resolve().parents[1] / "veri" / "altlik"


_KUCUK = str.maketrans({"I": "ı", "İ": "i"})
_BUYUK = {"i": "İ", "ı": "I"}


def _tr_baslik(s):
    """AFAD adlari BUYUK harfle gelir. str.title() Turkcede yanlis: 'İ'yi
    'i̇' (noktali iki harf), 'I'yi 'i' yapar. "GENERAL ŞÜKRÜ KANATLI" ->
    "General Şükrü Kanatlı"."""
    if not isinstance(s, str) or not s.strip():
        return None
    kelimeler = s.strip().translate(_KUCUK).lower().split()
    return " ".join(_BUYUK.get(k[0], k[0].upper()) + k[1:] for k in kelimeler)


@lru_cache(maxsize=1)
def _afad():
    yol = ck.ROAD_ROOT / "data" / "tum_turkiye_toplanma_alanlari.json"
    enlem, boylam, bilgi = [], [], []
    for k in json.loads(yol.read_text(encoding="utf-8")):
        try:
            la, lo = float(k["enlem"]), float(k["boylam"])
        except (KeyError, TypeError, ValueError):
            continue
        enlem.append(la)
        boylam.append(lo)
        adres = " · ".join(
            _tr_baslik(x) for x in (k.get("mahalle"), k.get("ilce"), k.get("il")) if x and x.strip() != "-"
        )
        bilgi.append((_tr_baslik(k.get("toplanma_alani")), adres or None))
    return np.array(enlem), np.array(boylam), bilgi


@lru_cache(maxsize=1)
def _hizmetler():
    yol = ALTLIK / "hizmetler.json"
    if not yol.exists():
        return None
    veri = json.loads(yol.read_text(encoding="utf-8"))
    yerler = veri["yerler"]
    return veri, np.array([y["lat"] for y in yerler]), np.array([y["lon"] for y in yerler])


@lru_cache(maxsize=1)
def _bolgeler():
    """Operasyon bolgeleri: hizmet verisi yalniz bunlarda uretildi. `il` turu
    altliklar (risk ekraninin 81 ili) burada sayilmaz."""
    yol = ALTLIK / "katalog.json"
    bolgeler = json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else []
    return [b for b in bolgeler if b.get("tur", "operasyon") == "operasyon"]


def _onyukle():
    """Sunucu acilirken arka planda: ilk afetzede istegi veri yuklemeyi
    (~1,8 sn, olculdu) beklemesin. Acilisi geciktirmez."""
    try:
        _afad()
        _hizmetler()
        _bolgeler()
        # Yol aglari (J-44): her biri ~0,5 sn; ilk rota istegi beklemesin.
        for b in yol_agi.katalog():
            yol_agi.ag_yukle(b["id"])
        # Arac aglari (J-55): yukleme ~0,6 sn, hasar carpanlari ~1,4 sn
        # (Antakya, olculdu). Bolge ortasinda bir arama carpanlari isitir;
        # ilk sevk ekrani 2 sn beklemesin.
        import arac_rotasi

        for b in arac_rotasi.katalog():
            w, s, e, n = b["kutu"]
            arac_rotasi.hedef_aramasi((w + e) / 2, (s + n) / 2)
        # Bolgeler arasi ag: bir sehrin ortasinda bir arama yukler ve isitir.
        if arac_rotasi.genel_bilgi() and arac_rotasi.katalog():
            w, s, e, n = arac_rotasi.katalog()[0]["kutu"]
            arac_rotasi.hedef_aramasi((w + e) / 2, (s + n) / 2, genel=True)
    except Exception as e:  # veri yoksa uc zaten bos/hata doner
        print(f"yakin yerler on yukleme: {e}", flush=True)


threading.Thread(target=_onyukle, name="yakin-yerler-onyukleme", daemon=True).start()


def _mesafe_m(lat0, lon0, lat, lon):
    """Haversine, vektorel (metre)."""
    f1, f2 = math.radians(lat0), np.radians(lat)
    dlat = f2 - f1
    dlon = np.radians(lon - lon0)
    a = np.sin(dlat / 2) ** 2 + math.cos(f1) * np.cos(f2) * np.sin(dlon / 2) ** 2
    return 2 * 6371000.0 * np.arcsin(np.sqrt(a))


@yonlendirici.get("/api/yakin-yerler")
def yakin_yerler(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    yaricapKm: float = Query(default=5.0, gt=0, le=25),
    sinir: int = Query(default=10, ge=1, le=30),
    _kul: dict = Depends(kimlik.kullanici),
):
    """Her tur icin yaricap icindeki en yakin `sinir` yer, uzakliga gore sirali."""
    yaricap_m = yaricapKm * 1000.0
    yerler = {t: [] for t in TURLER}

    # Toplanma: 72 bin kayit; once kutuyla suzulur, sonra mesafe.
    alat, alon, abilgi = _afad()
    dlat = yaricapKm / 110.574
    dlon = yaricapKm / (111.32 * max(0.1, math.cos(math.radians(lat))))
    aday = np.nonzero((np.abs(alat - lat) <= dlat) & (np.abs(alon - lon) <= dlon))[0]
    if aday.size:
        m = _mesafe_m(lat, lon, alat[aday], alon[aday])
        for j in np.argsort(m)[:sinir]:
            if m[j] > yaricap_m:
                break
            i = int(aday[j])
            ad, adres = abilgi[i]
            yerler["toplanma"].append({
                "id": f"afad-{i}", "tur": "toplanma", "ad": ad, "adres": adres,
                "lat": float(alat[i]), "lon": float(alon[i]), "mesafeM": round(float(m[j])),
            })

    hizmet = _hizmetler()
    hizmet_kaynagi = None
    if hizmet:
        veri, hlat, hlon = hizmet
        hizmet_kaynagi = veri.get("kaynak")
        m = _mesafe_m(lat, lon, hlat, hlon)
        for i in np.argsort(m):
            if m[i] > yaricap_m:
                break
            y = veri["yerler"][int(i)]
            liste = yerler[y["tur"]]
            if len(liste) < sinir:
                liste.append({
                    "id": y["osm"], "tur": y["tur"], "ad": y["ad"], "adres": None,
                    "lat": y["lat"], "lon": y["lon"], "mesafeM": round(float(m[i])),
                })

    # Yurume mesafesi (J-44): afetzedenin konumundan tek Dijkstra kosusu,
    # kendi yol agimizda ve hasar cezasiyla. Liste yurume mesafesine gore
    # siralanir: kus ucusu yakin olan yer, yol dolasiyorsa uzak olabilir.
    yurume = None
    try:
        arama = yol_agi.Arama(lon, lat)
        for liste in yerler.values():
            for y in liste:
                m = arama.mesafe(y["lon"], y["lat"])
                y["yuruyusM"] = round(m) if m is not None else None
            liste.sort(key=lambda y: (y["yuruyusM"] is None, y["yuruyusM"] or 0, y["mesafeM"]))
        yurume = {
            "ag": arama.ag.bilgi["id"],
            "osm": arama.ag.bilgi["kaynak"]["dosyaTarihi"],
            "baglantiM": round(arama.kaynak_mesafe),
            "hasar": arama.hasar_ozeti,
        }
    except LookupError:
        pass  # bolge icin yol agi yok: kus ucusu kalir, ekran bunu yazar

    # Hizmet verisi yalniz uretilmis bolgelerde var: disarida "yok" degil
    # "bilinmiyor" demek gerekir.
    bolgeler = _bolgeler()
    icinde = any(b["kutu"][0] <= lon <= b["kutu"][2] and b["kutu"][1] <= lat <= b["kutu"][3] for b in bolgeler)
    return {
        "yerler": yerler,
        "yaricapKm": yaricapKm,
        "kaynaklar": {
            "toplanma": "AFAD toplanma alanları listesi",
            "hizmet": hizmet_kaynagi,
        },
        "hizmetKapsami": {
            "uretildi": hizmet is not None,
            "icinde": icinde,
            "bolgeler": [b["ad"] for b in bolgeler],
        },
        "yurume": yurume,
    }


class YurumeRotasiIstegi(BaseModel):
    baslangicLat: float = Field(..., ge=-90, le=90)
    baslangicLon: float = Field(..., ge=-180, le=180)
    hedefLat: float = Field(..., ge=-90, le=90)
    hedefLon: float = Field(..., ge=-180, le=180)


@yonlendirici.post("/api/afetzede/rota")
def afetzede_rotasi(istek: YurumeRotasiIstegi, _kul: dict = Depends(kimlik.kullanici)):
    """Yurume rotasi, kendi yol agimizda (J-44): Dijkstra, hasar cezali.

    Dis servise istek gitmez; konum sunucudan cikmaz. Bolge icin yol agi
    uretilmemisse 404 doner (ekran o zaman kus ucusu yonu ve istege bagli dis
    servis rotasini sunar). Rota bilinen kapanma ve hasar noktalarini
    hesaba katar; bilinmeyen yikik yolu bilmez -- yanit bunu yazar."""
    try:
        arama = yol_agi.Arama(istek.baslangicLon, istek.baslangicLat)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    rota = arama.rota(istek.hedefLon, istek.hedefLat)
    if rota is None:
        raise HTTPException(
            status_code=404,
            detail="Hedef bu yol ağının dışında ya da yürüyerek ulaşılamıyor.",
        )
    h = rota["hasar"]
    if h["kapanma"] or h["hasarNoktasi"]:
        uyari = (
            f"Uydu analizinden bilinen {h['kapanma']} kapanma ve {h['hasarNoktasi']} hasar noktası "
            "hesaba katıldı; bilinmeyen yıkık yolu bilmez."
        )
    else:
        uyari = "Bu bölgede kayıtlı kapanma ya da hasar noktası yok; rota yıkık yolları bilmez."
    if h["rotadaKapanma"]:
        uyari = "Başka yol olmadığı için rota bilinen bir kapanmadan geçiyor. " + uyari
    return {**rota, "uyari": uyari}


class SokakRotasiIstegi(BaseModel):
    baslangicLat: float
    baslangicLon: float
    hedefLat: float
    hedefLon: float


YAYA_HIZI_M_DK = 80.0  # ~4,8 km/sa


@yonlendirici.post("/api/afetzede/sokak-rotasi")
def sokak_rotasi(istek: SokakRotasiIstegi, _kul: dict = Depends(kimlik.kullanici)):
    """Istege bagli yaya rotasi: FOSSGIS'in OSRM sunucusu (routing.openstreetmap.de,
    openstreetmap.org'un yol tarifi servisi).

    YEDEK: asil rota kendi yol agimizdan gelir (`/api/afetzede/rota`, J-44).
    Bu uc yalniz yol agi uretilmemis bolgede ve kullanici acikca istediginde
    cagrilir; baslangic ve hedef bu servise gider. Rota yikik ve kapali
    yollari BILMEZ. Servis yanit vermezse duz cizgi uydurulmaz, hata doner
    (eski /calculate_custom_route kus ucusu cizgiyi rota diye donduruyordu)."""
    import requests

    for d in (istek.baslangicLat, istek.hedefLat):
        if not -90 <= d <= 90:
            raise HTTPException(status_code=422, detail="Geçersiz enlem.")
    url = (
        "https://routing.openstreetmap.de/routed-foot/route/v1/foot/"
        f"{istek.baslangicLon:.6f},{istek.baslangicLat:.6f};{istek.hedefLon:.6f},{istek.hedefLat:.6f}"
        "?overview=full&geometries=geojson"
    )
    try:
        y = requests.get(url, timeout=10, headers={"User-Agent": "QuakeMind/0.1 (afet karar destek, akademik)"})
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Rota servisine ulaşılamadı.")
    rotalar = y.json().get("routes") if y.status_code == 200 else None
    if not rotalar:
        raise HTTPException(status_code=503, detail="Rota servisi bu iki nokta için rota vermedi.")
    r = rotalar[0]
    uzunluk = float(r["distance"])
    return {
        "koordinatlar": r["geometry"]["coordinates"],  # [lon, lat]
        "uzunlukM": round(uzunluk),
        "yuruyusDk": max(1, round(uzunluk / YAYA_HIZI_M_DK)),
        "kaynak": "OSRM yaya profili, routing.openstreetmap.de (OpenStreetMap verisi)",
        "uyari": "Bu rota yıkık ve kapalı yolları bilmez.",
    }
