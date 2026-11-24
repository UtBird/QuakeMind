"""Yurume rotasinin kapanma ve hasar verisi (J-181).

Kucuk yapay yol agi ve ayri gecici SQLite; gercek veritabanina ve gercek yol
agina dokunulmaz."""
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

LAT0, LON0 = 36.2, 36.16
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0


def ll(x, y):
    """Yerel metre -> (lon, lat)."""
    return LON0 + x / KX, LAT0 + y / KY


def _ag(dizin: Path):
    """Dugumler: 0 (0,0), 1 (100,0), 2 (600,0), 3 (700,0).
    Kenar 0: 0-1 (yakin yol), kenar 1: 2-3 (uzak yol)."""
    import yol_agi

    xy = np.array([[0, 0], [100, 0], [600, 0], [700, 0]], dtype=float)
    lon = LON0 + xy[:, 0] / KX
    lat = LAT0 + xy[:, 1] / KY
    u = np.array([0, 2])
    v = np.array([1, 3])
    # Yonsuz: CSR'de iki yon; komsular sirali.
    komsu = {0: [(1, 0)], 1: [(0, 0)], 2: [(3, 1)], 3: [(2, 1)]}
    indptr, indices, kenar = [0], [], []
    for n in range(4):
        for m, k in sorted(komsu[n]):
            indices.append(m)
            kenar.append(k)
        indptr.append(len(indices))
    np.savez(
        dizin / "t.npz",
        dugum_lon=lon, dugum_lat=lat,
        indptr=np.array(indptr), indices=np.array(indices), kenar=np.array(kenar),
        kenar_u=u, kenar_v=v, kenar_uzunluk=np.array([100.0, 100.0]),
        kenar_yol=np.array([0, 1]), yol_adi=np.array(["A", "B"]), yol_tipi=np.array(["residential"] * 2),
    )
    return yol_agi.Ag({"id": "t", "kutu": [LON0 - 0.01, LAT0 - 0.01, LON0 + 0.02, LAT0 + 0.01]}, dizin)


def _ag_kur(dizin: Path, dugumler, kenarlar):
    """Yapay yonsuz ag: dugumler [(x, y) metre], kenarlar [(u, v)]."""
    import yol_agi

    xy = np.array(dugumler, dtype=float)
    komsu = {i: [] for i in range(len(xy))}
    for k, (a, b) in enumerate(kenarlar):
        komsu[a].append((b, k))
        komsu[b].append((a, k))
    indptr, indices, kenar = [0], [], []
    for n in range(len(xy)):
        for m, k in sorted(komsu[n]):
            indices.append(m)
            kenar.append(k)
        indptr.append(len(indices))
    uz = [float(np.hypot(*(xy[b] - xy[a]))) for a, b in kenarlar]
    np.savez(
        dizin / "j.npz",
        dugum_lon=LON0 + xy[:, 0] / KX, dugum_lat=LAT0 + xy[:, 1] / KY,
        indptr=np.array(indptr), indices=np.array(indices), kenar=np.array(kenar),
        kenar_u=np.array([a for a, _ in kenarlar]), kenar_v=np.array([b for _, b in kenarlar]),
        kenar_uzunluk=np.array(uz), kenar_yol=np.arange(len(kenarlar)),
        yol_adi=np.array([f"Y{i}" for i in range(len(kenarlar))]),
        yol_tipi=np.array(["residential"] * len(kenarlar)),
    )
    return yol_agi.Ag({"id": "j", "kutu": [LON0 - 0.01, LAT0 - 0.01, LON0 + 0.02, LAT0 + 0.01]}, dizin)


def test_kapanma_uzerinde_yattigi_kenari_kapatir(tmp_path):
    ag = _ag(tmp_path)
    # Cizgi (-80,0) -> (20,0): orta noktasi kenar 0'a 30 m uzak, ama cizginin
    # 20 m'si kenarin ustunde. Kenar kapanir (J-181: orta nokta yetmiyordu).
    _c, kapali = ag.carpanlar(("a",), [(ll(-80, 0), ll(20, 0))], [])
    assert kapali.tolist() == [True, False]

    # Tek noktali (cizgisiz) kapanma en yakin kenara oturur.
    _c, kapali = ag.carpanlar(("b",), [(ll(650, 5),)], [])
    assert kapali.tolist() == [False, True]

    # Uzak cizgi hicbir kenari kapatmaz.
    _c, kapali = ag.carpanlar(("c",), [(ll(300, -200), ll(320, -200))], [])
    assert not kapali.any()


def test_dik_kapanma_kestigi_yolu_kapatmaz(tmp_path):
    """Baska bir sokaktaki kapanmanin ucu bu yola 1 m yaklasir: yalniz iki ornek
    nokta yakin; yol kapanmaz. Eski 25 m kurali kapatiyordu."""
    ag = _ag(tmp_path)
    _c, kapali = ag.carpanlar(("d",), [(ll(50, -60), ll(50, -1))], [])
    assert not kapali.any()


def test_kavsaktaki_kapanma_yan_sokaklari_kapatmaz(tmp_path):
    """Kavsak (100,0): bati (kenar 0), dogu (kenar 1), kuzey (kenar 2). Kuzey
    sokaktaki kapanma kavsaga kadar uzanir; yalniz kuzey sokak kapanir.
    Eskiden 25 m cevresindeki butun kenarlar kapaniyor, kavsak tumden
    tikaniyor ve rota "baska yol yok" diye kapanmadan geciyordu."""
    ag = _ag_kur(tmp_path, [(0, 0), (100, 0), (200, 0), (100, 100)], [(0, 1), (1, 2), (1, 3)])
    _c, kapali = ag.carpanlar(("e",), [(ll(100, 2), ll(100, 60))], [])
    assert kapali.tolist() == [False, False, True]


def test_kapanma_carpani_arac_icin_buyutulebilir(tmp_path):
    ag = _ag(tmp_path)
    cizgi = (ll(20, 0), ll(80, 0))
    c, kapali = ag.carpanlar(("f",), [cizgi], [], kapanma_carpani=1e6)
    assert kapali.tolist() == [True, False] and c[0] == 1e6 and c[1] == 1.0
    # Yaya varsayilani degismedi.
    c, _k = ag.carpanlar(("g",), [cizgi], [])
    assert c[0] == 20.0

@pytest.fixture()
def depo(tmp_path):
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_rota_")) / "t.sqlite3")
    import depo as depo_paketi
    import yol_agi

    depo_paketi._depo = None
    yol_agi._tehlike.clear()
    return depo_paketi.depo_ac()


KUTU = (LON0 - 0.01, LAT0 - 0.01, LON0 + 0.02, LAT0 + 0.01)


def test_hasar_verisi_suzme_tekrar_ve_onbellek(depo, monkeypatch):
    import yol_agi

    simdi = time.time()
    cizgi = [[LAT0, LON0], [LAT0 + 0.0002, LON0]]
    for z in (simdi - 10, simdi):  # ayni parca iki analizde
        depo.kapanma_ekle(lon=LON0, lat=LAT0 + 0.0001, derece=3, kaynak="uydu", zaman=z, cizgi=cizgi)
    depo.kapanma_ekle(lon=LON0 + 0.005, lat=LAT0, derece=3, kaynak="uydu", zaman=simdi)
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=0.9, guven=1, kaynak="kamera", etiket=None, zaman=simdi)
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=0.3, guven=1, kaynak="uydu", etiket=None, zaman=simdi)  # zayif
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=0.9, guven=1, kaynak="uydu", etiket=None, zaman=simdi)
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=1.0, guven=1, kaynak="sos", etiket=None, zaman=simdi)  # SOS
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=0.8, guven=1, kaynak="metin", etiket="Enkaz Bildirimi", zaman=simdi)
    depo.hasar_ekle(lon=LON0, lat=LAT0, skor=0.8, guven=1, kaynak="metin", etiket="Su", zaman=simdi)

    imza, kapanmalar, hasarlar, son = yol_agi.hasar_verisi(KUTU)
    assert len(kapanmalar) == 2  # tekrar bir kez
    cizgili = [k for k in kapanmalar if len(k) == 2]
    assert len(cizgili) == 1 and cizgili[0][0] == (LON0, LAT0)  # [enlem, boylam] -> (lon, lat)
    assert len(hasarlar) == 3  # kamera, guclu uydu, enkaz metni
    assert son == pytest.approx(simdi)

    # Veri degismedikce satirlar yeniden okunmaz.
    cagri = []
    asil = depo.rota_tehlike_noktalari
    monkeypatch.setattr(depo, "rota_tehlike_noktalari", lambda k: cagri.append(k) or asil(k))
    assert yol_agi.hasar_verisi(KUTU)[0] == imza
    assert cagri == []

    # Yeni kapanma imzayi degistirir, satirlar yeniden okunur.
    depo.kapanma_ekle(lon=LON0 + 0.008, lat=LAT0, derece=3, kaynak="uydu", zaman=simdi + 1)
    imza2, kapanmalar2, _h, _s = yol_agi.hasar_verisi(KUTU)
    assert imza2 != imza and len(cagri) == 1 and len(kapanmalar2) == 3


def test_imza_sorgusu_indeks_kullanir(depo):
    """Imza her rota isteginde sorulur; tablo taranmamali (CLAUDE.md 10)."""
    for tablo in ("yol_kapanmalari", "hasar_noktalari"):
        plan = depo._oku(
            f"EXPLAIN QUERY PLAN SELECT COUNT(*), MAX(zaman) FROM {tablo}"
            " WHERE lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?",
            (36.0, 36.3, 36.1, 36.3),
        )
        metin = " ".join(str(dict(p)) for p in plan)
        assert "INDEX" in metin, (tablo, metin)


def test_rotadaki_kapanmalar():
    import yol_agi

    rota = [ll(0, 0), ll(200, 0)]
    yakin = (ll(100, -60), ll(100, -15))  # ucu 15 m
    uzak = (ll(100, 60), ll(100, 30))  # en yakin 30 m
    tek = (ll(150, 5),)
    assert yol_agi.rotadaki_kapanmalar(rota, [yakin, uzak, tek]) == [0, 2]
    assert yol_agi.rotadaki_kapanmalar(rota, []) == []


def _osrm_rota(noktalar_m, uzunluk):
    return {"geometry": {"coordinates": [list(ll(x, y)) for x, y in noktalar_m]}, "distance": uzunluk}


@pytest.fixture()
def sokak(depo, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import kimlik
    from uclar import yerler

    k = kimlik.kullanici_kaydet("afz@rota.local", "afz", "test-sifresi-123")
    jeton = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(depo.kullanici_id(k['id']))}"}
    cagrilar = []

    def sahte(noktalar, alternatif):
        cagrilar.append((len(noktalar), alternatif))
        return sahte.yanit(noktalar, alternatif)

    monkeypatch.setattr(yerler, "_osrm", sahte)
    u = FastAPI()
    u.include_router(yerler.yonlendirici)
    istek = dict(zip(("baslangicLon", "baslangicLat"), ll(0, 0))) | dict(zip(("hedefLon", "hedefLat"), ll(400, 0)))
    return TestClient(u), jeton, sahte, cagrilar, istek


def test_sokak_rotasi_kapanmadan_kacinir(depo, sokak):
    c, j, sahte, cagrilar, istek = sokak
    # Kapanma duz yolun ortasinda (200, 0).
    depo.kapanma_ekle(lon=ll(200, 0)[0], lat=ll(200, 0)[1], derece=3, kaynak="uydu",
                      cizgi=[[ll(190, 0)[1], ll(190, 0)[0]], [ll(210, 0)[1], ll(210, 0)[0]]])
    duz = _osrm_rota([(0, 0), (400, 0)], 400)
    dolasan = _osrm_rota([(0, 0), (200, 150), (400, 0)], 500)
    # Ilk istek yalniz kapanmadan gecen rotayi verir; sapma istegi dolasani.
    sahte.yanit = lambda n, alt: [duz] if len(n) == 2 else [dolasan]
    g = c.post("/api/afetzede/sokak-rotasi", json=istek, headers=j).json()
    assert g["kapanma"]["rotada"] == 0 and g["kapanma"]["sapmaDenendi"] is True
    assert g["uzunlukM"] == 500 and "geçmeyen" in g["uyari"]
    assert cagrilar[0] == (2, True) and cagrilar[1] == (3, False) and len(cagrilar) == 2  # temiz bulununca durur


def test_sokak_rotasi_baska_yol_yoksa_soyler(depo, sokak):
    c, j, sahte, cagrilar, istek = sokak
    depo.kapanma_ekle(lon=ll(200, 0)[0], lat=ll(200, 0)[1], derece=3, kaynak="uydu")
    duz = _osrm_rota([(0, 0), (400, 0)], 400)
    sahte.yanit = lambda n, alt: [duz]
    g = c.post("/api/afetzede/sokak-rotasi", json=istek, headers=j).json()
    assert g["kapanma"]["rotada"] == 1 and "Dikkat" in g["uyari"]
    assert len(cagrilar) == 3  # 1 + iki yandan sapma


def test_sokak_rotasi_kapanma_yoksa_tek_istek(depo, sokak):
    c, j, sahte, cagrilar, istek = sokak
    sahte.yanit = lambda n, alt: [_osrm_rota([(0, 0), (400, 0)], 400)]
    g = c.post("/api/afetzede/sokak-rotasi", json=istek, headers=j).json()
    assert g["kapanma"]["cevrede"] == 0 and len(cagrilar) == 1
    sahte.yanit = lambda n, alt: []
    assert c.post("/api/afetzede/sokak-rotasi", json=istek, headers=j).status_code == 503
