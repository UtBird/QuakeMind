# -*- coding: utf-8 -*-
"""Bir goruntu sahnesinin OSM'e gore kaymasini OLCER (bir kez calistirilir).

Cikti, `apps/road_damage/utils/hizalama.py` icindeki tabloya elle yazilacak
kaydin ta kendisidir: boylece tablodaki her sayi tekrar uretilebilir olur
(CLAUDE.md 8 -- olcmeden iddia yok).

Kullanim:
    python araclar_hizalama_olc.py --oam-ara "elektrik" \
        --bbox 36.146753 36.195466 36.15189 36.199922

UYARI: olcut EGIK bakisli goruntude (ornegin ham Maxar karolari) yanilir --
binalar yatinca catilar sokagi ortuyor. Yalnizca DIK bakisli ortofotolarda
kullanin.
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from apps.road_damage.utils import hizalama  # noqa: E402
from apps.road_damage.utils.fetcher import (  # noqa: E402
    fetch_satellite_area,
    get_osm_roads_overpass,
    search_oam_images,
)
from apps.road_damage.utils.tiling import gsd_of_zoom  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", nargs=4, type=float, required=True,
                    metavar=("BATI", "GUNEY", "DOGU", "KUZEY"))
    ap.add_argument("--oam-ara", help="OAM sahne basliginda aranacak parca")
    ap.add_argument("--tms", help="Dogrudan karo sablonu (OAM aramasi yerine)")
    ap.add_argument("--zoom", type=int, default=18)
    ap.add_argument("--yaricap", type=int, default=24, help="tarama yaricapi, piksel")
    a = ap.parse_args()

    bbox = tuple(a.bbox)
    tms, ad, anahtar = a.tms, a.tms or "?", ""
    if a.oam_ara:
        eslesen = [s for s in search_oam_images(bbox, limit=50)
                   if a.oam_ara.lower() in (s.get("title") or "").lower()]
        if not eslesen:
            print(f"OAM'de '{a.oam_ara}' ile eslesen sahne yok.")
            return 1
        s = eslesen[0]
        tms = s["tms_url"] + "/{z}/{x}/{y}.png"
        ad = f"{s['title'].strip()} (OAM, cekim {s['date'][:10]})"
        anahtar = s["tms_url"].split("/")[3]

    img, bounds = fetch_satellite_area(None, None, bbox=bbox, zoom_level=a.zoom,
                                       provider="custom", custom_url=tms)
    if img is None:
        print("Goruntu alinamadi.")
        return 1
    w, h = img.size
    gsd = gsd_of_zoom(a.zoom, (bbox[1] + bbox[3]) / 2)
    yol = get_osm_roads_overpass(bounds, w, h, thickness=5)
    if not np.any(yol):
        print("OSM yol maskesi bos -- olcum yapilamaz (Overpass dustu mu?).")
        return 1

    t = hizalama.osm_taramasi(np.array(img.convert("RGB")), yol, yaricap_px=a.yaricap)
    dogu_m = round(t["goruntuDx"] * gsd, 1)
    kuzey_m = round(-t["goruntuDy"] * gsd, 1)
    buyukluk = round(float(np.hypot(dogu_m, kuzey_m)), 1)

    print(f"\nsahne    : {ad}")
    print(f"goruntu  : {w}x{h} px, z{a.zoom}, GSD {gsd:.3f} m")
    print(f"kayma    : dogu {dogu_m:+.1f} m, kuzey {kuzey_m:+.1f} m  (buyukluk {buyukluk} m)")
    print(f"skor     : en iyi {t['enIyi']:.2f} | kaydirmasiz {t['sifirKaymada']:.2f} "
          f"| en kotu {t['enKotu']:.2f}  -> aralik {t['enKotu'] - t['enIyi']:.2f}")
    if t["enKotu"] - t["enIyi"] < 3.0:
        print("UYARI: skor araligi dar -- goruntude kirmizi cati yok gibi. Olcum ANLAMSIZ.")
    print(f"esik     : {hizalama.ESIK_M} m -> "
          + ("UYGULANIR" if buyukluk >= hizalama.ESIK_M else "uygulanmaz (yalnizca raporlanir)"))
    print("\n--- hizalama.py OLCULEN_KAYMALAR icine: ---")
    print(json.dumps({
        "anahtar": anahtar, "ad": ad, "doguM": dogu_m, "kuzeyM": kuzey_m,
        "olcum": {
            "yontem": "OSM yol maskesi tarama (cati kirmiziligi R-B en dusuk)",
            "zoom": a.zoom, "gsdM": round(gsd, 3),
            "enIyiPiksel": {"dx": t["goruntuDx"], "dy": t["goruntuDy"]},
            "skorAraligi": {"enIyi": round(t["enIyi"], 2),
                            "sifirKaymada": round(t["sifirKaymada"], 2),
                            "enKotu": round(t["enKotu"], 2)},
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
