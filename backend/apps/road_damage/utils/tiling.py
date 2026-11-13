"""Pure tile-zoom math, kept dependency-free so it can be imported from both
fastapi_app.py and apps/road_damage/worker.py (a ProcessPoolExecutor worker
entrypoint that must not import fastapi_app.py).
"""


def zoom_for_radius(radius_km, target_tiles=6, min_zoom=13, max_zoom=18):
    """Pick a tile zoom so the stitched image stays a bounded number of tiles
    across, regardless of the requested analysis radius.

    The Segformer inference runs over overlapping 512px patches, so its cost
    scales roughly with pixel count. A larger radiusKm would otherwise push
    more tiles into a fixed tile cap -- either silently cropping the analyzed
    area back down, or (if the cap is raised to honor the radius) inflating
    inference time a lot for a wide analysis. Scaling zoom down for a larger
    radius keeps the tile/pixel budget (and so inference time) roughly
    constant while still covering the real requested area.
    """
    z = max_zoom
    while z > min_zoom:
        km_per_tile = 40075.0 / (2 ** z)
        if (2 * radius_km) / km_per_tile <= target_tiles:
            break
        z -= 1
    return z


def zoom_for_gsd(hedef_gsd_m, lat, min_zoom=13, max_zoom=20):
    """Modelin egitim cozunurlugune EN YAKIN karo yakinlastirmasi.

    Analiz her zaman ayni standartta kossun diye yakinlastirma alan
    buyuklugunden degil MODELIN egitildigi metre/piksel degerinden secilir.
    Onceki kuralda (`zoom_for_radius`) genis alan secmek cozunurlugu dusuruyor,
    model de egitildigi olcegin disina cikip hicbir sey bulamiyordu (J-76).

    Web Mercator'da bir karo pikselinin yer olcusu enlemle degisir:
        gsd = 156543,03392 * cos(enlem) / 2^z
    """
    import math

    if not hedef_gsd_m or hedef_gsd_m <= 0:
        return max_zoom
    tam = math.log2(156543.03392 * math.cos(math.radians(lat)) / hedef_gsd_m)
    return max(min_zoom, min(max_zoom, int(round(tam))))


def gsd_of_zoom(z, lat):
    """Verilen yakinlastirmada metre/piksel."""
    import math

    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** z)
