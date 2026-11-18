"""Harita katmanları ve görüntü önbelleği (J-172)."""
import io
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# --- sağlık katmanı -----------------------------------------------------------

@pytest.fixture(scope="module")
def istemci():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_hk_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    jeton = {}
    for ad, rol in [("koordinator", "koordinator"), ("afetzede", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@hk.local", ad, "test-sifresi-123")
        d.rol_ata(k["id"], rol)
        jeton[ad] = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}
    from uclar import katmanlar

    u = FastAPI()
    u.include_router(katmanlar.yonlendirici)
    return TestClient(u), jeton


def test_saglik_katmani(istemci, monkeypatch):
    from uclar import yerler

    c, j = istemci
    sahte = ({"kaynak": {"dosyaTarihi": "2026-08-12"}, "yerler": [
        {"tur": "hastane", "ad": "Devlet Hastanesi", "lon": 36.16, "lat": 36.20, "osm": "way/1"},
        {"tur": "saglik", "ad": "ASM", "lon": 36.17, "lat": 36.21, "osm": "node/2"},
        {"tur": "eczane", "ad": "Eczane", "lon": 36.16, "lat": 36.20, "osm": "node/3"},
        {"tur": "hastane", "ad": "Uzak", "lon": 30.0, "lat": 40.0, "osm": "way/4"},
    ]}, None, None)
    monkeypatch.setattr(yerler, "_hizmetler", lambda: sahte)
    assert c.get("/api/katman/saglik").status_code == 401
    assert c.get("/api/katman/saglik", headers=j["afetzede"]).status_code == 403
    y = c.get("/api/katman/saglik", params={"kutu": "36.0,36.0,36.5,36.5"}, headers=j["koordinator"])
    assert y.status_code == 200, y.text
    g = y.json()
    assert {k["ad"] for k in g["kayitlar"]} == {"Devlet Hastanesi", "ASM"}  # eczane ve kutu dışı yok
    assert "acik oldugunu" in g["kaynak"]["not"]


# --- görüntü önbelleği -------------------------------------------------------------

class _Yanit:
    def __init__(self, kod, icerik=b""):
        self.status_code = kod
        self.content = icerik


def _karo():
    b = io.BytesIO()
    Image.new("RGB", (256, 256), (90, 120, 60)).save(b, format="PNG")
    return b.getvalue()


@pytest.fixture()
def fetcher(monkeypatch, tmp_path):
    from apps.road_damage.utils import fetcher as f

    monkeypatch.setattr(f, "GORUNTU_ONBELLEGI", tmp_path / "onbellek")
    sayac = {"n": 0}
    karo = _karo()

    def get(url, headers=None, timeout=None):
        sayac["n"] += 1
        return _Yanit(200, karo)

    monkeypatch.setattr(f.requests, "get", get)
    return f, sayac


BBOX = (36.1466, 36.1955, 36.1522, 36.2000)


def test_acik_lisansli_goruntu_diskten_gelir(fetcher):
    f, sayac = fetcher
    img1, b1 = f.fetch_satellite_area(36.19, 36.14, bbox=BBOX, zoom_level=17, provider="custom",
                                      custom_url="https://ornek/{z}/{x}/{y}")
    ilk = sayac["n"]
    img2, b2 = f.fetch_satellite_area(36.19, 36.14, bbox=BBOX, zoom_level=17, provider="custom",
                                      custom_url="https://ornek/{z}/{x}/{y}")
    assert ilk > 0 and sayac["n"] == ilk  # ikinci kez ağa gidilmedi
    assert img1.size == img2.size and b1 == b2


def test_google_karosu_saklanmaz(fetcher):
    f, sayac = fetcher
    f.fetch_satellite_area(36.19, 36.14, bbox=BBOX, zoom_level=17, provider="google")
    ilk = sayac["n"]
    f.fetch_satellite_area(36.19, 36.14, bbox=BBOX, zoom_level=17, provider="google")
    assert sayac["n"] == 2 * ilk
    assert not f.GORUNTU_ONBELLEGI.exists() or not list(f.GORUNTU_ONBELLEGI.glob("*.png"))


def test_eksik_inen_goruntu_saklanmaz(fetcher, monkeypatch):
    """Gecici hatayla inmeyen karo varsa goruntu saklanmaz (siyah blok, J-89)."""
    f, _sayac = fetcher
    karo = _karo()
    durum = {"n": 0}

    def bir_karo_hep_duser(url, headers=None, timeout=None):
        durum["n"] += 1
        # Ilk karonun bütün denemeleri düşer, ötekiler iner.
        if durum["n"] <= 3:
            raise ConnectionError("gecici")
        return _Yanit(200, karo)

    monkeypatch.setattr(f.requests, "get", bir_karo_hep_duser)
    monkeypatch.setattr(f.time, "sleep", lambda s: None)
    img, _ = f.fetch_satellite_area(36.19, 36.14, bbox=BBOX, zoom_level=17, provider="custom",
                                    custom_url="https://baska/{z}/{x}/{y}")
    assert img is not None  # goruntu yine doner (eksik karo siyah)...
    assert not f.GORUNTU_ONBELLEGI.exists() or not list(f.GORUNTU_ONBELLEGI.glob("*.png"))  # ...ama saklanmaz
