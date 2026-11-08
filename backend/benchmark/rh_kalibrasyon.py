"""r_h kalibrasyonu: modelin kapanmalari EMSR648 yer gercegiyle ne kadar ortusuyor?

`model_in_real_world.py` (J-30 / Tablo 18) bu sayilari zaten uretiyor ama ajan
simulasyonlariyla birlikte; burada YALNIZ kapanma kumesi karsilastirmasi yapilir,
boylece farkli bir model maskesi setiyle dakikalar icinde yeniden kosulabilir.

Dunya  : EMSR648 Grading hasarli yol cizgileri -> closures_from_lines
Model  : <maske koku>/<bolge>-z<zoom>/ -> closures_from_damage_mask (r_h)
Olcut  : fiziksel kesim uzerinden TP/FP/FN, kesinlik, duyarlilik, F1, IoU
         (model_in_real_world.confusion / rates ile AYNI fonksiyonlar)

    python benchmark/rh_kalibrasyon.py [--maske-koku data/model_masks] [--etiket eski]

Cikti: benchmark/reports/rh_kalibrasyon_<etiket>.json + ekrana tablo.
"""
import argparse
import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
BACKEND = BENCH.parent
sys.path.insert(0, str(BACKEND))

from apps.road_damage.utils.network import (  # noqa: E402
    closures_from_damage_mask, closures_from_lines, fetch_osm_road_graph,
)
from benchmark.copernicus_ground_truth import aoi_rings, damaged_road_lines  # noqa: E402
from benchmark.model_in_real_world import confusion, load_mask, rates  # noqa: E402
from benchmark.scenario_dataset_drone import ZONES  # noqa: E402

ZOOMS = [18, 19, 20]
RADII_M = [0.0, 5.0, 10.0, 15.0, 25.0]
EMSR_RULE = "loose"
EMSR_BUFFER_M = 8.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maske-koku", default="data/model_masks",
                    help="Maske klasoru (benchmark/ altina gore). Ornek: data/model_masks_unet_mitb4")
    ap.add_argument("--etiket", default=None, help="Cikti dosyasi soneki (varsayilan: klasor adi)")
    a = ap.parse_args(argv)

    koku = BENCH / a.maske_koku
    etiket = a.etiket or koku.name
    if not koku.exists():
        raise SystemExit(f"Maske klasoru yok: {koku}")

    # load_mask kok klasoru modul duzeyinde tuttugu icin gecici olarak yonlendirilir.
    import benchmark.model_in_real_world as mrw
    mrw.MODEL_MASK_ROOT = koku

    toplam = {}
    bolge_basi = {}
    for zone in ZONES:
        bbox = tuple(zone["bbox"])
        G, err = fetch_osm_road_graph(bbox, network_type="walk")
        if G is None:
            raise SystemExit(f"{zone['id']}: graf yok ({err})")
        lines = damaged_road_lines(zone["emsrPackage"], EMSR_RULE, bbox)
        _a, _b, world_keys, _w = closures_from_lines(
            G, lines, buffer_m=EMSR_BUFFER_M, min_overlap=0.5,
            observed_polygons=aoi_rings(zone["emsrPackage"]))
        all_keys = set(G.edges(keys=True))
        print(f"{zone['id']:6s} graf {G.number_of_edges():6d} kenar | EMSR kapali {len(world_keys):4d}", flush=True)

        for zoom in ZOOMS:
            try:
                meta, damage, valid = load_mask(f"{zone['id']}-z{zoom}")
            except Exception as e:
                print(f"   z{zoom}: maske yok ({type(e).__name__})", flush=True)
                continue
            mb = meta["bounds"]
            bounds = (mb["west"], mb["south"], mb["east"], mb["north"])
            for r in RADII_M:
                _c, _d, keys, kapsama = closures_from_damage_mask(G, bounds, damage, valid, r)
                c = confusion(keys, world_keys, all_keys)
                ad = f"z{zoom}-r{int(r)}"
                t = toplam.setdefault(ad, {k: 0 for k in c})
                for k in c:
                    t[k] += c[k]
                bolge_basi.setdefault(ad, {})[zone["id"]] = {
                    **rates(c), "confusion": c,
                    "edgesObservedFraction": (kapsama or {}).get("edgesObservedFraction"),
                }

    satirlar = []
    for ad, c in sorted(toplam.items(), key=lambda kv: (int(kv[0].split("-")[0][1:]),
                                                        int(kv[0].split("-r")[1]))):
        satirlar.append({"ad": ad, "zoom": int(ad.split("-")[0][1:]), "yaricapM": int(ad.split("-r")[1]),
                         "confusion": c, **rates(c), "perZone": bolge_basi[ad]})

    print(f"\n{'zoom':>5} {'r_h':>5} {'modelKapali':>12} {'TP':>4} {'FP':>5} {'FN':>4} "
          f"{'kesinlik':>9} {'duyarlilik':>11} {'F1':>7} {'IoU':>7}")
    print("-" * 82)
    en_iyi = None
    for s in satirlar:
        c = s["confusion"]
        print(f"{s['zoom']:5d} {s['yaricapM']:5d} {c['modelClosed']:12d} {c['tp']:4d} {c['fp']:5d} "
              f"{c['fn']:4d} {(s['precision'] or 0):9.3f} {(s['recall'] or 0):11.3f} "
              f"{(s['f1'] or 0):7.3f} {(s['iou'] or 0):7.3f}")
        if en_iyi is None or (s["f1"] or 0) > (en_iyi["f1"] or 0):
            en_iyi = s
    if en_iyi:
        print(f"\nEN IYI F1: z{en_iyi['zoom']}, r_h={en_iyi['yaricapM']} m -> F1 {en_iyi['f1']:.3f} "
              f"(kesinlik {en_iyi['precision']:.3f}, duyarlilik {en_iyi['recall']:.3f})")
    ilk = satirlar[0]["confusion"] if satirlar else {}
    print(f"dunya (EMSR) kapali kesim: {ilk.get('worldClosed')} / toplam {ilk.get('segments')}")

    hedef = BENCH / "reports" / f"rh_kalibrasyon_{etiket}.json"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps({
        "maskeKoku": str(koku.relative_to(BACKEND)), "etiket": etiket,
        "emsrKural": EMSR_RULE, "emsrTamponM": EMSR_BUFFER_M,
        "bolgeler": [z["id"] for z in ZONES], "zoomlar": ZOOMS, "yaricaplarM": RADII_M,
        "enIyi": {"zoom": en_iyi["zoom"], "yaricapM": en_iyi["yaricapM"], "f1": en_iyi["f1"]} if en_iyi else None,
        "satirlar": satirlar,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nkayit: {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
