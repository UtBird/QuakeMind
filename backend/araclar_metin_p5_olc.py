# -*- coding: utf-8 -*-
"""Metin siniflandirmanin UST KATEGORI (P-5) duzeyinde basarimi (makale Tablo 22,
§5.3(c)) ve yol kapanmasi etiketi denetimi (J-123).

Kume: deprem-private/intent_test_v13_anonymized, model_benchmarks/04_turkce_metin
bolmesi (tohum 42; 1418/305/305). Sinama kumesi 305 kayit.

ALTIN KATEGORI. Her kaydin 13 alt etiketlik altin kumesi Tablo 8 eslemesiyle ust
kategorilere indirilir. "Lojistik" alt etiketi hatta anahtar sozcuge gore iki ust
kategoriye (Yol Kapanma / Lojistik Ihtiyac) ayrisir; altinda bu ayrimi yapacak bir
bilgi yoktur, ayni kurali altina uygulamak dongusel olurdu. Bu yuzden
degerlendirmede iki lojistik kategorisi TEK sinifta birlesir: Acil Yardim, Enkaz,
Lojistik (birlesik), Alakasiz. Tahmin tek kategoridir; "Belirsiz" cekimser sayilir
(yanlis pozitif uretmez, altin kategorisini kacirir).

UC DEGERLENDIRME (ayni model ciktisi uzerinden):
  model  -- en yuksek alt etiket, Tablo 8 eslemesi (katman yok)
  yeni   -- duzeltilmis katman (classify_detay: model once, anahtar sozcuk kurtarma)
  eski   -- 27 Eylul oncesi katman (anahtar sozcuk once ve kosulsuz, alt dizgi)

MODELLER. `--model` ile birden cok. Karsilastirma calismasinin BERTurk agirligi
yalniz egitim bolmesiyle egitildi (sizintisiz). Uretimdeki `2kveri`nin hangi
kayitlarla egitildigi kayitli degil; sizinti belirtisi icin egitim ve sinama
bolmelerindeki basarimi yan yana yazilir.

    python araclar_metin_p5_olc.py --veri D:/lastdance/.../data_cache \
        --model berturk=D:/lastdance/.../model_berturk 2kveri=apps/disaster_nlp/models/2kveri \
        --eski-katman <eski classification.py> --cikti benchmark/reports/metin_p5_olcumu.json
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK / "apps" / "disaster_nlp"))

from src import classification as C  # noqa: E402
from src.preprocessing import clean_text  # noqa: E402

SINIFLAR = ["Acil Yardım İhtiyacı", "Enkaz Bildirimi", "Lojistik (birleşik)", "Alakasız"]


def _birlestir(kat):
    if kat in ("Yol Kapanma Bilgisi / Lojistik", "Lojistik İhtiyaç Bildirimi"):
        return "Lojistik (birleşik)"
    return kat


def altin_kume(etiketler):
    k = set()
    for e in etiketler:
        n = C._normalize_label(e)
        k.add("Lojistik (birleşik)" if n == "Lojistik" else _birlestir(C.CATEGORY_MAPPING.get(n, n)))
    return k


def _sahte(tahmin):
    s = C.DisasterClassifier.__new__(C.DisasterClassifier)
    s.classifier = lambda _m: [tahmin]
    return s


def _eski_modul(yol):
    spec = importlib.util.spec_from_file_location("eski_siniflandirma", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def degerlendir(altin, tahmin):
    """Sinif basina bire-karsi-hepsi P/R/F1 + mikro/makro + dogruluk."""
    tp, fp, fn = collections.Counter(), collections.Counter(), collections.Counter()
    dogru = cekimser = 0
    for a, t in zip(altin, tahmin):
        t = _birlestir(t)
        if t == "Belirsiz":
            cekimser += 1
        elif t in a:
            dogru += 1
        for s in SINIFLAR:
            if t == s and s in a:
                tp[s] += 1
            elif t == s:
                fp[s] += 1
            elif s in a:
                fn[s] += 1
    sonuc, f1ler = {}, []
    for s in SINIFLAR:
        p = tp[s] / (tp[s] + fp[s]) if tp[s] + fp[s] else 0.0
        r = tp[s] / (tp[s] + fn[s]) if tp[s] + fn[s] else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        sonuc[s] = {"kesinlik": round(p, 4), "duyarlilik": round(r, 4), "f1": round(f, 4),
                    "destek": tp[s] + fn[s]}
        f1ler.append(f)
    TP, FP, FN = sum(tp.values()), sum(fp.values()), sum(fn.values())
    mp = TP / (TP + FP) if TP + FP else 0.0
    mr = TP / (TP + FN) if TP + FN else 0.0
    return {"siniflar": sonuc, "mikroF1": round(2 * mp * mr / (mp + mr), 4) if mp + mr else 0.0,
            "makroF1": round(sum(f1ler) / len(f1ler), 4), "dogruluk": round(dogru / len(altin), 4),
            "cekimser": cekimser, "n": len(altin)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", required=True, help="data_cache klasoru (train/test.parquet)")
    ap.add_argument("--model", nargs="+", required=True, help="ad=yol")
    ap.add_argument("--eski-katman", required=True, help="27 Eylul oncesi classification.py")
    ap.add_argument("--egitim-de", nargs="*", default=[], help="bu modeller egitim bolmesinde de olculur")
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args()

    import pandas as pd
    from transformers import pipeline

    veri = Path(a.veri)
    bolme = {"sinama": pd.read_parquet(veri / "test.parquet"), "egitim": pd.read_parquet(veri / "train.parquet")}
    # Karsilastirma calismasinin agirliklari etiketleri LABEL_i diye tasir; sirasi
    # egitimde kullanilan (alfabetik) etiket listesidir (data_multilabel.py).
    etiket_listesi = json.loads((veri / "labels.json").read_text(encoding="utf-8"))["label_list"]

    def adlandir(t):
        return [{**x, "label": etiket_listesi[int(x["label"][6:])]} if str(x["label"]).startswith("LABEL_")
                else x for x in t]

    def alt_etiket_f1(altin13, ham):
        """13 alt etiket, esik 0,50, mikro-F1 (makale Tablo 20 ile ayni tanim)."""
        tp = fp = fn = 0
        for a_, t in zip(altin13, ham):
            tahmin = {x["label"] for x in t if x["score"] >= 0.5}
            tp += len(tahmin & a_); fp += len(tahmin - a_); fn += len(a_ - tahmin)
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        return round(2 * p * r / (p + r), 4) if p + r else 0.0
    eski = _eski_modul(a.eski_katman)
    rapor = {"kume": "deprem-private/intent_test_v13_anonymized", "bolme": "tohum 42; 1418/305/305",
             "siniflar": SINIFLAR, "modeller": {}}

    for tanim in a.model:
        ad, yol = tanim.split("=", 1)
        clf = pipeline("text-classification", model=yol, tokenizer=yol, device=-1, top_k=None)
        rapor["modeller"][ad] = {"yol": yol}
        for bad, df in bolme.items():
            if bad == "egitim" and ad not in a.egitim_de:
                continue
            metinler = [clean_text(str(x), lowercase=False) for x in df["text"]]
            altin = [altin_kume(list(e)) for e in df["label"]]
            ham = [adlandir(t) for t in clf([m[:512] for m in metinler], batch_size=16, truncation=True)]
            f1_13 = alt_etiket_f1([set(e) for e in df["label"]], ham)
            v = {"model": [], "yeni": [], "eski": [], "kaynak": collections.Counter()}
            for m, t in zip(metinler, ham):
                t = sorted(t, key=lambda x: x["score"], reverse=True)
                n = C._normalize_label(t[0]["label"])
                v["model"].append("Lojistik (birleşik)" if n == "Lojistik" else C.CATEGORY_MAPPING.get(n, n))
                d = _sahte(t).classify_detay(m)
                v["yeni"].append(d["kategori"])
                v["kaynak"][d["kaynak"]] += 1
                e = eski.DisasterClassifier.__new__(eski.DisasterClassifier)
                e.classifier = lambda _m, _t=t: [_t]
                v["eski"].append(e.classify(m)[0])
            rapor["modeller"][ad][bad] = {
                k: degerlendir(altin, v[k]) for k in ("model", "yeni", "eski")}
            rapor["modeller"][ad][bad]["yeniKatmanKarariVeren"] = dict(v["kaynak"])
            rapor["modeller"][ad][bad]["altEtiketMikroF1"] = f1_13
            r = rapor["modeller"][ad][bad]
            print(f"{ad:8s} {bad:7s} n={len(altin)} | 13 etiket mikro-F1 {f1_13:.3f} | ust kategori mikro-F1 "
                  f"model {r['model']['mikroF1']:.3f} "
                  f"yeni {r['yeni']['mikroF1']:.3f} eski {r['eski']['mikroF1']:.3f} | makro-F1 model "
                  f"{r['model']['makroF1']:.3f} yeni {r['yeni']['makroF1']:.3f} eski {r['eski']['makroF1']:.3f} "
                  f"| dogruluk yeni {r['yeni']['dogruluk']:.3f} | cekimser {r['yeni']['cekimser']} | "
                  f"karar {dict(v['kaynak'])}")

    # J-123: "Lojistik" alt etiketi ulasimi mi anlatiyor? (butun kume)
    tum = pd.concat([bolme["egitim"], pd.read_parquet(veri / "val.parquet"), bolme["sinama"]])
    yol_anahtar = C.RESCUE_KEYWORDS["Yol Kapanma Bilgisi / Lojistik"]
    lojistik = [r for _, r in tum.iterrows() if "Lojistik" in list(r["label"])]
    yollu = [r for _, r in tum.iterrows()
             if any(C.anahtar_eslesir(C._sozcukler(str(r["text"])), k) for k in yol_anahtar)]
    lj_yol = [r for r in lojistik
              if any(C.anahtar_eslesir(C._sozcukler(str(r["text"])), k) for k in yol_anahtar)]
    dagilim = collections.Counter(e for r in yollu for e in r["label"])
    rapor["j123"] = {
        "toplamKayit": len(tum), "lojistikEtiketli": len(lojistik),
        "lojistikEtiketliVeUlasimSozcuklu": len(lj_yol),
        "ulasimSozcukluKayit": len(yollu),
        "ulasimSozcukluKayitlarinEtiketDagilimi": dict(dagilim.most_common()),
        # Ornek metin YAZILMAZ: kume ozeldir ve 'anonymized' adina karsin telefon
        # numarasi ve acik adres iceren kayitlar vardir (28 Eylul denetimi).
    }
    print(f"J-123: {len(tum)} kayit | Lojistik etiketli {len(lojistik)} (ulasim sozcuklu {len(lj_yol)}) | "
          f"ulasim sozcuklu kayit {len(yollu)}, etiketleri: {dict(dagilim.most_common(6))}")
    Path(a.cikti).write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rapor:", a.cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
