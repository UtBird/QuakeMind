"""Arac rotasi (J-55, J-171): yol agi uzerinde en kisa sureli rota.

Ag `araclar_arac_agi_uret.py` ile yerel OSM kopyasindan bir kez uretilir
(veri/yol_agi/arac/<bolge>.npz, genel.npz, yasaklar.json); sunucu bir kez
bellege alir (kural 3: ag istek yolunda kurulmaz).

KENAR TABANLI arama (J-171). Dijkstra'nin durumu dugum degil "hangi yolun
basindayim"dir; bir yoldan otekine gecis ayri bir adimdir. Boylece:

  * Tek yon ve gobek: ag yonludur; gobek (junction=roundabout) ve otoyol
    tek yondur. Gobek icinde donus bedeli sayilmaz.
  * Donus yasaklari: OSM `type=restriction` (no_left_turn, only_straight_on
    ...) gecisleri agdan cikarir. Dugum tabanli arama bunlari tasiyamiyordu:
    taban olcumde kavsaktan gecen 28 rotanin 16'si yasagi cigniyordu.
  * U donusu: yol ortasinda ve kavsakta yok; yalniz cikmaz sokagin sonunda.
  * Donus bedeli: kavsakta (en az uc yol) sola donus saga donusten pahali,
    duz gecis bedelsiz. Degerler VARSAYIMDIR [T] (DONUS_SN), olculmedi.
  * Yola oturtma: baslangic ve hedef en yakin dugume degil, en yakin YOL
    PARCASINA, yonuyle oturtulur. Tek yonlu caddenin ortasindaki olaya
    yalniz akis yonunden gelinir. Otoyol ve devlet yolu, yakinda baska yol
    varsa secilmez (yaya ya da bina otoyola baglanmaz).

Maliyet: kenar suresi (yol turu ve yasal sinirdan) x hasar carpani + donus
bedeli. Hasar carpani yurume rotasiyla ayni kuraldir (`yol_agi.Ag.carpanlar`):
hasar noktasina yakin kenar pahali, bilinen kapanmadaki kenar 20 kat. Rota
kapanmadan kacinir; baska yol yoksa yine bulunur ve yanit bunu soyler.
`kacin=False` hasar ve kapanmayi yok sayar (kiyas icin).

Iki ag vardir. Iki nokta ayni sehirdeyse sehir agi; farkli sehirlerdeyse
bolgeler arasi ag (`genel`: bes sehir agi ve aralarindaki ana yollar). Ikisinin
de disindaysa sonuc yoktur; ekran kus ucusuna doner ve bunu yazar.

Sure: kenar sureleri + donus bedelleri. Hiz yol turune gore ortalama bir
VARSAYIMDIR; anlik trafik verisi yok. Hasar carpani rota secimini etkiler,
sureye eklenmez.
"""

from __future__ import annotations

import json
import math
import threading
import time
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

import yol_agi

AG_DIZINI = Path(__file__).resolve().parent / "veri" / "yol_agi" / "arac"
MOTOR = "kenar tabanlı Dijkstra: tek yön, göbek, dönüş yasağı ve dönüş bedeli (J-171)"

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
# Kavsakta donus bedeli (sn), VARSAYIM [T]: sagdan akan trafikte sola donus
# karsi seridi keser. Yalniz en az uc yolun bulustugu dugumde sayilir; yolun
# kivrimi donus degildir.
DONUS_SN = {"duz": 0.0, "hafif": 1.0, "sag": 4.0, "sol": 9.0, "keskin": 14.0, "geri": 20.0}
GOBEGE_GIRIS_SN = 3.0
# Oturtma: once bu yaricaplarda yol parcasi aranir (m).
OTURTMA_YARICAPI_M = (60.0, 250.0, 1000.0)
# Otoyol ve devlet yoluna oturtma, yakinda baska yol varsa bu kat uzak sayilir.
ANA_YOL_OTURTMA_KATI = 3.0
ANA_YOL = {"motorway", "trunk"}
DUGUM_PAYI_M = 1.5

# Uzun rotanin cizgisi sadelestirilir (liste yanitlari sismesin): ~15 m sapma.
ROTA_NOKTA_SINIRI = 400
ROTA_SADELESTIRME_DERECE = 0.00015
# Konumdan yola ve yoldan olaya baglanti parcasi (duz cizgi) bu hizla sayilir.
BAGLANTI_HIZI_MS = 15 / 3.6
ONBELLEK_BOYU = 32
HASAR_TAZELIK_SN = 10.0
ARAC_KAPANMA_CARPANI = 1e6


@lru_cache(maxsize=1)
def katalog() -> list[dict]:
    yol = AG_DIZINI / "katalog.json"
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else []


@lru_cache(maxsize=1)
def _yasaklar() -> list[dict]:
    yol = AG_DIZINI / "yasaklar.json"
    return json.loads(yol.read_text(encoding="utf-8"))["yasaklar"] if yol.exists() else []


def bolge_bul(lon: float, lat: float) -> Optional[dict]:
    for b in katalog():
        w, s, e, n = b["kutu"]
        if w <= lon <= e and s <= lat <= n:
            return b
    return None


# --- kenar tabanli ag ---------------------------------------------------------------


class KenarAgi:
    """Yonlu yol aginin "kenardan kenara gecis" grafi.

    Durum `e`: kenar e'nin basindayim (u[e]); gecis e -> f, f kenar e'nin
    bittigi dugumden cikar; agirligi w(e) + donus bedeli(e, f). Yasakli ve
    U donusu gecisler grafta yoktur."""

    def __init__(self, ag: yol_agi.Ag, gobek_yol: Optional[np.ndarray], yasaklar: list[dict]):
        t0 = time.perf_counter()
        self.ag = ag
        E = len(ag.u)
        self.E = E
        u = ag.u.astype(np.int64)
        v = ag.v.astype(np.int64)
        indptr = ag.indptr.astype(np.int64)
        cikis = np.diff(indptr)

        # Gecisler: e -> f, f in cikis(v[e]). Arac aginda CSR girdisi j = kenar j.
        say = cikis[v]
        self.T_den = np.repeat(np.arange(E, dtype=np.int64), say)
        oncesi = np.repeat(np.cumsum(say) - say, say)
        self.T_e = np.repeat(indptr[v], say) + (np.arange(len(self.T_den), dtype=np.int64) - oncesi)

        geri = v[self.T_e] == u[self.T_den]
        cikmaz = say[self.T_den] == 1
        tut = ~geri | cikmaz

        # Donus acisi (derece, + sola) ve bedeli.
        xy = ag.dugum_xy
        d = xy[v] - xy[u]
        yon = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
        aci = (yon[self.T_e] - yon[self.T_den] + 540.0) % 360.0 - 180.0
        mutlak = np.abs(aci)
        bedel = np.select(
            [mutlak < 20, mutlak < 60, (mutlak < 135) & (aci > 0), mutlak < 135],
            [DONUS_SN["duz"], DONUS_SN["hafif"], DONUS_SN["sol"], DONUS_SN["sag"]],
            DONUS_SN["keskin"],
        )
        bedel = np.where(geri, DONUS_SN["geri"], bedel)
        # Kavsak: en az uc FARKLI komsu (yonsuz). Yol kivrimi bedelsiz.
        cift = np.unique(np.concatenate([np.stack([u, v], 1), np.stack([v, u], 1)]), axis=0)
        komsu = np.bincount(cift[:, 0], minlength=len(ag.lon))
        kavsak = komsu[v[self.T_den]] >= 3
        bedel = np.where(kavsak | geri, bedel, 0.0)
        if gobek_yol is not None and len(gobek_yol):
            gk = gobek_yol.astype(bool)[ag.yol]
            ici = gk[self.T_den] & gk[self.T_e]
            giris = ~gk[self.T_den] & gk[self.T_e]
            bedel = np.where(ici, 0.0, np.where(giris, np.minimum(bedel, GOBEGE_GIRIS_SN), bedel))
        self.gobek_kenar = gobek_yol.astype(bool)[ag.yol] if gobek_yol is not None and len(gobek_yol) else None

        # Donus yasaklari.
        self.yasak_ozeti = {"uygulanan": 0, "agdaYok": 0, "eslesmedi": 0}
        yasak = self._yasaklari_oturt(yasaklar, u, v, indptr)
        if len(yasak):
            anahtar = self.T_den * E + self.T_e
            tut &= ~np.isin(anahtar, yasak)

        self.T_den, self.T_e, self.T_bedel = self.T_den[tut], self.T_e[tut], bedel[tut].astype(np.float64)
        self.gecis_sayisi = len(self.T_den)
        # Ileri CSR (satir = T_den; zaten sirali): kenarin izinli gecisleri.
        self.ptr = np.zeros(E + 1, dtype=np.int64)
        np.cumsum(np.bincount(self.T_den, minlength=E), out=self.ptr[1:])
        self._zincir_kur()

        # Dugume giren kenarlar (oturtmada nokta dugumun ustune duserse).
        self.giris_sira = np.argsort(v, kind="stable")
        self.giris_ptr = np.zeros(len(ag.lon) + 1, dtype=np.int64)
        np.cumsum(np.bincount(v, minlength=len(ag.lon)), out=self.giris_ptr[1:])

        tip = np.array([str(t) for t in ag.yol_tipi])
        self.ana_yol = np.isin(tip, list(ANA_YOL))[ag.yol]
        self._kilit = threading.Lock()
        self._agirlik: dict = {}
        self.kurulum_sn = round(time.perf_counter() - t0, 2)

    # -- yasaklar --
    def _yasaklari_oturt(self, yasaklar, u, v, indptr) -> np.ndarray:
        ag = self.ag
        w, s, e, n = ag.bilgi["kutu"]
        giris_sira = np.argsort(v, kind="stable")
        giris_ptr = np.zeros(len(ag.lon) + 1, dtype=np.int64)
        np.cumsum(np.bincount(v, minlength=len(ag.lon)), out=giris_ptr[1:])
        anahtarlar = []

        def cizgiye(noktalar, cizgi):
            c = ag.xy([p[0] for p in cizgi], [p[1] for p in cizgi])
            en = np.full(len(noktalar), np.inf)
            for a, b in zip(c, c[1:]):
                ab = b - a
                l2 = max(float((ab * ab).sum()), 1e-9)
                t = np.clip(((noktalar - a) * ab).sum(axis=1) / l2, 0.0, 1.0)
                en = np.minimum(en, np.hypot(*(a + ab * t[:, None] - noktalar).T))
            return en

        for y in yasaklar:
            kx, ky = y["kavsak"]
            if not (w <= kx <= e and s <= ky <= n):
                continue
            mesafe, dugum = ag.dugum_agaci.query(ag.xy([kx], [ky])[0])
            if mesafe > 1.0:
                self.yasak_ozeti["agdaYok"] += 1
                continue
            gelenler = giris_sira[giris_ptr[dugum]:giris_ptr[dugum + 1]]
            gidenler = np.arange(indptr[dugum], indptr[dugum + 1])
            if not len(gelenler) or not len(gidenler):
                self.yasak_ozeti["eslesmedi"] += 1
                continue
            gelen = gelenler[cizgiye(ag.dugum_xy[u[gelenler]], y["gelen"]) < 1.5]
            giden = gidenler[cizgiye(ag.dugum_xy[v[gidenler]], y["giden"]) < 1.5]
            if not len(gelen) or not len(giden):
                self.yasak_ozeti["eslesmedi"] += 1
                continue
            if y["tur"] == "only_u_turn":
                self.yasak_ozeti["eslesmedi"] += 1  # U donusu zaten yalniz cikmazda
                continue
            if y["tur"] == "no_u_turn" and y["gelen"] == y["giden"]:
                # Ayni yol: yalniz geri donus yasak (zaten yok); yolun ortasindaki
                # duz gecis yasaklanmaz.
                giden = gidenler[np.isin(v[gidenler], u[gelen])]
            if y["tur"].startswith("no_"):
                yasakli = giden
            else:  # only_: verilen yol disindaki her cikis yasak
                yasakli = np.setdiff1d(gidenler, giden)
            for g in gelen:
                anahtarlar.extend(int(g) * self.E + int(f) for f in yasakli)
            self.yasak_ozeti["uygulanan"] += 1
        return np.array(sorted(set(anahtarlar)), dtype=np.int64)

    # -- zincir --
    def _zincir_kur(self):
        """Kavsak olmayan ardisik kenarlar tek durum (zincir) olur: tek cikisli
        kenardan tek girisli kenara bedelsiz gecis. Rota degismez (orada secim
        yok); arama grafi Antakya'da %23'e, bolgeler arasi agda %28'e iner."""
        E = self.E
        cikis = np.bincount(self.T_den, minlength=E)
        giris = np.bincount(self.T_e, minlength=E)
        birles = (cikis[self.T_den] == 1) & (giris[self.T_e] == 1) & (self.T_bedel == 0)
        sonraki = np.full(E, -1, dtype=np.int64)
        sonraki[self.T_den[birles]] = self.T_e[birles]
        onceki = np.full(E, -1, dtype=np.int64)
        onceki[self.T_e[birles]] = self.T_den[birles]
        sonraki_l = sonraki.tolist()
        no = [-1] * E
        sira = [0] * E
        sirali: list[int] = []
        ptr = [0]

        def yuru(h: int):
            e, j, z = h, 0, len(ptr) - 1
            while e >= 0 and no[e] < 0:
                no[e] = z
                sira[e] = j
                sirali.append(e)
                j += 1
                e = sonraki_l[e]
            ptr.append(len(sirali))

        for h in np.nonzero(onceki < 0)[0].tolist():
            yuru(h)
        for h in range(E):  # girisi olmayan kapali halka (ulasilamaz ama tutarli kalsin)
            if no[h] < 0:
                yuru(h)
        self.Z = len(ptr) - 1
        self.z_no = np.asarray(no, dtype=np.int64)
        self.z_sira = np.asarray(sira, dtype=np.int64)
        self.z_kenar = np.asarray(sirali, dtype=np.int64)
        self.z_ptr = np.asarray(ptr, dtype=np.int64)
        # Zincirler arasi gecisler (zincir ici olmayanlar).
        sinir = ((self.z_no[self.T_den] != self.z_no[self.T_e])
                 | (self.z_sira[self.T_e] != self.z_sira[self.T_den] + 1))
        zd, ze, zb = self.z_no[self.T_den[sinir]], self.z_no[self.T_e[sinir]], self.T_bedel[sinir]
        o = np.argsort(zd, kind="stable")
        self.ZT_den, self.ZT_e, self.ZT_bedel = zd[o], ze[o], zb[o]
        self.zptr = np.zeros(self.Z + 1, dtype=np.int64)
        np.cumsum(np.bincount(self.ZT_den, minlength=self.Z), out=self.zptr[1:])
        self.zters_sira = np.argsort(self.ZT_e, kind="stable")
        self.zters_ptr = np.zeros(self.Z + 1, dtype=np.int64)
        np.cumsum(np.bincount(self.ZT_e, minlength=self.Z), out=self.zters_ptr[1:])
        self.zters_den = self.ZT_den[self.zters_sira]

    def zincir_parcasi(self, z: int, bas_sira: int = 0, son_sira: Optional[int] = None) -> list[int]:
        a = int(self.z_ptr[z])
        b = int(self.z_ptr[z + 1]) if son_sira is None else a + son_sira + 1
        return self.z_kenar[a + bas_sira:b].tolist()

    def bedeller(self, kenarlar: list[int]) -> list[float]:
        """Ardisik kenarlar arasi donus bedelleri; zincir icinde sifir."""
        out = []
        for a, b in zip(kenarlar, kenarlar[1:]):
            if self.z_no[a] == self.z_no[b] and self.z_sira[b] == self.z_sira[a] + 1:
                out.append(0.0)
            else:
                out.append(self.gecis_bedeli(a, b) or 0.0)
        return out

    # -- agirlik --
    def agirlik(self, carpan: np.ndarray, imza):
        """(w kenar, W zincir, once: kenarin zincirdeki baslangic payi, gecis
        verisi). Hasar verisi degismedikce onbellekten."""
        with self._kilit:
            kayit = self._agirlik.get(imza)
            if kayit is not None:
                return kayit
        w = np.maximum(self.ag.taban * carpan, 0.01)
        sirali = w[self.z_kenar]
        kum = np.cumsum(sirali) - sirali
        bas = np.repeat(kum[self.z_ptr[:-1]], np.diff(self.z_ptr))
        once = np.empty(self.E)
        once[self.z_kenar] = kum - bas
        W = np.add.reduceat(sirali, self.z_ptr[:-1])
        veri = W[self.ZT_den] + self.ZT_bedel
        kayit = (w, W, once, veri)
        with self._kilit:
            if len(self._agirlik) > 4:
                self._agirlik.clear()
            self._agirlik[imza] = kayit
        return kayit

    def konum(self, k: int, t: float, agirlik) -> tuple[int, float]:
        """Kenar k'nin t noktasi: (zincir, zincir basindan maliyet)."""
        w, _W, once, _v = agirlik
        return int(self.z_no[k]), float(once[k] + t * w[k])

    def _dijkstra(self, veri, ters: bool, giris: list[tuple[int, float]]):
        """Zincir grafinda, ust dugumden (indis Z) `giris` durumlarina baslangic
        maliyetiyle tek arama."""
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import dijkstra

        Z = self.Z
        if ters:
            ptr, idx, dat = self.zters_ptr, self.zters_den, veri[self.zters_sira]
        else:
            ptr, idx, dat = self.zptr, self.ZT_e, veri
        hedefler = np.array([g for g, _ in giris], dtype=np.int64)
        maliyetler = np.array([max(m, 0.0) + 1e-6 for _, m in giris], dtype=np.float64)
        M = csr_matrix(
            (np.concatenate([dat, maliyetler]), np.concatenate([idx, hedefler]),
             np.concatenate([ptr, [ptr[-1] + len(hedefler)]])),
            shape=(Z + 1, Z + 1),
        )
        return dijkstra(M, directed=True, indices=Z, return_predecessors=True)

    # -- oturtma --
    def oturt(self, lon: float, lat: float) -> list[tuple[int, float, float]]:
        """Noktanin oturdugu yol parcasi: [(kenar, t, uzaklik_m), ...]. Iki yonlu
        yolda iki kenar (ters yonde t = 1 - t). t: kenar boyunca 0..1."""
        ag = self.ag
        p = ag.xy([lon], [lat])[0]
        aday = np.array([], dtype=np.int64)
        d = np.array([])
        for r in OTURTMA_YARICAPI_M:
            aday = np.union1d(np.asarray(ag.kenar_agaci.query_ball_point(p, r + ag.yari), dtype=np.int64), ag.uzun)
            d = ag._parca_uzakligi(p, aday)
            if (d <= r).any():
                break
        if not len(aday):
            return []
        puan = d * np.where(self.ana_yol[aday], ANA_YOL_OTURTMA_KATI, 1.0)
        k = int(aday[int(np.argmin(puan))])
        a = ag.dugum_xy[ag.u[k]]
        ab = ag.dugum_xy[ag.v[k]] - a
        t = float(np.clip(((p - a) * ab).sum() / max(float((ab * ab).sum()), 1e-9), 0.0, 1.0))
        uzaklik = float(np.hypot(*(a + ab * t - p)))
        # Nokta bir dugumun ustundeyse (kavsak, yol ucu) dugume giren ve cikan
        # butun kenarlar: tek kenara giris yasakli donus olabilir.
        boy = float(ag.uzunluk[k])
        dugum = int(ag.u[k]) if t * boy < DUGUM_PAYI_M else int(ag.v[k]) if (1 - t) * boy < DUGUM_PAYI_M else None
        if dugum is not None:
            gelen = self.giris_sira[self.giris_ptr[dugum]:self.giris_ptr[dugum + 1]]
            giden = np.arange(int(ag.indptr[dugum]), int(ag.indptr[dugum + 1]))
            return [(int(g), 1.0, uzaklik) for g in gelen] + [(int(f), 0.0, uzaklik) for f in giden]
        sonuc = [(k, t, uzaklik)]
        ters = self.kenar(int(ag.v[k]), int(ag.u[k]))
        if ters is not None:
            sonuc.append((ters, 1.0 - t, uzaklik))
        return sonuc

    def kenar(self, a: int, b: int) -> Optional[int]:
        ag = self.ag
        bas, son = int(ag.indptr[a]), int(ag.indptr[a + 1])
        j = bas + int(np.searchsorted(ag.indices[bas:son], b))
        return int(ag.kenar[j]) if j < son and int(ag.indices[j]) == b else None

    def gecis_bedeli(self, e: int, f: int) -> Optional[float]:
        bas, son = int(self.ptr[e]), int(self.ptr[e + 1])
        j = np.nonzero(self.T_e[bas:son] == f)[0]
        return float(self.T_bedel[bas + j[0]]) if len(j) else None


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


def _kenar_agi_kur(ag: yol_agi.Ag, dosya: Path) -> yol_agi.Ag:
    z = np.load(dosya)
    gobek = z["yol_gobek"] if "yol_gobek" in z.files else None
    ag.ka = KenarAgi(ag, gobek, _yasaklar())
    return ag


@lru_cache(maxsize=5)
def ag_yukle(bolge_id: str) -> yol_agi.Ag:
    bilgi = next(b for b in katalog() if b["id"] == bolge_id)
    ag = _sure_kur(yol_agi.Ag(bilgi, AG_DIZINI))
    return _kenar_agi_kur(ag, AG_DIZINI / f"{bolge_id}.npz")


@lru_cache(maxsize=1)
def genel_bilgi() -> Optional[dict]:
    yol = AG_DIZINI / "genel.json"
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else None


@lru_cache(maxsize=1)
def genel_ag() -> yol_agi.Ag:
    ag = yol_agi.Ag(genel_bilgi(), AG_DIZINI)
    sehir = np.load(AG_DIZINI / "genel.npz")["kenar_sehir"].astype(bool)
    return _kenar_agi_kur(_sure_kur(ag, sehir), AG_DIZINI / "genel.npz")


def _icinde(b: Optional[dict], lon, lat) -> bool:
    if b is None or lon is None or lat is None:
        return False
    w, s, e, n = b["kutu"]
    return w <= lon <= e and s <= lat <= n


def ag_sec(lon1, lat1, lon2, lat2) -> Optional[tuple[dict, bool]]:
    """Iki nokta icin ag: ayni sehirdeyse sehir agi, degilse bolgeler arasi."""
    b = bolge_bul(lon1, lat1) if lon1 is not None and lat1 is not None else None
    if b is not None and _icinde(b, lon2, lat2):
        return b, False
    g = genel_bilgi()
    if _icinde(g, lon1, lat1) and _icinde(g, lon2, lat2):
        return g, True
    return None


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


def _maliyet_verisi(ag: yol_agi.Ag, b: dict, kacin: bool):
    """(imza, carpan, kapali, agirlik, hasar ozeti)."""
    imza, kapanmalar, hasarlar = _hasar_verisi(b)
    if kacin:
        # Arac kapali yoldan gecmez: carpan cok buyuk, yalniz baska yol yoksa
        # (hedef kapali sokakta, ya da cevresi tumden kapali) gecer ve bunu
        # 'kapanmadanGecer' ile soyler. 20 kat yetmiyordu: kisa kapali parca
        # dolasmaktan ucuz kaliyordu (Elektrik, 40 rotanin 1'i 3 kapanmadan gecti).
        carpan, kapali = ag.carpanlar(imza, kapanmalar, hasarlar, kapanma_carpani=ARAC_KAPANMA_CARPANI)
        anahtar = imza
    else:
        carpan, kapali = np.ones(len(ag.u)), np.zeros(len(ag.u), dtype=bool)
        anahtar = ("kacinma-yok",)
    agirlik = ag.ka.agirlik(carpan, anahtar)
    ozet = {"kapanma": len(kapanmalar), "hasarNoktasi": len(hasarlar)}
    return imza, carpan, kapali, agirlik, ozet


def _rota_ozeti(ag, kenarlar, t_bas, t_son, bedeller, carpan, kapali, bas_mesafe, son_mesafe, bas_nokta, son_nokta):
    """Kenar dizisinden mesafe, sure, kapanma/hasar ozeti ve cizgi."""
    kenarlar = np.asarray(kenarlar, dtype=np.int64)
    pay = np.ones(len(kenarlar))
    if len(kenarlar) == 1:
        pay[0] = max(t_son - t_bas, 0.0)
    elif len(kenarlar):
        pay[0] = 1.0 - t_bas
        pay[-1] = t_son
    yol_m = float((ag.uzunluk[kenarlar] * pay).sum()) if len(kenarlar) else 0.0
    yol_sn = float((ag.sure[kenarlar] * pay).sum()) + float(sum(bedeller)) if len(kenarlar) else 0.0
    baglanti = bas_mesafe + son_mesafe
    ozet = {
        "mesafeM": round(yol_m + baglanti),
        "sureDk": max(1, round((yol_sn + baglanti / BAGLANTI_HIZI_MS) / 60)),
        "kapanmadanGecer": int(kapali[kenarlar].sum()) if len(kenarlar) else 0,
        # Baslangic ya da hedef kapali sokagin ustundeyse gecmek kacinilmaz;
        # ekran bunu "baska yol yok"tan ayri soyler.
        "baslangicKapanmada": bool(kapali[kenarlar[0]]) if len(kenarlar) else False,
        "hedefKapanmada": bool(kapali[kenarlar[-1]]) if len(kenarlar) else False,
        "riskliM": round(float((ag.uzunluk[kenarlar] * pay)[carpan[kenarlar] > 1.0].sum())) if len(kenarlar) else 0,
        "baglantiM": round(bas_mesafe),
    }
    # Cizgi: konum -> yola oturan nokta -> kenar uclari -> hedefe oturan nokta -> hedef.
    def ara(k, t):
        return [float(ag.lon[ag.u[k]] + (ag.lon[ag.v[k]] - ag.lon[ag.u[k]]) * t),
                float(ag.lat[ag.u[k]] + (ag.lat[ag.v[k]] - ag.lat[ag.u[k]]) * t)]

    koordinatlar = []
    if len(kenarlar):
        if bas_mesafe > 3:
            koordinatlar.append(list(bas_nokta))
        koordinatlar.append(ara(kenarlar[0], t_bas))
        for k in kenarlar[:-1]:
            koordinatlar.append([float(ag.lon[ag.v[k]]), float(ag.lat[ag.v[k]])])
        koordinatlar.append(ara(kenarlar[-1], t_son))
        if son_mesafe > 3:
            koordinatlar.append(list(son_nokta))
    dugumler = [int(ag.u[kenarlar[0]])] + [int(ag.v[k]) for k in kenarlar] if len(kenarlar) else []
    return ozet, koordinatlar, dugumler


class HedefAramasi:
    """Bir olaya gelen en kisa sureler: ters zincir grafinda tek Dijkstra.
    Olaya gelen butun ekiplerin suresi ve rotasi ayni aramadan cikar."""

    def __init__(self, b: dict, lon: float, lat: float, genel: bool = False, kacin: bool = True):
        self.ag = genel_ag() if genel else ag_yukle(b["id"])
        self.bolge = b
        self.hedef = (lon, lat)
        ka = self.ag.ka
        self.oturma = ka.oturt(lon, lat)
        self.hedef_mesafe = self.oturma[0][2] if self.oturma else math.inf
        self.imza, self.carpan, self.kapali, self.agirlik, self.hasar_ozeti = _maliyet_verisi(self.ag, b, kacin)
        # Hedefin oturdugu zincirler: zincir -> (zincir basindan maliyet, kenar, t).
        self.hedefler: dict[int, tuple[float, int, float]] = {}
        for k, t, _d in self.oturma:
            z, m = ka.konum(k, t, self.agirlik)
            if z not in self.hedefler or m < self.hedefler[z][0]:
                self.hedefler[z] = (m, k, t)
        t0 = time.perf_counter()
        giris = [(z, m) for z, (m, _k, _t) in self.hedefler.items()]
        self.maliyet, self.sonraki = (ka._dijkstra(self.agirlik[3], ters=True, giris=giris)
                                      if giris else (None, None))
        self.sure_ms = round((time.perf_counter() - t0) * 1000, 1)

    def _en_iyi(self, k: int, t: float):
        """Ekip kenar k'nin t noktasinda: (maliyet, ilk sonraki zincir; -1 ayni zincirde hedef)."""
        ka = self.ag.ka
        z, m0 = ka.konum(k, t, self.agirlik)
        en = (math.inf, None)
        if z in self.hedefler and self.hedefler[z][0] >= m0:
            en = (self.hedefler[z][0] - m0, -1)
        bas, son = int(ka.zptr[z]), int(ka.zptr[z + 1])
        if son > bas:
            d = ka.ZT_e[bas:son]
            m = (self.agirlik[1][z] - m0) + ka.ZT_bedel[bas:son] + self.maliyet[d]
            i = int(np.argmin(m))
            if m[i] < en[0]:
                en = (float(m[i]), int(d[i]))
        return en

    def ekipten(self, lon: Optional[float], lat: Optional[float], rota: bool = True) -> Optional[dict]:
        """Ekibin konumundan olaya: yoldan uzaklik, tahmini sure, rotanin
        kapanma ve hasar ozeti ve cizgisi. Ekip bolge disindaysa None."""
        if lon is None or lat is None or self.maliyet is None:
            return None
        if not _icinde(self.bolge, lon, lat):
            return None
        ka = self.ag.ka
        adaylar = []
        for k, t, d in ka.oturt(lon, lat):
            m, ilk = self._en_iyi(k, t)
            if np.isfinite(m):
                adaylar.append((m, k, t, d, ilk))
        if not adaylar:
            return None
        _m, k, t, d, ilk = min(adaylar, key=lambda x: x[0])
        z = int(ka.z_no[k])
        if ilk == -1:
            _hm, hk, ht = self.hedefler[z]
            kenarlar = ka.zincir_parcasi(z, int(ka.z_sira[k]), int(ka.z_sira[hk]))
        else:
            kenarlar = ka.zincir_parcasi(z, int(ka.z_sira[k]))
            durum = ilk
            while True:
                if int(self.sonraki[durum]) == ka.Z:  # hedef zinciri
                    _hm, hk, ht = self.hedefler[durum]
                    kenarlar += ka.zincir_parcasi(durum, 0, int(ka.z_sira[hk]))
                    break
                kenarlar += ka.zincir_parcasi(durum)
                durum = int(self.sonraki[durum])
        ozet, koordinatlar, _d = _rota_ozeti(self.ag, kenarlar, t, ht, ka.bedeller(kenarlar), self.carpan,
                                             self.kapali, d, self.hedef_mesafe, (lon, lat), self.hedef)
        if rota:
            ozet["rota"] = _sadelestir(koordinatlar)
        return ozet


def _sadelestir(koordinatlar: list) -> list:
    """Uzun rota (sehirler arasi binlerce nokta) ~15 m sapmayla sadelesir."""
    if len(koordinatlar) > ROTA_NOKTA_SINIRI:
        from shapely.geometry import LineString

        koordinatlar = [list(p) for p in LineString(koordinatlar).simplify(ROTA_SADELESTIRME_DERECE).coords]
    return [[round(x, 5), round(y, 5)] for x, y in koordinatlar]


def hedef_aramasi(lon: Optional[float], lat: Optional[float], genel: bool = False,
                  kacin: bool = True) -> Optional[HedefAramasi]:
    """Olay icin arama; ayni olaya (ayni yol parcasi) hasar verisi degismedikce
    onbellekten doner. `genel`: bolgeler arasi agda. Olay agin disindaysa None."""
    if lon is None or lat is None:
        return None
    b = genel_bilgi() if genel else bolge_bul(lon, lat)
    if not _icinde(b, lon, lat):
        return None
    ag = genel_ag() if genel else ag_yukle(b["id"])
    oturma = ag.ka.oturt(lon, lat)
    if not oturma:
        return None
    anahtar = (b["id"], oturma[0][0], round(oturma[0][1], 2), kacin)
    imza = _hasar_verisi(b)[0]
    with _kilit:
        arama = _aramalar.get(anahtar)
        if arama is not None and arama.imza == imza:
            _aramalar.move_to_end(anahtar)
            return arama
    arama = HedefAramasi(b, lon, lat, genel=genel, kacin=kacin)
    with _kilit:
        _aramalar[anahtar] = arama
        while len(_aramalar) > ONBELLEK_BOYU:
            _aramalar.popitem(last=False)
    return arama


def yoldan(hedef_lon, hedef_lat, ekip_lon, ekip_lat, rota: bool = True, kacin: bool = True) -> Optional[dict]:
    """Ekipten olaya yol ozeti. Ayni sehirdeyse sehir agi, farkli sehirlerdeyse
    bolgeler arasi ag; ikisinin de disindaysa None (ekran kus ucusu yazar)."""
    try:
        secim = ag_sec(hedef_lon, hedef_lat, ekip_lon, ekip_lat)
        if secim is None:
            return None
        arama = hedef_aramasi(hedef_lon, hedef_lat, genel=secim[1], kacin=kacin)
    except Exception as e:  # ag dosyasi bozuk ya da eksikse sevk durmasin
        print(f"arac rotasi: {e}", flush=True)
        return None
    return arama.ekipten(ekip_lon, ekip_lat, rota) if arama else None


# --- konsol rota araci (J-171) ---------------------------------------------------


class BaslangicAramasi:
    """Bir noktadan ileri arama: birden cok hedefe (en yakin hastane gibi)
    tek Dijkstra."""

    def __init__(self, b: dict, lon: float, lat: float, genel: bool, kacin: bool):
        self.ag = genel_ag() if genel else ag_yukle(b["id"])
        self.bolge, self.genel, self.bas = b, genel, (lon, lat)
        ka = self.ag.ka
        self.oturma = ka.oturt(lon, lat)
        self.imza, self.carpan, self.kapali, self.agirlik, self.hasar_ozeti = _maliyet_verisi(self.ag, b, kacin)
        W = self.agirlik[1]
        # Baslangic zinciri: kalan maliyet + donus bedeli -> sonraki zincirin basi.
        # Ayni duruma iki giris dusmesin: SciPy yinelenen girdiyi TOPLAR.
        self.ilk: dict[int, tuple[int, float, float]] = {}
        self.baslar: list[tuple[int, int, float, float]] = []  # (zincir, kenar, t, zincir ici maliyet)
        for k, t, _d in self.oturma:
            z, m0 = ka.konum(k, t, self.agirlik)
            self.baslar.append((z, k, t, m0))
            for j in range(int(ka.zptr[z]), int(ka.zptr[z + 1])):
                f = int(ka.ZT_e[j])
                m = (W[z] - m0) + float(ka.ZT_bedel[j])
                if f not in self.ilk or m < self.ilk[f][2]:
                    self.ilk[f] = (k, t, m)
        giris = [(f, m) for f, (_k, _t, m) in self.ilk.items()]
        t0 = time.perf_counter()
        self.maliyet, self.onceki = (ka._dijkstra(self.agirlik[3], ters=False, giris=giris)
                                     if giris else (None, None))
        self.sure_ms = round((time.perf_counter() - t0) * 1000, 1)

    def rota(self, lon: float, lat: float, adim: bool = False) -> Optional[dict]:
        if self.maliyet is None or not _icinde(self.bolge, lon, lat):
            return None
        ka, ag = self.ag.ka, self.ag
        en = (math.inf, None, None)
        for hk, hs, hd in ka.oturt(lon, lat):
            hz, hm = ka.konum(hk, hs, self.agirlik)
            for bz, bk, bt, bm in self.baslar:
                if bz == hz and hm >= bm and hm - bm < en[0]:
                    en = (hm - bm, ("ayni", bk, bt), (hk, hs, hd))
            m = float(self.maliyet[hz]) + hm
            if np.isfinite(m) and m < en[0]:
                en = (m, ("arama",), (hk, hs, hd))
        if not np.isfinite(en[0]):
            return None
        _m, yol, (hk, hs, hd) = en
        hz = int(ka.z_no[hk])
        if yol[0] == "ayni":
            _, bk, t_bas = yol
            kenarlar = ka.zincir_parcasi(hz, int(ka.z_sira[bk]), int(ka.z_sira[hk]))
        else:
            zincir = [hz]
            while int(self.onceki[zincir[-1]]) != ka.Z:
                zincir.append(int(self.onceki[zincir[-1]]))
            zincir.reverse()
            bk, t_bas, _ = self.ilk[zincir[0]]
            kenarlar = ka.zincir_parcasi(int(ka.z_no[bk]), int(ka.z_sira[bk]))
            for z in zincir[:-1]:
                kenarlar += ka.zincir_parcasi(z)
            kenarlar += ka.zincir_parcasi(hz, 0, int(ka.z_sira[hk]))
        bedeller = ka.bedeller(kenarlar)
        ozet, koordinatlar, dugumler = _rota_ozeti(ag, kenarlar, t_bas, hs, bedeller, self.carpan, self.kapali,
                                                   self.oturma[0][2], hd, self.bas, (lon, lat))
        ozet["rota"] = _sadelestir(koordinatlar)
        ozet["donus"] = {
            "sol": sum(1 for x in bedeller if x == DONUS_SN["sol"]),
            "sag": sum(1 for x in bedeller if x == DONUS_SN["sag"]),
        }
        if adim:
            ozet["adimlar"] = yol_agi._adimlar(ag, dugumler, kenarlar)
        return ozet


def baslangic_aramasi(lon, lat, hedef_lon, hedef_lat, kacin: bool = True) -> Optional[BaslangicAramasi]:
    secim = ag_sec(lon, lat, hedef_lon, hedef_lat)
    if secim is None:
        return None
    return BaslangicAramasi(secim[0], lon, lat, secim[1], kacin)


def rota(bas_lon, bas_lat, hedef_lon, hedef_lat, kacin: bool = True) -> Optional[dict]:
    """Iki nokta arasi arac rotasi, adim adim tarifle. Ag disindaysa None."""
    arama = baslangic_aramasi(bas_lon, bas_lat, hedef_lon, hedef_lat, kacin)
    if arama is None:
        return None
    r = arama.rota(hedef_lon, hedef_lat, adim=True)
    if r is not None:
        r["ag"] = "genel" if arama.genel else arama.bolge["id"]
        r["hasar"] = arama.hasar_ozeti
        r["aramaMs"] = arama.sure_ms
    return r


def en_yakinlar(bas_lon, bas_lat, adaylar: list[dict], n: int = 3, kacin: bool = True) -> list[dict]:
    """Adaylardan (lon, lat tasiyan sozlukler) yoldan en cabuk ulasilan n tanesi.
    Ayni sehirdekiler sehir aginda tek aramayla; sehir disindakiler atlanir."""
    b = bolge_bul(bas_lon, bas_lat)
    if b is None:
        return []
    arama = BaslangicAramasi(b, bas_lon, bas_lat, False, kacin)
    sonuc = []
    for a in adaylar:
        if not _icinde(b, a["lon"], a["lat"]):
            continue
        r = arama.rota(a["lon"], a["lat"])
        if r is not None:
            sonuc.append({**a, **r})
    sonuc.sort(key=lambda x: (x["sureDk"], x["mesafeM"]))
    return sonuc[:n]


def oturtma_mesafesi(ag: yol_agi.Ag, lon: float, lat: float) -> float:
    """Olcum araci icin: noktanin oturtuldugu yere uzakligi (m)."""
    o = ag.ka.oturt(lon, lat)
    return o[0][2] if o else math.inf


def kaynak() -> Optional[dict]:
    """Ekranin yazacagi kunye: OSM kopyasinin tarihi ve varsayimlar."""
    k = katalog()
    if not k:
        return None
    return {"osm": k[0]["kaynak"]["dosyaTarihi"], "hizKmSa": HIZ_KMS, "sehirDisiHizKmSa": HIZ_KMS_SEHIR_DISI,
            "donusBedeliSn": DONUS_SN, "motor": MOTOR}
