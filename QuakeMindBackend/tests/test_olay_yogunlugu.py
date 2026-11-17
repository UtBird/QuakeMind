"""Zaman seridi olay yogunlugu (J-167 F-4): SQL sayimi, indeks, yetki."""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture(scope="module")
def ortam():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_yog_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    jeton = {}
    for ad, rol in [("koordinator", "koordinator"), ("afetzede", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@yogunluk.local", ad, "test-sifresi-123")
        d.rol_ata(k["id"], rol)
        jeton[ad] = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}
    from uclar import zaman

    u = FastAPI()
    u.include_router(zaman.yonlendirici)
    return d, TestClient(u), jeton


def test_saat_basina_sayim(ortam):
    d, c, j = ortam
    t0 = 1_700_000_000.0
    # 1. saatte 2 SOS, 3. saatte 1 SOS; pencere disinda 1.
    for dk, kul in ((5, "a"), (50, "b"), (130, "c"), (-30, "d")):
        d.sos_ac_ya_da_guncelle(lon=36.16, lat=36.2, oncelik="kritik", kullanici_id=f"k-{kul}")
        d._baglanti.execute("UPDATE sos_cagrilari SET zaman = ? WHERE kullanici_id = ?", (t0 + dk * 60, f"k-{kul}"))
    d._baglanti.commit()
    y = c.get("/api/olay-yogunlugu", params={"baslangic": t0, "bitis": t0 + 4 * 3600}, headers=j["koordinator"])
    assert y.status_code == 200, y.text
    g = y.json()
    assert g["sos"] == [2, 0, 1, 0] and g["ihbar"] == [0, 0, 0, 0]


def test_tablo_taranmaz(ortam):
    d, _c, _j = ortam
    for tablo, indeks in (("sos_cagrilari", "ix_sos_zaman"), ("ihbarlar", "ix_ihbar_zaman")):
        plan = d._baglanti.execute(
            f"EXPLAIN QUERY PLAN SELECT CAST((zaman - ?) / ? AS INTEGER) AS d, COUNT(*) FROM {tablo} "
            "WHERE zaman >= ? AND zaman < ? GROUP BY d", (0, 3600, 0, 1)).fetchall()
        metin = " ".join(str(r[-1]) for r in plan)
        assert indeks in metin and "SCAN " + tablo not in metin.replace("USING", ""), metin


def test_yetki_ve_sinir(ortam):
    _d, c, j = ortam
    simdi = time.time()
    p = {"baslangic": simdi - 3600}
    assert c.get("/api/olay-yogunlugu", params=p).status_code == 401
    assert c.get("/api/olay-yogunlugu", params=p, headers=j["afetzede"]).status_code == 403
    cok = {"baslangic": simdi - 400 * 86400, "dilimSn": 60}
    assert c.get("/api/olay-yogunlugu", params=cok, headers=j["koordinator"]).status_code == 422
