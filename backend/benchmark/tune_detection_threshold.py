"""Tanı amaçlı, tek seferlik script: neden canlı SegFormer tespiti Copernicus
gerçek hasarının sadece %2.7'sini yakaladığını arastirir.

Pahali kisim (uydu goruntusu indirme + model forward-pass) BİR KEZ yapılır,
raw_probs (esik/booster uygulanmadan HAM model olasiliklari) elde edilir;
ardindan threshold/damage_booster/postprocess_level kombinasyonlari bu ayni
raw_probs uzerinde ucuzca denenir (saniyeler icinde), her kombinasyon icin
kac road-mask pikselinin "hasarli" isaretlendigini raporlar.

Kullanim:
  python benchmark/tune_detection_threshold.py
"""
import sys
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from apps.road_damage.utils.fetcher import fetch_satellite_area, get_osm_roads_overpass
from apps.road_damage.utils.inference import load_simple_model, run_inference
from apps.road_damage.utils.tiling import zoom_for_radius

# Kahramanmaras/EKMEKCI'nin gercek analiz sinirlari (benchmark/runs/kahramanmaras-*/summary.json'dan)
BOUNDS = {"west": 36.9140625, "south": 37.56199695314351, "east": 36.93603515625, "north": 37.59682400108366}
WAYBACK_ID = "57965"  # 2023-02-23, gercek kosuda kullanilan ayni surum
MODEL_PATH = str(BACKEND_DIR / "apps" / "road_damage" / "models" / "optimized_mitb4_focal_dice30.pth")


def main():
    lat = (BOUNDS["south"] + BOUNDS["north"]) / 2
    lon = (BOUNDS["west"] + BOUNDS["east"]) / 2
    bbox = (BOUNDS["west"], BOUNDS["south"], BOUNDS["east"], BOUNDS["north"])

    print("Model yukleniyor...")
    model, device = load_simple_model(MODEL_PATH)
    if model is None:
        print("HATA: model yuklenemedi.")
        return

    print("Uydu goruntusu indiriliyor (gercek kosuyla ayni Wayback surumu)...")
    img, bounds = fetch_satellite_area(lat=lat, lon=lon, bbox=bbox, zoom_level=zoom_for_radius(2.0),
                                        wayback_id=WAYBACK_ID, provider="esri")
    if img is None:
        print("HATA: goruntu indirilemedi.")
        return
    print(f"Goruntu boyutu: {img.size}")

    print("OSM yol maskesi cikariliyor...")
    w, h = img.size
    road_mask = get_osm_roads_overpass(bounds, w, h, thickness=6)
    road_mask_binary = (road_mask > 0).astype(np.uint8)
    print(f"Yol maskesi piksel sayisi: {int(road_mask_binary.sum())}")

    print("Segformer forward-pass calisiyor (bir kez, dakikalar surebilir)...")
    raw_probs, _, _, _, _ = run_inference(
        img, road_mask_binary, model, device,
        damage_booster=1.0, threshold=0.0,  # ham cikti icin notr degerler
        use_imagenet_norm=True, postprocess_level=0,
    )

    print("\n--- HAM MODEL OLASILIK DAGILIMI (damage_booster/threshold oncesi) ---")
    flat = raw_probs.flatten()
    for p in (50, 75, 90, 95, 99, 99.9, 100):
        print(f"  p{p}: {np.percentile(flat, p):.4f}")
    road_probs = raw_probs[road_mask_binary > 0]
    print(f"  Sadece YOL pikselleri -- max: {road_probs.max():.4f}, p99: {np.percentile(road_probs, 99):.4f}, p95: {np.percentile(road_probs, 95):.4f}")

    print("\n--- PARAMETRE TARAMASI (ayni raw_probs uzerinde, ucretsiz) ---")
    import cv2
    from apps.road_damage.utils.inference import _postprocess_mask

    print(f"{'booster':>8} {'threshold':>10} {'postproc':>9} {'road_px_flagged':>16} {'components':>11}")
    for booster in (1.0, 2.0, 3.5, 5.0, 8.0):
        for threshold in (0.05, 0.10, 0.20, 0.30, 0.40):
            for postproc in (0, 1, 2):
                boosted = np.clip(raw_probs * booster, 0, 1)
                mask = (boosted > threshold).astype(np.uint8)
                mask = _postprocess_mask(mask, level=postproc)
                intersection = cv2.bitwise_and(mask, road_mask_binary)
                flagged = int(intersection.sum())
                n_labels, _ = cv2.connectedComponents(intersection)
                print(f"{booster:>8.1f} {threshold:>10.2f} {postproc:>9d} {flagged:>16d} {n_labels-1:>11d}")


if __name__ == "__main__":
    main()
