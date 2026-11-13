"""Isi haritasi: eski (nokta x hucre) ile yeni (sayim + tek Gauss) karsilastirmasi.

CLAUDE.md kural 8 / MIMARI.md 5: yeni yontem eski fonksiyonla AYNI girdide
karsilastirilir; HAM izgaralar uzerinde hucre basina en buyuk fark ve sure
raporlanir. (Kirpilmis liste degil ham izgara karsilastirilir; kirpma esigi
iki yontemde farkli hucreleri elediginden liste karsilastirmasi yaniltir.)

    python araclar_isi_karsilastir.py
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from apps.road_damage.utils.heatmap import (  # noqa: E402
    izgara_hesapla,
    izgara_hesapla_eski,
)

BBOX = (36.10, 36.15, 36.25, 36.28)  # Antakya cevresi, ~13 x 14 km


def noktalar(adet, tohum=42):
    rng = np.random.default_rng(tohum)
    lat = rng.uniform(BBOX[1], BBOX[3], adet)
    lon = rng.uniform(BBOX[0], BBOX[2], adet)
    agirlik = rng.uniform(0.3, 1.0, adet)
    return list(zip(lat, lon, agirlik))


def main():
    print(f"{'nokta':>7} {'eski (ms)':>10} {'yeni (ms)':>10} {'hizlanma':>9} "
          f"{'en buyuk fark':>14} {'ortalama fark':>14}   (fark = |eski-yeni| / eski tepe)")
    for adet in (50, 200, 1000, 5000, 20000):
        p = noktalar(adet)

        t = time.perf_counter()
        eski, _, _ = izgara_hesapla_eski(p, BBOX, 100, 0.5)
        eski_sure = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        yeni, _, _ = izgara_hesapla(p, BBOX, 100, 0.5)
        yeni_sure = (time.perf_counter() - t) * 1000

        tepe = float(eski.max()) or 1.0
        fark = np.abs(eski - yeni) / tepe
        print(f"{adet:>7} {eski_sure:>10.1f} {yeni_sure:>10.1f} "
              f"{eski_sure / max(yeni_sure, 1e-9):>8.1f}x "
              f"{fark.max():>14.4f} {fark.mean():>14.4f}")


if __name__ == "__main__":
    main()
