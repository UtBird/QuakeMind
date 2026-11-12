# -*- coding: utf-8 -*-
"""Revizyon 18: Tablo 1'e KATE-PD ve KATE-CD satirlari; §2.1 cumlesi uyumlandi.

Sorun: Tablo 1 ("Afet sonrasi hasar degerlendirme veri kumelerinin
karsilastirmasi") Turkiye'ye ozgu kumeleri sayiyor (TUE-CD, TE23D) ama bu
calismanin bolutleme bileseninin EGITILDIGI iki kumeyi -- KATE-PD ve KATE-CD --
saymiyordu. Kumeler makalenin baska yerlerinde isleniyor (Tablo 2, Bolum 3.2.1,
Bolum 4.2, Veri Erisilebilirligi, kaynak [56]); eksik olan yalniz bu tabloydu.

Hucre degerlerinin kaynagi (hicbiri kestirim degil):
  yil 2025          <- kaynak [56] (Musaoglu vd., J. Appl. Remote Sens. 19(4))
  832 karo          <- Bolum 3.2.1 ve Bolum 4.2
  486 cift          <- Bolum 3.2.1 ve Bolum 4.2
  Maxar / Pleiades  <- Bolum 3.2.1 ("Maxar 193, Airbus Pleiades 639 karo")
  sinif sayisi 2    <- OLCULDU. Yereldeki KATE-PD maskeleri
                       (QuakeMindBackend/benchmark/reports/kate_pd_*_mask.png)
                       ikili: piksellerin %98,6-99,2'si <= 10, %0,7-1,3'u >= 245,
                       arada kalan %0,1 kenar sikistirma artigi. Veri kartindaki
                       `label` alani da YOLO cokgen biciminde ve sinif kimligi
                       hep 0 (tek nesne sinifi). KATE-CD icin makale zaten
                       "elle cizilmis IKILI hasar maskeleri" diyor.

Ayrica §2.1'deki "TUE-CD ve TE23D one cikmaktadir" cumlesi tabloyla celisiyordu
(tabloda dort Turkiye kumesi olacak, metinde iki tanesi sayiliyor); cumle ve
devamindaki "Her iki kume de" ifadesi duzeltildi.

Koşum:  python makale/analiz_arsivi/revize18.py
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
                   "QuakeMind_Makale_YEDEK_pre_revize18_2026-09-29.docx")

# Yedek yoksa guncel dosyadan alinir (devir belgesi Bolum 3'teki uyari).
os.makedirs(os.path.dirname(SRC), exist_ok=True)
if not os.path.exists(SRC):
    shutil.copyfile(DST, SRC)
    print(f"yedek alindi: {os.path.basename(SRC)}")
else:
    shutil.copyfile(SRC, DST)
    print(f"yedekten baslatildi: {os.path.basename(SRC)}")

doc = Document(DST)
D = Duzenleyici(doc)


def deg(eski, yeni):
    n = D.degistir(eski, yeni)
    if not n:
        raise SystemExit(f"BULUNAMADI: {eski[:80]}")
    return n


# --- 1. Tablo 1'i bul (icerikten; tablo indisleri surum surum kayiyor) -------
t1 = None
for t in doc.tables:
    basliklar = [c.text.strip() for c in t.rows[0].cells]
    ilk_sutun = [r.cells[0].text.strip() for r in t.rows]
    if basliklar[:2] == ["Veri kümesi", "Kaynak"] and any(s.startswith("xBD") for s in ilk_sutun):
        t1 = t
        break
if t1 is None:
    raise SystemExit("Tablo 1 bulunamadi")

mevcut = [r.cells[0].text.strip() for r in t1.rows]
print("Tablo 1 satirlari:", mevcut)
if any(s.startswith("KATE") for s in mevcut):
    raise SystemExit("KATE satirlari zaten var -- betik iki kez kosulmus olabilir")

# TE23D son uydu tabanli Turkiye kumesi; KATE'ler onun ARKASINA, insansiz hava
# araci / sosyal medya satirlarindan ONCE girer (tablo bu sirayi izliyor).
te23d_idx = [i for i, s in enumerate(mevcut) if s.startswith("TE23D")][0]

D.satir_ekle(t1, te23d_idx, [
    "KATE-PD", "[56]", "2025", "Çok yüksek çözünürlüklü uydu (Maxar, Pléiades)",
    "Bina hasarı bölütlemesi", "832", "2"])
# satir_ekle kaynak satirin ARKASINA ekler; KATE-CD'yi KATE-PD'nin arkasina al
D.satir_ekle(t1, te23d_idx + 1, [
    "KATE-CD", "[56]", "2025", "Çok yüksek çözünürlüklü uydu (Maxar, Pléiades)",
    "Bina hasarı değişim tespiti", "486 çift", "2"])
D.tablo_bicimle(t1)
print("Tablo 1 satirlari (sonra):", [r.cells[0].text.strip() for r in t1.rows])

# --- 2. Tablo 1 altyazisi: kumelerin hangisinin egitimde kullanildigi ---------
deg("Tablo 1. Afet sonrası hasar değerlendirme veri kümelerinin karşılaştırması.",
    "Tablo 1. Afet sonrası hasar değerlendirme veri kümelerinin karşılaştırması. "
    "KATE-PD ve KATE-CD, bu çalışmadaki hasar bölütleme bileşeninin eğitim ve "
    "sınama verisidir (Bölüm 3.2.1 ve 4.2); diğerleri yalnız yazın karşılaştırması "
    "için anılmaktadır.")

# --- 3. §2.1: cumle tabloyla celisiyordu -------------------------------------
deg("Türkiye'ye özgü kıyaslama veri kümeleri bakımından TUE-CD [10] ve TE23D [11] "
    "öne çıkmaktadır.",
    "Türkiye'ye özgü kıyaslama veri kümeleri bakımından TUE-CD [10], TE23D [11] ve "
    "bu çalışmanın eğitim verisini oluşturan KATE-PD ile KATE-CD [56] öne çıkmaktadır.")

deg("TUE-CD, çok ölçekli etkileşim ağı ve kayma kalibrasyonu ile bina değişim "
    "tespitine odaklanırken, TE23D 2023 depremleri için hasar değerlendirme ve "
    "değerlendirme protokolü sunmaktadır.",
    "TUE-CD, çok ölçekli etkileşim ağı ve kayma kalibrasyonu ile bina değişim "
    "tespitine odaklanırken, TE23D 2023 depremleri için hasar değerlendirme ve "
    "değerlendirme protokolü sunmaktadır. KATE-PD ve KATE-CD ise aynı depremlerin "
    "yedi ilini kapsayan çok yüksek çözünürlüklü uydu karolarında piksel düzeyinde "
    "hasarlı bina maskeleri sunar; bu çalışmanın bölütleme bileşeni bu iki kümeyle "
    "eğitilmiştir (Bölüm 3.2.1 ve 4.2).")

deg("Her iki küme de bina/enkaz hasarı odaklıdır (TE23D enkaz alanı etiketiyle); "
    "yol ağı hasarını piksel düzeyinde etiketleyen Türkiye kaynaklı bir küme yazında "
    "bulunmamaktadır.",
    "Bu kümelerin tümü bina/enkaz hasarı odaklıdır (TE23D enkaz alanı etiketiyle); "
    "yol ağı hasarını piksel düzeyinde etiketleyen Türkiye kaynaklı bir küme yazında "
    "bulunmamaktadır.")

D.kalinlik_duzelt()
doc.save(DST)
print("\n--- yapilanlar ---")
for s in D.log:
    print("  ", s)
print(f"\nkaydedildi: {DST}")
