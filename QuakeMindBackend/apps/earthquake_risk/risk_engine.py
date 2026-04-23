import math
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None

try:
    from geopy.geocoders import Nominatim
except ImportError:
    Nominatim = None

# --- CONSTANTS ---

# Detaylı Fay Hatları (Yaklaşık Koordinatlar)
FAULT_LINES = [
    # Kuzey Anadolu Fayı (NAF) - Segmentler halinde
    [
        (40.4, 26.5), (40.6, 27.5), (40.8, 28.5), (40.9, 29.5), # Marmara
        (40.8, 30.5), (40.8, 31.5), (40.9, 32.5), (41.0, 33.5), # Batı Karadeniz
        (40.8, 34.5), (40.7, 35.5), (40.6, 36.5), (40.3, 37.5), # Orta Anadolu
        (40.0, 38.5), (39.8, 39.5), (39.7, 40.5)  # Doğuya doğru
    ],
    # Doğu Anadolu Fayı (EAF)
    [
        (36.2, 36.1), (36.5, 36.3), (37.0, 36.8), (37.4, 37.0), # Hatay - Maraş
        (37.8, 37.5), (38.0, 38.0), (38.3, 38.8), (38.5, 39.5), # Malatya - Elazığ
        (38.8, 40.5), (39.0, 41.0) # Bingöl
    ],
    # Batı Anadolu Fay Zonları (Ege Grabenleri)
    [(39.5, 26.0), (39.5, 27.0), (39.5, 28.0)], # Edremit
    [(38.5, 26.5), (38.5, 27.5), (38.5, 28.5)], # İzmir
    [(37.8, 27.0), (37.8, 28.0), (37.8, 29.0)], # Aydın
    [(37.2, 27.5), (37.2, 28.5), (37.2, 29.5)], # Muğla
]

# Risk hesaplaması için tüm noktaları tek bir listede topla
FAULT_POINTS = [point for line in FAULT_LINES for point in line]

RISK_FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "depth",
    "rolling_mean_7d",
    "rolling_std_7d",
    "rolling_max_7d",
    "event_count_7d",
    "year",
    "month",
    "day",
    "hour",
    "day_of_year",
    "days_since_start",
    "sin_month",
    "cos_month",
    "sin_hour",
    "cos_hour",
    "distance_to_fault",
]

# --- HELPER FUNCTIONS ---

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def simple_declustering(
    df,
    time_col="time",
    lat_col="latitude",
    lon_col="longitude",
    mag_col="mag",
    time_window_days=1.0,
    space_window_km=50.0,
):
    df = df.sort_values(time_col).reset_index(drop=True)
    is_aftershock = np.zeros(len(df), dtype=bool)

    times = df[time_col].values
    lats = df[lat_col].values
    lons = df[lon_col].values
    mags = df[mag_col].values

    for i in range(len(df)):
        if is_aftershock[i]:
            continue
        t_main = times[i]
        lat_main = lats[i]
        lon_main = lons[i]
        mag_main = mags[i]

        j = i + 1
        while j < len(df):
            dt_days = (
                (times[j] - t_main).astype("timedelta64[s]").astype(float) / 86400.0
            )
            if dt_days > time_window_days:
                break
            dist = haversine(lat_main, lon_main, lats[j], lons[j])
            if dist <= space_window_km and mags[j] <= mag_main:
                is_aftershock[j] = True
            j += 1

    df["is_aftershock"] = is_aftershock
    return df


def build_label_30d(
    df,
    time_col="time",
    lat_col="latitude",
    lon_col="longitude",
    mag_col="mag",
    thr_mag=4.0,
    horizon_days=30,
    radius_km=100.0,
):
    df = df.sort_values(time_col).reset_index(drop=True)
    n = len(df)
    label = np.zeros(n, dtype=int)

    times = df[time_col].values
    lats = df[lat_col].values
    lons = df[lon_col].values
    mags = df[mag_col].values

    big_idx = np.where(mags >= thr_mag)[0]
    big_times = times[big_idx]
    big_lats = lats[big_idx]
    big_lons = lons[big_idx]

    p = 0
    for i in range(n):
        t_i = times[i]
        lat_i = lats[i]
        lon_i = lons[i]
        horizon = t_i + np.timedelta64(horizon_days, "D")

        while p < len(big_idx) and big_idx[p] <= i:
            p += 1

        q = p
        while q < len(big_idx) and big_times[q] <= horizon:
            dist = haversine(lat_i, lon_i, big_lats[q], big_lons[q])
            if dist <= radius_km:
                label[i] = 1
                break
            q += 1

    df["label_30d"] = label
    return df


def add_fault_distance(df, lat_col="latitude", lon_col="longitude"):
    d_list = []
    for la, lo in zip(df[lat_col].values, df[lon_col].values):
        d = min([haversine(la, lo, f[0], f[1]) for f in FAULT_POINTS])
        d_list.append(d)
    df["distance_to_fault"] = d_list
    return df


def fault_hazard_score(dist_km):
    if dist_km < 30:
        return 1.0
    if dist_km < 80:
        return 0.7
    if dist_km < 150:
        return 0.4
    return 0.1


def nearest_fault_distance(lat, lon):
    return min([haversine(lat, lon, f[0], f[1]) for f in FAULT_POINTS])


# --- ENGINE CLASS ---

class EarthquakeRiskEngine:
    def __init__(self, csv_path=None):
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_QUERY_CSV
        self.df_full = None
        self.df_main = None
        self.model = None
        self.geolocator = None

    def _check_dependencies(self):
        missing = []
        if CatBoostClassifier is None:
            missing.append("catboost")
        if Nominatim is None:
            missing.append("geopy")
        if missing:
            raise RuntimeError(
                f"Gerekli paketler eksik: {', '.join(missing)}. "
                "pip install catboost geopy komutunu çalıştır."
            )

    def _prepare_frames(self):
        if self.df_full is not None and self.df_main is not None:
            return
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Veri dosyası bulunamadı: {self.csv_path}. "
                "CSV'yi data klasörüne query.csv adıyla ekle."
            )

        df = pd.read_csv(self.csv_path)
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)

        df = simple_declustering(
            df,
            time_col="time",
            lat_col="latitude",
            lon_col="longitude",
            mag_col="mag",
            time_window_days=1.0,
            space_window_km=50.0,
        )

        df_main = df[~df["is_aftershock"]].copy().reset_index(drop=True)
        df_main = build_label_30d(
            df_main,
            time_col="time",
            lat_col="latitude",
            lon_col="longitude",
            mag_col="mag",
            thr_mag=4.0,
            horizon_days=30,
            radius_km=100.0,
        )

        df_main = df_main.sort_values("time").reset_index(drop=True)
        df_main["rolling_mean_7d"] = df_main["mag"].rolling(window=7).mean()
        df_main["rolling_std_7d"] = df_main["mag"].rolling(window=7).std()
        df_main["rolling_max_7d"] = df_main["mag"].rolling(window=7).max()
        df_main["event_count_7d"] = df_main["mag"].rolling(window=7).count()

        df_main["year"] = df_main["time"].dt.year
        df_main["month"] = df_main["time"].dt.month
        df_main["day"] = df_main["time"].dt.day
        df_main["hour"] = df_main["time"].dt.hour
        df_main["day_of_year"] = df_main["time"].dt.dayofyear
        df_main["days_since_start"] = (df_main["time"] - df_main["time"].min()).dt.days

        df_main["sin_month"] = np.sin(2 * np.pi * df_main["month"] / 12)
        df_main["cos_month"] = np.cos(2 * np.pi * df_main["month"] / 12)
        df_main["sin_hour"] = np.sin(2 * np.pi * df_main["hour"] / 24)
        df_main["cos_hour"] = np.cos(2 * np.pi * df_main["hour"] / 24)

        df_main = add_fault_distance(df_main, lat_col="latitude", lon_col="longitude")
        df_main = df_main.dropna().reset_index(drop=True)

        self.df_full = df
        self.df_main = df_main

    def _train_short_model(self):
        if self.model is not None:
            return
        self._prepare_frames()
        if len(self.df_main) < 20:
            raise RuntimeError("Model eğitimine yetecek kadar kayıt yok.")
        if CatBoostClassifier is None:
            raise RuntimeError("catboost paketi yüklü olmalı.")

        x = self.df_main[RISK_FEATURE_COLUMNS]
        y = self.df_main["label_30d"].astype(int)

        tscv = TimeSeriesSplit(n_splits=5)
        model = CatBoostClassifier(
            iterations=800,
            depth=8,
            learning_rate=0.03,
            loss_function="Logloss",
            random_seed=42,
            verbose=False,
        )

        # Son katmanda eğit
        for train_idx, test_idx in tscv.split(x):
            x_train_final, _ = x.iloc[train_idx], x.iloc[test_idx]
            y_train_final, _ = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(x_train_final, y_train_final)
        self.model = model

    def _compute_long_term_hazard(
        self, city_lat, city_lon, radius_km=200.0, mag_threshold=6.0, years_window=None
    ):
        df_full = self.df_full.copy().sort_values("time")
        dists = haversine(
            city_lat,
            city_lon,
            df_full["latitude"].values,
            df_full["longitude"].values,
        )
        sub = df_full[dists <= radius_km].copy()
        if sub.empty:
            return 0.0

        if years_window is None:
            years = (sub["time"].max() - sub["time"].min()).days / 365.25
        else:
            years = years_window

        if years <= 0:
            return 0.0

        n_big = (sub["mag"] >= mag_threshold).sum()
        lam = n_big / years if n_big > 0 else 0.01 / years
        t = 10.0
        p10 = 1 - math.exp(-lam * t)
        return max(0.0, min(1.0, p10))

    def _compute_short_term_ml_risk(self, city_lat, city_lon):
        df_main = self.df_main
        model = self.model

        latest_time = df_main["time"].max()
        one_year_ago = latest_time - pd.Timedelta(days=365)
        recent = df_main[df_main["time"] >= one_year_ago].copy()

        dists = haversine(
            city_lat,
            city_lon,
            recent["latitude"].values,
            recent["longitude"].values,
        )
        recent["dist_to_city"] = dists
        local = recent[recent["dist_to_city"] <= 150.0].copy()

        if len(local) >= 7:
            last_events = local.sort_values("time").tail(7)
        else:
            last_events = df_main.sort_values("time").tail(7)

        rolling_mean_7d = last_events["mag"].mean()
        rolling_std_7d = last_events["mag"].std()
        rolling_max_7d = last_events["mag"].max()
        event_count_7d = len(last_events)

        t_ref = df_main["time"].max()
        year = t_ref.year
        month = t_ref.month
        day = t_ref.day
        hour = t_ref.hour
        day_of_year = t_ref.timetuple().tm_yday
        days_since_start = (t_ref - df_main["time"].min()).days

        sin_month = np.sin(2 * np.pi * month / 12)
        cos_month = np.cos(2 * np.pi * month / 12)
        sin_hour = np.sin(2 * np.pi * hour / 24)
        cos_hour = np.cos(2 * np.pi * hour / 24)

        dist_fault = nearest_fault_distance(city_lat, city_lon)
        depth_mean = df_main["depth"].mean()

        row = pd.DataFrame(
            [
                {
                    "latitude": city_lat,
                    "longitude": city_lon,
                    "depth": depth_mean,
                    "rolling_mean_7d": rolling_mean_7d,
                    "rolling_std_7d": rolling_std_7d,
                    "rolling_max_7d": rolling_max_7d,
                    "event_count_7d": event_count_7d,
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "day_of_year": day_of_year,
                    "days_since_start": days_since_start,
                    "sin_month": sin_month,
                    "cos_month": cos_month,
                    "sin_hour": sin_hour,
                    "cos_hour": cos_hour,
                    "distance_to_fault": dist_fault,
                }
            ]
        )

        proba = model.predict_proba(row[RISK_FEATURE_COLUMNS])[0][1]
        return max(0.0, min(1.0, proba))

    def _risk_category(self, score):
        if score < 0.25:
            return "🟢 DÜŞÜK"
        if score < 0.50:
            return "🟡 ORTA"
        if score < 0.75:
            return "🟠 YÜKSEK"
        return "🔴 ÇOK YÜKSEK"

    def predict_city_risk(self, city_name, country_hint="Turkey", manual_coords=None):
        self._check_dependencies()
        self._prepare_frames()
        self._train_short_model()

        if manual_coords:
            city_lat, city_lon = manual_coords
        else:
            if self.geolocator is None and Nominatim is not None:
                self.geolocator = Nominatim(user_agent="eq-risk-ui")
            if self.geolocator is None:
                raise RuntimeError("Geocode için geopy gerekli.")
            loc = self.geolocator.geocode(f"{city_name}, {country_hint}")
            if loc is None:
                raise RuntimeError(f"Şehir bulunamadı: {city_name}")
            city_lat, city_lon = loc.latitude, loc.longitude

        # Koordinatları sakla (Harita için)
        self.last_lat = city_lat
        self.last_lon = city_lon

        short_risk = self._compute_short_term_ml_risk(city_lat, city_lon)
        long_hazard = self._compute_long_term_hazard(
            city_lat, city_lon, radius_km=200.0, mag_threshold=6.0
        )
        dist_fault = nearest_fault_distance(city_lat, city_lon)
        fault_score = fault_hazard_score(dist_fault)

        final_score = 0.4 * short_risk + 0.3 * long_hazard + 0.3 * fault_score

        short_cat = self._risk_category(short_risk)
        long_cat = self._risk_category(long_hazard)
        fault_cat = self._risk_category(fault_score)
        final_cat = self._risk_category(final_score)

        summary = [
            f"📍 Şehir: {city_name}",
            f"Konum: {city_lat:.4f}, {city_lon:.4f}",
            f"Kısa Vadeli Risk (30 gün, M≥4): {short_risk*100:.2f}%  {short_cat}",
            f"Uzun Vadeli Tehlike (10 yıl, M≥6): {long_hazard*100:.2f}%  {long_cat}",
            f"Fay Segment Riski (mesafe {dist_fault:.1f} km): {fault_cat}",
            f"Nihai Risk Skoru: {final_score*100:.2f}%  {final_cat}",
        ]
        return "\n".join(summary)
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUERY_CSV = BASE_DIR / "data" / "query.csv"
