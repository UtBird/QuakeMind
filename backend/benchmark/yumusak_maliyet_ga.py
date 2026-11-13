"""J-34 guven araliklari: yumusak maliyet deneyinin hucre duzeyi bootstrap'i.

Gorevler ayni hucrenin grafini, maskesini ve kapanmalarini paylastigi icin
bagimsiz degildir; yeniden ornekleme gorev degil HUCRE duzeyinde yapilir
(hucreler iadeli cekilir, cekilen hucrenin butun gorevleri alinir). Pay, R0 ->
R3 kazancinin ajanin yakaladigi kesri: (R0 - ajan) / (R0 - R3), ortalama gorev
suresi uzerinden.

Girdi: yumusak_maliyet_deneyi.py'nin yazdigi runs/yumusak_maliyet/satirlar.json
(depoda yok, 1,5 MB; deney yeniden kosularak uretilir).

    python benchmark/yumusak_maliyet_ga.py
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from naive_baseline import AVERAGE_SPEED_KMH  # noqa: E402

SATIRLAR = BENCH / "runs" / "yumusak_maliyet" / "satirlar.json"
ORNEK = 2000
# On kayitli capraz sinama: (sinama ili, ayar ilinde secilen ajan). Bugunku
# kural (M-sert) karsilastirma icin ayrica yazilir.
SINAMA = (("kahramanmaras", "M-y16"), ("hatay", "M-y8"))
EK = (("hatay", "M-sert"), ("kahramanmaras", "M-sert"))


def sure(s, t_u):
    return s["mesafeM"] / 1000 / AVERAGE_SPEED_KMH * 60 + s["kesif"] * t_u


def pay(veri, il, ajan, hucreler):
    ort = {}
    for a in ("R0", "R3", ajan):
        v = [x for h in hucreler for x in veri[(il, h, a)]]
        ort[a] = sum(v) / len(v)
    fark = ort["R0"] - ort["R3"]
    return (ort["R0"] - ort[ajan]) / fark if fark > 1e-9 else float("nan")


def main():
    satir = json.loads(SATIRLAR.read_text(encoding="utf-8"))
    for t_u in (20.0, 5.0):
        veri = defaultdict(list)
        for s in satir:
            if s["ulasti"]:
                veri[(s["il"], s["hucre"], s["ajan"])].append(sure(s, t_u))
        print(f"\n=== t_u = {t_u:g} dk -- hucre duzeyi bootstrap ({ORNEK} ornek) ===")
        for il, ajan in SINAMA + EK:
            hucreler = sorted({h for (i, h, _a) in veri if i == il})
            nokta = pay(veri, il, ajan, hucreler)
            rng = random.Random(7)
            boot = sorted(pay(veri, il, ajan, [rng.choice(hucreler) for _ in hucreler]) for _ in range(ORNEK))
            alt, ust = boot[int(0.025 * ORNEK)], boot[int(0.975 * ORNEK)]
            r0 = {(s["hucre"], s["tohum"], s["gorev"]): sure(s, t_u)
                  for s in satir if s["il"] == il and s["ajan"] == "R0" and s["ulasti"]}
            iyi = kotu = esit = 0
            for s in satir:
                if s["il"] == il and s["ajan"] == ajan and s["ulasti"]:
                    d = r0[(s["hucre"], s["tohum"], s["gorev"])] - sure(s, t_u)
                    if d > 0.05:
                        iyi += 1
                    elif d < -0.05:
                        kotu += 1
                    else:
                        esit += 1
            etiket = "SINAMA" if (il, ajan) in SINAMA else "bugunku kural"
            print(f"  {il:14} {ajan:7} ({etiket:13}) pay %{100 * nokta:5.1f}  "
                  f"%95 GA [%{100 * alt:5.1f}, %{100 * ust:5.1f}]   "
                  f"gorev: {iyi} iyi / {kotu} kotu / {esit} esit (R0'a gore)")


if __name__ == "__main__":
    main()
