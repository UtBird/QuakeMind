"""Esitleme tetikleyicisinin SOS yazma maliyeti (esitleme.py, CLAUDE.md 8).

Ne olculuyor: `SqliteDepo.sos_ekle` tek cagrinin duvar saati suresi (ms),
esitleme kapaliyken ve dugum rolunde (tetikleyici degisim gunlugune yazar).
Birim: SOS yazmasi basina ms, ortanca ve %95. Hedef: J-158'deki 50 SOS/sn
(yazma basina 20 ms) tutmali. Veritabani DISKTE (tmpfs'te degil), her kosu
bos dosyadan baslar. Sonuc JSON olarak benchmark/reports/'a yazilir.

    python benchmark/esitleme_yazma_olcumu.py [yazma_sayisi] [tekrar]
"""
import json
import platform
import random
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from depo import SqliteDepo  # noqa: E402


def kos(rol, n):
    dizin = Path(tempfile.mkdtemp(prefix="esitleme_olcum_", dir=KOK / "veri"))
    try:
        d = SqliteDepo(str(dizin / "t.sqlite3"))
        d.esitleme_kur(rol)
        sureler = []
        for _ in range(n):
            t = time.perf_counter()
            d.sos_ekle(lon=random.uniform(36.1, 36.2), lat=random.uniform(36.15, 36.25), oncelik="yuksek",
                       metin="olcum")
            sureler.append((time.perf_counter() - t) * 1000.0)
        gunluk = d.degisim_bekleyen_sayisi()
        d.kapat()
        sureler.sort()
        return {"ortancaMs": round(statistics.median(sureler), 4),
                "p95Ms": round(sureler[int(0.95 * len(sureler))], 4), "gunlukSatiri": gunluk}
    finally:
        shutil.rmtree(dizin, ignore_errors=True)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    tekrar = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    try:
        cpu = next(s.split(":", 1)[1].strip() for s in open("/proc/cpuinfo") if s.startswith("model name"))
    except (OSError, StopIteration):
        cpu = platform.processor() or platform.machine()
    sonuc = {"yazma": n, "tekrar": tekrar, "makine": cpu, "isletimSistemi": platform.platform(),
             "sqlite": __import__("sqlite3").sqlite_version, "tarih": time.strftime("%Y-%m-%d"),
             "python": platform.python_version(), "kosular": {}}
    for rol in (None, "dugum"):
        sonuc["kosular"][str(rol)] = [kos(rol, n) for _ in range(tekrar)]
    for rol, ks in sonuc["kosular"].items():
        print(rol, [k["ortancaMs"] for k in ks], [k["p95Ms"] for k in ks], ks[0]["gunlukSatiri"])
    cikti = KOK / "benchmark" / "reports" / "esitleme_yazma_olcumu.json"
    cikti.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(cikti)


if __name__ == "__main__":
    main()
