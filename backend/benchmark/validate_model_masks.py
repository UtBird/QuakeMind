"""Model hasar maskelerini EMSR648 yer gercegine karsi dogrular (M-20 / Tablo 18).

Iki duzey:

  BINA  -- modelin asil tahmin ettigi sey (egitim verisi KATE-CD: bina hasari).
           EMSR648 binasi, gorulen alanda kaliyorsa sayilir. Poligon
           katmaninda (builtUpA, Hatay) poligonun icinde hasar pikseli varsa;
           nokta katmaninda (builtUpP, Kahramanmaras) noktanin
           BUILDING_POINT_RADIUS_M metre cevresinde hasar pikseli varsa
           "model hasarli dedi" sayilir.

  YOL   -- kapanma karari. EMSR648 yol cizgisi boyunca ~2 m arayla orneklenen
           noktalardan biri, r_h metre genisletilmis hasar maskesinin icine
           dusuyorsa "model kapali dedi" sayilir. Bu, canli /analyze ve
           /closures_from_mask ile AYNI kuraldir (dilate_mask_by_metres), yalniz
           OSM kenari yerine EMSR'in kendi yol geometrisine uygulanir --
           iki farkli yol agini eslestirme hatasi karismasin diye.

Hasarli sayilan EMSR dereceleri: benchmark/copernicus_ground_truth.DAMAGED_GRADES
("Destroyed", "Damaged", "Possibly damaged").

    python benchmark/validate_model_masks.py --dataset drone --suffixes=-z18,-z19,-z20
"""
import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "benchmark"))

from apps.road_damage.utils.network import dilate_mask_by_metres  # noqa: E402
from benchmark.copernicus_ground_truth import DAMAGED_GRADES  # noqa: E402

MASK_ROOT = BACKEND / "benchmark" / "data" / "model_masks"
COPERNICUS = BACKEND / "benchmark" / "data" / "copernicus"
BUILDING_POINT_RADIUS_M = 10.0
ROAD_SAMPLE_STEP_M = 2.0
RADII_M = (5.0, 10.0, 15.0, 25.0)

# Bolge -> EMSR648 paketi ve bina katmani
EMSR_FOR_CITY = {
    "hatay": ("EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip", "builtUpA"),
    "kahramanmaras": ("EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1_vector.zip", "builtUpP"),
}


def load_layer(zip_name, pattern):
    with zipfile.ZipFile(COPERNICUS / zip_name) as zf:
        name = [n for n in zf.namelist() if n.endswith(".json") and pattern in n][0]
        return json.loads(zf.read(name))["features"]


class Grid:
    """Maske piksel izgarasi: canli boru hattiyla ayni dogrusal izdusum."""

    def __init__(self, bounds, w, h):
        self.w_, self.s, self.e, self.n = bounds["west"], bounds["south"], bounds["east"], bounds["north"]
        self.W, self.H = w, h
        mid = math.radians((self.s + self.n) / 2)
        self.m_per_px = (self.e - self.w_) * 111320.0 * math.cos(mid) / w

    def px(self, lon, lat):
        return ((lon - self.w_) / (self.e - self.w_) * self.W,
                (self.n - lat) / (self.n - self.s) * self.H)

    def inside(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H


def iter_rings(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        yield c[0]
    elif t == "MultiPolygon":
        for poly in c:
            yield poly[0]


def iter_lines(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "LineString":
        yield c
    elif t == "MultiLineString":
        yield from c


def confusion(pairs):
    tp = sum(1 for truth, pred in pairs if truth and pred)
    fp = sum(1 for truth, pred in pairs if not truth and pred)
    fn = sum(1 for truth, pred in pairs if truth and not pred)
    tn = sum(1 for truth, pred in pairs if not truth and not pred)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else (0.0 if (prec == 0 or rec == 0) else None)
    acc = (tp + tn) / len(pairs) if pairs else None
    return {"n": len(pairs), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": prec, "recall": rec, "f1": f1, "accuracy": acc,
            "truthPositive": tp + fn, "predPositive": tp + fp}


def evaluate(mask_id, zone, radii=RADII_M):
    d = MASK_ROOT / mask_id
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    dmg = (np.array(Image.open(d / "damage_mask.png").convert("L")) > 0).astype(np.uint8)
    valid = (np.array(Image.open(d / "valid_mask.png").convert("L")) > 0).astype(np.uint8)
    g = Grid(meta["bounds"], meta["width"], meta["height"])
    zip_name, bld_layer = EMSR_FOR_CITY[zone["city"]]
    w, s, e, n = zone.get("bbox") or (meta["zoneBbox"][k] for k in ("west", "south", "east", "north"))

    # ---------------- BINA ----------------
    b_pairs = []
    for f in load_layer(zip_name, bld_layer):
        grade = f["properties"].get("damage_gra")
        if grade not in DAMAGED_GRADES and grade != "No visible damage":
            continue  # "Not Analysed" vb. yer gercegi degil
        geom = f["geometry"]
        truth = grade in DAMAGED_GRADES
        if geom["type"] == "Point":
            lon, lat = geom["coordinates"][:2]
            if not (w <= lon <= e and s <= lat <= n):
                continue
            x, y = g.px(lon, lat)
            if not g.inside(x, y) or not valid[int(y), int(x)]:
                continue
            r = max(1, int(round(BUILDING_POINT_RADIUS_M / g.m_per_px)))
            local = np.zeros_like(dmg)
            cv2.circle(local, (int(x), int(y)), r, 1, -1)
        else:
            rings = list(iter_rings(geom))
            if not rings:
                continue
            clon = sum(p[0] for p in rings[0]) / len(rings[0])
            clat = sum(p[1] for p in rings[0]) / len(rings[0])
            if not (w <= clon <= e and s <= clat <= n):
                continue
            cx, cy = g.px(clon, clat)
            if not g.inside(cx, cy) or not valid[int(cy), int(cx)]:
                continue
            local = np.zeros_like(dmg)
            for ring in rings:
                pts = np.array([g.px(p[0], p[1]) for p in ring], dtype=np.int32)
                cv2.fillPoly(local, [pts], 1)
        pred = bool((local & dmg).any())
        b_pairs.append((truth, pred))

    # ---------------- YOL ----------------
    roads = []
    for f in load_layer(zip_name, "transportationL"):
        grade = f["properties"].get("damage_gra")
        if grade not in DAMAGED_GRADES and grade != "No visible damage":
            continue
        pts_px = []
        for line in iter_lines(f["geometry"]):
            for (lon1, lat1), (lon2, lat2) in zip(line[:-1], line[1:]):
                seg_m = math.hypot((lon2 - lon1) * 111320 * math.cos(math.radians(lat1)), (lat2 - lat1) * 110574)
                k = max(1, int(seg_m / ROAD_SAMPLE_STEP_M))
                for i in range(k + 1):
                    lon, lat = lon1 + (lon2 - lon1) * i / k, lat1 + (lat2 - lat1) * i / k
                    if not (w <= lon <= e and s <= lat <= n):
                        continue
                    x, y = g.px(lon, lat)
                    if g.inside(x, y) and valid[int(y), int(x)]:
                        pts_px.append((int(y), int(x)))
        if len(pts_px) >= 3:
            roads.append((grade in DAMAGED_GRADES, pts_px))

    road_by_radius = {}
    for r in radii:
        grown = dilate_mask_by_metres(dmg, (g.w_, g.s, g.e, g.n), g.W, r)
        pairs = [(truth, any(grown[y, x] for y, x in pts)) for truth, pts in roads]
        road_by_radius[f"{r:g}"] = confusion(pairs)

    return {
        "maskId": mask_id, "zoneId": zone["id"], "zoom": meta["zoom"],
        "metresPerPixel": meta["metresPerPixel"],
        "observedFraction": meta["validPixelFraction"],
        "damageFractionOfObserved": meta["damagePixelFractionOfObserved"],
        "buildings": confusion(b_pairs),
        "roadsByRadius": road_by_radius,
    }


def fmt(x, pct=True):
    if x is None:
        return "  -  "
    return f"{100 * x:5.1f}" if pct else f"{x:5d}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["v2", "drone"], default="drone")
    ap.add_argument("--suffixes", default="", help="Virgulle ayrilmis maske sonekleri, orn. --suffixes=-z18,-z19")
    ap.add_argument("--radii", default=None,
                    help="Virgulle ayrilmis r_h degerleri (metre). 0 = uygulamanin her zamanki kurali "
                         "(hasar yolun kendi ustunde). Varsayilan: 5,10,15,25")
    ap.add_argument("--out", default=None, help="Sonuc JSON yolu")
    args = ap.parse_args(argv)

    if args.dataset == "drone":
        import scenario_dataset_drone as DS
    else:
        import scenario_dataset as DS
    suffixes = [x for x in args.suffixes.split(",")] if args.suffixes else [""]
    radii = tuple(float(x) for x in args.radii.split(",")) if args.radii else RADII_M

    results = []
    for zone in DS.ZONES:
        for suf in suffixes:
            mid = f"{zone['id']}{suf}"
            if not (MASK_ROOT / mid / "meta.json").exists():
                print(f"  (yok) {mid}")
                continue
            results.append(evaluate(mid, zone, radii))

    print("\nBINA DUZEYI  (EMSR648 hasarli = Destroyed/Damaged/Possibly damaged)")
    print(f"{'maske':12} {'cm/px':>6} {'gorulen':>8} {'hasar px':>9} | {'n':>4} {'gercek+':>7} {'model+':>7} "
          f"{'TP':>4} {'FP':>4} {'FN':>4} | {'kesinlik':>8} {'duyarlilik':>10} {'F1':>6}")
    for r in results:
        b = r["buildings"]
        print(f"{r['maskId']:12} {100 * r['metresPerPixel']:6.1f} {100 * r['observedFraction']:7.1f}% "
              f"{100 * r['damageFractionOfObserved']:8.2f}% | {b['n']:4d} {b['truthPositive']:7d} {b['predPositive']:7d} "
              f"{b['tp']:4d} {b['fp']:4d} {b['fn']:4d} | {fmt(b['precision']):>8} {fmt(b['recall']):>10} {fmt(b['f1']):>6}")

    print("\nYOL DUZEYI  (r_h = sert kapatma yaricapi; model+ = modelin kapali dedigi EMSR yolu)")
    print(f"{'maske':12} {'r_h':>4} | {'n':>4} {'gercek+':>7} {'model+':>7} {'TP':>4} {'FP':>4} {'FN':>4} "
          f"| {'kesinlik':>8} {'duyarlilik':>10} {'dogruluk':>8}")
    for r in results:
        for rad, c in r["roadsByRadius"].items():
            print(f"{r['maskId']:12} {rad:>4} | {c['n']:4d} {c['truthPositive']:7d} {c['predPositive']:7d} "
                  f"{c['tp']:4d} {c['fp']:4d} {c['fn']:4d} | {fmt(c['precision']):>8} {fmt(c['recall']):>10} "
                  f"{fmt(c['accuracy']):>8}")

    # Uc bolgenin toplami (mikro ortalama): TP/FP/FN/TN bolgeler arasinda toplanir.
    # Hafif hasarli bolgelerde hic gercek-pozitif yol yok; bu yuzden yalniz
    # kesinlik/duyarlilik degil, dengeli dogruluk da raporlanir.
    def pooled(rows):
        tp, fp, fn, tn = (sum(r[k] for r in rows) for k in ("tp", "fp", "fn", "tn"))
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        spec = tn / (tn + fp) if tn + fp else None
        f1 = 2 * prec * rec / (prec + rec) if prec and rec else 0.0
        bal = (rec + spec) / 2 if rec is not None and spec is not None else None
        return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec,
                "specificity": spec, "f1": f1, "balancedAccuracy": bal}

    summary = {}
    for suf in suffixes:
        rows = [r for r in results if r["maskId"].endswith(suf) or (not suf)]
        if not rows:
            continue
        summary[suf or "-"] = {
            "buildings": pooled([r["buildings"] for r in rows]),
            "roadsByRadius": {rad: pooled([r["roadsByRadius"][rad] for r in rows])
                              for rad in rows[0]["roadsByRadius"]},
        }
    print("\nTOPLAM (uc bolge, mikro)")
    print(f"{'sonek':7} {'duzey':9} | {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4} | {'kesinlik':>8} "
          f"{'duyarlilik':>10} {'ozgulluk':>8} {'F1':>6} {'dengeli-dog':>11}")
    for suf, sm in summary.items():
        items = [("bina", sm["buildings"])] + [(f"yol r={k}", v) for k, v in sm["roadsByRadius"].items()]
        for name, c in items:
            print(f"{suf:7} {name:9} | {c['tp']:4d} {c['fp']:4d} {c['fn']:4d} {c['tn']:4d} | "
                  f"{fmt(c['precision']):>8} {fmt(c['recall']):>10} {fmt(c['specificity']):>8} "
                  f"{fmt(c['f1']):>6} {fmt(c['balancedAccuracy']):>11}")

    out = Path(args.out) if args.out else MASK_ROOT / f"validation_{args.dataset}.json"
    out.write_text(json.dumps({"perMask": results, "pooled": summary}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
