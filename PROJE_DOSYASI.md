# QuakeMind — Proje Dosyası

**Uzman ortak yazarlar için teknik tanıtım belgesi**

Son güncelleme: 12 Eylül 2026 · Kapsam: sistem mimarisi, veri mimarisi, veri
kaynakları, modeller, literatürle konum

---

## 0. Bu belge ne için

Bu belge, projeye sonradan katılan ve görüntü işleme alanına hâkim olan ortak
yazarların sistemi hızlıca kavrayıp katkı verebilmesi için hazırlanmıştır. Proje
geçmişini bilmeyi gerektirmez.

**Kanıt disiplini.** Bu belgedeki her ifade bir kanıt etiketiyle işaretlenmiştir.
Makaleye yalnızca `[Ö]` ve `[K]` etiketli ifadeler doğrudan taşınabilir.

| Etiket | Anlamı |
|---|---|
| `[Ö]` | **Ölçülmüş** — bir sonuç dosyasına dayanır; dosya yolu verilir |
| `[K]` | **Kodda** — çalışan kodda karşılığı vardır; dosya ve fonksiyon verilir |
| `[A]` | **Atıfla** — literatürden alınmıştır; kaynak verilir |
| `[T]` | **Tasarım kararı** — gerekçelendirilmiş seçim, ölçüm değil |
| `[Y]` | **Yapılmadı** — tanımlı ama henüz uygulanmamış/ölçülmemiş |

Açık eksikler ayrı bir dosyada kimlikli olarak takip edilmektedir:
`EKSIKLER_VE_SORUNLAR.md`.

---

## 1. Problem ve projenin tanımı

Afet sonrası müdahalede iki bilgi katmanı aynı anda gerekir: **nerede hasar var**
ve **oraya nasıl ulaşılır**. Yazın bu ikisini büyük ölçüde ayrı çözmüştür. Hasar
tespiti çalışmaları çıktıyı bir maskede veya sınıf etiketinde bırakır; güzergâh
çalışmaları ise kapanma bilgisini dışarıdan, çoğunlukla elle haritalanmış bir
girdi olarak alır. `[A]`

QuakeMind, bu iki katmanı tek bir karar zincirinde birleştirmeyi hedefleyen bir
karar destek platformudur: uydu görüntüsünden hasar bölütlemesi → yol çizgesi
üzerinde kapanma katmanı → kapanma-farkında güzergâh → ekip sevki. Zincire
paralel olarak vatandaş kaynaklı iki kanal (yer seviyesi görüntü ve Türkçe metin)
aynı mekânsal katmana beslenir. `[K]`

**Çalışma alanı:** 6 Şubat 2023 Kahramanmaraş depremleri (Mw 7,7 Pazarcık ve
Mw 7,6 Elbistan), Hatay ve Kahramanmaraş illeri, dokuz operasyon bölgesi.

---

## 2. Sistem mimarisi

### 2.1. Üç katman

```
VERİ EDİNME            ÇIKARIM                    KARAR
─────────────          ─────────                  ─────
uydu görüntüsü    →    anlamsal bölütleme    ┐
yer seviyesi      →    nesne tespiti         │
Türkçe metin      →    sınıflandırma + NER   ├→  ortak nesne   →  PostGIS  →  güzergâh
acil çağrı        →    (kural tabanlı)       │   (konum, skor,              →  toplanma alanı
sismik katalog    →    gradyan artırma       ┘    güven, zaman)             →  ısı haritası
                                                                            →  ekip sevki
```

Çıkarım katmanının tüm çıktıları **tek bir ortak biçime** indirgenir:
`(konum, hasar/aciliyet skoru, güven, zaman damgası)`. Bu, farklı modalitelerin
aynı mekânsal katmanda toplanmasını sağlayan tasarım kararıdır. `[T]` `[K]`

**Uygulama yüzeyi:** 38 REST uç noktası (FastAPI), 12 sayfalı web arayüzü
(Next.js), Flutter mobil istemci, her modülün bağımsız çalıştırılabildiği bir
çözümleme arayüzü. `[K]` — `backend/fastapi_app.py` (2 038 satır)

### 2.2. Bölge (zone) mimarisi — ölçeklenebilirlik kararı

Yol ağı çizgesi il ölçeğinde değil **bölge ölçeğinde** kurulur. Gerekçe ölçülmüş
bir kısıttır: 3 km yarıçaplı bir analiz alanı için OpenStreetMap tabanlı
sürülebilir yol çizgesi yaklaşık **20 000 düğüm** içermektedir. `[Ö]` İki ilin
tamamını tek çizgede tutmak bellek ve arama süresi bakımından etkileşimli
kullanıma uygun değildir.

Her operasyon bölgesi kendi çizgesini, kendi kapanma kümesini ve kendi analiz
kimliğini alır. `[K]` — `apps/road_damage/utils/network.py`

Sağladığı üç yarar: arama uzayı sınırlı kaldığı için süreler saniyeler
mertebesinde kalır; bir bölgedeki yeniden analiz diğerlerini geçersizleştirmez;
çizge önbellekleri bölge bazında saklandığı için çevrim dışı çalışma mümkündür.

**Bilinen kısıt:** bölge sınırını kesen güzergâhlar doğrudan hesaplanamaz.
Senaryodaki 18 sevkin tamamı bölge içidir. `[Y]`

### 2.3. Eşzamansız çıkarım

Tek bir 512 × 512 pencerenin işlenmesi merkezî işlem biriminde saniyeler
sürebilir; geniş yarıçaplı bir analizde yüzlerce pencere işlenir. Tek süreçli bir
sunucuda satır içi çıkarım, analiz boyunca tüm eşzamanlı istekleri bloklar — afet
anında aynı sunucudan acil çağrı, güzergâh isteği ve toplanma alanı sorgusu
gelirken bu kabul edilemez. `[T]`

Çözüm: çıkarım ayrı bir süreç havuzunda yürütülür; uç nokta HTTP 202 ve bir analiz
kimliği döndürür, istemci durum uç noktasını yoklar. `[K]` —
`POST /api/road_damage/analyze` → `GET /api/road_damage/status/{id}`

---

## 3. Veri mimarisi

### 3.1. Kapanma katmanı — zincirin dönüm noktası

Projenin yöntemsel çekirdeği, hasar bilgisinin bir **haritalama çıktısı** olmaktan
çıkıp **ulaşım kararını değiştiren bir kısıta** dönüşmesidir. İki mekanizma
kullanılır: `[K]` — `apply_risk_penalties`, `simulate_random_closures` @ `network.py`

**(a) Sert kapatma.** Bir tıkanıklık noktasının `r_h` = 25 m yarıçapındaki
kenarlar çizgeden çıkarılır. Kapatma **fiziksel yola** uygulanır: kenarın ters
yönü de aynı işlemde kapatılır. Tek yönün kapatılması, çift yönlü modellenmiş bir
yolun ters yönden kullanılabilir kalması gibi gerçekçi olmayan bir sonuç doğurur. `[T]`

**(b) Yumuşak ceza.** Artakalan her kenar, en yakın hasar noktasına uzaklığına
bağlı basamaklı bir çarpanla cezalandırılır: λ(d) = 3,0 (d < 50 m) · 1,5
(50–150 m) · 1,1 (150–400 m) · 1,0 (≥ 400 m). Basamaklı yapı tercih edilmiştir;
gerekçe, hasar noktası konumlarının metre düzeyinde belirsiz olması ve sürekli bir
çekirdeğin bu belirsizliği hak etmeyen bir çözünürlük izlenimi vermesidir. `[T]`

Güzergâh, cezalı çizge üzerinde A\* ile bulunur; sezgisel büyük çember
uzaklığıdır ve λ(d) ≥ 1 olduğundan kabul edilebilirdir. Süre hesabı **cezasız**
gerçek kenar uzunluğu üzerinden yapılır; cezalı ağırlık yalnızca güzergâh
seçiminde kullanılır. `[K]`

### 3.2. Mekânsal depo

PostGIS üzerinde altı tablo, GIST mekânsal indeksleriyle: `[K]` —
`utils/postgis_manager.py`

| Tablo | İçerik |
|---|---|
| `damage_points` | Tüm kanallardan gelen hasar noktaları (kaynak tipi, şiddet, etiket) |
| `road_blockages` | Tıkanıklık çizgileri (model çıktısı veya vatandaş bildirimi) |
| `sos_alerts` | Acil çağrılar |
| `afad_assembly_points` | Resmî toplanma alanları |
| `osm_safety_polygons` | OSM kaynaklı güvenli alan poligonları |
| `users` | Rol tabanlı kimlik (afetzede / saha ekibi / yönetici) |

`damage_points` tablosunun tasarımı önemlidir: kamera, bölütleme ve acil çağrı
kaynaklı noktalar **aynı tabloda** toplanır ve `source_type` ile ayrılır. Ekiplere
en yakın enkaz sorgusu ve yoğunluk ısı haritası bu ortak havuz üzerinden çalışır. `[K]`

### 3.3. Türetilen operasyonel ürünler

- **Kapanma-farkında güzergâh** — dört ayrı uç nokta (oturum tabanlı, PostGIS
  tabanlı oturumsuz, OSRM tabanlı, ekip hedefine) `[K]`
- **En yakın toplanma alanı + yürüyüş güzergâhı** — OSM `emergency=assembly_point`,
  resmî/aday ayrımıyla `[K]`
- **Gauss çekirdekli yoğunluk ısı haritası** — ızgara 100 × 100, bant genişliği
  0,5 km; dört kanal birlikte. Kapalı yol çizgileri bilinçli olarak dışarıda
  bırakılır: o veri güzergâh motorunun işidir, yoğunluk haritasının değil `[T]` `[K]`
- **Görev kilitleme** — bir hedefe ekip atandığında kilitlenir; ikinci istek
  HTTP 409 ile reddedilir `[K]`

---

## 4. Veri kaynakları

### 4.1. Görüntü kaynakları

| Kaynak | Tür | Çözünürlük | Lisans durumu | Kullanım |
|---|---|---|---|---|
| **Maxar Open Data** (2023 Türkiye) | WorldView-3, GeoEye-1 | 17 408² karo, ~0,3–0,4 m | Açık, yayında kullanılabilir | **Önerilen birincil kaynak** |
| **Esri World Imagery Wayback** | Sürümlü optik arşiv | z13–z18, 37°'de ~15,3–0,48 m/px | Atıf şartıyla | Deprem öncesi/sonrası karşılaştırma |
| **OpenAerialMap** | Açık havadan/İHA | Değişken, alt-metre | CC | Olay bazlı, düzensiz kapsama |
| **Google uydu karoları** | — | — | ⚠️ **Yayında kullanılamaz** | Kodda var (`fetcher.py`), makale koşumlarından çıkarılmalı |

Son satır kritik bir kısıttır: Google Earth/Maps görüntülerinin toplu indirilmesi
ve akademik yayında kullanımı izne tabidir. Dergiler görüntü kaynağı ve lisansını
sorar. Bkz. `EKSIKLER_VE_SORUNLAR.md` → **D-01**.

### 4.2. Yer gerçeği (ground truth)

**Copernicus EMS EMSR648** — 6 Şubat 2023 depremleri için üretilen resmî hasar
derecelendirme vektörleri. AOI-04 (Kahramanmaraş) ve AOI-11 (Hatay). Depoda
indirilmiş, açılmış ve JSON'a çevrilmiş durumda. `[Ö]` —
`benchmark/data/*_copernicus_ground_truth.json`

| | AOI-11 Hatay | AOI-04 K.maraş | Toplam |
|---|---|---|---|
| Toplam yol kesimi | 4 613 | 7 843 | 12 456 |
| Hasarlı yol kesimi | 73 (%1,58) | 134 (%1,71) | 207 (%1,66) |
| — Destroyed / Damaged / Possibly | 39 / 31 / 3 | 0 / 134 / 0 | 39 / 165 / 3 |
| Toplam bina | 3 689 | 4 619 | 8 308 |
| Hasarlı bina | 394 (%10,7) | 927 (%20,1) | 1 321 (%15,9) |
| — Destroyed / Damaged / Possibly | 68 / 212 / 114 | 286 / 185 / 456 | 354 / 397 / 570 |

**Metodolojik olarak en önemli gözlem:** Kahramanmaraş AOI-04'te hiç "Destroyed"
yol kesimi yoktur; 134 hasarlı kesimin tamamı "Damaged" derecesindedir. Bu, yol
hasarının binalardaki gibi tam göçme biçiminde ortaya çıkmadığını gösterir.
Dolayısıyla hasar derecesinin doğrudan geçilebilir/geçilemez ikilisine indirgenmesi
mümkün değildir ve açık bir eşleme kuralı zorunlu hâle gelir. `[Ö]`

**Benimsenen eşleme:** Destroyed → kapalı (sert kapatma) · Damaged → açık, ağırlık
cezalı · Possibly damaged → açık. Bu bir **tasarım kararıdır**, veriden okunan bir
olgu değildir; üç alternatif kural altında ayrı ayrı raporlanmalıdır. `[T]`

Aynı yer gerçeğinden, seçilen kurala göre bir ilde **134 kapanma ya da hiç
kapanma** elde edilebilmektedir. Bu, eşleme kuralının sonuç üzerindeki
belirleyiciliğini gösterir.

### 4.3. Sismik katalog

AFAD deprem kataloğu; artçı ayıklama (declustering) uygulanır, fay hattı mesafesi
ve geçmiş sismisite yoğunluğu öznitelik olarak türetilir. `[K]` —
`apps/earthquake_risk/risk_engine.py`

---

## 5. Veri setleri

### 5.1. Kullanılan

| Veri seti | Görev | Ölçek | Erişim |
|---|---|---|---|
| **KATE-CD** (`CSCRS/kate-cd`) | Bina hasarı, ikili maske | 404 görüntü–maske çifti; Maxar + Pléiades 0,3–0,5 m; 7 il | HuggingFace, açık |
| **MedBFS** (Zenodo `Turkey.zip`) | Bina hasarı, çok ölçekli | ~3,3 GB; Türkiye alt kümesi | Zenodo, açık |
| **`deprem-private/intent_test_v13_anonymized`** | Türkçe çok etiketli niyet | n_test = 305; tohum 42, %15 test, %15 doğrulama | HuggingFace, özel |
| **AFAD kataloğu** | Risk skorlama | 454 kayıt, 18 öznitelik; 29 Nisan 2022 – 4 Ekim 2024 | Açık |

### 5.2. Erişilebilir ama henüz kullanılmayan

Yol hasarı için: **CAU-RoadDamage** (alandaki tek piksel-etiketli yol hasarı
seti), DeepGlobe, Massachusetts Roads, SpaceNet-3.
Bina hasarı için: **xBD** (850 736 bina poligonu), **BRIGHT** (optik + SAR,
384 000+ bina), TUE-CD, TE23D.
Yer seviyesi için: **EIDSeg** (3 266 görüntü, 5 piksel sınıfı), EID, DSS, MEDIC,
**PEER Hub ImageNet** (36 413 görüntü–etiket çifti, 8 görev), RescueNet.
Çatlak için: **SDNET2018** (56 000+ görüntü).

### 5.3. Eksik olan

**Piksel düzeyinde yol hasarını etiketleyen Türkiye kaynaklı açık bir küme
yazında yoktur.** `[A]` Bu, projenin en belirleyici veri kısıtıdır ve çok mimarili
karşılaştırmanın neden bina hasarı görevinde yürütüldüğünü açıklar.

---

## 6. Modeller ve ölçülen sonuçlar

### 6.1. Uydudan hasar bölütlemesi

**Bizim yapılandırmamız:** SegFormer, MiT-B4 kodlayıcı, tek sınıflı ikili maske,
odaksal + Dice bileşik kaybı. Etrafındaki çıkarım mühendisliği modelin kendisi
kadar belirleyicidir: `[K]` — `apps/road_damage/utils/inference.py`

- **Örtüşmeli karolama** — 512 px pencere, 256 px adım (%50 örtüşme)
- **Ağırlıklı pencere harmanlaması** — merkeze doğru artan ağırlık; karo
  sınırlarındaki dikiş izlerini ortadan kaldırır
- **Üç seviyeli morfolojik son işleme** — seviye 1: 3×3 elips açma-kapama,
  asgari alan 30 px; seviye 2: 5×5 açma / 7×7 kapama, asgari alan 150 px
- **Yarıçapa göre otomatik yakınlaştırma** — hedef 6 karo, z ∈ [13, 18]

**Çok mimarili karşılaştırma — koşulan protokol** `[Ö]`:
Veri KATE-CD + MedBFS; 512 px karo, 256 px adım; hasarsız karoların %95'i elenir;
bölme %70/15/15, tohum 42; AdamW, lr 2 × 10⁻⁴, ağırlık sönümü 1 × 10⁻²;
CosineAnnealingWarmRestarts (T₀ = 5, T_mult = 2, η_min = 1 × 10⁻⁶); yığın 8;
en çok 50 devir, sabır 8; eşik 0,5. En iyi ağırlık geri yüklenip **ayrılmış test
kümesinde** değerlendirilir.

| Mimari (kodlayıcı) | IoU_hasar | F₁ | Kesinlik | Duyarlılık | Param (M) |
|---|---|---|---|---|---|
| LinkNet (ResNet-18) | **0,3700** | 0,5401 | 0,5046 | 0,5810 | 11,7 |
| U-Net (ResNet-18) | 0,3542 | 0,5232 | 0,5415 | 0,5060 | 14,3 |
| FPN (ResNet-18) | 0,3452 | 0,5132 | 0,5651 | 0,4700 | 13,0 |
| DeepLabV3+ (ResNet-101) | 0,3426 | 0,5103 | 0,4990 | 0,5222 | 45,7 |
| PSPNet (ResNet-18) | 0,3385 | 0,5058 | 0,5521 | 0,4667 | 11,3 |

Kaynak: `model_benchmarks/01_yol_hasari/local_colab_run/results/*.json`
(klasör adı yanıltıcıdır: deney **bina** verisiyle koşulmuştur — bkz. **D-03**)

**Üç uyarı, uzman görüşü gereken noktalar:**
1. Kodlayıcı sabitlenememiştir (beş taban ResNet, SegFormer MiT-B4). Gözlenen
   fark kodlayıcı ve kod çözücü değişimlerinin bileşkesidir. `[Y]`
2. Bölme rastgeledir ve karolama %50 örtüşmelidir; örtüşen karoların farklı
   bölmelere dağılmasından doğan **sızıntı denetlenmemiştir**. `[Y]`
3. Tek tohum, tek koşum. Mimariler arasındaki ~0,03'lük farkların varyans içinde
   kalıp kalmadığı bilinmemektedir. `[Y]`

**SegFormer satırı ayrıca sorunludur:** 0,4276 değeri farklı bir oturumda, iki
katmanlı bölmeyle ve **en iyi doğrulama** skoru olarak elde edilmiştir; ayrılmış
test kümesinde değerlendirilmemiştir. Diğer beş satırla karşılaştırılamaz.
Bkz. **A-01**.

### 6.2. Yer seviyesi hasar tespiti

İki YOLOv8 modeli: çatlak (tek sınıf, güven > 0,45 kritik) ve bina hasarı (üç
sınıf: hasarsız / orta / ağır). Güven eşiği 0,20 — bilinçli olarak duyarlılık
lehine, çünkü afet ortamında yanlış negatifin maliyeti yanlış pozitiften
yüksektir. `[T]` `[K]`

Ölçülen tek şey gecikmedir: 153,6 ms ve 173,3 ms (n = 2), güven %85,5 ve %78,8.
**mAP ölçülmemiştir.** `[Y]` — sekiz defter hazır
(`model_benchmarks/03_yer_seviyesi/`), sonuç yok.

### 6.3. Türkçe metin analizi

Üç aşamalı hat: biçimbilimsel çözümleme (Zeyrek) → BERTurk sınıflandırma
(13 alt kategori → 5 üst kategori) → varlık ismi tanıma + coğrafi kodlama.
Aciliyet kural tabanlı türetilir (1–5). `[K]`

**Sekiz model karşılaştırması** `[Ö]` — `deprem-private/intent_test_v13_anonymized`,
çok etiketli, n_test = 305, eşik 0,50:

| Model | Mikro-F₁ | Makro-F₁ | Eğitim (sn) |
|---|---|---|---|
| BERTurk (`dbmdz/bert-base-turkish-cased`) | **0,8247** | 0,4725 | 1 974 |
| TF-IDF + lojistik regresyon | 0,7598 | **0,5024** | 0,17 |
| TF-IDF + doğrusal DVM | 0,7596 | 0,4852 | 0,12 |
| ConvBERTurk | 0,7199 | 0,2747 | 2 281 |
| Çok dilli BERT | 0,6415 | 0,2282 | 2 139 |
| fastText | 0,6003 | 0,2589 | 1,08 |
| DistilBERTurk | 0,5542 | 0,1295 | 916 |
| BiLSTM + fastText | 0,5285 | 0,1533 | — |

**Bu tablonun en değerli bulgusu sıralamanın ölçüte göre tersine dönmesidir.**
0,17 saniyede eğitilen bir TF-IDF taban çizgisi, 1 974 saniye eğitilen BERTurk'ü
makro-F₁'de geçmektedir. Makro-F₁ tüm kategorilere eşit ağırlık verdiğinden bu tek
bir anlama gelir: dönüştürücü modeller **seyrek kategorilerde** klasik taban
çizgilerinden kötü başarım vermektedir. DistilBERTurk'ün 0,8035 mikro kesinlik ile
0,1295 makro-F₁ birlikteliği aynı davranışın uç örneğidir.

Bu bulgu, senaryoda gözlenen yanlış negatiflerle aynı yönü işaret etmektedir:
altı metin ihbarının ikisi "alakasız" sayılarak elenmiş, her ikisi de hayati
medikal çağrıydı. `[Ö]`

### 6.4. Risk skorlaması

CatBoost (800 yineleme, derinlik 8, öğrenme oranı 0,03); artçı ayıklama, fay
mesafesi, 30 günlük etiketleme. Nihai skor üç bileşenin ağırlıklı toplamıdır
(0,4 kısa vadeli + 0,3 uzun vadeli tehlike + 0,3 fay skoru) — ağırlıklar uzman
tanımlıdır. `[T]` `[K]`

**Yedi model karşılaştırması** `[Ö]` — n = 454, 18 öznitelik, beş katlı **ileri
yürüyen (walk-forward)** bölme, pozitif oran 0,687:

| Model | ROC-AUC | PR-AUC | Brier | MCC |
|---|---|---|---|---|
| CatBoost | **0,8465 ± 0,0935** | 0,9011 | 0,1368 | **0,4447** |
| Rastgele orman | 0,8417 ± 0,0920 | **0,9058** | **0,1318** | 0,3958 |
| XGBoost | 0,7962 ± 0,1554 | 0,8907 | 0,1374 | 0,4179 |
| Lojistik regresyon | 0,7776 ± 0,0449 | 0,8665 | 0,1511 | 0,4228 |
| Yığınlanmış topluluk | 0,7338 ± 0,2670 | 0,8729 | 0,2259 | −0,0225 |
| LightGBM | 0,7168 ± 0,2294 | 0,8767 | 0,1724 | 0,2875 |
| Çok katmanlı algılayıcı | 0,4276 ± 0,1088 | 0,7108 | 0,2288 | −0,0443 |

Dört gözlem: **(i)** PR-AUC temel oran çıkarılmadan yorumlanamaz — pozitif oran
0,687 olduğundan rastgele bir sınıflandırıcının beklenen PR-AUC'si de 0,687'dir.
**(ii)** CatBoost'un rastgele ormana üstünlüğü 0,0048'dir; kat standart sapması
≈ 0,09 olduğundan bu fark **anlamlı değildir**. **(iii)** Çok katmanlı algılayıcı
rastgele tahmin düzeyinin altındadır. **(iv)** Yığınlama 454 kayıtta
başarısızdır — mimari eleştirisi değil, örneklem yetersizliği.

### 6.5. Kapanma-farkında güzergâh ve uçtan uca senaryo

**Senaryo kurgusu:** 9 operasyon bölgesi, 18 afetzede, 18 ekip, 12 karargâh,
üç etkin veri kanalı. `[Ö]`

| Ölçüm | Değer |
|---|---|
| Görev ataması | 18/18 başarılı |
| Mükerrer sevk engelleme | 9/9 (HTTP 409) |
| Kapalı segmentten geçen güzergâh | 0/18 |
| Toplam süre — önerilen | 206,6 dk |
| Toplam süre — kapanma-bilgisiz naif ajan | 1 641,0 dk |
| Fark | 1 434,4 dk |

**Kazancın ayrıştırılması zorunludur.** Farkın 1 360,0 dakikası (%94,8) bir
**model parametresinden** gelir: naif ajanın her keşifte ödediği varsayılan
yeniden yönlenme cezası (68 keşif × 20 dk). Parametreden bağımsız bileşen
74,4 dakikadır. İki yüzde farklı paydalar üzerinden hesaplanır ve doğrudan
karşılaştırılamaz: %87,4 = 1 434,4/1 641,0 · %26,5 = 74,4/281,0.

Ceza süresine duyarlılık, yeni koşum gerektirmeden hesaplanabilir:
*t_u* = 0 → %26,5 · 5 dk → %66,7 · 20 dk → %87,4 · 30 dk → %91,1.

**"18 güzergâhın hiçbiri kapalı segmentten geçmedi" bulgusu yapısal olarak
beklenendir** ve bir başarım kanıtı değildir: sert kapatma ilgili kenarları
çizgeden çıkardığı için bu matematiksel zorunluluktur. Planlayıcının kendi
kapanma modeline iç tutarlılığını gösterir.

---

## 7. Ne yaptık, ne aldık, ne uyarladık

### 7.1. Kendi geliştirdiklerimiz

| Bileşen | Açıklama |
|---|---|
| **Kapanma katmanı üretimi** | Hasar bilgisinin çizgeye iki mekanizmayla (sert kapatma + yumuşak ceza) aktarılması; fiziksel yolun iki yönünün birlikte kapatılması |
| **Bölge mimarisi** | İl ölçeğinde hesaplanamayan çizgenin bölgelere ayrıştırılması, bölge bazlı önbellek ve analiz kimliği |
| **Örtüşmeli karolama + ağırlıklı harmanlama** | Karo sınırı dikiş izlerini ortadan kaldıran merkez-ağırlıklı birleştirme |
| **Naif ajan referansı** | Kapanma bilgisiz ajanın keşif-yeniden planlama davranışının simülasyonu ve kazancın bileşenlerine ayrıştırılması |
| **Görev kilitleme** | Eşzamanlılık denetimi; mükerrer sevkin sistem düzeyinde engellenmesi |
| **Türkçe metin hattının sevke bağlanması** | Sınıflandırma + aciliyet + NER + coğrafi kodlamanın doğrudan sevk kuyruğuna girdi üretmesi |
| **Derece–geçilebilirlik eşleme kuralı** | EMSR648 hasar derecelerinin çizge işlemlerine açık biçimde çevrilmesi |
| **Üç düzeyli değerlendirme protokolü** | Bileşen → kapanma → görev tabanlı değerlendirme |

### 7.2. Literatürden aldıklarımız (değiştirmeden)

SegFormer `[A]`, U-Net, LinkNet, FPN, PSPNet, DeepLabV3+ `[A]`, YOLOv8 `[A]`,
BERTurk `[A]`, CatBoost `[A]`, A\* ve Dijkstra `[A]`, odaksal kayıp `[A]`,
Dice kaybı `[A]`, AdamW `[A]`, OSMnx/OpenStreetMap `[A]`.

### 7.3. Uyarladıklarımız

| Ne | Kaynak | Uyarlama |
|---|---|---|
| Karo kalite filtresi (Laplacian varyansı) | EIDSeg protokolü `[A]` | Uydu karolarına uyarlanacak `[Y]` |
| Üç fazlı etiketleme protokolü | EIDSeg `[A]` | Kendi kümemiz için planlanıyor `[Y]` |
| %80/10/10 bölme | xBD `[A]` | Mekânsal blok bölmeye dönüştürülecek `[Y]` |
| Çok mimarili karşılaştırma kurgusu | Haciefendioğlu vd. `[A]` | Aynı kodlayıcı ilkesi benimsendi, henüz sağlanamadı `[Y]` |

---

## 8. Literatürle ortak noktalar ve ayrıldığımız noktalar

### 8.1. Ortak olduğumuz yerler

- **Mimari aile.** Kodlayıcı–kod çözücü bölütleme ve dönüştürücü tabanlı
  yaklaşımlar alanın standardıdır; biz de aynı aileyi kullanıyoruz.
- **Ölçüt disiplini.** Dengesiz sınıfta doğruluğun yanıltıcı olduğu, IoU ile
  birlikte raporlanması gerektiği yerleşik bir bulgudur (Haciefendioğlu vd.
  %97 doğruluk ↔ 0,39 IoU). Biz de aynı kuralı benimsiyoruz.
- **Transfer öğrenme.** Sınırlı etiketli veride ImageNet ön eğitimi alanın
  standart çözümüdür.
- **Çalışma alanı.** 6 Şubat 2023 depremleri, yazında en çok çalışılan Türkiye
  vakasıdır; TUE-CD, TE23D, KATE-CD aynı olayı kapsar.

### 8.2. Ayrıldığımız yerler

| # | Yazın ne yapıyor | Biz ne yapıyoruz |
|---|---|---|
| 1 | Hasar tespiti maskede veya sınıf etiketinde duruyor | Maskeyi yol çizgesine kapanma katmanı olarak işliyoruz |
| 2 | Bütünleşik hatlar zinciri görselleştirmede sonlandırıyor (DamageScope) | Zincire güzergâh ve kilitlemeli sevk katmanını ekliyoruz |
| 3 | Güzergâh çalışmaları kapanmayı **elle haritalanmış** veriden alıyor (openrouteservice afet sürümü, HOT OSM gönüllüleri) | Kapanmayı model çıktısından türetmeyi hedefliyoruz |
| 4 | CBS tabanlı çerçeveler elle ArcGIS analizi yapıyor (Awan vd.) | Uçtan uca otomatik zincir kuruyoruz |
| 5 | Kazanç tek bir toplu yüzde olarak bildiriliyor | Kazancı ölçülen ve varsayılan bileşenlerine ayrıştırıp ikisini birlikte raporluyoruz |
| 6 | Başarım bölütleme ölçütünde ölçülüyor | Başarımı **görev sonucu** üzerinden ölçmeyi öneriyoruz (ulaşım süresi, ulaşılamayan ihbar) |
| 7 | Türkçe afet metni çalışmaları duygu analizinde kalıyor | İhtiyaç + aciliyet + adres çıkarıp sevk edilebilir koordinata çeviriyoruz |

**Dürüst kayıt:** 3, 4 ve 6 numaralı farklar şu an **hedef** düzeyindedir, ölçülmüş
değildir. Kapanma katmanı bu sürümde sentetik üreticiden gelmektedir. Bkz. **C-01**, **B-01**.

### 8.3. Tek tek modüllerde emsallerin bizden iyi olduğu yerler

Bu kabul edilmeli ve makalede modül üstünlüğü iddia edilmemelidir:
yol hasarında SAM tabanlı yöntem piksel F₁ 0,7609 `[A]`; bina hasarı
bölütlemesinde DamageScope ortalama F₁ 0,598 `[A]`; yer seviyesi tespitte
YOLOv8 mAP 0,952 `[A]`. Bizim iddiamız **zinciri kapatmak ve ölçmek** olmalıdır.

---

## 9. Kanıt durumu özeti

| İddia | Durum | Kanıt |
|---|---|---|
| Görev orkestrasyonu eşzamanlılık güvencesi | `[Ö]` | 18/18, 9/9 — senaryo koşumu |
| Bina hasarı beş mimari karşılaştırması | `[Ö]` | `01_yol_hasari/.../results/*.json` |
| Türkçe metin sekiz model karşılaştırması | `[Ö]` | `04_turkce_metin/local_run/results/` |
| Risk yedi model karşılaştırması | `[Ö]` | `05_risk_skoru/local_run/results/` |
| EMSR648 hasar dağılımı | `[Ö]` | `benchmark/data/*_ground_truth.json` |
| Çizge ölçeği (~20 000 düğüm / 3 km) | `[Ö]` | ön inceleme |
| Kapanma-farkında güzergâh | `[K]` | `network.py` |
| PostGIS altı tablo | `[K]` | `postgis_manager.py` |
| **SegFormer'ın diğer mimarilere üstünlüğü** | `[Y]` | **karşılaştırılabilir değil — A-01** |
| Yol hasarı bölütleme başarımı | `[Y]` | veri kümesi yok — B-02 |
| YOLO mAP | `[Y]` | defterler hazır, koşulmadı — B-03 |
| Görev tabanlı değerlendirme | `[Y]` | merkezî katkı, ölçülmedi — B-01 |
| Rota kıyaslaması (R1, R2) | `[Y]` | tanımlı, koşulmadı — B-04 |
| Bölgeler arası genelleme | `[Y]` | B-06 |
| Çok kipli füzyon | `[Y]` | kodda yok — C-03 |
| BLE mesh taşıma katmanı | `[Y]` | kodda yok — C-04 |

---

## 10. Uzman ortak yazarlardan görüş beklenen noktalar

Aşağıdaki sorular görüntü işleme uzmanlığı gerektirmekte olup projenin mevcut
ekibinin tek başına karara bağlaması uygun görülmemektedir.

1. **Kodlayıcı sabitleme.** MiT kodlayıcısı dört kademeli hiyerarşik çıktı üretir,
   genişletilmiş evrişimi desteklemez ve beş kademeli kod çözücülerle doğrudan
   birleşmez; DeepLabV3+ ise çıkış adımı denetimi için genişletilmiş evrişim
   gerektirir. Adil karşılaştırma için hangi yol izlenmeli: (a) tüm mimarileri
   ResNet'te sabitleyip SegFormer'ı ayrı bir eksende sunmak, (b) MiT'i uyarlamak,
   (c) iki koşumu birlikte raporlamak?

2. **Sızıntı denetimi.** %50 örtüşmeli karolama + rastgele bölme sızıntı üretir.
   Mekânsal blok bölmesinde blok boyutu ne olmalı? 2 km × 2 km yeterli mi?

3. **Ölçüt seçimi.** Tek sınıflı ikili maskede "mIoU" tanımsızdır (arka plan
   dâhil edilirse 0,98'lik arka plan IoU'su ölçütü şişirir). IoU_hasar (ön plan
   IoU) doğru seçim mi, yoksa Dice/F₁ mi tercih edilmeli?

4. **Vektör → piksel dönüşümü.** EMSR648 yol katmanı çizgi geometrisidir. Piksel
   maskesine çevirmek için tampon genişliği seçimi gerekir ve IoU doğrudan bu
   keyfi genişliğe bağlıdır. Yol sınıfına göre nominal yarı genişlik makul mü?
   Duyarlılık hangi çarpanlarla raporlanmalı?

5. **Piksel → kenar eşiği.** Bir çizge kenarının "kapalı" sayılması için üzerine
   düşen hasar piksel oranı eşiği τ nasıl seçilmeli? Bu eşik görev sonucunu
   doğrudan belirlemektedir.

6. **Hata maliyeti asimetrisi.** Güzergâh probleminde kaçırılan kapanma (ekip
   kapalı yola girer) ile yanlış kapanma (ekip dolanır) maliyetleri asimetriktir.
   Bu, model seçiminde duyarlılığı kesinlikten öncelikli kılar mı? Eşik ayarı
   bu asimetriye göre nasıl yapılmalı?

7. **Seyrek sınıf sorunu.** Metin tarafında dönüştürücüler seyrek kategorilerde
   klasik taban çizgilerinin altında kalmaktadır (makro-F₁ 0,4725 < 0,5024).
   Görüntü tarafında benzer bir davranış bekleniyor mu? Sınıf-farkında örnekleme
   veya zor örnek madenciliği önerilir mi?

8. **Veri seti stratejisi.** Piksel etiketli Türkiye yol hasarı kümesi yok.
   Kendi kümemizi mi etiketlemeliyiz, CAU-RoadDamage'ı harici test kümesi olarak
   mı kullanmalıyız, yoksa yol eksenini gelecek çalışmaya mı bırakmalıyız?

---

## 11. İlgili belgeler

| Dosya | İçerik |
|---|---|
| `MAKALE_TASLAK_TR.md` / `.docx` | Makale taslağı (Türkçe, ulusal dergi formatı) |
| `EKSIKLER_VE_SORUNLAR.md` | Kimlikli eksik/hata takibi — 30 madde |
| `QuakeMind_makale/model_benchmarks/` | Ölçüm defterleri ve sonuçları (ayrı çalışma kopyası) |
| `backend/benchmark/reports/senaryo_v2_raporu.md` | Uçtan uca senaryo koşum raporu |
