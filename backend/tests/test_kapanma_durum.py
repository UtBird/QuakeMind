"""Yol kapanmasının durumu: kapalı · açıldı · yanlış alarm. Ayrı geçici SQLite."""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

LAT, LON = 36.2, 36.16
CIZGI = [[LAT, LON], [LAT + 0.0002, LON]]


@pytest.fixture()
def ortam():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_kapanma_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik
    import yol_agi

    depo_paketi._depo = None
    yol_agi._tehlike.clear()
    d = depo_paketi.depo_ac()

    def jeton(eposta, rol):
        k = kimlik.kullanici_kaydet(eposta, eposta, "test-sifresi-123")
        if rol != "afetzede":
            d.rol_ata(k["id"], rol)
        return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from uclar import kapanma_durum, katmanlar

    u = FastAPI()
    u.include_router(kapanma_durum.yonlendirici)
    u.include_router(katmanlar.yonlendirici)
    simdi = time.time()
    # Ayni parca iki analizde + baska bir parca, ayni analizde.
    a = d.kapanma_ekle(lon=LON, lat=LAT + 0.0001, derece=3, kaynak="uydu", analiz_id="analiz-1", zaman=simdi - 10, cizgi=CIZGI)
    d.kapanma_ekle(lon=LON, lat=LAT + 0.0001, derece=3, kaynak="uydu", analiz_id="analiz-2", zaman=simdi, cizgi=CIZGI)
    d.kapanma_ekle(lon=LON + 0.003, lat=LAT, derece=3, kaynak="uydu", analiz_id="analiz-1", zaman=simdi)
    return d, TestClient(u), jeton, a["id"]


def _katman(c, j, tumu=False):
    return c.get("/api/katman/kapanmalar", params={"tumu": "true"} if tumu else None, headers=j).json()


def test_acildi_isaretlenen_parca_rotadan_ve_haritadan_duser(ortam):
    d, c, jeton, kid = ortam
    import yol_agi

    saha = jeton("saha@k.local", "saha")
    kutu = (LON - 0.01, LAT - 0.01, LON + 0.01, LAT + 0.01)
    imza_once, kap_once, _h, _s = yol_agi.hasar_verisi(kutu)
    assert len(kap_once) == 2 and _katman(c, saha)["sayi"] == 3

    y = c.patch(f"/api/kapanmalar/{kid}", json={"durum": "acildi", "not": "ekip gecti"}, headers=saha)
    assert y.status_code == 200, y.text
    assert y.json()["degisenKayit"] == 2  # ayni parcanin iki kaydi birlikte

    imza_sonra, kap_sonra, _h, _s = yol_agi.hasar_verisi(kutu)
    assert imza_sonra != imza_once and len(kap_sonra) == 1  # rota motoru yeniden okur
    assert _katman(c, saha)["sayi"] == 1  # harita yalniz kapali olani cizer
    hepsi = _katman(c, saha, tumu=True)["kayitlar"]
    acik = [k for k in hepsi if k["durum"] == "acildi"]
    assert len(acik) == 2 and acik[0]["durumNotu"] == "ekip gecti" and acik[0]["durumZaman"]
    assert d.kapanma_sayisi() == 1

    # Geri alinabilir.
    assert c.patch(f"/api/kapanmalar/{kid}", json={"durum": "kapali"}, headers=saha).status_code == 200
    assert _katman(c, saha)["sayi"] == 3


def test_yetki_ve_gecersiz_istekler(ortam):
    _d, c, jeton, kid = ortam
    afetzede = jeton("afz@k.local", "afetzede")
    saha = jeton("saha2@k.local", "saha")
    assert c.patch(f"/api/kapanmalar/{kid}", json={"durum": "acildi"}, headers=afetzede).status_code == 403
    assert c.patch(f"/api/kapanmalar/{kid}", json={"durum": "acildi"}).status_code == 401
    assert c.patch(f"/api/kapanmalar/{kid}", json={"durum": "silindi"}, headers=saha).status_code == 422
    assert c.patch("/api/kapanmalar/kap-%25", json={"durum": "acildi"}, headers=saha).status_code == 422
    assert c.patch("/api/kapanmalar/kap-0000000000000000", json={"durum": "acildi"}, headers=saha).status_code == 404
    # Toplu degisiklik yalniz koordinasyon.
    assert c.post("/api/kapanmalar/analiz/analiz-1/durum", json={"durum": "yanlis"}, headers=saha).status_code == 403


def test_analizin_butun_kapanmalari_yanlis_alarm(ortam):
    d, c, jeton, _kid = ortam
    koord = jeton("k@k.local", "koordinator")
    y = c.post("/api/kapanmalar/analiz/analiz-1/durum", json={"durum": "yanlis"}, headers=koord)
    assert y.status_code == 200 and y.json()["degisenKayit"] == 2
    # analiz-2'nin kaydi kapali kalir (ayni parca olsa da ayri kanit).
    kalan = _katman(c, koord)["kayitlar"]
    assert [k["analizId"] for k in kalan] == ["analiz-2"]
    assert c.post("/api/kapanmalar/analiz/yok-boyle/durum", json={"durum": "yanlis"}, headers=koord).status_code == 404
    kayit = d._oku("SELECT tur, ayrinti FROM islem_kayitlari WHERE tur = 'kapanma_durumu'")
    assert kayit and "yanlis" in kayit[-1]["ayrinti"]
