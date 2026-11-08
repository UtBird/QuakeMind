"""Prototipin veri paketini (qm-data.js) depodaki gerçek verilerden üretir.

Kullanım (depo kökünden):
    python prototip/komuta-konsolu/veri_cikar.py

Kaynaklar (hepsi depoda mevcut):
  - Copernicus EMS EMSR648, AOI11 (Antakya) grading/monit01 katmanları
  - backend/apps/earthquake_risk/data/query.csv                    (deprem kataloğu)
  - .../fault_maps/fay_haritasi/gem_active_faults_harmonized.geojson (GEM aktif faylar)
  - .../road_damage/data/tum_turkiye_toplanma_alanlari.json        (AFAD toplanma alanları)
  - backend/benchmark/scenarios/hatay_orta.json                    (senaryo: SOS + ekipler)

Çıktı: qm-data.js  —  `window.QM = {...}`
Geometriler Douglas-Peucker ile ~2 m toleransla sadeleştirilir, 1e-5 derece tamsayıya
yuvarlanır ve delta kodlanır (3,0 MB → ~0,54 MB). Çözme kodu index.html içindeki `dec()`.
"""
import csv, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
B = os.path.join(ROOT, "backend")
COP = os.path.join(B, "benchmark", "data", "copernicus", "extracted", "aoi11_monit01")
SCALE = 100000.0
EPS = 2.2e-5          # ~2 m sadeleştirme toleransı
FAULT_EPS = 2e-4      # fay hatları kaba çizilir

CLS = {"2111-Highways": 0, "21120-Primary Road": 1, "21121-Secondary Road": 2,
       "21122-Local Road": 3, "21124-Cart Track": 4}
GRADE = {"No visible damage": 0, "Possibly damaged": 1, "Damaged": 2, "Destroyed": 3}


def layer(name):
    path = os.path.join(COP, name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["features"]


def rnd(c, p=5):
    return [round(c[0], p), round(c[1], p)]


def lines_of(geom, p=5):
    parts = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]
    out = []
    for part in parts:
        pts, last = [], None
        for pt in part:
            r = rnd(pt, p)
            if r != last:
                pts.append(r)
                last = r
        if len(pts) > 1:
            out.append(pts)
    return out


def rings_of(geom, p=5):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    out = []
    for poly in polys:
        ring, last = [], None
        for pt in poly[0]:
            r = rnd(pt, p)
            if r != last:
                ring.append(r)
                last = r
        if len(ring) >= 3:
            out.append(ring)
    return out


def dp(pts, eps):
    """Douglas-Peucker; kendi yazıldı ki shapely bağımlılığı gerekmesin."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        ax, ay = pts[i]
        bx, by = pts[j]
        dx, dy = bx - ax, by - ay
        den = dx * dx + dy * dy
        best, bi = -1.0, -1
        for k in range(i + 1, j):
            px, py = pts[k]
            if den == 0:
                dist = ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / den))
                qx, qy = ax + t * dx, ay + t * dy
                dist = ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5
            if dist > best:
                best, bi = dist, k
        if best > eps:
            keep[bi] = True
            stack.append((i, bi))
            stack.append((bi, j))
    return [p for p, k in zip(pts, keep) if k]


def enc(lines, eps, closed=False):
    """Sadeleştir, tamsayıya yuvarla, delta kodla: [x0,y0,dx,dy,...]"""
    out = []
    for ln in lines:
        p = dp(ln, eps)
        if len(p) < (3 if closed else 2):
            continue
        flat, px, py = [], 0, 0
        for x, y in p:
            ix, iy = round(x * SCALE), round(y * SCALE)
            flat += [ix - px, iy - py]
            px, py = ix, iy
        out.append(flat)
    return out


def main():
    # yollar ve hasarlı yollar
    roads_by_cls, droads = {}, []
    for f in layer("EMSR648_AOI11_GRA_MONIT01_transportationL_r1_v2.json"):
        p = f["properties"]
        cls = CLS.get(p.get("info"), 3)
        g = GRADE.get(p.get("damage_gra"), 0)
        for ln in lines_of(f["geometry"]):
            if g > 0:
                enc_ln = enc([ln], EPS)
                if enc_ln:
                    droads.append([g, enc_ln[0]])
            else:
                roads_by_cls.setdefault(cls, []).append(ln)

    # yapılar (hasar derecesine göre)
    blds_by_g, sat = {}, []
    for f in layer("EMSR648_AOI11_GRA_MONIT01_builtUpA_r1_v2.json"):
        g = GRADE.get(f["properties"].get("damage_gra"), 0)
        for r in rings_of(f["geometry"]):
            blds_by_g.setdefault(g, []).append(r)
            if g > 0:   # hasarlı yapı merkezleri = uydu kanalı
                xs = [q[0] for q in r]
                ys = [q[1] for q in r]
                sat.append([round(sum(xs) / len(xs), 5), round(sum(ys) / len(ys), 5), g])

    water = [ln for f in layer("EMSR648_AOI11_GRA_MONIT01_hydrographyL_r1_v2.json")
             for ln in lines_of(f["geometry"])]
    lakes = [r for f in layer("EMSR648_AOI11_GRA_MONIT01_hydrographyA_r1_v2.json")
             for r in rings_of(f["geometry"])]

    camps, barriers = [], []
    for f in layer("EMSR648_AOI11_GRA_MONIT01_ancillaryCrisisInfoP_r1_v2.json"):
        c = rnd(f["geometry"]["coordinates"])
        (camps if f["properties"].get("obj_type") == "Camp" else barriers).append(c)
    for f in layer("EMSR648_AOI11_GRA_MONIT01_ancillaryCrisisInfoA_r1_v2.json"):
        rs = rings_of(f["geometry"])
        if rs:
            xs = [q[0] for q in rs[0]]
            ys = [q[1] for q in rs[0]]
            camps.append([round(sum(xs) / len(xs), 5), round(sum(ys) / len(ys), 5)])

    aoi = layer("EMSR648_AOI11_GRA_MONIT01_areaOfInterestA_r1_v2.json")[0]
    ring = aoi["geometry"]["coordinates"][0]
    bbox = [round(min(p[0] for p in ring), 4), round(min(p[1] for p in ring), 4),
            round(max(p[0] for p in ring), 4), round(max(p[1] for p in ring), 4)]

    # AFAD toplanma alanları (Hatay, AOI çevresi)
    asm = []
    with open(os.path.join(B, "apps", "road_damage", "data",
                           "tum_turkiye_toplanma_alanlari.json"), encoding="utf-8") as fh:
        for rec in json.load(fh):
            if rec.get("il") != "HATAY":
                continue
            try:
                lat, lon = float(rec["enlem"]), float(rec["boylam"])
            except (TypeError, ValueError):
                continue
            if bbox[0] - .02 <= lon <= bbox[2] + .02 and bbox[1] - .02 <= lat <= bbox[3] + .02:
                asm.append([round(lon, 5), round(lat, 5),
                            (rec.get("toplanma_alani") or "").title(),
                            (rec.get("mahalle") or "").title()])

    # deprem kataloğu (bölge, Şubat 2023)
    qk = []
    with open(os.path.join(B, "apps", "earthquake_risk", "data", "query.csv"),
              encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                lat, lon, mag = float(r["latitude"]), float(r["longitude"]), float(r["mag"])
            except (TypeError, ValueError):
                continue
            if not (35.0 <= lon <= 39.6 and 35.4 <= lat <= 39.0):
                continue
            if not ("2023-02-01" <= r["time"] < "2023-04-01"):
                continue
            ts = int(datetime.datetime.strptime(r["time"][:19], "%Y-%m-%dT%H:%M:%S")
                     .replace(tzinfo=datetime.timezone.utc).timestamp())
            qk.append([round(lon, 4), round(lat, 4), round(mag, 1),
                       round(float(r["depth"] or 0), 1), ts, (r.get("place") or "").title()])
    qk.sort(key=lambda x: x[4])

    # GEM aktif faylar (bölge)
    faults = []
    fault_path = None
    for d, _, files in os.walk(os.path.join(B, "apps", "earthquake_risk", "data", "fault_maps")):
        for fn in files:
            if fn.endswith("harmonized.geojson"):
                fault_path = os.path.join(d, fn)
    if fault_path:
        with open(fault_path, encoding="utf-8") as fh:
            for f in json.load(fh)["features"]:
                if not f.get("geometry"):
                    continue
                for ln in lines_of(f["geometry"], 3):
                    if any(34.8 <= p[0] <= 39.8 and 35.2 <= p[1] <= 39.2 for p in ln):
                        faults.append(ln)

    # senaryo: SOS + ekipler + mahalle etiketleri
    with open(os.path.join(B, "benchmark", "scenarios", "hatay_orta.json"),
              encoding="utf-8") as fh:
        sc = json.load(fh)
    sos = [{"id": v["id"], "lon": round(v["lon"], 5), "lat": round(v["lat"], 5),
            "durum": v["durum"], "text": v["needText"], "mahalle": v["mahalle"],
            "sos": v["sos"]} for v in sc["afetzedeler"]]
    teams = [{"id": t["id"], "role": t["role"], "unit": t["unit"],
              "lon": round(t["startLon"], 5), "lat": round(t["startLat"], 5)}
             for t in sc["ekipler"]]
    mah = [[m["name"], round(m["centerLon"], 5), round(m["centerLat"], 5)]
           for m in sc["mahalleler"]]

    data = {
        "bbox": bbox, "scale": SCALE,
        "roads": {str(k): enc(v, EPS) for k, v in roads_by_cls.items()},
        "droads": droads,
        "blds": {str(k): enc(v, EPS, closed=True) for k, v in blds_by_g.items()},
        "water": enc(water, 3e-5), "lakes": enc(lakes, 3e-5, closed=True),
        "faults": enc(faults, FAULT_EPS),
        "camps": camps, "barriers": barriers, "sat": sat, "asm": asm,
        "quakes": qk, "sos": sos, "teams": teams, "mah": mah,
    }
    out = os.path.join(HERE, "qm-data.js")
    with open(out, "w", encoding="ascii") as fh:
        fh.write("window.QM=" + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";")

    print("yazıldı:", out, f"({os.path.getsize(out)/1024:.0f} KB)")
    print("yol:", sum(len(v) for v in data["roads"].values()),
          "· yapı:", sum(len(v) for v in data["blds"].values()),
          "· hasarlı yol:", len(droads), "· hasarlı yapı:", len(sat),
          "· deprem:", len(qk), "· toplanma:", len(asm))


if __name__ == "__main__":
    sys.exit(main())
