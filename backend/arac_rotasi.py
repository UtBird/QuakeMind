"""Arac rotasi (J-55): ekipten olaya yol agi uzerinden uzaklik ve tahmini sure.

Sevkte ekibin olaya uzakligi kus ucusuydu (J-54). Kullanici: "normal yolda,
normal trafigin aktigi sekilde yoldan yapamaz misin". Burada:

  * Ag `araclar_arac_agi_uret.py` ile yerel OSM kopyasindan bir kez uretilir
    (veri/yol_agi/arac/<bolge>.npz): tek yonlu sokaklar, kavsak halkalari,
    erisim kisitlari ve yol turune gore hiz. Sunucu bir kez bellege alir.
  * Arama: olaydan (hedef) TERS agda tek Dijkstra (scipy, C). Olaya gelen
    butun ekiplerin suresi ve rotasi ayni aramadan cikar; arama, hasar verisi
    degismedikce onbellekte kalir. Ekip konum bildirdikce yalniz rotasi
    yeniden izlenir, arama tekrarlanmaz.
  * Hasar cezasi ve bilinen kapanma yurume rotasiyla ayni kuraldir
    (`yol_agi.Ag.carpanlar`): hasar noktasina yakin kenar daha pahali,
    kapanmadaki kenar 20 kat. Rota kapanmadan kacinir; baska yol yoksa yine
    bulunur ve yanit bunu soyler.
  * Sure: rotadaki kenarlarin sure toplami. Hiz yol turune gore ortalama bir
    VARSAYIMDIR; anlik trafik verisi yok. Hasar cezasi rota secimini etkiler,
    sureye eklenmez (ceza sure degildir).

Iki ag vardir. Ekip ve olay ayni sehirdeyse sehir agi (hizli, ~22 ms).
Farkli sehirlerdeyse bolgeler arasi ag (`genel`): bes sehir agi ve sehirleri
baglayan ana yollar tek agda (J-55 ek; Antakya'daki ekip Kahramanmaras'taki
olaya kus ucusuyla gorunuyordu). Sehir disi yolda hiz varsayimi baskadir.
Ekip ya da olay iki agin da disindaysa sonuc yoktur; ekran kus ucusuna doner
ve bunu yazar.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

import yol_agi

AG_DIZINI = Path(__file__).resolve().parent / "veri" / "yol_agi" / "arac"

# km/sa: yol turune gore ortalama hiz VARSAYIMI [T], isik ve kavsak dahil
# sehir ici ortalama; olculmedi. Yolun yasal siniri (`maxspeed`) daha dusukse
# sinir kullanilir. Varsayim burada durur: degisince ag yeniden uretilmez.
HIZ_KMS = {
    "motorway": 80, "motorway_link": 40,
    "trunk": 60, "trunk_link": 35,
    "primary": 40, "primary_link": 30,
    "secondary": 35, "secondary_link": 25,
    "tertiary": 30, "tertiary_link": 25,
    "unclassified": 25, "road": 20,
    "residential": 20, "living_street": 10, "service": 10,
}
# Sehir disi (bes sehrin 12 km kutusunun disi) ortalama hiz VARSAYIMI [T];
# yasal sinirlar 90 (devlet yolu), 110 (bolunmus yol), 120 (otoyol).
HIZ_KMS_SEHIR_DISI = {
    "motorway": 100, "motorway_link": 50,
    "trunk": 80, "trunk_link": 40,
    "primary": 70, "primary_link": 35,
    "secondary": 60, "secondary_link": 30,
    "tertiary": 50, "tertiary_link": 30,
    "unclassified": 40, "road": 30,
    "residential": 30, "living_street": 10, "service": 15,
}
# Uzun rotanin cizgisi sadelestirilir (liste yanitlari sismesin): ~15 m sapma.
ROTA_NOKTA_SINIRI = 400
ROTA_SADELESTIRME_DERECE = 0.00015
# Konumdan yola ve yoldan olaya baglanti parcasi (duz cizgi) bu hizla sayilir.
BAGLANTI_HIZI_MS = 15 / 3.6
ONBELLEK_BOYU = 32
HASAR_TAZELIK_SN = 10.0


@lru_cache(maxsize=1)
def katalog() -> list[dict]:
    yol = AG_DIZINI / "katalog.json"
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else []


def bolge_bul(lon: float, lat: float) -> Optional[dict]:
    for b in katalog():
        w, s, e, n = b["kutu"]
        if w <= lon <= e and s <= lat <= n:
            return b
    return None


def _sure_kur(ag: yol_agi.Ag, sehir: Optional[np.ndarray] = None) -> yol_agi.Ag:
    """Kenar suresi (sn): yol turunun varsayim hizi (sehir ici ya da disi),
    yasal sinir dusukse sinir. `sehir` yoksa butun kenarlar sehir ici."""
    tipler = [str(t) for t in ag.yol_tipi]
    sinir = ag.yol_sinir.astype(np.float64)

    def hizlar(tablo, varsayilan):
        v = np.array([tablo.get(t, varsayilan) for t in tipler], dtype=np.float64)
        return np.where(np.isnan(sinir), v, np.minimum(v, sinir))[ag.yol]

    ici = hizlar(HIZ_KMS, 20)
    hiz = ici if sehir is None else np.where(sehir, ici, hizlar(HIZ_KMS_SEHIR_DISI, 30))
    ag.sure = ag.uzunluk / (hiz / 3.6)
    ag.taban = ag.sure
    return ag


@lru_cache(maxsize=5)
def ag_yukle(bolge_id: str) -> yol_agi.Ag:
    bilgi = next(b for b in katalog() if b["id"] == bolge_id)
    return _sure_kur(yol_agi.Ag(bilgi, AG_DIZINI))


@lru_cache(maxsize=1)
def genel_bilgi() -> Optional[dict]:
    yol = AG_DIZINI / "genel.json"
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else None


@lru_cache(maxsize=1)
def genel_ag() -> yol_agi.Ag:
    ag = yol_agi.Ag(genel_bilgi(), AG_DIZINI)
    sehir = np.load(AG_DIZINI / "genel.npz")["kenar_sehir"].astype(bool)
    return _sure_kur(ag, sehir)


def _icinde(b: Optional[dict], lon, lat) -> bool:
    if b is None or lon is None or lat is None:
        return False
    w, s, e, n = b["kutu"]
    return w <= lon <= e and s <= lat <= n


_kilit = threading.Lock()
_aramalar: "OrderedDict[tuple, HedefAramasi]" = OrderedDict()
_hasar: dict[str, tuple] = {}


def _hasar_verisi(b: dict):
    """Bolgenin kapanma ve hasar noktalari; en cok 10 sn eski. Ekip listesi
    her konum bildiriminde yenilenir, her seferinde depo taranmasin."""
    simdi = time.monotonic()
    with _kilit:
        kayit = _hasar.get(b["id"])
        if kayit and simdi - kayit[0] < HASAR_TAZELIK_SN:
            return kayit[1:]
    imza, kapanmalar, hasarlar, _son = yol_agi.hasar_verisi(b["kutu"])
    with _kilit:
        _hasar[b["id"]] = (simdi, imza, kapanmalar, hasarlar)
    return imza, kapanmalar, hasarlar


class HedefAramasi:
    """Bir olaya gelen en kisa sureler: ters agda tek Dijkstra."""

    def __init__(self, b: dict, lon: float, lat: float):
        self.ag = genel_ag() if b["id"] == "genel" else ag_yukle(b["id"])
        self.bolge = b
        self.hedef = (lon, lat)
        self.dugum, self.hedef_mesafe = self.ag.oturt(lon, lat)
        imza, kapanmalar, hasarlar = _hasar_verisi(b)
        self.imza = imza
        self.carpan, self.kapali = self.ag.carpanlar(imza, kapanmalar, hasarlar)
        t0 = time.perf_counter()
        self.maliyet, self.sonraki = self.ag.dijkstra_ters(self.dugum, self.carpan)
        self.sure_ms = round((time.perf_counter() - t0) * 1000, 1)

    def ekipten(self, lon: Optional[float], lat: Optional[float], rota: bool = True) -> Optional[dict]:
        """Ekibin konumundan olaya: yoldan uzaklik, tahmini sure, rotanin
        kapanma ve hasar ozeti ve cizgisi. Ekip bolge disindaysa None."""
        if lon is None or lat is None:
            return None
        w, s, e, n = self.bolge["kutu"]
        if not (w <= lon <= e and s <= lat <= n):
            return None
        ag = self.ag
        bas, bas_mesafe = ag.oturt(lon, lat)
        if not np.isfinite(self.maliyet[bas]):
            return None
        dugumler = [bas]
        while self.sonraki[dugumler[-1]] >= 0:
            dugumler.append(int(self.sonraki[dugumler[-1]]))
        kenarlar = np.array([ag.kenar_bul(x, y) for x, y in zip(dugumler, dugumler[1:])], dtype=np.int64)
        yol_m = float(ag.uzunluk[kenarlar].sum()) if len(kenarlar) else 0.0
        yol_sn = float(ag.sure[kenarlar].sum()) if len(kenarlar) else 0.0
        baglanti = bas_mesafe + self.hedef_mesafe
        sonuc = {
            "mesafeM": round(yol_m + baglanti),
            "sureDk": max(1, round((yol_sn + baglanti / BAGLANTI_HIZI_MS) / 60)),
            "kapanmadanGecer": int(self.kapali[kenarlar].sum()) if len(kenarlar) else 0,
            "riskliM": round(float(ag.uzunluk[kenarlar][self.carpan[kenarlar] > 1.0].sum())) if len(kenarlar) else 0,
            "baglantiM": round(bas_mesafe),
        }
        if rota:
            koordinatlar = [[float(ag.lon[d]), float(ag.lat[d])] for d in dugumler]
            if bas_mesafe > 3:
                koordinatlar.insert(0, [lon, lat])
            if self.hedef_mesafe > 3:
                koordinatlar.append([self.hedef[0], self.hedef[1]])
            sonuc["rota"] = _sadelestir(koordinatlar)
        return sonuc


def _sadelestir(koordinatlar: list) -> list:
    """Uzun rota (sehirler arasi binlerce nokta) ~15 m sapmayla sadelesir."""
    if len(koordinatlar) > ROTA_NOKTA_SINIRI:
        from shapely.geometry import LineString

        koordinatlar = [list(p) for p in LineString(koordinatlar).simplify(ROTA_SADELESTIRME_DERECE).coords]
    return [[round(x, 5), round(y, 5)] for x, y in koordinatlar]


def hedef_aramasi(lon: Optional[float], lat: Optional[float], genel: bool = False) -> Optional[HedefAramasi]:
    """Olay icin arama; ayni olaya (ayni dugum) hasar verisi degismedikce
    onbellekten doner. `genel`: bolgeler arasi agda. Olay agin disindaysa None."""
    if lon is None or lat is None:
        return None
    b = genel_bilgi() if genel else bolge_bul(lon, lat)
    if not _icinde(b, lon, lat):
        return None
    ag = genel_ag() if genel else ag_yukle(b["id"])
    dugum, _ = ag.oturt(lon, lat)
    anahtar = (b["id"], dugum)
    imza = _hasar_verisi(b)[0]
    with _kilit:
        arama = _aramalar.get(anahtar)
        if arama is not None and arama.imza == imza:
            _aramalar.move_to_end(anahtar)
            return arama
    arama = HedefAramasi(b, lon, lat)
    with _kilit:
        _aramalar[anahtar] = arama
        while len(_aramalar) > ONBELLEK_BOYU:
            _aramalar.popitem(last=False)
    return arama


def yoldan(hedef_lon, hedef_lat, ekip_lon, ekip_lat, rota: bool = True) -> Optional[dict]:
    """Ekipten olaya yol ozeti. Ayni sehirdeyse sehir agi, farkli sehirlerdeyse
    bolgeler arasi ag; ikisinin de disindaysa None (ekran kus ucusu yazar)."""
    try:
        b = bolge_bul(hedef_lon, hedef_lat) if hedef_lon is not None and hedef_lat is not None else None
        if b is not None and _icinde(b, ekip_lon, ekip_lat):
            arama = hedef_aramasi(hedef_lon, hedef_lat)
        elif _icinde(genel_bilgi(), hedef_lon, hedef_lat) and _icinde(genel_bilgi(), ekip_lon, ekip_lat):
            arama = hedef_aramasi(hedef_lon, hedef_lat, genel=True)
        else:
            return None
    except Exception as e:  # ag dosyasi bozuk ya da eksikse sevk durmasin
        print(f"arac rotasi: {e}", flush=True)
        return None
    return arama.ekipten(ekip_lon, ekip_lat, rota) if arama else None


def kaynak() -> Optional[dict]:
    """Ekranin yazacagi kunye: OSM kopyasinin tarihi ve hiz varsayimi."""
    k = katalog()
    if not k:
        return None
    return {"osm": k[0]["kaynak"]["dosyaTarihi"], "hizKmSa": HIZ_KMS, "sehirDisiHizKmSa": HIZ_KMS_SEHIR_DISI}
