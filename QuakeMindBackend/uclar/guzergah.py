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
