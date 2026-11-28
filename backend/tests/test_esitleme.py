"""Saha sunucusu <-> merkez esitlemesi (esitleme.py). Iki ayri gecici SQLite:
biri merkez (uclar uzerinden), biri dugum (Esitleyici, istemcisi TestClient)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

ANAHTAR_A = "a" * 32
ANAHTAR_B = "b" * 32
LAT, LON = 36.2, 36.16


def _gecici(ad):
    return str(Path(tempfile.mkdtemp(prefix=f"qm_esit_{ad}_")) / "t.sqlite3")


@pytest.fixture()
def ortam(monkeypatch):
    monkeypatch.setenv("QUAKEMIND_SQLITE", _gecici("merkez"))
    monkeypatch.setenv("QUAKEMIND_ESITLEME_DUGUMLERI", f"antakya-1:{ANAHTAR_A},maras-1:{ANAHTAR_B}")
    monkeypatch.delenv("QUAKEMIND_MERKEZ_URL", raising=False)
    import depo as depo_paketi
    from depo import SqliteDepo

    import esitleme

    depo_paketi._depo = None
    merkez = depo_paketi.depo_ac()
    merkez.esitleme_kur("merkez")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from uclar import esitleme as esitleme_uclari

    u = FastAPI()
    u.include_router(esitleme_uclari.yonlendirici)
    istemci = TestClient(u)

    def dugum(ad, anahtar):
        d = SqliteDepo(_gecici(ad))
        d.esitleme_kur("dugum")
        e = esitleme.Esitleyici(d, {"url": "http://merkez", "ad": ad, "anahtar": anahtar, "aralik": 30.0}, istemci=istemci)
        return d, e

    yield merkez, istemci, dugum
    depo_paketi._depo = None


def test_yukari_gercek_kayitlar_gider_tatbikat_gitmez(ortam):
    merkez, _, dugum = ortam
    d, e = dugum("antakya-1", ANAHTAR_A)
    h = d.hasar_ekle(lon=LON, lat=LAT, skor=0.8, guven=0.9, kaynak="kamera")
    d.hasar_ekle(lon=LON, lat=LAT, skor=0.8, guven=0.9, kaynak="uydu", ek={"tatbikat": "sim_1"})
    d.kapanma_ekle(lon=LON, lat=LAT, derece=3, kaynak="uydu", analiz_id="analiz-1")
    d.kapanma_ekle(lon=LON, lat=LAT, derece=3, kaynak="uydu", analiz_id="sim_1")
    s = d.sos_ekle(lon=LON, lat=LAT, oncelik="yuksek", metin="enkaz altindayiz")
    i = d.ihbar_ekle(tur="metin", lon=LON, lat=LAT, metin="yol kapali", kullanici_id="k-1",
                    istemci_anahtari="gizli-anahtar", istek_ozeti="ozet")

    assert d.degisim_bekleyen_sayisi() == 4
    assert e.tur() == {"basarili": True, "gonderilen": 4, "alinan": 0}
    assert d.degisim_bekleyen_sayisi() == 0

    gelen = {(g["tablo"], g["satir_id"]): g for g in merkez.gelen_listele("antakya-1", None)}
    assert len(gelen) == 4
    assert {("hasar_noktalari", h["id"]), ("sos_cagrilari", s["id"]), ("ihbarlar", i["id"])} <= set(gelen)
    assert sorted(t for t, _ in gelen) == ["hasar_noktalari", "ihbarlar", "sos_cagrilari", "yol_kapanmalari"]
    # Yerel tekrar-istek anahtari merkeze gitmez.
    assert "istemci_anahtari" not in gelen[("ihbarlar", i["id"])]["veri"]
    # Hasar ve kapanma merkezin kendi tablosunda kokeniyle; SOS ve ihbar yalniz ham kayitta.
    assert merkez._tek("SELECT id FROM hasar_noktalari WHERE id = ?", (f"antakya-1~{h['id']}",))
    assert merkez._tek("SELECT COUNT(*) AS n FROM yol_kapanmalari")["n"] == 1
    assert merkez._tek("SELECT COUNT(*) AS n FROM sos_cagrilari")["n"] == 0


def test_degisen_satir_yeniden_gider_eski_surum_yeniyi_ezmez(ortam):
    merkez, _, dugum = ortam
    d, e = dugum("antakya-1", ANAHTAR_A)
    s = d.sos_ekle(lon=LON, lat=LAT, oncelik="yuksek")
    e.tur()
    d.sos_kapat(s["id"])
    assert d.degisim_bekleyen_sayisi() == 1
    e.tur()
    [g] = merkez.gelen_listele("antakya-1", "sos_cagrilari")
    assert g["veri"]["durum"] == "kapandi"
    # Ayni satirin eski surumu sonradan gelirse yok sayilir.
    eski = {**g["veri"], "durum": "bekliyor"}
    merkez.gelen_kaydet("antakya-1", [{"sira": 1, "tablo": "sos_cagrilari", "veri": eski}])
    [g] = merkez.gelen_listele("antakya-1", "sos_cagrilari")
    assert g["veri"]["durum"] == "kapandi"


def test_asagi_merkez_kapanmasi_dugume_gelir_geri_gonderilmez(ortam):
    merkez, _, dugum = ortam
    a, ea = dugum("antakya-1", ANAHTAR_A)
    b, eb = dugum("maras-1", ANAHTAR_B)
    k = merkez.kapanma_ekle(lon=LON, lat=LAT, derece=3, kaynak="uydu", analiz_id="analiz-m")
    merkez.hasar_ekle(lon=LON, lat=LAT, skor=0.9, guven=0.9, kaynak="uydu", ek={"tatbikat": "sim_9"})
    ha = a.hasar_ekle(lon=LON, lat=LAT, skor=0.7, guven=0.8, kaynak="kamera")

    assert ea.tur()["basarili"]
    # A merkezin kapanmasini aldi; kendi gonderdigi hasar geri gelmedi; tatbikat gelmedi.
    kimlikler = {r["id"] for r in a._oku("SELECT id FROM yol_kapanmalari UNION ALL SELECT id FROM hasar_noktalari")}
    assert kimlikler == {f"merkez~{k['id']}", ha["id"]}
    # Gelen satir dugumun gunlugune girmez: geri gonderilmez.
    assert a.degisim_bekleyen_sayisi() == 0

    # B, A'nin hasarini merkez uzerinden alir.
    assert eb.tur()["alinan"] == 2
    assert b._tek("SELECT id FROM hasar_noktalari WHERE id = ?", (f"antakya-1~{ha['id']}",))

    # Merkezde kapanma "acildi" olunca dugume de iner (imlecten devam).
    merkez.kapanma_durum_yaz(k["id"], "acildi", "koordinator", None)
    assert ea.tur()["alinan"] == 1
    assert a._tek("SELECT durum FROM yol_kapanmalari WHERE id = ?", (f"merkez~{k['id']}",))["durum"] == "acildi"


def test_esitleme_sonradan_acilinca_eski_kayitlar_bir_kez_gunluge_girer(ortam):
    from depo import SqliteDepo

    d = SqliteDepo(_gecici("geç"))
    d.sos_ekle(lon=LON, lat=LAT, oncelik="orta")
    d.hasar_ekle(lon=LON, lat=LAT, skor=0.5, guven=0.5, kaynak="metin")
    assert d.esitleme_kur("dugum")["doldurulan"] == 2
    assert d.esitleme_kur("dugum")["doldurulan"] == 0
    assert d.degisim_bekleyen_sayisi() == 2
    # Rol kapatilinca tetikleyici kalkar: yeni kayit gunluge girmez.
    d.esitleme_kur(None)
    d.sos_ekle(lon=LON, lat=LAT, oncelik="orta")
    assert d.degisim_bekleyen_sayisi() == 2


def test_anahtar_ve_rol_denetimi(ortam, monkeypatch):
    _, istemci, _ = ortam
    govde = {"kayitlar": []}
    assert istemci.post("/api/esitleme/al", json=govde).status_code == 401
    assert istemci.post("/api/esitleme/al", json=govde, headers={"Authorization": "Bearer yanlis"}).status_code == 401
    assert istemci.post("/api/esitleme/al", json=govde, headers={"Authorization": f"Bearer {ANAHTAR_A}"}).status_code == 200
    # Merkez olmayan sunucu bu uclari hic acmaz.
    monkeypatch.delenv("QUAKEMIND_ESITLEME_DUGUMLERI")
    assert istemci.get("/api/esitleme/ver", headers={"Authorization": f"Bearer {ANAHTAR_A}"}).status_code == 404


def test_kimligi_bozuk_kayit_reddedilir(ortam):
    merkez, _, _ = ortam
    sonuc = merkez.gelen_kaydet("antakya-1", [
        {"sira": 1, "tablo": "kullanicilar", "veri": {"id": "x"}},
        {"sira": 2, "tablo": "hasar_noktalari", "veri": {"id": "merkez~hsr-1"}},
        {"sira": 3, "tablo": "hasar_noktalari", "veri": {}},
    ])
    assert sonuc == {"alinan": [], "reddedilen": 3}


def test_baglanti_yoksa_bekleme_katlanir_kayit_kaybolmaz(ortam):
    import esitleme

    class Kopuk:
        def post(self, *a, **k):
            raise ConnectionError("ağ yok")

        get = post

    from depo import SqliteDepo

    d = SqliteDepo(_gecici("kopuk"))
    d.esitleme_kur("dugum")
    d.sos_ekle(lon=LON, lat=LAT, oncelik="yuksek")
    e = esitleme.Esitleyici(d, {"url": "http://merkez", "ad": "x", "anahtar": ANAHTAR_A, "aralik": 30.0}, istemci=Kopuk())
    assert e.tur()["basarili"] is False
    assert e.durum()["sonrakiDenemeSn"] == 60.0
    assert d.degisim_bekleyen_sayisi() == 1


def test_ayar_hatalari(monkeypatch):
    import esitleme

    monkeypatch.setenv("QUAKEMIND_MERKEZ_URL", "http://m")
    monkeypatch.setenv("QUAKEMIND_ESITLEME_DUGUMLERI", f"a:{ANAHTAR_A}")
    with pytest.raises(esitleme.AyarHatasi):
        esitleme.rol()
    monkeypatch.delenv("QUAKEMIND_MERKEZ_URL")
    monkeypatch.setenv("QUAKEMIND_ESITLEME_DUGUMLERI", "a:kisa")
    with pytest.raises(esitleme.AyarHatasi):
        esitleme.dugumler()
