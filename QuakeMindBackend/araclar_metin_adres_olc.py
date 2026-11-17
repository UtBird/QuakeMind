# -*- coding: utf-8 -*-
"""Metin analizinin adres bulma, kategori ve sure olcumu (J-170).

Kume: `apps/disaster_nlp/data/metin_adres_kumesi.json` -- SENTETIK, etiketli:
tatbikat ihbarlari (27 Eylul, elle yazildi) ve konsol/afetzede ekranlarindaki
ornek cumleler. Her kaydin beklenen kategorisi yazarin niyetidir; beklenen
adresi metinde gecen gercek yer adidir (OSM'deki mahalle/sokak). Dis servise
(Nominatim) ISTEK GITMEZ: cagri sayilir ve basarisiz sayilir, cunku hedef
internetsiz ve adres disari cikmadan calismak.

Olculenler (her kayit icin):
  * kategori dogru mu (yazarin niyetiyle ortusme; dogruluk degil, ortusme)
  * adres bulundu mu ve beklenen yer adini iceriyor mu
  * koordinat beklenen yere ne kadar uzak (yer adi kumede koordinatliysa)
  * Nominatim'e gidilmeye calisildi mi
  * sure: model yukleme (soguk) ve istek basina (sicak)

    python araclar_metin_adres_olc.py --cikti benchmark/reports/metin_adres_taban.json [--yeni]
`--yeni`: yeni hatti (metin_analizi paketi) olcer; yoksa eski DisasterPipeline.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent
NLP = KOK / "apps" / "disaster_nlp"


def _mesafe_m(a, b):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def _norm(s):
    return str(s or "").casefold().replace("ı", "i").replace("İ".casefold(), "i")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--yeni", action="store_true")
    a = ap.parse_args()

    kume = json.loads((NLP / "data" / "metin_adres_kumesi.json").read_text(encoding="utf-8"))
    kayitlar = kume["kayitlar"]

    nominatim = {"cagri": 0}
    t0 = time.perf_counter()
    if a.yeni:
        sys.path.insert(0, str(KOK))
        from metin_analizi import MetinAnalizci  # noqa: E402

        analizci = MetinAnalizci()
        analizci.isit()

        def coz(metin):
            r = analizci.coz(metin)
            return {"kategori": r["kategori"], "konum": r["konum"], "konum_metin": r["konumMetin"],
                    "duzey": r.get("konumDuzeyi")}
    else:
        import os

        os.chdir(NLP)
        sys.path.insert(0, str(NLP))
        from src import ner_extraction  # noqa: E402
        from src.pipeline import DisasterPipeline  # noqa: E402

        p = DisasterPipeline()

        def sahte_geocode(*_a, **_k):
            nominatim["cagri"] += 1
            return None

        p.ner_extractor.geocode = sahte_geocode
        # Onbellek dosyasi da kullanilmaz: olcum dis servisin daha once verdigi
        # cevaplara yaslanmasin.
        ner_extraction._geocache = {}
        ner_extraction._geocache_put = lambda *_a, **_k: None

        def coz(metin):
            r = p.process_tweet(metin)
            if r is None:
                return {"kategori": "Alakasız", "konum": None, "konum_metin": None, "duzey": None}
            return {"kategori": r["kategori"], "konum": r["konum"], "konum_metin": r["konum_metin"], "duzey": None}

    yukleme_sn = time.perf_counter() - t0

    satirlar, sureler = [], []
    for k in kayitlar:
        once = nominatim["cagri"]
        t = time.perf_counter()
        r = coz(k["metin"])
        sureler.append((time.perf_counter() - t) * 1000)
        beklenen_yer = k.get("beklenenYer")
        bulunan = r["konum_metin"]
        yer_tuttu = bool(beklenen_yer and bulunan and _norm(beklenen_yer) in _norm(bulunan))
        uzaklik = None
        if r["konum"] and k.get("beklenenKonum"):
            uzaklik = round(_mesafe_m(r["konum"], k["beklenenKonum"]))
        satirlar.append({
            "metin": k["metin"],
            "beklenenKategori": k["beklenenKategori"],
            "kategori": r["kategori"],
            "kategoriOrtusuyor": r["kategori"] == k["beklenenKategori"],
            "beklenenYer": beklenen_yer,
            "bulunanAdres": bulunan,
            "duzey": r["duzey"],
            "yerTuttu": yer_tuttu,
            "uzaklikM": uzaklik,
            "nominatimCagrisi": nominatim["cagri"] - once,
            "sureMs": round(sureler[-1], 1),
        })

    adresli = [s for s in satirlar if s["beklenenYer"]]
    yakin = [s for s in adresli if s["uzaklikM"] is not None and s["uzaklikM"] <= 1500]
    rapor = {
        "kume": "apps/disaster_nlp/data/metin_adres_kumesi.json (SENTETIK, etiketli)",
        "hat": "yeni (metin_analizi)" if a.yeni else "eski (DisasterPipeline, Nominatim kapali)",
        "kayit": len(satirlar),
        "modelYuklemeSn": round(yukleme_sn, 1),
        "istekMsOrtanca": round(st.median(sureler), 1),
        "istekMsEnCok": round(max(sureler), 1),
        "kategoriOrtusme": f"{sum(s['kategoriOrtusuyor'] for s in satirlar)}/{len(satirlar)}",
        "adresBekleyen": len(adresli),
        "beklenenYerAdiBulundu": f"{sum(s['yerTuttu'] for s in adresli)}/{len(adresli)}",
        "koordinat1500mIcinde": f"{len(yakin)}/{len(adresli)}",
        "nominatimeGidecekti": sum(1 for s in satirlar if s["nominatimCagrisi"]),
        "satirlar": satirlar,
    }
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    Path(a.cikti).write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rapor.items() if k != "satirlar"}, ensure_ascii=False, indent=1))
    for s in satirlar:
        print(("OK " if s["kategoriOrtusuyor"] else "-- ") + ("ADR " if s["yerTuttu"] else "--- ")
              + f"{s['kategori'][:18]:18} | {str(s['bulunanAdres'])[:40]:40} | {s['metin'][:60]}")


if __name__ == "__main__":
    main()
