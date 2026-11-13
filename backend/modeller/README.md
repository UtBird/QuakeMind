# Model künyeleri

Üründe koşan uydu hasar modelinin künyesi `uydu/<ad>.json` dosyasındadır (J-36).
Künyede şunlar yazar:

- mimari (smp sınıfı ve kodlayıcı)
- ağırlık dosyası ve SHA-256'sı
- eğitim görüntülerinin çözünürlüğü
- modelin ölçüldüğü karar ayarı (eşik, güçlendirme, son işleme)
- ölçümler

Ağırlık dosyası depoya girmez: künyedeki yoldadır ya da Hugging Face'ten indirilir.

## Etkin model

`QM_UYDU_MODELI=<ad>` ortam değişkeni seçer. Tanımlı değilse bugünkü model
(`segformer_mitb4_dice30`) koşar.

- API açılışta künyeyi okur.
- İşçi mimariyi künyeden kurar. SHA-256 tutmazsa modeli yüklemez.
- Konsol eşik ve son işlemenin varsayılanını `GET /api/road_damage/model` ucundan alır.
- Her analiz sonucu, hangi modelle ve hangi ayarla üretildiğini `model` alanında taşır.

## Eğitim defterinden yeni model

1. 02 defterinde `AGIRLIK_SAKLA = True` olsun. Koşu klasöründe `sonuc.json` ve
   `model_en_iyi.pth` oluşur.
2. `python araclar_model_kunye.py <koşu_klasörü> --kopyala`
   - Künye `uydu/<model>_<protokol>_t<tohum>.json` olarak yazılır.
   - Karar ayarı defterin ölçtüğü ayardır: eşik, güçlendirme 1, son işleme yok.
3. `python araclar_model_teslim.py <ad>`
   - Künyeyi, parmak izini ve yazılım sürümlerini denetler.
   - Modeli katı modda yükler.
   - QQB dış sınama karolarında ürünün kendi çıkarım koduyla IoU ölçer ve defterdekiyle karşılaştırır.
4. API'yi `QM_UYDU_MODELI=<ad>` ile yeniden başlat.

## Bilinen sınır

`benchmark/colab/make_model_masks.py` (makale maskeleri) hâlâ eski modele sabit
(SHA-256 `7d7fb8d8…`). Yeni modelle maske üretmek için ayrıca güncellenmesi gerekir.
