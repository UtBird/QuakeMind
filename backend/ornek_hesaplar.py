"""Ortak ornek hesaplar: her rol icin bir hesap (J-183).

Teslim ve tanitim doneminde ekip, hoca ve degerlendiriciler ayni hesaplarla
girer; veri zaten tek veritabaninda ve herkese ortaktir (hangi rol neyi gorur,
rolu belirler).

Sifre depoda YAZMAZ. Sunucuda `QUAKEMIND_ORNEK_HESAP_SIFRESI` ortam
degiskeni tanimliysa API her aciliista hesaplari kurar ve sifrelerini bu
degere ceker; tanimli degilse hicbir sey yapmaz. Canlida degisken
`backend.env` dosyasina yazilir (bkz. deploy/README.md).

Ortak hesabin sifresi uygulamadan degistirilemez ve konsoldan sifirlanamaz:
biri degistirirse herkes disarida kalir. Sifre yalniz ortam degiskeninden
degisir. Yerel demo icin `araclar_demo_hesaplari.py` ayni listeyi kullanir.
"""

from __future__ import annotations

import os
from typing import Optional

import kimlik

ORTAM_DEGISKENI = "QUAKEMIND_ORNEK_HESAP_SIFRESI"
EN_AZ_UZUNLUK = 10
#: Depoda acik yazan yerel demo sifresi; canlida ortak sifre olarak kabul edilmez.
YEREL_DEMO_SIFRESI = "degistir1234"

# (e-posta, ad soyad, rol, giris kapisi)
HESAPLAR = [
    ("yonetici-demo@quakemind.local", "Demo Yönetici", "yonetici", "Koordinasyon"),
    ("demo@quakemind.local", "Demo Koordinatör", "koordinator", "Koordinasyon"),
    ("saha-demo@quakemind.local", "Demo Saha Ekibi", "saha", "Saha ekibi"),
    ("afetzede-demo@quakemind.local", "Demo Afetzede", "afetzede", "Afetzede"),
]
EPOSTALAR = frozenset(e for e, *_ in HESAPLAR)
DEMO_EKIP_ADI = "Demo Ekip"
KAYNAK = {"kaynak": "ornek_hesaplar"}


def ortak_mi(eposta: Optional[str]) -> bool:
    return bool(eposta) and eposta.strip().lower() in EPOSTALAR


def kur(depo, sifre: str, sifreyi_cek: bool) -> list[tuple[str, str, str, str]]:
    """Eksik hesaplari acar. `sifreyi_cek`: var olanin sifresi `sifre` degilse
    ona cekilir. Var olan hesabin rolune ve askisina dokunulmaz (yonetici
    bilerek degistirmis olabilir). Saha hesabi bir ekibe baglanir."""
    satirlar = []
    for eposta, ad, rol, kapi in HESAPLAR:
        var = depo.kullanici_eposta(eposta)
        if var is None:
            k = depo.kullanici_olustur(eposta=eposta, ad_soyad=ad, sifre_ozeti=kimlik.sifre_ozetle(sifre), rol=rol)
            depo.hesap_kaydi_ekle(None, k, "hesap-acildi", {"rol": rol, **KAYNAK})
            durum = "acildi"
        else:
            k = var
            durum = "zaten var"
            if var["rol"] != rol:
                durum += f" (rolu {var['rol']}; degistirilmedi)"
            if sifreyi_cek and (var.get("sifre_degismeli") or not kimlik.sifre_dogrula(sifre, var["sifre_ozeti"])):
                depo.sifre_ata(var["id"], kimlik.sifre_ozetle(sifre), degismeli=False)
                depo.hesap_kaydi_ekle(None, var, "sifre-yenilendi", KAYNAK)
                durum += ", sifresi ortak sifreye cekildi"
            if var.get("askida"):
                durum += ", ASKIDA (giremez; Hesaplar sayfasindan etkinlestir)"

        # Saha hesabi gorev gorsun diye bir ekibe bagli olmali (J-155).
        guncel = depo.kullanici_id(k["id"])
        if guncel["rol"] == "saha" and not guncel.get("ekip_id"):
            ekipler = depo.ekip_listele()
            ekip = next((e for e in ekipler if e["ad"] == DEMO_EKIP_ADI), None) or (ekipler[0] if ekipler else None)
            if ekip is None:
                # Konum: Antakya merkezi (konsolun varsayilan bolgesi).
                ekip = depo.ekip_olustur(DEMO_EKIP_ADI, kurum=None, tur=None, kisi_sayisi=4, lon=36.161, lat=36.202)
                durum += f", '{DEMO_EKIP_ADI}' ekibi acildi"
            depo.ekibe_bagla(k["id"], ekip["id"])
            durum += f", ekibe baglandi: {ekip['ad']}"
        satirlar.append((eposta, rol, kapi, durum))
    return satirlar


def acilista_kur(depo) -> None:
    """API acilisi: ortam degiskeni varsa hesaplari kur ve sifreyi esitle."""
    sifre = os.environ.get(ORTAM_DEGISKENI, "")
    if not sifre:
        return
    if len(sifre) < EN_AZ_UZUNLUK or sifre == YEREL_DEMO_SIFRESI:
        print(
            f"Ortak ornek hesaplar KURULMADI: {ORTAM_DEGISKENI} en az {EN_AZ_UZUNLUK} karakter olmali "
            "ve depodaki demo sifresi olmamali.",
            flush=True,
        )
        return
    satirlar = kur(depo, sifre, sifreyi_cek=True)
    print("Ortak ornek hesaplar: " + "; ".join(f"{e} ({r}) {d}" for e, r, _k, d in satirlar), flush=True)
