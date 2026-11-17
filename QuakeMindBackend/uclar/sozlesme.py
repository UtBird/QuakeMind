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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
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
        # "gps" ya da "mahalle" (mahalle merkezi, yaklasik konum).
        "konumKaynagi": ek.get("konumKaynagi"),
        "konumDogrulukM": ek.get("konumDogrulukM"),
        # False: afetzede durum secmeden SOS'a basti (tek dokunus, J-50).
        "durumSecildi": ek.get("durumSecildi"),
        # Acik cagri yeniden gonderildiyse (J-167 S-2): kac kez, en son ne zaman.
        "guncellemeSayisi": ek.get("guncellemeSayisi") or 0,
        "sonGuncelleme": _ms(ek["sonGuncelleme"]) if ek.get("sonGuncelleme") else None,
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
    import islem_kaydi

    islem_kaydi.goruntuleme(kul, "sos_listesi", ayrinti={"kayitSayisi": len(kayitlar), "durum": durum})
    # Hangi ekip, kac kisiyle, hangi asamada (J-54). Afetzede kendi cagrisina
    # giden ekibin adini, kisi sayisini ve gorev acikken konumunu gorur; kimin
    # atadigini ve ic notu gormez.
    return gorevleri_ekle("sos", kayitlar, [_sos_cikti(k) for k in kayitlar], afetzede=kendi is not None)


@yonlendirici.post("/sos", status_code=201)
def sos_ac(
    istek: SosIstegi,
    yanit: Response,
    http: Request,
    kul: dict = Depends(kimlik.kullanici),
):
    """Hesap basina tek acik SOS (J-167 S-2): acik cagrin varken yeniden basarsan
    yeni satir acilmaz, o cagri guncellenir ve 200 doner (yeni cagri 201).
    Ayrica hesap ve adres basina dakikalik sinir (429)."""
    if not (-90.0 <= istek.lat <= 90.0) or not (-180.0 <= istek.lon <= 180.0):
        raise HTTPException(status_code=422, detail="Gecersiz koordinat.")
    if istek.oncelik not in ("kritik", "yuksek", "orta"):
        raise HTTPException(status_code=422, detail="Oncelik: kritik | yuksek | orta")
    if istek.ihtiyaclar and any(i not in IHTIYACLAR for i in istek.ihtiyaclar):
        raise HTTPException(status_code=422, detail=f"Ihtiyac: {' | '.join(IHTIYACLAR)}")
    if istek.konumKaynagi not in (None, "gps", "mahalle"):
        raise HTTPException(status_code=422, detail="konumKaynagi: gps | mahalle")
    ek = {k: v for k, v in {
        "kisiSayisi": istek.kisiSayisi,
        "ihtiyaclar": sorted(set(istek.ihtiyaclar)) if istek.ihtiyaclar else None,
        "konumKaynagi": istek.konumKaynagi,
        "konumDogrulukM": round(istek.konumDogrulukM) if istek.konumDogrulukM is not None else None,
        "durumSecildi": istek.durumSecildi,
    }.items() if v is not None}

    import hiz_siniri

    hiz_siniri.sos_kontrol(kul["id"], hiz_siniri.istemci_ip(http))
    depo = aktif_depo()
    kayit, guncellendi = depo.sos_ac_ya_da_guncelle(
        lon=istek.lon,
        lat=istek.lat,
        oncelik=istek.oncelik,
        metin=istek.metin,
        mahalle=istek.mahalle,
        kullanici_id=kul["id"],
        kanal=istek.kanal,
        ek=ek or None,
    )
    if guncellendi:
        # Isi haritasi ve kuyruk kisiyi bir kez sayar: yeni nokta yazilmaz.
        yanit.status_code = 200
        canli_yayin.yayinla("yeni-sos", id=kayit["id"], durum=kayit["durum"])
        cikti = gorevleri_ekle("sos", [kayit], [_sos_cikti(kayit)], afetzede=kul["rol"] == "afetzede")[0]
        return {**cikti, "guncellendi": True}
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
    kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
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
    from uclar.gorev import _gorev_kaydi

    _gorev_kaydi(kul, "sevk", g, "ekip gönderildi (eski atama ucu)")
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
    import islem_kaydi

    cagri = depo.sos_bul(sos_id) or {}
    islem_kaydi.kaydet(
        kul,
        "sos_kapatildi",
        f"SOS kapatıldı: {cagri.get('mahalle') or 'mahalle bilinmiyor'}"
        + (f", {len(biten)} açık görev bitti" if biten else ""),
        hedef_tur="sos",
        hedef_id=sos_id,
        ayrinti={"bitenGorevler": biten, "oncelik": cagri.get("oncelik")},
    )
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

EKIP_ALAN_ADI = {"ad": "ad", "kurum": "kurum", "tur": "tür", "kisi_sayisi": "kişi sayısı", "durum": "durum"}


def _ekip_degisti_kaydi(kul: dict, ekip_id: str, onceki: Optional[dict], sonra: Optional[dict]) -> None:
    """Yalniz degisen alanlar yazilir; hicbiri degismediyse kayit yok (J-165)."""
    import islem_kaydi

    if sonra is None:
        return
    if onceki is None:
        islem_kaydi.kaydet(
            kul, "ekip_eklendi", f"Ekip eklendi: {sonra['ad']}",
            hedef_tur="ekip", hedef_id=ekip_id,
            ayrinti={k: sonra.get(k) for k in EKIP_ALAN_ADI},
        )
        return
    farklar = {k: [onceki.get(k), sonra.get(k)] for k in EKIP_ALAN_ADI if onceki.get(k) != sonra.get(k)}
    if not farklar:
        return
    metin = ", ".join(f"{EKIP_ALAN_ADI[k]} {a if a is not None else '—'} → {b if b is not None else '—'}" for k, (a, b) in farklar.items())
    islem_kaydi.kaydet(
        kul, "ekip_degisti", f"{sonra['ad']} güncellendi: {metin}",
        hedef_tur="ekip", hedef_id=ekip_id, ayrinti={"degisen": farklar},
    )


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
    # Telefonun bildirdigi dogruluk (m); gecmiste saklanir (J-166).
    dogrulukM: Optional[float] = Field(None, ge=0, le=100000)


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
def ekip_ekle(istek: EkipIstegi, kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON))):
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
    import islem_kaydi

    islem_kaydi.kaydet(
        kul, "ekip_eklendi",
        f"Ekip eklendi: {kayit['ad']}" + (f" ({kayit.get('kurum')})" if kayit.get("kurum") else ""),
        hedef_tur="ekip", hedef_id=kayit["id"],
        ayrinti={k: kayit.get(k) for k in ("ad", "kurum", "tur", "kisi_sayisi", "durum")},
    )
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
    kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
):
    """Ekibi acar ya da gunceller. Konum verilmezse eski konum korunur.
    Gorevdeki ekip hizmet disi yapilamaz: once gorev bitmeli."""
    _ekip_dogrula(istek)
    depo = aktif_depo()
    onceki = depo.ekip_bul(ekip_id)
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
    _ekip_degisti_kaydi(kul, ekip_id, onceki, depo.ekip_bul(ekip_id))
    return _tek_ekip(ekip_id)


@yonlendirici.put("/ekipler/{ekip_id}/uyeler")
def ekip_uyeleri(
    ekip_id: str,
    istek: UyelerIstegi,
    kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
):
    """Saha hesaplarini ekibe baglar: bagli kisi o ekibin gorevini kendi
    telefonundan gunceller. Baska ekipteki kisi oradan cikar."""
    depo = aktif_depo()
    if depo.ekip_bul(ekip_id) is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    saha = {u["id"] for u in depo.saha_kullanicilari()}
    if any(k not in saha for k in istek.kullaniciIdleri):
        raise HTTPException(status_code=422, detail="Yalnız saha ekibi hesapları ekibe bağlanır.")
    saha_hesaplari = depo.saha_kullanicilari()
    onceki_uyeler = {u["id"] for u in saha_hesaplari if u.get("ekip_id") == ekip_id}
    adlar = {u["id"]: u.get("ad_soyad") or u.get("eposta") for u in saha_hesaplari}
    depo.ekip_uyelerini_ayarla(ekip_id, list(dict.fromkeys(istek.kullaniciIdleri)))
    canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id)
    yeni_uyeler = set(istek.kullaniciIdleri)
    eklenen, cikan = sorted(yeni_uyeler - onceki_uyeler), sorted(onceki_uyeler - yeni_uyeler)
    if eklenen or cikan:
        import islem_kaydi

        ekip = depo.ekip_bul(ekip_id) or {}
        parcalar = []
        if eklenen:
            parcalar.append("eklendi: " + ", ".join(adlar.get(k) or k for k in eklenen))
        if cikan:
            parcalar.append("çıkarıldı: " + ", ".join(adlar.get(k) or k for k in cikan))
        islem_kaydi.kaydet(
            kul, "ekip_uyeleri", f"{ekip.get('ad') or ekip_id} hesapları · " + "; ".join(parcalar),
            hedef_tur="ekip", hedef_id=ekip_id, ayrinti={"eklenen": eklenen, "cikan": cikan},
        )
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
    # J-166: her nokta silinmeyen konum gecmisine de yazilir, gonderenle.
    onceki = depo.ekip_konum(ekip_id, istek.lon, istek.lat, gonderen=kul, dogruluk_m=istek.dogrulukM)
    # Islem kaydina her nokta degil, paylasimin basladigi an duser.
    if onceki is None or time.time() - onceki > PAYLASIM_ARASI_SN:
        import islem_kaydi

        ekip = depo.ekip_bul(ekip_id) or {}
        islem_kaydi.kaydet(
            kul,
            "konum_paylasimi_basladi",
            f"{ekip.get('ad') or ekip_id}: konum paylaşımı başladı",
            hedef_tur="ekip",
            hedef_id=ekip_id,
            ayrinti={"oncekiNoktaDk": None if onceki is None else round((time.time() - onceki) / 60)},
        )
    canli_yayin.yayinla("ekip-konumu", ekipId=ekip_id, lon=istek.lon, lat=istek.lat)
    return _tek_ekip(ekip_id)


#: Bu sureden uzun ara verilen konum paylasimi yeniden "basladi" sayilir.
PAYLASIM_ARASI_SN = 15 * 60


@yonlendirici.get("/ekipler/{ekip_id}/konum-gecmisi")
def ekip_konum_gecmisi(
    ekip_id: str,
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    sinir: int = 5000,
    kul: dict = Depends(kimlik.rol_gerektir(*KOORDINASYON)),
):
    """Ekibin bildirdigi konumlar, eskiden yeniye (J-166). Zaman ms."""
    import islem_kaydi

    depo = aktif_depo()
    if depo.ekip_bul(ekip_id) is None:
        raise HTTPException(status_code=404, detail="Ekip bulunamadi.")
    noktalar = depo.ekip_konum_gecmisi(
        ekip_id, baslangic=_sn(baslangic), bitis=_sn(bitis), sinir=max(1, min(sinir, 20000))
    )
    islem_kaydi.goruntuleme(kul, "konum_gecmisi", hedef_tur="ekip", hedef_id=ekip_id,
                            ayrinti={"noktaSayisi": len(noktalar)})
    return [
        {
            "lon": n["lon"], "lat": n["lat"], "dogrulukM": n["dogruluk_m"],
            "zaman": _ms(n["zaman"]), "gonderenAd": n["gonderen_ad"], "gonderenRol": n["gonderen_rol"],
        }
        for n in noktalar
    ]


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
    # Sayilar SQL'de (J-158): eskiden 100 000'er satir Python'a cekilip sayiliyordu;
    # yavasti ve 100 000'i asan kayitta sessizce eksik sayiyordu.
    hasar = depo.hasar_ozeti(b, s, yikik_esigi=0.8)
    # Ekip sayilari zaman araligina bagli degil: su anki durum (J-54).
    ekipler_simdi = ekipler_cikti(depo.ekip_listele())
    acik_gorevler = depo.gorev_listele(yalniz_acik=True)
    return {
        # Yikik/hasarli ayrimi skor esigiyle: 0,8 ustu yikik sayilir.
        "yikikYapi": hasar["yikikYapi"],
        "hasarliYapi": hasar["hasarliYapi"],
        "hasarliYol": depo.kapanma_sayisi(b, s),
        "bekleyenSos": sos_sayilari.get("bekliyor", 0),
        "atananSos": sos_sayilari.get("atandi", 0),
        "kapananSos": sos_sayilari.get("kapandi", 0),
        "ekipSayisi": len(ekipler_simdi),
        "musaitEkip": sum(1 for e in ekipler_simdi if e["musait"]),
        "gorevdekiEkip": sum(1 for e in ekipler_simdi if e["gorev"]),
        "sahadakiKisi": sum(g["kisi_sayisi"] for g in acik_gorevler),
        "kaynakSayilari": hasar["kaynakSayilari"],
        "olusturuldu": _ms(time.time()),
    }
