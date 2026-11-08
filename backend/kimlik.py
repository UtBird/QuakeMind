"""Kimlik ve yetki.

TASIMA_PLANI.md Faz 2 / MIMARI.md 9 / CLAUDE.md kural 5.

Kurallar burada kodla sabitlenmistir:
  * Rol ASLA istemciden gelmez. Kayit ucu rol alanini okumaz; herkes `afetzede`
    olarak acilir, yukseltmeyi yalnizca yonetici yapar.
  * Erisim jetonu kisa omurlu ve imzalidir (HS256); yenileme jetonu httpOnly
    cerezde tasinir, depoda yalnizca ozeti durur.
  * Jeton URL'de tasinmaz; Authorization basligindan ya da cerezden okunur.
  * Her korunan ucta `Depends(kullanici)` / `Depends(rol_gerektir(...))` bulunur.

Eski `/api/auth/*` uclari bu dosyayi kullanmaz; onlar oldugu gibi kalir ve
konsol devralinca silinecektir (bkz. TASIMA_PLANI.md Faz 2).
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Response

from depo import aktif_depo

# --- ayarlar ---------------------------------------------------------------

ROLLER = ("afetzede", "saha", "koordinator", "yonetici")
VARSAYILAN_ROL = "afetzede"

ERISIM_OMRU_SN = 15 * 60          # kisa omurlu erisim jetonu
YENILEME_OMRU_SN = 7 * 24 * 3600  # httpOnly cerezdeki yenileme jetonu
YENILEME_CEREZI = "qm_yenileme"

_GIZLI_ANAHTAR = os.environ.get("QUAKEMIND_JWT_ANAHTARI")
if not _GIZLI_ANAHTAR:
    # Gelistirmede her acilista yeni anahtar: sunucu yeniden baslayinca
    # eldeki erisim jetonlari gecersiz olur, bu bilincli bir tercihtir.
    # Uretimde QUAKEMIND_JWT_ANAHTARI ortam degiskeniyle sabitlenir.
    _GIZLI_ANAHTAR = secrets.token_urlsafe(48)

ALGORITMA = "HS256"


# --- sifre -----------------------------------------------------------------

def sifre_ozetle(sifre: str) -> str:
    return bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def sifre_dogrula(sifre: str, ozet: str) -> bool:
    try:
        return bcrypt.checkpw(sifre.encode("utf-8"), ozet.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- jetonlar --------------------------------------------------------------

def erisim_jetonu_uret(kullanici: dict) -> str:
    simdi = int(time.time())
    govde = {
        "sub": kullanici["id"],
        "rol": kullanici["rol"],
        "eposta": kullanici["eposta"],
        "iat": simdi,
        "exp": simdi + ERISIM_OMRU_SN,
        "tip": "erisim",
    }
    return jwt.encode(govde, _GIZLI_ANAHTAR, algorithm=ALGORITMA)


def erisim_jetonu_coz(jeton: str) -> dict:
    try:
        govde = jwt.decode(jeton, _GIZLI_ANAHTAR, algorithms=[ALGORITMA])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum suresi doldu.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Gecersiz oturum.")
    if govde.get("tip") != "erisim":
        raise HTTPException(status_code=401, detail="Gecersiz jeton tipi.")
    return govde


def yenileme_jetonu_uret(kullanici_id: str) -> tuple[str, str]:
    """(jeton, ozet) dondurur. Depoda yalnizca ozet saklanir."""
    jeton = secrets.token_urlsafe(48)
    return jeton, _ozet(jeton)


def _ozet(jeton: str) -> str:
    return hashlib.sha256(jeton.encode("utf-8")).hexdigest()


def yenileme_cerezi_yaz(yanit: Response, jeton: str) -> None:
    yanit.set_cookie(
        YENILEME_CEREZI,
        jeton,
        max_age=YENILEME_OMRU_SN,
        httponly=True,
        samesite="lax",
        # Gelistirmede http://127.0.0.1 kullaniliyor; uretimde HTTPS sart.
        secure=os.environ.get("QUAKEMIND_CEREZ_GUVENLI", "0") == "1",
        path="/api",
    )


def yenileme_cerezi_sil(yanit: Response) -> None:
    yanit.delete_cookie(YENILEME_CEREZI, path="/api")


# --- bagimliliklar ---------------------------------------------------------

def _jetonu_al(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Oturum acilmamis.")
    return authorization.split(" ", 1)[1].strip()


def kullanici(authorization: Optional[str] = Header(default=None)) -> dict:
    """Korunan uclarin temel bagimliligi.

    Rol, jetonun govdesinden DEGIL depodan okunur: bir kullanicinin rolu
    degistirildiginde eldeki jeton eski rolu tasimaya devam etmesin.
    """
    govde = erisim_jetonu_coz(_jetonu_al(authorization))
    kayit = aktif_depo().kullanici_id(govde["sub"])
    if kayit is None:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi.")
    kayit.pop("sifre_ozeti", None)
    return kayit


def rol_gerektir(*izinli: str):
    """Kullanim: `Depends(rol_gerektir("koordinator", "yonetici"))`"""
    gecersiz = [r for r in izinli if r not in ROLLER]
    if gecersiz:
        raise ValueError(f"Bilinmeyen rol: {gecersiz}")

    def kontrol(kul: dict = Depends(kullanici)) -> dict:
        if kul["rol"] not in izinli:
            raise HTTPException(status_code=403, detail="Bu islem icin yetkiniz yok.")
        return kul

    return kontrol


def istege_bagli_kullanici(authorization: Optional[str] = Header(default=None)) -> Optional[dict]:
    """Acik uclarda kimlik varsa okur, yoksa None doner (401 atmaz)."""
    if not authorization:
        return None
    try:
        return kullanici(authorization)
    except HTTPException:
        return None


# --- eski uclar (J-53) -----------------------------------------------------

ESKI_UC_DEGISKENI = "QUAKEMIND_ESKI_UCLAR"


def eski_uclar_acik() -> bool:
    """Eski webin bagli oldugu uclar acik mi (varsayilan: kapali)."""
    return os.environ.get(ESKI_UC_DEGISKENI, "0") == "1"


def eski_uc():
    """Yalniz eski webin kullandigi uclarin bagimliligi.

    Bu uclar oturumsuz yanit veriyordu: vatandas ihbarinin metni, konumu ve SOS
    listesi adresi bilen herkese aciktı (J-53). Yeni konsol hicbirini
    kullanmiyor. Varsayilan olarak KAPALILAR; eski webi gostermek gerekirse
    `QUAKEMIND_ESKI_UCLAR=1` ile acilir. Kapaliyken 404 doner: ucun varligi da
    disariya sizmasin.
    """
    if not eski_uclar_acik():
        raise HTTPException(
            status_code=404,
            detail=f"Bu uc kapali (J-53). Acmak icin {ESKI_UC_DEGISKENI}=1.",
        )


# --- oturum islemleri ------------------------------------------------------

def kullanici_kaydet(eposta: str, ad_soyad: str, sifre: str) -> dict:
    """Rol parametresi YOKTUR (kural 5). Herkes afetzede olarak acilir."""
    depo = aktif_depo()
    if depo.kullanici_eposta(eposta):
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayitli.")
    if len(sifre) < 8:
        raise HTTPException(status_code=422, detail="Sifre en az 8 karakter olmali.")
    return depo.kullanici_olustur(
        eposta=eposta,
        ad_soyad=ad_soyad,
        sifre_ozeti=sifre_ozetle(sifre),
        rol=VARSAYILAN_ROL,
    )


def giris_yap(eposta: str, sifre: str) -> dict:
    """Bilinmeyen e-posta OTOMATIK KAYDEDILMEZ; 401 doner."""
    depo = aktif_depo()
    kayit = depo.kullanici_eposta(eposta)
    if not kayit or not sifre_dogrula(sifre, kayit["sifre_ozeti"]):
        # Kullanicinin var olup olmadigi disari sizmasin diye tek mesaj.
        raise HTTPException(status_code=401, detail="E-posta veya sifre hatali.")
    depo.giris_isle(kayit["id"])
    kayit.pop("sifre_ozeti", None)
    return kayit


def oturum_baslat(kullanici_kaydi: dict, yanit: Response) -> str:
    jeton, ozet = yenileme_jetonu_uret(kullanici_kaydi["id"])
    aktif_depo().oturum_ac(kullanici_kaydi["id"], ozet, YENILEME_OMRU_SN)
    yenileme_cerezi_yaz(yanit, jeton)
    return erisim_jetonu_uret(kullanici_kaydi)


def cerezden_kullanici(cerez: Optional[str]) -> Optional[dict]:
    """Yenileme cerezinden oturum sahibini bulur, jetonu DONDURMEDEN.

    Canli akis (EventSource) baslik gonderemez; kimligi ayni kokenden giden
    httpOnly cerezle kanitlar (J-42). Gecersiz ya da suresi dolmussa None."""
    if not cerez:
        return None
    depo = aktif_depo()
    oturum = depo.oturum_bul(_ozet(cerez))
    if not oturum:
        return None
    kayit = depo.kullanici_id(oturum["kullanici_id"])
    if not kayit:
        return None
    return {"id": kayit["id"], "rol": kayit["rol"]}


def oturum_yenile(yanit: Response, cerez: Optional[str] = Cookie(default=None, alias=YENILEME_CEREZI)) -> dict:
    if not cerez:
        raise HTTPException(status_code=401, detail="Yenileme jetonu yok.")
    depo = aktif_depo()
    oturum = depo.oturum_bul(_ozet(cerez))
    if not oturum:
        raise HTTPException(status_code=401, detail="Yenileme jetonu gecersiz ya da suresi dolmus.")
    kayit = depo.kullanici_id(oturum["kullanici_id"])
    if not kayit:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi.")

    # Donusumlu jeton: her yenilemede eski jeton iptal edilir.
    depo.oturum_iptal(oturum["jeton_ozeti"])
    kayit.pop("sifre_ozeti", None)
    return {"erisimJetonu": oturum_baslat(kayit, yanit), "kullanici": kayit}


def oturum_kapat(yanit: Response, cerez: Optional[str]) -> None:
    if cerez:
        aktif_depo().oturum_iptal(_ozet(cerez))
    yenileme_cerezi_sil(yanit)
