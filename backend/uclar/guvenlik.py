"""Mobil kisisel guvende-durumu kaydi; yardim sevki veya SOS degildir."""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import kimlik
from depo import aktif_depo

yonlendirici = APIRouter(prefix="/api/afetzede", tags=["guvenlik"])


class GuvenlikBildirimi(BaseModel):
    status: Literal["SAFE", "NEED_HELP", "UNKNOWN"]
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    note: Optional[str] = Field(None, max_length=500)


def _cikti(kayit: dict) -> dict:
    return {
        "status": kayit["durum"],
        "latitude": kayit["lat"],
        "longitude": kayit["lon"],
        "note": kayit["not_metni"],
        "updatedAt": round(kayit["guncellendi"] * 1000),
    }


@yonlendirici.post("/guvende-durumu")
def guvende_durumu_bildir(istek: GuvenlikBildirimi, kul: dict = Depends(kimlik.kullanici)):
    """Bir kullanicinin kendi beyanini saklar, gelen kimlikle iliskilendirir.

    NEED_HELP durumu kendiliginden SOS acmaz ve ekiplere iletilmis gibi
    gosterilmez; acil yardim isteyen kisi ayrica POST /api/sos cagirir.
    """
    if (istek.latitude is None) != (istek.longitude is None):
        raise HTTPException(status_code=422, detail="Konum gonderilecekse hem latitude hem longitude gerekli.")
    kayit = aktif_depo().guvenlik_durumu_yaz(
        kul["id"], istek.status, istek.latitude, istek.longitude, istek.note,
    )
    return _cikti(kayit)


@yonlendirici.get("/guvende-durumu")
def guvende_durumu_oku(kul: dict = Depends(kimlik.kullanici)):
    kayit = aktif_depo().guvenlik_durumu_oku(kul["id"])
    return _cikti(kayit) if kayit else None
