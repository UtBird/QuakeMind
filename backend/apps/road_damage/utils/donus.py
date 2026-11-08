# -*- coding: utf-8 -*-
"""Sagdan akan trafikte donus maliyetleri ve KENAR TABANLI en kisa yol.

NEDEN KENAR TABANLI. Klasik Dijkstra/A* dugum uzerinde calisir ve bir kavsaga
NASIL girildigini bilmez; bu yuzden sola donusu saga donusle ayni fiyata alir,
U donusunu de bedava yapar. Turkiye'de trafik SAGDAN aktigi icin sola donus
karsi akimi keser ve gercek hayatta beklemeyi gerektirir. Maliyeti aramadan
SONRA rapora eklemek yanlistir: rota zaten yanlis secilmis olur. Bu yuzden
arama durumu "hangi kenardayim" olarak tutulur (satir grafigi / line graph) ve
kenar->kenar gecisine donus maliyeti eklenir.

DONUS SINIFLARI (sagdan trafik):
    duz    |a| <= 30 derece            maliyet yok
    sag    a  saga, 30 < |a| <= 150    kucuk (karsi akimi kesmez)
    sol    a  sola, 30 < |a| <= 150    buyuk (karsi akimi keser)
    U      |a| > 150 veya ayni sokaga geri donus

SAYILARIN KAYNAGI. Bunlar OLCULMUS degil, BEYAN EDILMIS tasarim
parametreleridir (CLAUDE.md 1: her sayinin bir kaynagi olmali; burada kaynak
"tasarim karari" ve mertebe kentici kavsak gecikmeleriyle uyumlu secilmistir).
Sonucun bu secime ne kadar bagli oldugu `duyarlilik` ile ayrica olculur ve
raporlanir -- eski tatbikattaki 20 dakikalik sabit "yeniden yonlenme cezasi"
gibi sonucu tek basina belirleyen bir sayi birakilmaz.
"""
from __future__ import annotations

import heapq
import math

# Donus basina saniye. Buyukluk mertebesi: sinyalsiz kentici kavsak.
DONUS_SN = {"duz": 0.0, "sag": 3.0, "sol": 10.0, "u": 25.0}
# U donusu yasak degildir (afette manevra yapilir) ama pahalidir.
DUZ_ESIGI = 30.0
U_ESIGI = 150.0


def _aci_farki(a: float, b: float) -> float:
    """b - a, (-180, 180] araliginda. Artı = SAGA (saat yonu)."""
    d = (b - a + 180.0) % 360.0 - 180.0
    return d


def yon(lat1, lon1, lat2, lon2) -> float:
    """Kuzeyden saat yonunde derece (0-360)."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(f2)
    x = math.cos(f1) * math.sin(f2) - math.sin(f1) * math.cos(f2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def donus_tipi(gelen_yon: float, giden_yon: float, geri_mi: bool = False) -> str:
    """Kavsaga `gelen_yon` ile girip `giden_yon` ile cikmanin donus sinifi."""
    if geri_mi:
        return "u"
    a = _aci_farki(gelen_yon, giden_yon)
    if abs(a) <= DUZ_ESIGI:
        return "duz"
    if abs(a) > U_ESIGI:
        return "u"
    return "sag" if a > 0 else "sol"


def _dugum_konumu(G, n):
    d = G.nodes[n]
    if "y" in d and "x" in d:
        return float(d["y"]), float(d["x"])
    if "lat" in d and "lon" in d:
        return float(d["lat"]), float(d["lon"])
    raise KeyError(f"dugum {n} icin konum yok")


def kenar_yonleri(G):
    """Her yonlu kenar icin (giris yonu, cikis yonu) derece.

    Kenarin `geometry`si varsa bas ve son parcasindan, yoksa dugumlerden
    hesaplanir -- egri bir sokakta giris ve cikis yonu farklidir ve donus
    acisini belirleyen budur.
    """
    yonler = {}
    for u, v, k, d in G.edges(keys=True, data=True):
        geom = d.get("geometry")
        koord = None
        if geom is not None:
            try:
                koord = [(lat, lon) for lon, lat in geom.coords]
            except Exception:
                koord = None
        if koord and len(koord) >= 2:
            giris = yon(koord[0][0], koord[0][1], koord[1][0], koord[1][1])
            cikis = yon(koord[-2][0], koord[-2][1], koord[-1][0], koord[-1][1])
        else:
            (la1, lo1), (la2, lo2) = _dugum_konumu(G, u), _dugum_konumu(G, v)
            giris = cikis = yon(la1, lo1, la2, lo2)
        yonler[(u, v, k)] = (giris, cikis)
    return yonler


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def en_yuksek_hiz(G, kenar_suresi) -> float | None:
    """Cizgedeki en yuksek kenar hizi (m/s): uzunluk / kenar_suresi.

    A* sezgiseli (kus ucusu uzaklik / en yuksek hiz) YALNIZ bu hiz hicbir
    kenarda asilmiyorsa kabul edilebilir. Eskiden sabit 22,2 m/s (~80 km/sa)
    kullaniliyordu; hiz tablosunda otoyol 90 km/sa ve `maxspeed` 130'a kadar
    kabul edildiginden A* eniyi yolu kacirabiliyordu (J-114)."""
    en = 0.0
    for u, v, k, d in G.edges(keys=True, data=True):
        uz = d.get("length", 0.0) or 0.0
        s = kenar_suresi(u, v, k, d)
        if uz > 0 and s is not None and not math.isinf(s) and s > 0:
            en = max(en, uz / s)
    return en or None


def en_kisa_yol(G, kaynak, hedef, kenar_suresi, yonler=None, donus_sn=None,
                a_yildiz: bool = True, en_yuksek_hiz_ms: float | None = None,
                gelen_kenar=None):
    """Donus maliyetli en kisa (SUREYE gore) yol.

    kenar_suresi(u, v, k, d) -> saniye. Kapali kenarlar icin `math.inf`
    dondurulerek kenar tamamen kapatilabilir.

    `gelen_kenar` verilirse (ekip o kavsaga BU kenarla girdi), ilk donus de
    ucretlendirilir -- yoksa ajan her yeniden planlamada bedava U donusu
    yapabilirdi ve sagdan trafik kurali ilk adimda delinirdi.

    Donus: (toplam_saniye, dugum_listesi, kenar_listesi, donus_sayaci) ya da
    yol yoksa (None, None, None, None).
    """
    if kaynak == hedef:
        return 0.0, [kaynak], [], {"duz": 0, "sag": 0, "sol": 0, "u": 0}
    if yonler is None:
        yonler = kenar_yonleri(G)
    ceza = dict(DONUS_SN if donus_sn is None else donus_sn)

    h_lat, h_lon = _dugum_konumu(G, hedef)
    if a_yildiz and en_yuksek_hiz_ms is None:
        # cagiran vermediyse cizgeden hesapla (kabul edilebilirlik icin sart)
        en_yuksek_hiz_ms = en_yuksek_hiz(G, kenar_suresi)
        if en_yuksek_hiz_ms is None:
            a_yildiz = False

    def sezgi(n):
        if not a_yildiz:
            return 0.0
        la, lo = _dugum_konumu(G, n)
        return _haversine_m(la, lo, h_lat, h_lon) / en_yuksek_hiz_ms

    # Durum = az once gecilen YONLU KENAR. Boylece kavsaga nasil girildigi bilinir.
    yigin = []
    en_iyi: dict = {}
    onceki: dict = {}
    gelen_yon0 = yonler[gelen_kenar][1] if gelen_kenar in yonler else None
    for _u, v, k, d in G.edges(kaynak, keys=True, data=True):
        s = kenar_suresi(kaynak, v, k, d)
        if s is None or math.isinf(s):
            continue
        durum = (kaynak, v, k)
        ilk = s
        if gelen_yon0 is not None:
            t0 = donus_tipi(gelen_yon0, yonler[durum][0],
                            geri_mi=(v == gelen_kenar[0]))
            ilk += ceza.get(t0, 0.0)
        if ilk < en_iyi.get(durum, math.inf):
            en_iyi[durum] = ilk
            onceki[durum] = None
            heapq.heappush(yigin, (ilk + sezgi(v), ilk, durum))

    while yigin:
        _f, g, durum = heapq.heappop(yigin)
        if g > en_iyi.get(durum, math.inf):
            continue
        u, v, k = durum
        if v == hedef:
            kenarlar = []
            d = durum
            while d is not None:
                kenarlar.append(d)
                d = onceki[d]
            kenarlar.reverse()
            dugumler = [kenarlar[0][0]] + [e[1] for e in kenarlar]
            sayac = {"duz": 0, "sag": 0, "sol": 0, "u": 0}
            for e1, e2 in zip(kenarlar, kenarlar[1:]):
                t = donus_tipi(yonler[e1][1], yonler[e2][0], geri_mi=(e2[1] == e1[0]))
                sayac[t] += 1
            return g, dugumler, kenarlar, sayac
        gelen = yonler[durum][1]
        for _v, w, k2, d2 in G.edges(v, keys=True, data=True):
            s = kenar_suresi(v, w, k2, d2)
            if s is None or math.isinf(s):
                continue
            t = donus_tipi(gelen, yonler[(v, w, k2)][0], geri_mi=(w == u))
            yeni = g + ceza.get(t, 0.0) + s
            yeni_durum = (v, w, k2)
            if yeni < en_iyi.get(yeni_durum, math.inf):
                en_iyi[yeni_durum] = yeni
                onceki[yeni_durum] = durum
                heapq.heappush(yigin, (yeni + sezgi(w), yeni, yeni_durum))
    return None, None, None, None
