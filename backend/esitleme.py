"""Saha sunucusu ile merkez arasinda esitleme (OPTIMIZASYON madde 31).

Hedef mimari (OPTIMIZASYON Bolum 0): afet bolgesindeki saha sunucusu (Pi ya da
dizustu, hotspot) internet olmadan bolgesine hizmet verir; baglanti geldiginde
merkezle kayit alisverisi yapar. Eskiden boyle bir yol yoktu: sahada acilan
SOS ve ihbar yalniz o makinenin diskinde kaliyordu.

Yonler.
  * Yukari (dugum -> merkez): hasar noktasi, yol kapanmasi, SOS, ihbar.
    Merkez SOS ve ihbari ham kayit olarak tutar (`gelen_kayitlar`), kendi is
    akisina karistirmaz: atama/kapatma sahada yapilir.
  * Asagi (merkez -> dugum): hasar noktasi ve yol kapanmasi. Uydu analizi
    internet ister ve merkezde kosar; sonucu (kapanmalar) sahadaki yurume ve
    arac rotasina boylece girer.
Tatbikat verisi hicbir yone gitmez. Ayrinti: `depo/esitleme_tablolari.py`.

Ayarlar (ortam degiskeni):
  Dugum:  QUAKEMIND_MERKEZ_URL      merkezin adresi (https://...)
          QUAKEMIND_DUGUM_ADI       bu sunucunun adi (a-z, 0-9, -)
          QUAKEMIND_ESITLEME_ANAHTARI  merkezin bu dugume verdigi anahtar
          QUAKEMIND_ESITLEME_ARALIK_SN deneme araligi (varsayilan 30)
  Merkez: QUAKEMIND_ESITLEME_DUGUMLERI  "ad:anahtar,ad2:anahtar2"
          QUAKEMIND_MERKEZ_ADI      merkezin kendi kayitlarinin oneki (merkez)
Ikisi birden verilirse sunucu acilmaz: zincirleme merkez desteklenmiyor.

Yoklama mi? Kural 4 arayuzun uclari yoklamasini yasaklar. Buradaki dongu
sunucudan sunucuya, baglantinin GELDIGINI anlamak icindir; merkez dugume
ulasamaz (dugum NAT/hotspot arkasinda), bu yuzden istek hep dugumden cikar.
Hata olursa aralik ikiye katlanir (en cok 10 dk).

Internetsiz kip (`internetsiz.py`) esitlemeyi kapatmaz: kip kamuya acik
servisleri kapatir, merkez bizim kendi sunucumuzdur.
"""
from __future__ import annotations

import hmac
import os
import re
import threading
import time
from typing import Optional

from fastapi import Header, HTTPException

AD_DESENI = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
EN_AZ_ANAHTAR = 24
PAKET = 200
EN_UZUN_BEKLEME_SN = 600.0


class AyarHatasi(ValueError):
    pass


def rol() -> Optional[str]:
    dugum = bool(os.environ.get("QUAKEMIND_MERKEZ_URL", "").strip())
    merkez = bool(os.environ.get("QUAKEMIND_ESITLEME_DUGUMLERI", "").strip())
    if dugum and merkez:
        raise AyarHatasi("QUAKEMIND_MERKEZ_URL ve QUAKEMIND_ESITLEME_DUGUMLERI birlikte verilemez.")
    return "dugum" if dugum else "merkez" if merkez else None


def merkez_adi() -> str:
    ad = os.environ.get("QUAKEMIND_MERKEZ_ADI", "merkez").strip()
    if not AD_DESENI.match(ad):
        raise AyarHatasi("QUAKEMIND_MERKEZ_ADI yalnız a-z, 0-9 ve - içerebilir.")
    return ad


def dugumler() -> dict[str, str]:
    """Merkez: anahtar -> dugum adi."""
    sonuc: dict[str, str] = {}
    for parca in os.environ.get("QUAKEMIND_ESITLEME_DUGUMLERI", "").split(","):
        parca = parca.strip()
        if not parca:
            continue
        ad, _, anahtar = parca.partition(":")
        ad, anahtar = ad.strip(), anahtar.strip()
        if not AD_DESENI.match(ad):
            raise AyarHatasi(f"Geçersiz düğüm adı: {ad!r}")
        if len(anahtar) < EN_AZ_ANAHTAR:
            raise AyarHatasi(f"{ad} anahtarı en az {EN_AZ_ANAHTAR} karakter olmalı.")
        if ad == merkez_adi():
            raise AyarHatasi(f"Düğüm adı merkezin adıyla aynı olamaz: {ad}")
        sonuc[anahtar] = ad
    return sonuc


def dugum_ayarlari() -> dict:
    url = os.environ.get("QUAKEMIND_MERKEZ_URL", "").strip().rstrip("/")
    ad = os.environ.get("QUAKEMIND_DUGUM_ADI", "").strip()
    anahtar = os.environ.get("QUAKEMIND_ESITLEME_ANAHTARI", "").strip()
    if not re.match(r"^https?://[A-Za-z0-9.\-]+(:\d+)?(/.*)?$", url):
        raise AyarHatasi("QUAKEMIND_MERKEZ_URL http(s) adresi olmalı.")
    if not AD_DESENI.match(ad):
        raise AyarHatasi("QUAKEMIND_DUGUM_ADI yalnız a-z, 0-9 ve - içerebilir.")
    if len(anahtar) < EN_AZ_ANAHTAR:
        raise AyarHatasi(f"QUAKEMIND_ESITLEME_ANAHTARI en az {EN_AZ_ANAHTAR} karakter olmalı.")
    try:
        aralik = max(5.0, float(os.environ.get("QUAKEMIND_ESITLEME_ARALIK_SN", "30")))
    except ValueError:
        aralik = 30.0
    return {"url": url, "ad": ad, "anahtar": anahtar, "aralik": aralik}


# ---- merkez: dugum dogrulama (uclar icin bagimlilik) -----------------------

def dugum_dogrula(authorization: str = Header(default="")) -> str:
    """Merkez uclari icin: Bearer anahtardan dugum adi. Kullanici jetonu
    burada gecmez; dugum anahtari kullanici ucuna da gecmez (ayri yollar)."""
    if rol() != "merkez":
        raise HTTPException(status_code=404, detail="Bu sunucu merkez değil.")
    tur, _, anahtar = authorization.partition(" ")
    if tur.lower() != "bearer" or not anahtar:
        raise HTTPException(status_code=401, detail="Düğüm anahtarı gerekli.")
    for bilinen, ad in dugumler().items():
        if hmac.compare_digest(bilinen.encode(), anahtar.strip().encode()):
            return ad
    raise HTTPException(status_code=401, detail="Düğüm anahtarı tanınmadı.")


# ---- dugum: esitleyici ------------------------------------------------------

class Esitleyici:
    """Arka plan is parcacigi: gonder, cek, bekle. Durumu `durum()` verir."""

    def __init__(self, depo, ayar: dict, istemci=None):
        self.depo = depo
        self.ayar = ayar
        self._istemci = istemci  # testler httpx.Client yerine TestClient verir
        self._dur = threading.Event()
        self._uyan = threading.Event()
        self._is: Optional[threading.Thread] = None
        self.son_basari: Optional[float] = None
        self.son_deneme: Optional[float] = None
        self.son_hata: Optional[str] = None
        self.gonderilen = 0
        self.alinan = 0
        self._bekleme = ayar["aralik"]

    # -- HTTP --
    def _http(self):
        if self._istemci is None:
            import httpx

            self._istemci = httpx.Client(
                base_url=self.ayar["url"], timeout=httpx.Timeout(20.0, connect=8.0),
                headers={"User-Agent": "QuakeMind-dugum/1.0"},
            )
        return self._istemci

    def _basliklar(self) -> dict:
        return {"Authorization": f"Bearer {self.ayar['anahtar']}"}

    # -- bir tur --
    def gonder(self) -> int:
        """Bekleyen degisiklikleri paket paket gonderir. Donus: gonderilen."""
        toplam = 0
        while True:
            bekleyen = self.depo.degisim_bekleyenler(PAKET)
            if not bekleyen:
                return toplam
            silinmis = [b["sira"] for b in bekleyen if b["veri"] is None]
            paket = [b for b in bekleyen if b["veri"] is not None]
            if paket:
                y = self._http().post("/api/esitleme/al", json={"kayitlar": paket}, headers=self._basliklar())
                if y.status_code != 200:
                    raise RuntimeError(f"merkez {y.status_code}: {y.text[:200]}")
                alinan = set(y.json().get("alinan") or [])
                # Merkezin reddettigi kayit (bicim hatasi) tekrar tekrar
                # gonderilmesin diye o da isaretlenir; sayisi gunluge yazilir.
                self.depo.degisim_gonderildi([b["sira"] for b in paket])
                toplam += len(alinan)
            if silinmis:
                self.depo.degisim_gonderildi(silinmis)
            if len(bekleyen) < PAKET:
                return toplam

    def cek(self) -> int:
        """Merkezin hasar/kapanma degisikliklerini imlecten sonrasindan ceker."""
        import canli_yayin

        toplam = 0
        imlec = int(self.depo.esitleme_deger("merkez_imleci") or 0)
        while True:
            y = self._http().get(
                "/api/esitleme/ver", params={"sonra": imlec, "n": 500}, headers=self._basliklar()
            )
            if y.status_code != 200:
                raise RuntimeError(f"merkez {y.status_code}: {y.text[:200]}")
            govde = y.json()
            kayitlar = govde.get("kayitlar") or []
            if kayitlar:
                toplam += self.depo.uzak_kayit_yaz(kayitlar)
            yeni = int(govde.get("sonSira") or imlec)
            if yeni != imlec:
                imlec = yeni
                self.depo.esitleme_deger_yaz("merkez_imleci", str(imlec))
            if not govde.get("devamVar"):
                break
        if toplam:
            try:
                canli_yayin.yayinla("yeni-analiz", kaynak="esitleme", sayi=toplam)
            except Exception:  # noqa: BLE001
                pass
        return toplam

    def tur(self) -> dict:
        self.son_deneme = time.time()
        try:
            g = self.gonder()
            a = self.cek()
        except Exception as e:  # noqa: BLE001 -- baglanti yokken beklenen durum
            self.son_hata = f"{type(e).__name__}: {str(e)[:200]}"
            self._bekleme = min(EN_UZUN_BEKLEME_SN, self._bekleme * 2)
            return {"basarili": False, "hata": self.son_hata}
        self.gonderilen += g
        self.alinan += a
        self.son_basari = time.time()
        self.son_hata = None
        self._bekleme = self.ayar["aralik"]
        return {"basarili": True, "gonderilen": g, "alinan": a}

    # -- is parcacigi --
    def _dongu(self) -> None:
        while not self._dur.is_set():
            self.tur()
            self._uyan.wait(self._bekleme)
            self._uyan.clear()

    def baslat(self) -> None:
        self._is = threading.Thread(target=self._dongu, name="esitleme", daemon=True)
        self._is.start()

    def simdi(self) -> None:
        """Beklemeyi keser (koordinator "simdi dene" dediginde)."""
        self._bekleme = self.ayar["aralik"]
        self._uyan.set()

    def durdur(self) -> None:
        self._dur.set()
        self._uyan.set()

    def durum(self) -> dict:
        from urllib.parse import urlparse

        return {
            "rol": "dugum",
            "dugum": self.ayar["ad"],
            "merkez": urlparse(self.ayar["url"]).hostname,
            "bekleyen": self.depo.degisim_bekleyen_sayisi(),
            "gonderilen": self.gonderilen,
            "alinan": self.alinan,
            "sonDeneme": self.son_deneme,
            "sonBasari": self.son_basari,
            "sonHata": self.son_hata,
            "sonrakiDenemeSn": self._bekleme,
            "imlec": int(self.depo.esitleme_deger("merkez_imleci") or 0),
        }


_esitleyici: Optional[Esitleyici] = None


def baslat(depo) -> Optional[str]:
    """Acilista (lifespan). Rolu okur, tetikleyicileri kurar, dugumse is
    parcacigini baslatir. Ayar hatasi sunucuyu durdurur (yanlis ayarla sessizce
    esitlemeden calismak, verinin merkeze gitmedigini gizlerdi)."""
    global _esitleyici
    r = rol()
    if r == "dugum":
        ayar = dugum_ayarlari()
    elif r == "merkez":
        dugumler()
        merkez_adi()
    kurulum = depo.esitleme_kur(r)
    if kurulum["doldurulan"]:
        print(f"Esitleme: {kurulum['doldurulan']} eski kayit gunluge eklendi", flush=True)
    if r == "dugum":
        _esitleyici = Esitleyici(depo, ayar)
        _esitleyici.baslat()
        print(f"Esitleme: dugum '{ayar['ad']}' -> {ayar['url']}", flush=True)
    elif r == "merkez":
        print(f"Esitleme: merkez, {len(dugumler())} dugum tanimli", flush=True)
    return r


def durdur() -> None:
    global _esitleyici
    if _esitleyici is not None:
        _esitleyici.durdur()
        _esitleyici = None


def esitleyici() -> Optional[Esitleyici]:
    return _esitleyici
