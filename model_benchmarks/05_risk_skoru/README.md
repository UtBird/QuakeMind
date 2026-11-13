# 05 · Deprem risk skorlaması

**Bizim yöntem:** CatBoost sınıflandırıcı (800 yineleme, derinlik 8, lr 0,03);
artçı ayıklama + fay hattı mesafesi öznitelikleriyle, 30 günlük etiketleme
üzerinden. Nihai skor: `0,4 × kısa vadeli ML + 0,3 × uzun vadeli tehlike + 0,3 × fay skoru`.

Bu alan **repodaki veriyle şimdi çalışır** —
`backend/apps/earthquake_risk/data/query.csv`.

## Görev

İkili sınıflandırma `label_30d`: bir depremden sonra 30 gün içinde, 100 km'de
M ≥ 4.0 bir olay var mı. Özellik mühendisliği + etiketleme `risk_engine.py`'den
birebir alındı → `common_preprocessing.py`. Değerlendirme: `TimeSeriesSplit`
walk-forward, 5 fold.

## Defterler

| dosya | model | katman |
|---|---|---|
| `01_catboost` | **CatBoost — referans** | referans |
| `02_xgboost` | XGBoost | zorunlu |
| `03_lightgbm` | LightGBM | zorunlu |
| `04_random_forest` | Random Forest | zorunlu |
| `05_logistic_regression` | Lojistik Regresyon | zorunlu — doğrusal taban |
| `06_mlp` | MLP (sinir ağı) | — |
| `07_stacking_ensemble` | CatBoost + LightGBM + RF yığınlama | güçlendirici |
| `08_calibration_and_shap` | kalibrasyon eğrisi + Brier + SHAP | zorunlu |
| `00_leaderboard` | özet tablo + LaTeX + ROC-AUC grafiği | — |

## Metrikler

ROC-AUC · **PR-AUC** (dengesiz veride ROC yanıltır) · Brier skoru ·
kalibrasyon eğrisi · SHAP değerleri (kara kutu itirazına cevap).

## İlk sonuçlar (5-fold walk-forward)

| model | ROC-AUC | PR-AUC | F1 |
|---|---|---|---|
| catboost | 0.846 ± 0.093 | 0.901 | 0.852 |
| random_forest | 0.842 ± 0.092 | 0.906 | 0.857 |
| xgboost | 0.796 ± 0.160 | 0.893 | 0.856 |
| logistic_regression | 0.778 ± 0.045 | 0.866 | 0.812 |
| lightgbm | 0.717 ± 0.229 | 0.877 | 0.827 |
| mlp | 0.428 ± 0.109 | 0.711 | 0.674 |

> Veri seti küçük (~454 kayıt, ilk fold'da 79 eğitim örneği); LightGBM/MLP bu
> boyutta kararsız. `data_manager.py` ile katalog uzadıkça yeniden çalıştır.

## Çalıştırma

```bash
source ../../backend/venv/bin/activate
pip install -q xgboost lightgbm shap
python _build_notebooks.py          # 01–06'yı yeniden üretir
jupyter nbconvert --to notebook --execute --inplace 0*.ipynb
```

## Veri kaynakları (çapraz doğrulama için)

AFAD kataloğu (mevcut) · KOERI/Kandilli · USGS ANSS ComCat · ISC-GEM
(homojenleştirilmiş, uzun vadeli tehlike) · AFAD TDTH (resmî tehlike haritası).
