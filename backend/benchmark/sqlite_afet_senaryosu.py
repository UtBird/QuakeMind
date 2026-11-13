"""Afet senaryosu yuk olcumu (J-158): saniyede N SOS yazilirken K konsol tazelenir.

Gercek veritabaninin KOPYASINDA calisir; gercek dosyaya yazilmaz.

Iki tazeleme kipi:
  olay      -- her SOS her konsolda listeyi + ozeti yeniden istetir (eski konsol)
  birlesik  -- konsol ilk mesajda hemen, pencere icinde gelenleri pencere sonunda
               tek tazelemede birlestirir (konsol `birlestirici`, 1 sn)

Kullanim (QuakeMindBackend icinden):
    ../venv/Scripts/python.exe -I benchmark/sqlite_afet_senaryosu.py \\
        --depo-dizini . --kip birlesik --satir 100000 --cikti benchmark/reports/x.json

`--depo-dizini`: icinde `depo/` paketi olan dizin. Eski surumu olcmek icin
`git show <commit>:QuakeMindBackend/depo/...` ile gecici bir dizine cikarilir.

Olculenler: SOS yazma gecikmesi (ms) ve gerceklesen yazma hizi; konsol basina
tazeleme suresi; guncellik gecikmesi = SOS yazildiktan konsolun onu iceren
tazelemeyi bitirmesine kadar gecen sure (ms).
"""
import argparse
import json
import os
import queue
import random
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--depo-dizini", required=True)
ap.add_argument("--kaynak-db", default="veri/quakemind.sqlite3")
ap.add_argument("--kip", choices=["olay", "birlesik"], required=True)
ap.add_argument("--satir", type=int, default=100_000)
ap.add_argument("--hiz", type=float, default=50.0, help="saniyede SOS")
ap.add_argument("--konsol", type=int, default=5)
ap.add_argument("--sure", type=float, default=10.0)
ap.add_argument("--pencere", type=float, default=1.0)
ap.add_argument("--cikti", required=True)
a = ap.parse_args()

gecici = Path(tempfile.mkdtemp(prefix="qm_afet_"))
kopya = gecici / "afet.sqlite3"
with sqlite3.connect(f"file:{Path(a.kaynak_db).resolve()}?mode=ro", uri=True) as k, sqlite3.connect(kopya) as h:
    k.backup(h)
os.environ["QUAKEMIND_SQLITE"] = str(kopya)
sys.path.insert(0, str(Path(a.depo_dizini).resolve()))
import depo as depo_paketi  # noqa: E402

depo_paketi._depo = None
d = depo_paketi.depo_ac()
assert Path(d.yol).resolve() == kopya.resolve()

random.seed(7)
SIMDI = time.time()
GENIS = (35.8, 35.8, 38.5, 38.2)
ANTAKYA = (36.05, 36.10, 36.30, 36.30)

# --- doldur (olcum disi) ---
con = sqlite3.connect(kopya)
n = con.execute("SELECT COUNT(*) FROM sos_cagrilari").fetchone()[0]
con.executemany(
    """INSERT INTO sos_cagrilari (id, lon, lat, oncelik, durum, zaman, mahalle, metin,
       kullanici_id, ekip_id, atama_zamani, kapanma_zamani, kanal, ek) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    [(f"sos-o{uuid.uuid4().hex}", random.uniform(GENIS[0], GENIS[2]), random.uniform(GENIS[1], GENIS[3]),
      random.choice(["kritik", "yuksek", "orta"]), random.choice(["bekliyor", "atandi", "kapandi"]),
      SIMDI - random.uniform(0, 72 * 3600), None, "olcum", None, None, None, None, "olcum", None)
     for _ in range(max(0, a.satir - n))])
n = con.execute("SELECT COUNT(*) FROM hasar_noktalari").fetchone()[0]
con.executemany(
    """INSERT INTO hasar_noktalari (id, lon, lat, skor, guven, zaman, kaynak, etiket, bolge, ek)
       VALUES (?,?,?,?,?,?,?,?,?,?)""",
    [(f"hsr-o{uuid.uuid4().hex}", random.uniform(GENIS[0], GENIS[2]), random.uniform(GENIS[1], GENIS[3]),
      random.random(), random.random(), SIMDI - random.uniform(0, 72 * 3600),
      random.choice(["uydu", "sos", "kamera", "metin"]), None, None, None) for _ in range(max(0, a.satir - n))])
con.commit()
con.close()


def ozet_cagir(b):
    """/api/ozet'in depo isi: yeni surumde SQL toplama, eskide 100 000 satir okuma."""
    d.sos_sayilari(b, None)
    if hasattr(d, "hasar_ozeti"):
        d.hasar_ozeti(b, None)
        d.kapanma_sayisi(b, None)
    else:
        d.hasar_listele(baslangic=b, sinir=100000)
        d.kapanma_listele(baslangic=b, sinir=100000)


def konsol_tazele():
    b = time.time() - 6 * 3600
    d.sos_listele(baslangic=b, kutu=ANTAKYA)  # /api/sos (harita gorunumu)
    ozet_cagir(b)  # /api/ozet


def yuzde(x, p):
    s = sorted(x)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))] if s else None


def ozet(x):
    return {"n": len(x), "ortanca": round(statistics.median(x), 1) if x else None,
            "p95": round(yuzde(x, 95), 1) if x else None, "p99": round(yuzde(x, 99), 1) if x else None,
            "en_cok": round(max(x), 1) if x else None}


dur = threading.Event()
yaz_ms: list[float] = []
yazilan: list[float] = []
kuyruklar = [queue.Queue() for _ in range(a.konsol)]
taze_ms = [[] for _ in range(a.konsol)]
guncellik_ms = [[] for _ in range(a.konsol)]


def yazici():
    t0 = time.perf_counter()
    i = 0
    while not dur.is_set():
        hedef = t0 + i / a.hiz
        bekle = hedef - time.perf_counter()
        if bekle > 0:
            time.sleep(bekle)
        t = time.perf_counter()
        d.sos_ekle(lon=random.uniform(ANTAKYA[0], ANTAKYA[2]), lat=random.uniform(ANTAKYA[1], ANTAKYA[3]),
                   oncelik="kritik", metin="olcum", kanal="olcum")
        bitti = time.perf_counter()
        yaz_ms.append((bitti - t) * 1000)
        yazilan.append(bitti)
        for q in kuyruklar:
            q.put(bitti)  # SSE mesaji
        i += 1


def konsol(k):
    q = kuyruklar[k]
    while not dur.is_set():
        try:
            ilk = q.get(timeout=0.2)
        except queue.Empty:
            continue
        bekleyen = [ilk]
        if a.kip == "olay":
            pass  # her mesaj ayri tazeleme
        t = time.perf_counter()
        konsol_tazele()
        son = time.perf_counter()
        taze_ms[k].append((son - t) * 1000)
        guncellik_ms[k].extend((son - e) * 1000 for e in bekleyen)
        if a.kip == "birlesik":
            # Pencere: ilk tazelemeden sonra `pencere` sn icinde gelenler tek tazelemede.
            pencere_sonu = t + a.pencere
            while not dur.is_set():
                kalan = pencere_sonu - time.perf_counter()
                if kalan > 0:
                    time.sleep(kalan)
                birikmis = []
                while True:
                    try:
                        birikmis.append(q.get_nowait())
                    except queue.Empty:
                        break
                if not birikmis:
                    break
                t = time.perf_counter()
                konsol_tazele()
                son = time.perf_counter()
                taze_ms[k].append((son - t) * 1000)
                guncellik_ms[k].extend((son - e) * 1000 for e in birikmis)
                pencere_sonu = t + a.pencere


ipler = [threading.Thread(target=yazici)] + [threading.Thread(target=konsol, args=(k,)) for k in range(a.konsol)]
t0 = time.perf_counter()
[i.start() for i in ipler]
time.sleep(a.sure)
dur.set()
[i.join() for i in ipler]
gecen = time.perf_counter() - t0

# Konsollarda islenmeden kalan mesaj = en kotu durumda hic gorulmeyen SOS
islenmeyen = sum(q.qsize() for q in kuyruklar)
sonuc = {
    "kip": a.kip, "depo_dizini": str(Path(a.depo_dizini).name), "satir": a.satir, "hedef_hiz": a.hiz,
    "konsol": a.konsol, "sure_sn": round(gecen, 1), "pencere_sn": a.pencere,
    # Hiz yalniz yazicinin kendi suresine bolunur: `gecen` konsollarin son
    # tazelemeyi bitirmesini beklemeyi de icerir (ilk surumde hizi dusuk gosteriyordu).
    "yazma": {**ozet(yaz_ms),
              "gerceklesen_hiz": round((len(yazilan) - 1) / (yazilan[-1] - yazilan[0]), 1)
              if len(yazilan) > 1 else None},
    "tazeleme_suresi": ozet([x for k in taze_ms for x in k]),
    "tazeleme_sayisi": sum(len(k) for k in taze_ms),
    "guncellik_gecikmesi": ozet([x for k in guncellik_ms for x in k]),
    "islenmeden_kalan_mesaj": islenmeyen,
}
Path(a.cikti).write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(sonuc, ensure_ascii=False))
d.kapat()
