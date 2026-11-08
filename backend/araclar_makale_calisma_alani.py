# -*- coding: utf-8 -*-
"""Makale Sekil 3 -- calisma alani haritasi (uc drone mahallesi).

Eski Sekil 3 sekiz operasyon bolgesini (H-Z1..K-Z3) gosteriyordu; tatbikat
artik uc gercek mahallede kosuyor. Hicbir konum elle yazilmaz:

  - Mahalleler  : apps/road_damage/data/tatbikat_alanlari.json (analizBbox, merkez)
  - Dis merkezler: USGS ComCat us6000jllz (37,226 K / 37,014 D) ve us6000jlqa
                   (38,011 K / 37,196 D); eski Sekil 3 ile ayni koordinatlar
  - Faylar      : GEM aktif fay veritabani (gem_active_faults_harmonized.geojson)
  - Zemin       : OpenStreetMap karolari (tek seferlik indirme, onbellege yazilir)

Cikti: benchmark/makale_sekilleri/sekil_calisma_alani.png
"""
import io
import json
import math
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

KOK = Path(__file__).resolve().parent
KATALOG = KOK / "apps/road_damage/data/tatbikat_alanlari.json"
FAYLAR = KOK / "apps/earthquake_risk/data/fault_maps/fay_haritası/gem_active_faults_harmonized.geojson"
ONBELLEK = KOK / "cache/osm_karo"  # git disi; karolar her seferinde yeniden indirilmesin
CIKTI = KOK / "benchmark/makale_sekilleri/sekil_calisma_alani.png"

SECILEN = {"Defne - Elektrik": "Defne / Elektrik", "Islahiye": "İslahiye", "Nurdagi": "Nurdağı"}
# etiket kaydirmasi (nokta cinsinden) -- dis merkez etiketleriyle cakismasin diye
ETIKET = {"Defne - Elektrik": (10, -4), "Islahiye": (10, -14), "Nurdagi": (-128, 6)}
DIS_MERKEZ = [  # USGS ComCat us6000jllz / us6000jlqa; adlar AFAD'i izler
    ("Pazarcık (04.17, Mw 7,7)", 37.2256, 37.0143, (10, -16)),
    ("Elbistan (13.24, Mw 7,6)", 38.0106, 37.1962, (-150, -20)),
]
BOYLAM = (35.85, 37.80)
ENLEM = (35.95, 38.25)
ZOOM = 9


def _merc(lon, lat):
    x = (lon + 180.0) / 360.0
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2
    return x, y


def _karo(z, x, y):
    ONBELLEK.mkdir(parents=True, exist_ok=True)
    yol = ONBELLEK / f"{z}_{x}_{y}.png"
    if not yol.exists():
        istek = urllib.request.Request(
            f"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            headers={"User-Agent": "QuakeMind-academic-figure/1.0 (single fetch, cached)"})
        yol.write_bytes(urllib.request.urlopen(istek, timeout=30).read())
    return Image.open(io.BytesIO(yol.read_bytes())).convert("RGB")


def zemin():
    n = 2 ** ZOOM
    x0, y0 = _merc(BOYLAM[0], ENLEM[1])
    x1, y1 = _merc(BOYLAM[1], ENLEM[0])
    tx0, ty0, tx1, ty1 = int(x0 * n), int(y0 * n), int(x1 * n), int(y1 * n)
    mozaik = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            mozaik.paste(_karo(ZOOM, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    # piksel -> Web Mercator birim kare [0,1] koordinati
    return mozaik, (tx0 / n, (tx1 + 1) / n, (ty1 + 1) / n, ty0 / n)


def main():
    alanlar = [a for a in json.loads(KATALOG.read_text(encoding="utf-8")) if a["parca"] in SECILEN]
    faylar = json.loads(FAYLAR.read_text(encoding="utf-8"))["features"]

    fig, ax = plt.subplots(figsize=(7.2, 8.0))
    img, (l, r, b, t) = zemin()
    ax.imshow(img, extent=(l, r, b, t), zorder=0)
    ax.imshow(Image.new("RGB", img.size, (255, 255, 255)), extent=(l, r, b, t), alpha=0.35, zorder=1)

    ilk = True
    for f in faylar:
        g = f["geometry"]
        cizgiler = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for c in cizgiler:
            if not any(BOYLAM[0] - .3 <= p[0] <= BOYLAM[1] + .3 and ENLEM[0] - .3 <= p[1] <= ENLEM[1] + .3 for p in c):
                continue
            xs, ys = zip(*[_merc(p[0], p[1]) for p in c])
            ax.plot(xs, ys, color="#6d28d9", lw=1.3, alpha=0.8, zorder=3,
                    label="Aktif fay (GEM)" if ilk else None)
            ilk = False

    for ad, lat, lon, kay in DIS_MERKEZ:
        x, y = _merc(lon, lat)
        ax.scatter([x], [y], marker="*", s=380, color="#d1332e", edgecolor="white", lw=1.1, zorder=8,
                   label="Dış merkez" if ad == DIS_MERKEZ[0][0] else None)
        ax.annotate(ad, (x, y), textcoords="offset points", xytext=kay, fontsize=9,
                    color="#7a1020", fontweight="bold", zorder=9)

    for i, a in enumerate(alanlar):
        x, y = _merc(a["merkez"]["lon"], a["merkez"]["lat"])
        ax.scatter([x], [y], s=70, marker="s", color="#1f6feb", edgecolor="white", lw=1.2, zorder=7,
                   label="Tatbikat mahallesi (drone ortofotosu)" if i == 0 else None)
        ax.annotate(f"{SECILEN[a['parca']]}\n({a['il']}, {a['tarih']})", (x, y),
                    textcoords="offset points", xytext=ETIKET[a["parca"]], fontsize=8.5, color="#111827",
                    fontweight="bold", zorder=9)

    x0, y0 = _merc(BOYLAM[0], ENLEM[1])
    x1, y1 = _merc(BOYLAM[1], ENLEM[0])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.92)
    ax.text(0.005, 0.005, "Zemin © OpenStreetMap katkıcıları · Fay: GEM Global Active Faults",
            transform=ax.transAxes, fontsize=6.5, color="#374151", zorder=10)
    fig.tight_layout()
    fig.savefig(CIKTI, dpi=300, facecolor="white", bbox_inches="tight")
    print("yazildi ->", CIKTI)


if __name__ == "__main__":
    main()
