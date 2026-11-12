# -*- coding: utf-8 -*-
"""Revizyon 19: Tablo 15'in Turkce metin gecikmesi duzeltilmis kodla yeniden olculdu (J-133).

Sorun: Tablo 15'in metin satiri KARISIK KOKENLIYDI. Ortusme (11/18) J-111/J-116
duzeltmesinden SONRAKI siniflandiriciya aitti ama gecikme (medyan 36,6 / en uzun
43,0 ms) duzeltme ONCESINDEN kalmisti; hucredeki not da bunu soyluyordu
("gecikme duzeltme oncesi olculdu").

Olcum (29 Eylul 2026, Tablo 11'in birinci sutunundaki i7-12700H makinesi,
duzeltilmis kodla, `araclar_kanal_olc.py --yalniz-metin`):

  kararli kosumlar : 47,8 · 47,8 · 48,5 · 48,5 · 48,2 ms  -> medyan 48,2 ± 0,3
  en uzun          : 52,0 - 58,9 ms
  SOGUK BASLANGIC  : ilk kosum 62,3 / 77,6 ms verdi. Aracin kendi isinma cagrisi
                     soguk baslangici kapatmiyor; raporlanan deger kararli
                     banttir ve bu, hucredeki nota yazildi.

Rapor: QuakeMindBackend/benchmark/reports/kanal_olcumu_metin_i7.json

Kosum:  python makale/analiz_arsivi/revize19.py
"""
import os
import shutil
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
from docx import Document  # noqa: E402
from yardimci import Duzenleyici  # noqa: E402

KOK = os.path.dirname(os.path.dirname(BURASI))
DST = os.path.join(KOK, "makale",
                   "QuakeMind_Makale_Taslak_2026-09-16_sekillieklendi_v3_LOCAL_2026-09-21.docx")
SRC = os.path.join(KOK, "makale", "arsiv",
                   "QuakeMind_Makale_YEDEK_pre_revize19_2026-09-29.docx")

os.makedirs(os.path.dirname(SRC), exist_ok=True)
if not os.path.exists(SRC):
    shutil.copyfile(DST, SRC)
    print(f"yedek alindi: {os.path.basename(SRC)}")
else:
    shutil.copyfile(SRC, DST)
    print(f"yedekten baslatildi: {os.path.basename(SRC)}")

doc = Document(DST)
D = Duzenleyici(doc)

# --- 1. Tablo 15'in Turkce metin satiri --------------------------------------
t15 = None
for t in doc.tables:
    bas = [c.text.strip() for c in t.rows[0].cells]
    if bas[:3] == ["Kanal", "Model", "n"] and any(
            r.cells[0].text.strip() == "Türkçe metin" for r in t.rows):
        t15 = t
        break
if t15 is None:
    raise SystemExit("Tablo 15 bulunamadi")

satir = next(r for r in t15.rows if r.cells[0].text.strip() == "Türkçe metin")
onceki = [c.text.strip() for c in satir.cells]
print("once :", onceki)
if onceki[3] != "36,6":
    raise SystemExit(f"beklenmeyen medyan hucresi: {onceki[3]!r} -- betik iki kez kosulmus olabilir")

D.hucre_yaz(satir.cells[3], "48,2")
D.hucre_yaz(satir.cells[4], "58,9")
D.hucre_yaz(satir.cells[6],
            "doğruluk değil; etiketli küme gerekir; beş koşumun medyanı "
            "(47,8–48,5), soğuk başlangıç koşumu hariç")
print("sonra:", [c.text.strip() for c in satir.cells])
D.tablo_bicimle(t15)

# --- 2. Govde cumlesi ---------------------------------------------------------
n = D.degistir(
    "Metin kanalında 18 ihbar metninin sınıflandırma medyanı 36,6 ms, en uzunu 43,0 ms'dir "
    "(gecikme, sınıflandırma katmanı düzeltilmeden önce ölçülmüştür; Bölüm 3.6); düzeltilmiş "
    "katmanla metinlerin on biri yazarın niyetiyle örtüşmüş",
    "Metin kanalında 18 ihbar metninin sınıflandırma medyanı 48,2 ms, en uzunu 58,9 ms'dir "
    "(düzeltilmiş sınıflandırma katmanıyla, beş koşumun medyanı 47,8–48,5 ms; ilk koşum soğuk "
    "başlangıç nedeniyle 62,3 ms verdiği için raporlanan değer kararlı banttır); aynı katmanla "
    "metinlerin on biri yazarın niyetiyle örtüşmüş")
if not n:
    raise SystemExit("govde cumlesi bulunamadi")

# --- 3. Tablo 15 altyazisina olcum ortami -------------------------------------
D.degistir(
    "Tablo 15. Tatbikat kanallarının ölçümü — kamera (YOLO) ve metin (BERTurk). Değerler tespit "
    "sayısı ve gecikmedir; doğruluk (mAP, F₁) değildir.",
    "Tablo 15. Tatbikat kanallarının ölçümü — kamera (YOLO) ve metin (BERTurk). Değerler tespit "
    "sayısı ve gecikmedir; doğruluk (mAP, F₁) değildir. Gecikmeler Tablo 11'in birinci "
    "sütunundaki dizüstü bilgisayarda, grafik işlemci hızlandırması olmadan ölçülmüştür.")

D.kalinlik_duzelt()
doc.save(DST)
print("\n--- yapilanlar ---")
for s in D.log:
    print("  ", s)
print(f"\nkaydedildi: {DST}")
