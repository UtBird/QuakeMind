"""
Model karsilastirma defterlerini (.ipynb) uretir.

Her defter AYNI iskeleti kullanir:
  1. common_preprocessing.load_dataset() ile veriyi yukle
  2. TimeSeriesSplit (walk-forward) 5 fold
  3. Her fold'da modeli egit, test olasiliklarini uret
  4. evaluate_predictions ile metrikleri hesapla
  5. aggregate_folds + save_result -> results/<model>.json ve leaderboard.csv
  6. ROC ve PR egrilerini ciz

Yeniden uretmek icin:  python _build_notebooks.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NB_VERSION = 4


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": _src(lines)}


def code(*lines):
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": _src(lines),
    }


def _src(lines):
    flat = []
    for ln in lines:
        flat.extend(ln.split("\n"))
    return [l + "\n" for l in flat[:-1]] + [flat[-1]]


COLAB_CELL = code(
    "# === COLAB KURULUM ===  (yerelde calistirinca atlanir)",
    "import os, sys",
    "IN_COLAB = 'google.colab' in sys.modules",
    "if IN_COLAB and not os.path.exists('/content/QuakeMind'):",
    "    !git clone --depth 1 https://github.com/UtBird/QuakeMind.git /content/QuakeMind",
    "if IN_COLAB:",
    "    %cd /content/QuakeMind/model_benchmarks/05_risk_skoru",
    "    %pip install -q catboost xgboost lightgbm shap scikit-learn",
    "print('cwd:', os.getcwd())",
)


COMMON_SETUP = code(
    "import sys, warnings, json",
    "from pathlib import Path",
    "warnings.filterwarnings('ignore')",
    "",
    "import numpy as np",
    "import pandas as pd",
    "import matplotlib.pyplot as plt",
    "",
    "# common_preprocessing.py bu klasorde",
    "sys.path.insert(0, str(Path.cwd()))",
    "import common_preprocessing as cp",
    "",
    "X, y, df_main = cp.load_dataset()",
    "print('Ornek sayisi     :', len(X))",
    "print('Ozellik sayisi   :', X.shape[1])",
    "print('Pozitif oran     :', round(float(y.mean()), 4))",
    "print('Zaman araligi    :', df_main['time'].min(), '->', df_main['time'].max())",
    "X.head()",
)

EVAL_CELL = code(
    "splits = cp.walk_forward_splits(len(X), n_splits=5)",
    "fold_metrics = []",
    "oof_true, oof_prob = [], []",
    "",
    "for i, (tr, te) in enumerate(splits, 1):",
    "    X_tr, X_te = X.iloc[tr], X.iloc[te]",
    "    y_tr, y_te = y.iloc[tr], y.iloc[te]",
    "",
    "    model = build_model()",
    "    prob = fit_predict(model, X_tr, y_tr, X_te)",
    "",
    "    m = cp.evaluate_predictions(y_te, prob)",
    "    fold_metrics.append(m)",
    "    oof_true.append(np.asarray(y_te)); oof_prob.append(np.asarray(prob))",
    "    print(f\"fold {i}: ROC-AUC={m['roc_auc']:.3f}  PR-AUC={m['pr_auc']:.3f}  F1={m['f1']:.3f}  n={m['n']}\")",
    "",
    "agg = cp.aggregate_folds(fold_metrics)",
    "print()",
    "for k in ['roc_auc', 'pr_auc', 'f1', 'precision', 'recall', 'balanced_accuracy', 'brier']:",
    "    print(f\"{k:20s}: {agg[k+'_mean']:.3f} +/- {agg[k+'_std']:.3f}\")",
)

SAVE_CELL = code(
    "lb = cp.save_result(MODEL_NAME, agg, extra={'params': PARAMS})",
    "print('Kaydedildi -> results/%s.json' % MODEL_NAME)",
    "lb[['model', 'roc_auc_mean', 'pr_auc_mean', 'f1_mean', 'recall_mean', 'precision_mean']]",
)

PLOT_CELL = code(
    "from sklearn.metrics import roc_curve, precision_recall_curve",
    "yt = np.concatenate(oof_true); yp = np.concatenate(oof_prob)",
    "fig, ax = plt.subplots(1, 2, figsize=(11, 4))",
    "fpr, tpr, _ = roc_curve(yt, yp)",
    "ax[0].plot(fpr, tpr); ax[0].plot([0, 1], [0, 1], '--', c='gray')",
    "ax[0].set_title(f'{MODEL_NAME} ROC (birlestirilmis OOF)'); ax[0].set_xlabel('FPR'); ax[0].set_ylabel('TPR')",
    "prec, rec, _ = precision_recall_curve(yt, yp)",
    "ax[1].plot(rec, prec); ax[1].axhline(float(yt.mean()), ls='--', c='gray')",
    "ax[1].set_title(f'{MODEL_NAME} Precision-Recall'); ax[1].set_xlabel('Recall'); ax[1].set_ylabel('Precision')",
    "plt.tight_layout(); plt.show()",
)


MODELS = {
    "01_catboost": dict(
        title="CatBoost",
        name="catboost",
        blurb="Mevcut production modeli (risk_engine.py). Referans / baz cizgi.",
        install="# pip install catboost",
        params_lines=[
            "PARAMS = dict(iterations=800, depth=8, learning_rate=0.03,",
            "              loss_function='Logloss', random_seed=42, verbose=False)",
        ],
        build_lines=[
            "from catboost import CatBoostClassifier",
            "def build_model():",
            "    return CatBoostClassifier(**PARAMS)",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
    "02_xgboost": dict(
        title="XGBoost",
        name="xgboost",
        blurb="Gradient boosting - agac tabanli guclu baz model.",
        install="# pip install xgboost",
        params_lines=[
            "PARAMS = dict(n_estimators=800, max_depth=6, learning_rate=0.03,",
            "              subsample=0.9, colsample_bytree=0.9, eval_metric='logloss',",
            "              random_state=42, n_jobs=-1)",
        ],
        build_lines=[
            "from xgboost import XGBClassifier",
            "def build_model():",
            "    return XGBClassifier(**PARAMS)",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
    "03_lightgbm": dict(
        title="LightGBM",
        name="lightgbm",
        blurb="Histogram tabanli hizli gradient boosting.",
        install="# pip install lightgbm",
        params_lines=[
            "PARAMS = dict(n_estimators=800, num_leaves=31, learning_rate=0.03,",
            "              subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1)",
        ],
        build_lines=[
            "from lightgbm import LGBMClassifier",
            "def build_model():",
            "    return LGBMClassifier(**PARAMS)",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
    "04_random_forest": dict(
        title="Random Forest",
        name="random_forest",
        blurb="Bagging tabanli klasik topluluk modeli.",
        install="# scikit-learn zaten kurulu",
        params_lines=[
            "PARAMS = dict(n_estimators=500, max_depth=None, min_samples_leaf=2,",
            "              class_weight='balanced', random_state=42, n_jobs=-1)",
        ],
        build_lines=[
            "from sklearn.ensemble import RandomForestClassifier",
            "def build_model():",
            "    return RandomForestClassifier(**PARAMS)",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
    "05_logistic_regression": dict(
        title="Logistic Regression",
        name="logistic_regression",
        blurb="Lineer baz model (olceklenmis ozelliklerle). Alt sinir referansi.",
        install="# scikit-learn zaten kurulu",
        params_lines=[
            "PARAMS = dict(C=1.0, class_weight='balanced', max_iter=2000, random_state=42)",
        ],
        build_lines=[
            "from sklearn.linear_model import LogisticRegression",
            "from sklearn.pipeline import make_pipeline",
            "from sklearn.preprocessing import StandardScaler",
            "def build_model():",
            "    return make_pipeline(StandardScaler(), LogisticRegression(**PARAMS))",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
    "06_mlp": dict(
        title="MLP (Sinir Agi)",
        name="mlp",
        blurb="Cok katmanli algilayici - olceklenmis ozelliklerle kucuk bir sinir agi.",
        install="# scikit-learn zaten kurulu",
        params_lines=[
            "PARAMS = dict(hidden_layer_sizes=(64, 32), activation='relu', alpha=1e-3,",
            "              learning_rate_init=1e-3, max_iter=500, early_stopping=True,",
            "              random_state=42)",
        ],
        build_lines=[
            "from sklearn.neural_network import MLPClassifier",
            "from sklearn.pipeline import make_pipeline",
            "from sklearn.preprocessing import StandardScaler",
            "def build_model():",
            "    return make_pipeline(StandardScaler(), MLPClassifier(**PARAMS))",
            "",
            "def fit_predict(model, X_tr, y_tr, X_te):",
            "    model.fit(X_tr, y_tr)",
            "    return model.predict_proba(X_te)[:, 1]",
        ],
    ),
}


def make_notebook(key, cfg):
    cells = [
        md(
            f"# {cfg['title']} - Deprem Risk Modeli Karsilastirmasi",
            "",
            f"**Gorev:** ikili siniflandirma - `label_30d` (onumuzdeki 30 gun, 100 km, M>=4.0)",
            "",
            f"**Veri:** `backend/apps/earthquake_risk/data/query.csv`",
            "",
            f"**Bu model:** {cfg['blurb']}",
            "",
            "Butun defterler `common_preprocessing.py` uzerinden AYNI ozellik muhendisligini,",
            "AYNI etiketi ve AYNI walk-forward (TimeSeriesSplit, 5 fold) bolmesini kullanir.",
            "Sonuclar `results/` klasorune yazilir ve `results/leaderboard.csv` guncellenir.",
        ),
        COLAB_CELL,
        code(cfg["install"]),
        md("## 1. Veri"),
        COMMON_SETUP,
        md("## 2. Model tanimi"),
        code(
            *cfg["params_lines"],
            "",
            f'MODEL_NAME = "{cfg["name"]}"',
            "",
            *cfg["build_lines"],
        ),
        md("## 3. Walk-forward degerlendirme"),
        EVAL_CELL,
        md("## 4. Sonucu kaydet"),
        SAVE_CELL,
        md("## 5. ROC ve Precision-Recall egrileri"),
        PLOT_CELL,
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main():
    for key, cfg in MODELS.items():
        nb = make_notebook(key, cfg)
        out = HERE / f"{key}.ipynb"
        out.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
        print("yazildi:", out.name)


if __name__ == "__main__":
    main()
