"""Depo: okuma baglantilari ve ozet toplamalari (J-158).

Ayri gecici SQLite dosyasi kullanir; gercek veritabanina dokunmaz.
"""
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from depo.sqlite_surucu import SqliteDepo  # noqa: E402


@pytest.fixture()
def d():
    depo = SqliteDepo(str(Path(tempfile.mkdtemp(prefix="qm_depo_")) / "t.sqlite3"))
    yield depo
    depo.kapat()


def test_baska_is_parcacigindaki_yazma_hemen_gorunur(d):
    """Okuma kendi baglantisinda; COMMIT edilen yazmayi hemen gormeli."""
    sonuc = {}

    def yaz():
        sonuc["sos"] = d.sos_ekle(lon=36.16, lat=36.20, oncelik="kritik")

    t = threading.Thread(target=yaz)
    t.start()
    t.join()
    assert d.sos_bul(sonuc["sos"]["id"]) is not None
    # bir baska is parcacigi da gorur (kendi okuma baglantisini acar)
    gordu = {}
    t = threading.Thread(target=lambda: gordu.setdefault("x", d.sos_bul(sonuc["sos"]["id"])))
    t.start()
    t.join()
    assert gordu["x"] is not None


def test_uzun_okuma_yazmayi_bekletmez(d):
    """Okuma kilit almaz: bir okuma surerken yazma beklemeden tamamlanir."""
    con = d._baglanti
    with d._kilit:
        con.executemany(
            "INSERT INTO sos_cagrilari (id, lon, lat, oncelik, durum, zaman) VALUES (?,?,?,?,?,?)",
            [(f"sos-{uuid.uuid4().hex}", 36.1, 36.2, "orta", "bekliyor", time.time()) for _ in range(50_000)],
        )
        con.commit()
    basladi, bitti = threading.Event(), threading.Event()

    def okuyucu():
        basladi.set()
        for _ in range(20):
            d.sos_listele(sinir=50_000)
        bitti.set()

    t = threading.Thread(target=okuyucu)
    t.start()
    basladi.wait()
    sureler = []
    for _ in range(20):
        t0 = time.perf_counter()
        d.sos_ekle(lon=36.16, lat=36.20, oncelik="kritik")
        sureler.append(time.perf_counter() - t0)
    t.join()
    # Eski tek baglantida her yazma bir 50 000 satirlik okumanin bitmesini beklerdi.
    assert max(sureler) < 0.25, sureler


def test_hasar_ozeti_100_binden_fazlasini_eksiksiz_sayar(d):
    """Eski /api/ozet 100 000 satir okuyup sayiyordu; fazlasini sessizce kaybediyordu."""
    simdi = time.time()
    n = 100_050
    with d._kilit:
        d._baglanti.executemany(
            "INSERT INTO hasar_noktalari (id, lon, lat, skor, guven, zaman, kaynak) VALUES (?,?,?,?,?,?,?)",
            [(f"hsr-{uuid.uuid4().hex}", 36.1, 36.2, 0.9 if i % 2 else 0.5, 0.5, simdi, "uydu") for i in range(n)]
            + [(f"hsr-{uuid.uuid4().hex}", 36.1, 36.2, 0.9, 0.5, simdi, "kamera") for _ in range(7)],
        )
        d._baglanti.commit()
    o = d.hasar_ozeti(simdi - 60, None)
    assert o["kaynakSayilari"] == {"uydu": n, "kamera": 7}
    assert o["yikikYapi"] == n // 2 and o["hasarliYapi"] == n - n // 2
    # eski yol 100 000'de kesilirdi
    assert len(d.hasar_listele(baslangic=simdi - 60, sinir=100000)) == 100000


def test_kapanma_sayisi_ve_zaman_araligi(d):
    assert d.kapanma_sayisi() == 0
    assert d.hasar_ozeti() == {"kaynakSayilari": {}, "yikikYapi": 0, "hasarliYapi": 0}
