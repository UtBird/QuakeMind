"""
Sekil 3 -- Calisma alani haritasi.
Gercek veri kaynaklari:
  - 8 operasyon bolgesi merkezi: 05_risk_skoru/local_run/district_coords.json
    (scenario.py DISTRICTS sozlugundeki Nominatim sorgularindan geocode edilmis)
  - Analiz yaricapi 3 km: scenario.py RADIUS_M = 3000.0 (OSM graph indirme yaricapi)
  - Iki dis merkez (Pazarcik Mw7.8/AFAD 7.7, Elbistan Mw7.5/AFAD 7.6):
    backend/apps/earthquake_risk/data/query.csv (USGS katalogu)
  - Fay hatti: backend/.../fault_maps/fay_haritasi/gem_active_faults_harmonized.geojson
    (GEM global aktif fay veritabani, calisma alani bounding box'iyla filtrelenmis)
  - Zemin: OpenStreetMap karo servisi (contextily), acik lisansli.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import contextily as ctx
import contextily.tile as ctx_tile
from pyproj import Transformer

ctx_tile.USER_AGENT = "QuakeMind-academic-figure/1.0 (contact: research use, single fetch)"

REPO = Path(__file__).resolve().parents[3]
DIST_COORDS = REPO / "model_benchmarks/05_risk_skoru/local_run/district_coords.json"
FAULTS_GEOJSON = Path(r"C:/Users/utkuc/AppData/Local/Temp/claude/C--Users-utkuc-Desktop-Makale-QuakeMind/9b96d986-c24f-430a-94ae-7714dfb6dc7a/scratchpad/figs/eafz_faults.geojson")
OUT_PATH = Path(__file__).resolve().parent / "results" / "figure3_studyarea.png"

DISTRICTS = {
    "H-Z1": {"il": "Hatay"}, "H-Z2": {"il": "Hatay"}, "H-Z3": {"il": "Hatay"},
    "H-Z4": {"il": "Hatay"}, "H-Z5": {"il": "Hatay"},
    "K-Z1": {"il": "Kahramanmaraş"}, "K-Z2": {"il": "Kahramanmaraş"}, "K-Z3": {"il": "Kahramanmaraş"},
}
RADIUS_M = 3000.0

EPICENTERS = [
    {"name": "Pazarcık (04.17, Mw 7,7)", "lat": 37.2256, "lon": 37.0143},
    {"name": "Elbistan (13.24, Mw 7,6)", "lat": 38.0106, "lon": 37.1962},
]

IL_COLOR = {"Hatay": "#2f6fed", "Kahramanmaraş": "#e2711d"}

to_merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def main():
    coords = json.loads(DIST_COORDS.read_text(encoding="utf-8"))
    faults = json.loads(FAULTS_GEOJSON.read_text(encoding="utf-8"))

    fig, ax = plt.subplots(figsize=(9, 8))

    # --- fault lines ---
    for feat in faults["features"]:
        geom = feat["geometry"]
        lines = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]
        for line in lines:
            xs, ys = zip(*[to_merc.transform(lon, lat) for lon, lat in line])
            ax.plot(xs, ys, color="#8a2be2", linewidth=1.6, alpha=0.85, zorder=3,
                     label="Doğu Anadolu Fay Zonu" if feat is faults["features"][0] and line is lines[0] else None)

    # --- region markers + 3 km analysis radius ---
    seen_il = set()
    for code, (lat, lon) in coords.items():
        il = DISTRICTS[code]["il"]
        x, y = to_merc.transform(lon, lat)
        color = IL_COLOR[il]
        circ = plt.Circle((x, y), RADIUS_M, color=color, alpha=0.18, zorder=4)
        ax.add_patch(circ)
        ax.scatter([x], [y], s=55, color=color, edgecolor="white", linewidth=1.2, zorder=6,
                    label=il if il not in seen_il else None)
        seen_il.add(il)
        ax.annotate(code, (x, y), textcoords="offset points", xytext=(7, 6),
                    fontsize=10, fontweight="bold", color="#222222", zorder=7)

    # --- epicenters ---
    for ep in EPICENTERS:
        x, y = to_merc.transform(ep["lon"], ep["lat"])
        ax.scatter([x], [y], marker="*", s=420, color="#d7263d", edgecolor="white",
                    linewidth=1.2, zorder=8, label="Dış merkez" if ep is EPICENTERS[0] else None)
        ax.annotate(ep["name"], (x, y), textcoords="offset points", xytext=(10, -14),
                    fontsize=9.5, color="#7a1020", fontweight="bold", zorder=8)

    # extents with margin
    xs_all = [to_merc.transform(lon, lat)[0] for lat, lon in coords.values()] + \
             [to_merc.transform(e["lon"], e["lat"])[0] for e in EPICENTERS]
    ys_all = [to_merc.transform(lon, lat)[1] for lat, lon in coords.values()] + \
             [to_merc.transform(e["lon"], e["lat"])[1] for e in EPICENTERS]
    mx = (max(xs_all) - min(xs_all)) * 0.18 + 8000
    my = (max(ys_all) - min(ys_all)) * 0.18 + 8000
    ax.set_xlim(min(xs_all) - mx, max(xs_all) + mx)
    ax.set_ylim(min(ys_all) - my, max(ys_all) + my)

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution_size=6)

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="lower right", fontsize=10, framealpha=0.9)

    fig.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=220, facecolor="white")
    print("yazildi ->", OUT_PATH)


if __name__ == "__main__":
    main()
