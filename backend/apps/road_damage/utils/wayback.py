"""Esri Wayback: bir konumda arsiv surumlerinin GERCEKTE gosterdigi goruntu.

Wayback surum tarihi goruntunun CEKIM tarihi degildir, iki sebeple:

1. Bir surum bir karoyu guncellemediyse karo onu son guncelleyen eski surumden
   gelir. `tile` ucu bunu 301 ile yapar; `tilemap` ucu `select` alaninda yazar.
2. Guncellenen karonun goruntusu de surumden aylar once cekilmis olabilir.
   Cekim tarihi her surumun metadata katmanindadir (SRC_DATE).

Olculdu (J-35, 21 Eylul 2026, Antakya merkezi, z17): 2023-01-11, 2023-02-23 ve
2023-03-15 surumlerinin ucu de 2021-09-27 cekimini gosteriyor. Deprem sonrasi
ilk cekim (2023-04-04) ancak 2024-02-08 surumunde geliyor. Konsolun
"depremden sonraki ilk surum" varsayilani bu yuzden deprem oncesi goruntuyu
cozumletiyordu.

Metadata servisinde her yakinlastirma icin ayri katman var; katman adlari
cozunurlugu verir (0 = 1,9 cm ... 13 = 150 m), yani katman = 23 - z.
"""
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests

CONFIG_URL = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
TILEMAP_URL = ("https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/"
               "MapServer/tilemap/{surum}/{z}/{y}/{x}")
# Calisma alaninin olayi: 6 Subat 2023 Kahramanmaras depremleri.
DEPREM_TARIHI = "2023-02-06"
# Bir konumda geriye dogru en fazla bu kadar farkli goruntu surumu dolasilir.
EN_FAZLA_ADIM = 25

_oturum = requests.Session()
_oturum.headers["User-Agent"] = "QuakeMind/1.0"
_kilit = threading.Lock()
_yapilandirma_onbellek = {"veri": None, "zaman": 0.0}


def _yapilandirma() -> dict:
    """{surum: {"tarih": "YYYY-MM-DD", "metadata": url}}; gunde bir tazelenir."""
    with _kilit:
        veri = _yapilandirma_onbellek["veri"]
        if veri is not None and time.time() - _yapilandirma_onbellek["zaman"] < 24 * 3600:
            return veri
    ham = _oturum.get(CONFIG_URL, timeout=15).json()
    yeni = {}
    for surum, kayit in ham.items():
        baslik = kayit.get("itemTitle") or ""
        if "Wayback " not in baslik or not kayit.get("metadataLayerUrl"):
            continue
        yeni[str(surum)] = {
            "tarih": baslik.split("Wayback ")[-1].rstrip(")"),
            "metadata": kayit["metadataLayerUrl"],
        }
    with _kilit:
        _yapilandirma_onbellek["veri"] = yeni
        _yapilandirma_onbellek["zaman"] = time.time()
    return yeni


def karo(lat: float, lon: float, z: int) -> tuple[int, int]:
    """Web Mercator karo numarasi (x, y) -- fetcher.py ile ayni formul."""
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return x, y


def _karo_merkezi(x: int, y: int, z: int) -> tuple[float, float]:
    n = 2 ** z
    lon = (x + 0.5) / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 0.5) / n))))
    return lat, lon


def _katman(z: int) -> int:
    return min(13, max(0, 23 - z))


@lru_cache(maxsize=4096)
def _gercek_surum(surum: str, z: int, x: int, y: int):
    """Bu surumde karo gercekte hangi surumden geliyor; karo yoksa None."""
    d = _oturum.get(TILEMAP_URL.format(surum=surum, z=z, y=y, x=x), timeout=15).json()
    if not d.get("valid", True) or not d.get("data") or d["data"][0] == 0:
        return None
    secili = d.get("select")
    return str(secili[0]) if secili else surum


def _cekim_kaydi(ozellik: dict) -> dict:
    ham = ozellik.get("SRC_DATE")
    tarih = None
    if ham:
        s = str(int(ham))
        tarih = f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return {
        "cekimTarihi": tarih,
        "kaynak": ozellik.get("SRC_DESC"),
        "katman": ozellik.get("NICE_NAME"),
        "cozunurlukM": ozellik.get("SRC_RES"),
    }


def _metadata_sorgu(surum: str, z: int, geometri: str, geometri_tipi: str) -> list:
    url = _yapilandirma()[surum]["metadata"]
    d = _oturum.get(f"{url}/{_katman(z)}/query", params={
        "geometry": geometri,
        "geometryType": geometri_tipi,
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "SRC_DATE,SRC_RES,SRC_DESC,NICE_NAME",
        "returnGeometry": "false",
        "f": "json",
    }, timeout=15).json()
    if "error" in d:
        raise RuntimeError(f"Wayback metadata hatasi: {d['error']}")
    return [f["attributes"] for f in d.get("features", [])]


@lru_cache(maxsize=4096)
def _noktada_cekim(surum: str, z: int, lat: float, lon: float):
    ozellikler = _metadata_sorgu(surum, z, f"{lon},{lat}", "esriGeometryPoint")
    return _cekim_kaydi(ozellikler[0]) if ozellikler else None


def olay_iliskisi(tarihler: list, olay_tarihi: str = DEPREM_TARIHI) -> str:
    """"pre" | "post" | "mixed" | "unknown" -- cekimler olaydan once mi sonra mi."""
    bilinen = [t for t in tarihler if t]
    if not bilinen or len(bilinen) < len(tarihler):
        return "unknown" if not bilinen else "mixed"
    if all(t < olay_tarihi for t in bilinen):
        return "pre"
    if all(t >= olay_tarihi for t in bilinen):
        return "post"
    return "mixed"


@lru_cache(maxsize=512)
def _yerel_surumler(z: int, x: int, y: int, olay_tarihi: str, _gun: int) -> dict:
    # `_gun` onbellek anahtarinda: Esri birkac haftada bir yeni surum yayimlar,
    # sonuc en fazla bir gun bayat kalir.
    yapi = _yapilandirma()
    sirali = sorted(yapi, key=lambda s: yapi[s]["tarih"], reverse=True)
    sira = {s: i for i, s in enumerate(sirali)}

    # Yeniden eskiye: her adimda karonun gercek surumu bulunur, sonra o
    # surumden bir onceki surume atlanir. Adim sayisi = farkli goruntu sayisi.
    bulunan, bitis, i = [], "sinir", 0
    while i < len(sirali) and len(bulunan) < EN_FAZLA_ADIM:
        gercek = _gercek_surum(sirali[i], z, x, y)
        if gercek is None:
            bitis = "karo-yok"
            break
        if gercek not in yapi:
            bitis = "bilinmeyen-surum"
            break
        bulunan.append(gercek)
        if yapi[gercek]["tarih"] < olay_tarihi:
            # Olaydan once yayimlanmis surum olay sonrasi goruntu tasiyamaz;
            # bu, olay oncesinin taban goruntusu.
            bitis = "taban"
            break
        i = sira[gercek] + 1
    if i >= len(sirali):
        bitis = "arsiv-basi"

    lat, lon = _karo_merkezi(x, y, z)
    with ThreadPoolExecutor(max_workers=8) as havuz:
        cekimler = list(havuz.map(lambda s: _noktada_cekim(s, z, lat, lon), bulunan))

    surumler = []
    for surum, cekim in zip(bulunan, cekimler):
        cekim = cekim or {"cekimTarihi": None, "kaynak": None, "katman": None, "cozunurlukM": None}
        surumler.append({
            "surumId": surum,
            "surumTarihi": yapi[surum]["tarih"],
            **cekim,
            "olaySonrasi": None if cekim["cekimTarihi"] is None else cekim["cekimTarihi"] >= olay_tarihi,
        })
    return {"zoom": z, "karo": {"x": x, "y": y}, "olayTarihi": olay_tarihi,
            "surumler": surumler, "bitis": bitis}


def yerel_surumler(lat: float, lon: float, z: int, olay_tarihi: str = DEPREM_TARIHI) -> dict:
    """Bir konumda (z yakinlastirmasindaki karo) Wayback'in gosterdigi farkli
    goruntuler, yeniden eskiye. Her biri: goruntuyu getiren surum, surum tarihi,
    cekim tarihi, uydu, cozunurluk, olaydan sonra mi.

    Dolasma olaydan once yayimlanmis ilk surumde durur (`bitis = "taban"`);
    `"karo-yok"` o yakinlastirmada daha eski surumlerde karo olmadigini soyler
    (fetcher bu durumda bir alt yakinlastirmaya iner)."""
    x, y = karo(lat, lon, z)
    return _yerel_surumler(z, x, y, olay_tarihi, int(time.time() // 86400))


def alan_cekimleri(surum: str, bounds, z: int) -> list:
    """Istenen surumun metadata katmaninda bir kutuya dusen farkli cekimler.

    Istenen surumun katmani, o surumun miras aldigi karolari da dogru anlatir
    (olculdu: 2023-02-23 surumu Antakya'da "Maps 2022.R04 / 2021-09-27" doner).
    Donus: cekim tarihine gore sirali, tekrarsiz liste."""
    west, south, east, north = bounds
    ozellikler = _metadata_sorgu(str(surum), z, f"{west},{south},{east},{north}", "esriGeometryEnvelope")
    gorulen, liste = set(), []
    for o in ozellikler:
        kayit = _cekim_kaydi(o)
        anahtar = (kayit["cekimTarihi"], kayit["kaynak"], kayit["cozunurlukM"])
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            liste.append(kayit)
    return sorted(liste, key=lambda k: k["cekimTarihi"] or "")


def surum_tarihi(surum: str):
    kayit = _yapilandirma().get(str(surum))
    return kayit["tarih"] if kayit else None
