"""Haritanin basvuru katmanlari (J-56): yol kapanmalari, depremler, fay hatlari,
toplanma alanlari.

Konsolda bu dort katmanin anahtari vardi ama hicbiri bir sey cizmiyordu: hasarli
yollar bos veriyle, otekiler haritaya hic bagli degildi. Veri vardi; disariya
kutuyla sorulabilen bir uctan acilmamisti.

Kaynaklar (kural 1: her katman kaynagini yazar; yanitin `kaynak` alani):
  * Yol kapanmalari -- depo `yol_kapanmalari`. Uydu hasar analizi bitince
    kapali her yol parcasinin ORTA NOKTASI yazilir (`cekirdek._kapanmalari_depoya_yaz`).
    Cizgi degil nokta; siddet derecesi olculmuyor (J-58).
  * Depremler -- `apps/earthquake_risk/data/query.csv` katalogu. Kandilli canli
    ucundan gelir, aradaki bosluk USGS'ten (M>=4) tamamlanir (`data_manager.py`).
  * Fay hatlari -- GEM Global Active Faults (harmonized). Veri setinde ad alani
    bos oldugu icin cizgilerin adi yok.
  * Toplanma alanlari -- AFAD toplanma alanlari listesi (72 232 kayit, ulke geneli).

Kutu (bbox) ile sorulur. Kutu verilmezse depremler ve faylar Turkiye kutusundan
gelir (risk ekrani 81 ili gosterir; ulke geneli ~4 bin deprem, ~400 fay);
kapanma ve toplanma alanlari operasyon bolgelerinin kutusundan (toplanma ulke
genelinde 72 bin kayit, konsol onu gorunen bolgenin kutusuyla sorar). Dosyalar istek yolunda ayristirilmaz, bir kez bellege
alinir (kural 3). Zaman disariya milisaniye gider (sozlesme.py ile ayni karar).
"""

from __future__ import annotations

import csv
import json
import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query

import cekirdek as ck
import kimlik
from depo import aktif_depo
from uclar import yerler

yonlendirici = APIRouter(prefix="/api/katman", tags=["katmanlar"])

SAHA_VE_USTU = ("saha", "koordinator", "yonetici")
ALTLIK = Path(__file__).resolve().parents[1] / "veri" / "altlik"
# Tek istekte istenebilecek en genis kenar; kazara "butun dunya" sorgusu olmasin.
EN_GENIS_KENAR = 8.0


def _ms(sn: Optional[float]) -> Optional[float]:
    return None if sn is None else round(float(sn) * 1000.0)


def _sn(ms: Optional[float]) -> Optional[float]:
    return None if ms is None else float(ms) / 1000.0


# --- kutu ------------------------------------------------------------------

@lru_cache(maxsize=1)
def _bolge_kutusu() -> Optional[tuple[float, float, float, float]]:
    """Operasyon bolgelerini kapsayan kutu (bati, guney, dogu, kuzey). `il`
    turu altliklar sayilmaz: 81 il kutuyu Turkiye boyutuna cikarirdi."""
    yol = ALTLIK / "katalog.json"
    if not yol.exists():
        return None
    bolgeler = json.loads(yol.read_text(encoding="utf-8"))
    kutular = [b["kutu"] for b in bolgeler
               if b.get("kutu") and b.get("tur", "operasyon") == "operasyon"]
    if not kutular:
        return None
    return (
        min(k[0] for k in kutular),
        min(k[1] for k in kutular),
        max(k[2] for k in kutular),
        max(k[3] for k in kutular),
    )


def _kutu(metin: Optional[str], ulke: bool = False) -> tuple[float, float, float, float]:
    if not metin:
        if ulke:
            return ck.TURKEY_BBOX
        varsayilan = _bolge_kutusu()
        if varsayilan is None:
            raise HTTPException(422, "Kutu verilmedi ve altlik katalogu yok.")
        return varsayilan
    try:
        w, s, e, n = (float(p) for p in metin.split(","))
    except ValueError:
        raise HTTPException(422, "Kutu bicimi: bati,guney,dogu,kuzey")
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise HTTPException(422, "Kutu sinirlari gecersiz.")
    if e - w > EN_GENIS_KENAR or n - s > EN_GENIS_KENAR:
        raise HTTPException(422, f"Kutu en cok {EN_GENIS_KENAR:.0f} derece olabilir.")
    return w, s, e, n


# --- yol kapanmalari -------------------------------------------------------

def _cizgi(ek) -> Optional[list]:
    """Kapanma kaydinin `ek` alanindaki cizgi; yoksa None."""
    if not ek:
        return None
    try:
        veri = json.loads(ek) if isinstance(ek, str) else ek
    except (TypeError, ValueError):
        return None
    cizgi = veri.get("cizgi") if isinstance(veri, dict) else None
    return cizgi if isinstance(cizgi, list) and len(cizgi) >= 2 else None


@yonlendirici.get("/kapanmalar")
def kapanmalar(
    kutu: Optional[str] = Query(default=None, description="bati,guney,dogu,kuzey"),
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    sinir: int = Query(default=5000, ge=1, le=20000),
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    k = _kutu(kutu)
    kayitlar = aktif_depo().kapanma_listele(
        baslangic=_sn(baslangic), bitis=_sn(bitis), kutu=k, sinir=sinir
    )
    return {
        "kutu": list(k),
        "sayi": len(kayitlar),
        "kaynak": {
            "ad": "Uydu hasar analizi",
            "aciklama": "Kapali bulunan yol parcasi; cizgisi varsa cizgi, yoksa orta nokta.",
            "not": "Siddet derecesi hala olculmuyor; her kayda ayni deger yaziliyor (J-58).",
        },
        "kayitlar": [
            {
                "id": x["id"],
                "lon": x["lon"],
                "lat": x["lat"],
                # Parcanin kendi cizgisi [[enlem, boylam], ...] (J-58). Eski
                # kayitlarda yok: istemci o zaman noktayi cizer.
                "cizgi": _cizgi(x.get("ek")),
                "zaman": _ms(x["zaman"]),
                "kaynak": x["kaynak"],
                "analizId": x.get("analiz_id"),
            }
            for x in kayitlar
        ],
    }


# --- depremler -------------------------------------------------------------

def _zaman_ms(metin: str) -> Optional[float]:
    """'2026-08-13T05:32:45.000Z' -> epoch ms. Bozuk satir atlanir."""
    if not metin:
        return None
    try:
        t = datetime.fromisoformat(metin.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return round(t.timestamp() * 1000.0)


@lru_cache(maxsize=1)
def _deprem_katalogu():
    """query.csv bir kez okunur: kutu suzgeci icin diziler, cikti icin kayitlar."""
    yol = ck.RISK_ROOT / "data" / "query.csv"
    if not yol.exists():
        return None
    kayitlar = []
    with open(yol, encoding="utf-8", newline="") as dosya:
        for satir in csv.DictReader(dosya):
            try:
                lat = float(satir["latitude"])
                lon = float(satir["longitude"])
                buyukluk = float(satir["mag"])
            except (KeyError, TypeError, ValueError):
                continue
            zaman = _zaman_ms(satir.get("time", ""))
            if zaman is None:
                continue
            try:
                derinlik = float(satir["depth"])
            except (KeyError, TypeError, ValueError):
                derinlik = None
            kayitlar.append(
                {
                    "id": satir.get("id") or f"{zaman:.0f}-{lat:.4f}-{lon:.4f}",
                    "lon": lon,
                    "lat": lat,
                    "buyukluk": buyukluk,
                    "derinlikKm": derinlik,
                    "zaman": zaman,
                    "yer": (satir.get("place") or "").strip() or None,
                    "durum": (satir.get("status") or "").strip() or None,
                }
            )
    if not kayitlar:
        return None
    kayitlar.sort(key=lambda k: k["zaman"], reverse=True)
    return {
        "kayitlar": kayitlar,
        "lon": np.array([k["lon"] for k in kayitlar]),
        "lat": np.array([k["lat"] for k in kayitlar]),
        "buyukluk": np.array([k["buyukluk"] for k in kayitlar]),
        "ilk": min(k["zaman"] for k in kayitlar),
        "son": max(k["zaman"] for k in kayitlar),
        "dosyaTarihi": datetime.fromtimestamp(yol.stat().st_mtime, timezone.utc)
        .date()
        .isoformat(),
    }


@yonlendirici.get("/depremler")
def depremler(
    kutu: Optional[str] = Query(default=None, description="bati,guney,dogu,kuzey"),
    enAz: float = Query(default=4.0, ge=0, le=10, description="en kucuk buyukluk"),
    baslangic: Optional[float] = None,
    sinir: int = Query(default=3000, ge=1, le=20000),
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Katalogdaki depremler: kutu, en kucuk buyukluk ve baslangic zamaniyla."""
    k = _kutu(kutu, ulke=True)
    veri = _deprem_katalogu()
    if veri is None:
        raise HTTPException(503, "Deprem katalogu (query.csv) bulunamadi.")

    w, s, e, n = k
    secim = (
        (veri["lon"] >= w)
        & (veri["lon"] <= e)
        & (veri["lat"] >= s)
        & (veri["lat"] <= n)
        & (veri["buyukluk"] >= enAz)
    )
    kayitlar = [veri["kayitlar"][i] for i in np.nonzero(secim)[0]]
    if baslangic is not None:
        kayitlar = [x for x in kayitlar if x["zaman"] >= baslangic]
    toplam = len(kayitlar)
    return {
        "kutu": list(k),
        "enAz": enAz,
        "sayi": min(toplam, sinir),
        "kutudakiToplam": toplam,
        "kaynak": {
            "ad": "Deprem katalogu",
            "atif": "Kandilli Rasathanesi (canli uc) + USGS (M>=4 tamamlama)",
            "dosya": "query.csv",
            "dosyaTarihi": veri["dosyaTarihi"],
            "ilk": veri["ilk"],
            "son": veri["son"],
            "kayit": len(veri["kayitlar"]),
        },
        "kayitlar": kayitlar[:sinir],
    }


# --- fay hatlari -----------------------------------------------------------

@yonlendirici.get("/faylar")
def faylar(
    kutu: Optional[str] = Query(default=None, description="bati,guney,dogu,kuzey"),
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Kutudan gecen etkin fay cizgileri. Cizgiler [lon, lat] noktalarindan olusur."""
    k = _kutu(kutu, ulke=True)
    w, s, e, n = k
    cizgiler = []
    for i, fay in enumerate(ck._get_turkey_fault_lines()):
        nokta = [[p["longitude"], p["latitude"]] for p in fay.get("points", [])]
        if len(nokta) < 2:
            continue
        if not any(w <= lon <= e and s <= lat <= n for lon, lat in nokta):
            continue
        cizgiler.append({"id": f"fay-{i}", "cizgi": nokta})
    return {
        "kutu": list(k),
        "sayi": len(cizgiler),
        "kaynak": {
            "ad": "GEM Global Active Faults",
            "atif": "GEM Foundation, harmonized active faults",
            "lisans": "CC BY-SA 4.0",
            "not": "Veri setinde ad alani bos; cizgilerin adi yok.",
        },
        "kayitlar": cizgiler,
    }


# --- toplanma alanlari -----------------------------------------------------

@yonlendirici.get("/toplanma")
def toplanma(
    kutu: Optional[str] = Query(default=None, description="bati,guney,dogu,kuzey"),
    sinir: int = Query(default=5000, ge=1, le=20000),
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """AFAD toplanma alanlari. Afetzede ekraniyla ayni veri (`/api/yakin-yerler`),
    burada konum yerine kutu ile."""
    k = _kutu(kutu)
    w, s, e, n = k
    lat, lon, bilgi = yerler._afad()
    secim = np.nonzero((lon >= w) & (lon <= e) & (lat >= s) & (lat <= n))[0]
    kayitlar = [
        {
            "id": f"afad-{int(i)}",
            "lon": float(lon[i]),
            "lat": float(lat[i]),
            "ad": bilgi[i][0],
            "adres": bilgi[i][1],
        }
        for i in secim[:sinir]
    ]
    return {
        "kutu": list(k),
        "sayi": len(kayitlar),
        "kutudakiToplam": int(secim.size),
        "kaynak": {
            "ad": "AFAD toplanma alanlari listesi",
            "not": "Alanin su an acik ya da kullanilabilir oldugunu soylemez.",
        },
        "kayitlar": kayitlar,
    }


# --- on yukleme ------------------------------------------------------------

def _onyukle():
    """Katalog ve fay dosyasi acilista okunur: ilk istek beklemesin.

    Olculdu (24 Eylul 2026): ilk deprem istegi 362 ms, ilk fay istegi 892 ms;
    ikinciler 42 ve 11 ms. Toplanma alanlari zaten `yerler._onyukle` ile geliyor.
    """
    try:
        _bolge_kutusu()
        _deprem_katalogu()
        ck._get_turkey_fault_lines()
    except Exception as e:  # veri yoksa uc zaten 503 doner
        print(f"katman on yukleme: {e}", flush=True)


threading.Thread(target=_onyukle, name="katman-onyukleme", daemon=True).start()
