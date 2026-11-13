"""
Ortak veri hazirlama ve degerlendirme yardimcilari.

Bu modul, QuakeMindBackend/apps/earthquake_risk/risk_engine.py icindeki
ozellik muhendisligini birebir yeniden uretir; boylece butun model
karsilastirma defterleri AYNI veriyle, AYNI etiketle ve AYNI zaman-serisi
bolme stratejisiyle egitilir. Amac: makale icin adil bir kiyaslama.

Gorev: ikili siniflandirma
    label_30d = 1  ->  onumuzdeki 30 gun icinde, 100 km yaricapta M>=4.0
                       bir deprem oluyor.
    label_30d = 0  ->  olmuyor.

Kaynak veri: QuakeMindBackend/apps/earthquake_risk/data/query.csv
             (USGS / Kandilli deprem katalogu, ~20k kayit)
"""

from pathlib import Path

import numpy as np
import pandas as pd

# --- Proje veri yolu -------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DEFAULT_QUERY_CSV = (
    _HERE.parent.parent
    / "QuakeMindBackend"
    / "apps"
    / "earthquake_risk"
    / "data"
    / "query.csv"
)

# --- Fay mesafesi (risk_engine.py ile ayni) -------------------------------
# GEM Global Active Faults cizgilerine en kisa mesafe; urunle AYNI modul.
# 19 Ekim 2026'ya kadar burada elle yazilmis ~38 yaklasik nokta vardi
# (yalniz KAF, DAF, dort Ege grabeni). O olcumler git gecmisinde.

import sys as _sys

_RISK_KOKU = _HERE.parent.parent / "QuakeMindBackend" / "apps" / "earthquake_risk"
if str(_RISK_KOKU) not in _sys.path:
    _sys.path.insert(0, str(_RISK_KOKU))
from fay_mesafesi import en_yakin_fay_km  # noqa: E402

RISK_FEATURE_COLUMNS = [
    "latitude", "longitude", "depth",
    "rolling_mean_7d", "rolling_std_7d", "rolling_max_7d", "event_count_7d",
    "year", "month", "day", "hour", "day_of_year", "days_since_start",
    "sin_month", "cos_month", "sin_hour", "cos_hour",
    "distance_to_fault",
]

TARGET_COLUMN = "label_30d"


# --- Yardimci fonksiyonlar (risk_engine.py ile ayni) ----------------------

def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def simple_declustering(df, time_window_days=1.0, space_window_km=50.0):
    df = df.sort_values("time").reset_index(drop=True)
    is_aftershock = np.zeros(len(df), dtype=bool)
    times = df["time"].values
    lats = df["latitude"].values
    lons = df["longitude"].values
    mags = df["mag"].values
    for i in range(len(df)):
        if is_aftershock[i]:
            continue
        j = i + 1
        while j < len(df):
            dt_days = (times[j] - times[i]).astype("timedelta64[s]").astype(float) / 86400.0
            if dt_days > time_window_days:
                break
            if haversine(lats[i], lons[i], lats[j], lons[j]) <= space_window_km and mags[j] <= mags[i]:
                is_aftershock[j] = True
            j += 1
    df["is_aftershock"] = is_aftershock
    return df


def build_label_30d(df, thr_mag=4.0, horizon_days=30, radius_km=100.0):
    df = df.sort_values("time").reset_index(drop=True)
    n = len(df)
    label = np.zeros(n, dtype=int)
    times = df["time"].values
    lats = df["latitude"].values
    lons = df["longitude"].values
    mags = df["mag"].values
    big_idx = np.where(mags >= thr_mag)[0]
    big_times = times[big_idx]
    big_lats = lats[big_idx]
    big_lons = lons[big_idx]
    p = 0
    for i in range(n):
        horizon = times[i] + np.timedelta64(horizon_days, "D")
        while p < len(big_idx) and big_idx[p] <= i:
            p += 1
        q = p
        while q < len(big_idx) and big_times[q] <= horizon:
            if haversine(lats[i], lons[i], big_lats[q], big_lons[q]) <= radius_km:
                label[i] = 1
                break
            q += 1
    df["label_30d"] = label
    return df


def add_fault_distance(df):
    df["distance_to_fault"] = en_yakin_fay_km(df["latitude"].values, df["longitude"].values)
    return df


# --- Ana giris noktasi ---------------------------------------------------

def load_dataset(csv_path=None):
    """query.csv -> (X: DataFrame, y: Series, df_main: tam DataFrame)

    Satirlar zamana gore SIRALIDIR; walk-forward bolme icin gereklidir.
    """
    csv_path = Path(csv_path) if csv_path else DEFAULT_QUERY_CSV
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Veri bulunamadi: {csv_path}\n"
            "QuakeMindBackend/apps/earthquake_risk/data/query.csv dosyasini kontrol et."
        )

    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df = df.dropna(subset=["latitude", "longitude", "depth", "mag"]).reset_index(drop=True)

    df = simple_declustering(df)
    df_main = df[~df["is_aftershock"]].copy().reset_index(drop=True)
    df_main = build_label_30d(df_main)

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

    df_main = add_fault_distance(df_main)
    # Yalnizca model oznitelikleri + hedef sutununda NaN olan satirlar elenir.
    # Onceki halde subset verilmeden dropna() cagriliyordu; bu, modelin hic
    # kullanmadigi USGS ag-kalite kolonlarinda (nst, gap, dmin, rms, magError,
    # depthError, magNst, horizontalError) NaN olan HER satiri da eliyor ve
    # declustering sonrasi 13.615 ana soktan 454'e (%97 kayip) dusuruyordu.
    df_main = df_main.dropna(subset=RISK_FEATURE_COLUMNS + [TARGET_COLUMN]).reset_index(drop=True)

    X = df_main[RISK_FEATURE_COLUMNS].copy()
    y = df_main[TARGET_COLUMN].astype(int).copy()
    return X, y, df_main


# --- Degerlendirme -----------------------------------------------------

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    """Standart ikili siniflandirma metrikleri -> dict"""
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, average_precision_score, brier_score_loss,
        balanced_accuracy_score, matthews_corrcoef, confusion_matrix,
    )

    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= threshold).astype(int)

    single_class = len(np.unique(y_true)) < 2
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    return {
        "n": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)),
        "roc_auc": float("nan") if single_class else float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float("nan") if single_class else float(average_precision_score(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)) if not single_class else float("nan"),
        "brier": float(brier_score_loss(y_true, y_prob)) if not single_class else float("nan"),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def walk_forward_splits(n_samples, n_splits=5):
    """sklearn TimeSeriesSplit ile ayni mantik; import olmadan kullanilabilir."""
    from sklearn.model_selection import TimeSeriesSplit
    return list(TimeSeriesSplit(n_splits=n_splits).split(np.arange(n_samples)))


def aggregate_folds(fold_metrics):
    """Fold dict listesi -> ortalama +/- std dict"""
    keys = [k for k in fold_metrics[0] if k not in ("n", "tn", "fp", "fn", "tp")]
    out = {}
    for k in keys:
        vals = np.array([m[k] for m in fold_metrics], dtype=float)
        out[f"{k}_mean"] = float(np.nanmean(vals))
        out[f"{k}_std"] = float(np.nanstd(vals))
    out["n_folds"] = len(fold_metrics)
    out["total_test_n"] = int(sum(m["n"] for m in fold_metrics))
    return out


def save_result(model_name, agg_metrics, results_dir=None, extra=None):
    """Sonucu results/<model>.json olarak yaz ve results/leaderboard.csv guncelle."""
    import json

    results_dir = Path(results_dir) if results_dir else (_HERE / "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    payload = {"model": model_name, **agg_metrics}
    if extra:
        payload["extra"] = extra
    with open(results_dir / f"{model_name}.json", "w") as f:
        json.dump(payload, f, indent=2)

    rows = []
    for jf in sorted(results_dir.glob("*.json")):
        with open(jf) as f:
            d = json.load(f)
        rows.append({k: v for k, v in d.items() if k != "extra"})
    lb = pd.DataFrame(rows)
    if "roc_auc_mean" in lb.columns:
        lb = lb.sort_values("roc_auc_mean", ascending=False)
    lb.to_csv(results_dir / "leaderboard.csv", index=False)
    return lb
