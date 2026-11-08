"""Gaussian kernel yoğunluk ısı haritası (rapor 2.4.3).

scipy'ye yeni bağımlılık eklememek için Gauss çekirdeği numpy ile hesaplanır.
Çıktı formatı bilinçli olarak leaflet.heat'in beklediği [lat, lon, intensity]
üçlüsü -- hem web hem mobil aynı formatı tüketebilir.

MIMARI.md §5'e göre iki karar burada uygulanır:

1. **Maliyet "nokta × hücre" değil "nokta + hücre".** Noktalar önce ızgaraya
   sayılır (`histogram2d`), sonra ızgaraya TEK bir ayrılabilir Gauss süzgeci
   uygulanır. Eski sürüm her nokta için tüm ızgarayı geziyordu.
2. **Normalizasyon mutlaktır.** Eski sürüm her isteği kendi maksimumuna
   bölüyordu; aynı mahalle, harita kaydırılınca başka renge giriyordu. Artık
   sabit bir referans kullanılır (`referans`, varsayılan 1,0 = bir birim
   ağırlıklı noktanın tepe değeri).

Sayısal eşdeğerlik: çekirdek tepe değeri 1'e ölçeklidir, yani tek bir birim
ağırlıklı nokta kendi hücresinde 1,0 üretir -- eski fonksiyonun tanımıyla aynı.
Tek fark noktanın kendi hücresinin merkezine yuvarlanmasıdır (yarım hücre).
"""
import numpy as np

from apps.road_damage.utils.assembly import haversine_m

# Grid hücreleri altında bu yoğunluğa (0-1) düşen noktalar cevaptan atılır --
# boş/önemsiz alanlarla payload'u şişirmemek için.
_INTENSITY_CUTOFF = 0.02

# Mutlak ölçek referansı: bir birim ağırlıklı noktanın tepe değeri.
VARSAYILAN_REFERANS = 1.0


def _haversine_km_grid(lat_grid, lon_grid, lat2, lon2):
    """haversine_m'in numpy grid üzerinde vektörize hali (km cinsinden)."""
    r_km = 6371.0
    phi1 = np.radians(lat_grid)
    phi2 = np.radians(lat2)
    d_phi = np.radians(lat2 - lat_grid)
    d_lambda = np.radians(lon2 - lon_grid)
    a = np.sin(d_phi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lambda / 2) ** 2
    return r_km * 2 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def _gauss_cekirdek(hucre_km, bandwidth_km):
    """Tepe değeri 1 olan tek boyutlu Gauss çekirdeği (hücre birimlerinde)."""
    if hucre_km <= 0:
        return np.array([1.0])
    yaricap = int(np.ceil(3.0 * bandwidth_km / hucre_km))
    yaricap = max(1, min(yaricap, 256))
    ofset = np.arange(-yaricap, yaricap + 1) * hucre_km
    return np.exp(-(ofset ** 2) / (2.0 * bandwidth_km ** 2))


def _eksende_suz(izgara, cekirdek, eksen):
    """Ayrılabilir Gauss: her eksende tek boyutlu evrişim."""
    return np.apply_along_axis(
        lambda satir: np.convolve(satir, cekirdek, mode="same"), eksen, izgara
    )


def _bilinear_dagit(izgara, nokta_lat, nokta_lon, agirlik, lats, lons, lat_adim, lon_adim):
    """Her noktanın ağırlığını dört komşu hücreye uzaklık oranıyla dağıtır."""
    boyut = izgara.shape[0]
    if lat_adim <= 0 or lon_adim <= 0:
        return

    y = (nokta_lat - lats[0]) / lat_adim
    x = (nokta_lon - lons[0]) / lon_adim
    gecerli = (y >= -0.5) & (y <= boyut - 0.5) & (x >= -0.5) & (x <= boyut - 0.5)
    y, x, agirlik = y[gecerli], x[gecerli], agirlik[gecerli]
    if y.size == 0:
        return

    y0 = np.floor(y).astype(int)
    x0 = np.floor(x).astype(int)
    fy, fx = y - y0, x - x0

    for dy, dx, pay in (
        (0, 0, (1 - fy) * (1 - fx)),
        (0, 1, (1 - fy) * fx),
        (1, 0, fy * (1 - fx)),
        (1, 1, fy * fx),
    ):
        yy, xx = y0 + dy, x0 + dx
        icerde = (yy >= 0) & (yy < boyut) & (xx >= 0) & (xx < boyut)
        np.add.at(izgara, (yy[icerde], xx[icerde]), (agirlik * pay)[icerde])


def izgara_hesapla(points, bbox, grid_size=100, bandwidth_km=0.5):
    """Ham yoğunluk ızgarası (normalizasyon ve kırpma öncesi).

    Ayrı durur ki eski yöntemle sayısal karşılaştırması yapılabilsin
    (`araclar_isi_karsilastir.py`).
    """
    west, south, east, north = bbox
    lats = np.linspace(south, north, grid_size)
    lons = np.linspace(west, east, grid_size)

    # Hücre adımları (derece).
    lat_adim = (north - south) / (grid_size - 1) if grid_size > 1 else (north - south)
    lon_adim = (east - west) / (grid_size - 1) if grid_size > 1 else (east - west)
    dizi = np.asarray(points, dtype=float)
    nokta_lat, nokta_lon, agirlik = dizi[:, 0], dizi[:, 1], dizi[:, 2]

    # 1) Sayım: maliyet nokta sayısıyla doğrusal.
    #    Nokta en yakın hücreye YUVARLANMAZ; ağırlığı dört komşu hücreye
    #    bilinear dağıtılır. Yuvarlama, tek noktalı seyrek alanlarda tepe
    #    değerini %9'a kadar kaydırıyordu (ölçüldü); dağıtımla %1'in altına iner.
    izgara = np.zeros((grid_size, grid_size), dtype=float)
    _bilinear_dagit(izgara, nokta_lat, nokta_lon, agirlik, lats, lons, lat_adim, lon_adim)

    # 2) Tek Gauss süzgeci. Hücre boyu enlem ve boylamda farklı km'ye denk
    #    geldiği için çekirdek eksen başına ayrı hesaplanır.
    orta_enlem = (south + north) / 2.0
    lat_hucre_km = lat_adim * 111.32
    lon_hucre_km = lon_adim * 111.32 * float(np.cos(np.radians(orta_enlem)))
    izgara = _eksende_suz(izgara, _gauss_cekirdek(lat_hucre_km, bandwidth_km), 0)
    izgara = _eksende_suz(izgara, _gauss_cekirdek(lon_hucre_km, bandwidth_km), 1)
    return izgara, lats, lons


def izgara_hesapla_eski(points, bbox, grid_size=100, bandwidth_km=0.5):
    """Eski yöntemin ham ızgarası: nokta başına tüm ızgara gezilir."""
    west, south, east, north = bbox
    lats = np.linspace(south, north, grid_size)
    lons = np.linspace(west, east, grid_size)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    intensity = np.zeros_like(lat_grid, dtype=float)
    two_sigma_sq = 2.0 * (bandwidth_km ** 2)
    for lat, lon, weight in points:
        dist_km = _haversine_km_grid(lat_grid, lon_grid, lat, lon)
        intensity += float(weight) * np.exp(-(dist_km ** 2) / two_sigma_sq)
    return intensity, lats, lons


def build_gaussian_heatmap(
    points, bbox, grid_size=100, bandwidth_km=0.5, referans=VARSAYILAN_REFERANS
):
    """points: [(lat, lon, weight), ...], bbox: (west, south, east, north).

    Noktalar ızgaraya sayılır, ızgaraya tek bir Gauss süzgeci uygulanır ve
    sonuç MUTLAK referansa göre 0..1 aralığına kırpılır.
    """
    if not points:
        return []

    west, south, east, north = bbox
    if not (west < east and south < north):
        return []

    izgara, lats, lons = izgara_hesapla(points, bbox, grid_size, bandwidth_km)

    # Mutlak normalizasyon: istek başına maksimuma göre ölçeklenmez.
    bolen = float(referans) if referans else VARSAYILAN_REFERANS
    normalized = np.clip(izgara / bolen, 0.0, 1.0)

    mask = normalized >= _INTENSITY_CUTOFF
    if not mask.any():
        return []

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    return [
        [round(float(lat), 6), round(float(lon), 6), round(float(val), 4)]
        for lat, lon, val in zip(lat_grid[mask], lon_grid[mask], normalized[mask])
    ]


def build_gaussian_heatmap_eski(points, bbox, grid_size=100, bandwidth_km=0.5):
    """Eski (nokta × hücre) uygulama -- yalnızca karşılaştırma için tutuluyor.

    CLAUDE.md kural 8: yeni yöntem, eski fonksiyonla aynı girdide karşılaştırılır
    ve hücre başına en büyük fark raporlanır (bkz. `araclar_isi_karsilastir.py`).
    """
    if not points:
        return []

    west, south, east, north = bbox
    if not (west < east and south < north):
        return []

    lats = np.linspace(south, north, grid_size)
    lons = np.linspace(west, east, grid_size)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    intensity = np.zeros_like(lat_grid, dtype=float)
    two_sigma_sq = 2.0 * (bandwidth_km ** 2)
    for lat, lon, weight in points:
        dist_km = _haversine_km_grid(lat_grid, lon_grid, lat, lon)
        intensity += float(weight) * np.exp(-(dist_km ** 2) / two_sigma_sq)

    max_val = float(intensity.max())
    if max_val <= 0:
        return []
    normalized = intensity / max_val

    mask = normalized >= _INTENSITY_CUTOFF
    return [
        [round(float(lat), 6), round(float(lon), 6), round(float(val), 4)]
        for lat, lon, val in zip(lat_grid[mask], lon_grid[mask], normalized[mask])
    ]


__all__ = ["build_gaussian_heatmap", "build_gaussian_heatmap_eski", "haversine_m"]
