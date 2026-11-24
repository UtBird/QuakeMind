# QuakeMind — Eksikler ve Sorunlar Takip Dosyası

Bu dosya, makale ve proje üzerinde tespit edilen her eksik, hata ve açık konuyu
tek yerde tutar. Amaç hiçbir sorunun gözden kaçmaması ve sonradan geri dönülebilmesidir.

**Son güncelleme:** 18 Kasım 2026 (temizlik: kapanan maddeler arşive taşındı — bkz. değişiklik günlüğü)
**Nasıl kullanılır:** Her maddenin bir kimliği var (örn. `J-38`). Bu dosyada yalnız açık, kısmen
kapalı ve karar bekleyen maddeler durur. Bir madde kapanınca durumunu `KAPALI` yapıp kapanış
tarihini ve kanıtını yazın, sonra maddeyi değiştirmeden `EKSIKLER_ARSIV.md`'ye taşıyın ve sondaki
dizine bir satır ekleyin. Hiçbir madde silinmez; kimlikler değişmez.

## Önem dereceleri

| Kod | Anlamı |
|---|---|
| 🔴 KRİTİK | Hakem tek başına ret gerekçesi sayabilir; gönderimden önce mutlaka çözülmeli |
| 🟠 YÜKSEK | Gönderimden önce çözülmeli; çözülmezse ciddi revizyon isteği gelir |
| 🟡 ORTA | Makaleyi güçlendirir; eksikliği savunulabilir ama zayıflatır |
| ⚪ DÜŞÜK | Biçim, adlandırma, düzen |

## Durumlar

`AÇIK` · `DEVAM EDİYOR` · `KAPALI` · `KARAR BEKLİYOR` (kullanıcı kararı gerekiyor)

## Özet (güncellendi 24 Kasım 2026)

192 maddenin **110'u kapandı** ve `EKSIKLER_ARSIV.md`'ye taşındı (dizini bu dosyanın sonunda).
Burada kalan **82 madde** şöyle dağılıyor:

| Neye ait | Madde | Ne zaman |
|---|---|---|
| Ürün — teslimden önce bakılmalı | 4 | Bu hafta (aşağıdaki liste) |
| Ürün — iyileştirme | 10 | Teslimden sonra olabilir |
| Makale ve model sonuçları | 63 | Makale aşamasında (`MAKALE_DUZELTME_LISTESI.md` ile birlikte) |
| Kapsam dışı (C grubu) | 5 | Makalede "yapılmadı" diye yazılır |

**Ürün — teslimden önce bakılmalı.**

| Kimlik | Ne | Kimde |
|---|---|---|
| D-08 🔴 | Roboflow API anahtarı makale dalında açık metin; anahtar yenilenmeli | Kullanıcı (anahtar sahibi) |
| J-153 🟠 | Deprem kataloğu kendiliğinden tazelenmiyor. Risk modeli artık her dağıtımda imajda yeniden eğitiliyor; kalan: katalog tazeleme | Geliştirme |
| J-58 🟠 | Kapanmanın geometrisi artık saklanıyor ve harita/rota kullanıyor; kalan: derece sabit 3 (ekranda gösterilmiyor) | Geliştirme |
| J-39 🟡 | Büyük alan kırpılınca sonuç notu bunu yazıyor; kalan: yakınlaştırma çizilen kutudan seçilmiyor | Geliştirme |

**Ürün — iyileştirme (teslimden sonra olabilir):**
- J-10: soğuk başlangıç.
- J-15: kamera çıkarımı sunucu sürecinde ve iş parçacığı sınırı yok.
- J-16: graf pickle boyutu.
- J-32: görseller PNG.
- J-67: iki venv belgelenmemiş.
- J-147: mobilde harita lejantı ve renk (Deha).
- J-151: 81 il altlığı (Utku).
- J-155, J-158: büyük ölçüde kapandı, kalanları maddelerinde yazılı.
- J-192: deprem kataloğunda yer adlarında "?" (kaynak veride).

**Makale ve model sonuçları (62):** A grubundan 21, B 12, D 8 (D-08 hariç), G 3, E 4 ve şu J maddeleri:
- Model ve kapanma: J-20, J-21, J-22, J-25, J-26, J-34, J-36, J-65, J-69, J-70.
- Deney sonuçları: J-28, J-29, J-31.
- Risk: J-149. Ayrıca J-173'te uzun vadeli tehlike değerleri değişti; makaledeki risk sayıları denetlenmeli.

---

# A. MAKALE — KRİTİK BULGULAR

## A-01 🔴 SegFormer satırı diğer beş mimariyle karşılaştırılabilir değil
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

**Sorun.** Tablo 12'deki beş taban mimari **ayrılmış test kümesinde** ölçülmüştür:
`model_benchmarks/01_yol_hasari/local_colab_run/build_notebook.py` üç katmanlı bölme
yapıyor (%70/15/15, tohum 42), en iyi ağırlığı geri yüklüyor, sonra `test_loader`
üzerinde değerlendiriyor. SegFormer'ın 0,4276 değeri ise `optimized_training_colab.ipynb`
çıktısındaki **"En iyi Val IoU"** — iki katmanlı bölme, erken durdurmanın seçtiği
devirdeki **doğrulama** skoru. Ayrılmış test kümesi yok.

En iyi doğrulama skoru seçim yanlılığı taşır ve sistematik olarak iyimserdir.
Dolayısıyla 0,3700 → 0,4276 farkı modele atfedilemez.

**Nerede.** Öz; Abstract; Bölüm 4.2 satır "Esas alınan SegFormer yapılandırması
0,4276 ile beş kıyaslama mimarisinin tümünün üzerindedir"; Tablo 12 SegFormer satırı.

**Yapılacak.** SegFormer'ı aynı üç katmanlı bölmeyle (%70/15/15, tohum 42) yeniden
koştur ve test kümesi IoU_hasar değerini raporla. Defter ve veri mevcut.

---

## A-02 🔴 Öz ve Abstract, A-01'deki kaydı taşımıyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

**Sorun.** Öz'de *"en yüksek hasar sınıfı IoU değeri 0,4276 ile SegFormer
yapılandırmasında elde edilmiştir"*, Abstract'ta *"the highest damage-class IoU
(0.4276) obtained by the SegFormer configuration"* geçiyor. Makalenin gövdesinde
(dipnot ve sapma listesi) kayıt var, ancak Öz'de yok. Hakem Öz ile Bölüm 4.2
arasındaki bu farkı "üstü örtülü iddia" olarak nitelendirir.

**Yapılacak.** A-01 çözülene kadar iddiayı Öz ve Abstract'tan çıkar. Yerine:
"kıyaslama mimarileri arasında en yüksek IoU_hasar LinkNet'te (0,3700) elde
edilmiştir; esas alınan yapılandırmanın aynı protokolde değerlendirilmesi
sürmektedir."

---

## A-03 🟠 Bölüm 4.2 iddiayı önce olgu olarak kuruyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

**Sorun.** *"Esas alınan SegFormer yapılandırması 0,4276 ile beş kıyaslama
mimarisinin tümünün üzerindedir. Ancak bu fark bir mimari üstünlüğü kanıtı olarak
sunulamaz..."* — olumlu iddia önce, kayıt sonra geliyor. Alıntılanan cümle ilki olur.

**Yapılacak.** Sırayı ters çevir: önce protokol farkını söyle, sonra sayıyı ver.

---

## A-04 🔴 İç çelişki — artçı ayıklaması yapıldı mı yapılmadı mı?
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

Bölüm 3.7 "kümelenmeden arındırma uygulanarak artçı sarsıntılar ayıklanır" diyor;
Bölüm 4.11 son paragrafı "katalogda artçı ayıklaması yapılmamıştır" diyor. İkisi
aynı anda doğru olamaz. Çözülmezse Tablo 22'nin tüm değerleri sorgulanır.

**Yapılacak.** `model_benchmarks/05_risk_skoru/local_run/run_all_risk.py` kontrol
edilip hangisinin doğru olduğu belirlenecek, diğer bölüm düzeltilecek.

---

## A-05 🟠 Vaat edilen iki naif risk tabanı Tablo 22'de yok
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

Bölüm 3.7 "yalnızca fay mesafesine dayalı" ve "yalnızca geçmiş sismisite
yoğunluğuna dayalı" iki naif taban vaat ediyor; Tablo 22'de yoklar. Bu tabanlar,
PR-AUC'nin temel oranla karşılaştırılması argümanının tamamlayıcısıdır.

**Yapılacak.** İkisini koştur ve tabloya ekle (tek öznitelikli sıralama,
dakikalar sürer) ya da Bölüm 3.7'deki vaadi kaldır.

---

## A-06 🔴 Sentetik kapanma üreticisi Bölüm 3'te hiç tanımlanmamış
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-04

`sentetik` sözcüğü Bölüm 3'te (5 788 kelime, satır 62–301) **sıfır kez** geçiyor;
makalenin tamamında 13 kez, hepsi Bölüm 4–5'te. Manşet sonucu (206,6 ↔ 1 641,0 dk)
üreten kapanma kümesinin nasıl üretildiği hiçbir yerde yazmıyor: kaç kapanma,
hangi dağılım, hangi uzamsal kural, hangi tohum.

**Yapılacak.** Bölüm 3'e "3.10. Sentetik Kapanma Üretimi" alt bölümü ekle; üretici
algoritmayı, kapanma sayısını/oranını, uzamsal seçim kuralını, tohumu ve EMSR648
oranlarıyla (%1,58 / %1,71) kalibrasyonu yaz. Kod referansı: `backend/benchmark/`.

---

## A-07 🔴 Ekip–hedef atama kuralı tanımsız
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-05

Bölüm 3.9 toplam **102 kelime** ve yalnızca kilitlemeyi tarif ediyor (HTTP 409,
üç rollü yetkilendirme). Oysa 206,6 dakika tamamen atama kararına bağlı: hedef
sıralama ölçütü, eşitlik bozma, ekip başına eşzamanlı görev, görev sonrası
yeniden atama. Naif referansın (R0) aynı atama kuralını kullanıp kullanmadığı da
belirsiz — kullanmıyorsa karşılaştırma adil değil.

**Yapılacak.** Bölüm 3.9'a atama yordamını sözde kodla ekle (Algoritma 2).

---

## A-08 🔴 Tek etiketli ↔ çok etiketli çelişkisi ve iki farklı eşik
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-07

Bölüm 3.6: *"ihbarı 13 alt kategoriden **birine** atar"* (tek etiketli), eşik 0,30.
Bölüm 4.10 ve Tablo 21: *"çok etiketli"*, eşik 0,50. Raporlanan tüm metin başarımı
çok etiketli kurguya ait; yöntem tek etiketli sınıflandırıcı tarif ediyor.

**Yapılacak.** Bölüm 3.6'yı fiilen koşulan kurguya göre yeniden yaz; iki eşiğin
hangisinin ne için kullanıldığını aynı paragrafta tanımla.

---

## A-09 🔴 Üç geçilebilirlik kuralı Bölüm 3'te yok; üstelik atıf yanlış
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-08

`Katı kural`, `Dengeli kural`, `Gevşek kural` ifadelerinin her biri makalede **tam
bir kez** geçiyor, üçü de Bölüm 4'te; Bölüm 3'te **sıfır**. Buna karşın Bölüm 4.3
*"Bölüm 3.2'de tanımlanan üç kural"* diyor — Bölüm 3.2 "Çalışma Alanı ve Veri
Kaynakları" bölümüdür, böyle bir tanım içermez. Tablo 19 bu kurallar üzerine
kurulu olduğu için okunamaz durumda.

**Yapılacak.** Hasar derecesi → geçilebilirlik eşlemesini tablo hâlinde Bölüm 3'e
ekle; 4.3'teki atfı düzelt.

---

## A-10 🟠 Yakınlaştırma düzeyi seçiminde üç hata
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-12

Bölüm 3.3: (i) Web Mercator yer çözünürlüğünde `cos φ` düzeltmesi yok — Hatay için
`cos 36,2° ≈ 0,807`, düzeltmesiz alan %24 büyük görünür; (ii) sağlayıcının harita
karosu (256/512 px) ile modelin karosu (512 px) karışmış; (iii) "hedef karo sayısı
altı" muhtemelen kenar başına — toplam 36 karo demek, çıkarım süresi tahmini altı
kat sapıyor.

---

## A-11 🟡 λ(d)'nin ilk basamağı sert kapatma yarıçapıyla örtüşüyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-13

`r_h = 25 m` altındaki kenarlar çizgeden çıkarıldığı için Denklem (9)'un
`λ = 3,0` basamağı (`d < 50 m`) fiilen yalnızca 25 ≤ d < 50 m bandında çalışır.
Metin bunu söylemiyor.

---

## A-12 🟡 Kenar orta noktası ölçütü bir yerde reddedilip başka yerde kullanılıyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-14

Bölüm 5 orta nokta ölçütünü eleştiriyor ("kenarın bir ucundaki kapanmayı
sistematik olarak kaçırır"); Tablo 4 notu ise "Damaged" cezasını **orta nokta**
üzerinden uyguluyor. Savunulabilir bir tasarım kararı ama iki yer bağlanmamış.

---

## A-13 🟠 Bölüm 4.1.1 kendisiyle çelişiyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-16

*"eğitim ortamına ait alanlar Bölüm 4.2'deki karşılaştırma yürütüldükten sonra
raporlanacaktır"* — oysa 4.2 zaten yürütülmüş, Tablo 12 dolu.

---

## A-15 🔴 Tablo 13'teki SegFormer ile beş mimari aynı koşullarda karşılaştırılmamış
**Durum:** KOŞULDU (23 Eylül 2026) — 10 modelin hepsi aynı mekânsal bölme, aynı veri (P2: KATE-PD sonrası + KATE-CD öncesi, 1 013 karo), aynı tarif (focal α 0,25 + dice, sabır 20, ≤50 dönem), aynı ölçüt ve aynı cihazla (Kaggle Tesla T4) koşuldu; tohum 42, artırım tohumlu (A-22). Kayıt: `QuakeMind_veri/cikti/kosular/kaggle/P2/`, şekiller `cikti/kosular/sekiller/modeller_kaggle_P2.png` ve `maliyet_kaggle_P2.png`. Tablo 13 bundan üretilecek, `[KARŞILAŞTIRILAMAZ]` kalkabilir. **Sınama IoU_hasar:** unet_mitb4 0,433 · upernet_mitb4 0,425 · deeplabv3plus_mitb4 0,412 · segformer_mitb2 0,409 · segformer_mitb4 0,407 · fpn_mitb4 0,397 · segformer_mitb0 0,382 · unet_resnet18 0,339 · deeplabv3plus_resnet101 0,339 · upernet_convnext_small 0,327. **Okuma:** belirleyici olan kodlayıcı — MiT-B4 kodlayıcılı beş modelin hepsi (0,397–0,433) ResNet/ConvNeXt kodlayıcılıların (0,327–0,339) üstünde; kod çözücüler arasındaki fark (0,397–0,433) tohum oynamasına (±0,02) yakın, tek tohumla "en iyi mimari" iddiası edilemez. Makalenin SegFormer tercihi ayakta ama "SegFormer en iyisi" denemez; U-Net MiT-B4 bu koşuda önde · **Bulundu:** 19 Eylül 2026 · **Birleşik liste:** M-96, M-90 (ayrıntı) · **İlgili:** KALAN_ISLER.md madde 6

Kaynaklar (yalnız `makale` dalında var; `main` ve diğer dallarda `model_benchmarks/` yok):
beş mimari `model_benchmarks/01_yol_hasari/local_colab_run/build_notebook.py`, SegFormer depo kökündeki
`optimized_training_colab.ipynb` (çıktılarıyla birlikte). Eğitim tarifi ortak: aynı 842 görüntü (KATE-CD `train`
404 + MEDBFS Türkiye 438), focal + dice (0,5/0,5), AdamW 2e-4, kosinüs yeniden başlatmalı çizelge, aynı
artırımlar, parti 8, en çok 50 dönem, sabır 8, gradyan kırpma 1,0, ImageNet ağırlıkları.

Farklar (sonucu karşılaştırılamaz kılıyor):
1. **Bölme:** beş mimari %70/15/15 (sınama kümesi var); SegFormer %85/15, **sınama kümesi yok**. 0,4276 doğrulama
   kümesinden, en iyi dönem de aynı kümeyle seçilmiş (iyimser).
2. **Ölçüt:** SegFormer'ın 0,4276'sı yalnız hasar sınıfının IoU'su, **parti başına ortalanmış**; beş mimarininki
   tüm sınama pikselleri üzerinden. `results/00_comparison_table.csv` bu değeri `mean_iou` (hasar + arka plan
   ortalaması, 0,66–0,68) sütununa yazmış — elma ile armut.
3. **Kapasite:** SegFormer MiT-B4 61,4 M parametre; ResNet-18'li dört mimari 11,3–14,3 M. Yakın olan yalnız
   DeepLabV3+ ResNet-101 (45,7 M).
4. **Makalenin kendi sözü tutulmamış:** Tablo 6 tüm mimariler için "kodlayıcı (hedeflenen): MiT-B4", Tablo 24
   "kodlayıcı sabitlemesi, mekânsal blok bölmesi ve çoklu tohum" diyor; hiçbiri yapılmadı. Ayrıca
   **smp 0.5.0'da LinkNet ve UNet++ MiT kodlayıcısını desteklemiyor** (yerel deneme) → Tablo 6'daki LinkNet +
   MiT-B4 hedefi uygulanamaz; PSPNet + MiT-B4 yalnız ilk üç kademeyi kullanıyor (26,5 GFLOPs).
5. KATE-CD'nin resmî `validation` (44) ve `test` (38) bölmeleri hiç kullanılmamış.
6. `01_yol_hasari/0*.ipynb` ve `02_bina_hasari/0*.ipynb` (Mask2Former dahil) defterleri hiç koşulmamış
   (çıktısız şablonlar).

Yerel ölçüm (19 Eylül, smp 0.5.0, 1×3×512×512, `FlopCounterMode`; SegFormer değerleri Tablo 13 ile birebir):
MiT-B4 kodlayıcıyla Segformer 61,4 M / 116,6 GFLOPs · U-Net 64,1 / 129,1 · FPN 62,7 / 123,5 · DeepLabV3+ 62,0 /
134,5 · UPerNet 69,2 / 212,4 · PAN 61,1 / 131,0 · MAnet 71,6 / 132,1 · DeepLabV3 65,6 / 1 249,1 (pratik değil).
Başka kodlayıcıyla: DeepLabV3+ ResNet-101 45,7 / 111,9 · UPerNet ConvNeXt-S 58,7 / 197,0 · U-Net ConvNeXt-S
53,6 / 115,6 · UPerNet ResNet-101 56,3 / 191,6 · U-Net HRNet-W48 72,2 / 202,5. Ölçek: SegFormer B0 3,7 / 15,5 ·
B2 24,7 / 50,1 · B5 82,0 / 148,5.

**Yapılacak.** Seçilen mimarilerin tamamı aynı bölme (veri seti incelemesinden sonra karar), aynı ölçüt
(hasar IoU'su tüm sınama pikselleri üzerinden + kesinlik/duyarlılık/F₁) ve aynı tohumlarla Colab'da yeniden
eğitilmeli; Tablo 6, 13, 24 ve Şekil 7 buna göre güncellenmeli.

**İlk sonuç — SegFormer MiT-B4 (19 Eylül 2026, Colab T4, tohum 42; ayrıntı `QuakeMind_veri/cikti/sonuclar/`):**
Koşu A (ortak mekânsal bölme): en iyi dönem 15/23 (erken durdurma), doğrulama IoU_hasar 0,421; **sınama (103 sonrası karo)
IoU_hasar 0,401**, kesinlik 0,534, duyarlılık 0,618, F1 0,573; KATE-PD 0,410 · MEDBFS 0,086 (n = 12) · Hatay 0,398 ·
Kahramanmaraş 0,407; 53 öncesi karoda yanlış alarm 0 (eşik 0,2'de bile 0 → büyük olasılıkla görünüm kestirmesi, gerçek
hasarsız sonrası alanı temsil etmez). Maliyet 61,37 M / 116,6 GFLOPs / T4'te 70 ms. Koşu B (KATE-PD resmî bölmesi):
doğrulama 0,469, sınama (79) 0,481 (F1 0,650); yayımlanmış U-Net ResNet-152 doğrulama 0,36 (IoU hesap yöntemi doğrulanmalı).
Tanı: çözünürlük etkisi belirgin — Maxar 0,375 m 0,486 (n = 16) · Pléiades 0,5 m 0,395 (n = 75) · MEDBFS 0,75 m 0,086;
3 piksel sınır toleransı IoU'yu yalnız 0,401 → 0,466 yapıyor (hataların çoğu kenar kayması değil); bina/bileşen düzeyi:
>200 m² hasar kümelerinin %74'ü (KATE-PD'de %78) bulunuyor, 50–200 m²'nin %32'si; tahmin edilen 189 bileşenin 63'ü yanlış
alarm (bileşen kesinliği 0,67); eşik 0,2–0,8 arasında sınama IoU'su değişmiyor (0,397–0,402); parlaklık etkisi zayıf
(Spearman r = 0,18, p = 0,08). Protokol notu: erken durdurma sabrı (8) kosinüs döngüsünden (10–20 dönem) kısa; ikinci
döngü tamamlanmadan duruyor.

**Deneme 2 (19 Eylül 2026, kullanıcı isteği; mevcut model korunarak ayrı klasöre):** MEDBFS eğitimden ve ölçümden çıkarıldı
(sonrası + öncesi), SABIR = 20 (en çok 50 dönem), diğer her şey aynı. En iyi dönem 30/50 (doğrulama 0,465; 23. dönemde
durulsaydı en iyi 0,444 kalacaktı). **Aynı 91 KATE-PD sınama karosunda: yeni 0,434 (P 0,591 · R 0,620 · F1 0,605), eski model
0,410 (P 0,543 · R 0,627 · F1 0,582)** → kazanç büyük ölçüde kesinlikte (daha az yanlış alarm). Tek tohum; fark tohum
değişkenliği içinde olabilir. İki değişiklik aynı anda yapıldığı için katkıları ayrılamıyor. Süre 73 dk (T4).

**Ek veri — QuickQuakeBuildings (19 Eylül 2026, kullanıcı onayıyla):** TeraBox hesap istediği için veri kaynaklarından
yeniden kuruldu: Maxar ARD katalog 1040010082698700 (2023-02-07, 0,305 m, CC BY-NC 4.0; 4 karo, 314 MB) + OSM bina
poligonları 2023-03-01 tarihli attic sorgusuyla (4 029 kimlik; 169 yıkık; 1 kayıt Teksas'ta çıktı → çıkarıldı).
`araclar/qqb_osm.py`, `araclar/qqb_karola.py`: 0,375 m'ye örneklenmiş 425 karo (512²); 63'ü yıkık bina içeriyor, 362'si
yalnız sağlam bina (deprem sonrası gerçek negatif). Mevcut bölmeyle uyum: doğrulama/sınama bloklarındaki ya da o karolarla
örtüşen 86 karo dışarıda → **339 karo eğitime girebilir**, sınama kümesi değişmedi. Önizleme: `cikti/qqb_onizleme.jpg`.
Uyarılar: etiket yalnız tamamen yıkık binalar (kısmi hasar "sağlam" sayılmış olabilir; önizlemede birkaç örnek); OSM
çizimleri deprem öncesi görüntüden, 1–2 m kayma var. TE23D (YTÜ) için yazarlarla iletişim sonraya bırakıldı.

**Karar (19 Eylül 2026, kullanıcı):** üç grup, 9 model — MiT-B4 kodlayıcıyla SegFormer, U-Net, FPN, DeepLabV3+,
UPerNet; aynı kapasitede DeepLabV3+ ResNet-101 ve UPerNet ConvNeXt-S; ölçek için SegFormer B0 ve B2. Eğitime
geçilmeden önce parametreler ve veri hazırlığı sabitlenecek (tohum sayısı sonra).

**Devir (19 Eylül 2026 akşam, kullanıcı kararı):** 9 modelin eğitimi **Utku'ya devredildi**. Paket:
`Desktop\2209-A Afet\QuakeMind_Devir_Utku_Egitim_2026-09-19\` (+ aynı adlı `.zip`, 6,3 MB; `BENIOKU.md` devir notu),
web sürümü https://claude.ai/artifact/DUDdsRkgACUA4xPs1hgtWC (özel; kullanıcı paylaşacak). Yeni defter
`QuakeMind_veri/defterler/02_dokuz_model_protokol.ipynb` (`araclar/defter_dokuz_model.py` üretir): P1/P2 protokol
seçimi (P2 = MEDBFS yalnız dış sınama + SABIR 20, önerilen), tohum döngüsü ve tamamlananı atlama, QQB eğitime ekleme
(A3) ve **74 karoluk QQB dış sınaması** (deprem sonrası sağlam binalarda bina düzeyinde yanlış alarm; `araclar/qqb_bolme.py`
→ `qqb/qqb_bolme.csv`, `qqb_paket.json`: 339 eğitim / 74 dış sınama / 12 dışarıda), bölge kısıtlı eğitim (Tablo 15),
kayıp ağırlığı (Tablo 21), morfoloji 0/1/2, Koşu B, özet hücresi (Tablo 13 ort. ± ss, Tablo 15, iki şekil). Yerelde CPU
duman testiyle bütün kombinasyonlar denendi; QQB karoları Colab kodu ile yerel `qqb_karola.py` çıktısı 55 yıkık binalı
karoda birebir aynı. Önerilen sıra: P2 SegFormer → P2+QQB kıyası → 9 model tek tohum → en iyi 3 model × 3 tohum →
Tablo 15 (3 koşu) → Tablo 21 (4 koşu).

---

## A-16 🔴 Bölütleme eğitim verisinde sızıntı ve hiç negatif örnek yok
**Durum:** AÇIK — veri hazırlığı önerisi kullanıcıya sunuldu · **Bulundu:** 19 Eylül 2026 · **İlgili:** A-15, M-96, M-24

Ölçülenler (Hugging Face kart/API, KATE-CD GitHub, Zenodo kaydı ve MEDBFS arşivinin uzaktan okunması):
- **KATE-CD** (Nayir vd., SAMCD makalesi, JARS): 7 il (Adıyaman, Gaziantep, Hatay, Kahramanmaraş, Kilis, Osmaniye,
  Malatya), Maxar Open Data + Airbus Pléiades, 0,3–0,5 m, EPSG:32637, 512×512, 486 öncesi/sonrası çifti; resmî bölme
  404/44/38; etiket = hasarlı bina poligonları (ikili). **Lisans CC0 1.0** (`CITATION.cff`) — "lisans veri
  kartında yok" notu böylece kapanıyor. Hugging Face sürümünde karoların konumu/adı yok.
- **MEDBFS** = Zenodo 11647956 "AIR-DERSL-Earthquake Feature Set", **CC BY-NC 4.0**; `Turkey.zip` 3,33 GB, 438 karo
  (512×512, ~0,75 m), öncesi + sonrası + etiket (0/1). Karolar 6 büyük sahneden (`part0`…`part5`: 26/28/66/146/137/35).
  GeoTIFF'lerde yalnız **sahnenin** başlangıç noktası var (karonun değil), CRS etiketi yok. **Düzeltme (19 Eylül,
  aynı gün):** ilk hesap 512 piksel adım varsaydığı için yanlıştı; karolar **256 piksel adımla, yarı örtüşmeli**
  kesilmiş. EPSG:32637 + 256 adım, KATE-PD'nin Maxar karolarıyla şablon eşleştirmesiyle doğrulandı (16 güçlü eşleşme,
  konum farkı ≤ 4,5 piksel ≈ 3 m; görsel: `QuakeMind_veri/cikti/dogrulama_medbfs_katepd_duzeltilmis.png`).
  Gerçek konumlar (geoBoundaries il/ilçe sınırlarıyla): Kahramanmaraş/Türkoğlu 283, Gaziantep/İslahiye 94,
  Gaziantep/Nurdağı 35, Hatay/Hassa 26. `PreCloud.txt`'teki 386 bulutlu öncesi görüntünün hepsi Fas'a ait.
- **Envanter (19 Eylül, `QuakeMind_veri/araclar/envanter.py`):** KATE-CD'nin 486 sonrası görüntüsünün **tamamı KATE-PD'de
  piksel piksel aynı** ve aynı resmî bölmede (404/44/38 ↔ train/val/test) → KATE-CD yeni sonrası görüntü getirmiyor,
  katkısı öncesi görüntüleri. KATE-PD'de aynı ızgara hücresinden 32 neredeyse aynı çift var (hepsi aynı bölmede).
  KATE-PD'de hasarsız karo yok (ort. hasar oranı %3,0); MEDBFS'te 1 (ort. %0,66). MEDBFS'in kendi içinde **1 953 örtüşen
  karo çifti** var (rastgele bölmede büyük sızıntı); KATE-PD'nin 27 karosu MEDBFS'in 45 karosuyla aynı yerde
  (İslahiye) → ikisi aynı bölmeye düşmeli. İl dağılımı: KATE-PD Hatay 340, Kahramanmaraş 199, Gaziantep 180,
  Malatya 63, Adıyaman 24, Osmaniye 23, Kilis 3; Tablo 15 için Hatay 366, Kahramanmaraş 482 karo.

Sorunlar:
1. **Sızıntı:** her iki eğitimde de bölme karo düzeyinde rastgele; aynı sahnenin komşu karoları eğitim ve sınamaya
   dağılıyor → sonuçlar iyimser.
2. **Negatif örnek yok:** 842/842 karo hasarlı (SegFormer defteri çıktısı). Model hasarsız bir sahneyi hiç görmedi;
   yanlış alarm davranışı ne öğretildi ne ölçüldü (J-30'daki yanlış alarm sorunuyla doğrudan ilgili).
3. KATE-CD'nin resmî doğrulama/sınama bölmeleri kullanılmadı (A-15/5).
4. Çözünürlük karışık: KATE-CD 0,3–0,5 m, MEDBFS 0,75 m; simülasyon için düşünülen Help.NGO drone 3–8 cm.

**Yapılacak (öneri):** KATE-CD resmî bölmesi + MEDBFS sahne bazlı bölme (ör. eğitim part3+4, doğrulama part0+1,
sınama part2+5); olay öncesi görüntüler (bulutlu olanlar hariç) aynı bölmede tüm-sıfır etiketli negatif örnek
olarak eklenir; sonuçlar iki küme için ayrı raporlanır.

**Durum (19 Eylül 2026, DEVAM EDİYOR):** Ortak bölme listesi kuruldu (`QuakeMind_veri/araclar/bolme.py` →
`cikti/bolme_listesi.csv`, 2 194 satır): 2 km UTM blokları, il bazında %80/%10/%10 (kare sapması en küçük atama),
tampon kuralı (örtüşen karolardan düşük öncelikli olan kullanılmaz; 28 MEDBFS karosu), doğrulama/sınamada
küme içi örtüşmesiz alt küme ölçüte girer (62 karo dışarıda). Sonuç: KATE-PD 636/105/91, MEDBFS 359/17/34 (+28 tampon),
öncesi (negatif) 736/85/75; bölmeler arası örtüşen çift **0**. Örtüşen blokları birleştirme denendi, MEDBFS sahneleri tek
parça olup Maraş doğrulamasını %27'ye çıkardığı için bırakıldı. SegFormer defteri (`araclar/defter_segformer.py`,
liste gömülü) yerelde duman testinden geçti ve Colab'da (T4) koşuluyor; çıktılar Drive `QuakeMind_egitim/`.

**Karar (19 Eylül 2026, kullanıcı):** veri setleri kesin — **KATE-CD, KATE-PD, MEDBFS**.
**KATE-PD** (Musaoğlu vd., IGARSS 2025; HF `CSCRS/kate-pd`, CodeOcean DOI 10.24433/CO.8064763.v1): yalnız deprem
sonrası görüntü (bizim modelin girdisiyle aynı), aynı 7 il, Maxar + Pléiades 0,3–0,5 m, 832 karo, resmî bölme
675/78/79 (karo kimlikleri bölmeler arasında iç içe → karo düzeyinde rastgele, mekânsal değil). **Veri lisansı CC0 1.0**
(CodeOcean `data/LICENSE`, 19 Eylül'de görüldü). Yayımlanmış taban: SMP U-Net ResNet-152, Jaccard kaybı, doğrulama
IoU 0,36. CodeOcean'da karoların konumunu veren `data/preprocessing/grid_maxar.geojson` (1 013 KB),
`grid_pleidas.geojson` (725 KB), `katepd_polygons.geojson` (1,78 MB) var — Hatay/Maraş ayrımı ve mekânsal blok
bölmesi için gerekli; indirmek için kullanıcı izni bekleniyor.
**Yeni risk:** KATE-CD de aynı ekibin, aynı görüntü ve ızgaradan (834 etiketli sonrası görüntünün 486'sı çiftlenmiş;
KATE-PD 832 karo). KATE-CD sonrası görüntüleri büyük olasılıkla KATE-PD'nin alt kümesi → iki küme birlikte
kullanılırsa aynı görüntü bir kümede eğitimde, ötekinde sınamada olabilir. Görüntü özetleriyle (hash) denetlenmeli.

---

## A-17 🟠 Makaledeki yer tutucuların doldurma haritası
**Durum:** AÇIK · **Bulundu:** 19 Eylül 2026 · **İlgili:** A-15, A-16, KALAN_ISLER.md 6–10

v3'te (kullanıcının 19 Eylül dosyası) 88 `[ÖLÇÜLECEK]`, 6 `[TARANACAK]`, 1 `[KARŞILAŞTIRILAMAZ]`, 1 `[GELECEK ÇALIŞMA]`:
Tablo 5 (6), Tablo 13 (5 + 1), Tablo 14 (36 + 6 τ), Tablo 15 (28), Tablo 21 (7), Tablo 24 (4), 5.3(q) ve Bölüm 4
girişindeki "iskelet" cümlesi. Doldurma yolu:
- **Tablo 5** → v3'ün yeni çerçevesinde "yol hasarı kümesi" değil, üç eğitim kümesinin künyesi olmalı; veriden ve
  küme makalelerinden ölçülür (eğitim gerekmez).
- **Tablo 13** → 9 model aynı protokolle (A-15 kararı), Colab.
- **Tablo 15** → karoların il bilgisi gerekir (KATE-PD ızgara dosyaları; MEDBFS hesaplandı); SegFormer Hatay / Maraş /
  birleşik eğitim, Colab.
- **Tablo 14** → eğitilen modeller EMSR648 AOI04/AOI11 üzerindeki deprem sonrası uydu görüntüsünde koşulur, kapanma
  kesim düzeyinde EMSR648 ile karşılaştırılır; τ taraması yerelde.
- **Tablo 21** → harmanlama ve morfoloji yalnız çıkarım (ucuz); kayıp ağırlıkları ek eğitim; r_h ve λ(d) yeni
  simülasyonda; V₀ modülü yok (gelecek çalışma olarak kalmalı); risk ağırlıkları yerelde.
- **Tablo 24** → satırlar yukarıdakilerden dolar; "çok mimarili kıyaslama — yol" satırı yeni çerçevede Tablo 13 ile
  birleşmeli; YOLO mAP ayrı iş.
- **Bölüm 3.10** 2 km × 2 km mekânsal blok (%80/10/10), ikincil rastgele bölme ve **model başına 10 tohum** vaat
  ediyor → koşulacak protokolle metin eğitimden önce hizalanmalı.

---

## A-18 🟠 Yeniden kurulan QuickQuakeBuildings verisinde etiket ve bölme sorunları
**Durum:** KISMEN KAPALI (21 Eylül 2026) — madde 1 yapıldı: 95 bina maskede 255 (`qqb_karola.py`, `qqb_bolme.py`, pakette `belirsiz`), dış sınamadaki sağlam bina 1 109 → 1 066; 02 defterinde kayıp (`ignore_index=255`) ve bütün ölçütler 255'i atlıyor. Madde 2–3 açık · **Bulundu:** 19 Eylül 2026 (QQB makalesinin incelemesi, `Furkan--Utku--Model_ve_veriseti_aktarımı/AKTARIM_BELGESI.md` Ç-02) · **İlgili:** A-15, A-16

1. **"Sağlam" listesinde hasar etiketli binalar:** 1 Mart 2023 OSM verisinde 3 859 sağlam binanın 95'inde
   `earthquake:damage` (49 "yes", 18 "possible") ya da `damaged:building=yes` (27) etiketi var. 49'u eğitim, 43'ü dış sınama,
   3'ü dışlanan karolarda (dış sınamadaki 1 109 sağlam poligonun %3,9'u). **Yapılacak:** maskede 255 = yok say; dış
   sınamada yanlış alarm sayımından çıkar.
2. **Dış sınamanın 23/74 karosu doğrulama bloklarında** → model seçimi o bölgeyi görmüş olabilir. **Yapılacak:** sınama
   bloklarındaki 51 karo ayrıca raporlanmalı.
3. **Dışlanan dağlık kesim:** QQB batıdaki dağlık kesimi (SAR belirsizliği yüzünden) veri setine almamış; bizim karo zarfımız
   (dışbükey zarf − 30 m) orayı içeriyorsa listede olmayan binalar maskede 0 sayılıyor olabilir. **Yapılacak:** zarf ile QQB
   kapsamını karşılaştır.
4. **Lisans çelişkisi:** makale uydu verisine CC BY 4.0 diyor; Maxar Open Data kaydımız CC BY-NC 4.0. BY-NC varsayımıyla,
   atıf vererek kullanılıyor (ticari olmayan proje).

Ek bilgi: QQB'nin 5 katı rastgele (1. katta en yakın komşunun %81,4'ü başka katta); yayımlanmış bina düzeyi sonuçları
(optik F1 0,605) bizim piksel IoU'muzla kıyaslanamaz.

**Ölçüm — QQB eğitime eklenince (21 Eylül 2026, SegFormer-B4, P2, tohum 42, Colab T4):** eğitim 1 013 → 1 352 karo.
Doğrulama IoU_hasar 0,455 → 0,431; sınama 0,413 → 0,392 (kesinlik 0,615 → 0,498, duyarlılık 0,558 → 0,646). QQB dış
sınamasında sağlam bina yanlış alarmı %1,03 → %1,13 (11 → 12 / 1 066), yıkık duyarlılığı 22 → 23 / 36; Adıyaman
(HOTOSM dış sınama) yıkık duyarlılığı 54 → 37 / 208. Aynı P2 ayarı iki ayrı günde sınamada 0,434 ve 0,413 verdiği için
tek tohum oynaması ~±0,02; fark bu sınırda ama doğrulama ile sınama aynı yönde. QQB'nin beklenen katkısı (yanlış
alarmı azaltmak) görülmedi. Öneri: veri kurulumu doğrulamaya göre seçildiği için QQB eğitime alınmasın; böylece QQB
dış sınaması da gerçekten dış kalır. Kayıt: `QuakeMind_veri/cikti/kosular/` (`P2`, `P2_qqb`).

---

## A-19 🟡 Focal kaybın α = 0,25 ayarı hasar piksellerine arka plandan daha az ağırlık veriyor
**Durum:** ÖLÇÜLDÜ, VARSAYILAN KORUNDU (22 Eylül 2026) — Kaggle, SegFormer-B4, P2, tohum 42: α 0,25 doğrulama 0,435 (tohum 7: 0,457) / sınama 0,426; **α 0,5** doğrulama **0,475** / sınama **0,400**; **α 0,75** doğrulama 0,470 / sınama 0,419; dengeli örnekleyici (%50) doğrulama 0,450 / sınama 0,423. Doğrulama α'yı büyütmeyi istiyor, sınama istemiyor: α kesinliği artırıp duyarlılığı düşürüyor (α 0,5: kesinlik 0,639, duyarlılık 0,517) ve **eşik 0,5'te sabit** olduğu için kalibrasyon farkı ölçüme karışıyor. İki ölçüt çeliştiği için varsayılan α 0,25 korundu; üç değer Tablo 21'e satır olarak girer. Eşiği doğrulamada ayarlamak ya da eşikten bağımsız ölçüt (AP) eklemek açık iş · **Bulundu:** 19 Eylül 2026 (DA-SegFormer incelemesi, `AKTARIM_BELGESI.md` Ç-11) · **İlgili:** A-15, Tablo 21

smp 0.5.0 `losses/_functional.py` satır 83–84: `loss *= alpha * target + (1 - alpha) * (1 - target)`. Bütün
eğitimlerimizde kullanılan `FocalLoss(mode="binary", alpha=0.25, gamma=2.0)` hasar piksellerini 0,25, arka planı 0,75 ile
çarpıyor (RetinaNet varsayılanı; γ = 2 kolay negatifleri ayrıca bastırıyor, Dice terimi de hasar sınıfına odaklı). Hata
değil ama "azınlığa odaklan" mantığının tersi ve hiç sınanmadı. **Yapılacak:** SegFormer-B4 / P2 ile α ∈ {0,25 · 0,5 · 0,75}
taraması (Tablo 21'deki kayıp ağırlığı taramasına kol olarak). Seçim doğrulama kümesinde; varsayılan değişmeden önce çoklu
tohumla doğrulanmalı.

---

## A-20 🟠 Tablo 15 (bölgeler arası genelleme) tasarımı il ile veri kümesini karıştırıyor ve gerçek aktarım testi içermiyor
**Durum:** KISMEN (21 Eylül 2026) — 02 defterinde il-dışarıda-bırakma (`BOLGE_EGITIMI = "haric:Hatay"` / `"haric:Kahramanmaraş"`) ve Tablo 15'te oran sütunu. P2'de MEDBFS eğitimde olmadığı için bölge koşuları zaten KATE-PD (+ KATE-CD öncesi) ile yapılır; bu koşularda QQB/HOTOSM kapalı tutulmalı. Madde 3 açık · **Bulundu:** 19 Eylül 2026 (Valentijn vd. 2020 incelemesi, `AKTARIM_BELGESI.md` Ç-16; önceki kayıtta tarih yanlışlıkla 20 Eylül yazılmıştı) · **İlgili:** A-15, A-16, Tablo 15

1. **Kaynak küme karışıklığı:** Hatay'ın karoları ağırlıkla KATE-PD (340 KATE-PD + 26 MEDBFS), Kahramanmaraş'ınkiler ağırlıkla
   MEDBFS (199 KATE-PD + 283 MEDBFS; 0,75 m, farklı etiket protokolü). Hatay ↔ Maraş farkı il değil veri kümesi farkı olabilir.
   **Yapılacak:** yalnız KATE-PD karolarıyla kontrol koşusu ya da sonuçların kaynak kümeye göre ayrı raporlanması.
2. **"Birleşik" satırı hedef ili de içerdiği için aktarım testi değil.** **Yapılacak:** "hedef il hariç diğer iller → hedef"
   (il-dışarıda-bırakma) satırı ve IoU(kaynak→hedef)/IoU(hedef→hedef) oran sütunu.
3. İsteğe bağlı: tek il eğitimlerini eşit eğitim miktarına alt-örnekleyen kontrol; az etiketle ince ayar eğrisi (1/2/5/10
   blok); eşik kayması (kaynak eşiği / kâhin eşik / AP) ayrı raporlanmalı.

---

## A-21 🟠 HOTOSM yıkık bina verisiyle eğitim genişletmesi — veri kalitesi notları
**Durum:** KARAR VERİLDİ (22 Eylül 2026, kullanıcıyla) — HOTOSM eğitime alınmıyor, yalnız Adıyaman dış sınaması; ikinci tohum koşulmadı (ölçüm tablosu ve madde 8'deki etiket kayması yeterli görüldü). 10 model P2 (KATE-PD + KATE-CD öncesi) ile — pakette eğitim 164 karo (106 dik, 58 eğik; 903 yıkık bina) + Adıyaman dış sınama 44 karo (208 yıkık bina); 02 defterine gömüldü, yerel duman testinde görüntü ve maske birebir. Etkisi SegFormer koşularıyla ölçülecek: ilk HOTOSM koşusu (P2_qqb_hotdik) veri yüklenmişken, eğitim başlamadan Colab ücretsiz çalışma zamanının ~3,3 saatte bağlantıyı kesmesiyle koşulamadı (21 Eylül 2026, 14.09); QQB'nin katkısı olumsuz çıktığı için (A-18) HOTOSM koşularının QQB'siz yapılması önerildi · **Bulundu:** 21 Eylül 2026 (veri genişletme; `QuakeMind_veri/araclar/hotosm_*.py`) · **İlgili:** A-15, A-16, A-18

HOTOSM yıkık binaları (ODbL) + Maxar Open Data deprem sonrası görüntüsü (CC BY-NC 4.0) ile yeni ilçelerde eğitim karosu:
1. **HDX dışa aktarımı eksik:** HOTOSM'un HDX'teki GeoJSON'u (22 Mayıs 2023) 3 239 poligon; aynı süzgeç ve tarihle
   Overpass 3 434 yol veriyor. Eksik 195 binanın 127'si seçili karolara düşüyor (çoğu Nurdağı ve Kahramanmaraş merkez).
   Eksikler tarihli Overpass kimlik sorgusuyla tamamlandı; aksi hâlde bu binalar maskede "hasarsız" (0) sayılırdı.
2. **Görüntü çoğunlukla eğik ve kaba:** KATE-PD ile çakışmayan 517 aday karonun 469'unda deprem sonrası Maxar var;
   yalnız 151'inde bakış açısı ≤ 30° (ortalama 21°), tümünün ortalaması 35°. Sahnelerin çoğu WorldView-2, 0,46–0,65 m.
   Karolar bu yüzden 0,5 m'de kesildi (256 m, 512 px). Eğik sahnede bina izi ile çatı arasında kayma olur.
   **Geç sahneler dışarıda (21 Eylül kontrol panosu):** 28 Şubat sahnelerinde bazı yıkık binaların enkazı kaldırılmış;
   etiket 1, görüntü düz toprak → model "boş arsa = hasar" öğrenebilir. Kullanılan sahnelere göre: dik + erken (≤ 13 Şubat)
   124 karo, eğik + erken 108, dik + geç 27, eğik + geç 210. 23–28 Şubat sahneli 237 karo deftere gömülen pakete girmez;
   deneyler `HOTOSM_EGITIME = "dik"` (124'ün eğitime düşenleri) ve `"erken"` (232'nin eğitime düşenleri).
   Ayrıca OSM izleri ile çatılar arasında 1–3 m kayma görülüyor (izler başka görüntülerden çizilmiş).
3. **Etiket tanımı farklı:** HOTOSM yalnız "yıkık" (destroyed:building); KATE-PD "hasarlı bina". HOTOSM eksiksiz de değil →
   maskede yıkık = 1, diğer binalar = 255 (yok say), gerisi 0.
4. **"Diğer binalar" (255) Microsoft Global ML Building Footprints'ten (ODbL):** OSM'den çekilmek istendi; tarihli
   (2023-05-22) ve bugünkü sorgular genel Overpass sunucularında saatlerce 504 / zaman aşımı verdi (232 erken karonun ~30'u
   alınabildi; ilk 10 karoda 2023 ile bugün arasındaki fark %0,8 ölçülmüştü). Kullanıcı onayıyla (300 MB'a kadar) 8 quadkey
   dosyası, 84 MB indirildi; erken karolara 15 419 bina düştü (`araclar/hotosm_ms_binalar.py`). Yıkık binalar yine OSM/HOTOSM.
5. **Adıyaman merkez** hiç eğitilmez; yeni ilçede yıkık bina duyarlılığı için dış sınama.
6. **Görüntü:** 469 karonun hepsi okundu (COG pencere okuması, dosya indirilmedi); 83 karoda ilk sahnede veri dışı (siyah)
   alan çıktı, yedek sahne kullanıldı ve karonun sahne bilgisi (tarih, uydu, bakış) yedeğe göre yazıldı.
7. **Bulut:** Maxar bulut maskesi 1 837 sahnenin yalnız 13'ünde var; sahne düzeyi bulut yüzdesi karo için yanıltıcı (%21
   bulutlu sahneden temiz karolar çıktı). Karo düzeyinde parlak + düşük doygunluklu + dokusuz + geniş alan = bulut
   (kalibrasyon: bulutlu karolarda %46–79, bulutsuz sahnelerde %0–2). Bulut > %25 olan 13 karo çıkarıldı, kalanlarda bulut
   pikselleri (yıkık bina dahil) 255. Karla kaplı ama dokusu görünen karolar (ör. Adıyaman, 8 Şubat) bulut sayılmadı, kaldı.
   Dik karoların çoğu 7 Şubat GeoEye-1 / WorldView-3 sahnelerinden; GeoEye-1 sahneleri belirgin karanlık (eğitimdeki parlaklık
   artırması karşılar diye bırakıldı). "Önce bulutsuz" seçim kuralında bulutsuz erken sahnelerin neredeyse hepsi eğik (9 dik).

8. **Etiket kayması görsel olarak doğrulandı (22 Eylül, kullanıcı fark etti):** QQB (OSM) ve HOTOSM + Microsoft
   poligonları görüntüdeki çatılardan kayık (`QuakeMind_veri/cikti/etiket_kaymasi_qqb.png`, `…_hotosm.png`, 3× büyütme).
   Nedenler: poligonlar bu görüntüde değil başka görüntülerde çizilmiş; eğik çekimde (ör. 21,5°) yüksek binanın çatısı
   zemindeki izden bina yüksekliği × tan(açı) kadar kayar (15 m bina ≈ 6 m ≈ 12 piksel, 0,5 m'de). Bazı "yıkık" izlerin
   üstünde sağlam görünen çatı var: ya kayma ya da katların çöküp çatının üstte kaldığı çökme (uydudan ayırt etmek zor).
   HOTOSM eksik: her yıkık bina haritalanmamış, Microsoft izleri bazı binaları atlıyor. Bakılan KATE-PD örneklerinde
   etiketler görüntüyle uyumlu görünüyor (kayma ölçülmedi). Sonuç: QQB/HOTOSM piksel IoU'su kaymadan cezalanır; bina
   düzeyi ölçüm (≥ %25 örtüşme) daha toleranslı. QQB ve HOTOSM'un eğitime katkı vermemesinin olası bir nedeni.

**Ölçüm (22 Eylül 2026, Kaggle T4, SegFormer-B4, P2, tohum 42; Colab ücretsiz kotası dolduğu için eğitim Kaggle'a
taşındı, P2 aynı platformda yeniden koşuldu):**

| | P2 | + HOTOSM dik (1 119 karo) | + HOTOSM erken (1 177 karo) |
|---|---|---|---|
| Doğrulama IoU (en iyi dönem) | 0,435 | 0,452 | 0,454 |
| Doğrulama, en iyi 5 dönemin ortalaması | 0,430 | 0,443 | 0,447 |
| Sınama IoU | 0,426 | 0,346 | 0,423 |
| Adıyaman yıkık bina bulunan | 40 / 208 | 50 / 208 | 36 / 208 |
| QQB sağlam binada yanlış alarm | 7 / 1 066 | 30 / 1 066 | 10 / 1 066 |

Doğrulamadaki artış (+0,017…0,019) aynı P2 ayarının Colab–Kaggle farkı (0,455 / 0,435) kadar; sınamada ve dış
sınamalarda tutarlı kazanç yok (dik: sınama −0,08, yanlış alarm 4 kat). HOTOSM'un katkısı tek tohumla gürültüden
ayrılamıyor. Karar (22 Eylül, kullanıcıyla): ikinci tohum koşulmadan HOTOSM eğitimden çıkarıldı (madde 8'deki etiket
kayması da göz önüne alınarak). Kayıt: `QuakeMind_veri/cikti/kosular/kaggle/`.

---

## A-23 🟡 Deprem öncesi görüntüyü de girdi yapmak (değişim tespiti) kazanç vermedi
**Durum:** ÖLÇÜLDÜ (23 Eylül 2026) — 03 defterinde `GIRDI = "cd_oncesi_sonrasi"` (6 kanal: sonrası RGB + öncesi RGB, öncesi renkleri sonrasına histogram eşlemesiyle uydurulur) ve kıyas tabanı `"cd_sonrasi"`; ikisi de KATE-CD'nin 377 eğitim çiftiyle, aynı 41 sınama karosunda · **Bulundu:** 22 Eylül 2026 (kullanıcı önerisi: "KATE-CD'de öncesi, sonrası ve etiket var") · **İlgili:** A-15, A-16

| SegFormer-B4, tohum 42 | Eğitim | Doğrulama IoU | Sınama IoU (41 karo) | Kesinlik | Duyarlılık |
|---|---|---|---|---|---|
| Yalnız sonrası (`cd_sonrasi`) | 377 çift | 0,456 | **0,448** | 0,602 | 0,637 |
| Öncesi + sonrası (`cd_oncesi_sonrasi`) | 377 çift | 0,449 | **0,449** | 0,555 | 0,701 |

Fark +0,001: öncesi görüntüsü bu veri ve bu mimaride kazanç vermiyor (duyarlılık +0,06, kesinlik −0,05; denge kayıyor).
Olası nedenler: öncesi görüntüler farklı tarih/mevsim ve bazı çiftlerde eşlemesi kusurlu; erken birleştirme (6 kanal) yerine
iki kollu (siyam) mimari ve fark özellikleri denenmedi; 377 çift az. Aynı 41 karoda tam veriyle eğitilen 10 modelin değeri
0,313–0,490 (en iyi upernet_mitb4 0,490) — yani çift verisiyle sınırlı eğitim, tam veriyle eğitmenin gerisinde kalabiliyor.
**Yapılacak (isteğe bağlı):** siyam mimari + fark katmanı; MEDBFS çiftleriyle (438) birlikte eğitim.

---

# B. MAKALE — HENÜZ ÖLÇÜLMEMİŞ

## B-01 🔴 Görev tabanlı değerlendirme (Bölüm 4.7) — makalenin merkezî katkısı
**Durum:** AÇIK

Bölütleme kalitesinin operasyonel sonuca etkisi. Tablo 18 tamamen iskelet.
Makalenin özgünlük iddiası bu; ölçülmeden "katkı" olarak savunulması zor.
Gerekli: kapanma katmanının model çıkarımından türetilmesi (bkz. E-01).

## B-02 🟠 Gerçek yol hasarı bölütlemesi ölçülmedi
**Durum:** AÇIK

Tablo 12 bina hasarı görevinde koşuldu; yol hasarı için piksel etiketli Türkiye
kümesi yok. Tablo 5 (eğitim kümesi künyesi) tamamen `[ÖLÇÜLECEK]`.
Seçenekler: (a) kendi kümemizi etiketle, (b) CAU-RoadDamage'ı harici test kümesi
olarak kullan, (c) yol eksenini açıkça gelecek çalışmaya bırak.

## B-03 🟠 YOLO tespit başarımı (mAP) ölçülmedi
**Durum:** AÇIK

`model_benchmarks/03_yer_seviyesi/` altında 8 defter hazır (YOLOv8, YOLOv8 ölçek,
YOLOv11, YOLOv11-seg, Faster R-CNN, RT-DETR, YOLOv8+SimAM, Mask R-CNN) ama
**hiç sonuç yok**. Makalede yer seviyesi için tek ölçülen şey gecikme.

## B-04 🟠 Rota kıyaslaması ölçülmedi
**Durum:** AÇIK

`model_benchmarks/06_rota/` boş (sonuç yok). R1 (görüş mesafeli ajan) ve
R2 (bilgi paylaşan filo) ara referansları tanımlı ama koşulmamış. R0 tek başına
"straw man" olarak okunur ve %87,4 kazancı savunulamaz kılar.

## B-05 🟠 Kapanma katmanının yer gerçeğine göre değerlendirilmesi (Bölüm 4.3)
**Durum:** AÇIK

Tablo 13 iskelet. Vektör–piksel tampon kuralı ve τ eşiği tanımlı ama uygulanmamış.

## B-06 🟡 Bölgeler arası genelleme (Bölüm 4.4)
**Durum:** AÇIK

Tablo 14 iskelet. Hatay ↔ Kahramanmaraş çapraz koşum. Yeni veri gerekmiyor,
yalnızca bölmenin coğrafi yapılması yeterli.

## B-07 🟡 Bileşen çıkarma / parametre duyarlılığı (Bölüm 4.9)
**Durum:** AÇIK

Tablo 20 iskelet: harmanlama var/yok, morfoloji seviyesi 0/1/2, kayıp ağırlıkları,
`r_h` ∈ {10, 25, 50, 100} m, λ(d) basamakları, kalite eşiği, risk ağırlıkları.

## B-08 🟡 GFLOPs ve çıkarım süresi
**Durum:** AÇIK

Tablo 12'de iki sütun `[ÖLÇÜLECEK]`. Mobil/uç cihaz argümanı bunlarsız savunulamaz.

## B-10 🟡 Gecikme ölçümleri n = 2
**Durum:** AÇIK

YOLOv8 için iki gözlem (153,6 ms; 173,3 ms), BERTurk için iki gözlem
(48,8 ms; 11 419,4 ms). Isınma sonrası ≥100 tekrarla medyan/p95/p99 ölçülmeli.
BERTurk'ün 11,4 saniyesi bileşenlerine ayrıştırılmamış (ısınma / biçimbilim /
ileri geçiş / NER / coğrafi kodlama).

## B-11 🟡 18 eşleştirilmiş görev için istatistiksel test yok
**Durum:** AÇIK

Sadece toplamlar veriliyor. 352,5 dk'lık uç değer dağılımın ağır kuyruklu olduğunu
gösteriyor. Görev başına fark tablosu + medyan + çeyrekler arası açıklık +
Wilcoxon işaretli sıra testi + etki büyüklüğü eklenmeli.

## B-12 🟡 Şekil 9 üretilmemiş
**Durum:** AÇIK

Görsel bölütleme karşılaştırması. Makalede "Bu şekil üretilmemiştir" notu var.

---

## B-13 🟠 Türkçe metin veri kümesinin künyesi makalede hiç geçmiyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-33

`intent_test`, `deprem-private` ve `anonymized` sözcükleri makalede **sıfır kez**
geçiyor. Tablo 21'deki 305 kayıtlık sınama kümesinin kaynağı, etiketleme yönergesi,
etiketleyici sayısı ve erişim koşulu yazılmamış. Çok etiketli bir kümede bunlar
olmadan makro-F₁ tartışması yorumlanamaz. F-3 ile birlikte kapatılmalı.

---

# C. MAKALE — UYGULANMAMIŞ YETENEKLER

## C-01 🟠 Kapanma katmanı sentetik
**Durum:** AÇIK

Senaryo, kapanmaları bölütleme çıkarımından değil sentetik üreticiden alıyor.
Oranı EMSR648 ile tutarlı (%0,6–4,5 ↔ %1,52–1,71 katı kural) ama **uzamsal dağılım
modelden gelmiyor**. Makale bunu Öz'de açıkça söylüyor — bu doğru davranış.
Kapanması B-01'e bağlı.

## C-02 🟡 Karo kalite filtresi uygulanmamış
**Durum:** AÇIK

Bölüm 3.3'teki Laplacian varyans filtresi tanımlı ama kodda yok. Makalede
"bu sürümde uygulanmamıştır" diye işaretli. Elenen karo oranı `[ÖLÇÜLECEK]`.

## C-03 🟡 Çok kipli füzyon uygulanmamış
**Durum:** AÇIK

`S = w₁·P_seg + w₂·P_nlp` formülü kodda yok. Gelecek çalışma olarak sunuluyor.

## C-04 🟡 BLE mesh taşıma katmanı uygulanmamış
**Durum:** AÇIK

`commsStatus` bir veri alanı, protokol değil. 81–85 baytlık paket ölçümü
makaleden çıkarıldı (doğru karar). Ya gerçekten uygulanmalı ya tasarım önerisi
olarak kalmalı.

## C-05 🟡 Risk modülü sevk zincirine bağlı değil
**Durum:** AÇIK

Denklem (7) tanımlı, Tablo 22'de ölçülmüş, ama Bölüm 4.5'teki senaryoda
kullanılmıyor. Hakem "bu bölüm çıkarılsa makale ne kaybeder?" diye sorar.
Ya zincire bağla ya afet öncesi planlama olarak ayrı konumlandır (şu an ikincisi
yapılmış, kabul edilebilir).

---

# D. DEPO VE KOD

## D-01 🟠 Google Earth karoları yayında kullanılamaz
**Durum:** AÇIK

`backend/apps/road_damage/utils/fetcher.py` içinde
`mt1.google.com/vt/lyrs=s` üzerinden Google uydu karosu çekiliyor. Toplu indirme
ve akademik yayında kullanım izne tabi. Makale koşumları **Maxar Open Data** ile
yapılmalı (hem ücretsiz hem 17 408² çözünürlükte).

## D-02 🟡 Karşılaştırma CSV'si SegFormer'ın değerini yanlış sütuna koymuş
**Durum:** AÇIK

`model_benchmarks/01_yol_hasari/local_colab_run/results/00_comparison_table.csv`
SegFormer'ın 0,4276'sını `mean_iou` sütununa yazmış. Oysa
`optimized_training_colab.ipynb` içindeki `compute_iou` ikili **ön plan** IoU'su
hesaplıyor. Buna bağlı olarak `00_comparison_chart.png` ön plan IoU'sunu ortalama
IoU'yla yan yana çiziyor ve SegFormer'ı haksız yere çok kötü gösteriyor.
Makalenin Şekil 7'si SegFormer'ı dışarıda bırakarak bundan kaçınmış, ama depo
dosyası ileride yanıltır.

## D-03 ⚪ Klasör adı yanıltıcı
**Durum:** AÇIK

`model_benchmarks/01_yol_hasari/` içindeki deney KATE-CD + MedBFS ile, yani
**bina** verisiyle koşulmuş. Klasör adı `01_bina_hasari_kate_medbfs` gibi
düzeltilmeli veya README'ye açık not düşülmeli.

## D-05 🟠 Defter şablonu ile fiilen koşulan hiperparametreler uyuşmuyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026

**Sorun.** `model_benchmarks/01_yol_hasari/seg_common.py` içindeki `CONFIG`
öğrenme oranını 6 × 10⁻⁵, yığın boyutunu 4, devir sayısını 30 olarak tanımlıyor.
Buna karşılık sonuçların üretildiği `local_colab_run/build_notebook.py`
lr = 2 × 10⁻⁴, yığın 8, en çok 50 devir, sabır 8 kullanıyor. Makale ikincisini
raporluyor (doğru olan bu), ancak `01_yol_hasari/*.ipynb` defterleri
`seg_common.py`'yi çağırdığı için bunlardan yeniden koşan biri **farklı sonuç
alır**.

**Yapılacak.** `seg_common.py` CONFIG'ini fiilen koşulan değerlere eşitle veya
defterlerin hangi yapılandırmayı kullandığını README'de açıkça belirt.
Tekrarlanabilirlik açısından gereklidir.

---

## D-04 ⚪ Akış diyagramlarındaki adlandırmalar koddaki gerçekle uyuşmuyor
**Durum:** AÇIK

"GNN Rota Motoru" → gerçekte Dijkstra/A*. "Multimodal Füzyon" formülü → kodda yok.
Makaleden çıkarıldı ama diyagramlar hâlâ eski; sunum/rapor materyalleri
güncellenmeli.

---

## D-06 🔴 Word belgesindeki 17 denklemin tamamı ham LaTeX
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-10

`MAKALE_TASLAK_TR (1).docx` → `word/document.xml` üzerinde sayım:
`<m:oMath>` = **0**, `w:val="subscript"` = **0**, `w:val="superscript"` = **0**;
buna karşılık ham `\tag{` = 17, `\frac` = 12, `\begin{cases}` = 1, `\left` = 4.
Okuyucu Denklem (9) yerine ham LaTeX kaynağını görüyor.

**Neden oldu.** `.docx`, bu oturumda yazılan `md2docx.py` dönüştürücüsü yerine
başka bir araçla yeniden üretilmiş; o araç LaTeX'i düz metne düşürmüş.

**Yapılacak.** Word üzerindeki içerik değişikliklerini `MAKALE_TASLAK_TR.md`'ye
işle, sonra `.docx`'i `md2docx.py` ile yeniden üret (gerçek alt/üst simge üretir).
Dergi denklem editörü şart koşarsa 17 denklem Word'de **Alt + =** ile denklem
nesnesine çevrilir.

---

## D-07 🟠 Model seçimi `mean_iou` ile yapılmış, raporlama `iou_fg` ile
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-11

`model_benchmarks/01_yol_hasari/local_colab_run/build_notebook.py` satır 278:
`if val_metrics['mean_iou'] > best_val_iou:` — en iyi ağırlık ve erken durdurma
**ortalama IoU** üzerinden seçiliyor. Oysa makale ortalama IoU'nun arka plan
baskınlığı nedeniyle yanıltıcı olduğunu savunup IoU_hasar'ı esas ölçüt yapıyor.
Ölçüt tartışmasının inandırıcılığını zedeliyor.

**Yapılacak.** Erken durdurmayı `iou_fg`'ye taşıyıp yeniden koştur (A-01 ile aynı
koşumda kapanır) ya da Bölüm 4.2'ye açık bir kayıt cümlesi ekle.

## D-08 🔴 Roboflow API anahtarı makale dalında açık metin olarak duruyor
**Durum:** AÇIK · **Bulundu:** 16 Eylül 2026 (M-62 incelemesi)

`model_benchmarks/03_yer_seviyesi/local_colab_run/build_notebook.py` ve aynı klasördeki
`00_catlak_bina_yolo.ipynb`, Roboflow hesabının API anahtarını kodun içinde açıkça taşıyor (değer bu
dosyaya bilerek yazılmadı). Depo şu an özel, ancak makale "kaynak kod erişime açılacaktır" diyor; depo
açıldığında anahtar herkese görünür olur ve git geçmişinde kalır.

**Yapılacak.** (1) Roboflow panelinden anahtarı **iptal edip yenisini üret** (asıl koruma budur; dosyadan
silmek geçmişteki kopyayı kaldırmaz). (2) Kodda anahtarı ortam değişkeninden ya da Colab "Secrets"ten oku.
(3) Depo açılmadan önce geçmişte başka gizli bilgi olup olmadığını tara.

## D-09 🟡 Risk yeniden koşumu `leaderboard.csv`'den iki naif taban satırını sildi
**Durum:** AÇIK · **Bulundu:** 17 Eylül 2026 (`UtBird/QuakeMind` makale dalı, commit `7024d64` incelemesi)

`model_benchmarks/05_risk_skoru/local_run/run_all_risk.py` yeniden koşulunca `results/leaderboard.csv` yalnız yedi
modelle baştan yazıldı; 13 Eylül'de (M-09) eklenen **"Naif — Yalnızca fay mesafesi (r0a)"** ve **"Naif — Yalnızca
sismisite yoğunluğu (r0b)"** satırları düştü. Makaledeki Tablo 23 bu iki satırı içeriyor, yani tablonun kaynak
dosyası artık tabloyla uyuşmuyor. Satırların JSON'ları (`naive_fault_distance.json`, `naive_seismicity.json`)
değişmedi; `naive_baselines.py` leaderboard'a yazmıyor.
Ayrıca yeniden koşumda **eğitim süreleri** değişti (CatBoost 14,61 → 14,97 sn, RO 6,32 → 5,21, XGBoost 10,31 → 11,00,
LR 0,32 → 0,14, topluluk 33,88 → 36,46, LightGBM 1,45 → 1,23, ÇKA 0,40 → 0,33). Tablo 23 eski süreleri taşıyor.
Başarım değerleri ise birebir aynı (katlama kayıtları dahil; fark < 10⁻¹²).

**Yapılacak.** (1) İki naif satırı `leaderboard.csv`'ye geri ekle ya da `run_all_risk.py`'nin naif JSON'ları da
okumasını sağla. (2) Tablo 23'teki eğitim sürelerini yeni koşuma göre güncelle ya da "süreler ilk koşumdan; makineye
bağlıdır" notu düş.

---

# E. SENARYO VE ÖLÇÜM

## E-01 🔴 Kapanma katmanı EMSR648'e bağlanmadı
**Durum:** KISMEN KAPALI (16 Eylül 2026) — EMSR kapsamındaki 4 ilçede bağlandı (J-12, J-28)

`benchmark/data/copernicus/` altında EMSR648 paketleri indirilmiş, açılmış ve
`*_copernicus_ground_truth.json` üretilmiş durumda. Kapanma üretimine bağlanmayı
bekliyor. Bu iş B-01, B-05 ve C-01'i aynı anda kapatır.

**Karar gerekiyor:** derece → geçilebilirlik kuralı. Kahramanmaraş'ta hiç
"Destroyed" yol yok, 134'ü de "Damaged". Önerilen: Destroyed = kapalı,
Damaged = ağırlık cezası, Possibly damaged = açık.

**16 Eylül 2026 güncellemesi.** Bağlandı: EMSR yol çizgisi → OSM kenarı eşlemesi
(`closures_from_lines`, 8 m tampon, ≥ %50 örtüşme), `POST /api/road_damage/closures_from_emsr`,
`full_scenario.py --closure-source emsr --emsr-rule {strict,medium,loose}`.
Kural **üç seçenekli ikili kapanma** olarak uygulandı (katı = Destroyed, orta = +Damaged,
gevşek = +Possibly damaged) ve üçü de koşuldu (J-28). Yukarıdaki öneri
("Damaged = ağırlık cezası") **uygulanmadı** — makalede duyarlılık olarak üç kural
birlikte raporlanmalı (M-26). **Açık kalan:** EMSR kapsamı dışındaki 4 ilçe
(H-Z2 İskenderun, H-Z4 Samandağ, H-Z5 Belen, K-Z3 Pazarcık) hâlâ yalnız sentetik
kapanmayla koşulabiliyor; EMSR AOI'lerinin dışında kalan ~%6 kenar açık kabul ediliyor.

## E-02 🟠 U-dönüşü cezası bir model parametresi
**Durum:** KISMEN KAPALI

`t_u = 20 dk` ölçülmüş değil, varsayım. Kazancın %94,8'ini bu üretiyor
(16 Eylül 2026 koşularında %96; EMSR648 gevşek kuralda 13 atamada 87 keşif — J-28).
Makalede iki paydayla raporlanıyor ve Tablo 17'de tarama var — **bu yeterli
çözüm**. Açık kalan: cezanın Algoritma 1'deki fiziksel karşılığı
(kavşakta yeniden yönlenme) 20 dk için gerekçelendirilmeli.

## E-03 🟠 Rota geçerliliği denetimi totolojik
**Durum:** KISMEN KAPALI

"18 rotanın hiçbiri kapalı segmentten geçmedi" — sert kapatma kenarları çizgeden
çıkardığı için bu matematiksel zorunluluk. Makale bunu açıkça söylüyor (doğru
davranış). Gerçek bir geçilebilirlik doğrulaması için saha verisi gerekir.

## E-04 🟡 NLP yanlış negatifi: 6 ihbarın 2'si elendi
**Durum:** KISMEN KAPALI

Her ikisi de hayati medikal çağrıydı. Neden teşhis edildi: eleme kuralı kategori
bakımından asimetrikti (kurtarma yalnızca yol/ulaşım terimleri için tanımlıydı).
Bölüm 3.6'da kural düzeltildi (kurtarma kümesi beş kategoriye genişletildi,
düşük güvenli kayıtlar "belirsiz" kuyruğuna alınıyor).
**Açık kalan:** düzeltilmiş kuralın kodda uygulanması ve yeniden ölçülmesi.

# F. GİT VE SÜREÇ

*Bu bölümün bütün maddeleri kapandı; metinleri `EKSIKLER_ARSIV.md`'de.*

---

# G. KAYNAKÇA

## G-01 🟠 Altı kaynak yazarsız
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-35

[23], [24], [25], [29], [31] ve [57] doğrudan tırnak içinde başlıkla başlıyor,
yazar alanı yok. [56] ve [57] `[KÜNYE DOĞRULANACAK]` notu taşıyor, diğer dördünde
not bile yok. Hiçbir dergi yazarsız kaynak kabul etmez.

**Yapılacak.** Altı kaydın yazar listelerini DOI üzerinden tamamla; aynı geçişte
[56] KATE-CD künyesini doğrula.

---

## G-02 🟠 ConvBERTurk ve DistilBERTurk için yanlış kaynak gösterilmiş
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-36

Bölüm 4.10: *"DistilBERTurk [52], ConvBERTurk [51]"*. Ancak [51] = Jiang ve ark.,
*ConvBERT* (NeurIPS 2020) ve [52] = Sanh ve ark., *DistilBERT* (arXiv:1910.01108)
— ikisi de genel mimari/yöntem makalesi, Türkçe model değil. Kullanılan
ağırlıklar Schweter'in Türkçe modelleridir, yani [32] ile aynı kaynağa aittir.

**Yapılacak.** Ya [32]'ye atıfla ver ve mimariyi ikincil belirt, ya da model
kartlarına (`dbmdz/distilbert-base-turkish-cased`,
`dbmdz/convbert-base-turkish-cased`) ayrı kaynak ekle.

---

## G-03 🟡 [1] hem AFAD olay raporu hem deprem kataloğu için kullanılıyor
**Durum:** AÇIK · **Bulundu:** 12 Eylül 2026 · **Birleşik liste:** M-37

[1] = AFAD Ön Değerlendirme Raporu (2023), bir olay raporudur; Bölüm 3.7'de risk
modelinin eğitildiği **katalog** için de aynı numara kullanılıyor. İkisi farklı
veri ürünleridir.

**Yapılacak.** Katalog için ayrı kaynak ekle (AFAD Deprem Kataloğu / TDVMS,
erişim tarihi ve sorgu aralığıyla). Tablo 2 ile tutarlı olmalı.

---

# H. İNCELENİP KAPATILAN ŞÜPHELER

*Bu bölümün bütün maddeleri kapandı; metinleri `EKSIKLER_ARSIV.md`'de.*

---

# I. ÖNERİLEN SIRA

| # | İş | Kapattığı maddeler | Tahmini süre |
|---|---|---|---|
| 0 | **Yazım işleri** — Bölüm 3'teki üç tanımsız mekanizmayı yaz, denklemleri yeniden üret, kaynakçayı düzelt | A-06, A-07, A-08, A-09, D-06, G-01, G-02 | 2–3 gün |
| 1 | SegFormer'ı üç katmanlı bölmeyle yeniden koştur (erken durdurmayı `iou_fg`'ye taşıyarak) | A-01, A-02, A-03, D-07 | 1 gün |
| 2 | EMSR648'i kapanma katmanına bağla | E-01, B-05, C-01 | 2–3 gün |
| 3 | Görev tabanlı değerlendirmeyi koştur | B-01 | 2–3 gün |
| 4 | YOLO defterlerini koştur | B-03 | 2–3 gün |
| 5 | R1 ve R2 ara referanslarını ekle | B-04 | 1–2 gün |
| 6 | Bölgeler arası genelleme | B-06 | 1–2 gün |
| 7 | Gecikmeleri yeniden ölç (n ≥ 100) | B-10 | yarım gün |
| 8 | Donanım künyesi ve `v_ort`'u doldur | B-09 | yarım gün |
| 9 | Depo düzeltmeleri (CSV sütunu, klasör adı) | D-02, D-03 | yarım gün |
| 10 | Görüntü kaynağını Maxar'a taşı | D-01 | 1 gün |

0 numaralı iş **koşum gerektirmez** ve hocaya gönderilecek taslağın önkoşuludur;
Bölüm 3'te tanımlanmamış bir mekanizmanın Bölüm 4'te kullanılması, eksik ölçümden
daha ağır bir kusurdur. Ardından ilk üç iş bittiğinde makalenin en kırılgan
noktaları kapanır.

**Not.** Makale özelindeki tüm maddeler tek bir dosyada birleştirilmiştir:
`MAKALE_DUZELTME_LISTESI.md` (kimlikler `M-01` … `M-48`, öncelik sırası ve iki
listenin kimlik eşlemesi orada).

---

# J. PERFORMANS VE SİSTEM (gecikme / kaynak yönetimi)

> Bu bölümdeki her madde **ölçülmüştür**. Ölçüm makinesi: kullanıcının kendi PC'si
> (Intel Core i7 14. nesil, 16 GB RAM, GPU hızlandırma yok — bkz. B-09). Graf
> ölçümleri `osm_graph_cache/b93e549b00f9debf.pkl` (18 004 düğüm / 39 285 kenar,
> Kahramanmaraş Merkez ölçeği) üzerinde yapıldı. Tarih: 15 Eylül 2026.

## J-22 🔴 r_h kalibre edilmemiş — 25 m'de model gerçeğin ~8 katı yol kapatıyor
**Durum:** AÇIK · **Bulundu:** 16 Eylül 2026 · **İlgili:** J-19, M-26, M-27

**Ölçüm.** J-19'un yarıçap kuralı, **gerçek model çıktısı** üzerinde (Antakya
merkezi, Maxar Open Data 2023-02-11, z=18 / 0,48 m/px, 389 yol kenarı) farklı
r_h değerleriyle koşturuldu ve **aynı alanın** EMSR648 AOI11 MONIT01 yer
gerçeğiyle karşılaştırıldı:

| Kural | Kapalı kenar | Oran |
|---|---|---|
| Eski kural (hasar yol pikselinde) | 0 | %0,0 |
| r_h = 5 m | 30 | %7,7 |
| r_h = 10 m | 46 | %11,8 |
| r_h = 15 m | 76 | %19,5 |
| **r_h = 25 m (makaledeki değer)** | **100** | **%25,7** |
| r_h = 50 m | 188 | %48,3 |
| **EMSR648 — aynı alan, yollar** | 5 / 156 | **%3,2** |
| EMSR648 — aynı alan, binalar | 21 / 150 | %14,0 |

Karşılaştırma aynı 0,3 km'lik alan üzerinden yapıldı; EMSR648'in AOI geneli
ortalaması (%1,58) bu alan için adil değil çünkü burası Antakya'nın en çok
yıkılan merkezi.

**Sonuç.** Makalede belgelenen r_h = 25 m bu örneklemde gerçeğin **~8 katı**
kapanma üretiyor. En yakın değer (5 m) bile ~2,4 kat fazla. Eğilim r_h ≈ 2-3 m
civarını işaret ediyor, ama bu **tek bir 389 kenarlık örneklem** — kalibrasyon
için yetersiz.

**Dürüst kayıt — iki olası sebep ayrıştırılmadı.** (a) r_h fazla büyük;
(b) model %1,26 piksel hasar buluyor ama bunların ne kadarı gerçek hasar
bilinmiyor (A-01: SegFormer'ın IoU_hasar'ı 0,37-0,43 arası, yani yanlış pozitif
oranı yüksek olabilir). İkisi birlikte de olabilir.

**Yapılacak.** r_h'yi EMSR648'in kapsadığı 4 bölgede (H-Z1, H-Z3, K-Z1, K-Z2)
çok sayıda örnek alan üzerinden, yer gerçeğiyle hatayı en aza indiren değere
kalibre et. Bu aynı zamanda M-26 (Tablo 19) ve M-27 (Tablo 20) için gereken
duyarlılık verisini üretir.

---

## J-29 🔴 Çoklu tohum (10 tohum): tek tohumlu sonuç kazancı yukarı çekiyordu
**Durum:** AÇIK — sonuçlar makaleye işlenmeli · **Bulundu:** 16 Eylül 2026 · **İlgili:** E-06 (kapandı), E-02, J-28, J-30, M-20, M-25, M-26

**Tasarım.** `benchmark/multi_seed.py` — J-28'in dokuz yapılandırması × tohum 42–51 =
90 koşu (180 il yarısı), toplam ~49 dk, hatasız. Tohum afetzede yerleşimini (tüm
kaynaklarda) ve sentetik kapanma kümesini (yalnız sentetikte) değiştirir; EMSR648 ve
model kapanmaları sabittir. **Tohum 42, J-28 koşularını afetzede konumları dahil birebir
yeniden üretti** (koşular deterministik). Süreler **aynı küme** üzerinden, tohum başına
toplamların ortalama ± standart sapmasıdır. Çıktılar: `runs/multi_seed/`
(`multi_seed_tablo.md`, `multi_seed_summary.json`, koşu başına klasör ve günlük).

| Yapılandırma (afetzede) | Rotalanan | QuakeMind (dk) | Klasik (dk) | Kazanç (dk) | Kazanç %95 GA | Yol farkı (dk) | Klasik ek yol | U-dönüşü payı | Tohum 42 kazancı | 10 tohum aralığı |
|---|---|---|---|---|---|---|---|---|---|---|
| v2 sentetik, 8 ilçe (18) | 17,8 ± 0,4 | 203,5 ± 18,9 | 1 552,0 ± 252,0 | **1 348,5 ± 241,7** | [1 175,6; 1 521,4] | 54,5 ± 15,2 | %26,7 ± 6,9 | %96 | 1 522,6 | 978,1–1 678,0 |
| v2 sentetik, 4 ilçe (13) | 13,0 | 153,4 ± 17,8 | 1 262,7 ± 219,9 | 1 109,3 ± 209,3 | [959,6; 1 259,0] | 35,3 ± 12,7 | %22,8 ± 6,7 | %97 | 1 420,0 (en yüksek) | 829,6–1 420,0 |
| EMSR648 katı (13) | 13,0 | 144,3 ± 23,0 | 197,1 ± 59,9 | 52,8 ± 47,1 | [19,1; 86,5] | 0,8 ± 1,1 | %0,5 ± 0,8 | %99 | 60,4 | 0,0–121,9 |
| EMSR648 orta (13) | 13,0 | 154,0 ± 23,2 | 1 406,2 ± 589,7 | 1 252,2 ± 579,5 | [837,7; 1 666,8] | 50,2 ± 30,6 | %32,2 ± 18,5 | %96 | 1 735,6 | 304,5–2 248,0 |
| **EMSR648 gevşek (13)** | 13,0 | **154,1 ± 23,3** | **1 433,0 ± 607,8** | **1 278,9 ± 597,1** | [851,7; 1 706,1] | **50,9 ± 31,1** | %32,5 ± 18,7 | %96 | 1 817,2 | 304,5–2 309,8 |
| Drone sentetik (9) | 8,7 ± 0,9 | 16,5 ± 2,9 | 81,3 ± 59,9 | 64,8 ± 58,4 | [23,1; 106,6] | 0,8 ± 0,8 | %5,3 ± 4,7 | %98 | 141,4 | 0,0–181,8 |
| Drone EMSR648 gevşek (9) | 9,0 | 18,4 ± 1,4 | 58,7 ± 17,3 | 40,3 ± 16,4 | [28,5; 52,0] | 0,3 ± 0,1 | %1,5 ± 0,7 | %99 | 40,2 | 0,0–60,4 |
| Drone model z18, r_h = 0 (9) | 9,0 | 16,7 ± 1,6 | 20,7 ± 8,1 | 4,0 ± 8,4 | [−2,0; 10,0] | 0,0 | %0,0 | %100 | 0,0 | 0,0–20,0 |
| Drone model z19, r_h = 15 (9) | **2,1 ± 0,6** | 1,9 ± 0,9 | 3,9 ± 6,3 | 2,0 ± 6,3 | [−2,5; 6,5] | 0,0 | %0,0 | %100 | 0,0 | 0,0–20,0 |

"Klasik ek yol" = klasik ekibin U-dönüşü cezası hariç yürüdüğü fazladan yol / QuakeMind yolu.

**Bulgular.**
1. **Tohum 42 iyimser uçtaydı.** 4 ilçe sentetikte on tohumun en yükseği; EMSR gevşekte
   1 817,2 dk'ya karşı ortalama 1 278,9 dk (%42 fazla); 8 ilçe sentetikte 1 522,6'ya karşı
   1 348,5 dk. Makale tek koşu yerine ortalama ± ss (ve GA) vermeli; J-28'in tek tohum
   tablosu en fazla "örnek koşu" olarak kalabilir.
2. **Kazancın %95 GA'sı sıfırı içermiyor** — sentetik (v2 ve drone) ve EMSR648 (üç kural,
   v2 ve drone) için. **İki model koşusunda GA sıfırı içeriyor**: model kapanmalarıyla kazanç
   gösterilemiyor (J-25, J-26; ayrıca J-30).
3. **U-dönüşü payı her yapılandırmada %96–100.** Yalnız gerçek yol farkı: 8 ilçe sentetik
   54,5 ± 15,2 dk (klasik ekip %27 daha uzun yol), EMSR gevşek 50,9 ± 31,1 dk (%33). t_u
   duyarlılığı aynı koşulardan: 8 ilçe için t_u = 0 / 5 / 10 / 20 / 30 dk → 54,5 / 378,0 /
   701,5 / 1 348,5 / 1 995,5 dk (tablo `multi_seed_tablo.md`'de).
4. **Kazanç birkaç görevde ve tek bölgede toplanıyor.** EMSR orta/gevşekte görevlerin
   %57–60'ı hiç kapanmaya çarpmıyor (medyan görev kazancı 0 dk, üst çeyrek 142,3 dk);
   keşiflerin **%89'u K-Z1'de** (Maraş merkez, 614'ün 545'i); en çok keşifli %10 görev
   keşiflerin %59'unu üretiyor; **tek görevde 38 keşif** (KMS-01, tohum 46: 760 dk = 12,7
   saat ceza). Sentetikte de K-Z1 baskın (647'nin 400'ü; görev başına en çok 16). R0 ajanı
   her kapalı kenarı tek tek öğreniyor; yoğun hasar kümesinde bu gerçekçi değil →
   **R1/R2 (M-25) olmadan toplam kazanç abartılı** okunmalı.
5. **Gerçek hasarda değişkenlik ~3 kat.** EMSR gevşekte kazancın ss'si 597 dk, sentetikte
   209 dk: gerçek hasar kümeli; afetzede kümenin içine düşerse kazanç büyük, dışına düşerse
   sıfıra yakın. Aynı tohumda EMSR gevşek − sentetik (4 ilçe, %88 aynı yerleşim):
   **+169,6 ± 586,8 dk** — gerçek hasarla kazanç sentetikten sistematik olarak farklı değil;
   katı kuralda −1 056,5 ± 195,3 dk.
6. **Görev düzeyi anlamlılık testi yapı gereği anlamlı.** Klasik ajan yalnız açık kenarda
   yürüdüğü için (`simulate_naive_agent`) yolu kapanmaları bilen en kısa yoldan kısa olamaz:
   986 görevin **hiçbirinde** yol farkı negatif değil. Wilcoxon p < 0,001 ve r = 1 bu yüzden
   bilgi taşımaz — makalede kazancın kanıtı olarak **sunulmamalı** (E-03'ün istatistik
   karşılığı). Anlamlı ölçüler büyüklük (ortalama ± ss, GA) ve sıklıktır: kapanmaya çarpan
   görev oranı sentetik %79–82, EMSR gevşek %43, orta %40, katı %6.
7. **Rastgele kapanma bazen afetzedeyi ağdan koparıyor:** 8 ilçede 17,8 / 18, drone
   sentetikte 8,7 / 9 rota (yerleşim 12 denemede ulaşılabilir nokta bulamayınca son adayla
   sürüyor, `_sample_reachable_point`). Model z19 / r_h = 15: 10 tohumda da 2,1 / 9 → J-25
   çok tohumla doğrulandı.

**Yapılacak (makale).** Tablo 16–19'daki tek koşu değerleri 10 tohum ortalaması ± ss ile
değiştirilmeli; sınırlılık (b) ve (g) maddeleri güncellenmeli ("tek koşumdan güven aralığı
türetilememektedir" artık geçersiz); görev düzeyi p değeri kullanılmamalı; kazancın K-Z1'de
toplandığı ve R0'ın öğrenmeyen ajan olduğu açıkça yazılmalı.

---

## J-58 🟠 Yol kapanması kaydı: şiddet derecesi ölçülmüyor, kapalı parçanın geometrisi atılıyor
**Durum:** AÇIK · **Bulundu:** 24 Eylül 2026 (J-56 katmanı bağlanırken) · **İlgili:** J-56, J-44, J-34

`cekirdek._kapanmalari_depoya_yaz` uydu analizinin kapalı yol parçalarını depoya yazarken
iki bilgi kaybediyor:
1. **Derece sabit.** Her kayda `derece=3` yazılıyor (`cekirdek.py:632`); depodaki 39 kaydın
   hepsi 3. Alan "şiddet" gibi duruyor ama ölçülmüş bir şey değil. Bu yüzden konsol
   katmanında ve ipucunda derece **gösterilmiyor**; gösterilseydi uydurma bilgi olurdu.
2. **Geometri atılıyor.** Kapalı parçanın çizgisi yerine yalnız orta noktası saklanıyor
   (`orta = yol[len(yol) // 2]`). Harita bu yüzden kapanmayı nokta olarak çiziyor; "şu yol
   şu kadar kapalı" denemiyor. Rota motoru da noktanın 25 m çevresindeki kenarları
   cezalandırıyor, gerçek parçayı değil.

**Öneri.** Depoya parçanın iki ucunu (ya da sadeleştirilmiş çizgisini) ve modelin hasar
skorunu yazmak; derece alanını ya skordan türetmek ya da kaldırmak. Geriye dönük kayıtlar
nokta olarak kalır, yeni kayıtlar çizgi olur.

---

## J-39 🟡 Büyük alan çizilince görüntü sessizce 8 × 8 karoya kırpılıyor
**Durum:** AÇIK · **Bulundu:** 21 Eylül 2026 (kod okuması; gerçek koşuyla ölçülmedi) · **İlgili:** J-20, J-35

**Sorun.**
- `apps/road_damage/utils/fetcher.py` (`_try_fetch`): istenen kutu 64 karoyu aşarsa kutunun
  ortasındaki 8 × 8 karoya kırpıyor.
- İşçi yakınlaştırmayı kutudan değil `radiusKm`'den seçiyor (`zoom_for_radius`), kutu
  gönderilse bile.
- Örnek: konsolda "Alan çiz" ile 10 km'lik kutu ve varsayılan 2,5 km yarıçap → z15, ~10 × 10
  karo → ortadaki ~7,9 km analiz ediliyor, kenarlar hiç girmiyor. Sonuç bunu söylemiyor.
- Konsolda OAM görüntüsü seçilince alan görüntünün tüm kutusuna (40 × 30 km'lik Maxar
  şeritleri) oturuyordu; bu J-35'te kaldırıldı ama kırpmanın kendisi duruyor.

**Yapılacak.** İşçi istenen kutuyu ve fiilen analiz edilen sınırları sonuca yazsın; konsol
fark varsa söylesin. Yakınlaştırma çizilen kutunun boyundan seçilsin; bütçeyi aşan alanda
kırpmak yerine süre ya da çözünürlük uyarısı verilsin (J-20 kararıyla birlikte).

---

## J-36 🟠 Eğitilen modeller ürüne takılmaya hazır değil
**Durum:** DEVAM EDİYOR — 1, 2 ve 4 yapıldı ve ölçüldü; 3 uyarıyla sınırlı; 5 ve 6 açık · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-20, kural 1, kural 8

**Soru (kullanıcı):** eğitimden sonra modelleri verdiğimizde proje onlarla doğru çalışacak mı?
Kod okundu; bugünkü hâliyle **hayır**. Sebepler:

1. **Yükleyici tek mimariye sabit.** `apps/road_damage/utils/inference.py:39`
   `smp.Segformer(encoder_name="mit_b4", classes=1)`; dosya yolu `cekirdek.py:691`'de sabit.
   Eğitim defterinde 11 aday var (`QuakeMind_veri/araclar/defter_dokuz_model.py:397-407`);
   yalnız `segformer_mitb4` yüklenir. Öbürleri `load_state_dict`'te düşer, işçi havuzu
   kurulamaz, **bütün analizler hata verir**. İyi haber: defter düz `state_dict` kaydediyor
   (satır 584-585) ve Colab'daki sürümler (smp 0.5.0, torch 2.11) yereldekiyle aynı; bir
   SegFormer-B4 yüklenmeli (gerçek dosyayla henüz denenmedi). Ağırlık yalnız
   `AGIRLIK_SAKLA` açıksa Drive'a yazılıyor.
2. **Eşik uyuşmuyor.** Makaledeki IoU, sigmoid çıktısında 0,5 eşiğiyle ölçülüyor
   (`ESIK = 0.5`, defter satır 111). Ürün olasılığı 3,5 ile çarpıp 0,40'ta kesiyor
   (etkin eşik 0,40 / 3,5 = **0,114**) ve üstüne 2. düzey morfoloji uyguluyor. Üründeki
   çıktı ölçülen modelin çıktısı değil. Değerler dört yere dağılmış: `RoadDamageRequest`
   varsayılanları, konsol hazırları (`hasar.tsx` HAZIRLAR: 0,45 / 0,40 / 0,28; güçlendirme
   3,5 / 4,5), `make_model_masks.py` INFERENCE_PARAMS, işçi varsayılanları.
3. **Çözünürlük (J-20).** Eğitim 0,375–0,5 m/px. Ürün yakınlaştırmayı yarıçaptan seçiyor:
   konsol hazırları 1,5 / 2,5 / 4 km → z16 / z15 / z14 → 36° enlemde 1,9 / 3,9 / 7,7 m/px.
   z18 (0,48 m/px) yalnız r ≤ 0,46 km'de. Defterin kendi tanısı: MEDBFS 0,75 m'de IoU 0,086.
4. **Sonuç hangi modelden çıktığını yazmıyor.** Künyede görüntü var, model adı / sha256 /
   eşik yok (kural 1).
5. **Kıyas hattı eski modele sabit.** `make_model_masks.py` model ağırlığını SHA-256 ile
   doğruluyor (`7d7fb8d8…`); yeni model yeni iz ister.
6. **Metin sınıflandırıcı** (`apps/disaster_nlp/src/classification.py`): yeni modelin
   etiketleri `CATEGORY_MAPPING`'deki 13 adla eşleşmezse sonuç "Diğer"e düşer;
   `DISASTER_MODEL_NAME` ortam değişkeni yerel varsayılan model varken hiç okunmuyor;
   anahtar kelime kuralı `max(score, 0.50)` döndürüyor — modelin üretmediği bir güven
   değeri (kural 1). YOLO eğitilmeyecek (21 Eylül kararı); risk CatBoost'u
   `araclar_risk_egit.py` ile eğitildiği sürece takılır.

**Önerilen çözüm (model kaydı).** Her model için `kunye.json`: mimari, kodlayıcı, sınıf
sayısı, karo boyu, eğitim GSD'si, normalizasyon, doğrulamada seçilen eşik, son işlem,
sha256, eğitim deneyi / tohum, sınama ölçütleri. Yükleyici `smp.create_model` ile mimariyi
künyeden kurar, sha256'yı açılışta doğrular; eşik ve son işlem künyeden gelir, istek
yalnız açıkça ezerse değişir; yakınlaştırma eğitim GSD'sinden seçilir; sonuç model adını
ve izini yazar; kıyas hattı aynı kaydı okur. Defter `model_en_iyi.pth`'nin yanına
`kunye.json` yazar. **Teslim testi:** (1) yükleme, (2) defterin sınama karolarının bir
kısmında defterdeki IoU'nun yeniden üretilmesi (aynı ön işlemenin kanıtı), (3) bilinen bir
Maxar alanında canlı koşu.

**Yapıldı (21 Eylül).**
- **Künye ve yükleyici (madde 1).**
  - `modeller/uydu/<ad>.json` ve `apps/road_damage/utils/model_kunyesi.py`. Etkin modeli
    `QM_UYDU_MODELI` seçer; varsayılan bugünkü model. Mimari künyeden kurulur, SHA-256
    tutmazsa ağırlık yüklenmez, anahtarlar katı (strict) eşleşir.
  - Bugünkü modelin künyesi (`segformer_mitb4_dice30`) bilinmeyenleri açıkça yazıyor:
    eğitim kaydı yok, sınama ölçümü yok (A-01).
  - *Ölçüldü:*
    - Künyeden yükleme eski yükleyiciyle birebir aynı çıktıyı veriyor (en büyük fark 0).
    - Defterin 11 mimarisinin 11'i yükleniyor, 1×1×512×512 çıktı veriyor.
    - Yanlış parmak izi reddediliyor.
    - Eski yükleyici U-Net ResNet-18'i yükleyemiyor.
    - CPU'da 512² ileri geçiş: MiT-B4 1,19 sn, U-Net R18 0,29 sn.
- **Karar ayarı künyeden (madde 2).**
  - `RoadDamageRequest` eşik, güçlendirme, normalizasyon ve son işleme alanları artık
    isteğe bağlı; gönderilmezse künyeden gelir.
  - Bugünkü künye eski sabitleri taşıyor, davranış değişmedi: duman testi 57 istekte
    0 fark.
  - Defterden gelen modellerin künyesi defterin ölçtüğü ayarı taşır: eşik, güçlendirme 1,
    son işleme yok.
  - Konsol hazırları artık yalnız alanı seçiyor. Hassas tarama eşiği modelinkinin %70'ine
    indiriyor.
  - **Değişen davranış:** "Hızlı tarama" eskiden eşiği 0,45, son işlemeyi 1 yapıyordu; artık
    modelin ayarıyla (0,40 / 2) koşuyor.
  - *Ölçüldü (QQB dış sınama, 74 karo, ürünün kendi `run_inference`'ı, bugünkü model):*

    | Ayar | IoU | Kesinlik | Duyarlılık |
    |---|---|---|---|
    | Ürün ayarı 0,40 / ×3,5 / son işleme 2 | 0,208 | 0,319 | 0,372 |
    | Ham ayar 0,5 / ×1 / son işleme yok | 0,222 | 0,402 | 0,332 |
- **Çözünürlük (madde 3), yalnız uyarı.** Yakınlaştırma otomatik değiştirilmedi.
  - Sebep: 2,5 km'de z18 CPU'da saatler sürer (J-20). Ayrıca indirici 64 karoyu aşan alanı
    sessizce kırpar (J-39).
  - Bunun yerine sonuç `model.kullanilanGsdM` ve `model.gsdUyarisi` alanlarını taşıyor
    (eğitim üst sınırının 1,5 katından kaba ise uyarı). Konsol uyarıyı gösteriyor.
  - Karar kullanıcıda (J-20 seçenekleri).
- **Sonuç künyesi (madde 4).**
  - Her sonuç `model` alanını (ad, mimari, ağırlık izi, karar ayarı, eğitim çözünürlüğü,
    ölçüm) ve `postProcessLevel`'ı taşıyor.
  - Yeni uç `GET /api/road_damage/model`: konsol varsayılanları buradan alıyor.
- **Araçlar.**
  - `araclar_model_kunye.py` defter koşusundan (`sonuc.json` + `model_en_iyi.pth`) künye
    üretiyor. Yerelde gerçek koşu klasörü olmadığı için yalnız defter şemasına uyan test
    klasörüyle mekanik olarak sınandı; ölçüm değil.
  - `araclar_model_teslim.py` teslim testini koşuyor.
  - Rehber: `modeller/README.md`.
- **Açık.** Madde 5 (`make_model_masks.py` eski modele sabit) ve madde 6 (metin
  sınıflandırıcı) yapılmadı.

---

## J-34 🟠 Sürekli yumuşak maliyet ve simetrik kural — bölgeler arası görev tabanlı sınama
**Durum:** KOŞULDU (21 Eylül 2026); canlı sistemde bayrak arkasında, varsayılan değişmedi · **Açıldı:** 21 Eylül 2026 · **İlgili:** J-30, B-01, B-06, M-20

**Soru.** J-30'da modelin ikili kapanmaları sert (kenar silinir) ve kaba yumuşak (×3,
×10) kullanıldı; hiçbir ayarda tutarlı kazanç çıkmadı. İki yöntemsel fark hiç
denenmedi: (1) ikili kapanma yerine **sürekli olasılık** p(e) = kenar boyunca
örneklerin hasarlı piksele düşen oranı; (2) **simetrik kural**: yer gerçeği bir
kenarı örneklerinin %50'si hasarlı çizgiye yakınsa kapalı sayıyor, bugünkü model
kuralı ise TEK hasarlı pikselle tüm kenarı kapatıyor. J-30'daki düşük kesinliğin
(~0,10-0,18) bir kısmı bu asimetriden gelebilir.

**Ön kayıt (sonuç görülmeden, 21 Eylül 2026 — `benchmark/yumusak_maliyet_deneyi.py`):**
- Veri: EMSR648'in hasarlı yol işaretlediği 1 km'lik hücreler (Hatay AOI11 13 hücre,
  K.Maraş AOI04 20 hücre; hücre ızgarası hasar kümesine göre değil sabit ızgaraya
  göre). Maskeler z18, OpenAerialMap Maxar deprem sonrası (en erken tarihli sahne
  önce), canlı sistemle aynı SegFormer ve eşikler (`make_model_masks.py`).
- Dünya: EMSR gevşek kural, tampon 8 m, en az örtüşme 0,5 (J-30 ile aynı).
- Ajanlar: R0, R3, M-sert (p > 0; bugünkü sistem), M-simetrik (p ≥ 0,5),
  M-y(λ) maliyet = uzunluk × (1 + λp), λ ∈ {0,5; 1; 2; 4; 8; 16}.
- λ seçimi: bir ilde (ayar) ortalama görev süresini en aza indiren λ; öbür ilde
  (sınama) YALNIZ o λ raporlanır; iki yön. Tüm eğri şeffaflık için yazılır, iddia
  yalnız sınama değerine dayanır.
- Görevler: hücre × tohum (42-51) × 3; ekip hücre sınırına 150 m içinden, afetzede
  EMSR hasarlı yol çizgisine 60 m içinden; kusursuz bilgiyle ulaşılabilir olmalı.
- t_u 20 dk (5 dk duyarlılık). Ölçütler: ortalama görev süresi, R0→R3 kazancının
  yakalanan payı, keşif, "rota bulunamadı", kesim düzeyi kesinlik/duyarlılık/IoU.

**Bilinen sınırlar (şimdiden):** hücreler hasarlı yol içeren yerlerden seçildiği için
kesinlik şehir geneline göre iyimser olabilir; ağ "walk" (J-30 ile karşılaştırılabilir
olsun diye); EMSR hasar derecesi = geçilemezlik bir varsayım (J-28, M-26).

**Sonuç (21 Eylül 2026).** 33 hücre (Hatay 13, K.Maraş 20), 976 görev, 10 tohum.
Kod: `benchmark/yumusak_maliyet_deneyi.py`; maskeler `benchmark/data/model_masks_emsr/`
(33/33 hücrede görüntü kapsaması %100, hücre başına ~75 sn CPU); graf yerel PBF'ten.

*Algılama (kesim düzeyi):*

| Kural | Hatay kesinlik / duyarlılık / IoU | K.Maraş kesinlik / duyarlılık / IoU |
|---|---|---|
| M-sert (bugünkü, p > 0) | 0,159 / 0,071 / 0,052 | 0,181 / 0,085 / 0,062 |
| M-simetrik (p ≥ 0,5) | 0,189 / 0,021 / 0,019 | 0,191 / 0,028 / 0,025 |

*Görev (t_u = 20 dk, R0→R3 kazancının yakalanan payı):*

| Ajan | Hatay | K.Maraş |
|---|---|---|
| R0 / R3 süresi | 14,47 / 2,99 dk | 14,70 / 3,23 dk |
| M-sert | %4,4 (39 "rota bulunamadı") | %15,9 (26) |
| M-simetrik | %−3,5 | %−1,7 |
| M-y λ = 0,5 · 1 · 2 · 4 · 8 · 16 | %2,8 · 3,7 · 3,7 · 10,5 · 13,6 · 22,3 | %1,5 · 1,8 · 4,8 · 10,5 · 16,7 · 14,1 |

*Ön kayıtlı çapraz sınama:* λ Hatay'da seçildi (16) → K.Maraş'ta **%14,1**, hücre
düzeyi bootstrap %95 GA **[%0,8; %27,9]**. λ K.Maraş'ta seçildi (8) → Hatay'da
**%13,6**, GA **[%−0,4; %22,2]**. t_u = 5 dk: %12,9 [−0,6; 26,3] ve %12,2 [−2,2; 20,1].
Görev bazında (R0'a göre) sınama ajanı K.Maraş'ta 53 görevde iyi, 54'ünde kötü,
484'ünde eşit; Hatay'da 19 iyi, 25 kötü, 341 eşit — ortalama kazanç, pahalı geri
dönüşlerin önlendiği az sayıda görevden geliyor.

*Değerlendirme.*
1. **Simetrik kural hipotezi desteklenmedi.** Kesinliği yalnız 0,16 → 0,19'a çıkardı,
   duyarlılığı 0,07 → 0,02'ye düşürdü; görevde R0'dan kötü. Düşük kesinliğin kaynağı
   kenar kuralı değil maskenin kendisi.
2. **Sürekli yumuşak maliyet, iki yönde de pozitif sınama değeri veren ilk
   varyant** (~%13-14) ve ağı hiç koparmıyor (sert kurallarda 26-39 "rota
   bulunamadı"). Ancak güven aralıkları geniş: bir yönde alt sınır sıfırın hemen
   üstünde (%0,8), öbür yönde sıfırı içeriyor. **Anlamlı kazanç iddia edilemez;
   yönü tutarlı bir işaret olarak raporlanmalı.**
3. Hatay'da en iyi λ ızgaranın sınırında (16): daha büyük λ denenmedi; denenirse ayrı
   ve yeniden ön kayıtlı bir koşu olmalı (sonuca bakıp ızgara genişletmek çatallı yol).
4. Darboğaz J-30'daki gibi algılama kalitesi (IoU 0,05-0,06).

**Ürün için karar (kullanıcıda):** canlı sistemde kapanmaları sert silmek yerine
yumuşak maliyet kullanmak kazanç açısından belirsiz ama **sağlamlık açısından**
avantajlı (yanlış alarmlar hedefi ağdan koparamaz). Varsayılan sessizce
değiştirilmez; bayrak arkasında eklenmesi önerilir.

**Güven aralıklarının kaynağı.** `benchmark/yumusak_maliyet_ga.py` (hücre düzeyi
bootstrap, 2 000 örnek, tohum 7; girdi `runs/yumusak_maliyet/satirlar.json`). Yukarıdaki
dört aralık ve görev sayıları bu betikle yeniden üretildi, birebir aynı. Aynı betiğe göre
bugünkü kural (M-sert) K.Maraş'ta %15,9 [0,8; 30,9], Hatay'da %4,4 [−10,6; 24,2]:
yumuşak maliyetin sert kurala üstünlüğü de gösterilmiş değil.

**Canlı sistemde bayrak (21 Eylül 2026, kullanıcı: "bayrak arkasında ekle").**

- `POST /api/road_damage/route` iki isteğe bağlı alan aldı: `costModel`
  (`"hard"` varsayılan = bugünkü kural, `"soft"`) ve `softLambda` (varsayılan 8,
  0–64). λ = 8, K.Maraş'ta seçilip Hatay'da sınanan değer; Hatay'da seçilen 16 ızgaranın
  kenarına dayandığı için daha az güvenilir sayıldı. Yumuşak yanıt ek olarak
  `closureExposureMeters` (rotadaki Σ uzunluk × p) ve `riskyEdgeCount` döner. Sert
  yanıt birebir eski biçimde.
- p, işçide **genişletilmemiş** model maskesinden hesaplanır (deneydeki tanım, r_h'den
  bağımsız); oturumda yalnız p > 0 kenarlar tutulur. Konsol bu ucu henüz çağırmıyor.
- `/analyze` oturumu artık tam grafı ve kapalı kenar kümesini tutuyor; sert rota grafın
  kopyası yerine `restricted_view` üzerinde koşuyor (bellek aynı: bir graf). Anahtarlar
  bilerek `G`/`closedEdgeKeys` değil — o ikisi `/naive_compare` ve `/reference_compare`'in
  "yer gerçeği olan oturum" işareti.
- **Eşdeğerlik ölçüldü:** 33 EMSR hücresinde, modelin gerçek maskesinden çıkan
  kapanmalarla (734 kapalı kenar), hücre başına 50 rastgele çift: kopya ile görünümde
  A* rotaları **1 650 / 1 650 birebir aynı**.
- `edge_closure_probability` vektörleştirildi: döngülü sürümle 33 hücre × (geçerli maske
  var / yok) **66 / 66** ve 31 596 kenarlı 5 × 5 km grafta **2 / 2** karşılaştırmada
  birebir aynı; o grafta 5,9 sn → 0,78 sn. J-34 sonuçları bu değişiklikten etkilenmez.
- **Varsayılan değişmedi:** uç duman testi 57 istekte `testler/uc_imzalari.json` ile
  **0 fark**.
- *Uçtan uca (Antakya, OAM Maxar `10300100E18CB600` 2023-02-11, r = 0,35 km, z18):*
  analiz 154 sn (çıkarım 92,9 sn), `damageRate` 0,0126 (J-19'daki ölçümle aynı),
  396 açık / 11 kapalı parça, p > 0 olan 13 kenar, olasılık hesabı 0,0 sn. 20 rastgele
  çift: 14'ünde üç ayar da (sert, λ = 8, λ = 0) aynı mesafe; 1'inde yumuşak rota kısa (465,7 → 346,0 m, 1 riskli
  kenar, 5,5 m beklenen kapalı metre); 1'inde λ = 8 sert kuralın dolambacını korudu
  (846,5 m), λ = 0 riskli kenardan geçti (658,1 m, 26,6 m); 4'ünde iki modda da yol yok —
  sebebi kapanma değil ağ (bkz. J-37). Yanıtta graf nesnesi sızmadı.

---

## J-32 🟠 Analiz sonucu ucu 17,6 MB dönüyor; 16 MB'ı tanı görseli
**Durum:** KISMEN KAPALI · **Bulundu:** 20 Eylül 2026

**Ölçüm.** `GET /api/road_damage/status/{id}` biten bir analiz için (Antakya, 1 km
yarıçap) **17,59 MB** JSON döndürüyor. Dağılım: `imageOriginalB64` 5,5 MB ·
`imageSegmentationOverlayB64` 5,5 MB · `imageDamageOverlayB64` 5,3 MB ·
`imageRoadMaskB64` 117 KB · `safeRoadSegments` 1,69 MB · `blockedRoadSegments`
12 KB · geri kalan bütün sayılar ve künye toplam ~1 KB.

**Neden sorun.** Eski web bu ucu yoklamayla çağırıyor ve her çağrıda tam gövde
iniyor; sonucu yalnız sayı olarak gösteren bir istemci de 17 MB indirmek zorunda
kalıyor. Büyük veriyi JSON ile taşımak MIMARI §8'de zaten kırılma noktası olarak
yazılı: asıl maliyet ayrıştırma.

**Yapılan (20 Eyl).** Uca `?gorseller=0&segmentler=0` seçeneği eklendi; varsayılan
davranış değişmedi (eski web etkilenmiyor). Yeni konsol özeti bu seçenekle ~1 KB
olarak çekiyor, yol geometrisini ise zaten var olan ve ETag ile önbelleklenen
`GET /api/road_damage/segments/{id}` ucundan alıyor.

**Yapılan (21 Eyl).** Görseller artık JSON'da değil diskte: iş bitince
`veri/analiz_gorselleri/{isId}/{ad}.png` olarak yazılıyor, `GET
/api/road_damage/gorsel/{isId}/{ad}` ile tek tek ve önbelleklenebilir şekilde
alınıyor. Bellekteki iş deposu görsel tutmuyor (20 iş × ~16 MB tavanı kalktı).
Eski web base64 beklediği için `gorseller=1` (varsayılan) çağrısında dosyadan
okunup kodlanıyor — davranışı değişmedi.

**Kalan.** (1) Görseller PNG; WebP'ye çevrilirse dosya boyutu düşer (tek görsel
bugün ~10 MB).
(2) `safeRoadSegments` 1,69 MB JSON: MIMARI §8'deki eşiğe göre ikili ya da vektör
karo olmalı. (3) Eski web yoklamayı bırakıp SSE'ye geçtiğinde bu uç tamamen
sayı-özeti hâline gelebilir.

---

## J-31 🔴 Ara referanslar R1/R2 (Tablo 16, M-25): güçlü referanslara karşı kazancın %55–90'ı kalıyor
**Durum:** AÇIK — sonuçlar makaleye işlenmeli · **Bulundu:** 16 Eylül 2026 · **İlgili:** M-25, E-02, J-29, J-30

**Tasarım.** `simulate_reference_fleet` (`network.py`; zaman sıralı, R0/R1/R2 tek fonksiyonda),
`POST /api/road_damage/reference_compare` (aynı oturum, aynı kapanma kümesi, aynı atamalar),
`full_scenario.py --references` (varsayılan kapalı — canlı gösterim betikleri değişmedi),
`multi_seed.py run --references --out multi_seed_refs --compare-with multi_seed`.
- **R0:** Algoritma 1, değişmedi.
- **R1:** her kavşakta planlı yolun önündeki 100 m'yi görür (yol boyunca ölçülür; köşe
  dönüşleri görüşü kesmez — R1 için iyimser); aynı kavşaktaki gözlemler **tek** t_u.
- **R2:** bölge içi filo aynı anda yola çıkar; bir ekibin öğrendiği kapanma o anda telsizle
  herkese yayılır; telsizle öğrenilen kapanma **cezasız** yeniden planlanır, kendi keşfi R0 gibi
  cezalı. Aynı karargâhtan çıkan kafilede öndeki keşfeder, arkadakiler cezasız yön değiştirir
  ("anında yayılır"). **R2e** (duyarlılık): kafile kuralı yok, aynı anda varan her ekip kendisi
  keşfeder. **R1+R2**: ikisi birlikte (makalede tanımlı değil, ek).
- **Doğrulama:** yeni simülatörün R0 modu **986/986** görevde naive_compare ile birebir;
  QuakeMind/R0 toplamları ve afetzede yerleşimleri J-29 taramasıyla **90/90** koşuda aynı;
  ağırlık fonksiyonlu yol bulucu, görünümlü olanla bütün varyantlarda birebir (~5× hızlı).
  90 koşu, 62 dk, hatasız. Kafile kuralı eklenmeden önceki yarım tarama:
  `runs/_superseded/2026-09-16-r2-kafile-kurali-oncesi/`.

**Tablo 16 (t_u = 20 dk, 10 tohum, ortalama ± ss; fark = referans − QuakeMind; kazanç % = fark / referans):**

| Yaklaşım | 8 ilçe sentetik: toplam (dk) | fark | kazanç | EMSR648 gevşek, 4 ilçe: toplam (dk) | fark | kazanç |
|---|---|---|---|---|---|---|
| QuakeMind (kusursuz bilgi, R3) | 203,5 ± 18,9 | — | — | 154,1 ± 23,3 | — | — |
| R0 — naif (t_u = 20) | 1 552,0 ± 252,0 | 1 348,5 | %86,7 | 1 433,0 ± 607,8 | 1 278,9 | %86,8 |
| R0 — yalnız yol (t_u = 0) | 258,0 | 54,5 | %21 | 205,0 | 50,9 | %23 |
| **R1 — görüş mesafeli** | 1 357,1 ± 185,2 | 1 153,7 | %84,9 | 942,4 ± 340,5 | 788,2 | %81,6 |
| **R2 — bilgi paylaşan filo** | 1 409,5 ± 251,0 | 1 206,0 | %85,3 | 1 062,6 ± 297,5 | 908,5 | %84,1 |
| R1 + R2 (ek) | 1 264,1 ± 203,2 | 1 060,7 | %83,7 | 763,8 ± 175,0 | 609,7 | %78,7 |

R0'a karşı ölçülen kazancın referansa karşı **kalan payı**: R1 %86 / %64, R2 %90 / %77,
R1+R2 %80 / %55 (8 ilçe / EMSR). Yalnız yol farkı (t_u'dan bağımsız, t_u = 0 simülasyonu):
R1 33,7 / 34,2 dk, R2 52,8 / 45,4 dk, R1+R2 32,6 / 32,9 dk (%14 / %17). Diğer yapılandırmalar,
t_u taraması ve R2e: `runs/multi_seed_refs/multi_seed_tablo.md`.

**Bulgular.**
1. **Kazanç güçlü referanslara karşı da büyük** (t_u = 20'de %78–85) — "R0 samandan adam"
   eleştirisine cevap. Ama bu büyüklük hâlâ t_u'dan geliyor: en güçlü referansa (R1+R2) karşı
   yalnız yol farkı 8 ilçede 32,6 dk (%14), EMSR'de 32,9 dk (%17).
2. **Gerçek hasarda erime daha büyük:** sentetikte R1+R2'ye karşı kazancın %80'i kalıyor,
   EMSR'de %55'i. Gerçek hasar kümeli olduğu için görüş ve telsiz orada çok daha etkili.
3. **R1'in avantajının bir kısmı sayım kuralından:** R0 aynı kavşaktaki ardışık keşifleri ayrı
   ayrı cezalandırıyor (Algoritma 1). EMSR gevşekte R0 − R1 = 490,6 dk'nın **272,0 dk**'sı bu
   sayımdan, **218,6 dk**'sı görüşten; sentetikte 20,0 + 174,8 dk. R0'ı durak başına sayan satır
   tabloda ayrıca var.
4. **Bilgi paylaşımı her zaman kısaltmıyor:** bilinmeyen yolu açık sayan ekip, telsizle erken
   yön değiştirip daha kötü bir koridora sapabiliyor. R2 sentetikte 10 tohumun 1'inde, EMSR
   katı kuralda 1'inde R0'dan yavaş; EMSR orta/gevşekte hiç. Ortalama R2 − R0: sentetik
   −142,5 ± 149,0, EMSR gevşek −370,4 ± 364,7, katı +2,1 ± 6,7 dk. R1 hiçbir tohumda R0'dan
   yavaş değil.
5. **Kafile kuralı önemli:** kuralsız (R2e) sentetikte R2'nin R0'a karşı kazancının yarısı
   kayboluyor (−77,4'e karşı −142,5 dk); drone sahnelerinde R2e neredeyse R0'ın aynısı
   (EMSR'de 10/10, sentetikte 9/10 tohumda eşit — aynı karargâhtan çıkan ekipler hep birlikte
   keşfediyor). v2 EMSR koşularında R2 ile R2e arasında fark yok.
6. **Drone sahneleri:** EMSR'li K-D1'de paylaşım belirleyici (R0 58,7 → R2 36,7 dk, kalan pay
   %47); model koşularında referanslar R0'dan farksız (J-30: bu koşular modelin hatasını
   zaten ölçmüyor).

**Yapılacak (makale).** Tablo 16'nın R1/R2 satırları (isteğe bağlı R1+R2) 10 tohum
ortalamasıyla doldurulmalı; Bölüm 3.8'deki R1/R2 tanımlarına uygulama kararları eklenmeli
(yol boyunca 100 m görüş, durak başına ceza, kafile kuralı, telsizle öğrenilen kapanmanın
cezasız olması); sınırlılık (b)'deki "R1 ve R2 koşulmamıştır" cümlesi kaldırılmalı; bulgu 3
(sayım kuralı) ve 4 (paylaşım paradoksu) açıkça yazılmalı.

---

## J-28 🔴 Eşleştirilmiş deney: kapanma kaynağına göre sistem kazancı (sentetik / EMSR648 / model)
**Durum:** AÇIK — sonuçlar makaleye işlenmeli; tek tohum, **10 tohumlu sürümü J-29'da** · **Bulundu:** 16 Eylül 2026 · **İlgili:** E-01, E-02, M-20, M-26, J-29

**Tasarım.** Aynı afetzede, ekip, karargâh, rota motoru, atama, BERTurk, YOLOv8
ve naif ajan; değişen **yalnız hangi yolların kapalı olduğu**. Tohum 42.
Karşılaştırma `benchmark/compare_closure_sources.py` ile **aynı küme** (naif
ajanın da ulaşabildiği atamalar) üzerinden yapılır ve kazanç iki bileşene
ayrılır: gerçek yol farkı + U-dönüşü ceza varsayımı (E-02). Koşular:
`benchmark/runs/{v2-*, drone-*}`, tablo `runs/closure_source_comparison.json`.

**Senaryo v2 — EMSR kapsamındaki 4 ilçe (H-Z1, H-Z3, K-Z1, K-Z2; 13 afetzede):**

| Kapanma kaynağı | Rotalanan | QuakeMind | Klasik | Kazanç | yol farkı | U-dönüşü | U-dönüşü payı |
|---|---|---|---|---|---|---|---|
| Sentetik (%18 istenen) | 13/13 | 180,3 dk | 1 600,3 dk | 1 420,0 | 60,0 | 1 360,0 | %96 |
| **EMSR648 katı** (Destroyed) | 13/13 | 177,6 | 238,0 | 60,4 | 0,4 | 60,0 | %99 |
| **EMSR648 orta** (+ Damaged) | 13/13 | 189,1 | 1 924,7 | 1 735,6 | 75,6 | 1 660,0 | %96 |
| **EMSR648 gevşek** (+ Possibly) | 13/13 | 189,5 | 2 006,7 | **1 817,2** | **77,2** | 1 740,0 | %96 |

**Senaryo v2 — 8 ilçe, sentetik (yeni taban, Göksun çıkarılmış):**
QuakeMind 222,2 dk · Klasik 1 744,8 dk · kazanç 1 522,6 dk (yol 62,6 + U-dönüşü 1 460,0).
Hatay yarısı referansla **birebir aynı** (98,5 / 650,0 dk). Makaledeki 206,6 /
1 641,0 dk bu değerlerle değişmeli (Maraş'taki değişiklik Göksun'un
çıkarılmasından ve HQ-K1'in taşınmasından).

**Drone sahneleri (H-D1, H-D2, K-D1; 9 afetzede):**

| Kapanma kaynağı | Rotalanan | QuakeMind | Klasik | Kazanç |
|---|---|---|---|---|
| Sentetik | 9/9 | 20,4 | 161,8 | 141,4 (U-dönüşü %99) |
| EMSR648 gevşek | 9/9 | 20,7 | 60,9 | 40,2 (U-dönüşü %100) |
| Model z=18, r_h=0 (uygulama kuralı) | 9/9 | 19,5 | 19,5 | 0 |
| Model z=19, r_h=15 | **1/9** | — | — | ağ parçalanıyor (J-25) |

**Yorum.**
1. **Gerçek hasarla (EMSR648) sistem kazancı var ve sentetiğe benzer büyüklükte**
   (gevşek/orta kurallarda sentetikten de büyük — gerçek hasar Maraş merkezinin
   ana eksenlerinde toplanmış). Bu, makalenin sistem iddiasını gerçek veriye
   dayandırmayı mümkün kılıyor.
2. **Ama kazancın %96–100'ü U-dönüşü ceza varsayımından geliyor** (keşif başına
   20 dk). Yalnız gerçek yol farkından gelen kazanç 4 ilçede **77,2 dk**.
   Makale iki bileşeni ayrı raporlamalı; t_u duyarlılığı (Tablo 17) bu yüzden kritik.
3. **Geçilebilirlik kuralı sonucu belirliyor** (M-26 / Tablo 19): katı kuralda
   kazanç 60 dk, orta/gevşekte ~1 700–1 800 dk. EMSR "Damaged" dereceli yolun
   gerçekten kapalı olup olmadığı bir varsayım; makalede açıkça yazılmalı.
4. **Model koşulu darboğazı gösteriyor:** SegFormer'ın bugünkü kapanmaları ya
   rotaları hiç etkilemiyor (uygulama kuralı) ya da ağı kilitliyor (yarıçap
   kuralı). Algılama katmanı iyileşmeden model tabanlı kapanmayla kazanç iddia
   edilemez (J-25, J-26).

**Dürüst kayıtlar.** Tek tohum; 13 + 9 afetzede (E-06). Drone sahnelerinde
afetzedeler arası 700 m ayrım sağlanamıyor. EMSR AOI dışındaki ~%6 kenar açık
kabul edildi. `--zones` süzgeci rastgele sayı dizisini değiştirdiği için 4 ilçe
koşularının bölge sonuçları 8 ilçe koşusunun aynı bölgeleriyle birebir
karşılaştırılmamalı (4 ilçe koşuları kendi aralarında eşleştirilmiş).

---

## J-25 🔴 Model kapanmaları drone sahnelerinde yol ağını kilitliyor
**Durum:** AÇIK · **Bulundu:** 16 Eylül 2026 · **İlgili:** J-22, J-26

**Bağlam.** Kullanıcının modeli uygulamada test ettiği üç Help.NGO drone sahnesi
(9 Şubat 2023, 3,4–3,9 cm/px) için ayrı bir senaryo kuruldu
(`benchmark/scenario_dataset_drone.py`: H-D1 Defne–Elektrik Mah., H-D2 Defne–
Turunçlu/Akdeniz/Armutlu, K-D1 Maraş–12 Şubat Stadyumu; 9 afetzede / 9 ekip /
3 karargâh). Yol grafikleri H-Z1 ve K-Z1'in önbellekteki 3 km yaya grafiğinin
sahne kutusuna kırpılmış hâli (`benchmark/warm_drone_scene_cache.py`) —
Overpass'a gidilmiyor.

**Ölçüm** (`runs/drone-model-z19-r15-*`, tohum 42, z=19, r_h=15):

| Sahne | Kapalı kenar | Görülen kenar | Rotalanan atama |
|---|---|---|---|
| H-D1 | 98 / 382 (%25,7) | %69 | **0 / 3** |
| H-D2 | 80 / 442 (%18,1) | %71 | **0 / 3** |
| K-D1 | 118 / 394 (%29,9) | %87 | **1 / 3** |

Olay günlüğü: 9 afetzedenin 8'i için `victim_point_unreachable` (12 deneme) —
karargâhın giriş yolu kesiliyor, karargâhtan ulaşılabilir nokta kalmıyor.
Aynı tohumla **sentetik** (%18) koşuda (`runs/drone-sentetik-r018-*`) 9/9 atama
rotalanıyor (Hatay 12,0 / 153,3 dk; Maraş 8,2 / 8,2 dk).

EMSR648'e göre gerçek yol hasarı: H-D1 %0, H-D2 %0, K-D1 %30. Model Antakya
sahnelerinde hiç hasar yokken yolların beşte birini kapatıyor; K-D1'de oran
tutuyor ama çoğunlukla **farklı** yolları kapatıyor (J-26).

**Sonuç.** Altyapı gerçek yerde, gerçek görüntüyle uçtan uca çalışıyor; fakat
modelin bugünkü kapanma tahminleri küçük mahalle ağlarını parçalıyor ve
simülasyon anlamlı rota verisi üretemiyor. Bu bir **model kalitesi** sorunu.

---

## J-26 🔴 Model–EMSR648 doğrulaması: yüksek zoom daha çok hasar buluyor ama daha çok uyduruyor
**Durum:** AÇIK · **Bulundu:** 16 Eylül 2026 · **İlgili:** M-20 (Tablo 18), J-22, A-01

**Yöntem.** `benchmark/validate_model_masks.py`. Bina düzeyi: EMSR648 binası
görülen alandaysa, poligon içinde (Hatay, `builtUpA`) ya da noktanın 10 m
çevresinde (Maraş, `builtUpP`) hasar pikseli varsa "model hasarlı dedi".
Yol düzeyi: EMSR yol çizgisi ~2 m arayla örneklenir; r_h ile genişletilmiş
maskeye düşen nokta varsa "model kapalı dedi" — canlı sistemle aynı kural,
EMSR'in kendi geometrisine uygulanmış. Hasarlı dereceler: Destroyed / Damaged /
Possibly damaged. Sonuçlar: `benchmark/data/model_masks/validation_drone.json`.

**Bina düzeyi (sahne bazında):**

| | z=18 (48 cm/px) | z=19 (24 cm/px) | z=20 (12 cm/px) |
|---|---|---|---|
| K-D1 (ağır hasar): duyarlılık / kesinlik | %3,7 / %100 | %19,5 / %100 | **%33,3 / %96** |
| H-D1 (hafif): yanlış alarm | 2 / 39 | 9 / 39 | **22 / 38** |
| H-D2 (hasarsız): yanlış alarm | 5 / 22 | 7 / 22 | **14 / 22** |

**Üç sahne toplamı (mikro):**

| | Bina F1 | Bina özgüllük | Yol en iyi dengeli doğruluk |
|---|---|---|---|
| z=18 | 8,4 | %89 | %57,0 (r_h=25) |
| z=19 | 27,6 | %75 | **%59,1 (r_h=15)** |
| z=20 | 37,8 | **%41** | %53,3 (r_h=10) |

Yol düzeyinde kesinlik tüm yapılandırmalarda **%14–20**: modelin kapattığı
yolların ~%80'i EMSR'e göre açık.

**Yorum.**
1. Zoom arttıkça model gerçek hasarı daha iyi buluyor (K-D1 bina F1: 7 → 33 → 50),
   ama hasarsız binaları da giderek daha çok hasarlı sayıyor (H-D2'de z=20'de
   22 binanın 14'ü). **En yüksek zoom en iyi sonuç değil**; yol kararı için en
   iyi denge z=19'da ve o da şansa (%50) yakın.
2. Olası sebep **alan kayması**: model KATE-CD ile (Maxar/Pléiades, 0,3–0,5 m/px)
   eğitildi; drone görüntüsünde nesneler eğitimdekinden 2–15 kat büyük.
   Göz kontrolü (K-D1 z=19 önizleme) bunu destekliyor: geniş bitişik moloz
   alanlarının çoğu kaçırılıyor, sağlam çatıların üstünde dağınık küçük
   "hasar" lekeleri var.
3. Eğilim, z=21–22'nin (Colab) daha da fazla yanlış alarm üreteceğini gösteriyor.

**Dürüst kayıtlar.** (a) Örneklem küçük: 146 bina, 152 yol, 3 sahne.
(b) EMSR648 uydu görüntüsünden (~50 cm) yorumlandı; 3 cm'lik drone görüntüsünde
modelin gördüğü bazı "yanlış alarmlar" EMSR'in göremediği moloz olabilir —
elimizdeki veriyle ayrıştırılamaz. (c) Parametreler (zoom, r_h) bu üç sahnede
seçilirse, aynı sahnelerde raporlanan başarım iyimser olur; makalede ayrı bir
test kümesi ya da bu kaydın açıkça yazılması gerekir.

**Ek ölçüm — uygulamanın her zamanki kuralı (r_h = 0), üç sahne toplamı:**

| | Yol kesinlik | Yol duyarlılık | Yol özgüllük | Dengeli doğruluk |
|---|---|---|---|---|
| z=18, r_h=0 | %14,3 | **%4,5** | **%95,4** | %50,0 |
| z=19, r_h=0 | %8,3 | %9,1 | %83,1 | %46,1 |
| z=20, r_h=0 | %13,3 | %27,3 | %70,0 | %48,6 |

Eski kural **temkinli**: sağlam yolların %95'ini açık bırakıyor (bu yüzden
uygulamada hasarsız bölgelerde "doğru" görünüyor), ama ağır hasarlı K-D1'de
EMSR'in işaretlediği 22 hasarlı yoldan **yalnız 1'ini** kapatıyor. Dengeli
doğruluk %50 — şans düzeyi. Yani ne eski ne yeni kural, bu modelle drone
görüntüsünde yol kapanmasını güvenilir biçimde tahmin etmiyor.

---

## J-20 🟠 Senaryo modele Maxar'ın sekizde bir çözünürlüğünü veriyor
**Durum:** DEVAM EDİYOR (16 Eylül 2026) · **Bulundu:** 16 Eylül 2026

**Sorun.** `tiling.py:zoom_for_radius` çıkarım maliyetini sabit tutmak için
yarıçap büyüdükçe zoom'u düşürüyor. Senaryo `radiusKm = 3.0` kullanıyor:

| Yarıçap | Zoom | Çözünürlük |
|---|---|---|
| **3,0 km (senaryo)** | z=15 | **3,86 m/piksel** |
| 1,0 km | z=16 | 1,93 m/piksel |
| 0,3 km | z=18 | 0,48 m/piksel |

Maxar Open Data doğal çözünürlüğü **0,3–0,5 m/piksel**. Senaryo, kaynaktaki
çözünürlüğün ~1/8'ini (alan olarak ~1/64) modele veriyor. 3,86 m/pikselde
çökmüş bir bina 2-3 piksel, yoldaki moloz piksel altı.

**Ölçülen etki:** aynı konum ve aynı modelde z=16 → z=18 geçişi `damageRate`'i
**25 kat** artırdı (0,0005 → 0,0126).

**Çatışma.** Çözünürlüğü artırmanın bedeli ağır: r=0,3 km'de z=18 çıkarımı
**306,8 sn** sürdü (49 yama). Alan r² ile büyüdüğü için r=3,0 km'de z=18
yaklaşık **100 kat** alan = binlerce yama demek — bu makinede (GPU yok,
bkz. J-15) bölge başına saatler eder. Dokuz bölge pratikte imkânsız.

**Seçenekler.** (a) bölge yarıçapını küçült; (b) çıkarımı Colab/GPU'ya taşı
(model eğitimi zaten orada); (c) yalnız yol çevresindeki karoları işle
(karo düzeyinde ön filtre); (d) makalede mevcut çözünürlüğü ve sonucunu
açıkça raporla.


**Uygulanan çözüm yolu (GPU yok → Colab).** `benchmark/colab/make_model_masks.py`
bölge/sahne için OpenAerialMap karolarını istenen zoom'da indirip mozaikler,
backend'in **kendi** `run_inference`'ıyla hasar maskesi üretir; model ağırlığı
SHA-256 ile doğrulanır (`7d7fb8d8…`), farklıysa durur. Çıktı:
`damage_mask.png`, `valid_mask.png` (gerçekten görülen pikseller),
`preview.jpg`, `meta.json` (sınırlar, zoom, sahneler, model izi, süreler).
`benchmark/colab/build_colab_notebook.py` bunları depodan **birebir** gömen
Colab defterini üretir; gömülü dosyaların parmak izleri Colab'da doğrulanır.
Colab kod yolu depo dışında taklit edilerek sınandı — yerel sonuçla aynı çıktı.

**Durum.** Drone sahneleri (J-25) için z=18/19/20 yerelde üretildi (CPU, yama
başına ~1,3-1,8 sn; en büyük sahne z=20'de 548 sn). z=21 ve z=22 Colab defterinde
hazır, kullanıcı çalıştıracak. **Ancak J-26'daki eğilim, daha yüksek zoom'un
sonucu iyileştirmeyeceğini gösteriyor.**

---

## J-21 🟡 Esri Wayback'te Antakya'nın deprem sonrası görüntüsü YOK
**Durum:** AÇIK · **Bulundu:** 16 Eylül 2026

**Ölçüm.** Wayback'in 196 sürümü tarandı. Antakya merkezinin z=17 karosu
(x=78701, y=51378) için:

| Sürüm | Tarih | sha1 |
|---|---|---|
| 11475 | 2023-01-11 (deprem **öncesi**) | `fa0263438072c2f8` |
| 57965 | 2023-02-23 (deprem sonrası olmalıydı) | `fa0263438072c2f8` — **birebir aynı** |
| 44873 | 2023-03-15 | farklı, ama gözle bakıldı: binalar hâlâ ayakta, deprem izi yok |

Yani "2023-02-23" sürümü bu karoyu hiç güncellememiş. Wayback sürümleri
**karo bazlıdır**; listede sürümün görünmesi o karonun yenilendiği anlamına
gelmez.

**Sonuç:** deprem sonrası görüntü için Esri Wayback kullanılamaz.
**Maxar Open Data (OpenAerialMap) kullanılmalı** — D-01'in zaten söylediği şey.
Doğrulanan sahneler: `10300100E18CB600` (2023-02-11, Antakya'yı ortalıyor),
`10300100E3D52E00` (2023-02-22), `10300100E32F7A00` (2023-03-05). Gözle
doğrulandı: aynı karo, çökmüş binalar, moloz yığınları, yola birikmiş araçlar.
`/analyze` bunları `oamTileUrl` ile sorunsuz kullanıyor
(`satelliteSource: "OpenAerialMap (Event Specific)"`).

---

## J-10 🟡 Soğuk başlangıç dakikalar sürüyor
**Durum:** KISMEN KAPALI (15 Eylül 2026)

**Ölçüm.** `import networkx + osmnx` = **31,0 s**; `disaster_nlp` zincirinin
(`torch` + `transformers` + `zeyrek`) import'u = **60,8 s**. Buna SegFormer
yüklemesi, CatBoost'un ilk istekte senkron eğitilmesi (`OPTIMIZASYON_ANALIZI.md`
madde 5 ve 15) ve Windows'ta ProcessPool worker doğuşu (~10–15 s) ekleniyor.

**Yapılacak.** Ağır import'ları gerçekten tembel yap (modül üstü değil fonksiyon
içi), CatBoost modelini diske persist et, ölçülen açılış süresini makalenin
donanım künyesine yaz (B-09).

**Kismen kapandi.** J-04 kapsaminda Zeyrek tembel hale getirildi:
`disaster_nlp` import suresi **60,8 sn -> 20,6 sn**. Geri kalan maddeler
(osmnx import'unun 31 sn'si, CatBoost'un diske persist edilmemesi, Windows
ProcessPool worker dogusu) hala acik.

---

## J-15 🟠 torch iş parçacığı aşırı-aboneliği — hiçbir yerde sınırlanmamış
**Durum:** KISMEN (18 Kasım 2026, temizlik) — işçiler sınırlı, sunucu sürecindeki kamera çıkarımı sınırsız · **Bulundu:** 15 Eylül 2026

**Sorun.** Kod tabanında `torch.set_num_threads`, `OMP_NUM_THREADS` veya
`MKL_NUM_THREADS` **hiç geçmiyor**. torch varsayılan olarak fiziksel çekirdek
sayısı kadar intra-op iş parçacığı açıyor.

**Ölçüm.** Makine: 14 fiziksel / 20 mantıksal çekirdek. `torch.get_num_threads()
= 14`, interop = 14. `import torch` tek başına **+22 iş parçacığı**, ilk matris
çarpımı **+13 daha** — yani 39 iş parçacığının 35'i torch'un. Ayakta duran
sunucuda ölçülen 49 iş parçacığının büyük çoğunluğu budur.

İki torch süreci (sunucu + havuz işçisi) aynı anda çalıştığında 2 × 14 = 28
hesap iş parçacığı 14 fiziksel çekirdeği paylaşmaya çalışıyor. YOLO çıkarımı
(`/api/camera/analyze`, sunucu sürecinde) ile SegFormer çıkarımı (işçi süreçte)
çakıştığında bu aşırı-abonelik ikisini de yavaşlatır.

**Yapılacak.** İşçi sürecine çıkarım için makul bir pay (ör. 8), sunucu sürecine
küçük bir pay (ör. 2–4) ver. J-14 uygulanırsa sunucudaki torch yükü zaten
YOLO'ya iner ve bu ayarlama daha da kolaylaşır.

**Not.** Bu bir **doğrulanmamış varsayım değil, ölçülmüş bir yapılandırma
eksikliği** — ancak kazancın ne kadar olacağı ölçülmedi; çakışan çıkarım
senaryosu henüz koşulmadı.

**Temizlik (18 Kasım 2026).** Uydu işçisi (`apps/road_damage/worker.py`) ve metin işçisi (`metin_analizi/isci.py`, `QUAKEMIND_METIN_IS_PARCACIGI`, varsayılan 2) `torch.set_num_threads` ile sınırlı `[K]`. **Kalan:** kamera (YOLO) çıkarımı API sürecinde koşuyor ve orada sınır yok; çakışan çıkarım senaryosu ölçülmedi. J-07'nin kalan kısmı da bu.

---

## J-16 🟡 Graf pickle'ları 1,23 milyon kullanılmayan öznitelik taşıyor
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

**Sorun.** `warm_local_graph_cache.py`'nin ürettiği graflar pyrosm'un **ham OSM
etiket kümesini** olduğu gibi taşıyor: düğüm başına 9, kenar başına **30**
öznitelik. Rotalama yalnızca düğümde `x`/`y`, kenarda `length`/`geometry`/`osmid`
kullanıyor; geri kalanı (`access`, `bicycle`, `bridge`, `lit`, `maxspeed`,
`sidewalk`, `tracktype`, `changeset`, `timestamp`, `version`, `tags`, düğüm
başına ayrı bir shapely `POINT` …) hiç okunmuyor ve büyük çoğunluğu `nan`.

**Ölçüm** (18 060 düğüm / 40 950 kenar, Hatay-Antakya):
kullanılmayan öznitelik girdisi düğümlerde **126 420**, kenarlarda **1 105 650**.

| | Şimdi | Budanmış |
|---|---|---|
| Pickle boyutu | 21,3 MB | **4,5 MB** (4,8×) |
| `pickle.load` | 0,61 sn | **0,36 sn** |
| Bellekte | 135 MB | 123 MB |

**Dürüst kayıt: bu bir DİSK/AÇILIŞ kazancı, bellek kazancı değil.** Bellekte
yalnızca %9 fark var, çünkü `nan` değerleri tek bir nesneye işaret ediyor
(girdi başına 8 bayt) ve ağırlığın çoğu korunması gereken shapely
`LineString` geometrilerinde. Toplam 16 önbelleklenmiş graf 130 MB disk
tutuyor; budama bunu ~27 MB'a indirir.

**Yapılacak.** `warm_local_graph_cache.py` / `warm_scenario_v2_cache.py`
grafı yazmadan önce budasın. Mevcut `.pkl` dosyaları yeniden üretilmeli.

---

## J-65 🟠 Model drone ortofotosunda yıkıntıların yalnız en belirginlerini buluyor (duyarlılık düşük)
**Durum:** AÇIK · **Bulundu:** 25 Eylül 2026 (ölçüldü) · **Düzeltildi:** 25 Eylül 2026, ilk yazım fazla sertti — aşağıya bakın · **İlgili:** J-20, A-15

**İlk yazılan (YANLIŞ çerçeve).** "Model drone ortofotosunda hasarı görmüyor (%0,26–0,58)."
İki hata vardı: (1) oran KARE üzerinden hesaplanmıştı, oysa ortofotoda karenin **%61'i siyah**
(uçuş izi dışı) — doğru payda ile oran **%1,70**; (2) çıktıya bakılmamıştı: model yıkık yapıları
**doğru** işaretliyor, sadece azını buluyor.

**Kontrol edildi — boru hattında hata yok.** Ürünün kendi çıkarım yolu (`run_inference`, künyedeki
karar ayarıyla) etiketli QQB karolarında defterin ölçtüğünü birebir veriyor:
IoU **0,2941** · defter 0,2946 · fark −0,0006 (tolerans 0,02). Kesinlik 0,3593, duyarlılık 0,6182.

**Ölçüm — aynı ortofoto, farklı model ve karar ayarı** (Hatay/Defne — Elektrik, Help.NGO
2023-02-09, z18, 0,482 m/px, GSD uyarısı yok). Kare üzerinden:

| Model / ayar | Hasar | Blob |
|---|---|---|
| Eski ürün modeli (mitb4_dice30, kendi ayarı: eşik 0,40 · güç 3,5 · son işleme 2) | %0,55 | 5 |
| Yeni U-Net B4 (defter ayarı: eşik 0,50 · güç 1,0 · son işleme 0) | %0,58 | 3 |
| Yeni U-Net B4, eski ayarla | %0,67 | 4 |
| Yeni SegFormer-B2, eski ayarla | %0,81 | 7 |
| Yeni U-Net B4, eşik 0,20 | %0,64 | 4 |
| Yeni U-Net B4, eşik 0,10 | %0,68 | 4 |

Üç sonuç: (a) **eski model de aynı bantta** — yeni ağırlıklarda gerileme yok; (b) karar ayarı
belirleyici değil; (c) eşiği 0,10'a indirmek oranı değiştirmiyor — model çoğu molozda düşük
olasılık üretiyor, bu bir eşik sorunu değil.

**Göze bakınca.** İşaretlenen lekeler gerçekten çökmüş yapılar (kesinlik iyi görünüyor); ama
aynı karede gözle onlarca yıkık yapı daha var ve model onları kaçırıyor. Yani **duyarlılık
düşük**, yanlış alarm değil. Maxar uydu katmanında (2023-02-08, aynı z18) %0,69 ve 11 blob —
eğitim verisiyle aynı görüntü tipi olduğu için orada daha fazla yapı yakalanıyor.

**Yapılacak.** (1) Maxar ve drone katmanlarında 20–30 bina elle işaretlenip kesinlik/duyarlılık
ölçülsün — "düşük duyarlılık" sayıyla yazılsın. (2) Tatbikatın ana katmanı bu ölçüme göre
seçilsin. (3) Makalede ürünün hangi görüntü tipinde ne kadar yakaladığı açıkça yazılsın; drone
ortofotosu eğitim alanının dışında. (4) İyileştirme seçeneği: drone görüntüleriyle ince ayar —
ayrı iş, bu tatbikatın önkoşulu değil.

**Yan düzeltme (yapıldı).** `damageRate` kare üzerinden hesaplanmaya devam ediyor (eski
istemciler), sonuca `damageRateValid` (boş olmayan alana göre) ve `validPixelRatio` eklendi;
simülasyon sonucunda `hasar.hasarliPikselOraniGecerli` ve `hasar.gecerliAlanOrani`.

---

## J-67 🟡 İki venv var; ürünün hangisi olduğu belgeli değil, aralarında 6 kat hız farkı
**Durum:** AÇIK · **Bulundu:** 25 Eylül 2026

Depoda iki sanal ortam var: kök `venv` (torch 2.11.0, jwt var → API bunu kullanıyor) ve
`backend/venv` (torch 2.13.0, jwt YOK → API başlatılamaz). Aynı modelin 512×512
ileri geçişi kök venv'de 0,61 sn, backend venv'de 4,39 sn — **6 kat**. Model künyelerindeki
ölçüm notu hangi ortamda alındığını yazıyor, ama depoda hangi venv'in ürün olduğu ve
diğerinin niye durduğu yazılı değil. Yanlış venv ile alınan bir ölçüm makaleye girerse
hatalı olur.

---

## J-69 🟠 r_h (sert kapanma yarıçapı) duyarlılığı ölçüldü — araca erişimi belirleyen ayar
**Durum:** ÖLÇÜLDÜ, karar bekliyor · **Bulundu:** 25 Eylül 2026 · **İlgili:** J-19, J-64, J-68, J-26

**Neden.** Kapanma bina hasarından türetiliyor: bir yol, hasarlı noktaya r_h metreden yakınsa
kapalı sayılır. r_h = 0 iken yalnız yolun tam üstündeki hasar sayılır (uygulamanın eski kuralı)
ve sokağa dökülen moloz görünmez; büyüdükçe açık sokaklar da kapalı sayılır.

**Ölçüm.** Hatay/Defne — Elektrik, geniş katman (Maxar 2023-02-08), U-Net MiT-B4, eşik 0,5,
tohum 42; graf 4 164 düğüm / 11 491 kenar / **831,6 km**; 5 gerçek ekip üssü × 5 senaryo
afetzedesi = 25 çift. Çıkarım bir kez koştu, dört yarıçap aynı maske ve aynı graf üzerinde
denendi. Betik `backend/benchmark/rh_duyarlilik.py`, kayıt
`benchmark/reports/rh_duyarlilik_hatay_elektrik.json`.

| r_h | Kapanan kenar | Kapanan yol | Yolun payı | Tam araç rotası kalan çift | Ort. uzama (o çiftlerde) | Araç giremeyen çift | Ort. yürüme |
|---|---|---|---|---|---|---|---|
| 0 m | 29 | 2 217 m | %0,27 | **20/25** | 23,2 m (%1,5) | 5/25 | 17,1 m |
| 10 m | 72 | 4 740 m | %0,57 | **5/25** | 44,9 m (%1,4) | 20/25 | 47,1 m |
| 15 m | 104 | 7 277 m | %0,87 | **0/25** | — | 25/25 | 47,6 m |
| 25 m | 148 | 11 674 m | %1,40 | **0/25** | — | 25/25 | 55,0 m |

**Bulgu — beklediğimiz gibi değil.** r_h "rotayı ne kadar uzatıyor" sorusunu değil, **"araç
hedefe girebiliyor mu"** sorusunu belirliyor. Tam araç rotası kalan çift 20 → 5 → 0 → 0. r_h ≥ 15 m
olduğunda hiçbir afetzedeye araçla ulaşılamıyor; uzama ortalaması tanımsız hâle geliyor. Buna
karşılık yürüme mesafesi küçük kalıyor (17 → 55 m): araç her hâlükârda ~55 m yakınına kadar
gidiyor. Hiçbir ayarda tamamen ulaşılamayan çift yok.

**Uyarı (kendi kurgumuzdan gelen yanlılık).** Afetzedeler modelin hasarlı bulduğu blobların
üzerinde seçiliyor, yani tanım gereği molozun içindeler. Yarıçap büyüdükçe tam etraflarındaki
yollar kapanıyor — "araç giremiyor" sonucunun bir kısmı bu seçimden geliyor. Gerçek çağrı
konumlarıyla (bina girişleri, sokak adresleri) sonuç farklı çıkabilir.

**Ölçüm hatası düzeltildi (aynı gün).** İlk tabloda uzama ortalaması, yürüme yedeği devreye
giren çiftleri de içeriyordu; oralarda `kapanmaliM` hedefe değil aracın gidebildiği en yakın
noktaya olan KISMİ mesafe. Bu yüzden r_h = 0'da %8,7, r_h = 10'da %3,4 gibi ters bir eğilim
çıkmıştı. Uzama artık yalnız **tam araç rotası olan** çiftlerden hesaplanıyor
(`olcum.uzamaHesabindakiCift` kaç çift olduğunu yazar). İlk yayımlanan "%0,6 → %24,2, 40 kat"
tablosu geçersizdir.

**Karar ve açık iş.** Bu ölçüm duyarlılığı gösterir, doğruyu değil: hangi r_h'nin gerçeğe yakın
olduğunu söylemek için "bu sokaklar gerçekten kapalıydı" diyen bir yer gerçeği gerekir; bu alanda
yok. Tek aday **EMSR648** (makaledeki gerçek koşuda dünya olarak zaten kullanılıyor) — r_h orada
kalibre edilip buraya taşınmalı. **Varsayılan düzeltildi (25 → 0 m).** Ürünün kuralı zaten r_h = 0: `worker.py`'de
`blockageRadiusM` varsayılanı 0 ve yarıçap kuralı yalnız açıkça istenince devreye giriyor (J-26).
Simülasyon modülü isteğe 25 yazarak bu varsayılanı sessizce değiştiriyordu — tam olarak J-19'un
yasakladığı şey. Tatbikat artık ürünün kuralıyla koşar; yarıçap farkı kıyas kutusunda görünür. Makaleye tek değer değil
bu tablo konmalı. Ölçüm tek alan, tek model, tek tohum.

**Arayüz.** Kıyas kutusu eklendi: istekte `karsilastirYaricaplar` (varsayılan [0, 10, 25]),
sonuçta `yaricapKiyasi`. Model bir kez koşar, her yarıçap yalnız kapanma + rota hesabı ekler
(ölçüldü: yarıçap başına ~16 sn).

---

## J-70 🔴 Model kapanmaları EMSR648 yer gerçeğiyle zayıf uyuşuyor — r_h bunu kurtarmıyor
**Durum:** AÇIK · **Bulundu:** 25 Eylül 2026 (kayıtlı koşudan çıkarıldı) · **İlgili:** J-30, J-65, J-69, Tablo 18

**Soru.** r_h hangi değerde gerçeğe en yakın kapanma kümesini üretir?

**Veri.** `benchmark/runs/model_gercek_dunya/summary.json` (J-30 koşusu) her (zoom, r_h) için
modelin kapanmalarını EMSR648 Grading'den çıkarılan gerçek kapanmalarla karşılaştırıyor:
3 bölge, 609 segment, **48'i gerçekten kapalı**; kural "loose", 8 m tampon. Maskeler **eski
üretim modeliyle** (`optimized_mitb4_focal_dice30`) üretilmiş.

| zoom | r_h | Model kapalı | TP | FP | FN | Kesinlik | Duyarlılık | F1 |
|---|---|---|---|---|---|---|---|---|
| 18 | 0 | 6 | 1 | 5 | 47 | 0,167 | 0,021 | 0,037 |
| 18 | 10 | 44 | 3 | 41 | 45 | 0,068 | 0,062 | 0,065 |
| 18 | 25 | 95 | 6 | 89 | 42 | 0,063 | 0,125 | 0,084 |
| **19** | **10** | 108 | 16 | 92 | 32 | 0,148 | 0,333 | **0,205** |
| 19 | 25 | 246 | 29 | 217 | 19 | 0,118 | 0,604 | 0,197 |
| 20 | 15 | 305 | 35 | 270 | 13 | 0,115 | 0,729 | 0,198 |
| 20 | 25 | 434 | 44 | 390 | 4 | 0,101 | 0,917 | 0,183 |

**Bulgular.**
1. En iyi F1 **0,205** (z19, r_h = 10 m). Kesinlik 0,148 → modelin "kapalı" dediği her 7 yoldan
   biri gerçekten kapalı.
2. r_h bir denge düğmesi: duyarlılık 0,02 → 0,92'ye çıkıyor ama kesinlik 0,10–0,18'de çakılı.
   **Hiçbir r_h değeri sonucu kurtarmıyor.**
3. Asıl kaldıraç **zoom**: z18'de en iyi F1 0,084, z19'da 0,205 (2,4 kat). Tatbikat bugün z18
   kullanıyor. Drone sahnesinin doğal çözünürlüğü 0,034 m; z18'e indirmek bilgiyi atıyor.
4. Gerilim: z19 = 0,24 m/px, modelin eğitim aralığının (0,3–0,5 m) DIŞINDA — ama orada daha iyi.
   "Eğitim GSD'sine sadık kal" kuralı (J-20) bu veride tutmuyor.

**Kararlar.** (a) r_h arayüzden kaldırıldı — operatöre sonucu düzeltmeyen düğme sunulmaz;
`kapanmaYaricapiM` (varsayılan 0) ve `karsilastirYaricaplar` (varsayılan boş) araştırma alanı
olarak API'de kaldı. (b) Tatbikatın zoom'u yeniden değerlendirilmeli.

**Yeni modelle tekrarlandı (25 Eylül akşamı).** 9 maske yeniden üretildi
(`benchmark/data/model_masks_unet_mitb4/`, `make_model_masks.py --kunye unet_mitb4_p2_t42`);
kalibrasyon `benchmark/rh_kalibrasyon.py` ile koşuldu (betik önce ESKİ maskelerde doğrulandı:
kayıtlı J-30 tablosunu birebir üretti). Kayıtlar `benchmark/reports/rh_kalibrasyon_*.json`.

| | Eski (mitb4_dice30) | Yeni (U-Net MiT-B4) |
|---|---|---|
| En iyi F1 | **0,205** (z19, r_h 10 m) | **0,098** (z18, r_h 25 m) |
| Kesinlik / duyarlılık | 0,148 / 0,333 | 0,118 / 0,083 |
| z19 · r_h 10 m'de kapatılan kenar | 108 | 56 |

**Ama bu iki modelin değil, iki AYARIN kıyası.** Eski maskeler eşik 0,40 + güçlendirme 3,5 +
son işleme 2 ile üretilmiş (ham olasılıkta etkin eşik 0,114; morfolojik işlem lekeleri büyütüp
birleştiriyor). Yeni maskeler defterin ölçüm ayarıyla: eşik 0,50, güçlendirme yok, son işleme
yok — 4,4 kat daha katı. Kapatılan kenarın yarıya düşmesi (108 → 56) bunu gösteriyor.
**"Yeni model daha kötü" sonucu bu tablodan ÇIKARILAMAZ.**

**Açık iş.** Yeni modeli (a) eski karar ayarıyla ve (b) eşik taramasıyla yeniden koş; adil kıyas
ancak o zaman olur (~40 dk maske üretimi). Makaleye girecek sayı odur.

---

## PR #5 incelemesi — Android uygulaması (J-141…J-148)

**Kaynak:** [UtBird/QuakeMind#5](https://github.com/UtBird/QuakeMind/pull/5) (Deha, dal
`codex/quakeminds-app`, uç `c515203`). **İnceleme tarihi:** 12 Kasım 2026. Bulgular PR'a yorum olarak
yazıldı; düzeltmeyi PR sahibi yapacak. **Bu maddeler `main`'de değil, PR dalında**; PR birleşmeden
kapatılırsa birleşme sonrası yeniden denetlenmeli.

**Nasıl sınandı.** PR dalı ayrı çalışma ağacında; backend ayrı SQLite veritabanıyla (`QUAKEMIND_SQLITE`),
yerel model dosyalarıyla. `:app:assembleDebug` temiz (JDK 21, AGP 9.3, compileSdk 37). Pixel 6 /
Android 36 emülatörü, debug derlemesi `10.0.2.2:8000`. `backend/tests/test_mobile_*.py` 12/12 geçti.
Çalışanlar: misafir girişi, deprem listesi, ihbar (201), SOS (GPS ±5 m), "Yardım Gerekli" (SOS
açmıyor), harita (OSM + 83 yakın yer), risk puanı, Idempotency-Key (aynı içerik → aynı kayıt,
farklı içerik → 409).

## J-147 🟡 Mobilde kaynak etiketi ve ölçümsüz iddia eksikleri
**Durum:** KISMEN (18 Kasım 2026, temizlik) — README ve deprem kaynağı düzeltildi; harita lejantı ve marka rengi doğrulanmadı · **İlgili:** CLAUDE.md §1, §6, §8

- Ana ekran "Yakındaki depremler" kartı 2026-08-12 tarihli kaydı gösteriyor (inceleme 12 Kasım),
  kaynak (Kandilli/AFAD) yazmıyor; tanıtım ekranı "saniyeler içinde takip edin" diyor.
- Haritada lejant ve kaynak yok; kırmızı iğnelerin ne olduğu belirsiz.
- Koyu kırmızı marka rengi olarak kullanılıyor (kırmızı yalnız hasar/aciliyet için).
- `mobile/README.md`: "120 FPS", "0 per-frame allocation" kaynaksız; "aile fertlerinin pil/konum
  takibi" yazıyor ama uygulama "bu sürümde doğrulanamıyor" diyor.

**Temizlik (18 Kasım 2026).** `mobile/README.md`'de "120 FPS", "0 per-frame allocation" ve aile takibi iddiaları yok; ana ekranda deprem kaydının kaynağı yazılıyor (`HomeScreen.kt`, kaynak yoksa "Kaynak belirtilmedi"); "saniyeler içinde" metni yok `[K]`. **Kalan:** haritada lejant ve kaynak, koyu kırmızının marka rengi olarak kullanılması — bakılmadı.

## J-149 🟠 Üründeki risk modeli makaledeki risk tablosundan ayrıştı
**Durum:** AÇIK · **Kodda/ölçümde görüldü** · **İlgili:** CLAUDE.md §8, Utku `07e3bfb`

`07e3bfb` (20 Ekim, `main`'de) fay mesafesini elle yazılmış ~38 noktadan GEM Global Active Faults
çizgilerine taşıdı ve modeli yeniden eğitti. Commit iletisine göre ROC-AUC: CatBoost 0,611 → 0,606,
lojistik regresyon 0,639 → 0,642. Gönderim belgesi (`makale/QuakeMind_Makale_GONDERIM_vurgusuz.docx`)
ise lojistik regresyon için 0,6370 ± 0,0637, R0b için 0,6143 yazıyor. Bu değer iki koşudan da farklı.
Ya makale tablosu yeni koşuyla güncellenmeli, ya da makalede "üründeki model farklı fay mesafesi
yöntemiyle yeniden eğitildi" diye belirtilmeli. Word'e dokunulmadı; karar makaleyi düzelten arkadaşta.
Bu dal (`makale-simulasyon-guncel`) `07e3bfb`'yi henüz içermiyor.

## J-151 🟡 Utku'nun 81 il ekranı yerel üretim istiyor; üretim süresi ve altlık eksiği
**Durum:** KISMEN · **Ölçüldü** · **İlgili:** `07e3bfb`, PR #4

- `veri/il_merkezleri.json` depoya girmiyor (`.gitignore`). Dosya yokken risk ekranı "il merkezleri
  üretilmedi" diyor, 81 il listesi boş. `araclar_il_merkezleri_uret.py` ile üretildi: 81 il.
  **Süre:** betik başlığı "~50 sn" diyor, bu makinede (14 çekirdek, D: sürücüsündeki
  `turkey-latest.osm.pbf`) okuma **245,7 sn**, toplam 4 dk 13 sn.
- 76 il altlığı bu makinede yok; yalnız 5 operasyon bölgesi var. İl seçince "harita altlığı bu alan
  için üretilmedi" yazıyor. PR #4 (HF'ten otomatik indirme) bunu çözüyor; il merkezleri dosyası da
  aynı yolla HF'ten gelebilir.

## J-153 🟠 Deprem kataloğu kendiliğinden güncellenmiyordu; 3 ay bayattı
**Durum:** KISMEN · **Ölçüldü**

`apps/earthquake_risk/data/query.csv` içindeki en yeni kayıt 2026-08-13 idi (12 Kasım'da bakıldı).
Risk ekranındaki "Son depremler" 3 ay önceyi gösteriyordu. Otomatik tazeleme yok; yalnız elle
`/api/risk/refresh_live_data` ya da `fetch_and_update_data()` çağrılınca güncelleniyor. 12 Kasım'da
elle tazelendi: +50 Kandilli, +34 USGS (M≥4 boşluk doldurma), 20.471 satır, 6,9 sn.

Ardından risk modeli `araclar_risk_egit.py` ile yeniden eğitildi. Önceki model 20 Eylül tarihliydi,
454 kayıtlı künyeyle; sunucu "başka bir veri sürümüyle eğitilmiş" uyarısı veriyordu. Yeni model
13.709 kayıt, 33,8 sn eğitim, parmak izi `bba9a9a7e74a42c9`; uyarı kalktı.

**Dikkat.** Van'ın skoru 73,3 → 48,7 düştü. Kısa vadeli bileşen 82,0 → 20,6; fay mesafesi
11,2 → 10,9 km. Kısa vadeli model zayıf (ROC-AUC ~0,61) ve veriye çok duyarlı. Ekranda tek sayı
olarak durması yanıltıcı olabilir.

**Yapılacak.** Kataloğu bir işçi süreçte zamanlı tazeleme (istek yolunda değil, §3), ekranda "katalog
son güncelleme" tarihi.

## J-155 🟠 Saha ekibi ekranına girecek yol yoktu: rol verme ekranı yok, demo saha şifresi kayıp
**Durum:** BÜYÜK ÖLÇÜDE KAPALI (rol ekranı eklendi) · **Görüldü** · **İlgili:** CLAUDE.md §5, J-54

Kullanıcı ekip ekranına giremedi. Nedenleri:
- Kayıt ekranından açılan her hesap `afetzede` olarak açılıyor (doğru davranış, §5). `/ekip` rotası
  `saha / koordinator / yonetici` istiyor, bu yüzden hesap afetzede ekranına geri gönderiliyor.
- Rol yükseltmenin tek yolu `POST /api/oturum/rol` (yönetici) ya da `araclar_kullanici.py ekle`.
  Konsolda bunu yapacak ekran **yok**: yönetici kayıt olmuş bir gönüllüyü saha ekibine alamıyor.
- Yerel veritabanındaki `saha@quakemind.local` hesabının şifresi depoda hiçbir yerde yazılı değil,
  varsayılan şifre de tutmuyor. Hiçbir ekibe bağlı değil.

**Yapılan (12 Kasım).** `saha-demo@quakemind.local` (saha, varsayılan şifre) açıldı ve AKUT 1
(`EKP-01`) ekibine bağlandı; `DEMO_CALISTIRMA.md` §2'ye yazıldı. `/ekip` açıldı; görev kartı,
durum düğmeleri ve konum paylaşımı göründü.

**Rol ekranı eklendi (12 Kasım, aynı gün).** Konsolda yeni **Kullanıcılar** modu
(`modlar/kullanicilar.tsx`); yalnız koordinatör ve yöneticiye görünür (`modlar.ts` `roller`
alanı, sekme ve komut paletinde süzülür).
- Sunucu: `GET /api/oturum/kullanicilar` (koordinasyon; şifre özeti dönmez) ve genişletilmiş
  `POST /api/oturum/rol`. **Kural [T]:** yönetici her rolü verir; koordinatör yalnız
  afetzede ↔ saha geçişi yapar ve koordinasyon rolündeki birine dokunamaz; kimse kendi rolünü
  değiştiremez (409; son yöneticinin kendini düşürmesi de böylece kapalı). Saha dışına çıkan kişi
  ekibinden çıkar, rolü değişenin açık oturumları düşer.
- Test: `tests/test_oturum_rol.py`, 7/7 geçti. Ayrı geçici SQLite kullanıyor, gerçek veritabanına
  dokunmuyor. Venv'e `pytest` kuruldu; daha önce yoktu.
- Tarayıcıda (koordinatör): saha hesabında sekme görünmüyor; `vatandas@ornek.com` afetzede →
  saha → afetzede çevrildi, iki `POST /rol` 200, liste ve sayılar tazelendi.

**Açık.**
- Rol değişikliğinin kim tarafından ve ne zaman yapıldığı kayda geçmiyor (denetim izi yok).
- Kayıt ucu `son_giris` yazmıyor; ekran bu yüzden "son giriş" yerine kayıt tarihini gösteriyor.
- AKUT 1'in açık görevi 22 Eylül'den kalma bir deneme kaydı (51 gün önce, 178 km, not "aa").
  Tanıtımdan önce deneme kayıtları temizlenmeli ya da tohum veriyle yeniden kurulmalı.

## J-158 🟠 SQLite yeterli mi? Ham yazma bol; darboğaz tek bağlantı + olay başına tam liste
**Durum:** BÜYÜK ÖLÇÜDE KAPALI (13 Kasım 2026, iyileştirme ve yeniden ölçüm aşağıda); artımlı tazeleme AÇIK · **Ölçüldü** · **İlgili:** CLAUDE.md §8, §10; MIMARI §3

**Soru.** Çalışan sistem SQLite kullanıyor (PostGIS hedef, yazılmadı). Performans için yeterli mi?

**Ölçümden önce yazılan birim ve hedef.**
- Birim: depo katmanında işlem gecikmesi (ms; ortanca, p95, p99) ve yazma/okuma sayısı (işlem/sn).
- Yazma: `sos_ekle`. Okuma: konsolun gerçek sorguları (`sos_listele` son 6 saat, kutulu;
  `hasar_listele` kutulu; ısı/özet yolunun 100 bin sınırlı hasar okuması; `sos_sayilari`).
- Ölçek: bugün (12 SOS, 2 076 hasar), 10 bin, 100 bin, 1 milyon satır.
- Cihaz: bu dizüstü, 20 mantıksal çekirdek. Veri: gerçek veritabanının kopyası, rastgele tekdüze
  sentetik satırlar. HTTP ve JSON maliyeti hariç.
- **Hedef `[T]`** (tasarım varsayımı, saha verisi değil): büyük depremin ilk saatinde 100 bin SOS
  ≈ 28/sn; iki kat payla **50 SOS/sn sürekli yazma, yazma p95 < 50 ms**; konsol listesi
  **p95 < 100 ms**.

Betik `benchmark/sqlite_yuk_olcumu.py`, sonuç `benchmark/reports/sqlite_yuk_2026-11-13.json`.

**Sonuç `[Ö]`.**

| Satır (SOS / hasar) | Dosya | 16 eşzamanlı yazıcı | SOS listesi p95 | Hasar kutu p95 | Isı yolu (100 bin) p95 | Karışık: yazma p95 / yazma/sn |
|---|---|---|---|---|---|---|
| 12 / 2 076 | 1 MB | 9 276/sn, p95 9 ms | 9 ms | 0,1 ms | <0,1 ms | 495 ms / 72,5 |
| 10 bin | 4,6 MB | 4 112/sn, p95 12 ms | 62 ms | 0,4 ms | 23 ms | 989 ms / 35,2 |
| 100 bin | 42 MB | 3 868/sn, p95 18 ms | 51 ms | 9,5 ms | 510 ms | 2 836 ms / 17,5 |
| 1 milyon | 420 MB | 4 176/sn, p95 16 ms | 47 ms | 118 ms | 1 965 ms | 1 800 ms / 15,8 |

"Karışık": 16 okuyucu sürekli SOS listesi ister, 8 yazıcı aynı anda SOS yazar, 5 sn.

**Yorum.**
1. **Ham yazma kapasitesi hedefin çok üstünde.** 1 milyon satırda bile ~4 000 yazma/sn, p95 16 ms
   (hedef 50/sn, 50 ms). SQLite'ın kendisi darboğaz değil.
2. **Okuma ve yazma birlikte gelince hedef kaçıyor.** 10 bin satırdan itibaren yazma p95 1–2,8 sn,
   yazma 15–35/sn (hedef 50/sn). Sebep bizim erişim desenimiz:
   - Depo tek bağlantı ve tek `Lock` kullanıyor; WAL eşzamanlı okumaya izin verse de her işlem
     sırayla yürüyor.
   - `sos_listele` her çağrıda 5 000 satıra kadar dönüyor (~45 ms kilitte).
   - Canlı akışta her yeni SOS her açık konsolda listenin **tamamını** yeniden istetiyor.
     5 konsol ve 50 SOS/sn → saniyede ~250 tam liste ≈ 11 sn kilit süresi/sn. Sistem doyar.
3. **Isı / özet yolu** 100 bin satırda 0,5 sn, 1 milyonda 2 sn (her çağrıda 100 bin satır okunuyor).
   Önbelleklenmezse büyür.
4. Kutu sorgusu mekânsal indeks olmadan 1 milyon satırda 118 ms. Kabul edilebilir; PostGIS GIST
   burada fark yaratır.

**Karar önerisi.**
- Tanıtım, teslim ve pilot ölçeği (onlarca kullanıcı, saatte yüzlerce kayıt) için SQLite
  **yeterli**.
- Afet ölçeğindeki karışık yük için **önce erişim deseni** düzeltilmeli; bu PostGIS'ten ucuz:
  1. okuma için ayrı bağlantılar (WAL'de paralel okuyucu);
  2. canlı akış mesajında yeni kaydın kendisini gönderip tam liste yerine yalnız değişeni
     tazelemek (ya da `sonrasi=` artımlı sorgu);
  3. istemcide kısa süreli tazeleme birleştirme.
- Ardından aynı betikle yeniden ölçülmeli.
- PostGIS tek başına (2) sorununu çözmez.

**Sınırlar.** Tek makine, sentetik ve tekdüze dağılım. HTTP ve JSON ayrıca maliyet ekler. Gerçek
afet trafiğinin şekli ölçülmedi.

**İyileştirme (13 Kasım 2026, aynı gün).**
1. **Okuma bağlantıları.** `depo/sqlite_surucu.py` artık tek yazma bağlantısı (kilitli) ve iş
   parçacığı başına salt-okunur okuma bağlantısı (`query_only`, WAL) kullanıyor. `_oku`/`_tek`
   kilit almıyor. Kilit içinde okuma yapan yöntem yok (tarandı). `tests/test_depo_eszamanlilik.py`
   yeni: bağlantılar arası görünürlük, 50 000 satırlık okuma sürerken yazma < 0,25 sn.
2. **`/api/ozet` SQL'de sayıyor** (`hasar_ozeti`, `kapanma_sayisi`). Eskisi 100 000'er satırı
   Python'a çekip sayıyordu; 100 000'den fazla kayıtta **sessizce eksik sayıyordu** (testte
   100 050 kayıt → eski yol 100 000). Gerçek veride üç zaman aralığında eskisiyle birebir aynı.
3. **Kapsayıcı indeksler.** Planlayıcı `GROUP BY` yüzünden `durum`/`kaynak` indeksini seçip tabloyu
   tarıyordu; `ANALYZE` de değiştirmedi. Eski tek sütunlu indeksler açılışta kaldırılıp yerine
   kapsayıcı olanlar kuruluyor; gruplamada `+durum` / `+kaynak` kullanılıyor. 1 milyon satırda:
   - `sos_sayilari` 884 → 30 ms (`ix_sos_zaman_kapsar` = zaman, lon, lat, durum);
   - `hasar_ozeti` 1 436 → 61 ms (`ix_hasar_zaman_kapsar` = zaman, kaynak, skor);
   - kutulu SOS listesi 498 → 16–30 ms;
   - **afetzedenin kendi çağrıları 10 085 → < 1 ms** (`ix_sos_kullanici_zaman`). Eski tek sütunlu
     indeksle tablo zaman sırasıyla taranıyordu; bu sorun bu ölçümde ortaya çıktı.
   - Aynı desen ihbarlarda da düzeltildi (`ix_ihbar_kullanici_zaman`).
4. **Konsolda tazeleme birleştirme** (`canli/canliAkis.ts` `birlestirici`). Aynı sorgu anahtarı
   için ilk mesaj hemen tazeler; 1 sn içindekiler pencere sonunda tek tazelemede birleşir.
   Tarayıcıda gerçek modülle: 2 sn'ye yayılmış 100 mesaj → 3 tazeleme (0, 1 003, 2 005 ms),
   son mesaj kaçmadı. Yoklama değil, yalnız mesajla çalışır.

**Yeniden ölçüm `[Ö]`.** Afet senaryosu `benchmark/sqlite_afet_senaryosu.py`: 50 SOS/sn,
5 konsol (her biri kutulu SOS listesi + özet), 10 sn. "Önce" = commit'li eski depo.
Sonuç: `benchmark/reports/sqlite_afet_2026-11-13.json`.

| Durum (100 bin satır) | Yazma p95 | 10 sn'de yazılan | Tazeleme p95 | Güncellik gecikmesi p95 | İşlenmeyen mesaj |
|---|---|---|---|---|---|
| Önce | 723 ms | 41 (hedef 501) | 997 ms | 6,1 sn | 103 |
| Yalnız okuma bağlantısı + SQL özet | 1,2 ms | 501 | 309 ms | 8,9 sn | 2 304 |
| + birleştirme | 0,5 ms | 501 | 589 ms | 1,4 sn | 0 |
| **+ kapsayıcı indeksler (son)** | **0,8 ms** | **501** | **199 ms** | **1,07 sn** | **0** |
| Son, 1 milyon satır | 1,2 ms | 501 (50,0/sn) | 547 ms | 1,45 sn | 0 |

Hedefe göre: yazma 50/sn ve p95 < 50 ms **sağlandı**. Konsol tazelemesi p95 < 100 ms (liste ve
özet birlikte, 5 konsol eşzamanlı) **sağlanmadı**: 199 ms (100 bin), 547 ms (1 milyon). Güncellik
gecikmesi ~1–1,5 sn; bunun yaklaşık 1 sn'si bilinçli birleştirme penceresi.

Temel ölçüm de yeniden koşuldu (`benchmark/reports/sqlite_yuk_2026-11-13_sonra.json`).
- Karışık yükte (16 okuyucu + 8 yazıcı, **sınırsız** hız) yazma p95 0,5–2,8 sn'den 12–16 ms'ye
  indi; saniyede 15–72 yerine 500–700 yazma.
- **Ama okuyucular aç kaldı:** okuma p95 ~7 sn, saniyede 2–3,5 okuma.
- Sebep Python GIL'i: 5 000 satırlık okuma her satırda GIL'i bırakıp geri alıyor, sürekli yazan
  iş parçacıkları araya giriyor. Eskiden tersiydi: okuyucu kilitle yazıcıyı bekletiyordu.
- Gerçekçi hızda (50/sn, yukarıdaki tablo) sorun görülmedi. Saniyede yüzlerce yazmada büyük
  liste okumaları yavaşlar.
- Daha çok indeks yüzünden 16 yazıcının ham hızı ~3 900'den ~3 000–3 500/sn'ye indi; hedefin
  60 katı.

**Açık.**
- **Artımlı tazeleme** (önerinin 2. maddesi, uygulanmadı): canlı akış mesajı yeni kaydı taşısın
  ya da `sonrasi=` ile yalnız değişen satırlar gelsin. Böylece her tazelemede 5 000 satır
  dönmez; hem 547 ms'lik tazeleme hem doyumdaki GIL açlığı küçülür.
- Isı ızgarası yolu (`/api/road_damage/heatmap`) bu ölçüme girmedi.
- HTTP ve JSON maliyeti ölçülmedi; uvicorn tek worker.
- Ölçüm betiğinin ilk sürümünde "gerçekleşen hız" konsol bekleme süresini de paydaya katıyordu
  (47,5 ve 39,9 gibi düşük değerler). Düzeltildi; bütün koşularda 10 sn'de 501 yazma = 50/sn.

## J-189 🟠 Makale "mekânsal sorgular PostGIS ile yürütülmektedir" diyor — çalışan sistem SQLite kullanıyor
**Durum:** AÇIK · **Bulundu:** 18 Kasım 2026 (makalenin gönderime hazırlığı denetlenirken; başka bir oturumda "J-175" numarasıyla not edilmişti, numara ısı haritası maddesiyle çakıştığı için 24 Kasım'da J-189 oldu) · **İlgili:** J-136, CLAUDE.md §1, §8, §10

**Bulgu.** Makalenin §4.1 ortam paragrafı: *"Risk skorlaması CatBoost [48] ile, yol ağı çizgesi OSMnx [43] ve NetworkX [62] ile, mekânsal sorgular PostGIS [63] ile yürütülmektedir."* Kaynakçada [63] PostGIS kaydı var. Oysa CLAUDE.md §10 (13 Kasım 2026): çalışan sistem SQLite kullanır (`backend/veri/quakemind.sqlite3`, `depo/sqlite_surucu.py`); PostGIS sürücüsü (`depo/postgis_surucu.py`) yazılmadı ve "belgede, sunumda ve makalede 'sistem PostGIS kullanıyor' denmez; PostGIS hedef mimaridir". Makalede "SQLite" hiç geçmiyor.

**Neden ciddi.** Bu bir sistem tarifi; depo herkese açık olursa hakem ya da okuyucu kodu açıp PostGIS kodu bulamaz. CLAUDE.md §1 (her iddianın kaynağı var) ve §8 (ölçmeden iddia yok) ihlali.

**Önerilen düzeltme.** (a) Cümle *"mekânsal sorgular SQLite üzerinde (WAL kipinde, kapsayıcı zaman indeksleriyle) yürütülmektedir"* olsun, [63] SQLite belgesiyle değiştirilsin; (b) PostGIS hedef mimari olarak ayrı bir cümlede anılsın (Bölüm 5.3, gelecek çalışma). (a)+(b) birlikte önerilir.

**Not.** Makaleye dokunulmadı; makale hocanın okumasında, düzeltme sırası ekip kararı.

## J-192 🟡 Deprem kataloğunda Türkçe harfler "?" olarak kayıtlı (yer adları bozuk görünüyor)
**Durum:** AÇIK · **Bulundu:** 24 Kasım 2026 (J-191 sırasında, risk ekranındaki deprem listesinde) · **İlgili:** J-191, kural 1

**Bulgu.** `apps/earthquake_risk/data/query.csv`'de 6 265 satırın yer adında Türkçe harfler soru işaretine dönmüş: aynı yer bir satırda "Doğubayazıt", 2006 tarihli USGS satırlarında "Do?ubayaz?t". Bozulma kaynak dosyada; ekran olduğu gibi gösteriyor (risk listesi, deprem katmanı ipucu).

**Yapılacak.** Uydurma düzeltme yapılmaz. Seçenekler: (a) aynı USGS kimliğini (`id` sütunu) USGS'ten yeniden çekip yer adını oradan almak, (b) yer adı yerine koordinattan en yakın il/ilçe adını (yerel OSM kopyası) yazmak ve kaynağını belirtmek.

# KAPANAN MADDELER DİZİNİ

Kapanan maddelerin tam metni `EKSIKLER_ARSIV.md`'de, aynı bölüm başlıkları altında ve aynı
kimlikle. Başka belgelerdeki "EKSIKLER J-xxx" atıfları için kimliği burada ya da arşivde arayın.

| Kimlik | Madde | Kapanış |
|---|---|---|
| A-14 | 🔴 Geçilebilirlik kuralı adları ve tanımları makale ile kodda ters | 16 Eylül 2026 |
| A-22 | 🟠 Veri artırımı tohuma bağlı değildi — "tohum 42" koşuları tekrarlanabilir değil | 22 Eylül 2026 |
| B-09 | 🟡 Donanım künyesi ve `v_ort` | 16 Eylül 2026 |
| E-05 | 🟡 Telafi iddiası kurgu gereği | 12 Eylül 2026 |
| E-06 | 🟡 Örneklem büyüklüğü | 16 Eylül 2026 |
| F-01 | KARAR BEKLİYOR — 15 commit upstream'e gönderilmedi | 18 Kasım 2026 |
| F-02 | KARAR BEKLİYOR — 123 commit edilmemiş dosya | 18 Kasım 2026 |
| F-03 | ⚪ `makale` dalı yerele alındı | 12 Eylül 2026 |
| H-01 | ✔ Tablo 12'deki 0,4276 ile Tablo 22'deki ROC-AUC 0,4276 çakışması | 12 Eylül 2026 |
| H-02 | ✔ Karolama adımının örtüşmesiz olduğu şüphesi | 12 Eylül 2026 |
| J-13 | 🟠 Geocoding hala aga bagli — yerel cozum yok | 18 Kasım 2026 |
| J-18 | 🟡 `/status/{id}` tek seferde 17 MB dönüyor — 15,5 MB'ı base64 görsel | 18 Kasım 2026 |
| J-23 | 🔴 `/naive_compare`, `/analyze` oturumlarıyla çalışmıyor — senaryo modele bağlanamaz | 16 Eylül 2026 |
| J-24 | ⚪ (bilgi) Model tabanlı kapanma için gereken EMSR648 değil, Maxar kapsaması | 16 Eylül 2026 |
| J-62 | 🟠 Simülasyon (tatbikat) modu konsolda kuruldu; sözleşmeyle üç uyuşmazlık çıktı | 25 Eylül 2026 |
| J-61 | 🟠 Yanıtlar sıkıştırılmıyordu: konsol açılışında 660 KB ham JSON iniyordu | 25 Eylül 2026 |
| J-60 | 🔴 CORS herkese açıktı: her site kimlik bilgisiyle API'ye istek atabiliyordu | 25 Eylül 2026 |
| J-59 | 🟠 Uçların üçte biri hâlâ kimlik istemiyor (kural 5) | 18 Kasım 2026 |
| J-57 | 🟠 `npm run kontrol` konsol kaynaklarının yanına `.js` yazıyor; Vite bu kopyaları `.tsx`'ten önce yükler | 24 Eylül 2026 |
| J-56 | 🟠 Konsol düzeni: sol panel her modda "Katmanlar", 10 katman anahtarının 4'ü hiçbir şey çizmiyordu | 24 Eylül 2026 |
| J-55 | 🟠 Sevkte ekibin olaya uzaklığı kuş uçuşuydu; araç yolundan süre yoktu | 22 Eylül 2026 |
| J-54 | 🔴 Sevkte kim, nereye, kaç kişiyle gidiyor belirsiz; ekip üç yere birden "müsait" görünüyor | 22 Eylül 2026 |
| J-53 | 🔴 Eski uçlar oturumsuz yanıt veriyor: vatandaş ihbarlarının metni ve konumu açık | 24 Eylül 2026 |
| J-52 | 🟠 Canlı modda yeni SOS ve ihbar konsol listesine en çok 60 sn geç düşüyordu | 22 Eylül 2026 |
| J-51 | 🔴 Afetzedenin fotoğraf, yazılı ve ihtiyaç ihbarı konsola düşmüyordu; fotoğrafta model seçimi yoktu | 22 Eylül 2026 |
| J-50 | 🟠 Afetzede ekranı telefon gibi dar yapılmıştı; harita, hastane ve fotoğraf yoktu | 18 Kasım 2026 |
| J-49 | 🔴 Oturumsuz açılış "Yükleniyor…"da takılıyordu (b998807 ile gelen hata) | 21 Eylül 2026 |
| J-48 | 🟠 Afetzede hesap açamıyordu; konsolda afetzede ekranına giden yol yoktu | 21 Eylül 2026 |
| J-47 | 🟠 Canlı akış sessizce ölünce ekran "canlı" diyordu; kopukken gelen mesajlar kayboluyordu | 21 Eylül 2026 |
| J-46 | 🟠 Konsol canlı modda dakikada bir bütün pencere sorgularını yeniden istiyor | 18 Kasım 2026 |
| J-45 | 🔴 Eski demo hesaplarının jetonu kodda sabit; herkes acil bildirim yayınlayabiliyor | 18 Kasım 2026 |
| J-44 | 🟠 Afetzedeye hasar bilgili yol tarifi verilemiyor | 22 Eylül 2026 |
| J-43 | 🟠 Afetzede ekranı: eski webdeki portal yeni konsolda yeniden yazıldı | 21 Eylül 2026 |
| J-42 | 🔴 Canlı akış (SSE) kimliksizdi: herkes her SOS konumunu ve ekip konumlarını alıyordu | 21 Eylül 2026 |
| J-41 | 🟠 Haritada ad yoktu, şehre gitme yoktu, noktalar ne olduğunu söylemiyordu | 21 Eylül 2026 |
| J-40 | 🟠 Konsolun haritasında altlık yoktu: zemin boştu | 21 Eylül 2026 |
| J-37 | 🟡 Sert rotanın 422 mesajı ağ kopukluğunu kapanma sanıyor | 18 Kasım 2026 |
| J-35 | 🟠 Konsolun Wayback "deprem sonrası" varsayılanı Antakya'da deprem öncesi görüntü | 21 Eylül 2026 |
| J-33 | 🟡 Sağlık kontrolü model yüklüyordu ve kamera durumunu uyduruyordu | 21 Eylül 2026 |
| J-30 | 🟠 Model kapanma koşuları algılama hatasını ölçmüyor — klasik ajan modelin kapanmalarını "gerçek" sayıyor | 16 Eylül 2026 |
| J-27 | ⚪ (bilgi) Drone sahnelerinin gerçek en yüksek zoom'u z=22 | 16 Eylül 2026 |
| J-19 | 🔴 Kapanma kuralı yolun MERKEZ ÇİZGİSİ pikselini istiyor — model kaynaklı kapanma üretilemiyor | 16 Eylül 2026 |
| J-01 | 🔴 `/api/road_damage/recent` her 20 saniyede tüm segment dizilerini yeniden gönderiyor | 15 Eylül 2026 |
| J-02 | 🔴 `simulate_naive_agent` döngünün içinde `G.copy()` yapıyor | 15 Eylül 2026 |
| J-03 | 🔴 NLP gecikmesinin %89'u Nominatim geocoding'i; önbellek yok | 15 Eylül 2026 |
| J-04 | 🟠 `zemberek_lemmatize` çağrılıyor ama sonucu hiç kullanılmıyor | 15 Eylül 2026 |
| J-05 | 🟠 `calculate_route` her rotayı iki kez hesaplıyor, birini atıyor | 15 Eylül 2026 |
| J-06 | 🟠 `ox.distance.nearest_nodes` her çağrıda KD-ağacını sıfırdan kuruyor | 15 Eylül 2026 |
| J-07 | 🟠 Tüm uç noktalar senkron `def` — ağır iş GIL'i tutup her şeyi bekletiyor | 18 Kasım 2026 |
| J-08 | 🟠 `apply_risk_penalties` O(kenar × hasar noktası) saf Python | 15 Eylül 2026 |
| J-09 | 🟡 `_nearest_graph_node` O(n) lineer tarama | 18 Kasım 2026 |
| J-11 | 🟡 Harita sayfasında beş ayrı polling döngüsü | 18 Kasım 2026 |
| J-12 | 🔴 Senaryo verisi gerçek değil — kapanmalar `rng.sample` ile rastgele | 16 Eylül 2026 |
| J-14 | 🔴 SegFormer, HTTP sunucu sürecinde boşuna yükleniyor | 15 Eylül 2026 |
| J-17 | 🟠 Oturum deposu 20 tam graf tutabiliyor — 2,7 GB tavan | 15 Eylül 2026 |
| J-63 | 🟠 Tatbikat rota grafiği görüntü kutusuyla sınırlıydı — 25 OD çiftinin 25'i "ulaşılamaz" | 25 Eylül 2026 |
| J-64 | 🟠 Araç giremeyince "ulaşılamaz" deniyordu; gerçekte son adım yaya yürünür | 25 Eylül 2026 |
| J-66 | 🟠 Çıkarım iş parçacığı sınırsızdı: aynı iş 26,6 sn ile 243,1 sn arasında oynuyordu | 25 Eylül 2026 |
| J-68 | 🟠 Overpass düşünce yol katmanı sessizce boş geliyor, analiz "0 kapalı yol" diyordu | 25 Eylül 2026 |
| J-71 | 🟢 Simülasyon uçtan uca çalıştı (konsol + backend), dört hata düzeltildi | 26 Eylül 2026 |
| J-72 | 🟠 Analizin bulduğu hasar hiçbir yere kaydedilmiyordu (PostGIS yokken sessiz düşüyordu) | 26 Eylül 2026 |
| J-73 | 🟠 Tatbikat başlatılabiliyordu ama bitirilemiyordu; verisi gerçek veriyle karışıyordu | 26 Eylül 2026 |
| J-74 | 🟠 Tatbikat modu sayfa yenilenince kayboluyordu (koşu sunucuda sürerken) | 26 Eylül 2026 |
| J-75 | 🟠 Seçilen görüntü haritada görünmüyordu — model neye baktığı ekranda yoktu | 26 Eylül 2026 |
| J-76 | 🔴 Analiz yakınlaştırmayı çizilen alandan değil istekteki yarıçaptan seçiyordu — model hiçbir şey bulamıyordu | 26 Eylül 2026 |
| J-77 | 🟠 Analiz artık sabit standartta koşuyor; öncesi / sonrası / etiketli üçlüsü üretiliyor | 26 Eylül 2026 |
| J-141 | 🔴 Sunucuya ulaşılamazken eşitleme worker'ı sonsuz döngüye giriyor | 18 Kasım 2026 |
| J-142 | 🟠 İhbar formundaki kategori, aciliyet ve kişi sayıları sunucuya gitmiyor | 18 Kasım 2026 |
| J-143 | 🟠 İhbar formu GPS kullanmıyor; afetzededen koordinat elle isteniyor | 18 Kasım 2026 |
| J-144 | 🟠 Risk ekranı etkenleri atıyor ve "servis bildirmedi" diyor | 18 Kasım 2026 |
| J-145 | 🟠 `/api/oturum/misafir` sınırsız hesap açıyor; kişi başı ihbar sınırı aşılıyor | 18 Kasım 2026 |
| J-146 | 🟡 Birleştirme sırası, klasör yeniden adlandırma ve mobil kapsamı karar bekliyor | 18 Kasım 2026 |
| J-148 | ⚪ PR #5 küçük notlar | 18 Kasım 2026 |
| J-150 | 🟠 Tatbikat sağ paneli, uzama ölçülemeyen koşuda çöküyordu | 12 Kasım 2026 |
| J-152 | 🔴 Risk uçlarında kimlik denetimi yok; canlı veri tazeleme istek yolunda | 13 Kasım 2026 |
| J-154 | 🟠 Tatbikat kıyas kolları dakikaya yuvarlanıp QuakeMind farkını siliyordu | 12 Kasım 2026 |
| J-156 | 🟠 Giriş üç kapıya ayrıldı; ekip hesaplarını koordinasyon açıyor | 12 Kasım 2026 |
| J-157 | 🟠 Hesap yönetimi tek sayfada: düzenle-kaydet, askıya alma, ilk girişte şifre, kayıt defteri | 13 Kasım 2026 |
| J-159 | 🔴 SOS ve ihbar kimlikleri 32 bitti: ~77 bin kayıtta çakışma olasılığı %50 | 13 Kasım 2026 |
| J-160 | 🔴 Hasar analizi drone görüntüsünde "0 kapalı yol": alan görüntüye taşınmıyor, çözünürlük sessizce düşüyordu | 13 Kasım 2026 |
| J-161 | 🟠 Hasar analizi ekranı: panel genişlik sıçraması, yanıltıcı alan ayarları, yakın çekim seçeneği | 13 Kasım 2026 |
| J-162 | 🟠 Saha ekibi kapanmalardan kaçınan rotayı haritada göremiyordu; rol erişimi incelemesi | — |
| J-163 | 🟠 Saha ekibi koordinasyon işlerini yapabiliyordu; eski ve araştırma uçları oturumsuz açıktı | — |
| J-164 | 🟡 Konsol üst çubuğu 1024 px'te taşıyordu; hesap sayıları yüklenirken 0 görünüyordu | — |
| J-165 | 🟠 Kamera tespiti çatlağa "binayı boşaltın" diyordu; analizlerin ve bazı işlemlerin kaydı tutulmuyordu | — |
| J-166 | 🟠 İşlem kaydı kurcalanmaya açıktı; girişler, kişisel veri görüntüleme ve ekip konum geçmişi tutulmuyordu | — |
| J-169 | 🟠 Başarısız bir yazma veritabanı kilidini bırakmıyordu | — |
| J-170 | 🟠 Metin analizi: adres dış servise gidiyordu ve çoğu zaman yanlış yerdi; sonuç ekranı okunmuyordu | — |
| J-171 | 🟠 Araç rotası dönüş yasaklarını çiğniyordu, "Yol ve Rota" sayfası ölüydü (J-167 Grup E) | — |
| J-172 | 🟠 Harita karmaşık ve okunmuyordu: aynı yuvarlaklar, kesilen bilgi kutusu, anlaşılmaz kaynak ağırlıkları; J-167 Grup F | — |
| J-173 | 🔴 Deprem riski: eşzamanlı istekte başka ilin sonucu, şişkin uzun vadeli tehlike, açık uçlar; ekran soruya cevap vermiyordu | — |
| J-174 | 🔴 Uçtan uca akış: canlı akış ilk jeton yenilemesinde kalıcı kapanıyordu; ihtiyaç geçen yazılı ihbar ihtiyaç sayfasına düşmüyordu | — |
| J-175 | 🟠 Genel durum: ısı haritası kaynak ayırmıyor ve az veriyi yoğun gösteriyordu; sağ panel bir sonraki adımı söylemiyordu; gereksiz veri iniyordu | 18 Kasım 2026 |
| J-176 | 🟡 Giriş ekranı: hesap açarken üç kapı seçilebilir duruyordu; şifre görünür yapılamıyordu; zemin boştu | 18 Kasım 2026 |
| J-177 | 🟠 Konsol yazısı küçüktü (U-5); acil bildirim saha ekibi ekranında hiç görünmüyordu | 18 Kasım 2026 |
| J-167 | 🟠 Uçtan uca tarama (17 Kasım): giriş ve SOS sınırsız, birkaç ölü ekran, saha ana düğmesi ekran dışında | 18 Kasım 2026 |
| J-178 | 🟡 Haritada mahalle, sokak ve cadde adları okunmuyordu | 20 Kasım 2026 |
| J-180 | 🟠 Afetzede çevresindeki kapalı yolları ve hasarı görmüyordu; toplanma alanları hiç yüklenmiyordu | 23 Kasım 2026 |
| J-181 | 🟠 Yürüme rotası kapanmanın yalnız orta noktasına bakıyordu, her istekte bütün hasar kayıtlarını okuyordu; dış servis yedeği kapanmayı denetlemiyordu | 24 Kasım 2026 |
| J-182 | 🔴 Boş sunucuda (canlıya ilk çıkış) hiçbir rolde girilemiyordu; ilk yöneticiyi açmanın güvenli ve belgeli yolu yoktu | 24 Kasım 2026 |
| J-183 | 🟡 Ortak örnek hesap yoktu; profil simgesi doğrudan çıkış yapıyordu, hesap ayarları yoktu | 24 Kasım 2026 |
| J-184 | 🔴 Canlıda hasar analizi kapalı yol bulamıyordu; model listesinde 4 yerine 1 model (sunucuya dosya kurulumu Deha'da) | 24 Kasım 2026 |
| J-185 | 🟠 Tatbikat: canlıda koşmuyordu; sonuç paneli okunmuyor ve etkileşimsizdi, çizgiler üst üste, iki yanlış değer | 24 Kasım 2026 |
| J-186 | 🔴 Tatbikatı kapatmanın görünür yolu yoktu; yeniden başlatmada tatbikat noktaları gerçek veriye karışıyordu | 24 Kasım 2026 |
| J-187 | 🟠 Üç uydu modeli ve yerel OSM kesiti hiçbir yerden indirilemiyordu | 24 Kasım 2026 |
| J-188 | 🟠 81 il risk sıralaması canlıda boştu (il merkezleri depoda yoktu); dağıtım kontrol testi eski uçlarda düşüyordu | 24 Kasım 2026 |
| J-38 | 🟠 Yol ağı zaman aşımına uğrayınca sonuç "0 kapalı yol, bölge erişilebilir" diyordu | 24 Kasım 2026 |
| J-168 | 🔴 Eski web kamera sayfası API'ye ulaşamayınca uydurma sonuç gösteriyordu | 24 Kasım 2026 |
| J-190 | 🟠 Yol ve rota: yarım çokgen rota ekranına taşınıyordu, araç kapalı yoldan geçiyordu, kapanmanın durumu değiştirilemiyordu | 24 Kasım 2026 |
| J-191 | 🟠 Deprem riski ekranı okunmuyordu; harita noktaları uzakta görünmüyor ya da üst üste biniyordu; logo ana ekrana götürmüyordu | 24 Kasım 2026 |

---

# DEĞİŞİKLİK GÜNLÜĞÜ

| Tarih | Değişiklik |
|---|---|
| 12 Eylül 2026 | Dosya oluşturuldu. Makale incelemesinden A-01…A-03, B-01…B-12, C-01…C-05, D-01…D-04, E-01…E-06, F-01…F-03 kaydedildi. E-05 ve F-03 kapalı olarak açıldı. |
| 12 Eylül 2026 | Makalenin **tam metni** incelendi; `MAKALE_DUZELTME_LISTESI.md` oluşturuldu. A-04 (artçı ayıklaması çelişkisi) ve A-05 (eksik naif tabanlar) eklendi. Yapısal kontroller temiz çıktı: tablo 1–23, şekil 1–21, denklem 1–17 kesintisiz; kaynakça 57 kayıt, anılmayan/eksik kaynak yok. |
| 12 Eylül 2026 | `PROJE_DOSYASI.md` hazırlandı (uzman ortak yazarlar için teknik tanıtım). D-05 eklendi: defter şablonu ile fiilen koşulan hiperparametreler uyuşmuyor. Karolama adımının 512 olduğu yönündeki ilk şüphe **yanlış çıktı** — `tile_size, tile_stride = 512, 256`, yani %50 örtüşme gerçektir ve makalenin sızıntı uyarısı geçerlidir. |
| 12 Eylül 2026 | Başka bir oturumda yapılan bağımsız inceleme madde madde **doğrulandı** ve bu dosyaya işlendi: A-06 (sentetik üretici Bölüm 3'te tanımsız), A-07 (atama kuralı tanımsız), A-08 (tek/çok etiketli çelişkisi), A-09 (üç kural tanımsız + yanlış atıf), A-10 (yakınlaştırma hesabı), A-11 (λ(d) ↔ r_h), A-12 (orta nokta ölçütü), A-13 (4.1.1 çelişkisi), B-13 (metin kümesi künyesi), D-06 (ham LaTeX denklemler), D-07 (erken durdurma ölçütü), G-01…G-03 (kaynakça). İki şüphe kapatıldı: H-01 (0,4276 çakışması gerçek rastlantı), H-02 (karolama örtüşmesi gerçek). |
| 12 Eylül 2026 | İki inceleme listesi **tek dosyada birleştirildi**: `MAKALE_DUZELTME_LISTESI.md` yeniden yazıldı — 48 madde (`M-01`…`M-48`), kapatılan şüpheler, üç aşamalı öncelik sırası ve kimlik eşleme tablosu. |
| 15 Eylül 2026 | **M-04 kapatıldı** — belgeye Bölüm 3.8.1 "Senaryo Koşumlarında Kullanılan Sentetik Kapanma Kümesi" eklendi (Algoritma 2 + yeni Tablo 10). Koddan çıkarılan ölçüm: istenen ρ₀ = %18 hiçbir bölgede gerçekleşmemiş, bağlantılılık kısıtı oranı 2–5 kez yarılamış; etkin oran %0,55–4,50, toplam %2,87 (6 378 / 222 298 kenar). Bu aralık EMSR648 gerçek oranlarını (%1,58 / %1,71) kapsıyor. Eski "kapanma oranı hedefin altında, bug olabilir" şüphesi **kesin olarak kapandı**: bug değil, bağlantılılık kısıtının tasarım gereği yan etkisi. |
| 15 Eylül 2026 | **`v_ort` = 15,0 km/sa bulundu** (`naive_baseline.py:48`) — B-09 kısmen kapandı. 206,6 dk ve 1 641,0 dk değerlerinin tamamı bu varsayımdan türüyor; makalede hiçbir yerde geçmiyor. |
| 15 Eylül 2026 | **Karar:** simülasyon güncellemesi **ayrı bir sohbette** yapılacak (kullanıcı kararı). Bölünmenin yarattığı bilgi kaybını önlemek için `SIMULASYON_DEVIR_BELGESI.md` hazırlandı: depo durumu, kod haritası, atama kuralının koddan çıkarılmış tam hâli, ölçülmüş parametreler, açık maddeler, güncelleme yapılırsa makalede değişecek yerler ve geri dönüşte bu sohbete getirilecek bilgiler. |
| 15 Eylül 2026 | **Performans incelemesi** yapıldı (ölçümlü): J-01…J-12 eklendi. En ağır üçü: /recent her 20 sn’de ~19 MB segment gönderiyor (J-01); simulate_naive_agent döngü içinde G.copy() yapıyor, ~78 s (J-02); NLP gecikmesinin %89’u önbeleksiz Nominatim (J-03, uçtan uca 7,28 s). J-12, E-01’in sistem tarafındaki yüzü olarak kaydedildi. |
| 15 Eylül 2026 | **Hızlı kazanç paketi uygulandı ve ölçüldü.** KAPALI: J-01 (`/recent` 1 272 288 → **264 bayt**, 0,4 sn → **0,0023 sn**; ayrı `/segments/{id}` ucu + ETag), J-02 (naif ajan `G.copy()` → `restricted_view`: **18×** hızlı, 6/6 birebir aynı sonuç), J-03 (geocoding önbelleği + adaylar arası dedupe: tekrar eden metin **7,28 → 0,55 sn**, çıktı aynı), J-04 (ölü lemmatizasyon çağrısı + tembel Zeyrek: NLP import **60,8 → 20,6 sn**), J-05 (`/route` artık yalnız A*: Dijkstra ile maliyet farkı **0,000000 m**), J-06 (önbellekli `nearest_node`: **541×**, 20/20 aynı düğüm). KISMEN: J-10. YENİ: J-13 (geocoding'in ağa bağlı ilk sorgusu, J-03'ten ayrıldı). Tüm değişiklikler canlı backend üzerinde uçtan uca doğrulandı. |
| 15 Eylül 2026 | **Süreç/iş parçacığı/bellek incelemesi** (ölçümlü): J-14 (SegFormer HTTP sunucusunda boşuna yükleniyor — **+618 MB, +5,3 sn**, hiç okunmayan bir sözlük girdisi için; gerçek çıkarım zaten ayrı işçi süreçte), J-15 (torch iş parçacığı sayısı hiç sınırlanmamış — `import torch` tek başına +22, ilk matmul +13; iki torch süreci × 14 intra-op thread, 14 fiziksel çekirdek), J-16 (graf pickle'larında **1,23 milyon** kullanılmayan öznitelik — 21,3 → 4,5 MB, yükleme 0,61 → 0,36 sn; **bellek kazancı değil, disk/açılış kazancı**), J-17 (oturum deposu 20 × 135 MB = **2,70 GB** tavan, yaşa göre tahliye yok). Ölçülen ayakta duran sistem: 2 ağır süreç, 56 iş parçacığı, ~2,2 GB RSS. |
| 15 Eylül 2026 | **J-14 kapatıldı** — SegFormer artık HTTP sunucu sürecine yüklenmiyor. Ölçülen: sunucu süreci **1 183 → 681 MB (−502 MB)**, toplam 2 218 → 1 716 MB; 5,3 sn'lik model yüklemesi açılıştan kalktı. İş parçacığı sayısı **düşmedi** (torch YOLO için sunucuda kalıyor) — J-15 açık. Beş uç noktada işlevsel doğrulama yapıldı; `/route` sonucu birebir aynı (7 645,2 m / 405 nokta), `/analyze` işçi süreçte baştan sona tamamlandı (16 parça çıkarım, 3 924 yol segmenti, 6 görsel). YENİ: J-18 (`/status` tek seferde 17 MB, 15,5 MB'ı base64 görsel). |
| 15 Eylül 2026 | **J-17 kapatıldı** — oturum deposuna süre aşımı (30 dk), bellek bütçesi (1024 MB, ölçülmüş 1 900 bayt/eleman sabitiyle) ve arka plan süpürücüsü eklendi; üçü de ortam değişkeniyle ayarlanabilir. 12/12 birim kontrolü + canlı doğrulama. Uygulama sırasında **iki hata bulunup düzeltildi**: (a) bütçeden büyük tek graf ilk okumada tahliye edilip /route'u 422'ye düşürüyordu, (b) aynı kimlik iki kez saklanınca sıra listesinde mükerrer girdi oluşuyordu. **Dürüst kayıt:** RSS düşmüyor (CPython arena'ları işletim sistemine iade etmiyor); kazanç büyümenin sınırlanması — tahliye sonrası 3 yeni oturum +44 MB ekledi, ilk üçü +173 MB'dı. Dokuz bölgeli senaryo (~607 MB tahmin) bütçeye rahat sığıyor. |
| 15 Eylül 2026 | **J-08 kapatıldı** — `apply_risk_penalties` vektörize edildi (BallTree, radyan haversine). Gerçek EMSR648 yüküyle (1 321 hasar noktası, 207 kapanma, 49 666 kenar) **139,49 → 3,49 sn (40×)**; 75,9 milyon haversine çağrısı elendi. Sonuçlar **bit düzeyinde aynı**: kaldırılan kenar kümesi birebir, `risk_cost` farkı 0,00e+00. numpy skaleri → saf float dönüşümü eklendi (aksi halde `/safe_route` JSON serileştirmede 500 verirdi). Sınır durumları (hasar/kapanma yok) ayrıca sınandı. Gerçek veriye geçişin (J-12/E-01) teknik ön koşulu kalktı. |
| 15 Eylül 2026 | **J-12 kapsama analizi** (kod değişikliği YOK). EMSR648'in açık erişim olduğu doğrulandı (public S3, HTTP 200, kayıt/token yok) — hakem sorusuna karşı güçlü kaynak. Aktivasyonda 20 AOI var; üçü daha indirildi (AOI08 Pazarcık, AOI18 Kırıkhan, AOI20 Elbistan; 3,7 MB). **Kritik bulgu:** yol kapanma katmanı yalnız **4 bölgede** kullanılabilir (Pazarcık'ın yol katmanı 'Not Analysed', Kırıkhan yalnız 'Possibly damaged' + PRODUCT geçişi); hasar noktası katmanı **5 bölgede** zengin (2 729 kayıt). İskenderun/Samandağ/Belen/Göksun için AOI yok. Ayrıca doğrulandı: EMSR648 vektör paketlerinde **hiç görüntü dosyası yok** (5 pakette raster sayısı 0) — modeller bu veri üzerinde çalışmaz, ona karşı **doğrulanır**. Kapsam kararı kullanıcıda. |
| 16 Eylül 2026 | **Model tabanlı kapanma zinciri uçtan uca denendi** (kod değişikliği YOK). Üç bulgu: **J-21** Esri Wayback'te Antakya'nın deprem sonrası görüntüsü yok (2023-02-23 karosu öncesiyle bayt bayt aynı) — Maxar Open Data'da var ve `/analyze` onu sorunsuz kullanıyor; **J-20** senaryo modele 3,86 m/px veriyor, Maxar doğalı 0,3-0,5 m/px, z=18'e çıkınca tespit edilen hasar **25 kat** artıyor (ama çıkarım 94,9 → 306,8 sn); **J-19** çözünürlük düzelse bile kapanan yol **sıfır** kalıyor, çünkü kural hasarın yolun MERKEZ ÇİZGİSİ pikselinde olmasını istiyor; gerçekte moloz yan binadan sokağa dökülüyor. `simulate_random_closures`'ın var olma sebebi büyük olasılıkla bu. Çözüm mekanizması zaten mevcut: `apply_risk_penalties`'in r_h=25 m sert-kapatma yarıçapı. |
| 16 Eylül 2026 | **J-19 kapatıldı** — kapanma kuralına metre cinsinden yarıçap eklendi (`blockageRadiusM`, varsayılan 25 = r_h; 0 = eski kural, Streamlit tarafı değişmedi). Gerçek model çıktısında eski kural 0, yeni kural r_h=5/25/50 m'de 30/100/188 kapalı kenar (389'dan) — kapanmalar artık modelden geliyor. Canlı boru hattı ile çevrimdışı sonuç birebir aynı. **Yeni:** J-22 (r_h=25 m, aynı alanda EMSR648'in %3,2'sine karşı %25,7 — ~8 kat fazla kapanma, kalibrasyon gerekli), J-23 (`/naive_compare` `/analyze` oturumlarını desteklemiyor — senaryo modele bağlanamaz), J-24 (model tabanlı kapanma için Maxar kapsaması önemli: **8/9 bölge** kapsanıyor, yalnız Göksun'da görüntü yok; doğrulama 4/9 bölgede). |
| 16 Eylül 2026 | **Drone sahneleri senaryosu kuruldu ve ölçüldü.** Kullanıcının modeli test ettiği üç Help.NGO sahnesi (H-D1, H-D2, K-D1; 3,4–3,9 cm/px) bulundu; veri seti, kırpılmış graf önbelleği, `--dataset drone`, bbox destekli uçlar eklendi. z=18/19/20 maskeleri yerelde üretildi; z=21/22 için Colab defteri hazır (J-20 DEVAM). **J-23 KAPALI** (`/closures_from_mask`). Sentetik Hatay regresyonu birebir aynı. **Yeni:** J-25 (model kapanmaları ağı kilitliyor: 9 atamadan 1'i rotalandı), J-26 (EMSR648 doğrulaması: zoom arttıkça gerçek hasar tespiti artarken yanlış alarm daha hızlı artıyor; yol dengeli doğruluğu en iyi %59,1 — şansa yakın; en yüksek zoom en iyi değil), J-27 (gerçek en yüksek zoom z=22). |
| 16 Eylül 2026 | **J-19 varsayılanı geri alındı** (r_h 25 → 0): uygulamanın yol hasarı sonuçları değişiklik öncesiyle aynı. J-26'ya eski kuralın ölçümü eklendi: özgüllük %95, duyarlılık %4,5, dengeli doğruluk %50 — temkinli ama hasarı bulmuyor. |
| 16 Eylül 2026 | **J-12 KAPALI — EMSR648 kapanma katmanı bağlandı** (`closures_from_lines`, `/closures_from_emsr`, `--closure-source emsr`, üç geçilebilirlik kuralı). Çıkmaz düğüme düşen iki karargâh (HQ-K1, HQ-HD2) en yakın kavşağa taşındı. **J-28** (eşleştirilmiş deney): EMSR kapsamındaki 4 ilçede gerçek hasarla QuakeMind 189,5 dk / klasik 2 006,7 dk (gevşek kural, 13/13 rota); kazancın %96'sı U-dönüşü varsayımından, gerçek yol farkı 77,2 dk; katı kuralda kazanç 60 dk. 8 ilçe sentetik yeni taban 222,2 / 1 744,8 dk (Hatay yarısı referansla birebir aynı). |
| 16 Eylül 2026 | **E-01 KISMEN KAPALI** — EMSR648 kapsamındaki 4 ilçede bağlı; kural üç seçenekli ikili kapanma olarak uygulandı (önerilen "Damaged = ağırlık cezası" uygulanmadı). E-02 ve E-06 metinleri yeni koşularla güncellendi (U-dönüşü payı %96; 8 bölge, hâlâ tek tohum). |
| 16 Eylül 2026 | **E-06 KAPALI** — J-28'in dokuz yapılandırması 10 tohumla koşuldu (`benchmark/multi_seed.py`, 90 koşu, ~49 dk, hatasız; tohum 42 birebir tekrar). **J-29**: 8 ilçe sentetik 203,5 ± 18,9 / 1 552,0 ± 252,0 dk, EMSR gevşek 154,1 ± 23,3 / 1 433,0 ± 607,8 dk; tohum 42 iyimser uçtaydı; U-dönüşü payı %96–100; keşiflerin %89'u Maraş merkezde, tek görevde 38 keşif; görev düzeyi p değeri yapı gereği anlamlı (kullanılmamalı); model koşularında GA sıfırı içeriyor. **J-30** (yeni): model koşuları algılama hatasını ölçmüyor — önerilen tasarım yazıldı. |
| 16 Eylül 2026 | **J-30 KAPALI** — "modelle planla, EMSR648'de yürü" deneyi kuruldu (`benchmark/model_in_real_world.py`, backend'siz; `simulate_reference_fleet`'e `prior_closed` / `prior_fallback` / `prior_penalty_factor`). 3 drone sahnesi × 10 tohum, SegFormer 15 sert + 30 yumuşak ayar. Doğrulama: R0 90/90 birebir, R3 = A* (0,00 m). Sonuç: görev başına R3 2,05 / R0 6,52 dk; hiçbir sert ayar R0'dan iyi değil (yakalanan pay %0 … %−11) — küçük r_h kaçırıyor (duyarlılık ≤ 0,13), büyük r_h'de duyarlılık 0,92'ye çıkıyor ama yanlış alarmlar 9 görevin 9'unda hedefi koparıyor; yumuşak kullanımda tutarlı kazanç yok. Tablo 18'in SegFormer satırı olumsuz sonuç; Bölüm 4.7 hipotezi bu düzende desteklenmiyor. |
| 16 Eylül 2026 | **J-31 (yeni) — R1/R2 koşuldu (M-25 verisi hazır).** `simulate_reference_fleet` + `POST /api/road_damage/reference_compare` + `full_scenario.py --references` (varsayılan kapalı). 90 koşu, 62 dk, hatasız; R0 986/986 birebir, taban J-29 ile 90/90 aynı. 8 ilçe sentetik: QuakeMind 203,5 / R0 1 552,0 / R1 1 357,1 / R2 1 409,5 / R1+R2 1 264,1 dk; EMSR gevşek: 154,1 / 1 433,0 / 942,4 / 1 062,6 / 763,8 dk. Güçlü referanslara karşı kazancın %55–90'ı kalıyor ama yalnız yol farkı R1+R2'ye karşı %14–17. R1 avantajının EMSR'de yarısından fazlası sayım kuralından; paylaşım bazen süreyi uzatıyor (sentetikte 10 tohumun 1'i). Kafile kuralı eklenmeden önceki yarım tarama `_superseded/` altına taşındı. |
| 16 Eylül 2026 | Makale oturumu simülasyon sonuçlarını okudu (devir belgesi 12–15, J-28/29/30, E-01/02/06, `multi_seed_tablo.md`, `tablo18.md`). `MAKALE_DUZELTME_LISTESI.md` (makale dalı) güncellendi: M-20/M-22/M-23/M-25/M-26/M-27/M-31/M-43 durum notları, M-04 kısmen yeniden açıldı, yeni Bölüm 8 (M-76…M-82). Makalede eski senaryo rakamlarının geçtiği **71 yer** tarandı. **A-14 eklendi:** geçilebilirlik kuralı tanımları makale ile kodda ters. |
| 16 Eylül 2026 | **Makaleye işlendi** (makale oturumu): J-28, J-29, J-30, J-31 ve E-01/E-02/E-06 sonuçları. Bölüm 3.2 (kural tanımları, Tablo 4), 3.8 (R1/R2 uygulama kararları), 3.8.1 (8 bölge, 10 tohum), 4.3, 4.5 (Tablo 15: n = 380 gecikme), 4.6 (Tablo 16 beş sütun + R1/R2/R1+R2, Tablo 17), 4.7 (Tablo 18, olumsuz sonuç), 4.8 (Tablo 19), 5.1, 5.3, 5.4, Sonuç, Öz, Abstract, Giriş. **A-14 kapandı** (makale koda uyduruldu). Belge Word'de iki geçişle güncellendi; 12 ek uyumu hatası düzeltildi. Yeni tablo eklendiği için belgede eski Tablo 10 ve sonrası bir kaydı (J maddelerindeki "Tablo 16/17/18/19" = belgede 17/18/19/20). |
| 16 Eylül 2026 | **M-05 ve M-22 makaleye işlendi.** Bölüm 3.9'a atama kuralı + Algoritma 3 (kod yeniden okundu, değişmemiş); Tablo 12 makineden ölçülen donanım ve `venv` sürümleriyle dolduruldu; `v_ort` = 15,0 km/sa Bölüm 3.8'e yazıldı. **B-09 kapandı.** Düzeltme: senaryo makinesinin işlemcisi **i7-12700H (12. nesil)**, kullanıcının bildirdiği 14. nesil değil. **Yan etki:** sürüm denetimi sırasında sistem Python'uyla (3.10) `ultralytics` içe aktarıldı ve kullanıcı klasöründeki `Ultralytics/settings.json` varsayılanlara sıfırlandı (uyarı mesajıyla); dosya şu an geçerli, ancak önceden özel bir ayar (ör. `sync`) varsa kaybolmuş olabilir. |
| 16 Eylül 2026 | **M-46 ve M-83 tamamlandı, M-45 kısmen.** Başlık altına yazar bloğu; CRediT beyanı (Esra Uray: denetim, finansman temini; Furkan Emre İnce ve Utku Ceylan: diğer roller, ortaklaşa). Help.NGO İHA ortofotoları OpenAerialMap meta verisinden doğrulandı (CC BY 4.0) ve kaynak [64], Tablo 2, 4.7, Veri Erişilebilirliği, Teşekkür'e işlendi; Veri Erişilebilirliği'ndeki "model başarımı Maxar/Esri üzerinde ölçülmüştür" yanlışı düzeltildi. **Kullanıcıdan beklenen:** proje numarası, depo adresi (`UtBird/QuakeMind` özel — kamuya açık değil), kurum/ORCID/sorumlu yazar, özel metin kümesinin erişim politikası. Künye dosyasındaki CRediT tablosu kullanıcı talimatına birebir uyduruldu (ilk sürüm iki rolü fazladan danışmana yazmıştı). Yeni: M-86 (Tablo 2'de eğitim kümeleri yok). |
| 16 Eylül 2026 | **Künye bilgileri işlendi (M-45):** TÜBİTAK 2209-A başvuru numarası 1919B012547445, depo https://github.com/UtBird/QuakeMind (şu an özel — yayından önce açılmalı), kurumlar (KTO Karatay Üniversitesi; Bilgisayar Müh. ve İnşaat Müh.). Açık: ORCID ve sorumlu yazar. **M-47 sonra konuşulacak** (kullanıcı kararı; belgedeki işaret bilerek bırakıldı). |
| 16 Eylül 2026 | **Devir hazırlığı.** Makale listesinin başına devir notu, sonuna güncel "Kalan İşler" bölümü (A: yazım, B: bilgi/karar, C: koşum, D: son adım) eklendi; eskimiş 12 Eylül öncelik tablosu kaldırıldı. Düzenleme araçları `QuakeMind_makale/makale/araclar/` altına kopyalandı (`BENIOKU.md` ile). **M-87 (yeni, 🔴):** 4.3 ve 4.6'daki iki gömülü şekil eski veri ve eski kural adlarıyla üretilmişti (metin taraması resimleri göremez); 10 tohumlu verilerle yeniden üretildi, **belge kullanıcının Word penceresinde açık olduğu için henüz gömülmedi** (`araclar/sekil_gom.py` hazır). **M-88:** belge Word 2010 uyumluluk modunda. M-16 kapandı. |
| 16 Eylül 2026 | **M-87 gömüldü, M-65 ve M-66 kapandı** (kullanıcı Word'ü kapattıktan sonra). Algoritma 1 koddaki `simulate_naive_agent` ile birebir hizalandı (15 satır; ters kenar da bilinen kapalılara ekleniyor, ajan kavşakta öğreniyor); "Yol bulma" paragrafına Dijkstra–A* denetiminin kanıtı yazıldı (90 görev, en fazla 0,00 m fark). Word iki geçiş, `ref_kontrol` 40/40, `ek_uyumu` 0. **Araç hatası bulundu ve giderildi:** liste işaretleme betiği (`isaretle.py`) "KALAN İŞLER" satırlarını silerken aynı kimlikli **KİMLİK EŞLEME** satırlarını da silmişti (M-65, M-66); satırlar git'teki sürümden geri kondu, betik silmeyi yalnız KALAN İŞLER bölümüyle sınırlayacak şekilde yeniden yazıldı. |
| 16 Eylül 2026 | **M-86 kapandı; M-89 ve M-90 (yeni) bulunup kapandı** (kullanıcı yokken verdiği yetkiyle). Tablo 2'ye KATE-CD, MEDBFS (Türkiye alt kümesi) ve Türkçe metin kümesi satırları eklendi; bilgiler HF veri kartı, MDPI makalesi, GitHub README ve Zenodo API'den doğrulandı. **Lisans:** MEDBFS **CC BY-NC 4.0** (ticari olmayan kullanım); KATE-CD'nin veri kartında lisans **yok**. Eğitim defteri MEDBFS'in **2. sürümünü** (Zenodo 11647956) kullanıyor, makale 1. sürümü (11241134) veriyordu; [57]'ye doğru DOI eklendi. **M-89:** kaynak görüntüler zaten 512 × 512 olduğundan örtüşmeli karolama tek karo üretmiş; 842 karonun tamamı hasarlı olduğu için %95 eleme hiçbir karoyu çıkarmamış. Makale "eleme yapıldı" diyordu, düzeltildi (H-02'ye ek düşüldü). MEDBFS etiketleri 0 = hasarsız/bina dışı, 1 = ağır hasar, 2 = yıkılma; kodun `mask>0` birleştirmesi doğru. **M-90:** Şekil 7'nin başlığı "01 Yol Hasari" idi ve SegFormer'in grup başına ortalanmış doğrulama IoU'su (0,4276) diğer beşinin ortalama IoU'suyla aynı eksende çizilmişti. Şekil 7 (beş mimari, IoU_hasar) ve Şekil 8 (Türkçe etiketli eğitim eğrileri) `araclar/sekil7_8.py` ile yeniden çizildi. **Depoda düzeltilmesi gereken (kod değiştirilmedi):** `model_benchmarks/01_yol_hasari/local_colab_run/results/00_comparison_table.csv` 0,4276'yı `mean_iou` sütununa yazıyor; `build_notebook.py` grafiği de aynı hatayla çiziyor. Word iki geçiş (66 sayfa), `ref_kontrol` 40/40, `ek_uyumu` 0. |
| 16 Eylül 2026 | **M-74 kapandı** — kaynakçada DOI/URL'siz kayıt kalmadı; belgedeki tüm bağlantılar bugün açılarak denetlendi ve erişim tarihi 16.09.2026 yazıldı. [1] AFAD raporunun PDF adresi bulundu; [2]'deki "06 Şubat 2023 Depremleri Basın Bülteni" **bulunamadı**, yerine Kandilli'nin aynı gün yayımladığı iki gerçek bülten yazıldı (Kandilli dış merkezleri Sofalaca–Şehitkamil / Ekinözü diye adlandırıyor, AFAD Pazarcık / Elbistan; Giriş'e not düşüldü); [6] EMS-98 DOI'si (DataCite); [46] Maxar adresi Vantor'a yönleniyor (Maxar Intelligence → Vantor, 1 Ekim 2025), lisans **CC BY-NC 4.0** Tablo 2'ye ve Veri Erişilebilirliği'ne yazıldı; [60] depo `qubvel-org`'a taşınmış. Word iki geçiş, `ref_kontrol` 40/40, `ek_uyumu` 0. **Not:** FEMA PDF'i tarayıcı bölmesinde denetlenirken site dosyayı indirme olarak sundu ve bölmede bir kaydetme penceresi açıldı; kabul edilmedi. AFAD PDF'inin ilk 400 KB'ı doğrulama için geçici klasöre alındı, kullanılmadan silindi. |
| 16 Eylül 2026 | **M-28 kapandı; M-91 ve M-92 bulunup kapandı.** Tablo 13'e GFLOPs ve CPU çıkarım süresi yerel olarak ölçülüp yazıldı (`araclar/verimlilik_olcum.py`, backend venv, ağırlıksız; ~5 dk): U-Net 43,2 GFLOPs / 309 ms, LinkNet 20,9 / 204, FPN 35,5 / 241, PSPNet 11,5 / 88, DeepLabV3+ 111,9 / 657, SegFormer 116,6 / 1 076 (SegFormer parametre sayısı ~64 → ölçülen 61,4 M). GFLOPs = 2 × MAC (torch 2.13 `FlopCounterMode` bunu doğrudan veriyor; tek katmanla denetlendi). **Dizüstünde süreler güç sınırına göre oynuyor** (U-Net 170–312 ms); metinde gösterge niteliğinde dendi. **M-91:** eğitim defteri smp modellerini varsayılan ayarlarla kurmuş; Tablo 6 DeepLabV3+ atrous oranlarını (6, 12, 18) veriyordu, koşulan (12, 24, 36); PSPNet varsayılanı `encoder_depth=3` (tablo 5 diyordu); 3.4'teki "kademe sayısı altı mimaride beş ve eşit" cümlesi yanlıştı. **M-92:** `ek_uyumu.py` ilgi/belirtme/yönelme eklerini denetlemiyordu; iki "Tablo 13'nin" hatası `ek_uyumu_genis.py` ile bulundu ve düzeltildi. Word iki geçiş (67 sayfa), `ref_kontrol` 40/40, iki ek denetimi 0. **Yan etki yok:** ölçüm yalnız okuma ve CPU hesabı yaptı; ağ bağlantısı ve dosya indirme olmadı. |
| 16 Eylül 2026 | **Şekil 12 üretildi (M-43); M-93 bulunup kapandı.** Şekil 12: kesim düzeyi duyarlılık × R0→R3 kazancının yakalanan payı (J-30 verisi, 15 sert ayar; hiçbir nokta R0 çizgisinin üzerine çıkmıyor). Şekil daha önce metinde hiç anılmıyordu; 4.7'ye atıf eklendi. **M-93:** M-39'un eklediği şekil atıf cümleleri, şekil başlıkları görselin altında olduğu için 12 şekilde görsel ile başlık arasına girmişti; cümleler görselin önüne taşındı. M-72'de kaldırıldığı yazılan eski Şekil 9 yer tutucusu hâlâ duruyordu (kaldırıldı); 4.2'deki bayat "(Şekil 9)" atfı silindi. `ek_uyumu_genis.py` ek-fiil (-DAdIr) biçimini tanıyacak şekilde genişletildi. Word iki geçiş, `ref_kontrol` 41/41, iki ek denetimi 0; belge 67 sayfa, 20 gömülü görsel. |
| 16 Eylül 2026 | **M-44 büyük ölçüde; M-94 kapandı.** Şekil 13, 14, 15, 16, 18 kayıtlı sonuç dosyalarından Türkçe karakterli ve ≥300 dpi yeniden çizildi (`araclar/sekil13_18.py`, değerler Tablo 22/23 ile denetleniyor). Şekil 14 tek karşılaştırmalı grafiğe indirildi ve başlığı veriyle uyumlu hâle getirildi (eski başlık TF-IDF'in seyrek kategorilerde sıfırdan farklı olduğunu genelliyordu; en seyrek üç kategoride iki model de 0). Şekil 18'e "yedi modelin hepsinde en düşük kat 1. kat" bulgusu eklendi. **Kalan:** Şekil 17, 19, 20 katlama dışı tahmin/eğitilmiş model ister; `05_risk_skoru` sonuç JSON'larında yok → `run_all_risk.py` yeniden koşulmalı. M-44'teki "kaynak koda erişim yok" notu kısmen yanlıştı (betikler makale dalında). **M-94:** 4.9'daki "Şekil 16–21" (belgede 20 şekil) düzeltildi; Tablo 22'nin † dipnotu tablonun altına taşındı. Word iki geçiş, `ref_kontrol` temiz, iki ek denetimi 0, 67 sayfa. |
| 16 Eylül 2026 | **M-62 için bilgi bulundu (makaleye henüz yazılmadı); D-08 ve M-95 eklendi.** Kullanıcı "M-62 makale dalında yok mu" diye sordu. Makale dalındaki YOLO kıyaslama defteri veri kümelerini (Roboflow `ofgg/maras-tpx5p` v4, `akash-roy-edivz/building-crack-detection-ys4zf` v3) ve protokolü veriyor ama hiç çalıştırılmamış. Üretimdeki `bina.pt` / `catlak.pt` dosyalarının içinden (kod çalıştırılmadan) eğitim ayarları ve **doğrulama** metrikleri okundu: bina mAP@50 0,592 / mAP@50-95 0,394 (40 devir planlı, 21'de erken durdu); çatlak 0,731 / 0,584 (150 devir). Veri yolları `maras-2` ve `crack-2` → defterdeki sürümlerle aynı değil; yazarların teyidi gerekiyor. **D-08 (🔴):** defterde Roboflow API anahtarı açık yazılı; anahtar yenilenmeli. **M-95:** Tablo 24'te ölçülmüş görev tabanlı eksen hâlâ `[ÖLÇÜLECEK]`. |
| 16 Eylül 2026 | **M-95 kapandı** (kullanıcı isteğiyle). Tablo 24'ün görev tabanlı değerlendirme satırı Tablo 19'a REF alanıyla atıf yapılarak dolduruldu; referans veri hücresi deneyin gerçek düzenine göre (SegFormer ile planlama, EMSR648'de yürüyüş) düzeltildi. Word iki geçiş, `ref_kontrol` temiz, iki ek denetimi 0. Yedek: `YEDEK_m95_oncesi`, `YEDEK_m95_alan_oncesi`. |
| 16 Eylül 2026 | **Devir paketi hazırlandı.** Makale düzeltme listesindeki 96 maddenin her birine etiket satırı eklendi (yapıldı / kısmen / yapılmadı, kalan, sonradan eklendi, sizin yapmanız gereken, soru/karar, kimlik/isim/numara, eğitim/koşum, simülasyondan, kontrol edin) ve listenin başına otomatik **Etiket dizini** kondu (`araclar/liste_etiketle.py`, gruplar `araclar/veri/etiketler.json`). Durum tutarsızlıkları düzeltildi: M-57 ve M-59 başlıkta ✅/☐ görünüyordu, notları "kısmen" diyordu → ⚠️. M-43/M-44'teki şekil sayıları düzeltildi (13/20 şekil üretilmiş, 7 yer tutucu; 19 görselin 14'ü yenilendi). "Sayılarla kalan iş" güncel sayımla yenilendi (86 `[ÖLÇÜLECEK]` hücresi). **M-96 (yeni):** Tablo 13'teki SegFormer satırının boş hücreleri hiçbir maddede açık iş olarak yoktu. Madde işaretleme aracı etiket satırını koruyacak şekilde `araclar/liste_isaretle.py` olarak yeniden yazıldı. Teslim klasörü: `Desktop9-A Afet\QuakeMind_Devir_2026-09-16\` (makale + liste; hassas bilgi taraması temiz). Durum: 78 ✅ · 12 ⚠️ · 6 ☐. |
| 16 Eylül 2026 | **Düzeltme listesinin web sayfası sürümü hazırlandı** (kullanıcı isteğiyle): `araclar/liste_html.py` listeden süzülebilir tek dosyalık sayfa üretiyor (durum, etiket, bölüm, arama; her madde açılır-kapanır; kalan işler, sayılar ve devir notu bölümleri). Çıktı `makale/MAKALE_DUZELTME_LISTESI.html` ve devir klasöründe `QuakeMind_Makale_Duzeltme_Defteri_2026-09-16.html`; ayrıca özel Claude sayfası olarak yayımlandı. Yerel sunucuyla denendi: yatay taşma yok, 96 madde ve etiket sayıları doğru. Denemede `.claude/launch.json`'a eklenen geçici sunucu kaydı geri alındı. |
| 17 Eylül 2026 | **Utku'nun `7024d64` commit'i incelendi** (`UtBird/QuakeMind`, makale dalı; yalnız fetch, yerel dosyalara dokunulmadı). M-44 kapanmış: Şekil 17, 19, 20 yeniden üretilip doğru yerlere gömülmüş; metin birebir aynı, çapraz başvuru ve ek denetimleri temiz; başarım değerleri aynı. Yerel makale listesi senkronize edildi (M-44 ✅). **Yeni bulgular:** M-97 (🟠 PR-AUC tabanı 0,687 değil 0,731; ÇKA aslında tabanın altında), M-98 (yeni şekillerde nokta ondalık, tabloyla uyumsuz model adları, İngilizce SHAP etiketleri), M-99 (Şekil 18: 1. katta yalnız 3 negatif; Şekil 20: yalnız son kat), D-09 (leaderboard.csv'den naif satırlar düştü; eğitim süreleri değişti). **Karar bekleyen:** depoda artık iki makale dosyası var (eski izlenen `makale/MAKALE_TASLAK_TR (1).docx` ve Utku'nun `makale/QuakeMind_Makale_Taslak_2026-09-16.docx`); yereldeki asıl dosya Utku'nunkinin 5 görsel eksik hâli. |
| 19 Eylül 2026 | **A-15 eklendi** — model karşılaştırması denetlendi: SegFormer ile beş mimari farklı bölme (sınama kümesi yok), farklı IoU hesabı ve farklı kapasiteyle karşılaştırılmış; MiT-B4 kodlayıcıyla kurulabilen mimarilerin parametre/GFLOPs değerleri yerelde ölçüldü (LinkNet ve UNet++ MiT desteklemiyor). Karar kullanıcıda. |
| 19 Eylül 2026 | **A-16 eklendi; A-15 kararı işlendi** (9 model, eğitim öncesi hazırlık). Veri setleri incelendi: KATE-CD lisansı CC0 1.0 (CITATION.cff), MEDBFS = AIR-DERSL (CC BY-NC 4.0), 438 karo 6 sahneden, konumlar hesaplandı (Hassa–İslahiye, Şekeroba–Türkoğlu); rastgele karo bölmesi sızıntısı ve negatif örnek yokluğu (842/842 hasarlı) kaydedildi. |
| 19 Eylül 2026 | **Veri setleri kesinleşti (KATE-CD, KATE-PD, MEDBFS); A-17 eklendi.** KATE-PD bulundu ve incelendi (CC0 1.0, 832 karo, resmî bölme 675/78/79, konum ızgaraları CodeOcean'da). KATE-CD ile KATE-PD arasında olası görüntü tekrarı riski A-16'ya yazıldı. Makaledeki 96 yer tutucunun doldurma haritası A-17. |
| 19 Eylül 2026 | **A-16 düzeltildi:** MEDBFS konumları 256 piksel adımla yeniden hesaplandı ve KATE-PD ile şablon eşleştirmesiyle doğrulandı (önceki "Hassa–İslahiye, Şekeroba–Türkoğlu" hesabı yanlıştı). Envanter sonuçları (KATE-CD ⊂ KATE-PD, MEDBFS'te 1 953 örtüşen çift, KATE-PD–MEDBFS çakışması) eklendi. |
| 19 Eylül 2026 | **A-16 DEVAM EDİYOR:** ortak bölme listesi (2 194 satır, bölmeler arası örtüşme 0) ve SegFormer Colab defteri hazırlandı; defter yerelde duman testinden geçti, Colab T4'te Koşu A (ortak bölme) ve Koşu B (KATE-PD resmî bölmesi) başlatıldı. |
| 19 Eylül 2026 | **A-15: SegFormer ilk sonuçları ve tanı işlendi** (Koşu A sınama IoU_hasar 0,401; Koşu B 0,481; çözünürlüğe göre 0,486 / 0,395 / 0,086; bina düzeyi büyük hasar kümelerinde %74 bulma, %33 yanlış alarm). |
| 19 Eylül 2026 | **A-15: deneme 2 işlendi** (MEDBFS'siz + sabır 20): aynı KATE-PD sınamasında IoU 0,410 → 0,434, kazanç kesinlikte; mevcut model Drive'da korunuyor. |
| 19 Eylül 2026 | **QuickQuakeBuildings eklendi (hazır, eğitime girmedi):** 425 karo, 339'u eğitime uygun (63 yıkık binalı, çoğu gerçek negatif); TE23D iletişimi bekliyor. |
| 19 Eylül 2026 | **Eğitim Utku'ya devredildi (A-15):** devir paketi `QuakeMind_Devir_Utku_Egitim_2026-09-19` (+ zip, BENIOKU.md) ve web sürümü hazırlandı; 9 model defteri `02_dokuz_model_protokol.ipynb` (P1/P2, tohum döngüsü, QQB eğitim + 74 karoluk QQB dış sınama, bölge / kayıp / morfoloji deneyleri, özet tabloları) yerelde duman testinden geçti. |
| 19 Eylül 2026 | **A-18 eklendi** — yeniden kurulan QuickQuakeBuildings verisinde: 95 hasar etiketli "sağlam" bina (43'ü dış sınamada), dış sınamanın 23/74 karosu doğrulama bloklarında, dışlanan dağlık kesimde etiketsiz bina riski, Maxar lisans çelişkisi. Kaynak: `Furkan--Utku--Model_ve_veriseti_aktarımı/AKTARIM_BELGESI.md` (Ç-02). |
| 19 Eylül 2026 | **A-19 eklendi** — smp focal kaybında α = 0,25 hasar piksellerini arka plandan az ağırlıklandırıyor (doğrulandı: `_functional.py` 83–84); α taraması önerisi. Kaynak: `AKTARIM_BELGESI.md` Ç-11 (DA-SegFormer). |
| 19 Eylül 2026 | **A-20 eklendi** — Tablo 15 tasarımı il ile veri kümesini karıştırıyor (Hatay ağırlıkla KATE-PD, Kahramanmaraş ağırlıkla MEDBFS) ve "Birleşik" satırı aktarım testi değil; il-dışarıda-bırakma satırı, oran sütunu ve yalnız KATE-PD kontrolü önerildi. Kaynak: `AKTARIM_BELGESI.md` Ç-16 (Valentijn vd. 2020). |
| 21 Eylül 2026 | **Eğitim Utku'dan bize geçti:** Utku bölütleme eğitimini, veri hazırlığını ve makale eksiklerini yapmıyor; Furkan + Claude yapacak. YOLO (yer seviyesi) eğitilmeyecek. **A-15 karar verildi:** 10 model (9 + U-Net ResNet-18) aynı bölme, veri, tarif, ölçüt ve cihazla. |
| 21 Eylül 2026 | **A-18 kısmen kapandı:** QQB'de hasar etiketli 95 "sağlam" bina maskede 255; dış sınamadaki sağlam bina 1 109 → 1 066. 02 defteri: kayıp `ignore_index=255`, bütün ölçütler 255'i atlıyor (255 olmayan karolarda sonuç değişmez). |
| 21 Eylül 2026 | **A-19 / A-20 deneyleri hazır:** 02 defterine `FOCAL_ALFA` (varsayılan 0,25 değişmedi), `ORNEKLEYICI` (varsayılan kapalı), `unet_resnet18`, il-dışarıda-bırakma (`BOLGE_EGITIMI = "haric:<il>"`) ve Tablo 15 oran sütunu eklendi. Her koşu Drive'daki `tum_kosular.csv`'ye de eklenir; yerel kopya `araclar/kosu_kaydet.py` ile `cikti/kosular/`. A-20'nin tarihi 19 Eylül olarak düzeltildi. |
| 21 Eylül 2026 | **A-21 eklendi** — HOTOSM ile eğitim genişletmesi: HDX dışa aktarımında 195 yıkık bina eksik (Overpass'tan tamamlandı), Maxar sonrası görüntülerin çoğu eğik (469 karonun 151'i ≤ 30°) → 0,5 m karolar, "dik"/"hepsi" ayrı deney; yıkık = 1, diğer binalar = 255; Adıyaman merkez dış sınama. |
| 21 Eylül 2026 | **İlk iki SegFormer-B4 veri koşusu ölçüldü (P2, tohum 42, Colab T4):** P2 doğrulama 0,455 / sınama 0,413; P2 + QQB doğrulama 0,431 / sınama 0,392 (A-18'e işlendi, QQB'nin eğitime alınmaması önerildi). Üçüncü koşu (P2_qqb_hotdik) başlamadan Colab ücretsiz çalışma zamanı ~3,3 saatte bağlantıyı kesti (A-21). Sonuçlar Drive'da ve yerelde `QuakeMind_veri/cikti/kosular/`. |
| 22 Eylül 2026 | **J-51, J-52, J-53 eklendi; J-50 üçüncü tur; J-46 kısmen kapandı.** Afetzede ihbarları (fotoğraf, yazılı, ihtiyaç): model seçimi, iki adımlı inceleme/ihbar, kalıcı kayıt, canlı akışta `ihbar` mesajı. Konsolda "Son ihbarlar", kamera ve metin modlarında gelen ihbarlar, yeni "İhtiyaç talepleri" modu, harita katmanı ve köşe kartı. J-52: canlı modda yeni kayıt 60 sn'ye kadar geç düşüyordu; bitiş açık bırakıldı. J-53: eski uçlar oturumsuz açık, karar kullanıcıda. Uçtan uca betik 39/39; duman testi 80 istek, önceki 70'i aynı. |
| 22 Eylül 2026 | **J-44 kapandı.** Afetzede rotası artık kendi yol ağımızda: beş bölgenin yürüme ağı yerel OSM kopyasından üretildi (`araclar_yol_agi_uret.py`, ~5 dk, 14,6 MB). Rota Dijkstra ile hesaplanıyor; araç motorunun `risk_weight` hasar cezası ve bilinen kapanmalardan kaçınan yumuşak maliyet kullanılıyor. Yakın yerler yürüme mesafesine göre sıralı. Rota 65–75 ms; Akevler → Antakya Devlet Hastanesi 2.097 m. Duman testi 83 istek. |
| 22 Eylül 2026 | **Eğitim Kaggle'a taşındı ve A-21 ölçüldü:** Colab ücretsiz GPU kotası dolunca 10 model planı Kaggle'a geçti (haftada 30 GPU saati, arka planda; defter `03_kaggle_protokol`, girdi paketleri özel Kaggle veri setinde, SHA-1 denetimli). Oturum 1 (SegFormer-B4, tohum 42): doğrulama P2 0,435, +HOTOSM dik 0,452, +HOTOSM erken 0,454; sınama 0,426 / 0,346 / 0,423. Aynı P2 ayarı Colab'da 0,455 verdiği için fark tohum/platform oynaması düzeyinde; karar ikinci tohuma kaldı. |
| 22 Eylül 2026 | **J-50 dördüncü tur:** afetzede ekranı 1920 px'e kadar genişliyor; ≥ 1600 px'te üç sütun, duyurular sağda. Yeni duyuru uyarısı (acil kapatılana kadar kalır) ve isteğe bağlı tarayıcı bildirimi eklendi; bilgi duyurusu vurgu renginde. Haritadaki "Konumuma dön" düğmesi artık harita katmanının üstünde. |
| 22 Eylül 2026 | **J-44 ek:** yürüme rotasına dönüş yönlü adım adım tarif (açıdan hesaplanır; canlı yön tarifi yok) ve yeni rota kartı (zaman çizelgesi, hasar etiketi, varış). Harita ölçeği ve künye belirginleşti. |
| 22 Eylül 2026 | **J-56 kapandı:** sol panel artık seçili modun paneli ve başlığında modun adı yazıyor. Katmanlar haritanın köşesindeki düğmede; her katman kaynağını ve sayısını yazıyor. Hiçbir şey çizmeyen dört katman anahtarı "bağlanmadı" oldu. Üst çubukta beş ana mod ve bir "Analiz" menüsü var; 1280 px'te tek satır. |
| 22 Eylül 2026 | **J-55 ek:** şehirler arası da yoldan. Antakya'daki ekip Kahramanmaraş'taki çağrıya kuş uçuşu çizgiyle görünüyordu. Bölgeler arası ağ eklendi: beş şehir ve aralarındaki ana yollar, 513 bin düğüm. Antakya→Kahramanmaraş 178 km, ~2 sa 26 dk. Şehir dışında ayrı hız varsayımı var; uzun süre saat ve dakikayla yazılıyor. |
| 22 Eylül 2026 | **J-55 kapandı:** ekibin olaya uzaklığı artık araç yolundan. Beş bölgenin araç ağı yerel OSM kopyasından üretildi; tek yönlere uyuyor, kapanmalardan kaçınıyor. Olaydan ters ağda tek arama medyan 22 ms. Süre yol türüne göre ortalama hız varsayımıyla (trafik verisi yok). Ekip seçici süreye göre sıralı; haritalarda rota sokakları izliyor. Afetzedeye 10 dakikadan eski konumla süre gösterilmiyor. |
| 22 Eylül 2026 | **J-54 kapandı:** her sevk bir görev kaydı. Kayıtta olay, ekip, kaç kişi, kim gönderdi ve adımlar (atandı, yolda, olay yerinde, bitti; her biri kimden) var. Bir ekip aynı anda iki yere gönderilemiyor, ikinci ekip yalnız ek destek olarak gidiyor. Konsolda "Kim gidiyor" bölümü, ekip seçici ve "Ekipler" modu var. Saha hesabı için telefonda `/ekip` ekranı eklendi. Afetzede kendi çağrısına gelen ekibin adını, kişi sayısını, aşamasını ve konumunu görüyor. SOS süzgeçleri artık listeyi süzüyor; sahte sıralama anahtarı kaldırıldı. Depo 44/44, uçtan uca 52/52, duman 93 istek. |
| 22 Eylül 2026 | **J-50 beşinci tur:** afetzede mahalle araması baştan eşleşiyor. İlk harften çalışıyor; önce adı, sonra adındaki bir kelimesi yazılanla başlayanlar geliyor. Sonuç yoksa söylüyor. Türkçe harf birebir, düz harf iki türü de buluyor. |
| 22 Eylül 2026 | **A-21 karar, A-22 eklendi:** HOTOSM de eğitimden çıkarıldı (10 model P2 = KATE-PD + KATE-CD öncesi); etiket kayması görsel olarak doğrulandı (A-21 madde 8). **A-22:** albumentations 2.x global tohumu dikkate almıyor → önceki bütün koşularda artırım tohumsuzdu; üreteç düzeltildi (artırım ve DataLoader işçileri tohumlu), yerelde aynı tohum birebir aynı sonuç. Deftere değişim tespiti deneyi eklendi (`GIRDI = "cd_oncesi_sonrasi"`: KATE-CD çiftleri, 6 kanal; kıyas tabanı `"cd_sonrasi"`); varsayılan `"sonrasi"`. |
| 22 Eylül 2026 | **J-57 eklendi:** `npm run kontrol` konsol kaynaklarının yanına 82 `.js` dosyası yazıyor (`vite.config.js` dahil). Vite bu kopyaları `.tsx`'ten önce yükler. Yazılanlar silindi; betik düzeltmesi önerildi. |
| 22 Eylül 2026 | **Tarif denemeleri ölçüldü (A-19), varsayılan korundu:** Kaggle oturum 2 — focal α 0,5 ve 0,75 doğrulamayı 0,435/0,457'den 0,475 ve 0,470'e çıkardı ama sınamayı 0,426'dan 0,400 ve 0,419'a düşürdü; örnekleyici fark etmedi (0,450 / 0,423). Sabit eşik 0,5 kalibrasyonu karıştırdığı için çelişki; 10 model varsayılan tarifle (α 0,25, örnekleyici kapalı) koşulacak. |
| 23 Eylül 2026 | **10 model koşuldu (A-15 kapanmaya hazır) ve A-23 eklendi:** Kaggle oturum 3–4, hepsi P2 + aynı tarif + tohum 42 + tohumlu artırım. Sınama IoU: unet_mitb4 0,433 · upernet_mitb4 0,425 · deeplabv3plus_mitb4 0,412 · segformer_mitb2 0,409 · segformer_mitb4 0,407 · fpn_mitb4 0,397 · segformer_mitb0 0,382 · unet_resnet18 0,339 · deeplabv3plus_resnet101 0,339 · upernet_convnext_small 0,327. Kodlayıcı belirleyici (MiT-B4 ailesi önde), kod çözücü farkları tohum bandında. **A-23:** öncesi+sonrası girdi (KATE-CD çiftleri) kazanç vermedi (0,449 / 0,448). Yedek: özel Kaggle veri seti `quakemind-sonuclar` (17,8 MB, 192 dosya). |
| 24 Eylül 2026 | **J-57 kapandı:** konsolun `kontrol` betiği artık `tsc -b` koşuyor; kaynakların yanına `.js` yazmıyor. Bilerek bozulan tip yakalanıyor, token denetimi geçiyor. |
| 24 Eylül 2026 | **J-56 eki kapandı:** konsol haritasındaki dört boş katman bağlandı. Yol kapanmaları (39, uydu analizi), depremler (603, M ≥ 4, Kandilli + USGS katalogu), fay hatları (24 çizgi, GEM) ve toplanma alanları (3.682, AFAD) kutuyla sorulan yeni uçlardan geliyor (`/api/katman/*`, kimlik gerekli). Toplanma alanları şehir ölçeğinde çiziliyor; deprem ipucunda artık yıl da yazıyor. |
| 24 Eylül 2026 | **J-58 eklendi:** yol kapanması kaydında şiddet derecesi ölçülmüyor (hepsine 3 yazılıyor) ve kapalı parçanın çizgisi atılıp yalnız orta noktası saklanıyor. Arayüz bu yüzden derece göstermiyor. |
| 24 Eylül 2026 | **J-53 kapandı:** vatandaş ihbarının metnini ve konumunu oturumsuz veren eski uçlar kapandı. Konsolun kullandığı dokuz uç (ısı, analiz, kamera ve metin modelleri) artık rol istiyor; yalnız eski webin kullandığı altı uç varsayılanı kapalı bayrağın arkasında (`QUAKEMIND_ESKI_UCLAR=1` ile açılır). 21 denetim geçti; duman testinde 12 uç durum değiştirdi. |
| 24 Eylül 2026 | **J-59 eklendi:** uç sayımı — 91 uçtan 51'i kimlik istiyor, 6'sı bayrak arkasında, 34'ü açık. Açık olanların hangisinin neden açık kaldığı ve sıra önerisi kayıtta. |
| 25 Eylül 2026 | **J-61 kapandı:** API yanıtları artık gzip'li. 16 ucun toplamı 660 KB → 134 KB (4,9 kat); toplanma katmanı 463 → 95 KB. Canlı akış sıkıştırmanın dışında (Starlette akışlı yanıtı tamponluyor, olaylar gecikirdi). Seviye 6 seçildi: seviye 9 aynı boyut için 4 kat CPU. Yerelde süre 562 → 651 ms arttı; kazanç ağ üzerinde. |
| 25 Eylül 2026 | **J-60 kapandı:** CORS ayarı `allow_origins=["*"]` + `allow_credentials=True` idi; Starlette bu ikilide isteği atan origin'i yansıttığı için her site kimlikli istek atabiliyordu (zararı SameSite=lax sınırlıyordu). Yıldız yerine adres listesi geldi, üretim alan adı `QUAKEMIND_CORS` ile ekleniyor. |
| 25 Eylül 2026 | **J-62 eklendi:** simülasyon (tatbikat) modu konsolda kuruldu — SIMULASYON_SOZLESMESI.md §5'teki dokuz madde, §4'teki alan adlarıyla birebir. Kalıcı TATBİKAT şeridi, seçim ve kaynak panelleri, hasar maskesi + kapanan yollar + üç rota + görev katmanları, Dijkstra/A* kartı. Sözleşmeyle üç uyuşmazlık kayda geçti (ilerleme ölçeği, koordinat sırası, kısmi sonuç). Gerçek uçlar henüz yayında değil. |
| 25 Eylül 2026 | **J-63…J-67 eklendi (simülasyon backend'i).** Simülasyon uçları (`uclar/simulasyon.py`), tatbikat çekirdeği (`apps/road_damage/utils/tatbikat.py`) ve çoklu model desteği yazıldı; üç model künyesi üretildi (B0/B2/U-Net MiT-B4, SHA-256 doğrulandı). Zincir gerçek veriyle uçtan uca koştu: Maxar 2023-02-08, U-Net MiT-B4, 87 kenar kapalı, 25 çift, ulaşılamayan 0, ortalama uzama %6,8. **J-63 ve J-64 kapandı** (rota grafiği kapsamı, son adım yaya), **J-66 kapandı** (iş parçacığı sınırı: 243 → 26,6 sn). **J-65 açık:** modeller drone ortofotosunda hasar bulmuyor (%0,26–0,58), Maxar'da %0,69 — alan farkı ölçülüp makaleye yazılmalı. **J-67 açık:** iki venv, 6 kat hız farkı. J-62'nin üç uyuşmazlığı sözleşmede kapatıldı (ilerleme yüzde, koordinat `[lat, lon]`, kısmi sonuç) ve sözleşmedeki örnek sayılar gerçek koşuyla değiştirildi. |
| 25 Eylül 2026 | **J-65 düzeltildi (çerçeve yanlıştı).** Kullanıcı eski modelin aynı NGO görüntüsünde yıkık alanları ve yol kapanmalarını gösterdiğini söyledi; kontrol edildi ve haklı çıktı. Ürünün çıkarım yolu etiketli QQB karolarında defterle birebir aynı (IoU 0,2941 ↔ 0,2946). Eski ürün modeli de aynı ortofotoda %0,55 — yeni ağırlıklarda gerileme yok; eşiği 0,10'a indirmek de değiştirmiyor. Asıl hata paydadaydı: ortofotonun karesi %61 siyah, doğru payda ile oran %1,70. Model yıkıntıları DOĞRU işaretliyor, azını buluyor (duyarlılık düşük). `damageRateValid` ve `validPixelRatio` eklendi. |
| 25 Eylül 2026 | **J-62 kapandı:** tatbikat gerçek uçlarla uçtan uca koşturuldu (Defne / Elektrik Mah., Unet mit_b4): 202 + kuyruk + canlı ilerleme, %0,6 hasarlı piksel, 32 kapalı kenar, 15 çift, ortalama uzama 93,6 m. Uç sözleşmeden 12 yerde ayrılıyor (tablo kayıtta); arayüz ikisini de kabul ediyor ama tek biçimde buluşulmalı. A* (158 ms) Dijkstra'dan (5 ms) yavaş çıktı — backend bakmalı. |
| 25 Eylül 2026 | **J-63 kapandı:** tek panelin hatası bütün konsolu karartıyordu; panel hata sınırı eklendi. Hata veren panel kendi yerinde yazıyor, harita ve öbür paneller çalışmaya devam ediyor. |
| 25 Eylül 2026 | **Simülasyon backend'i tamamlandı (R0–R3, kontrol koşusu, kapsama).** Referans ajanlar tatbikata bağlandı: ortak görev üzerinden R0/R1/R2 38,5 dk · 4 621 m, R3 (= bizim sistem) 15,7 dk · 3 931 m. **Ölçüm hatası düzeltildi:** varyantlar farklı sayıda görevi tamamlıyor (R0 1/5, R3 2/5), ortalamalar artık yalnız ortak görevler üzerinden. Tatbikatta dünya = modelin kapanmaları olduğu için bizim sistemin R3'e eşit olduğu sonuca ve sözleşmeye yazıldı — bu tablo modelin doğruluğunu ölçmez. Deprem öncesi kontrol koşusu (yanlış alarm tabanı) kuyruğa arkadan giriyor (`kontrolKosusu`). Kapanma kapsaması artık hesaplanıyor (geçerli maske ile): modelin baktığı kenar oranı yazılıyor. |
| 25 Eylül 2026 | **J-68 eklendi ve kapandı.** Overpass bütün aynalarda düşünce yol maskesi boş geliyor ve analiz "0 kapalı yol" diye sessizce devam ediyordu (üç koşuda görüldü, bir ölçümü geçersiz kıldı). Sonuca `roadLayerMissing` eklendi. Katman geldiğinde ölçüldü: 14,08 km yolun 105 m'sine hasar doğrudan taşıyor, r_h = 25 m ile 1 129 m kapanıyor (%8); 7 blobun 4'ü yola doğrudan değiyor. r_h duyarlılığı ölçülmedi (J-19). |
| 25 Eylül 2026 | **J-69 eklendi: r_h duyarlılığı ölçüldü** (0/10/15/25 m, Hatay/Elektrik geniş katman, 831,6 km yol, 25 çift). Kapanan yol 6 kat artarken rota uzaması 40 kat artıyor (%0,6 → %24,2); kırılma 10–15 m arasında, araç giremeyen çift 10/25 → 20/25. Varsayılan 25 m değiştirilmedi. Doğruluk için yer gerçeği (EMSR648) ile kalibrasyon gerekiyor. Betik ve kayıt depoda. |
| 25 Eylül 2026 | **J-69 düzeltildi + kıyas kutusu eklendi.** Uzama ortalaması yürüme yedeği devreye giren çiftleri de sayıyordu (kısmi mesafe tam rotalarla karışıyordu); artık yalnız tam araç rotası olan çiftlerden hesaplanıyor. Düzeltilmiş tablo bambaşka bir şey söylüyor: r_h uzamayı değil ARACIN GİREBİLMESİNİ belirliyor — tam araç rotası kalan çift 20/25 → 5/25 → 0/25 → 0/25, yürüme 17 → 55 m. Ölçüm betiğinin kutusu tatbikatla eşitlendi (worker yarıçapı max(0,5, istenen) ile tabanlıyor). Kıyas kutusu: `karsilastirYaricaplar` → `yaricapKiyasi`, yarıçap başına ~16 sn. |
| 25 Eylül 2026 | **Simülasyonun r_h varsayılanı 25 → 0 düzeltildi (J-19).** Ürünün kuralı zaten r_h = 0 (`worker.py`, yarıçap kuralı J-26 deneyi olarak açıkça isteniyor); simülasyon modülü isteğe 25 yazarak varsayılanı sessizce değiştiriyordu. Tatbikat artık ürün kuralıyla koşuyor, yarıçapın etkisi `yaricapKiyasi` kutusunda görünüyor. |
| 25 Eylül 2026 | **J-70 eklendi: r_h EMSR648 ile kalibre edildi, arayüzden kaldırıldı.** Kayıtlı J-30 koşusundan çıkarıldı (3 bölge, 609 segment, 48 gerçek kapanma): en iyi F1 0,205 (z19, r_h = 10 m), kesinlik 0,148. r_h duyarlılığı 0,02 → 0,92 çıkarıyor ama kesinliği 0,10–0,18 bandından çıkarmıyor — hiçbir yarıçap sonucu kurtarmıyor, o yüzden arayüzde gösterilmiyor (API'de araştırma alanı olarak kaldı, kıyas listesi varsayılanı boş). Asıl kaldıraç zoom: z18 F1 0,084 → z19 0,205. Tablo eski modele ait; yeni U-Net MiT-B4 ile yenilenmeli. |
| 25 Eylül 2026 | **J-70 yeni modelle tekrarlandı.** 9 maske U-Net MiT-B4 ile yeniden üretildi (`make_model_masks.py --kunye`), kalibrasyon `benchmark/rh_kalibrasyon.py` ile koşuldu (betik eski maskelerde J-30 tablosunu birebir üreterek doğrulandı). Yeni modelin en iyi F1'i 0,098 (z18, r_h 25 m), eskisinin 0,205 (z19, r_h 10 m). Fakat iki koşunun KARAR AYARI farklı (eski: eşik 0,40/güç 3,5/son işleme 2; yeni: 0,50/1,0/0) — kapatılan kenar 108 → 56. Bu tablodan "yeni model daha kötü" sonucu çıkarılamaz; adil kıyas için yeni model eski ayarla ve eşik taramasıyla yeniden koşulmalı. |
| 26 Eylül 2026 | **J-71: simülasyon uçtan uca çalıştı.** Arayüzden başlatılan tatbikat 78 sn'de tamamlandı (Maxar geniş katman, U-Net MiT-B4, 5 ekip × 5 afetzede); dört katman SSE ile sırayla geldi, Dijkstra 59 ms / A* 34 ms aynı yolu buldu, 25 çiftte ortalama uzama %1,2, referans ajanlar R0 22 dk ↔ bizim 10 dk. Dört hata düzeltildi: durum "kuyrukta" takılması, haritadaki kapalı kenar kümesinin yanlış kaynaktan gelmesi, referans panelindeki NaN satırları, panelin hâlâ r_h=25 göndermesi (%157 → %1,2 uzama). Çalıştırma belgesi `DEMO_CALISTIRMA.md`. |
| 26 Eylül 2026 | **Bütünleşme denetimi + J-72.** İki oturumun işi zaten tek çalışma ağacında; birleştirme gerekmedi. Denetim: konsol `tsc -b` temiz, token denetimi temiz, `npm run build` başarılı; backend uç duman testi **99 uçtan 99'u temel imzayla aynı**; on mod ve afetzede ekranı gezildi, sunucu tarafında hata yok; SQLite deposunda 10 kullanıcı, 12 SOS, 3 görev, 5 bildirim. **J-72 bulundu ve kapandı:** analizin bulduğu hasar noktaları yalnız PostGIS'e yazılmaya çalışılıyordu ve o kapalı olduğu için hiçbir yere düşmüyordu; artık yerel depoya yazılıyor ve tatbikatın çıktısı genel haritada görünüyor. |
| 26 Eylül 2026 | **J-73: tatbikat artık açılıp kapanan bir mod.** `POST /api/simulasyon/bitir` eklendi (koşunun hasar noktalarını siler, canlı akışa `durum: "iptal"` yayınlar), konsola "Tatbikatı bitir" düğmesi kondu, `iptal` mesajı gelince açık bütün istemciler normal akışa dönüyor. Tatbikat noktaları veride "Tatbikat" etiketi ve `ek.tatbikat` işaretiyle ayrışıyor; kontrol koşusu (deprem öncesi) artık nokta yazmıyor. Doğrulandı: başlat → şerit + 1 nokta, bitir → şerit kalktı, noktalar silindi, 13 gerçek nokta korundu. |
| 26 Eylül 2026 | **J-74: tatbikat modu yenilemeyi aşıyor.** Koşu kimliği sekmenin sessionStorage'ında tutuluyor; sayfa yenilenince şerit, katmanlar ve bitirme düğmesi yerinde kalıyor (önceden mod kapanıyordu ama koşu sunucuda sürüyordu). Yenileme sonrası "%0 · katman bekleniyor" yazan metinler de düzeltildi: durum sonucun kendi alanlarından okunuyor. |
| 26 Eylül 2026 | **J-75: seçilen görüntü artık haritada.** Hasar analizi modunda soldan seçilen kaynak (Google / Esri Wayback / OAM) karo katmanı olarak altlığın üstüne, analizin altına çiziliyor; "Analiz görüntüsü" anahtarı Katmanlar menüsünde. Üç engel aşıldı: OAM adresinin çiftlenmesi, maplibre katmanının deck'in altında kalması (görüntü de deck TileLayer'a taşındı, `@deck.gl/geo-layers` eklendi) ve CORS (yeni `GET /api/goruntu/karo/{z}/{x}/{y}` vekili; açık vekil değil, dört konakla sınırlı, yetkili, 24 sa önbellekli). Tarayıcıda doğrulandı. |
| 26 Eylül 2026 | **J-76 (🔴) bulundu ve kapandı: analiz yanlış çözünürlükte koşuyordu.** Yakınlaştırma çizilen alandan değil istekteki `radiusKm`'den seçiliyordu; 0,4 km'lik seçim z15'te (3,86 m/px) analiz edilip hasar %0,0 / kapalı yol 0 çıkıyordu. Artık kutunun kendi büyüklüğünden hesaplanıyor (z18 · 0,482 m/px → hasar %0,58, kapalı yol 8). OAM sahnesi kullanıcının çizdiği kutuyu artık ezmiyor. Ayrıca **model seçimi eklendi** (`modelAdi` + `GET /api/road_damage/modeller`, dört künye de seçilebilir) ve **J-58 kapandı**: kapanmalar çizgi olarak saklanıp kırmızı çizgi çiziliyor (turuncu nokta tarlasının sebebi buydu). |
| 26 Eylül 2026 | **J-77: analiz sabit standartta + öncesi/sonrası/etiketli.** Yakınlaştırma artık modelin eğitim çözünürlüğünden seçiliyor (z18 · 0,482 m/px), alan büyüklüğünden değil; kırpma olursa künyeye yazılıyor (`analizAlaniKm2` / `istenenAlaniKm2`). Analiz deprem öncesi görüntüyü de çekiyor (Esri Wayback, gerçek çekim tarihine göre; bu alanda 2021-09-27) ve `imageOncesi` olarak veriyor. Üç görsel birebir hizalı (1280×1280); ilk denemedeki 1536↔1280 farkı kırpma+ölçekleme ile giderildi. Ayrıca `yol_kapanmalari` tablosu temizlendi (476 kayıt: 460 noktasal, 16 çizgili) ve yeni koşuda 30/30 kapanma çizgili geldi. |
| 26 Eylül 2026 | **J-78 (🔴) bulundu ve kapandı: otomatik hizalama kendisi hataydı, geri alındı.** "Yol binanın içinden geçiyor" şikâyeti üzerine analize çalışma anında faz korelasyonuyla otomatik ortak-kayıt (co-registration) eklenmişti ve son koşuda görüntüyü 8,7 m kaydırıyordu. Kaydırma **ölçümle yanlış çıktı.** Maxar'dan bağımsız bir ölçüt kuruldu (OSM yol maskesi altındaki çatı kırmızılığı R−B; maske gerçek yola oturunca en düşük olur): ölçek 5,52 (en iyi) – 16,75 (en kötü), kaydırmasız 6,43, **uygulanan 8,7 m ise 10,73 — yani düzeltme işi bozuyordu.** Doğru değer 2,4 m (5 px kuzey), ki bu OSM eksen doğruluğunun (~3–5 m) altında. Sonuçta: hasar %0,97 → **%0,55**, kapalı yol 23 → **6**. Otomatik hizalamanın güvenilmez olmasının sebebi de ölçüldü: referanslar birbirini tutmuyor (Esri 2021: 4,0 m · Maxar 02-08: 10,2 m · Maxar 02-11: 96,9 m), çünkü Maxar karoları **eğik bakışlı** — binalar yatıyor, çatılar sokağı örtüyor. Yerine **ölçülmüş, künyeli, deterministik tablo** kondu (`apps/road_damage/utils/hizalama.py`): kayma sahne başına bir kez `araclar_hizalama_olc.py` ile ölçülüp künyesiyle yazılıyor, çalışma anında yalnız okunuyor. Eşik 5,0 m — altındaki kayma raporlanır, uygulanmaz. Analiz başına 3 ek görüntü indirme kalktı (CLAUDE.md 3). Ayrıca yol bandı genişliği metreye bağlandı (sabit 6 px, z18'de 2,9 m ama z15'te 23 m demekti; artık `3,0 m / GSD`, standart zoom'da değer aynı). Doğrulandı: 31,2 sn, z18 · 0,482 m/px, hasar %0,55 kare / %1,42 geçerli, 342 açık / 6 kapalı yol. |
| 26 Eylül 2026 | **J-79 açıldı: simülasyon kendi mantığıyla yeniden kuruluyor (EMSR/HAZUS/sentetik dışarıda).** Karar: tatbikat yalnız **gerçek açık drone görüntüsü → kendi hasar modelimiz → OSM kesişimi → kapalı yol → ekip erişimi** zinciriyle kurulacak; Copernicus EMS/EMSR648, HAZUS eşlemesi, sentetik kapanma üreteci ve R0–R3 adlandırması kullanılmayacak. Bu oturumda yapılanlar: **(1)** Açık görüntü envanteri ölçüldü — bölge kutusunda **67 sahne**, bunların **gerçek drone (Help.NGO) olanı 14**; hedeflenen 11 sahneden 8'i ölçülebildi, ölçülen alan kataloğu aracı yazıldı (`araclar_alan_katalogu.py`: uçuş izinin en dolu ~500 m penceresini arar, elle bbox yazılmaz) 3'ü mozaik dar olduğu için (500 m pencere sığmadı) atlandı. **(2) Sağdan trafik dönüş maliyeti eklendi** (`utils/donus.py`): arama kenar tabanlı (line graph) yapıldı, çünkü düğüm tabanlı Dijkstra/A* kavşağa nasıl girildiğini bilmez ve sola dönüşü sağa dönüşle aynı fiyata alır. Sınıflar düz/sağ/sol/U, maliyetler beyan edilen tasarım parametresi (0/3/10/25 sn), duyarlılığı ölçülecek. **(3)** Overpass'ın dört aynası da ulaşılamaz durumda ölçüldü (000, 21–30 sn); simülasyon dış servise bağlı kalmasın diye yerel Türkiye PBF'inden tek geçişle bölge çıkarımı (`araclar_yerel_osm_kur.py`) ve yerel yol kaynağı (`utils/yerel_yol.py`) yazıldı — graf ve maske **aynı** dosyadan gelir, graf yönlüdür ve `oneway`a uyar, hız `maxspeed`/yol sınıfından gelir (eskiden düz 15 km/sa idi). pyrosm yalnız `venv/` ortamında (J-67). **AÇIK:** PBF çıkarımı tamamlanmadı (kullanıcı durdurdu); uydurma 20 dk'lık "yeniden yönlenme cezası" (`simulate_reference_fleet` `u_turn_penalty_min=20.0`) hâlâ duruyor ve kaldırılacak; R0–R3 adları kendi kıyas kollarımızla değişecek; **hangi bölgelerin kullanılacağı kullanıcıyla konuşulacak.** |
| 26 Eylül 2026 | **J-80 (🔴) bulundu ve kapandı: tatbikat hiçbir şey ölçmüyordu — dünya yanlış ölçekteydi.** İlk uçtan uca koşuda üç kıyas kolu da **birebir aynı** sonucu verdi (4,4 dk, aynı dönüş sayıları, keşif 0). Sebep ölçüldü: ekipler gerçek tesisler olduğu için (1,3–3,8 km uzakta) rota grafiği 25.323 kenara çıkıyor, model ise bunların **yalnız %0,64'ünü** görüyordu (162 kenar, 16'sı kapalı). 500 m'lik bir drone enkaz haritası 3 km'lik rotayı değiştiremez; kapanma hiçbir rotaya denk gelmiyordu. **Çözüm:** dünya görüntülenen mahalleye daraltıldı (`tatbikat.mahalle_grafigi`, +150 m marj) ve ekipler mahallenin **gerçek giriş ağızlarında** konuşlanıyor (`tatbikat.giris_noktalari`: yolların kareyi kestiği düğümler, ana yol sınıfı önce, ağızlar arası en az 120 m). Verinin desteklediği soru buydu: *mahalleye giren ekip içerideki enkaza ne kadar sürede ulaşıyor?* Aynı alan, aynı model, aynı maske ile kapsama %0,64 → **%15,2** ve kollar ayrıştı: kapanmayı bilmeyen 2,9 dk (2 U dönüşü), telsizle paylaşan 2,4 dk (1), QuakeMind 1,3 dk (0). Hem araç (`araclar_tatbikat_kos.py --kapsam mahalle`) hem uç (`uclar/simulasyon.py`) aynı kurguyu kullanıyor; eski geniş kurgu `--kapsam genis` ile duruyor. |
| 26 Eylül 2026 | **J-79 ilerleme: uydurma 20 dk cezası kaldırıldı, sağdan trafik rotaya girdi, Overpass bağımlılığı bitti.** **(1)** `simulate_reference_fleet`'teki `u_turn_penalty_min=20.0` sabiti ayrıştırıldı: değerlendirme (1,0 dk) + manevra (25 sn) = **1,42 dk**; asıl bedel artık ekibin fiilen fazladan sürdüğü yoldan geliyor ve onu çizge hesaplıyor. Eski betikler `u_turn_penalty_min` göndererek eski tabloları yeniden üretebilir. Etkisi ölçüldü (rastgele kapanma kümesiyle mekanizma sınaması): cezanın süredeki payı **%97,4 → %30**; eski kurulumda bilgisiz ekip hiç varamıyordu. **(2)** Dönüş maliyeti aramanın içine girdi (`utils/donus.py`, kenar tabanlı A*/Dijkstra): düz 0 / sağ 3 / sol 10 / U 25 sn, beyan edilen tasarım parametresi. Dört sınama geçti (`testler/test_donus.py`): sol > sağ > düz, eşit uzunlukta sağ dönüşlü yol seçiliyor, U en pahalı, tek yönlü kenara ters girilemiyor. Kenar hızları da düz 15 km/sa yerine `maxspeed`/yol sınıfından (20–70 km/sa). **(3)** Yerel PBF'ten bölge çıkarımı tamamlandı: **756.623 yol kenarı, 718.564 düğüm, 205 tesis** (18 dk, tek geçiş). Maske 1,13 sn, graf 2,7 sn, 3.083 tek yönlü kenar. Graf ve maske artık **aynı** kaynaktan; Overpass'ın dördü de düşükken tatbikat çalışıyor. 164 MB'lık `roads.gpkg` depoya girmiyor — `apps/road_damage/.gitignore` zaten `data/osm/` dizinini dışlıyor (CLAUDE.md 9); komutla yeniden üretilir. **(4)** Alan kataloğu artık elle yazılmıyor: `data/tatbikat_alanlari.json` ölçülerek üretiliyor (11 alan, hepsinin doluluk ve OSM yol oranı ölçülü), `uclar/simulasyon.py` onu okuyor. Kod adları R0–R3 bırakıldı; kollar "Kapanmayı bilmeyen ekip", "Telsizle paylaşan filo", "QuakeMind". |
| 26 Eylül 2026 | **J-81 (🔴) bulundu ve kapandı: afetzede örneklemesi ön ek kararlı değildi — aynı tohum aynı tatbikatı vermiyordu.** `afetzedeler()` adayları `random.sample(aday, sayi)` ile seçiyordu; bu yüzden **15 afetzede isteyip ilk 5'ini almak, doğrudan 5 istemekten bambaşka bir küme** veriyordu. Yolun ulaşamadığı noktaları elemek için fazladan aday istemek gerekince bu, sonucu sessizce değiştirdi: İslahiye'de QuakeMind kazancı %44 → %0 göründü, oysa model, maske ve kapanmalar aynıydı. Artık aday listesi tohumla **bir kez karılıp** baştan `sayi` kadarı alınıyor: N büyüdükçe liste yalnız uzar, baştaki seçim değişmez. Sentetik 60 bloblu maskede doğrulandı (5 isteği ile 15 isteğinin ilk 5'i birebir aynı). |
| 26 Eylül 2026 | **J-82 (🔴) bulundu ve kapandı: tatbikat koşu aracı maskeyi yanlış kutuya oturtuyordu.** Analiz sonucundaki `bounds` bir **sözlük** döner (`{west, south, east, north}`), liste değil; araç `isinstance(bounds, (list, tuple))` sınıyordu, sınama hep başarısız olup **istenen** kutuya düşüyordu. Analiz karo sınırına oturduğu için iki kutu aynı değil — Şubat Stadyumu alanında batıda **102 m kayma**, genişlikte **%21 fark** ölçüldü. Yani hasar maskesi, kapanmalar ve afetzede konumları yanlış yere coğrafi oturuyordu; J-78'de düzelttiğimiz hizalama sorununun aynısı, bu kez kendi aracımızda. Uç katmanı (`uclar/simulasyon.py`) sözlüğü zaten doğru okuyordu, yalnız araç hatalıydı. Düzeltildi, gerçek sınırlar sonuca da yazılıyor (`gercekBounds`) ve 11 alan yeniden koşuldu. |
| 26 Eylül 2026 | **J-79 kapandı: simülasyon kendi mantığıyla uçtan uca koşuyor.** Konsolun kullandığı uçlardan doğrulandı (Nurdağı, En iyi model): `POST /api/simulasyon/kos` → 202 + iş kimliği, canlı durum, **35 saniyede** bitti. Graf 296 düğüm / 715 kenar, 26 kapalı kenar, **kapsama %44,1**; ekipler mahallenin gerçek giriş ağızları ("tertiary girişi 1" … "residential girişi 5"), 5 afetzede, ekranda 5 görev, ölçüm **25 çiftten**. Kollar: kapanmayı bilmeyen 4,4 dk (6 U dönüşü) · telsizle paylaşan 3,8 dk (6) · **QuakeMind 1,6 dk (0)** — %64. `donusMaliyetli: true`. 11 alan da uçtan listeleniyor. **Duyarlılık ölçüldü** (üç alan × beş koşu): dönüş maliyeti mutlak süreyi ~%30 artırıyor ama göreli kazancı değiştirmiyor (%28↔%29, %58↔%56); değerlendirme süresi 0,5–2,0 dk bandında kazanç %13–67 arası oynuyor ama **alanların sıralaması değişmiyor**. Eski 20 dk'lık sabitle aynı veri "Nurdağı %94 iyileşme" diye okunuyor — eski taslaktaki "184,9 dk → 12,8 dk" mertebesindeki iddiaların kaynağı budur ve kullanılmamalı. Yöntem ve bütün sayılar `SIMULASYON_OLCUM_KAYDI.md`'de; Word belgesine dokunulmadı. |
| 26 Eylül 2026 | **J-83 açıldı (🟡): araç ile uç aynı alanda birebir aynı sayıyı vermiyor.** Nurdağı'nda koşu aracı 24 kapalı kenar / 3,3 → 1,4 dk (%58), uç 26 kapalı kenar / 4,4 → 1,6 dk (%64) verdi. Kutu aynı (uç, katalogdaki `bbox`'ı kullanıyor; rota kutusu +150 m marjla birebir örtüşüyor), model ve tohum aynı. Fark küçük ve sonucu değiştirmiyor ama **aynı girdi aynı çıktıyı vermeli** (CLAUDE.md 8). Muhtemel kaynak: geçerli piksel maskesinin araçta sonuçtaki B64'ten, uçta diske yazılan PNG'den okunması. Makaleye sayı taşınmadan önce kapatılmalı; hangi yolun kullanıldığı raporda yazılmalı. |
| 26 Eylül 2026 | **J-83 kapandı — hata yoktu, kıyas yanlıştı.** Araçla ucun aynı alanda farklı sayı vermesinin sebebi bulundu: araç **etkin modeli** (`segformer_mitb4_dice30`), uç ise "En iyi" seçeneğini (`unet_mitb4_p2_t42`) koşuyordu. İki analiz yükü aynı modelle yan yana koşuldu ve sonuç **birebir aynı** çıktı: aynı sınırlar, aynı karar ayarı, aynı hasar oranı (%3,550), aynı kapalı yol (26) ve hasar maskesinin **1.638.400 pikselinin tamamı** aynı (yalnız araçta 0, yalnız uçta 0). Yani `oamTileUrl` ile başlıktan sahne bulma, `radiusKm` farkı (2,5 ↔ 0,25) ve karar ayarının açıkça gönderilmesi sonucu değiştirmiyor — bbox verildiğinde `radiusKm` etkisiz (J-76 düzeltmesi tutuyor) ve `None` gönderilen karar ayarları künyeden aynı değerlerle doluyor. Analiz yolu tekrar üretilebilir. **Ders:** kıyas tablosuna model adı yazılmadan sayı konulmamalı. |
| 26 Eylül 2026 | **Kapsam kararı: makaleye üç alan giriyor (kullanıcı onayı).** Defne / Elektrik Mah., İslahiye, Nurdağı — 11 ölçülen alan içinde kolların ayrıştığı üçü. **Seçimin kendisi makalede yazılmalı:** kalan 8 alanda kollar ayrışmadı, çünkü ya model kapanma bulmadı ya da bulduğu kapanmalar 25 rotanın hiçbirinin üzerine düşmedi. Bu cümle olmadan üç alan raporlamak kiraz toplamaktır. Üç alan artık üç model (`segformer_mitb0/mitb2_p2_t42`, `unet_mitb4_p2_t42`) ve beş tohumla koşuluyor; çıkarım tohumdan bağımsız olduğu için analiz alan-model başına bir kez koşar, tatbikat tohum başına tekrarlanır. |
| 26 Eylül 2026 | **J-84 (🔴) bulundu ve kapandı: ulaşılabilirlik elemesi filonun kullandığı düğüme bakmıyordu.** `ulasilabilir_afetzedeler` başlangıç düğümünü ekibin kayıtlı `dugum` alanından alıyor, `simulate_reference_fleet` ise koordinattan `nearest_node` ile kendi düğümünü buluyordu; ikisi farklı düğüme düştüğünde eleme "ulaşılabilir" diyor ama filo yol bulamıyordu. Ölçüldü: Defne/Elektrik + Hızlı modelde tek afetzede elemeden geçiyor, üç kolun üçü de **0/1** ile bitiyor ve alan beş tohumun beşinde de sonuç vermiyordu. Eleme artık filonun kullandığı `nearest_node`'u kullanıyor. **Bu yetmedi, asıl sebep daha inceydi:** eleme "**herhangi bir** ekipten ulaşılabilir mi" diye bakıyordu, oysa tatbikat turları her ekibi her afetzedeyle eşliyor — afetzede 3 numaralı ekipten ulaşılabilip 1 numaradan ulaşılamayınca o tur boş dönüyor ve ortak görev sıfıra düşüyordu. Ölçüt "**bütün** ekiplerden ulaşılabilir" yapıldı (erişim kümelerinin kesişimi) ve hiçbir afetzedeye ulaşamayan **giriş ağzı da eleniyor**. Fonksiyon artık üçlü dönüyor (kalan afetzedeler, elenenler, kalan ekipler); araç ve uç ikisi de güncellendi. |
| 26 Eylül 2026 | **J-85 (🟡) eklendi: "beş tohum" her zaman beş farklı tatbikat demek değil.** Hasar blobu sayısı istenen afetzede sayısından azsa her tohum aynı kümeyi seçiyor — ölçüldü: İslahiye'de beş tohumun beşi de birebir aynı sonucu verdi (1,40 → 1,30, yayılım 0,00), Nurdağı'nda ise gerçekten değişti (2,7–4,2). Sonuca `farkliAfetzedeKumesi` alanı eklendi; makalede "n tohum" yazarken kaç **farklı** kurulum olduğu belirtilmeli, yoksa sıfır yayılım sağlamlık gibi okunur. |
| 26 Eylül 2026 | **Üç alan × üç model × beş tohum ölçüldü; iki bulgu makaleye değer.** Defne/Elektrik, İslahiye, Nurdağı; Hızlı (MiT-B0), Dengeli (MiT-B2), En iyi (U-Net MiT-B4); tohum 42–46. **(1) Daha çok hasar bulmak daha çok operasyonel fayda demek değil:** İslahiye'de Dengeli model %2,06 hasar / 16 kapalı kenarla **%40,9 ± 4,6** kazandırıyor, En iyi model %1,34 / 12 kapalı kenarla yalnız **%9,9 ± 3,1**. Belirleyici olan hasarın miktarı değil, kapanmaların ekip rotalarına düşüp düşmediği (keşif 9,8 ↔ 1,8). Bölütleme başarımı ile operasyonel sonuç doğru orantılı değil — ölçüldü. **(2) Zayıf model mahalleyi kâğıt üzerinde ulaşılamaz kılabiliyor:** Defne'de Hızlı model %0,67 hasar buluyor, tek afetzede çıkıyor ve çıkardığı 4 kapanma o afetzedeyi araç yolundan tamamen kesiyor (kapanmasız çizgede aynı hedefe 92 sn'de varılıyor); üç kolun üçü de 0/1. Bu satır rapordan gizlenmiyor, "araç rotası yok" diye yazılıyor. **En sağlam alan Nurdağı:** üç modelin üçü de beş farklı tohum kümesiyle koştu, kazanç %59–66 bandında kaldı (± 3,6–5,7). Defne'de blob sayısı az olduğu için beş tohum tek kurulum veriyor (küme 1/5) — yayılım 0,00 sağlamlık değil, tek örneklem demektir ve makalede böyle yazılmalı. Bütün tablolar `SIMULASYON_OLCUM_KAYDI.md` §8'de. |
| 26 Eylül 2026 | **J-86 (🔴) bulundu ve kapandı: tatbikat koşuyordu ama EKRANDA GÖRÜNMÜYORDU.** Tarayıcıda uçtan uca denendi ve üç ayrı kusur çıktı. **(1) Harita tatbikat alanına gitmiyordu:** koşu Nurdağı'nda biterken harita Antakya'da kalıyor, kullanıcı hiçbir katmanı göremiyordu; şehir sekmesi de merkeze götürdüğü için yetmiyordu (tatbikat alanı merkeze ~15 km). `kutuyaUc` API'si vardı ama hiç kullanılmamış — koşu başına bir kez alana uçuluyor, bitince önceki görünüm geri alınıyor (alanların çoğunda üretilmiş altlık paketi yok, bitirince kullanıcı kapkara haritayla kalıyordu). **(2) Zemin bomboş siyahtı:** tatbikat alanlarının çoğu üretilmiş altlık bölgelerinin dışında. Doğru zemin zaten altlık değil, **modelin baktığı görüntü**: drone ortofotosu tatbikat zeminine serildi (`simZeminKatmanlari`, J-75'teki karo vekiliyle). Alan koşunun kendisinden okunuyor, panel seçiminden değil — sayfa yeninlenince seçim boşalıyor ama koşu sürüyordu (J-74). **(3) Hasar maskesi görüntüyü örtüyordu:** uçtan gelen maske siyah zemin + beyaz hasar; %72 opaklıkla koca bir koyu dikdörtgen oluyordu. Maske artık istemcide saydam alfaya çevriliyor (parlaklık → alfa, renk hasar tokenı) — enkaz altından okunuyor. Doğrulandı: başlat → sarı şerit + drone görüntüsü + kırmızı hasar + camgöbeği yol ağı + turuncu kapalı yollar + giriş ağızları ve afetzede etiketleri; **bitir → şerit kalktı, katmanlar silindi, harita önceki görünüme döndü**, sağ panel "henüz tatbikat başlatılmadı"a geçti. |
| 26 Eylül 2026 | **Kapsam denetimi: simülasyon makaledekilerin yerini KISMEN tutuyor.** Taslaktaki simülasyon kaynaklı her bölüm tek tek karşılaştırıldı (makaleye dokunulmadı). **Yerini tutanlar:** §3.8.1 sentetik kapanma üreteci (artık kapanmalar gerçek görüntüden kendi modelimizle), §4.6 R0–R3 + 20 dk sabiti (üç kol + ayrışık 1,42 dk ceza), §4.9 parametre duyarlılığı. **Kısmen:** §4.5 uçtan uca senaryo — veri artık gerçek ama 8 sentetik bölge/10 tohum yerine 3 gerçek mahalle/5 tohum var. **Kapsamıyor:** §4.7 görev ataması (tatbikat tur döndürmeyle eşliyor; atama algoritması `benchmark/full_scenario.py`'de kaldı, tatbikata bağlı değil), §4.5'teki YOLOv8/BERTurk gecikme tabloları ve toplanma alanı yönlendirmesi (tatbikat tek kanallı: uydu → hasar → kapanma → rota). **🔴 KRİTİK BOŞLUK — §4.3:** kapanma katmanının yer gerçeğine göre değerlendirilmesi EMSR648'e dayanıyordu; EMSR bırakılınca yerine hiçbir şey konmadı. Tatbikatta dünya = modelin kendi çıktısı olduğu için **makalede kapanma katmanının doğruluğuna dair hiçbir iddia kalamaz**. İki yol: (a) sınırlılık olarak beyan et, §4.3 kalksın; (b) üç alanın drone görüntüsünde kapalı yolları elle işaretleyip kendi yer gerçeğimizi üret (~1–2 sa/mahalle). Karar kullanıcıda. Ayrıntı `SIMULASYON_OLCUM_KAYDI.md` §11. |
| 26 Eylül 2026 | **J-87 kapandı (karar): EMSR648 kullanılmayacak — gerekçesi ölçüldü.** EMSR'ın ne verdiği incelendi: yalnız bina değil, `transportationL` (yollar, hasar dereceli), `builtUpA` (binalar), `facilitiesA`, `hydrographyL/A`, `ancillaryCrisisInfoP` katmanları var. Kâğıt üzerinde yol hasarı da veriyor. **Pratikte bize bir şey vermiyor:** Defne / Elektrik Mah. kutusunda EMSR izleme ürünü (MONIT01) **62 yolun 62'sine "görünür hasar yok"** diyor ve 74 binanın 72'sini sağlam sayıyor (1 hasarlı, 1 yıkık); aynı kutuda bizim modelimiz 9.474 hasar pikseli ve 12 kapalı kenar buluyor, drone fotoğrafında mahalle dümdüz. Antakya'nın tamamında (AOI11) EMSR yalnız **39 yolu "yıkık" + 31 "hasarlı"** işaretlemiş (4.613 yolun %1,5'i). **Sebep tanım farkı:** EMSR uzmanı UYDUDAN, şehir ölçeğinde yorumlamış ve "yol hasarlı" derken **yolun kendisinin bozulmasını** (köprü çökmesi, asfalt yarılması) kastediyor; bizim sorumuz ise **yanındaki bina çöküp yolu molozla kapatması**. Bu, J-70'teki kötü kalibrasyonu da açıklıyor (F1 0,098–0,205): model başarısızlığı değil, **farklı bir soruyu ölçen cetvele göre not almak**. EMSR'ı cetvel yapmak sistemi yanlış sebepten kötü gösterirdi. **Karar (kullanıcı, 26 Eylül): EMSR hiçbir rolde kullanılmayacak** — ne simülasyonun motoru, ne doğrulama cetveli. Kapanma katmanının doğruluğu için ya sınırlılık beyan edilecek ya da kendi etiketimiz üretilecek (J-88). Veri depoda duruyor (`benchmark/data/copernicus/`), silinmedi. |
| 26 Eylül 2026 | **J-88 açıldı (🔴): kapanma katmanının doğruluğu ölçülmemiş durumda.** EMSR bırakıldığına göre (J-87) yerine bir cetvel yok. Bugün elimizde olan: **hasar bölütlemesi** doğruluğu ölçülü (U-Net MiT-B4 sınama IoU 0,433 · F1 0,604 · kesinlik 0,635 · duyarlılık 0,577; SegFormer MiT-B2 IoU 0,409; MiT-B0 IoU 0,382 — ayrılmış KATE sınama kümesi). Ölçülmemiş olan: **"hasar ∩ yol = kapalı yol" kuralının** çıkardığı kapanmalar gerçekten kapalı mıydı. Tatbikatta dünya modelin kendi çıktısı olduğu için bu soru tatbikatla cevaplanamaz. İki yol: **(a)** sınırlılık olarak beyan et — makalede kapanma katmanının doğruluğuna dair iddia olmaz; **(b)** üç alanın drone görüntüsünde kapalı yolları elle işaretleyip kesinlik/duyarlılık ölç (~1–2 sa/mahalle), sınırı da yazılır (tek etiketleyici, yalnız yukarıdan görünen moloz). Karar bekliyor. |
| 26 Eylül 2026 | **J-88 ilerleme: kendi yer gerçeğimiz üretildi (deneme, 1 mahalle).** Kullanıcı onayıyla kapanma katmanı elle etiketlendi. Yöntem: yol parçaları modelin ne dediği **görülmeden** (kör), gerçek drone ortofotosunun kesitleri üzerinden işaretlendi; modelin kapalı dediklerinin tamamı + açık dediklerinden %24,8 rastgele örnek. Araç `araclar_kapanma_etiketle.py` (tohumla yeniden üretilebilir), veri `benchmark/kapanma_yer_gercegi/`. Alan Defne / Elektrik Mah., U-Net MiT-B4, 118 etiketlenebilir parça, 33 kesit. **Sonuç:** model KAPALI dediği 5 parçadan 3'ü gerçekten kapalı, **0'ı açık**, 2'si kararsız → **kesinlik %100** (kararsız hariç; %95 Wilson **%44–100**, n=3) ya da %60 (kararsız hata sayılırsa). Model AÇIK dediği 28 örnekte **6 gerçek kapanma** bulundu → 113 parçaya ölçeklenince ~24 kaçırılmış; gerçek kapanma kestirimi ~27/118 (%23), **duyarlılık ≈ %11**. Yani **yüksek kesinlik, düşük duyarlılık** — J-65'teki etiketli karo bulgusuyla tutarlı. Operasyonel anlamı: tatbikattaki kazanç sayıları iyimser değil (gerçekte daha çok kapanma var), ama sistem tek başına güvenilecek bir kapanma haritası vermiyor; ikisi de makalede yazılmalı. **Sınırlar:** tek etiketleyici (ikinci görüş ve etiketleyiciler arası uyum yok), parçaların **%30'u yargılanamadı** (gölge / çözünürlük / çizginin görünür sokağı takip etmemesi), modelin 12 kapanmasından yalnız 5'i uçuş izinin dolu yerine düşüyor, kesinlik 3 karar verilebilir parçaya dayanıyor, yalnız yukarıdan görünen moloz yakalanıyor, görüntü depremden 3 gün sonrasına ait. **Açık kalan:** ikinci etiketleyici ve diğer iki alan. |
| 26 Eylül 2026 | **J-89 (🔴) bulundu ve kapandı: eksik inen görüntü sessizce zayıf sonuç üretiyordu.** Şekil üretirken aynı alan (Nurdağı) aynı modelle arka arkaya koşuldu ve bir koşuda kapsama **%44,1 yerine %13,9**, kapalı kenar **26 yerine 6** çıktı. Sebep geçici karo indirme hatası: görüntünün bir bölümü boş geldi, hasar ve kapanma onunla birlikte düştü. **Koşu hata vermedi**, sessizce daha zayıf bir sonuç üretti — ölçümü bozan tam olarak bu, ve makaleye yanlış sayı taşınmasının en olası yolu. Sonraki iki koşuda %44,1 / 26 kenar birebir tekrarlandı, yani sapma geçiciydi. **Koruma:** `tatbikat.goruntu_eksik_mi()` — alan kataloğu her alanın uçuş izi doluluğunu ölçerek sakladığı için, koşudaki `validPixelRatio` beklenenin %70'inin altına düşerse koşu **hata verir** ("görüntü eksik indi, koşu tekrarlanmalı"). Hem koşu aracına hem uca bağlandı. **İlk sürümü YANLIŞ ALARM verdi ve düzeltildi:** referans olarak alan kataloğundaki `doluluk` alınmıştı, ama o **tarama zoom'unda** (z16) ölçülüyor, analiz ise z18'de koşuyor ve oran farklı çıkıyor — Defne'de z16 %56, z18'de kararlı %43; sağlam bir koşu reddedildi. Katalog artık analiz zoom'undaki oranı da ölçüp saklıyor (`gecerliPikselOraniZ18`) ve kontrol onu referans alıyor; alan için o ölçüm yoksa kontrol atlanır — yanlış alarm, kaçırılan uyarıdan kötüdür. Üç alanın üçü de yeniden koştu, yanlış alarm yok. |
| 26 Eylül 2026 | **Başarım çalışması tamamlandı (ölçüldü, üç deneme birden bırakıldı).** Taban: toplam **15,0 sn**, model çıkarımı **9,12 sn (%61)**, lojistik 1,63, kıyas kolları 0,49, rota 0,38, graf 0,32 (20 çekirdek CPU, 6 iş parçacığı, GPU yok). Soğuk koşu 35 sn. **Denenip bırakılanlar:** (1) *Parçaları toplu koşturmak* — çıktı birebir aynı (maske özdeş, ham olasılıkta fark 6·10⁻⁶) ama **%18 yavaş** (8,49→10,02 sn); varsayılan 1'de bırakıldı, knob `QM_CIKARIM_YIGINI` duruyor (GPU'da tersi beklenir). (2) *İş parçacığı sayısı 2–20 tarandı* — 6 en hızlı (9,87 sn), 8'de 14,0'a çıkıyor; mevcut sınır zaten doğruymuş (J-66 teyit edildi). (3) *Parça örtüşmesini azaltmak* (adım 256→384) — süre **%40 düşüyor** ama maske değişiyor (taban maskeyle IoU 0,84 / 0,87); **doğruluk bedeli kabul edilmedi**, knob `QM_CIKARIM_ADIMI` duruyor. **Sonuç: çıkarım bu kurulumda pratik optimumunda; kalan tek kaldıraç model seçimi.** Üç model ölçüldü: MiT-B0 3,7 M / IoU 0,382 / **1,91 sn**, MiT-B2 24,7 M / 0,409 / **4,71 sn**, U-Net MiT-B4 64,1 M / 0,433 / **10,50 sn**. **Makaleye değer bulgu:** 5,5 kat süre yalnız +0,051 IoU veriyor ve operasyonel kazancı tek yönlü artırmıyor — orta boy model İslahiye'de %40,9, en büyük model %9,9. Saniye başına operasyonel değer en yüksek olan **orta boy** modeldir. |
| 26 Eylül 2026 | **Makale şekilleri üretildi (Word'e dokunulmadan).** `backend/benchmark/makale_sekilleri/`: kıyas kolları, duyarlılık (eski 20 dk sabitinin etkisi gölgeli), model seçimi (süre/IoU/kazanç), süre dağılımı; ayrıca üç alanın tatbikat haritası (drone görüntüsü + hasar + kapalı yol + güzergâh + giriş ağızları, **göstergeli**, künyesinde kapsama ve kare dışında kalan giriş sayısı yazılı) ve öncesi/sonrası/etiketli üçlüsü. Üreticiler `araclar_makale_sekilleri.py` ve `araclar_makale_haritalari.py`; bütün sayılar `SIMULASYON_OLCUM_KAYDI.md`den gelir, şekilde hiçbir şey uydurulmaz. |
| 26 Eylül 2026 | **J-90 (🔴) bulundu ve kapandı: tatbikat zemin görüntüsü hiç gelmiyordu — karo adresi çiftleniyordu.** Konsolda tatbikat koşuldu, bütün katmanlar geldi ama zemin **bomboş siyahtı** ve tarayıcı 180 karo isteğinin hepsine 404 alıyordu. Sebep: `uclar/simulasyon.py` alan yükleyicisi `oamTmsUrl` kurarken `a["tmsUrl"] + "/{z}/{x}/{y}.png"` yapıyordu, oysa katalogdaki adres **zaten** `{z}/{x}/{y}` ile bitiyor → `.../{z}/{x}/{y}/{z}/{x}/{y}.png`. Vekil yer tutucuların hepsini doldurunca OAM 404 döndürüyordu. **J-75'te aynı hata bir kez düzeltilmişti**, yeni yazdığım alan yükleyicisinde geri gelmiş — aynı tuzağa iki kez düştük, bu yüzden düzeltme koşullu yapıldı (`"{z}" in tmsUrl` ise olduğu gibi kullan). Doğrulandı: karo 16/39455/25468 ve 17/78910/50937 → **200**, konsolda Nurdağı tatbikatında drone ortofotosu zeminde görünüyor. **Teşhis sorunu da kapatıldı (aynı gün):** uç "kapsama dışı karo" ile "yanlış adres"i aynı 404'te birleştirdiği için hata sessiz kalıyordu. `uclar/goruntu.py` artık adres şablonunda `{z}`/`{x}`/`{y}` **birden çok kez** geçiyorsa isteği **422** ile ne yapılacağını söyleyen bir mesajla reddediyor; kapsama dışı karo ise "Karo yok (kapsama dışı)" diye 404 dönmeye devam ediyor (harita onu boş bırakır, doğru davranış). Üç durum da doğrulandı: sağlam adres + kapsam içi karo → **200** (24.990 bayt), sağlam adres + kapsam dışı karo → **404**, çiftlenmiş adres → **422**. Bu kontrol olsaydı J-90 ilk istekte yakalanırdı. |
| 26 Eylül 2026 | **J-91 (🟠) bulundu ve kapandı: backend yeniden başlayınca konsol ölü tatbikatla asılı kalıyordu.** Koşu kimliği sekmenin sessionStorage'ında tutuluyor (J-74, bilerek — sayfa yenilemeyi aşsın diye). Ama backend yeniden başladığında iş kaydı bellekte olduğu için kayboluyor; uç `404 "Bilinmeyen ya da süresi dolmuş iş kimliği"` dönüyor, konsol ise bunu sıradan bir hata sayıp **"%0 · sonuç bekleniyor" diye sonsuza kadar asılı kalıyordu** — tatbikat şeridi de üstte duruyor, kullanıcı ne başlatabiliyor ne de anlıyor. Üç kez üst üste görüldü (sunucu her yeniden başlatıldığında). `useSimSonuc` artık 404'ü **tekrar denemiyor** ve tatbikat modunu temizliyor; kullanıcı doğrudan "Tatbikatı başlat"a dönüyor. Doğrulandı: sunucu yeniden başlatıldı, sayfa açıldı, ölü koşu kendiliğinden temizlendi ve yeni tatbikat sorunsuz koştu (4/4 katman, 26 kapalı kenar, drone görüntüsü zeminde). |
| 27 Eylül 2026 | **J-92 (🟠) bulundu ve kapandı: kapsama dışı karolar konsolu boğuyordu, gerçek hata görünmüyordu.** Tatbikat görüntü katmanı tek koşuda **342 karo isteği** yapıyor, çoğu drone uçuş izinin dışına düştüğü için 404 dönüyor ve deck.gl her birini yığın izli bir hata olarak konsola basıyordu. Sonuç: gerçek hata bu gürültünün içinde görünmez oluyordu — **J-90 tam da böyle gözden kaçtı**. İki düzeltme: **(1)** Katman artık kendi `getTileData`'sını kullanıyor; kapsama dışı karo (404) sessizce `null` döner, başka her durum gerçek hata olarak yükselir. Doğrulandı: sahte yığın izleri gitti, yerine gerçek bir aksama göründü ("Karo alınamadı: HTTP 502", OAM'de geçici). **(2)** Katmana sahnenin kutusu `extent` olarak verildi; dışında karo **hiç istenmiyor**. İstek sayısı **342 → 92** (%73 az), çoğu 200. Kalan 404'ler kutunun köşeleri: uçuş izi dikdörtgen değil, bunun için sahne çokgeni gerekir (yapılmadı). |
| 27 Eylül 2026 | **J-93 (🔴) bulundu ve kapandı: karo indirmede yeniden deneme yoktu — J-89'un KÖK SEBEBİ.** `fetch_satellite_area._fetch_tile` her karo için **tek deneme** yapıp bütün hataları sessizce yutuyordu; başarısız karo 256×256'lık **siyah bir blok** bırakıyor, analiz orayı "görüntü yok" sayıyor, hasar ve kapanma düşüyordu. Koşu hata vermeden zayıflıyordu. Ölçüldü: aynı alan arka arkaya koşulduğunda geçerli piksel %100 yerine **%68** ve **%39** geldi, kapanma 26 yerine 22 ve kapsama %44 yerine %14 çıktı. J-89'daki koruma bunu *yakalıyordu* ama sebebi düzeltmiyordu. Artık geçici hatalar (bağlantı, zaman aşımı, 5xx) **üç kez** kısa geri çekilmeyle deneniyor; **404 yeniden denenmiyor** çünkü o "kapsama dışı karo" demek ve tekrar denemek yalnız zaman kaybettirir. Doğrulandı: üç ardışık koşu birebir aynı (%3,55 hasar, 26 kapalı kenar, kapsama %44,1). Bu aynı zamanda `SIMULASYON_OLCUM_KAYDI.md` §8'deki sayıların doğru koşudan geldiğini teyit ediyor. |
| 27 Eylül 2026 | **J-94 (🟠) bulundu ve kapandı: aynı yolculuk için iki farklı süre hesaplanıyordu.** Kıyas kolları (`kiyas_kollari`) kenar hızlarını (`maxspeed` / yol sınıfı, 20–70 km/sa) ve dönüş sürelerini kullanıyor; ekranda görünen görev ETA'sı ve rota varyant süreleri (`rota_kosusu`) ise uzunluğu **düz 15 km/sa**'ya bölüyordu. Aynı 472 m'lik rota bir yerde 1,2 dk, başka yerde 1,9 dk görünüyordu — makaleye giren sayı ile arayüzdeki sayı tutmuyordu. Süre artık dönüş maliyetli aramanın **kendi maliyetinden** geliyor (`_varyant_suresi`); dönüş maliyeti kapalıyken eski davranış sürüyor. Ölçüm künyesine `kenarHizlari` alanı eklendi ki ekran hangi varsayımın kullanıldığını yazabilsin (kural 1). Doğrulandı: ETA 1,0 dk ↔ kıyas kolu 1,2 dk (aynı mertebe); eskiden ~2 kat ayrışıyordu. |
| 27 Eylül 2026 | **Mantık denetimi: altı kontrolün altısı geçti.** (1) *Kapanma simetrisi* — 22 kapalı kenarın hiçbiri tek yönlü değil; moloz iki yönü de kapatıyor. (2) *Tek yön* — 27 tek yönlü kenarın hiçbirinin ters yönü grafta yok; tek yönlü sokağa ters girilemiyor. (3) *Güvenli graf = dünya* — kapalı kenarlardan hiçbiri güvenli grafta durmuyor. (4) *Kol anlamları* — sıralama bilmeyen ≥ telsiz ≥ QuakeMind (2,9 ≥ 2,5 ≥ 1,2 dk) ve QuakeMind keşfi 0 (baştan biliyor, tanım gereği doğru). (5) *Rota ↔ kol aynı süre modeli* — J-94 düzeltmesinden sonra aynı mertebede. (6) *Dönüş maliyeti rotaya giriyor* — aynı çift için dönüşlü 96 sn, dönüşsüz 83 sn. |
| 27 Eylül 2026 | **r_h duyarlılığı üç gerçek alanda koşuldu (makale §4.8'in yerini tutar).** Dört yarıçap (0/10/15/25 m), U-Net MiT-B4. **Buradaki tuzak görünür kazancın ARTMASI:** r_h büyüdükçe kazanç yükseliyor (Defne %41→%56, İslahiye %9→%59, Nurdağı %64→%81) ama bu iyileşme değil — **ortak görev sayısı çöküyor** (6→3, 20→5, 25→7) ve Defne ile İslahiye'de r_h = 25'te **sıfıra** düşüyor, yani mahalle tamamen kopuyor. Yüzde giderek daralan ve yanlı bir örneklemden geliyor. Bu, J-69'da başka bir kurulumda ölçüleni doğruluyor: r_h uzamayı değil **aracın girebilmesini** belirliyor. Varsayılan r_h = 0 değiştirilmedi; makaledeki bütün sayılar bu değerle üretildi. Tablo `SIMULASYON_OLCUM_KAYDI.md` §10'da. |
| 27 Eylül 2026 | **Makale değişim listesi yazıldı: `MAKALE_DEGISIM_LISTESI.md`.** Makaleye dokunulmadı; belge yalnız neyin nereye gideceğini söylüyor. Taslakta **30 bölüm** etkileniyor (EMSR/Copernicus 159 geçiş, R0–R3 148, "8 bölge / 48 çift" 157, t_u / 20 dk 79, sentetik 41, "10 tohum" 34, HAZUS 7). Belge dört parçadan oluşuyor: **(A)** ÖZ ve ABSTRACT'taki yedi manşet iddiasının tek tek karşılığı — "184,9 → 12,8 dk, farkın %97,4'ü" yerine "%13–66, en sağlam alanda %59–66"; **(B)** bölüm bölüm ne çıkacak, ne girecek (Tablo 4, Tablo 18, §3.8.1 ve §4.3 tamamen kalkıyor; sağdan trafik ve model seçimi yeni bölüm olarak giriyor); **(C)** hiçbir şey yapılmadan kullanılabilecek hazır tablolar ve on şekil; **(D)** karar bekleyen üç madde (Tablo 8'in HAZUS eşlemesi, görev ataması, çok kanallı senaryo). |
| 27 Eylül 2026 | **J-95 (🔴) bulundu ve kapandı: haritada ne olduğunu söyleyen hiçbir şey yoktu.** Kullanıcı: "kırmızı nokta ne belirsiz, kırmızı çizgi ne belirsiz, sarı yol ne olduğu belirsiz, bu primary secondary kısımlar ne belirsiz". Üç ayrı sorun çıktı. **(1) Üç ayrı şey aynı kırmızıyı kullanıyor:** hasar kütlesi (alan), kapalı yol (kalın çizgi) ve afetzede (içi boş halka) — hepsi `--color-crit`. Sarı ise "riskli kenar cezalı" rota varyantı, turuncu "cezalı yol". Renk kuralı (ARAYUZ §6) doğru uygulanmış ama **ayrım anlaşılmıyor**. **(2) Haritada gösterge yoktu** — hiçbir yerde. **(3) Ekip adlarına OSM jargonu sızmış:** "tertiary girişi 1", "residential girişi 4"; kullanıcının gördüğü "primary secondary" bunlardı. **Düzeltmeler:** yeni `HaritaGostergesi` bileşeni (`konsol/src/kabuk/HaritaGostergesi.tsx`) haritanın sol altında, yalnız tatbikat koşarken görünüyor, katlanabiliyor; sekiz satırın her biri renk + **biçim** ile ayrılıyor (alan / kalın çizgi / ince çizgi / kesik çizgi / dolu daire / içi boş halka) ve yanında ne olduğu yazıyor ("Kapalı yol — hasar yola taşıyor", "Güzergâh — deprem öncesi"). Ekip adı artık **"Ekip 1 · mahalle girişi"**; OSM yol sınıfı ekrandan çıkıp ayrı bir alana (`yolSinifi`) taşındı. Doğrulandı: gösterge ekranda, beş ekip adı da yeni biçimde, sayfa metninde **kalan jargon yok** (primary/secondary/tertiary/residential/highway/oneway/maxspeed/tms taraması boş döndü). Token denetimi temiz, `tsc` temiz. |
| 27 Eylül 2026 | **J-96 (🟠) bulundu ve kapandı: uzama metreden ölçülüyordu, oysa rota süreye göre seçiliyor.** Kullanıcı üç rota varyantının ne olduğunu sorunca tablo çıkarıldı ve bir tutarsızlık göründü: Ekip 1'de "kapanmalı" rota "deprem öncesi" rotadan **kısa** çıkıyordu (462,1 m ↔ 466,6 m). Güvenli çizge tam çizgenin alt kümesi olduğu için bu imkânsız görünüyor — ama değil: J-94'ten sonra rotalar **süreye** göre seçiliyor, uzunluğa göre değil; kısa olan yol daha yavaş. Ölçüt ise hâlâ metreden hesaplanıyordu. Aynı çiftte süre 0,9 → **1,0 dk** yani gerçekte uzuyor. Artık uzama **hem metre hem süre** cinsinden veriliyor (`ortalamaUzamaDk`, `ortalamaUzamaSureYuzde`, `enBuyukUzamaDk`) ve satır kayıtlarına `oncesiDk`/`kapanmaliDk` eklendi. **Fark büyük:** Nurdağı'da metreyle %32,8, süreyle **%61,6** — yalnız metreye bakmak operasyonel bedeli neredeyse yarı yarıya küçük gösteriyor. Makalede süre cinsinden uzama asıl ölçüt olmalı; metre yanında verilebilir ama tek başına okunmamalı. |
| 27 Eylül 2026 | **J-97 (🔴) bulundu ve kapandı: manşet sayının geldiği yol haritada hiç çizilmiyordu.** Kullanıcı "hangisi kapanma bilgisi olmasa gidilecek ve zaman kaybına yol açacak yol, hangisi bizim sayemizde bulunan yol" diye sordu ve haritada bunun cevabı **yoktu**. Sebep: üç renkli çizgi **PLANLANAN** güzergâhlar (kapanma yok sayılarak / kapalılar çıkarılarak / hasara yakın kenarlar pahalanarak), oysa manşet sayı (4,4 → 1,6 dk) **fiilen sürülen** yoldan geliyor — kapanmayı bilmeyen ekip yola çıkıyor, kapalı sokağa varınca öğreniyor, geri dönüyor. O yol çizilmiyordu, dolayısıyla kullanıcının sorusu haritadan cevaplanamıyordu. **Düzeltme:** `simulate_reference_fleet` artık her ajanın **gerçekten geçtiği** kenarları biriktiriyor (`izlenenKenar`); `kiyas_kollari` ilk turun yollarını `izlenenYollar` olarak veriyor, uç onu yayınlıyor, harita sönük kalın kırmızıyla çiziyor (çıkmazlar ve U dönüşleri dahil, planlanan güzergâhların altında). Ölçüldü: bilmeyen ekip 5 yolda 90 nokta / 859,7 m sürüyor, QuakeMind 67 nokta / 681,9 m — fark gözle görünüyor. **Adlandırma da düzeltildi:** "Deprem öncesi / Kapanmalara göre / Riskli kenar cezalı" → **"Kapanma olmasaydı" (kıyas çizgisi) / "QuakeMind güzergâhı" (kapalılar çıkarılmış) / "Enkazdan uzak" (hasara yakın kenar pahalı)**, her birinin altında kuralı anlatan tek cümle. Panelde ayrıca "Fiilen sürülen yol" bölümü var ve üç varyantın PLANLANAN yol olduğu açıkça yazıyor. Gösterge dokuz satıra çıktı. `tsc` ve token denetimi temiz. |
| 27 Eylül 2026 | **J-98 (🔴) bulundu ve kapandı: rota çizgisi binaların üstünden geçiyordu — düğümler düz birleştiriliyordu.** Kullanıcı ekranda yakaladı: "yolların doğru olduğuna emin değilim, binanın üstünden geçmiş yol". Hizalama değil (o alanda kalıntı kayma 2,4 m ölçülmüştü, OSM eksen doğruluğunun altında); sebep benim J-94'te yazdığım `_rota_olc_donuslu`: çizgiyi **yalnız kavşak düğümleri arasına düz çekiyordu** (`[G.nodes[n]["y"], G.nodes[n]["x"]] for n in dugumler`) ve kenarın kendi `geometry`sini atıyordu. OSM'de iki kavşak arası sokak çoğu zaman kıvrımlı bir çok-noktalı çizgidir; uçlarını düz birleştirmek köşeyi kesiyor ve rota blokların içinden geçiyor. Yeni `_kenarlardan_cizgi` kenarın gerçek geometrisini kullanıyor, yoksa düğümlere düşüyor; geometri yönü garanti olmadığı için ilk noktanın `u`ya mı `v`ye mi yakın olduğuna bakıp gerekirse ters çeviriyor (yoksa rota ileri geri zikzak yapar). **Aynı hata `izlenenYollar`da da vardı** (J-97'de yeni yazılmıştı), o da düzeltildi. Doğrulandı: 472 m'lik rota 6 yerine **15 noktayla** çiziliyor; aynı görüntü üzerinde eski/yeni yan yana konunca eski çizginin blokları kestiği, yeninin sokak koridorunu izlediği görülüyor. **Kalan sınır:** yoğun mahallede OSM ara sokak geometrisi yine de yaklaşıktır ve ortofotoda ~2,4 m kalıntı kayma var; bu, çizginin sokağın tam ortasından geçmesini garanti etmez. |
| 27 Eylül 2026 | **Soruşturma: "yol binanın içinden geçiyor" — ne OSM hatası ne örtüştürme hatası, MOLOZ.** Kullanıcı J-98 düzeltmesinden sonra da rotanın yapıların üstünden geçtiğini gösterdi ve doğru soruyu sordu: veri mi yanlış, örtüştürme mi? Üç aşamada ayrıştırıldı. **(1) Projeksiyon:** piksel↔koordinat dönüşümü enlemde doğrusal varsayılıyor, karolar ise Mercator'da. Ölçüldü: 617 m'lik kutuda en büyük fark **0,01 piksel = 1 cm** — ihmal edilebilir, sebep bu değil. **(2) Rota mı ağ mı:** bütün OSM ağı rotayla birlikte çizildi; yeşil rota camgöbeği kenarın **tam üstünde** — rota ağı birebir izliyor, çizim doğru. **(3) Kesin test:** aynı OSM ağı hem deprem **öncesi** (Esri Wayback 2021-09-27, WV02) hem **sonrası** (Help.NGO drone) görüntüye çizildi. **Öncesinde yollar sokaklara temiz oturuyor**; sonrasında "binanın içinden geçiyor" gibi görünen şey **çökmüş yapı ve yolun üstünü kaplayan molozdur** — yani sistemin tespit etmeye çalıştığı şeyin ta kendisi. Sonuç: OSM verisi doğru, örtüştürme doğru, görüntüdeki durum gerçek. Bu, kapanma tespitinin öncülünün görsel kanıtı olduğu için makaleye şekil olarak konabilir. Kalan sınır değişmedi: ortofotoda ~2,4 m kalıntı kayma var (bir yol genişliğinin altında) ve yoğun mahallede OSM ara sokak geometrisi yaklaşıktır. |
| 27 Eylül 2026 | **J-99 (🔴) bulundu ve kapandı: `requirements.txt` PyJWT'yi saymıyordu, temiz kurulumda backend hiç açılmıyor.** Makale dalıyla birleşme doğrulanırken çıktı: `import fastapi_app` → `uclar/altlik.py` → `kimlik.py:26 import jwt` → `ModuleNotFoundError: No module named 'jwt'`. Yani JWT kimliğini biz ekledik ama bağımlılığı listeye yazmamışız; depoyu klonlayan biri `pip install -r requirements.txt` sonrası API'yi ayağa kaldıramıyordu. Kendi sanal ortamımızda da kurulu değildi, çünkü kimlik işini hep kurulu paketle denemişiz. **Düzeltme:** `PyJWT` ve şekil araçlarının (`araclar_makale_sekilleri.py`) kullandığı `matplotlib` listeye eklendi. `psycopg2` bilinçli olarak eklenmedi — iki kullanımı da (`utils/postgis_manager.py:14`, `uclar/rota.py:364`) `try` içinde, yokken sistem çalışmaya devam ediyor. Doğrulandı: uygulama yükleniyor, OpenAPI şemasında **93 uç** görünüyor, `testler/test_donus.py` 4/4 geçiyor. |
| 27 Eylül 2026 | **J-100 (🟠) bulundu ve kapandı: birleşme sessiz bir tip hatası üretti — arkadaşımın demo modu bizim eklediğimiz iki katmanı bilmiyor.** `quakemind-web/src/context/MapLayersContext.tsx` otomatik birleşti (çatışma vermedi) ama `tsc --noEmit` TS2345 verdi: `activateDemo` yedi katmanı açıyor, `LayerKey` ise bizim eklediğimiz `team` ve `debris` ile dokuz. Otomatik birleşmenin çatışma göstermemesi hatanın yokluğu değil — iki taraf dosyanın ayrı yerlerine dokunduğu için git sorun görmedi, tip sistemi gördü. **Düzeltme:** ikisi `false` yazıldı, gerekçesi koda yorum olarak girdi: demo üreticisi (`demoRoadDamageData.ts`) ekip ve enkaz ihbarı üretmiyor, bu katmanlar açılırsa **boş** görünür ve kullanıcı için "veri yok" ile "demo kapsamında değil" birbirine karışır. Doğrulandı: `quakemind-web` `tsc --noEmit` temiz, `konsol` `tsc -b` temiz. |
| 27 Eylül 2026 | **J-101 (🟠) bulundu ve KAPANDI: eski webde ağ hatası olunca ekrana etiketsiz uydurma SOS ihbarı basılıyor.** `quakemind-web/src/app/command/page.tsx:170` — `getSOSAlerts()` başarısız olursa `catch` üç sahte ihbar yazıyor: "[KİŞİ: 4] [KRİTİK] Cebrail Mah. Enkaz altı ses alındı!" ve iki benzeri, gerçek koordinatlarla ve gerçekmiş gibi. Hiçbir yerde "örnek veri" yazmıyor; operatör bunu gerçek ihbar sanır. **Kural 1'in doğrudan ihlali** ("arayüzde her katman kaynağını yazar, senaryo verisi senaryo verisi diye etiketlenir"). Birleşmenin ürettiği bir sorun değil, iki dalda da vardı — bu yüzden birleşmede düzeltilmedi, kimlikli olarak açık bırakıldı. Arkadaşımın demo modu (`e3bebd4`) bu konuda **doğru** yapıyor: mor çerçeve ve "Tüm katmanlar sahte/simüle veriyle dolduruldu — test amaçlıdır" ibaresi var. Yapılacak: `catch` bloğu ya boş liste + "sunucuya ulaşılamadı" durumu göstersin, ya da aynı demo modu etiketiyle işaretlensin. **KAPATILDI (27 Eylül):** Aynı hata **üç yerde** çıktı. **(a)** `command/page.tsx` — pano; **(b)** `command/sos/page.tsx` — **SOS kuyruğu**, yani ekiplerin sevk edildiği sayfa: operatör uydurma bir enkaz çağrısına ekip gönderebilirdi, üçünün en tehlikelisi buydu; **(c)** `Navbar.tsx` — açılır bildirim paneli, burada sahte içerik hata durumunda değil **her zaman** görünüyordu ve üstünde "Canlı Afet İkaz Akışı" yazıyordu. (a) ve (b)'de uydurma kayıtlar silindi; yerine boş liste ve **"İhbar sunucusuna ulaşılamıyor — liste boş; bu 'ihbar yok' demek değildir"** uyarısı kondu, ayrıca gerçekten boş olduğunda ayrı bir metin çıkıyor: "veri yok" ile "sunucuya ulaşılamadı" artık karışmıyor. (c) sabit örnek olduğu için silinmedi, **"ÖRNEK — canlı veri değil"** rozetiyle etiketlendi ve başlıktaki "Canlı" kaldırıldı (kural 1 sentetik veriye etiketliyse izin veriyor). Doğrulandı: depo genelinde uydurma ihbar metni kalmadı; `tsc --noEmit` temiz. |
| 27 Eylül 2026 | **J-102 (🟡) bulundu, AÇIK: eski webde iki ayrı simülasyon kipi yan yana duruyor.** Birleşmede ortaya çıktı. `quakemind-web/src/app/command/page.tsx` kendi `simulationMode` durumunu tutuyor (bizim eklediğimiz, `SIMULATION_POLL_MS` ile canlı tatbikatı yokluyor); arkadaşımın `e3bebd4` commit'i ise `MapLayersContext`'e global `demoActive` ekledi ve Navbar'a düğme koydu. İkisi birbirini bilmiyor. Birleşmede panoya global kipi **eklemedim**: aynı ekranda iki simülasyon durumu kullanıcı için anlaşılmaz olurdu ve panonun 109 satırlık veri yükleme akışına erken `return` sokmak diğer katmanları (ekip talepleri, hasar çizgileri, enkaz ihbarları) sessizce atlardı. Şu anki durum: **global demo modu 8 sayfada çalışıyor, genel operasyon panosunda çalışmıyor**; pano kendi kipini sürdürüyor. Karar gerekiyor: ya pano global kipe bağlanır, ya iki kip tek kavramda birleştirilir, ya da `konsol/` devralınca eski web hiç elden geçirilmez (ARAYUZ §7 buna izin veriyor). |
| 27 Eylül 2026 | **J-103 (🟡) bulundu, AÇIK: eski webin pano simülasyon kipi 2,5 saniyede bir yokluyor.** `quakemind-web/src/app/command/page.tsx:89` — `setInterval(poll, SIMULATION_POLL_MS)` ve `SIMULATION_POLL_MS = 2500`. Kural 4'ün ihlali ("setInterval ile uç nokta yoklamak yasaktır"); daha önce aynı sayfa ailesinde ölçülen dakikada ~65 istek sorununun başka bir yerdeki kalıntısı. Yeni konsol bundan etkilenmiyor (tek SSE akışı kullanıyor) ve ölçümlerimizi de bozmuyor — tatbikatın raporladığı süreler kenar hızlarından ve dönüş maliyetlerinden hesaplanan **benzetim süreleri**, duvar saati gecikmesi değil. Bu yüzden düzeltilmedi, kayda geçirildi: `konsol/` devralınca eski web elden geçmeyecekse açık kalabilir (ARAYUZ §7). |
| 27 Eylül 2026 | **J-104 (🔴) bulundu ve kapandı: konsol tek bir `undefined`'dan komple beyaz ekrana düşüyordu.** Web çalıştırılıp bakılırken çıktı. `/konsol/simulasyon` doğrudan yenilendiğinde `TatbikatSeridi.tsx` `sonuc.data?.alan.ad` okuyordu: `data` korunmuş, `alan` korunmamış. Bayat bir iş kimliğiyle (sunucu o koşuyu tanımıyor, 404) ya da koşu daha kuyruktayken yanıtta künye alanları bulunmadığı için `alan` boş geliyor ve bileşen çöküyordu. Şerit **kabukta** durduğu için panel hata sınırının dışında kalıyor ve bütün konsol boş ekrana düşüyordu. **Kök sebep tipteydi:** `SimSonuc.alan` ve `.kaynak` ZORUNLU ilan edilmişti ama `sonucuNormalle` ikisini de `undefined` olabilir diye okuyor — yani TypeScript hiçbir kullanım yerinde uyaramıyordu. Tip gerçeğe uyduruldu (`alan?`, `kaynak?`), normalleştirici yarım nesne yerine `undefined` döndürüyor, sağ panel (`modlar/simulasyon.tsx`) künye yokken "Künye bekleniyor…" ya da "koşu hata verdi; yeniden başlat" gösteriyor. Tip değişikliği 8 derleme hatası açtı, hepsi bu iki dosyadaydı; `tsc -b` temiz. |
| 27 Eylül 2026 | **J-105 (🔴) bulundu ve kapandı: BİRLEŞME REGRESYONU — tatbikat "Hasar maskesi okunamadı" ile düşüyordu.** `makale` dalıyla birleşmeden sonra konsolda tatbikat koşturulunca sunucu `RuntimeError: Hasar maskesi okunamadı.` veriyordu; `veri/analiz_gorselleri/<isId>/` dizini hiç oluşmuyordu. Sebep git'in göremeyeceği cinsten bir çakışma: **bizim dalda** `worker.py` tanı görsellerini `**diagnostic_images` ile **üst düzeye** yayıyordu ve `cekirdek._gorselleri_diske_al` sonucun üst düzeyinde `B64` ile biten anahtarları arayıp diske yazıyordu; **makale dalında** ise (`9041696`, J-18) aynı görseller `"diagnosticImages": {...}` altına sarmalanmış ve tek tüketicisi monolitik `fastapi_app.py`'deki `_on_road_damage_job_done` olmuştu. Birleşmede o satır çatışma vermeden **makale tarafından** geldi (iki taraf aynı sözlüğün farklı satırlarına dokunmuştu), monoliti de bilerek attığım için **görselleri açan hiç kimse kalmadı**. `**diagnostic_images` geri kondu, bayat J-18 yorumu güncellendi. Doğrulandı: Defne/Elektrik · U-Net MiT-B4 koşusu **%100, 4/4 katman**, %0,6 piksel hasarlı, **12 kapalı kenar**, rota ortalamaları 640 / 640 / 620 m. **Ders:** otomatik birleşmenin çatışma göstermemesi doğruluk kanıtı değil; sözleşme değiştiren commit'lerde üreticiyle tüketiciyi birlikte sınamak gerekiyor. |
| 27 Eylül 2026 | **J-106 (🟠) bulundu ve kapandı: `/api/simulasyon/kos` varsayılanları bayattı, gövdesiz istek 404 alıyordu.** `SimulasyonIstegi.alanId` sabit `"hatay-elektrik"`, `katmanId` sabit `"yakin"` yazılmıştı; bu ikisi yalnız `YEDEK_ALANLAR` yedeğinde var. Ölçülmüş katalog (`tatbikat_alanlari.json`, 11 alan) yüklendiğinde karşılıkları `"defne---elektrik"` ve `"drone"` oluyor, dolayısıyla varsayılanlarla gelen istek `_katman`'da "Bilinmeyen katman" ile düşüyordu. Konsol kimlikleri hep açıkça gönderdiği için arayüzde görünmüyordu; OpenAPI varsayılanlarına bakan biri (ör. makaleyi inceleyen arkadaşım) doğrudan çarpardı. Varsayılanlar artık katalogdan türetiliyor, katalog yoksa yedeğe düşüyor. Doğrulandı: varsayılan alan + katman çözülüyor. |
| 27 Eylül 2026 | **J-107 (🟡) bulundu ve kapandı: `DEMO_CALISTIRMA.md` olmayan iki görüntü katmanı tarif ediyordu.** Belgenin §3'ü üç katman sayıyor ve sunum için `Uydu — geniş` (Maxar) seçilmesini söylüyordu; arayüzde ve uçta alan başına **tek** katman var (`Drone ortofoto`, katalogdaki `tmsUrl`). `Deprem öncesi (kontrol)` de ayrı bir katman değil, koşunun içindeki `kontrolKosusu` adımı. Maxar geniş katmanıyla yapılan ölçümler uç noktayla değil `araclar_tatbikat_kos.py` aracıyla koşulmuş. Belge gerçeğe uyduruldu ve fark açıkça yazıldı — sunumda olmayan bir düğme aranmasın. |
| 27 Eylül 2026 | **J-108 (🟢) yapıldı: tatbikata yer seviyesi iki kanal eklendi — kamera (YOLO) ve metin (BERTurk).** Eksiklik buydu: tatbikat yalnız uydu kanalını koşturuyordu, oysa makale üç kanallı bir zincir iddia ediyor (§4.5). Artık üçü de ortak sözleşmeye iniyor (kural 2) ve konsolun ısı haritasındaki kendi kanallarını besliyor. **Gerçek olan:** 13 deprem fotoğrafı (6 Şubat 2023, çoğu Hatay; Wikimedia Commons, Public domain/VOA ve CC BY-SA 4.0, künye + SHA-256 `KUNYE.json`'da) ve bunların üstünde koşan `catlak.pt` + `bina.pt`; ayrıca sentetik metinlerin üstünde koşan BERTurk sınıflandırıcı ve NER. **Üretilen:** ihbar metinleri (elle yazıldı) ve her iki kanalın **haritadaki konumu** — tohumla, modelin hasarlı bulduğu alanlardan seçilir, her kayıt `sentetikKonum: true` taşır, gösterge/panel/depo ayrı ayrı yazar. **Konum neden üretiliyor:** (a) fotoğrafların EXIF konumu yok, (b) metin hattının coğrafi kodlayıcısı mahalle merkezine düşürüyor — "Defne Elektrik Mahallesi" → (36,17/36,13), tatbikat kutusu (36,1977/36,1494), yaklaşık **2 km** ötede ve kutunun dışında. **Ölçüldü** (`araclar_kanal_olc.py`, rapor `benchmark/reports/kanal_olcumu.json`): kamera **13/13** fotoğraf tespit verdi, 47 çatlak + 65 bina, medyan 308 ms; metin 18'de **9** yazarın niyetiyle örtüştü, medyan 37 ms. Örtüşme bir doğruluk DEĞİLDİR (tek kişilik etiket, bulanık sınır) ve örtüşmeyen 9'un **8'i "Acil Yardım İhtiyacı"na** kayıyor — model aciliyet taşıyan her metni o sınıfa çekiyor. Tam hatta coğrafi kodlama iki metinde 3,3 ve 4,4 sn sürdüğü için tatbikat onu çağırmıyor (kural 3). Ayrıntı: `SIMULASYON_OLCUM_KAYDI.md` §17. |
| 27 Eylül 2026 | **J-109 (🟠) bulundu ve kapandı: üç alanın şeklinde de aynı dört fotoğraf çıkıyordu, üstelik fotoğrafların ili başkaydı.** Üç kanallı makale şekli üretilirken görüldü. **(1)** Kamera kanalının fotoğraf seçimi yalnız tohuma bağlıydı; tohum her alanda 42 olduğu için Defne, İslahiye ve Nurdağı şekillerinde birebir aynı dört fotoğraf ve aynı tespit sayıları (13 çatlak / 15 bina) çıkıyordu. Üç ayrı mahallede aynı dört binanın fotoğraflanmış olması inandırıcı değil ve şekiller birbirinin kopyası görünüyordu. Alan adı artık `zlib.crc32` ile kararlı bir sayıya çevrilip tohuma karışıyor — aynı alan + aynı tohum yine aynı sonucu verir, farklı alan farklı fotoğraf alır. (`hash` kullanılamaz: Python'da süreç başına tuzlanır.) Sonuç: Defne 14/40, İslahiye 12/41, Nurdağı 15/41 (çatlak/bina). **(2) Daha önemlisi:** katalogdaki 13 fotoğrafın hepsi **Hatay ve Adıyaman**'dan. Gaziantep alanlarına yerleştirildiklerinde aynı depremin gerçek fotoğraflarıdır ama **o mahallenin** fotoğrafı değildirler; "konum üretildi" etiketi bunu tek başına söylemiyordu. Uyarı artık hem şekil künyesinde hem kanal çıktısının `not` alanında yazılı, makale altyazısı önerisine de kondu (`MAKALE_DEGISIM_LISTESI` §F). Ayrıntı: `SIMULASYON_OLCUM_KAYDI.md` §17.5. |
| 27 Eylül 2026 | **J-110 (🔴) bulundu ve kapandı: üç kanal şekli ilk hâliyle makaleye konulamazdı — künyedeki dürüstlük uyarısı kesikti ve gösterge çizilmeyen şeyleri sayıyordu.** Kullanıcı şekli ekranda büyütünce çıktı. **Dört ayrı kusur:** **(1)** Ortak `_gosterge` metni sarmalamıyor, tek satır çizip taşanı kırpıyor; künyedeki "…**ÜRETİLEN**: ihbar metinleri ve kamera/metin konumları. Fotoğraflar aynı depremden (Hatay ve Adıyaman); bu mahallenin fotoğrafı DEĞİLDİR" kısmı sağdan kesiliyordu — yani şeklin en kritik parçası görünmüyordu. Sarmalayan kendi çizicimizi yazdık (`_gosterge_sarmali`), ortak fonksiyona dokunulmadı ki mevcut 15 şekil bozulmasın. **(2)** Gösterge "Mahalle giriş ağzı — 5 ekip" diyordu ama Nurdağı'da giriş ağızlarının **hepsi kare dışında** (mahalle grafiği görüntünün +150 m dışına taşar): çizilmeyen şey göstergede sayılıyordu. Satır artık gerçeği yazıyor. **(3)** Kamera ve metin kanallarının asgari ayrım kuralı yalnız kanalın **kendi içinde** çalışıyordu; iki kanal farklı tohum kullandığı için K3 ile M4 **16 piksel** arayla düşmüş, haritada tek nokta gibi görünüyordu. `_hasar_konumlari` artık `kacinilacak` listesi alıyor; kamera önce koşup konumlarını metin kanalına veriyor (uç noktasında da öyle). **(4)** Kamera fotoğrafı haritanın sağ altına gömülüydü ve **altında kalan iki metin işaretini (M3, M5) gizliyordu** — gösterge 5 ihbar derken haritada 3 tanesi görünüyordu. Fotoğraf haritanın altında kendi şeridine taşındı; hem harita kapanmıyor hem fotoğraf büyüdü, lisans ve fotoğrafçı da yanında yazıyor. Doğrulandı: Nurdağı'da K1–K4 ve M1–M5'in dokuzu da görünür, göstergedeki sayılarla birebir. Üç şekil de yeniden üretildi. |
| 27 Eylül 2026 | **J-111 (🔴) bulundu, AÇIK: metin sınıflandırmasının 13→5 üst kategori katmanı modelin doğru cevabını bozuyor.** F1 ölçümü için etiket eşlemesi çıkarılırken görüldü. Model 13 etiketli (Alakasız, Arama Ekipmanı, Barınma, Cenaze, Elektrik, Enkaz Kaldırma, Giysi, Isınma, Lojistik, Sağlık, Su, Tuvalet, Yemek); `classification.py` bunları P-5'e indiriyor. **Üç hata:** **(1) Anahtar kelime kurtarması modeli EZİYOR.** `classify()` içinde `_keyword_rescue` en başta koşuyor ve eşleşirse hemen `return` ediyor — model %97 güvenle doğru etiketi vermiş olsa bile. Ölçüldü: "…bina tamamen çöktü, enkaz altından ses geliyor acil ekip lazım" metninde model **"Enkaz Kaldirma"** diyor (doğru), "ekip lazım" anahtar kelimesi devreye girip çıktıyı **"Acil Yardım İhtiyacı"**'na çeviriyor. Kurtarma, düşük güvenli kayıtların sessizce elenmesini önlemek için yazılmıştı (E-04); koşulsuz uygulanınca tam tersini yapıyor. **(2) İki harflik anahtar kelime alt dizgi tuzağı.** `RESCUE_KEYWORDS["Acil Yardım İhtiyacı"]` içinde **`"aç"`** var ve kontrol `k in metin` — yani **araç, ağaç, ilaç, açık, kaçak, saç** kelimelerinin hepsi eşleşiyor. "…ağır **araç** geçemiyor" metni bu yüzden "Acil Yardım İhtiyacı" oluyor. Aynı risk `"yol"` için de var (yollayın, yolcu). **(3) Dönen güven, dönen kategoriye ait değil.** Kurtarma `max(score, 0.50)` döndürüyor; skor modelin BAŞKA bir etikete verdiği skor. Arayüzde ve Tablo 15'te "güven" diye gösterilen sayı, gösterilen kategorinin güveni değil. **Sonuç:** 27 Eylül'deki "18 metnin 9'u örtüştü" ölçümü modelin başarımı DEĞİLDİR; 13 etiketli ham çıktı bakıldığında model belirgin biçimde daha iyi. F1 bu yüzden **13 etiket düzeyinde** ölçülmeli (eşleme gerekmez, yargı payı yok), P-5 katmanı ayrıca ve kural tabanlı bir son-işlem olarak raporlanmalı. Katman düzeltilmeden makaleye sayı yazılmamalı — §3.6'daki E-04 anlatımı da buna göre güncellenmeli. |
| 27 Eylül 2026 | **J-112 (🔴) bulundu, AÇIK: "cezanın payı %97,4 → %30" iddiası bu tatbikata ait değil.** Makale–kod taramasında görüldü. %30, rastgele kapanma kümesiyle yapılan bir mekanizma sınamasından geliyor; betiği ve çıktısı depoda yok. `SIMULASYON_OLCUM_KAYDI` §8.2'den kaba kestirim (keşfin bilmeyen kola ait olduğu ve 25 ortak görev varsayımıyla): Nurdağı U-Net 44,4 × 1,4167 ≈ 62,9 dk / 25 × 3,04 ≈ 76,0 dk → **≈ %83**; Defne ≈ %86, İslahiye ≈ %100 (yuvarlama yüzünden güvenilmez). Yani sabit 1,42 dk'ya inse de kazancın çoğu hâlâ cezadan geliyor. Makale buna göre düzeltildi (ÖZ, §3.8, §4.6, §5.1, §5.3(b)); kesin pay için koşu `cezadanGelenDk` alanıyla tekrarlanmalı. **Ek kusur:** kapanmada geri dönen ekibin manevrası hem cezanın içindeki 25 sn'de hem de yeniden planlamadaki 25 sn'lik U dönüşünde (`network.py:831-832`, `donus.py:140-150`) sayılıyor. |
| 27 Eylül 2026 | **J-113 (🟠) bulundu, AÇIK: `oneway=-1` ileri yön sayılıyor** (`apps/road_damage/utils/yerel_yol.py:76`). OSM'de -1, çizim yönünün tersine tek yön demek; bu kenarlar yanlış yönde kuruluyor. `testler/test_donus.py` yalnız elle kurulmuş çizgeyi sınıyor, gerçek çizge kurulumunu sınamıyor. Düzeltme ölçülen sayıları değiştirebilir; üç alanda kaç kenarın etkilendiği sayılmalı. |
| 27 Eylül 2026 | **J-114 (🟠) bulundu, AÇIK: süre tabanlı A* sezgiseli her çizgede kabul edilebilir değil.** Sezgisel `haversine / 22,2 m/s` (≈80 km/sa; `donus.py:108,130-134`); hız tablosunda otoyol 90 km/sa ve `maxspeed` 130'a kadar kabul ediliyor. 80'i aşan kenar varsa A* eniyi yolu kaçırabilir. `v_max` çizgedeki en yüksek kenar hızından alınmalı. Makale §3.8 koşullu olarak yazıldı. |
| 27 Eylül 2026 | **J-115 (🟡) bulundu, AÇIK: kamera eşiği kodda 0,20 ama fiilen 0,25.** `uclar/kamera.py:83,107` model çağrısına `conf` vermiyor; ultralytics varsayılanı 0,25 önce uygulanıyor, `>= 0.20` filtresi hiç devreye girmiyor. Makale Tablo 7 fiilî değerle düzeltildi. |
| 27 Eylül 2026 | **J-116 (🔴) J-111'e ek bulgular (AÇIK).** (1) Tatbikat metin ölçümünde 18 çıktının **12'sine anahtar sözcük karar vermiş**; Acil Yardım'a kayan 8 metnin 5'i kurtarmadan (2'si "araç" içindeki "aç"), 3'ü Su/Elektrik/Isınma → Acil Yardım eşlemesinden. (2) Anahtar sözcük kurtarması dört kategoriyi kapsıyor, beşi değil; sağlık listesinde "kan", "insülin" yok, enkazda "mahsur" yok. (3) Etiket başına 0,50 eşiği yok; en yüksek etiket alınıyor. (4) Model "Lojistik" dediğinde dal hep aciliyet 2'ye düşüyor (ulaşım sözcüğü kurtarmada önce yakalanıyor); aciliyet 3 yalnız anahtar sözcükle geliyor. (5) "Alakasız" kayıt `None` dönüp zincirden düşüyor (Tablo 9'daki aciliyet 1 yazılı değil). (6) `text.lower()` Türkçeye duyarlı değil: "I" → "i" (`classification.py:159`). (7) Zemberek çağrısı kaldırılmış ama arayüz metinleri hâlâ "Zeyrek" diyor. Makale §3.6, §4.5, §5.3(c) koda göre yeniden yazıldı. |
| 27 Eylül 2026 | **J-117 (🟠) bulundu, AÇIK: tatbikat sonuçlarının ham dosyası ve birleştiricisi depoda yok.** `araclar_tatbikat_kos.py` yalnız ilk tohumu `kollar` alanına yazıyor, 5 tohumun ortalama ± s.s.'sini üreten betik yok; §8.2'deki "Keşif" sütununun hangi kola ait olduğu kayıtlı değil. Ayrıca `araclar_tatbikat_kos.py:142` `elenen = []` satırı değeri eziyor, `elenenAfetzede` hep 0. Kıyas ortalamaları 0,1 dk'ya yuvarlanıyor (`tatbikat.py:586`); İslahiye gibi küçük farklarda kazanç ±5 puan belirsiz. Bu makinede tatbikat belgelenen kurulumla koşmuyor (eski `roads.gpkg`, P2 ağırlıkları yok; yerel çizge boş dönünce kod sessizce Overpass'a ve düz 15/30 km/sa'ya düşüyor). |
| 27 Eylül 2026 | **J-118 (🟡) bulundu, AÇIK: yan bulgular.** (1) `benchmark/data/model_masks_unet_mitb4/*/meta.json` modeli "dispath…dice30 / Segformer mit_b4" diye etiketliyor ama SHA-256 `unet_mitb4_p2_t42`'ninki. (2) `tile_quality_score` tanımlı ama hiçbir yerden çağrılmıyor. (3) `zoom_for_radius` analiz yolunda artık kullanılmıyor (`zoom_for_gsd`, z18). (4) Makale Tablo 12'deki yerel sürümler (Python 3.12.6, PyTorch 2.13.0, Ultralytics 8.4.116 …) ne `backend/venv` (3.12.10 / 2.11.0 / 8.4.57) ne ölçüm kaydı (PyTorch 2.10) ile tutuyor; ölçümün yapıldığı i7-12700H makinesinde `pip freeze` ile doğrulanmalı. (5) `araclar_makale_haritalari.py` künye satırını sarmalamıyor, taşan kısım kesiliyor (makaleye kırpılmış sürüm kondu). |
| 27 Eylül 2026 | **J-119 (🔴) bulundu, AÇIK (güvenlik, CLAUDE.md kural 5): eski `/api/auth/register` hâlâ bağlı ve istemciden `role` alıyor** (`uclar/eski_kimlik.py:40`, `cekirdek.py:1227`); `POST /api/team/claim` (HTTP 409 kilidi) yetki bağımlılığı olmadan çalışıyor (`uclar/ekip.py:41-60`). Rol şeması üç değil dört rollü (afetzede, saha, koordinatör, yönetici; `kimlik.py:33`) — makale düzeltildi. |
| 27 Eylül 2026 | **J-120 (🔴) bulundu ve KAPANDI: risk karşılaştırmasındaki "yalnız sismisite yoğunluğu" naif tabanı (R0b) sabit bir öznitelikle koşulmuştu.** `naive_baselines.py` `event_count_7d` kullanıyordu; bu `rolling(window=7).count()` olduğundan 13 609 kaydın hepsinde 7 — taban tanım gereği ROC-AUC 0,5000 veriyordu ve makale bunu "sismisite yoğunluğu bilgisiz" diye yorumluyordu. Makalenin tanımladığı öznitelik (`rolling_mean_7d`, son 7 olayın ortalama büyüklüğü) ile aynı 5 katlı ileri yürüyen bölmede yeniden ölçüldü (`model_benchmarks/05_risk_skoru/local_run/naive_r0b_duzeltme.py`, katalog 2 Ağustos 2026'ya süzülerek n = 13 609; düzenek R0a'yı Tablo 21'deki değerlerle birebir üretti). **Sonuç: ROC-AUC 0,6143 ± 0,0520, PR-AUC 0,4021, MCC 0,1616** — MCC'de bütün öğrenilmiş modelleri, ROC/PR-AUC'de üretimdeki CatBoost'u geçiyor. Makale §3.7, §4.11 (5. gözlem), Tablo 21, Tablo 22 ve §6 güncellendi. Ayrıca `_7d` öznitelikleri 7 günlük değil 7 olaylık; Şekil 20 etiketleri düzeltilip yeniden üretildi (`shap_figure.py --son-tarih 2026-08-02T23:59:59`, öznitelik önemi eskisiyle birebir). Tablo 21'deki kalın işaretler yanlış hücrelerdeydi (PR-AUC, F₁, Brier); ölçülen en iyi değerlere göre düzeltildi. |
| 27 Eylül 2026 | **J-121 (🟠) bulundu ve KAPANDI: kaynakçada dört hatalı DOI.** doi.org + Crossref ile 53 DOI tek tek sınandı: [9] xBD'nin DOI'si (10.1109/CVPRW.2019.00332) bambaşka bir makaleyi (melanom doku bölütlemesi) gösteriyordu → CVF açık erişim sayfasıyla değiştirildi (s. 10–17 doğrulandı); [10] 10.1109/TGRS.2024.3437470 yok → doğrusu 10.1109/TGRS.2024.3438290 (başlık, cilt, sayfa tutuyor); [48] ve [55] doi.org'da kayıtsız 10.5555 (ACM) DOI'leri → CatBoost arXiv DOI'si, LightGBM NeurIPS bildiri adresi. Erişimi bugün doğrulanan 13 URL'nin erişim tarihi 27.09.2026 yapıldı. |
| 27 Eylül 2026 | **J-122 (🟠) bulundu ve KAPANDI: üç şema eski senaryoyu gösteriyordu.** Şekil 6 (protokol) "EMSR648 ile kesim düzeyi karşılaştırma" ve R0–R3 kollarını; Şekil 2 (mimari) "yol hasarı bölütleme" ve "HTTP 202 + yoklama"yı; Şekil 4 seviye 1-2-3'ü (metinde 0-1-2) ve yumuşak tepeli bir ağırlık penceresini (kodda düz tepeli yamuk) gösteriyordu, ayrıca var olmayan "Bölüm 3.1.2"ye atıf yapıyordu. Üçü `araclar_makale_semalar.py` ile yeniden çizildi; Şekil 4 (b) ve (d) doğrudan `inference.py` fonksiyonlarıyla üretiliyor. Aynı turda boş Tablo 5 (yol hasarı kümesi künyesi) ve Tablo 15 (il-ayrık genelleme) metne çevrildi, tablolar 1–22 olarak yeniden numaralandı ve Türkçe ek uyumu otomatik onarıldı. |
| 27 Eylül 2026 | **J-112, J-113, J-114 KODDA DÜZELTİLDİ, J-117 kısmen (kullanıcı kararı: düzelt + yeniden koş).** `network.py`: dönüş maliyeti açıkken kapanma sabiti yalnız değerlendirme (1,0 dk); manevrayı ekibin fiilen yaptığı dönüş ödüyor. `yerel_yol.py`: `oneway=-1` ters yönde (v → u) kuruluyor. `donus.py`: A* sezgiseli çizgenin gerçek en yüksek hızını kullanıyor (`en_yuksek_hiz`; sınamada eski sabit 80 km/sa 44,4 sn'lik yolu, doğrusu 41,5 sn). `tatbikat.py`: kol ortalamaları 3 basamak, `toplamSureDk`/`toplamCezaDk` eklendi. `araclar_tatbikat_kos.py`: `elenen` ezme hatası giderildi. Yeni `araclar_tatbikat_ozet.py`: tohumları birleştirir, keşfi HER KOL İÇİN AYRI ve ceza payını ölçülmüş olarak yazar. `testler/test_donus.py`: 3 yeni sınama, 7/7 geçiyor. **Makaledeki sayılar eski kodla üretildi**; yeniden koşu i7 makinesinde (makale/KALAN_ISLER_2026-09-27.md, B0). |
| 27 Eylül 2026 | **J-119 KODDA DÜZELTİLDİ (kural 5).** `uclar/eski_kimlik.py`: `/api/auth/register`, `/login`, `/me` artık `Depends(kimlik.eski_uc)` arkasında (varsayılan KAPALI, `QUAKEMIND_ESKI_UCLAR=1` ile açılır); kayıt `req.role`'ü yok sayıyor, eski uçlardan açılan her hesap `survivor` (girişteki otomatik kayıt da — eskiden `responder`'dı). `uclar/ekip.py`: `claim`, `claims`, `route`, `release` aynı bağımlılığın arkasında. TestClient ile sınandı: kapalıyken 404; açıkken `role: "coordinator"` gönderen kayıt `survivor` dönüyor, ikinci ekibin aynı hedef için `claim`'i 409. **Dikkat:** 409 kilidini çağıran ölçüm betikleri ve uç duman testi (`araclar_uc_duman_testi.py`; imzada bu 7 uç var) artık sunucunun `QUAKEMIND_ESKI_UCLAR=1` ile açılmasını ister; açıkken imza (durum kodu + üst düzey anahtarlar) değişmez, yalnız dönen `role` değeri değişir. Kalan: `/api/auth/me` belirteci URL sorgusunda taşıyor (kural 5) — eski web bunu kullandığı için yeni akışa (uclar/oturum.py) geçişte kaldırılacak. |
| 27 Eylül 2026 | **J-111 ve J-116 KODDA DÜZELTİLDİ, yeniden ölçüldü, makale güncellendi.** `apps/disaster_nlp/src/classification.py`: yeni `classify_detay()` karar sırası — (1) model ≥ 0,30 ve "Alakasız" değilse modelin etiketi eşlenir, anahtar sözcük onu EZMEZ; (2) kararsız ya da "Alakasız" ise kurtarma; (3) kurtarılamayan kararsız → "Belirsiz". Eşleşme sözcük sınırına bağlı (`anahtar_eslesir`: 4 harften kısa anahtar tam sözcük, uzunlar sözcük başından); "aç" çıkarıldı, yerine "aç kaldık/aç kaldı/açız"; "yol" yalnız tam sözcük + çekimleri; Türkçe küçük harf (`turkce_kucuk`, I→ı); gösterilen güven gösterilen kategorinin kendi skoru (`_kategori_guveni`, eski `max(skor, 0.50)` kalktı); "Lojistik" dalı artık çalışıyor. Eşik (0,30) ve 13→5 eşlemesi DEĞİŞMEDİ — 18 tatbikat metnine göre ayar yapılmadı. `testler/test_siniflandirma.py` 7/7. **Ölçüm** (`araclar_kanal_olc.py --yalniz-metin --cikti benchmark/reports/kanal_olcumu_metin_duzeltilmis.json`; i7 raporu `kanal_olcumu.json`'a dokunulmadı): örtüşme **9/18 → 11/18**; kararın kaynağı model 15, anahtar sözcük 3 (eskiden 12'si anahtar sözcük — eski kod bu makinede 18/18 aynı kategoriyi üretti, sayım doğrulandı). Kazanılan 4 (üç enkaz metni artık "ekip lazım"/"arama kurtarma"/"araç"a ezilmiyor; "ağır araç geçemiyor" Yol Kapanma), kaybedilen 2 ("çökmüş duvar yüzünden kapalı" cadde ve "yaralı var kanaması durmuyor": ikisinde de model %89 / %55 ile Enkaz Kaldırma diyor, eskiden anahtar sözcük kurtarıyordu). Örtüşmeyen 7'nin 3'ü eşleme (Yemek/Isınma/Arama Ekipmanı → Acil Yardım), 3'ü modelin Enkaz Kaldırma'sı, 1'i kurtarma önceliği ("ambulans giremiyor"). `pipeline.py` açılış iletisindeki "Zeyrek" kaldırıldı. **Makale (revize7):** §3.6 normalleştirme (sınıflandırıcı küçük harf görmüyordu — metin yanlıştı; BERTurk ayrıştırıcısı `do_lower_case: false`), karar sırası, kurtarma katmanının ilk hâli + düzeltmesi, NER paragrafı ("iki ayrı biçim" yanlıştı, ikisi aynı metni alıyor), Tablo 8 dipnotu; §3.9 atama örneği ("hilti ve jeneratör lazım" gerçekte Elektrik Kaynağı → Acil Yardım, "doğru biçimde lojistik" yanlıştı; aynı paragrafta kalın yazı kelime ortasında bitiyordu); §4.5 kanal ölçümleri, metin eğilimi paragrafı, Tablo 14; §5.3(c); §6 gelecek işler ve sonuç; Denklem (8) metinde anılmıyordu. **Açık kalan:** J-116 (2) anahtar sözcük kapsamı ("kan", "insülin", "mahsur" yok) — değiştirmek test metnine ayar olur, etiketli kümeyle birlikte ele alınacak. **i7'de yapılacak:** Tablo 14 gecikmesi düzeltme öncesi hatla ölçüldü (makalede yazılı) → `araclar_kanal_olc.py` tam koşu; Şekil 10 (Nurdağı) metin işaretlerinin boyu aciliyete bağlı ve 5 Gaziantep metninin 3'ü Acil Yardım → Enkaz'a geçti → `araclar_makale_uc_kanal.py --hepsi` (U-Net ağırlığı bu makinede yok). |
| 27 Eylül 2026 | **J-123 (🟠) bulundu, AÇIK: metin modeli yol kapanmasını tanımıyor.** Düzeltilmiş katmanla görüldü: yazarın "Yol Kapanma" dediği 4 tatbikat metninin hiçbirine model ulaşım etiketi ("Lojistik") vermiyor — üçüne "Alakasız" (0,58–0,65), birine "Enkaz Kaldırma" (0,89). Üçü yalnız anahtar sözcük kurtarmasıyla zincirde kalıyor. Yani hatta yol kapanması bilgisi bugün modelden değil anahtar sözcükten geliyor; eğitim kümesinin (intent_test_v13) "Lojistik" etiketi ulaşımdan çok ihtiyaç lojistiği anlatıyor olabilir — denetlenmedi. Makale §4.5, §5.3(c), §6'ya yazıldı. Çözüm: etiketli kümede yol kapanması örneği sayısını çıkarmak, gerekiyorsa ayrı bir "ulaşım" etiketiyle yeniden eğitmek. |
| 27 Eylül 2026 | **J-124 (🟠) bulundu ve KAPANDI: Şekil 1'in noktaları hiçbir kaynağa bağlı değildi.** Yazın konumlandırma şeklinde ~42 gri nokta vardı; üretici betik depoda yoktu, hangi noktanın hangi çalışma olduğu hiçbir yerde kayıtlı değildi (kural 1). §2 yalnız ~20 uygulamalı çalışma tartışıyor ve sağ üst çeyrekteki (çok kanal + ekip sevki) üç nokta §2.3'teki "böyle bir çalışmaya rastlanmamıştır" ifadesiyle çelişiyordu; ayrıca y ekseni yazısı x ekseni yazısına biniyordu ve "Bu çalışma" yıldızı turuncuydu. Yeni `araclar_makale_yazin_konumu.py`: her kutu §2'deki bir kaynak numarası (19 kaynak), sütun = algılama kanalı (yok / uydu-hava / yer seviyesi / iki / üç), satır = çıktının ulaştığı düzey (veri kümesi, model çıktısı, hasar haritası, erişilebilirlik/güzergâh, ekip sevki); her yerleşimin §2'deki gerekçesi betikte yazılı. Genel amaçlı mimariler, dil modelleri ve derleme [7] dışarıda. Makale (revize8): şekil, §2.5 atıf cümlesi ve altyazı ("niteliksel sınıflama" yazılı). Sınıflama bir yargıdır — yazar gözden geçirmeli. |
| 27 Eylül 2026 | **Şekil 5 üreticisi düzeltildi (B4):** `araclar_makale_haritalari.py` `_gosterge` künye satırını tek satır çizip sağdan kırpıyordu; artık sarmalıyor (tek satırlık künyede yerleşim birebir aynı). Sentetik görüntüyle sınandı. Yeniden üretim model ağırlığı ister → i7 (KALAN_ISLER B0). |
| 28 Eylül 2026 | **J-112, J-113, J-114 ve J-117 KAPANDI: tatbikat düzeltilmiş kodla yeniden koşuldu (B0 paketi, ikinci makine).** Tek komut `araclar_b0_kos.sh` (17 dk). Çıktılar `benchmark/reports/tatbikat_b0/`. P2 ağırlıkları Kaggle `furkanemrence/quakemind-modeller`'dan alındı; SHA-256 künyelerle aynı. Yol verisi 30 Mayıs PBF'inden `pyrosm` 0.13.1 ile yeniden üretildi (755.236 kenar; i7'de 756.623). `cykhash` Windows'ta derlenemediği için conda-forge'un derlenmiş paketi kullanıldı. Tatbikat alanlarında fark yok: hasar, kapalı kenar, kapsama ve Nurdağı mahalle çizgesi (296/715) aynı. **Sonuç:** Nurdağı bandı %59–66 → %54–60, genel bant %7–66 → %8–60, Defne %41 → %18–28, İslahiye dengeli / en iyi %40,9 / %9,9 → %33,7 / %8,3. **Ceza payı ölçüldü:** %68–78 (Nurdağı %73–76; eski kaba kestirim %83). **J-117 cevabı:** eski "Keşif" sütunu kapanmayı bilmeyen ekibinmiş. **J-113:** bölge verisinde `oneway=-1` kenar yok, etkisi sıfır. Tablo 17 artık koşucunun `--guzergah` seçeneğiyle üretiliyor; eksik Ekip 4 eklendi. Duyarlılık (Tablo 19) bu kez U-Net ile koşuldu. **Makale (revize10, revize11):** ÖZ, Abstract, Kısaltmalar, Tablo 11 (ikinci makine sütunu), §3.8 (A* sezgiseli, yol verisi sayıları, 43.821 tek yönlü kenar, c_kapanma), Tablo 15 (12 sütun: keşif iki kol, ceza payı), Tablo 16–19, §4.6–4.9, §5.1, §5.3(b), §6, Tablo 22; Şekil 5, 10, 11, 12. `araclar_makale_sekilleri.py` artık sayıları JSON'dan okuyor. |
| 28 Eylül 2026 | **J-125 (🟡) bulundu ve KAPANDI: üç tabloda punto tutarsızlığı ve iki şekil göstergesinde taşma.** Tablo 2, 11 ve 22'de 12 hücre Normal stilin büyük puntosunu alıyordu; tablonun baskın puntosuna (9,5 pt) eşitlendi. Şekil 5 göstergesinde "0'i karede" yazıyordu, "hepsi kare dışında" oldu. Şekil 12'de yeni noktalarda etiketler üst üste biniyordu, kaydırıldı. `araclar_tatbikat_ozet.py` model adını sözlük olarak basıyordu ve araç rotası olmayan satırda hasarı boş bırakıyordu; ikisi de düzeltildi. |
| 28 Eylül 2026 | **Ölçülmemiş ve kapatılabilir eksikler kapatıldı (revize12).** (1) **A\* çapraz doğrulama:** 248 sorguda A\* = bağımsız Dijkstra, uyumsuzluk yok (`araclar_astar_capraz.py`). J-114'ün tatbikat alanlarında etkisi yok (v_max 45–70 km/sa). (2) **Kalan sekiz alan** üç model × beş tohumla yeniden koşuldu: eski "ayrışmadı" cümlesi yanlıştı. Şubat Stadyumu (B2 %40,4), Şekeroba orta (B2 %13,7) ve Türünçlü (U-Net %32,5) tek modelde ayrışıyor. Seçim ölçütü "en az iki modelde ayrışma" olarak yazıldı. (3) **Metin üst kategori F₁** sızıntısız karşılaştırma BERTurk'üyle ölçüldü (`araclar_metin_p5_olc.py`): mikro 0,797 / makro 0,758 (düzeltilmiş katman), 0,819 / 0,787 (yalnız eşleme), 0,722 / 0,710 (eski katman). (4) **YOLO mAP:** model dosyalarındaki eğitim doğrulama metrikleri — bina 0,592 / 0,394, çatlak 0,731 / 0,584; iyimser, bağımsız sınama değil. (5) **Son işleme seviyesi:** ekip Kaggle kayıtlarından; on modelde ΔIoU ≤ 0,0009. (6) **Şekil 24** (örnek veri kipi) kaldırıldı. (7) **GPU işleri** için hazır ayarlar: `makale/analiz_arsivi/GPU_IS_PAKETI_2026-09-28.md`. |
| 28 Eylül 2026 | **J-126 (🔴) bulundu: kapanma "yer gerçeği"ni bir insan değil Claude etiketlemiş; makale bunu söylemiyordu.** `benchmark/kapanma_yer_gercegi/etiketler_defne_elektrik.json` → `"etiketleyen": "Claude (tek etiketleyici)"`. Makale §4.3'te "elle işaretlenmiştir" diyor, ÖZ'de "kör etiketlemeyle sınanmış" (3/3, ≈%11). Makaleye açıkça yazıldı: ÖZ, Abstract, §4.1, §4.3 ve Tablo 13, §5.1, §5.3, §5.4, §6, Tablo 22. **Açık:** bir yazarın aynı 33 kesiti etiketlemesi. Kit: `benchmark/kapanma_yer_gercegi/insan_kiti/` (etiketle.html, BENIOKU). Ölçüm ve Cohen κ: `araclar_kapanma_uyum.py`; Claude etiketleriyle makaledeki sayıları aynen üretiyor. |
| 28 Eylül 2026 | **J-127 (🔴) bulundu: "anonimleştirilmiş" metin kümesinde kişisel veri var.** `deprem-private/intent_test_v13_anonymized` içinde kişi adları `[MASK]`lı, ama telefon numarası ve açık adres içeren kayıtlar var. Etik Beyanı "tüm veriler açık erişimli" diyordu → düzeltildi. §3.6'ya bulgu, Veri Erişilebilirliği'ne "kişisel veri alanları maskelendikten sonra" koşulu eklendi. Ölçüm raporuna örnek metin yazdırılmıyor. **Karar sizde:** kümenin paylaşım politikası ve gerekiyorsa etik kurul / KVKK değerlendirmesi. |
| 28 Eylül 2026 | **J-128 (🟠) bulundu: üretimdeki metin ağırlığı (`2kveri`) sınama bölmesini görmüş görünüyor.** 13 alt etiket mikro-F₁ sınamada 0,916, eğitimde 0,912 (karşılaştırma BERTurk'ünde 0,828 ve 0,903). Başarım sayıları sızıntısız karşılaştırma ağırlığıyla verildi, durum §4.10'a yazıldı (CLAUDE.md kural 8). **J-123 kapandı:** eğitim kümesinde "Lojistik" 2.028 kaydın 38'inde geçiyor ve taşıma ihtiyacı anlatıyor; ulaşım sözcüklü 69 kaydın yalnız 3'ünde bu etiket var, sözcük çoğunlukla adresin parçası. Yol kapanması ihbarı kümede neredeyse yok. |
| 28 Eylül 2026 | **J-127 ilerleme: maskeli yerel kopya üretildi.** `araclar_metin_maskele.py` ile, depo dışına (`C:\Users\utkuc\quakemind_ozel\intent_test_v13_maskeli\`). Kayıtların **%49'unda (999/2.028) telefon numarası** vardı; maskelendi, kalan 0. 2.775 kullanıcı adı ve 225 URL de maskelendi. **Adresler kayıtların %97'sinde** geçiyor (mahalle, sokak, cadde, no); kümenin görevi konum çıkarımı olduğu için maskelenmedi. Kapı numaraları `--adres-numarasi` seçeneğiyle maskelenebiliyor. Rapor yalnız sayı içeriyor: `benchmark/reports/metin_maskeleme_raporu.json`. Hugging Face'teki asıl kümeye dokunulmadı. **Karar sizde:** paylaşımda maskeli kopya kullanılsın mı, adresler de maskelensin mi. |
| 28 Eylül 2026 | **Etiketleme sayfası düzeltildi (J-126 kiti).** Kesit görselleri yan klasörden okunuyordu; sayfa başka bir yerde (önizleme, e-posta eki, GitHub) açılınca görünmüyordu. 33 kesit sayfanın içine gömüldü (tek dosya, 5,1 MB); tarayıcıda 33/33 görsel yüklendiği ve etiketin JSON'a düştüğü sınandı. **Ayrıca:** Veri Erişilebilirliği'ne Kaggle model ağırlıkları, rapor paketi ve Hugging Face metin modeli bağlantıları eklendi (revize13). Sarı vurguları kaldırılmış gönderim kopyası: `makale/QuakeMind_Makale_GONDERIM_vurgusuz.docx`. |
| 28 Eylül 2026 | **J-126 KAPANDI: kapanma yer gerçeği artık insan etiketiyle (revize14).** Bir yazar 33 kesiti kör etiketledi (`benchmark/kapanma_yer_gercegi/etiketler_insan_1.json`); ölçüm `araclar_kapanma_uyum.py` → `uyum.json`. **İnsan:** model KAPALI dedi → 4 kapalı / 1 açık / 0 kararsız; model AÇIK örneği → 10 / 13 / 5; kesinlik **4/5 = %80** (Wilson %38–96), duyarlılık kestirimi **≈%9** (4/44; 118 parçada tahmini 44 gerçek kapanma, %38), yargılanamayan %15. **Claude (ikinci görüş):** 3/3, ≈%11, yargılanamayan %30. **Uyum zayıf:** 33 kesitin 14'ünde aynı etiket, Cohen κ = 0,13 (üç sınıf), 0,37 (kararsız hariç, n = 19). **Makaledeki anlam değişti:** "model yanlış alarm üretmiyor" artık doğru değil → "az yanlış alarm üretiyor (5'in 1'i)"; insan etiketinde gerçek kapanma daha çok, duyarlılık biraz daha düşük. İnsan esas, Claude ikinci görüş olarak yazıldı: ÖZ, Abstract, §4.1, §4.3 (yöntem, Tablo 13 yeniden kuruldu: iki etiketleyici sütunu + uyum satırı, başlık), §5.1, §5.3(a), §5.4, §6 (üç yer), Tablo 22. Sınır olarak kalan: tek insan etiketleyici, tek mahalle, küçük örneklem; κ düşüklüğü ortofotodan kapanma yargısının öznel olduğunu gösteriyor. |
| 28 Eylül 2026 | **J-129 (🟡) bulundu: Kaggle defterinin kuyruğu 0. hücrenin ayarlarını kullanmıyor.** `03_kaggle_protokol` kuyruk hücresi (9) her deneyde deftere gömülü eski ayar kaynağını (`_KAYNAK["ayar"]`, sonunda `MODEL_ADI = "unet_mitb4"`) yeniden çalıştırıyor; 0. hücreye eklenen oturum ayarları yalnız ilk koşuya uygulanıyor. Sonuç: 2. oturumda `dict(BOLGE_EGITIMI="haric:Kahramanmaraş")` SegFormer yerine U-Net koştu. Eksik deney ayrı defterle (oturum 3) koşuldu. **Kural:** kuyruk öğesine bütün farklı ayarlar açıkça yazılır ya da tek deneylik defter kullanılır. Kalıcı çözüm üreteçte (`defter_dokuz_model.py`): kuyruk 0. hücrenin güncel değerlerinin üstüne yazmalı. Not: `makale/analiz_arsivi/GPU_IS_PAKETI_2026-09-28.md`. |
| 28 Eylül 2026 | **J-130 (🟡) bulundu: makaledeki "SegFormer-B4 tohum oynaması ±0,02" iki farklı kod sürümünü karşılaştırıyordu.** Tablo 12'deki SegFormer-B4 değeri (0,407) artırımın tohumlandığı yeni kodla koşan `tohum_42__2` kaydından; ±0,02'nin öbür ucu olan `tohum_7` (0,425) ve ilk `tohum_42` (0,426) ise artırım tohumlanmadan, eski kodla koşmuş (`artirim_tohumlu` alanı yok). Fark tohumdan değil kod değişikliğinden de geliyor olabilir. Tablo 12'nin öbür dokuz kaydı yeni kodla. **Çözüm:** SegFormer-B4 tohum 7 yeni kodla yeniden koşuluyor (oturum 4); çoklu tohum istatistiği ve §4.4'teki oynama bandı yalnız aynı kod ayarındaki koşulardan hesaplanıyor (revize15/16 betikleri `artirim_tohumlu=True` denetler). |
| 28 Eylül 2026 | **Bölgeler arası genelleme ölçüldü (revize15; §4.4, yeni Tablo 14).** Kaggle oturum 2 ve 3: bir ilin bütün blokları eğitim ve doğrulamadan çıkarıldı, sınama kümesi aynı. Görülmemiş ilde IoU_hasar 0,05–0,10 düşük (%14–25); dört koşunun üçünde çıkarılan il 0,08–0,10 düşerken öteki il değişmiyor (±0,005). "Hatay hariç" U-Net'te eğitim yarıya indiği için etki veri azlığından ayrılamıyor. Kayıtlar `makale/analiz_arsivi/kaggle/sonuclar/` (günlükten `gunluk_ayikla.py` ile). Tablo 14 eklendiği için eski Tablo 14–22 → 15–23; metindeki atıflar, Türkçe ekler ve iki şekil (Şekil 6, 12) güncellendi. |
| 28 Eylül 2026 | **J-131 (🟠) bulundu ve makaleye işlendi: eğitim tohumu oynaması makalede yazan ±0,02'nin çok üstünde (revize16).** Üç tohum (42, 7, 2026), aynı kod: U-Net 0,433 / 0,412 / 0,349 (0,398 ± 0,043), UPerNet 0,425 / 0,357 / 0,396 (0,392 ± 0,034), SegFormer-B4 0,407 / 0,438 / 0,390 (0,412 ± 0,024). Sıralama tohuma göre değişiyor. Sonuçları: (1) MiT-B4 içinde mimari üstünlüğü iddiası kaldırıldı; (2) "belirleyici olan kodlayıcıdır" ön bulguya indi (MiT-B4 ortalamaları ile taban çizgileri farkı ≈ 0,05, SS ≈ 0,04); (3) "bölütleme başarımını artırmak kazancı orantılı artırmıyor" → "modeller arası sınama IoU farkları kazancı öngörmüyor" (ÖZ, Abstract, katkılar, §4.7, §5.1, §6); (4) tatbikattaki "En iyi (U-Net)" etiketi "Büyük" oldu; (5) §4.4'teki kayıplar tek tohumla tohum oynaması mertebesinde, metin bunu söylüyor; (6) yeni sınırlılık: tatbikat modelleri tek eğitim tohumundan. Bütün cümleler `revize16.py`'de ölçülen değerden kuruluyor. |
| 28 Eylül 2026 | **Yardımcı düzeltmesi:** `yardimci.py` `_run_degistir` birden çok run'a yayılan değişimde son run'ın kalanını ilk run'a (ör. kalın başlığa) taşıyordu; "Gözlemler" paragrafı tümüyle kalın çıktı. Düzeltildi; ayrıca önceden tümüyle kalın olan iki tablo başlığı (Tablo 20, 22) "etiket kalın, metin normal" yapıldı. |
| 29 Eylül 2026 | **Bölgeler arası genelleme üç tohumla kesinleşti (revize17; §4.4, Tablo 14).** Kaggle oturum 5 (U-Net) ve 6 (SegFormer-B4): il dışarıda bırakma, tohum 7 ve 2026; tohum 42 ile birlikte üç tohum, birleşik eğitimle tohum başına eşleştirildi. Görülmemiş ilde IoU_hasar üç tohum ortalamasında 0,04–0,08 düşük (%9–22): U-Net Hatay hariç −0,079, Kahramanmaraş hariç −0,037; SegFormer-B4 Hatay hariç −0,055, Kahramanmaraş hariç −0,044. Düşüş 12 eşleşmenin 11'inde. Öteki ildeki ortalama değişim ±0,011 içinde; istisna, eğitimin yarıya indiği U-Net/Hatay hariç (öteki ilde −0,038, veri azlığı). Tek tohumlu ilk aralık (0,05–0,10) oynaktı. ÖZ, Abstract, Tablo 23 ve "tek tohumla" diyen üç cümle güncellendi. Kayıtlar `makale/analiz_arsivi/kaggle/sonuclar/oturum5_*`, `oturum6_*`; betik `makale/analiz_arsivi/revize17.py`. |
| 29 Eylül 2026 | **J-132 (🟠) bulundu ve kapandı: Tablo 1 bu çalışmanın kendi eğitim kümelerini saymıyordu.** Kullanıcı yakaladı. Tablo 1 ("Afet sonrası hasar değerlendirme veri kümelerinin karşılaştırması") sekiz yazın kümesini listeliyor ve Türkiye'ye özgü olanları (TUE-CD, TE23D) ayrıca vurguluyor; ama bölütleme bileşeninin **eğitildiği** KATE-PD ve KATE-CD tabloda yoktu. Kümeler makalenin başka yerlerinde işlenmiş (Tablo 2, §3.2.1, §4.2, Veri Erişilebilirliği, kaynak [56]); eksik olan yalnız bu karşılaştırma tablosuydu. **Sınıf sayısı ölçüldü, kestirilmedi:** yereldeki KATE-PD maskelerinde (`benchmark/reports/kate_pd_*_mask.png`) piksellerin %98,6–99,2'si ≤10, %0,7–1,3'ü ≥245, arada kalan %0,1 kenar sıkıştırma artığı — maske **ikili**; veri kartındaki `label` alanı da YOLO çokgen biçiminde ve sınıf kimliği hep 0. KATE-CD için makale zaten "elle çizilmiş **ikili** hasar maskeleri" diyor. Diğer hücreler makalenin kendi metninden: 832 karo ve 486 çift (§3.2.1, §4.2), Maxar + Pléiades (§3.2.1), yıl 2025 (kaynak [56]). **İkinci bir tutarsızlık daha vardı:** §2.1'deki "Türkiye'ye özgü … bakımından TUE-CD ve TE23D öne çıkmaktadır" cümlesi, tabloya dört Türkiye kümesi girince tabloyu yalanlıyordu; cümle ve devamındaki "Her iki küme de" ifadesi düzeltildi, KATE'leri tanıtan bir cümle eklendi. Betik: `makale/analiz_arsivi/revize18.py`. Denetim: `atif.py` temiz (68 kaynak, 23 tablo, 23 şekil, 17 denklem; tek uyarı `[0]` değişiklikten önce de vardı). Gönderim kopyası yenilendi (204 vurgu kaldırıldı). **Yapılmadı:** PDF sayfa düzeni taraması — iki satır eklenince tablo başlığı sayfa sonuna düşmüş olabilir, Word COM gerektiriyor. |
| 29 Eylül 2026 | **Düzeltme (J-109 ve J-110 kayıtlarına):** o satırlarda *"katalogdaki 13 fotoğrafın hepsi **Hatay ve Adıyaman**'dan"* yazıyor. **Yanlış.** `KUNYE.json`'da "Adıyaman" hiç geçmiyor; doğrusu **dokuzu Hatay/Antakya**, **dördünün ili kaynakta belirtilmemiş** ("in Turkiye", fotoğrafçı Adem). Ben o ifadeyi bir web arama sonucundan çıkarımla yazmışım, kayda dayanmıyordu — kural 1 ihlali ve üstelik şeklin içine gömülmüştü. Utku 27 Eylül'de yakalayıp aracın gösterge metnini (`araclar_makale_uc_kanal.py`), `SIMULASYON_OLCUM_KAYDI.md` §17.5'i ve makale Şekil 10 altyazısını düzeltmiş. Bugün kalan iki bayat yer de düzeltildi: `MAKALE_DEGISIM_LISTESI.md` §F'deki önerilen altyazı ve bu not. **Ders:** şeklin içine gömülen bir ifadeyi künye dosyasından türetmek gerekiyordu, elle yazmak değil. |
| 29 Eylül 2026 | **J-118 kapandı ve J-133 (🟠) bulundu: Tablo 11 doğrulandı, Tablo 15'in metin gecikmesi bayat çıktı.** `KALAN_ISLER` C maddesindeki iki i7 işi yapıldı; makine Tablo 11'in birinci sütunuyla birebir aynı (i7-12700H, 14/20, 16 GB, Windows 10.0.26200). **J-118 (Tablo 11 sürümleri) — doğrulandı, fark yok:** Python 3.12.6, PyTorch 2.13.0 (CUDA yok), Ultralytics 8.4.116, Transformers 5.14.1, NetworkX 3.6.1, OSMnx 2.1.1, pyrosm 0.13.1, FastAPI 0.141.1, segmentation_models_pytorch 0.5.0 — dokuzunun dokuzu tabloda yazanla aynı. **J-133 — Tablo 15'in Türkçe metin satırı karışık kökenli:** örtüşme (11/18) J-111/J-116 düzeltmesinden SONRAKİ sınıflandırıcıya ait ama **gecikme (medyan 36,6 / en uzun 43,0 ms) düzeltme ÖNCESİNDEN**. Aynı makinede düzeltilmiş kodla yeniden ölçüldü: **kararlı medyan 48,2 ± 0,3 ms** (beş koşum: 47,8 · 47,8 · 48,5 · 48,5 · 48,2), **en uzun 52,0–58,9 ms**. Fark **%32** — düzeltme sözcük sınırı için düzenli ifadeyle belirteçleme, Türkçeye duyarlı küçük harf ve kurtarma dalı ekledi, hepsi ek iş. **Ayrıca bir tuzak kaydedildi:** aracın kendi ısınma çağrısı soğuk başlangıcı kapatmıyor — ilk koşum 62,3 / 77,6 ms verdi, sonraki beşi 47,8–48,5 bandında. Raporlanacak değer kararlı banttır. Rapor: `benchmark/reports/kanal_olcumu_metin_i7.json`. **Tablo 15'in metin satırı güncellenmeli** (makaleye dokunulmadı, kullanıcı kararı bekleniyor). |
| 29 Eylül 2026 | **J-134 (🟡) bulundu, AÇIK: makale docx'i Word COM ile PDF'e çevrilemiyor — dönüşüm kaçak döngüye giriyor.** `KALAN_ISLER` 3.5'teki sayfa düzeni taraması için `ExportAsFixedFormat(pdf, 17)` koşuldu (i7-12700H, Word masaüstü). Süreç **takılmıyor**: COM'a yanıt veriyor, `Documents.Count = 1`, `BackgroundSavingStatus = 0`, açık iletişim kutusu yok. Ama **hiç PDF yazmadan** CPU'yu tüketiyor: 196 → 375 → 497 → 504 → **9.450 saniye** (2,6 saat işlemci zamanı), bellek 242 MB'de sabit. Yaklaşık 45 dakika duvar saatinden sonra durduruldu, yarım dosya oluşmamıştı. **Muhtemel sebep:** 23 şeklin bazıları iri (3–6 MB PNG) ve yeniden örnekleme döngüye giriyor olabilir; kesin tanı yapılmadı. **Etkisi:** Tablo 1'e iki satır (J-132) ve Tablo 15'e uzun bir not (J-133) eklendi, bunlar tablo başlığını sayfa sonuna itmiş olabilir — **bu sürümde doğrulanamadı**. LibreOffice bu makinede kurulu değil, alternatif dönüştürücü yok. **Öneri:** Utku'nun makinesinde denensin (o daha önce başarıyla koşturmuş) ya da yazar okumasında gözle bakılsın; `KALAN_ISLER` B maddesindeki okuma bunu zaten kapsıyor. |
| 29 Eylül 2026 | **J-135 (🟠) bulundu ve kapandı: Şekil 21–23'ün üstünde makaleyle ilgisiz amber bildirim şeridi vardı.** Kullanıcı yakaladı ("sarı sarı izler"). Üç arayüz ekran görüntüsünün de tepesinde tam genişlikte bir şerit duruyordu: *"Afet İkaz Bildirimleri Kapalı: Deprem anında anlık acil durum push bildirimi alabilmek için bildirim izni veriniz"* + "Bildirim İznini Aç" ve "Test Alarmı Çal" düğmeleri. Bu, tarayıcının bildirim izni durumundan doğan bir uyarı; makalenin konusuyla ilgisi yok ve üç şekilde de aynı yeri kaplıyordu. **Sınırlar ölçüldü** (`2_risk_skoru.png`, x=760 sütunu ve satır medyanları): navbar y≤64 (15,22,36) · ayırıcı y=65 (39,45,58) · şerit zemini y=66–113 (21,24,40) · amber alt kenar y=114 (84,62,29) · sayfa y≥115 (11,15,23). **Kırpma:** 65–114 arası 50 piksel atıldı, navbar ile sayfa doğrudan birleşti; dikiş gözle denetlendi, iz yok. Görüntü 1600×1050 → 1600×1000. **En-boy oranı da düzeltildi:** belgedeki `wp:extent` ve `a:ext` sabit kalsaydı Word resmi %5 dikey ezecekti; altı değer (3 görsel × 2) `cy` 1724625 → 1642500 EMU yapıldı. `4_isi_haritasi_guzergah.png` de tutarlılık için kırpıldı ama o görüntü belgede **kullanılmıyor** (rId46, kullanım 0). Doğrulandı: docx açılıyor (527 paragraf, 26 tablo), `atif.py` temiz, Tablo 15 ve KATE satırları yerinde. Betik: `makale/analiz_arsivi/revize20.py`. **Not:** navbar'da hâlâ "Örnek Verilerle Simüle Et" düğmesi görünüyor — veri gerçek (risk paneli "Deprem Riskini Hesapla" ile dolduruldu) ama düğmenin karede olması okuyucuyu yanıltabilir; kırpılmadı, karar kullanıcıda. |
| 29 Eylül 2026 | **Kaynakça denetimi yapıldı; bir bulgu (J-136 🟡, AÇIK) ve bir sahte alarm çözüldü.** **Temiz çıkanlar:** 68 kaynağın 68'i gövdede atıflı, atıfsız kaynak yok; listede olmayan atıf yok; **DOI ya da bağlantısı olmayan kayıt yok**; **yinelenen DOI yok** (51 benzersiz DOI, kalan 17 kayıt bağlantılı web kaynağı); yılsız görünen üç kayıt ([7] "2026, çevrimiçi erken yayın", [58] AFAD ve [63] PostGIS erişim tarihli) aslında kurallı. **Sahte alarm çözüldü:** `atif.py`'nin yıllardır verdiği `listede yok: [0]` uyarısı bir kaynak eksikliği değil — atıf deseni matematik aralık gösterimini yakalıyor: "pᵢ ∈ **[0, 1]**" ve "gᵢ ∈ {0, 1}" (Denklem 3 ve 7 çevresi). Kaynakça eksiksiz. **J-136:** kaynaklar **ilk geçiş sırasına göre numaralanmamış**. Gövdede (1. GİRİŞ'ten sonra) **10 sıra bozulması** var: [33]→[19], [66]→[34], [56]→[20], [39]→[7], [64]→[58], [58]→[57], [57]→[6], [68]→[67], [67]→[50], [52]→[51]. Son ikisi komşu numara takası, diğerleri daha büyük sıçrama. Ön sayfalardaki kısaltmalar tablosu sayılırsa bir bozulma daha eklenir ([32], [48], [56], [57], [40] ABSTRACT sonrası terim tablosunda geçiyor). **Şimdi düzeltilmedi, bilinçli:** IEEE ve birçok Türk dergisi ilk geçiş sırası ister ama bazı stiller istemez; hedef dergi henüz seçilmedi (`KALAN_ISLER` A). 68 kaynağı yeniden numaralamak riskli ve stil belli olmadan yapılırsa boşa gider. Dergi seçilince bir kez ve doğru stille yapılmalı. |
| 29 Eylül 2026 | **Sarı vurgular makale dosyasından kaldırıldı (kullanıcı isteği).** Revizyon turlarında değiştirilen cümleler sarı vurguluydu (204 vurgu, 180 metin parçası); `KALAN_ISLER` B'deki yazar okuması bu vurgular üzerinden iç tutarlılık denetimi yapacaktı. Vurgular kaldırılmadan önce **hangi cümlelerin vurgulu olduğu `makale/VURGULU_CUMLELER_2026-09-29.md` dosyasına çıkarıldı** (yer bilgisiyle: paragraf numarası ya da tablo/satır), böylece okuma o liste üzerinden yapılabilir. Yedek: `makale/arsiv/QuakeMind_Makale_YEDEK_pre_vurgusuz_2026-09-29.docx`. Doğrulandı: iki docx'te de kalan vurgu 0, `atif.py` temiz, Tablo 15 ve KATE satırları yerinde. **Not:** artık ana dosya ile `…_GONDERIM_vurgusuz.docx` içerikçe aynı; gönderim kopyasının ayrı tutulmasının tek sebebi vurgulardı, o sebep kalktı. |
| 29 Eylül 2026 | **Belge içi tekrar taraması yapıldı: makale temiz çıktı.** Kullanıcı intihal taramasını sordu; iThenticate/Turnitin erişimi olmadığı için yapılabilecek olan belge İÇİ tekrar taraması yapıldı ve araç depoya kondu: `makale/analiz_arsivi/tekrar.py` (birebir cümle tekrarı + 5-gram Jaccard ile yakın paragraf; kaynakça, altyazı ve kısa cümleler elenir). **Sonuç:** 784 cümlede yalnız **3 birebir tekrar**, 208 paragrafta **2 yakın çift** (eşik 0,33'e indirildiğinde de artmadı). Dördü de meşru: **(1)** İngilizce başlık iki kez — iki dilli başlık bloğu; **(2)** "Adıyaman, Gaziantep, Hatay, Kahramanmaraş, Kilis, Malatya, Osmaniye" il listesi iki kez — Tablo 2'nin KATE-PD ve KATE-CD satırları; **(3)** CRediT beyanlarının benzerliği (0,76) — Furkan ve Utku'nun rol listeleri aynı, ama hemen altında *"yukarıdaki rolleri ortaklaşa yürütmüştür"* yazıyor, yani bilinçli ve açıklanmış; Esra Uray'ın ayrı rolü var (denetim, finansman). **(4) Tek bakılacak nokta:** *"Ölçümler tek bir dizüstü bilgisayarda, grafik işlemci hızlandırması olmadan yapılmıştır."* cümlesi §4.5 ile §5.3(d)'de aynen geçiyor. Sınırlılıklar bölümünün ölçümü yinelemesi olağandır, ama §4.5 revize19'da uzadığı için tekrar daha görünür oldu; yazar okumasında istenip istenmediğine bakılsın. **Not:** bu tarama intihal taraması DEĞİLDİR, dışarıdan kopyalanan metni bulmaz — o, üniversitenin iThenticate aboneliğinden yapılmalı (`KALAN_ISLER` A'ya eklenmeli). |
| 9 Ekim 2026 | **J-137 (🔴) bulundu ve kapandı: zorla kapatılan Word süreci, depoya işlenmiş makale dosyasını sessizce bozdu.** J-134'ün PDF denemelerinden biri `SaveAs2(wdFormatPDF)` ile yapıldı; o da PDF yazmadan CPU tüketti ve süreç **zorla öldürüldü**. Word, öldürülmeden önce kaynak dosyayı kendi iç biçiminde yeniden yazmış: `makale/QuakeMind_Makale_GONDERIM_vurgusuz.docx` **31,2 MB → 18,1 MB** olmuş. Dosya açılıyordu, bozulma hata vermiyordu; **yalnızca boyut uyuşmazlığından yakalandı** (okuma kopyası üretilirken beklenen 31,2 yerine 18,1 okundu). `git status` dosyayı ` M` gösterdi, `git checkout -- <dosya>` ile geri alındı. Geri alma sonrası iki docx de doğrulandı: 31,2 MB · vurgu 0 · Tablo 15 medyan 48,2 · KATE satırları VAR · 26 tablo · çalışma ağacı temiz. **Ders:** Word COM'u makalenin **asıl dosyası üzerinde** çalıştırmak yasak — her zaman geçici bir kopya açılsın; ayrıca `taskkill` ile Word öldürüldükten sonra ilgili docx'in boyutu ve `git status` çıktısı mutlaka denetlensin. Bu bozulma depoya girmemişti çünkü commit öncesi yakalandı; girmiş olsaydı 13 MB'lık görsel kaybı fark edilmeden gönderim dosyasına taşınırdı. |
| 9 Ekim 2026 | **J-134 tanısı tamamlandı (hâlâ AÇIK, çözüm yok).** Üç yol denendi, **üçü de hiç PDF yazmadan** CPU tüketti: **(1)** `ExportAsFixedFormat` tam dosyada — 9.450 s işlemci zamanı, dosya yok; **(2)** `SaveAs2(wdFormatPDF)` — dosya yok, üstelik kaynağı bozdu (J-137); **(3)** görselleri 1400 piksele düşürülmüş **12,5 MB'lık hafifletilmiş kopyada** `ExportAsFixedFormat` — 264 s, dosya yok. Yani **sebep görsel boyutu değil**; hafifletme hiç yardım etmedi, bu yüzden J-134'teki "iri PNG'ler döngüye sokuyor olabilir" tahmini **çürütüldü**. Word'ün kendisi dosyayı sorunsuz açıyor ve sayfalandırıyor (73 sayfa), yalnız PDF motoru çıktı üretmiyor. **Kalan seçenekler:** LibreOffice `--convert-to pdf` (bu makinede kurulu değil), Utku'nun makinesi, ya da Word'ün kullanıcı arayüzünden elle "PDF olarak kaydet". **Yan ürün:** aktarılabilir **okuma kopyası** üretildi — görseller 1400 piksele düşürülmüş, 31,2 MB → 11,3 MB; metin, 26 tablo ve 17 denklem birebir aynı. Depoya konmadı (türev dosya), kullanıcıya doğrudan iletildi. |
| 11 Ekim 2026 | **J-138 (🟠) bulundu, AÇIK: makale §4'teki TE23D sızıntı sayısı (99/118) kaynaksız ve kendi ölçümümüzle çelişiyor.** Kullanıcı TE23D incelemesini sorunca denetlendi. Makale *"sınama karolarının 99/118'inin eğitimde coğrafi komşusu vardır"* diyor; bizim kendi ölçümümüz (`Furkan--Utku--Model_ve_veriseti_aktarımı/AKTARIM_BELGESI.md` §Ç-03) **112/118** veriyor ve ölçütü farklı tanımlıyor: *"en az bir eğitim karosuyla aynı 1024'lük üst karodan geliyor"* (TE23D dosya adı deseni `sahne_satır_sütun_altkaro`'dan çıkarıldı). **99 sayısının kaynağı hiçbir yerde yok:** aktarım belgesi, `RAPOR_BILGILERI.md`, `araclar_makale_yazin_konumu.py` ve depodaki betiklerde geçmiyor. `makale/arsiv/` içindeki **bütün** docx sürümlerinde (pre-revize18'e kadar, 29 Eylül) 99 yazıyor → revize18/19/20'den önce girmiş. **Mantıksal tutarsızlık:** "coğrafi komşu" ölçütü "aynı üst karo"dan daha geniştir, o hâlde sayı 112'den **büyük** çıkmalı, küçük değil. **Neden önemli:** bu, başka bir grubun yayımlanmış kümesine yönelik nicel bir metodoloji eleştirisi; yanlışsa hem hatalı hem de TE23D yazarlarına haksızlık. **Yeniden ölçülemiyor:** TE23D verisi yerelde yok, yalnız `Makale - Kaynaklar/TE23D_…pdf` (3,3 MB) var; karo listesi Google Drive klasöründen yeniden alınmalı. **ÇÖZÜM YOLU BULUNDU (11 Ekim 2026):** sayıya hiç gerek yok — iddia TE23D makalesinin **kendi yöntem cümleleriyle** kurulabilir ve okuyucu doğrulayabilir: *"We divided 15 GeoTIFF images into 1024 × 1024 px patches"* (§III-B) · *"the images were divided into smaller, more manageable 256 × 256 pixel patches"* (§III-C) · *"The dataset was split into three sets: train, validation, and test, with a ratio of 80:10:10, as shown in Table III"*. Her 1024'lük yama en çok 16 komşu 256'lık karo veriyor; bölme 1 183 karo üzerinden oran bazlı yapılmış ve **kardeş karoları birlikte tutan bir kısıt belirtilmemiş** → komşu karoların eğitim ile sınama arasına dağılması yöntemin doğal sonucu. **Öneri:** "99/118" kaldırılsın, yerine bu argüman konsun (sayısız, alıntıyla desteklenen, site kapanmasından etkilenmeyen). **Neden sayı kurtarılamıyor:** 112/118 ölçümü Drive'daki dosya adı listesinden türetilmişti; kullanıcı sayfaya ~Eylül 2026'da erişebildiğini söylüyor ama site artık kapalı → liste yeniden alınamaz, 99 ile 112 arasındaki fark yerelden çözülemez. CLAUDE.md §8 gereği ölçülemeyen sayı iddia edilmez. **Makaleye dokunulmadı**, karar kullanıcıda. İlgili: Ç-03'ün 5. dersi (blok bootstrap güven aralığı) de makaleye girmemiş — yerine üç tohumun ortalama ± SS'si var, o mekânsal değil tohum belirsizliğini ölçer; bilinçli tercih olabilir ama kayıtlı değil. |
| 11 Ekim 2026 | **J-139 (🟠) bulundu ve kapandı: TE23D lisans kaydımız iki kaynağı karıştırmıştı; yazarlara gidecek e-posta taslağı yanlış bir iddia taşıyordu.** Kullanıcı *"makalede '© 2025 TE23D all rights reserved' nerede geçiyor"* diye sorunca denetlendi. **Ölçüm:** TE23D PDF'inin 12 sayfasının tam metni çıkarıldı (`pymupdf`); **"rights reserved" ifadesi makalede hiç geçmiyor.** Makaledeki tek lisans ifadesi 1. sayfa dipnotu: *"© 2025 The Authors. This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 License"* → bu IEEE'nin **makale** lisansı (JSTARS açık erişim dipnotu), **veri kümesinin lisansı değil.** Veri kümesi için makalede tek cümle var: *"The dataset can be reached at https://isl.ce.yildiz.edu.tr/datasets/te23d."* — kullanım koşulu, lisans ya da "upon request" kaydı yok. **Hatalı kayıtlar düzeltildi:** (a) `AKTARIM_BELGESI.md` §Ç-03'teki *"Lisans: belirsiz — sayfada hem CC BY-NC-ND 4.0 hem 'tüm hakları saklıdır' yazıyor"* satırı — CC BY-NC-ND **makaleden**, "all rights reserved" **veri sayfasından**; tek sayfadaki çelişki değil. (b) `makale/lisans_epostalari_taslak.md` §1: gerekçesi *"Makalede TE23D 'CC BY-NC-ND' olarak anılıyor"* diyordu — **bizim makalemiz TE23D'nin lisansını hiç belirtmiyor** (denetlendi: docx'teki bütün lisans ifadeleri kendi veri kaynaklarımıza ait), ve e-posta gövdesi yazarlara *"the distribution page states a CC BY-NC-ND license, while another part of the same page states 'all rights reserved'"* diyordu — **gönderilse yazarlara kendi sayfaları hakkında doğru olmayan bir şey söylenecekti.** Gövde yeniden yazıldı: lisans sorusu doğru kurgulandı, erişim sorusu ve karo koordinatları talebi eklendi. **Doğru durum:** veri kümesinin açık lisansı yok, sayfa tüm hakları saklı tutuyor → "ana eğitime katılmaz" kararı (Ç-03) bu bilgiyle daha da güçlü. **Doğrulanamayan:** veri sayfasının tam metni — site 11 Ekim 2026'da erişilemiyor (80 zaman aşımı, 443 bağlantı reddi, DNS 95.183.138.64), Wayback'te `/datasets/te23d` için **hiç** anlık görüntü yok (yalnız 2010–2018 eski site kayıtları), arama da sayfayı indekslememiş. "All rights reserved" ifadesi **kullanıcının birinci elden gözlemine** dayanıyor: sayfaya ~Eylül 2026'da erişmiş ve alt bilgide bu ifadeyi görmüş; site o tarihten sonra kapanmış. Kayıtlarda tarihli birinci el gözlem olarak etiketlendi — bağımsız doğrulama artık mümkün değil (arşiv kaydı yok). **Makalemize etkisi yok** — makale TE23D'yi yalnız yazın kıyası olarak anıyor, verisini kullanmıyor ve lisansı hakkında bir şey söylemiyor. |
| 11 Ekim 2026 | **J-140 (🟢) TE23D lisansı yazarlardan teyit edildi; "eğitime katılmaz" kararının gerekçesi ortadan kalktı.** Can Ekkazan (TE23D birinci yazarı) ilk e-postamıza ayrıntılı yanıt verdi. **İki bileşen, iki koşul:** uydu görüntüleri **Planet Labs PBC** telifli, Planet'in yazılı izniyle ve yalnız ticari olmayan bilimsel araştırma için paylaşılıyor; **etiketler CC BY-NC-ND 4.0**, TE23D yazarlarınca lisanslı. **İzin verilenler (açık yazılı):** ticari olmayan akademik çalışmada model **eğitimi, doğrulama ve test**; görüntüleri yeniden boyutlandırma; **kendi bölmemize göre yeniden ayırma**; sonuçları (metrik, kıyas, örnek çıktı) akademik yayında paylaşma. **Yasaklar:** veri kümesi/görüntüler/türevleri **yeniden dağıtılamaz**; Planet görüntülerini yeniden üretmeye yönelik modellerde (süper çözünürlük, görüntü üretimi) kullanılamaz — **bölütleme bu kapsamda değil**; ve **TE23D ile eğitilmiş ağırlıklar kamuya açık paylaşılacaksa Planet'ten yazılı onay şart.** **Bu son madde bizi doğrudan bağlıyor:** bölütleme ağırlıklarımız `huggingface.co/Utbird/dispath_optimized_mitb4_focal_dice30` adresinde **açık** yayımlanıyor. Çıkış yolu: TE23D yalnız **dış sınama** olarak kullanılırsa (mevcut KATE ağırlıklarıyla çıkarım) TE23D ile eğitilmiş ağırlık doğmaz ve Planet onayı gerekmez; protokol reprodüksiyonu yapılırsa yalnız metrik yayımlanır, o ağırlıklar paylaşılmaz. Teyit için cevaba yazıldı. **Sahne konum kodları alındı** (dosya adının ilk üç hanesi) — Ç-03'teki *"konum yok"* engeli kalktı: 001–002 Adıyaman-Merkez · 003 Gaziantep-İslahiye · 004 Gaziantep-Nurdağı · 005 Hatay-İskenderun · 006–008 Hatay-Antakya · 010 Hatay-Payas · 011 Hatay-Dörtyol · 013 Hatay-İskenderun · 014–015 Kahramanmaraş-Merkez. **Örtüşme uyarısı:** 003, 004 ve 006–008 bizim üç değerlendirme sahnemizle (İslahiye, Nurdağı, Antakya/Defne) örtüşüyor; KATE-PD/CD de aynı yedi ili kapsadığından TE23D **temiz bir "görülmemiş bölge" sınaması olmaz** — ayak izi paylaşılmazsa en iyi hâlde ilçe düzeyinde ayıklanabilir ve sonuç "aynı bölge, farklı etiketleyici ve sensör" çapraz-küme sınaması olarak raporlanmalıdır. **Eksik:** gönderilen tabloda 13 kod var, makale 15 GeoTIFF diyor → **009 ve 012 sorulacak**. **Can'ın bize sorduğu düzeltme:** *"© 2025 TE23D, All rights reserved" makalede nerede?* → J-139'un sonucu: **makalede değil**, veri sayfasının alt bilgisindeydi; ilk e-postamız iki kaynağı karıştırmıştı. Cevabın ilk maddesi bu oldu, yoksa yazar makalesinde olmayan bir şeyi düzeltmeye çalışacaktı. Cevap taslağı: `makale/lisans_epostalari_taslak.md` §1. **J-138 ile bağ:** cevapta bölme yönteminin (256'lık karo düzeyinde mi, yamaya/sahneye göre gruplanmış mı) doğrudan sorulması J-138'i birincil kaynakla kapatabilir — kendi çıkarımımız yerine yazarın tarifi yazılır. |
| 12 Kasım 2026 | **PR #5 (Deha, Android uygulaması) incelendi ve çalıştırıldı; J-141…J-148 eklendi.** PR dalı ayrı çalışma ağacında derlendi (`:app:assembleDebug` temiz), backend ayrı SQLite ile ayağa kaldırıldı, uygulama Android 36 emülatöründe gerçek uçlara karşı denendi; `test_mobile_*.py` 12/12. **En ağırı J-141 (🔴):** sunucu yokken eşitleme worker'ı ~150 bağlantı/sn ve %112 CPU ile sonsuz döngüde (80 sn'de ~12 000 bağlantı). J-142 (form alanları sunucuya gitmiyor), J-143 (ihbar formunda GPS yok, harf klavyesi), J-144 (risk etkenleri atılıyor, ekran yanlış bilgi veriyor), J-145 (misafir ucu sınırsız → kişi başı sınır aşılıyor) 🟠; J-146 karar bekliyor (birleştirme sırası, `backend/` yeniden adlandırma, mobil kapsamı); J-147/J-148 küçükler. Bulgular PR'a genel yorum ve satır yorumları olarak yazıldı; düzeltme PR sahibinde. |
| 12 Kasım 2026 | Utku (`07e3bfb`, PR #4) ve Deha (PR #5) değişiklikleri teslim hazırlığı için tarandı. **J-149** (yeni): üründeki risk modeli GEM fay mesafesiyle yeniden eğitildi, makaledeki risk tablosu bu koşuyla uyuşmuyor. |
| 12 Kasım 2026 | Teslim hazırlığı: proje `teslim-toparlama` dalında (main + `07e3bfb`) ayağa kaldırıldı. API, konsol, giriş, risk (81 il) ve tatbikat uçtan uca denendi. **J-150** ve **J-154** kapatıldı (tatbikat paneli null çökmesi; kıyas kollarının dakikaya yuvarlanması). Yeni: **J-151** (il merkezleri yerel üretim, 4 dk), **J-152** (risk uçlarında yetki yok), **J-153** (deprem kataloğu 3 ay bayattı; elle tazelendi, model yeniden eğitildi). |
| 12 Kasım 2026 | **J-155** (yeni): saha ekibi ekranına girilemiyordu. Saha test hesabı açıldı, ekibe bağlandı, `DEMO_CALISTIRMA.md`'ye yazıldı; rol verme ekranı eksik. |
| 12 Kasım 2026 | **J-155**: konsola Kullanıcılar (rol yönetimi) modu eklendi. Koordinatör afetzede ↔ saha, yönetici her rol; kimse kendi rolünü değiştiremez. `tests/test_oturum_rol.py` 7/7 geçti. |
| 12 Kasım 2026 | **J-156**: giriş üç kapıya ayrıldı (kapı rol vermez, sunucu denetler). Ekip ve koordinasyon hesaplarını konsoldan koordinasyon açıyor; tek seferlik şifre ve şifre yenileme eklendi. Testler 12/12. |
| 13 Kasım 2026 | **J-157**: Hesaplar tam sayfa oldu (tablo, düzenle-kaydet çekmecesi, kayıt defteri). Askıya alma, ilk girişte zorunlu şifre değiştirme (sunucuda 403) ve hesap işlemleri kayıt defteri eklendi. İstemcide hesap uçlarında jeton yenilemesi düzeldi. Testler 16/16. |
| 13 Kasım 2026 | Belgeler SQLite gerçeğine göre düzeltildi (CLAUDE.md, MIMARI.md, PROJE_DOSYASI.md: bugün SQLite, PostGIS hedef). **J-158**: SQLite yük ölçümü; ham yazma ~4 000/sn ama karışık yükte yazma p95 1–2,8 sn (tek bağlantı + olay başına tam liste). **J-159** kapatıldı: SOS ve ihbar kimlikleri 32 bitten 64 bite. |
| 13 Kasım 2026 | **J-158** iyileştirildi: okuma bağlantıları, `/api/ozet` SQL'de sayıyor (100 bin üstünde eksik sayma hatası da kapandı), kapsayıcı indeksler (afetzedenin kendi çağrıları 1 milyon satırda 10 sn → < 1 ms), konsolda 1 sn tazeleme birleştirme. Afet senaryosu (50 SOS/sn, 5 konsol, 100 bin satır): yazma p95 723 → 0,8 ms, güncellik p95 6,1 → 1,07 sn, kaybolan mesaj 103 → 0. Artımlı tazeleme açık. |
| 13 Kasım 2026 | **J-160** (kullanıcı bildirdi, kapatıldı): hasar analizi Defne/Elektrik drone görüntüsünde 0 kapalı yol buluyordu. Alan görüntüye taşınmıyordu ve sunucu sessizce z17'ye iniyordu. Görüntü seçimi alanı taşıyor, düşük kapsamada başlatma kapalı, sunucu açıklamalı hatayla duruyor. Aynı görüntüde z18'de 8 kapalı yol. |
| 13 Kasım 2026 | **J-161** (kullanıcı istedi, kapatıldı): hasar analizi ekranı yeniden düzenlendi. Görüntü → alan → başlat adımları, aşamalı ilerleme ve büyük sayılı sonuç. Panel genişlik sıçraması giderildi. Yanıltıcı 2,5 / 4 km hazır ayarları kaldırıldı (tek koşu ~1 km²). İsteğe bağlı yakın çekim (z19) eklendi; Defne'de 8 → 19 kapalı yol, doğruluk ölçülmedi. |
| 13 Kasım 2026 | **J-152** kapatıldı: risk tahmini giriş istiyor; canlı veri tazeleme ve `refreshData` yalnız koordinasyonda. Eski web ve Flutter'ın risk ekranları 401 alır. |
| 17 Kasım 2026 | **J-162**: saha ekibi görev ekranına kapanmalardan kaçınan rota haritası eklendi (tembel yükleme). Rolüne kapalı konsol modları adresten de açılmıyor. Karar: saha konsolu görür, koordinasyon işleri kapalı (J-163). |
| 17 Kasım 2026 | **J-163** kapatıldı: ekip gönderme sunucuda ve ekranda yalnız koordinasyonda; Acil bildirim ve Simülasyon saha ekibine görünmüyor. Oturumsuz 14 eski/araştırma ucu `QUAKEMIND_ESKI_UCLAR` bayrağının arkasına alındı, tanı görseli giriş istiyor. Yeni `tests/test_uc_yetkileri.py` (18). |
| 17 Kasım 2026 | **J-164** kapatıldı: konsol üst çubuğu 1024 px'te 202 px taşıyordu (çıkış ve Canlı rozeti ekran dışında); 1280 altında yazılar simgeye iniyor, sağ denetimler hep görünür. Kullanıcılar sayfası yüklenirken sayıları 0 yerine "—" yazıyor. |
| 17 Kasım 2026 | **J-165** kapatıldı: kamera tespiti çatlağa "binayı derhal boşaltın" diyordu (tek sınıflı modelin güveni şiddet sayılıyordu); derece artık yalnız bina modelinin sınıfından. Silinmeyen işlem kaydı: analizler, sevk, SOS/ihbar, ekip, bildirim (18 tür). Kamera sonucu numaralı kutularla ve tam ekran incelemeyle. `tests/test_islem_kaydi.py` (10). |
| 17 Kasım 2026 | **J-167** açıldı: uçtan uca tarama (yalıtılmış kopyada, 4 rol, 54 kontrol). Giriş ve SOS sınırsız (S-1, S-2), kamera ucu bilinmeyen modelde "temiz" diyor (S-3), metin modeli örnek cümlesinin adresini bulamıyor (F-1), Yol ve Rota sayfası ve zaman şeridi ölü (F-3, F-4), saha ana düğmesi telefonda ekran dışında (U-1); iki backend testi kırık (T-1). |
| 17 Kasım 2026 | **J-166** kapatıldı: işlem kaydına hash zinciri (artımlı doğrulama: 100 bin kayıttan sonra 100 yeni kayıt 2,9 ms; tam tarama 3,1–3,4 sn), giriş geçmişi (başarısızlar ve nedenleri), kişisel veri görüntüleme kaydı (10 dk'da bir), silinmeyen ekip konum geçmişi. J-167 S-3, P-6 ve T-1 düzeltildi; `pytest -q` 76/76. |
| 17 Kasım 2026 | **J-168** açıldı: eski web kamera sayfası API'ye ulaşamayınca %96,2 güvenli uydurma "bina ağır hasarlı" sonucu gösteriyor; düzeltme kararı kullanıcıda (§7). |
| 17 Kasım 2026 | **J-167 Grup B** (güvenlik) düzeltildi: giriş denemesi sınırı (S-1, 6. hatalı denemede 429, sayaç SQLite'ta), hesap başına tek açık SOS ve dakikalık sınır (S-2, U-3), API belgeleri varsayılan kapalı (S-4), canlı akış oturumu 15 sn'de bir denetliyor (S-6). S-3 J-166'da, S-5 Grup D'ye bırakıldı. Yeni `tests/test_hiz_siniri.py` (11); `pytest -q` 87/87. Canlıda Nginx arkasında `QUAKEMIND_VEKIL_GUVENILIR=1` açılmalı. |
| 17 Kasım 2026 | **J-167 Grup C** (saha ve giriş arayüzü) düzeltildi: saha adım düğmeleri telefonda yapışkan alt çubukta (U-1, "Yola çıktık" 375×812'de kaydırmadan görünüyor), giriş ekranı sunucu açılırken insan diliyle yazıyor (U-2) ve `/api/hazir` ucu (P-5), tatbikat lejantı varsayılan kapalı (U-4), afetzede kartları ve yer satırları ekran okuyucuya adlı (U-6). |
| 17 Kasım 2026 | **J-169** kapatıldı: başarısız bir yazma açık işlem bırakıp veritabanını kilitliyordu; 14 yazma bloğu hata anında geri alıyor. `pytest -q` 89/89. |
| 17 Kasım 2026 | **J-170** kapatıldı (kategori kararı hariç): metin analizinde adres yerel dizinden (metin dışarı gitmiyor), düzey ve sapma payıyla; model işçide; kişi, ihtiyaç, işaret çıkarımı ve kategori uyarısı. 22 metinlik kümede beklenen yer 7/12 → 11/12, 1,5 km içinde 5/12 → 10/12. Konsolda yazılı ihbar kuyruğu, vurgulu sonuç kartı ve haritada sapma çemberi; afetzede akışı iki adım. J-167 F-1, P-2, S-5 kapandı. `pytest -q` 104/104. |
| 17 Kasım 2026 | **J-170** ek: "Cumhuriyet meydanında ölüler var 2 tane" ilgisiz ve adressiz çıkıyordu. Meydan adres türü, ölü işareti ve "N tane" sayımı eklendi; model ilgisiz dese de ağır işarette uyarı. `pytest -q` 107/107. |
| 18 Kasım 2026 | **J-171** kapatıldı: araç rotası kenar tabanlı (dönüş yasağı, U dönüşü yalnız çıkmazda, dönüş bedeli, göbek, yola yönüyle oturtma, zincirle küçültülmüş graf). Dönüş yasağı ihlali 16 → 0; arama şehirde 22,9 → 13,4 ms. Konsol "Yol ve rota" bağlandı. J-167 Grup E (F-3…F-7) kapandı. `pytest -q` 118/118. |
| 18 Kasım 2026 | **J-172** kapatıldı: haritada türe göre ayrı simgeler (şekil + glif + renk), hastane katmanı, yakınlaştırma eşikleri, sayfa üstünde bilgi kartı, lejant olan sade katman paneli, kaynak ağırlıklarında dört seçenek. Grup F: ısı soğuk 4,3 sn → 44 ms (PostGIS denemesi), tatbikat görüntüsü 2,75 → 0,03 sn (disk önbelleği); P-1 ölçüldü (kritik yol 153 KB), ertelendi. `pytest -q` 123/123. |
| 18 Kasım 2026 | **J-173** kapatıldı: deprem riskinde eşzamanlı istekte başka ilin sonucu dönüyordu (40'ta 35 → 0); hesap iş parçacığı güvenli ve önbellekli (ortanca 162 → 30 ms). Uzun vadeli tehlike artçısız (Gardner–Knopoff) ve katalog süresiyle (81 il ortancası 0,63 → 0,53). İki açık uç kapandı. Ekran 81 il sıralaması, haritada risk renkli iller ve bileşen kartlarıyla yeniden. `pytest -q` 127/127. |
| 18 Kasım 2026 | **J-174** kapatıldı: uçtan uca akış 48 adımda dört hesapla sınandı (`araclar_akis_senaryosu.py`). Canlı akış ilk jeton yenilemesinde kalıcı kapanıyordu (bütün roller), düzeltildi. Saha akışına işlem kaydı işareti gitmiyor. İhtiyaç geçen yazılı ihbar ihtiyaç sayfasına düşüyor. Afetzede ihbarına gelen ekibi ve "olay sürüyor" durumunu doğru görüyor. Yüklenirken "veri yok" yazılmıyor. `pytest -q` 131/131. |
| 18 Kasım 2026 | **Temizlik.** Açık görünen ürün maddeleri birleşik dalda (UtBird/QuakeMind#12) kodla ve ölçümle doğrulandı. 22 madde güncellendi: J-07, J-09, J-11, J-13, J-18, J-37, J-45, J-46 (ölçüldü: boşta 137 sn'de 0 istek), J-50, J-59 (sayıldı: 116 uçtan 6'sı oturumsuz, hepsi olması gerektiği gibi), J-141–J-145, J-148, J-146, F-01, F-02 kapandı; J-15, J-147 kısmen; J-167 büyük ölçüde. Durum satırı KAPALI ya da DÜZELTİLDİ olan 92 madde değiştirilmeden `EKSIKLER_ARSIV.md`'ye taşındı; burada dizin ve baştaki özet kaldı. Taşımada satır kaybı yok (betikle sayıldı: 175 madde, bütün satırlar iki dosyada). |
| 18 Kasım 2026 | **J-175** kapatıldı: genel durum ısı haritasında renk kaynağı, koyuluk yoğunluğu gösteriyor; üzerine gelince kaynak payları. Listeler, sayılar ve ısı aynı pencerede. Sağ panel "Şimdi / Uydu hasarı / Açık ihbarlar". Genel mod açılışı 16 istek / 993 KB → 13 / 201 KB. Madde arşivde. |
| 18 Kasım 2026 | **J-176** kapatıldı: giriş ekranında hesap açma kipinde kapı seçicisi gizli; bütün şifre alanlarında göster/gizle ve büyük harf uyarısı; zemin gerçek veriden okunur bir Türkiye haritası (fay türü renkte, kayma hızı kalınlıkta, 6 Şubat 2023 depremleri, OSM yol silüeti), açılışta bir kez belirir, yalnız geniş ekranda iner (gzip 20,2 KB). Madde arşivde. |
| 18 Kasım 2026 | Toplanma alanları genel durum, SOS kuyruğu ve ekipler modlarının varsayılan katmanlarına geri eklendi. J-172'deki sadeleştirmede SOS ve ekipler modlarından çıkarılmıştı; kullanıcı "acil toplanma alanlarını göremiyorum" dedi. Veri sağlamdı (AFAD dosyası yerinde, API Antakya'da 129 alan veriyor); simgeler yalnız z11 ve üstünde çizilir. |
| 18 Kasım 2026 | **J-177** kapatıldı: konsol yazı ölçeği bir kademe büyük (12 px'te yalnız etiket; genel %91 → %13). Acil bildirim uçtan uca sınandı (senaryo 61/61); saha ekibi ekranı bildirimi hiç göstermiyordu, duyuru bandı ve listesi eklendi; bildirim sayfasında önem rengi, bölge önerisi, yayın süresi, 5'ten fazla uyarısı. J-167 Grup G bitti. |
| 20 Kasım 2026 | **J-178** kapatıldı: harita adları okunur (sokak 14 px ink-2, mahalle 14 px kalın beyaz, kalın hale). Madde arşivde. |
| 23 Kasım 2026 | **J-180** kapatıldı: afetzede haritasında 3 km çevresindeki kapalı yollar (kırmızı çizgi) ve hasar bildirilen bölgeler (~250 m kare, SOS sayılmaz, en az 3 bildirim) yeni `/api/afetzede/cevre` ucuyla; lejant, bilgi kartı, aç/kapa. Toplanma alanları ülke iskeleti yüzünden 422 alıyordu, düzeltildi. `pytest -q` 153/153. Madde arşivde. |
| 24 Kasım 2026 | **J-181** kapatıldı: rota kapanmayı çizgisiyle eşler (kaçan kenar 4 → 0); tehlike verisi yalnız değişince okunur (100 000 kayıtla istek başı 1240 → 36 ms) ve süzme SQL'de (eski sınır kayıt atlıyordu); aynı kapalı parça bir kez (356 → 48). Dış servis yedeği alternatifleri ve iki yandan sapmayı kapanmalara karşı denetler, temiz yol yoksa açıkça söyler. Harita ve rota aynı kapanma kümesine bakar. Madde arşivde. |
| 24 Kasım 2026 | **J-182** kapatıldı: ilk yönetici sunucuda `araclar_kullanici.py ilk-yonetici` ile (yalnız yönetici yokken, rastgele geçici şifre, ilk girişte değişir, defterde kayıt); `sifre-sifirla` eklendi; açık varsayılan şifre kalktı. Kurulum belgesinde "İlk hesaplar" bölümü. Gerisi konsoldan. `pytest -q` 164/164. Madde arşivde. |
| 24 Kasım 2026 | **J-183** kapatıldı: dört rol için ortak örnek hesap (şifre ortam değişkeninden, uygulamadan değişmez); üç ekranda aynı profil menüsü (Hesap ayarları, Çıkış yap) ve `/hesap` sayfası; telefonda afetzede üst şeridi taşmıyor. Madde arşivde. |
| 24 Kasım 2026 | **J-184** kod tarafı kapatıldı: canlıda `roads.gpkg` ve üç model ağırlığı yok (depoya girmiyorlar). Yol dosyası artık kalıcı veri biriminde aranır; boş yol katmanı nedenini yazar; `/api/hazir` eksikleri gösterir; `deploy.sh` kaynağı olan bütün modelleri hazırlar. Dosya kopyalama adımları `deploy/README.md`'de, Deha'da. Madde arşivde. |
| 24 Kasım 2026 | **J-185** kapatıldı: tatbikat sağ paneli soruya göre (sonuç, tıklanır görevler, katman açan bulgu kutuları, katlanır ayrıntılar); görev seçince harita yalnız o çifti çizer; varsayılan iki çizgi; ekip 'gerçek tesis' ve kapanma yarıçapı metni düzeltildi; ağırlığı olmayan modelle başlatma kapalı. Canlıda koşması J-184'teki dosyalara bağlı. Madde arşivde. |
| 24 Kasım 2026 | **J-186** kapatıldı: TATBİKAT şeridinde (her modda) onaylı "Tatbikatı bitir"; sunucu koşuyu tanımasa da noktaları siler; açılışta sahipsiz tatbikat noktaları silinir (kopya veritabanında 296 nokta bulundu); kimlik biçimi denetlenir. `pytest -q` 171/171. Madde arşivde. |
| 24 Kasım 2026 | **J-187** kapatıldı: üç model `Furkei/quakemind-uydu-modelleri`, OSM kesiti `Furkei/quakemind-osm-yollar` (ODbL) depolarında; künyeler ve `araclar_osm_indir.py` sabit sürümle indirir, `deploy.sh` kurar. Anahtarsız indirme ve parmak izleri doğrulandı. J-184'teki elle kopyalama artık gerekmiyor. Madde arşivde. |
| 24 Kasım 2026 | **J-188** kapatıldı: `il_merkezleri.json` depoya (`apps/earthquake_risk/data/`); `deploy/test_road_api.py` eski uçlarda bayrağı test içinde açar. Sunucu paket sürümleriyle temiz kopyada 163 geçti, 0 hata. Madde arşivde. |
| 24 Kasım 2026 | **J-189** açık madde eklendi: makale §4.1 "mekânsal sorgular PostGIS ile" diyor, sistem SQLite (18 Kasım'da başka oturumda "J-175" diye not edilmişti, numara çakıştığı için J-189). Makaleye dokunulmadı. |
| 24 Kasım 2026 | **J-38** kapatıldı: yol ağı kurulamazsa sonuç ve konsol "hesaplanamadı" der, "0 kapalı yol" / "kapanma yok" demez (`roadNetworkMissing`, `oneri_metni`). **J-168** kapatıldı: eski web kamera sayfası API'ye ulaşamayınca uydurma sonuç yerine "Analiz yapılamadı" gösterir. `pytest -q` 177/177. Maddeler arşivde. |
| 24 Kasım 2026 | **J-190** kapatıldı: Yol ve rota baştan; iki nokta (A/B) ve sıralı çok duraklı rota; hasar ekranının yarım çokgeni artık taşınmıyor; araç kapalı yoldan yalnız başka yol yoksa geçer ve söyler; kapanma eşleşmesi en yakın kenar + en az 3 nokta; kapanma durumu (kapalı / açıldı / yanlış alarm) konsoldan değişir, işlem kaydına ve canlı akışa gider. 186 test geçti. Madde arşivde. |
| 24 Kasım 2026 | **J-191** kapatıldı: deprem riski ekranı baştan (il seçilince yalnız skora giren depremler ve hesap alanı; olasılıklar soru cümlesiyle; deprem listesi haritayla bağlı); harita noktaları uzakta sayılı kümeler (toplanma, sağlık, ekip, ihbar, SOS); logo genel duruma götürür. **J-192** açık madde: katalogda yer adlarında "?" (kaynak veride). |
