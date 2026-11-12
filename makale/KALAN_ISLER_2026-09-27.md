# Kalan İşler — makale (29 Eylül 2026, 9. tur sonrası)

Bu dosya makalenin **gönderilebilir hâle gelmesi için kalan** işleri tutar. Bu
makinede yapılabilen her şey yapıldı; aşağıdakiler karar, başka makine ya da
başka kişi gerektiriyor. Ayrıntılar: `EKSIKLER_VE_SORUNLAR.md` J-111…J-131,
`SIMULASYON_OLCUM_KAYDI.md`.

**Devir (28 Eylül 23:20):** iş Furkan'a devredildi; kaldığı yer ve adımlar `makale/YAPILACAKLAR_FURKAN_2026-09-28.md`'de.

**Güncel dosya:** `makale/QuakeMind_Makale_Taslak_2026-09-16_sekillieklendi_v3_LOCAL_2026-09-21.docx`
(72 sayfa · 23 şekil · 23 tablo · 68 kaynak · 17 denklem; bütün atıflar çözülüyor)

**Yedekler:** `makale/arsiv/` altındaki yerel revizyon yedekleri (~440 MB) ve eski makale sürümleri 29 Eylül'de
temizlendi. Yedekler Geri Dönüşüm Kutusu'nda; commit'lenmiş sürümler git geçmişinde (ör. `68a1cf3` = revize16
sonrası, bu turun commit'i = revize17 sonrası).

**Betikler (`makale/analiz_arsivi/`):** `revize2*.py`, `revize3.py` … `revize17.py`,
`yardimci.py`, `cikar.py`, `atif.py`. Yedekler temizlendiği için bir betiği yeniden çalıştırmak üzere
güncel docx'in kopyasını `SRC` olarak verin; revize13–16'da `sys.path` Utku'nun geçici klasörüne göre yazılı,
`revize17.py` depo içi yollarla çalışır.

---

## Bu turda yapılanlar (11. tur, 29 Eylül) — i7 doğrulamaları (revize19)

- **J-118 kapandı.** Tablo 11'in birinci sütunu (i7-12700H) doğrulandı: Python 3.12.6,
  PyTorch 2.13.0 (CUDA yok), Ultralytics 8.4.116, Transformers 5.14.1, NetworkX 3.6.1,
  OSMnx 2.1.1, pyrosm 0.13.1, FastAPI 0.141.1, smp 0.5.0 — dokuzunun dokuzu tabloda yazanla aynı.
- **J-133 bulundu ve kapandı: Tablo 15'in metin gecikmesi bayattı.** Örtüşme (11/18) düzeltme
  sonrasıydı ama gecikme (36,6 / 43,0 ms) düzeltme öncesinden kalmıştı. Aynı makinede
  düzeltilmiş kodla yeniden ölçüldü: **medyan 48,2 ms, en uzun 58,9 ms** (beş koşum:
  47,8 · 47,8 · 48,5 · 48,5 · 48,2). Fark %32.
  - **Tuzak kaydedildi:** aracın ısınma çağrısı soğuk başlangıcı kapatmıyor; ilk koşum
    62,3 / 77,6 ms verdi. Raporlanan değer kararlı banttır, hücre notunda yazılı.
  - Tablo 15 satırı, §4.5 "Kanal ölçümleri" cümlesi ve Tablo 15 altyazısı güncellendi.
- Betik: `makale/analiz_arsivi/revize19.py`. Rapor:
  `QuakeMindBackend/benchmark/reports/kanal_olcumu_metin_i7.json`.
- Denetim: `atif.py` temiz. Gönderim kopyası yenilendi.
- C listesinden kalan: YOLO bağımsız saha sınama kümesi; veri miktarıyla eşlenmiş genelleme kıyası.

## Bu turda yapılanlar (10. tur, 29 Eylül) — Tablo 1'e KATE kümeleri (revize18)

- **Tablo 1'e KATE-PD ve KATE-CD satırları eklendi** (J-132). Tablo Türkiye'ye özgü kümeleri sayıyordu
  ama bu çalışmanın kendi eğitim verisini saymıyordu.
  - Sınıf sayısı (2) yereldeki KATE-PD maskelerinden ölçüldü, kestirilmedi; diğer hücreler makalenin
    kendi §3.2.1 ve §4.2 metninden, yıl kaynak [56]'dan.
  - Tablo 1 altyazısına hangi kümelerin eğitimde kullanıldığı yazıldı.
- **§2.1 cümlesi tabloyla uyumlandı:** "TUE-CD ve TE23D öne çıkmaktadır" artık KATE'leri de sayıyor;
  "Her iki küme de" → "Bu kümelerin tümü"; KATE'leri tanıtan bir cümle eklendi.
- Betik: `makale/analiz_arsivi/revize18.py`. Yedek: `makale/arsiv/…_pre_revize18_2026-09-29.docx`.
- Denetim: `atif.py` temiz. Gönderim kopyası yenilendi.
- **Kalan:** PDF sayfa düzeni taraması (Word COM gerekiyor; iki satır tabloyu sayfa sonuna itmiş olabilir).

## Bu turda yapılanlar (9. tur, 29 Eylül) — genelleme üç tohumla (revize17)

- Kaggle oturum 5 ve 6 bitti (il dışarıda bırakma, tohum 7 ve 2026). Tablo 14 artık üç tohumun ortalama ± SS'si.
- Görülmemiş ilde IoU_hasar 0,04–0,08 düşük (%9–22); düşüş 12 eşleşmenin 11'inde. ÖZ, Abstract, §4.4,
  Tablo 23 ve "tek tohumla" diyen cümleler güncellendi. 72 sayfa; atıf ve sayfa düzeni denetimi temiz.
- `YAPILACAKLAR_FURKAN_2026-09-28.md`'nin 2. ve 3. bölümleri tamamlandı; kalanlar 5. bölümdeki karar ve insan işleri.

## Önceki tur (8. tur, 28 Eylül akşamı) — GPU paketi: genelleme ve çoklu tohum (revize15, revize16)

- **Kaggle'da dört oturum koşuldu** (Chrome'dan; kayıtlar `makale/analiz_arsivi/kaggle/sonuclar/`, günlükten
  `gunluk_ayikla.py` ile çıkarılıyor; çıktı indirilmiyor).
- **§4.4 bölgeler arası genelleme ölçüldü, yeni Tablo 14:** görülmemiş ilde IoU_hasar 0,05–0,10 düşük; dört
  koşunun üçünde yalnız çıkarılan il düşüyor. Eski Tablo 14–22 artık 15–23.
- **Çoklu tohum:** üç mimari × üç tohum. Tohum oynaması ±0,02 değil, SS 0,024–0,043 (EKSIKLER J-131).
  Mimari sıralaması, kodlayıcı iddiası ve "bölütlemeyi artırmak kazancı artırmıyor" yorumu ölçüye göre
  yeniden yazıldı; tatbikattaki U-Net etiketi "En iyi" → "Büyük".
- İl dışarıda bırakmanın iki ek tohumla yinelenmesi (oturum 5, 6) 9. turda işlendi (revize17).
- 72 sayfa · 23 şekil · 23 tablo · 68 kaynak · 17 denklem; atıf ve sayfa düzeni denetimi temiz.

## Önceki tur (7. tur, 28 Eylül) — kapanma yer gerçeği insan etiketiyle (revize14)

- **J-126 kapandı.** Bir yazar 33 kesiti kör etiketledi. İnsan etiketi esas, Claude ikinci görüş:
  kesinlik **4/5** (Wilson %38–96), duyarlılık **≈%9**, yargılanamayan %15. Claude 3/3, ≈%11, %30.
- **Uyum zayıf:** 33 kesitin 14'ü aynı; Cohen κ 0,13 (üç sınıf), 0,37 (kararsız hariç).
- **Makaledeki bir cümle değişti:** "model yanlış alarm üretmiyor" → "az yanlış alarm üretiyor"
  (kapalı dediği beş parçanın biri insana göre açık). Tablo 13 iki etiketleyici sütunu ve uyum
  satırıyla yeniden kuruldu; ÖZ, Abstract, §4.1, §4.3, §5.1, §5.3, §5.4, §6, Tablo 22 güncellendi.
- 71 sayfa korundu; atıf, tablo, şekil ve denklem denetimi temiz. Gönderim kopyası
  (`QuakeMind_Makale_GONDERIM_vurgusuz.docx`) yeniden üretildi.

## Önceki tur (6. tur, 28 Eylül) — ölçülmemiş eksiklerin kapatılması (revize12)

- **A\* çapraz doğrulandı:** 248 sorguda bağımsız Dijkstra ile aynı (`araclar_astar_capraz.py`).
- **Kalan sekiz alan koşuldu:** eski "ayrışmadı" cümlesi yanlıştı; üç alan tek modelde ayrışıyor.
  Seçim ölçütü "en az iki modelde ayrışma" olarak makaleye yazıldı.
- **Metin üst kategori F₁ ölçüldü:** sızıntısız karşılaştırma BERTurk'üyle mikro 0,797 / makro 0,758.
  Üretim ağırlığı sınama bölmesini görmüş görünüyor (J-128).
- **YOLO:** eğitim doğrulama bölmesindeki mAP'ler makaleye girdi (iyimser, bağımsız sınama değil).
- **Son işleme seviyesi:** ekip Kaggle kayıtlarından; etkisi pratikte yok (ΔIoU ≤ 0,0009).
- **Şekil 24 kaldırıldı:** örnek veri kipiyle çekilmişti; modülün gerçek çıktısı Şekil 5 ve 10'da.
- **İki ciddi bulgu makaleye yazıldı:** kapanma etiketlerini Claude yapmış (J-126); metin kümesinde
  telefon numarası ve adres var (J-127). Etik ve Veri Erişilebilirliği düzeltildi.

## Daha önceki tur (5. tur, 28 Eylül)

- **B0 yeniden koşusu bu makinede tamamlandı.** Ağırlıklar Kaggle'dan, SHA-256 doğrulandı; yol
  verisi PBF'ten yeniden üretildi. Bütün tatbikat sayıları düzeltilmiş kodla yeniden üretildi
  ve makaleye işlendi (revize10): Nurdağı %54–60, genel %8–60, ceza payı ölçüldü %68–78.
  Ayrıntı: `SIMULASYON_OLCUM_KAYDI.md` §18, EKSIKLER J-112…J-117 kapanış satırı.
- **Tablo 11 (revize11):** tatbikatın koşulduğu ikinci makine ayrı sütun olarak eklendi;
  gecikmeler i7 ölçümü olarak kalıyor. Üç tablodaki punto tutarsızlığı giderildi (J-125).

## Önceki tur (4. tur)

- **Metin sınıflandırma katmanı düzeltildi ve yeniden ölçüldü (J-111/J-116):** model
  eminse anahtar sözcük onu ezmiyor; eşleşme sözcük sınırında ("araç" artık "aç"
  sayılmıyor); Türkçe küçük harf; gösterilen güven gösterilen kategorinin. Eşik ve
  13→5 eşlemesi değişmedi (test metnine ayar yapılmadı). Örtüşme **9/18 → 11/18**;
  kararın kaynağı model 15, anahtar sözcük 3 (eskiden 12'si anahtar sözcük). Rapor:
  `QuakeMindBackend/benchmark/reports/kanal_olcumu_metin_duzeltilmis.json` (i7 raporu
  `kanal_olcumu.json`'a dokunulmadı). Sınama: `testler/test_siniflandirma.py` 7/7.
- **Yeni bulgu (J-123):** model yol kapanması metinlerini tanımıyor (4/4'ünde ulaşım
  etiketi yok); yol bilgisi bugün yalnız anahtar sözcükten geliyor. Makaleye yazıldı.
- **Makale (revize7):** §3.6 (normalleştirme — sınıflandırıcı küçük harf görmüyordu,
  metin yanlıştı; karar sırası; kurtarma katmanı; NER paragrafı; Tablo 8 dipnotu), §3.9
  atama örneği ("hilti ve jeneratör lazım" gerçekte Elektrik Kaynağı → Acil Yardım),
  §4.5 + Tablo 14, §5.3(c), §6 gelecek işler ve sonuç, Denklem (8) atfı.
- **Güvenlik (J-119) kodda kapandı:** eski kayıt/giriş uçları rolü istemciden almıyor,
  varsayılan kapalı; `/api/team/*` 409 kilidi de aynı bağımlılığın arkasında. Sınandı.
- **Şekil 1 yeniden çizildi (J-124):** eski şeklin üreticisi yoktu, ~42 noktanın hiçbiri bir
  kaynağa bağlı değildi ve sağ üstteki üç nokta §2.3'teki "rastlanmamıştır" ifadesiyle
  çelişiyordu; eksen yazıları da üst üste biniyordu. Yeni şekilde her kutu §2'deki bir
  kaynak numarası (19 kaynak), yeri betikte gerekçesiyle yazılı
  (`QuakeMindBackend/araclar_makale_yazin_konumu.py`); §2.5'teki atıf cümlesi ve altyazı
  güncellendi (revize8). **Bakmanızı isterim:** sınıflama niteliksel bir karardır.
- **Şekil 5 üreticisi:** künye satırı artık sarmalanıyor (`araclar_makale_haritalari.py`);
  yeniden üretim i7'de (B0).
- **Sayfa düzeni okuması (revize9):** PDF'te taşma, sayfa sonunda kalan tablo başlığı ve
  görselinden ayrılmış altyazı tarandı. Şekil 11'in altyazısı sonraki sayfadaydı → görseller
  altyazılarıyla, tablo başlıkları tablolarıyla birlikte tutuluyor; kısa tablolar (≤ 15
  satır) bölünmüyor, uzun tablolarda başlık satırı yineleniyor. Tablo hücreleri iki yana
  yaslıydı (dar sütunlarda "Defne   /   Elektrik") → sola yaslandı. Tablo 21'in ROC-AUC
  sütunu genişletildi. Sayfa sayısı 67 → 69 (tabloların bölünmemesinden).
- **Tatbikat koşucusuna `--rh`:** Tablo 18 (r_h duyarlılığı) artık depodaki betikle
  üretiliyor; `araclar_tatbikat_ozet.py` tabloyu yazıyor.

## Önceki tur (3. tur)

- **Boş tablolar metne çevrildi:** Tablo 5 (oluşturulmamış yol hasarı kümesinin künyesi)
  ve Tablo 15 (koşulmamış il-ayrık genelleme). Tablolar 1–22 olarak yeniden
  numaralandı; kaydırmadan bozulan 17 Türkçe ek ("Tablo 12'ün" → "Tablo 12'nin")
  otomatik düzeltildi. Kalan tek `[ÖLÇÜLECEK]`: §4.6 ceza payı (aşağıda B1).
- **R0b risk tabanı düzeltildi (J-120):** sabit öznitelikle koşulmuştu; doğru öznitelikle
  ölçüldü → CatBoost'u geçiyor. §4.11 beşinci gözlem tersine döndü; Sonuç'a eklendi.
  Tablo 21'deki yanlış kalın işaretler düzeltildi.
- **Şekiller:** Şekil 2 (mimari), 4 (karolama/morfoloji), 6 (protokol) koda göre yeniden
  çizildi (`QuakeMindBackend/araclar_makale_semalar.py`); Şekil 20 "7 olaylık" etiketiyle
  aynı veriden yeniden üretildi.
- **Kaynakça (J-121):** 53 DOI doğrulandı; 4 hatalı DOI düzeltildi ([9] başka makaleyi
  gösteriyordu); 13 URL'nin erişim tarihi güncellendi.
- **Okuma turu:** tekrarlar (katkı 1–2, "Tablo 15'te verilmektedir" ×2), "25 çift" → "en
  çok 25", ölçülmüş çıkarım süresi, "yol maskesi" → "hasar maskesi", kod yolu
  parantezleri, keşif–kazanç ilişkisinin kısmen yapısal olduğu uyarısı (§4.6, Şekil 12,
  §5.1, §6), mobil istemci geri eklendi, teşekkür cümlesi.

---

## Alınan kararlar (27 Eylül, kullanıcı)

| Konu | Karar | Durum |
|---|---|---|
| Üç kod kusuru (J-112/113/114) | **Düzelt + yeniden koş** | Kod düzeltildi, sınamalar geçiyor (7/7); yeniden koşu i7'de (B0) |
| Tablo 15 "Keşif" sütunu | **Yeniden koşuda her kol için ayrı çıksın** | Koşucu + yeni `araclar_tatbikat_ozet.py` kol başına keşif ve ölçülmüş ceza payı yazıyor |
| Türkçe metin kümesi erişimi | **İstek üzerine** | Makaleye işlendi (Veri Erişilebilirliği + Tablo 2) |
| Hedef dergi | Henüz belli değil | Biçim şimdilik olduğu gibi |
| ORCID / sorumlu yazar | Sonra eklenecek | Yer tutucu duruyor |

**Kodda yapılan düzeltmeler (27 Eylül):**
- `network.py` — dönüş maliyeti açıkken kapanma sabiti yalnız değerlendirme (1,0 dk);
  manevrayı ekibin fiilen yaptığı dönüş ödüyor (eskiden U dönüşü iki kez sayılıyordu).
- `yerel_yol.py` — `oneway=-1` artık ters yönde (v → u) kuruluyor.
- `donus.py` — A* sezgiseli sabit 80 km/sa yerine çizgenin gerçek en yüksek hızını
  kullanıyor (sınamada eski sezgisel 44,4 sn'lik yolu, doğrusu 41,5 sn).
- `tatbikat.py` — kol ortalamaları 3 basamak; ortak görevler üzerinden `toplamSureDk`,
  `toplamCezaDk` eklendi. `araclar_tatbikat_kos.py` — `elenen` hatası giderildi, tohum
  başına afetzede sayacı. Yeni: `araclar_tatbikat_ozet.py` (tohum birleştirici).
- `testler/test_donus.py` — üç kusur için birer sınama eklendi.

---

## KALAN İŞLER (29 Eylül, güncel liste)

Makalede ölçülebilir bir eksik kalmadı. Kalanlar karar ya da insan işi. Gönderim için şart
olanlar: A'daki beş madde ve B'deki yazar okuması.

### A. 🔴 Ekip kararı (gönderimden önce şart)
- [ ] **Kişisel veri (J-127).** Metin kümesinde telefon numarası (%49) ve adres (%97) var. Karar verilecekler:
  - paylaşımda maskeli kopya mı kullanılacak;
  - adresler de maskelenecek mi;
  - etik kurul / KVKK değerlendirmesi gerekiyor mu.

  Maskeli yerel kopya hazır: `C:/Users/utkuc/quakemind_ozel/intent_test_v13_maskeli/`.
- [ ] **İntihal taraması (iThenticate / Turnitin).** Gönderimden önce şart. KTO Karatay aboneliğinden
  (kütüphane ya da enstitü) yapılmalı; Claude'un erişimi yok.
  - Belge **içi** tekrar taraması 29 Eylül'de yapıldı ve temiz çıktı (`makale/analiz_arsivi/tekrar.py`;
    784 cümlede 3 birebir tekrar, hepsi meşru). **Bu intihal taraması değildir**, dışarıdan kopyalanan
    metni bulmaz — yalnızca belge içi tekrarı gösterir.
  - Tarama sonucu gelince: eşleşme oranı ve kaynak listesi değerlendirilmeli; kendi önceki
    yayınlarımızla örtüşme varsa (öz-intihal) atıfla belirtilmeli.
- [ ] **ORCID numaraları ve sorumlu yazar** (başlıktaki yer tutucu).
- [ ] **Hedef dergi.** Seçilince kaynak stili, sayfa sınırı ve kör hakem başlığı ayarlanır. Makale 72
  sayfa; en büyük iş muhtemelen kısaltma.
- [ ] **GitHub deposunun görünürlüğü.** Veri Erişilebilirliği'ndeki bağlantı, depo özel olduğu için açılmıyor.
- [ ] **Roboflow API anahtarının iptali ve yenilenmesi.** Git geçmişinde açıkta (`9d4cc22`, `55a50d1`).
  Güvenlik sorunu.

### B. 🟠 İnsan işi
- [ ] **İkinci insan etiketleyici (önerilir).** Utku dışında bir yazar aynı 33 kapanma kesitini etiketlesin
  (~20 dk); insanlar arası κ ölçülür, §4.3 güçlenir.
  - Kit: `QuakeMindBackend/benchmark/kapanma_yer_gercegi/insan_kiti/etiketle.html`
  - Ölçüm: `araclar_kapanma_uyum.py`
- [ ] **Yazar okuması.** Bütün makale baştan sona okunmalı. Sarı vurgulu revizyon cümlelerinin (204 vurgu)
  iç tutarlılığı da bu okumada denetlenmeli; eski listelerdeki "sarı vurgu tutarlılık taraması" maddesi budur.

### C. 🟡 İsteğe bağlı (makaleyi güçlendirir, şart değil)
- [ ] **i7 makinesi:**
  - `pip freeze` ile Tablo 11 yazılım sürümlerinin doğrulanması (J-118);
  - `python araclar_kanal_olc.py` ile Tablo 15 metin gecikmesinin yeniden ölçülmesi.
- [ ] **YOLO bağımsız saha sınama kümesi** (etiketli fotoğraf). Makalede şimdilik eğitim doğrulama değeri
  var ve iyimser olduğu yazılı.
- [ ] **Veri miktarıyla eşlenmiş genelleme kıyası.** Birleşik eğitimden aynı sayıda karo rastgele
  çıkarılır; böylece "U-Net, Hatay hariç" durumunda veri azlığı ile görülmemiş il etkisi ayrılır. ~2–3 GPU
  saati; §4.4'te gelecek çalışma olarak yazılı.

### D. ⚪ Makale dışı (ürün kodu; sınırlılık olarak makalede yazılı)
- [ ] **J-129:** Kaggle defter üretecindeki kuyruk sorunu kalıcı düzeltilmeli
  (`QuakeMind_veri/araclar/defter_dokuz_model.py`).
- [ ] **J-115:** Kamera eşiği kodda 0,20, fiilen 0,25 (makalede doğrusu yazılı, kod düzeltilmedi).
- [ ] **J-123 ve J-128:** Metin modeli yol kapanması ihbarlarıyla yeniden eğitilmeli; üretim ağırlığındaki
  sınama sızıntısı giderilmeli.
- [ ] **Güvenlik:**
  - üretim dağıtımında `QUAKEMIND_DEMO_TOKEN=false` (eski DURUM B-1/3);
  - eski `/api/auth/me` belirteci URL'de taşıyor, eski web kalkınca uçla birlikte kaldırılacak (J-119 kalıntısı).
- [ ] **Kaggle hesabı:** Boş `notebook2195d8897c` taslağı silinebilir.

### E. Doğrulanacak (eski listelerden devralındı)
- [ ] **TE23D / TUE-CD lisans teyidi.** Makale bu iki kümeyi yalnız yazında atıfla anıyor, verilerini
  kullanmıyor. E-postanın hâlâ gerekip gerekmediği değerlendirilsin. Taslaklar: `makale/lisans_epostalari_taslak.md`.

### Tamamlananlar (özet)
Yukarıdaki tur özetlerinde ayrıntılı:
- B0 yeniden koşu ve ham sonuçlar;
- kapanma yer gerçeği insan etiketiyle (J-126);
- il dışarıda bırakma genellemesi (üç tohum);
- üç mimaride çoklu tohum (J-131);
- YOLO doğrulama mAP'ı ve metin F₁;
- sayfa düzeni, Şekil 1, J-119;
- `makale` dalına push.

Eski listelerdeki öteki açık maddeler bu turlarda kapandı ya da geçersiz kaldı:
- LinkNet/PSPNet eğitimi, Haiti/Noto dış sınaması ve tatbikattaki P232/P333 cümleleri makalede artık yok;
- tohum çelişkisi ile il-ayrık deney ölçüldü.
