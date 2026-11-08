# model_benchmarks — QuakeMind Kıyaslama Kodları

Makale için: her yöntem alanında **bizim modelimizi** literatürdeki kıyaslama
modellerine karşı **aynı veri, aynı bölme, aynı metrik protokolü** ile eğitir.
Her alan kendi klasöründe, kendi `common.py` / `seg_common.py` yardımcısıyla,
`_build.py` ile üretilen `NN_*.ipynb` defterleriyle ve bir `00_leaderboard.ipynb`
özet defteriyle gelir. Sonuçlar her klasörün `results/` altına JSON + `leaderboard.csv`
olarak yazılır.

## Klasörler (Kıyaslama Planı ile birebir)

| # | klasör | görev | bizim model | kıyaslama motoru | veri kaynağı |
|---|---|---|---|---|---|
| 01 | `01_yol_hasari/` | uydudan yol hasarı segmentasyonu | SegFormer MiT-B4 | `segmentation_models_pytorch` | **Roboflow Universe** (senin linkin) |
| 02 | `02_bina_hasari/` | uydudan bina hasarı segmentasyonu | SegFormer MiT-B4 (aktarım) | `segmentation_models_pytorch` + HF Mask2Former | **Roboflow Universe** |
| 03 | `03_yer_seviyesi/` | yer seviyesi çatlak / yapısal hasar tespiti | 2× YOLOv8 | `ultralytics` + `torchvision` | **Roboflow Universe** |
| 04 | `04_turkce_metin/` | Türkçe metinden ihtiyaç + aciliyet | BERTurk hattı | `transformers` + `scikit-learn` | `data/` (DepremKit / TSEqD) |
| 04 | `04_turkce_metin/ner/` | konum varlığı çıkarımı | alan-özel NER | `transformers` + `seqeval` | HF `yhaslan/...` veya CoNLL |
| 05 | `05_risk_skoru/` | 30 günlük deprem risk sınıflandırması | CatBoost | boosting + `scikit-learn` | `backend/.../query.csv` (repoda) |
| 06 | `06_rota/` | kapanma-farkında rota (algoritma kıyaslaması) | risk-ağırlıklı A* | `networkx` / `osmnx` / OSRM / ORS | Geofabrik PBF + EMSR648 |

## Görüntü modelleri — veri setini nasıl bağlarsın

`01`, `02`, `03` klasörlerindeki defterler veriyi **Roboflow Universe**'ten çeker.
Her defterin başındaki **AYAR hücresi**ne (ya da klasörün `*_common.py > CONFIG`
sözlüğüne) kendi bilgilerini gir:

```python
roboflow_api_key = "..."       # roboflow.com > Settings > API Key
roboflow_workspace = "..."     # Universe dataset > Download > "show download code"
roboflow_project   = "..."
roboflow_version   = 1
```

- Segmentasyon (`01`, `02`): format `png-mask-semantic`
- Tespit (`03` YOLO ailesi): format `yolov8`
- Tespit (`03` Faster/Mask R-CNN): format `coco`

Roboflow kullanmıyorsan `source="local"` yapıp `data/images` + `data/masks`
(segmentasyon) veya standart YOLO/COCO klasör yapısını koyabilirsin.

## Uydu ve risk modeli — hazır veri

- `05_risk_skoru/` doğrudan repodaki `query.csv` ile **şimdi çalışır** (aşağıda ilk sonuçlar var).
- `06_rota/` repodaki `safety_areas.geojson` + Geofabrik Türkiye PBF ile çalışır.

## Colab'da çalıştırma — defter defter

Her defterin **ilk hücresi** Colab kurulum hücresidir: Colab'da çalışınca repoyu
klonlar, doğru klasöre geçer, paketleri kurar; yerelde hiçbir şey yapmaz. Yani
elle `%cd` / `pip` yazmana gerek yok.

**Ön koşul:** bu klasörü (`model_benchmarks/`) repoya push et —
`git add model_benchmarks && git commit -m "benchmark kodlari" && git push`.
Kurulum hücresi `github.com/UtBird/QuakeMind` reposunu klonlar; push etmezsen
klonda bu klasör olmaz.

**Her defter için:**

1. **colab.research.google.com** → File → Open notebook → **GitHub** sekmesi →
   `UtBird/QuakeMind` → defteri seç. (Ya da `model_benchmarks/`'i Drive'a atıp
   Drive'dan aç.)
2. Runtime → Change runtime type → **T4 GPU** (05 hariç; o CPU'da da çalışır).
3. İlk hücreyi çalıştır (kurulum). `cwd: /content/QuakeMind/model_benchmarks/...` yazmalı.
4. **AYAR hücresini doldur:**
   - `01, 02` → `SC.CONFIG.update(...)` içine Roboflow `api_key`/`workspace`/`project`/`version`
   - `03` → aynısı `C.CONFIG.update(...)` içine
   - `04` → önce sol panelden `04_turkce_metin/data/`ye `train.csv` yükle (`text,label`)
   - `05, 06` → dokunma, veri repoda
5. Runtime → **Run all**.
6. Bitince sol panel → `results/` klasörü → sağ tık → indir (Colab kapanınca silinir),
   ya da bir hücrede `from google.colab import drive; drive.mount('/content/drive')` yapıp kopyala.
7. Hepsini bitirince ilgili `00_leaderboard.ipynb`'yi çalıştır → özet tablo + LaTeX.

### Yerelde (bu repoda) çalıştırma

```bash
source ../backend/venv/bin/activate
cd 04_turkce_metin && python _build.py         # defterleri (yeniden) üret
pip install -q transformers datasets accelerate
jupyter nbconvert --to notebook --execute --inplace 0*.ipynb
```

Defterler `_build.py` çıktısıdır — mantığı değiştireceksen `_build.py`'yi düzenleyip
yeniden çalıştır; hızlı denemeler için doğrudan `.ipynb`'yi düzenlemek de olur.

### Bilinen kırılgan 3 defter (diğer ~50'si sağlam)

| defter | sorun | ne yapmalı |
|---|---|---|
| `04_turkce_metin/10_turna` | TURNA seq2seq; `AutoModelForSequenceClassification` bazı transformers sürümlerinde hata verir | sürüm hatasında bu defteri atla ya da `T5ForSequenceClassification`'a çevir |
| `03_yer_seviyesi/05_faster_rcnn` + `08_mask_rcnn` | Roboflow COCO bbox `[x,y,w,h]→[x1,y1,x2,y2]` dönüşümü ve boş görüntüler elle kontrol ister | eğitim hücresindeki `NOT` yorumuna bak; YOLO defterleri sorunsuz |
| `06_rota/*` | `pyrosm` Colab kurulumu oynak; OSRM/ORS defterleri ayrı sunucu ister | `osmnx` + `graph_from_place` yolunu kullan (PBF olmadan), OSRM/ORS'yi en sona bırak |

## Öncelik sırası (Kıyaslama Planı → "Uygulama")

1. `01_yol_hasari` — 5 mimari + SegFormer, aynı protokol
2. `06_rota` — EMSR648'i kapanma katmanına bağla, mIoU/erişilebilirlik ölç
3. `05_risk_skoru` — LR + RF + XGBoost + kalibrasyon (**bugün çalışır**)
4. `04_turkce_metin` — DepremKit/TSEqD üzerinde BERTurk + 3 taban çizgisi
5. `03_yer_seviyesi` — YOLOv8 ölçek ablasyonu + YOLOv11, SDNET2018 harici test
6. Hatay ↔ Kahramanmaraş çapraz genelleme (tüm modüller)
7. `01_yol_hasari/07_segformer_scale` + DA-SegFormer reçetesi (ablasyon)
8. `02_bina_hasari` — xBD / BRIGHT (ayrı makale bile olabilir)

## Lisans notu

İndirdiğin her veri setinin lisansını ve atıf metnini `<klasör>/data/LICENSES.md`
içine kaydet — Maxar Open Data, Copernicus EMS, EIDSeg, Roboflow setleri açık
ama her birinin kendi atıf şartı var, dergi gönderiminde istenir.

---

## 05_risk_skoru — ilk sonuçlar (5-fold walk-forward, ROC-AUC ort ± std)

| model | ROC-AUC | PR-AUC | F1 |
|---|---|---|---|
| catboost | 0.846 ± 0.093 | 0.901 | 0.852 |
| random_forest | 0.842 ± 0.092 | 0.906 | 0.857 |
| xgboost | 0.796 ± 0.160 | 0.893 | 0.856 |
| logistic_regression | 0.778 ± 0.045 | 0.866 | 0.812 |
| lightgbm | 0.717 ± 0.229 | 0.877 | 0.827 |
| mlp | 0.428 ± 0.109 | 0.711 | 0.674 |

Veri seti küçük (~454 kayıt); `backend/apps/earthquake_risk/data_manager.py`
ile katalog uzadıkça defterleri yeniden çalıştır.
