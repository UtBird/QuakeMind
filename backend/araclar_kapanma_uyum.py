# -*- coding: utf-8 -*-
"""Kapanma yer gercegi: etiketleyici basina kesinlik / duyarlilik kestirimi ve
etiketleyiciler arasi uyum (Cohen kappa). Makale §4.3, Tablo 13.

Girdi: tam anahtar (araclar_kapanma_etiketle.py ciktisi; modelin her kesit icin ne
dedigi ve acik parcalarin orneklem orani) ve bir ya da daha cok etiket dosyasi
(insan_kiti/etiketle.html ciktisi ya da ayni bicimde el ile).

Olcumler (kararsiz etiketler kesinlikten dusulur, yargilanamayan oran ayrica yazilir):
  kesinlik    = modelin KAPALI dedigi ve etiketin kapali dedigi / modelin KAPALI dedigi, kararsiz haric
                (Wilson %95 araligiyla)
  duyarlilik  = kapali buldugu / (kapali buldugu + kacirilan kestirimi); kacirilan kestirimi = acik
                orneklemde kapali etiketlenen / orneklem orani
  kappa       = iki etiketleyicinin 33 kesitteki uc sinifli uyumu (ve kararsiz haric ikili uyum)

    python araclar_kapanma_uyum.py benchmark/kapanma_yer_gercegi/anahtar_tam_defne_elektrik.json \
        benchmark/kapanma_yer_gercegi/etiketler_defne_elektrik.json [etiketler_<insan>.json ...]
"""
import argparse
import itertools
import json
import math
import sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    o = (p + z * z / (2 * n)) / (1 + z * z / n)
    return max(0.0, o - m), min(1.0, o + m)


def kappa(a, b, siniflar):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(s) / n) * (b.count(s) / n) for s in siniflar)
    return None if pe == 1 else (po - pe) / (1 - pe)


def olc(anahtar, etiket):
    k = anahtar["kesitler"]
    oran = anahtar["acikOrneklemOrani"]
    toplam = anahtar["toplamAday"]
    mk = [c for c in k if k[c]["modelKapali"]]
    ma = [c for c in k if not k[c]["modelKapali"]]
    say = lambda kodlar, e: sum(1 for c in kodlar if etiket.get(c) == e)
    tp, fp, mk_kar = say(mk, "kapali"), say(mk, "acik"), say(mk, "kararsiz")
    ka, aa, ma_kar = say(ma, "kapali"), say(ma, "acik"), say(ma, "kararsiz")
    kacirilan = ka / oran if oran else None
    gercek = tp + (kacirilan or 0)
    alt, ust = wilson(tp, tp + fp)
    return {
        "modelKapali": {"kapali": tp, "acik": fp, "kararsiz": mk_kar},
        "modelAcikOrnek": {"kapali": ka, "acik": aa, "kararsiz": ma_kar},
        "kesinlik": (tp / (tp + fp)) if tp + fp else None, "kesinlikWilson95": [alt, ust],
        "kesinlikKararsizHata": tp / len(mk) if mk else None,
        "kacirilanKestirim": kacirilan, "gercekKapanmaKestirim": gercek,
        "gercekKapanmaOrani": gercek / toplam if toplam else None,
        "duyarlilikKestirim": (tp / gercek) if gercek else None,
        "yargilanamayan": (mk_kar + ma_kar) / len(k),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("anahtar")
    ap.add_argument("etiketler", nargs="+")
    ap.add_argument("--cikti", default=None)
    a = ap.parse_args()

    anahtar = json.loads(Path(a.anahtar).read_text(encoding="utf-8"))
    kodlar = sorted(anahtar["kesitler"])
    etiketciler = {}
    for yol in a.etiketler:
        e = json.loads(Path(yol).read_text(encoding="utf-8"))
        eksik = [c for c in kodlar if c not in e["etiket"]]
        if eksik:
            print(f"UYARI {yol}: {len(eksik)} kesit etiketsiz ({eksik[:5]}...)")
        etiketciler[e.get("etiketleyen", yol)] = e["etiket"]

    rapor = {"alan": anahtar.get("alan"), "model": anahtar.get("model"), "etiketleyiciler": {}, "uyum": []}
    for ad, et in etiketciler.items():
        r = olc(anahtar, et)
        rapor["etiketleyiciler"][ad] = r
        w = r["kesinlikWilson95"]
        print(f"{ad}\n  model KAPALI: {r['modelKapali']} | model ACIK ornek: {r['modelAcikOrnek']}")
        print(f"  kesinlik {r['modelKapali']['kapali']}/{r['modelKapali']['kapali'] + r['modelKapali']['acik']}"
              f" (Wilson %95 {w[0]:.2f}-{w[1]:.2f}) | duyarlilik kestirimi "
              f"{r['duyarlilikKestirim']:.3f} (gercek kapanma ~{r['gercekKapanmaKestirim']:.0f}/{anahtar['toplamAday']})"
              f" | yargilanamayan %{100 * r['yargilanamayan']:.0f}")
    for (a1, e1), (a2, e2) in itertools.combinations(etiketciler.items(), 2):
        ortak = [c for c in kodlar if c in e1 and c in e2]
        x, y = [e1[c] for c in ortak], [e2[c] for c in ortak]
        k3 = kappa(x, y, ["kapali", "acik", "kararsiz"])
        ikili = [(p, q) for p, q in zip(x, y) if p != "kararsiz" and q != "kararsiz"]
        k2 = kappa([p for p, _ in ikili], [q for _, q in ikili], ["kapali", "acik"]) if ikili else None
        esit = sum(p == q for p, q in zip(x, y))
        rapor["uyum"].append({"a": a1, "b": a2, "kesit": len(ortak), "ayniEtiket": esit,
                              "kappa3": k3, "kappa2KararsizHaric": k2, "ikiliKesit": len(ikili)})
        print(f"uyum [{a1}] x [{a2}]: {esit}/{len(ortak)} ayni | kappa (3 sinif) {k3:.3f} | "
              f"kappa (kararsiz haric, n={len(ikili)}) {k2 if k2 is None else round(k2, 3)}")
    if a.cikti:
        Path(a.cikti).write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
