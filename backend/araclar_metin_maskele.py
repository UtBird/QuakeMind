# -*- coding: utf-8 -*-
"""Turkce ihbar metin kumesinde kisisel veri maskeleme (J-127).

deprem-private/intent_test_v13_anonymized adina karsin kisi adlari disinda maskelenmemis:
telefon numarasi, e-posta, kullanici adi ve acik adres numarasi iceren kayitlar var. Bu arac
kumenin YEREL ve maskeli bir kopyasini uretir; Hugging Face'teki asil kumeye dokunmaz, depoya
metin yazmaz (rapor yalniz sayi icerir).

Varsayilan maskeler:
  [TELEFON]   9 ya da daha cok rakamlik dizi (arada bosluk, tire, nokta, parantez olabilir;
              +90 / 0 5xx / sabit hat bicimleri dahil). Kaba ama kacirmaz: uzun sayisal kimlikleri
              de maskeler.
  [EPOSTA]    ad@alan.uzanti
  [KULLANICI] @kullanici_adi
  [URL]       http(s)://... ve www....
--adres-numarasi ile ayrica: "no: 12", "no 5", "daire 3", "kat 2", "blok A" -> [ADRES_NO].
Mahalle / sokak / cadde ADLARI maskelenmez: kumenin gorevi (konum cikarimi) bunlara dayanir;
bunlarin da gizlenmesi istenirse ayri bir karar gerekir.

    python araclar_metin_maskele.py --veri <data_cache> --cikti <depo DISI klasor> \
        [--adres-numarasi] --rapor benchmark/reports/metin_maskeleme_raporu.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DESEN = [
    ("[EPOSTA]", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("[URL]", re.compile(r"(?:https?://|www\.)\S+", re.I)),
    ("[KULLANICI]", re.compile(r"(?<![\w.])@\w{2,}")),
    # cep numarasi, gruplar arasinda tek bir yazim hatasi karakteriyle ("0535n791 23 54" gibi)
    ("[TELEFON]", re.compile(r"(?<!\d)(?:\+?90\D?)?0?5\d{2}\D?\d{3}\D?\d{2}\D?\d{2}(?!\d)")),
    ("[TELEFON]", re.compile(r"(?<!\d)(?:\+?\s?\(?\d[\s\-.()]{0,2}){9,}\d?(?!\d)")),
]
ADRES = ("[ADRES_NO]", re.compile(
    r"\b(?:no|numara|daire|d|kat|blok)\s*[:.]?\s*[0-9]+[a-zçğıöşü]?\b|\bblok\s*[:.]?\s*[a-zçğıöşü]\b", re.I))
ADRES_IZ = re.compile(r"\b(mahallesi|mah\.?|sokak|sok\.?|sk\.?|cadde(si)?|cad\.?|cd\.?|bulvar[ıi]?|apartman[ıi]?|"
                      r"apt\.?|site(si)?|no\s*[:.]?\s*\d)\b", re.I)


def maskele(metin: str, adres_numarasi: bool, sayac: dict) -> str:
    for etiket, d in DESEN + ([ADRES] if adres_numarasi else []):
        metin, n = d.subn(etiket, metin)
        sayac[etiket] = sayac.get(etiket, 0) + n
    return metin


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", required=True, help="train/val/test.parquet klasoru")
    ap.add_argument("--cikti", required=True, help="maskeli kopyanin yazilacagi klasor (DEPO DISI)")
    ap.add_argument("--adres-numarasi", action="store_true")
    ap.add_argument("--rapor", default=None, help="yalniz sayilarin yazildigi JSON")
    a = ap.parse_args()

    import pandas as pd

    cikti = Path(a.cikti).resolve()
    depo = Path(__file__).resolve().parents[1]
    if depo in cikti.parents or cikti == depo:
        raise SystemExit(f"Cikti depo icinde olamaz: {cikti} (kisisel veri iceren kume depoya girmez)")
    cikti.mkdir(parents=True, exist_ok=True)

    rapor = {"adresNumarasiMaskelendi": a.adres_numarasi, "bolmeler": {}}
    for ad in ("train", "val", "test"):
        yol = Path(a.veri) / f"{ad}.parquet"
        if not yol.exists():
            continue
        df = pd.read_parquet(yol)
        sayac: dict = {}
        once_tel = int(df["text"].astype(str).apply(lambda t: any(d.search(t) for e, d in DESEN if e == "[TELEFON]")).sum())
        df["text"] = [maskele(str(t), a.adres_numarasi, sayac) for t in df["text"]]
        if "image_url" in df.columns:
            df["image_url"] = df["text"]
        sonra_tel = int(df["text"].astype(str).apply(lambda t: any(d.search(t) for e, d in DESEN if e == "[TELEFON]")).sum())
        adresli = int(df["text"].astype(str).apply(lambda t: bool(ADRES_IZ.search(t))).sum())
        df.to_parquet(cikti / f"{ad}.parquet")
        rapor["bolmeler"][ad] = {"kayit": len(df), "telefonluKayitOnce": once_tel, "telefonluKayitSonra": sonra_tel,
                                 "maskeSayisi": sayac, "adresIziKalanKayit": adresli}
        print(f"{ad}: {len(df)} kayit | telefonlu kayit {once_tel} -> {sonra_tel} | maskeler {sayac} | "
              f"adres izi kalan kayit {adresli}")
    if a.rapor:
        Path(a.rapor).write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print("maskeli kopya:", cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
