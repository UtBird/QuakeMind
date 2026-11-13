"""Senaryo v2'nin 8 bolgesi icin yol grafi cache'ini on-isitir.

warm_rich_sim_cache.py ile AYNI desen -- tek farki bolge listesini
scenario_dataset.py'den okumasi (tek dogruluk kaynagi) ve "mevcut-cache"
isaretli bolgeleri atlamasi.

Neden gerekli: /api/road_damage/simulate_closures canli istekte SADECE
onceden pre-warm edilmis pickle'i okur (load_local_graph_from_cache), asla
PBF taramasi baslatmaz -- worker'in timeout'unu asmamak icin. Yani bu script
kosmadan yeni bolgeler icin simulasyon calismaz.

network_type='walk': simulate_closures'un kullandigi tip (bkz.
fastapi_app.py::simulate_road_closures) -- cache anahtari tipe bagli oldugu
icin ayni tiple isitilmali.

Kullanim:
  python benchmark/warm_scenario_v2_cache.py            # eksik olanlari isit
  python benchmark/warm_scenario_v2_cache.py --check    # sadece durum raporu
"""
import argparse
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apps.road_damage.utils.assembly import bbox_from_center  # noqa: E402
from apps.road_damage.utils.network import (  # noqa: E402
    build_local_graph_from_pbf,
    load_local_graph_from_cache,
)
from scenario_dataset import ZONES  # noqa: E402

NETWORK_TYPE = "walk"


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Sadece cache durumunu raporla, isitma yapma.")
    args = parser.parse_args()

    missing = []
    for zone in ZONES:
        lat, lon = zone["center"]
        bbox = bbox_from_center(lat, lon, zone["radiusKm"])
        cached = load_local_graph_from_cache(bbox, network_type=NETWORK_TYPE)
        if cached is not None:
            _safe_print(f"[{zone['id']}] {zone['label']}: cache VAR "
                        f"({cached.number_of_nodes()} dugum, {cached.number_of_edges()} kenar)")
        else:
            _safe_print(f"[{zone['id']}] {zone['label']}: cache YOK")
            missing.append((zone, bbox))

    if args.check:
        _safe_print(f"\n{len(ZONES) - len(missing)}/{len(ZONES)} bolge hazir.")
        return 0 if not missing else 1

    if not missing:
        _safe_print("\nTum bolgeler zaten hazir.")
        return 0

    _safe_print(f"\n{len(missing)} bolge PBF'ten cikarilacak (her biri dakikalar surebilir)...\n")
    failed = []
    for zone, bbox in missing:
        t0 = time.time()
        _safe_print(f"[{zone['id']}] {zone['label']} cikariliyor...")
        try:
            G = build_local_graph_from_pbf(bbox, network_type=NETWORK_TYPE, cache=True)
            _safe_print(f"[{zone['id']}] OK -- {G.number_of_nodes()} dugum, "
                        f"{G.number_of_edges()} kenar ({time.time() - t0:.0f}s)")
        except Exception as e:
            _safe_print(f"[{zone['id']}] HATA -- {e}")
            failed.append(zone["id"])

    if failed:
        _safe_print(f"\nBASARISIZ: {', '.join(failed)}")
        return 1
    _safe_print("\nTum bolgeler hazir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
