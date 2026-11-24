"""Konsol "Yol ve rota" uclari (J-171): iki nokta arasi arac rotasi ve en
yakin hastane / toplanma alani.

Motor `arac_rotasi.py` (kenar tabanli Dijkstra: tek yon, gobek, donus yasagi,
donus bedeli, hasar ve kapanma cezasi). Sevk ve gorev ekranlari ayni motoru
kullanir; konsol ile saha ayni rotayi gorur.

Kapsama: bes sehrin yol agi ve aralarindaki ana yollar. Disindaki nokta icin
rota uydurulmaz; uc 422 ile bunu soyler.
"""
from __future__ import annotations

import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import arac_rotasi
import hiz_siniri
import kimlik

yonlendirici = APIRouter()

ROLLER = ("koordinator", "yonetici", "saha")
# En yakin yer: once kus ucusu en yakin bu kadar aday, sonra yoldan siralanir.
ADAY_SAYISI = 25


class GuzergahIstegi(BaseModel):
    basLon: float = Field(..., ge=-180, le=180)
    basLat: float = Field(..., ge=-90, le=90)
    hedefLon: float = Field(..., ge=-180, le=180)
    hedefLat: float = Field(..., ge=-90, le=90)
    kacin: bool = True


class EnYakinIstegi(BaseModel):
    basLon: float = Field(..., ge=-180, le=180)
    basLat: float = Field(..., ge=-90, le=90)
    tur: Literal["hastane", "toplanma"]
    kacin: bool = True
    adet: int = Field(3, ge=1, le=5)


def _kus(lon1, lat1, lon2, lat2) -> float:
    kx = 111320.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot((lon2 - lon1) * kx, (lat2 - lat1) * 110574.0)


AG_DISI = ("Bu nokta yol ağımızın dışında. Rota beş şehrin (Antakya, Kahramanmaraş, Gaziantep, "
           "Malatya, Adıyaman) yol ağında ve aralarındaki ana yollarda hesaplanır.")


@yonlendirici.post("/api/guzergah")
def guzergah(istek: GuzergahIstegi, kul: dict = Depends(kimlik.rol_gerektir(*ROLLER))):
    hiz_siniri.rota_kontrol(kul["id"])
    r = arac_rotasi.rota(istek.basLon, istek.basLat, istek.hedefLon, istek.hedefLat, kacin=istek.kacin)
    if r is None:
        raise HTTPException(status_code=422, detail=AG_DISI)
    r["kusUcusuM"] = round(_kus(istek.basLon, istek.basLat, istek.hedefLon, istek.hedefLat))
    r["kacin"] = istek.kacin
    return r


EN_COK_DURAK = 10


class Durak(BaseModel):
    lon: float = Field(..., ge=-180, le=180)
    lat: float = Field(..., ge=-90, le=90)


class DuraklarIstegi(BaseModel):
    noktalar: list[Durak] = Field(..., min_length=2, max_length=EN_COK_DURAK)
    kacin: bool = True


@yonlendirici.post("/api/guzergah/duraklar")
def guzergah_duraklar(istek: DuraklarIstegi, kul: dict = Depends(kimlik.rol_gerektir(*ROLLER))):
    """Sirali duraklar arasi arac rotasi (J-190): 1 -> 2 -> ... -> n.
    Her bacak iki nokta rotasiyla AYNI motordan gecer; sira kullanicinindir,
    yeniden siralanmaz (en kisa tur problemi cozulmez, bilerek: ekip hangi
    sirayla gidecegini koordinasyon belirler). Bir bacak agin disindaysa hangi
    bacak oldugu soylenir. Hiz siniri istek basina bir kez sayilir; durak
    sayisi en cok EN_COK_DURAK."""
    hiz_siniri.rota_kontrol(kul["id"])
    bacaklar = []
    for i, (a, b) in enumerate(zip(istek.noktalar, istek.noktalar[1:]), start=1):
        r = arac_rotasi.rota(a.lon, a.lat, b.lon, b.lat, kacin=istek.kacin)
        if r is None:
            raise HTTPException(status_code=422, detail=f"{i}. bacak ({i} → {i + 1}) yol ağının dışında. " + AG_DISI)
        r["kusUcusuM"] = round(_kus(a.lon, a.lat, b.lon, b.lat))
        bacaklar.append(r)
    rota: list = []
    for r in bacaklar:
        # Ardisik bacaklarin ortak ucu iki kez yazilmasin.
        rota.extend(r["rota"][1:] if rota and r["rota"] and r["rota"][0] == rota[-1] else r["rota"])
    return {
        "rota": rota,
        "mesafeM": sum(r["mesafeM"] for r in bacaklar),
        "sureDk": sum(r["sureDk"] for r in bacaklar),
        "kapanmadanGecer": sum(r["kapanmadanGecer"] for r in bacaklar),
        "riskliM": sum(r["riskliM"] for r in bacaklar),
        "kacin": istek.kacin,
        "bacaklar": [
            {k: r[k] for k in ("mesafeM", "sureDk", "kapanmadanGecer", "riskliM", "kusUcusuM", "adimlar",
                               "baslangicKapanmada", "hedefKapanmada") if k in r}
            for r in bacaklar
        ],
        "ag": bacaklar[0].get("ag"),
        "hasar": bacaklar[0].get("hasar"),
    }


@yonlendirici.post("/api/guzergah/en-yakin")
def en_yakin(istek: EnYakinIstegi, kul: dict = Depends(kimlik.rol_gerektir(*ROLLER))):
    hiz_siniri.rota_kontrol(kul["id"])
    from uclar import yerler

    if arac_rotasi.bolge_bul(istek.basLon, istek.basLat) is None:
        raise HTTPException(status_code=422, detail=AG_DISI)
    if istek.tur == "hastane":
        h = yerler._hizmetler()
        adaylar = [
            {"ad": y.get("ad") or "Adsız hastane", "lon": y["lon"], "lat": y["lat"], "osm": y.get("osm")}
            for y in (h[0]["yerler"] if h else []) if y["tur"] == "hastane"
        ]
        kaynak = "OpenStreetMap (hastane); kayıttır, şu an açık olduğunu göstermez."
    else:
        enlem, boylam, bilgi = yerler._afad()
        adaylar = [{"ad": b[0], "adres": b[1], "lon": float(lo), "lat": float(la)}
                   for la, lo, b in zip(enlem, boylam, bilgi)]
        kaynak = "AFAD toplanma alanları listesi; kayıttır, alanın şu an güvenli olduğunu göstermez."
    for a in adaylar:
        a["kusUcusuM"] = round(_kus(istek.basLon, istek.basLat, a["lon"], a["lat"]))
    adaylar.sort(key=lambda a: a["kusUcusuM"])
    sonuc = arac_rotasi.en_yakinlar(istek.basLon, istek.basLat, adaylar[:ADAY_SAYISI], n=istek.adet,
                                    kacin=istek.kacin)
    return {"yerler": sonuc, "kaynak": kaynak, "aday": min(len(adaylar), ADAY_SAYISI)}


@yonlendirici.get("/api/guzergah/kunye")
def kunye(_kul: dict = Depends(kimlik.rol_gerektir(*ROLLER))):
    k = arac_rotasi.kaynak() or {}
    return {
        **k,
        "sehirler": [{"id": b["id"], "ad": b["ad"], "kutu": b["kutu"]} for b in arac_rotasi.katalog()],
        "genel": (arac_rotasi.genel_bilgi() or {}).get("kutu"),
    }
