"""Tatbikati bitirme ve sahipsiz tatbikat noktalari (J-186). Ayri gecici SQLite."""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture()
def ortam():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_tatbikat_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    k = kimlik.kullanici_kaydet("k@tatbikat.local", "Koordinator", "test-sifresi-123")
    d.rol_ata(k["id"], "koordinator")
    jeton = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from uclar import simulasyon

    u = FastAPI()
    u.include_router(simulasyon.yonlendirici)
    return d, TestClient(u), jeton


def _sayi(d):
    return d._tek("SELECT COUNT(*) AS n FROM hasar_noktalari")["n"]


def _nokta(d, ek):
    d.hasar_ekle(lon=36.15, lat=36.2, skor=0.9, guven=0.9, kaynak="uydu", etiket=None, zaman=time.time(), ek=ek)


def test_sunucu_kosuyu_tanimasa_da_noktalar_silinir(ortam):
    d, c, j = ortam
    _nokta(d, {"analizId": "sim_aaaaaaaaaaaa", "tatbikat": "sim_aaaaaaaaaaaa"})
    _nokta(d, {"analizId": "sim_bbbbbbbbbbbb", "tatbikat": "sim_bbbbbbbbbbbb"})
    _nokta(d, {"analizId": "gercek-analiz"})
    # Sunucu yeniden basladi: kosu bellekte yok. Eskiden 404, noktalar kaliyordu.
    y = c.post("/api/simulasyon/bitir", json={"isId": "sim_aaaaaaaaaaaa"}, headers=j)
    assert y.status_code == 200, y.text
    assert y.json()["silinenHasarNoktasi"] == 1
    assert _sayi(d) == 2


def test_gecersiz_kimlik_reddedilir(ortam):
    d, c, j = ortam
    _nokta(d, {"tatbikat": "sim_aaaaaaaaaaaa"})
    for kimlik_ in ("%", "sim_%", "", "baska"):
        assert c.post("/api/simulasyon/bitir", json={"isId": kimlik_}, headers=j).status_code == 422
    assert _sayi(d) == 1


def test_acilista_sahipsiz_tatbikat_noktalari_silinir(ortam):
    d, _c, _j = ortam
    _nokta(d, {"tatbikat": "sim_aaaaaaaaaaaa"})
    _nokta(d, {"tatbikat": "sim_cccccccccccc_kontrol"})
    _nokta(d, {"analizId": "gercek-analiz"})
    assert d.hasar_sil_tatbikat_hepsi() == 2
    assert _sayi(d) == 1
    assert d.hasar_sil_tatbikat_hepsi() == 0
