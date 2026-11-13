"""SQLite depo katmani yuk olcumu (J-158).

Gercek veritabaninin KOPYASINDA calisir; gercek dosyaya yazilmaz.
Kullanim (QuakeMindBackend icinden):
    ../venv/Scripts/python.exe -I benchmark/sqlite_yuk_olcumu.py . benchmark/reports/sqlite_yuk_<tarih>.json
Sonuc 13 Kasim 2026: benchmark/reports/sqlite_yuk_2026-11-13.json (J-158).
"""
import json
import os
import random
import shutil
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

BACKEND = Path(sys.argv[1]).resolve()
CIKTI = Path(sys.argv[2])
KAYNAK_DB = BACKEND / "veri" / "quakemind.sqlite3"

gecici = Path(tempfile.mkdtemp(prefix="qm_sqlite_olcum_"))
kopya = gecici / "olcum.sqlite3"
# WAL'li canli dosyayi tutarli kopyalamak icin backup API.
with sqlite3.connect(f"file:{KAYNAK_DB}?mode=ro", uri=True) as kaynak, sqlite3.connect(kopya) as hedef:
    kaynak.backup(hedef)
os.environ["QUAKEMIND_SQLITE"] = str(kopya)
sys.path.insert(0, str(BACKEND))
import depo as depo_paketi  # noqa: E402

depo_paketi._depo = None
d = depo_paketi.depo_ac()
assert Path(d.yol).resolve() == kopya.resolve(), "kopya acilmadi"

random.seed(42)
SIMDI = time.time()
# Hatay / Antakya cevresi (yaklasik) -- konsolun "Antakya" kutusu
ANTAKYA = (36.05, 36.10, 36.30, 36.30)  # lon_min, lat_min, lon_max, lat_max
GENIS = (35.8, 35.8, 38.5, 38.2)


def yuzdelik(liste, p):
    s = sorted(liste)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def ozet(ms):
    return {
        "n": len(ms),
        "ortanca": round(statistics.median(ms), 3),
        "p95": round(yuzdelik(ms, 95), 3),
        "p99": round(yuzdelik(ms, 99), 3),
        "en_cok": round(max(ms), 3),
    }


def doldur(hedef_sos: int, hedef_hasar: int):
    """Tablolari dogrudan executemany ile hedef boyuta getirir (olcum disi)."""
    con = d._baglanti
    with d._kilit:
        n_sos = con.execute("SELECT COUNT(*) FROM sos_cagrilari").fetchone()[0]
        n_has = con.execute("SELECT COUNT(*) FROM hasar_noktalari").fetchone()[0]
        satirlar = []
        for _ in range(max(0, hedef_sos - n_sos)):
            satirlar.append((f"sos-o{uuid.uuid4().hex}", random.uniform(GENIS[0], GENIS[2]),
                             random.uniform(GENIS[1], GENIS[3]), random.choice(["kritik", "yuksek", "orta"]),
                             random.choice(["bekliyor", "atandi", "kapandi"]), SIMDI - random.uniform(0, 72 * 3600),
                             None, "olcum", None, None, None, None, "olcum", None))
        con.executemany("""INSERT INTO sos_cagrilari (id, lon, lat, oncelik, durum, zaman, mahalle, metin,
                           kullanici_id, ekip_id, atama_zamani, kapanma_zamani, kanal, ek)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", satirlar)
        satirlar = []
        for _ in range(max(0, hedef_hasar - n_has)):
            satirlar.append((f"hsr-o{uuid.uuid4().hex}", random.uniform(GENIS[0], GENIS[2]),
                             random.uniform(GENIS[1], GENIS[3]), random.random(), random.random(),
                             SIMDI - random.uniform(0, 72 * 3600),
                             random.choice(["uydu", "sos", "kamera", "metin"]), None, None, None))
        con.executemany("""INSERT INTO hasar_noktalari (id, lon, lat, skor, guven, zaman, kaynak, etiket, bolge, ek)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""", satirlar)
        con.commit()


def tek_yazma_olc(n=500):
    ms = []
    for _ in range(n):
        t = time.perf_counter()
        d.sos_ekle(lon=random.uniform(*ANTAKYA[0::2]), lat=random.uniform(*ANTAKYA[1::2]),
                   oncelik="yuksek", metin="olcum", kanal="olcum")
        ms.append((time.perf_counter() - t) * 1000)
    return ozet(ms)


def esz_yazma_olc(is_parcacigi=16, her_biri=100):
    """API'nin is parcacigi havuzu gibi: ayni anda N yazici."""
    ms, kilit = [], threading.Lock()

    def yazici():
        yerel = []
        for _ in range(her_biri):
            t = time.perf_counter()
            d.sos_ekle(lon=random.uniform(*ANTAKYA[0::2]), lat=random.uniform(*ANTAKYA[1::2]),
                       oncelik="kritik", metin="olcum", kanal="olcum")
            yerel.append((time.perf_counter() - t) * 1000)
        with kilit:
            ms.extend(yerel)

    t0 = time.perf_counter()
    ipler = [threading.Thread(target=yazici) for _ in range(is_parcacigi)]
    [i.start() for i in ipler]
    [i.join() for i in ipler]
    sure = time.perf_counter() - t0
    o = ozet(ms)
    o["is_parcacigi"] = is_parcacigi
    o["islem_sn"] = round(len(ms) / sure, 1)
    return o


def okuma_olc(tekrar=30):
    sorgular = {
        # /api/sos: konsol "son 6 saat"
        "sos_son6sa": lambda: d.sos_listele(baslangic=SIMDI - 6 * 3600),
        # /api/sos kutulu (harita gorunumu)
        "sos_son6sa_antakya": lambda: d.sos_listele(baslangic=SIMDI - 6 * 3600, kutu=ANTAKYA),
        # /api/hasar-noktalari: son 6 saat, Antakya kutusu (sinir 20000)
        "hasar_son6sa_antakya": lambda: d.hasar_listele(baslangic=SIMDI - 6 * 3600, kutu=ANTAKYA),
        # ozet/isi yolu: son 24 saatin butun hasari, sinir 100000 (sozlesme.py:440)
        "hasar_son24sa_100bin": lambda: d.hasar_listele(baslangic=SIMDI - 24 * 3600, sinir=100000),
        "sos_sayilari": lambda: d.sos_sayilari(baslangic=SIMDI - 6 * 3600),
    }
    sonuc = {}
    for ad, f in sorgular.items():
        ms, satir = [], 0
        f()  # isinma
        for _ in range(tekrar):
            t = time.perf_counter()
            r = f()
            ms.append((time.perf_counter() - t) * 1000)
            satir = len(r) if isinstance(r, list) else len(r or {})
        o = ozet(ms)
        o["donen_satir"] = satir
        sonuc[ad] = o
    return sonuc


def karisik_olc(okuyucu=16, yazici=8, sure_sn=5.0):
    """Ayni anda okuyan konsollar + yazan afetzedeler; yazma gecikmesi."""
    yaz_ms, oku_ms, kilit, dur = [], [], threading.Lock(), threading.Event()

    def oku():
        yerel = []
        while not dur.is_set():
            t = time.perf_counter()
            d.sos_listele(baslangic=SIMDI - 6 * 3600, kutu=ANTAKYA)
            yerel.append((time.perf_counter() - t) * 1000)
        with kilit:
            oku_ms.extend(yerel)

    def yaz():
        yerel = []
        while not dur.is_set():
            t = time.perf_counter()
            d.sos_ekle(lon=random.uniform(*ANTAKYA[0::2]), lat=random.uniform(*ANTAKYA[1::2]),
                       oncelik="kritik", metin="olcum", kanal="olcum")
            yerel.append((time.perf_counter() - t) * 1000)
        with kilit:
            yaz_ms.extend(yerel)

    ipler = [threading.Thread(target=oku) for _ in range(okuyucu)] + \
            [threading.Thread(target=yaz) for _ in range(yazici)]
    t0 = time.perf_counter()
    [i.start() for i in ipler]
    time.sleep(sure_sn)
    dur.set()
    [i.join() for i in ipler]
    sure = time.perf_counter() - t0
    return {
        "okuyucu": okuyucu, "yazici": yazici, "sure_sn": round(sure, 2),
        "yazma": {**ozet(yaz_ms), "islem_sn": round(len(yaz_ms) / sure, 1)},
        "okuma": {**ozet(oku_ms), "islem_sn": round(len(oku_ms) / sure, 1)},
    }


sonuclar = {"kopya": str(kopya), "zaman": time.strftime("%Y-%m-%d %H:%M"), "olcekler": []}
for hedef in (0, 10_000, 100_000, 1_000_000):
    t = time.perf_counter()
    if hedef:
        doldur(hedef, hedef)
    dolum = round(time.perf_counter() - t, 1)
    with d._kilit:
        n_sos = d._baglanti.execute("SELECT COUNT(*) FROM sos_cagrilari").fetchone()[0]
        n_has = d._baglanti.execute("SELECT COUNT(*) FROM hasar_noktalari").fetchone()[0]
    satir = {
        "sos_satir": n_sos, "hasar_satir": n_has, "dolum_sn": dolum,
        "dosya_mb": round(kopya.stat().st_size / 1e6, 1),
        "tek_yazma": tek_yazma_olc(),
        "esz_yazma_16": esz_yazma_olc(),
        "okuma": okuma_olc(10 if hedef >= 1_000_000 else 30),
        "karisik": karisik_olc(),
    }
    sonuclar["olcekler"].append(satir)
    print(f"{n_sos:>9} SOS / {n_has:>9} hasar  ok ({dolum} sn dolum)", flush=True)

CIKTI.write_text(json.dumps(sonuclar, ensure_ascii=False, indent=1), encoding="utf-8")
d.kapat()
shutil.rmtree(gecici, ignore_errors=True)
print("yazildi", CIKTI)
