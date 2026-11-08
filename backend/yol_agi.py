"""Yurume yol agi ve afetzede rotasi (J-44).

Afetzede ekrani toplanma alanina ve hastaneye rotayi eskiden kus ucusu
cizgiyle gosteriyordu. Yol tarifi istenirse dis servisten (OSRM) geliyordu;
o servis bilinen kapanmalari bilmiyordu. Burada rota kendi motorumuzla ve
kendi yol agimizda hesaplanir:

  * Ag `araclar_yol_agi_uret.py` ile yerel OSM kopyasindan bir kez uretilir
    (veri/yol_agi/<bolge>.npz) ve burada bir kez bellege alinir. Yol agi
    istek yolunda kurulmaz (kural 3).
  * Arama: Dijkstra (scipy, C), afetzedenin konumundan TEK kosu. Secilen
    yere giden rota da yakindaki butun yerlerin yurume mesafesi de ayni
    aramadan cikar.
  * Hasar cezasi arac motorunun kuraliyla aynidir
    (`apps/road_damage/utils/network.py::risk_weight`): kenarin en yakin
    hasar noktasina uzakligi 50 m altindaysa 3x, 150 m 1,5x, 400 m 1,1x.
    Uzaklik kenarin dogru parcasina olculur. Arac motoru kenarin orta
    noktasini kullanir; yurume aginin kenarlari kisa oldugu icin fark kucuk,
    ama uzun kenar orta noktayla olculunce kapanma kaciyordu (39'un 4'u).
    Hasar noktasi: uydu analizi (skor >= 0,5), kamera ihbari ve enkaz
    bildiren yazili ihbar. SOS cagrisi tehlike sayilmaz: yardim bekleyen
    insandir.
  * Bilinen kapanma (uydu analizi, `yol_kapanmalari`): 25 m icindeki kenar
    SILINMEZ, maliyeti 20 kat olur (yumusak maliyet, J-34). Baska yol yoksa
    rota yine bulunur ve yanit bunu soyler. Tasarim karari [T]: yaya, arac
    icin kapali yoldan cogu zaman gecebilir ama tehlikelidir.

Istek basina maliyet: bir Dijkstra ve hasar verisi degistiyse carpan
yeniden hesabi. Olculen degerler J-44'te.
"""

from __future__ import annotations

import json
import math
import threading
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

AG_DIZINI = Path(__file__).resolve().parent / "veri" / "yol_agi"

YAYA_HIZI_M_DK = 80.0  # ~4,8 km/sa; sokak rotasiyla ayni
KAPANMA_YARICAPI_M = 25.0
KAPANMA_CARPANI = 20.0
HASAR_YARICAPI_M = 400.0  # risk_weight'in en genis kademesi
OTURMA_UYARI_M = 300.0  # konum yol agina bundan uzaksa ekran uyarir

# Adsiz yolun ekrandaki adi, OSM yol turune gore.
TUR_ADI = {
    "footway": "yaya yolu", "pedestrian": "yaya alanı", "path": "patika", "steps": "merdiven",
    "track": "toprak yol", "cycleway": "bisiklet yolu", "service": "servis yolu",
    "living_street": "sokak", "residential": "sokak", "unclassified": "yol", "corridor": "geçit",
}


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


class Ag:
    """Bir bolgenin yol agi: dugumler, kenarlar ve CSR komsuluk.

    Yurume agi yonsuzdur (her kenar CSR'de iki yonde) ve maliyeti metredir.
    Arac agi (J-55, `arac_rotasi.py`) yonludur ve maliyeti saniyedir (yolun
    turu ve yasal sinirindan `arac_rotasi.ag_yukle` kurar); ayni sinif ikisini
    de tasir."""

    def __init__(self, bilgi: dict, dizin: Optional[Path] = None):
        from scipy.spatial import cKDTree

        z = np.load((dizin or AG_DIZINI) / f"{bilgi['id']}.npz")
        self.bilgi = bilgi
        self.lon = z["dugum_lon"]
        self.lat = z["dugum_lat"]
        self.indptr = z["indptr"]
        self.indices = z["indices"]
        self.kenar = z["kenar"]  # CSR girdisinin yonsuz kenar numarasi
        self.u = z["kenar_u"]
        self.v = z["kenar_v"]
        self.uzunluk = z["kenar_uzunluk"].astype(np.float64)
        self.yol = z["kenar_yol"]
        self.yol_adi = z["yol_adi"]
        self.yol_tipi = z["yol_tipi"]
        # Aramanin taban maliyeti: yurumede uzunluk (m). Arac aginda
        # `arac_rotasi` yolun turu ve yasal sinirindan sureyi (sn) kurar.
        self.yol_sinir = z["yol_sinir"] if "yol_sinir" in z.files else None
        self.sure: Optional[np.ndarray] = None
        self.taban = self.uzunluk

        # Yerel metre izdusumu (bolge 24 km; esdikdortgen yaklasim yeterli).
        self.lat0 = float(self.lat.mean())
        self.lon0 = float(self.lon.mean())
        self.kx = 111320.0 * math.cos(math.radians(self.lat0))
        self.ky = 110574.0
        xy = self.xy(self.lon, self.lat)
        self.dugum_xy = xy
        self.dugum_agaci = cKDTree(xy)
        self.orta = (xy[self.u] + xy[self.v]) / 2.0
        self.kenar_agaci = cKDTree(self.orta)
        # Aday kenar aramasi orta noktadan yapilir; uzun kenarin bir ucu
        # noktaya yakinken orta noktasi uzak olabilir. Arama yaricapi
        # kenarlarin %99,5'inin yarim boyu kadar genisletilir; ondan uzun
        # (kir yolu gibi) birkac yuz kenar her noktada ayrica denenir.
        # Uzaklik sonra dogru parcasina tam olculur.
        yarim = self.uzunluk / 2.0
        self.yari = float(np.percentile(yarim, 99.5))
        self.uzun = np.nonzero(yarim > self.yari)[0]

        self._kilit = threading.Lock()
        self._imza = None
        self._carpan = np.ones(len(self.u))
        self._kapali = np.zeros(len(self.u), dtype=bool)

    def xy(self, lon, lat):
        lon = np.asarray(lon, dtype=np.float64)
        lat = np.asarray(lat, dtype=np.float64)
        return np.column_stack(((lon - self.lon0) * self.kx, (lat - self.lat0) * self.ky))

    def _adaylar(self, noktalar: np.ndarray, r: float):
        for p, aday in zip(noktalar, self.kenar_agaci.query_ball_point(noktalar, r + self.yari)):
            k = np.union1d(np.asarray(aday, dtype=np.int64), self.uzun)
            yield p, k, self._parca_uzakligi(p, k)

    def _parca_uzakligi(self, p: np.ndarray, k: np.ndarray) -> np.ndarray:
        """Noktanin kenar dogru parcalarina uzakligi (metre)."""
        a = self.dugum_xy[self.u[k]]
        ab = self.dugum_xy[self.v[k]] - a
        uzunluk2 = np.maximum((ab * ab).sum(axis=1), 1e-9)
        t = np.clip(((p - a) * ab).sum(axis=1) / uzunluk2, 0.0, 1.0)
        return np.hypot(*(a + ab * t[:, None] - p).T)

    def oturt(self, lon: float, lat: float) -> tuple[int, float]:
        mesafe, i = self.dugum_agaci.query(self.xy([lon], [lat])[0])
        return int(i), float(mesafe)

    def carpanlar(self, imza, kapanmalar, hasarlar) -> tuple[np.ndarray, np.ndarray]:
        """Kenar basina maliyet carpani ve kapali kenar isareti. Hasar verisi
        degismedikce onceki hesap kullanilir (imza: sayi + son zaman)."""
        from apps.road_damage.utils.network import risk_weight

        with self._kilit:
            if imza == self._imza:
                return self._carpan, self._kapali
            carpan = np.ones(len(self.u))
            kapali = np.zeros(len(self.u), dtype=bool)
            if hasarlar:
                en_az = np.full(len(self.u), np.inf)
                noktalar = self.xy([h[0] for h in hasarlar], [h[1] for h in hasarlar])
                for _p, k, d in self._adaylar(noktalar, HASAR_YARICAPI_M):
                    np.minimum.at(en_az, k, d)
                yakin = np.nonzero(en_az < HASAR_YARICAPI_M)[0]
                # Arac motorunun kurali, ayni islev (kademeler tek yerde).
                carpan[yakin] = [risk_weight(float(d)) for d in en_az[yakin]]
            if kapanmalar:
                noktalar = self.xy([k[0] for k in kapanmalar], [k[1] for k in kapanmalar])
                for _p, k, d in self._adaylar(noktalar, KAPANMA_YARICAPI_M):
                    kapali[k[d <= KAPANMA_YARICAPI_M]] = True
                carpan[kapali] *= KAPANMA_CARPANI
            self._imza, self._carpan, self._kapali = imza, carpan, kapali
            return carpan, kapali

    def _matris(self, carpan: np.ndarray):
        from scipy.sparse import csr_matrix

        agirlik = np.maximum(self.taban[self.kenar] * carpan[self.kenar], 0.01)
        return csr_matrix((agirlik, self.indices, self.indptr), shape=(len(self.lon), len(self.lon)))

    def dijkstra(self, kaynak: int, carpan: np.ndarray):
        from scipy.sparse.csgraph import dijkstra

        return dijkstra(self._matris(carpan), directed=True, indices=kaynak, return_predecessors=True)

    def dijkstra_ters(self, hedef: int, carpan: np.ndarray):
        """Her dugumden HEDEFE en kisa maliyet (yonlu agda ters kenarlar
        uzerinde tek arama). Donen `onceki` dizisi, her dugumden hedefe giden
        yoldaki bir SONRAKI dugumdur."""
        from scipy.sparse.csgraph import dijkstra

        return dijkstra(self._matris(carpan).T.tocsr(), directed=True, indices=hedef, return_predecessors=True)

    def kenar_bul(self, a: int, b: int) -> int:
        bas, son = self.indptr[a], self.indptr[a + 1]
        j = bas + int(np.searchsorted(self.indices[bas:son], b))
        return int(self.kenar[j])

    def yol_dugumleri(self, onceki: np.ndarray, hedef: int) -> list[int]:
        yol = [hedef]
        while onceki[yol[-1]] >= 0:
            yol.append(int(onceki[yol[-1]]))
        return yol[::-1]


@lru_cache(maxsize=5)
def ag_yukle(bolge_id: str) -> Ag:
    bilgi = next(b for b in katalog() if b["id"] == bolge_id)
    return Ag(bilgi)


def hasar_verisi(kutu) -> tuple[tuple, list, list, Optional[float]]:
    """Bolgedeki bilinen kapanmalar ve hasar noktalari (lon, lat)."""
    from depo import aktif_depo

    depo = aktif_depo()
    kapanma = depo.kapanma_listele(kutu=tuple(kutu), sinir=50000)
    hasar = [
        h for h in depo.hasar_listele(kutu=tuple(kutu), sinir=100000)
        if h["kaynak"] == "kamera"
        or (h["kaynak"] == "uydu" and h["skor"] >= 0.5)
        or (h["kaynak"] == "metin" and h.get("etiket") == "Enkaz Bildirimi")
    ]
    son = max([k["zaman"] for k in kapanma] + [h["zaman"] for h in hasar], default=None)
    imza = (len(kapanma), len(hasar), son)
    return imza, [(k["lon"], k["lat"]) for k in kapanma], [(h["lon"], h["lat"]) for h in hasar], son


class Arama:
    """Afetzedenin konumundan tek Dijkstra kosusu; hedeflere rota ve mesafe."""

    def __init__(self, lon: float, lat: float):
        b = bolge_bul(lon, lat)
        if b is None:
            raise LookupError("Bu konum için yol ağı üretilmedi.")
        self.ag = ag_yukle(b["id"])
        self.bas = (lon, lat)
        self.kaynak, self.kaynak_mesafe = self.ag.oturt(lon, lat)
        imza, kapanmalar, hasarlar, son = hasar_verisi(b["kutu"])
        self.carpan, self.kapali = self.ag.carpanlar(imza, kapanmalar, hasarlar)
        self.hasar_ozeti = {
            "kapanma": len(kapanmalar),
            "hasarNoktasi": len(hasarlar),
            "sonVeri": round(son * 1000) if son else None,
        }
        self.maliyet, self.onceki = self.ag.dijkstra(self.kaynak, self.carpan)

    def icinde(self, lon: float, lat: float) -> bool:
        w, s, e, n = self.ag.bilgi["kutu"]
        return w <= lon <= e and s <= lat <= n

    def mesafe(self, lon: float, lat: float) -> Optional[float]:
        """Yurume mesafesi (metre): rotanin gercek uzunlugu, maliyeti degil."""
        if not self.icinde(lon, lat):
            return None
        hedef, hedef_mesafe = self.ag.oturt(lon, lat)
        if not np.isfinite(self.maliyet[hedef]):
            return None
        dugumler = self.ag.yol_dugumleri(self.onceki, hedef)
        uzunluk = sum(self.ag.uzunluk[self.ag.kenar_bul(a, b)] for a, b in zip(dugumler, dugumler[1:]))
        return float(uzunluk) + self.kaynak_mesafe + hedef_mesafe

    def rota(self, lon: float, lat: float) -> Optional[dict]:
        if not self.icinde(lon, lat):
            return None
        ag = self.ag
        hedef, hedef_mesafe = ag.oturt(lon, lat)
        if not np.isfinite(self.maliyet[hedef]):
            return None
        dugumler = ag.yol_dugumleri(self.onceki, hedef)
        kenarlar = [ag.kenar_bul(a, b) for a, b in zip(dugumler, dugumler[1:])]

        koordinatlar = [[float(ag.lon[n]), float(ag.lat[n])] for n in dugumler]
        # Konumdan yola ve yoldan hedefe kisa baglanti (duz cizgi, birkac metre).
        if self.kaynak_mesafe > 3:
            koordinatlar.insert(0, [self.bas[0], self.bas[1]])
        if hedef_mesafe > 3:
            koordinatlar.append([lon, lat])

        ag_uzunlugu = float(sum(ag.uzunluk[k] for k in kenarlar))
        uzunluk = ag_uzunlugu + self.kaynak_mesafe + hedef_mesafe

        adimlar = _adimlar(ag, dugumler, kenarlar)

        riskli = [k for k in kenarlar if self.carpan[k] > 1.0]
        kapali = [k for k in kenarlar if self.kapali[k]]
        return {
            "koordinatlar": koordinatlar,
            "uzunlukM": round(uzunluk),
            "yuruyusDk": max(1, round(uzunluk / YAYA_HIZI_M_DK)),
            "adimlar": adimlar,
            "algoritma": "Dijkstra, hasar cezalı yürüme maliyeti",
            "hasar": {
                **self.hasar_ozeti,
                "rotadaRiskliM": round(float(sum(ag.uzunluk[k] for k in riskli))),
                "rotadaKapanma": len(kapali),
            },
            "baglanti": {"baslangicM": round(self.kaynak_mesafe), "hedefM": round(hedef_mesafe)},
            "kaynak": {
                "ag": ag.bilgi["id"],
                "osm": ag.bilgi["kaynak"]["dosyaTarihi"],
                "uretim": ag.bilgi["uretim"],
            },
        }


# --- adim adim yol tarifi --------------------------------------------------------
#
# Adimlar rotanin kendisinden cikar, elle yazilmaz: ardisik ayni adli (OSM `name`)
# kenarlar tek adimdir; adsiz yol turune gore adlandirilir. Donus yonu sokak
# gecisindeki aci farkindan hesaplanir: kavsaktan ADIM_ACI_M once ve sonraki
# noktalara yon alinir (kisa kenarlar yonu oynatmasin). Yurume sirasinda hangi
# adimda olundugunu izleyen bir sistem YOK; liste rota istendiginde bir kez
# hesaplanir.

ADIM_ACI_M = 20.0
KISA_ADIM_M = 12.0  # bundan kisa adim sonrakiyle birlesir (kavsak icindeki parca)
YONLER = ("kuzey", "kuzeydoğu", "doğu", "güneydoğu", "güney", "güneybatı", "batı", "kuzeybatı")


def _yon_derece(lon1, lat1, lon2, lat2) -> float:
    r = math.pi / 180.0
    dl = (lon2 - lon1) * r
    y = math.sin(dl) * math.cos(lat2 * r)
    x = math.cos(lat1 * r) * math.sin(lat2 * r) - math.sin(lat1 * r) * math.cos(lat2 * r) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _manevra(fark: float) -> str:
    """Gelen ve giden yon farki (-180, 180] -> donus turu. Pozitif: saga."""
    a = abs(fark)
    if a < 20:
        return "duz"
    taraf = "sag" if fark > 0 else "sol"
    if a < 60:
        return f"hafif-{taraf}"
    if a < 135:
        return taraf
    return f"keskin-{taraf}"


def _adimlar(ag: "Ag", dugumler: list[int], kenarlar: list[int]) -> list[dict]:
    if not kenarlar:
        return []
    # Dugum boyunca birikimli uzaklik.
    kum = [0.0]
    for k in kenarlar:
        kum.append(kum[-1] + float(ag.uzunluk[k]))

    # 1) Ayni adli ardisik kenarlar: [baslangic dugum sirasi, bitis sirasi, ad].
    parcalar: list[list] = []
    for i, k in enumerate(kenarlar):
        yol = int(ag.yol[k])
        ad = str(ag.yol_adi[yol]) or TUR_ADI.get(str(ag.yol_tipi[yol]), "adsız yol")
        if parcalar and parcalar[-1][2] == ad:
            parcalar[-1][1] = i + 1
        else:
            parcalar.append([i, i + 1, ad])

    # 2) Kavsak icindeki kisa parca sonrakine katilir (sonuncusu oncekine).
    #    Katilan parca yeniden denenir: art arda kisa parcalar da toplanir.
    i = 0
    while i < len(parcalar) and len(parcalar) > 1:
        bas, son, _ad = parcalar[i]
        if kum[son] - kum[bas] >= KISA_ADIM_M:
            i += 1
            continue
        if i < len(parcalar) - 1:
            parcalar[i + 1][0] = bas
        else:
            parcalar[i - 1][1] = son
        parcalar.pop(i)
        if i == len(parcalar):
            break

    # 3) Birlesmeden sonra yan yana dusen ayni adli adimlar tek adim olur.
    birlesik: list[list] = []
    for bas, son, ad in parcalar:
        if birlesik and birlesik[-1][2] == ad:
            birlesik[-1][1] = son
        else:
            birlesik.append([bas, son, ad])

    def nokta(i: int):
        n = dugumler[i]
        return float(ag.lon[n]), float(ag.lat[n])

    def geri(i: int) -> int:
        j = i
        while j > 0 and kum[i] - kum[j] < ADIM_ACI_M:
            j -= 1
        return j

    def ileri(i: int) -> int:
        j = i
        while j < len(dugumler) - 1 and kum[j] - kum[i] < ADIM_ACI_M:
            j += 1
        return j

    adimlar = []
    for j, (bas, son, ad) in enumerate(birlesik):
        uzunluk = round(kum[son] - kum[bas])
        if uzunluk <= 0:
            continue
        if j == 0:
            yon = _yon_derece(*nokta(bas), *nokta(ileri(bas)))
            adimlar.append({"ad": ad, "uzunlukM": uzunluk, "manevra": "basla",
                            "yon": YONLER[round(yon / 45.0) % 8]})
            continue
        gelen = _yon_derece(*nokta(geri(bas)), *nokta(bas))
        giden = _yon_derece(*nokta(bas), *nokta(ileri(bas)))
        fark = (giden - gelen + 540.0) % 360.0 - 180.0
        adimlar.append({"ad": ad, "uzunlukM": uzunluk, "manevra": _manevra(fark)})
    return adimlar
