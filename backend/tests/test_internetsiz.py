"""Internetsiz kip (internetsiz.py) ve karo onbellegi (karo_onbellegi.py)."""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


@pytest.fixture()
def ortam(monkeypatch):
    monkeypatch.setenv("QUAKEMIND_SQLITE", str(Path(tempfile.mkdtemp(prefix="qm_inetsiz_")) / "t.sqlite3"))
    monkeypatch.setenv("QUAKEMIND_KARO_ONBELLEK", tempfile.mkdtemp(prefix="qm_karo_"))
    monkeypatch.delenv("QUAKEMIND_INTERNETSIZ", raising=False)
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()

    def jeton(eposta, rol):
        k = kimlik.kullanici_kaydet(eposta, eposta, "test-sifresi-123")
        if rol != "afetzede":
            d.rol_ata(k["id"], rol)
        return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from uclar import genel, goruntu, yerler

    u = FastAPI()
    for m in (genel, goruntu, yerler):
        u.include_router(m.yonlendirici)
    yield TestClient(u), jeton
    depo_paketi._depo = None


class _Yanit:
    def __init__(self, govde=PNG, kod=200, tur="image/png"):
        self.content, self.status_code, self.headers = govde, kod, {"content-type": tur}


class _Istemci:
    def __init__(self):
        self.istekler = []

    def get(self, adres):
        self.istekler.append(adres)
        return _Yanit()


ESRI = {"kaynak": "esri", "surum": "12345"}


def test_karo_internetliyken_esri_saklanir_google_saklanmaz(ortam, monkeypatch):
    c, jeton = ortam
    from uclar import goruntu

    sahte = _Istemci()
    monkeypatch.setattr(goruntu, "_http", lambda: sahte)
    j = jeton("saha@i.local", "saha")
    for _ in range(2):
        assert c.get("/api/goruntu/karo/15/1/2", params=ESRI, headers=j).status_code == 200
        assert c.get("/api/goruntu/karo/15/1/2", params={"kaynak": "google"}, headers=j).status_code == 200
    # Esri ikinci kez agdan inmedi, Google iki kez indi.
    assert sum("arcgis" in a for a in sahte.istekler) == 1
    assert sum("google" in a for a in sahte.istekler) == 2


def test_internetsiz_kipte_karo_yalniz_onbellekten(ortam, monkeypatch):
    c, jeton = ortam
    from uclar import goruntu

    monkeypatch.setattr(goruntu, "_http", lambda: _Istemci())
    j = jeton("saha2@i.local", "saha")
    assert c.get("/api/goruntu/karo/15/1/2", params=ESRI, headers=j).status_code == 200

    def ag_yok():
        raise AssertionError("internetsiz kipte aga gidildi")

    monkeypatch.setattr(goruntu, "_http", ag_yok)
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    y = c.get("/api/goruntu/karo/15/1/2", params=ESRI, headers=j)
    assert y.status_code == 200 and y.headers["x-karo-onbellek"] == "evet" and y.content == PNG
    y = c.get("/api/goruntu/karo/15/9/9", params=ESRI, headers=j)
    assert y.status_code == 503 and "önbellekte yok" in y.json()["detail"]
    y = c.get("/api/goruntu/karo/15/1/2", params={"kaynak": "google"}, headers=j)
    assert y.status_code == 503 and "Google" in y.json()["detail"]


def test_internetsiz_kipte_osrm_beklemeden_503(ortam, monkeypatch):
    c, jeton = ortam
    import requests

    monkeypatch.setattr(requests, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("aga gidildi")))
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    j = jeton("afet@i.local", "afetzede")
    t = time.perf_counter()
    y = c.post("/api/afetzede/sokak-rotasi", json={"baslangicLat": 36.2, "baslangicLon": 36.16,
                                                   "hedefLat": 36.21, "hedefLon": 36.17}, headers=j)
    assert y.status_code == 503 and "İnternetsiz kip" in y.json()["detail"]
    assert time.perf_counter() - t < 1.0


def test_ozellik_matrisi_ucu(ortam, monkeypatch):
    c, jeton = ortam
    j = jeton("afet2@i.local", "afetzede")
    assert c.get("/api/internetsiz").status_code == 401
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    g = c.get("/api/internetsiz", headers=j).json()
    assert g["kip"] is True
    ozellikler = {o["ozellik"]: o for o in g["ozellikler"]}
    assert ozellikler["Uydu hasar analizi"]["internetsiz"] == "hayir"
    assert all(o["internetsiz"] in ("evet", "kismen", "hayir") for o in g["ozellikler"])
    # Dosya yolu donmez (yalniz var/yok ve sayi).
    assert str(BASE_DIR) not in str(g)


def test_eksik_yerel_dosya_ozelligi_hayir_yapar():
    import internetsiz

    y = internetsiz._yerel_dosyalar()
    y = {**y, "metinModeli": False}
    metin = next(o for o in internetsiz.matris(y) if o["ozellik"].startswith("Metin analizi"))
    assert metin["internetsiz"] == "hayir" and metin["yerelVeriHazir"] is False


def test_kipi_uygula_kitapliklari_kapatir(monkeypatch):
    import internetsiz

    for ad in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "QUAKEMIND_OFFLINE_ONLY"):
        monkeypatch.delenv(ad, raising=False)
    monkeypatch.delenv("QUAKEMIND_INTERNETSIZ", raising=False)
    assert internetsiz.kipi_uygula() is False and "HF_HUB_OFFLINE" not in os.environ
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    assert internetsiz.kipi_uygula() is True
    assert os.environ["HF_HUB_OFFLINE"] == "1" and os.environ["QUAKEMIND_OFFLINE_ONLY"] == "1"


def test_altlik_internetsiz_indirme_denemez(monkeypatch):
    from uclar import altlik

    monkeypatch.setattr(altlik, "hf_hub_download", lambda **k: (_ for _ in ()).throw(AssertionError("indirildi")))
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    assert altlik._indir("olmayan-bolge.json.gz") is None


def test_onbellek_siniri_en_eskiyi_siler(monkeypatch, tmp_path):
    import karo_onbellegi

    monkeypatch.setenv("QUAKEMIND_KARO_ONBELLEK", str(tmp_path))
    monkeypatch.setenv("QUAKEMIND_KARO_ONBELLEK_MB", "1")
    iri = b"x" * 600_000
    assert karo_onbellegi.yaz("oam", "https://a/1", iri, "image/png")
    eski = next(tmp_path.rglob("*.png"))
    os.utime(eski, (1, 1))
    assert karo_onbellegi.yaz("oam", "https://a/2", iri, "image/jpeg")
    assert karo_onbellegi.buda()["silinen"] == 1
    assert karo_onbellegi.oku("oam", "https://a/1") is None
    assert karo_onbellegi.oku("oam", "https://a/2") == (iri, "image/jpeg")
    # Saklanmayan kaynak ve sinir 0.
    assert karo_onbellegi.yaz("google", "https://g/1", iri, "image/png") is False
    monkeypatch.setenv("QUAKEMIND_KARO_ONBELLEK_MB", "0")
    assert karo_onbellegi.yaz("oam", "https://a/3", iri, "image/png") is False


def test_uydu_iscisi_internetsiz_kipte_acilmaz(monkeypatch):
    import internetsiz

    monkeypatch.delenv("QUAKEMIND_UYDU_ISCISI", raising=False)
    monkeypatch.delenv("QUAKEMIND_INTERNETSIZ", raising=False)
    assert internetsiz.uydu_iscisi_gerekli() is True
    monkeypatch.setenv("QUAKEMIND_INTERNETSIZ", "1")
    assert internetsiz.uydu_iscisi_gerekli() is False
    tatbikat = next(o for o in internetsiz.matris() if o["ozellik"] == "Tatbikat")
    assert tatbikat["internetsiz"] == "hayir"
    monkeypatch.setenv("QUAKEMIND_UYDU_ISCISI", "1")
    assert internetsiz.uydu_iscisi_gerekli() is True
