"""Hiz sinirlari (J-167 S-1, S-2): hatali giris, SOS ve hesap acma.

Sayaclar SQLite'ta (`hiz_sayaclari`), bellekte degil. Gerekce: sunucu
yeniden baslatilarak kilit sifirlanamaz ve ileride birden cok uvicorn
worker'ina gecilirse sayac ortak kalir. Bedeli deneme basina bir yazma;
hatali giris ve SOS seyrek isler oldugu icin onemsiz.

Esikler afet aninda gercek kullaniciyi engellemeyecek kadar gevsek,
otomatik denemeyi durduracak kadar sikidir. Hepsi asagida, tek yerde.

IP adresi: vekil (Nginx) arkasinda dogrudan baglanan adres vekilin kendisidir.
O zaman herkes ayni IP'den gelir ve IP sinirini bir kisi doldurup herkesi
kilitler. Bu yuzden:
  * `X-Forwarded-For` yoksa dogrudan baglanan adres kullanilir;
  * varsa ve `QUAKEMIND_VEKIL_GUVENILIR=1` ise basligin ilk adresi kullanilir
    (vekil basligi kendisi yaziyor demektir);
  * varsa ama vekile guvenilmiyorsa IP siniri UYGULANMAZ (istemci basligi
    uydurabilir), yalniz hesap siniri kalir.
Canlida Nginx arkasinda calisilacaksa bu degisken acilmalidir.
"""
from __future__ import annotations

import math
import os
import time
from typing import Optional

from fastapi import HTTPException

from depo import aktif_depo

# --- esikler -----------------------------------------------------------------
GIRIS_PENCERE_SN = 15 * 60
GIRIS_HESAP_SINIRI = 5        # ayni e-postaya 15 dk'da 5 hatali deneme
GIRIS_IP_SINIRI = 30          # ayni adresten 15 dk'da 30 hatali deneme (cok hesaba yayilan deneme)
SOS_PENCERE_SN = 60
SOS_HESAP_SINIRI = 6          # ayni hesaptan dakikada 6 SOS basisi (acik cagriyi gunceller)
SOS_IP_SINIRI = 30            # ayni adresten dakikada 30 SOS
KAYIT_PENCERE_SN = 60 * 60
KAYIT_IP_SINIRI = 10          # ayni adresten saatte 10 yeni hesap (aile, ayni Wi-Fi payi)
METIN_PENCERE_SN = 60
METIN_HESAP_SINIRI = 30       # ayni hesaptan dakikada 30 metin analizi (model CPU'su)


def istemci_ip(istek) -> Optional[str]:
    """Sinir icin kullanilacak adres; guvenilir degilse None (IP siniri yok)."""
    if istek is None:
        return None
    ileten = istek.headers.get("x-forwarded-for")
    if ileten:
        if os.environ.get("QUAKEMIND_VEKIL_GUVENILIR", "0") == "1":
            return ileten.split(",")[0].strip() or None
        return None
    return istek.client.host if istek.client else None


def _dur(kalan_sn: float, ileti: str) -> HTTPException:
    sn = max(1, math.ceil(kalan_sn))
    dk = max(1, math.ceil(sn / 60))
    return HTTPException(
        status_code=429,
        detail=ileti.format(dk=dk, sn=sn),
        headers={"Retry-After": str(sn)},
    )


def _eposta(eposta: str) -> str:
    return (eposta or "").strip().lower()


# --- giris --------------------------------------------------------------------

def giris_kontrol(eposta: str, ip: Optional[str]) -> None:
    """Sifre denetiminden ONCE cagrilir: kilitliyken dogru sifre de 429 alir.
    Ileti hesabin var olup olmadigini soylemez (anahtar e-posta metnidir)."""
    depo = aktif_depo()
    simdi = time.time()
    e = _eposta(eposta)
    # Basarili giris sayaci sifirlar: kisi sonunda dogru sifreyi bulduysa eski
    # hatalari onu kilitlemez.
    son_basari = depo.sayac_son(f"giris-ok:e:{e}") or 0.0
    n, ilk = depo.sayac(f"giris-hata:e:{e}", max(simdi - GIRIS_PENCERE_SN, son_basari))
    if n >= GIRIS_HESAP_SINIRI:
        raise _dur(ilk + GIRIS_PENCERE_SN - simdi,
                   "Çok fazla hatalı deneme. {dk} dakika sonra yeniden dene.")
    if ip:
        n, ilk = depo.sayac(f"giris-hata:ip:{ip}", simdi - GIRIS_PENCERE_SN)
        if n >= GIRIS_IP_SINIRI:
            raise _dur(ilk + GIRIS_PENCERE_SN - simdi,
                       "Bu bağlantıdan çok fazla hatalı deneme. {dk} dakika sonra yeniden dene.")


def giris_basarisiz(eposta: str, ip: Optional[str]) -> None:
    anahtarlar = [f"giris-hata:e:{_eposta(eposta)}"]
    if ip:
        anahtarlar.append(f"giris-hata:ip:{ip}")
    aktif_depo().sayac_ekle(*anahtarlar)


def giris_basarili(eposta: str) -> None:
    aktif_depo().sayac_ekle(f"giris-ok:e:{_eposta(eposta)}")


# --- hesap acma ------------------------------------------------------------------

def kayit_kontrol(ip: Optional[str]) -> None:
    if not ip:
        return
    simdi = time.time()
    n, ilk = aktif_depo().sayac(f"kayit:ip:{ip}", simdi - KAYIT_PENCERE_SN)
    if n >= KAYIT_IP_SINIRI:
        raise _dur(ilk + KAYIT_PENCERE_SN - simdi,
                   "Bu bağlantıdan çok fazla hesap açıldı. {dk} dakika sonra yeniden dene.")


def kayit_oldu(ip: Optional[str]) -> None:
    if ip:
        aktif_depo().sayac_ekle(f"kayit:ip:{ip}")


# --- metin analizi ----------------------------------------------------------------

def metin_kontrol(kullanici_id: str) -> None:
    """J-170: metin analizi modeli CPU'da kosar; tek hesap onu tikamasin."""
    depo = aktif_depo()
    simdi = time.time()
    n, ilk = depo.sayac(f"metin:k:{kullanici_id}", simdi - METIN_PENCERE_SN)
    if n >= METIN_HESAP_SINIRI:
        raise _dur(ilk + METIN_PENCERE_SN - simdi,
                   "Çok sık analiz istendi. {sn} saniye sonra yeniden dene.")
    depo.sayac_ekle(f"metin:k:{kullanici_id}")


# --- SOS -------------------------------------------------------------------------

def sos_kontrol(kullanici_id: str, ip: Optional[str]) -> None:
    """Denemeyi sayar; sinir asildiysa 429. Acik cagri zaten tek satirda
    guncelleniyor (S-2); bu sinir yalniz otomatik seli keser."""
    depo = aktif_depo()
    simdi = time.time()
    n, ilk = depo.sayac(f"sos:k:{kullanici_id}", simdi - SOS_PENCERE_SN)
    if n >= SOS_HESAP_SINIRI:
        raise _dur(ilk + SOS_PENCERE_SN - simdi,
                   "Çağrın zaten iletildi. Yeniden göndermek için {sn} saniye bekle; şebeke varsa 112'yi ara.")
    if ip:
        n, ilk = depo.sayac(f"sos:ip:{ip}", simdi - SOS_PENCERE_SN)
        if n >= SOS_IP_SINIRI:
            raise _dur(ilk + SOS_PENCERE_SN - simdi,
                       "Bu bağlantıdan çok fazla çağrı geldi. {sn} saniye sonra yeniden dene; şebeke varsa 112'yi ara.")
    anahtarlar = [f"sos:k:{kullanici_id}"] + ([f"sos:ip:{ip}"] if ip else [])
    depo.sayac_ekle(*anahtarlar)
