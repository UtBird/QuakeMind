"""Oturum uclari -- yeni konsolun kimlik akisi.

TASIMA_PLANI.md Faz 2. Eski `/api/auth/*` uclari dokunulmadan duruyor; eski web
onlarla calismaya devam ediyor. Yeni konsol yalnizca buradaki uclari kullanir.

Rol istemciden GELMEZ: kayit istegi rol alani tasimaz, rol yalnizca depodan
okunur ve yalnizca yonetici degistirebilir (CLAUDE.md kural 5).
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

import kimlik
from depo import aktif_depo

yonlendirici = APIRouter(prefix="/api/oturum", tags=["oturum"])

MISAFIR_EPOSTA_ALANI = "guest.quakemind.invalid"


class KayitIstegi(BaseModel):
    eposta: str
    adSoyad: str
    sifre: str
    # Bilerek rol alani yok.


class GirisIstegi(BaseModel):
    eposta: str
    sifre: str


class RolIstegi(BaseModel):
    kullaniciId: str
    rol: str


def _profil(kayit: dict) -> dict:
    return {
        "id": kayit["id"],
        "eposta": kayit["eposta"],
        "adSoyad": kayit["ad_soyad"],
        "rol": kayit["rol"],
        "birim": kayit.get("birim"),
        "sehir": kayit.get("sehir"),
        # Saha kullanicisinin bagli oldugu ekip (J-54); yalniz gorunum icin,
        # yetkiyi her uc sunucuda kendisi kontrol eder.
        "ekipId": kayit.get("ekip_id"),
        "misafir": kayit["eposta"].endswith(f"@{MISAFIR_EPOSTA_ALANI}"),
    }


@yonlendirici.post("/misafir", status_code=201)
def misafir(yanit: Response, qm_yenileme: Optional[str] = Cookie(default=None, alias=kimlik.YENILEME_CEREZI)):
    """Acil mod icin en dusuk yetkili, kalici kimlikli misafir oturumu.

    Gecerli oturum cerezi varsa ayni hesaba erisim jetonu verir. Aksi halde
    yalniz `afetzede` rolunde yeni bir kayit acar; sifre disari verilmez.
    Boylece SOS/ihbar sahipligi ve kayit duzeyi yetkilendirme korunur.
    """
    mevcut = kimlik.cerezden_kullanici(qm_yenileme)
    if mevcut is not None:
        kayit = aktif_depo().kullanici_id(mevcut["id"])
        return {"erisimJetonu": kimlik.erisim_jetonu_uret(kayit), "kullanici": _profil(kayit)}

    kayit = aktif_depo().kullanici_olustur(
        eposta=f"misafir-{secrets.token_hex(16)}@{MISAFIR_EPOSTA_ALANI}",
        ad_soyad="Misafir",
        # Rastgele sifre yalniz sunucuda olusturulur ve hicbir yere dondurulmez.
        sifre_ozeti=kimlik.sifre_ozetle(secrets.token_urlsafe(32)),
        rol=kimlik.VARSAYILAN_ROL,
    )
    erisim = kimlik.oturum_baslat(kayit, yanit)
    return {"erisimJetonu": erisim, "kullanici": _profil(kayit)}


@yonlendirici.post("/kayit", status_code=201)
def kayit(istek: KayitIstegi, yanit: Response):
    kayit_edilen = kimlik.kullanici_kaydet(istek.eposta, istek.adSoyad, istek.sifre)
    erisim = kimlik.oturum_baslat(kayit_edilen, yanit)
    return {"erisimJetonu": erisim, "kullanici": _profil(kayit_edilen)}


@yonlendirici.post("/giris")
def giris(istek: GirisIstegi, yanit: Response):
    kayit_edilen = kimlik.giris_yap(istek.eposta, istek.sifre)
    erisim = kimlik.oturum_baslat(kayit_edilen, yanit)
    return {"erisimJetonu": erisim, "kullanici": _profil(kayit_edilen)}


@yonlendirici.post("/yenile")
def yenile(
    yanit: Response,
    qm_yenileme: Optional[str] = Cookie(default=None, alias=kimlik.YENILEME_CEREZI),
):
    sonuc = kimlik.oturum_yenile(yanit, qm_yenileme)
    return {"erisimJetonu": sonuc["erisimJetonu"], "kullanici": _profil(sonuc["kullanici"])}


@yonlendirici.post("/cikis")
def cikis(
    yanit: Response,
    qm_yenileme: Optional[str] = Cookie(default=None, alias=kimlik.YENILEME_CEREZI),
):
    kimlik.oturum_kapat(yanit, qm_yenileme)
    return {"durum": "kapandi"}


@yonlendirici.get("/ben")
def ben(kul: dict = Depends(kimlik.kullanici)):
    return {"kullanici": _profil(kul)}


@yonlendirici.post("/rol")
def rol_degistir(
    istek: RolIstegi,
    _yonetici: dict = Depends(kimlik.rol_gerektir("yonetici")),
):
    """Rol yukseltme tek kapi. Istemcinin kendi rolunu secmesi mumkun degil."""
    if istek.rol not in kimlik.ROLLER:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen rol: {istek.rol}")
    depo = aktif_depo()
    if depo.kullanici_id(istek.kullaniciId) is None:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
    depo.rol_ata(istek.kullaniciId, istek.rol)
    # Rol degisince eldeki oturumlar dusurulur.
    depo.oturumlari_iptal(istek.kullaniciId)
    return {"durum": "guncellendi", "kullaniciId": istek.kullaniciId, "rol": istek.rol}
