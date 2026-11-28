"""Esitleme uclari (esitleme.py, OPTIMIZASYON madde 31).

Merkezde (dugum anahtariyla, kullanici jetonu degil):
  POST /api/esitleme/al     dugumun degisiklikleri
  GET  /api/esitleme/ver    dugume gidecek hasar/kapanma degisiklikleri
Kullaniciya (koordinator, yonetici):
  GET  /api/esitleme/durum  bu sunucunun rolu ve esitleme durumu
  POST /api/esitleme/simdi  dugumde beklemeyi kesip hemen dener
  GET  /api/esitleme/gelen  merkezde dugumlerden gelen ham kayitlar
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import esitleme
import kimlik
from depo import aktif_depo

yonlendirici = APIRouter(prefix="/api/esitleme", tags=["esitleme"])
_KOORDINASYON = ("koordinator", "yonetici")


class Kayit(BaseModel):
    sira: int = Field(..., ge=1)
    tablo: str = Field(..., max_length=40)
    veri: dict


class AlIstegi(BaseModel):
    kayitlar: list[Kayit] = Field(..., max_length=500)


@yonlendirici.post("/al")
def al(istek: AlIstegi, dugum: str = Depends(esitleme.dugum_dogrula)):
    """Dugumun gonderdigi kayitlar. Ayni kayit iki kez gelirse (yanit
    kaybolmus, dugum yeniden gondermis) bir kez sayilir."""
    sonuc = aktif_depo().gelen_kaydet(dugum, [k.model_dump() for k in istek.kayitlar])
    return {"dugum": dugum, **sonuc}


@yonlendirici.get("/ver")
def ver(
    sonra: int = Query(0, ge=0),
    n: int = Query(500, ge=1, le=1000),
    dugum: str = Depends(esitleme.dugum_dogrula),
):
    return aktif_depo().degisimler_sonra(sonra, n, haric_dugum=dugum, merkez_adi=esitleme.merkez_adi())


@yonlendirici.get("/durum")
def durum(_kul: dict = Depends(kimlik.rol_gerektir(*_KOORDINASYON))):
    rol = esitleme.rol()
    if rol == "dugum" and esitleme.esitleyici() is not None:
        return esitleme.esitleyici().durum()
    if rol == "merkez":
        return {"rol": "merkez", "dugumler": sorted(set(esitleme.dugumler().values())),
                "gelen": aktif_depo().gelen_ozeti()}
    return {"rol": rol, "not": "Eşitleme kapalı: QUAKEMIND_MERKEZ_URL ya da QUAKEMIND_ESITLEME_DUGUMLERI verilmemiş."}


@yonlendirici.post("/simdi")
def simdi(_kul: dict = Depends(kimlik.rol_gerektir(*_KOORDINASYON))):
    e = esitleme.esitleyici()
    if e is None:
        raise HTTPException(status_code=409, detail="Bu sunucu merkeze bağlı bir düğüm değil.")
    e.simdi()
    return {"tamam": True}


@yonlendirici.get("/gelen")
def gelen(
    dugum: Optional[str] = Query(None, max_length=40),
    tablo: Optional[str] = Query(None, pattern="^(hasar_noktalari|yol_kapanmalari|sos_cagrilari|ihbarlar)$"),
    sinir: int = Query(100, ge=1, le=1000),
    _kul: dict = Depends(kimlik.rol_gerektir(*_KOORDINASYON)),
):
    """Merkezde: dugumlerden gelen kayitlarin son hali (SOS ve ihbar dahil)."""
    if esitleme.rol() != "merkez":
        raise HTTPException(status_code=409, detail="Bu sunucu merkez değil.")
    return {"kayitlar": aktif_depo().gelen_listele(dugum, tablo, sinir)}
