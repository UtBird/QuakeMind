# Makale Taslağı — Birleşik Düzeltme Listesi

**İncelenen belge:** `MAKALE_TASLAK_TR (1).docx` — 481 paragraf, 23 tablo, 21 şekil,
17 denklem, 57 kaynak, 17 gömülü görsel, 18 169 kelime
**Son güncelleme:** 12 Eylül 2026
**Amaç:** Bu listedeki maddeler tamamlandığında taslak nihai düzeye ulaşır.

## Bu dosya neyin birleşimi

İki bağımsız inceleme tek listede toplanmıştır. Çakışan maddeler tekilleştirilmiş,
her maddeye tek bir kimlik (`M-01` …) verilmiştir.

| Kaynak imi | Anlamı |
|---|---|
| `[B]` | Bu oturumdaki inceleme (depo ↔ makale hizası, ölçüm eksikleri) |
| `[D]` | Diğer sohbetteki inceleme (makale iç tutarlılığı, dizgi, kaynakça) |
| `[B+D]` | İki incelemenin de bağımsız olarak bulduğu madde |

**Not.** `[D]` işaretli maddelerin **tamamı** bu oturumda belge ve depo üzerinde
tek tek doğrulanmıştır; hiçbiri olduğu gibi aktarılmamıştır. Doğrulanamayan ya da
yanlış çıkan iddialar **Bölüm 7**'de ayrıca listelenmiştir.

## Önem dereceleri

| Kod | Anlamı |
|---|---|
| 🔴 | Hakem tek başına ret gerekçesi sayabilir; gönderimden önce mutlaka çözülmeli |
| 🟠 | Gönderimden önce çözülmeli; çözülmezse ciddi revizyon isteği gelir |
| 🟡 | Makaleyi güçlendirir; eksikliği savunulabilir ama zayıflatır |
| ⚪ | Biçim, adlandırma, düzen |

---

## Genel değerlendirme

Taslak **yapısal olarak sağlam**. Doğrulanan noktalar:

- Tablo numaraları 1–23 kesintisiz, çakışma ve boşluk yok ✓
- Şekil numaraları 1–21 kesintisiz, çakışma yok ✓
- Denklem numaraları 1–17, her biri tam bir kez ✓
- Kaynakça 57 kayıt, 1–57 arası boşluksuz; **listede olup metinde anılmayan yok,
  metinde anılıp listede olmayan yok** ✓
- Tablo 21 (metin) ve Tablo 22 (risk) değerleri depodaki ölçüm dosyalarıyla
  **birebir** tutuyor ✓
- Tablo 12'nin beş taban satırı `iou_fg` değerleriyle **birebir** tutuyor ✓
- Tablo 3 (EMSR648) değerleri yer gerçeği JSON'larıyla tutuyor ✓

Kalan sorunların ağırlığı iki yerde toplanıyor: **(i)** Bölüm 3 (Yöntem), Bölüm 4'te
raporlanan koşumu tarif etmiyor — sonucu üreten üç mekanizma (sentetik kapanma
üreticisi, ekip–hedef atama kuralı, üç geçilebilirlik kuralı) yöntemde hiç
tanımlanmamış; **(ii)** 187 ölçülmemiş hücre.

### Sayılarla kalan iş

| | Adet |
|---|---|
| `[ÖLÇÜLECEK]` hücre | **187** |
| `[EKLENECEK]` alan | **8** |
| Üretilmemiş şekil | **11** (Şekil 1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13) |
| Metinde numarayla anılmayan tablo | **9** |
| Metinde numarayla anılmayan şekil | **12** |
| Yöntemde tanımsız, sonuçta kullanılan mekanizma | **3** |
| İç çelişki | **5** |
| Kip (zaman) tutarsızlığı | **3 bölüm** |
| Yazarsız kaynak | **6** |

---

# BÖLÜM 1 — YAYIN ENGELLEYİCİ

Bunlar çözülmeden makale hakeme gönderilmemelidir.

### ☐ M-01 🔴 SegFormer satırı karşılaştırılabilir değil `[B+D]`
**Nerede:** Öz · Abstract · Bölüm 4.2 (Gözlemler) · Tablo 12 son satır

Tablo 12'deki beş taban **ayrılmış test kümesinde** ölçülmüştür
(`build_notebook.py`: %70/15/15 bölme, tohum 42, en iyi ağırlık geri yüklenip
`test_loader` üzerinde değerlendirme). SegFormer'ın 0,4276 değeri ise
`optimized_training_colab.ipynb` çıktısındaki **"En iyi Val IoU"** — iki katmanlı
bölme, erken durdurmanın seçtiği devirdeki **doğrulama** skoru.

En iyi doğrulama skoru seçim yanlılığı taşır ve sistematik olarak iyimserdir;
0,3700 → 0,4276 farkı modele atfedilemez.

**Yapılacak (biri):**
- **(a) Tercih edilen:** SegFormer'ı aynı üç katmanlı bölmeyle yeniden koştur,
  test kümesi IoU_hasar değerini raporla. Defter ve veri mevcut.
- **(b) Geçici:** Tablo 12'deki hücreyi `[KARŞILAŞTIRILAMAZ]` yap, satırı tablodan
  ayırıp dipnota taşı.

### ☐ M-02 🔴 Öz ve Abstract M-01'in kaydını taşımıyor `[B]`
**Nerede:** Öz, "en yüksek hasar sınıfı IoU değeri 0,4276 ile SegFormer
yapılandırmasında elde edilmiştir" · Abstract, "the highest damage-class IoU
(0.4276) obtained by the SegFormer configuration"

Gövdede (Bölüm 4.2 dipnotu ve sapma listesi) kayıt var, Öz'de yok. Hakem Öz ile
gövde arasındaki bu farkı "üstü örtülü iddia" olarak nitelendirir.

**Yapılacak.** M-01 çözülene kadar iddiayı Öz ve Abstract'tan çıkar. Önerilen metin:
> "Kıyaslama mimarileri arasında en yüksek hasar sınıfı IoU değeri LinkNet ile
> elde edilmiştir (0,3700); esas alınan yapılandırmanın aynı protokolde
> değerlendirilmesi sürmektedir."

İngilizcesi:
> "Among the comparison architectures, the highest damage-class IoU was obtained
> by LinkNet (0.3700); evaluation of the adopted configuration under the identical
> protocol is ongoing."

### ☐ M-03 🟠 Bölüm 4.2 iddiayı önce olgu olarak kuruyor `[B]`
**Nerede:** Bölüm 4.2, "Gözlemler" paragrafı

Mevcut sıra: *"Esas alınan SegFormer yapılandırması 0,4276 ile beş kıyaslama
mimarisinin tümünün üzerindedir. Ancak bu fark bir mimari üstünlüğü kanıtı olarak
sunulamaz…"* — olumlu iddia önce, kayıt sonra. Alıntılanan cümle ilki olur.

**Yapılacak.** Sırayı ters çevir. Önerilen:
> "Esas alınan SegFormer yapılandırması ayrı bir oturumda ve iki katmanlı bölmeyle
> eğitildiğinden, elde edilen 0,4276 değeri bir doğrulama skorudur ve beş
> kıyaslama mimarisinin test kümesi değerleriyle aynı ölçekte değildir; bu nedenle
> tabloda karşılaştırma dışı tutulmuştur."

### ☐ M-04 🔴 Sentetik kapanma üreticisi Bölüm 3'te hiç tanımlanmamış `[D]`
**Nerede:** Bölüm 3 (tamamı) ↔ Bölüm 4.5, 4.6

**Ölçüm:** `sentetik` sözcüğü Bölüm 3'te (5 788 kelime, satır 62–301) **sıfır kez**
geçiyor; makalenin tamamında 13 kez geçiyor — hepsi Bölüm 4 ve 5'te.

Makalenin manşet sonucu (206,6 dk ↔ 1 641,0 dk) sentetik olarak üretilmiş bir
kapanma kümesi üzerinde elde edilmiştir. Bu kümenin **nasıl üretildiği hiçbir
yerde yazmıyor**: kaç kapanma, hangi olasılık dağılımı, hangi uzamsal kural,
hangi tohum, yol sınıfına göre ağırlıklandırma var mı. Yöntem bölümü yalnızca
gerçek kapanma katmanını (bölütleme → çizge) tarif ediyor; oysa raporlanan koşum
o katmanı kullanmıyor.

Bu, tek başına yeniden üretilebilirlik ret gerekçesidir: hakem sonucu üreten
girdinin tanımını bulamaz.

**Yapılacak.** Bölüm 3'e yeni bir alt bölüm (**3.10. Sentetik Kapanma Üretimi**)
ekle ve şunları yaz: üretici algoritma, kapanma sayısı ve yol ağına oranı,
uzamsal seçim kuralı (rastgele mi, yol sınıfına göre ağırlıklı mı, kümelenmiş mi),
rastgelelik tohumu, EMSR648 oranlarıyla (%1,58 / %1,71) nasıl kalibre edildiği.
Kod: `backend/benchmark/` altındaki senaryo üreticisi referans verilmeli.

### ☐ M-05 🔴 Ekip–hedef atama kuralı tanımsız `[D]`
**Nerede:** Bölüm 3.9 (102 kelime) ↔ Bölüm 4.5

**Ölçüm:** Bölüm 3.9 "Görev Orkestrasyonu ve Çakışma Önleme" toplam **102
kelimedir** ve yalnızca **kilitlemeyi** tarif eder: hedef kilitlenir, ikinci istek
HTTP 409 ile reddedilir, üç rollü yetkilendirme. Bölüm kendi sınırını da dürüstçe
yazıyor: *"hedef kilitleme bir eşzamanlılık denetimidir, bir atama eniyilemesi
değildir."*

Ancak 206,6 dakikalık toplam süre **tamamen** atama kararına bağlıdır: hangi ekip
hangi ihbara gider, sıra neye göre belirlenir (aciliyet mi, mesafe mi, ikisinin
bileşimi mi), bir ekip görevi bitirince sonraki hedefi nasıl seçer. Bu kural
yazılmadan senaryo yeniden üretilemez ve "kapanma-farkındalığın kazancı" ile
"atama kuralının kazancı" birbirinden ayrılamaz.

**Yapılacak.** Bölüm 3.9'u genişlet: atama yordamını sözde kod ya da açık kuralla
yaz (**Algoritma 2** olarak numaralandırılabilir). En az şunlar: hedef sıralama
ölçütü, eşitlik bozma kuralı, ekip başına eşzamanlı görev sayısı, görev
tamamlandıktan sonraki yeniden atama. Naif referansın (R0) aynı atama kuralını
kullanıp kullanmadığı **açıkça** belirtilmeli — kullanmıyorsa karşılaştırma
adil değildir.

### ☐ M-06 🔴 İç çelişki — artçı ayıklaması yapıldı mı yapılmadı mı? `[B+D]`
**Nerede:** Bölüm 3.7 ↔ Bölüm 4.11 (son paragraf)

- **Bölüm 3.7:** *"Katalog verisi üzerinde önce kümelenmeden arındırma
  uygulanarak artçı sarsıntılar ayıklanır."* → yapıldı
- **Bölüm 4.11:** *"(ii) katalogda artçı ayıklaması (declustering) yapılmamıştır,
  dolayısıyla ana şok–artçı dizilerinin zamansal özilintisi başarımı iyimser yönde
  sapmaya uğratıyor olabilir."* → yapılmadı

İkisi aynı anda doğru olamaz. Hakem bu çelişkiyi bulduğunda Tablo 22'nin tüm
değerleri sorgulanır.

**Yapılacak.** Koşulan kodu kontrol et
(`model_benchmarks/05_risk_skoru/local_run/run_all_risk.py`), hangisinin doğru
olduğunu belirle ve diğer bölümü düzelt. Yapılmadıysa Bölüm 3.7'yi
"uygulanacaktır" olarak değiştir.

### ☐ M-07 🔴 Tek etiketli ↔ çok etiketli çelişkisi ve iki farklı eşik `[D]`
**Nerede:** Bölüm 3.6 ↔ Bölüm 4.10 ↔ Tablo 21

Yöntem ve sonuç iki farklı görev tanımlıyor:

| | Bölüm 3.6 (Yöntem) | Bölüm 4.10 (Sonuç) |
|---|---|---|
| Etiket uzayı | *"ihbarı 13 alt kategoriden **birine** atar"* → tek etiketli | *"bir ihbar **birden çok** etiket taşıyabilmekte"* → çok etiketli |
| Karar eşiği | 0,30 (altındaysa "belirsiz" kuyruğu) | 0,50 (sabit) |

Tablo 21'in başlığı da *"n_sınama = 305, çok etiketli, eşik 0,50"* diyor. Yani
raporlanan tüm metin başarımı çok etiketli kurguya aittir; yöntem bölümü ise tek
etiketli bir sınıflandırıcı tarif etmektedir. Mikro-F₁, makro-F₁ ve kesinlik
değerlerinin anlamı iki kurguda farklıdır.

**Yapılacak.** Bölüm 3.6'yı fiilen koşulan kurguya göre yeniden yaz: çok etiketli
sigmoid çıkış, etiket başına bağımsız karar, eşik 0,50. 0,30'luk eşiğin **ne için**
kullanıldığını ayrıca açıkla (muhtemelen "belirsiz" kuyruğu için ikinci bir alt
eşik) — iki eşik aynı paragrafta tanımlanmalı, aksi hâlde tutarsız görünüyor.

### ☐ M-08 🔴 Üç geçilebilirlik kuralı Bölüm 3'te yok, üstelik atıf yanlış `[D]`
**Nerede:** Bölüm 4.3 ↔ Bölüm 3.2

**Ölçüm:** `Katı kural`, `Dengeli kural` ve `Gevşek kural` ifadelerinin her biri
makalenin tamamında **tam bir kez** geçiyor — üçü de Bölüm 4'te. Bölüm 3'te
**sıfır** kez geçiyorlar.

Buna karşın Bölüm 4.3 *"Bölüm 3.2'de tanımlanan üç kural"* diye atıf yapıyor.
Bölüm 3.2 "Çalışma Alanı ve Veri Kaynakları" bölümüdür ve böyle bir tanım
içermez. Bu hem **eksik yöntem** hem **yanlış çapraz başvuru**.

Tablo 19 (geçilebilirlik duyarlılığı) bu üç kural üzerine kuruludur; kurallar
tanımsız olduğu için tablo okunamaz durumdadır.

**Yapılacak.** Bölüm 3.8'e (ya da yeni 3.10'a) üç kuralın tanımını ekle —
hasar derecesi → geçilebilirlik eşlemesi tablo hâlinde:

| Kural | Destroyed | Damaged | Possibly damaged |
|---|---|---|---|
| Katı | kapalı | kapalı | ceza |
| Dengeli | kapalı | ceza | açık |
| Gevşek | kapalı | açık | açık |

*(Yukarıdaki eşleme öneridir; koşulan koddan doğrulanmalıdır.)* Ardından Bölüm
4.3'teki atfı doğru bölüm numarasına düzelt.

### ☐ M-09 🟠 Vaat edilen iki naif risk tabanı Tablo 22'de yok `[B+D]`
**Nerede:** Bölüm 3.7 ↔ Tablo 22

Bölüm 3.7: *"Karşılaştırma tabanı olarak lojistik regresyon, rastgele orman ve
XGBoost'un yanı sıra **iki naif taban** da koşulacaktır: yalnızca fay mesafesine
dayalı sıralama ve yalnızca geçmiş sismisite yoğunluğuna dayalı sıralama."*

Tablo 22'de bu iki taban **yok**. Naif tabanlar, PR-AUC'nin temel oranla
karşılaştırılması argümanının tamamlayıcısıdır; yoklukları Bölüm 4.11'in birinci
gözlemini zayıflatır.

**Yapılacak.** İki tabanı koştur ve Tablo 22'ye ekle (her ikisi de tek öznitelikli
sıralama, dakikalar sürer), ya da Bölüm 3.7'deki vaadi kaldır.

### ☐ M-10 🔴 On yedi denklemin tamamı Word'de ham LaTeX olarak duruyor `[D]`
**Nerede:** Belgenin tamamı

**Ölçüm** (`word/document.xml` üzerinde doğrudan sayım):

| Aranan | Adet | Anlamı |
|---|---|---|
| `<m:oMath>` | **0** | Hiç Word denklem nesnesi yok |
| `w:val="subscript"` | **0** | Hiç gerçek alt simge yok |
| `w:val="superscript"` | **0** | Hiç gerçek üst simge yok |
| `\tag{` | 17 | 17 denklemin numarası ham LaTeX |
| `\frac` | 12 | Kesirler ham |
| `\begin{cases}` | 1 | λ(d) tanımı ham |
| `\left` | 4 | Parantezler ham |

Yani okuyucu Denklem (9) yerine şunu görüyor:

```
\lambda(d) = \begin{cases} 3{,}0 & d < 50\ \text{m} \\ ... \end{cases} \tag{9}
```

Hiçbir dergi bu hâliyle kabul etmez; hoca da okuyamaz.

**Yapılacak.** `.docx` dosyasını `MAKALE_TASLAK_TR.md`'den **`md2docx.py`
dönüştürücüsüyle** yeniden üret — bu betik LaTeX'i gerçek Word alt/üst simge
biçimlendirmesine çevirir (`font.subscript` / `font.superscript`, Cambria Math).
**Ön koşul:** Word üzerinde yapılmış içerik değişiklikleri önce `.md` dosyasına
işlenmeli, yoksa geri gider.

**Not.** Dergi "denklem editörü kullanın" şartı koyarsa bir adım daha gerekir:
denklemlerin Word denklem nesnesine (`<m:oMath>`) dönüştürülmesi. Bu, Word'de
her denklemi seçip **Alt + =** ile dönüştürmekle elle de yapılabilir (17 denklem).

---

# BÖLÜM 2 — YÖNTEM VE İÇ TUTARLILIK

### ☐ M-11 🟠 Model seçimi ortalama IoU ile yapılmış — makale ortalama IoU'yu eleştiriyor `[D]`
**Nerede:** `build_notebook.py` satır 278 ↔ Bölüm 4.2

Makale, arka plan baskınlığı nedeniyle ortalama IoU'nun yanıltıcı olduğunu
savunuyor ve bu yüzden IoU_hasar'ı esas ölçüt olarak seçiyor. Ancak koşulan kod:

```python
if val_metrics['mean_iou'] > best_val_iou:
    best_val_iou = val_metrics['mean_iou']; epochs_no_improve = 0
```

Yani **saklanan en iyi ağırlık ve erken durdurma kararı ortalama IoU üzerinden**
verilmiştir. Raporlanan test ölçütü IoU_hasar olsa da, o ölçütü üreten model
başka bir ölçüte göre seçilmiştir. Hakem bu noktayı ölçüt tartışmasının
inandırıcılığına karşı kullanır.

**Yapılacak (biri):**
- **(a)** Erken durdurmayı `iou_fg` üzerinden yapıp beş mimariyi yeniden koştur
  (aynı koşumda M-01 de kapatılabilir).
- **(b)** Bölüm 4.2'ye açık bir cümle ekle: *"Model seçimi ortalama IoU üzerinden
  yapılmış, raporlama ise IoU_hasar üzerinden verilmiştir; bu seçim tüm
  mimariler için aynı olduğundan karşılaştırmayı yanlı kılmaz, ancak mutlak
  IoU_hasar değerleri ölçüt-uyumlu bir seçimle elde edilebilecek olandan düşük
  olabilir."*

### ☐ M-12 🟠 Yakınlaştırma düzeyi seçiminde üç hata `[D]`
**Nerede:** Bölüm 3.3

Metin: *"yakınlaştırma düzeyi z, hedef karo sayısı altı olacak biçimde ve
z ∈ [13, 18] aralığında otomatik seçilmektedir."*

Üç sorun:

1. **Enlem düzeltmesi yok.** Web Mercator'da yer çözünürlüğü
   `156543,03 · cos φ / 2^z` m/piksel'dir. Hatay ≈ 36,2° K için `cos φ ≈ 0,807`;
   düzeltme uygulanmazsa hesaplanan alan gerçekte kapsanandan **%24 büyük**
   görünür. Formül metinde hiç verilmemiş.
2. **İki farklı "karo" karışmış.** Sağlayıcının döndürdüğü harita karosu
   256 × 256 (ya da 512 × 512) pikseldir; modelin işlediği karo 512 × 512'dir.
   "Hedef karo sayısı altı" hangisine ait belirsiz.
3. **"Altı" muhtemelen bir kenardaki sayı.** Altı karolu bir mozaik 6 × 6 = **36**
   karo demektir. Metin toplam sayı izlenimi veriyor; çıkarım süresi tahmini buna
   göre altı kat yanlış olur.

**Yapılacak.** Bölüm 3.3'e açık formülü yaz (enlem düzeltmesiyle birlikte),
"harita karosu" ile "model karosu" terimlerini ayır, altı sayısının kenar başına
mı toplam mı olduğunu netleştir ve bir sayısal örnek ver (ör. *r* = 2 km, φ = 36,2° →
z = ?, kaç karo, kaç piksel).

### ☐ M-13 🟡 λ(d)'nin ilk basamağı sert kapatma yarıçapıyla örtüşüyor `[D]`
**Nerede:** Bölüm 3.8, Denklem (9)

Sert kapatma: *"kenar geometrisine en kısa dik uzaklığı r_h = 25 m'den küçük olan
tüm kenarlar çizgeden çıkarılır."*
Yumuşak ceza: `λ(d) = 3,0` için `d < 50 m`.

25 m'den yakın kenarlar zaten çizgeden çıkarıldığı için `λ = 3,0` basamağı
fiilen yalnızca **25 ≤ d < 50 m** bandında çalışır. Metin bunu söylemiyor; okuyucu
0–50 m bandının cezalandırıldığını sanıyor. Denklemin yazıldığı gibi okunması
sert kapatmayla çelişiyor.

**Yapılacak.** Denklem (9)'un altına bir cümle: *"İlk basamağın etkin aralığı
r_h = 25 m ≤ d < 50 m'dir; d < r_h olan kenarlar sert kapatma ile zaten
çizgeden çıkarılmıştır."* Alternatif olarak basamak sınırını 25 m'den başlat.

### ☐ M-14 🟡 Kenar orta noktası ölçütü bir yerde reddedilip başka yerde kullanılıyor `[D]`
**Nerede:** Bölüm 5 (sınırlılıklar) ↔ Tablo 4 / Bölüm 3.8

- **Sınırlılıklar:** *"Uzaklık ölçütünün kenar orta noktası yerine kenar geometrisi
  üzerinden tanımlanması gereklidir… orta nokta ölçütü, kenarın bir ucunda
  gerçekleşen bir kapanmayı sistematik olarak kaçırmaktadır."*
- **Yöntem (Tablo 4 notu):** *"'Damaged' derecesine karşılık gelen ceza, ilgili
  kesimin **orta noktası** hasar noktası kabul edilerek Denklem (9) üzerinden
  uygulanır."*

Yani makale, kendi eleştirdiği ölçütü yöntemin içinde kullanmaya devam ediyor.
Bu savunulabilir bir tasarım kararıdır ama **çelişki gibi okunuyor** çünkü iki
yerde bağlantı kurulmamış.

**Yapılacak.** Tablo 4 notuna açık bir gerekçe ekle: *"Bu sürümde 'Damaged'
cezası, hesap yükü nedeniyle kesim orta noktası üzerinden uygulanmıştır; ölçütün
kenar geometrisine taşınması Bölüm 5'te sınırlılık olarak kaydedilmiştir."*
Sert kapatmanın zaten kenar geometrisi kullandığını da belirt — asimetri
kasıtlıdır ve bunu söylemek gerekir.

### ☐ M-15 🟠 Kip (zaman) tutarsızlıkları `[B]`
Yapılmış işler gelecek zamanla anlatılıyor. Hakem bunu "yapılmamış deneyin
yapılmış gibi" ya da tersi olarak okur.

| Nerede | Mevcut | Olması gereken |
|---|---|---|
| Bölüm 3.4 | "…kullanılacaktır" (kayıp fonksiyonu) | "…kullanılmıştır" |
| Bölüm 3.4 | "…sabit tutulacaktır" (bileşim ağırlıkları) | "…sabit tutulmuştur" |
| Bölüm 3.4 | "…Bölüm 4.1.2'de raporlanacaktır" | "…Bölüm 4.1.2'de verilmektedir" |
| Bölüm 3.7 | "…koşulacaktır" (kıyas tabanları) | "…koşulmuştur" (Tablo 22 mevcut) |
| Bölüm 3.7 | "Bu karşılaştırma ve olasılık kalibrasyonu henüz yapılmamıştır" | Karşılaştırma **yapılmıştır** (Tablo 22); yalnızca kalibrasyon yapılmamıştır |

### ☐ M-16 🟠 Bölüm 4.1.1 kendisiyle çelişiyor `[D]`
**Nerede:** Bölüm 4.1.1, Tablo 11 öncesi

Metin: *"Senaryo koşum ortamına ait alanlar hâlihazırda bilinmekte olup nihai
metinde doldurulacaktır; eğitim ortamına ait alanlar **Bölüm 4.2'deki karşılaştırma
yürütüldükten sonra** raporlanacaktır."*

Bölüm 4.2'deki karşılaştırma **zaten yürütülmüştür** — Tablo 12 dolu, beş
mimarinin sonuçları depoda. Dolayısıyla cümle, aynı makalenin bir sonraki
bölümünde sunduğu sonucu "henüz yapılmamış" saymaktadır.

**Yapılacak.** Cümleyi kaldır ve Tablo 11'in eğitim ortamı alanlarını doldur:
koşum Colab üzerinde yapıldıysa GPU modeli, RAM, sürücü ve kütüphane sürümleri
`local_colab_run` çıktılarından okunabilir.

### ☐ M-17 🟡 Bölüm 3.6'daki "belirsiz" durumu — kodda mı, kâğıtta mı? `[B]`
**Nerede:** Bölüm 3.6, ikinci aşama

Metin, düşük güvenli kayıtların "belirsiz" durumuna alınıp operatör kuyruğuna
düşürüldüğünü **şimdiki zamanla** anlatıyor. Ancak aynı paragraf bunun "bu sürümde
yapılan bir tasarım değişikliği" olduğunu söylüyor — bu ifade, değişikliğin
**makalede mi kodda mı** yapıldığını belirsiz bırakıyor.

**Yapılacak.** Kodda uygulanmışsa dosya/fonksiyon adını belirt. Uygulanmamışsa
kipi gelecek zamana çevir ve Bölüm 5.3'e bir sınırlılık maddesi ekle.

### ☐ M-18 🟡 Tablo 12'nin ortalama IoU değerleri metinde, sütunda değil `[B]`
**Nerede:** Bölüm 4.2, Tablo 12 sonrası paragraf

LinkNet 0,6752; U-Net 0,6680; FPN 0,6638; DeepLabV3+ 0,6614; PSPNet 0,6603
değerleri düz metinde veriliyor. Gerekçe doğru (arka plan baskınlığı) ama beş
sayının metne gömülmesi okunurluğu düşürüyor.

**Yapılacak.** Tabloya "Ortalama IoU (yardımcı)" sütunu ekle, dipnotla uyarıyı
koru. **Uyarı:** SegFormer hücresi bu sütunda da boş kalmalı — 0,4276 ortalama
IoU değil, doğrulama ön plan IoU'sudur.

### ☐ M-19 ⚪ Bölüm 4.10'daki "Tablo 23" atfı dolaylı `[B]`
**Nerede:** Bölüm 4.10, kısıtlar paragrafı — *"dolayısıyla Tablo 23'te hedeflenen
ölçüm bu tabloyla karşılanmamaktadır"*

Atıf doğru görünüyor ancak okuyucu için dolaylı.

**Yapılacak.** Açık yaz: "…beş üst kategori üzerindeki ölçüm (Tablo 23, üçüncü
satır) bu tabloyla karşılanmamaktadır."

---

# BÖLÜM 3 — ÖLÇÜM EKSİKLERİ

187 `[ÖLÇÜLECEK]` hücre. Tablo bazında döküm:

### ☐ M-20 🔴 Tablo 18 — Görev tabanlı değerlendirme `[B]`
**Eksik:** neredeyse tamamı (8 satır × 8 sütun)

**Makalenin merkezî katkı iddiası budur.** Bölütleme kalitesinin operasyonel
sonuca etkisi ölçülmeden "katkı" olarak savunulması zordur.
**Ön koşul:** kapanma katmanının model çıkarımından türetilmesi (M-23).

### ☐ M-21 🟠 Tablo 5 — Etiketli yol hasarı eğitim kümesi künyesi `[B]`
**Eksik:** kaynak görüntü ve sürüm · toplam karo sayısı · hasarlı piksel oranı ·
etiketleyici sayısı · etiketleyiciler arası uyum · uzman doğrulaması (6 alan)

Bu tablo doldurulmadan Bölüm 4.2'deki karşılaştırma yol eksenine taşınamaz.
**Ön koşul:** yol hasarı için piksel etiketli küme oluşturulması.

**Karar gerekiyor:** (a) kendi kümemizi etiketle · (b) CAU-RoadDamage'ı harici
test kümesi olarak kullan · (c) yol eksenini açıkça gelecek çalışmaya bırak.

### ☐ M-22 🟠 Tablo 11 — Donanım ve `v_ort` `[B+D]`
**Eksik:** Senaryo koşum ortamı 5 alan (`[EKLENECEK]`) + eğitim ortamı 5 alan
(`[ÖLÇÜLECEK]`) + ortalama hız `v_ort`

Senaryo koşum ortamı **bugün bilinmektedir**, hemen doldurulabilir. `v_ort` süre
hesabının temel parametresidir ve makalenin hiçbir yerinde sayısal değeri yoktur —
bu, 206,6 dk / 1 641,0 dk sonuçlarının yeniden üretilmesini imkânsız kılar.
Ayrıca bkz. M-16.

### ☐ M-23 🔴 Tablo 13 — Kapanma katmanının yer gerçeğine göre değerlendirilmesi `[B]`
**Eksik:** tablo tamamen boş (6 model × 6 sütun = 36 hücre)

**Ön koşul:** vektör→piksel tampon kuralı ve τ eşiğinin uygulanması.
Bu iş aynı anda M-20'yi ve sentetik kapanma bağımlılığını (M-04) da hafifletir.

### ☐ M-24 🟡 Tablo 14 — Bölgeler arası genelleme `[B]`
**Eksik:** tablo tamamen boş (6 satır × 5 sütun)

Yeni veri gerektirmez; yalnızca bölmenin coğrafi yapılması yeterlidir.

### ☐ M-25 🟠 Tablo 16 — R1 ve R2 ara referansları `[B]`
**Eksik:** iki satır tamamen boş

Bu, kazanç iddiasının en zayıf noktasını kapatan ölçümdür: R0 tek başına
"straw man" olarak okunur. Özellikle **R2 (bilgi paylaşan filo)** gerçek
operasyonel tabana en yakın referanstır.

### ☐ M-26 🟠 Tablo 19 — Geçilebilirlik kuralı duyarlılığı `[B]`
**Eksik:** operasyonel sütunlar (ortalama ulaşım süresi, ulaşılamayan ihbar) —
12 hücre. Kapalı kesim sayıları ve oranları **doldurulmuş** ✓
**Ön koşul:** M-08 (kuralların tanımlanması) — tanımsız kural duyarlılık
analizini okunmaz kılıyor.

### ☐ M-27 🟡 Tablo 20 — Bileşen çıkarma ve parametre duyarlılığı `[B]`
**Eksik:** tablo tamamen boş (7 eksen)

Yedi eksenin tamamı elle seçilmiş parametrelerdir; hiçbirinin sonuca duyarlılığı
gösterilmemiştir. `r_h`, λ(d) basamakları ve morfoloji seviyesi öncelikli.

### ☐ M-28 🟡 Tablo 12 — GFLOPs ve çıkarım süresi `[B]`
**Eksik:** altı mimarinin tamamı için iki sütun (12 hücre)

Mobil ve uç cihaz argümanı bunlarsız savunulamaz. `seg_common.py` içinde
`efficiency_stats` fonksiyonu mevcut; yeniden eğitim gerektirmez.

### ☐ M-29 🟡 Tablo 15 — Acil çağrı satırı `[B]`
**Eksik:** gecikme hücresi

**Not:** Aynı satırın not sütununda "Model çıkarımı içermez" yazıyor. Model yoksa
gecikme ölçümü ne anlama geliyor? Ya uç nokta yanıt süresi olarak tanımla ya
hücreyi "—" yap.

### ☐ M-30 🟡 Gecikme ölçümleri n = 2 `[B]`
**Nerede:** Tablo 15, Bölüm 4.5

YOLOv8 için iki gözlem, BERTurk için iki gözlem. Isınma sonrası **en az 100
tekrarla** medyan / p95 / p99 / standart sapma ölçülmelidir. BERTurk'ün
11 419,4 ms'si bileşenlerine ayrıştırılmalıdır (ısınma · biçimbilimsel çözümleme ·
ileri geçiş · varlık ismi tanıma · coğrafi kodlama ağ gecikmesi).

### ☐ M-31 🟠 18 eşleştirilmiş görev için istatistiksel test `[B]`
**Nerede:** Bölüm 4.6 son paragrafı

Sadece toplamlar veriliyor. 352,5 dakikalık uç değer dağılımın ağır kuyruklu
olduğunu gösteriyor. Eklenecekler: görev başına fark tablosu, medyan fark,
çeyrekler arası açıklık, Wilcoxon işaretli sıra testi *p* değeri, Cliff's delta
etki büyüklüğü. **Yeni koşum gerektirmez**, mevcut 18 gözlemden hesaplanır.

### ☐ M-32 🟡 Bölüm 3.3 — Kalite filtresi eşiği ve elenen karo oranı `[B]`
**Eksik:** `V₀` eşik değeri ve elenen karo oranı

Modül bu sürümde uygulanmamıştır (makalede açıkça yazıyor). Uygulanırsa iki değer
de ölçülebilir; uygulanmayacaksa bölüm gelecek çalışmaya taşınmalıdır.

### ☐ M-33 🟠 Türkçe metin veri kümesinin kaynağı makalede hiç geçmiyor `[D]`
**Nerede:** Bölüm 3.6 · Bölüm 4.10 · Veri Erişilebilirliği

**Ölçüm:** `intent_test`, `deprem-private` ve `anonymized` sözcükleri makalede
**sıfır kez** geçiyor. `etiketleyici` üç kez geçiyor ama hepsi Tablo 5'in
(yol hasarı) boş hücrelerinde.

Tablo 21'de sekiz modelin karşılaştırıldığı 305 kayıtlık sınama kümesinin
**nereden geldiği, nasıl etiketlendiği ve erişilebilir olup olmadığı** yazılmamış.
Çok etiketli bir kümede etiketleme yönergesi ve etiketleyiciler arası uyum
olmadan makro-F₁ tartışması yorumlanamaz.

**Yapılacak.** Bölüm 3.6'ya kümenin künyesi için bir tablo ekle: kaynak
(`deprem-private/intent_test_v13_anonymized`), toplam kayıt, eğitim/sınama bölmesi,
kategori dağılımı, etiketleyici sayısı, etiketleme yönergesi, anonimleştirme
yöntemi, erişim koşulu. Erişim kapalıysa Veri Erişilebilirliği beyanında açıkça
belirt (bkz. M-47).

### ☐ M-34 ⚪ Tablo 21'de BiLSTM eğitim süresi boş `[D]`
Satır: `Çift yönlü UKSB + fastText | 0,5285 | 0,1533 | 0,5666 | 0,4852 | 0,6690 | 0,4368 | —`

Diğer yedi modelin eğitim süresi dolu. Ya ölç ya da "—" için dipnot düş
(ör. "ölçüm kaydı alınmamıştır").

---

# BÖLÜM 4 — KAYNAKÇA

### ☐ M-35 🟠 Altı kaynak yazarsız `[D]`
**Kaynaklar:** [23], [24], [25], [29], [31], [57]

Bu altı kayıt doğrudan tırnak içinde başlıkla başlıyor, yazar alanı yok. Örnek:

> [23] "Vector-guided post-earthquake damaged road extraction using diffusion-augmented
> remote sensing imagery", *Remote Sensing*, 18 (4): 613, (2026).

[57] ve [56] zaten `[KÜNYE DOĞRULANACAK]` notu taşıyor; diğer dördünde not bile
yok. Hiçbir dergi yazarsız kaynak kabul etmez; ayrıca hakem "bu kaynaklar
gerçekten okundu mu?" sorusunu sorar.

**Yapılacak.** Altı kaydın yazar listelerini DOI üzerinden tamamla. Aynı geçişte
[56] KATE-CD künyesini de doğrula (varsa eşlik eden makaleyi ekle).

### ☐ M-36 🟠 ConvBERTurk ve DistilBERTurk için yanlış kaynak gösterilmiş `[D]`
**Nerede:** Bölüm 4.10, model listesi

Metin: *"…dört önceden eğitilmiş dönüştürücü (BERTurk [32], DistilBERTurk [52],
ConvBERTurk [51]…)"*

Ancak:
- **[51]** = Jiang, Z. ve ark., *"ConvBERT: Improving BERT with span-based dynamic
  convolution"*, NeurIPS 2020 → **mimari** makalesi, Türkçe model değil.
- **[52]** = Sanh, V. ve ark., *"DistilBERT, a distilled version of BERT"*,
  arXiv:1910.01108 → **yöntem** makalesi, Türkçe model değil.

ConvBERTurk ve DistilBERTurk, Stefan Schweter'in Türkçe önceden eğitilmiş
modelleridir — yani **[32]** ile aynı kaynağa aittir. Şu anki hâliyle makale,
kullandığı ağırlıkların kaynağını yanlış göstermektedir.

**Yapılacak.** İki seçenekten biri:
- **(a)** Her iki modeli de [32]'ye atıfla ver, mimari kaynaklarını ikincil
  olarak belirt: *"DistilBERTurk [32] (damıtma yöntemi [52]), ConvBERTurk [32]
  (mimari [51])"*.
- **(b)** Schweter'in model kartlarına ayrı birer kaynak ekle
  (`dbmdz/distilbert-base-turkish-cased`, `dbmdz/convbert-base-turkish-cased`).

### ☐ M-37 🟡 [1] hem AFAD raporu hem deprem kataloğu kaynağı olarak kullanılıyor `[D]`
[1] = AFAD *Ön Değerlendirme Raporu* (2023). Bu bir olay raporudur; Bölüm 3.7'de
risk modelinin eğitildiği **deprem kataloğu** için de aynı numara kullanılıyor.
İkisi farklı veri ürünleridir.

**Yapılacak.** Katalog için ayrı bir kaynak ekle (AFAD Deprem Kataloğu / TDVMS,
erişim tarihi ve sorgu aralığıyla birlikte). Tablo 2'deki satırla tutarlı olmalı.

### ☐ M-38 ⚪ [56] ve [57] künye doğrulaması `[B]`
İki kayıt `[KÜNYE DOĞRULANACAK]` notu taşıyor. M-35 ile aynı geçişte kapatılmalı.

---

# BÖLÜM 5 — BİÇİM VE DERGİ KURALLARI

### ☐ M-39 🟠 Dokuz tablo metinde numarayla anılmıyor `[B]`
**Anılmayanlar:** Tablo 7, 11, 13, 14, 15, 16, 19, 21, 22

Hemen her dergi "her tablo metinde numarasıyla anılmalıdır" kuralını biçim
denetiminde uygular. Anılmayan tablo, hakem gözünde gereksiz tablodur.

**Yapılacak.** Her tablonun önüne en az bir cümle: "…Tablo 15'te verilmiştir",
"Tablo 22'de görüldüğü üzere…" vb.

### ☐ M-40 🟠 On iki şekil metinde numarayla anılmıyor `[B]`
**Anılmayanlar:** Şekil 2, 3, 4, 5, 6, 11, 12, 16, 18, 19, 20, 21

Özellikle Şekil 16–21 (metin ve risk bölümlerinin grafikleri) hiç çağrılmıyor.

### ☐ M-41 ⚪ Çapraz başvurular alan kodu değil, sabit metin `[D]`
**Ölçüm:** `<w:fldChar>` = **0**, `<w:instrText>` = **0**.

Belgedeki tüm "Tablo 12", "Şekil 7", "Bölüm 3.2" atıfları elle yazılmış sabit
metindir. Bir tablo eklenip numaralar kaydığında **hiçbiri güncellenmez** —
M-08'deki yanlış atıf (`Bölüm 3.2`) bunun somut sonucudur.

**Yapılacak.** Kritik değil ama revizyon döngüsünde zaman kazandırır: Word'de
tablo/şekil başlıklarına **Ekle → Başvuru → Resim Yazısı**, metin içinde
**Çapraz Başvuru** kullan. En azından numaraları her düzenlemeden sonra elle
denetleyen bir kontrol adımı tanımla.

### ☐ M-42 🟠 Hedef dergi seçilmemiş; Öz ve Abstract iki katından uzun `[B+D]`

**Ölçüm:** Öz ≈ **390 kelime** (anahtar kelime satırı hariç; dahil 405),
Abstract ≈ **470 kelime** (dahil 513). Dergilerin tamamı 150–250 aralığında.

Biçim kuralları dergiye göre değişiyor ve şu an hiçbirine tam uymuyor:

| Dergi | Öz | Anahtar kelime | Kaynak | Tablo başlığı | Başlık dili |
|---|---|---|---|---|---|
| Politeknik | ≤200 kelime | 3–5 | `[1]` numaralı | Üstte | Çift dilli |
| GAZİMMFD | ≤200 kelime | ≤5, alfabetik | `[1]`, listede numara noktayla | Üstte | Çift dilli |
| DACD | 150–200 | 3–6 | Yazar-yıl (APA) | Üstte, `Tablo 1:` | Tek dil |
| Afet ve Risk | 150–250 | 4–6 | Yazar-yıl (APA 7) | Üstte, `Tablo 1.` | Tek dil |

**Mevcut durum:** anahtar kelime 5 ✓, kaynak numaralı `[1]` biçiminde, tablo
başlığı üstte ✓, başlıklar tek dilli.

**Yapılacak.**
1. Hedef dergiyi seç.
2. **Öz'ü 200–250 kelimeye indir**, Abstract'ı aynı oranda kısalt.
3. Dergi yazar-yıl istiyorsa tüm atıfları dönüştür.
4. GAZİMMFD seçilirse: anahtar kelimeleri alfabetik sırala, genişletilmiş
   İngilizce özet (ayrı dosya, ≤1 sayfa, Highlights + Graphical Abstract +
   Purpose/Theory and Methods/Results/Conclusion) hazırla, bölüm başlıklarını çift
   dilli yap.

### ☐ M-43 🟠 On bir şekil üretilmemiş `[B]`

**Üretilmiş (10 şekil, 17 gömülü görsel):** Şekil 7, 8, 14, 15, 16, 17, 18, 19, 20, 21 ✓

| Şekil | İçerik | Üretim zorluğu |
|---|---|---|
| 1 | Yazının algılama/karar eksenlerinde konumlandırılması | Kolay — çizim |
| 2 | Sistem mimarisi ve veri akışı | Kolay — çizim |
| 3 | Çalışma alanı haritası (fay zonu, dış merkezler, 9 bölge) | Orta — GIS |
| 4 | Karolama, harmanlama, son işleme şeması | Orta — kod çıktısı + çizim |
| 5 | Kapanma katmanının çizgeye işlenmesi (4 panel) | Orta — kod çıktısı |
| 6 | Üç düzeyli değerlendirme protokolü şeması | Kolay — çizim |
| 9 | Bölütleme sonuçlarının görsel karşılaştırması | **Kolay — modeller eğitilmiş, çıkarım yeter** |
| 10 | Kapanma oranı karşılaştırma çubuğu | Kolay — veri hazır |
| 11 | Güzergâh karşılaştırması (harita) | Orta — senaryo çıktısı |
| 12 | Kazanç ayrıştırma yığılmış çubuk | **Kolay — veri hazır (Tablo 17)** |
| 13 | IoU–ulaşım süresi ilişkisi | Tablo 18'e bağlı (M-20) |

**Öncelik:** Şekil 9, 10, 12 hemen üretilebilir. Şekil 1, 2, 6 çizim işidir.

### ☐ M-44 ⚪ Şekil çözünürlüğü ve dili `[B]`
Dergiler genellikle ≥300 dpi ister; GAZİMMFD ayrıca şekil üzerindeki yazıların
Times 10 pt, **yalnız siyah** ve **Türkçe** olmasını şart koşar. Mevcut 17
görselin bu ölçütlere uygunluğu denetlenmemiştir.

**Yapılacak.** Üretilmiş grafiklerin eksen etiketlerini Türkçeleştir, çözünürlüğü
kontrol et.

---

# BÖLÜM 6 — KÜNYE VE İDARİ ALANLAR

### ☐ M-45 🟠 Sekiz `[EKLENECEK]` alanı `[B]`

| Alan | Nerede |
|---|---|
| Yazar adları (4 kişi) | Yazarların Katkıları |
| TÜBİTAK proje numarası | Teşekkür |
| Depo adresi | Veri Erişilebilirliği |
| Senaryo koşum ortamı (5 alan) | Tablo 11 |

### ☐ M-46 🟠 Yazar listesi ve katkı beyanı güncellenmeli `[B]`
Görüntü işleme uzmanı hocalar projeye katılacağından, yazar sırası ve CRediT
katkı beyanı buna göre yeniden düzenlenmelidir. Mevcut taslakta dört genel rol
tanımlı; uzman katkısı (yöntem danışmanlığı, deney tasarımı denetimi) için ayrı
satır gerekir.

### ☐ M-47 🟠 Veri erişilebilirliği beyanı — özel veri kümesi `[B+D]`
Beyan yalnızca açık kaynakları listeliyor. Ancak Türkçe metin karşılaştırması
`deprem-private/intent_test_v13_anonymized` adlı **özel** bir küme kullanıyor
(bkz. M-33).

**Yapılacak.** Kümenin erişim koşulunu beyana ekle. Erişim kapalıysa bunu açıkça
belirt; hakem yeniden üretilebilirlik açısından sorar.

### ☐ M-48 🟠 Görüntü kaynağı lisansı `[B]`
Kodda Google uydu karoları çekiliyor
(`backend/apps/road_damage/utils/fetcher.py`, `mt1.google.com/vt/lyrs=s`).
Makale koşumlarının **Maxar Open Data** ile yapıldığı Veri Erişilebilirliği
beyanında açıkça belirtilmeli; aksi hâlde kod paylaşıldığında çelişki doğar.

---

# BÖLÜM 7 — İNCELENİP KAPATILANLAR

Bu maddeler iki listede sorun olarak yer aldı ama **doğrulama sonucunda sorun
olmadıkları** ya da **yanlış oldukları** anlaşıldı. Yeniden gündeme gelmemeleri
için kayda geçiriliyor.

### ✔ K-01 Tablo 12'deki 0,4276 ile Tablo 22'deki ROC-AUC 0,4276 çakışması
**Durum:** KAPALI — gerçek rastlantı, kopyala-yapıştır hatası **değil**.

İki değer iki bağımsız kaynaktan geliyor:
- Tablo 12 → `optimized_training_colab.ipynb` çıktısı, *"En iyi Val IoU: 0.4276"*
- Tablo 22 → `05_risk_skoru/.../leaderboard.csv`, ÇKA satırı
  `0.42759818884895767`

Aynı dört haneye yuvarlanmaları tesadüftür. **Düzeltme gerekmiyor.**
*(İsteğe bağlı: Tablo 22'de bu değeri beş haneye yazmak okuyucuda şüphe
uyandırmasını önler.)*

### ✔ K-02 Karolama adımının örtüşmesiz olduğu şüphesi
**Durum:** KAPALI — şüphe **yanlış çıktı**.

`build_notebook.py`: `tile_size, tile_stride = 512, 256`. Yani %50 örtüşme
gerçektir ve makalenin veri sızıntısı uyarısı **geçerlidir**.

### ✔ K-03 Sayısal sapmalar (diğer incelemedeki küçük hatalar)
| İddia | Ölçülen | Not |
|---|---|---|
| Abstract 499 kelime | **≈470** (anahtar kelimeler dahil 513) | Sonuç değişmiyor: iki katından uzun |
| Toplam ≈17 280 kelime | **18 169** (gövde ≈15 326) | Sonuç değişmiyor: çok uzun |
| Öz 389 kelime | **389** ✓ | Birebir doğru |

Bu sapmalar hiçbir maddenin geçerliliğini etkilemiyor; yalnızca sayılar
alıntılanırken bu dosyadaki ölçümler kullanılmalıdır.

---

# ÖNCELİK SIRASI

## Aşama 1 — Hocaya göndermeden önce (1 hafta)

Bu aşamanın tamamı **yazım ve dizgi işidir; yeni koşum gerektirmez.**

| ☐ | İş | Madde | Süre |
|---|---|---|---|
| ☐ | **Denklemleri `md2docx.py` ile yeniden üret** | M-10 | 1 saat |
| ☐ | Sentetik kapanma üreticisini Bölüm 3'te tanımla | M-04 | yarım gün |
| ☐ | Ekip–hedef atama kuralını Bölüm 3.9'a yaz | M-05 | yarım gün |
| ☐ | Üç geçilebilirlik kuralını tanımla, 4.3'teki atfı düzelt | M-08 | 2 saat |
| ☐ | Tek/çok etiketli çelişkisini ve iki eşiği çöz | M-07 | 2 saat |
| ☐ | Artçı ayıklaması çelişkisini çöz | M-06 | 1 saat |
| ☐ | Öz ve Abstract'tan SegFormer iddiasını çıkar | M-02 | 1 saat |
| ☐ | Bölüm 4.2'de sırayı ters çevir | M-03 | yarım saat |
| ☐ | Kip tutarsızlıklarını düzelt | M-15 | 1 saat |
| ☐ | Bölüm 4.1.1'deki çelişkiyi kaldır, Tablo 11'i doldur | M-16, M-22 | 2 saat |
| ☐ | Altı yazarsız kaynağı tamamla | M-35, M-38 | 2 saat |
| ☐ | ConvBERTurk/DistilBERTurk atıflarını düzelt | M-36 | yarım saat |
| ☐ | Türkçe metin kümesinin künyesini yaz | M-33 | 2 saat |
| ☐ | Tüm tablo ve şekilleri metinde numarayla an | M-39, M-40 | yarım gün |
| ☐ | Öz'ü 200–250 kelimeye indir | M-42 | 2 saat |
| ☐ | Şekil 9, 10, 12'yi üret | M-43 | yarım gün |

## Aşama 2 — Hoca görüşü sonrası (2–3 hafta)

| ☐ | İş | Madde |
|---|---|---|
| ☐ | SegFormer'ı üç katmanlı bölmeyle yeniden koştur | M-01 |
| ☐ | Erken durdurma ölçütünü `iou_fg`'ye taşı (aynı koşumda) | M-11 |
| ☐ | İki naif risk tabanını koştur | M-09 |
| ☐ | GFLOPs ve çıkarım süresini ölç | M-28 |
| ☐ | Gecikmeleri n ≥ 100 ile yeniden ölç | M-30 |
| ☐ | 18 görev için istatistiksel test ekle | M-31 |
| ☐ | Bölgeler arası genellemeyi koştur | M-24 |
| ☐ | R1 ve R2 referanslarını koştur | M-25 |
| ☐ | Yakınlaştırma hesabını düzelt ve örnekle | M-12 |
| ☐ | λ(d) ve orta nokta notlarını ekle | M-13, M-14 |
| ☐ | Kalan şekilleri üret | M-43 |
| ☐ | Hedef dergi biçimine geçir | M-42 |

## Aşama 3 — Merkezî katkının tamamlanması (3–4 hafta)

| ☐ | İş | Madde |
|---|---|---|
| ☐ | EMSR648'i kapanma katmanına bağla | M-23 |
| ☐ | Görev tabanlı değerlendirmeyi koştur | M-20 |
| ☐ | Geçilebilirlik duyarlılığını tamamla | M-26 |
| ☐ | Bileşen çıkarma analizini koştur | M-27 |
| ☐ | Yol hasarı eğitim kümesi kararını ver ve uygula | M-21 |

---

# KİMLİK EŞLEME

Eski listelerdeki numaralarla arama yapılabilmesi için:

| Bu dosya | Bu oturumun listesi | Diğer inceleme | `EKSIKLER_VE_SORUNLAR.md` |
|---|---|---|---|
| M-01 | A-1 | B8 / B9 | A-01 |
| M-02 | A-2 | — | A-02 |
| M-03 | A-3 | — | A-03 |
| M-04 | — | A1 | A-06 |
| M-05 | — | A2 | A-07 |
| M-06 | A-4 | A3 | A-04 |
| M-07 | — | A4 | A-08 |
| M-08 | — | B6 | A-09 |
| M-09 | A-5 | A3-ek | A-05 |
| M-10 | — | D1 | D-06 |
| M-11 | — | C4 | D-07 |
| M-12 | — | C5 | A-10 |
| M-13 | — | C2 | A-11 |
| M-14 | — | C3 | A-12 |
| M-15 | C-1 | — | — |
| M-16 | — | C14 | A-13 |
| M-17 | C-2 | — | E-04 |
| M-18 | C-4 | — | — |
| M-19 | C-3 | — | — |
| M-20 | B-8 | — | B-01 |
| M-21 | B-1 | — | B-02 |
| M-22 | B-2 | B4 | B-09 |
| M-23 | B-4 | — | B-05 |
| M-24 | B-5 | — | B-06 |
| M-25 | B-7 | — | B-04 |
| M-26 | B-9 | — | — |
| M-27 | B-10 | — | B-07 |
| M-28 | B-3 | — | B-08 |
| M-29 | B-6 | — | — |
| M-30 | B-12 | — | B-10 |
| M-31 | B-13 | — | B-11 |
| M-32 | B-11 | — | C-02 |
| M-33 | — | B2 | B-13 |
| M-34 | — | C12 | — |
| M-35 | — | E1 | G-01 |
| M-36 | — | E2 | G-02 |
| M-37 | — | E6 | G-03 |
| M-38 | — | — | G-01 |
| M-39 | D-1 | — | — |
| M-40 | D-2 | — | — |
| M-41 | — | D3 | — |
| M-42 | D-3 | D4 / D5 / D6 | — |
| M-43 | E-1 | — | B-12 |
| M-44 | E-2 | — | — |
| M-45 | F-1 | — | — |
| M-46 | F-2 | — | — |
| M-47 | F-3 | — | — |
| M-48 | F-4 | — | D-01 |
| K-01 | — | C11 | H-01 |
| K-02 | — | — | H-02 |

---

# NE ZAMAN NİHAİ SAYILIR

Taslak şu dört koşul sağlandığında nihai düzeydedir:

1. **Bölüm 1'in tamamı kapalı** — yayın engelleyici hiçbir madde kalmamış.
2. **Bölüm 3'te tanımlanmamış hiçbir mekanizma Bölüm 4'te kullanılmıyor.**
   Bugün üç tane var: sentetik üretici (M-04), atama kuralı (M-05), üç
   geçilebilirlik kuralı (M-08). Bir hakem için bu, eksik ölçümden daha ağır bir
   kusurdur: eksik ölçüm "henüz yapılmadı" demektir, tanımsız mekanizma
   "yapılanın ne olduğu bilinmiyor" demektir.
3. **Her tablo ya doludur ya da tabloda değildir.** İskelet tablolar makaleden
   çıkarılıp "Gelecek Çalışmalar" bölümünde metin olarak anlatılmalıdır; dergiler
   boş tablo kabul etmez. Şu an 187 boş hücre var.
4. **Her şekil üretilmiştir** ve metinde numarayla anılmaktadır.

**Stratejik not.** 187 boş hücrenin tamamının doldurulması gerekmiyor olabilir.
Alternatif bir yol: makalenin kapsamını **ölçülmüş olanla sınırla** — bina hasarı
çok mimarili kıyaslaması, Türkçe metin kıyaslaması, risk kıyaslaması ve uçtan uca
senaryo. Ölçülmemiş eksenleri (yol bölütlemesi, görev tabanlı değerlendirme,
bölgeler arası genelleme) tablo iskeleti olarak değil, "Gelecek Çalışmalar"da
paragraf olarak sun. Bu, makaleyi bugün gönderilebilir hâle getirir; görev tabanlı
değerlendirme ise ikinci bir makalenin çekirdeği olur.

Hangi yolun seçileceği bir **kapsam kararıdır** ve danışman görüşü gerektirir.

---

*İlgili belgeler: `EKSIKLER_VE_SORUNLAR.md` (proje geneli takip — kod, depo, git
maddeleri dahil), `PROJE_DOSYASI.md` (uzman ortak yazarlar için teknik tanıtım)*
