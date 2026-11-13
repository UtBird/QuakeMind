"""
Gercek EMSR648 (Copernicus EMS) yol hasari derecelendirmesini OSM yol
cizgesine kapanma olarak esler.

Kaynak veri: https://mapping.emergency.copernicus.eu/activations/EMSR648/
  AOI-04 Kahramanmaras -> GRA_MONIT01 transportationL katmani
  AOI-11 Hatay          -> GRA_MONIT01 transportationL katmani
Bu iki katman dogrudan Copernicus S3 kovasindan indirilip
backend/apps/road_damage/data/emsr648/{AOI04,AOI11}/ altina
kondu (2026-09-17). damage_gra alani: "No visible damage" | "Possibly
damaged" | "Damaged" | "Destroyed" | "Not Analysed".

Makale Tablo 4 / Bolum 3.2 uc kurali:
  katı   (strict) : yalniz Destroyed kapali
  orta   (medium) : Destroyed + Damaged kapali
  gevsek (loose)  : Destroyed + Damaged + Possibly damaged kapali

Esleme kurali (M-76 duzeltmesiyle uyumlu, Bolum 3.2 P339):
  bir OSM kenari, geometrisi boyunca ~2 m araliklarla ornekklenen
  noktalarinin en az %50'si kapali sayilan bir EMSR648 kesitinin 8 m
  yakininda ise kapali kabul edilir.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.prepared import prep

REPO = Path(__file__).resolve().parents[3]
EMSR_DIR = REPO / "backend" / "apps" / "road_damage" / "data" / "emsr648"

AOI_FILES = {
    "AOI04": EMSR_DIR / "AOI04" / "EMSR648_AOI04_GRA_MONIT01_transportationL_r1_v1.json",
    "AOI11": EMSR_DIR / "AOI11" / "EMSR648_AOI11_GRA_MONIT01_transportationL_r1_v2.json",
}

RULES = {
    "strict": {"Destroyed"},
    "medium": {"Destroyed", "Damaged"},
    "loose": {"Destroyed", "Damaged", "Possibly damaged"},
}

BUFFER_M = 8.0
SAMPLE_STEP_M = 2.0
COVERAGE_FRACTION = 0.5
METRIC_CRS = "EPSG:32637"  # UTM 37N - Hatay ve Kahramanmaras icin yeterli dogrulukta


def load_aoi(aoi_code):
    """AOI04 | AOI11 -> GeoDataFrame (EPSG:4326), damage_gra sutunuyla."""
    path = AOI_FILES[aoi_code]
    if not path.exists():
        raise FileNotFoundError(f"EMSR648 verisi bulunamadi: {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf


def damage_counts(aoi_code):
    gdf = load_aoi(aoi_code)
    return gdf["damage_gra"].value_counts().to_dict()


def closure_geometry_for_rule(aoi_code, rule):
    """Verilen kural altinda kapali sayilan EMSR648 kesitlerinin tek bir
    (metrik CRS'e projekte edilmis) unary_union tampon geometrisini dondurur.
    Bos ise None."""
    grades = RULES[rule]
    gdf = load_aoi(aoi_code)
    closed = gdf[gdf["damage_gra"].isin(grades)]
    if closed.empty:
        return None
    closed_m = closed.to_crs(METRIC_CRS)
    buffered = closed_m.geometry.buffer(BUFFER_M)
    return unary_union(list(buffered))


def _sample_points(line: LineString, step_m: float):
    length = line.length
    if length <= 0:
        return [line.interpolate(0.0)]
    n = max(2, int(length / step_m) + 1)
    return [line.interpolate(t, normalized=True) for t in np.linspace(0.0, 1.0, n)]


def closed_osm_edges(G, aoi_code, rule, edge_crs="EPSG:4326"):
    """G: osmnx grafi (dugum x/y = lon/lat, EPSG:4326).
    Donen deger: kapali sayilan (u, v, k) uclulerinin kumesi (iki yon de dahil,
    fiziksel yol bazinda gruplanarak - Bolum 3.2/Algoritma 2 (a) kurali)."""
    closure_union = closure_geometry_for_rule(aoi_code, rule)
    if closure_union is None:
        return set()

    # OSM kenarlarini metrik CRS'e projekte etmek icin GeoDataFrame kur
    records = []
    for u, v, k, data in G.edges(keys=True, data=True):
        if "geometry" in data:
            line = data["geometry"]
        else:
            line = LineString([
                (G.nodes[u]["x"], G.nodes[u]["y"]),
                (G.nodes[v]["x"], G.nodes[v]["y"]),
            ])
        osmid = data.get("osmid")
        if isinstance(osmid, list):
            osmid = tuple(sorted(osmid))
        records.append({"u": u, "v": v, "k": k, "geometry": line,
                         "osmid": osmid})
    edges_gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=edge_crs)
    edges_m = edges_gdf.to_crs(METRIC_CRS)

    # Bounding-box on kontrolle cogu kenari hizlica ele: sadece tampon
    # geometrisinin kapladigi alana yakin kenarlarda nokta-bazli ornekleme
    # yapilir. prepared geometri tekil nokta testlerini de hizlandirir.
    prepared_union = prep(closure_union)
    minx, miny, maxx, maxy = closure_union.bounds
    pad = BUFFER_M
    bbox_minx, bbox_miny, bbox_maxx, bbox_maxy = minx - pad, miny - pad, maxx + pad, maxy + pad

    closed = set()
    n_candidates = 0
    for rec, line_m in zip(records, edges_m.geometry):
        elx0, ely0, elx1, ely1 = line_m.bounds
        if elx1 < bbox_minx or elx0 > bbox_maxx or ely1 < bbox_miny or ely0 > bbox_maxy:
            continue
        n_candidates += 1
        pts = _sample_points(line_m, SAMPLE_STEP_M)
        if not pts:
            continue
        inside = sum(1 for p in pts if prepared_union.intersects(p))
        frac = inside / len(pts)
        if frac >= COVERAGE_FRACTION:
            closed.add((rec["u"], rec["v"], rec["k"]))
    print(f"    [emsr648] {aoi_code}/{rule}: bbox-aday kenar={n_candidates}/{len(records)}, kapali={len(closed)}")

    # Fiziksel yol grubu: ayni (u,v) dugum cifti + ayni osmid -> her iki yon de kapat
    physical_keys = set()
    for (u, v, k) in closed:
        rec = next(r for r in records if r["u"] == u and r["v"] == v and r["k"] == k)
        physical_keys.add((frozenset((u, v)), rec["osmid"]))

    grouped = set()
    for rec in records:
        pk = (frozenset((rec["u"], rec["v"])), rec["osmid"])
        if pk in physical_keys:
            grouped.add((rec["u"], rec["v"], rec["k"]))
    return grouped


if __name__ == "__main__":
    for aoi in ("AOI04", "AOI11"):
        print(aoi, damage_counts(aoi))
