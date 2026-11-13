"""
Tablo 21, satir 7 (Risk skoru agirliklari) icin parametre duyarlilik
taramasi.

Uretim kodundaki (backend/apps/earthquake_risk/risk_engine.py)
EarthquakeRiskEngine sinifini BIREBIR kullanir; short_risk (CatBoost),
long_hazard ve fault_score bilesenleri sabit tutulup nihai agirliklar
(w_short, w_long, w_fault; varsayilan 0.4/0.3/0.3) izgara halinde
taranir. Senaryo boyunca kullanilan 8 bolgenin (H-Z1..K-Z3) merkez
koordinatlari (district_coords.json, Nominatim ile geocode edilmis,
uretim kodundaki predict_city_risk ile ayni kaynak) uzerinde her agirlik
kombinasyonu icin risk kategorisi (DUSUK/ORTA/YUKSEK/COK YUKSEK) hesaplanir.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))

from apps.earthquake_risk.risk_engine import (
    EarthquakeRiskEngine,
    nearest_fault_distance,
    fault_hazard_score,
)

DISTRICT_COORDS_PATH = Path(__file__).resolve().parent / "district_coords.json"
OUT_PATH = Path(__file__).resolve().parent / "results" / "table21_row7_risk_weights.json"

CAT_ORDER = ["DUSUK", "ORTA", "YUKSEK", "COK_YUKSEK"]


def risk_category(score):
    if score < 0.25:
        return "DUSUK"
    if score < 0.50:
        return "ORTA"
    if score < 0.75:
        return "YUKSEK"
    return "COK_YUKSEK"


def main():
    districts = json.loads(DISTRICT_COORDS_PATH.read_text(encoding="utf-8"))

    engine = EarthquakeRiskEngine()
    engine._prepare_frames()
    engine._train_short_model()

    components = {}
    for code, (lat, lon) in districts.items():
        short_risk = engine._compute_short_term_ml_risk(lat, lon)
        long_hazard = engine._compute_long_term_hazard(lat, lon, radius_km=200.0, mag_threshold=6.0)
        dist_fault = nearest_fault_distance(lat, lon)
        fault_score = fault_hazard_score(dist_fault)
        components[code] = {
            "lat": lat, "lon": lon,
            "short_risk": short_risk, "long_hazard": long_hazard, "fault_score": fault_score,
        }
        print(f"{code}: short={short_risk:.3f} long={long_hazard:.3f} fault={fault_score:.3f}")

    # Izgara: w_short in {0.3,0.4,0.5}, w_long in {0.2,0.3,0.4}, w_fault = 1 - w_short - w_long
    # (0.4/0.3/0.3 varsayilanin +-0.1 komsulugu; yalniz gecerli - toplami 1,
    # her agirlik >=0.1 - kombinasyonlar tutulur)
    grid = []
    for w_short in (0.3, 0.4, 0.5):
        for w_long in (0.2, 0.3, 0.4):
            w_fault = round(1.0 - w_short - w_long, 2)
            if w_fault < 0.1 or w_fault > 0.5:
                continue
            grid.append((w_short, w_long, w_fault))

    baseline = (0.4, 0.3, 0.3)
    baseline_cats = {}
    for code, c in components.items():
        s = baseline[0] * c["short_risk"] + baseline[1] * c["long_hazard"] + baseline[2] * c["fault_score"]
        baseline_cats[code] = risk_category(s)

    sweep_results = []
    for (ws, wl, wf) in grid:
        cats = {}
        dist = {k: 0 for k in CAT_ORDER}
        n_changed = 0
        for code, c in components.items():
            s = ws * c["short_risk"] + wl * c["long_hazard"] + wf * c["fault_score"]
            cat = risk_category(s)
            cats[code] = cat
            dist[cat] += 1
            if cat != baseline_cats[code]:
                n_changed += 1
        sweep_results.append({
            "w_short": ws, "w_long": wl, "w_fault": wf,
            "is_baseline": (ws, wl, wf) == baseline,
            "category_by_district": cats,
            "category_distribution": dist,
            "n_districts_changed_vs_baseline": n_changed,
        })
        marker = " (varsayilan)" if (ws, wl, wf) == baseline else ""
        print(f"w=({ws:.1f},{wl:.1f},{wf:.1f}){marker}: dagilim={dist} degisen={n_changed}/8")

    out = {
        "district_components": components,
        "baseline_weights": baseline,
        "baseline_category_by_district": baseline_cats,
        "grid_sweep": sweep_results,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"yazildi -> {OUT_PATH}")


if __name__ == "__main__":
    main()
