# -*- coding: utf-8 -*-
"""Yol agi ve yol maskesi YEREL dosyadan (Overpass'siz).

NEDEN. Overpass'in dort aynasi da ulasilamadiginda (olculdu 26 Eylul: 000,
21-30 sn) yol maskesi bos geliyor, kosu "0 kapali yol" deyip sessizce
anlamsizlasiyordu (J-68). Tatbikat ayni alanda her kosuda ayni sonucu vermeli;
bu, dis bir servisin o anki haline baglanamaz (CLAUDE.md 8).

KAYNAK. `araclar_yerel_osm_kur.py`nin yerel Turkiye PBF'inden tek gecisle
cikardigi `data/osm/roads.gpkg`. Ayni dosya hem grafi hem maskeyi besler --
boylece "modelin kapattigi yol" ile "rotanin kullandigi yol" AYNI veridir;
iki ayri kaynak kullanildiginda kenarlar birbirini tutmuyordu.

Graf YONLUDUR ve `oneway` etiketine uyar: Turkiye'de trafik sagdan akar, tek
yonlu sokaga ters girilemez. Donus maliyetleri `donus.py`de.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

VERI = Path(__file__).resolve().parents[1] / "data" / "osm"
YOLLAR = VERI / "roads.gpkg"

# Yol sinifina gore serbest akis hizi (km/sa). `maxspeed` etiketi varsa O
# kullanilir; yoksa buradan gelir. Degerler Turkiye kentici yol siniflarinin
# olagan hizlaridir (tasarim karari, olcum degil) -- tatbikat raporunda hangi
# hizin nereden geldigi yazilir.
SINIF_HIZI_KMH = {
    "motorway": 90, "motorway_link": 50,
    "trunk": 70, "trunk_link": 45,
    "primary": 50, "primary_link": 35,
    "secondary": 45, "secondary_link": 30,
    "tertiary": 40, "tertiary_link": 30,
    "unclassified": 30, "residential": 30, "living_street": 20,
    "service": 20, "road": 30, "track": 20,
}
VARSAYILAN_HIZ_KMH = 30.0
# Afet sonrasi yavaslama: enkaz, kalabalik, gecici kapanmalar. Tatbikatta
# BEYAN EDILEN carpan; duyarliligi raporda olculur.
AFET_CARPANI = 0.5


def veri_var() -> bool:
    return YOLLAR.exists()


def _oku(bounds):
    import geopandas as gpd

    bati, guney, dogu, kuzey = bounds
    return gpd.read_file(YOLLAR, bbox=(bati, guney, dogu, kuzey))


def _sayi(x, varsayilan=None):
    try:
        if x is None:
            return varsayilan
        s = str(x).strip().split()[0]
        return float(s)
    except Exception:
        return varsayilan


def hiz_kmh(satir) -> float:
    """Kenarin serbest akis hizi: once `maxspeed`, sonra yol sinifi."""
    v = _sayi(satir.get("maxspeed"))
    if v and 5 <= v <= 130:
        return float(v)
    return float(SINIF_HIZI_KMH.get(str(satir.get("highway") or ""), VARSAYILAN_HIZ_KMH))


def tek_yon(satir) -> bool:
    return str(satir.get("oneway") or "").lower() in ("yes", "true", "1", "-1", "reverse")


def ters_tek_yon(satir) -> bool:
    """OSM `oneway=-1`: trafik cizim yonunun TERSINE akar (v -> u). Eskiden bu
    da duz tek yon sayilip u -> v kuruluyordu, yani bu yollar yanlis yonde
    acikti (J-113)."""
    return str(satir.get("oneway") or "").lower() in ("-1", "reverse")


def graf(bounds):
    """Kutudaki yol agi: yonlu MultiDiGraph, `oneway` uygulanmis.

    Dugum kimligi PBF'teki dugum kimligidir; kenarda `length`, `highway`,
    `maxspeed`, `oneway`, `hizKmh` ve `geometry` tasinir.
    """
    import networkx as nx
    from shapely.geometry import LineString

    gdf = _oku(bounds)
    G = nx.MultiDiGraph()
    if gdf.empty:
        return G
    for _, s in gdf.iterrows():
        g = s.get("geometry")
        if g is None or g.is_empty:
            continue
        hatlar = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        u, v = s.get("u"), s.get("v")
        if u is None or v is None:
            continue
        for hat in hatlar:
            if not isinstance(hat, LineString) or len(hat.coords) < 2:
                continue
            koord = list(hat.coords)
            uzunluk = _sayi(s.get("length")) or _hat_uzunlugu_m(koord)
            h = hiz_kmh(s)
            for n, (lon, lat) in ((u, koord[0]), (v, koord[-1])):
                if n not in G:
                    G.add_node(n, x=float(lon), y=float(lat))
            ortak = dict(length=float(uzunluk), highway=s.get("highway"),
                         maxspeed=s.get("maxspeed"), oneway=tek_yon(s),
                         hizKmh=h, name=s.get("name"), osmid=s.get("id"))
            if ters_tek_yon(s):
                # yalniz v -> u; geometri de trafik yonunde olsun
                G.add_edge(v, u, geometry=LineString(koord[::-1]), **ortak)
                continue
            G.add_edge(u, v, geometry=hat, **ortak)
            if not tek_yon(s):
                G.add_edge(v, u, geometry=LineString(koord[::-1]), **ortak)
    return G


def _hat_uzunlugu_m(koord):
    R = 6371000.0
    t = 0.0
    for (lo1, la1), (lo2, la2) in zip(koord[:-1], koord[1:]):
        f1, f2 = math.radians(la1), math.radians(la2)
        df, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
        a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
        t += 2 * R * math.asin(math.sqrt(a))
    return t


def maske(bounds, w, h, kalinlik_px=6):
    """Yol maskesi (uint8 0/1) -- grafla AYNI kaynaktan."""
    import cv2

    gdf = _oku(bounds)
    m = np.zeros((h, w), dtype=np.uint8)
    if gdf.empty:
        return m
    bati, guney, dogu, kuzey = bounds
    for g in gdf.geometry.dropna():
        hatlar = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        for hat in hatlar:
            p = [[int((lo - bati) / (dogu - bati) * w), int((kuzey - la) / (kuzey - guney) * h)]
                 for lo, la in hat.coords]
            if len(p) >= 2:
                cv2.polylines(m, [np.array(p, np.int32).reshape((-1, 1, 2))], False, 1,
                              thickness=int(kalinlik_px))
    return m
