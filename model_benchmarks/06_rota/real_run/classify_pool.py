"""
Sentetik ihbar metinleri icin GERCEK BERTurk siniflandiricisiyla (
backend/apps/disaster_nlp/src/classification.py::DisasterClassifier)
kategori uretir ve sonucu bir kere onbelleklerki assignment.py her
kosumda modeli yeniden yuklemesin (yukleme ~100 sn, cikarim ~3-4 sn/metin).
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))

from apps.disaster_nlp.src.classification import DisasterClassifier  # noqa: E402

TEXT_POOL = [
    "Bina tamamen yikildi enkaz altinda kaldik lutfen yardim edin",
    "Ust kat cokmus icerde iki kisi var enkaz kaldirma ekibi lazim",
    "Duvar uzerimize devrildi cikamiyoruz enkazdan sesleniyoruz",
    "Su ve gida ihtiyacimiz var cocuklarimiz ac kaldik",
    "Yarali var kanama var acil saglik ekibi gerekiyor",
    "Isinamiyoruz battaniye ve giysi ihtiyacimiz var soguktan donuyoruz",
    "Cadir ve barinma malzemesi lazim disarida kaldik",
    "Is makinesi ve jenerator lazim molozu kaldiramiyoruz",
    "Elektrik yok jenerator ve yakit ihtiyaci var",
    "Tuvalet ve hijyen malzemesi ihtiyacimiz var",
    "Sadece bilgi almak istiyorum tesekkur ederim",
    "Komsumuzu merak ediyorum haber alamiyoruz",
]

OUT = Path(__file__).resolve().parent / "text_category_cache.json"


def main():
    clf = DisasterClassifier()
    cache = {}
    for text in TEXT_POOL:
        cat, score = clf.classify(text)
        cache[text] = {"category": cat, "score": float(score)}
        print(f"{text!r} -> {cat} ({score:.3f})")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"\nKaydedildi: {OUT}")


if __name__ == "__main__":
    main()
