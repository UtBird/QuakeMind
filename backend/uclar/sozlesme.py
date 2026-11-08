"""Ortak cikti sozlesmesi uclari -- konsolun bagli oldugu API.

TASIMA_PLANI.md Faz 3 · CLAUDE.md kural 2:
    (konum, hasar/aciliyet skoru, guven, zaman damgasi, kaynak tipi)

Arayuz modellere degil bu sozlesmeye baglanir; yeni bir model eklemek bu uclari
degistirmez.

Birim karari: API disariya **milisaniye** (JavaScript'in kendi zamani) verir ve
alir; depo saniye tutar. Cevirme yalnizca bu dosyanin kenarinda yapilir.

Yetki: her uc `Depends` ile korunur. Afetzede yalniz kendi cagrisini gorur
(MIMARI 9, kayit duzeyinde kontrol).
"""

from __future__ import annotations

import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import canli_yayin
import kimlik
from depo import aktif_depo
from depo.sqlite_surucu import GorevHatasi, mesafe_m
from uclar.gorev_bicim import (
    EKIP_DURUMLARI,
    EKIP_TURLERI,
    ekip_cikti,
    ekipler_cikti,
    gorev_yayinla,
    gorevleri_ekle,
)

yonlendirici = APIRouter(prefix="/api", tags=["sozlesme"])

SAHA_VE_USTU = ("saha", "koordinator", "yonetici")
KOORDINASYON = ("koordinator", "yonetici")


# --- birim cevrimi ---------------------------------------------------------

def _sn(ms: Optional[float]) -> Optional[float]:
    return None if ms is None else float(ms) / 1000.0


def _ms(sn: Optional[float]) -> Optional[float]:
    return None if sn is None else round(float(sn) * 1000.0)


# --- cikti bicimleri -------------------------------------------------------

def _hasar_cikti(k: dict) -> dict:
    return {
        "id": k["id"],
        "lon": k["lon"],
        "lat": k["lat"],
        "skor": k["skor"],
        "guven": k["guven"],
        "zaman": _ms(k["zaman"]),
        "kaynak": k["kaynak"],
        "etiket": k.get("etiket"),
    }


def _sos_ek(k: dict) -> dict:
    try:
        return json.loads(k["ek"]) if k.get("ek") else {}
    except (TypeError, ValueError):
        return {}


def _sos_cikti(k: dict) -> dict:
    ek = _sos_ek(k)
    return {
        "id": k["id"],
        "lon": k["lon"],
        "lat": k["lat"],
        "oncelik": k["oncelik"],
        "durum": k["durum"],
        "zaman": _ms(k["zaman"]),
        "mahalle": k.get("mahalle"),
        "metin": k.get("metin"),
        "ekipId": k.get("ekip_id"),
        "atamaZamani": _ms(k["atama_zamani"]) if k.get("atama_zamani") else None,
        # Afetzede ekranindan gelen yapilandirilmis bilgi (yoksa None).
        "kisiSayisi": ek.get("kisiSayisi"),
        "ihtiyaclar": ek.get("ihtiyaclar"),
        # "gps", "manuel" ya da "mahalle" (mahalle merkezi, yaklasik konum).
        "konumKaynagi": ek.get("konumKaynagi"),
        "konumDogrulukM": ek.get("konumDogrulukM"),
        # False: afetzede durum secmeden SOS'a basti (tek dokunus, J-50).
        "durumSecildi": ek.get("durumSecildi"),
    }


# --- hasar noktalari -------------------------------------------------------

@yonlendirici.get("/hasar-noktalari")
def hasar_noktalari(
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    kaynak: Optional[str] = None,
    sinir: int = Query(default=20000, le=100000),
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    kayitlar = aktif_depo().hasar_listele(
        baslangic=_sn(baslangic), bitis=_sn(bitis), kaynak=kaynak, sinir=sinir
    )
    return [_hasar_cikti(k) for k in kayitlar]


# --- SOS -------------------------------------------------------------------

IHTIYACLAR = ("su", "gida", "barinma", "isinma", "ilac", "tuvalet")


class SosIstegi(BaseModel):
    lon: float
    lat: float
    oncelik: str = "kritik"
    metin: Optional[str] = Field(None, max_length=500)
    mahalle: Optional[str] = Field(None, max_length=120)
    kanal: Optional[str] = None
    # Afetzede ekrani (J-43): eskiden mesajin icine "[KISI SAYISI: 3]" diye
    # yaziliyordu; artik ekiplerin suzup siralayabilecegi alanlar.
    kisiSayisi: Optional[int] = Field(None, ge=1, le=500)
    ihtiyaclar: Optional[list[str]] = None
    konumKaynagi: Optional[str] = None
    konumDogrulukM: Optional[float] = Field(None, ge=0, le=100000)
    # Afetzede durum secmeden SOS'a bastiysa False (J-50): cagri "kritik"
    # oncelikle gelir ama ekip bunun afetzedenin secimi olmadigini gorur.
    durumSecildi: Optional[bool] = None


class AtamaIstegi(BaseModel):
    ekipId: str


@yonlendirici.get("/sos")
def sos_listesi(
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    durum: Optional[str] = None,
    kul: dict = Depends(kimlik.kullanici),
):
    # Afetzede yalniz kendi cagrisini gorur; sahada ve ustunde herkes hepsini.
    kendi = kul["id"] if kul["rol"] == "afetzede" else None
    kayitlar = aktif_depo().sos_listele(
        baslangic=_sn(baslangic), bitis=_sn(bitis), durum=durum, kullanici_id=kendi
    )
    # Hangi ekip, kac kisiyle, hangi asamada (J-54). Afetzede kendi cagrisina
    # giden ekibin adini, kisi sayisini ve gorev acikken konumunu gorur; kimin
    # atadigini ve ic notu gormez.
    return gorevleri_ekle("sos", kayitlar, [_sos_cikti(k) for k in kayitlar], afetzede=kendi is not None)


@yonlendirici.post("/sos", status_code=201)
def sos_ac(istek: SosIstegi, kul: dict = Depends(kimlik.kullanici)):
    if not (-90.0 <= istek.lat <= 90.0) or not (-180.0 <= istek.lon <= 180.0):
        raise HTTPException(status_code=422, detail="Gecersiz koordinat.")
    if istek.oncelik not in ("kritik", "yuksek", "orta"):
        raise HTTPException(status_code=422, detail="Oncelik: kritik | yuksek | orta")
    if istek.ihtiyaclar and any(i not in IHTIYACLAR for i in istek.ihtiyaclar):
        raise HTTPException(status_code=422, detail=f"Ihtiyac: {' | '.join(IHTIYACLAR)}")
    if istek.konumKaynagi not in (None, "gps", "manuel", "mahalle"):
        raise HTTPException(status_code=422, detail="konumKaynagi: gps | manuel | mahalle")
    ek = {k: v for k, v in {
        "kisiSayisi": istek.kisiSayisi,
        "ihtiyaclar": sorted(set(istek.ihtiyaclar)) if istek.ihtiyaclar else None,
        "konumKaynagi": istek.konumKaynagi,
        "konumDogrulukM": round(istek.konumDogrulukM) if istek.konumDogrulukM is not None else None,
        "durumSecildi": istek.durumSecildi,
    }.items() if v is not None}

    depo = aktif_depo()
    kayit = depo.sos_ekle(
        lon=istek.lon,
        lat=istek.lat,
        oncelik=istek.oncelik,
        metin=istek.metin,
        mahalle=istek.mahalle,
        kullanici_id=kul["id"],
        kanal=istek.kanal,
        ek=ek or None,
    )
    # Cagri ayni zamanda ortak sozlesmeye bir nokta olarak duser: birlesik isi
    # haritasinin "SOS" kanali bu noktalardan beslenir.
    depo.hasar_ekle(
        lon=istek.lon,
        lat=istek.lat,
        skor={"kritik": 1.0, "yuksek": 0.75, "orta": 0.45}[istek.oncelik],
        guven=1.0,
        kaynak="sos",
        etiket=istek.metin,
        zaman=kayit["zaman"],
    )
    canli_yayin.yayinla(
        "yeni-sos",
        id=kayit["id"],
        lon=kayit["lon"],
        lat=kayit["lat"],
        oncelik=kayit["oncelik"],
        mahalle=kayit.get("mahalle"),
    )
    return {**_sos_cikti(kayit), "gorevler": []}


def _sos_tam(kayit: dict) -> dict:
    return gorevleri_ekle("sos", [kayit], [_sos_cikti(kayit)])[0]


@yonlendirici.post("/sos/{sos_id}/ata")
def sos_ata(
    sos_id: str,
    istek: AtamaIstegi,
    kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Eski tek-ekip atamasi; artik bir sevk gorevi acar (J-54). Yalniz bekleyen
    cagri atanir (mukerrer sevk engeli). Yeni konsol `POST /api/gorevler`
    kullanir: ekip, kisi sayisi ve ek destek orada secilir."""
    from uclar.gorev import _yetki, hata_http

    depo = aktif_depo()
    cagri = depo.sos_bul(sos_id)
    if cagri is None:
        raise HTTPException(status_code=404, detail="Cagri bulunamadi.")
    if depo.ekip_bul(istek.ekipId) is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    if cagri["durum"] != "bekliyor":
        raise HTTPException(status_code=409, detail="Cagri zaten atanmis ya da kapanmis.")
    _yetki(kul, istek.ekipId)
    try:
        g = depo.gorev_ac(
            hedef_tur="sos",
            hedef_id=sos_id,
            ekip_id=istek.ekipId,
            kisi_sayisi=None,
            kisi_id=kul["id"],
            kisi_ad=kul.get("ad_soyad"),
            kaynak="ekip" if kul["rol"] == "saha" else "koordinasyon",
        )
    except GorevHatasi as h:
        raise hata_http(h) from h
    gorev_yayinla(g)
    return _sos_tam(depo.sos_bul(sos_id))


@yonlendirici.post("/sos/{sos_id}/kapat")
def sos_kapat(sos_id: str, kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU))):
    """Cagriyi kapatir. Acik gorevler de biter: olay yerindeki ekip
    'tamamlandi', yoldaki 'iptal' olur; ekip gorevde asili kalmaz (J-54)."""
    depo = aktif_depo()
    if depo.sos_bul(sos_id) is None:
        raise HTTPException(status_code=404, detail="Cagri bulunamadi.")
    kapandi, biten = depo.sos_kapat(sos_id, kul["id"], kul.get("ad_soyad"))
    if not kapandi:
        raise HTTPException(status_code=409, detail="Cagri zaten kapanmis.")
    canli_yayin.yayinla("yeni-sos", id=sos_id, durum="kapandi")
    for gorev_id in biten:
        gorev_yayinla(depo.gorev_bul(gorev_id), "kapandi")
    return _sos_tam(depo.sos_bul(sos_id))


@yonlendirici.get("/sos/{sos_id}/en-yakin-ekip")
def en_yakin_ekip(sos_id: str, _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU))):
    """Musait ekiplerin en yakini (kus ucusu). Musait ekip yoksa bos doner;
    gorevdeki ekip artik onerilmez (J-54). Konsol butun adaylari
    `GET /api/gorevler/aday-ekipler` ile alir."""
    depo = aktif_depo()
    cagri = depo.sos_bul(sos_id)
    if cagri is None:
        raise HTTPException(status_code=404, detail="Cagri bulunamadi.")
    ekip = depo.en_yakin_ekip(cagri["lon"], cagri["lat"])
    if ekip is None:
        return {"ekip": None, "mesafeM": None}
    return {
        "ekip": ekip_cikti(ekip),
        "mesafeM": round(mesafe_m(cagri["lon"], cagri["lat"], ekip["lon"], ekip["lat"])),
    }


# --- ekipler ---------------------------------------------------------------

class EkipIstegi(BaseModel):
    """Ekip tanimi (J-54). Kurum, tur ve kisi sayisi sevkte "kac kisi, hangi
    ekip" sorusunun cevabidir. `id` yalniz eski PUT cagrilari icin var."""

    id: Optional[str] = None
    ad: str = Field(..., min_length=1, max_length=60)
    kurum: Optional[str] = Field(None, max_length=60)
    tur: Optional[str] = None
    kisiSayisi: Optional[int] = Field(None, ge=1, le=500)
    lon: Optional[float] = None
    lat: Optional[float] = None
    durum: str = "musait"


class KonumIstegi(BaseModel):
    lon: float
    lat: float


class UyelerIstegi(BaseModel):
    kullaniciIdleri: list[str] = Field(default_factory=list, max_length=100)


def _ekip_dogrula(istek: EkipIstegi) -> None:
    if istek.tur is not None and istek.tur not in EKIP_TURLERI:
        raise HTTPException(status_code=422, detail=f"Tür: {' | '.join(EKIP_TURLERI)}")
    if istek.durum not in EKIP_DURUMLARI:
        raise HTTPException(status_code=422, detail=f"Durum: {' | '.join(EKIP_DURUMLARI)}")
    if (istek.lon is None) != (istek.lat is None):
        raise HTTPException(status_code=422, detail="Konum için enlem ve boylam birlikte verilmeli.")
    if istek.lat is not None and not (-90.0 <= istek.lat <= 90.0 and -180.0 <= istek.lon <= 180.0):
        raise HTTPException(status_code=422, detail="Gecersiz koordinat.")


def _tek_ekip(ekip_id: str) -> dict:
    kayit = aktif_depo().ekip_bul(ekip_id)
    if kayit is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    return ekipler_cikti([kayit])[0]


@yonlendirici.get("/ekipler")
def ekipler(_kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU))):
    """Ekipler, su anki gorevleri ve uyeleri. Gorevdeki ekip musait gorunmez."""
    return ekipler_cikti(aktif_depo().ekip_listele())


@yonlendirici.post("/ekipler", status_code=201)
def ekip_ekle(istek: EkipIstegi, _kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON))):
    _ekip_dogrula(istek)
    kayit = aktif_depo().ekip_olustur(
        ad=istek.ad.strip(),
        kurum=(istek.kurum or "").strip() or None,
        tur=istek.tur,
        kisi_sayisi=istek.kisiSayisi,
        lon=istek.lon,
        lat=istek.lat,
    )
    canli_yayin.yayinla("ekip-konumu", ekipId=kayit["id"], lon=kayit["lon"], lat=kayit["lat"])
    return _tek_ekip(kayit["id"])


@yonlendirici.get("/ekipler/uye-adaylari")
def uye_adaylari(_kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON))):
    """Ekibe baglanabilecek saha hesaplari ve su an bagli olduklari ekip."""
    return [
        {"id": u["id"], "adSoyad": u["ad_soyad"], "eposta": u["eposta"], "ekipId": u.get("ekip_id")}
        for u in aktif_depo().saha_kullanicilari()
    ]


@yonlendirici.put("/ekipler/{ekip_id}")
def ekip_kaydet(
    ekip_id: str,
    istek: EkipIstegi,
    _kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
):
    """Ekibi acar ya da gunceller. Konum verilmezse eski konum korunur.
    Gorevdeki ekip hizmet disi yapilamaz: once gorev bitmeli."""
    _ekip_dogrula(istek)
    depo = aktif_depo()
    if istek.durum == "hizmet-disi" and depo.ekibin_acik_gorevi(ekip_id) is not None:
        raise HTTPException(
            status_code=409, detail="Ekip görevde; önce görevi bitir ya da iptal et."
        )
    depo.ekip_kaydet(
        ekip_id=ekip_id,
        ad=istek.ad.strip(),
        lon=istek.lon,
        lat=istek.lat,
        durum=istek.durum,
        kurum=(istek.kurum or "").strip() or None,
        tur=istek.tur,
        kisi_sayisi=istek.kisiSayisi,
    )
    canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id, lon=istek.lon, lat=istek.lat)
    return _tek_ekip(ekip_id)


@yonlendirici.put("/ekipler/{ekip_id}/uyeler")
def ekip_uyeleri(
    ekip_id: str,
    istek: UyelerIstegi,
    _kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
):
    """Saha hesaplarini ekibe baglar: bagli kisi o ekibin gorevini kendi
    telefonundan gunceller. Baska ekipteki kisi oradan cikar."""
    depo = aktif_depo()
    if depo.ekip_bul(ekip_id) is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    saha = {u["id"] for u in depo.saha_kullanicilari()}
    if any(k not in saha for k in istek.kullaniciIdleri):
        raise HTTPException(status_code=422, detail="Yalnız saha ekibi hesapları ekibe bağlanır.")
    depo.ekip_uyelerini_ayarla(ekip_id, list(dict.fromkeys(istek.kullaniciIdleri)))
    canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id)
    return _tek_ekip(ekip_id)


@yonlendirici.post("/ekipler/{ekip_id}/konum")
def ekip_konum(
    ekip_id: str,
    istek: KonumIstegi,
    kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Ekibin konumu. Saha kullanicisi yalniz kendi ekibinin konumunu yazar
    (telefonu, sayfa acikken); koordinasyon her ekibinkini (telsizle gelen)."""
    from uclar.gorev import _yetki

    depo = aktif_depo()
    if depo.ekip_bul(ekip_id) is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    if not (-90.0 <= istek.lat <= 90.0 and -180.0 <= istek.lon <= 180.0):
        raise HTTPException(status_code=422, detail="Gecersiz koordinat.")
    _yetki(kul, ekip_id)
    depo.ekip_konum(ekip_id, istek.lon, istek.lat)
    canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id, lon=istek.lon, lat=istek.lat)
    return _tek_ekip(ekip_id)


# --- ozet ------------------------------------------------------------------

@yonlendirici.get("/ozet")
def ozet(
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """KPI sayilari sunucuda hazirlanir; istemci hesap yapmaz (MIMARI 2)."""
    depo = aktif_depo()
    b, s = _sn(baslangic), _sn(bitis)

    sos_sayilari = depo.sos_sayilari(b, s)
    hasar = depo.hasar_listele(baslangic=b, bitis=s, sinir=100000)
    kapanmalar = depo.kapanma_listele(baslangic=b, bitis=s, sinir=100000)

    uydu = [h for h in hasar if h["kaynak"] == "uydu"]
    # Ekip sayilari zaman araligina bagli degil: su anki durum (J-54).
    ekipler_simdi = ekipler_cikti(depo.ekip_listele())
    acik_gorevler = depo.gorev_listele(yalniz_acik=True)
    return {
        # Yikik/hasarli ayrimi skor esigiyle: 0,8 ustu yikik sayilir.
        "yikikYapi": sum(1 for h in uydu if h["skor"] >= 0.8),
        "hasarliYapi": sum(1 for h in uydu if h["skor"] < 0.8),
        "hasarliYol": len(kapanmalar),
        "bekleyenSos": sos_sayilari.get("bekliyor", 0),
        "atananSos": sos_sayilari.get("atandi", 0),
        "kapananSos": sos_sayilari.get("kapandi", 0),
        "ekipSayisi": len(ekipler_simdi),
        "musaitEkip": sum(1 for e in ekipler_simdi if e["musait"]),
        "gorevdekiEkip": sum(1 for e in ekipler_simdi if e["gorev"]),
        "sahadakiKisi": sum(g["kisi_sayisi"] for g in acik_gorevler),
        "kaynakSayilari": _kaynak_sayilari(hasar),
        "olusturuldu": _ms(time.time()),
    }


def _kaynak_sayilari(hasar: list[dict]) -> dict[str, int]:
    sayac: dict[str, int] = {}
    for h in hasar:
        sayac[h["kaynak"]] = sayac.get(h["kaynak"], 0) + 1
    return sayac
