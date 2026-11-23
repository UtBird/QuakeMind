"""Ortak ornek hesaplar (J-183). Ayri gecici SQLite."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

SIFRE = "ortak-ornek-sifre-2026"


@pytest.fixture()
def ortam(monkeypatch):
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_ornek_")) / "t.sqlite3")
    import depo as depo_paketi

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import ornek_hesaplar
    from uclar import oturum

    u = FastAPI()
    u.include_router(oturum.yonlendirici)
    return d, ornek_hesaplar, TestClient(u), monkeypatch


def _giris(c, eposta, sifre):
    return c.post("/api/oturum/giris", json={"eposta": eposta, "sifre": sifre})


def test_degisken_yoksa_ya_da_zayifsa_kurulmaz(ortam):
    d, o, _c, mp = ortam
    mp.delenv(o.ORTAM_DEGISKENI, raising=False)
    o.acilista_kur(d)
    assert d.kullanici_sayisi() == 0
    for zayif in ("kisa", o.YEREL_DEMO_SIFRESI):
        mp.setenv(o.ORTAM_DEGISKENI, zayif)
        o.acilista_kur(d)
        assert d.kullanici_sayisi() == 0


def test_her_rol_kurulur_girilir_sifre_degismez(ortam):
    d, o, c, mp = ortam
    mp.setenv(o.ORTAM_DEGISKENI, SIFRE)
    o.acilista_kur(d)
    o.acilista_kur(d)  # ikinci acilis: tekrar acmaz, sifreye dokunmaz
    assert d.kullanici_sayisi() == 4
    for eposta, _ad, rol, _kapi in o.HESAPLAR:
        g = _giris(c, eposta, SIFRE)
        assert g.status_code == 200, (eposta, g.text)
        k = g.json()["kullanici"]
        assert k["rol"] == rol and k["ortakHesap"] is True and k["sifreDegismeli"] is False
        if rol == "saha":
            assert k["ekipId"]
    kayitlar = [r for r in d.hesap_kayitlari(None, 100) if r["islem"] == "sifre-yenilendi"]
    assert kayitlar == []  # sifre zaten ayniydi

    # Ortak hesabin sifresi uygulamadan degismez.
    j = {"Authorization": f"Bearer {_giris(c, 'demo@quakemind.local', SIFRE).json()['erisimJetonu']}"}
    s = c.post("/api/oturum/sifre", json={"eskiSifre": SIFRE, "yeniSifre": "baska-sifre-123"}, headers=j)
    assert s.status_code == 403 and "ortak" in s.json()["detail"]
    # Yonetici de konsoldan sifirlayamaz.
    jy = {"Authorization": f"Bearer {_giris(c, 'yonetici-demo@quakemind.local', SIFRE).json()['erisimJetonu']}"}
    hedef = d.kullanici_eposta("demo@quakemind.local")
    assert c.post(f"/api/oturum/kullanicilar/{hedef['id']}/sifre", headers=jy).status_code == 409
    liste = c.get("/api/oturum/kullanicilar", headers=jy).json()["kullanicilar"]
    assert all(k["ortakHesap"] for k in liste)

    # Sifre ortam degiskeninden degisir.
    mp.setenv(o.ORTAM_DEGISKENI, SIFRE + "-yeni")
    o.acilista_kur(d)
    assert _giris(c, "demo@quakemind.local", SIFRE).status_code == 401
    assert _giris(c, "demo@quakemind.local", SIFRE + "-yeni").status_code == 200
