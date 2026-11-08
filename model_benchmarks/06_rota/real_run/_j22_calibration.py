# -*- coding: utf-8 -*-
"""J-22 r_h kalibrasyonu: gercek Maxar/Esri Wayback goruntusu + gercek
SegFormer yol hasari cikarimi + gercek EMSR648 yer gercegiyle, 4 ornek
alanda (H-Z1 x2, K-Z1 x2) r_h taramasi.

Kucuk kapsam: her biri ~800m x 800m, 2023-02-23 tarihli Esri Wayback
goruntusu (id=57965, deprem sonrasi +17 gun).
"""
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import cv2
import osmnx as ox
import networkx as nx

from apps.road_damage.utils.fetcher import fetch_satellite_area, get_osm_roads_overpass
from apps.road_damage.utils.inference import load_simple_model, run_inference
from apps.road_damage.utils.network import apply_risk_penalties, haversine
from emsr648_closures import closed_osm_edges

WAYBACK_ID = "57965"  # 2023-02-23
MODEL_PATH = REPO / "backend" / "apps" / "road_damage" / "models" / "optimized_mitb4_focal_dice30.pth"
RADIUS_M = 400.0  # yaricap -> ~800m x 800m bbox
R_H_SWEEP = (5, 10, 15, 25, 50, 100)

SAMPLES = [
    ("K-Z1-A", "AOI04", 37.57809, 36.91172),
    ("K-Z1-B", "AOI04", 37.57696, 36.93522),
]


def bbox_from_point(lat, lon, radius_m):
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * np.cos(np.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)  # west, south, east, north


def mask_to_damage_points(pred_mask_binary, bounds, grid_step_px=12):
    """J-22 duzeltme: yalniz bagli bilesen merkezleri (3-10 nokta, hasarin
    gercek uzamsal izini kaybediyordu) yerine, maske uzerinde SIK bir izgara
    ile ornekleme -- her hasar bolgesinin butun genisligi boyunca noktalar
    uretir, boylece kenar-orta-noktasi mesafe hesabi gercekci kalir."""
    west, south, east, north = bounds
    h, w = pred_mask_binary.shape
    ys, xs = np.where(pred_mask_binary[::grid_step_px, ::grid_step_px] > 0)
    points = []
    for gy, gx in zip(ys, xs):
        cy = gy * grid_step_px
        cx = gx * grid_step_px
        lon = west + (cx / w) * (east - west)
        lat = north - (cy / h) * (north - south)
        points.append((lat, lon))
    return points


def run_sample(name, aoi_code, lat, lon):
    print(f"\n{'='*60}\n{name}  center=({lat:.5f},{lon:.5f})  AOI={aoi_code}\n{'='*60}", flush=True)
    t0 = time.time()
    bounds = bbox_from_point(lat, lon, RADIUS_M)
    west, south, east, north = bounds

    img, real_bounds = fetch_satellite_area(lat, lon, bbox=bounds, zoom_level=18,
                                             wayback_id=WAYBACK_ID, provider="esri")
    if img is None:
        print(f"  GORUNTU ALINAMADI ({name}) - atlaniyor")
        return None
    print(f"  goruntu: {img.size}, gercek bounds={real_bounds} ({time.time()-t0:.1f}s)", flush=True)
    w, h = img.size

    road_mask = get_osm_roads_overpass(real_bounds, w, h, thickness=6)
    print(f"  yol maskesi olusturuldu, pozitif piksel oran={road_mask.mean():.4f} ({time.time()-t0:.1f}s)", flush=True)

    model, device = load_simple_model(str(MODEL_PATH))
    if model is None:
        print("  MODEL YUKLENEMEDI")
        return None

    _, boosted_probs, pred_mask_binary, intersection, img_np = run_inference(
        img, road_mask, model, device, damage_booster=3.5, threshold=0.4,
        use_imagenet_norm=False, postprocess_level=1)
    n_damage_px = int(pred_mask_binary.sum())
    print(f"  cikarim tamam, hasar piksel sayisi={n_damage_px} ({time.time()-t0:.1f}s)", flush=True)

    damage_points = mask_to_damage_points(pred_mask_binary, real_bounds)
    print(f"  hasar noktasi (bagli bilesen) sayisi={len(damage_points)}", flush=True)

    # OSM yol cizgesi (drive) - ayni real_bounds icin
    # J-22 duzeltme: osmnx 2.x bbox sirasi (left, bottom, right, top) =
    # (west, south, east, north) -- onceki kosumda (north, south, east, west)
    # kullanilmisti, bu da K-Z1 orneklerinde 130 binin uzerinde kenarli
    # (yanlislikla cok genis) bir graf cekilmesine yol acmisti.
    G = None
    last_exc = None
    for attempt in range(4):
        try:
            G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type="drive", simplify=True)
            break
        except Exception as exc:
            last_exc = exc
            print(f"  Overpass denemesi {attempt+1}/4 basarisiz: {exc}", flush=True)
            time.sleep(10)
    if G is None:
        print(f"  Overpass'a 4 denemede ulasilamadi, {name} atlaniyor: {last_exc}")
        return None
    n_edges_total = G.number_of_edges()
    print(f"  OSM graf: {G.number_of_nodes()} dugum, {n_edges_total} kenar", flush=True)
    if n_edges_total == 0:
        print("  Bu alanda OSM yolu yok - atlaniyor")
        return None

    # EMSR648 yer gercegi (medium kural) - AYNI graf uzerinde
    truth_closed = closed_osm_edges(G, aoi_code, "medium")
    truth_pct = 100.0 * len(truth_closed) / n_edges_total
    print(f"  EMSR648 (medium) yer gercegi: {len(truth_closed)}/{n_edges_total} kenar kapali (%{truth_pct:.1f})", flush=True)

    results = {"name": name, "n_edges": n_edges_total, "truth_closed": len(truth_closed),
               "truth_pct": truth_pct, "n_damage_points": len(damage_points), "sweep": {}}
    for r_h in R_H_SWEEP:
        Gc = G.copy()
        apply_risk_penalties(Gc, damage_points, blockages=damage_points, blockage_hard_radius_m=r_h)
        n_closed = n_edges_total - Gc.number_of_edges()
        pct = 100.0 * n_closed / n_edges_total
        results["sweep"][r_h] = {"n_closed": n_closed, "pct": pct}
        print(f"    r_h={r_h:>4}m: model kapali={n_closed}/{n_edges_total} (%{pct:.1f})  "
              f"[yer gercegi %{truth_pct:.1f}, fark={pct-truth_pct:+.1f}]", flush=True)

    print(f"  {name} toplam sure: {time.time()-t0:.1f}s", flush=True)
    return results


if __name__ == "__main__":
    all_results = []
    for name, aoi_code, lat, lon in SAMPLES:
        r = run_sample(name, aoi_code, lat, lon)
        if r:
            all_results.append(r)

    print("\n\n" + "=" * 70)
    print("OZET")
    print("=" * 70)
    for r_h in R_H_SWEEP:
        diffs = []
        for res in all_results:
            d = res["sweep"][r_h]["pct"] - res["truth_pct"]
            diffs.append(d)
        mean_abs_diff = np.mean([abs(d) for d in diffs]) if diffs else float("nan")
        print(f"r_h={r_h:>4}m: ortalama |fark|={mean_abs_diff:.1f} puan  (fark listesi: "
              f"{[f'{d:+.1f}' for d in diffs]})")

    import json
    out_path = Path(__file__).resolve().parent / "results" / "j22_calibration_kz1.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nSonuc: {out_path}")
