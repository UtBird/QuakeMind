# -*- coding: utf-8 -*-
"""Donus maliyetli aramanin gercekten donusu umursadigini gosterir.

Bu bir IDDIA degil OLCUMDUR: sagdan trafikte sola donus karsi akimi keser,
o yuzden esit uzunluktaki iki secenekten sag donuslu olan secilmelidir.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx  # noqa: E402

from apps.road_damage.utils import donus  # noqa: E402

# 3x3 izgara; ~111 m arayla (0,001 derece enlem).
ADIM = 0.001


def izgara():
    G = nx.MultiDiGraph()
    for i in range(3):
        for j in range(3):
            G.add_node((i, j), y=36.0 + i * ADIM, x=36.0 + j * ADIM)
    for i in range(3):
        for j in range(3):
            for di, dj in ((0, 1), (1, 0)):
                a, b = (i, j), (i + di, j + dj)
                if b in G:
                    G.add_edge(a, b, length=111.0)
                    G.add_edge(b, a, length=111.0)
    return G


def sure(_u, _v, _k, d):
    return d["length"] / (30.0 / 3.6)     # 30 km/sa


def test_sol_donus_sagdan_pahali():
    """Ayni kavsakta sola donmek saga donmekten pahali olmali."""
    G = izgara()
    y = donus.kenar_yonleri(G)
    # (1,1)'e GUNEYDEN gelelim: (0,1) -> (1,1). Kuzeye gidiyoruz.
    gelen = ((0, 1), (1, 1), 0)
    sag = donus.en_kisa_yol(G, (1, 1), (1, 2), sure, yonler=y, gelen_kenar=gelen)[0]
    sol = donus.en_kisa_yol(G, (1, 1), (1, 0), sure, yonler=y, gelen_kenar=gelen)[0]
    duz = donus.en_kisa_yol(G, (1, 1), (2, 1), sure, yonler=y, gelen_kenar=gelen)[0]
    print(f"   duz {duz:.1f} sn | sag {sag:.1f} sn | sol {sol:.1f} sn")
    assert duz < sag < sol, (duz, sag, sol)
    assert math.isclose(sag - duz, donus.DONUS_SN["sag"], abs_tol=1e-6)
    assert math.isclose(sol - duz, donus.DONUS_SN["sol"], abs_tol=1e-6)


def test_esit_uzunlukta_sag_donuslu_yol_secilir():
    """Iki L yolu ayni uzunlukta; sagdan trafikte sag donuslu olan secilir."""
    G = izgara()
    y = donus.kenar_yonleri(G)
    gelen = ((0, 0), (1, 0), 0)          # kuzeye gidiyoruz, (1,0)'dayiz
    # hedef (2,1): ya once kuzey sonra dogu (sag donus), ya once dogu sonra kuzey (sol)
    sn, dugumler, kenarlar, sayac = donus.en_kisa_yol(
        G, (1, 0), (2, 1), sure, yonler=y, gelen_kenar=gelen)
    print(f"   secilen yol {dugumler} | donusler {sayac} | {sn:.1f} sn")
    assert sayac["sol"] == 0, sayac
    assert sayac["sag"] == 1, sayac


def test_u_donusu_en_pahali():
    G = izgara()
    y = donus.kenar_yonleri(G)
    gelen = ((0, 1), (1, 1), 0)
    u = donus.en_kisa_yol(G, (1, 1), (0, 1), sure, yonler=y, gelen_kenar=gelen)[0]
    duz = donus.en_kisa_yol(G, (1, 1), (2, 1), sure, yonler=y, gelen_kenar=gelen)[0]
    print(f"   duz {duz:.1f} sn | U {u:.1f} sn")
    assert u - duz >= donus.DONUS_SN["u"] - 1e-6, (u, duz)


def test_tek_yon_ters_girilemez():
    """`oneway` kenar tek yonlu eklendiyse ters yon bulunmamali."""
    G = nx.MultiDiGraph()
    G.add_node("a", y=36.000, x=36.000)
    G.add_node("b", y=36.001, x=36.000)
    G.add_edge("a", "b", length=111.0)          # yalniz a->b
    y = donus.kenar_yonleri(G)
    ileri = donus.en_kisa_yol(G, "a", "b", sure, yonler=y)[0]
    geri = donus.en_kisa_yol(G, "b", "a", sure, yonler=y)[0]
    print(f"   ileri {ileri:.1f} sn | geri {geri}")
    assert ileri is not None and geri is None


def test_ters_tek_yon_ters_yonde_kurulur():
    """OSM `oneway=-1`: trafik cizim yonunun tersine akar; yalniz v -> u (J-113)."""
    import geopandas as gpd
    from shapely.geometry import LineString

    from apps.road_damage.utils import yerel_yol

    satirlar = gpd.GeoDataFrame([
        {"u": "a", "v": "b", "oneway": "-1", "highway": "residential", "length": 111.0,
         "maxspeed": None, "name": None, "id": 1,
         "geometry": LineString([(36.000, 36.000), (36.000, 36.001)])},
        {"u": "c", "v": "d", "oneway": "yes", "highway": "residential", "length": 111.0,
         "maxspeed": None, "name": None, "id": 2,
         "geometry": LineString([(36.001, 36.000), (36.001, 36.001)])},
    ], geometry="geometry", crs="EPSG:4326")
    eski = yerel_yol._oku
    yerel_yol._oku = lambda _bounds: satirlar
    try:
        G = yerel_yol.graf((35.9, 35.9, 36.1, 36.1))
    finally:
        yerel_yol._oku = eski
    print(f"   kenarlar {sorted((u, v) for u, v in G.edges())}")
    assert G.has_edge("b", "a") and not G.has_edge("a", "b")   # oneway=-1
    assert G.has_edge("c", "d") and not G.has_edge("d", "c")   # oneway=yes


def _hizli_dolambac_cizgesi():
    """Kisa ama yavas dogrudan yol (S->H, 90 km/sa) ile uzun ama hizli dolambac
    (S->A->H, 130 km/sa). Dolambac daha kisa surer; 80 km/sa varsayan sabit
    sezgisel A'yi fazla pahali sanip yavas yolu secer."""
    G = nx.MultiDiGraph()
    G.add_node("S", y=36.0, x=36.0)
    G.add_node("H", y=36.0 + 0.00998, x=36.0)
    G.add_node("A", y=36.0 + 0.00499, x=36.0 + 0.0056)
    def uz(a, b):
        na, nb = G.nodes[a], G.nodes[b]
        return donus._haversine_m(na["y"], na["x"], nb["y"], nb["x"])
    G.add_edge("S", "H", length=uz("S", "H"), v=90 / 3.6)
    G.add_edge("S", "A", length=uz("S", "A"), v=130 / 3.6)
    G.add_edge("A", "H", length=uz("A", "H"), v=130 / 3.6)
    return G


def _hizli_sure(_u, _v, _k, d):
    return d["length"] / d["v"]


def test_astar_hizli_kenarda_eniyi_yolu_bulur():
    """A* sezgiseli cizgenin gercek en yuksek hizini kullanir (J-114)."""
    G = _hizli_dolambac_cizgesi()
    y = donus.kenar_yonleri(G)
    # Yalniz sezgisel sinaniyor: dolambactaki donusun maliyeti sonucu karistirmasin.
    sifir = {"duz": 0.0, "sag": 0.0, "sol": 0.0, "u": 0.0}
    dijkstra = donus.en_kisa_yol(G, "S", "H", _hizli_sure, yonler=y, donus_sn=sifir, a_yildiz=False)[0]
    astar = donus.en_kisa_yol(G, "S", "H", _hizli_sure, yonler=y, donus_sn=sifir)[0]
    eski = donus.en_kisa_yol(G, "S", "H", _hizli_sure, yonler=y, donus_sn=sifir,
                             en_yuksek_hiz_ms=22.2)[0]
    print(f"   Dijkstra {dijkstra:.1f} sn | A* {astar:.1f} sn | eski sabit 80 km/sa A* {eski:.1f} sn")
    assert math.isclose(astar, dijkstra, abs_tol=1e-6)
    assert eski > dijkstra + 1.0   # eski sezgisel gercekten eniyi olmayan yolu seciyordu


def test_manevra_iki_kez_sayilmaz():
    """Donus maliyeti acikken kapanma sabiti yalniz degerlendirmedir; manevrayi
    ekibin fiilen yaptigi donus oder (J-112)."""
    from apps.road_damage.utils import network

    G = izgara()
    for _u, _v, d in G.edges(data=True):
        d["hizKmh"] = 30.0
    kapali = {((1, 1), (2, 1), 0), ((2, 1), (1, 1), 0)}
    gorev = [{"startLat": 36.0, "startLon": 36.0 + ADIM,          # (0,1)
              "endLat": 36.0 + 2 * ADIM, "endLon": 36.0 + ADIM}]  # (2,1)
    acik = network.simulate_reference_fleet(G, kapali, gorev, turn_costs=True, edge_speeds=True)[0]
    kapali_donus = network.simulate_reference_fleet(G, kapali, gorev, turn_costs=False, edge_speeds=True)[0]
    print(f"   donus acik: ceza {acik['kapanmaCezasiDk']} dk, kesif {acik['discoveries']}, "
          f"donusler {acik['donusler']} | donus kapali: ceza {kapali_donus['kapanmaCezasiDk']} dk")
    assert math.isclose(acik["kapanmaCezasiDk"], network.DEGERLENDIRME_DK, abs_tol=1e-3)
    assert math.isclose(kapali_donus["kapanmaCezasiDk"],
                        network.DEGERLENDIRME_DK + network.MANEVRA_DK, abs_tol=1e-3)
    assert acik["discoveries"] == 1


if __name__ == "__main__":
    for ad, f in sorted(globals().items()):
        if ad.startswith("test_"):
            print(f"{ad}:")
            f()
            print("   GECTI")
