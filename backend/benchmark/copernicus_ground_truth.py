"""Copernicus EMS EMSR648 gercek hasar zemin dogrulamasini (ground truth)
okuyup benchmark senaryolari icin kullanilabilir hale getirir.

Kaynak: mapping.emergency.copernicus.eu/activations/EMSR648 -- Kahramanmaras
(AOI04) ve Hatay/Antakya (AOI11) icin resmi "Grading" urunleri, dogrudan
public S3 bucket'indan (kayit/login gerekmeden) indirildi:
benchmark/data/copernicus/*.zip

Her aktivasyon icin iki gecis var: "PRODUCT" (ilk hizli degerlendirme) ve
"MONIT01" (sonraki, daha kapsamli izleme gecisi). MONIT01'in gercek hasar
sayilari acikca daha zengin (orn. AOI04 yollarinda PRODUCT'ta 0 hasarli yol
varken MONIT01'de 134 hasarli yol var) -- bu yuzden birincil kaynak olarak
MONIT01 kullaniliyor, PRODUCT sadece capraz referans icin saklaniyor.
"""

import json
import re
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

DATA_DIR = Path(__file__).resolve().parent / "data"
COPERNICUS_DIR = DATA_DIR / "copernicus"
EXTRACTED_DIR = COPERNICUS_DIR / "extracted"

# damage_gra degerleri "No visible damage" / "Not Analysed" / "Not Applicable"
# disinda kalan her sey gercek bir hasar demek.
DAMAGED_GRADES = {"Destroyed", "Damaged", "Possibly damaged"}

REGION_LAYERS = {
    "kahramanmaras": {
        "zip": "EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1_vector.zip",
        "extract_dir": "aoi04_monit01",
        "roads_glob": "*transportationL*.json",
        "buildings_glob": "*builtUpP*.json",
    },
    "hatay": {
        "zip": "EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip",
        "extract_dir": "aoi11_monit01",
        "roads_glob": "*transportationL*.json",
        "buildings_glob": "*builtUpA*.json",
    },
}


def _ensure_extracted(region_key: str) -> Path:
    cfg = REGION_LAYERS[region_key]
    out_dir = EXTRACTED_DIR / cfg["extract_dir"]
    if not out_dir.exists() or not any(out_dir.iterdir()):
        zip_path = COPERNICUS_DIR / cfg["zip"]
        if not zip_path.exists():
            raise FileNotFoundError(
                f"{zip_path} bulunamadi. Once EMSR648 vector paketlerini "
                f"benchmark/data/copernicus/ altina indirin."
            )
        out_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    return out_dir


def _centroid(geometry: dict) -> tuple[float, float]:
    """Point/LineString/Polygon(+Multi*) icin kaba ama yeterli bir merkez nokta."""
    coords_flat: list[tuple[float, float]] = []

    def _walk(c):
        if isinstance(c[0], (int, float)):
            coords_flat.append((c[0], c[1]))
        else:
            for sub in c:
                _walk(sub)

    _walk(geometry["coordinates"])
    lon = sum(c[0] for c in coords_flat) / len(coords_flat)
    lat = sum(c[1] for c in coords_flat) / len(coords_flat)
    return lat, lon


def _line_coords(geometry: dict) -> list[list[float]]:
    """LineString/MultiLineString -> [[lat, lon], ...] tek bir hat listesi."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    if gtype == "LineString":
        return [[c[1], c[0]] for c in coords]
    if gtype == "MultiLineString":
        # en uzun parcayi al -- coklu kesintili parcalarin tamamini birlestirmek
        # anlamsiz bir yol geometrisi uretir.
        longest = max(coords, key=len)
        return [[c[1], c[0]] for c in longest]
    return []


def load_region_ground_truth(region_key: str) -> dict:
    cfg = REGION_LAYERS[region_key]
    extract_dir = _ensure_extracted(region_key)

    roads_files = list(extract_dir.glob(cfg["roads_glob"]))
    buildings_files = list(extract_dir.glob(cfg["buildings_glob"]))
    if not roads_files or not buildings_files:
        raise FileNotFoundError(f"{region_key}: roads/buildings GeoJSON bulunamadi ({extract_dir}).")

    with open(roads_files[0], encoding="utf-8") as f:
        roads_gj = json.load(f)
    with open(buildings_files[0], encoding="utf-8") as f:
        buildings_gj = json.load(f)

    damaged_roads = []
    for feat in roads_gj["features"]:
        grade = feat["properties"].get("damage_gra")
        if grade not in DAMAGED_GRADES:
            continue
        line = _line_coords(feat["geometry"])
        if not line:
            continue
        lat, lon = _centroid(feat["geometry"])
        damaged_roads.append({
            "name": feat["properties"].get("name") or "Isimsiz yol",
            "damageGrade": grade,
            "lat": lat,
            "lon": lon,
            "coords": line,
        })

    damaged_buildings = []
    for feat in buildings_gj["features"]:
        grade = feat["properties"].get("damage_gra")
        if grade not in DAMAGED_GRADES:
            continue
        lat, lon = _centroid(feat["geometry"])
        damaged_buildings.append({
            "objType": feat["properties"].get("obj_type"),
            "damageGrade": grade,
            "lat": lat,
            "lon": lon,
        })

    return {
        "region": region_key,
        "source": cfg["zip"],
        "totalRoadSegments": len(roads_gj["features"]),
        "damagedRoadSegments": damaged_roads,
        "totalBuildings": len(buildings_gj["features"]),
        "damagedBuildings": damaged_buildings,
    }


# --------------------------------------------------------------------------
# Kapanma katmani icin: paketten dogrudan okuma (zip icinden, cikartmadan)
# --------------------------------------------------------------------------
# Hangi EMSR derecelerinin yolu KAPATTIGI bir karardir (M-26 / Tablo 19);
# uc kural birlikte raporlanabilsin diye adlandirilmistir. Projenin geri
# kalaninda (dogrulama, J-12) "hasarli" = DAMAGED_GRADES = gevsek kural.
ROAD_GRADE_RULES = {
    "strict": frozenset({"Destroyed"}),
    "medium": frozenset({"Destroyed", "Damaged"}),
    "loose": frozenset(DAMAGED_GRADES),
}
# Yalnizca bu klasordeki, bu bicimdeki dosya adlari kabul edilir (API'den
# gelen bir degerle dosya sisteminde gezinilmesin).
EMSR_PACKAGE_RE = re.compile(r"EMSR648_AOI\d{2}_GRA_[A-Z0-9]+_r1_[A-Z0-9]+_v\d+_vector\.zip")


def _iter_line_parts(geometry):
    if geometry["type"] == "LineString":
        yield geometry["coordinates"]
    elif geometry["type"] == "MultiLineString":
        yield from geometry["coordinates"]


@lru_cache(maxsize=16)
def _package_layers(package: str):
    """(yol kayitlari, AOI halkalari) -- paket basina bir kez okunur."""
    if not EMSR_PACKAGE_RE.fullmatch(package or ""):
        raise ValueError(f"Gecersiz EMSR paket adi: {package!r}")
    path = COPERNICUS_DIR / package
    if not path.exists():
        raise FileNotFoundError(f"{path} yok -- paketi benchmark/data/copernicus/ altina indirin.")
    with zipfile.ZipFile(path) as zf:
        def layer(pattern):
            names = [n for n in zf.namelist() if n.endswith(".json") and pattern in n]
            return json.loads(zf.read(names[0]))["features"] if names else []

        roads = tuple(
            (f["properties"].get("damage_gra"),
             tuple(tuple((float(x), float(y)) for x, y, *_ in part) for part in _iter_line_parts(f["geometry"])))
            for f in layer("transportationL")
        )
        rings = []
        for f in layer("areaOfInterestA"):
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for poly in polys:
                rings.append(tuple((float(x), float(y)) for x, y, *_ in poly[0]))
    return roads, tuple(rings)


def damaged_road_lines(package: str, rule: str = "loose", bbox=None, margin_deg: float = 0.002):
    """Kurala gore hasarli sayilan yol cizgileri: [[(lon, lat), ...], ...].
    `bbox` verilirse yalnizca kutuya (payla) degen cizgiler doner."""
    grades = ROAD_GRADE_RULES[rule]
    roads, _ = _package_layers(package)
    out = []
    for grade, parts in roads:
        if grade not in grades:
            continue
        for part in parts:
            if bbox is not None:
                w, s, e, n = bbox
                if not any(w - margin_deg <= x <= e + margin_deg and s - margin_deg <= y <= n + margin_deg
                           for x, y in part):
                    continue
            out.append(list(part))
    return out


def road_grade_counts(package: str, bbox=None):
    """Kutudaki EMSR yol kayitlarinin derece dagilimi (raporlama icin)."""
    roads, _ = _package_layers(package)
    counts = {}
    for grade, parts in roads:
        if bbox is not None:
            w, s, e, n = bbox
            if not any(w <= x <= e and s <= y <= n for part in parts for x, y in part):
                continue
        counts[grade] = counts.get(grade, 0) + 1
    return counts


def aoi_rings(package: str):
    """Copernicus'un GERCEKTEN inceledigi alanin halkalari."""
    return [list(r) for r in _package_layers(package)[1]]


def main():
    for region_key in REGION_LAYERS:
        print(f"[{region_key}] Copernicus EMSR648 ground truth cikariliyor...")
        gt = load_region_ground_truth(region_key)
        out_path = DATA_DIR / f"{region_key}_copernicus_ground_truth.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        print(
            f"[{region_key}] {len(gt['damagedRoadSegments'])}/{gt['totalRoadSegments']} "
            f"hasarli yol, {len(gt['damagedBuildings'])}/{gt['totalBuildings']} hasarli bina "
            f"-> {out_path}"
        )


if __name__ == "__main__":
    main()
