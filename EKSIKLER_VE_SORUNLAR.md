# QuakeMind — Eksikler ve Sorunlar Takip Dosyası

Bu dosya, makale ve proje üzerinde tespit edilen her eksik, hata ve açık konuyu
tek yerde tutar. Amaç hiçbir sorunun gözden kaçmaması ve sonradan geri dönülebilmesidir.

**Son güncelleme:** 12 Eylül 2026 (ikinci tur — bkz. değişiklik günlüğü)
**Nasıl kullanılır:** Her maddenin bir kimliği var (örn. `M-01`). Kapatınca durumu
`KAPALI` yapın ve kapanış tarihini yazın; satırı silmeyin — geçmiş kalsın.

## Önem dereceleri

| Kod | Anlamı |
|---|---|
| 🔴 KRİTİK | Hakem tek başına ret gerekçesi sayabilir; gönderimden önce mutlaka çözülmeli |
| 🟠 YÜKSEK | Gönderimden önce çözülmeli; çözülmezse ciddi revizyon isteği gelir |
| 🟡 ORTA | Makaleyi güçlendirir; eksikliği savunulabilir ama zayıflatır |
| ⚪ DÜŞÜK | Biçim, adlandırma, düzen |

## Durumlar

`AÇIK` · `DEVAM EDİYOR` · `KAPALI` · `KARAR BEKLİYOR` (kullanıcı kararı gerekiyor)

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
oranlarıyla (%1,58 / %1,71) kalibrasyonu yaz. Kod referansı: `QuakeMindBackend/benchmark/`.

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

## A-14 🔴 Geçilebilirlik kuralı adları ve tanımları makale ile kodda ters
**Durum:** KAPALI (16 Eylül 2026) — kullanıcı tercih belirtmedi; makale koşulan koda uyduruldu (M-76) · **Bulundu:** 16 Eylül 2026 · **Birleşik liste:** M-76 · **İlgili:** E-01, J-28, J-29, M-26

Makale (Bölüm 3.2 P87, Tablo 4, 4.3, 4.8, Tablo 19): **katı** = Destroyed + Damaged kapalı;
**dengeli** (esas) = Destroyed kapalı, Damaged yumuşak ceza; **gevşek** = yalnız Destroyed kapalı.
Kod (`benchmark/copernicus_ground_truth.py:158`): `strict` = yalnız Destroyed; `medium` =
Destroyed + Damaged; `loose` = + Possibly damaged. Yani makaledeki **gevşek = kodun strict**'i,
makaledeki **katı = kodun medium**'u; kodun `loose`'u makalede yok; makalenin **esas aldığı
dengeli kural hiç koşulmadı** (E-01: "Damaged = ağırlık cezası uygulanmadı").
J-28, J-29 ve devir belgesi Türkçe "katı/orta/gevşek" adlarını **kod anlamında** kullanıyor.
Bu adlarla sayılar makaleye taşınırsa bir kurala ait sonuç başka bir kurala atfedilir.

**Yapılacak.** Kullanıcı kararı: (a) makalenin tanımlarını koşulan kodla hizala, ya da
(b) dengeli kuralı (Damaged = yumuşak ceza) kodda uygulayıp 10 tohumla koş. Karar verilene
kadar Tablo 13 "Kural" sütunu, Tablo 19, Bölüm 4.8 ve EMSR satırları yazılmayacak.

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

## A-22 🟠 Veri artırımı tohuma bağlı değildi — "tohum 42" koşuları tekrarlanabilir değil
**Durum:** DÜZELTİLDİ (22 Eylül 2026) — 02/03 defterinin üreteci (`araclar/defter_dokuz_model.py`): `tohumla()` artırımı da tohumlar, DataLoader işçileri torch'un işçi tohumundan yeniden tohumlanır; sonuç kaydında `ayarlar.artirim_tohumlu = true` · **Bulundu:** 22 Eylül 2026 (öncesi + sonrası deneyi eklenirken yerel duman testinin iki koşusu farklı çıktı) · **İlgili:** A-15, B-11

albumentations 2.x `random.seed` / `np.random.seed` / `torch.manual_seed`'i dikkate almıyor: aynı tohumla iki süreçte
aynı dönüşüm farklı sonuç verdi (ölçüldü, 2.0.8). Bu yüzden 21–22 Eylül'deki bütün eğitimlerde (Colab P2, P2_qqb; Kaggle
oturum 1 ve 2) artırım tohumdan bağımsızdı: aynı tohum aynı sonucu vermez; tohumlar arası oynamanın bir kısmı buradan
(Colab–Kaggle P2 farkı 0,455 / 0,435 de kısmen). Düzeltmeden sonra yerelde aynı tohumla iki koşu birebir aynı (CPU;
GPU'da cuDNN'in küçük sayısal farkları kalabilir). 10 model tablosu düzeltilmiş defterle koşulacak; makalede tekrarlanabilirlik
cümlesi buna göre yazılmalı ve önceki koşular "artırım tohumsuz" diye ayrılmalı.

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

## B-09 🟡 Donanım künyesi ve `v_ort`
**Durum:** KAPALI (16 Eylül 2026) — Tablo 12'ye ve Bölüm 3.8'e işlendi (M-22); önceki durum: KISMEN KAPALI (15 Eylül 2026) — üç bilginin üçü de artık elde:
· **`v_ort` = 15,0 km/sa** (`benchmark/naive_baseline.py:48`; kodda "afet sonrası
molozlu sokakta ortalama saha ilerleme hızı varsayımı" olarak yorumlanmış — bir
**ölçüm değil varsayımdır**, makalede öyle sunulmalıdır)
· **Eğitim ortamı:** Google Colab, NVIDIA Tesla T4
· **Senaryo ortamı:** Intel Core i7 14. nesil, 16 GB RAM, 512 GB SSD, Intel Iris Xe
(tümleşik, GPU hızlandırma yok)
Kalan iş: bu değerlerin Tablo 11'e ve Bölüm 3.8'e işlenmesi (M-22).

Tablo 11'de senaryo koşum ortamı ve eğitim ortamı boş. Ortalama hız `v_ort`
süre hesabının temel parametresi ama sayısal değeri makalede hiç verilmemiş.

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

`QuakeMindBackend/apps/road_damage/utils/fetcher.py` içinde
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

## E-05 🟡 Telafi iddiası kurgu gereği
**Durum:** KAPALI (12 Eylül 2026)

Elenen iki çağrının SOS üzerinden kurtarılması, senaryoda paralel SOS kaydı
bulunduğu için kurgu gereğiydi. Makalede "yedeklilik potansiyeline işaret eder,
gerçekleştiğini göstermez" olarak düzeltildi.

## E-06 🟡 Örneklem büyüklüğü
**Durum:** KAPALI (16 Eylül 2026) — 10 tohum koşuldu (J-29)

18 afetzede, 9 bölge, tek tohum. Çoklu tohum protokolü tanımlı ama koşulmamış.
Öneri: 10 tohum × kaynak, ortalama ± standart sapma.

**16 Eylül 2026:** Göksun çıkarıldı → 8 bölge, 18 afetzede. Eşleştirilmiş deney
(J-28) EMSR kapsamındaki 4 ilçede 13, drone sahnelerinde 9 afetzedeyle koşuldu;
hepsi yine **tek tohum (42)**. Madde açık.

**16 Eylül 2026 — kapanış.** J-28'in dokuz yapılandırması 10 tohumla (42–51) koşuldu:
`benchmark/multi_seed.py`, 90 koşu, hatasız; tohum 42 tek tohumlu koşuları afetzede
yerleşimi dahil birebir yeniden üretti. Sonuçlar ortalama ± ss ve %95 GA olarak
`runs/multi_seed/multi_seed_tablo.md` içinde; yorum **J-29**'da. Afetzede sayısı
(13 / 18 / 9) değişmedi — tohum yalnız yerleşimi ve sentetik kapanmayı değiştiriyor.

---

# F. GİT VE SÜREÇ

## F-01 KARAR BEKLİYOR — 15 commit upstream'e gönderilmedi
**Durum:** KARAR BEKLİYOR

Yerel `main`, `upstream/main`'in (UtBird/QuakeMind) 15 commit ilerisinde.
`origin/main` (Femrei/QuakeMindDev) ile birebir aynı.
Kullanıcı şu an gönderim istemiyor.

## F-02 KARAR BEKLİYOR — 123 commit edilmemiş dosya
**Durum:** KARAR BEKLİYOR

14 değiştirilmiş + 109 izlenmeyen dosya. İçinde makale taslakları, senaryo
koşuları, benchmark çıktıları var. Hangisinin depoya gireceği karar bekliyor.

## F-03 ⚪ `makale` dalı yerele alındı
**Durum:** KAPALI (12 Eylül 2026)

`git worktree` ile `Desktop\2209-A Afet\QuakeMind_makale\` klasörüne alındı.
Ana çalışma ağacına dokunulmadı. Kaldırmak için:
`git worktree remove "C:/Users/femre/Desktop/2209-A Afet/QuakeMind_makale"`

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

## H-01 ✔ Tablo 12'deki 0,4276 ile Tablo 22'deki ROC-AUC 0,4276 çakışması
**Durum:** KAPALI (12 Eylül 2026)

Kopyala-yapıştır hatası **değil**, gerçek rastlantı. Tablo 12 →
`optimized_training_colab.ipynb` "En iyi Val IoU: 0.4276"; Tablo 22 →
`05_risk_skoru/.../leaderboard.csv` ÇKA satırı `0.42759818884895767`. İki bağımsız
kaynak. Düzeltme gerekmiyor; isteğe bağlı olarak Tablo 22'de beş hane yazılabilir.

---

## H-02 ✔ Karolama adımının örtüşmesiz olduğu şüphesi
**Durum:** KAPALI (12 Eylül 2026)

`build_notebook.py`: `tile_size, tile_stride = 512, 256`. %50 örtüşme gerçektir,
makalenin sızdırma uyarısı geçerlidir.

> **16 Eylül 2026 eki (makale listesi M-89):** Kodda örtüşme var, girdide yok. KATE-CD ve MEDBFS görüntüleri zaten
> 512 × 512 (MEDBFS `Turkey.zip` dizini Zenodo'dan HTTP Range ile okundu; SegFormer defteri 842 görüntüden 842 karo
> üretmiş, **842'sinin tamamı hasarlı**). Bu koşumda örtüşen karo ve %95 elemeyle çıkarılan karo **yok**. Makale düzeltildi.

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

## J-13 🟠 Geocoding hala aga bagli — yerel cozum yok
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026 · **J-03'ten ayrildi**

J-03'te kalici onbellek eklendi ve TEKRAR eden sorgular 0,3 sn'ye dustu, ancak
**ilk** (onbellekte olmayan) sorgu hala canli Nominatim'e gidiyor — olculdu:
7–10 sn, en kotu durumda ~28 sn. Bu, offline-first hedefiyle dogrudan celisiyor:
internet yoksa NLP metinden konum cikaramiyor.

**Yapilacak.** `tr_locations.py` su an yalnizca il/ilce **adlarini** tutuyor,
koordinat yok. Il/ilce/mahalle merkez koordinatlarini iceren yerel bir
sozlugu birinci siraya koy, Nominatim yalnizca son care olsun. Ayrica
`_build_queries` tek metinden 23 sorgu adayi uretiyor; bu ~4'e indirilebilir.

**DIKKAT — bu bir davranis degisikligidir.** Cozulen konumlar degisebilir,
dolayisiyla makalede raporlanan NLP konum-cikarim sonuclarini etkiler; senaryo
yeniden kosulmadan yapilmamali (bkz. E-04).

---

## J-18 🟡 `/status/{id}` tek seferde 17 MB dönüyor — 15,5 MB'ı base64 görsel
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

**Ölçüm.** Tamamlanmış bir `/analyze` işinin durum yanıtı **17 159 639 bayt**;
bunun 15,5 MB'ı altı adet base64 gömülü PNG (`imageOriginalB64`,
`imageDamageOverlayB64`, `imageDamageMaskB64`, `imageRoadMaskB64`,
`imageIntersectionB64`, `imageSegmentationOverlayB64`).

**J-01 ile aynı sınıf DEĞİL — daha hafif.** `pollRoadDamageStatus` (api.ts:299)
`done` görünce döngüden çıkıyor, yani ağır yük **bir kez** çekiliyor; kuyrukta
bekleyen turlar hafif. Yine de base64 ham baytı %33 şişiriyor (~4 MB fazladan)
ve 17 MB'lık tek bir JSON ayrıştırması tarayıcıyı bir an dondurur.

**Yapılacak.** Görselleri JSON gövdesine gömmek yerine
`/api/road_damage/image/{analysisId}/{kind}` gibi ikili uçlardan sun; `/status`
yalnızca adlarını döndürsün. Tarayıcı bunları paralel ve önbellekli çeker.

---

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

## J-23 🔴 `/naive_compare`, `/analyze` oturumlarıyla çalışmıyor — senaryo modele bağlanamaz
**Durum:** KAPALI (16 Eylül 2026) · **Bulundu:** 16 Eylül 2026

**Sorun.** `/analyze` işi bitince oturuma yalnız `{"safe_G", "bounds"}`
yazılıyor (`fastapi_app.py`, `_on_road_damage_job_done`). `/naive_compare` ise
`"G"` ve `"closedEdgeKeys"` istiyor; bunlar yalnız `/simulate_closures`
oturumlarında var. `benchmark/full_scenario.py` de hâlâ `/simulate_closures`
çağırıyor.

**Sonuç.** Senaryoyu model tabanlı kapanmalara (`/analyze`) geçirmek, R0 naif
karşılaştırmasını — yani makalenin manşet sayılarını (206,6 dk / 1 641,0 dk) —
**kırar**.

**Yapılacak.** İşçi, `safe_G` kopyası yerine tam `G` + kaldırılan kenar
kümesini döndürsün; ana süreç `safe_G`'yi `nx.restricted_view` ile kursun
(`/simulate_closures` zaten böyle yapıyor). Bu hem uyumluluğu sağlar hem de
süreçler arası taşınan pickle'ı küçültür (bugün `G.copy()` gönderiliyor).
Ardından `full_scenario.py` bölge başına `/analyze` + Maxar sahnesi kullanacak
şekilde değiştirilmeli.


**Kapandı.** Yeni uç: `POST /api/road_damage/closures_from_mask` — hazır bir
hasar maskesinden (Colab'da üretilir) canlı `/analyze` ile **aynı kural ve aynı
örneklemeyle** kapanma çıkarır; oturuma `G` + `safe_G` (görünüm) +
`closedEdgeKeys` yazar, yanıt biçimi `/simulate_closures` ile birebir aynıdır.
`/naive_compare`, `/route`, `/recent`, `/segments` model oturumlarında çalışıyor
(canlı doğrulandı). `full_scenario.py` artık `--closure-source {synthetic,model}`,
`--mask-suffix`, `--blockage-radius-m`, `--dataset {v2,drone}` alıyor; her çıktıya
`closureSource` yazılıyor. Güvenlik: `maskId` yalnız
`benchmark/data/model_masks/` altında çözülür (yol gezinme denemeleri 422).

`analyze_road_network_graph`'in iç döngüsü `_classify_edges`'e taşındı; refaktör
öncesi/sonrası gerçek model maskesinde **her alt segmentin geometrisi dahil
birebir aynı** (r_h=0 ve 25).

**Regresyon:** tüm bu değişikliklerden sonra sentetik Hatay (tohum 42) referans
koşuyla (`runs/canli-gosterim-hatay`) **birebir aynı**: 5 bölgenin kapanma
sayıları, 9 atamanın rota/naif mesafeleri, keşif sayıları ve 98,5 / 650,0 dk.

---

## J-24 ⚪ (bilgi) Model tabanlı kapanma için gereken EMSR648 değil, Maxar kapsaması
**Durum:** KAPALI — bilgi kaydı · **Bulundu:** 16 Eylül 2026

J-12'de "9 bölgenin 5'inde veri yok" diye kaydedilen kısıt **yalnız doğrulama**
içindir. Kapanmaları modelin üretmesi için gereken şey deprem sonrası görüntü;
EMSR648 ise karnedir. `/oam_search` ile dokuz bölge merkezinde (1 km yarıçap)
ölçülen deprem sonrası (2023-02-06 … 2023-06-30) görüntü kapsaması:

| Bölge | Maxar | Diğer | En erken | EMSR648 doğrulama |
|---|---|---|---|---|
| H-Z1 Antakya | 2 | 2 | 2023-02-08 | var |
| H-Z2 İskenderun | 3 | 0 | 2023-02-12 | yok |
| H-Z3 Kırıkhan | 1 | 0 | 2023-02-28 | var |
| H-Z4 Samandağ | 3 | 0 | 2023-02-08 | yok |
| H-Z5 Belen | 3 | 0 | 2023-02-12 | yok |
| K-Z1 Maraş Merkez | 4 | 1 | 2023-02-08 | var |
| K-Z2 Elbistan | **0** | 1 | 2023-02-15 | var |
| K-Z3 Pazarcık | 4 | 0 | 2023-02-08 | yok (yol katmanı analiz edilmemiş) |
| K-Z4 Göksun | **0** | **0** | — | yok |

**Yani:** model tabanlı kapanma **8 bölgede** mümkün (Elbistan'ın Maxar-dışı
kaynağı kalite bakımından kontrol edilmeli), doğrulama **4 bölgede** mümkün.
Yalnız **Göksun**'da hiçbir deprem sonrası görüntü yok.

**Dikkat:** arama bölge merkezinin 1 km çevresinde yapıldı; sahnelerin 3 km'lik
bölgenin tamamını kaplayıp kaplamadığı ayrıca kontrol edilmeli.

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

## J-62 🟠 Simülasyon (tatbikat) modu konsolda kuruldu; sözleşmeyle üç uyuşmazlık çıktı
**Durum:** KAPALI (25 Eylül 2026) — arayüz iskeleti gerçek uçlarla uçtan uca koşturuldu; uç sözleşmeden sapıyor, sapmalar aşağıda · **Bulundu:** 25 Eylül 2026 (SIMULASYON_SOZLESMESI.md'ye göre kurulurken) · **İlgili:** J-56, kural 2, kural 4

**Yapıldı.** Sözleşmenin §5'indeki dokuz madde konsola kuruldu; katman ve alan adları §4
ile birebir. Backend'e (`QuakeMindBackend/`) dokunulmadı, orayı öbür oturum yazıyor.

| Sözleşme maddesi | Nerede | Durum |
|---|---|---|
| 1. TATBİKAT şeridi kalıcı | `kabuk/TatbikatSeridi.tsx`, kabukta | SOS ve Ekipler modlarında da görünüyor (ölçüldü) |
| 2. Seçim paneli (amaç → hazır seçenek → ince ayar) | `modlar/simulasyon.tsx` | Alan, görüntü katmanı, model; altında eşik, yarıçap, yumuşak maliyet, ekip/afetzede, tohum |
| 3. Kaynak paneli | sağ panel | Sağlayıcı, çekim tarihi, GSD; `gercek: false` için "senaryo" rozeti |
| 4. Katmanlar | `harita/simKatmanlari.ts` | Maske (raster), kapalı (kırmızı) ve cezalı (turuncu) kenar, üç rota, görev uçları |
| 5. Dijkstra / A* kartı | sağ panel | İki süre yan yana, `ayniYol` yazılıyor |
| 6. İlerleme SSE'den | `CanliSaglayici` + `islerDurumu` | `is-durumu` mesajı; yoklama yok |
| 7. Harita tek örnek | mevcut kabuk | Mod değişince tuval aynı örnek (ölçüldü); geçiş süresi ÖLÇÜLMEDİ |
| 8. Keyfi değer yok | token denetimi | Geçiyor (denetim bir `transition-[width]` yakaladı, düzeltildi) |
| 9. Ana iş parçacığı | maske `createImageBitmap` ile çözülüyor | Uzun iş ÖLÇÜLMEDİ (pencere arkada, ölçüm güvenilmez) |

Mesaj tipleri (§3) `konsol/src/canli/mesajlar.ts`'ye eklendi: `simulasyon-katman` yeni;
`is-durumu` zaten vardı, `isTipi: 'simulasyon'` ile kullanılıyor. Katman mesajı yalnız o
koşunun sonucunu tazeliyor.

**Gerçek koşu (25 Eylül 2026, 15:02).** Uçlar yayına girince tatbikat gerçek veriyle
koşturuldu: `POST /api/simulasyon/kos` → **202**, iş kuyruğa girdi, ilerleme canlı akıştan
geldi, şerit başka moda geçilince de koşuyu gösterdi.
- Alan: Hatay / Defne — Elektrik Mah., drone ortofoto (Help.NGO OAM, çekim 2023-02-09,
  0,482 m/piksel). Model: Unet (mit_b4), eşik 0,5.
- Sonuç: %0,6 hasarlı piksel, 32 kapalı kenar (330 açık), 5 ekip × 3 afetzede = 15 çift.
- Sunucunun aşama süreleri: uydu 10,5 sn · yol ağı 1,0 sn · **model çıkarımı 20,5 sn** ·
  lojistik 8,4 sn · toplam 40,4 sn.
- Ölçüm: ortalama uzama 93,6 m (%9,9), en çok 454,6 m, ulaşılamayan çift yok; son adım
  ortalama 57 m yürüme. Süreler 15 km/sa varsayımıyla.
- Ekip üsleri gerçek OSM tesisleri: Özel Mozaik Kadın Hastalıkları ve Doğum Merkezi, Özel
  Antakya Göz Hastanesi, Antakya Devlet Hastanesi.

**Uç ile sözleşme arasındaki sapmalar (25 Eylül, ölçülen gerçek yanıtlar).** Sözleşme
"alanlar bu belgede sabittir, değişirse burası önce güncellenir" diyor; uygulama
sözleşmeyi güncellemeden ayrılmış. Arayüz bugün ikisini de kabul ediyor
(`veri/simulasyon.ts` içindeki çeviriler), ama **tek biçimde buluşulmalı**:

| Sözleşme (§2, §4) | Uç (bugün) | Arayüz ne yapıyor |
|---|---|---|
| `alanlar` / `modeller` düz dizi | `{alanlar: […]}` / `{modeller: […]}` | İkisini de kabul ediyor |
| `bbox: [batı, güney, doğu, kuzey]` | `{west, south, east, north}` | Diziye çeviriyor |
| `agirlikSha1`, `tahminiSureSn` | `agirlikSha256`, `ileriGecis512Sn` (+ `olcumNotu`, `hazir`) | Ölçülen süreyi yazıyor |
| `katman.gsdM`, `kapsamKm2` | yok; `kaynak`, `oamBasligi`, `yaricapKm`, `gercek`, `not` var | Yoksa yazmıyor |
| `hasar.maskeUrl = /api/simulasyon/kosu/{id}/maske.png` | `/api/road_damage/gorsel/{id}/imageDamageMask` | Adres neyse onu kullanıyor |
| `hasar.noktaSayisi`, `hasar.oncesiKontrol` | yok | Satırı hiç yazmıyor |
| `kapanma.kapaliKenarlar = [{id, cizgi}]` | doğrudan `[[lat,lon], …]` çoklu çizgi dizisi | İkisini de kabul ediyor |
| `kapanma.cezaliKenarSayisi` / `cezaliKenarlar` | yok; `acikKenarSayisi`, `kural` var | Cezalı satırı yazmıyor |
| `rotalar: [...]` ayrı dizi | yok; rota alanları **görevin içinde** | Görevlerden rota listesi kuruyor |
| `varyantlar.riskli` | `{cizgi: null, …}` (hesaplanmamış) | O katmanı kurmuyor |
| `arama.ayniYol: true/false` | `null` | "Uç aynı yol mu demiyor; uzunluklar aynı çıktı" yazıyor |
| `referansAjanlar` | yok | Bölüm çıkmıyor |
| — | `sureler`, `gunluk`, `olcum.hizKmh`, `olcum.enBuyukUzamaM`, `sonAdimYurumeM` | Hepsi ekranda gösteriliyor |

**Bir ölçüm sorusu:** aynı koşuda **A\* 158 ms, Dijkstra 5 ms** çıktı (rota başına
ortalama, üç rota). A\* normalde daha az düğüm açar ve daha hızlıdır; sezgisel ölçeği
yanlışsa (ör. metre–derece karışması) A\* hem yavaşlar hem en kısa yolu garanti etmez.
Backend oturumu bakmalı.

**Sözleşmenin kendi içindeki üç uyuşmazlık.**
1. **İlerleme ölçeği.** §3 `ilerleme` için 0..1 diyor; bugünkü backend hasar analizinde
   YÜZDE gönderiyor (`cekirdek.py:668`, `percent`). Arayüz ikisini de kabul ediyor
   (1'den küçük değer oran sayılıyor) ama tek ölçek seçilmeli.
2. **Koordinat sırası.** §4'te çizgiler `[[lat, lon], …]`; haritada (deck.gl) `[lon, lat]`
   gerekiyor. Çevirme tek yerde yapılıyor (`simKatmanlari.cevir`, denetlendi). Sözleşme
   böyle kalacaksa sorun yok; ama öbür uçlarımız (`/api/katman/*`, `/api/sos`) `lon`/`lat`
   alanlarıyla dönüyor, tutarsızlık kalıyor.
3. **Kısmi sonuç.** §3 "arayüz her mesajda yalnız o katmanı ister" diyor ama §2'de tek
   sonuç ucu var. Arayüz sonucun bölümlerini isteğe bağlı sayıyor ve eldekini çiziyor;
   sunucunun bitmemiş bölümleri boş bırakması (ya da hiç göndermemesi) yeterli.

Ayrıca: maske PNG ucu yetki istiyor, bu yüzden `<img src>` ile çekilemiyor — jetonla
indirilip `createImageBitmap` ile çözülüyor (`veri/simulasyon.ts`).

**Denetlendi (25 Eylül, geçici önizleme koşumuyla; sahte veri ürüne girmez).**
- Sol panel: alan, görüntü katmanı ve model seçilebiliyor; ince ayar altta.
- Koşu başlatılınca şerit çıkıyor: "gerçek olay değildir", alan adı, 4/4 katman.
- Sağ panel: kaynak (Help.NGO, 2023-02-09, 0,48 m), hasar %11,4 (kontrol koşusu %0,8),
  41 kapalı / 96 cezalı kenar, arama kartı, ölçüm (25 çift), referans ajanlar, 5 görev.
- Katman kurulumu doğrudan çağrılarak denetlendi: 8 katman kuruluyor, kapalı kenar 6,
  rota 5, görev ucu 10; varyant kapatılınca yalnız o katman düşüyor; maske yoksa zemin
  katmanı kurulmuyor; maske 256×256 ImageBitmap, sınırlar sözleşmedeki bbox.
- **Koordinat çevrimi doğrulandı:** sözleşmedeki `[36,1965, 36,1472]` haritaya
  `[36,1472, 36,1965]` olarak gidiyor.
- Şerit SOS ve Ekipler modlarına geçince duruyor; harita tuvali aynı örnek kalıyor.

**Yan çıktı: panel hata sınırı (J-63).** Gerçek uçla ilk denemede sol panel `alanlar.data.find
is not a function` ile çöktü ve **bütün konsol bembeyaz kaldı** — tek panelin hatası haritayı
ve öbür panelleri de götürüyordu. `kabuk/PanelSiniri.tsx` eklendi: hata veren panel kendi
yerinde "Bu panel açılamadı" yazıyor, harita ve öteki paneller ayakta kalıyor. İkinci bir
hatada (eksik `noktaSayisi`) sınır iş başında görüldü: konsol ayakta kaldı, yalnız sağ panel
hata gösterdi.

**Açık kalanlar.**
- Madde 7'nin süresi (< 200 ms) ve madde 9'un uzun iş ölçümü YAPILMADI: tarayıcı paneli
  gizliyken tarayıcı boyamayı durduruyor, `requestAnimationFrame` hiç çalışmıyor; ölçüm
  yanıltıcı olurdu. Harita örneğinin mod değişince aynı kaldığı ölçüldü.
- `riskli` varyantı sunucuda hesaplanmıyor (`cizgi: null`); tanımı da sözleşmede yazmıyor.
- `arama.ayniYol` sunucuda hesaplanmıyor.
- Sapma tablosundaki alanlar için sözleşme mi uygulama mı değişecek, kararlaşmalı.

---

## J-61 🟠 Yanıtlar sıkıştırılmıyordu: konsol açılışında 660 KB ham JSON iniyordu
**Durum:** KAPALI (25 Eylül 2026) — ölçüldü · **Bulundu:** 25 Eylül 2026 (kullanıcının performans sorusu üzerine yapılan incelemede) · **İlgili:** J-56, J-60, kural 8

**Sorun.** `fastapi_app.py`'de yalnız CORS ara katmanı vardı; gzip yoktu. Harita altlığı
diskte gzip'li durduğu için sıkıştırılmış gidiyordu (J-40), ama **bütün JSON yanıtları ham**
gidiyordu. JSON çok tekrarlı bir metin olduğu için bu, tel üzerinde birkaç kat fazla bayt
demek. Yerelde fark edilmez; sahada tablet 4G ile bağlandığında doğrudan bekleme süresi olur.

**Yapıldı.** `SecmeliGzip` ara katmanı (`fastapi_app.py`).
- 500 bayttan küçük yanıtlar sıkıştırılmıyor (Starlette varsayılanı).
- **Canlı akış (`/api/live`) gzip'e girmiyor.** Starlette 0.38.6'nın gzip katmanı akışlı
  yanıtta parçaları tamponda biriktirip yalnız akış kapanınca boşaltıyor (kaynakta parça
  başına flush yok). SSE böyle sıkıştırılsaydı olaylar tarayıcıya akış bitene kadar
  ulaşmazdı — kural 4'ün tersi. Yeni bir akış ucu eklenirse `HARIC` listesine yazılmalı.
- Sıkıştırma seviyesi 9 değil **6**: 462 KB'lik toplanma yanıtında ikisi de 4,9 kat
  sıkıştırıyor ama seviye 9 sıkıştırma 55,9 ms, seviye 6 13,5 ms sürüyor (ölçüldü). 1 KB
  için 4 kat CPU.

**Ölçüm (25 Eylül 2026, 16 uç, her biri 5 kez; ısınma isteği sayılmadı).**

| Uç | Önce | Sonra | Kat |
|---|---|---|---|
| `/api/katman/toplanma` | 462,8 KB | 95,0 KB | 4,9 |
| `/api/katman/depremler?enAz=4` | 93,1 KB | 15,4 KB | 6,0 |
| `/api/altlik/yerler` | 51,4 KB | 7,9 KB | 6,5 |
| `/api/sos` | 9,2 KB | 2,6 KB | 3,5 |
| `/api/road_damage/heatmap` (sos kanalı) | 7,9 KB | 1,8 KB | 4,5 |
| `/api/katman/kapanmalar` | 6,3 KB | 1,1 KB | 5,6 |
| **16 ucun toplamı** | **660 KB** | **134 KB** | **4,9** |

**Dürüst not: yerelde süre azalmadı, arttı.** Aynı 16 ucun medyan sürelerinin toplamı
562 ms → 651 ms. Sebebi açık: localhost'ta taşınacak bayt zaten bedava, sıkıştırma ise CPU
harcıyor. Kazanç ağ üzerinden görünür — 526 KB'lik fark 10 Mbit/sn bağlantıda ~0,4 sn,
1 Mbit/sn'de ~4 sn eder. Saha bağlantısında ölçülmedi.

**Denetlendi (11 denetim, hepsi geçti).**
- Canlı akış: 200, `Content-Encoding` yok, `text/event-stream`, ilk parça 6 ms'de geldi.
- Büyük yanıt gzip (95 KB), 224 baytlık yanıt ham.
- Konsol tarayıcıda: bütün istekler 200, üst çubukta "Canlı akış bağlı".
- Duman testi 99 istek, **0 fark** (urllib `Accept-Encoding` göndermediği için imzalar
  sıkıştırmadan etkilenmiyor; sözleşme değişmedi).

**Açık kalan.** Toplanma yanıtı sıkıştırılmış hâlde bile 95 KB; yükün yarısı adres alanı.
Harita için ad ve konum yetiyor, adres tıklayınca getirilebilir. Bir de değişmeyen katmanlara
(`faylar`, `depremler`, `toplanma`) `ETag` ve `Cache-Control` konmadı: sayfa yenilenince
hepsi yeniden iniyor.

---

## J-60 🔴 CORS herkese açıktı: her site kimlik bilgisiyle API'ye istek atabiliyordu
**Durum:** KAPALI (25 Eylül 2026) · **Bulundu:** 25 Eylül 2026 (kullanıcı "CORS ne demek" diye sorunca ayara bakılırken) · **İlgili:** J-53, kural 5

**Sorun.** `fastapi_app.py`'de ayar şöyleydi:

```python
allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
```

Starlette bu ikiliyi (yıldız + kimlik bilgisi) gördüğünde `Access-Control-Allow-Origin`
başlığına isteği atan origin'i **olduğu gibi yansıtır**. Yani herhangi bir web sitesi,
ziyaretçisinin tarayıcısından bizim API'ye çerezli istek atıp yanıtı okuyabilirdi.

**Zararı sınırlayan şey** yenileme çerezinin `SameSite=lax` olmasıydı: tarayıcı başka
siteden gelen XHR'a o çerezi eklemiyor. Yani bilinen bir sömürü yolu yoktu; ama koruma
tek bir ayara bağlı kalıyordu ve erişim jetonuyla yapılan istekler için de kapı açıktı.

**Yapıldı.** Yıldız yerine adres listesi: `127.0.0.1` ve `localhost` üzerinde 3200 (konsol),
3201 (ikinci konsol), 3100 (eski web), 4173 ve 5173 (Vite önizleme). Üretimde alan adı
`QUAKEMIND_CORS` ortam değişkeniyle eklenir. Yöntemler ve başlıklar da yıldızdan çıkarıldı
(`GET, POST, PUT, DELETE, OPTIONS`; `authorization`, `content-type`).

**Not.** CORS bir koruma değil, tarayıcıya verilen bir izindir: `curl` ya da bir betik onu
hiç umursamaz. API'yi koruyan şey kimlik ve rol kontrolüdür (J-53).

**Denetlendi.**
- İzinli origin (`http://127.0.0.1:3200`, `http://localhost:3100`): başlık dönüyor,
  `allow-credentials: true`.
- İzinsiz origin (`https://kotu.example`): `Access-Control-Allow-Origin` başlığı yok;
  ön kontrol (OPTIONS) 400 alıyor.
- Konsol tarayıcıda çalışmaya devam ediyor (Vite vekili üzerinden aynı origin).

---

## J-59 🟠 Uçların üçte biri hâlâ kimlik istemiyor (kural 5)
**Durum:** AÇIK · **Bulundu:** 24 Eylül 2026 (J-53 çalışması sırasında sayıldı) · **İlgili:** J-53, J-45, CLAUDE.md kural 5

Sayım (24 Eylül 2026, `uclar/*.py`): **91 uç** — 51'i rol ya da kimlik istiyor, 6'sı J-53
bayrağının arkasında, **34'ü açık**. CLAUDE.md §5'teki "43 uçtan yalnız 3'ünde var" cümlesi
artık bayat.

Açık olan 34 ucun dökümü:
- **Açık kalması gereken (8):** `/`, `/api/status`, `/api/postgis/status`, oturum uçları
  (`/kayit`, `/giris`, `/yenile`, `/cikis`) ve `/api/live` (akış kendi içinde jeton
  doğruluyor; kimliksiz 401 döndüğü duman testinde kayıtlı).
- **Eski demo kimliği (3):** `/api/auth/register`, `/api/auth/login`, `/api/auth/me`.
  J-45 madde 2'nin kararına bağlı.
- **Eski bildirim ve sohbet (4):** `/api/notifications/send_emergency`,
  `/api/notifications/active`, `/api/chat/send`, `/api/chat/messages`. İlk ikisi J-45'te,
  sohbeti yeni konsol kullanmıyor.
- **Eski ekip üstlenme (4):** `/api/team/claim`, `/api/team/claims`,
  `/api/team/claim/{id}/route`, `/api/team/claim/{id}/release`. J-54'ün görev kaydı bunların
  yerine geçti; muhtemelen silinmeli.
- **Risk (4):** `/api/risk/predict`, `/api/risk/fault_lines`, `/api/risk/all_quakes`,
  `/api/risk/refresh_live_data`. İlk üçü kamuya açık başvuru verisi ama model koşturuyor;
  sonuncusu dış servise istek atıyor — en azından o kimlik istemeli.
- **Eski rota (5):** `/api/road_damage/route`, `…/safe_route`, `…/assembly`,
  `…/calculate_custom_route`, `…/nearest_debris`. Afetzede artık `/api/afetzede/rota`
  kullanıyor; `assembly` kamuya açık AFAD verisi.
- **Kıyas ve kapanma üretimi (5):** `…/simulate_closures`, `…/closures_from_mask`,
  `…/closures_from_emsr`, `…/naive_compare`, `…/reference_compare`. Ağır iş koşturuyorlar;
  benchmark betikleri kullanıyor, kimlik eklenirse betikler de giriş yapmalı.
- **Analiz görselleri (1):** `/api/road_damage/gorsel/{id}/{ad}`. `<img>` ile çekilirse
  başlık gönderilemez; kısa ömürlü imzalı bağlantı gerekir.

**Sıra önerisi:** eski ekip üstlenme uçlarını sil → risk `refresh_live_data`'ya kimlik →
kıyas uçlarını bayrak arkasına → görseller için imzalı bağlantı.

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

## J-57 🟠 `npm run kontrol` konsol kaynaklarının yanına `.js` yazıyor; Vite bu kopyaları `.tsx`'ten önce yükler
**Durum:** KAPALI (24 Eylül 2026) — betik düzeltildi, denendi · **Bulundu:** 22 Eylül 2026 (commit öncesi denetimde) · **İlgili:** kural 6 (token denetimi), J-56

**Ne oldu.** Commit öncesi `npm run kontrol` koşuldu. Tip ve token denetimi geçti. Ama betik
`konsol/src` içinde her `.ts`/`.tsx` dosyasının yanına derlenmiş bir `.js` yazdı. Toplam 82
dosya: kaynak kopyaları ve `konsol/vite.config.js`.
- **Neden** [K]. Betik `tsc -b --noEmit false --emitDeclarationOnly false` koşuyor. İki
  tsconfig'de de `noEmit: true` var ve `outDir` yok. Komut satırındaki bayrak ayarı eziyor ve
  çıktı kaynağın yanına yazılıyor. Betik ilk konsol commit'inden (a8080a3) beri böyle.
- **Tehlike** [K]. Vite 7.3.6 uzantısız içe aktarmayı `.mjs, .js, .mts, .ts, .jsx, .tsx`
  sırasıyla çözüyor. Yapılandırmada da `vite.config.js`'i `vite.config.ts`'ten önce okuyor.
  Kopyalar kalsaydı geliştirme sunucusu yeniden açılınca bayat `.js`'i yükleyecekti;
  `.tsx`'teki düzenlemeler ekrana yansımayacaktı.
- **Yapılan.** Silmeden önce iki şey denetlendi: 82 dosyanın hepsinin `.ts`/`.tsx` kardeşi
  var ve hepsi o koşuda oluşmuş. Sonra silindi. Çalışan geliştirme sunucusunun günlüğünde o
  saatten sonra kayıt yok; sunucu etkilenmedi.

**Yapıldı (24 Eylül 2026).** Betik `tsc -b && node scripts/token-kontrol.mjs` oldu; iki
tsconfig'deki `noEmit: true` artık ezilmiyor. `build` betiği de aynı `tsc -b`'yi kullanıyor.
- Denetim geçiyor ve `git status` temiz kalıyor: `package.json` dışında değişen dosya yok.
- Tip denetimi hâlâ çalışıyor: bilerek bozulmuş bir dosyada (`const x: number = "yazi"`)
  `error TS2322` verip 2 ile çıkıyor. Deneme dosyası silindi.
- Token denetimi yerinde: "Keyfi değer yok" diyor.

---

## J-56 🟠 Konsol düzeni: sol panel her modda "Katmanlar", 10 katman anahtarının 4'ü hiçbir şey çizmiyordu
**Durum:** KAPALI (24 Eylül 2026) — dört katman da bağlandı (aşağıdaki ek); 22 Eylül'de düzen değişmişti · **Bulundu:** 22 Eylül 2026 (kullanıcı, sol panelin görüntüsüyle: "bu katmanlar ve veri kaynakları kısmı her yerde var, aşağı kaydırınca geliyor, tasarım olarak sevmedim, kullanışsız; üst menüde bir sürü alan var, birini seçince soldaki katmanlar kısmı değişiyor gibi, anlamadım") · **İlgili:** ARAYUZ §8, J-54, kural 1

**Sorunlar.**
1. **Sol panelin başlığı yanlıştı.** Başlık her modda "Katmanlar" ve "7 katman açık"tı. Oysa
   içerik moda göre değişiyordu (SOS'ta çağrı kuyruğu, Ekipler'de ekip listesi). Üst
   çubukta mod seçince neyin değiştiği anlaşılmıyordu.
2. **Her modun altında aynı iki bölüm vardı.** "Harita katmanları" (10 anahtar) ve "Veri
   kaynakları", her modda kaydırınca geliyordu.
3. **10 katman anahtarının 4'ü hiçbir şey çizmiyordu:**
   - "Hasarlı yollar" boş veriyle çiziliyordu (`data: []`).
   - "Depremler", "Toplanma alanları" ve "Fay hatları" haritaya hiç bağlı değildi.
   - "Depremler" genel modda açık geliyordu ve "7 katman açık" sayısına giriyordu.
   - Veri kaynakları listesi "Harita altlığı: karo ucu henüz bağlanmadı" diyordu; oysa
     altlık J-40'tan beri yerel OSM kopyasından geliyor.
4. **On mod sekmesi üst çubuğa sığmıyordu.** 1366 px'te hepsi iki satıra kırılıyordu
   (J-54'ün açık maddesi).

**Yapılan.**
- **Sol panel seçili modun paneli** (`SolPanel.tsx`). Başlıkta modun adı yazıyor. Panel
  içeriği kadar uzuyor; altında harita görünüyor.
- **Katmanlar düğmesi** (`KatmanDugmesi.tsx`) haritanın sol alt köşesinde; düğmede açık
  katman sayısı var. Açılan listede:
  - bu mod için önerilen katmanların açık olduğu ve mod değişince önerilerin yeniden
    uygulandığı yazıyor;
  - SOS çağrıları "her zaman açık" satırı var;
  - üç grup var: olaylar ve ekipler, hasar, altlık. Her katmanın yanında kaynağı ve sayısı
    yazıyor (kural 1); ayrı kaynak bölümü kalktı;
  - bağlı olmayan dört katman anahtarsız, "bağlanmadı" ve nedeniyle yazıyor. Sayaç
    yalnız bağlı katmanları sayıyor.
- **Üst çubuk** (`UstCubuk.tsx`): beş ana mod sekme; hasar, kamera, metin, risk ve yol tek
  "Analiz ▾" menüsünde. Menü her modun ne işe yaradığını yazıyor; seçili analiz modu
  düğmede görünüyor.
- Dar ekranda (≤ 980 px) katmanlar düğmesi panellerin üstünde, aşağı açılıyor.

**Denetim.** Test sunucusuna bağlı konsolda gerçek istekle denendi:
- 1366 × 768 ve 1280 × 720'de üst çubuk tek satır ve taşmıyor, en uzun düğme adı ("Analiz ·
  Kamera tespiti") ile de.
- Sol panel başlığı modla değişiyor: Genel durum, SOS kuyruğu, Ekipler, Kamera tespiti.
- Katman sayacı: genel 5, SOS 2, Ekipler 3.
- Liste Escape ile ve dışarı tıklayınca kapanıyor. Analiz menüsünden mod seçince menü
  kapanıyor.
- SOS modunda sol panel 323 px (kaydırma yok); genel ve Ekipler'de sütun boyunda
  kaydırılıyor.

**Ek (24 Eylül 2026): dört katman da bağlandı.** Anahtarı olup hiçbir şey çizmeyen
katman kalmadı; "bağlanmadı" satırı da kalktı.

**Sebep.** Veri üçünde de vardı ama konsolun kullanabileceği bir uçtan açılmamıştı:
kapanmalar yalnız rota motorunun okuduğu tabloda (`yol_kapanmalari`), depremler ve faylar
eski risk uçlarında (kimlik istemeden), toplanma alanları ise yalnız afetzedenin konum
merkezli ucunda (`/api/yakin-yerler`, en çok 25 km yarıçap).

**Yapıldı.** Dört katman için kutu (bbox) ile sorulan yeni uçlar: `uclar/katmanlar.py`.
- `GET /api/katman/kapanmalar` · `…/depremler` · `…/faylar` · `…/toplanma`.
- Hepsi `Depends(rol_gerektir("saha", "koordinator", "yonetici"))`; kimliksiz 401 (ölçüldü).
- Kutu verilmezse altlık kataloğundaki beş bölgeyi kapsayan kutu kullanılır; en geniş kenar
  8 derece (kazara ülke çapında sorgu olmasın). Bozuk kutu ve geçersiz büyüklük 422 döner.
- Her yanıt kendi kaynağını taşır (kural 1): katman listesindeki açıklama ve sayı buradan
  gelir, koda gömülü değil.

| Katman | Kaynak | Bölgede | Yanıt | İlk istek | Sonraki |
|---|---|---|---|---|---|
| Yol kapanmaları | Depo `yol_kapanmalari` (uydu analizi) | 39 nokta | 7 KB | 9 ms | 18 ms |
| Depremler (M ≥ 4) | `query.csv` katalogu, Kandilli + USGS | 603 / 20.387 | 103 KB | 362 ms | 42 ms |
| Fay hatları | GEM Global Active Faults (13.696 çizgi) | 24 çizgi, 272 nokta | 7 KB | 892 ms | 11 ms |
| Toplanma alanları | AFAD listesi (72.232 kayıt) | 3.682 alan | 499 KB | 115 ms | 118 ms |

İlk istekteki dosya okuması açılışa alındı (`katmanlar._onyukle`, arka plan iş parçacığı).

**Haritada.**
- **Yol kapanmaları** turuncu nokta. Çizgi değil, çünkü depoya kapalı yol parçasının yalnız
  orta noktası yazılıyor (J-58). Katmanın adı "Hasarlı yollar"dan "Yol kapanmaları"na döndü.
- **Depremler** içi boş halka, çapı büyüklüğe göre. Dolu nokta değil: geçmiş katalog kaydı
  bugünün hasarıyla karışmasın. Kırmızı, turuncu ve sarı aciliyete ayrı olduğu için kendi
  token'ı var (`--color-deprem`).
- **Fay hatları** kesik ve sönük çizgi, altlığın hemen üstünde (`--color-fay`). GEM veri
  setinde ad alanı boş olduğu için etiket yazılmıyor; ipucu bunu söylüyor.
- **Toplanma alanları** afetzede ekranıyla aynı yeşil. Bölge ölçeğinde 3.682 nokta haritayı
  kapattığı için yalnız şehir ölçeğinde (z ≥ 11) çiziliyor; katman listesi bunu yazıyor.
- İpuçları kaynağı da söylüyor: "Katalog kaydı (Kandilli, USGS); bugünün hasarı değil",
  "AFAD listesi; alanın şu an açık olduğunu göstermez".

**Denetlendi (gerçek sunucu, koordinatör oturumu, 1366 × 768).**
- Katman listesinde dördü de anahtarlı: "39 kapanma", "603 deprem · M ≥ 4", "24 hat",
  "3.682 alan". "Bağlanmadı" yazan satır kalmadı.
- Bölge görünümünde 603 deprem halkası Doğu Anadolu Fayı boyunca diziliyor, fay çizgileri
  üstünde geçiyor — koordinatlar yerine oturuyor.
- Deprem ipucu: "M 4,5 deprem · 21 km SSW of Kahramanmaraş · Derinlik 12 km · 6 Şub 2023 05:31".
- Antakya'da toplanma alanları z ≥ 11'de çıkıyor, altında çizilmiyor.
- Konsolda hata yok (yalnız oturum açılmadan önceki 401).
- Duman testi: 99 istek (6'sı yeni). Önceki 93 isteğin tek farkı görev listesinin dolu
  gelmesi (veriye bağlı, koda değil). Referans imza yenilendi.

**Denetimde çıkan iki düzeltme.**
- Deprem ipucunda yıl yazmıyordu: 2023'teki kayıt "6 Şub 05:31" diye görünüyor, bu yıl
  olmuş gibi okunuyordu. `tarihSaatYilli` eklendi: kayıt başka yıldaysa yıl da yazılıyor.
- Deprem halkaları koyu zeminde 1,2 px kenarla kayboluyordu; kenar 1,5 px ve içi çok sönük
  dolu oldu.

**Açık kalan.** Kapanmalar yalnız uydu analizinden geliyor. Sahadan bildirilen kapanma
(`/report_blockage`, PostGIS) ve EMSR648 katmanı bu depoya yazılmıyor; ne rota motoru ne de
bu katman onları görüyor (J-55'in açık maddesiyle aynı).

---

## J-55 🟠 Sevkte ekibin olaya uzaklığı kuş uçuşuydu; araç yolundan süre yoktu
**Durum:** KAPALI (22 Eylül 2026) — ölçüldü; hız varsayımı ölçülmedi, açık maddeler en altta · **Bulundu:** 22 Eylül 2026 (kullanıcı: "neden kuş uçuşu, normal yolda normal trafiğin aktığı şekilde yoldan yapamaz mısın") · **İlgili:** J-54, J-44, J-34, kural 3

**Sorun.** J-54'te ekibin olaya uzaklığı kuş uçuşuydu. Afetzedenin yürüme ağı (J-44) araca
uymaz: tek yönü bilmez, yaya yollarını içerir. Eski araç motoru (`apps/road_damage`,
networkx) Python'da çalışır ve her istekte yavaştır.

**Yapılan.**
- **Araç ağı** (`araclar_arac_agi_uret.py`). Yerel OSM kopyasından beş bölge için üretiliyor
  (~3 dk; her bölgede OSM dosyasının tamamı taranıyor, okuma ~35 sn). Ağda şunlar var:
  - motorlu aracın girdiği yol türleri; `no/private` erişimli yollar yok;
  - tek yön (`oneway`, kavşak halkası, otoyol);
  - en büyük güçlü bağlı parça; her düğümden her düğüme yol var.

  Antakya ağı: 103.501 düğüm, 212.735 yönlü kenar, 747 tek yönlü yol. Güçlü bağlı parça
  oranı beş bölgede %97,8–98,3. Beş dosya toplam 12,8 MB; depoya girmez.
- **Rota** (`arac_rotasi.py`).
  - Olaydan ters ağda tek Dijkstra; olaya gelen bütün ekiplerin süresi bu tek aramadan
    çıkıyor.
  - Arama önbellekte (32 olay); hasar verisi değişince yenileniyor.
  - Hasar cezası ve kapanma kuralı yürüme rotasıyla aynı. Kapanmadan geçen rota ekranda
    söyleniyor.
- **Süre.** Yol türüne göre ortalama hız varsayımıyla hesaplanıyor [T]: ana yol 40, ara
  yol 35, sokak 20 km/sa; ışık ve kavşak hıza gömülü.
  - Yolun yasal sınırı daha düşükse sınır kullanılıyor. OSM'de sınır yolların yalnız
    %0,2–2,9'unda yazılı; süre neredeyse tamamen varsayıma dayanıyor.
  - Anlık trafik verisi yok.
  - Varsayım sunucuda (`HIZ_KMS`); değişince ağ yeniden üretilmez.
- **Nerede görünüyor.**
  - Ekip seçicide ekipler süreye göre sıralı: "~6 dk · yoldan 3,0 km".
  - "Kim gidiyor" kartında, Ekipler modunda, ekip ekranında ve afetzede kartında süre ve
    yoldan uzaklık var.
  - Haritalarda rota çizgisi sokakları izliyor. Yol ağı dışındaki ekip için kesik düz
    çizgi ve "kuş uçuşu" yazısı var.
- **Afetzedeye eski süre gösterilmiyor.** Ekibin konumu 10 dakikadan eskiyse süre yerine
  "konum eski olduğu için süre verilemiyor" yazıyor. İlk denemede 28 dakikalık konumla
  "~6 dk" yazıyordu; denerken düzeltildi.

**Ölçüm** (Antakya, test sunucusu, kopya veritabanı):
- Yeni olay araması: medyan 22 ms, en çok 23 ms (12 olay). Önbellekten 0,1 ms. Ekip başına
  rota 1 ms'nin altında.
- İlk istek 2,1 sn sürüyordu: ağ yükleme 0,6 sn, hasar çarpanları ~1,4 sn. Artık sunucu
  açılışında arka planda yapılıyor.
- Kuş uçuşu ile fark:
  - Cebrail → Akevler: kuş uçuşu 1.176 m, yoldan 3.023 m (2,6 kat), ~6 dk. Köprüden
    dolaşıyor.
  - Öteki iki örnek: 1,7 ve 1,3 kat.
- Tek yön: 76 düğümlük rotada ters gidiş yok. Aynı iki nokta arasında A→B 3.023 m,
  B→A 2.961 m.
- API yanıtı (medyan, önbellekle): aday ekipler 4 ms, `/api/sos` 4 ms, `/api/ekipler` 4 ms.
- Denetimler:
  - API testi 11/11. Ağ dışı ekip (Ankara) kuş uçuşuna düşüyor, listede sonra geliyor.
  - J-54'ün uçtan uca testi (52/52) ve depo testi (44/44) yeniden geçti.
  - Duman testi 93 istek; tek fark veriye bağlı (`/api/gorevler` listesi artık dolu).
- Arayüz, test sunucusunda gerçek isteklerle denendi: konsol, ekip ekranı ("Olaya yoldan
  2,0 km · tahmini ~4 dk") ve afetzede ("sana yoldan ~2 dk (1,7 km, tahmini)").

**Açık kalanlar.**
- **Hız varsayımı ölçülmedi.** Görev kaydı yola çıkış ve varış saatini tutuyor. Yeterli
  görev birikince tahmin bu kayıtlarla karşılaştırılmalı ve hız tablosu buna göre
  ayarlanmalı.
- **Anlık trafik yok.** Açık bir kaynak yok; ticari servis kullanılmadı.
- **Hasar süreye eklenmiyor.** Hasar noktası rota seçimini etkiliyor, ama enkazlı yolda
  yavaşlama yok.
- **Kapsam.** Aşağıdaki ek ile şehirler arası da yoldan. Beş şehri kapsayan kutunun
  (+0,15°) dışından gelen ekip için hâlâ kuş uçuşu yazılıyor.

**Ek (22 Eylül): şehirler arası yine kuş uçuşuydu.** Kullanıcı genel durum ekranının
görüntüsüyle geldi ("bak ne durumda"). Haritada Antakya'daki AKUT 1'den Kahramanmaraş'taki
çağrıya (Abdülhamid Han) 160 km'lik kesik düz çizgi vardı.
- **Neden.** Kullanıcı AKUT 1'i (Antakya) o çağrıya önce 2, sonra 4 kişiyle göndermiş.
  Şehir ağları yalnız şehrin 12 km çevresini kapsıyordu. İki şehir arasında ağ olmadığı
  için rota bulunamadı ve ekran sessizce kuş uçuşuna düştü.
- **Yapılan.**
  - Bölgeler arası ağ (`araclar_arac_agi_uret.py --genel`): beş şehir ağı (dosyadan) ve
    şehirleri bağlayan ana yollar (otoyol, devlet ve il yolu; OSM'den tek okuma, 28 sn)
    kavşaklarından birleşti.
  - Ağın boyutu: 513.343 düğüm, 1.004.496 yönlü kenar, 8.622 ana yol, şehir dışında
    9.894 km yol; güçlü bağlı parça %98,3; dosya 15,1 MB.
  - Ekip ve olay aynı şehirdeyse şehir ağı (hızlı), farklı şehirlerdeyse genel ağ
    kullanılıyor.
  - Şehir dışı yolda ayrı hız varsayımı var [T]: otoyol 100, devlet yolu 80, ana yol 70,
    il yolu 60 km/sa. Şehir içi hızlar şehirler arasında süreyi iki katına çıkarırdı.
  - Uzun rota çizgisi yaklaşık 15 m sapmayla sadeleşiyor (178 km → 199 nokta); liste
    yanıtları şişmiyor.
  - Uzun süre saat ve dakikayla yazılıyor ("~2 sa 26 dk").
- **Ölçüm.**

  | Nereden → Kahramanmaraş | Yoldan | Tahmini süre | Kuş uçuşu |
  |---|---|---|---|
  | Antakya (AKUT 1, kullanıcının görevi) | 178,4 km | ~2 sa 26 dk | 166,5 km |
  | Gaziantep | 80,8 km | ~1 sa 15 dk | 71,7 km |
  | Malatya | 221,8 km | ~3 sa | 149,5 km |
  | Adıyaman | 163,8 km | ~2 sa 16 dk | 122,1 km |

  - Genel ağ yükleme 1,0 sn, ilk hasar çarpanı ~1 sn; ikisi de sunucu açılışında arka
    planda yapılıyor.
  - Yeni şehirler arası arama medyan 111 ms, önbellekten 6 ms.
  - Kullanıcının verisinin kopyasıyla (sürekli durum): `/api/sos` 11 ms,
    `/api/ekipler` 9 ms, aday ekipler 13 ms. İlk istek 135 ms.
- **Not.** Tahminler genel olarak bilinen yol sürelerine yakın; ama hız varsayımı
  ölçülmedi. Madde yukarıda "Açık kalanlar"da.

---

## J-54 🔴 Sevkte kim, nereye, kaç kişiyle gidiyor belirsiz; ekip üç yere birden "müsait" görünüyor
**Durum:** KAPALI (22 Eylül 2026) — sevk görevi, ekip ekranı ve afetzede görünümü yapıldı; test sunucusunda uçtan uca ölçüldü. Açık maddeler en altta · **Bulundu:** 22 Eylül 2026 (kullanıcı: "hangi ihbar, neredeki ihbar, hangi ekip gidecek ya da gidiyor, kaç kişi gidiyor; bunlar hep belirsiz") · **İlgili:** J-43, J-51, J-53, kural 5

Kod ve çalışan veritabanı okunarak doğrulandı:
1. **Ekibin durumu atamayla değişmiyor.** Veritabanında tek ekip var (EKP-01, "AKUT 1").
   Üç çağrı ona atanmış, ama ekip hâlâ "müsait" ve görevi boş. `sos_ata` yalnız çağrıyı
   güncelliyor (`depo/sqlite_surucu.py:401`). En yakın ekip hesabı müsaitleri seçtiği
   için aynı ekibi yeniden öneriyor. Bir ekip aynı anda üç yere gidiyor görünüyor.
2. **Ekip seçilemiyor.** "Ekip gönder" yalnız sunucunun önerdiği en yakın ekibi atıyor
   (`konsol/src/modlar/sos.tsx:171`).
3. **Kaç kişi gittiği yok.** Ekip kaydında kişi sayısı, türü ve kurumu yok.
4. **Gidiş izlenmiyor.** Çağrı yalnız bekliyor → atandı → kapandı. Yola çıkış, varış ve
   bitiş zamanı yok. Kimin atadığı yazılmıyor.
5. **Ad yerine kimlik.** Liste ve harita "Ekip atandı (EKP-01)" yazıyor, ekibin adını değil.
6. **İhbarlar ekibe atanamıyor.** Fotoğraf, yazılı ve ihtiyaç ihbarında yalnız
   "görüldü / kapandı" var (`uclar/ihbar.py:520`).
7. **İkinci ekip gönderilemiyor.** Yalnız bekleyen çağrı atanıyor. Enkazda çoğu zaman
   ek ekip gerekir.
8. **Ekip tanımlanamıyor.** Konsol "ekipler koordinatör tarafından tanımlanır" diyor ama
   bunun ekranı yok; tek ekip API ile girilmiş.
9. **Afetzede** yalnız "Ekip atandı" görüyor; ekibin yola çıkıp çıkmadığını bilmiyor.
10. Eski web'in `/api/team/claim` uçları bellekte ve oturumsuz (`uclar/ekip.py`); konsol
    kullanmıyor. J-53'ün listesinde yok.

**Kullanıcının kararları (22 Eylül).**
- Durumu kim işaretler: ikisi de. Ekip kendi telefonundan, koordinasyon telsizle gelen
  bilgiyle işaretler; her adım kimden geldiğiyle yazılır.
- Afetzede ne görür: durum, saat, kişi sayısı, ekibin adı ve ekibin nerede olduğu.

**Yapılan.**
- **Görev kaydı** (`gorevler`, `gorev_adimlari`; MIMARI §3).
  - Her sevk bir kayıttır: olay, ekip, giden kişi, atayan, adımlar ve saatleri.
  - Kurallar veritabanında:
    - bir ekibin tek açık görevi olur;
    - ikinci ekip yalnız "ek destek" olarak gider;
    - giden kişi, ekibin kayıtlı sayısını geçemez;
    - kapanmış olaya ekip gitmez.
  - Son görev bitince olay eşitlenir. İş bittiyse olay kapanır; iptal ya da "olay sürüyor"
    ise SOS kuyruğa döner. Olay kapatılınca açık görevler biter.
  - Madde 1–7 kapandı.
- **Uçlar** (`uclar/gorev.py`, `uclar/gorev_bicim.py`):
  - `GET/POST /api/gorevler`, `POST /api/gorevler/{id}/durum`,
    `GET /api/gorevler/aday-ekipler`, `GET /api/ekibim`;
  - `POST /api/ekipler`, `PUT /api/ekipler/{id}/uyeler`, `GET /api/ekipler/uye-adaylari`;
  - SOS ve ihbar çıktısı `gorevler`, ekip çıktısı kurum/tür/kişi/görev/üyeler, özet
    ekip sayılarını kazandı.
  - Eski `/api/sos/{id}/ata` artık görev açıyor.
  - Canlı akışta yeni `gorev` mesajı var.
- **Yetki.** Saha hesabı yalnız bağlı olduğu ekip adına çalışır (gönderme, adım, konum);
  hesabı ekibe koordinasyon bağlar. Afetzede sevk uçlarına giremez.
- **Konsol** (madde 8 kapandı):
  - Olay ayrıntısında "Kim gidiyor" bölümü ve ekip seçici var.
  - Yeni "Ekipler" modunda ekip ekleme, düzenleme ve hesap bağlama yapılıyor.
  - Harita görevdeki ekipten olaya çizgi çekiyor; ekip adları haritada yazıyor.
  - Özet kartlarına "Görevdeki ekip" ve "Sahadaki kişi" eklendi.
  - Ayrıntı ARAYUZ §8'de.
- **Ekip ekranı (`/ekip`).** Saha hesabı açılışta buraya gelir. Olayın bütün bilgisini
  görür; "Yola çıktık / Vardık / İşimiz bitti / Gidemiyoruz" düğmeleri var. İsterse
  konumunu paylaşır (sayfa açıkken, 30 sn ya da 25 m'de bir).
- **Afetzede** (madde 9 kapandı):
  - Çağrı kartında aşama, ekibin adı, kişi sayısı ve saat görünür; dört adım çizelgesi var.
  - Ekip konumunu paylaştıysa nerede olduğu ve uzaklığı yazar.
  - Haritada gelen ekip ve çağrıya kesik çizgi görünür.
  - Görevlendirilen ekip gelemezse bu yazılır.
  - Afetzedeye atayan, iç not ve adımların kimden geldiği gitmez.

**Denerken bulunan ve düzeltilenler.**
- SOS kuyruğunun süzgeçleri ("Yalnız kritik" vb.) yalnız sayıyı değiştiriyordu, liste
  süzülmüyordu. Süzgeç artık iki panelde ortak.
- "Ekibe yakınlığa göre sırala" anahtarı hiçbir şey yapmıyordu (`SosSol` içinde yerel
  durumdu, sıralamaya bağlı değildi). Kaldırıldı.
- Bekleyen çağrılar artık en uzun bekleyen üstte sıralanıyor. Eskiden en yeni üstteydi.
- Bekleme süresi aşağı yuvarlanıyordu: 1 saat 59 dakika "1 saattir" yazıyordu. Artık
  "1 saat 59 dakikadır" yazıyor.
- Saat ekleri sabitti ("14:02'te" yanlış). Artık okunuşa göre: "14:02'de", "14:05'te",
  "14:30'da".
- Ekip yeri adı: noktaya en yakın OSM yer adı (5 km içinde yoksa yazılmaz).
- Görev kaydından önce yapılmış üç atama (EKP-01) var. Bunlar "eski kayıt: kaç kişi ve
  hangi aşamada bilinmiyor" diye gösteriliyor; görev uydurulmadı.

**Sınama.** Gerçek veritabanının kopyasıyla, test sunucusunda (8001):
- Depo katmanı: 44/44 denetim. Eski veritabanı tamamlanıyor, ikinci açılış hatasız.
  Veritabanı ikinci açık görevi reddediyor. Olay eşitlemenin dört durumu ölçüldü.
- Uçtan uca: 52/52 denetim. Koordinatör, saha hesabı ve iki afetzede aynı anda canlı
  akışı dinledi. Ölçülenler:
  - Afetzedeye yalnız kendi olayının `gorev` ve `ekip-konumu` mesajı gitti; öteki
    afetzedeye hiçbiri gitmedi.
  - Afetzede çıktısında atayan, not ve adım yok.
  - Saha hesabı başka ekibin görevine ve konumuna 403 aldı.
  - Eski `ata` ucu görev açıyor.
- Duman testi 93 istek. Önceki 83'ün 80'i aynı. Farklı olan 3'ü beklenen: `/api/sos`'ta
  `gorevler`, ekiplerde yeni alanlar, özette ekip sayıları. 10 istek yeni uçlar için.
  Referans (`testler/uc_imzalari.json`) yeniden kaydedildi.
- Arayüz, test sunucusuna bağlı konsolda gerçek isteklerle denendi:
  - Koordinatör: T2'yi "hizmet dışı"dan "müsait"e aldı ve bekleyen çağrıya 3 kişiyle
    gönderdi ("Gönder: Test UMKE 9, 3 kişi"). "Yola çıktı"yı işaretledi.
  - İptal nedensiz kaydedilmedi; iptalden sonra çağrı kuyruğa döndü ve "Test UMKE 9
    gelemedi (…)" yazdı.
  - Ekip ekranında "Paylaş" konumu sunucuya yazdı; "Vardık" adımı "ekip · Önizleme Saha
    Veli" olarak geldi.
  - Afetzede kartında "Ekip yolda · AKUT 1 (4 kişi) 15:27'de yola çıktı · sana kuş uçuşu
    1,2 km" yazdı; haritada ekip ve kesik çizgi göründü.
  - 1600 px, 1366 px ve telefonda (375 px) sayfa yatay kaymıyor.
- Üretim derlemesi geçti. Ekip ekranı ayrı parça: 12,4 KB (4,1 KB gzip); harita motorunu
  indirmiyor.
- Test sonrası gerçek API yeniden başlatıldı. Veritabanına yalnız yeni tablolar ve
  sütunlar eklendi; 11 çağrı ve EKP-01 yerinde.

**Açık kalanlar.**
- **Arka planda konum yok.** Tarayıcı, sayfa kapalı ya da arka plandayken konum vermez.
  Ekip telefonu cebe koyunca konum eskir; ekranda konumun yaşı yazar. Yerel uygulama ya da
  arka plan konumu mobil kapsamında (bugün kapsam dışı).
- ~~**Uzaklık kuş uçuşu.**~~ J-55'te çözüldü: araç ağında yoldan uzaklık ve tahmini süre.
- **Ekibe bildirim yok.** Görev atanınca ekibin telefonuna yalnız sayfa açıksa düşer
  (canlı akış). Anlık bildirim (push) yok.
- **Kimin gittiği.** Kişi sayısı tutuluyor, isimler değil; yalnız ekibe bağlı hesaplar
  biliniyor.
- ~~**Üst çubuk.**~~ J-56'da çözüldü: beş ana mod sekme, analiz modları tek menüde;
  1280 px'te de tek satır.
- **Eski uçlar.** `/api/team/claim` bellekte ve oturumsuz duruyor (madde 10); J-53'ün
  kararıyla birlikte ele alınmalı.

---

## J-53 🔴 Eski uçlar oturumsuz yanıt veriyor: vatandaş ihbarlarının metni ve konumu açık
**Durum:** KAPALI (24 Eylül 2026) — konsolun kullandığı uçlar kimlik ister, eski webe özel uçlar varsayılanı kapalı bayrağın arkasında · **Bulundu:** 22 Eylül 2026 (J-51'in duman testi imzalarında) · **İlgili:** CLAUDE.md kural 5, J-45, J-51

**Sorun.** Duman testinin referans imzasında (`testler/uc_imzalari.json`) jetonsuz istekler
200 dönüyor:
- `GET /api/nlp/locations`: eski metin ucunun çözümlediği ihbarlar, konumları ve metnin
  kendisi (`sourceText`).
- `GET /api/camera/reports`: kamera ucunun enkaz/çatlak raporları ve konumları.
- `GET /api/sos/alerts`, `POST /api/sos/alert`: eski SOS listesi ve SOS açma.
- `GET /api/road_damage/heatmap`: bütün kanalların (SOS dahil) yoğunluk ızgarası.
- `POST /api/camera/analyze`: herkes model koşturabiliyor (`/api/nlp/analyze` 422 döndü,
  o da kimlik istemiyor).

J-51'in yeni kayıtları bu listelere yazılmıyor; yeni uçlar kimlik ister. Ama ihbarın ısı
noktası, oturumsuz ısı ucundan yoğunluk olarak görünür.

**Yapıldı (24 Eylül 2026).** Kullanıcı kararı bana bıraktı ("ben anlamadım bu işi, sence ne
olsun"); önerilen orta yol uygulandı.

**1. Konsolun kullandığı uçlar kimlik istiyor** — `Depends(rol_gerektir("saha",
"koordinator", "yonetici"))`. Konsol bunları zaten jetonla çağırdığı için kaybı yok:
`/api/road_damage/heatmap`, `…/segments/{id}`, `…/status/{id}`, `…/recent`, `…/analyze`,
`…/oam_search`, `…/wayback_versions`, `/api/camera/analyze`, `/api/nlp/analyze`.
Model koşturan üç uç (kamera, metin, uydu analizi) da böylece kimliksiz çalıştırılamıyor.

**2. Yalnız eski webin kullandığı uçlar bayrağın arkasında** — `Depends(kimlik.eski_uc)`,
varsayılan **kapalı**; kapalıyken 404 döner (ucun varlığı da sızmasın):
`/api/nlp/locations`, `/api/camera/reports`, `/api/sos/alerts`, `POST /api/sos/alert`,
`POST /api/sos/alert/{id}/status`, `POST /api/road_damage/report_blockage`.
Açmak için `QUAKEMIND_ESKI_UCLAR=1`. Bayrak her istekte okunuyor, kodda sabit değil.

`report_blockage` bu listeye ayrıca yazma ucu olduğu için girdi: kimliksiz herkes kapanma
ihbarı yazabiliyordu.

**Denetlendi (gerçek sunucu, 21 denetim, hepsi geçti).**
- Bayraklı uçlar kimliksiz de jetonla da 404.
- Konsolun uçları kimliksiz 401, koordinatör jetonuyla 200.
- Yeni katman uçları ve afetzedenin kullandığı `/api/road_damage/assembly` etkilenmedi.
- Bayrak işlevi ayrıca doğrudan denendi: `QUAKEMIND_ESKI_UCLAR=1` iken istisna atmıyor,
  0 ya da tanımsızken 404 atıyor.
- Duman testi: 99 istekten 12'si değişti — 5'i 404 (bayrak), 7'si 401 (kimlik). Referans
  imza yenilendi.
- Konsol tarayıcıda denendi: hasar modunda ısı (4 kanal), wayback ve model uçları 200;
  401 yok.

**Eski webde ne bozuldu.** Eski webin SOS listesi, kamera raporları, metin konumları ve
kapanma ihbarı ekranları artık 404 alıyor. Bu bilinçli (CLAUDE.md §7: eski webde yalnız
kritik düzeltme yapılır; burada kritik olan veri sızıntısıydı). Göstermek gerekirse sunucu
`QUAKEMIND_ESKI_UCLAR=1` ile açılır.

**Kalan.** Isı ucu artık kimlik istiyor ama hâlâ eski uçtur; konsolun ısı verisi zamanla yeni
sözleşme uçlarına taşınmalı. Kimlik istemeyen öbür uçlar J-59'da toplandı.

---

## J-52 🟠 Canlı modda yeni SOS ve ihbar konsol listesine en çok 60 sn geç düşüyordu
**Durum:** KAPALI (22 Eylül 2026) — kodda düzeltildi [K]; gerçek sunucu ve oturumla tarayıcıda ölçülmedi · **Bulundu:** 22 Eylül 2026 (J-51 yazılırken, kod okumasıyla) · **İlgili:** J-43, J-46, ARAYUZ §10, kural 4

**Sorun.** Canlı modda sorguların bitişi saatin son dakikasıydı (`simdi`, dakikada bir
ilerliyor). Yeni SOS o dakikadan sonra kaydediliyordu. Canlı akış sorguyu tazelese de sunucu
kaydı `zaman <= bitis` süzgecinde eliyordu. Kayıt bir sonraki dakikaya kadar listede
görünmüyordu: ortalama 30, en çok 60 sn. İstemcinin saati sunucudan gerideyse gecikme daha
da uzardı. Kullanıcının istediği "yönetici panelinde anlık düşmeli" bu yüzden sağlanmıyordu.

**Yapıldı.**
- `useSorguAraligi` (`durum/zamanDurumu.ts`): canlıda bitiş gönderilmez (açık uç).
- Başlangıç 15 dakikalık çapaya yuvarlanır. Listeler tam pencereye istemcide süzülür (`select`).
- Canlı akış yalnız değişen şeyi tazeler (`tazelenecekler`). Yeni SOS'ta yalnız SOS ısı
  kanalı, ihbarda yalnız ilgili kanal tazelenir, durum değişikliğinde hiçbiri. Eskiden bir
  mesaj tipi sabit bir anahtar listesini tazeliyordu.

---

## J-51 🔴 Afetzedenin fotoğraf, yazılı ve ihtiyaç ihbarı konsola düşmüyordu; fotoğrafta model seçimi yoktu
**Durum:** KAPALI (22 Eylül 2026) — kodda, uçtan uca betikte ve önizlemede sınandı; gerçek oturumla son bakış kullanıcıda; "Açık" başlığındaki üç madde sürüyor · **Bulundu:** 22 Eylül 2026 (kullanıcı: "afetzedenin fotoğraf çekip modele karar vereceği ve seçilen modele göre cevap alacağı ve ihbar oluşturabileceği sistem yok … SOS ihbarları, enkaz / çatlak ihbarları, NLP ihbarları, ihtiyaç ihbarları yönetici panelinde uygun yere anlık olarak düşmeli") · **İlgili:** J-50, J-52, J-53, J-13, kural 2, 3, 4, 5

**Sorun.**
- Afetzede ekranındaki hasar fotoğrafı iki modeli birden koşuyordu. Afetzede model
  seçemiyor, ihbarı kendisi açamıyordu. Konum varsa kamera ucu sonucu sessizce haritaya
  yazıyordu.
- Yazılı ihbar (metin modeli) afetzede ekranında yoktu. İhtiyaç talebi yalnız SOS'un
  içinde bir seçimdi.
- Konsola canlı akışla yalnız SOS düşüyordu. Kamera ucu canlı akışa bir şey yayınlamıyordu.
  Fotoğraf raporları bellekteki bir listede duruyor, sunucu yeniden başlayınca kayboluyordu.

**Yapıldı (sunucu).**
- **Depo.** `ihbarlar` ve `ihbar_fotograflari` tabloları. Fotoğraf ayrı tabloda; liste
  okunurken görüntü belleğe alınmaz.
- **İki adımlı akış** (`uclar/ihbar.py`):
  1. İnceleme. `POST /api/afetzede/fotograf-analiz` (model: çatlak / bina / ikisi) ve
     `POST /api/afetzede/metin-analiz`. Kayıt açmaz, haritaya yazmaz. Sonuç 30 dakika
     sunucu belleğinde durur.
  2. İhbar. `POST /api/ihbarlar` (fotograf / metin / ihtiyac). Modelin çıktısı istemciden
     alınmaz, sunucudaki incelemeden okunur. Aynı inceleme ikinci ihbarı açamaz (409).
- Model hasar ya da aciliyet çıkardıysa ihbar ortak sözleşmeye de nokta olarak yazılır
  (kaynak `kamera` / `metin`). İhtiyaç talebi hasar değildir, ısıya yazılmaz.
- Hasar skoru sınıfın ağırlığından gelir: ağır 1,0, orta 0,6, çatlak 0,5 (tasarım kararı [T]).
  Güven modelin olasılığıdır. Eski kamera ucu ikisine de güveni yazıyordu.
- Kötüye kullanım sınırı: bir kişi 10 dakikada en çok 20 ihbar açar (429).
- Fotoğraf sunucuda yeniden kodlanır, EXIF silinir. `GET /api/ihbarlar/{id}/fotograf`
  yalnız sahibine ve saha rolüne ve üstüne açık. Fotoğraf JSON içinde döner, jeton adrese
  yazılmaz.
- Durum: `POST /api/ihbarlar/{id}/durum` (görüldü / kapandı; yalnız ileri gider).
- Seçilen model yüklenemezse 503 döner. Eski kamera ucu modeli atlayıp "tespit yok"
  diyordu.
- **Canlı akış.** Yeni mesaj tipi `ihbar`. Konsol rolleri konumlu tam mesajı alır.
  Afetzede yalnız kendi ihbarının kimliğini, türünü ve durumunu alır.
- Kamera ucunun YOLO kodu ortak işleve ayrıldı (`yolo_tespit`); eski ucun davranışı aynı
  (duman testi).

**Yapıldı (konsol).**
- "Son ihbarlar" (genel durum): SOS, fotoğraf, metin ve ihtiyaç tek listede; tür süzgeci,
  sayı ve renkli simge var. Seçilen ihbarın ayrıntısı açılır: işaretli fotoğraf, metin
  modelinin sonucu ya da ihtiyaçlar. "Gördüm", "Kapat" ("Karşılandı") ve "Haritada"
  düğmeleri var. Uydu noktaları ihbar olmadığı için listeden çıktı.
- Kamera modunda "Afetzedelerden gelen fotoğraflar", metin modunda "Afetzedelerden gelen
  yazılı ihbarlar" başlıkları var.
- Yeni "İhtiyaç talepleri" modu: ihtiyaç başına talep ve kişi sayısı, süzgeçler, liste.
- Harita katmanı "Afetzede ihbarları": nokta türün renginde; her mod kendi türünü gösterir.
- Yeni SOS ya da ihbar gelince köşede 20 sn'lik kart çıkar (ARAYUZ §10). Tıklayınca ilgili
  mod açılır, kayıt seçilir, harita oraya gider.

**Yapıldı (afetzede ekranı).** Ayrıntı J-50 üçüncü turda.
- "Bildir" düğmeleri:
  - Hasar fotoğrafı: fotoğraf → model seçimi → modelin cevabı → ihbar.
  - Yazarak bildir: metin → modelin anladığı → ekibin gideceği yer → ihbar.
  - İhtiyaç bildir.
- "Bildirimlerim": gönderilen SOS'ların ve ihbarların canlı durumu.
- İhbar türü token'ları (`--color-ihbar-*`): SOS kırmızı, fotoğraf sarı (kamera kanalı),
  metin mor (metin kanalı), ihtiyaç pembe. Pembe hasar ya da aciliyet rengi değildir.

**Ölçüldü / sınandı.**
- **Uçtan uca betik.** Test sunucusu (8001) kopya veritabanıyla çalıştı; 39/39 kontrol geçti.
  - Fotoğraf incelemesi sunucuda 400–665 ms sürdü (çatlak / bina / ikisi). Seçilen modelin
    dışında model koşmadı.
  - Metin incelemesi ilk istekte 43,5 sn sürdü: model yükleme ve adres araması. İncelemenin
    kendisi 13,5 sn; model yüklüyken ikinci metin 8,1 sn.
  - Afetzede başkasının ihbarını, fotoğrafını ve canlı mesajını alamıyor. Konsol her ihbarı
    ve durum değişikliğini alıyor.
- **Duman testi.** 10 yeni istek eklendi (toplam 80). Önceki 70 istek referansla aynı.
  Referans imza güncellendi.
- **Önizleme.** İki sekmeyle yapıldı: sahte sunucu, test sunucusundan alınmış gerçek
  yanıtlar. Oturum açılamadığı için bu yol seçildi; sayfa denetimden sonra silindi.
  - Afetzedenin gönderdiği fotoğraf, metin ve ihtiyaç ihbarı konsol sekmesine anında düştü:
    kart, liste ve harita.
  - Karttaki "Göster" kamera modunu açtı, ihbarı seçti, haritayı oraya götürdü.
  - Konsolda "Gördüm", afetzedenin satırını canlı olarak "Görüldü" yaptı.
- **Üretim derlemesi.** Afetzede ekranının ilk açılışı 136,6 KB gzip (J-50 ikinci tur:
  116,2). Artışın çoğu simgelerden. İhbar pencereleri yalnız açılınca iner (1,8–3,1 KB).

**Açık.**
- **Kural 3.** Model çıkarımı hâlâ istek yolunda. YOLO ~0,5 sn sürüyor; metin modeli adres
  araması yüzünden 8–15 sn. İş kuyruğuna ve canlı akışa taşınmalı.
- **Adres çözümü.** Metin modeli çoğu zaman yalnız ilçeyi buluyor: metinde "Akevler"
  geçmesine rağmen sonuç "Antakya, Hatay" oldu. Bu yüzden ekran ekibin gideceği yeri
  varsayılan seçmiyor ve metindeki adresin afetzedeye uzaklığını yazıyor. Adres çözümü J-13.
- **Dış servis.** Metindeki adres, konuma çevrilmek için Nominatim'e gidiyor. Ekran bunu
  afetzedeye yazıyor.

---

## J-50 🟠 Afetzede ekranı telefon gibi dar yapılmıştı; harita, hastane ve fotoğraf yoktu
**Durum:** DEVAM EDİYOR — üçüncü tur (J-51) tamam ve önizlemede denetlendi; gerçek oturumla son bakış kullanıcıda · **Bulundu:** 22 Eylül 2026 (kullanıcı: "afetzede tarafını mobil gibi yapmışsın… webe yapıyorsun… SOS butonu kırmızı, text yazabilecekler, en yakın toplanma merkezi, hastane ve benzeri yerleri haritadan görebilecekler") · **İlgili:** J-43, J-44, ARAYUZ §8, MIMARI §7

**Sorun.**
- J-43'teki ekran tek dar sütundu (420 px) ve haritasızdı. Tasarım belgesindeki "afetzede
  ekranı hafif, harita motoru indirmez" kuralı uygulanmıştı; kullanıcı ekranı web için ve
  haritalı istiyor.
- Eski webin afetzede portalında olup yeni ekranda olmayanlar vardı: büyük SOS düğmesi,
  haritada toplanma alanı ve rota, bina/duvar fotoğrafıyla hasar tarama.

**Yapıldı.**
- **Düzen (web).** Solda SOS kartı, çağrılarım ve hasar fotoğrafı; ortada harita; sağda
  yakındaki yerler. Dar ekranda sütunlar alt alta dizilir.
- **SOS kartı.** Büyük kırmızı "SOS · Yardım çağır" düğmesi var. "Durumunu yaz" metin alanı
  öne alındı. Durum seçimi isteğe bağlı: seçilmezse çağrı "kritik" gider ve ekip bunu
  "Durum seçilmedi (tek dokunuş SOS)" diye görür. Sözleşmeye `durumSecildi` alanı eklendi.
- **Harita.** Konsolun harita kabuğu ve kendi OSM altlığımız kullanılıyor. Haritada konumun
  (doğruluk çemberiyle), yakındaki yerler (renkli daire ve harf), açık çağrıların, seçilen
  yere kuş uçuşu kesikli çizgi ve istenirse yürüyüş rotası görünüyor. Yer türleri haritada
  açılıp kapatılabiliyor. Harita tembel yükleniyor.
- **Yakındaki yerler.** Yeni uç `GET /api/yakin-yerler` (kimlik ister).
  - Toplanma alanları AFAD listesinden geliyor; adlar Türkçe büyük/küçük harf kuralıyla
    yazılıyor.
  - Hastane, sağlık merkezi, eczane, itfaiye ve polis yerel OSM kopyasından çıkarıldı:
    `araclar_altlik_uret.py --hizmetler`, 1.386 kayıt (1.160 eczane, 128 sağlık, 68 hastane,
    23 polis, 7 itfaiye), okuma 31 + 145 sn.
  - Veri yalnız beş bölgede var. Kapsam dışında ekran "yok" değil "bu bölge için üretilmedi"
    yazıyor.
  - AFAD listesi bir kez belleğe alınıyor. Sunucu açılırken arka planda yükleniyor: ilk istek
    1,8 sn sürüyordu, sonrakiler 9 ms.
- **Yürüyüş rotası.** Yalnız istenince çiziliyor: `POST /api/afetzede/sokak-rotasi`, OSRM
  yaya profili, routing.openstreetmap.de.
  - Ekran, konumun dış servise gideceğini ve rotanın yıkık ve kapalı yolları bilmediğini
    yazıyor.
  - Servis yanıt vermezse hata dönüyor. Eski uç böyle durumda kuş uçuşu çizgiyi "rota" diye
    gösteriyordu.
  - Hasar bilgili rota hâlâ J-44.
- **Hasar fotoğrafı.** Eski kamera sayfasının dürüst hâli:
  - Sahte sonuç yok. Eski sayfa sunucuya ulaşamayınca "%96,2 derin çatlak" uyduruyordu.
  - "Güvenli" hükmü yok. Sonuç "modelin tahmini; binanın güvenli olduğunu göstermez" diye
    yazılıyor.
  - Fotoğraf göndermeden önce 1280 piksele küçültülüyor.
  - Kutular tarayıcıda çiziliyor. Sunucunun görüntüsü kullanılmıyor, çünkü üstüne
    "Bina Hasarsız / Güvenli" yazıyor ve Türkçe harfleri bozuyor.
- **Kamera ucu düzeltmesi.** Model "hasarsız" dese bile en güçlü tespit ekiplerin haritasına
  hasar noktası olarak yazılıyordu. Hasarsız binanın fotoğrafı ısı haritasında hasar gibi
  görünüyordu. Artık yalnız hasar tespitleri yazılıyor.
- **Belgeler.** ARAYUZ §8 ve MIMARI §7 kullanıcı kararıyla güncellendi.

**Ölçüldü / sınandı.**
- **Yakındaki yerler.** Akevler (Antakya) için 10 toplanma (en yakın 3 m), 5 hastane (en yakın
  1.556 m), 10 sağlık merkezi, 10 eczane. Kızılay (Ankara) için 10 toplanma; hizmet kapsamı
  yok olarak işaretli.
- **Rota.** Akevler'den Antakya Devlet Hastanesi'ne 2.245 m yürüyüş (~28 dk), kuş uçuşu
  1.747 m; yanıt 273 ms.
- **Kimliksiz istek.** Yakındaki yerler ve rota 401 dönüyor.
- **Duman testi.** 70 istek. İki fark bilerek yapıldı: `/api/sos`'a `durumSecildi` alanı ve
  3 yeni istek. Referans imza güncellendi.
- **Üretim derlemesi.** Afetzede rotası ilk açılışta 112,3 KB gzip JS. Harita (~570 KB)
  sayfa çizildikten sonra ayrıca yükleniyor.
- **Kalan.** Oturumlu ekranın tarayıcıda görsel denetimi. Giriş şifresini Claude yazamaz;
  kullanıcı panelde giriş yapınca yapılacak.

**İkinci tur (22 Eylül 2026).** Kullanıcı: "harita ortada çok büyük olmuş; afetzedelere özel,
kaydırmadan her şeyi kolayca bulacakları bir tasarım yap."

- **Görev odaklı tek ekran** (≥ 1280 × 640, kaydırmasız):
  - Solda "Yardıma mı ihtiyacın var?" kartı: isteğe bağlı durum, "durumunu yaz", kişi ve
    ihtiyaç; altta büyük kırmızı SOS. Düğme kalan yeri doldurur, en çok 288 px olur.
  - Çağrı gidince aynı kart "Çağrının durumu"na döner: büyük durum yazısı, üç adım (alındı /
    ekip atandı / kapandı, saatleriyle), gönderilenin özeti, "Ekip gelene kadar" önerileri,
    **Düdük sesi** düğmesi ve "Durumum değişti".
  - Düdük sesi üç kısa sestir (uluslararası yardım işareti) ve cihazda çalar; sunucuya bir
    şey gitmez.
  - Sağda "Nereye gidebilirim?": tür sekmeleri, 10 yerlik liste ve yanında küçük harita.
  - Hasar fotoğrafı, duyurular ve çağrı geçmişi altta üç düğme; pencerede (`<dialog>`)
    açılır.
  - En yeni duyuru en üstte tek satır. Konum yoksa SOS'a basınca konum penceresi açılır.
  - Uzun ekranda (yükseklik ≥ 860 px) formun altında "Deprem sonrası ilk adımlar" kutusu çıkar.
- **Dar ekran.** Kartlar alt alta dizilir, SOS ilk ekranda kalır. Üst çubuk sadeleşir: marka,
  canlılık noktası, 112, çıkış.
- **Denetim.** Oturum açılamadığı için geçici bir önizleme sayfası kullanıldı. Sayfa gerçek
  API'den önceden alınmış yanıtlarla çalıştı: Akevler yakın yerleri, altlık kataloğu, mahalle
  listesi, Antakya altlığı. Denetimden sonra silindi.
  - 1366×680, 1280×640, 1024×700 ve 1920×980'de ana alan ve SOS kartı kaymıyor.
  - Telefonda (375×812) SOS ilk ekranda.
  - Konum, hasar, duyuru ve çağrı pencereleri açılıyor. SOS gönderimi kartı "Bekliyor"
    durumuna çeviriyor.
- **Denerken düzeltilenler.**
  - Esc pencereyi kapatmıyordu; açık işleyici eklendi.
  - Dar ekranda kartlar ekrana sıkıştırılıyor, SOS görünmüyor ve harita düğmelerin üstüne
    biniyordu; sıkıştırma artık yalnız geniş ekranda.
  - SOS düğmesine ekran okuyucu adı verildi.
- **Kamera ucu.** Konumsuz gönderilen bir görüntüde 1,4 sn'de 4 tespit döndü, hepsinde kutu
  bilgisi var; ekip haritasına bir şey yazılmadı.
  - Model alakasız bir uydu görüntüsünde bile %29–38 güvenle "ağır hasar" işaretledi. Arayüzün
    sonucu "modelin tahmini" diye sunması bu yüzden gerekli.
- **Üretim derlemesi.** Afetzede rotası ilk açılışta 113,5 KB gzip JS; harita sonradan gelir.

**Üçüncü tur (22 Eylül 2026, J-51 ile).** Kullanıcı: "SOS butonu çok büyük ve ölü alan var;
renkler hep aynı, ayırt edici değil; bazı butonlar küçük, ayırt edilemiyor." Ayrıca fotoğrafta
model seçimi ve ihbar istendi (J-51).
- **SOS.** Düğme sabit boyda (64 px); boş yeri doldurmuyor. Kart içeriği kadar uzuyor.
  İhtiyaç seçimi SOS'tan çıktı, kendi penceresine taşındı: SOS hayati tehlike içindir.
  Durum seçenekleri simgeli ve 48 px.
- **Ölü alan.** SOS'un altında "Bildirimlerim" duruyor: gönderilen çağrı ve ihbarların canlı
  durumu. Boşken deprem sonrası ilk adımları yazıyor. Uzun ekranda (≥ 860 px) en altta
  duyuruların tam metni var. Sayfa 1440 px'te duruyor; geniş ekranda harita büyüyüp ekranı
  kaplamıyor.
- **Renk.**
  - Her ihbar türünün rengi ve simgesi var: SOS kırmızı, fotoğraf sarı, metin mor, ihtiyaç
    pembe. Konsolda da aynı renkler kullanılıyor.
  - Yer türü sekmeleri seçilince kendi renklerini alıyor.
  - Kartların başlığında simge var; SOS kartının üstünde kırmızı şerit var.
- **Düğmeler.** Dokunma hedefleri en az 40 px: kişi sayacı, konum, yol tarifi, üst çubuk
  (Duyurular, 112, Çıkış) ve pencere düğmeleri. Simgeler Phosphor'dan (ARAYUZ §6).
- **Düzen.**
  - Solda SOS ve Bildirimlerim; sağda Nereye gidebilirim ve üç "Bildir" düğmesi.
  - Duyurular üst çubukta, sayısıyla.
  - Konum penceresi ihbar penceresinin üstünde açılıyor; seçilen fotoğraf ya da yazılan
    metin kaybolmuyor.
  - Dar ekranda sıra: SOS, Bildir, Nereye, Bildirimlerim.
- **Denetim.** Önizleme sayfasıyla yapıldı; ayrıntı J-51'de.
  - 1280×640, 1366×680 ve 1920×980'de sayfa kaymıyor. 1280×640'ta çağrı durumu hâli de
    sığıyor.
  - Telefonda (375×812) kartlar üst üste binmiyor.
- **Denerken düzeltilenler.**
  - Dar ekranda "Nereye" ve "Bildirimlerim" üst üste biniyordu. Sıkışma artık yalnız geniş
    ekranda.
  - 1920 px'te sol altta büyük boşluk kalıyordu ve harita çok büyüyordu. Sayfa 1440 px'e
    sınırlandı ve duyuru kartı eklendi.
  - Fotoğraf incelendikten sonra 1. adım boş kalıyordu; "Başka fotoğraf seç" eklendi.
  - Kişi sayacında hızlı çift tıklama bir artışı yutuyordu. Artık işlevsel güncelleme
    kullanılıyor.
  - Metin modelinin adresi varsayılan hedefti. İlçe düzeyinde çözüldüğü için ekibi ilçe
    merkezine gönderecekti. Artık seçim afetzedede ve uzaklık yazılıyor.
  - Köşedeki kart 12 sn'de kapanıyordu; 20 sn yapıldı.

**Dördüncü tur (22 Eylül 2026).** Kullanıcı 1918×944 ekran görüntüsüyle geldi: "sağda ve
solda ölü alan var; duyurular ve gönderilenler alt alta sıkışmış, çok küçük; duyurular ilgi
çekmeli, bildirim düşmeli; 'Mahalleme dön' düğmesi haritanın bazı yerlerinde altta kalıyor."
- **Genişlik.** Sayfa sınırı 1440 → 1920 px. ≥ 1600 px'te üç sütun (`uclu:`):
  - Sol: SOS ve gönderilenler.
  - Orta: "Nereye" ve bildir düğmeleri.
  - Sağ: duyurular, boydan boya.
  - Izgara alan adlarıyla kuruldu (`kilav-afetzede`, `alan-*`). Dar ekranda kartlar
    `order` ile diziliyor.
- **Duyurular.**
  - Sağ sütun en önemli duyurunun renginde çerçeveleniyor. Üst bant duyurunun önem
    renginde zeminli.
  - Üst çubuktaki "Duyurular" düğmesi, duyuru varken renkli ve sayılı.
  - "Bilgi" önemi gri değil, vurgu renginde (kırmızı ve turuncu yine yalnız acil ve uyarı
    için).
  - Yeni duyuru canlı akıştan gelince üst çubuğun altında uyarı çıkıyor. Acil uyarı
    kapatılana kadar, ötekiler 30 sn kalıyor. Yeni kart bir kez vurgulanıyor.
  - İstenirse tarayıcı bildirimi var ("Bildirim aç"). Sekme arka plandayken düşüyor.
  - Dar ekranda en yeni iki duyuru gösteriliyor, kalanı pencerede.
- **Harita düğmesi.** Harita kabı `isolate` ile kendi katman bağlamında. deck.gl tuvali
  "Konumuma / Mahalleme dön" düğmesinin ve künyenin üstüne boyanıyordu. Düğme büyüdü ve
  simge aldı.
- **Denetim.** Önizleme, test sunucusunun gerçek yanıtlarıyla yapıldı: iki test duyurusu kopya
  veritabanına yayınlandı, sayfa denetimden sonra silindi. Panel gizli olduğu için
  denetimin çoğu ölçümle yapıldı.
  - 1918×944: üç sütun. Gönderilenler 180 → 400 px, "Nereye" 1022 px geniş, duyurular
    814 px. Sayfa kaymıyor.
  - 1600×900: üç sütun, harita 421×479.
  - 1366×680: iki sütun. Acil duyuru bandıyla gönderilenler 136 px'e iniyor.
  - Telefon: sıra SOS, Bildir, Duyurular (iki tane), Nereye, Gönderilenler.
  - Düğmenin ortasındaki noktada artık düğmenin kendisi var (`elementFromPoint`).
- **Denerken düzeltilen.** Telefonda duyuru kartı 5 px'e eziliyordu; sıkışma yalnız geniş
  ekranda.
- **Not.** Kullanıcının görüntüsünde liste "kuş uçuşu" diyordu. Sayfa, sunucu yeni rota
  koduyla yeniden başlamadan önce açılmıştı ve eski liste önbellekte kalmıştı. Mahalle
  merkezinden (Akevler) sunucu yürüme mesafesini veriyor: Cebrail 358 → 476 m. Sayfa
  yenilenince düzelir.
- Afetzede ilk açılışı 140,7 KB gzip (önceki 137,4).

**Beşinci tur (22 Eylül 2026): mahalle araması.** Kullanıcı konum penceresinin görüntüsüyle
geldi: "a yazınca a ile olanlar çıksın, b yazınca b ile olanlar; yoksa onu belirtsin; ab
yazarsa ab ile başlayanlar olsun."
- **Sorun.** Eski arama iki harften önce çalışmıyordu: "a" yazınca liste boştu ve "yok"
  da denmiyordu. İki harften sonra adın herhangi bir yerinde geçen diziyi buluyordu ("ab"
  yazınca adının ortasında "ab" geçenler de çıkıyordu). En çok 8 sonuç gösteriyordu ve
  kaç tane bulunduğunu söylemiyordu.
- **Yapılan** (`MahalleSecici.tsx`):
  - Arama ilk harften başlıyor.
  - Önce adı yazılanla başlayan yerler geliyor, sonra adındaki başka bir kelimesi
    yazılanla başlayanlar ("ab" → "Hacı Abdi"). Adın ortasındaki harf dizisi sayılmıyor.
  - Liste alfabetik. Eşleşen harfler kalın, kaç yer bulunduğu yazılıyor.
  - Sonuç yoksa "“xq” ile başlayan yer yok." yazıyor; ne yapılacağı da altında.
  - En çok 50 sonuç gösteriliyor; fazlası varsa "bir harf daha yaz" deniyor.
  - Enter ilk sonucu seçiyor, oklar listede geziyor.
- **Türkçe harfler.**
  - Düz harf Türkçe karşılığını da buluyor: "c" hem C'yi hem Ç'yi getiriyor.
  - Türkçe harf yazılırsa birebir aranıyor: "ç" yalnız Ç ile başlayanları getiriyor.
  - Büyük "I" Türkçe klavyede ı, İngilizce klavyede i. İkisini de buluyor. Birebir
    arama ilk denendiğinde "I" yazınca İbrahimli, İnönü gibi 19 yer kayboluyordu;
    denerken düzeltildi.
- **Denetim.** Önizleme sayfası, gerçek yer listesiyle (`veri/altlik/yerler.json`,
  496 yer) yapıldı. Sayfa denetimden sonra silindi.

  | Yazılan | Sonuç |
  |---|---|
  | (boş) | ipucu |
  | a | 46 yer |
  | ab | 5: Abdulgaffar, Abdülhamid Han (iki bölge), Hacı Abdi, Şehit. Abdullah Çavuş. Mah. |
  | c / ç | 30 / 18 |
  | cu / çu | 6 (Cumhuriyet'ler ve Çukurdere) / 1 (Çukurdere) |
  | I, i, İ | 19 (İ ile başlayanlar) |
  | xq | "“xq” ile başlayan yer yok." |

  Klavye: aşağı ok → Akasya, Akbulut; yukarı ok arama kutusuna dönüyor; Enter Akasya'yı
  seçip pencereyi kapatıyor.

---

## J-49 🔴 Oturumsuz açılış "Yükleniyor…"da takılıyordu (b998807 ile gelen hata)
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (kullanıcı: "yükleniyor diyor kalıyor ekran") · **İlgili:** J-43, J-48

**Sorun.** J-43'te `apiPost`'a "401 gelirse jetonu yenile, bir kez tekrar dene" adımı
eklendi. Bu adım kimlik uçlarına da uygulanıyordu:
- Oturum yokken açılıştaki yenileme isteği 401 alıyor.
- `apiPost` bu yüzden yenileme başlatmak istiyor.
- Yenileme fonksiyonu uçuştaki isteğin kendisini döndürüyor; istek kendi bitmesini bekliyor.

Sonuç: oturumu olmayan herkes, yeni afetzede dahil, "Yükleniyor…" ekranında kalıyordu.
Yanlış şifreyle giriş de hiç bitmezdi. Tarayıcı testleri hep açık oturumla yapıldığı için
yakalanmadı.

**Yapıldı.** Kimlik uçlarında (`/api/oturum/*`) yenileme denenmiyor. Öteki POST'larda
(SOS, bildirim, analiz) 401'de bir kez yenileyip yeniden gönderme sürüyor.

**Denetlendi.** Çerezsiz adreste (`127.0.0.1:3200/afetzede`) denendi:
- Düzeltmeden önce 5 saniye sonra hâlâ "Yükleniyor…" vardı ve tek bir yenileme isteği
  gitmişti.
- Düzeltmeden sonra sayfa giriş ekranına yönlendi.
- Oturumu açık sekme afetzede ekranını açmaya devam ediyor.

**Ders.** Oturumsuz açılış da sınanmalı. Çerezsiz sekme için `localhost` yerine `127.0.0.1`
kullanılabilir.

---

## J-48 🟠 Afetzede hesap açamıyordu; konsolda afetzede ekranına giden yol yoktu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (kullanıcı: "hani ben göremiyorum afetzede tarafını") · **İlgili:** J-43, kural 5

**Sorun.**
- Giriş ekranı "yeni hesaplar afetzede yetkisiyle açılır" diyordu ama hesap açma formu yoktu.
  Kayıt ucu (`/api/oturum/kayit`) çalışıyordu, arayüzden ulaşılamıyordu. Gerçek bir afetzede
  ekrana hiç giremiyordu.
- Koordinatör girişte konsola yönleniyordu. Konsolda afetzede ekranına bağlantı yoktu; ekran
  ancak adres elle yazılınca açılıyordu.

**Yapıldı.**
- **Giriş ekranı.** "Hesap aç" formu eklendi: ad soyad, e-posta, en az 8 karakterlik şifre.
  Rol alanı yok; sunucu afetzede açar. Hesap açılınca doğrudan afetzede ekranına gidiliyor.
  Başlık "Konsola giriş" yerine "Giriş yap" oldu, çünkü afetzede de buradan giriyor.
- **Konsol.** Üst çubukta koordinatör ve yönetici için "Afetzede ekranı" bağlantısı var
  (önizleme).
- **Afetzede önizlemesi.** "Konsol" dönüş bağlantısı eklendi.

**Denetlendi.**
- Üst çubukta bağlantı `/afetzede`'ye gidiyor.
- Çerezsiz adreste (`127.0.0.1`) giriş ekranında "Hesap aç" düğmesi ve form görünüyor.
- Formla hesap açmayı Claude denemedi (şifre girmek kullanıcıya ait). Kayıt ucunun yeni
  hesabı afetzede rolüyle açtığı J-42/J-45 testlerinde görüldü.

---

## J-47 🟠 Canlı akış sessizce ölünce ekran "canlı" diyordu; kopukken gelen mesajlar kayboluyordu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (J-45 sınanırken) · **İlgili:** J-42, J-45, kural 4

**Sorun.**
- **Ölü bağlantı fark edilmiyordu.** Arka uç yeniden başlayınca geliştirme vekili (Vite)
  tarayıcıya giden akışı kapatmadı. EventSource bağlantıyı açık sandı, ekran "canlı" dedi,
  sunucuda ise hiç bağlantı yoktu. Üç dakika beklendi; yeniden bağlanma olmadı. Aynı durum
  mobil ağda bağlantı sessizce koptuğunda da olur.
- **Nabız istemciye ulaşmıyordu.** Sunucunun 20 saniyelik nabzı SSE yorum satırıydı
  (`: ping`). EventSource yorumları JavaScript'e iletmediği için istemci ölü akışı göremiyordu.
- **Kopukken gelen mesajlar kayboluyordu.** Sunucu mesaj biriktirmez; istemci de yeniden
  bağlanınca verisini tazelemiyordu. Kopukluk sırasında geri çekilen bildirim afetzede
  ekranında kaldı. Ekip ataması ve yeni bildirim de aynı yoldan kaçabilirdi.

**Yapıldı.**
- Sunucu nabzı adlandırılmış olay olarak gönderiyor: `event: nabiz`.
- İstemcide yerel bir bekçi var. 45 saniye hiçbir sinyal (mesaj ya da nabız) gelmezse
  bağlantıyı düşmüş sayıyor ve yeniden bağlanıyor. Bekçi sunucuya istek atmıyor.
- Akış **yeniden** bağlandığında akışa bağlı sorgular bir kez tazeleniyor: çağrılar, özet,
  bildirimler, hasar, ısı ve ekipler. Yoklama değil; yalnız bağlantı geri geldiğinde oluyor.

**Sınandı.** Afetzede sekmesi açıkken test bildirimi yayınlandı. Sonra:
- Arka uç kapatılıp açıldı.
- Bildirim, sekme yeniden bağlanmadan geri çekildi (o anda sunucuda 0 akış bağlantısı vardı).
- Sekme 27 saniye sonra bekçiyle yeniden bağlandı ve hemen çağrılarını ve bildirimlerini
  yeniden istedi.
- Bant kalktı. Düzeltmeden önceki aynı denemede bant kalmış, sekme hiç yeniden bağlanmamıştı.

---

## J-46 🟠 Konsol canlı modda dakikada bir bütün pencere sorgularını yeniden istiyor
**Durum:** KISMEN KAPALI (22 Eylül 2026) — öneri J-52 ile birlikte uygulandı [K]; ağ kaydıyla ölçüm yapılmadı · **Bulundu:** 21 Eylül 2026 (J-43'ün ağ kaydında) · **İlgili:** kural 4, ARAYUZ §10, J-11, J-52

**Sorun.** Canlı modda zaman penceresi saatle birlikte kayıyor (varsayılan: son 6 saat) ve
pencere, sorgu anahtarının parçası. Dakika değişince anahtarlar değişiyor ve pencereye bağlı
her sorgu yeniden gidiyor. Hiçbir şey değişmese bile bu böyle.

**Ölçüldü.** Genel mod, boşta, tek sekme: **dakikada 7 istek.** Bunlar `hasar-noktalari`,
`sos`, `ozet` ve dört `heatmap` (uydu, sos, kamera, metin). Eski webin ~65 isteğinden az,
ama kural 4 "yalnızca değişiklik olduğunda" diyor.

**Öneri.**
- Sorguyu kaba bir çapaya bağla: pencere başlangıcı 15 dakikaya yuvarlanır ya da canlıya
  geçerken sabitlenir.
- Tam pencereyi istemci süzsün. Yeni veri zaten canlı akışla geliyor.
- Isı ızgarası sunucuda üretiliyor; onu da aynı çapaya bağla.

**22 Eylül 2026 (J-52 ile).**
- Canlıda sorgu başlangıcı 15 dakikalık çapaya bağlandı ve bitiş açık bırakıldı. Listeler
  tam pencereye istemcide süzülüyor. Sorgu anahtarları artık dakikada bir değişmiyor;
  yalnız çapa değişince (15 dakikada bir) ve canlı akış mesajında tazeleniyor.
- Sunucunun saydığı özet ve ısı en çok 15 dakika geniş pencereyle hesaplanıyor. Listeler
  tam.
- **Ölçülmedi.** Dakikadaki istek sayısı gerçek oturumla ağ kaydında sayılmalı; hedef ~0.

---

## J-45 🔴 Eski demo hesaplarının jetonu kodda sabit; herkes acil bildirim yayınlayabiliyor
**Durum:** KISMEN KAPALI (21 Eylül 2026) — madde 1 yapıldı (yeni bildirim ucu, konsol modu, kalıcı kayıt, geri çekme); madde 2 (eski demo hesapları bayrak arkasına) KARAR BEKLİYOR · **Bulundu:** 21 Eylül 2026 (J-43 sınanırken) · **İlgili:** J-43, J-47, CLAUDE.md kural 5

**Sorun.**
- `cekirdek.py::_demo_user` sekiz demo hesap tanımlıyor. Jetonları kodda sabit:
  `token-<kimlik>`, ör. `token-responder-101`. Şifreleri `password123`. Eski webin giriş
  sayfası bu şifreyi ekranda gösteriyor. Depo açık (upstream).
- `POST /api/notifications/send_emergency` bu jetonu kabul ediyor. Jetonu bilen herkes bütün
  afetzedelerin ekranına acil bildirim düşürebilir, ör. "Baraj yıkıldı, tahliye edin".
  Afetzede ekranı bildirimi en üstte gösterdiği için etkisi arttı.
- Aynı jetonlar `_require_role` kullanan öteki eski uçları da açıyor: ekip sohbeti, görev
  kilidi vb.
- Yeni kimlikle bildirim gönderen bir uç yok. Konsoldan henüz bildirim yayınlanamıyor.
- J-43 sınanırken test bildirimi bu yoldan gönderildi. Açığın gerçek olduğu böyle
  doğrulandı.

**Öneri.** Karar gerekiyor, çünkü eski webin demo girişini etkiliyor.
1. `POST /api/bildirimler` ucu: yeni kimlik,
   `Depends(rol_gerektir('koordinator', 'yonetici'))`. Konsola bir gönderme paneli.
2. Eski demo hesapları bir ortam bayrağının arkasına alınsın, ör. `QUAKEMIND_ESKI_DEMO=1`.
   Geliştirmede açık, dağıtımda kapalı olur. Varsayılanı değiştirmek eski webin demo girişini
   kapatır.

**Yapıldı: madde 1** (21 Eylül 2026, kullanıcı: "J-45'teki bildirim ucunu yap").
- **Kalıcı kayıt.** Bildirimler artık depoda (`bildirimler` tablosu). Eskiden bellekteydi:
  sunucu yeniden başlayınca yayındaki bildirim kayboluyor, kimin gönderdiği tutulmuyordu.
  Önem tek sözlükte: `acil` / `uyari` / `bilgi`.
- **Yeni uçlar.**
  - `POST /api/bildirimler`: yalnız koordinatör ve yönetici (`Depends(rol_gerektir)`).
    Başlık 3–120, metin 3–1000 karakter, büyüklük 0–10; ikisi de isteğe bağlı olan bölge ve
    büyüklük boş kalabiliyor.
  - `POST /api/bildirimler/{id}/kaldir`: yanlış ya da tanımadık bildirimi geri çeker. Kayıt
    silinmez; kimin ve ne zaman çektiği yazılır. İkinci kez çekmek 409.
  - `GET /api/bildirimler`: konsol için geçmiş, gönderen ve kaynakla (saha ve üstü).
  - `GET /api/bildirimler/aktif`: afetzedeye yalnız yayındakiler gider; gönderenin adı ve
    kaynak gitmez.
- **Eski uçlar aynı tabloda.** `send_emergency` artık depoya `kaynak = eski` diye yazıyor,
  `/api/notifications/active` depodan okuyor. İkisinin biçimi değişmedi. Konsoldan yayınlanan
  bildirim eski webde de görünüyor. Sınır: eski webin bandı geri çekilen bildirimi sayfa
  yenilenene kadar göstermeye devam ediyor; eski web dondurulduğu için düzeltilmedi.
- **Konsol modu "Acil bildirim".**
  - Dört şablon var: artçı sarsıntı, tahliye, dağıtım noktası, yol kapalı. Şablondaki
    `[bölge]` gibi köşeli ayraçlı yerler doldurulmadan yayın açılmıyor; şablon metni gerçek bir
    olaymış gibi gidemiyor. Elle yazılmış metin şablonla sessizce ezilmiyor, önce soruluyor.
  - Önizleme, afetzedenin göreceği kartın aynısı (ortak bileşen: `kabuk/BildirimKarti.tsx`).
  - Yayın iki adımlı onayla yapılıyor.
  - Sağ panel yayındakileri ve geri çekilenleri gösteriyor. Eski uçtan gelen kayıtta şu
    uyarı var: "o uç sabit demo jetonlarını kabul ediyor, tanımadığın bir bildirimse geri çek".
    Böylece madde 2 kararına kadar sahte bildirim en azından kaldırılabiliyor.

**Sınandı.**
- **Uçtan uca, 22 denetim geçti.**
  - Kimliksiz istek 401, afetzede 403 alıyor (yayın, geçmiş ve geri çekme). Geçersiz önem,
    boş başlık ve 12 büyüklük 422 dönüyor.
  - Yayın afetzedenin akışına düşüyor; afetzedeye gönderen gitmiyor.
  - Eski web aynı bildirimi kendi biçiminde görüyor.
  - Sabit demo jetonuyla eski uçtan gönderilen kayıt konsolda `eski` ve "Afet Saha Ekibi"
    diye çıkıyor.
  - Geri çekme sırayla akışa düşüyor; ikinci çekme 409, olmayan kayıt 404.
- **Kalıcılık.** Yayın sonrası arka uç yeniden başlatıldı; bildirim yayında kaldı.
- **Tarayıcı.**
  - Şablon, köşeli ayraç kilidi, ezme sorusu, önizleme ve onay denendi.
  - Konsoldan yayınlanan bildirim ikinci sekmedeki afetzede ekranına yoklamasız düştü
    (açılış dahil 2 istek). Konsoldan geri çekildi.
- **Duman testi.** 67 istek. İlk 63'ü önceki imzayla aynı; 4 yeni istek eklendi ve referans
  imza güncellendi.
- **Üretim derlemesi.** Afetzede rotası 108,3 KB gzip JS; harita motoru girmiyor.

**Test kayıtları.** 5 bildirim, hepsi "TEST J-45" etiketli ve geri çekilmiş; bir test
afetzede hesabı.

---

## J-44 🟠 Afetzedeye hasar bilgili yol tarifi verilemiyor
**Durum:** KAPALI (22 Eylül 2026) — beş bölgede kendi yol ağımız ve Dijkstra; üç açık madde aşağıda · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-43, J-34, J-17, J-50, D-04, ARAYUZ §8 ("rota ve toplanma alanı")

**Sorun.**
- Kapanma bilgisi yalnız analiz oturumunda duruyor: bellekte ve 30 dakika
  (`ROAD_DAMAGE_SESSION_TTL_SEC`). Rota ucu `/api/road_damage/route` bu oturumu istiyor.
  Afetzedenin isteği geldiğinde çoğu zaman oturum yok.
- Oturumsuz `safe_route` her istekte yol ağını Overpass'tan indiriyor. Bu kural 3'ü çiğniyor,
  dakikalar sürüyor ve bölgeyi üçüncü tarafa gönderiyor.
- Kapanmalar `yol_kapanmalari` tablosuna yalnız segmentin orta noktası olarak yazılıyor.
  Yönlendirilebilir yol ağı hiçbir yerde saklanmıyor.
- Bu yüzden yeni ekran toplanma alanını kuş uçuşu uzaklık ve yönle veriyor, yol tarifi yok.
  Ekranda da bu açıkça yazıyor.

**Öneri.**
1. Bölge yol ağını yerel OSM kopyasından bir kez üret (altlık gibi) ve dosyaya yaz. API ya da
   rota işçisi onu belleğe bir kez yüklesin.
2. `yol_kapanmalari` noktalarını en yakın kenara oturt. Kaynağı ve zamanı kenarda dursun.
3. `GET /api/afetzede/rota?hedef=…` ucu: yumuşak maliyetli A* (J-34 bayrağı), birkaç on ms.
   Yanıtta sokak adlarıyla adım listesi, uzunluk, geçilen riskli kenar ve kullanılan kapanma
   verisinin tarihi olsun.
4. Ekranda harita motoru olmadan adım listesi. İstenirse küçük bir SVG çizimi.

**22 Eylül 2026 — yapıldı (kullanıcı: "A* / Dijkstra çalışmıyor herhalde, toplanma alanına
giderken yollardan değil kuş bakışı çiziyor").**

**Sebep.** Motor bozuk değildi; afetzede ekranı yol ağına hiç bağlı değildi. Yer seçilince
haritada kuş uçuşu kesikli çizgi çiziliyordu. "Yürüyerek yol tarifi" düğmesi dış servise
(OSRM) gidiyordu ve bilinen kapanmaları bilmiyordu. Not: kodda ve eski arayüzde geçen "GNN
rota motoru" bir sinir ağı değil, Dijkstra/A*'dır (D-04).

**Yapıldı.**
- **Yol ağı** (öneri 1): `araclar_yol_agi_uret.py`.
  - Yerel OSM kopyasından beş bölgenin (±12 km) yürünebilir yolları okunuyor. Kavşaklar
    koordinat birleştirilerek kuruluyor (1e-7°).
  - `foot=no` ve `access=no/private` yollar ve otoyol dışarıda. Tek yön yayaya
    uygulanmıyor. En büyük bağlı parça tutuluyor.
  - Çıktı `veri/yol_agi/<bölge>.npz` ve `katalog.json` (git dışında).
- **Rota motoru** (`yol_agi.py`, öneri 2–3).
  - Ağ bir kez belleğe alınıyor. Afetzedenin konumundan tek bir Dijkstra koşuyor
    (scipy, C); seçilen yere rota ve yakındaki bütün yerlerin yürüme mesafesi aynı
    aramadan çıkıyor.
  - **Hasar cezası:** araç motorunun `risk_weight` işlevi. Hasar noktasına 50 m içinde
    3×, 150 m içinde 1,5×, 400 m içinde 1,1×. Uzaklık kenarın doğru parçasına ölçülüyor.
    Hasar noktası şunlar: uydu (skor ≥ 0,5), kamera ihbarı, enkaz bildiren yazılı ihbar.
    SOS tehlike sayılmıyor.
  - **Bilinen kapanma:** Uydu analizinden gelen kapanmanın 25 m içindeki kenar silinmiyor,
    maliyeti 20 kat oluyor (yumuşak maliyet, J-34). Başka yol yoksa rota yine bulunuyor ve
    ekran bunu yazıyor. Tasarım kararı [T].
- **Uçlar.**
  - `POST /api/afetzede/rota` (kimlik ister; dış servise istek gitmez). Yanıtta yol
    koordinatları, uzunluk, süre, sokak adlarıyla adımlar, rotadaki riskli metre ve
    kapanma, hesaba katılan kapanma ve hasar sayısı var.
  - `GET /api/yakin-yerler` her yer için yürüme mesafesi (`yuruyusM`) veriyor. Liste buna
    göre sıralı.
- **Afetzede ekranı.**
  - Yer seçilince rota yollar üzerinden kendiliğinden çiziliyor; harita bütün rotayı
    sığdırıyor.
  - Seçili satırda uzunluk ve süre, kuş uçuşu uzaklık, ilk dört adım ve hasar uyarıları
    yazıyor.
  - Liste başlığı "yürüme mesafesi" diyor.
  - Kuş uçuşu çizgi yalnız rota yokken görünüyor. Dış servis rotası yalnız yol ağı
    üretilmemiş bölgede ve istenince kullanılıyor.

**Ölçüldü.**
- **Üretim.** Beş bölge ~5 dk sürdü (okuma 44–69 sn/bölge, kurulum ≤ 1,7 sn). Diskte
  14,6 MB tuttu.

  | Bölge | Düğüm | Kenar | En büyük parça |
  |---|---|---|---|
  | Antakya | 139.749 | 147.013 | %99,5 |
  | Antep | 131.492 | 152.390 | %99,3 |
  | Malatya | 113.407 | 121.372 | %98,0 |
  | Maraş | 98.580 | 107.945 | %99,4 |
  | Adıyaman | 57.104 | 61.595 | %99,1 |

- **Süre.** Ağ yükleme 0,66 sn (açılışta arka planda). Hasar cezası ve Dijkstra 23–25 ms.
  Çarpan hesabı veri değişince bir kez yapılıyor, 6 ms sürüyor; uzun kenarlar ayrı
  denenmeden önce 1.372 ms sürüyordu. Uç üzerinden rota 65–75 ms, 35 yerin yürüme
  mesafesiyle yakın yerler 97–117 ms.
- **Hasar verisi.** Antakya'daki 39 kapanmanın hepsi yola oturdu (48 kenar). Uzaklık kenar
  orta noktasından ölçülünce 4'ü kaçıyordu.
- **Akevler → Antakya Devlet Hastanesi.** 2.097 m, ~26 dk. OSRM 2.245 m, kuş uçuşu 1.747 m.
  Adımlar: 7. Bahçeli Sk. → 2. Bahçeli Sk. → Şen Sk. → Cumhuriyet Cd. → Mehmet Kafadar Cd.
- **Sıralama.** Kuş uçuşunda en yakın hastane Özel Mozaik (1.556 m); yürüyerek 2.498 m ile
  ikinci. Malatya'da "Şifa" toplanma alanı kuş uçuşu 144 m, yürüyerek 446 m.
- **Duman testi.** 83 istek. Önceki 80'den fark: yakın yerler `yurume` alanını kazandı;
  3 yeni rota isteği (kimliksiz 401, Ankara 404, Antakya 200) eklendi.
- **Önizleme.** Test sunucusunun gerçek yanıtlarıyla bakıldı. Rota haritada sokakları
  izliyor. Yol ağı yokken ekran kuş uçuşuna ve dış servis düğmesine dönüyor.

**Açık.**
- Yol ağı yalnız beş bölgede (±12 km). Dışarıda kuş uçuşu ve istenirse dış servis kalıyor.
- Kapanma verisi yalnız uydu analizinden geliyor. Sahadan bildirilen kapanma
  (`/report_blockage`) ve EMSR648 katmanı bu depoya yazılmıyor, rota onları bilmiyor.
- Konsolun "Yol ve rota" modu hâlâ bağlı değil. Ekip rotası ayrı iş.

**22 Eylül 2026 — adım adım tarif (kullanıcı: "bu bilgileri sen mi yazdın, adım adım ilerleyişi
yapan bir sistemimiz var mı; gösterimi modern ve belirgin yapalım").**
- **Kaynak.** Adımlar elle yazılmıyor, rotanın kendisinden çıkıyor.
  - Aynı adlı (OSM `name`) ardışık kenarlar tek adım. Adsız yol, türüne göre adlanıyor
    ("yaya yolu", "merdiven").
  - 12 m'den kısa kavşak parçası komşu adıma katılıyor.
- **Dönüş yönü (yeni).** Sokak geçişinde kavşaktan 20 m önceki ve sonraki noktaya göre açı
  farkı ölçülüyor. Sınıflar: düz (< 20°), hafif (20–60°), dönüş (60–135°), keskin (≥ 135°);
  sağ ve sol ayrı. İlk adımda yürüme yönü (8 yön) veriliyor.
- **Ekran.** Rota kartı yenilendi.
  - Üstte büyük uzunluk ve süre.
  - Rotadaki hasar durumu renkli etiketle: yeşil "bilinen kapanma ya da hasar yok",
    turuncu "hasar noktasına yakın", kırmızı "kapanmadan geçiyor".
  - Dönüş oklu zaman çizelgesi, varış adımı, "tüm adımlar" düğmesi, katlanan "Nasıl
    hesaplandı?".
- **Sınır.** Yürürken hangi adımda olunduğunu izleyen bir sistem (canlı yön tarifi, rotadan
  sapınca yeniden hesap) YOK. Liste rota istendiğinde bir kez hesaplanıyor; ekran bunu da
  yazıyor.
- **Ölçüldü.** Akevler (ekrandaki konum) → Antakya Devlet Hastanesi: 2.097 m, 8 adım, uç 39 ms.
  - Adımlar: güneybatıya başla 7. Bahçeli Sk. → sağ 2. Bahçeli Sk. → sol Şen Sk. → sağ
    Cumhuriyet Cd. 713 m → düz Mehmet Kafadar Cd. 582 m → sol → sağ → sol.
  - Haraparası rotasında "sola dön" haritadaki kuzeye kıvrılışla tutarlı.
- **Harita denetimleri.** Ölçek çubuğu ve künye "Konumuma dön" düğmesiyle aynı görünüşte:
  opak zemin, belirgin kenar, açık yazı, gölge. deck.gl tuvalinin üstünde; ölçek konsolda da
  değişti.

---

## J-43 🟠 Afetzede ekranı: eski webdeki portal yeni konsolda yeniden yazıldı
**Durum:** KAPALI (21 Eylül 2026, ilk sürüm; açık kalanlar J-44, J-45) · **Bulundu:** 21 Eylül 2026 (kullanıcı isteği) · **İlgili:** J-42, ARAYUZ §8, MIMARI §7

**Eski webde bulunanlar** (`quakemind-web/src/app/survivor`). Bunlar ya taşınmadı ya
düzeltilerek taşındı:
- Gönderim başarısız olunca da "SOS sinyaliniz alındı" yazıyordu
  (`catch { setSosSent(true) }`). Yardım talebi de hatada "kayıtlara eklendi" diyordu.
- Konum alınamazsa çağrı sessizce Antakya merkezine düşüyordu (`ANTAKYA_COORDS`).
- Kişi sayısı ve aciliyet mesajın içine metin olarak gömülüyordu ("[KİŞİ SAYISI: 3]").
  Ekipler bunlara göre süzemiyordu.
- Bütün toplanma alanları "🟢 Güvenli" etiketliydi. Oysa liste depremden önceki resmi
  listedir, alanın bugünkü durumu bilinmiyor.
- Rota dış OSRM demo sunucusundan isteniyordu. Kullanıcının tam konumu üçüncü tarafa
  gidiyordu, rota da yıkık ya da kapalı yolu bilmiyordu. `allowOnlineFallback=false`
  adının söylediğini yapmıyordu.
- Bildirim bandı 10 saniyede bir yokluyordu (kural 4).
- Gönderen yazmasa da bildirimlere 6,8 büyüklük ve "Hatay" varsayılan olarak ekleniyordu.
- Kamera sayfası analiz başarısız olunca sahte sonuç gösteriyordu. Yapıya "güvenli" hükmü de
  veriyordu.

**Yeni ekran** (`konsol/src/afetzede/`): telefonda tek sütun, harita motoru yok.
- **Bildirim bandı.** `GET /api/bildirimler/aktif` ile gelir, canlı akıştaki `bildirim`
  mesajıyla tazelenir.
- **Yardım çağrısı.**
  - Durum seçilir: Mahsur kaldım / Yaralı var / Yardım gerekli. Ayrıca kişi sayısı,
    ihtiyaçlar (su, gıda, barınma, ısınma, ilaç, tuvalet) ve en çok 500 karakterlik not.
  - Konum cihazdan alınır. Kısa bir izlemeyle en iyi doğruluk tutulur ve "±m" yazılır.
  - Cihaz konum veremezse mahalle seçilir: altlığın yer adları, 5 bölgede 496 ad. Böyle
    gelen konum "yaklaşık" diye işaretlenir. Hiç konum yoksa çağrı gönderilemez ve ekran bunu
    söyler.
  - Başarı mesajı ancak sunucu 201 dönünce çıkar. Hatada sebep yazılır, bilgiler silinmez.
  - Açık çağrısı olan afetzedeye ikinci çağrıdan önce hatırlatılır.
- **Çağrılarım.** Son 7 gün; her çağrıda durum rozeti ve açıklaması. Canlı akışla tazelenir.
  Bağlantı koparsa ekran bunu yazar ve elle yenileme düğmesi çıkar.
- **En yakın toplanma alanları.** AFAD veri setinden; kuş uçuşu uzaklık ve sekiz yönlü yön.
  "Haritada aç" bağlantısı yalnız alanın konumunu götürür. Kaynak ve sınırlar Teknik notunda
  yazılı.
- **Sözleşme.** `POST /api/sos` artık `kisiSayisi`, `ihtiyaclar`, `konumKaynagi`
  (`gps` | `mahalle`) ve `konumDogrulukM` alıyor (`ek` JSON sütunu). `GET /api/sos` bunları
  geri veriyor.
- **Ekip ekranları.** SOS kuyruğu, seçili çağrı ve harita ipucu kişi ve ihtiyaç satırını
  gösteriyor. Mahalle merkezinden gelen çağrıda "Dikkat: yaklaşık konum" uyarısı çıkıyor.
- **`apiPost`.** 401 alınca jetonu bir kez yeniliyor. Erişim jetonu 15 dakikalık; sayfayı açık
  bırakan afetzedenin çağrısı bu yüzden düşmesin.
- **Bildirim.** `send_emergency` canlı akışa `bildirim` yayınlıyor. Büyüklük ve konum
  varsayılanları kaldırıldı.
- **Toplanma ucu.** `allowOnlineFallback=false` iken OSRM'e gitmiyor. Varsayılan (`true`)
  değişmedi; eski web aynı çalışıyor.
- Koordinatör ve yönetici ekranı "önizleme" notuyla açabiliyor.

**Ölçüldü.**
- **Rota başına indirilen JS** (üretim derlemesi, gzip):

  | Rota | Önce | Sonra |
  |---|---|---|
  | afetzede | 637,6 KB | 107,8 KB |
  | giriş ekranı | 626,6 KB | 96,9 KB |
  | konsol | 658,4 KB | 664,6 KB (harita burada, tembel yüklenir) |

  Sebep `vite.config.ts`'teki `manualChunks` nesne biçimiydi: Vite'ın ön-yükleyicisini ve
  CommonJS yardımcısını harita parçasına çekiyordu. Giriş dosyası da bu yüzden 2 MB'lık
  parçayı statik olarak içe aktarıyordu. Parça ayarı işlev biçimine çevrildi, yardımcılar ayrı
  bir parçaya alındı. Önizleme sunucusunda doğrulandı: /afetzede yalnız 5 dosya indiriyor,
  konsol haritayla açılıyor.
- **İstek sayısı.** Afetzede ekranı açılışta 5 istek atıyor: oturum yenileme, akış,
  bildirimler, çağrılarım, toplanma. Sonrasında yalnız canlı akış mesajı gelince tazeleniyor.
- **Toplanma ucu.** 5 istekte 172–198 ms, yanıt 20 KB. Sürenin ~122 ms'si 15,7 MB'lık AFAD
  JSON'unu her istekte yeniden ayrıştırmaktan geliyor. Veri bellekte tutulursa süre düşer; bu
  yapılmadı.

**Denetlendi** (tarayıcı, 375 × 812).
- **GPS yolu.** Tarayıcı konumu test için Ankara'ya sabitlendi. Ekran ±15 m doğruluk ve en
  yakın 5 AFAD alanını gösterdi (Cumhuriyet 20 m, Kızılay 60 m…).
- **Gönderim.** Ekran "Çağrın alındı · 19:03 · Bekliyor" dedi. Koordinatör çağrıyı kapatınca
  başarı kutusu ve liste yoklama olmadan "Kapandı" oldu.
- **Mahalle yolu.** "akev" yazınca Akevler (Antakya) çıktı. Toplanma listesi mahalle merkezine
  göre hesaplandı ve "yaklaşık" yazdı.
- **Duman testi.** 63 ucun 61'i aynı. İki fark bilerek yapıldı: `/api/sos` dört alan kazandı
  ve yeni uçlar eklendi. Referans imza güncellendi.

**Taşınmayan: kamera / fotoğraf.** Güvenli yeniden tasarım önerisi:
- Fotoğraf saklanır ve ihbar olarak kuyruğa girer.
- Yapıya "güvenli" hükmü verilmez.
- Model sonucu ekip ekranında "modelin tahmini" diye görünür.

**Test kayıtları.** Geliştirme veritabanında duruyorlar, "TEST J-43" etiketli ve kapatıldılar:
- SOS: `sos-af570c07`, `sos-9212d9f0`, `sos-4166b7a2`
- Test afetzedeleri: `kul-a1b1670f81`, `kul-28d8597e7f`
- Test bildirimi bellekte duruyor; arka uç yeniden başlayınca silinir.

---

## J-42 🔴 Canlı akış (SSE) kimliksizdi: herkes her SOS konumunu ve ekip konumlarını alıyordu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (afetzede ekranı incelenirken) · **İlgili:** J-43, CLAUDE.md kural 5, MIMARI §9

**Sorun.**
- `/api/live` kimlik istemiyordu. Giriş yapmamış biri akışı açıp her yeni SOS çağrısının
  konumunu, önceliğini ve mahallesini alabiliyordu; ekip konumlarını da.
- Afetzede de aynı akışı alıyordu, başkalarının çağrı konumları dahil. MIMARI §9 "afetzede yalnız
  kendi çağrısını görür" diyor. Liste ucu bunu uyguluyordu, akış uygulamıyordu.
- Konsolda akış giriş ekranında da açılıyordu. Çıkış yapılınca sekmede önceki kullanıcının
  kimliğiyle sürüyordu.
- Sorgu önbelleği çıkışta temizlenmiyordu (`staleTime` sonsuz). Koordinatörden sonra aynı
  sekmede giren afetzede önceki oturumun bütün çağrı listesini görebilirdi.

**Yapıldı.**
- Akış kimliği httpOnly yenileme çerezinden okuyor (`kimlik.cerezden_kullanici`).
  EventSource başlık gönderemediği için bu yol seçildi; jeton URL'ye yazılmıyor (kural 5).
  Çerez okunurken yenilenmiyor. Çerez yoksa ya da oturum iptal edilmişse 401.
- Afetzedeye yalnız iki tip mesaj gidiyor (`uclar/canli.py::_afetzede_icin`):
  - kendi çağrısının durum değişikliği: yalnız `{id, durum}`, konum ve öncelik gitmez;
  - acil bildirim.

  Başkasının çağrısı, ekip konumu ve analiz olayları gitmiyor.
- Konsolda akış yalnız oturum varken açılıyor ve kullanıcı değişince yeniden kuruluyor. Giriş
  ve çıkışta sorgu önbelleği temizleniyor.

**Denetlendi.**
- **Duman testi.** Çerezsiz `/api/live` 401 dönüyor. Bu istek `testler/uc_imzalari.json`'a
  eklendi.
- **Uçtan uca.** İki test afetzedesi (A, B) ve koordinatör akışı aynı anda dinledi:
  - A yalnız kendi çağrısının "bekliyor" ve "kapandi" olaylarını ve bildirimi aldı. B'nin
    çağrısını almadı.
  - Afetzede olaylarında `lon`, `lat` ve `ekipId` yok.
  - Koordinatör iki çağrıyı da konumlarıyla aldı.

---

## J-41 🟠 Haritada ad yoktu, şehre gitme yoktu, noktalar ne olduğunu söylemiyordu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (kullanıcı) · **İlgili:** J-40, ARAYUZ §7, §11

**Sorun.** Prototipte olup konsola taşınmayanlar:
- Haritada şehir, mahalle ve sokak adı yoktu.
- Şehre gitme düğmeleri yoktu (prototipte "Antakya / Bölge" vardı).
- Haritadaki SOS noktasına tıklayınca seçme ve yakınlaşma yoktu.
- Noktaların üstüne gelince ne oldukları görünmüyordu (prototipte `getTooltip` vardı).
- Genel durum ekranında tıklanıp konuma gidilecek bir ihbar listesi yoktu.

**Yapıldı.**
- **Adlar.**
  - `araclar_altlik_uret.py` paketlere OSM yer adlarını (şehir, ilçe, köy, mahalle) ve sokak
    adı yerleşimlerini ekliyor: adlı yolun ortası, yol yönünde açı; 80 m'den kısa yola ad
    yazılmıyor, aynı ad 250 m'den sık tekrarlanmıyor.
  - Yer adı / sokak adı: Antakya 91 / 1 492, Kahramanmaraş 111 / 657, Gaziantep 141 / 1 036,
    Malatya 101 / 509, Adıyaman 52 / 1 459. Beş bölgenin yeniden üretimi ~13 dk.
  - Konsolda deck.gl `TextLayer` ile yakınlaştırmaya göre yazılıyor: z<9 bölge adı, z9 şehir
    ve ilçe, z12 köy, z13 mahalle, z15 sokak.
  - Çakışan ad yazılmıyor (`CollisionFilterExtension`, öncelik şehir > mahalle > sokak).
    Adlar zemin renginde haleyle çiziliyor; renk ve boy token dosyasından.
- **Şehir düğmeleri.** Haritanın üst ortasında: Antakya, Kahramanmaraş, Gaziantep, Malatya,
  Adıyaman, "Tüm bölge". Görünümdeki şehir seçili görünüyor.
- **Tıklama.** Haritadaki SOS, hasar noktası ya da ekibe tıklayınca oraya yakınlaşılıyor;
  SOS seçiliyor.
- **Üstüne gelince bilgi.**
  - SOS: kimlik, aciliyet, durum, mahalle, metin, zaman.
  - Hasar noktası: kaynak, skor, güven, zaman.
  - Ekip: ad, durum, görev.
  - Kapalı yol: "modelin tahmini, sahada doğrulanmadı".
  - Metin HTML'e kaçırılıyor.
- **Genel durum sağ paneli.**
  - "Son ihbarlar" listesi (SOS ve öteki kaynaklar, en yeni önce). Tıklayınca haritada
    oraya gidiyor.
  - "Seçili çağrı" künyesi ve "SOS kuyruğunda aç" düğmesi.
- **Önbellek.** Paket adresi üretim zamanını taşıyor (`?v=`). Paket günlük önbellekte
  kalsa da yeniden üretilen paket eski hâliyle gelmiyor.

**Tarayıcıda denetlendi (21 Eylül).**
- Antakya z12'de şehir, ilçe ve köy adları; Kahramanmaraş düğmesiyle z13'te mahalle adları
  (Osman Gazi, Dulkadir, Hacı Bayram…); sokak ölçeğinde yol yönünde sokak adları.
- "Tüm bölge" beş şehri panellerin arasındaki açık alana sığdırıyor. İlk hâlinde Antakya zaman
  şeridinin altında kalıyordu; kutuya sığdırma artık panel ve şerit ölçülerini token
  dosyasından alıyor.
- Ekip noktasında "AKUT 1 · Müsait · konum saati" bilgisi çıkıyor. SOS noktasında "kimlik ·
  kritik aciliyet · Bekliyor · metin · saat · Tıkla: seç ve yakınlaş" çıkıyor.
- "Son ihbarlar"da bir SOS'a tıklayınca harita oraya yakınlaşıyor, çağrı seçiliyor ve
  künyesi görünüyor.

**Denerken düzeltilenler.**
- Isı haritası sokak ölçeğinde zemini mora boyuyordu. Örtücülüğü artık yakınlaştırmaya bağlı:
  z13'e kadar 0,72, z16'da 0,30.
- Adlar veri noktalarının üstünde çiziliyordu, bir sokak adı SOS noktasını örtüyordu. Adlar
  artık noktaların altında.
- Ekip durumu ham yazılıyordu ("musait"); artık "Müsait".
- Bölge paketi adresine sürüm eklendi (üretim zamanı), yeniden üretilen paket önbellekten
  eski hâliyle gelmiyor.

**Ölçüldü.** Sayfa açıldıktan sonra harita `load` olayı 437 ms'de geliyor, Antakya paketinin
isteği 469–504 ms'de bitiyor. Bir kez görülen 8 sn'lik gecikme, yeni eklenen
`@deck.gl/extensions` için Vite'ın bağımlılıkları yeniden paketlemesinden geliyordu; geliştirme
ortamına özgü ve tek seferlik.

---

## J-40 🟠 Konsolun haritasında altlık yoktu: zemin boştu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 (kullanıcı: "hani bir harita yok, hiçbir şey belli değil") · **İlgili:** ARAYUZ §11, MIMARI §8

**Sorun.** Konsolu kurarken altlığı bağlamamıştım. `haritaStili.ts` yalnız siyah zemindi ve
"karo ucu henüz bağlı değil" notu düşülmüştü. "Yol ağı" katmanının çizim kodu yoktu,
"Hasarlı yollar" boş dizi çiziyordu, "Yapılar" bayrağı hasar noktalarını açıyordu. Prototip
Antakya'yı EMSR648 verisiyle çiziyordu; konsola taşınmamıştı.

**Yapıldı.**
- `araclar_altlik_uret.py`: yerel OSM kopyasından (Türkiye PBF, 12 Ağustos 2026) GDAL'ın OSM
  sürücüsüyle bölge başına yollar (5 sınıf), yapılar, su alanları ve nehirler. Sadeleştirme,
  1e-5 derece tamsayı-delta kodlama, gzip. Çıktı `veri/altlik/<bölge>.json.gz` (git dışı,
  yeniden üretilebilir). Bölge başına ~2 dk.
- `GET /api/altlik` (katalog) ve `GET /api/altlik/{bölge}` (hazır dosya; istek yolunda iş yok).
  Giriş gerekli.
- Konsol: harita durunca (`moveend`) görünen alanla kesişen bölgelerin paketleri bir kez
  iner. deck.gl ikili verisiyle en alta çizilir: su, yapılar, nehirler, yollar.
  - Renkler token dosyasından okunuyor (`--color-map-*`), yol genişlikleri prototipteki gibi.
  - "Yol ağı" bayrağı yolları, "Yapılar" bayrağı yapıları açıyor.
  - Hasar noktaları artık ısı bayrağıyla açılıyor; tek görünür fark metin modunda noktaların
    da görünmesi.
  - Künye notu altlığın kaynağını ve tarihini yazıyor: "© OpenStreetMap katkıcıları
    (ODbL 1.0) · yerel kopya 12 Ağustos 2026 · Antakya (Hatay)". Görünen alanda altlık yoksa
    bunu da yazıyor.
- **Ölçüldü (±8 km):**

  | Bölge | Yol | Yapı | Su alanı | Nehir | Paket (gzip) |
  |---|---|---|---|---|---|
  | Antakya | 10 216 | 59 225 | 14 | 9 | 0,96 MB |
  | Kahramanmaraş | 11 483 | 66 659 | 23 | 38 | 1,03 MB |
  | Gaziantep | 19 521 | 171 980 | 46 | 1 | 2,41 MB |
  | Malatya | 9 689 | 52 370 | 31 | 54 | 0,90 MB |
  | Adıyaman | 5 254 | 29 961 | 9 | 2 | 0,50 MB |
- Tarayıcıda denetlendi (Antakya): z12'de şehrin yol ağı ve Asi nehri, z15'te yol
  hiyerarşisi, kavşaklar, köprüler ve yapılar okunuyor. Tip ve token denetimleri temiz.
- Paketler z9'dan itibaren iner. O yakınlıkta ekran birkaç bölgeyi birden kapsayabilir.
  Bu yüzden yapı katmanı yalnız z13 ve üstünde kurulur; yoksa 300 bini aşan çokgen aynı anda
  üçgenlenirdi. Gaziantep'te (172 bin yapı) z13'e geçişin ana iş parçacığında ne kadar
  sürdüğü **ölçülmedi**.

**Sınır.** Yalnız konsolun beş bölgesi (şehir merkezi ±8 km) üretildi; dışında zemin boş ve
künye bunu söylüyor. Adlar J-41'de eklendi. Bölge sayısı büyüyünce aynı veri
vektör karoya (MVT / PMTiles) taşınmalı (MIMARI §8).

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

## J-38 🟠 Yol ağı zaman aşımına uğrayınca sonuç "0 kapalı yol, bölge erişilebilir" diyor
**Durum:** AÇIK · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-21, kural 1

**Ölçüm.** Antakya, Wayback 57965, r = 0,75 km: OSM grafı 45 sn sınırını aştı
(`lojistik=49,1 sn`), işçi "Lojistik analiz opsiyonel - OSMnx zaman asimina ugradi"
satırını yazıp `openRoads = 0`, `blockedRoads = 0` döndü; `/route` oturumu hiç açılmadı.
Konsol (`konsol/src/modlar/hasar.tsx`, Sonuç bölümü) bunu "Kapalı yol 0 segment · Açık yol
0 segment" diye gösteriyor; o koşunun öneri metni de **"Bolge genel olarak erisilebilir
durumda."** oldu (öneri, graftan değil yol rasterından hesaplanan `blockedRoadPct =
0,0019`'a bakıyor). Yani yol ağı **hiç çözümlenmemişken** sonuç "kapanma yok, bölge
erişilebilir" diye okunuyor.

**Sıklık.** 21 Eylül'deki dört uçtan uca koşunun üçünde yol ağı zaman aşımına uğradı
(49,0–49,1 sn); yalnız OAM r = 0,35 km koşusunda graf 4,9 sn'de geldi. Yani bu
koşulların çoğunda canlı analiz kapanma hiç çıkarmıyor.

**Yapılacak.** İşçi sonuca `roadNetwork: "ok" | "timeout" | "error"` yazsın; konsol
zaman aşımında sayıları göstermesin, "yol ağı alınamadı, kapanma çıkarılamadı" desin;
öneri metni bu durumda erişilebilirlik iddia etmesin. Grafı yerel PBF önbelleğinden
okuma yolu var (`load_local_graph_from_cache`) ama yalnız önceden ısıtılmış kutular için.

---

## J-37 🟡 Sert rotanın 422 mesajı ağ kopukluğunu kapanma sanıyor
**Durum:** AÇIK · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-34

**Ölçüm.** J-34 uçtan uca koşusunda 20 rastgele çiftin 4'ünde iki modda da yol yok. Tam
grafta (hiç kenar gizlenmeden) de yok; dört çiftin dördünde ters yönde rota bulunuyor.
Sebep: araç ağı yönlü (tek yön sokaklar) ve analiz kutusunun kenarında kesiliyor. Sert
mod buna "Bu iki nokta arasinda guvenli bir baglanti bulunamadi. Yol tamamen kapali
olabilir." diyor (`uclar/rota.py`) — kapanmayı suçluyor.

**Yapılacak.** 422'den önce tam grafta yol olup olmadığına bak: yoksa "ağda bu yönde yol
yok (tek yön / kutu sınırı)", varsa "kapanmalar yüzünden yol yok" de. Mesaj değişikliği
yanıt metnini değiştirdiği için duman imzası yeniden kaydedilmeli.

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

## J-35 🟠 Konsolun Wayback "deprem sonrası" varsayılanı Antakya'da deprem öncesi görüntü
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-21, D-01, kural 1

**Sorun.** Bu oturumda yazılan konsol (`konsol/src/modlar/hasar.tsx`) "Deprem sonrası"
düğmesiyle 6 Şubat'tan sonraki ilk Wayback sürümünü (57965, 2023-02-23) seçiyor,
"hasarı bu görüntüde ararız" diyor ve sonuç künyesinde "23 Şubat 2023 tarihli Esri
Wayback arşiv görüntüsü" yazıyor. Sürüm tarihi çekim tarihi gibi sunuluyor.

**Yeniden ölçüldü (21 Eylül).** J-21'deki karo (z17, x 78701, y 51378): 11475
(2023-01-11) ve 57965 (2023-02-23) isteklerinin **ikisi de 301 ile 48232 sürümüne
yönleniyor**, dönen karo aynı (sha1 `fa0263438072c2f8`, J-21'deki değer). Wayback bir
karoyu güncellemeyen sürümde onu son güncellendiği sürüme yönlendiriyor. Yani konsolun
varsayılanı Antakya merkezinde **deprem öncesi** görüntüyü çözümletiyor; bulunan her
"hasar" yanlış alarm.

**Yapılacak.** (a) Arka uç karonun gerçekte hangi sürümden geldiğini 301'i izleyerek
çözsün (ya da Esri World Imagery metadata katmanından çekim tarihini okusun) ve sonuca
yazsın; (b) konsol "arşiv sürüm tarihi ≠ çekim tarihi" desin, çözülen karo deprem
öncesiyse uyarsın ve OAM'ı önersin; (c) deprem bölgesinde varsayılan kaynak OAM Maxar
olsun (D-01, J-21 zaten bunu söylüyor).

**Ölçüm: üç şehirde Wayback'in gerçekte gösterdiği görüntü (21 Eylül).** Esri'nin
`tilemap` ucu karonun hangi sürümden geldiğini (`select`), her sürümün metadata katmanı
(katman = 23 − z) çekim tarihini (`SRC_DATE`) veriyor. z15 / z17 / z18'de sonuç aynı:

| Şehir | Şubat–Mart 2023 sürümlerinin gösterdiği çekim | Deprem sonrası ilk çekim | O çekimi getiren ilk sürüm |
|---|---|---|---|
| Antakya | 27 Eylül 2021 | 4 Nisan 2023 (57 gün sonra) | 8 Şubat 2024 |
| Kahramanmaraş | 27 Haziran 2021 (23 Şubat sürümü), 15 Temmuz 2022 (15 Mart sürümü) | 22 Şubat 2023 (16 gün sonra) | 8 Şubat 2024 |
| Adıyaman | 30 Temmuz 2021 | 21 Nisan 2024 (440 gün sonra) | 24 Nisan 2025 |

Deprem sonrası ilk bir yılın hiçbir Wayback sürümü bu üç merkezde depremi göstermiyor.
Ayrıca 23 Şubat 2023 sürümünde Antakya'nın z18 karosu hiç yok (404); indirici bu durumda
sessizce z17'ye iniyordu.

**Yapıldı (21 Eylül).**
- `apps/road_damage/utils/wayback.py`: konumun görüntü geçmişi (sürüm → gerçek sürüm →
  çekim tarihi, uydu, çözünürlük); yeni uç `GET /api/road_damage/wayback_goruntuler`
  (saha ve üstü; soğuk 1,4–5,7 sn, önbellekten 26 ms).
- İşçi sonuca `imageryZoom`, `imageryRequestedZoom`, `imageryCaptures` ve
  `imageryEventTiming` ("pre" / "post" / "mixed" / "unknown") yazıyor. Yakınlaştırmanın
  düşürülmesi de artık günlükte ve sonuçta görünüyor.
- Konsol:
  - Varsayılan kaynak OAM. Öneri, analiz alanını en çok kapsayan en erken Maxar çekimi;
    Antakya'da 8 Şubat 2023, z16'da gözle bakıldı: bulutsuz, deprem sonrası.
  - OAM görüntüsü seçmek analiz alanını değiştirmiyor. Eskiden alan görüntünün tüm
    kutusuna (40 × 30 km'lik şeritler) oturuyordu; bkz. J-39.
  - OAM'da görüntü seçilmeden analiz başlamıyor. Sunucu seçimsiz istekte görüntüyü kendi
    seçiyor ya da Google'a düşüyordu.
  - Wayback düğmeleri çekim tarihine göre çalışıyor ("Deprem sonrası ilk çekim"). Listede
    her sürümün çekim tarihi yazıyor. Açıklama deprem öncesi ve sonrası durumu ve depremden
    kaç gün geçtiğini söylüyor; bu konumda deprem sonrası görüntü yoksa uyarı çıkıyor.
  - Sonuçta çekim tarihleri ve çözünürlük görünüyor. Görüntü deprem öncesiyse uyarı
    sayılardan önce çıkıyor ve "bölge erişilebilir" önerisi gizleniyor.
- **Uçtan uca:** Wayback 57965 ile Antakya, r = 0,35 km. Sonuç z18 istendiğini, karo
  olmadığı için z17 kullanıldığını ve çekimin 27 Eylül 2021 (`pre`) olduğunu yazıyor. Model
  bu deprem öncesi görüntüde piksellerin %0,16'sını hasar işaretledi; hepsi yanlış alarm.
- Tip denetimi ve token denetimi temiz. Duman testi 57 istekte 0 fark.

**Tarayıcıda denetlendi (21 Eylül).** Varsayılan kaynak OAM; öneri "Maxar, 8 Şubat 2023 (depremden 2 gün
sonra), alanın ~%100'ü", listede her görüntünün kapsama oranı. Wayback'e geçince varsayılan "8 Şubat 2024
sürümü · çekim 4 Nisan 2023" ve "depremden 57 gün sonra"; "Deprem öncesi" düğmesi "15 Mart 2023 sürümü ·
çekim 27 Eylül 2021" ve kalın uyarı: "görüntüde depremin hasarı yok, bulunan her hasar yanlış alarmdır".

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

## J-33 🟡 Sağlık kontrolü model yüklüyordu ve kamera durumunu uyduruyordu
**Durum:** KAPALI (21 Eylül 2026) · **Bulundu:** 21 Eylül 2026

**Sorun.** `GET /api/status` içinde `"nlp": _get_nlp_pipeline() is not None`
satırı tembel yükleyiciyi çağırıyordu: sunucu açıldıktan sonraki ilk sağlık
kontrolü BERTurk'ü (sınıflandırma + NER) belleğe alıyordu (log: "NLP Pipeline
loaded lazily" sağlık kontrolüyle tetiklendi). `"camera": True` ise hiçbir
kontrol yapmadan sabit dönüyordu — model dosyası olmasa da "var" diyordu
(CLAUDE.md kural 1).

**Düzeltme.** Alanlar yükleme tetiklemeden hesaplanıyor: model bellekteyse ya da
dosyası diskteyse kullanılabilir. Bellekteki modeller ayrı `yuklu` alanında.
Ölçüm: ilk sağlık kontrolü 13 ms, NLP yükleme sayısı 0.

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

## J-30 🟠 Model kapanma koşuları algılama hatasını ölçmüyor — klasik ajan modelin kapanmalarını "gerçek" sayıyor
**Durum:** KAPALI (16 Eylül 2026) — deney kuruldu ve koşuldu; sonuç aşağıda ("Çözüm"). Tablo 18 verisi hazır, makaleye işlenmeli · **Bulundu:** 16 Eylül 2026 · **İlgili:** M-20, M-23, J-25, J-26, J-29

`/api/road_damage/naive_compare`, gerçek kapalı kenar kümesi olarak oturumun **kendi**
kapanmalarını kullanıyor (`simulate_naive_agent(G, real_closed_edges, …)`). Model
koşularında bu küme SegFormer'ın çıktısı; yani hem QuakeMind hem klasik ekip "model
haklı" varsayımıyla değerlendiriliyor. **Yanlış alarm** (açık yolu kapalı sanıp gereksiz
dolanma) ve **kaçırma** (kapalı yolu açık sanıp QuakeMind ekibinin de U-dönüşü yapması)
hiç ölçülmüyor. J-25 ve J-29'daki model satırları bu yüzden "modelin kapanmaları doğru
olsaydı bilgi ne kazandırırdı" sorusunu yanıtlar; M-20'nin sorusunu (bölütleme kalitesinin
operasyonel etkisi) yanıtlamaz. Aynı durum sentetik koşular için de geçerli ama orada
kasıtlı (kusursuz bilgi referansı R3, makale Bölüm 3.8).

**Önerilen tasarım.** Planlayıcı modelin kapanmalarını bilir, dünya EMSR648 kapanmalarıdır.
`simulate_naive_agent`'a bir başlangıç bilgisi (`prior_closed`) eklenirse tek fonksiyonla
üç ajan kurulur: R0 (başlangıç bilgisi boş), model-bilgili (model kapanmaları), R3/kâhin
(EMSR kapanmaları). Üçü de EMSR kümesinde yürür; model-bilgili ajanın U-dönüşleri
kaçırmaları, R3'e göre fazladan yolu yanlış alarmları ölçer.

**Kısıtlar.** Drone sahnelerinde EMSR yol hasarı yalnız K-D1'de var (H-D1 ve H-D2'de %0)
→ anlamlı test şimdilik tek sahne. v2 ilçeleri için model maskesi üretilmedi (Colab
defterinde isteğe bağlı z=18 adımı var; J-20). EMSR648 de geçilebilirlik değil hasar
derecesi veriyor (J-28, M-26) — "dünya" olarak kullanılması da bir varsayım.

**Çözüm (16 Eylül 2026).** `benchmark/model_in_real_world.py` (backend gerektirmez).
Dünya = EMSR648 gevşek kural, tampon 8 m. Aynı dünyada üç ekip türü yürür (hepsi kapalı
kenara girmez, kavşakta öğrenir, keşif başına t_u = 20 dk):
**R3** yola EMSR kapanmalarını bilerek çıkar; **model-bilgili QuakeMind** yola SegFormer'ın
kapanmalarını bilerek çıkar (yanlış alarmları sorgulamaz, kaçırdığı gerçek kapanmaya varınca
keşfeder); **R0** hiçbir bilgiyle çıkmaz. Yanlış alarmlar hedefi bağlantısız bırakırsa
("rota bulunamadı") ekip modeli bırakıp R0 gibi devam eder — sayısı ayrıca raporlanır.
Model kapanmaları canlı sistemle aynı kuralla (`closures_from_damage_mask`) hazır
maskelerden, 3 zoom (18/19/20) × 5 r_h (0/5/10/15/25 m) = 15 ayarla üretildi; ayrıca
yumuşak kullanım (kenar silinmez, uzunluğu ×3 / ×10) = 30 ayar daha. Görevler:
`runs/multi_seed/drone-emsr-loose-s42…51` atamaları (3 sahne × 3 görev × 10 tohum = 90).
Kod: `simulate_reference_fleet(..., prior_closed, prior_fallback, prior_penalty_factor)`.
Çıktı: `runs/model_gercek_dunya/tablo18.md`, `summary.json`.

**Doğrulama.** R0 = önceki koşuların naive_compare sonucu **90/90** görev birebir; R3
mesafesi = QuakeMind'ın A* rotası (en büyük fark **0,00 m**); EMSR ve model kapanma
sayıları önceki koşularla aynı (0 uyuşmazlık); yeni yol bulucu ↔ görünümlü yol bulucu
tüm varyantlarda birebir.

**Tablo 18 (sert kullanım = bugünkü sistem; kesim düzeyi, 3 sahne toplamı; süre görev başına, 10 tohum):**

| Kaynak | IoU | Duyarlılık | Kesinlik | Kaçırılan | Yanlış | Ort. ulaşım süresi (dk) | Model rota bulamadı (9 görevde) | Keşif / tohum | R0→R3 kazancının yakalanan payı |
|---|---|---|---|---|---|---|---|---|---|
| R3 — kusursuz bilgi | — | — | — | 0 | 0 | **2,05 ± 0,15** | 0 | 0 | %100 |
| SegFormer z18, r_h 0 (uygulama) | 0,019 | 0,021 | 0,167 | 47 | 5 | 6,52 ± 1,92 | 0 | 2,0 | %0 |
| SegFormer z18, r_h 15 | 0,029 | 0,062 | 0,051 | 45 | 56 | 6,97 ± 2,15 | 6,1 | 2,2 | **%−11** |
| SegFormer z19, r_h 10 | 0,114 | 0,333 | 0,148 | 32 | 92 | 6,52 ± 1,92 | 8,7 | 2,0 | %0 |
| SegFormer z20, r_h 0 | 0,079 | 0,125 | 0,176 | 42 | 28 | 6,57 ± 1,92 | 0 | 2,0 | %−1 |
| SegFormer z20, r_h 25 | 0,100 | **0,917** | 0,101 | 4 | 390 | 6,52 ± 1,92 | **9,0** | 2,0 | %0 |
| R0 — naif ajan | — | 0 | — | 48 (tümü) | 0 | **6,52 ± 1,92** | 0 | 2,0 | %0 |

(15 ayarın tamamı `tablo18.md`'de.) Gerçek hasarlı tek sahne K-D1'de (197 kesimin 48'i
kapalı) görev başına R3 **2,46** dk, R0 **15,88** dk — kazanılabilecek süre büyük; H-D1 ve
H-D2'de EMSR hiç yol hasarı işaretlememiş (R0 = R3 = 1,84 dk), orada modelin her
kapanması yanlış alarm.

**Sonuç.**
1. **Bugünkü SegFormer kapanmalarıyla planlama, klasik ekipten hiçbir ayarda iyi değil**
   (15 sert ayarda yakalanan pay %0 ile %−11 arası). İki başarısızlık biçimi var:
   küçük r_h'de model gerçek kapanmaların çoğunu **kaçırıyor** (duyarlılık ≤ 0,13 → aynı
   keşifler); r_h büyüdükçe duyarlılık 0,92'ye çıkıyor ama kesinlik ~0,10'da kalıyor ve
   **yanlış alarmlar hedefleri ağdan koparıyor** (9 görevin 9'unda "rota bulunamadı" → ekip
   modeli bırakıyor → R0).
2. **Yumuşak kullanım da tutarlı kazanç vermiyor:** 30 ayarın 2'si (z19/15 m ×3, z20/25 m ×3)
   %18 ± 23 yakalıyor; diğer 28 ayar %+2 ile %−26 arasında, bu iki ayarın komşuları bile
   %−12 ile %+2 arasında. En iyi ayarı seçip raporlamak çoklu karşılaştırma hatası olur.
3. **Makalenin hipotezi (Bölüm 4.7, "duyarlılık kesinlikten belirleyici") bu düzende
   desteklenmiyor:** duyarlılığı 0,92'ye çıkarmak kazanç getirmedi, çünkü kesinlik düşük
   kaldıkça yanlış alarmlar ağı kilitledi. Makalenin öngördüğü alternatif —
   kapanmaların **ağ topolojisindeki konumu** sayılarından belirleyici — veriyle uyumlu.
4. Bu sonuç J-25/J-26 ile tutarlı ve Tablo 18'in SegFormer satırı için **olumsuz sonuç**
   olarak raporlanmalı; algılama katmanı (alan kayması, KATE-CD eğitimi) iyileşmeden model
   tabanlı kazanç iddia edilemez.

**Kısıtlar (makaleye yazılmalı).** Yalnız SegFormer (diğer beş model eğitilmedi); 3 küçük
drone sahnesi (~200 kesim), gerçek hasar yalnız K-D1'de (sürenin farkını K-D1'in 3 görevi
belirliyor); IoU/duyarlılık/kesinlik **kesim düzeyinde**, piksel IoU_hasar değil; dünya
EMSR648 gevşek kural (hasar derecesi = geçilemezlik varsayımı); "rota bulunamadı"
durumunda R0'a dönme bir tasarım seçimi (alternatifi görevi ulaşılamaz saymak).

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

## J-27 ⚪ (bilgi) Drone sahnelerinin gerçek en yüksek zoom'u z=22
**Durum:** KAPALI — bilgi kaydı · **Bulundu:** 16 Eylül 2026

OpenAerialMap karo sunucusu üç sahnede z=24'e kadar dolu karo döndürüyor, ama
sahnelerin doğal çözünürlüğü 3,4–3,9 cm/px; bu **z=22'ye (3,0 cm/px)** karşılık
geliyor. z=23–24 yeni bilgi katmadan yalnız büyütüyor. CPU maliyeti (yama başına
~1,3–1,8 sn ölçüldü): üç sahne toplamı z=20 ~20 dk, z=21 ~70–95 dk, z=22 ~5–6 saat;
z=22'de tek sahne ~370 MP ve ~9 GB RAM ister — bu yüzden Colab'a bırakıldı.

---

## J-19 🔴 Kapanma kuralı yolun MERKEZ ÇİZGİSİ pikselini istiyor — model kaynaklı kapanma üretilemiyor
**Durum:** KAPALI (16 Eylül 2026) — kalibrasyon J-22'de açık

**Sorun.** Model tabanlı kapanma yolu şöyle çalışıyor:
`inference.py:171` → `intersection = cv2.bitwise_and(pred_mask_binary, road_mask_binary)`,
ardından `network.py:analyze_road_network_graph` her kenar boyunca nokta örnekleyip
`blockage_mask[py, px] > 0` diye bakıyor. Yani bir yolun kapalı sayılması için
modelin hasarı **yolun çizilmiş merkez çizgisinin üstünde** tespit etmesi gerekiyor.

Gerçekte baskın kapanma mekanizması bu değil: **yanındaki bina çöküp molozu
sokağa döküyor.** Yolun kendi yüzeyinde hasar nadir. OSM merkez çizgisi 1-2
piksel genişliğinde olduğu için kesişim pratikte hep boş çıkıyor.

**Ölçüm (Antakya, Maxar Open Data 2023-02-11, gerçek deprem sonrası görüntü):**

| | z=16 · 1,93 m/px | z=18 · 0,48 m/px |
|---|---|---|
| Görüntü | 1 280 px | 2 048 px |
| `damageRate` | 0,0005 | **0,0126** (25 kat) |
| **`blockedRoads`** | **0** | **0** |
| Çıkarım süresi | 94,9 sn | **306,8 sn** |

Yani çözünürlük düzeltilse bile (model 25 kat daha fazla hasar buluyor)
**kapanma sayısı sıfır kalıyor**. `simulate_random_closures`'ın (E-01/J-12)
var olma sebebi büyük olasılıkla budur: bu duvara çarpılıp rastgele kapanmaya
dönülmüş.

**Yapılacak.** Kapanma ölçütünü "yol pikselinde hasar" yerine **"yola r metre
içinde hasar"** yap. Mekanizma zaten var ve çalışıyor:
`apply_risk_penalties`'in `blockage_hard_radius_m = 25` sert-kapatma yarıçapı
(J-08'de vektörize edildi, 40× hızlandı). Eksik olan, bu kuralı `/analyze`
boru hattına da bağlamak. Makaledeki `r_h` = 25 m parametresi zaten bunu
tarif ediyor.

**Kapandı.** Kapanma kuralına yarıçap eklendi:

- `network.py`: yeni `dilate_mask_by_metres()` — hasar maskesini metre
  cinsinden bir daireyle genişletir; metre→piksel dönüşümü görüntünün kendi
  sınırlarından hesaplanır, zoom'dan bağımsızdır (birim kontrolü: 0,48 m/px'te
  5 m → 10 px, 25 m → 52 px).
- `analyze_road_network_graph(..., blockage_radius_m=0.0)` — varsayılan 0,
  yani `main.py` / `apps/road_damage/app.py` (Streamlit) **değişmedi**.
- `worker.py`: yarıçap > 0 iken grafa `intersection` (yalnız yol üstündeki
  hasar) yerine **tüm** hasar maskesi (`pred_mask_binary`) gidiyor.
- `RoadDamageRequest.blockageRadiusM` (varsayılan 25,0 = makaledeki r_h) —
  istek başına ayarlanabilir; M-26 duyarlılık taraması bununla yapılabilir.
- Sonuca `blockageRadiusM` ve `closureRule` (`"radius"` / `"on_road_pixel"`)
  yazılıyor: aynı görüntü farklı r_h ile çok farklı sayıda kapanma verdiği için
  sonuç bu bilgi olmadan yorumlanamaz.

**Doğrulama.**

1. *Teşhis:* z=18 çıktısında model **52 641 piksel** (%1,26) hasar buldu;
   bunların **yol rasterının üstüne düşeni: 0**. Eski kuralın hep sıfır
   vermesinin sebebi tam olarak bu.
2. *Yeni kural, gerçek model çıktısı üzerinde:* aynı maskeyle r_h = 5 / 10 /
   15 / 25 / 50 m → 30 / 46 / 76 / 100 / 188 kapalı kenar (389 kenardan).
   Kapanmalar artık **modelden** geliyor. Tablo J-22'de.
3. *Canlı `/analyze` boru hattı:* r_h=0 ve r_h=25 iki ayrı istek; çıktıda
   `closureRule` sırasıyla `"on_road_pixel"` ve `"radius"`, `blockageRadiusM`
   0,0 ve 25,0 — parametre istekten işçiye, oradan sonuca doğru akıyor.
4. *Canlı = çevrimdışı:* canlı z=16 sonucunun hasar maskesi çevrimdışı aynı
   fonksiyona verildi — **birebir aynı sonuç** (3 924 kenar, 0 kapalı).
   Bağlantıda hata yok.

**Dürüst kayıt.** z=16'da (1,93 m/px) yeni kural bile **0** kapanma verdi:
model o çözünürlükte yalnız 779 piksel hasar görüyor ve bunlar sürülebilir yol
kenarlarının 25 m'sine düşmüyor. Yani J-19 tek başına yetmiyor — **J-20
(çözünürlük) çözülmeden senaryo ölçeğinde model tabanlı kapanma çıkmaz.**
Ayrıca r_h = 25 m gerçeğin ~8 katı kapanma üretiyor — **J-22**.

**Not.** Projede `pytest` kurulu değil; `tests/test_road_damage_api.py`
koşturulamadı. Etkilenen yollar eski/yeni karşılaştırmalı testlerle doğrudan
doğrulandı (J-05, J-08).

**16 Eylül 2026 — varsayılan GERİ ALINDI.** `blockageRadiusM` varsayılanı 25'ten
**0'a** (uygulamanın her zamanki kuralı) çekildi. Sebep: web uygulaması bu alanı
göndermiyor; varsayılanı 25 yapmak, uygulamanın yol hasarı sonuçlarını
kullanıcıya sorulmadan değiştirmişti. r_h=0 yolu (maske = hasar ∩ yol maskesi,
aynı örnekleme) değişiklik öncesiyle birebir aynı çalışıyor; yarıçap kuralı
yalnızca açıkça istenirse kullanılıyor. `/closures_from_mask` (araştırma ucu)
ve `full_scenario.py --blockage-radius-m` kendi parametrelerini açıkça taşıyor.

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

## J-01 🔴 `/api/road_damage/recent` her 20 saniyede tüm segment dizilerini yeniden gönderiyor
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `fastapi_app.py:1538` her çağrıda son 60 dakikadaki **tüm** analizlerin
`safeRoadSegments` + `blockedRoadSegments` dizilerini eksiksiz döndürüyor.
Frontend (`quakemind-web/src/app/command/map/page.tsx:48`, `ROAD_DAMAGE_POLL_MS = 20000`)
bunu 20 saniyede bir çekiyor ve **yalnızca kümenin değişip değişmediğine** bakıyor
(`if (changed)`), yani gelen verinin neredeyse tamamı atılıyor.

**Ölçüm.** Tek bölge = 39 285 kenar → 78 570 koordinat noktası → **2,10 MB JSON**
(`json.dumps` 0,066 s, `serialize_segments` 0,550 s). Dokuz bölgeli senaryoda
oturumda 9 analiz birikiyor → **her 20 saniyede ~19 MB** üretiliyor, serileştiriliyor,
ağdan geçiriliyor ve tarayıcıda ayrıştırılıyor. Serileştirme tek başına ~5 s CPU
demek ve bu süre boyunca GIL tutulduğu için **diğer tüm uç noktalar bekliyor** (bkz. J-07).

**Yapılacak.** `/recent` yalnız hafif özet döndürsün (`analysisId`, `createdAt`,
`bounds`, `segmentCount`); segmentler ayrı bir `/api/road_damage/segments/{analysisId}`
ucundan **analiz başına bir kez** çekilsin. Ek olarak `ETag`/`If-None-Match` ile
304 dönülebilir.

**Kapandi.** `/recent` artik yalnizca ozet doner
(`analysisId`, `createdAt`, `bounds`, `safeSegmentCount`, `blockedSegmentCount`);
agir diziler yeni `GET /api/road_damage/segments/{analysisId}` ucundan gelir ve
`ETag` + `Cache-Control: private, max-age=3600` tasir. Istemci tarafinda
`getRoadDamageSegments` (api.ts) ucus-halindeki istegi de paylasan kalici bir
onbellek tutar, yani bir analiz sekme omru boyunca bir kez cekilir.
Ayni degisiklige gore guncellenen uc tuketici: `command/map/page.tsx`,
`command/page.tsx`, `SafeEvacuationMap.tsx`. Python tarafinda `/recent`'i
kullanan tek script `benchmark/prepare_demo.py` yalnizca `len(analyses)`
okudugu icin etkilenmedi.

**Olculen sonuc (canli backend, Antakya r=3km):**

| | Once | Sonra |
|---|---|---|
| `/recent` yanit boyutu | 1 272 288 bayt (tek bolge) | **264 bayt** |
| `/recent` sure | ~0,4 sn | **0,0023 sn** |
| 20 sn'de bir, 9 bolge | ~19 MB | **~2,4 KB** |

Agir veri kaybolmadi, yalnizca yerini degistirdi: `/segments` 0,40 sn'de
1 272 288 bayt donuyor ve analiz basina **bir kez** cagriliyor.

---

## J-02 🔴 `simulate_naive_agent` döngünün içinde `G.copy()` yapıyor
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `apps/road_damage/utils/network.py`, `simulate_naive_agent` içindeki
keşif döngüsü her yinelemede `G_view = G.copy()` çağırıyor (en çok
`MAX_NAIVE_ITERATIONS = 60` kez, atama başına). `simulate_random_closures` içinde
**aynı hata zaten `nx.restricted_view` ile düzeltilmiş** ve koda "kopya almaya geri
dönülmemeli" uyarısı yazılmış — ama bu fonksiyon atlanmış.

**Ölçüm.** `G.copy()` = **0,91 s** (39 285 kenarlık MultiDiGraph); `nx.restricted_view`
= **0,0001 s**, yani ~9 000 kat. Mevcut koşumda 18 atama + 68 keşif ≈ 86 yineleme →
**~78 saniye saf kopyalama**. Hatay grafında (40 950 kenar) daha da fazla. Bellek
riski de aynı: Antakya grafında MemoryError'a düşüren desenin ta kendisi.

**Yapılacak.** `G_view = nx.restricted_view(G, [], known_closed)`. Davranış birebir
aynı (görünüm salt-okunur, döngü zaten yazmıyor).

**Kapandi.** `G.copy()` yerine `nx.restricted_view(G, [], known_closed)`.

**Esdegerlik dogrulandi:** eski davranis (G.copy) bagimsiz bir referans
uygulama olarak yeniden yazilip yenisiyle 6 farkli rota uzerinde
karsilastirildi -- `routeCoords` dahil **6/6 birebir ayni sonuc**
(basarili ve "yol bulunamadi" durumlarinin ikisi de kapsandi).

**Olculen sonuc** (18 004 dugum / 39 285 kenar, %2 kapanma, 6 rota):
toplam **19,59 sn -> 1,10 sn (18x)**. %10 kapanmada (daha cok kesif dongusu)
**56,07 sn -> 9,80 sn (6x)**. Canli backend'de `/naive_compare` 29 kesifli bir
rotayi 1,78 sn'de tamamliyor.

---

## J-03 🔴 NLP gecikmesinin %89'u Nominatim geocoding'i; önbellek yok
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `apps/disaster_nlp/src/ner_extraction.py:68` geocoding'i
`RateLimiter(min_delay_seconds=1.2)` ardına koyuyor ve `get_coordinates`
**aday × sorgu** iç içe döngüsüyle canlı `nominatim.openstreetmap.org`'a gidiyor.
Hiçbir önbellek yok — aynı metin ikinci kez gelse aynı bedel yeniden ödeniyor.

**Ölçüm** (metin: *"Hatay Antakya Cebrail mahallesi bina yıkıldı enkaz altında 3 kişi var acil yardım"*):

| Aşama | Süre |
|---|---|
| Zeyrek lemmatizasyon (sonucu kullanılmıyor, bkz. J-04) | 0,28 s |
| BERTurk sınıflandırma | 0,75 s |
| BERTurk NER | 0,81 s |
| **Nominatim geocoding** | **6,45 s** |
| **Uçtan uca `process_tweet`** | **7,28 s** |

`_build_queries` bu tek metinden **23 sorgu adayı** üretiyor. Yukarıdaki 6,45 s
*şanslı* durum (ikinci sorgu tutmuş); hiçbir sorgu tutmazsa 23 × 1,2 s ≈ **28 s**.
Ayrıca offline-first hedefiyle doğrudan çelişiyor: internet yoksa NLP konum
çıkaramıyor.

**Yapılacak.** (a) Sorgu → sonuç disk önbelleği. (b) Türkiye il/ilçe/mahalle
tablosundan **yerel** çözüm birinci sıraya, Nominatim yalnız son çare
(`tr_locations.py` zaten var). (c) Sorgu adayı sayısını 23'ten ~4'e indir.

**Kapandi.** Iki degisiklik:
1. **Kalici geocoding onbellegi** (`apps/disaster_nlp/data/geocode_cache.json`,
   .gitignore'a eklendi). Sorgu metnine gore anahtarlanir ve **basarisiz**
   sonuclari da saklar -- asil maliyet zaten tutmayan sorgulari taramaktir.
2. **Adaylar arasi dedupe:** `get_coordinates` ayni sorgu metnini farkli
   adaylar icin tekrar aga gondermiyor. Sonucu degistirmez: tutan bir sorgu
   zaten aninda donerdi, dolayisiyla atlanan her sorgu daha once basarisiz
   olmus bir sorgudur.

**Olculen sonuc.** Ayni metnin tekrari: **7,28 sn -> 0,55 sn**; canli
backend'de `/api/nlp/analyze` ikinci cagri **0,32 sn**. Cikti birebir ayni
(dogrulandi: `results[0] == results[2]`).

**Acik kalan kisim -> J-13.** Ilk (onbelleksiz) sorgu hala aga bagli; yerel
il/ilce/mahalle tablosundan cozum offline-first hedefi icin ayrica gerekli.

---

## J-04 🟠 `zemberek_lemmatize` çağrılıyor ama sonucu hiç kullanılmıyor
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `apps/disaster_nlp/src/pipeline.py:24` içinde
`lemmatized_text = zemberek_lemmatize(clean_tx_lower)` atanıyor; değişken
dosyanın hiçbir yerinde okunmuyor. Sınıflandırma `clean_tx_cased` ile,
NER de `clean_tx_cased` ile çalışıyor.

**Ölçüm.** İstek başına **0,28 s** tamamen boşa. Ayrıca Zeyrek her çağrıda
stdout'a onlarca `APPENDING RESULT: ...` satırı basıyor — log kirliliği ve
gereksiz I/O.

**Yapılacak.** Ya satırı kaldır, ya da lemmatize edilmiş metni gerçekten
sınıflandırıcıya ver. İkincisi **davranış değişikliğidir** ve makalede raporlanan
sınıflandırma skorlarını etkiler; bu yüzden güvenli olan satırı kaldırmaktır.

**Kapandi.** Olu cagri kaldirildi; ayrica `preprocessing.py`'de
`zeyrek.MorphAnalyzer()` modul yuklenirken degil **ilk gercek lemmatizasyon
cagrisinda** kuruluyor (lemmatizasyon su an hicbir yerde kullanilmadigi icin
pratikte hic kurulmuyor).

**Olculen yan kazanc:** `disaster_nlp` import suresi **60,8 sn -> 20,6 sn**.
Zeyrek'in her cagrida stdout'a bastigi `APPENDING RESULT` kirliligi de
ortadan kalkti.

---

## J-05 🟠 `calculate_route` her rotayı iki kez hesaplıyor, birini atıyor
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `network.py:calculate_route` hem `nx.shortest_path` (Dijkstra) hem
`nx.astar_path` çalıştırıyor. `/api/road_damage/route` yalnızca Dijkstra sonucunu
kullanıyor, A* sonucunu `_astar_coords` adıyla atıyor.

**Ölçüm.** Dijkstra 0,039 s · A* 0,013 s — yani **A\* üç kat hızlı** ve aynı yolu
buluyor (ikisi de 99 düğüm). Şu an rota başına 0,052 s ödeniyor, 0,013 s yeterdi.

**Yapılacak.** Tek algoritma. `/safe_route` ikisini bilinçli olarak karşılaştırdığı
için oradaki davranış korunmalı; `/route` için yalnız A* yeterli.

**Kapandi.** `calculate_route` artik `algorithms` parametresi
aliyor; `/route` yalnizca `('astar',)` gecer. `/safe_route` ikisini bilerek
karsilastirdigi icin varsayilan degismedi.

**Esdegerlik dogrulandi:** ayni rota icin Dijkstra ve A* maliyet farki
**0,000000 m** -- A*'in haversine sezgisi kabul edilebilir oldugu icin
optimalligi garantili, dolayisiyla `/route`'un dondurdugu mesafe degismez.

---

## J-06 🟠 `ox.distance.nearest_nodes` her çağrıda KD-ağacını sıfırdan kuruyor
**Durum:** KAPALI (15 Eylül 2026) · **Bulundu:** 15 Eylül 2026

**Sorun.** `calculate_route` ve `simulate_naive_agent`, başlangıç/bitiş düğümünü
bulmak için her seferinde `ox.distance.nearest_nodes(G, ...)` çağırıyor; osmnx bu
çağrıda grafın tüm düğümlerinden yeni bir dizi + KD-ağacı üretiyor.

**Ölçüm.** İlk çağrı 0,265 s, sonraki 0,088 s. Senaryo başına ~70 çağrı ≈ **6 s**.

**Yapılacak.** Graf başına bir kez `scipy.spatial.cKDTree` kur ve session'da sakla
(`road_damage_sessions[analysisId]["kdtree"]`).

**Kapandi.** `network.py`'ye onbellekli `nearest_node(G, lat, lon)`
eklendi; BallTree zayif referansli bir sozlukte (graf cop toplandiginda
kendiliginden dusen) graf basina **bir kez** kurulur. Metrik osmnx'in
projeksiyonsuz-graf yolunun birebir aynisi (radyan haversine BallTree).

**Esdegerlik dogrulandi:** 20 rastgele nokta, **20/20 ayni dugum**.
**Olculen sonuc:** 20 sorgu **1,918 sn -> 0,0035 sn (541x)**.

---

## J-07 🟠 Tüm uç noktalar senkron `def` — ağır iş GIL'i tutup her şeyi bekletiyor
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

**Sorun.** `fastapi_app.py`'deki uç noktaların tamamı `def` (`async def` değil).
FastAPI bunları anyio iş parçacığı havuzunda koşturur; ancak NetworkX, JSON
serileştirme ve haversine döngüleri saf Python olduğu için **GIL'i bırakmaz**.
Sonuç: tek bir `/recent` (J-01) veya `/naive_compare` (J-02) çağrısı sürerken
`/api/sos/alerts`, `/api/team/claims`, `/api/chat/messages` gibi hafif pollingler
de kuyrukta bekliyor. Kullanıcının gördüğü "veriler geç geliyor" tablosunun
doğrudan sebebi budur.

**Yapılacak.** CPU-bağımlı uçları (rota, naif karşılaştırma, segment serileştirme)
`road_damage_pool` benzeri bir **ProcessPoolExecutor**'a taşı; hafif okuma uçlarını
`async def` yap. J-01 ve J-02 çözülünce bu maddenin aciliyeti düşer ama ortadan
kalkmaz.

---

## J-08 🟠 `apply_risk_penalties` O(kenar × hasar noktası) saf Python
**Durum:** KAPALI (15 Eylül 2026)

**Sorun.** `network.py:apply_risk_penalties` her kenar için **her** hasar noktasına
ve **her** kapanma noktasına tek tek `haversine` hesaplıyor.

**Ölçüm/projeksiyon.** Şu an hasar noktası sayısı düşük olduğu için gizli kalıyor.
EMSR648 bağlandığında (E-01) hasar noktası = 394 + 927 = 1 321 olacak →
39 285 × 1 321 ≈ **52 milyon** Python-seviyesi haversine → dakikalar mertebesi.
Yani bu madde **E-01 kapanır kapanmaz patlayacak** bir zaman bombası.

**Yapılacak.** Hasar noktalarından bir `cKDTree` kur, kenar orta noktaları için
toplu (vektörize) en-yakın-komşu sorgusu yap.

**Kapandı.** Mesafe araması vektörize edildi: kenar orta noktaları bir kez
hesaplanıp `numpy` dizisine alınıyor, hasar noktalarından ve kapanma
noktalarından birer `sklearn.neighbors.BallTree` (radyan haversine) kuruluyor
ve tüm kenarlar **tek toplu sorguda** işleniyor. Metrik `haversine()` ile aynı
küre yarıçapını (6 371 000 m) kullanır.

**Ölçüm — bu maddenin varlık sebebi olan gerçek yük ile.** Hasar noktaları
uydurma değil: EMSR648'in Hatay + Kahramanmaraş katmanının tamamı
(**1 321 hasarlı bina, 207 hasarlı yol segmenti**), en büyük bölge grafında
(20 643 düğüm / 49 666 kenar):

| | Süre |
|---|---|
| Eski (saf Python, O(kenar × nokta)) | **139,49 sn** |
| Yeni (BallTree, toplu sorgu) | **3,49 sn** |
| | **40× hızlı** |

Kaçınılan haversine çağrısı: **75 889 648**.

**Eşdeğerlik — bit düzeyinde aynı.** Eski davranış bağımsız bir referans
uygulama olarak yeniden yazılıp aynı graf ve aynı EMSR648 verisiyle
karşılaştırıldı:

- Sert kapatılan kenar kümesi **birebir aynı** (49 666 → 49 036, 630 kenar).
- `risk_cost` değeri farklı olan kenar sayısı: **0** (en büyük fark 0,00e+00).
  `risk_weight` basamaklı bir fonksiyon olduğu için asıl kritik nokta basamak
  seçimiydi; 49 036 kenarın tamamında aynı basamak seçildi.
- `risk_cost` tipi saf Python `float` — numpy skaleri JSON'a serileştirilemez
  ve bu değer `/safe_route`'un döndürdüğü `riskScore`'a kadar taşınıyor.
  Dönüşüm olmasaydı uç nokta 500 verirdi.

**Sınır durumları ayrıca sınandı:** hasar yok + kapanma yok (PostGIS kapalıyken
`/safe_route`'un fiili durumu) → ceza uygulanmıyor, `risk_cost == length`;
yalnız hasar; yalnız kapanma. Üçünde de atanmayan veya yanlış tipte değer yok.

**J-12/E-01 önündeki engel kalktı.** EMSR648 kapanma katmanı bağlandığında bu
fonksiyon artık dakikalar değil saniyeler sürüyor.

---

## J-09 🟡 `_nearest_graph_node` O(n) lineer tarama
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

`apps/road_damage/utils/local_osm.py:_nearest_graph_node` tüm düğümleri Python
döngüsüyle tarıyor; `shortest_route_from_local_roads` bunu çağrı başına iki kez
çağırıyor. J-06 ile aynı çözüm (KD-ağacı).

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

## J-11 🟡 Harita sayfasında beş ayrı polling döngüsü
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

`command/map/page.tsx` aynı anda beş `setInterval` çalıştırıyor (TEAM 2,5 s ·
SOS 6 s · NLP 6 s · DEBRIS 6 s · ROAD_DAMAGE 20 s), ayrıca Sidebar 8 s, chat 4 s,
bildirim 10 s. Dakikada ~50 HTTP isteği. J-07 ile birleşince backend'i sürekli
meşgul tutuyor.

**Yapılacak.** Tek bir `/api/live/state` birleşik ucu veya SSE/WebSocket ile
sunucu-itmeli akış. Kısa vadede: pollingleri tek bir zamanlayıcıda birleştir.

---

## J-12 🔴 Senaryo verisi gerçek değil — kapanmalar `rng.sample` ile rastgele
**Durum:** KAPALI (16 Eylül 2026) — kapsam dışı 4 ilçe için kısıt sürüyor · **Bulundu:** 15 Eylül 2026 · **Kök madde:** E-01 / C-01 / M-23

Bu madde E-01'in **sistem tarafındaki** yüzüdür ve burada tekrar kaydedilmiştir
çünkü performans işiyle **aynı dosyalara** dokunuyor (`network.py`,
`full_scenario.py`), dolayısıyla birlikte planlanmalıdır.

**Eldeki gerçek veri (doğrulandı, 15 Eylül 2026):**

| | Hatay (AOI11) | Kahramanmaraş (AOI04) |
|---|---|---|
| Kaynak paketi | `EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2` | `EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1` |
| Toplam yol segmenti | 4 613 | 7 843 |
| **Hasarlı yol segmenti** | **73** (tam çizgi geometrisi + `damageGrade`) | **134** |
| Toplam bina | 3 689 | 4 619 |
| **Hasarlı bina** | **394** (lat/lon + `damageGrade` + `objType`) | **927** |

Veri `benchmark/data/*_copernicus_ground_truth.json` içinde **ayrıştırılmış ve
kullanıma hazır**; `simulate_random_closures`'ın `rng.sample` satırının yerine
geçecek eşleme (EMSR çizgisi → OSM kenarı) yazılmamış durumda.

---

### J-12 ek bulgu — EMSR648 kapsama analizi (15 Eylül 2026, ölçülmüş)

**Erişim sorunu YOK — doğrulandı.** Paketler Copernicus EMS'in public S3'ünden
kayıt/giriş/token olmadan iniyor (`curl -I` → **HTTP 200**). Makalede kaynak
gösterimi: aktivasyon kimliği + AOI + geçiş + sürüm + teslim tarihi. Hakem aynı
dosyayı indirebilir. Sürümlü ve dondurulmuş olduğu için Google/Esri karolarının
aksine zamanla değişmez.

**EMSR648'de 20 AOI var.** Üçü daha indirildi (AOI08 Pazarcık, AOI18 Kırıkhan,
AOI20 Elbistan; toplam 3,7 MB). AOI18'in MONIT01 geçişi **yok** (HTTP 403),
yalnız PRODUCT var. İskenderun, Samandağ, Belen ve Göksun için bu aktivasyonda
**hiç AOI yok**.

**Ölçülen bölge kapsaması (3 km yarıçap içinde, hasarlı kayıt sayısı):**

| Bölge | AOI | Hasarlı **yol** | Hasarlı **bina** |
|---|---|---|---|
| H-Z1 Antakya–Defne | AOI11 MONIT01 | 30 | 112 |
| H-Z3 Kırıkhan | AOI18 **PRODUCT** | 16 (*hepsi yalnız "Possibly damaged"*) | 1 505 |
| K-Z1 Maraş Merkez | AOI04 MONIT01 | 119 | 744 |
| K-Z2 Elbistan | AOI20 MONIT01 | 26 | 289 |
| K-Z3 Pazarcık | AOI08 MONIT01 | **0** (*yol katmanının 424 kaydının tamamı "Not Analysed"*) | 79 |
| H-Z2 İskenderun · H-Z4 Samandağ · H-Z5 Belen · K-Z4 Göksun | **yok** | — | — |
| **TOPLAM** | | **191 (4 bölge)** | **2 729 (5 bölge)** |

**İki katmanın kapsaması FARKLI — bu ayrım makalede korunmalı:**

- **Yol kapanma katmanı** (`simulate_random_closures`'ın `rng.sample`'ının yerine
  geçecek olan): yalnız **4 bölgede** veri var. Pazarcık'ta yol katmanı hiç
  analiz edilmemiş; Kırıkhan'daki 16 kayıt en zayıf derecede ve PRODUCT
  geçişinden — kodun kendi notu PRODUCT'ın MONIT01'e göre çok fakir olduğunu
  söylüyor.
- **Hasar noktası katmanı** (λ(d) cezası + model doğrulaması): **5 bölgede**
  veri var ve zengin (2 729 kayıt).

**Açık kalan karar.** 9 bölgenin 4'ünde (İskenderun, Samandağ, Belen, Göksun)
ve yol katmanı bakımından 5'inde yer gerçeği yok. Seçenekler: (a) hibrit —
kapsanan bölgelerde gerçek, kalanlarda sentetik ve **açıkça etiketli**;
(b) senaryoyu kapsanan bölgelere indir (örneklem küçülür, E-06 ağırlaşır);
(c) bölge kümesini AOI'lere göre yeniden seç. Kullanıcı kararı bekleniyor.

---


### J-12 kapanış — EMSR648 kapanma katmanı bağlandı (16 Eylül 2026)

**Uygulama.**
- `apps/road_damage/utils/network.py` → `closures_from_lines()`: yer gerçeği
  hasarlı yol çizgilerini OSM grafına eşler. Bir kenar, boyunca ~2 m arayla
  alınan noktalarının **en az %50'si** hasarlı bir çizginin **8 m** yakınındaysa
  kapanır (kavşakta değen sokaklar kapanmaz). Tampon ölçüme dayanıyor: EMSR
  köşe noktalarının en yakın OSM kenarına medyan uzaklığı 0,1–2,2 m, %75'i 3–6 m.
- `benchmark/copernicus_ground_truth.py` → `damaged_road_lines()`,
  `road_grade_counts()`, `aoi_rings()`; üç geçilebilirlik kuralı
  (`strict` = Destroyed · `medium` = + Damaged · `loose` = + Possibly damaged).
- `POST /api/road_damage/closures_from_emsr` — `/simulate_closures` ile aynı
  yanıt ve oturum; `closureSource: "emsr648"`.
- `full_scenario.py --closure-source emsr --emsr-rule … --zones …`.
- Veri setlerinde bölge başına `emsrPackage`: H-Z1 (AOI11), H-Z3 (AOI18,
  yalnız PRODUCT), K-Z1 (AOI04), K-Z2 (AOI20); drone sahneleri H-D1/H-D2
  (AOI11), K-D1 (AOI04). H-Z2, H-Z4, H-Z5 için AOI yok; K-Z3'ün yol katmanı
  "Not Analysed".

**Göz kontrolü (K-D1):** kapatılan OSM kenarları EMSR "Damaged" çizgileriyle
örtüşüyor; birkaç EMSR çizgisinin OSM'de karşılığı yok (grafta o sokak yok ya
da 8 m'den fazla kayık) — onlar kapanmıyor.

**Kapsam kaydı:** 3 km'lik ilçe graflarında kenarların %92,7–94,4'ü EMSR AOI'si
içinde; kalan ~%6 hakkında yer gerçeği yok ve **açık kabul edildi**.

**Kapanma oranları (gevşek kural):** K-Z1 %1,80 (EMSR il geneli Maraş %1,71 ile
uyumlu) · H-Z1 %0,84 · K-Z2 %0,53 · H-Z3 %0,32 · K-D1 %24,4 · H-D1/H-D2 %0.

**Bulunan ve düzeltilen yerleşim hatası:** EMSR koşusunda HQ-K1 (Maraş) "ağdan
kopmuş" göründü — gerçek sebep, karargâh koordinatının grafta **12 m'lik çıkmaz
bir bağlantı yoluna** düşmesi ve o parçanın kapanmasıydı (ağın geri kalanı,
20 641 düğüm, açıktı). Tüm karargâhlar tarandı; çıkmaz düğüme düşen iki tane
(HQ-K1, HQ-HD2) en yakın gerçek kavşağa (~40 m) taşındı ve veri setine
gerekçesiyle yazıldı. Önceki koşular `runs/_superseded/2026-09-16-karargah-duzeltmesi-oncesi/`.

## J-14 🔴 SegFormer, HTTP sunucu sürecinde boşuna yükleniyor
**Durum:** KAPALI (15 Eylül 2026)

**Sorun.** `fastapi_app.py:170` (`_load_road_runtime`) SegFormer ağırlıklarını
sunucu sürecine yükleyip `runtime["model"]` / `runtime["device"]` /
`runtime["run_inference"]` / `runtime["analyze_road_network_graph"]` anahtarlarına
koyuyor. Bu anahtarların **hiçbiri `fastapi_app.py` içinde okunmuyor** — dosyadaki
tek `runtime[...]` okumaları `get_wayback_versions`, `search_oam_images`,
`bbox_from_center` ve `calculate_route`. Gerçek çıkarım `apps/road_damage/worker.py`
içinde, **ayrı süreçte**, o sürecin **kendi** model kopyasıyla çalışıyor
(`_init_worker` → `load_simple_model`).

**Ölçüm** (bileşen bileşen, aynı süreçte RSS artışı):

| Aşama | İş parçacığı | RSS |
|---|---|---|
| Boş yorumlayıcı | 4 | 19 MB |
| `import torch` | 26 | 205 MB |
| İlk torch matris çarpımı | 39 | 211 MB |
| `ultralytics` + YOLO catlak + YOLO bina | 39 | 365 MB |
| **SegFormer (sunucuda kullanılmıyor)** | 39 | **983 MB** |
| `osmnx` | 39 | 1 119 MB |

Yani **+618 MB ve +5,3 sn açılış**, hiç okunmayan bir sözlük girdisi için.
Ayakta duran sistemde ölçülen: sunucu süreci 1 183 MB, havuz işçisi 1 030 MB,
toplam ~2,2 GB — bunun ~618 MB'ı doğrudan bu maddedir.

**Yapılacak.** `_load_road_runtime`'dan `load_simple_model` çağrısını ve
`model`/`device`/`run_inference`/`analyze_road_network_graph` anahtarlarını
çıkar. **Yan etki (olumlu):** şu an model dosyası eksikse `_get_road_runtime`
patlıyor ve `/route`, `/wayback_versions`, `/oam_search` 503 dönüyor; bu
bağımlılık da kalkar.

**Dikkat.** `main.py` (Streamlit) ve `apps/road_damage/app.py` bu anahtarları
kendi kopyalarında kullanıyor — onlara dokunulmamalı.

**Kapandı.** `_load_road_runtime`'dan `load_simple_model` çağrısı ve
`model` / `device` / `run_inference` / `analyze_road_network_graph` anahtarları
çıkarıldı; `apps.road_damage.utils.inference` artık sunucu sürecine hiç import
edilmiyor. `main.py` ve `apps/road_damage/app.py` (Streamlit) dokunulmadı.

**Ölçülen sonuç** (aynı makine, aynı koşullar, ayakta duran sistem):

| | Önce | Sonra |
|---|---|---|
| Sunucu süreci RSS | 1 183 MB | **681 MB** (−502 MB) |
| Havuz işçisi RSS | 1 030 MB | 1 030 MB (değişmedi — doğrusu bu) |
| **Toplam** | **2 218 MB** | **1 716 MB** |
| Sunucu iş parçacığı | 49 | 51 |

**Dürüst kayıt.** (a) Bellek kazancı, izole ölçümdeki 618 MB tahmininin altında
çıktı: gerçek değer **502 MB**. (b) İş parçacığı sayısı **düşmedi** — torch
YOLO modelleri için sunucuda kalmaya devam ediyor, dolayısıyla J-15
(iş parçacığı aşırı-aboneliği) bu maddeyle kapanmadı. (c) Ayrıca önceden
ölçülen 5,3 sn'lik SegFormer yüklemesi artık açılışta hiç yapılmıyor.

**İşlevsel doğrulama (canlı backend, beş uç nokta):**

| Uç nokta | Sonuç |
|---|---|
| `/wayback_versions` | HTTP 200 · 1,54 sn |
| `/oam_search` | HTTP 200 · 1,03 sn |
| `/route` | HTTP 200 · **7 645,2 m / 405 nokta — değişiklik öncesiyle birebir aynı** |
| `/naive_compare` | HTTP 200 · 10 166,5 m / 29 keşif |
| `/analyze` | HTTP 202 → **done**; SegFormer işçi süreçte 16 parçayı işledi (inference 41,2 sn, toplam 66,3 sn), 3 924 yol segmenti + 6 sonuç görseli üretildi |

---

## J-15 🟠 torch iş parçacığı aşırı-aboneliği — hiçbir yerde sınırlanmamış
**Durum:** AÇIK · **Bulundu:** 15 Eylül 2026

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

## J-17 🟠 Oturum deposu 20 tam graf tutabiliyor — 2,7 GB tavan
**Durum:** KAPALI (15 Eylül 2026)

**Sorun.** `ROAD_DAMAGE_SESSION_LIMIT = 20` (`fastapi_app.py:263`) ve her oturum
bir **tam** `G` tutuyor (`safe_G` bir görünüm olduğu için ek yer kaplamıyor —
bu doğru yapılmış).

**Ölçüm.** Tek bölge grafı bellekte **135 MB** → 20 oturum = **2,70 GB**.
Makine 16,9 GB ve ölçüm sırasında %91 doluydu. Dokuz bölgeli senaryo koşumu
tek başına 9 × 135 MB ≈ 1,2 GB oturum verisi bırakıyor ve bu veri, sınır
dolana kadar **hiç boşalmıyor** (zaman aşımı yok, yalnızca FIFO taşması var).

**Yapılacak.** Yaşa göre tahliye ekle (ör. 30 dakika) ve sınırı senaryo
ihtiyacına göre (9–12) düşür. J-16 uygulanırsa graf başına 123 MB'a iner ama
asıl çözüm tahliyedir.

**Kapandı.** Tahliye artık **üç ölçüte** birden bakıyor (`fastapi_app.py`,
`_evict_road_damage_sessions_locked`), üçü de ortam değişkeniyle ayarlanabilir:

| Ölçüt | Varsayılan | Değişken |
|---|---|---|
| Süre aşımı | 30 dk | `QUAKEMIND_SESSION_TTL_SEC` |
| Sayı sınırı | 20 | `QUAKEMIND_SESSION_LIMIT` |
| **Bellek bütçesi** | **1024 MB** | `QUAKEMIND_SESSION_BUDGET_MB` |

Bütçe tahmini ölçülmüş bir sabite dayanıyor: beş gerçek bölge grafında
(2 535 – 70 309 eleman) RSS artışı eleman başına **792 – 1 855 bayt**; oran graf
büyüdükçe arttığı için hesapta ortalama değil **üst değer (1 900)** kullanılıyor.
Ayrıca `_sweep_road_damage_sessions` adlı bir arka plan iş parçacığı dakikada
bir süpürüyor — tahliyeyi yalnızca istek anlarına bağlamak yetmiyordu.

**Senaryo bozulmuyor.** Dokuz bölgeli Senaryo v2'nin tamamı ~97 300 düğüm +
222 300 kenar = ~319 600 eleman ≈ **607 MB tahmin**, yani 1024 MB'lik bütçe tam
bir koşumu ~1,7× paylayla taşır.

**Bulunan ve düzeltilen hata.** İlk uygulamada bütçeden tek başına büyük bir
graf, saklanırken `protect` ile korunuyor ama **ilk okumada** tahliye ediliyordu
— `/route` hemen 422 dönerdi. Bütçe döngüsü artık hiçbir zaman son oturumu
düşürmüyor. (Bunu yakalayan test: "Tek başına bütçeden BÜYÜK graf yine de
saklanır".) Ayrıca aynı kimlik iki kez saklandığında sıra listesinde mükerrer
girdi oluşup canlı bir oturumu düşürebilen eski hata da kapatıldı.

**Doğrulama.** 12/12 birim kontrolü (süre aşımı, sayı sınırı, bütçe, görünümün
iki kez sayılmaması, mükerrer kimlik, süpürücü) + canlı sistemde gerçek
Antakya grafıyla uçtan uca:

| Adım | Ölçüm |
|---|---|
| Başlangıç | 681 MB |
| 3 oturum + her birine `/route` | 854 MB · rotalar 8 413,1 / 7 448,1 / 7 987,8 m |
| 60 sn sessiz bekleme (hiç istek yok) | süpürücü 3 oturumu düşürdü |
| Süresi dolmuş oturuma `/route` | **HTTP 422** — "oturum bulunamadi veya suresi doldu" |
| 3 oturum daha | 854 → **898 MB (+44 MB)**, ilk üçü +173 MB'dı |

**Dürüst kayıt — RSS DÜŞMÜYOR.** Tahliyeden sonra RSS 854 MB'da kaldı: CPython
serbest bıraktığı arena'ları işletim sistemine geri vermiyor. Kazanç bellek
*iadesi* değil, **büyümenin sınırlanması**: boşalan arena'lar yeniden kullanılıyor
(yukarıdaki son satır bunu kanıtlıyor — ikinci üç oturum ilkinin dörtte biri
kadar yer kapladı). Yani tavan 2,7 GB'a tırmanmak yerine platoya oturuyor.

**Not.** Bütçe tahmini gerçek kullanımın ~2 katı kadar temkinli çıkıyor (canlı
ölçümde oturum başına ~58 MB, tahmin ~112 MB). Bu güvenli yön: bütçe gerçek
tavana varmadan tetikleniyor.

---

## J-63 🟠 Tatbikat rota grafiği görüntü kutusuyla sınırlıydı — 25 OD çiftinin 25'i "ulaşılamaz"
**Durum:** KAPALI (25 Eylül 2026) · **Bulundu:** 25 Eylül 2026 (simülasyon backend'i uçtan uca koşulurken) · **İlgili:** J-62, SIMULASYON_SOZLESMESI.md §4

**Sorun.** Simülasyonun ilk uçtan uca koşusunda rota aşaması, hasar analizinin kendi
grafiğini (`road_damage_sessions`) kullanıyordu. O grafik yalnız **görüntü kutusunu**
kapsar: yakın katmanda 120 düğüm / 340 kenar, yaklaşık 500 m. Ekip üsleri ise gerçek
tesisler ve 1,31–3,80 km uzakta. Sonuç: bütün ekipler kutunun dışında kaldı,
`nearest_node` hepsini kutunun kenarına yapıştırdı, 25 çiftin **25'i** "ulaşılamadı"
döndü — rota özelliği aslında hiç çalışmamış oluyordu.

**Düzeltme.** `apps/road_damage/utils/tatbikat.py: tatbikat_grafigi()` grafiği ayrı çeker:
ekipleri ve afetzedeleri kapsayan kutu + 600 m pay. Kapanmalar maskeden
`closures_from_damage_mask` ile türetilir (canlı `/analyze` ile aynı kural ve aynı
örnekleme). Ölçüldü (Maxar geniş katman): 4 410 düğüm, 12 108 kenar, 87 kenar kapalı,
**ulaşılamayan çift 0**.

---

## J-64 🟠 Araç giremeyince "ulaşılamaz" deniyordu; gerçekte son adım yaya yürünür
**Durum:** KAPALI (25 Eylül 2026) · **Bulundu:** 25 Eylül 2026 · **İlgili:** J-63

**Sorun.** J-63 düzeltildikten sonra bile 25 çiftin 15'i "ulaşılamadı" dönüyordu: afetzedenin
en yakın düğümüne giden kenarlar kapandığında `safe_G` üzerinde yol kalmıyor. Bu, sahadaki
gerçeği yansıtmıyor — ekip aracıyla enkazın kenarına kadar gider, kalanı yürür.

**Düzeltme.** `son_adim_yurume()`: ekipten ulaşılabilir bütün düğümler tek kaynaklı
Dijkstra ile bulunur, afetzedeye kuş uçuşu en yakın olanına rota çizilir, kalan mesafe
`sonAdimYurumeM` olarak (yaya 5 km/sa) yazılır. Ölçüldü: 15 çiftte gerekti, **ortalama
56,4 m**. Ulaşılamayan çift 15 → 0; ortalama uzama 121,4 m → 69,2 m (%6,8).

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

## J-66 🟠 Çıkarım iş parçacığı sınırsızdı: aynı iş 26,6 sn ile 243,1 sn arasında oynuyordu
**Durum:** KAPALI (25 Eylül 2026) · **Bulundu:** 25 Eylül 2026 · **İlgili:** J-15

**Ölçüm.** Aynı görüntü (Maxar, 2048×2048, 25 yama), aynı model (U-Net MiT-B4), üç koşu:
AI süresi 52,1 / 243,1 / 26,6 sn. torch varsayılan olarak 14 iş parçacığı açıyor
(20 çekirdekli makinede) ve başka süreçlerle yarışınca süre savruluyor. Yama başına ölçüm:
14 parçacık 0,52 sn · 10 → 0,58 · 8 → 0,66 · **6 → 0,48** · 4 → 0,63 · 2 → 1,02.

**Düzeltme.** `worker._is_parcacigi_sinirla()` işçi sürecini `min(6, çekirdek/2)` ile
sınırlar (`QM_CIKARIM_IS_PARCACIGI` ile değiştirilebilir). Hız bedeli yok, üstelik ölçüm
kararlı hâle geldi (243 → 26,6 sn) ve kalan 14 çekirdek API sürecine ve tarayıcıya kalıyor
— "arka iş koşarken ön taraf yavaşlamasın" kuralının çalışma şartı bu.

---

## J-67 🟡 İki venv var; ürünün hangisi olduğu belgeli değil, aralarında 6 kat hız farkı
**Durum:** AÇIK · **Bulundu:** 25 Eylül 2026

Depoda iki sanal ortam var: kök `venv` (torch 2.11.0, jwt var → API bunu kullanıyor) ve
`QuakeMindBackend/venv` (torch 2.13.0, jwt YOK → API başlatılamaz). Aynı modelin 512×512
ileri geçişi kök venv'de 0,61 sn, backend venv'de 4,39 sn — **6 kat**. Model künyelerindeki
ölçüm notu hangi ortamda alındığını yazıyor, ama depoda hangi venv'in ürün olduğu ve
diğerinin niye durduğu yazılı değil. Yanlış venv ile alınan bir ölçüm makaleye girerse
hatalı olur.

---

## J-68 🟠 Overpass düşünce yol katmanı sessizce boş geliyor, analiz "0 kapalı yol" diyordu
**Durum:** KAPALI (25 Eylül 2026) · **Bulundu:** 25 Eylül 2026 (üç ayrı koşuda) · **İlgili:** J-64

`get_osm_roads_overpass` bütün aynalar düştüğünde **boş maske** dönüyor; analiz bunu "bu
alanda yol yok" gibi işleyip devam ediyordu. Sonuç: `2/4 OSM yol agi cikarildi (0 piksel)`,
kesişim 0, "kapalı yol 0". Sıfır yol, yol olmadığı anlamına gelmez — katmanın alınamadığı
anlamına gelir. Bir ölçümde bu fark, "model hiçbir yolu kapatmıyor" gibi yanlış bir sonuca
götürür (bu oturumda bir kez götürdü).

**Düzeltme.** `worker.py` yol maskesi boşsa günlüğe uyarı yazıyor ve sonuca
`roadLayerMissing: true` koyuyor; simülasyon sonucunda `kapanma.yolKatmaniYok`. Arayüz bu
durumda sayı göstermez, "yol katmanı alınamadı" yazar.

**Ölçüm (katman geldiğinde, aynı görüntü).** 14,08 km yol; modelin hasarı **doğrudan yol
pikseline düşen** kısmı 1 303 px ≈ **105 m**; r_h = 25 m ile yayıldığında 14 055 px ≈
**1 129 m** (yolun %8'i). Yedi blobun dördü yola doğrudan değiyor.

**Açık soru (J-19'a bağlı).** r_h = 25 m, 105 metrelik gerçek taşmayı 1 129 metreye çeviriyor
(11 kat). Bu bir tasarım kararı; tatbikat sonucunda yarıçap yazılı ama duyarlılık ölçülmedi —
r_h = 10 / 15 / 25 m için kapanan yol uzunluğu ve rota uzaması ölçülmeli.

---

## J-69 🟠 r_h (sert kapanma yarıçapı) duyarlılığı ölçüldü — araca erişimi belirleyen ayar
**Durum:** ÖLÇÜLDÜ, karar bekliyor · **Bulundu:** 25 Eylül 2026 · **İlgili:** J-19, J-64, J-68, J-26

**Neden.** Kapanma bina hasarından türetiliyor: bir yol, hasarlı noktaya r_h metreden yakınsa
kapalı sayılır. r_h = 0 iken yalnız yolun tam üstündeki hasar sayılır (uygulamanın eski kuralı)
ve sokağa dökülen moloz görünmez; büyüdükçe açık sokaklar da kapalı sayılır.

**Ölçüm.** Hatay/Defne — Elektrik, geniş katman (Maxar 2023-02-08), U-Net MiT-B4, eşik 0,5,
tohum 42; graf 4 164 düğüm / 11 491 kenar / **831,6 km**; 5 gerçek ekip üssü × 5 senaryo
afetzedesi = 25 çift. Çıkarım bir kez koştu, dört yarıçap aynı maske ve aynı graf üzerinde
denendi. Betik `QuakeMindBackend/benchmark/rh_duyarlilik.py`, kayıt
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

## J-71 🟢 Simülasyon uçtan uca çalıştı (konsol + backend), dört hata düzeltildi
**Durum:** KAPALI (26 Eylül 2026) · **İlgili:** J-62, J-70, `DEMO_CALISTIRMA.md`

İlk kez arayüzden başlatılan tatbikat baştan sona koştu: Hatay/Elektrik geniş katman
(Maxar 2023-02-08), U-Net MiT-B4, 5 gerçek ekip üssü → 5 senaryo afetzedesi. Toplam 78 sn
(görüntü 7,5 · yol 0,8 · çıkarım 63,7 · lojistik 6,2). SSE ile dört katman sırayla geldi
(hasar → kapanma → rota → görev), TATBİKAT şeridi koşu boyunca durdu.

**Düzeltilen dört hata:**
1. **Durum yanlış görünüyordu.** Analiz iş deposunun durumu işin sonuna kadar "queued"
   kaldığı için sonuç ucu %47 ilerlemede bile "kuyrukta" diyordu. İlerleme > 0 ise
   "calisiyor" döner.
2. **Haritadaki kırmızı katman yanlış kümeydi.** Kapalı kenar çizgileri analizin (görüntü
   kutusuyla sınırlı) sonucundan geliyordu; artık tatbikatın kendi grafiğinden geliyor
   (`kapanma.kapaliKenarlar`), analizinki `analizKapaliKenarlar` olarak ayrı duruyor.
3. **"NaN sa" satırları.** `referansAjanlar` sözlüğüne konan metin ve görüş mesafesi
   alanları arayüzde varyant sanılıp NaN olarak çiziliyordu; ikisi ayrı alana taşındı
   (`referansNotu`, `referansGorusMesafesiM`).
4. **Panel hâlâ r_h gönderiyordu.** Kapanma yarıçapı kaydırıcısı ve yumuşak maliyet
   anahtarı panelden kaldırıldı, konsol varsayılanı 25 → 0 (J-70). Bu düzeltilmeden önce
   koşu %157 rota uzaması üretiyordu; sonrasında %1,2.

Sunum hesabı `demo@quakemind.local` (koordinatör) açıldı; çalıştırma sırası
`DEMO_CALISTIRMA.md`'de.

---

## J-72 🟠 Analizin bulduğu hasar hiçbir yere kaydedilmiyordu (PostGIS yokken sessiz düşüyordu)
**Durum:** KAPALI (26 Eylül 2026) · **Bulundu:** 26 Eylül 2026 (uçtan uca bütünleşme denetiminde) · **İlgili:** J-71, kural 2

**Sorun.** `worker.py` hasar bloblarının ağırlık merkezlerini `damage_points` olarak
**yalnız PostGIS'e** yazmayı deniyordu. Yerel geliştirmede PostGIS kapalı
(`check_connection()` False, depo SQLite) ve yazma `except` içinde sessizce düşüyordu.
Sonuç: analiz ve tatbikat gerçek hasar buluyor ama ısı haritası, risk motoru ve genel
durum ekranı bundan hiç haberdar olmuyordu — ölçüldü, `hasar_noktalari` tablosunda
`kaynak='uydu'` **sıfır** kayıt vardı.

**Düzeltme.** PostGIS yoksa yerel depoya yazılır (`aktif_depo().hasar_ekle`,
`kaynak="uydu"` — konsolun uydu kanalının sorguladığı değer). Doğrulandı: tatbikat
koşusundan sonra `/api/hasar-noktalari` 14 kayıt döndü (12 SOS + 1 kamera + **1 uydu**),
nokta genel haritada görünüyor. Böylece simülasyonun çıktısı sistemin geri kalanına
gerçekten bağlanmış oldu (kural 2: her model aynı sözleşmeye iner).

---

## J-73 🟠 Tatbikat başlatılabiliyordu ama bitirilemiyordu; verisi gerçek veriyle karışıyordu
**Durum:** KAPALI (26 Eylül 2026) · **Bulundu:** 26 Eylül 2026 (kullanıcı isteği) · **İlgili:** J-71, J-72

**Sorun.** Simülasyon bir sayfaydı, mod değildi: "Tatbikatı başlat" vardı, bitirme yoktu.
Koşu başlayınca TATBİKAT şeridi kalıcı oluyordu (doğru) ama çıkmanın yolu yoktu. Dahası
J-72 ile hasar noktaları veritabanına yazılmaya başlandığı için **tatbikat verisi gerçek
olay verisiyle karışıyordu** — koşu bitse de noktalar canlı kümede kalıyordu.

**Yapılan.**
- `POST /api/simulasyon/bitir` eklendi: koşunun yazdığı hasar noktalarını siler
  (`depo.hasar_sil_tatbikat`, `ek.tatbikat` işaretinden önek eşlemesiyle — kontrol
  koşusunun `<isId>_kontrol` kimliği de kapsanır) ve canlı akışa `durum: "iptal"` yayınlar.
- Konsola **"Tatbikatı bitir"** düğmesi eklendi; başlatma düğmesi koşu varken
  "Yeniden koştur" olur. Şeritte kapatma yok (uyarı susturulamaz), bitirme panelde.
- `durum: "iptal"` canlı akıştan gelince AÇIK olan bütün istemciler tatbikat modundan
  çıkar — bitiren sekmeyi temizlemek yetmez.
- Hasar noktaları "Tatbikat — uydu hasar bölütlemesi" diye etiketlenir ve `ek.tatbikat`
  taşır; hangisinin tatbikattan geldiği veride de bellidir (kural 1).
- **Kontrol koşusu artık hasar noktası yazmıyor:** deprem öncesi görüntüde bulunan şey
  yanlış alarm tabanıdır, olay değildir.

**Doğrulandı.** Başlat → şerit açıldı, 1 nokta yazıldı (kontrol koşusundan sıfır); bitir →
şerit kalktı, düğme başa döndü, tatbikat noktaları silindi, 13 gerçek nokta yerinde kaldı.

---

## J-74 🟠 Tatbikat modu sayfa yenilenince kayboluyordu (koşu sunucuda sürerken)
**Durum:** KAPALI (26 Eylül 2026) · **Bulundu:** 26 Eylül 2026 (arayüz turunda) · **İlgili:** J-73

**Sorun.** Koşunun kimliği yalnız bellekteki durumda (zustand) duruyordu. Sayfa yenilenince
— ya da tam sayfa yüklenen bir adrese gidilince — TATBİKAT şeridi kalkıyor, katmanlar
düşüyor, ekran normal akışa dönüyordu. Oysa **koşu sunucuda sürüyor** ve hasar noktaları
duruyordu: kullanıcı tatbikatın bittiğini sanıp gerçek veriye bakıyor sanıyordu. Sunumda
yanlışlıkla F5'e basmak tatbikatı "bitirmiş" gibi görünürdü.

**Düzeltme.** Koşu kimliği sekmenin `sessionStorage`'ında tutuluyor: yenilemeyi aşar, sekme
kapanınca biter, başka sekmeye ya da kullanıcıya sızmaz. Okuma/yazma try/catch içinde —
özel pencerede ya da depolama kapalıyken uygulama yine çalışır, yalnız mod yenilemeyi aşmaz.

**İkinci hata (aynı kökten).** Yenileme sonrası iş kaydı da sıfırlandığı için biten koşu
şeritte "%0", panelde "katman bekleniyor" görünüyordu. Durum artık sonucun kendi
`durum`/`ilerleme` alanlarından da okunuyor; yenileme sonrası "4/4 katman · bütün katmanlar
hazır" yazıyor. Doğrulandı.

---

## J-75 🟠 Seçilen görüntü haritada görünmüyordu — model neye baktığı ekranda yoktu
**Durum:** KAPALI (26 Eylül 2026) · **Bulundu:** 26 Eylül 2026 (kullanıcı isteği) · **İlgili:** J-35, kural 1

**Sorun.** Hasar analizi modunda soldan görüntü kaynağı (Google / Esri Wayback / OpenAerialMap)
ve tarih aralığı seçiliyor, hatta OAM görüntüsü tek tek seçilebiliyordu; ama harita yalnız OSM
altlığını çiziyordu. Kullanıcı **modelin neye baktığını göremiyordu**; analiz bitince de kapalı
yol çizgileri boşlukta duruyordu.

**Yapılan.** Seçilen kaynağın karoları haritaya katman olarak bindi: altlığın ÜSTÜNDE, olay ve
analiz katmanlarının ALTINDA. "Katmanlar" menüsüne **"Analiz görüntüsü (modelin gördüğü)"**
anahtarı eklendi (hasar modunda varsayılan açık, kapatılınca altlığa dönülüyor). Kaynak künyesi
katmanın yanında yazılı.

**Yol boyunca çıkan üç engel.**
1. **Adres çiftlenmesi.** OAM'in `tms` adresi `{z}/{x}/{y}` yer tutucularını zaten taşıyor;
   körlemesine eklemek adresi `.../{z}/{x}/{y}/{z}/{x}/{y}.png` yapıyordu.
2. **Maplibre katmanı görünmüyor.** Bağımlılık eklememek için önce maplibre raster kaynağı
   denendi: karolar iniyor, katman stile giriyor, ekranda hiçbir şey çıkmıyordu — altlık ve
   analiz deck.gl ile çizildiği için maplibre katmanı onların altında kalıyor. Çözüm: görüntü de
   deck ile çiziliyor (`@deck.gl/geo-layers` TileLayer, mevcut deck sürümüyle aynı hat).
3. **CORS.** deck karoyu `fetch` ile indiriyor; OpenAerialMap ve Esri `Access-Control-Allow-Origin`
   göndermiyor, tarayıcı hepsini engelliyordu (12 istek gidiyor, sıfırı çiziliyordu). Çözüm:
   karolar kendi API'mizden geçiyor — **`GET /api/goruntu/karo/{z}/{x}/{y}`**. Uç bir açık vekil
   DEĞİL: yalnız bilinen dört karo konağına gidiyor (SSRF'e kapalı), yetki istiyor ve 24 saat
   önbellek başlığı veriyor. Yetkili olduğu için jeton katmana `loadOptions` ile geçiriliyor.

**Doğrulandı (tarayıcıda).** Maxar 2023-02-08 görüntüsü haritaya oturdu, hasar noktaları üstünde
kaldı; katman anahtarı kapatılınca görüntü kalkıp altlık geri geldi, açılınca döndü.

---

## J-76 🔴 Analiz yakınlaştırmayı çizilen alandan değil istekteki yarıçaptan seçiyordu — model hiçbir şey bulamıyordu
**Durum:** KAPALI (26 Eylül 2026) · **Bulundu:** 26 Eylül 2026 (kullanıcı bildirdi) · **İlgili:** J-20, J-58, J-26

**Belirti.** Haritada 0,4 × 0,3 km'lik alan seçilip analiz koşuluyor; sonuç
**"Kapalı yol 0 segment · %0,0, Hasar oranı %0,0"** diyor. Aynı bölge daha önce doğru analiz
edilmişti. Ekranda künye "2,5 km yarıçap · z15 · ~3,86 m/piksel" yazıyor ve panelin kendi
uyarısı "model 0,3–0,5 m/piksel ile eğitildi" diyor.

**Kök sebep.** Yakınlaştırma `zoom_for_radius(radiusKm)` ile seçiliyordu. Konsol alan çizilse
bile hazır ayarın yarıçapını (Standart analiz = 2,5 km) gönderiyor; sunucu da kutuya değil o
sayıya bakıyordu. Sonuç: 0,4 km'lik alan z15'te (~3,86 m/piksel) indiriliyor, görüntü ~100
piksel kalıyor, çöken bina 1–2 piksele düşüyor ve model hiçbir şey bulamıyor.

**Düzeltme.**
1. **Sunucu:** yakınlaştırma artık ANALİZ KUTUSUNUN kendi büyüklüğünden hesaplanıyor
   (`worker.py`); kutu verilmediğinde eski davranış aynen kalıyor.
2. **Sunucu:** OpenAerialMap sahnesi, kullanıcının çizdiği kutuyu artık EZMİYOR. Önceden
   sahne seçilince `bbox` sahnenin kutusuyla değiştiriliyordu — Maxar sahnesi 31×40 km'dir,
   0,4 km'lik seçim bir anda bütün sahneye dönüşüyordu.
3. **Konsol:** isteğe giden `radiusKm` analiz kutusundan hesaplanıyor; ekrandaki yazı da doğru.

**Ölçüldü (aynı istek, aynı alan).**

| | Önce | Sonra |
|---|---|---|
| Yakınlaştırma | z15 · 3,86 m/px | **z18 · 0,482 m/px** |
| GSD uyarısı | var | **yok** |
| Hasar oranı | %0,0 | **%0,58** (geçerli alanda %1,49) |
| Kapalı yol | 0 | **8** |

**Aynı koşuda kapatılan iki eksik daha.**
- **Model seçimi (kullanıcı isteği).** `/api/road_damage/analyze` artık `modelAdi` alıyor ve yeni
  `GET /api/road_damage/modeller` ucu eğitilen bütün künyeleri (mimari, sınama IoU, eşik, eğitim
  GSD'si, ağırlık izi, hazır mı) listeliyor. Konsolun hasar panelinde model seçici var; seçilmezse
  sunucunun etkin modeli koşar. Dört model de listede ve seçilebilir durumda.
- **J-58 kapandı: kapanmalar artık çizgi.** `yol_kapanmalari` kaydına parçanın kendi çizgisi
  eklendi ve konsol kapanmayı **kırmızı çizgi** olarak çiziyor. Önceden yalnız orta nokta
  saklandığı için harita kapanmaları turuncu nokta tarlası gibi gösteriyordu — kullanıcının
  "her taraf nokta oldu" dediği şey buydu. Eski kayıtlarda çizgi yok; onlar nokta kalır.

**Açık kalan.** Eski (çizgisiz) 280 kapanma kaydı hâlâ nokta olarak çiziliyor; bunlar yanlış
yakınlaştırmayla koşmuş analizlerden geliyor. Silinmesi kullanıcı kararı.

---

## J-77 🟠 Analiz artık sabit standartta koşuyor; öncesi / sonrası / etiketli üçlüsü üretiliyor
**Durum:** KAPALI (26 Eylül 2026) · **Kullanıcı isteği** · **İlgili:** J-76, J-20, J-35

**İstenen.** "Analiz için görüntüler hep aynı standartta olsun, hep doğru sonuç alalım; analiz
bitince bana öncesi, sonrası ve etiketli hâlini ver."

**1. Standart çözünürlük.** Yakınlaştırma artık alan büyüklüğünden değil **modelin eğitildiği
metre/piksel** değerinden seçiliyor (`tiling.zoom_for_gsd`). Künyedeki eğitim bandının ortası
hedeftir: 0,3–0,5 m → hedef 0,4 m → **z18 = 0,482 m/piksel**, bandın içinde. Böylece hangi alan
seçilirse seçilsin analiz aynı ölçekte koşar; J-76'daki "geniş alan seçince çözünürlük düşüyor,
model hiçbir şey bulamıyor" durumu bir daha oluşamaz.

**Alan tavanı sessiz değil.** Bu çözünürlükte seçim karo tavanına sığmazsa `fetch_satellite_area`
merkezden kırpıyor; sonuç artık `analizAlaniKm2` ve `istenenAlaniKm2` alanlarını ve künyeye
"seçilen alan X km², tek koşuya Y km² sığdı, merkezden kırpıldı" notunu yazıyor.

**2. Öncesi / sonrası / etiketli.** Analiz, deprem ÖNCESİ görüntüyü de çekiyor
(`oncesiGoruntusu`, varsayılan açık): Esri Wayback sürümleri **çekim tarihine** göre taranıp
olaydan önceki ilk çekim seçiliyor (J-35; bu alanda sürüm 44873, çekim 2021-09-27). Görüntü
`imageOncesi` adıyla diğer görsellerle aynı uçtan iniyor:

| Görsel | Ne |
|---|---|
| `imageOncesi` | Deprem öncesi (Esri Wayback, gerçek çekim tarihi künyede) |
| `imageOriginal` | Analiz edilen deprem sonrası görüntü |
| `imageSegmentationOverlay` | Aynı görüntü + modelin hasar maskesi |
| `imageDamageOverlay` | Hasar + yol ağı + kesişim |

**Hizalama düzeltildi.** İlk denemede öncesi 1536×1536, sonrası 1280×1280 çıktı: karo ızgarası
farklı oturuyor. Öncesi görüntüsü artık sonrasının kutusuna kırpılıp aynı piksel ölçüsüne
getiriliyor — üçü birebir hizalı (doğrulandı: 1280×1280 · 1280×1280 · 1280×1280).

**Ölçüldü (Hatay/Defne — Elektrik, U-Net MiT-B4, r_h 15 m).** z18 · 0,482 m/px · GSD uyarısı yok ·
hasar %0,58 (geçerli alanda %1,49) · açık yol 333 / **kapalı 30** · öncesi çekim 2021-09-27.

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

## J-141 🔴 Sunucuya ulaşılamazken eşitleme worker'ı sonsuz döngüye giriyor
**Durum:** AÇIK (PR #5) · **Ölçüldü**

`mobile/sync/.../IncidentSyncWorker.kt:34` `while (true)` + `IncidentDao.kt:20` `claimPendingBatch`
`PENDING` **ve** `FAILED` kayıtları çekiyor. Ağ hatasında kayıt `FAILED` yapılıyor, döngü aynı
çalışmada onu hemen yeniden çekiyor; `Result.retry()` satırına hiç ulaşılmıyor, WorkManager backoff'u
devreye girmiyor.

**Ölçüm.** Backend durduruldu, 8000 portuna bağlantı sayıp yanıt vermeden kapatan bir dinleyici
kondu, uygulamadan tek ihbar gönderildi: **80 sn'de ~12 000 bağlantı (~150/sn), uygulama %112 CPU**,
kendiliğinden durmadı. Afet anında sunucu çöktüğünde pil tükenir, sunucu dönünce de boğulur.

**Çözüm önerisi.** Bir çalışmada yalnız `PENDING` al ya da kurtarılabilir hatada döngüden çıkıp
`Result.retry()` dön.

## J-142 🟠 İhbar formundaki kategori, aciliyet ve kişi sayıları sunucuya gitmiyor
**Durum:** AÇIK (PR #5) · **Ölçüldü** · **İlgili:** CLAUDE.md §2

`BackendServices.kt:166` gövdeye yalnız `tur`, `metin`, `lat/lon`, `konumKaynagi` koyuyor. Formda
"Enkaz / Mahsur · Kritik · 1 mahsur kişi" seçilip gönderildi; veritabanındaki kayıt:
`tur=metin, etiket="Model incelemedi", ek={"konumKaynagi":"manuel"}`. Konsol bunun kritik enkaz
ihbarı olduğunu göremez. Çevrimdışı kuyruk yolu da (`IncidentSyncWorker.kt:41`) `IncidentDraft`'ı
kurarken `urgency`, `peopleCount`, `injuredCount`, `locationSource` alanlarını doldurmuyor →
varsayılana düşüyor. Backend tarafında da bu alanları taşıyacak yer yok (`IhbarIstegi` yalnız
`kisiSayisi` ve `ihtiyaclar` biliyor); sözleşme iki tarafta birlikte genişletilmeli.

## J-143 🟠 İhbar formu GPS kullanmıyor; afetzededen koordinat elle isteniyor
**Durum:** AÇIK (PR #5) · **Emülatörde görüldü** · **İlgili:** afetzede UX kararları

Ana ekran "Konum hazır · ±5 m" derken ve SOS ekranı GPS'i sorunsuz alırken `ReportScreen.kt:210`
"GPS bu formda otomatik alınmıyor" diyip enlem/boylam istiyor. Alanlar rakam klavyesi değil tam
QWERTY açıyor (`KeyboardType.Decimal` yok); emülatörde otomatik tamamlama boylama kendiliğinden
`" ft"` ekledi. GPS varsayılan olmalı, elle giriş yedek kalmalı.

## J-144 🟠 Risk ekranı etkenleri atıyor ve "servis bildirmedi" diyor
**Durum:** AÇIK (PR #5) · **Ölçüldü** · **İlgili:** CLAUDE.md §1

`BackendServices.kt:408` `factors = emptyList()` sabit. Aynı istekte backend
`factors: {"Kisa vadeli risk": 0.25, "Uzun vadeli tehlike": 0.43, "Fay etkisi": 1.0}` dönüyor
(Defne, 36.2021 / 36.1612). Ekranda "Servis bu analiz için ek etken bildirmedi" yazıyor — doğru değil.

## J-145 🟠 `/api/oturum/misafir` sınırsız hesap açıyor; kişi başı ihbar sınırı aşılıyor
**Durum:** AÇIK (PR #5) · **Ölçüldü** · **İlgili:** CLAUDE.md §5

`backend/uclar/oturum.py:58` kimliksiz, hız sınırsız; her çağrıda yeni `afetzede` hesabı. 30 misafir
art arda → 30 × 201; her biriyle SOS → 10 × 201. Her misafir yeni "kişi" olduğundan
`KISI_BASI_SINIR` anlamını yitiriyor; `/api/sos`'ta zaten sınır yok (eski sorun), `/kayit` de
sınırsız (eski sorun). Sahte SOS yağmuru riski → IP başına hız sınırı gerekli.

## J-146 🟡 Birleştirme sırası, klasör yeniden adlandırma ve mobil kapsamı karar bekliyor
**Durum:** KARAR BEKLİYOR

- PR `main`'e değil #4'ün dalına (`feat/altlik-hf-otomatik-indirme`) açık: önce #4, sonra taban `main`.
- `QuakeMindBackend/` → `backend/` (~640 dosya): açık dallar (#3 dahil) ve yerel
  `QuakeMindBackend/venv` kurulumları etkilenir. Belgelerde yalnız yol değişmiş (denetlendi).
- CLAUDE.md §10 mobili kapsam dışı sayıyor; PR Flutter uygulamasını cihaz içi `bina.tflite` ve
  `catlak.tflite` ile siliyor. `PROJE_DOSYASI.md:71` hâlâ "Flutter mobil istemci" diyor.

## J-147 🟡 Mobilde kaynak etiketi ve ölçümsüz iddia eksikleri
**Durum:** AÇIK (PR #5) · **İlgili:** CLAUDE.md §1, §6, §8

- Ana ekran "Yakındaki depremler" kartı 2026-08-12 tarihli kaydı gösteriyor (inceleme 12 Kasım),
  kaynak (Kandilli/AFAD) yazmıyor; tanıtım ekranı "saniyeler içinde takip edin" diyor.
- Haritada lejant ve kaynak yok; kırmızı iğnelerin ne olduğu belirsiz.
- Koyu kırmızı marka rengi olarak kullanılıyor (kırmızı yalnız hasar/aciliyet için).
- `mobile/README.md`: "120 FPS", "0 per-frame allocation" kaynaksız; "aile fertlerinin pil/konum
  takibi" yazıyor ama uygulama "bu sürümde doğrulanamıyor" diyor.

## J-148 ⚪ PR #5 küçük notlar
**Durum:** AÇIK (PR #5)

- `backend/fastapi_app.py:135` doğrudan çalıştırınca varsayılan `0.0.0.0` (API yerel ağa açılır).
- `BackendClient.kt:47` yenileme jetonu düz `SharedPreferences`'ta.
- `start.sh` "konsol klasörü yok" diyor ama denetlediği `quakemind-web`.
- PR açıklaması "`QuakeMinds/` altında" diyor; klasörler kökte.

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
| 26 Eylül 2026 | **Makale şekilleri üretildi (Word'e dokunulmadan).** `QuakeMindBackend/benchmark/makale_sekilleri/`: kıyas kolları, duyarlılık (eski 20 dk sabitinin etkisi gölgeli), model seçimi (süre/IoU/kazanç), süre dağılımı; ayrıca üç alanın tatbikat haritası (drone görüntüsü + hasar + kapalı yol + güzergâh + giriş ağızları, **göstergeli**, künyesinde kapsama ve kare dışında kalan giriş sayısı yazılı) ve öncesi/sonrası/etiketli üçlüsü. Üreticiler `araclar_makale_sekilleri.py` ve `araclar_makale_haritalari.py`; bütün sayılar `SIMULASYON_OLCUM_KAYDI.md`den gelir, şekilde hiçbir şey uydurulmaz. |
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
| 27 Eylül 2026 | **J-118 (🟡) bulundu, AÇIK: yan bulgular.** (1) `benchmark/data/model_masks_unet_mitb4/*/meta.json` modeli "dispath…dice30 / Segformer mit_b4" diye etiketliyor ama SHA-256 `unet_mitb4_p2_t42`'ninki. (2) `tile_quality_score` tanımlı ama hiçbir yerden çağrılmıyor. (3) `zoom_for_radius` analiz yolunda artık kullanılmıyor (`zoom_for_gsd`, z18). (4) Makale Tablo 12'deki yerel sürümler (Python 3.12.6, PyTorch 2.13.0, Ultralytics 8.4.116 …) ne `QuakeMindBackend/venv` (3.12.10 / 2.11.0 / 8.4.57) ne ölçüm kaydı (PyTorch 2.10) ile tutuyor; ölçümün yapıldığı i7-12700H makinesinde `pip freeze` ile doğrulanmalı. (5) `araclar_makale_haritalari.py` künye satırını sarmalamıyor, taşan kısım kesiliyor (makaleye kırpılmış sürüm kondu). |
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
