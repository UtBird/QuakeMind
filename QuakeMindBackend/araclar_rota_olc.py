"""Arac rotasi olcumu (J-171): donus yasagi uyumu, yola oturtma ve hiz.

Ayni arac eski ve yeni motoru olcer (kural 8: once taban, sonra iyilestirme).
Yalniz `arac_rotasi`nin disa acik islevlerini kullanir: `yoldan`,
`hedef_aramasi`, `ag_yukle`, `genel_ag`, `katalog`.

  * Yasak uyumu: OSM donus yasaklarinin (veri/yol_agi/arac/yasaklar.json) her
    biri icin gelen yolda kavsaktan ~60 m once baslayan, giden yolda ~60 m
    sonra biten rota istenir. Rota kavsaktan gecip yasakli donusu yapiyorsa
    ihlal sayilir. Kavsaga hic ugramayan rota ihlal degildir.
  * Oturtma: yol kenarindan 5-25 m uzaga rastgele dusen noktalar; motorun
    noktayi oturttugu yer ile gercek yol arasindaki fark (metre).
  * Hiz: soguk arama (onbellek bos) ve rota suresi.

Veritabani okunur (hasar ve kapanma), yazilmaz. Ornek: rastgele, tohum 42.

    python araclar_rota_olc.py --cikti benchmark/reports/rota_yeni.json
    python araclar_rota_olc.py --cikti benchmark/reports/rota_taban.json --motor eski/arac_rotasi.py
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

if "--motor" in sys.argv:
    # Eski motoru dosyasindan yukle (taban olcumu icin): ayni arac, ayni ornek.
    import importlib.util

    _yol = sys.argv[sys.argv.index("--motor") + 1]
    _spec = importlib.util.spec_from_file_location("arac_rotasi", _yol)
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["arac_rotasi"] = _mod
    _spec.loader.exec_module(_mod)
    _mod.AG_DIZINI = BACKEND / "veri" / "yol_agi" / "arac"  # ag dosyalari depodaki

import arac_rotasi  # noqa: E402

YASAKLAR = BACKEND / "veri" / "yol_agi" / "arac" / "yasaklar.json"


def _m(lon1, lat1, lon2, lat2):
    kx = 111320.0 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot((lon2 - lon1) * kx, (lat2 - lat1) * 110574.0)


def _cizgiye(p, cizgi):
    """Noktanin kirik cizgiye uzakligi (m)."""
    en = math.inf
    for (x1, y1), (x2, y2) in zip(cizgi, cizgi[1:]):
        kx = 111320.0 * math.cos(math.radians(y1))
        ax, ay = 0.0, 0.0
        bx, by = (x2 - x1) * kx, (y2 - y1) * 110574.0
        px, py = (p[0] - x1) * kx, (p[1] - y1) * 110574.0
        l2 = bx * bx + by * by or 1e-9
        t = max(0.0, min(1.0, (px * bx + py * by) / l2))
        en = min(en, math.hypot(px - (ax + bx * t), py - (ay + by * t)))
    return en


def _uzaktaki_nokta(cizgi, kavsak, uzaklik=60.0):
    """Cizgi uzerinde kavsaktan `uzaklik` m (ya da cizginin oteki ucu) uzaktaki nokta."""
    if _m(*cizgi[0], *kavsak) > _m(*cizgi[-1], *kavsak):
        cizgi = cizgi[::-1]  # kavsak basta olsun
    toplam = 0.0
    for (x1, y1), (x2, y2) in zip(cizgi, cizgi[1:]):
        d = _m(x1, y1, x2, y2)
        if toplam + d >= uzaklik and d > 0:
            t = (uzaklik - toplam) / d
            return [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t]
        toplam += d
    return list(cizgi[-1])


def yasak_uyumu() -> dict:
    yasaklar = json.loads(YASAKLAR.read_text(encoding="utf-8"))["yasaklar"]
    sonuc = {"denenen": 0, "rotaYok": 0, "kavsaktanGecmedi": 0, "uydu": 0, "ihlal": 0, "ihlaller": []}
    for y in yasaklar:
        kav = y["kavsak"]
        if arac_rotasi.bolge_bul(*kav) is None:
            continue
        bas = _uzaktaki_nokta(y["gelen"], kav)
        if y["tur"] == "no_u_turn" or y["giden"] == y["gelen"]:
            hedef = _uzaktaki_nokta(y["giden"], kav, 30.0)  # ayni yola geri donus
        else:
            hedef = _uzaktaki_nokta(y["giden"], kav)
        sonuc["denenen"] += 1
        r = arac_rotasi.yoldan(hedef[0], hedef[1], bas[0], bas[1], rota=True)
        if not r or not r.get("rota"):
            sonuc["rotaYok"] += 1
            continue
        rota = r["rota"]
        gecti = False
        ihlal = False
        for i in range(1, len(rota) - 1):
            # Yalniz kavsaga en yakin nokta: yolun kavsaga birkac metre
            # kalan ara noktasi kavsak sanilmasin.
            d = _m(*rota[i], *kav)
            if d > 3.0 or d > _m(*rota[i - 1], *kav) or d > _m(*rota[i + 1], *kav):
                continue
            gecti = True
            gelen_uzerinde = _cizgiye(rota[i - 1], y["gelen"]) < 3.0
            giden_uzerinde = _cizgiye(rota[i + 1], y["giden"]) < 3.0
            if y["tur"].startswith("no_") and gelen_uzerinde and giden_uzerinde:
                # U donusu yasaginda gelen ve giden ayni yol: geri donus mu?
                if y["tur"] == "no_u_turn" and _m(*rota[i - 1], *rota[i + 1]) > 3.0:
                    continue
                ihlal = True
            if y["tur"].startswith("only_") and gelen_uzerinde and not giden_uzerinde:
                ihlal = True
        if not gecti:
            sonuc["kavsaktanGecmedi"] += 1
        elif ihlal:
            sonuc["ihlal"] += 1
            sonuc["ihlaller"].append({"tur": y["tur"], "kavsak": kav})
        else:
            sonuc["uydu"] += 1
    return sonuc


def oturtma(bolge: str, n: int, rng: random.Random) -> dict:
    ag = arac_rotasi.ag_yukle(bolge)
    farklar = []
    for _ in range(n):
        k = rng.randrange(len(ag.u))
        if ag.uzunluk[k] < 20:
            continue
        t = rng.uniform(0.2, 0.8)
        x1, y1 = ag.dugum_xy[ag.u[k]]
        x2, y2 = ag.dugum_xy[ag.v[k]]
        dx, dy = x2 - x1, y2 - y1
        boy = math.hypot(dx, dy) or 1.0
        kayma = rng.uniform(5, 25) * rng.choice((-1, 1))
        px, py = x1 + dx * t - dy / boy * kayma, y1 + dy * t + dx / boy * kayma
        lon, lat = px / ag.kx + ag.lon0, py / ag.ky + ag.lat0
        gercek = abs(kayma)
        if hasattr(arac_rotasi, "oturtma_mesafesi"):
            d = arac_rotasi.oturtma_mesafesi(ag, lon, lat)
        else:
            d = ag.oturt(lon, lat)[1]
        farklar.append(d - gercek)
    farklar.sort()
    return {
        "nokta": len(farklar),
        "fazlaMOrtanca": round(statistics.median(farklar), 1),
        "fazlaMYuzde95": round(farklar[int(len(farklar) * 0.95)], 1),
        "30mUstuOran": round(sum(1 for f in farklar if f > 30) / len(farklar), 3),
    }


def hiz(bolge: str, n: int, rng: random.Random, genel: bool = False) -> dict:
    ag = arac_rotasi.genel_ag() if genel else arac_rotasi.ag_yukle(bolge)
    arama_ms, rota_ms, bulunan = [], [], 0
    for _ in range(n):
        h = rng.randrange(len(ag.lon))
        e = rng.randrange(len(ag.lon))
        hl, ha, el, ea = float(ag.lon[h]), float(ag.lat[h]), float(ag.lon[e]), float(ag.lat[e])
        arac_rotasi._aramalar.clear()
        t0 = time.perf_counter()
        arama = arac_rotasi.hedef_aramasi(hl, ha, genel=genel)
        t1 = time.perf_counter()
        r = arama.ekipten(el, ea, rota=True) if arama else None
        t2 = time.perf_counter()
        arama_ms.append((t1 - t0) * 1000)
        rota_ms.append((t2 - t1) * 1000)
        bulunan += bool(r)
    return {
        "istek": n, "rotaBulundu": bulunan,
        "aramaMsOrtanca": round(statistics.median(arama_ms), 1),
        "aramaMsEnCok": round(max(arama_ms), 1),
        "rotaMsOrtanca": round(statistics.median(rota_ms), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--motor", help="olculecek arac_rotasi.py (varsayilan: depodaki)")
    a = ap.parse_args()
    rng = random.Random(42)
    rapor = {"motor": getattr(arac_rotasi, "MOTOR", "dugum tabanli Dijkstra (J-55)"),
             "olcum": time.strftime("%Y-%m-%d %H:%M")}
    # Isinma: aglar ve hasar carpanlari bellege (olcume girmez).
    arac_rotasi.ag_yukle("antakya")
    arac_rotasi.genel_ag()
    rapor["yasakUyumu"] = yasak_uyumu()
    rapor["oturtma"] = {b: oturtma(b, 400, rng) for b in ("antakya", "antep")}
    rapor["hiz"] = {"antakya": hiz("antakya", 40, rng), "genel": hiz("antakya", 10, rng, genel=True)}
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    Path(a.cikti).write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    ozet = {k: v for k, v in rapor["yasakUyumu"].items() if k != "ihlaller"}
    print("yasak:", ozet)
    print("oturtma:", rapor["oturtma"])
    print("hiz:", rapor["hiz"])


if __name__ == "__main__":
    main()
