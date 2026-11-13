"""Oturum uclari -- yeni konsolun kimlik akisi.

TASIMA_PLANI.md Faz 2. Eski `/api/auth/*` uclari dokunulmadan duruyor; eski web
onlarla calismaya devam ediyor. Yeni konsol yalnizca buradaki uclari kullanir.

Rol istemciden GELMEZ: kayit istegi rol alani tasimaz, rol yalnizca depodan
okunur ve yalnizca `/rol` ucundan degisir (CLAUDE.md kural 5): yonetici her
rolu, koordinator yalniz afetzede <-> saha gecisini yapar; kimse kendi rolunu
degistiremez (J-155).
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

import canli_yayin
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
    # Giris ekraninda secilen kapi (J-156): "afetzede" | "ekip" | "koordinasyon".
    # ROL DEGILDIR; sunucu hesabin roluyle karsilastirir. Mobil istemci gondermez.
    kapi: Optional[str] = None


class HesapAcmaIstegi(BaseModel):
    eposta: str
    adSoyad: str
    rol: str
    # Saha hesabi acilirken dogrudan baglanacagi ekip (istege bagli).
    ekipId: Optional[str] = None


class RolIstegi(BaseModel):
    kullaniciId: str
    rol: str


class HesapGuncellemeIstegi(BaseModel):
    """Hesap duzenleme cekmecesinin tek "Kaydet"i (J-157). Gonderilmeyen alan
    degismez. `ekipId: null` acikca gonderilirse kisi ekipten cikar."""
    adSoyad: Optional[str] = None
    rol: Optional[str] = None
    ekipId: Optional[str] = None
    askida: Optional[bool] = None


class SifreDegistirmeIstegi(BaseModel):
    eskiSifre: str
    yeniSifre: str


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
        # J-157: gecici sifreyle girildi; istemci zorunlu degistirme ekranina gider.
        "sifreDegismeli": bool(kayit.get("sifre_degismeli")),
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
    # Kayit ayni zamanda ilk giristir; yazilmazsa liste "hic girmedi" der.
    aktif_depo().giris_isle(kayit_edilen["id"])
    erisim = kimlik.oturum_baslat(kayit_edilen, yanit)
    return {"erisimJetonu": erisim, "kullanici": _profil(kayit_edilen)}


@yonlendirici.post("/giris")
def giris(istek: GirisIstegi, yanit: Response):
    kayit_edilen = kimlik.giris_yap(istek.eposta, istek.sifre, istek.kapi)
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
def ben(kul: dict = Depends(kimlik.kullanici_sifre_serbest)):
    return {"kullanici": _profil(kul)}


#: Kim hangi rolleri verebilir (J-155). Koordinator saha ekibini kurar: kayit
#: olmus bir gonullu (afetzede) saha ekibine alinir ya da geri cikarilir.
#: Koordinasyon rolleri (koordinator, yonetici) yalniz yoneticiden gelir.
SAHA_GECISI = frozenset({"afetzede", "saha"})


def _verebilecegi_roller(veren_rol: str) -> frozenset:
    if veren_rol == "yonetici":
        return frozenset(kimlik.ROLLER)
    if veren_rol == "koordinator":
        return SAHA_GECISI
    return frozenset()


def _kullanici_satiri(k: dict) -> dict:
    return {
        "id": k["id"],
        "eposta": k["eposta"],
        "adSoyad": k["ad_soyad"],
        "rol": k["rol"],
        "ekipId": k.get("ekip_id"),
        # epoch ms (konsolun bütün zamanlari gibi)
        "olusturuldu": int(k["olusturuldu"] * 1000) if k.get("olusturuldu") else None,
        "sonGiris": int(k["son_giris"] * 1000) if k.get("son_giris") else None,
        "askida": bool(k.get("askida")),
        "sifreDegismeli": bool(k.get("sifre_degismeli")),
    }


@yonlendirici.get("/kullanicilar")
def kullanicilar(kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici"))):
    """Rol yonetimi ekrani (J-155): hesaplar ve cagiranin verebilecegi roller.
    Sifre ozeti hicbir zaman donmez."""
    return {
        "kullanicilar": [_kullanici_satiri(k) for k in aktif_depo().kullanici_listele()],
        "verebilecegiRoller": sorted(_verebilecegi_roller(kul["rol"])),
        "benimId": kul["id"],
    }


#: Gecici sifre alfabesi: karistirilan karakterler (0/O, 1/l/I) yok; telefonda
#: okunup elle yazilacak.
_SIFRE_ALFABESI = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gecici_sifre(uzunluk: int = 12) -> str:
    return "".join(secrets.choice(_SIFRE_ALFABESI) for _ in range(uzunluk))


def _yonetebilir_mi(veren: dict, hedef: dict) -> None:
    """Rol ve sifre islemlerinin ortak kapisi: kendine yok, yetkin olmayana yok."""
    if hedef["id"] == veren["id"]:
        raise HTTPException(status_code=409, detail="Kendi hesabında bu işlemi yapamazsın.")
    if hedef["rol"] not in _verebilecegi_roller(veren["rol"]):
        raise HTTPException(
            status_code=403,
            detail="Bu hesabı yalnız yönetici yönetir (koordinatör ve yönetici hesapları).",
        )


def _hesap_yayini(kullanici_id: str, *ekip_idler: Optional[str]) -> None:
    """Acik konsollar hesap listesini, etkilenen ekip ekranlari uyelerini tazeler."""
    canli_yayin.yayinla("hesap", kullaniciId=kullanici_id)
    for ekip_id in {e for e in ekip_idler if e}:
        canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id)


@yonlendirici.post("/kullanicilar", status_code=201)
def hesap_ac(
    istek: HesapAcmaIstegi,
    veren: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Ekip ve koordinasyon hesabini koordinasyon acar (J-156). Afetzede kendi
    hesabini giris ekranindan acar; buradan acilmaz.

    Sifre sunucuda uretilir ve YALNIZ bu yanitta bir kez doner; depoda ozeti
    durur. Koordinator yalniz saha hesabi acar, yonetici koordinator/yonetici de."""
    if istek.rol not in kimlik.ROLLER or istek.rol == "afetzede":
        raise HTTPException(status_code=422, detail="Buradan yalnız ekip ya da koordinasyon hesabı açılır.")
    if istek.rol not in _verebilecegi_roller(veren["rol"]):
        raise HTTPException(status_code=403, detail="Koordinatör ve yönetici hesabını yalnız yönetici açar.")
    eposta = istek.eposta.strip().lower()
    ad = istek.adSoyad.strip()
    if "@" not in eposta or len(ad) < 2:
        raise HTTPException(status_code=422, detail="Ad soyad ve geçerli bir e-posta gerekli.")
    depo = aktif_depo()
    if istek.ekipId is not None:
        if istek.rol != "saha":
            raise HTTPException(status_code=422, detail="Ekibe yalnız saha ekibi hesabı bağlanır.")
        if depo.ekip_bul(istek.ekipId) is None:
            raise HTTPException(status_code=404, detail="Ekip bulunamadı.")
    if depo.kullanici_eposta(eposta):
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı.")
    sifre = _gecici_sifre()
    yeni = depo.kullanici_olustur(
        eposta=eposta, ad_soyad=ad, sifre_ozeti=kimlik.sifre_ozetle(sifre), rol=istek.rol
    )
    depo.sifre_ata(yeni["id"], kimlik.sifre_ozetle(sifre), degismeli=True)
    if istek.ekipId is not None:
        depo.ekibe_bagla(yeni["id"], istek.ekipId)
    depo.hesap_kaydi_ekle(veren, yeni, "hesap-acildi", {"rol": istek.rol, "ekipId": istek.ekipId})
    _hesap_yayini(yeni["id"], istek.ekipId)
    return {"kullanici": _kullanici_satiri(depo.kullanici_id(yeni["id"])), "geciciSifre": sifre}


@yonlendirici.post("/kullanicilar/{kullanici_id}/sifre")
def sifre_sifirla(
    kullanici_id: str,
    veren: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Unutulan sifre: yeni gecici sifre uretir, eldeki oturumlari dusurur.
    Sifre yalniz bu yanitta bir kez doner."""
    depo = aktif_depo()
    hedef = depo.kullanici_id(kullanici_id)
    if hedef is None:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
    _yonetebilir_mi(veren, hedef)
    sifre = _gecici_sifre()
    depo.sifre_ata(kullanici_id, kimlik.sifre_ozetle(sifre), degismeli=True)
    depo.oturumlari_iptal(kullanici_id)
    depo.hesap_kaydi_ekle(veren, hedef, "sifre-yenilendi")
    _hesap_yayini(kullanici_id)
    return {"kullaniciId": kullanici_id, "geciciSifre": sifre}


@yonlendirici.patch("/kullanicilar/{kullanici_id}")
def hesap_guncelle(
    kullanici_id: str,
    istek: HesapGuncellemeIstegi,
    veren: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Hesap duzenleme cekmecesinin "Kaydet"i (J-157): ad, rol, ekip ve aski tek
    istekte. Once hepsi denetlenir, sonra uygulanir; bir alan reddedilirse hicbiri
    degismez. Her degisiklik kayit defterine ayri satir olarak yazilir."""
    depo = aktif_depo()
    hedef = depo.kullanici_id(kullanici_id)
    if hedef is None:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
    _yonetebilir_mi(veren, hedef)
    gonderilen = istek.model_fields_set
    izinli = _verebilecegi_roller(veren["rol"])

    # --- denetim (hicbir sey yazilmadan) ---
    yeni_ad = istek.adSoyad.strip() if "adSoyad" in gonderilen and istek.adSoyad is not None else None
    if yeni_ad is not None and len(yeni_ad) < 2:
        raise HTTPException(status_code=422, detail="Ad soyad en az 2 harf olmalı.")
    yeni_rol = istek.rol if "rol" in gonderilen and istek.rol is not None else None
    if yeni_rol is not None:
        if yeni_rol not in kimlik.ROLLER:
            raise HTTPException(status_code=422, detail=f"Bilinmeyen rol: {yeni_rol}")
        if yeni_rol not in izinli:
            raise HTTPException(
                status_code=403,
                detail="Koordinatör yalnız afetzede ile saha ekibi arasında geçiş yapar; "
                       "koordinatör ve yönetici rolünü yönetici verir.",
            )
    son_rol = yeni_rol or hedef["rol"]
    ekip_degisiyor = "ekipId" in gonderilen
    if ekip_degisiyor and istek.ekipId is not None:
        if son_rol != "saha":
            raise HTTPException(status_code=422, detail="Ekibe yalnız saha ekibi hesabı bağlanır.")
        if depo.ekip_bul(istek.ekipId) is None:
            raise HTTPException(status_code=404, detail="Ekip bulunamadı.")

    # --- uygulama ---
    degisen: list[str] = []
    eski_ekip = hedef.get("ekip_id")
    if yeni_ad is not None and yeni_ad != hedef["ad_soyad"]:
        depo.ad_ata(kullanici_id, yeni_ad)
        depo.hesap_kaydi_ekle(veren, hedef, "ad-degisti", {"once": hedef["ad_soyad"], "sonra": yeni_ad})
        degisen.append("ad")
    if yeni_rol is not None and yeni_rol != hedef["rol"]:
        depo.rol_ata(kullanici_id, yeni_rol)  # saha disina cikan ekipten de cikar
        depo.hesap_kaydi_ekle(veren, hedef, "rol-degisti", {"once": hedef["rol"], "sonra": yeni_rol})
        degisen.append("rol")
    guncel_ekip = depo.kullanici_id(kullanici_id).get("ekip_id")
    if ekip_degisiyor and istek.ekipId != guncel_ekip:
        if istek.ekipId is None:
            depo.ekipten_cikar(kullanici_id)
        else:
            depo.ekibe_bagla(kullanici_id, istek.ekipId)
        depo.hesap_kaydi_ekle(veren, hedef, "ekip-degisti", {"once": guncel_ekip, "sonra": istek.ekipId})
        degisen.append("ekip")
    elif guncel_ekip != eski_ekip:
        # Rol degisimi kisiyi ekipten cikardiysa bu da kayda gecsin.
        depo.hesap_kaydi_ekle(veren, hedef, "ekip-degisti", {"once": eski_ekip, "sonra": guncel_ekip})
        degisen.append("ekip")
    if "askida" in gonderilen and istek.askida is not None and bool(istek.askida) != bool(hedef.get("askida")):
        depo.askiya_al(kullanici_id, istek.askida)
        depo.hesap_kaydi_ekle(veren, hedef, "askiya-alindi" if istek.askida else "etkinlestirildi")
        degisen.append("askida")
    if "rol" in degisen or "askida" in degisen:
        # Yeni rol / aski bir sonraki istekte sunucudan okunur; acik oturumlar duser.
        depo.oturumlari_iptal(kullanici_id)
    if degisen:
        _hesap_yayini(kullanici_id, eski_ekip, depo.kullanici_id(kullanici_id).get("ekip_id"))
    return {"kullanici": _kullanici_satiri(depo.kullanici_id(kullanici_id)), "degisen": degisen}


@yonlendirici.post("/sifre")
def sifre_degistir(
    istek: SifreDegistirmeIstegi,
    yanit: Response,
    kul: dict = Depends(kimlik.kullanici_sifre_serbest),
):
    """Kisinin kendi sifresini degistirmesi. Gecici sifreyle giren burada
    degistirmeden baska hicbir ucu kullanamaz (J-157). Butun eski oturumlar
    duser, bu cihaza yeni oturum verilir."""
    depo = aktif_depo()
    tam = depo.kullanici_id(kul["id"])
    if not kimlik.sifre_dogrula(istek.eskiSifre, tam["sifre_ozeti"]):
        # 400: 401 olsaydi istemci jeton yenileyip ayni istegi tekrar gonderirdi.
        raise HTTPException(status_code=400, detail="Şu anki şifre hatalı.")
    if len(istek.yeniSifre) < 8:
        raise HTTPException(status_code=422, detail="Yeni şifre en az 8 karakter olmalı.")
    if istek.yeniSifre == istek.eskiSifre:
        raise HTTPException(status_code=422, detail="Yeni şifre eskisiyle aynı olamaz.")
    depo.sifre_ata(kul["id"], kimlik.sifre_ozetle(istek.yeniSifre), degismeli=False)
    depo.oturumlari_iptal(kul["id"])
    depo.hesap_kaydi_ekle(kul, kul, "sifre-degistirildi", {"geciciydi": bool(tam.get("sifre_degismeli"))})
    _hesap_yayini(kul["id"])
    guncel = depo.kullanici_id(kul["id"])
    guncel.pop("sifre_ozeti", None)
    erisim = kimlik.oturum_baslat(guncel, yanit)
    return {"erisimJetonu": erisim, "kullanici": _profil(guncel)}


@yonlendirici.get("/hesap-kayitlari")
def hesap_kayitlari(
    kullaniciId: Optional[str] = None,
    sinir: int = 100,
    _kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Kayit defteri (J-157): kim, kime, ne zaman, ne yapti. Silinmez."""
    sinir = max(1, min(sinir, 500))
    return [
        {
            "id": k["id"],
            "zaman": int(k["zaman"] * 1000),
            "yapanId": k["yapan_id"],
            "yapanAd": k["yapan_ad"],
            "hedefId": k["hedef_id"],
            "hedefAd": k["hedef_ad"],
            "hedefEposta": k["hedef_eposta"],
            "islem": k["islem"],
            "ayrinti": k["ayrinti"],
        }
        for k in aktif_depo().hesap_kayitlari(kullaniciId, sinir)
    ]


@yonlendirici.post("/rol")
def rol_degistir(
    istek: RolIstegi,
    veren: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Rol degistirmenin tek kapisi. Istemci KENDI rolunu secemez (kural 5):
    kayit ucu rol almaz, burada da kisi kendi rolunu degistiremez.

    Yonetici her rolu verir. Koordinator yalniz afetzede <-> saha gecisi yapar;
    koordinasyon rolundeki birine dokunamaz."""
    if istek.rol not in kimlik.ROLLER:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen rol: {istek.rol}")
    depo = aktif_depo()
    hedef = depo.kullanici_id(istek.kullaniciId)
    if hedef is None:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
    if hedef["id"] == veren["id"]:
        # Son yoneticinin kendini dusurmesi de boylece imkansiz.
        raise HTTPException(status_code=409, detail="Kendi rolünü değiştiremezsin.")
    izinli = _verebilecegi_roller(veren["rol"])
    if istek.rol not in izinli or hedef["rol"] not in izinli:
        raise HTTPException(
            status_code=403,
            detail="Koordinatör yalnız afetzede ile saha ekibi arasında geçiş yapar; "
                   "koordinatör ve yönetici rolünü yönetici verir.",
        )
    onceki = hedef["rol"]
    if onceki != istek.rol:
        depo.rol_ata(istek.kullaniciId, istek.rol)
        # Rol degisince eldeki oturumlar dusurulur: yeni rol bir sonraki
        # giriste sunucudan okunur.
        depo.oturumlari_iptal(istek.kullaniciId)
        depo.hesap_kaydi_ekle(veren, hedef, "rol-degisti", {"once": onceki, "sonra": istek.rol})
        _hesap_yayini(istek.kullaniciId, hedef.get("ekip_id"))
    return {
        "durum": "guncellendi" if onceki != istek.rol else "degismedi",
        "kullaniciId": istek.kullaniciId,
        "rol": istek.rol,
        "oncekiRol": onceki,
    }
