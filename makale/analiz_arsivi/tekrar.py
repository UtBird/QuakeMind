# -*- coding: utf-8 -*-
"""Belge ici tekrar taramasi: ayni cumle ya da cok benzer paragraf iki yerde mi?

BU BIR INTIHAL TARAMASI DEGILDIR. Disaridan kopyalanmis metni bulmaz; yalnizca
makalenin KENDI ICINDE yinelenen cumleleri ve birbirine cok benzeyen
paragraflari cikarir. Gercek intihal taramasi iThenticate/Turnitin ister.

Iki olcum:
  1) BIREBIR CUMLE TEKRARI -- normallestirilmis (kucuk harf, noktalama ve
     bosluk sadelestirilmis) cumle iki ya da daha cok yerde geciyorsa.
  2) YAKIN PARAGRAF -- paragraf ciftleri 5-gram Jaccard benzerligiyle
     karsilastirilir; esigin ustundekiler listelenir.

Elenenler: kaynakca girdileri, tablo/sekil altyazilari, kisa cumleler
(varsayilan 60 karakterden kisa), yalnizca sayi/simge iceren satirlar.
Bunlarin tekrari dogaldir ve bulgu degildir.

Kosum:
    python makale/analiz_arsivi/tekrar.py [docx yolu] [--esik 0.55] [--uzunluk 60]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
import zipfile
from collections import defaultdict


def belge_metni(yol: str) -> str:
    xml = zipfile.ZipFile(yol).read("word/document.xml").decode("utf-8")
    ham = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", ham)


def turkce_kucuk(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def normalle(s: str) -> str:
    s = turkce_kucuk(s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[^\w\s]", " ", s)      # noktalama
    s = re.sub(r"\d+[,.]?\d*", "#", s)  # sayilar tek simgeye: "2,35" ve "3,82" ayni sayilmasin diye DEGIL,
    return re.sub(r"\s+", " ", s).strip()  # sadece bicimsel farki silmek icin


def cumleler(metin: str):
    """(cumle, kaynak satir) ciftleri. Kaynakca ve altyazilar elenir."""
    for satir in metin.split("\n"):
        s = satir.strip()
        if not s:
            continue
        if re.match(r"^\[\d+\]", s):                      # kaynakca
            continue
        if re.match(r"^(Tablo|Şekil|Denklem)\s*\(?\d+", s):  # altyazi
            continue
        for c in re.split(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])", s):
            c = c.strip()
            if c:
                yield c, s


def ngramlar(s: str, n: int = 5):
    k = normalle(s).split()
    return {" ".join(k[i:i + n]) for i in range(max(0, len(k) - n + 1))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="?", default=None)
    ap.add_argument("--esik", type=float, default=0.55, help="yakin paragraf Jaccard esigi")
    ap.add_argument("--uzunluk", type=int, default=60, help="en kisa cumle uzunlugu (karakter)")
    a = ap.parse_args()

    yol = a.docx
    if not yol:
        kok = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        yol = os.path.join(kok, "makale",
                           "QuakeMind_Makale_Taslak_2026-09-16_sekillieklendi_v3_LOCAL_2026-09-21.docx")
    metin = belge_metni(yol)
    print(f"belge: {os.path.basename(yol)}  ({len(metin)} karakter)\n")

    # --- 1) birebir cumle tekrari ---
    kova = defaultdict(list)
    for c, _ in cumleler(metin):
        if len(c) < a.uzunluk:
            continue
        kova[normalle(c)].append(c)
    tekrar = {k: v for k, v in kova.items() if len(v) > 1}
    print(f"=== 1. BIREBIR CUMLE TEKRARI (>= {a.uzunluk} karakter) ===")
    print(f"  incelenen cumle: {sum(len(v) for v in kova.values())} | yinelenen kalip: {len(tekrar)}\n")
    for k, v in sorted(tekrar.items(), key=lambda x: -len(x[0]))[:25]:
        print(f"  {len(v)}x ({len(v[0])} krk): {v[0][:190]}")

    # --- 2) yakin paragraf ---
    paragraflar = [s.strip() for s in metin.split("\n")
                   if len(s.strip()) >= 200 and not re.match(r"^(\[\d+\]|Tablo|Şekil)", s.strip())]
    gramlar = [ngramlar(p) for p in paragraflar]
    print(f"\n=== 2. YAKIN PARAGRAF (5-gram Jaccard >= {a.esik}) ===")
    print(f"  incelenen paragraf: {len(paragraflar)}\n")
    bulunan = 0
    for i in range(len(paragraflar)):
        if not gramlar[i]:
            continue
        for j in range(i + 1, len(paragraflar)):
            if not gramlar[j]:
                continue
            ortak = len(gramlar[i] & gramlar[j])
            if not ortak:
                continue
            benzerlik = ortak / len(gramlar[i] | gramlar[j])
            if benzerlik >= a.esik:
                bulunan += 1
                print(f"  benzerlik {benzerlik:.2f}")
                print(f"    A: {paragraflar[i][:150]}")
                print(f"    B: {paragraflar[j][:150]}\n")
    if not bulunan:
        print("  esigi asan paragraf cifti yok.")
    print("\nNOT: Bu tarama INTIHAL taramasi degildir; yalnizca belge ici tekrari gosterir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
