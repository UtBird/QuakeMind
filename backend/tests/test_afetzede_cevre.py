"""Afetzedenin çevresi: kapalı yollar ve hasar bölgeleri (J-180).

Ayrı geçici SQLite; gerçek veritabanına dokunulmaz."""
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

# Karenin ortasi (kare 0,0025 derece): kenara konan nokta kayan nokta yuzunden
# komsu kareye dusebilir.
LAT, LON = 36.20105, 36.16105


@pytest.fixture(scope="module")
def ortam():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_cevre_")) / "t.sqlite3")
    import depo as depo_paketi
    import kimlik

    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    k = kimlik.kullanici_kaydet("afz@cevre.local", "afz", "test-sifresi-123")
    jeton = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}

    simdi = time.time()
    # Kare A (LAT, LON): 3 kamera + 1 metin -> doner (4 bildirim).
    for i in range(3):
        d.hasar_ekle(lon=LON + 0.0001 * i, lat=LAT + 0.0001, skor=0.9, guven=1.0, kaynak="kamera", etiket=None, zaman=simdi)
    d.hasar_ekle(lon=LON + 0.0002, lat=LAT + 0.0002, skor=0.8, guven=1.0, kaynak="metin", etiket=None, zaman=simdi)
    # Kare B: 2 uydu -> esigin altinda, donmez.
    for i in range(2):
        d.hasar_ekle(lon=LON + 0.01, lat=LAT + 0.01, skor=0.9, guven=1.0, kaynak="uydu", etiket=None, zaman=simdi)
    # Kare C: 5 SOS -> SOS sayilmaz, donmez.
    for i in range(5):
        d.hasar_ekle(lon=LON - 0.01, lat=LAT - 0.01, skor=1.0, guven=1.0, kaynak="sos", etiket=None, zaman=simdi)
    # Kare D: 3 kamera ama 60 gun once -> varsayilan 30 gun disinda.
    for i in range(3):
        d.hasar_ekle(lon=LON + 0.02, lat=LAT, skor=0.9, guven=1.0, kaynak="kamera", etiket=None, zaman=simdi - 60 * 86400)
    # Ayni kapali yol parcasi iki analizde kaydedilmis + bir baska parca.
    cizgi = [[LAT + 0.001, LON], [LAT + 0.001, LON + 0.0005]]
    for z in (simdi - 100, simdi):
        d.kapanma_ekle(lon=LON + 0.00025, lat=LAT + 0.001, derece=3, kaynak="uydu", zaman=z, cizgi=cizgi)
    d.kapanma_ekle(lon=LON + 0.003, lat=LAT, derece=3, kaynak="uydu", zaman=simdi)
    # Eski kapanma: zaman siniri yok, rota da ondan kacinir.
    d.kapanma_ekle(lon=LON - 0.003, lat=LAT, derece=3, kaynak="uydu", zaman=simdi - 60 * 86400)
    from uclar import afetzede_cevre

    u = FastAPI()
    u.include_router(afetzede_cevre.yonlendirici)
    return TestClient(u), jeton, d


def test_oturumsuz_401(ortam):
    c, _, _ = ortam
    assert c.get("/api/afetzede/cevre", params={"lat": LAT, "lon": LON}).status_code == 401


def test_hasar_bolgeleri_sos_ve_az_bildirim_haric(ortam):
    c, j, _ = ortam
    y = c.get("/api/afetzede/cevre", params={"lat": LAT, "lon": LON}, headers=j)
    assert y.status_code == 200, y.text
    g = y.json()
    bolgeler = g["hasarBolgeleri"]
    assert len(bolgeler) == 1, bolgeler
    b = bolgeler[0]
    assert b["sayi"] == 4 and b["kaynaklar"] == {"uydu": 0, "fotograf": 3, "metin": 1}
    s, w, n, e = b["kare"]
    assert s <= LAT + 0.0001 <= n and w <= LON <= e
    assert "SOS" in g["kaynak"]["hasarBolgeleri"]


def test_zaman_penceresi(ortam):
    c, j, _ = ortam
    g = c.get("/api/afetzede/cevre", params={"lat": LAT, "lon": LON, "gun": 90}, headers=j).json()
    assert sorted(b["sayi"] for b in g["hasarBolgeleri"]) == [3, 4]


def test_sinirlar(ortam):
    c, j, _ = ortam
    assert c.get("/api/afetzede/cevre", params={"lat": LAT, "lon": LON, "yaricapKm": 50}, headers=j).status_code == 422
    assert c.get("/api/afetzede/cevre", params={"lat": 51.5, "lon": 0.0}, headers=j).status_code == 422


def test_sayim_indeks_kullanir(ortam):
    """Tablo taranmamalı (CLAUDE.md §10): zaman ya da konum indeksi kullanılır."""
    _, _, d = ortam
    plan = d._oku(
        """EXPLAIN QUERY PLAN SELECT CAST((lat - 30.0) / 0.0025 AS INTEGER) AS gy, COUNT(*)
           FROM hasar_noktalari WHERE zaman >= ? AND lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?
           AND kaynak NOT IN ('sos') GROUP BY gy""",
        (0.0, 36.0, 36.3, 36.1, 36.3),
    )
    metin = " ".join(str(dict(p)) for p in plan)
    assert "USING" in metin and "INDEX" in metin, metin


def test_kapali_yol_tekrari_bir_kez(ortam):
    c, j, _ = ortam
    g = c.get("/api/afetzede/cevre", params={"lat": LAT, "lon": LON}, headers=j).json()
    yollar = g["kapaliYollar"]
    assert len(yollar) == 3, yollar  # tekrar bir kez; 60 gunluk eski kapanma da var
    cizgili = [y for y in yollar if y["cizgi"]]
    assert len(cizgili) == 1 and len(cizgili[0]["cizgi"]) == 2
