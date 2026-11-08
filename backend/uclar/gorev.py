"""Sevk gorevleri (J-54): hangi olaya hangi ekip, kac kisiyle gidiyor.

Kullanici: "hangi ihbar, neredeki ihbar, hangi ekip gidecek ya da gidiyor, kac
kisi gidiyor; bunlar hep belirsiz."

Her sevk bir gorev kaydidir: olay (SOS ya da ihbar), ekip, giden kisi sayisi,
atayan ve durum sirasi (atandi -> yolda -> olay-yerinde -> tamamlandi, her an
iptal). Durumu hem ekip kendi telefonundan hem koordinasyon (telsizle gelen
bilgi) isaretler; her adim kimden geldigiyle yazilir (`gorev_adimlari`).

Yetki (kural 5):
  * Koordinator ve yonetici her ekibi gonderir ve her gorevi gunceller.
  * Saha kullanicisi yalniz BAGLI OLDUGU ekip adina calisir: kendi ekibini
    gonderebilir, kendi ekibinin gorevini gunceller. Ekibe baglamayi
    koordinasyon yapar (`PUT /api/ekipler/{id}/uyeler`).
  * Afetzede bu uclara giremez; kendi cagrisindaki ekibi SOS ve ihbar
    uclarindan gorur.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import arac_rotasi
import kimlik
from depo import aktif_depo
from depo.sqlite_surucu import ACIK_GOREV, GorevHatasi, mesafe_m
from uclar.gorev_bicim import (
    ekip_cikti,
    ekipler_cikti,
    gorev_cikti,
    gorev_yayinla,
    hedef_bul,
    hedef_ozeti,
)

yonlendirici = APIRouter(prefix="/api", tags=["gorev"])

SAHA_VE_USTU = ("saha", "koordinator", "yonetici")
KOORDINASYON = ("koordinator", "yonetici")
HEDEF_TURLERI = ("sos", "ihbar")

# Kural ihlali -> HTTP durumu. Mesajlar Turkce ve kullaniciya gosterilir.
_HTTP = {
    "hedef-yok": 404,
    "ekip-yok": 404,
    "gorev-yok": 404,
    "kisi-yok": 422,
    "kisi-gecersiz": 422,
    "kisi-fazla": 422,
    "gecersiz-durum": 422,
}


def hata_http(h: GorevHatasi) -> HTTPException:
    return HTTPException(status_code=_HTTP.get(h.kod, 409), detail=h.mesaj)


def _kaynak(kul: dict) -> str:
    return "ekip" if kul["rol"] == "saha" else "koordinasyon"


def _yetki(kul: dict, ekip_id: str) -> None:
    """Saha kullanicisi yalniz kendi ekibi adina islem yapar."""
    if kul["rol"] in KOORDINASYON:
        return
    if kul["rol"] == "saha" and kul.get("ekip_id") == ekip_id:
        return
    if kul["rol"] == "saha" and not kul.get("ekip_id"):
        raise HTTPException(status_code=403, detail="Bir ekibe bağlı değilsin; koordinasyona haber ver.")
    raise HTTPException(status_code=403, detail="Yalnız kendi ekibin adına işlem yapabilirsin.")


def _tam_cikti(g: dict) -> dict:
    hedef = hedef_bul(g["hedef_tur"], g["hedef_id"])
    adimlar = aktif_depo().gorev_adimlari([g["id"]]).get(g["id"], [])
    c = gorev_cikti(g, (hedef["lon"], hedef["lat"]) if hedef else None, adimlar)
    c["hedef"] = hedef_ozeti(g["hedef_tur"], hedef)
    return c


# --- listeleme -------------------------------------------------------------

@yonlendirici.get("/gorevler")
def gorevler(
    hedefTur: Optional[str] = None,
    hedefId: Optional[str] = None,
    ekipId: Optional[str] = None,
    acik: bool = False,
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    if hedefTur and hedefTur not in HEDEF_TURLERI:
        raise HTTPException(status_code=422, detail="hedefTur: sos | ihbar")
    depo = aktif_depo()
    kayitlar = depo.gorev_listele(
        hedef_tur=hedefTur,
        hedef_idler=[hedefId] if hedefId else None,
        ekip_id=ekipId,
        yalniz_acik=acik,
        sinir=1000,
    )
    return [_tam_cikti(g) for g in kayitlar]


@yonlendirici.get("/gorevler/aday-ekipler")
def aday_ekipler(
    hedefTur: str,
    hedefId: str,
    _kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Olaya gonderilebilecek ekipler: once musaitler, olaya tahmini sureye
    gore (arac aginda yoldan, J-55; ag yoksa kus ucusu uzakliga gore).
    Gorevdeki ve hizmet disi ekipler de listelenir ama neden gonderilemedikleri
    yazilir. Butun ekiplerin suresi olaydan tek aramayla cikar."""
    if hedefTur not in HEDEF_TURLERI:
        raise HTTPException(status_code=422, detail="hedefTur: sos | ihbar")
    hedef = hedef_bul(hedefTur, hedefId)
    if hedef is None:
        raise HTTPException(status_code=404, detail="Olay bulunamadı.")
    liste = []
    for e in ekipler_cikti(aktif_depo().ekip_listele()):
        konumlu = e["lon"] is not None and e["lat"] is not None
        mesafe = round(mesafe_m(e["lon"], e["lat"], hedef["lon"], hedef["lat"])) if konumlu else None
        # Ayni sehirdeki ekip sehir aginda, baska sehirdeki bolgeler arasi agda;
        # olay basina tek arama, sonraki ekipler onbellekten.
        yol = arac_rotasi.yoldan(hedef["lon"], hedef["lat"], e["lon"], e["lat"], rota=False) if konumlu else None
        liste.append({"ekip": e, "mesafeM": mesafe, "yol": yol})
    liste.sort(
        key=lambda x: (
            not x["ekip"]["musait"],
            x["yol"] is None,
            x["yol"]["sureDk"] if x["yol"] else 0,
            x["mesafeM"] is None,
            x["mesafeM"] if x["mesafeM"] is not None else 0,
            x["ekip"]["ad"],
        )
    )
    return liste


# --- sevk ------------------------------------------------------------------

class SevkIstegi(BaseModel):
    hedefTur: str
    hedefId: str
    ekipId: str
    kisiSayisi: Optional[int] = Field(None, ge=1, le=500)
    not_: Optional[str] = Field(None, alias="not", max_length=300)
    # Olaya zaten ekip gidiyorsa ikincisi ancak bununla gider (yanlislikla
    # iki kez sevk olmasin).
    ekDestek: bool = False

    model_config = {"populate_by_name": True}


@yonlendirici.post("/gorevler", status_code=201)
def sevk_et(istek: SevkIstegi, kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU))):
    if istek.hedefTur not in HEDEF_TURLERI:
        raise HTTPException(status_code=422, detail="hedefTur: sos | ihbar")
    _yetki(kul, istek.ekipId)
    try:
        g = aktif_depo().gorev_ac(
            hedef_tur=istek.hedefTur,
            hedef_id=istek.hedefId,
            ekip_id=istek.ekipId,
            kisi_sayisi=istek.kisiSayisi,
            kisi_id=kul["id"],
            kisi_ad=kul.get("ad_soyad"),
            kaynak=_kaynak(kul),
            not_metni=(istek.not_ or "").strip() or None,
            ek_destek=istek.ekDestek,
        )
    except GorevHatasi as h:
        raise hata_http(h) from h
    gorev_yayinla(g)
    return _tam_cikti(g)


class GorevDurumIstegi(BaseModel):
    durum: str
    not_: Optional[str] = Field(None, alias="not", max_length=300)
    # Ekip isini bitirdi ama olay surmekte (baska ekip ya da ekipman lazim):
    # olay kapanmaz, kuyruga doner.
    olaySuruyor: bool = False

    model_config = {"populate_by_name": True}


@yonlendirici.post("/gorevler/{gorev_id}/durum")
def gorev_durumu(
    gorev_id: str,
    istek: GorevDurumIstegi,
    kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    depo = aktif_depo()
    mevcut = depo.gorev_bul(gorev_id)
    if mevcut is None:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    _yetki(kul, mevcut["ekip_id"])
    not_metni = (istek.not_ or "").strip() or None
    if istek.durum == "iptal" and not not_metni:
        raise HTTPException(status_code=422, detail="İptalin nedenini yaz; olay yeniden sıraya girer.")
    try:
        g, hedef_durumu = depo.gorev_durum(
            gorev_id,
            istek.durum,
            kisi_id=kul["id"],
            kisi_ad=kul.get("ad_soyad"),
            kaynak=_kaynak(kul),
            not_metni=not_metni,
            olay_suruyor=istek.olaySuruyor,
        )
    except GorevHatasi as h:
        raise hata_http(h) from h
    gorev_yayinla(g, hedef_durumu)
    return _tam_cikti(g)


# --- saha ekibinin kendi ekrani -------------------------------------------

@yonlendirici.get("/ekibim")
def ekibim(kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU))):
    """Saha kullanicisinin ekibi, acik gorevi (olayin butun bilgisiyle) ve son
    bitmis gorevleri. Ekibe bagli degilse `ekip` bos doner."""
    ekip_id = kul.get("ekip_id")
    depo = aktif_depo()
    e = depo.ekip_bul(ekip_id) if ekip_id else None
    if e is None:
        return {"ekip": None, "gorev": None, "gecmis": []}
    tum = depo.gorev_listele(ekip_id=ekip_id, sinir=6)
    acik = next((g for g in tum if g["durum"] in ACIK_GOREV), None)
    uyeler = [u for u in depo.saha_kullanicilari() if u.get("ekip_id") == ekip_id]
    gorev = None
    if acik is not None:
        gorev = _tam_cikti(acik)
        # Ekip olaya gitmek icin olayin butun bilgisini gorur: afetzedenin notu,
        # kisi sayisi, ihtiyaclar, konumun dogrulugu, modelin sonucu.
        gorev["olay"] = _olay_ayrintisi(acik["hedef_tur"], acik["hedef_id"])
    return {
        "ekip": ekip_cikti(e, acik, uyeler),
        "gorev": gorev,
        "gecmis": [_tam_cikti(g) for g in tum if g is not acik][:5],
    }


def _olay_ayrintisi(hedef_tur: str, hedef_id: str) -> Optional[dict]:
    # Dongusel ice aktarma olmasin diye burada: sozlesme ve ihbar da bu
    # paketteki bicimi kullanir.
    from uclar import ihbar, sozlesme

    kayit = hedef_bul(hedef_tur, hedef_id)
    if kayit is None:
        return None
    return sozlesme._sos_cikti(kayit) if hedef_tur == "sos" else ihbar._cikti(kayit)
