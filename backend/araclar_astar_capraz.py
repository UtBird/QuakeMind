# -*- coding: utf-8 -*-
"""A* yol bulucusunun bagimsiz capraz dogrulamasi (makale §4.5).

Makale "rotalanan guzergahlar ayri ve bagimsiz bir yol bulucuyla capraz
dogrulanmamistir" diyordu. Bu arac, tatbikatin kurdugu AYNI cizge, AYNI kenar
suresi ve AYNI donus cezasi modeliyle:

  1. donus.en_kisa_yol (A*, kenar durumlu, sezgisel = kus ucusu / cizgenin en
     yuksek hizi) sonucunu,
  2. acikca kurulan kenar grafigi (satir grafigi) uzerinde networkx'in
     Dijkstra'si (sezgisiz, baska bir uygulama) sonucuyla

bir cift bir cift karsilastirir. Iki gorunum sinanir: kapanmasiz cizge (gri /
kapanmayi bilmeyen ekibin ilk plani) ve kapali kenarlari cikarilmis cizge
(QuakeMind). Ayrica eski sabit sezgisel (v_max = 22,2 m/s, J-114) ile kac
ciftin farkli (daha kotu) sonuc verdigi de sayilir.

    python araclar_astar_capraz.py --alanlar apps/road_damage/data/tatbikat_alanlari.json \
        --sec "Defne - Elektrik" Islahiye Nurdagi --model unet_mitb4_p2_t42 \
        --tohum 42 43 44 45 46 --cikti benchmark/reports/tatbikat_b0/astar_capraz.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))

from araclar_tatbikat_kos import _alanlari_oku, _b64_maske  # noqa: E402


def _satir_grafigi_dijkstra(G, s, t, sure, yonler, gizli, donus_sn):
    """Bagimsiz cozum: kenar durumlu cizgeyi ACIKCA kurup networkx Dijkstra."""
    import networkx as nx
    from apps.road_damage.utils import donus

    L = nx.DiGraph()
    acik = [(u, v, k) for u, v, k in G.edges(keys=True) if (u, v, k) not in gizli]
    acik_kume = set(acik)
    for e in acik:
        u, v, k = e
        se = sure(u, v, k, G[u][v][k])
        if u == s:
            L.add_edge("S", e, weight=se)
        if v == t:
            L.add_edge(e, "T", weight=0.0)
        for _v, w, k2 in G.edges(v, keys=True):
            e2 = (v, w, k2)
            if e2 not in acik_kume:
                continue
            tip = donus.donus_tipi(yonler[e][1], yonler[e2][0], geri_mi=(w == u))
            L.add_edge(e, e2, weight=donus_sn[tip] + sure(v, w, k2, G[v][w][k2]))
    if "S" not in L or "T" not in L:
        return None
    try:
        return nx.dijkstra_path_length(L, "S", "T", weight="weight")
    except nx.NetworkXNoPath:
        return None


def _alan(alan, model, tohumlar, ekip_sayisi):
    from apps.road_damage.utils import donus, tatbikat
    from apps.road_damage.utils.network import nearest_node
    from apps.road_damage.worker import run_analysis_job

    k = alan["analizBbox"]
    r = run_analysis_job({
        "_analysisId": f"capraz-{alan['parca']}", "city": alan.get("il") or "?", "source": "oam",
        "latitude": alan["merkez"]["lat"], "longitude": alan["merkez"]["lon"],
        "bboxWest": k[0], "bboxSouth": k[1], "bboxEast": k[2], "bboxNorth": k[3],
        "oamTileUrl": alan["tmsUrl"] + "/{z}/{x}/{y}.png", "oamPreferredTitle": alan["sahneAdi"],
        "oncesiGoruntusu": False, "modelAdi": model, "radiusKm": 2.5,
    })
    maske = _b64_maske(r, "imageDamageMaskB64", esik=127)
    gecerli = _b64_maske(r, "imageOriginalB64", esik=12)
    s = r["bounds"]
    bounds = (float(s["west"]), float(s["south"]), float(s["east"]), float(s["north"]))
    G, _sg, kapali, _k, _kap, _c = tatbikat.mahalle_grafigi(maske, bounds, gecerli_maske=gecerli)
    ekip = tatbikat.giris_noktalari(G, bounds, sayi=ekip_sayisi)
    yonler = donus.kenar_yonleri(G)
    ceza = dict(donus.DONUS_SN)
    kapali = {e for e in kapali if G.has_edge(*e)}

    def sure(u, v, kk, d):   # network.simulate_reference_fleet ile ayni (_kenar_dk * 60)
        h = d.get("hizKmh")
        return d.get("length", 0.0) / (float(h) / 3.6) if h else d.get("length", 0.0) / (15.0 / 3.6)

    vmax = donus.en_yuksek_hiz(G, sure)
    satir = {"alan": alan["yer"], "vmaxMs": round(vmax, 2), "vmaxKmh": round(vmax * 3.6, 1),
             "kenarHizUstuEskiSabit": sum(1 for u, v, kk, d in G.edges(keys=True, data=True)
                                          if (d.get("hizKmh") or 0) / 3.6 > 22.2),
             "cift": 0, "ayni": 0, "enBuyukFarkSn": 0.0, "ulasilamazUyumlu": 0, "uyumsuz": [],
             "eskiSezgiselFarkli": 0, "eskiSezgiselEnBuyukKayipSn": 0.0}
    goruldu = set()
    for t in tohumlar:
        kurban = tatbikat.afetzedeler(maske, bounds, sayi=ekip_sayisi * 3, tohum=t)
        if not kurban:
            continue
        kurban, _e, ekip_t = tatbikat.ulasilabilir_afetzedeler(G, ekip, kurban)
        n = min(len(ekip_t), len(kurban))
        for a in ekip_t[:n]:
            for b in kurban[:n]:
                s_n = nearest_node(G, a["lat"], a["lon"])
                t_n = nearest_node(G, b["lat"], b["lon"])
                for gorunum, gizli in (("kapanmasiz", set()), ("kapanmali", kapali)):
                    anahtar = (s_n, t_n, gorunum)
                    if anahtar in goruldu:
                        continue
                    goruldu.add(anahtar)

                    def s_g(u, v, kk, d, _g=gizli):
                        return math.inf if (u, v, kk) in _g else sure(u, v, kk, d)

                    a_sn = donus.en_kisa_yol(G, s_n, t_n, s_g, yonler=yonler, en_yuksek_hiz_ms=vmax)[0]
                    d_sn = _satir_grafigi_dijkstra(G, s_n, t_n, sure, yonler, gizli, ceza)
                    eski = donus.en_kisa_yol(G, s_n, t_n, s_g, yonler=yonler, en_yuksek_hiz_ms=22.2)[0]
                    satir["cift"] += 1
                    if a_sn is None and d_sn is None:
                        satir["ulasilamazUyumlu"] += 1
                        continue
                    if a_sn is None or d_sn is None or abs(a_sn - d_sn) > 1e-6:
                        satir["uyumsuz"].append({"gorunum": gorunum, "astar": a_sn, "dijkstra": d_sn})
                        continue
                    satir["ayni"] += 1
                    satir["enBuyukFarkSn"] = max(satir["enBuyukFarkSn"], abs(a_sn - d_sn))
                    if eski is not None and eski - d_sn > 1e-6:
                        satir["eskiSezgiselFarkli"] += 1
                        satir["eskiSezgiselEnBuyukKayipSn"] = round(
                            max(satir["eskiSezgiselEnBuyukKayipSn"], eski - d_sn), 2)
    return satir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alanlar", required=True)
    ap.add_argument("--sec", nargs="*")
    ap.add_argument("--model", required=True)
    ap.add_argument("--tohum", type=int, nargs="+", default=[42])
    ap.add_argument("--ekip", type=int, default=5)
    ap.add_argument("--cikti", default=None)
    a = ap.parse_args()

    from apps.road_damage.utils import model_kunyesi
    from apps.road_damage.worker import _init_worker

    alanlar = _alanlari_oku(Path(a.alanlar))
    if a.sec:
        istenen = {x.lower() for x in a.sec}
        alanlar = [x for x in alanlar if x["parca"].lower() in istenen]
    _init_worker(model_kunyesi.kunye_oku(a.model))
    t0 = time.perf_counter()
    sonuc = [_alan(x, a.model, a.tohum, a.ekip) for x in alanlar]
    for s in sonuc:
        print(f"{s['alan']}: {s['cift']} sorgu | A* = Dijkstra: {s['ayni']} | ikisi de ulasilamaz: "
              f"{s['ulasilamazUyumlu']} | UYUMSUZ: {len(s['uyumsuz'])} | en buyuk fark {s['enBuyukFarkSn']:.2e} sn "
              f"| v_max {s['vmaxKmh']} km/sa ({s['kenarHizUstuEskiSabit']} kenar 80 km/sa ustu) | eski sabit "
              f"sezgisel {s['eskiSezgiselFarkli']} sorguda daha kotu (en cok +{s['eskiSezgiselEnBuyukKayipSn']} sn)")
    print(f"sure {time.perf_counter() - t0:.0f} sn")
    if a.cikti:
        Path(a.cikti).write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if all(not s["uyumsuz"] for s in sonuc) else 2


if __name__ == "__main__":
    raise SystemExit(main())
