"""Arac rotasi (J-171): kenar tabanli arama kurallari.

Kucuk sentetik aglarda her kural tek tek sinanir (tek yon, donus yasagi,
U donusu, donus bedeli, gobek, yola oturtma). Gercek ag (veri/yol_agi/arac)
bu makinede varsa OSM donus yasaklarina uyum da sinanir; yoksa atlanir.
"""
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import arac_rotasi  # noqa: E402
import yol_agi  # noqa: E402

LAT0, LON0 = 36.20, 36.16
ADIM = 0.001  # ~100 m


def _kur(dugumler: dict, yollar: list, yasaklar=None, monkeypatch=None):
    """dugumler: ad -> (x, y) izgara birimi. yollar: (ad_listesi, yon, tip, gobek)
    yon: 'iki' | 'ileri'. Donen: (ag, ad -> dugum no)."""
    adlar = list(dugumler)
    no = {a: i for i, a in enumerate(adlar)}
    lon = np.array([LON0 + dugumler[a][0] * ADIM for a in adlar])
    lat = np.array([LAT0 + dugumler[a][1] * ADIM for a in adlar])
    a_l, c_l, y_l = [], [], []
    for yi, (seri, yon, _tip, _g) in enumerate(yollar):
        for p, q in zip(seri, seri[1:]):
            a_l.append(no[p]); c_l.append(no[q]); y_l.append(yi)
            if yon == "iki":
                a_l.append(no[q]); c_l.append(no[p]); y_l.append(yi)
    a, c, y = np.array(a_l), np.array(c_l), np.array(y_l)
    sira = np.lexsort((c, a))
    a, c, y = a[sira], c[sira], y[sira]
    kx = 111320.0 * math.cos(math.radians(LAT0))
    uzunluk = np.hypot((lon[c] - lon[a]) * kx, (lat[c] - lat[a]) * 110574.0)
    N = len(lon)
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(np.bincount(a, minlength=N), out=indptr[1:])
    dizin = Path(tempfile.mkdtemp(prefix="qm_rota_"))
    np.savez(
        dizin / "test.npz",
        dugum_lon=lon, dugum_lat=lat, indptr=indptr.astype(np.int32), indices=c.astype(np.int32),
        kenar=np.arange(len(a), dtype=np.int32), kenar_u=a.astype(np.int32), kenar_v=c.astype(np.int32),
        kenar_uzunluk=uzunluk.astype(np.float32), kenar_yol=y.astype(np.int32),
        yol_adi=np.array([f"yol{i}" for i in range(len(yollar))]),
        yol_tipi=np.array([t for _, _, t, _ in yollar]),
        yol_sinir=np.full(len(yollar), np.nan, dtype=np.float32),
        yol_gobek=np.array([g for *_, g in yollar], dtype=np.uint8),
    )
    bilgi = {"id": "test", "kutu": [LON0 - 0.05, LAT0 - 0.05, LON0 + 0.05, LAT0 + 0.05],
             "kaynak": {"dosyaTarihi": "test"}, "uretim": "test"}
    ag = arac_rotasi._sure_kur(yol_agi.Ag(bilgi, dizin))
    ag.ka = arac_rotasi.KenarAgi(ag, np.array([g for *_, g in yollar], dtype=np.uint8), yasaklar or [])
    monkeypatch.setattr(arac_rotasi, "ag_yukle", lambda _id: ag)
    monkeypatch.setattr(arac_rotasi, "_hasar_verisi", lambda b: ((0, 0, None), [], []))
    return ag, no, bilgi


def _p(x, y):
    return LON0 + x * ADIM, LAT0 + y * ADIM


def _rota(bilgi, bas, hedef):
    a = arac_rotasi.BaslangicAramasi(bilgi, *_p(*bas), False, True)
    return a.rota(*_p(*hedef), adim=True)


def _gecer_mi(rota, *noktalar):
    """Rota cizgisi verilen izgara noktalarindan bu sirayla art arda geciyor mu?"""
    hedef = [list(map(lambda v: round(v, 5), _p(*n))) for n in noktalar]
    r = rota["rota"]
    return any(r[i:i + len(hedef)] == hedef for i in range(len(r) - len(hedef) + 1))


def test_tek_yon_uyulur(monkeypatch):
    # A -> B tek yon (kisa); geri donus B -> C -> D -> A (uzun cevre).
    _ag, _no, b = _kur(
        {"A": (0, 0), "B": (3, 0), "C": (3, 2), "D": (0, 2)},
        [(["A", "B"], "ileri", "residential", 0), (["B", "C", "D", "A"], "iki", "residential", 0)],
        monkeypatch=monkeypatch,
    )
    r = _rota(b, (2.5, 0), (0.5, 0))  # tek yonlu yolda geriye
    assert r is not None
    assert r["mesafeM"] > 600  # kisa yoldan (~200 m) degil, cevreden
    assert not _gecer_mi(r, (3, 0), (0, 0))


def _dortlu(yasaklar=None, monkeypatch=None):
    # Dort kollu kavsak J; kuzey ve bati kollari bir cevre yoluyla bagli.
    return _kur(
        {"J": (0, 0), "N": (0, 2), "S": (0, -2), "E": (2, 0), "W": (-2, 0), "NW": (-2, 2)},
        [(["S", "J"], "iki", "residential", 0), (["J", "N"], "iki", "residential", 0),
         (["J", "E"], "iki", "residential", 0), (["J", "W"], "iki", "residential", 0),
         (["N", "NW", "W"], "iki", "residential", 0)],
        yasaklar, monkeypatch,
    )


def test_donus_yasagi_uygulanir(monkeypatch):
    _ag0, _no, b = _dortlu(monkeypatch=monkeypatch)
    serbest = _rota(b, (0, -1.5), (-1.5, 0))  # guneyden bati koluna: sola donus
    # Yasak yokken J'den dogrudan doner: ~150 m + ~150 m.
    assert serbest is not None and serbest["mesafeM"] < 400 and serbest["donus"]["sol"] == 1
    yasak = [{"tur": "no_left_turn", "gelen": [list(_p(0, -2)), list(_p(0, 0))],
              "kavsak": list(_p(0, 0)), "giden": [list(_p(0, 0)), list(_p(-2, 0))]}]
    ag, _no, b = _dortlu(yasak, monkeypatch)
    assert ag.ka.yasak_ozeti["uygulanan"] == 1
    r = _rota(b, (0, -1.5), (-1.5, 0))
    assert r is not None
    # J'de guneyden batiya donulmez: kuzeye cikip cevre yolundan gelir.
    rota = r["rota"]
    j = [i for i, p in enumerate(rota) if p == [round(v, 5) for v in _p(0, 0)]]
    for i in j:
        if 0 < i < len(rota) - 1:
            assert not (rota[i - 1][0] == rota[i][0] and rota[i - 1][1] < rota[i][1]
                        and rota[i + 1][0] < rota[i][0]), "yasakli sola donus yapildi"
    assert r["mesafeM"] > 500


def test_sag_donus_sol_donusten_ucuz(monkeypatch):
    # Esit uzunlukta iki yol: biri J'de saga, oteki K'da sola doner.
    ag, _no, b = _kur(
        {"S": (0, -2), "J": (0, 0), "E": (2, 0), "T": (2, 2), "W": (-2, 0), "U": (-2, 2), "K": (0, 2),
         "X": (0, -3), "Y": (1, -3), "Z": (-1, -3)},
        [(["S", "J"], "ileri", "residential", 0), (["J", "E", "T", "K"], "ileri", "residential", 0),
         (["J", "W", "U", "K"], "ileri", "residential", 0), (["X", "S"], "ileri", "residential", 0),
         (["Y", "X"], "iki", "residential", 0), (["Z", "X"], "iki", "residential", 0),
         (["K", "Y"], "ileri", "residential", 0)],
        monkeypatch=monkeypatch,
    )
    bedeller = ag.ka.T_bedel
    assert arac_rotasi.DONUS_SN["sol"] in bedeller and arac_rotasi.DONUS_SN["sag"] in bedeller
    r = _rota(b, (0, -1), (0.5, 2.0))  # J'den K'ya iki esit yol
    assert r is not None and r["donus"]["sol"] <= r["donus"]["sag"] + 1


def test_gobek_icinde_donus_bedeli_yok(monkeypatch):
    # Kare gobek (tek yon, saat yonunun tersi) + bir giris kolu.
    ag, _no, _b = _kur(
        {"G1": (0, 0), "G2": (1, 0), "G3": (1, 1), "G4": (0, 1), "G": (0, -2), "C": (2, 1)},
        [(["G1", "G2", "G3", "G4", "G1"], "ileri", "residential", 1),
         (["G", "G1"], "iki", "residential", 0), (["G3", "C"], "iki", "residential", 0)],
        monkeypatch=monkeypatch,
    )
    ka = ag.ka
    gk = ka.gobek_kenar
    ici = gk[ka.T_den] & gk[ka.T_e]
    assert ici.any() and (ka.T_bedel[ici] == 0).all()


def test_yol_ortasina_oturtma(monkeypatch):
    # Uzun tek yonlu cadde; yanindan gecen nokta caddeye, ortasina oturur.
    ag, no, _b = _kur(
        {"A": (0, 0), "B": (10, 0), "C": (0, 3), "D": (10, 3)},
        [(["A", "B"], "ileri", "residential", 0), (["C", "D"], "iki", "residential", 0),
         (["B", "D"], "iki", "residential", 0), (["A", "C"], "iki", "residential", 0)],
        monkeypatch=monkeypatch,
    )
    oturma = ag.ka.oturt(*_p(5, 0.2))
    k, t, d = oturma[0]
    assert (int(ag.u[k]), int(ag.v[k])) == (no["A"], no["B"])
    assert 0.4 < t < 0.6 and d < 30
    assert len(oturma) == 1  # tek yon: ters kenar yok


@pytest.mark.skipif(not (arac_rotasi.AG_DIZINI / "yasaklar.json").exists()
                    or not arac_rotasi.katalog(), reason="gercek yol agi bu makinede yok")
def test_gercek_agda_osm_yasaklarina_uyulur():
    import araclar_rota_olc

    s = araclar_rota_olc.yasak_uyumu()
    assert s["denenen"] > 0
    assert s["ihlal"] == 0, s["ihlaller"][:5]


# --- konsol uclari ------------------------------------------------------------------

GERCEK_AG = (arac_rotasi.AG_DIZINI / "katalog.json").exists()


@pytest.fixture(scope="module")
def istemci():
    import os

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_guz_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    jeton = {}
    for ad, rol in [("koordinator", "koordinator"), ("afetzede", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@guzergah.local", ad, "test-sifresi-123")
        d.rol_ata(k["id"], rol)
        jeton[ad] = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}
    from uclar import guzergah

    u = FastAPI()
    u.include_router(guzergah.yonlendirici)
    return TestClient(u), jeton


ANTAKYA_A = {"basLon": 36.1610, "basLat": 36.2020}
ANTAKYA_B = {"hedefLon": 36.1700, "hedefLat": 36.2100}


def test_guzergah_yetki_ve_ag_disi(istemci):
    c, j = istemci
    g = {**ANTAKYA_A, **ANTAKYA_B}
    assert c.post("/api/guzergah", json=g).status_code == 401
    assert c.post("/api/guzergah", json=g, headers=j["afetzede"]).status_code == 403
    disari = {"basLon": 29.0, "basLat": 41.0, "hedefLon": 29.1, "hedefLat": 41.05}
    y = c.post("/api/guzergah", json=disari, headers=j["koordinator"])
    assert y.status_code == 422 and "yol ağımızın dışında" in y.json()["detail"]


@pytest.mark.skipif(not GERCEK_AG, reason="gercek yol agi bu makinede yok")
def test_guzergah_antakyada_rota_ve_en_yakin(istemci):
    c, j = istemci
    y = c.post("/api/guzergah", json={**ANTAKYA_A, **ANTAKYA_B}, headers=j["koordinator"])
    assert y.status_code == 200, y.text
    r = y.json()
    assert r["ag"] == "antakya" and r["mesafeM"] >= r["kusUcusuM"] and len(r["rota"]) > 2
    assert r["adimlar"] and r["sureDk"] >= 1
    y = c.post("/api/guzergah/en-yakin", json={**ANTAKYA_A, "tur": "hastane"}, headers=j["koordinator"])
    assert y.status_code == 200, y.text
    yerler = y.json()["yerler"]
    assert yerler and [x["sureDk"] for x in yerler] == sorted(x["sureDk"] for x in yerler)


def test_guzergah_hiz_siniri(istemci, monkeypatch):
    import hiz_siniri

    c, j = istemci
    monkeypatch.setattr(hiz_siniri, "ROTA_HESAP_SINIRI", 2)
    disari = {"basLon": 29.0, "basLat": 41.0, "hedefLon": 29.1, "hedefLat": 41.05}
    kodlar = [c.post("/api/guzergah", json=disari, headers=j["koordinator"]).status_code for _ in range(3)]
    assert kodlar[-1] == 429, kodlar
