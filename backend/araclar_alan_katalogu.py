# -*- coding: utf-8 -*-
"""Tatbikat alan katalogunu OLCEREK uretir (elle bbox yazilmaz).

Her acik drone sahnesi icin:
  1) sahnenin kendi kapsamini (OAM bbox) kaba bir zoom'da indirir,
  2) ucus izinin GERCEKTEN dolu oldugu en iyi ~`--pencere-m` metrelik kareyi arar,
  3) o karede OSM yol agi ve gercek tesis (ekip ussu) var mi diye bakar,
  4) `uclar/simulasyon.py` ALANLAR girdisini basar.

Neden gerekli: drone mozaiginin OAM kutusu butun ucus zarfidir; icinin buyuk
bolumu siyahtir. Kutuyu elle yazmak "goruntunun %61'i bos" durumunu (J-65)
yeniden uretir. Pencere olculerek secilince analiz hep dolu alanda kosar.
"""
import argparse
import json
import math
import time
import sys

import numpy as np

sys.path.insert(0, ".")
from apps.road_damage.utils.fetcher import (  # noqa: E402
    fetch_satellite_area,
    get_osm_roads_overpass,
    search_oam_images,
)

# Aranacak gercek sahneler: baslikta gecen ayirt edici parca -> (il, ilce/mahalle)
HEDEF_SAHNELER = [
    ("Defne - Elektrik",        "Hatay",         "Defne / Elektrik Mah."),
    ("Narlica Ortaokulu",       "Hatay",         "Antakya / Narlıca (ortaokul çevresi)"),
    ("Hatay - Narlica",         "Hatay",         "Antakya / Narlıca"),
    ("Mansurlu",                "Hatay",         "Antakya / Mansurlu"),
    ("Turinclu",                "Hatay",         "Antakya / Türünçlü – Akdeniz – Armutlu"),
    ("Islahiye",                "Gaziantep",     "İslahiye"),
    ("Nurdagi",                 "Gaziantep",     "Nurdağı"),
    ("Sekeroba Flight 1",       "Kahramanmaraş", "Şekeroba (kuzeybatı)"),
    ("Sekeroba Flight 4",       "Kahramanmaraş", "Şekeroba (orta)"),
    ("Gokcedere",               "Gaziantep",     "Gökçedere"),
    ("Stadyumu",                "Kahramanmaraş", "Merkez / Şubat Stadyumu çevresi"),
]
BOLGE_KUTUSU = (35.9, 36.0, 38.6, 38.6)   # butun deprem bolgesi


def _pencere_ara(img, bounds, pencere_px, adim_px):
    """Gecerli (siyah olmayan) piksel orani en yuksek kareyi bul."""
    a = np.asarray(img.convert("RGB")).mean(axis=2)
    gecerli = (a > 12).astype(np.float32)
    H, W = gecerli.shape
    if H < pencere_px or W < pencere_px:
        return None
    # toplam alan tablosu: her pencerenin dolulugu O(1)
    bt = gecerli.cumsum(0).cumsum(1)
    bt = np.pad(bt, ((1, 0), (1, 0)))
    en_iyi = None
    for y in range(0, H - pencere_px + 1, adim_px):
        for x in range(0, W - pencere_px + 1, adim_px):
            s = (bt[y + pencere_px, x + pencere_px] - bt[y, x + pencere_px]
                 - bt[y + pencere_px, x] + bt[y, x])
            oran = s / (pencere_px * pencere_px)
            if en_iyi is None or oran > en_iyi[0]:
                en_iyi = (float(oran), x, y)
    if en_iyi is None:
        return None
    oran, x, y = en_iyi
    bati, guney, dogu, kuzey = bounds
    d_lon, d_lat = (dogu - bati) / W, (kuzey - guney) / H
    return {
        "doluluk": round(oran, 3),
        "bbox": [round(bati + x * d_lon, 6), round(kuzey - (y + pencere_px) * d_lat, 6),
                 round(bati + (x + pencere_px) * d_lon, 6), round(kuzey - y * d_lat, 6)],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pencere-m", type=float, default=500.0)
    ap.add_argument("--en-az-pencere-m", type=float, default=250.0,
                    help="bundan dar mozaik alan olarak kullanilmaz")
    ap.add_argument("--tarama-zoom", type=int, default=16)
    ap.add_argument("--cikti", default="alan_katalogu.json")
    ap.add_argument("--yalniz", help="yalniz basliginda bu parca gecen sahne")
    a = ap.parse_args()

    sahneler = search_oam_images(BOLGE_KUTUSU, "2023-02-06", "2023-03-15", limit=200)
    print(f"OAM: {len(sahneler)} sahne tarandi\n")
    katalog = []
    for parca, il, yer in HEDEF_SAHNELER:
        if a.yalniz and a.yalniz.lower() not in parca.lower():
            continue
        eslesen = [s for s in sahneler if parca.lower() in (s.get("title") or "").lower()]
        if not eslesen:
            print(f"[ATLANDI] {parca}: OAM'de bulunamadi")
            continue
        # Birden cok sahne eslesirse EN KISA basligi sec: "Hatay - Narlica"
        # hem kendi sahnesine hem "Hatay - Narlica Ortaokulu ..."ya uyuyordu ve
        # katalogda AYNI alan iki kez cikiyordu (olculdu).
        eslesen.sort(key=lambda x: len((x.get("title") or "").strip()))
        s = eslesen[0]
        if len(eslesen) > 1:
            print(f"   (\"{parca}\" {len(eslesen)} sahneyle eslesti; en dar baslik secildi)")
        kutu = s.get("bbox")
        if not kutu or len(kutu) != 4:
            print(f"[ATLANDI] {parca}: bbox yok")
            continue
        merkez_lat = (kutu[1] + kutu[3]) / 2
        gsd = 156543.03392 * math.cos(math.radians(merkez_lat)) / (2 ** a.tarama_zoom)
        pencere_px = max(16, int(round(a.pencere_m / gsd)))
        # PENCERE UYARLANABILIR. Zoom artirmak ISE YARAMIYOR: fetch_satellite_area
        # karo sayisini sinirladigi icin zoom buyudukce kapsanan ALAN kuculuyor
        # (olculdu: ayni sahne z16'da 494 m, z18'de 247 m genis). Dar mozaiklerde
        # (Narlica, Turinclu) 500 m'lik pencere hicbir zoom'da sigmiyordu ve
        # sahne sessizce dusuyordu. Cozum: pencereyi goruntuye gore KUCULT ve
        # gercek boyutu kunyeye yaz -- alanlar ayni buyuklukte degilse bu
        # raporda gorunur, gizlenmez.
        a_zoom = a.tarama_zoom
        gsd = 156543.03392 * math.cos(math.radians(merkez_lat)) / (2 ** a_zoom)
        try:
            img, bounds = fetch_satellite_area(
                None, None, bbox=tuple(kutu), zoom_level=a_zoom,
                provider="custom", custom_url=s["tms_url"] + "/{z}/{x}/{y}.png")
        except Exception as e:
            print(f"[ATLANDI] {parca}: goruntu alinamadi ({type(e).__name__})")
            continue
        if img is None:
            print(f"[ATLANDI] {parca}: goruntu bos")
            continue
        istenen_px = max(16, int(round(a.pencere_m / gsd)))
        sigan_px = int(min(img.size) * 0.95)
        pencere_px = min(istenen_px, sigan_px)
        pencere_m = pencere_px * gsd
        if pencere_m < a.en_az_pencere_m:
            print(f"[ATLANDI] {parca}: mozaik cok dar "
                  f"({img.size} px @ z{a_zoom} -> en fazla {pencere_m:.0f} m, "
                  f"taban {a.en_az_pencere_m:.0f} m)")
            continue
        p = _pencere_ara(img, bounds, pencere_px, max(4, pencere_px // 10))
        if p is None:
            print(f"[ATLANDI] {parca}: pencere aranamadi")
            continue
        if pencere_px < istenen_px:
            print(f"   (pencere {a.pencere_m:.0f} m yerine {pencere_m:.0f} m -- mozaik dar)")
        # o pencerede OSM yolu var mi?
        # Overpass dusunce yol orani 0.0 gorunuyordu; bu "yol yok" degil "katman
        # alinamadi" demek (J-68 ile ayni tuzak). Uc deneme, arada bekleme.
        yol_orani = None
        for deneme in range(3):
            try:
                yol = get_osm_roads_overpass(tuple(p["bbox"]), 256, 256, thickness=3)
                oran = float((yol > 0).mean())
                if oran > 0:
                    yol_orani = round(oran, 4)
                    break
            except Exception:
                pass
            time.sleep(4)
        # ANALIZ ZOOM'UNDAKI gecerli piksel orani. Tarama zoom'undaki doluluk
        # ayni sey DEGIL: pencere z16'da secilir, analiz z18'de kosar ve oran
        # farkli cikar (olculdu: Defne %59 -> %39). "Goruntu eksik indi" kontrolu
        # bu degeri referans alir; yanlisini alirsa saglam kosuyu reddeder.
        gecerli_z18 = None
        try:
            _a18, _b18 = fetch_satellite_area(
                None, None, bbox=tuple(p["bbox"]), zoom_level=18,
                provider="custom", custom_url=s["tms_url"] + "/{z}/{x}/{y}.png")
            if _a18 is not None:
                _g = np.asarray(_a18.convert("L"))
                gecerli_z18 = round(float((_g > 12).mean()), 4)
        except Exception:
            pass

        print(f"[{parca}] {il} / {yer}")
        print(f"   sahne     : {s['title'].strip()}  ({s['date'][:10]}, {s.get('provider')})")
        print(f"   kapsam    : {img.size} px @ z{a_zoom} (GSD {gsd:.1f} m)")
        print(f"   en iyi kare: doluluk %{p['doluluk']*100:.0f}"
              f"  (z18 gecerli %{gecerli_z18*100:.0f})" if gecerli_z18 is not None else ""
              f"  bbox {p['bbox']}  yol orani {yol_orani}")
        katalog.append({
            "parca": parca, "il": il, "yer": yer,
            "sahneAdi": s["title"].strip(), "tarih": s["date"][:10],
            "saglayici": s.get("provider"), "tmsUrl": s["tms_url"],
            "oamBbox": kutu, "analizBbox": p["bbox"], "doluluk": p["doluluk"],
            "osmYolOrani": yol_orani, "taramaZoom": a_zoom,
            "gecerliPikselOraniZ18": gecerli_z18,
            "pencereM": round(pencere_m, 1),
            "merkez": {"lat": round((p["bbox"][1] + p["bbox"][3]) / 2, 6),
                       "lon": round((p["bbox"][0] + p["bbox"][2]) / 2, 6)},
        })
    json.dump(katalog, open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(katalog)} alan -> {a.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
