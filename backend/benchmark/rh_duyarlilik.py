# -*- coding: utf-8 -*-
"""r_h (sert kapanma yaricapi) duyarliligi: 0 / 10 / 15 / 25 m.

Cikarim BIR KEZ kosar -- r_h yalnizca kapanma turetmesini etkiler, maskeyi
degil. Boylece dort yaricap ayni maske uzerinde, ayni ekip/afetzede kumesiyle
ve ayni grafikle kiyaslanir; tek degisen yaricaptir.
"""
import json
import os
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
CIK = Path(r"C:\Users\femre\AppData\Local\Temp\claude\C--Users-femre-Desktop-2209-A-Afet-QuakeMind-Proje-Repo\5010c4b2-2d55-4982-a500-64b0762e1603\scratchpad")
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))

import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

from apps.road_damage.utils import model_kunyesi as mk, tatbikat  # noqa: E402
from apps.road_damage.utils.fetcher import fetch_satellite_area, search_oam_images  # noqa: E402
from apps.road_damage.utils.inference import run_inference  # noqa: E402
from apps.road_damage.utils.network import closures_from_damage_mask  # noqa: E402

torch.set_num_threads(6)
MODEL = "unet_mitb4_p2_t42"
YARICAPLAR = [0.0, 10.0, 15.0, 25.0]

# Kutu tatbikatin kullandigi kuralla ayni olmali, yoksa sayilar kiyaslanamaz:
# uclar/simulasyon.py geniş katman icin yaricapKm = 0,45 gonderir ve worker
# bunu bbox_from_center ile kutuya cevirir.
from apps.road_damage.utils.assembly import bbox_from_center  # noqa: E402

clat, clon = 36.197694, 36.149322
# DIKKAT: worker yaricapi `max(0.5, radiusKm)` ile tabanliyor -- istekte 0,45
# gonderilse bile kutu 0,5 km'den kurulur (yakinlastirma yine istenen yaricaptan
# secildigi icin z18 kalir ve 64 karo tavani goruntuyu 2048 px'e kirpar).
# Olcumun tatbikatla ayni goruntuyu kullanmasi icin burada da 0,5 yazilir.
bbox = bbox_from_center(clat, clon, 0.5)
aday = [r for r in search_oam_images(bbox, "2023-02-06", "2023-02-20", limit=50)
        if "maxar" in r["title"].lower()]
aday.sort(key=lambda r: r["date"])
kaynak = aday[0]
img, bounds = fetch_satellite_area(None, None, bbox=bbox, zoom_level=18, provider="custom",
                                   custom_url=kaynak["tms_url"] + "/{z}/{x}/{y}.png")
w, h = img.size
print(f"goruntu : {w}x{h} px, {kaynak['title'][:34]}, {kaynak['date'][:10]}")

kunye = mk.kunye_oku(MODEL)
model, cihaz = mk.model_yukle(kunye)
t0 = time.perf_counter()
_ham, _g, maske, _kes, img_np = run_inference(
    img, np.zeros((h, w), np.uint8), model, cihaz,
    kunye["karar"]["guclendirme"], kunye["karar"]["esik"], True, kunye["karar"]["sonIsleme"])
gecerli = (img_np.max(axis=2) > 12).astype(np.uint8)
print(f"model   : {kunye['ad']}, esik {kunye['karar']['esik']}, cikarim {time.perf_counter()-t0:.0f} sn")
print(f"hasar   : {int(maske.sum())} px (%{maske[gecerli > 0].mean()*100:.2f} gecerli alanin)\n")

kurbanlar = tatbikat.afetzedeler(maske, bounds, 5, 42)
takimlar = tatbikat.ekipler(clat, clon, 5)
print(f"ekip {len(takimlar)}, afetzede {len(kurbanlar)}")

# Graf bir kez: butun yaricaplar ayni graf uzerinde.
G, _sg, _k, kutu, _kap = tatbikat.tatbikat_grafigi(
    takimlar, kurbanlar, maske, bounds, kapanma_yaricapi_m=YARICAPLAR[-1], gecerli_maske=gecerli)
toplam_m = sum(d.get("length", 0.0) for _u, _v, d in G.edges(data=True))
print(f"graf    : {G.number_of_nodes()} dugum, {G.number_of_edges()} kenar, "
      f"{toplam_m/1000:.1f} km yol\n")

satirlar = []
for rh in YARICAPLAR:
    _a, _b, kapali, kapsama = closures_from_damage_mask(
        G, bounds, maske, valid_mask=gecerli, blockage_radius_m=rh)
    kapali_m = 0.0
    for (u, v, k) in kapali:
        try:
            kapali_m += G[u][v][k].get("length", 0.0)
        except KeyError:
            pass
    safe_G = nx.restricted_view(G, [], kapali)
    r = tatbikat.rota_kosusu(G, safe_G, takimlar, kurbanlar,
                             hasar_noktalari=tatbikat.hasar_noktalari(maske, bounds), ekranda=5)
    o = r["olcum"]
    satirlar.append({
        "rh": rh, "kapaliKenar": len(kapali), "kapaliM": round(kapali_m, 1),
        "kapaliYuzde": round(100 * kapali_m / toplam_m, 2) if toplam_m else None,
        "ortUzamaM": o["ortalamaUzamaM"], "ortUzamaYuzde": o["ortalamaUzamaYuzde"],
        "uzamaCift": o["uzamaHesabindakiCift"],
        "enBuyukUzamaM": o["enBuyukUzamaM"],
        "yurumeCift": o["yurumeGerekenCift"], "ortYurumeM": o["ortalamaYurumeM"],
        "ulasilamayan": o["ulasilamayanCift"],
    })
    s = satirlar[-1]
    print(f"r_h={rh:5.0f} m | kenar {s['kapaliKenar']:4d} | kapali {s['kapaliM']:8.0f} m "
          f"(%{s['kapaliYuzde']:5.2f}) | uzama {s['ortUzamaM']} m (%{s['ortUzamaYuzde']}) "
          f"[{s['uzamaCift']} tam rota] | "
          f"en buyuk {s['enBuyukUzamaM']} m | yurume {s['yurumeCift']}/25 ort {s['ortYurumeM']} m | "
          f"ulasilamayan {s['ulasilamayan']}")

(CIK / "rh_duyarlilik.json").write_text(json.dumps({
    "alan": "hatay-elektrik", "katman": "genis", "kaynak": kaynak["title"], "tarih": kaynak["date"][:10],
    "model": kunye["ad"], "esik": kunye["karar"]["esik"], "tohum": 42,
    "toplamYolM": round(toplam_m, 1), "ciftSayisi": 25, "satirlar": satirlar,
}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nkayit: rh_duyarlilik.json")
