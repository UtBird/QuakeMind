# -*- coding: utf-8 -*-
"""Metin siniflandirma katmaninin karar sirasi (J-111/J-116).

Model yuklenmez: siniflandiriciya sabit skorlar donduren sahte bir islev
verilir. Boylece yalniz P-5 katmaninin mantigi sinanir.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "disaster_nlp"))

from src import classification as c  # noqa: E402


def _siniflandirici(skorlar):
    s = c.DisasterClassifier.__new__(c.DisasterClassifier)
    s.classifier = lambda _metin: [[{"label": k, "score": v} for k, v in skorlar.items()]]
    return s


def test_anahtar_sozcuk_emin_modeli_ezmez():
    """Model 'Enkaz Kaldirma' diyor (%97); 'ekip lazım' onu Acil Yardım'a cevirmemeli."""
    s = _siniflandirici({"Enkaz Kaldirma": 0.97, "Arama Ekipmani": 0.40})
    d = s.classify_detay("bina tamamen çöktü, enkaz altından ses geliyor acil ekip lazım")
    print("  ", d)
    assert d["kategori"] == "Enkaz Bildirimi" and d["kaynak"] == "model"
    assert abs(d["guven"] - 0.97) < 1e-9


def test_arac_sozcugu_ac_ile_eslesmez():
    """'araç' icindeki 'aç' eskiden Acil Yardım'a kurtarıyordu."""
    s = _siniflandirici({"Alakasiz": 0.20, "Lojistik": 0.15})
    d = s.classify_detay("ağır araç geçemiyor, köprü kapalı")
    print("  ", d)
    assert d["kategori"] == "Yol Kapanma Bilgisi / Lojistik", d
    assert not c.anahtar_eslesir(c._sozcukler("ağır araç geldi"), "aç kaldık")


def test_yol_yollayin_ile_eslesmez():
    assert not c.anahtar_eslesir(c._sozcukler("battaniye yollayın"), "yol")
    assert c.anahtar_eslesir(c._sozcukler("yolda enkaz var"), "yolda")
    assert c.anahtar_eslesir(c._sozcukler("enkazda ses var"), "enkaz")   # uzun anahtar: ek alir


def test_turkce_buyuk_I():
    """'Isınamıyoruz' str.lower() ile 'isınamıyoruz' olur ve eslesmezdi."""
    assert c.anahtar_eslesir(c._sozcukler("Isınamıyoruz, çadır yok"), "ısınamıyoruz")


def test_alakasiz_dense_de_hayati_ihbar_kurtarilir():
    """E-04 amaci korunur: model 'Alakasiz' dese de hayati ihbar elenmez."""
    s = _siniflandirici({"Alakasiz": 0.80, "Saglik": 0.12})
    d = s.classify_detay("annem yaralı kanama durmuyor ambulans lazım")
    print("  ", d)
    assert d["kategori"] == "Acil Yardım İhtiyacı" and d["kaynak"] == "anahtar_sozcuk"
    # gosterilen guven gosterilen kategoriye ait (Saglik -> Acil Yardım), %50'ye sisirilmez
    assert abs(d["guven"] - 0.12) < 1e-9


def test_kurtarilamayan_kararsiz_belirsiz():
    s = _siniflandirici({"Yemek": 0.21, "Alakasiz": 0.19})
    d = s.classify_detay("burada durum nasıl bilmiyoruz")
    assert d["kategori"] == "Belirsiz" and d["kaynak"] == "belirsiz"


def test_lojistik_dali_calisir():
    """Model 'Lojistik' dediginde ulasim sozcugu varsa Yol Kapanma (eskiden olu kod)."""
    s = _siniflandirici({"Lojistik": 0.70})
    assert s.classify_detay("iş makinesi giremiyor yol kapalı")["kategori"] == "Yol Kapanma Bilgisi / Lojistik"
    assert s.classify_detay("jeneratör ve malzeme gönderin lütfen")["kategori"] == "Lojistik İhtiyaç Bildirimi"


if __name__ == "__main__":
    for ad, f in sorted(globals().items()):
        if ad.startswith("test_"):
            print(f"{ad}:")
            f()
            print("   GECTI")
