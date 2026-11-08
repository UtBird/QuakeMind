# -*- coding: utf-8 -*-
"""Tatbikat sonuclarini (araclar_tatbikat_kos.py ciktisi) makale tablosuna
birlestirir: alan x model satirlari, tohumlar uzerinden ortalama +- s.s.

Eskiden bu birlestirici depoda yoktu; makaledeki tablo elle derleniyordu ve
"Kesif" sutununun hangi kola ait oldugu kaybolmustu (J-117). Burada:

  - her kolun ortalama erisim suresi (ortak gorevler, gorev basina, dk),
  - kazanc = (bilmeyen - QuakeMind) / bilmeyen, TOHUM BASINA hesaplanip
    ortalanir,
  - kesif sayisi HER KOL ICIN AYRI (bilmeyen ve telsizle paylasan),
  - ceza payi = bilmeyen kolun toplam cezasi / (bilmeyen toplam sure -
    QuakeMind toplam sure), ortak gorevler uzerinden toplamlarla (tohum
    basina, sonra ortalama) -- makalenin Bolum 4.6'daki [OLCULECEK] hucresi,
  - kume = kac tohumun farkli afetzede kumesi urettigi.

Standart sapma orneklem s.s.'sidir (ddof = 1); tek tohumda 0 yazilir.

Kullanim (her model ayri kosulmus olabilir):
    python araclar_tatbikat_ozet.py sonuc_b0.json sonuc_b2.json sonuc_unet.json \
        --cikti tatbikat_ozet.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

BILMEYEN, TELSIZ, QM = "Kapanmayı bilmeyen ekip", "Telsizle paylaşan filo", "QuakeMind"


def _ort_ss(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None
    return float(np.mean(xs)), (float(np.std(xs, ddof=1)) if len(xs) > 1 else 0.0)


def _bic(ort, ss, basamak=2, yuzde=False):
    if ort is None:
        return "—"
    on = "%" if yuzde else ""
    return f"{on}{ort:.{basamak}f} ± {ss:.{basamak}f}".replace(".", ",")


def _model_adi(m):
    # kosucu modeli kunye sozlugu olarak yazar; tabloya yalniz adi gider
    return (m.get("ad") or m.get("etiket")) if isinstance(m, dict) else m


def alan_ozeti(s):
    tohum_sonuc = s.get("kollarTohum") or {}
    satir = {"alan": s.get("alan"), "model": _model_adi(s.get("model")), "hasarGecerli": s.get("hasarGecerli"),
             "kapaliKenar": s.get("kapaliKenar"), "afetzede": s.get("afetzedeSayisi"),
             "kapsama": (s.get("kapsama") or {}).get("edgesObservedFraction"),
             "kume": f"{s.get('farkliAfetzedeKumesi')}/{len(s.get('tohumlar') or [])}",
             "rh": s.get("rhKiyasi"), "rhTohum": s.get("rhTohum"), "tohum": {}}
    for t, k in tohum_sonuc.items():
        v = (k or {}).get("varyantlar") or {}
        b, te, q = v.get(BILMEYEN) or {}, v.get(TELSIZ) or {}, v.get(QM) or {}
        if (k or {}).get("hata") or not b or not q or b.get("ortalamaSureDk") is None \
                or q.get("ortalamaSureDk") is None:
            satir["tohum"][t] = {"hata": (k or {}).get("hata") or "kol ulasamadi (arac rotasi yok)"}
            continue
        fark_top = (b.get("toplamSureDk") or 0) - (q.get("toplamSureDk") or 0)
        satir["tohum"][t] = {
            "bilmeyen": b["ortalamaSureDk"], "telsiz": te.get("ortalamaSureDk"),
            "quakemind": q["ortalamaSureDk"],
            "kazanc": 100.0 * (b["ortalamaSureDk"] - q["ortalamaSureDk"]) / b["ortalamaSureDk"],
            "kesifBilmeyen": b.get("toplamKesif"), "kesifTelsiz": te.get("toplamKesif"),
            "ortakGorev": b.get("ortakGorev"),
            "cezaPayi": (100.0 * b["toplamCezaDk"] / fark_top)
                        if b.get("toplamCezaDk") is not None and fark_top > 1e-9 else None,
            "kapanmaCezasiDk": b.get("kapanmaCezasiDk"),
        }
    gecerli = [x for x in satir["tohum"].values() if "hata" not in x]
    for alan_adi in ("bilmeyen", "telsiz", "quakemind", "kazanc", "kesifBilmeyen", "kesifTelsiz",
                     "ortakGorev", "cezaPayi"):
        satir[alan_adi] = _ort_ss([x.get(alan_adi) for x in gecerli])
    satir["gecerliTohum"] = len(gecerli)
    return satir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("girdiler", nargs="+", help="araclar_tatbikat_kos.py JSON ciktilari")
    ap.add_argument("--cikti", default=None, help="ozet JSON")
    a = ap.parse_args()

    satirlar = []
    for yol in a.girdiler:
        for s in json.loads(Path(yol).read_text(encoding="utf-8")):
            if s.get("hata"):
                satirlar.append({"alan": s.get("alan"), "model": _model_adi(s.get("model")), "hata": s["hata"]})
                continue
            satirlar.append(alan_ozeti(s))

    bas = ("| Alan | Model | Hasar | Kapalı k. | Afetzede | Bilmeyen | Telsizle paylaşan | QuakeMind | "
           "Kazanç | Keşif (bilmeyen) | Keşif (telsiz) | Ortak görev | Ceza payı | Kapsama | Küme |")
    print(bas)
    print("|" + "---|" * 15)
    for r in satirlar:
        if r.get("hata"):
            print(f"| {r['alan']} | {r.get('model')} | HATA: {r['hata']} |" + " |" * 12)
            continue
        hasar = f"%{(r['hasarGecerli'] or 0) * 100:.2f}".replace(".", ",")
        kapsama = f"%{(r['kapsama'] or 0) * 100:.0f}"
        if not r["gecerliTohum"]:
            print(f"| {r['alan']} | {r['model']} | {hasar} | {r['kapaliKenar']} | {r['afetzede']} | — | — | — | "
                  f"araç rotası yok | — | — | — | — | {kapsama} | {r['kume']} |")
            continue
        print(f"| {r['alan']} | {r['model']} | {hasar} | {r['kapaliKenar']} | {r['afetzede']} | "
              f"{_bic(*r['bilmeyen'])} | {_bic(*r['telsiz'])} | {_bic(*r['quakemind'])} | "
              f"{_bic(*r['kazanc'], basamak=1, yuzde=True)} | {_bic(*r['kesifBilmeyen'], basamak=1)} | "
              f"{_bic(*r['kesifTelsiz'], basamak=1)} | {_bic(*r['ortakGorev'], basamak=1)} | "
              f"{_bic(*r['cezaPayi'], basamak=0, yuzde=True)} | {kapsama} | {r['kume']} |")
    rh_var = [r for r in satirlar if r.get("rh")]
    if rh_var:
        print("\nr_h duyarliligi (Tablo 18; ilk tohum):")
        print("| Alan | Model | r_h (m) | Kapalı kenar | Ortak görev | Bilmeyen (dk) | QuakeMind (dk) | "
              "Görünür kazanç | Keşif (bilmeyen) |")
        print("|" + "---|" * 9)
        for r in rh_var:
            for x in r["rh"]:
                sayi = (lambda v: "—" if v is None else f"{v:.2f}".replace(".", ","))
                kaz = "—" if x.get("gorunurKazanc") is None else f"%{x['gorunurKazanc']:.0f}"
                print(f"| {r['alan']} | {r['model']} | {x['yaricapM']:.0f} | {x['kapaliKenar']} | "
                      f"{x.get('ortakGorev')} | {sayi(x.get('bilmeyenDk'))} | {sayi(x.get('quakemindDk'))} | "
                      f"{kaz} | {x.get('kesifBilmeyen')} |")
    if a.cikti:
        Path(a.cikti).write_text(json.dumps(satirlar, ensure_ascii=False, indent=1, default=str),
                                 encoding="utf-8")
        print(f"\nozet -> {a.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
