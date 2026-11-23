# QuakeMind — Eksikler ve Sorunlar: Kapanan Maddeler Arşivi

`EKSIKLER_VE_SORUNLAR.md`'den taşınan, durumu **KAPALI** ya da **DÜZELTİLDİ** olan maddeler.
Metinler değiştirilmeden taşındı (18 Kasım 2026 temizliği). Açık, kısmen kapalı ve karar
bekleyen maddeler ana dosyada kalır. Bir madde yeniden açılırsa ana dosyaya geri taşınır.

---

# A. MAKALE — KRİTİK BULGULAR

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

## A-22 🟠 Veri artırımı tohuma bağlı değildi — "tohum 42" koşuları tekrarlanabilir değil
**Durum:** DÜZELTİLDİ (22 Eylül 2026) — 02/03 defterinin üreteci (`araclar/defter_dokuz_model.py`): `tohumla()` artırımı da tohumlar, DataLoader işçileri torch'un işçi tohumundan yeniden tohumlanır; sonuç kaydında `ayarlar.artirim_tohumlu = true` · **Bulundu:** 22 Eylül 2026 (öncesi + sonrası deneyi eklenirken yerel duman testinin iki koşusu farklı çıktı) · **İlgili:** A-15, B-11

albumentations 2.x `random.seed` / `np.random.seed` / `torch.manual_seed`'i dikkate almıyor: aynı tohumla iki süreçte
aynı dönüşüm farklı sonuç verdi (ölçüldü, 2.0.8). Bu yüzden 21–22 Eylül'deki bütün eğitimlerde (Colab P2, P2_qqb; Kaggle
oturum 1 ve 2) artırım tohumdan bağımsızdı: aynı tohum aynı sonucu vermez; tohumlar arası oynamanın bir kısmı buradan
(Colab–Kaggle P2 farkı 0,455 / 0,435 de kısmen). Düzeltmeden sonra yerelde aynı tohumla iki koşu birebir aynı (CPU;
GPU'da cuDNN'in küçük sayısal farkları kalabilir). 10 model tablosu düzeltilmiş defterle koşulacak; makalede tekrarlanabilirlik
cümlesi buna göre yazılmalı ve önceki koşular "artırım tohumsuz" diye ayrılmalı.

---

# B. MAKALE — HENÜZ ÖLÇÜLMEMİŞ

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

# E. SENARYO VE ÖLÇÜM

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
**Durum:** KAPALI (18 Kasım 2026, temizlik) — geçersizleşti

Yerel `main`, `upstream/main`'in (UtBird/QuakeMind) 15 commit ilerisinde.
`origin/main` (Femrei/QuakeMindDev) ile birebir aynı.
Kullanıcı şu an gönderim istemiyor.

**Temizlik (18 Kasım 2026).** Eylül'deki git durumunu anlatıyor. Ekip akışı değişti (biz geliştiriyoruz, Utku main'e alır): bütün iş dalları upstream'de ve tek birleştirme PR'ında toplandı (UtBird/QuakeMind#12). Yerelde gönderilmemiş commit yok `[K]`.

## F-02 KARAR BEKLİYOR — 123 commit edilmemiş dosya
**Durum:** KAPALI (18 Kasım 2026, temizlik) — geçersizleşti

14 değiştirilmiş + 109 izlenmeyen dosya. İçinde makale taslakları, senaryo
koşuları, benchmark çıktıları var. Hangisinin depoya gireceği karar bekliyor.

**Temizlik (18 Kasım 2026).** Eylül'deki çalışma ağacını anlatıyor. Ürün işleri J-149…J-174 boyunca konu konu commit edildi; bugün çalışma ağacı temiz `[K]`. Makale taslakları ve koşu çıktıları kendi dallarında (`makale`, #3).

## F-03 ⚪ `makale` dalı yerele alındı
**Durum:** KAPALI (12 Eylül 2026)

`git worktree` ile `Desktop\2209-A Afet\QuakeMind_makale\` klasörüne alındı.
Ana çalışma ağacına dokunulmadı. Kaldırmak için:
`git worktree remove "C:/Users/femre/Desktop/2209-A Afet/QuakeMind_makale"`

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


# J. PERFORMANS VE SİSTEM (gecikme / kaynak yönetimi)

## J-13 🟠 Geocoding hala aga bagli — yerel cozum yok
**Durum:** KAPALI (18 Kasım 2026, temizlik) — J-170 ile çözüldü · **Bulundu:** 15 Eylül 2026 · **J-03'ten ayrildi**

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

**Temizlik (18 Kasım 2026).** Ürün yolunda adres artık yerel dizinden çözülüyor (`metin_analizi/adres.py`, OSM'den 81 il, 151 ilçe, 496 mahalle/köy, 6 173 sokak); `/api/nlp/analyze` ve ihbar akışı Nominatim'e gitmiyor (J-170). Uçlarda Nominatim çağrısı kalmadı `[K]`. Eski `apps/disaster_nlp` zinciri (`ner_extraction.py`, `tr_locations.py`) hâlâ Nominatim içeriyor; makale senaryosu o zinciri kullanıyorsa sonuçlar için E-04'e bakılmalı.

---

## J-18 🟡 `/status/{id}` tek seferde 17 MB dönüyor — 15,5 MB'ı base64 görsel
**Durum:** KAPALI (18 Kasım 2026, temizlik) — J-32 ile çözüldü · **Bulundu:** 15 Eylül 2026

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

**Temizlik (18 Kasım 2026).** Görseller 21 Eylül'den beri JSON'a gömülmüyor; diske yazılıp `/api/road_damage/gorsel/{isId}/{ad}` ile tek tek ve önbelleklenebilir iniyor. Konsol özeti `?gorseller=0&segmentler=0` ile ~1 KB çekiyor (J-32). Ağır gövde yalnız eski webin varsayılan çağrısında kaldı.

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

## J-62 🟠 Simülasyon (tatbikat) modu konsolda kuruldu; sözleşmeyle üç uyuşmazlık çıktı
**Durum:** KAPALI (25 Eylül 2026) — arayüz iskeleti gerçek uçlarla uçtan uca koşturuldu; uç sözleşmeden sapıyor, sapmalar aşağıda · **Bulundu:** 25 Eylül 2026 (SIMULASYON_SOZLESMESI.md'ye göre kurulurken) · **İlgili:** J-56, kural 2, kural 4

**Yapıldı.** Sözleşmenin §5'indeki dokuz madde konsola kuruldu; katman ve alan adları §4
ile birebir. Backend'e (`backend/`) dokunulmadı, orayı öbür oturum yazıyor.

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
**Durum:** KAPALI (18 Kasım 2026, ölçüldü) · **Bulundu:** 24 Eylül 2026 (J-53 çalışması sırasında sayıldı) · **İlgili:** J-53, J-45, CLAUDE.md kural 5

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

**Temizlik (18 Kasım 2026).** Sayıldı `[Ö]` (birleşik dal, `backend/uclar/*.py`): **116 uç**, oturumsuz yanıt veren **6**: `/`, `/api/hazir`, `/api/status`, `/api/postgis/status`, `/api/oturum/kayit`, `/api/oturum/giris`. Hepsinin oturumsuz olması gerekiyor. Eski uçlar `kimlik.eski_uc` ile varsayılan kapalı; risk uçları J-152 ve J-173'ten beri giriş istiyor; `/api/live` çerezle kimlik doğruluyor.

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
**Durum:** KAPALI (18 Kasım 2026, temizlik) · **Bulundu:** 22 Eylül 2026 (kullanıcı: "afetzede tarafını mobil gibi yapmışsın… webe yapıyorsun… SOS butonu kırmızı, text yazabilecekler, en yakın toplanma merkezi, hastane ve benzeri yerleri haritadan görebilecekler") · **İlgili:** J-43, J-44, ARAYUZ §8, MIMARI §7

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

**Temizlik (18 Kasım 2026).** Afetzede ekranı sonraki turlarda tamamlandı ve uçtan uca sınandı: Nereye kartı ve yakın yerler (J-171), metin ihbarı (J-170), J-174'te afetzede rolü tarayıcıda ve 48 adımlık akış senaryosunda (`araclar_akis_senaryosu.py`) denendi.

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
**Durum:** KAPALI (18 Kasım 2026, ölçüldü) · **Bulundu:** 21 Eylül 2026 (J-43'ün ağ kaydında) · **İlgili:** kural 4, ARAYUZ §10, J-11, J-52

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

**Temizlik (18 Kasım 2026).** Ölçüldü `[Ö]`: birleşik dal (PR #12), konsol genel mod, koordinatör oturumu, boşta 137 sn (dakika değişimi dahil). Akış (`/api/live`) dışında **0 istek**; akış bağlı kaldı. Hedef (~0) tuttu.

---

## J-45 🔴 Eski demo hesaplarının jetonu kodda sabit; herkes acil bildirim yayınlayabiliyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — madde 2 J-53 bayrağıyla çözüldü · **Bulundu:** 21 Eylül 2026 (J-43 sınanırken) · **İlgili:** J-43, J-47, CLAUDE.md kural 5

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

**Temizlik (18 Kasım 2026).** Kodda sabit demo jetonlarını kabul eden bütün eski uçlar (`/api/notifications/send_emergency`, sohbet, ekip üstlenme, `/api/auth/*`, eski SOS) `kimlik.eski_uc` bağımlılığıyla varsayılan olarak kapalı; bayrak (`QUAKEMIND_ESKI_UCLAR=1`) verilmezse 404. `deploy/` altında bu bayrak açılmıyor `[K]`. **Canlıda bu bayrak açılmamalı**; açılırsa açık geri gelir.

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

## J-37 🟡 Sert rotanın 422 mesajı ağ kopukluğunu kapanma sanıyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — eski uca ait · **Bulundu:** 21 Eylül 2026 · **İlgili:** J-34

**Ölçüm.** J-34 uçtan uca koşusunda 20 rastgele çiftin 4'ünde iki modda da yol yok. Tam
grafta (hiç kenar gizlenmeden) de yok; dört çiftin dördünde ters yönde rota bulunuyor.
Sebep: araç ağı yönlü (tek yön sokaklar) ve analiz kutusunun kenarında kesiliyor. Sert
mod buna "Bu iki nokta arasinda guvenli bir baglanti bulunamadi. Yol tamamen kapali
olabilir." diyor (`uclar/rota.py`) — kapanmayı suçluyor.

**Yapılacak.** 422'den önce tam grafta yol olup olmadığına bak: yoksa "ağda bu yönde yol
yok (tek yön / kutu sınırı)", varsa "kapanmalar yüzünden yol yok" de. Mesaj değişikliği
yanıt metnini değiştirdiği için duman imzası yeniden kaydedilmeli.

**Temizlik (18 Kasım 2026).** İleti eski `/api/road_damage/route` ve `/safe_route` uçlarında (`uclar/rota.py`); ikisi de `kimlik.eski_uc` ile varsayılan kapalı (404). Konsol ve sevk J-171'den beri yeni motoru kullanıyor (`/api/guzergah`); o, ağ dışı noktayı ayrı iletiyle (`AG_DISI`) bildiriyor. `[K]`

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
**Durum:** KAPALI (18 Kasım 2026, temizlik) — geçersizleşti · **Bulundu:** 15 Eylül 2026

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

**Temizlik (18 Kasım 2026).** Maddenin andığı yoklama uçları (`/api/sos/alerts`, `/api/team/claims`, `/api/chat/messages`, `naive_compare`) eski web uçları; J-53'ten beri `kimlik.eski_uc` bağımlılığıyla varsayılan olarak kapalı (404). Yeni konsol yoklamaz, tek SSE akışı dinler (J-46 ölçümü: boşta 137 sn'de 0 istek). Ağır işler işçide: uydu analizi `road_damage_pool`, metin `metin_analizi/isci.py`. Kalan tek süreç içi ağır iş kamera çıkarımı; o J-15'te izleniyor. `[K]`

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
**Durum:** KAPALI (18 Kasım 2026, temizlik) · **Bulundu:** 15 Eylül 2026

`apps/road_damage/utils/local_osm.py:_nearest_graph_node` tüm düğümleri Python
döngüsüyle tarıyor; `shortest_route_from_local_roads` bunu çağrı başına iki kez
çağırıyor. J-06 ile aynı çözüm (KD-ağacı).

**Temizlik (18 Kasım 2026).** `apps/road_damage/utils/local_osm.py:_nearest_graph_node` artık `scipy.spatial.cKDTree` ile aday kümesini daraltıp yalnız adaylarda tam haversine hesaplıyor (scipy yoksa eski tarama). Araç rotası da J-171'den beri ayrı motorda (`arac_rotasi.py`, kenara oturtma). `[K]`

---

## J-11 🟡 Harita sayfasında beş ayrı polling döngüsü
**Durum:** KAPALI (18 Kasım 2026, temizlik) — yeni konsolda yok; eski web'e ait · **Bulundu:** 15 Eylül 2026

`command/map/page.tsx` aynı anda beş `setInterval` çalıştırıyor (TEAM 2,5 s ·
SOS 6 s · NLP 6 s · DEBRIS 6 s · ROAD_DAMAGE 20 s), ayrıca Sidebar 8 s, chat 4 s,
bildirim 10 s. Dakikada ~50 HTTP isteği. J-07 ile birleşince backend'i sürekli
meşgul tutuyor.

**Yapılacak.** Tek bir `/api/live/state` birleşik ucu veya SSE/WebSocket ile
sunucu-itmeli akış. Kısa vadede: pollingleri tek bir zamanlayıcıda birleştir.

**Temizlik (18 Kasım 2026).** Beş yoklama döngüsü eski webin `command/map/page.tsx` sayfasında. Yeni konsolda uç yoklayan zamanlayıcı yok (kural 4); konsoldaki `setInterval`'lar yalnız yerel saat ve akış bekçisi. Ölçüldü `[Ö]`: birleşik konsol, genel mod, boşta, 137 sn (dakika değişimi dahil) → akış dışında **0 istek**. Eski web açık kaldıkça döngüler orada sürer; eski webin akıbeti J-168 ile aynı karar.

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

## J-141 🔴 Sunucuya ulaşılamazken eşitleme worker'ı sonsuz döngüye giriyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi · **Ölçüldü**

`mobile/sync/.../IncidentSyncWorker.kt:34` `while (true)` + `IncidentDao.kt:20` `claimPendingBatch`
`PENDING` **ve** `FAILED` kayıtları çekiyor. Ağ hatasında kayıt `FAILED` yapılıyor, döngü aynı
çalışmada onu hemen yeniden çekiyor; `Result.retry()` satırına hiç ulaşılmıyor, WorkManager backoff'u
devreye girmiyor.

**Ölçüm.** Backend durduruldu, 8000 portuna bağlantı sayıp yanıt vermeden kapatan bir dinleyici
kondu, uygulamadan tek ihbar gönderildi: **80 sn'de ~12 000 bağlantı (~150/sn), uygulama %112 CPU**,
kendiliğinden durmadı. Afet anında sunucu çöktüğünde pil tükenir, sunucu dönünce de boğulur.

**Çözüm önerisi.** Bir çalışmada yalnız `PENDING` al ya da kurtarılabilir hatada döngüden çıkıp
`Result.retry()` dön.

**Temizlik (18 Kasım 2026).** `mobile/sync/.../worker/IncidentSyncWorker.kt`: kurtarılabilir hatada kayıt `FAILED`, partinin kalanı `PENDING` yapılıyor ve döngüden `Result.retry()` ile çıkılıyor; WorkManager geri çekilmesi devreye giriyor `[K]`. Cihazda yeniden ölçülmedi.

## J-142 🟠 İhbar formundaki kategori, aciliyet ve kişi sayıları sunucuya gitmiyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi · **Ölçüldü** · **İlgili:** CLAUDE.md §2

`BackendServices.kt:166` gövdeye yalnız `tur`, `metin`, `lat/lon`, `konumKaynagi` koyuyor. Formda
"Enkaz / Mahsur · Kritik · 1 mahsur kişi" seçilip gönderildi; veritabanındaki kayıt:
`tur=metin, etiket="Model incelemedi", ek={"konumKaynagi":"manuel"}`. Konsol bunun kritik enkaz
ihbarı olduğunu göremez. Çevrimdışı kuyruk yolu da (`IncidentSyncWorker.kt:41`) `IncidentDraft`'ı
kurarken `urgency`, `peopleCount`, `injuredCount`, `locationSource` alanlarını doldurmuyor →
varsayılana düşüyor. Backend tarafında da bu alanları taşıyacak yer yok (`IhbarIstegi` yalnız
`kisiSayisi` ve `ihtiyaclar` biliyor); sözleşme iki tarafta birlikte genişletilmeli.

**Temizlik (18 Kasım 2026).** Mobil gövdeye `bildirilenKategori`, `bildirilenAciliyet`, `mahsurSayisi`, `yaraliSayisi` ekleniyor (`BackendServices.kt`); çevrimdışı kuyruk da bu alanları dolduruyor. Sunucu `IhbarIstegi` bunları kabul edip saklıyor (`uclar/ihbar.py`), konsol ihbar ayrıntısında "Bildirilen …" satırlarıyla gösteriyor `[K]`.

## J-143 🟠 İhbar formu GPS kullanmıyor; afetzededen koordinat elle isteniyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi · **Emülatörde görüldü** · **İlgili:** afetzede UX kararları

Ana ekran "Konum hazır · ±5 m" derken ve SOS ekranı GPS'i sorunsuz alırken `ReportScreen.kt:210`
"GPS bu formda otomatik alınmıyor" diyip enlem/boylam istiyor. Alanlar rakam klavyesi değil tam
QWERTY açıyor (`KeyboardType.Decimal` yok); emülatörde otomatik tamamlama boylama kendiliğinden
`" ft"` ekledi. GPS varsayılan olmalı, elle giriş yedek kalmalı.

**Temizlik (18 Kasım 2026).** İhbar formu cihaz konumunu varsayılan alıyor, elle giriş yedek (`ReportScreen.kt`, `manualLocation`); koordinat alanları `KeyboardType.Decimal` `[K]`.

## J-144 🟠 Risk ekranı etkenleri atıyor ve "servis bildirmedi" diyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi · **Ölçüldü** · **İlgili:** CLAUDE.md §1

`BackendServices.kt:408` `factors = emptyList()` sabit. Aynı istekte backend
`factors: {"Kisa vadeli risk": 0.25, "Uzun vadeli tehlike": 0.43, "Fay etkisi": 1.0}` dönüyor
(Defne, 36.2021 / 36.1612). Ekranda "Servis bu analiz için ek etken bildirmedi" yazıyor — doğru değil.

**Temizlik (18 Kasım 2026).** Mobil artık `factors` alanını okuyup listeliyor (`BackendServices.kt`). Sunucu yanıtı bu alanı taşıyor; birleştirmede `tests/test_mobile_risk_bridge.py` `riskScore`, `factors` ve `lastUpdate`'i gerçek modelle sınıyor `[K]`.

## J-145 🟠 `/api/oturum/misafir` sınırsız hesap açıyor; kişi başı ihbar sınırı aşılıyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi · **Ölçüldü** · **İlgili:** CLAUDE.md §5

`backend/uclar/oturum.py:58` kimliksiz, hız sınırsız; her çağrıda yeni `afetzede` hesabı. 30 misafir
art arda → 30 × 201; her biriyle SOS → 10 × 201. Her misafir yeni "kişi" olduğundan
`KISI_BASI_SINIR` anlamını yitiriyor; `/api/sos`'ta zaten sınır yok (eski sorun), `/kayit` de
sınırsız (eski sorun). Sahte SOS yağmuru riski → IP başına hız sınırı gerekli.

**Temizlik (18 Kasım 2026).** `/api/oturum/misafir` IP başına dakikada 5 yeni oturumla sınırlı (`MISAFIR_IP_SINIRI`; geçerli çerezle gelen aynı hesabı alır). Kayıt (`hiz_siniri.kayit_kontrol`) ve SOS (hesap başına tek açık çağrı + dakikada 6 basış) da sınırlı. Testler: `test_misafir_ip_siniri_...`, `test_sos_siniri_kullaniciya_ozel` `[K]`.

## J-146 🟡 Birleştirme sırası, klasör yeniden adlandırma ve mobil kapsamı karar bekliyor
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #12 ile karara bağlandı

- PR `main`'e değil #4'ün dalına (`feat/altlik-hf-otomatik-indirme`) açık: önce #4, sonra taban `main`.
- `QuakeMindBackend/` → `backend/` (~640 dosya): açık dallar (#3 dahil) ve yerel
  `QuakeMindBackend/venv` kurulumları etkilenir. Belgelerde yalnız yol değişmiş (denetlendi).
- CLAUDE.md §10 mobili kapsam dışı sayıyor; PR Flutter uygulamasını cihaz içi `bina.tflite` ve
  `catlak.tflite` ile siliyor. `PROJE_DOSYASI.md:71` hâlâ "Flutter mobil istemci" diyor.

**Temizlik (18 Kasım 2026).** (1) Birleştirme sırası: #4 main'de; #7 ve #6–#11 tek PR'da birleştirildi (UtBird/QuakeMind#12). (2) `QuakeMindBackend/` → `backend/` kabul edildi; yığının eklediği dosyalar yeni klasöre taşındı. (3) Mobil: `CLAUDE.md` ve `PROJE_DOSYASI.md` artık `mobile/` altındaki Android uygulamasını anıyor (Flutter klasörü kalktı) `[K]`. Bazı belgelerde eski klasör adı hâlâ geçiyor; çalışmayı etkilemiyor.

## J-148 ⚪ PR #5 küçük notlar
**Durum:** KAPALI (18 Kasım 2026, temizlik) — PR #7'de düzeltildi

- `backend/fastapi_app.py:135` doğrudan çalıştırınca varsayılan `0.0.0.0` (API yerel ağa açılır).
- `BackendClient.kt:47` yenileme jetonu düz `SharedPreferences`'ta.
- `start.sh` "konsol klasörü yok" diyor ama denetlediği `quakemind-web`.
- PR açıklaması "`QuakeMinds/` altında" diyor; klasörler kökte.

**Temizlik (18 Kasım 2026).** `fastapi_app.py` doğrudan çalıştırınca `QUAKEMIND_HOST` yoksa `127.0.0.1`; yenileme jetonu cihazda şifreli saklanıyor (`BackendClient.kt`, `*_encrypted` ve eski düz kaydı taşıma); `start.sh` iletisi denetlediği klasörü (`quakemind-web`) doğru adlandırıyor `[K]`.

## J-150 🟠 Tatbikat sağ paneli, uzama ölçülemeyen koşuda çöküyordu
**Durum:** KAPALI (12 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü**

Defne / Elektrik Mah., Hızlı model (SegFormer-B0), 5 ekip / 5 kişi / tohum 42: model %0,26 piksel hasar
buldu, 4 kenar kapandı, yalnız **1 çift** oluştu ve son adımı yürüme gerektirdiği için uzama hesabına
girmedi. Sunucu bu durumda bilerek `olcum.ortalamaUzamaYuzde = null` ve kıyas kollarında
`ortalamaSureDk = null` döndürüyor (`tatbikat.py:967`, `:598`). Konsol `null.toFixed` ile çöktü:
"Bu panel açılamadı" (`simulasyon.tsx:500`). Kıyas kollarında aynı durumda "NaN dk" yazacaktı.

**Düzeltme.** `veri/simulasyon.ts` tipleri `number | null` yapıldı. Panel uzama yoksa "Uzama
hesaplanamadı: uzama yalnız araçla ulaşılan çiftlerden alınır, bu koşuda öyle çift yok", kol için
"araçla ulaşılan görev yok" yazıyor. `tsc -b` ve `kontrol:token` temiz; tarayıcıda aynı koşuyla
panelin açıldığı görüldü.

**Açık kalan.** Hızlı modelle bu alanda tanıtım içi boş kalıyor (1 afetzede, kıyas yok). Sunumda
"En iyi" model kullanılmalı (DEMO_CALISTIRMA.md zaten öyle diyor).

## J-152 🔴 Risk uçlarında kimlik denetimi yok; canlı veri tazeleme istek yolunda
**Durum:** KAPALI (13 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü** · **İlgili:** CLAUDE.md §3, §5

`uclar/risk.py`: `/api/risk/predict` ve `/api/risk/refresh_live_data` `Depends` almıyor (yalnız
`/api/risk/iller` alıyor). Oturumsuz `curl -X POST /api/risk/predict` → 200 ve tam skor döndü.
`refresh_live_data` oturumsuz herkesin Kandilli ve USGS'e dış istek attırıp `query.csv`'yi yeniden
yazdırmasına izin veriyor. `predict` içindeki `refreshData=true` da dış servisi istek yolunda çağırıyor.

**Düzeltme (13 Kasım).**
- `POST /api/risk/predict` artık giriş ister; her rol kullanabilir.
- `refreshData` (dış servise istek, `query.csv`'yi yeniden yazma) yalnız koordinatör ve
  yöneticide çalışır; diğer rollerde yok sayılır.
- `POST /api/risk/refresh_live_data` yalnız koordinatör ve yönetici.
- Ölçüldü (canlı API):
  - tahmin jetonsuz 401, saha 200, koordinatör 200;
  - saha `refreshData=true` → 200 ve katalog dosyası değişmedi;
  - tazeleme jetonsuz 401, saha 403;
  - `fault_lines` açık veri olarak açık kaldı.
- **Etkisi:** eski web (`quakemind-web`) ve eski Flutter uygulaması risk uçlarını jetonsuz
  çağırıyor; risk ekranları 401 alır. Eski web'in giriş uçları zaten kapalı (J-53), Flutter PR #5
  ile değişiyor. Yeni konsol etkilenmez. Tazelemenin istek yolunda dış servise gitmesi (§3) hâlâ
  böyle; artık yalnız koordinasyon tetikleyebiliyor.

## J-154 🟠 Tatbikat kıyas kolları dakikaya yuvarlanıp QuakeMind farkını siliyordu
**Durum:** KAPALI (12 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü**

Defne / Elektrik Mah., En iyi model (U-Net MiT-B4), tohum 42. Koşu 84,1 sn sürdü (AI 73,3 sn),
12 kapalı kenar, 9 çift, kollar 6/9 göreve araçla ulaştı. Sunucunun verdiği ortalamalar:
bilmeyen ekip 2,400 · telsizle paylaşan filo 2,233 · QuakeMind 1,573 dk. Panel
`sureMetni(Math.round(...))` ile üçünü de **"2 dk"** yazıyordu. Tanıtımın ana mesajı (kapanmayı
önceden bilmek erişimi kısaltır) ekranda görünmüyordu. 10 dakikanın altı artık bir ondalıkla
yazılıyor: 2,4 · 2,2 · 1,6 dk. `tsc -b` ve `kontrol:token` temiz; tarayıcıda görüldü.

## J-156 🟠 Giriş üç kapıya ayrıldı; ekip hesaplarını koordinasyon açıyor
**Durum:** KAPALI (12 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü** · **İlgili:** CLAUDE.md §5, J-155

**İstek (kullanıcı).** Girişte hesap türü seçilsin. Hesap açma yalnız afetzede için olsun. Ekip
hesaplarını biz açalım ve denetleyebilelim.

**Yapılan.**
- **Giriş kapıları:** giriş ekranında Afetzede · Saha ekibi · Koordinasyon seçimi. Kapı rol
  **vermez**: `kimlik.giris_yap(…, kapi)` şifre doğrulandıktan sonra hesabın depodaki rolünü
  kapıyla karşılaştırır. Uymazsa 403 döner ("Bu hesap … hesabı değil. Yukarıdan “Saha ekibi”
  girişini seç"), oturum açılmaz, `son_giris` yazılmaz. Yanlış şifrede kapıdan bağımsız tek 401
  döner, hesabın varlığı sızmaz. Kapı gönderilmezse eski davranış sürer (mobil istemci, PR #5).
  Son seçilen kapı tarayıcıda hatırlanır (`localStorage`, try/catch'li).
- **Hesap açma** yalnız Afetzede kapısında. Saha ve Koordinasyon kapılarında "hesabını
  koordinasyon merkezi / yönetici açar" yazıyor.
- **Ekip hesabı açma:** `POST /api/oturum/kullanicilar`. Koordinatör yalnız saha hesabı açar;
  yönetici koordinatör ve yönetici hesabı da açar. Açarken ekibe bağlanabilir. Afetzede hesabı
  buradan açılmaz (422).
- **Şifre:** sunucuda 12 karakterlik tek seferlik şifre üretilir; karıştırılan 0/O, 1/l/I harfleri
  yok. Yalnız yanıtta bir kez döner, depoda özeti kalır. `POST /api/oturum/kullanicilar/{id}/sifre`
  ile yenilenir; eski şifre ve açık oturumlar düşer. Kimse kendi hesabında bu işlemi yapamaz.
- Kayıt ucu artık `son_giris` yazıyor (J-155'te kalan madde kapandı).
- **Kullanıcılar ekranı yeniden düzenlendi.** Sol panel: yeni hesap (tür, ad, e-posta, ekip) ve
  tek seferlik şifre kartı (kopyala / not aldım). Sağ panel: hesaplar (gruplar ve sayıları, arama,
  rol değiştir, şifreyi yenile, ekibe bağla).

**Ölçüm.** `tests/test_oturum_rol.py` 12/12 geçti; ayrı geçici SQLite kullanıyor. `tsc -b` ve
`kontrol:token` temiz. Token kuralı bir keyfi `grid-cols-[…]` değerini yakaladı, düzeltildi.
Tarayıcıda:
- Koordinatör "Deneme Ekip Üyesi" (`deneme-ekip@quakemind.local`) hesabını AKUT 1'e bağlı açtı.
- Saha hesabıyla Afetzede kapısı → 403 ve doğru kapı mesajı.
- Yeni hesap Saha ekibi kapısından → `/ekip`, AKUT 1.
- Giriş ekranı 375 px genişlikte taşmıyor.

**Açık.**
- Tek seferlik şifreyle ilk girişte şifre değiştirme zorunlu değil.
- Rol ve şifre işlemlerinin denetim izi yok.
- Hesap kapatma (silme / askıya alma) yok.
- `deneme-ekip@quakemind.local` deneme hesabı yerel veritabanında duruyor.

## J-157 🟠 Hesap yönetimi tek sayfada: düzenle-kaydet, askıya alma, ilk girişte şifre, kayıt defteri
**Durum:** KAPALI (13 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü** · **İlgili:** CLAUDE.md §5, J-155, J-156

**Kullanıcının bulduğu eksik.** Ekipsiz bir saha hesabı (`ali@gmail.com`) açılmıştı. Ekip atamak
için ayrı Ekipler ekranına gitmek gerekiyordu. Koordinatörün bütün hesapları görüp değiştirip
kaydedeceği bir yer yoktu. Ayrıca J-156'nın üç açık maddesi vardı: ilk girişte şifre
değiştirme, denetim izi, hesap kapatma.

**Yapılan.**
- **Hesaplar sayfası** (Kullanıcılar sekmesi) tam sayfa oldu (`modlar.ts` `sayfa: true`). Harita
  altında kurulu kalır, yalnız örtülür (CLAUDE.md §6).
  - Tabloda herkes var: ad / e-posta, rol, ekip ("Ekip yok" vurgulu), durum (Aktif / Askıda /
    Şifre bekliyor), son giriş.
  - Gruplar sayılarıyla: Tümü, Saha, Ekibe bağlı olmayan saha, Şifresini koymamış, Askıda,
    Koordinasyon, Afetzede. Ekipsiz saha varsa üstte uyarı çıkar.
  - Satıra tıklayınca **düzenleme çekmecesi** açılır: ad, rol, ekip, durum ve tek **Kaydet**
    düğmesi ("Kaydedince: ekip yok → AKUT 1" özeti, Geri al). Çekmecede geçici şifre üretme ve
    kişinin işlem geçmişi de var.
  - "Yeni ekip hesabı" çekmecesi: açılınca doğrudan o hesabın düzenleme çekmecesine geçer.
  - **Kayıt defteri** sekmesi.
- **Tek kaydet ucu:** `PATCH /api/oturum/kullanicilar/{id}` (ad, rol, ekipId, askida).
  Önce hepsi denetlenir, sonra uygulanır: bir alan reddedilirse hiçbiri değişmez (testte
  doğrulandı). `ekipId: null` ekipten çıkarır. Gönderilmeyen alan değişmez.
- **Askıya alma:** `kullanicilar.askida` sütunu. Askıdaki hesap doğru şifreyle de giremez (403
  "Hesabın askıya alınmış"); elindeki erişim jetonu, yenileme ve canlı akış o an düşer. Kayıtları
  silinmez, geri açılabilir. Kalıcı silme bilerek yok: kişinin SOS ve ihbar kayıtları hesaba bağlı.
- **İlk girişte şifre:** `kullanicilar.sifre_degismeli` sütunu.
  - Koordinasyonun açtığı ya da şifresini yenilediği hesapta bayrak açılır.
  - Bu hesap `/ben` ve `POST /api/oturum/sifre` dışındaki **her** korunan uçta 403 alır; zorunluluk
    sunucuda.
  - Konsol `/sifre-degistir` ekranına zorlar (`RolKapisi`, `acilisYolu`).
  - Şifre değişince bütün eski oturumlar düşer, bu cihaza yeni oturum verilir.
- **Kayıt defteri:** `hesap_kayitlari` tablosu (yalnız eklenir). Hesap açma, rol, ekip, ad, askı,
  şifre yenileme ve kişinin kendi şifresini değiştirmesi; kim, kime, ne zaman.
  `GET /api/oturum/hesap-kayitlari`. Kişi başına geçmiş çekmecede görünür.
- **Canlı akış:** yeni `hesap` mesajı (yalnız konsol rollerine). Başka bir koordinatörün
  değişikliği açık listelerde de görünür. Yoklama yok (CLAUDE.md §4).
- **İstemci düzeltmesi:** jeton yenilemesi `/api/oturum/` altındaki her yolda atlanıyordu. Hesap
  ekranı 15 dakika açık kalınca 401'de kalacaktı. Artık yalnız giriş, kayıt, yenileme ve çıkış
  uçlarında atlanıyor. `apiGet` sunucunun hata açıklamasını da gösteriyor.
- Yanlış "şu anki şifre" 400 dönüyor. 401 olsaydı istemci gereksiz yere jeton yenileyip isteği
  tekrar gönderirdi.

**Ölçüm.**
- `tests/test_oturum_rol.py` 16/16 geçti (yeni: zorunlu şifre, askı, tek kaydet ve atomiklik,
  kayıt defteri).
- `tsc -b` ve `kontrol:token` temiz.
- Korunan 9 uç demo jetonuyla 200 döndü, oturumsuz 401 aldı.
- Var olan veritabanına sütunlar ve tablo açılışta veri kaybı olmadan eklendi.
- Tarayıcıda "Deneme İki" hesabıyla:
  1. Ekipsiz açıldı.
  2. Çekmeceden AKUT 1 seçilip kaydedildi.
  3. Askıya alındı; doğru şifreyle giriş 403 aldı.
  4. Yeniden etkinleştirildi.
  5. Geçici şifreyle giriş `/sifre-degistir`'e gitti; `/ekip`'e elle gidince de geri itildi.
  6. Şifre değişince AKUT 1 ekip ekranı açıldı.
  7. Kayıt defterinde 5 satır doğru sırayla, yapanıyla göründü.

**Açık.**
- Kayıt defteri 13 Kasım 2026'da başladı; daha önceki işlemler yok.
- `deneme-iki@quakemind.local` ve `deneme-ekip@quakemind.local` deneme hesapları yerel
  veritabanında duruyor. İstenirse askıya alınabilir.
- E-posta değiştirme yok.

## J-159 🔴 SOS ve ihbar kimlikleri 32 bitti: ~77 bin kayıtta çakışma olasılığı %50
**Durum:** KAPALI (13 Kasım 2026, dal `teslim-toparlama`) · **Hesap + ölçümde görüldü**

J-158 ölçümünde 1 milyon satır doldururken `UNIQUE constraint failed: hasar_noktalari.id` alındı.
Bu, ölçüm betiğinin kısa kimliklerinden geliyordu ama depoda da aynı desen vardı:
`sos-` + `uuid4().hex[:8]` (32 bit), `ihb-` 32 bit, `grv-` 32 bit, `hsr-` ve `kap-` 40 bit,
`ekp-` 24 bit.

Doğum günü sınırı: 32 bitte 10 bin kayıtta %1, ~77 bin kayıtta %50 çakışma. Çakışan `INSERT`
`IntegrityError` → HTTP 500 olur; **afetzedenin SOS'u kaydedilmez**. Büyük bir afette bu sayılara
ulaşılabilir.

**Düzeltme.** SOS, ihbar, görev, hasar noktası ve yol kapanması 64 bit (`hex[:16]`), ekip 40 bit.
Mevcut kayıtlar aynı kalır (kimlik `TEXT`). Kimlik uzunluğuna bağlı kod bulunmadı.
`tests/test_oturum_rol.py` 16/16 geçti.

**Açık.**
- `bil-` (bildirim, 32 bit) ve eski uçlar (`usr-`, `blk-`) düşük hacimli olduğu için bırakıldı.
- Çakışmada yeniden deneme yok; 64 bitte gerek görülmedi.

## J-160 🔴 Hasar analizi drone görüntüsünde "0 kapalı yol": alan görüntüye taşınmıyor, çözünürlük sessizce düşüyordu
**Durum:** KAPALI (13 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü** · **İlgili:** J-20, J-76, J-35

**Görülen (kullanıcı).** Hasar analizi → OpenAerialMap → "Help.NGO · Hatay - Defne - Elektrik Mah."
seçildi, analiz başlatıldı. Sonuç 0 kapalı yol, 6 482 açık. Kullanıcı daha önce aynı yerde kapalı yol
görmüştü.

**Sebep (ölçüldü, aynı model ve görüntü, veritabanı kopyasında).**

| Analiz alanı | Kullanılan zoom | İncelenen alan | Kapalı yol | Süre |
|---|---|---|---|---|
| Ekrandaki: "Şehir merkezi" Antakya + 2,5 km | z17 (0,96 m/px); z18 istendi | 3,9 / 25,1 km² | **0** | 69 sn |
| Görüntünün kendi alanı (katalog `analizBbox`) | z18 (0,48 m/px) | 0,38 km² | **8** | 23 sn |

1. Listeden görüntü seçmek analiz alanını **değiştirmiyordu**. Görüntü (~0,5 km'lik drone sahnesi)
   alanın ~%1'ini kapsıyordu. Panel uyarı yazıyor ama analiz yine başlıyordu.
2. Sunucu (`fetch_satellite_area`) 64 karolık pencereyi analiz merkezinden kırpıyor. Merkez görüntünün
   dışında kalınca z18'de karo bulamadı ve bunu "bu zoomda karo yok" sayıp **sessizce z17'ye indi**.
   Model eğitim ölçeğinin iki katı kaba ve çoğu boş görüntü gördü; standart çözünürlük kuralı (J-76)
   delindi.
3. Sonuç ekranı bu koşuda "Bu görüntüde yolu kapatan hasar bulunmadı" dedi. Yanıltıcı: incelenen
   kutunun çok küçük bir kısmında görüntü vardı.

**Düzeltme.**
- `veri/analiz.ts` `goruntuyeTasinmisAlan`: listeden görüntü seçince, kapsama %95'in altındaysa alan
  görüntünün üstüne taşınır. Görüntü alandan küçükse alan görüntünün kendisi olur; büyükse boyu
  korunup içine kaydırılır. Mod "Alan çiz" olur, harita oraya uçar.
- Kapsama `EN_AZ_KAPSAMA` (%50) altındaysa "Analizi başlat" kapalı; yerine "Alanı görüntüye taşı"
  düğmesi.
- Başlatınca harita şehir merkezine değil analiz alanına uçar. Künyedeki yarıçap gerçekte incelenen
  kutudan yazılır (eskiden hep hazır ayarın 2,5 km'si).
- `worker.py`: OpenAerialMap (özel karo) kaynağında istenen zoomda karo yoksa koşu **durur** ve
  "Seçilen görüntü analiz alanının merkezinde yok… alanı görüntüye taşı" der. Wayback ve Esri'nin
  alt zooma inmesi değişmedi.
- Sonuç ekranı: `validPixelRatio` %50'nin altındaysa "görüntü incelenen kutunun ~%X kadarını
  dolduruyor" notu çıkar. Hiç kapalı yol yoksa sunucunun "hasar bulunmadı" önerisi gizlenir.

**Doğrulama.**
- Betikte: ekrandaki ayar artık açıklamalı hatayla duruyor; görüntü alanı z18'de 8 kapalı yol.
- Tarayıcıda, API ile uçtan uca:
  - Defne/Elektrik'e tıklanınca kapsama %1 → %100 oldu, analiz başladı;
  - sonuç **8 kapalı / 662 açık segment, z18, 0,48 m/px**;
  - haritada 8 kırmızı segment çizildi.
  - Bu koşu gerçek veritabanına normal kullanım gibi yazıldı.
- `tsc -b` ve `kontrol:token` temiz.

**Not.** Drone sahnelerinde görüntü kutunun ~%39'unu doldurur (katalogda `gecerliPikselOraniZ18`
0,387); kenarlar düzensizdir. Not bu yüzden "taşı" demez, yalnız sayıların görüntülü kısmı anlattığını
yazar.

**Açık.** Sınır kutusundan hesaplanan kapsama görüntünün gerçek izinden büyük olabilir. Gerçek iz
(OAM footprint çokgeni) kullanılmıyor.

## J-161 🟠 Hasar analizi ekranı: panel genişlik sıçraması, yanıltıcı alan ayarları, yakın çekim seçeneği
**Durum:** KAPALI (13 Kasım 2026, dal `teslim-toparlama`) · **Ölçüldü** · **İlgili:** J-160, J-76, J-20, J-26

**Kullanıcının bildirdikleri.** (1) Sağ paneldeki iş alanı küçük başlıyor, ilerleme çubuğu gelince
sağa doğru büyüyor. (2) "Yakından bakınca daha iyi buluyor"; bu da eklenmeli mi? (3) Ekranın
UI/UX'i daha kullanışlı olsun.

**1. Panel genişliği.** `kabuk/Panel.tsx`'te `section` sabit genişlikli sütunun içinde ama `w-full`
değildi. İçerik kadar daralıyor, ilerleme çubuğu gelince genişliyordu (bütün modlarda, iki panelde).
`w-full` eklendi. 1 600 px'te ölçüldü: sağ panel 336/336, sol 292/292 px. Analiz boyunca genişlik
sabit kaldı.

**2. Hazır ayarlar yanıltıcıydı (yeni bulgu).** Analiz her zaman eğitim ölçeğinde (z18 ≈ 0,48 m/px)
koşuyor ve `fetcher.py` en çok 8×8 karo indiriyor, yani tek koşu **~0,99 × 0,99 km**. Eski hazır
ayarlar "Standart 2,5 km", "Geniş alan 4 km" diyordu: 25–50 km² seçiliyor, ortadaki ~1 km² dışında
hiçbir yer incelenmiyordu. Hazır ayarlar kaldırıldı; varsayılan yarıçap 0,5 km. Ekran tek koşunun
sınırını hesaplayıp alan sığmazsa açıkça yazıyor.

**3. Yakın çekim (ölçüldü, veritabanı kopyasında, Defne/Elektrik aynı kutu).**

| | z18 (eğitim ölçeği, 0,48 m/px) | z19 (0,24 m/px) |
|---|---|---|
| Kapalı yol | 8 | 19 |
| Hasar oranı (görüntülü kısım) | %1,42 | %1,78 |
| İncelenen alan | 0,38 km² | 0,24 km² (tek koşu dörtte bir) |
| Süre | 64 sn | 44 sn |

Gözle bakınca z19'un yeni bulduklarının çoğu enkaza benziyor. **Doğruluk ölçülmedi:** yer gerçeği
yok. Model 0,3–0,5 m/px ile eğitildi, 0,24 bu aralığın dışında; J-26'da yakınlaştıkça yanlış alarmın
daha hızlı arttığı görülmüştü.

Karar `[T]`: **isteğe bağlı, varsayılan kapalı** "Yakın çekim (deneysel)" anahtarı.
- İstekte `yakinCekim`, işçide zoom+1; sonuç künyesine `yakinCekim` yazılır.
- Standart çözünürlük kuralı (J-76, 26 Eylül kullanıcı kararı) varsayılan olarak değişmedi.
- Makaleye taşınmaz: yalnız koşu sayısı ölçüldü, doğruluk ölçülmedi.

**4. Ekran yeniden düzeni (`modlar/hasar.tsx`).**
- **Sol panel üç adım:**
  1. Görüntü: kaynak seçimi (deprem sonrası OAM / Wayback / güncel); OAM görüntüleri kart olarak
     (drone ya da uydu, sağlayıcı, tarih, depremden kaç gün sonra, kapsama çubuğu); tarih aralığı
     katlanır.
  2. Alan: görüntünün tamamı, alan çiz, çokgen, nokta çevresi, şehir merkezi.
  3. Özet ve Başlat: alan, görüntü, çözünürlük; başlatılamıyorsa nedeni yazar.
- **İnce ayar:** hassas tarama ve yakın çekim anahtarları, yarıçap (yalnız nokta ve şehir
  merkezinde), eşik, son işleme, model.
- **Sağ panel:** aşama göstergesi (görüntü → yol ağı → model, "12/16 parça" ile → kapanan yollar →
  sonuç). Sonuçta üç büyük sayı (kapalı yol, açık yol, hasar), öneri, "Sonuca yaklaş" ve "Bu ağda
  rota planla" düğmeleri; künye katlanır bölümde. Hata olursa sebep kutu içinde.

**Doğrulama.**
- `tsc -b` ve `kontrol:token` temiz.
- Tarayıcıda:
  - Defne/Elektrik seçildi; alan "Görüntünün tamamı" (0,46 × 0,50 km, kapsama %100, z18).
  - Yakın çekim anahtarı özeti z19 / 0,24 m/px yaptı, geri alınınca z18'e döndü.
  - Analiz aşama aşama izlendi (13/16 → 16/16 parça → %90 → %97 → bitti).
  - Sonuç 8 kapalı / 662 açık, %0,5 hasar.
- Ekran görüntüsü alınamadı (tarayıcı paneli gizliydi); düzen DOM ölçümüyle doğrulandı.

**Ek düzeltme (aynı gün, kullanıcı bildirdi): mahalle sahneleri listeden kayboluyordu.**
- Görüntü araması o anki analiz alanında yapılıyordu. J-160'tan sonra görüntü seçmek alanı
  0,5 km'lik sahne kutusuna küçülttüğü için liste de daraldı (11 → 3). Narlıca, Türünçlü gibi
  öbür mahalle sahneleri kayboldu.
- Arama artık seçili şehrin çevresinde (~8 km) yapılıyor; çizilen alan dışarı taşarsa birleşimi
  aranıyor. Şehir seçimi 1. adıma taşındı; şehir değişince alan ve görüntü seçimi sıfırlanıyor.
- Tarayıcıda: Defne seçilmeden önce de sonra da 11 sahne listelendi (Mansurlu da eklendi).
  Narlıca'ya geçince alan 0,34 × 0,53 km, kapsama %100 oldu.

**Açık.**
- Gerçek yer izi (OAM footprint çokgeni) kullanılmıyor; kapsama sınır kutusundan.
- Büyük alanı birden çok koşuya bölme (döşeme) yok; alan sığmazsa ortası incelenir.
- Yakın çekimin doğruluğu ölçülmeli; etiketli bir mahalle gerekir.

## J-162 🟠 Saha ekibi kapanmalardan kaçınan rotayı haritada göremiyordu; rol erişimi incelemesi
**Durum:** KAPALI (harita; konsol erişimi kararı J-163'te uygulandı) · **Görüldü** · **İlgili:** J-54, J-155, J-163, CLAUDE.md §5

**Bulgu (17 Kasım, rol rol ekran incelemesi).**
- Görev ekranında harita yoktu. Rota yalnız yazıyla veriliyordu: "olaya yoldan X km, ~Y dk,
  kapanmalardan kaçınır".
- "Telefonun haritasında aç" `geo:` bağlantısıyla telefonun kendi haritasını yalnız varış
  noktasıyla açıyor. O harita bizim kapanmalarımızı bilmez, ekibi kapalı sokağa sokabilir.
- Sunucu rotanın çizgisini zaten veriyordu (`gorev.rota`, `arac_rotasi.py`); ekran kullanmıyordu.
- Saha ekibi bilgisayarda (≥640 px) "Konsol" düğmesiyle, telefonda adres yazarak konsolun
  tamamına geçebiliyor. Bütün SOS'ları ve konumları görüyor; SOS'a ekip atayabiliyor.
- Kullanıcılar sayfası saha ekibine kapalıydı (sekme yok, sunucu 403), ama adres yazılınca boş
  sayfa iskeleti açılıyordu.

**Yapılan.**
- `ekip/GorevHaritasi.tsx`: görev kartında "Rotayı haritada göster". Rota (mavi, kapanmalardan
  kaçınır), yakındaki kapalı yollar (kırmızı), ekip ve olay noktaları, lejant ve kaynak. Altlık
  konsoldakiyle aynı yerel OSM paketleri: önce operasyon bölgesi, yoksa tek il paketi.
- Harita `React.lazy` ile ayrı yükleniyor. Ölçüldü: düğmeye basılmadan maplibre/deck.gl hiç inmedi
  (0 istek), basınca indi. "Telefonun haritasında aç" ikincil düğme oldu; altında "telefonun
  haritası kapalı yolları bilmez" uyarısı var.
- `KonsolKabugu`: rolüne kapalı mod adresten de açılmıyor (saha → `/konsol/kullanicilar` →
  `/konsol/genel`). Tarayıcıda doğrulandı.

**Doğrulama.**
- `tsc -b` ve `kontrol:token` temiz.
- 430 px telefon görünümünde `saha-demo` ile: harita açıldı (2 tuval), rota çizildi, rota kutusunda
  218 kapalı yol; kaydırmayla yakınlaşma çalışıyor.
- Deneme görevi şehirler arası (Antakya → Kahramanmaraş, 178 km); şehir içi bir görevle de
  bakılmalı.

**Karar (17 Kasım, kullanıcı).** Saha ekibi konsolu görür; koordinasyon işleri kapalı: (b).
Uygulaması ve sunucu yetkisi J-163'te.

## J-163 🟠 Saha ekibi koordinasyon işlerini yapabiliyordu; eski ve araştırma uçları oturumsuz açıktı
**Durum:** KAPALI · **Görüldü** · **İlgili:** J-53, J-152, J-162, CLAUDE.md §5

**Karar (17 Kasım, kullanıcı).** Saha ekibi konsolu görür, ama şunları görmez: Acil bildirim,
Simülasyon (tatbikat), SOS'a ekip gönderme, Ekip tanımlama. Ayrıca açık uçlar kapatılsın.

**Bulgu.**
- `POST /api/gorevler` ve `POST /api/sos/{id}/ata` saha rolüne açıktı. Saha kendi ekibini
  istediği olaya gönderebiliyordu.
- Konsolda Acil bildirim sekmesi ve Analiz menüsündeki Simülasyon saha ekibine görünüyordu.
  Sunucu ikisini de zaten reddediyordu (403); ekran boşuna açılıyordu.
- Ekip ekle / Düzenle / hesap bağlama zaten yalnız koordinasyona görünüyordu, sunucu da
  kısıtlıydı. Değişiklik gerekmedi.
- Oturumsuz yanıt veren 15 uç vardı:
  - eski web ve Flutter'ın bildirim ve sohbet uçları: `notifications/send_emergency`,
    `notifications/active`, `chat/send`, `chat/messages`;
  - makale ölçüm betiklerinin kapanma uçları: `simulate_closures`, `closures_from_mask`,
    `closures_from_emsr`, `naive_compare`, `reference_compare`;
  - eski rota uçları: `route`, `safe_route`, `assembly`, `calculate_custom_route`,
    `nearest_debris`;
  - analiz tanı görseli: `road_damage/gorsel/{id}/{ad}`.
- Kimlerin çağırdığı tarandı. Yeni konsol bunların hiçbirini doğrudan çağırmıyor; tanı görselini
  jetonla (`apiGorsel`) istiyor. Deha'nın Android uygulaması da (`upstream/codex/web-harita-yayin`,
  `mobile/`) çağırmıyor; o `bildirimler/aktif`, `afetzede/*`, `katman/kapanmalar` kullanıyor.

**Yapılan.**
- Sunucu: ekip gönderme (`POST /api/gorevler`, `POST /api/sos/{id}/ata`) yalnız koordinatör ve
  yönetici. Saha ekibi kendi görevini yürütmeye devam eder: görev durumu ve konum paylaşımı.
- Sunucu: eski ve araştırma uçlarının 14'ü J-53'teki `kimlik.eski_uc` bayrağının arkasında.
  Bayraksız 404 döner; `QUAKEMIND_ESKI_UCLAR=1` ile açılır. Ölçüm betikleri (`benchmark/
  full_scenario.py` vb.) zaten bayrak isteyen `team/claim`, `sos/alert` uçlarını kullanıyordu;
  bayrak gereksinimi yeni değil.
- Sunucu: tanı görseli giriş istiyor (saha, koordinatör, yönetici).
- Konsol:
  - `bildirim` ve `simulasyon` modlarına `roller` eklendi. Sekme, Analiz menüsü ve komut paleti
    gizliyor; adresle girilince Genel duruma yönleniyor (J-162).
  - SOS/ihbar ayrıntısında saha "Kim gidiyor"u görür; "Ekip gönder" yerine "Ekibi koordinasyon
    gönderir." yazar.
  - Tatbikat şeridi herkese görünür (gerçek olay değil uyarısı), "Tatbikat paneli" bağlantısı
    yalnız koordinasyona.
  - `kimlik/roller.ts`: ortak `koordinasyonMu`.

**Doğrulama.**
- `tests/test_uc_yetkileri.py` (yeni, 18 test):
  - 14 uç bayraksız 404, bayrakla açılıyor;
  - görsel: jetonsuz 401, afetzede 403, saha geçer;
  - saha ekip gönderemez (403), koordinatör gönderir (201);
  - saha konum paylaşabilir.
- `test_oturum_rol.py`, `test_depo_eszamanlilik.py` ile birlikte **38/38** geçti.
- Tarayıcıda `saha-demo` ile:
  - üst çubukta Acil bildirim, Kullanıcılar ve Simülasyon yok;
  - `/konsol/simulasyon` ve `/konsol/bildirim` adresleri `/konsol/genel`e yönlendi;
  - SOS ayrıntısında "Ekip gönder" düğmesi yok, not görünüyor.
  - Denemede yerel veritabanına "TEST J-163" etiketli tek bir SOS eklendi; bakıldıktan sonra silindi.
- Yerel API: `notifications/active` 404, `road_damage/route` 404, `gorsel` jetonsuz 401.
- `npx tsc -b`, `npm run kontrol:token` temiz.

**Etkisi.**
- Eski web (`quakemind-web`) ve Flutter (`quakemind/`) bildirim bandı, sohbet, güvenli rota ve
  toplanma alanı ekranları bayraksız çalışmaz. Kapsam dışılar (CLAUDE.md §7, §10).
- `araclar_uc_duman_testi.py` imzaları değişti: bu uçlar artık 404. Referans
  `testler/uc_imzalari.json` yeniden kaydedilmedi.
- Koordinatörün konsolda ekip gönderme düğmesi tarayıcıda ayrıca denenmedi; koşul kodda
  `koordinasyonMu` ile, sunucu tarafı testle doğrulandı.

**Karar (17 Kasım, kullanıcı): saha ekibi SOS çağrısını kapatabilir.** Sahada olan ekip
çağrının bittiğini ya da yanlış olduğunu ilk bilen taraftır. "Çağrıyı kapat…" düğmesi sahaya
görünür, `/api/sos/{id}/kapat` saha ve üstüne açık kalır; değişiklik yapılmadı.

**Açık.**
- `tests/test_road_damage_api.py::test_heatmap_offline_fallback_returns_200` bu değişiklikten
  önce de düşüyordu. Uç giriş istiyor (401), test jetonsuz çağırıyor. Rota testleri bayrakla
  çalışacak şekilde güncellendi (3/4 geçiyor).


## J-164 🟡 Konsol üst çubuğu 1024 px'te taşıyordu; hesap sayıları yüklenirken 0 görünüyordu
**Durum:** KAPALI · **Görüldü** · **İlgili:** J-56, J-157, ARAYUZ §6

**Bulgu (17 Kasım, koordinatör ekranı incelemesi, 1024×768).**
- Üst çubuğun içeriği 1 226 px, ekran 1 024 px: 202 px taşıyordu.
  - "Ara veya komut ver" üç satıra, "Afetzede ekranı" iki satıra kırılıyordu.
  - Canlı/Geçmiş rozeti ve çıkış (ad baş harfleri) düğmesi ekran dışında kalıyordu.
- Kullanıcılar sayfası liste gelene kadar "Hesaplar · 0", "Tümü · 0", "Saha ekibi · 0" yazıyordu.
  Bir iki saniye "hiç hesap yok" diye okunuyor; bilinmeyen sayı 0 diye gösterilmiş oluyor
  (CLAUDE.md §1).

**Yapılan.**
- `UstCubuk.tsx`, `Marka.tsx`: 1280 px altında
  - marka yazısı gizlenir, yalnız simge kalır;
  - arama düğmesi büyüteç simgesine, "Afetzede ekranı" ve "Görev ekranı" telefon/pano simgesine
    iner (ad `aria-label` ve `title`'da);
  - sekme dolgusu ve çubuk aralığı daralır.
- Sağdaki denetimler küçülmez (`shrink-0`, `whitespace-nowrap`). Yine sığmazsa yalnız mod
  sekmeleri yatay kayar. Analiz menüsü kayan alanın dışında; açılır listesi kırpılmaz.
- `kullanicilar.tsx`: liste gelmeden sayaçlar "—" yazar.

**Doğrulama (koordinatör, tarayıcıda ölçüldü).**

| Genişlik | Kip | Çubuk (içerik / ekran) | Sekmeler |
|---|---|---|---|
| 1024 | Canlı | 1 024 / 1 024 | kaymıyor |
| 1024 | Geçmiş + "Canlıya dön" | 1 024 / 1 024 | kaymıyor |
| 1440 | Canlı | 1 440 / 1 440 | tam yazılar |
| 900 | Geçmiş | 900 / 900 | kayıyor (385 / 523 px), Analiz menüsü tam görünüyor |

- Yeniden yüklemede sayaçlar önce "Hesaplar · — | Tümü · —", sonra "17".
- `npx tsc -b`, `npm run kontrol:token` temiz.


## J-165 🟠 Kamera tespiti çatlağa "binayı boşaltın" diyordu; analizlerin ve bazı işlemlerin kaydı tutulmuyordu
**Durum:** KAPALI · **Görüldü** · **İlgili:** J-50, J-51, J-54, J-157, B-03, CLAUDE.md §1

**Bulgu (17 Kasım, kullanıcı kamera ekranından bildirdi).**
- **Çatlak uyarısı uydurmaydı.**
  - `catlak.pt`'nin tek sınıfı var: `crack`. Çatlağın derin mi yüzeysel mi, taşıyıcı elemanda mı
    olduğunu ayırt etmiyor.
  - Uç ise güven %45'i geçince tespiti `CRITICAL` sayıyor ve "TAŞIYICI ELEMANDA DERİN YAPISAL
    ÇATLAK… BİNAYI DERHAL BOŞALTIN" yazıyordu. Güven oranı şiddet değildir.
  - Kullanıcının denediği fotoğraf yakın çekim bir beton çatlağı (stok görsel). Model neredeyse
    bütün resmi kaplayan bir kutu çizdi (%75) ve üçünü de "KRİTİK" işaretledi.
- **Resimdeki etiketler bozuktu.** OpenCV'nin yazı tipi Türkçe harf çizmiyor:
  "Duvar/Kolon ??atla????". Ayrıca "Duvar/Kolon" da modelin bilmediği bir iddia.
- **Ölçüm (13 gerçek deprem fotoğrafı, `tatbikat_foto/`, Wikimedia):**
  - 47 çatlak kutusu, hiçbiri resmin yarısından büyük değil (ortanca ≈ %0–1).
  - Yani bütün resmi kaplayan kutu yakın çekim beton dokusunda çıkıyor; sahadan gelen fotoğrafta
    çatlak kutuları küçük.
  - Bina modelinin sınıfları: `0_NoDamage`, `1_ModerateDamage`, `2_VeryHeavyDamage`.
- **Kayıt tutma taraması.**
  - Tutulanlar:
    - görev adımları (`gorev_adimlari`: kim, hangi adım, ne zaman);
    - hesap işlemleri (`hesap_kayitlari`, J-157);
    - bildirimin gönderen ve geri çekeni;
    - afetzede ihbarının model sonucu.
  - Tutulmayanlar:
    - konsoldaki kamera, metin ve hasar analizi (kim, ne zaman, hangi model, ne buldu);
    - tatbikatı kimin başlattığı;
    - SOS'u kimin kapattığı (yalnız zamanı vardı);
    - ekip tanımını ve ekibe bağlı hesapları kimin değiştirdiği.
  - İhbar durumunda yalnız son işleyen kalıyordu.

**Kararlar (kullanıcı, 17 Kasım).**
- Çatlak için dürüst metin: "kritik" ve "boşaltın" yok. Ağır/orta derece yalnız bina modelinin
  sınıfından gelir.
- Kayıt: analizler ve eksik işlemlerin hepsi tek, silinmeyen işlem kaydına.

**Yapılan: sunucu.**
- `uclar/kamera.py`:
  - Her tespitte `siddet` var: `agir` / `orta` / `yok` bina modelinin sınıfından, çatlakta
    `belirsiz`. `severity` eski istemciler için duruyor; çatlakta `UNRATED`.
  - Yeni durum `CRACK_FOUND`. Tavsiye metinleri bina hakkında karar vermez, uzman
    değerlendirmesine yönlendirir.
  - Resme numara ve model sınıfı yazılır (ASCII). Tespitler güvene göre sıralı.
  - Yanıta fotoğraf ölçüsü ve süre eklendi.
- `islem_kayitlari` tablosu (`depo/sqlite_surucu.py`):
  - kim (ad, rol), ne zaman, tür, hedef, tek cümlelik özet, ayrıntı (JSON);
  - tetikleyiciler UPDATE ve DELETE'i reddeder;
  - fotoğraf saklanmaz.
- `islem_kaydi.kaydet` (`islem_kaydi.py`): kayıt yazılamazsa asıl iş durmaz, hata günlüğe gider.
  Açık konsollara yalnız türü taşıyan `islem-kaydi` mesajı gider; afetzedeye gitmez.
- Kayda bağlanan 18 tür:
  - analizler: kamera, metin, hasar analizi (başladı / bitti / hata), tatbikat (başladı / bitti /
    hata / kapatıldı);
  - sevk ve görev adımı;
  - SOS kapatma, ihbar durumu;
  - ekip ekleme, ekip değişikliği (yalnız değişen alanlar), ekibe bağlı hesaplar;
  - bildirim yayınlama ve geri çekme.
- Analiz bitişi işçi sürecinden döner; kayıt, başlatan kişinin adına iş kaydı kilidinin dışında
  yazılır.
- `GET /api/islem-kayitlari`: yalnız koordinatör ve yönetici; tür süzgeci, sayfalama (`once`).

**Yapılan: konsol.**
- **Kamera sağ paneli:**
  - en üstte tek cümlelik sonuç (rozet + tavsiye);
  - gönderilen fotoğrafın üstüne tarayıcıda numaralı kutular;
  - listede satıra gelince kutu öne çıkar;
  - künye: model, en yüksek güven, süre, ölçü.
  - Kendi analizin varsa afetzede fotoğraflarının üstünde durur.
- **Tam ekran inceleme (`kabuk/FotoInceleme.tsx`):**
  - yakınlaştırma 1–4×, kutuya ya da satıra tıklayınca seçim;
  - ← → ile gezinme;
  - ince ayar en altta: güven süzgeci, kutuları kapat.
  - Afetzede ihbar fotoğraflarında da var.
- **Kullanıcılar sayfasında "İşlem kaydı" sekmesi:**
  - hazır süzgeçler: Analizler, Sevk ve görev, SOS ve ihbar, Ekip tanımı, Bildirimler;
  - satır açılınca ayrıntı;
  - "Daha eski kayıtlar".
  - Eski "Kayıt defteri" sekmesinin adı "Hesap defteri" oldu.
- Kamera Teknik notu güncellendi: modellerin bilinen tek sayısı eğitim doğrulama mAP@50'dir
  (çatlak 0,731 · bina 0,592), bağımsız sınama değildir. "mAP henüz ölçülmedi" cümlesi eskiydi.

**Doğrulama.**
- `tests/test_islem_kaydi.py` (10 test):
  - kayıt değiştirilemez ve silinemez;
  - okuma yalnız koordinasyonda;
  - sevk, görev adımı, SOS kapatma, ekip ekleme / değiştirme / üyeler, ihbar, bildirim ve
    analiz bitişi kaydediliyor;
  - kamerada çatlak "boşalt" demiyor, fotoğraf kayda girmiyor;
  - sayfalama çalışıyor.
- Önceki yetki testleriyle birlikte **48/48** geçti. `tsc -b` ve `kontrol:token` temiz.
- Gerçek modelle: Hatay fotoğrafında 7 çatlak, hepsi `belirsiz`, durum `CRACK_FOUND`.
- Tarayıcıda koordinatörle:
  - Hatay hasar fotoğrafı "İkisi birden": 6 işaret (2 ağır, 1 orta, 3 çatlak), 1 385 ms;
  - büyütme penceresinde seçim, → tuşu, 2× yakınlaştırma ve %60 süzgeci (6 → 2 kutu) çalıştı;
  - işlem kaydında satır ve ayrıntısı göründü.

**Etkisi.**
- Eski web ve Flutter `severity == "CRITICAL"` bakıyorsa çatlak tek başına artık kritik
  görünmez. Etiket "Duvar/Kolon Çatlağı" → "Çatlak". Bina etiketleri afetzede ekranıyla aynı.
- `araclar_kanal_olc.py`'nin rapordaki `kritik` alanı eski kuralla üretildi; yeniden koşulursa
  çatlak tek başına kritik sayılmaz.

**Açık.**
- Hasar analizi ve tatbikat kayıtları tarayıcıda uçtan uca koşulmadı; birim testle sınandı.
- Afetzede ihbar fotoğrafının büyütme penceresi tarayıcıda açılmadı. Yerel ihbarlar Eylül'den,
  30 günlük pencerenin dışında kalıyor.
- Kayıt süresizdir; saklama süresi ve dışa aktarma ayrı karar.

## J-166 🟠 İşlem kaydı kurcalanmaya açıktı; girişler, kişisel veri görüntüleme ve ekip konum geçmişi tutulmuyordu
**Durum:** KAPALI · **Görüldü** · **İlgili:** J-165, J-167 (S-3, P-6, T-1), J-157, CLAUDE.md §1, §3, §5

**Karar (kullanıcı, 17 Kasım).** J-165'teki işlem kaydına dört ek: giriş geçmişi, kimin neye
baktığı, ekip konum paylaşımı ve hash zinciri.

**Yapılan.**
- **Hash zinciri.**
  - `islem_kayitlari` her satırda `onceki_hash` ve `hash` (SHA-256) taşıyor. Satırın alanları
    kanonik JSON'a yazılır (`depo/sqlite_surucu.py`, `islem_hash`).
  - Sıra tek yazma bağlantısı ve kilitle korunur.
  - Bu sürümden önceki satırlar özetsizdir; doğrulama onları "zincir öncesi" diye ayrı sayar.
    Tetikleyici güncellemeye izin vermediği için geriye dönük doldurulmadı (bilerek).
- **Doğrulama, artımlı (J-167 P-6).**
  - `GET /api/islem-kayitlari/dogrula`: son sağlam denetimden devam eder. Önce o noktadaki satırın
    özeti hâlâ aynı mı diye bakar; kuyruktan silme de yakalanır. `?tam=true` baştan sona tarar.
  - Her sonuç silinmeyen `islem_zinciri_denetimleri` tablosuna yazılır.
  - `GET /api/islem-kayitlari/son-denetim` doğrulama yapmadan son sonucu verir.
  - Ölçüm `[Ö]` (bu makine, geçici SQLite, satır başına 6 tespitli kamera ayrıntısı):

    | Kayıt sayısı | Tam doğrulama | Artımlı doğrulama |
    |---|---|---|
    | 10 000 | 0,14 sn | — |
    | 100 000 | 3,08–3,36 sn | 100 yeni kayıt: 2,9 ms |

  - Yazma: satır başına 0,11 ms (10 bin) → 0,26 ms (100 bin).
- **Giriş geçmişi** (`uclar/oturum.py`):
  - kayıt türleri: `giris_basarili`, `giris_basarisiz`, `cikis`, `kayit_oldu`;
  - başarısız girişin nedeni: şifre hatalı, böyle bir hesap yok, yanlış kapı, hesap askıda;
  - denenen e-posta, bağlanan adres, tarayıcı ve vekilin ilettiği adres (doğrulanmamış diye
    işaretli) yazılır;
  - şifre yazılmaz; istemciye giden ileti değişmez (hesabın varlığı sızmaz).
- **Görüntüleme kaydı** (`islem_kaydi.goruntuleme`):
  - kayıt altındaki ekranlar: SOS listesi, ihbar listesi, ihbar fotoğrafı, kullanıcı listesi,
    hesap defteri, işlem kaydının kendisi, ekip konum geçmişi;
  - aynı kişi aynı şeyi 10 dakikada bir kez yazılır (sayaç süreç içi);
  - afetzedenin kendi kaydına bakması yazılmaz.
- **Ekip konum geçmişi:**
  - her konum noktası silinmeyen `ekip_konum_gecmisi` tablosuna gönderen ve telefonun bildirdiği
    doğrulukla yazılır;
  - işlem kaydına yalnız paylaşımın başladığı an düşer (15 dakikadan uzun aradan sonra);
  - `GET /api/ekipler/{id}/konum-gecmisi` yalnız koordinasyonda;
  - ekip ekranı artık doğruluğu da gönderiyor.
- **Konsol, İşlem kaydı sekmesi:**
  - "Kayıt zinciri" paneli: sağlam ya da bozuk, kaç kayıt, son özet, zincir öncesi kayıt sayısı;
    "Yeni kayıtları doğrula" ve "Baştan doğrula" düğmeleri. Doğrulama kendiliğinden koşmaz;
  - "Girişler" ve "Görüntülemeler" süzgeçleri, "Ekip ve konum" grubu;
  - ayrıntıda zincir özeti.
- **Kamera ucu (J-167 S-3):**
  - bilinmeyen `modelType` artık 422 alıyor;
  - model dosyası yoksa 503 dönüyor ("tespit yok" denmiyor);
  - çözülemeyen fotoğraf 422;
  - `activeModels` yalnız gerçekten koşan modelleri yazıyor.
- **Testler (J-167 T-1):**
  - `test_konum_gecmisi_tutulur` kendi ekibini ve hesabını kuruyor;
  - heatmap testi sahte koordinatörle oturumlu çağırıyor (gerçek veritabanına hesap yazmadan),
    uç PostGIS yokken `yerel_depo` dönüyor;
  - oturumsuz çağrının 401 aldığı ayrı testle sabitlendi.

**Doğrulama.**
- `pytest -q`: **76/76**. Bunlara `test_islem_kaydi.py`'deki 19 test dahil:
  - zincir değişikliği ve kuyruktan silmeyi yakalıyor;
  - giriş türleri ve nedenleri doğru;
  - görüntüleme 10 dakikada bir yazılıyor;
  - konum paylaşımı bir kez yazılıyor;
  - konum geçmişi silinemiyor;
  - kamera 422/503 dönüyor.
- `npx tsc -b`, `npm run kontrol:token` temiz.
- Tarayıcıda koordinatörle:
  - yanlış şifre ve doğru giriş kayda düştü (neden "şifre hatalı", adres, tarayıcı);
  - SOS, ihbar, kullanıcı listesi ve işlem kaydı görüntülemeleri yazıldı;
  - çıkış yazıldı;
  - baştan doğrulama: 6 kayıt sağlam, zincir öncesi 3 kayıt; artımlı doğrulama da çalıştı;
  - çerezsiz açılış (`127.0.0.1`) giriş ekranına düşüyor, kilitlenme yok.
- Çalışan API'de gerçek modelle:
  - `modelType="ikisi"` 422;
  - `hybrid` iki modeli de çalıştırdı (6 tespit, ağır + çatlak, 4,1 sn; ilk çağrı modeli belleğe
    yüklüyor);
  - kayıt ve zincir güncel.

**Sınırlar (bilinerek).**
- Zincir kurcalamayı **gösterir, engellemez**. Dosyaya erişen biri bütün özetleri yeniden
  hesaplayabilir. Bunu yakalamak için son özet zaman zaman dışarıya yazılmalı (ekranda öneriliyor).
- Vekil arkasında `ip` vekilin adresidir. Nginx `X-Forwarded-For` eklerse o da yazılır ama
  doğrulanmamıştır (istemci uydurabilir).
- Kayıtlarda kişisel veri var: e-posta, IP, konum izi. Saklama süresi, erişim ve dışa aktarma
  kararı verilmedi (KVKK).
- Başarısız giriş denemesi sınırsız yazılır; sınırlama J-167 S-1'de.
- Konum geçmişini haritada izleyen bir ekran yok; yalnız uç var.

## J-169 🟠 Başarısız bir yazma veritabanı kilidini bırakmıyordu
**Durum:** KAPALI · **Görüldü** · **İlgili:** J-158, J-166, J-167

**Bulgu (17 Kasım, J-167 Grup C testlerinde).**
- `depo/sqlite_surucu.py`'deki 14 yazma bloğunun hiçbiri hata anında işlemi geri almıyordu.
- Bir yazma reddedilince (tetikleyici, kısıt, disk) bağlantıda açık işlem kalıyordu.
  - Aynı dosyaya yazan başka bağlantılar ve süreçler "database is locked" alıyordu.
  - Sonraki yazmalar da o yarım işlemin içine giriyordu.
- Testte, işlem kaydının silinemediğini sınayan testten sonra 16 test kuruluşta düştü.
- Canlıda: tek bir başarısız yazma, aynı dosyaya yazan araç betiklerini kilitleyebilirdi.

**Yapılan.**
- `_yazma()`: kilit + hata anında `rollback`, hata yine fırlatılır. 14 blok buna çevrildi.
- Test: `tests/test_depo_eszamanlilik.py::test_basarisiz_yazma_kilidi_birakir`.
  - Reddedilen silmeden sonra açık işlem kalmıyor.
  - Başka bir bağlantı 0,5 sn içinde yazabiliyor.
- `pytest -q` **89/89**.

## J-170 🟠 Metin analizi: adres dış servise gidiyordu ve çoğu zaman yanlış yerdi; sonuç ekranı okunmuyordu
**Durum:** KAPALI (kategori kararı hariç, aşağıda) · **Ölçüldü** · **İlgili:** J-167 (F-1, P-2, S-5), J-111, J-51

**Bulgu (17 Kasım).**
- Adres metinden NER modeliyle aday çıkarılıp kamuya açık Nominatim'e soruluyordu: afetzedenin yazdığı adres üçüncü tarafa gidiyordu.
- Çoğu metinde yalnız ilçe merkezi bulunuyordu; "Armutlu Mahallesi" yazan metin Antakya merkezine düşüyordu. Ekranda bunun yaklaşık olduğu yazmıyordu.
- Model API sürecinde tembel yükleniyordu: ilk istek 31,8 sn.
- Metin uzunluğu sınırsızdı, analiz başına hız sınırı yoktu.
- Konsoldaki deneme analizi sonucu PostGIS hasar tablosuna ve bellekteki konum listesine yazıyordu: deneme haritaya nokta bırakıyordu.
- Konsolda metin modu tek bir metni çözümlüyordu; gelen yazılı ihbarlar ayrı, sıralanmamış bir listedeydi. Sonuçta düzey, sapma payı, kişi ve ihtiyaç yoktu; haritayla bağ yoktu.

**Yapılan: arka uç** (`QuakeMindBackend/metin_analizi/`).
- `adres.py`: yerel adres dizini, ağa çıkmaz.
  - Dizin `araclar_adres_dizini_kur.py` ile OSM'den kurulur (`roads.gpkg`, `yerler.json`, `tr_locations`): 81 il, 151 ilçe, 496 mahalle/köy, 6 173 sokak kaydı. 117 KB, kurulum 21 sn. ODbL künyesi dosyada.
  - Her sonuç düzeyini (sokak, mahalle, köy, ilçe, il) ve sapma payını yazar: sokak ≥400 m, mahalle 800 m, köy 1,5 km, ilçe 5 km, il 30 km.
  - Sokak yalnız yazılan mahalleye bağlıysa ya da 800 m içindeyse seçilir; aynı adlı yerler ayırt edilemiyorsa konum seçilmez, adaylar döner.
  - Dizinde olmayan ad uydurulmaz, "dizininde yok" notu düşülür. Bulanık eşleşme yalnız büyük harfle başlayan sözcükte ("altından" → Altındağ hatası).
  - Metindeki her eşleşmenin karakter aralığı döner (ekranda vurgu için).
- `cikarim.py`: kişi sayısı, ihtiyaç (su, gıda, barınma, ısınma, ilaç, tuvalet) ve aciliyet işaretleri (enkaz altında, ses geliyor, yaralı, mahsur, çökme, riskli bina, yol kapalı, savunmasız kişi). Kural tabanlı.
- Metindeki işaret modelin kategorisiyle çelişirse "kontrol et" uyarısı döner; **karar değiştirilmez**.
- NER modeli artık yüklenmiyor (adres dizinden çözüldüğü için çıktısının kullanılacak yolu kalmadı). Tatbikat kanalı kendi NER kullanımını koruyor.
- Model ayrı işçi süreçte (`isci.py`, CLAUDE.md §3); açılışta açılışı bekletmeden ısınır. `/api/hazir` `metinModeli` alanını raporlar. Model çalışmazsa 503.
- Metin en çok 1 000 karakter; hesap başına dakikada 30 analiz (`hiz_siniri.metin_kontrol`).
- `/api/nlp/analyze` artık kayıt açmıyor, haritaya yazmıyor; yalnız işlem kaydına düşüyor.
- `apps/disaster_nlp/src/classification.py`: `classify_detay` hazır tahminleri alabiliyor (model iki kez koşmasın). Karar mantığı aynı.

**Yapılan: arayüz** (`konsol/src/modlar/metin.tsx`, `metinKarti.tsx`, `veri/metin.ts`).
- Metin modunun solu yazılı ihbar kuyruğu: en acil ve açık olan önce; süzgeç "Açık / Bakılması gereken / Kapanan / Hepsi". Satırda aciliyet, kategori, adres düzeyi ve sapma payı; bakılması gerekenlerde nedeni ("kategori metinle çelişiyor", "adres yalnız bölge düzeyinde", "metinde adres yok").
- Sağda tek sonuç kartı: kategori ve aciliyet, model güveni ve ikinci olasılık, uyarılar, adres/kişi/işaret/ihtiyaç vurgulu metin, düzey rozeti ve sapma payıyla adres kartı, "Haritada göster".
- Haritada seçili kaydın sapma alanı çember olarak çiziliyor (metinden çözülen adreste düzeyin payı, cihaz konumunda telefonun doğruluğu). Payı bilinmeyen konumda çember çizilmez.
- "Metni kendin incelet" ikincil araç: kayıt açmaz; sonuç aynı kartta, haritada merkez noktası ve çemberle.
- Afetzede "Yazarak bildir" iki adıma indi: yaz → kontrol et ve gönder. Ekibin gideceği yer adresin düzeyine göre önseçili (sokak/mahalle/köy → metindeki adres; ilçe/il → kendi konumu); "adres Nominatim'e gider" yazısı kalktı.

**Ölçüm** `[Ö]` (`araclar_metin_adres_olc.py`, `apps/disaster_nlp/data/metin_adres_kumesi.json`: 22 elle yazılmış, etiketli sentetik metin; yer adları gerçek. Raporlar `benchmark/reports/metin_adres_taban.json`, `metin_adres_yeni.json`).

| | Önce | Sonra |
|---|---|---|
| Beklenen yer bulundu | 7/12 | 11/12 |
| Koordinat 1,5 km içinde | 5/12 | 10/12 |
| Dış servise giden metin | 5 | 0 |
| İstek süresi (ortanca) | 52,5 ms | 27,8 ms |
| Kategori örtüşmesi | 14/22 | 14/22 (karar değişmedi) |

- Gerçek işçiyle uçtan uca: API 6 sn'de açıldı; ısınma sürerken gelen ilk istek 6,8 sn (önce 31,8 sn), sonrakiler ~65 ms.
- `tests/test_metin_analizi.py` (15); `pytest -q` 104/104.
- Ekran denemesi veritabanı kopyasında (8001): afetzede telefon boyutunda (375×812) gönderdi, konsolda kuyruk, kart, çember ve deneme aracı görüldü.

**Kullanıcı bulgusu (17 Kasım akşam): "Cumhuriyet meydanında ölüler var 2 tane".**
- Önce: model "afetle ilgisiz" (%65) dedi; adres, kişi ve işaret bulunamadı. Koordinatöre ölü bildiren metin uyarısız "ilgisiz" görünüyordu.
- "Meydan" adres türü değildi; dizinde "Cumhuriyet Meydanı" (Antakya) vardı ama aranmıyordu. Eklendi (sokak düzeyi, ±400 m).
- "Ölü" kişi ve işaret olarak eklendi. Sonradan gelen sayı ("ölüler var 2 tane") yalnız "tane/adet" ile sayılıyor ("çocuk 5 yaşında" sayılmaz).
- "öldü/ölmüş" özgün metinde ö harfiyle aranıyor: harfler sadeleşince "oldu/olmuş" (olmak) ile karışıyordu. "ö" yazılmamışsa yakalanmaz.
- Model "ilgisiz" dediğinde metinde ağır işaret (ölü, enkaz altında, ses, yaralı, mahsur, çökme) varsa "Kontrol et" uyarısı çıkıyor. Karar değişmedi (J-111); kartta başlık "Model: afetle ilgisiz".
- Sonra: "Cumhuriyet Meydanı, Hatay" (sokak), 2 ölü, uyarı. Ölçüm kümesinde gerileme yok (11/12, 10/12). `pytest -q` 107/107.

**Açık kalan.**
- Kategori kararı değiştirilmedi. Gerçek sınama kümesi D: sürücüsünde, bu makinede yok; değişiklik ölçülemezdi (J-111). Uyarılar yalnız koordinatöre "kontrol et" der.
- 22 kayıtlık küme küçük ve sentetik; makaleye taşınacaksa gerçek ihbar metinleriyle yeniden ölçülmeli.
- `apps/disaster_nlp/data/geocode_cache.json` artık kullanılmıyor ve eski adres sorgularını içeriyor; silinmesi kullanıcı kararı.
- Adres dizini (`metin_analizi/veri/adres_dizini.json.gz`, 117 KB) depoya girmeli mi: kullanıcı kararı. Girmezse sunucuda `araclar_adres_dizini_kur.py` koşulmalı.
- Bina numarası çözülmüyor; sokak noktası sokağın orta yeridir.

## J-171 🟠 Araç rotası dönüş yasaklarını çiğniyordu, "Yol ve Rota" sayfası ölüydü (J-167 Grup E)
**Durum:** KAPALI · **Ölçüldü** · **İlgili:** J-55, J-162, J-167 (F-3…F-7)

**Bulgu (17–18 Kasım).**
- Araç rotası (`arac_rotasi.py`, sevk ve görev ekranları) düğüm tabanlı Dijkstra'ydı. Tek yön ve göbek (tek yön olarak) vardı; ama OSM dönüş yasakları (`type=restriction`) hiç okunmuyordu ve bu yapıda taşınamıyordu. Kavşakta dönüş bedeli yoktu.
- Başlangıç ve hedef en yakın **düğüme** oturtuluyordu: tek yönlü caddenin ortasındaki olay yanlış yöndeki ya da paralel sokaktaki bir düğüme bağlanabiliyordu.
- Konsolun "Yol ve rota" sayfası hiçbir şey hesaplamıyordu ("rota ucu (A*) henüz bağlı değil").

**Yapılan.**
- `araclar_arac_agi_uret.py`: her yol için göbek işareti (`yol_gobek`); `--yasaklar` OSM dönüş yasaklarını koordinatla `veri/yol_agi/arac/yasaklar.json`'a yazar (136 yasak; kavşağı bir yol olan 30'u uygulanamaz, sayılır).
- `arac_rotasi.py` **kenar tabanlı** arama: durum "hangi yolun başındayım", geçiş ayrı adım.
  - Yasaklı geçişler grafta yok (Antakya 7, bölgeler arası ağ 44 yasak oturdu).
  - U dönüşü yalnız çıkmaz sokakta.
  - Kavşakta (en az üç yol) dönüş bedeli: sola 9 sn, sağa 4 sn, keskin 14 sn, hafif 1 sn; göbek içinde 0, göbeğe giriş en çok 3 sn. **Varsayım [T], ölçülmedi.**
  - Oturtma en yakın yol parçasına, yönüyle; otoyol ve devlet yolu yakında başka yol varsa seçilmez; nokta bir düğümün üstündeyse düğüme giren ve çıkan bütün yollar.
  - Kavşak olmayan ardışık yollar tek "zincir" durumu: arama grafı Antakya'da 212 735 → 49 105, bölgeler arası ağda 1 004 496 → 277 127. 200 rastgele çiftte zincirli ve zincirsiz graf aynı mesafe ve süreyi verdi `[Ö]`.
  - Dışa açık arayüz (`yoldan`, `hedef_aramasi`, `ekipten`) aynı: sevk, görev ve saha ekranları yeni motoru kendiliğinden kullanıyor.
- Yeni uçlar `uclar/guzergah.py`: `/api/guzergah` (iki nokta, adım adım tarif), `/api/guzergah/en-yakin` (hastane: OSM; toplanma: AFAD; yoldan en çabuk üç yer), `/api/guzergah/kunye`. Koordinatör, yönetici ve saha.
- Konsol "Yol ve rota" (`konsol/src/modlar/yol.tsx`): iki nokta arası (haritaya tıklayarak), ekipten olaya, en yakın hastane, en yakın toplanma alanı, kapalı yollar (analiz başına). Sağda süre, mesafe, kuş uçuşu, sola/sağa dönüş sayısı, kapanma ve hasar uyarısı, kaçınmanın bedeli (kaçınmasız rotayla kıyas), adım adım tarif. Haritada rota, kesik kıyas çizgisi, adaylar ve uçlar.
- Grup E'nin geri kalanı: zaman şeridi histogramı (F-4), "Nereye" kartında "0" yerine "—" (F-5), Türkçe ilerleme metinleri (F-6), kapsamasız görüntüler altta (F-7).

**Ölçüm** `[Ö]` (`araclar_rota_olc.py`; aynı araç, aynı örnek, tohum 42; eski motor `--motor` ile dosyadan; veritabanı kopyası):

| | Eski | Yeni |
|---|---|---|
| Dönüş yasağı (kavşaktan geçen rotada) çiğnenen | 16 / 28 | 0 / 29 |
| Oturtma: yoldan fazla sapma, en kötü %5 (Antakya / Antep) | 23,0 / 38,5 m | 0,0 / 0,0 m |
| Oturtma: 30 m'den fazla sapan nokta (Antakya / Antep) | %3,7 / %7,3 | %0,0 / %0,0 |
| Arama, ortanca: şehir / bölgeler arası | 22,9 / 129,5 ms | 13,4 / 91,2 ms |

- Raporlar: `QuakeMindBackend/benchmark/reports/rota_taban.json`, `rota_yeni.json`.
- Ölçüm aracının ilk hâli kavşağa 3 m'den yakın ara noktayı kavşak sanıyordu (yanlış ihlal); düzeltildi, taban o düzeltmeyle yeniden alındı.
- Oturtma ölçümü yolun kendisinden 5–25 m kaydırılmış noktalarla yapıldı; gerçek ihbar konumlarıyla değil.
- `tests/test_arac_rotasi.py` (8: tek yön, yasak, sağ/sol, göbek, oturtma, gerçek ağda OSM yasakları, uç yetkisi, Antakya rotası), `tests/test_olay_yogunlugu.py` (3: sayım, `EXPLAIN QUERY PLAN` ile indeks, yetki). `pytest -q` 118/118.
- Tarayıcıda kopya veritabanıyla: iki nokta (~10 dk, 5,4 km), en yakın hastane (üçü süreye göre), ekipten olaya (AKUT 1, ~3 dk, arama 14 ms), kapalı yollar.

**Canlıya alırken (Deha).** Yol ağı dosyaları git'te değil (`veri/yol_agi/`). Göbek ve dönüş yasağı için sunucuda bir kez:
`python araclar_arac_agi_uret.py && python araclar_arac_agi_uret.py --genel && python araclar_arac_agi_uret.py --yasaklar` (bu makinede ~5 dk). Koşulmazsa motor eski dosyalarla da çalışır, ama göbek ve yasak olmadan.

**Açık kalan.**
- Dönüş bedeli ve hız değerleri varsayım; gerçek seyahat süreleriyle ölçülmedi. Trafik verisi yok.
- OSM'de Türkiye'deki dönüş yasakları seyrek (Antakya'da 8); motor yalnız haritada olanı bilir.
- Simülasyon (tatbikat) kendi rota motorunu kullanıyor (`apps/road_damage`); bu iş ona dokunmadı.

## J-172 🟠 Harita karmaşık ve okunmuyordu: aynı yuvarlaklar, kesilen bilgi kutusu, anlaşılmaz kaynak ağırlıkları; J-167 Grup F
**Durum:** KAPALI (P-1 ertelendi) · **Ölçüldü** · **İlgili:** J-41, J-56, J-167 (P-1, P-3, P-4, P-6)

**Bulgu (kullanıcı, 18 Kasım).** "Katmanlar karışık; her nokta ne, anlaşılmıyor; kapalı yol, AFAD, ekip, hastane ayrı ve açık simgelerle gösterilsin; hepsi aynı anda gösterilmesin; kaynak ağırlıkları kullanışsız."
- Haritadaki bütün noktalar (SOS, ihbar, ekip, toplanma, kapanma) aynı biçimde renkli yuvarlaktı; tür yalnız renkten okunuyordu.
- Üstüne gelince çıkan bilgi kutusu haritanın içinde çiziliyordu; panellerin ve zaman şeridinin altında kalıp kesiliyordu.
- Katman paneli 17 katmanı uzun açıklamalarla tek listede gösteriyordu; tatbikat katmanları her modda vardı.
- Genel durum modunda deprem kataloğu (4 939 halka) varsayılan açıktı.
- Isı haritası şehir ölçeğinde %72 örtücüydü; simgeleri bastırıyordu.
- Kaynak ağırlıkları -1…1,5 arası kaydırıcıydı ("×1,0"); ne demek olduğu yazmıyordu.

**Yapılan.**
- `konsol/src/harita/simgeler.ts`: her tür ayrı **şekil + glif + renk** (deck.gl IconLayer; glifler Phosphor, MIT): SOS daire + siren (aciliyet rengi), ihbar daire + kamera/konuşma/paket, ekip kare + araç (müsait / görevde / hizmet dışı), toplanma kare + kişiler, hastane ve sağlık kare + hastane, kapanma kırmızı daire + yasak. Seçili olan beyaz halkalı ve büyük; kapanan sönük.
- Yeni katman: **Hastane ve sağlık** (`/api/katman/saglik`, OSM, 196 tesis). SOS, Yol ve rota modlarında açık.
- Yakınlaştırma eşikleri: tek tek uydu noktaları z ≥ 13, ekip adları z ≥ 12, sağlık z ≥ 12 (toplanma z ≥ 11, yapılar z ≥ 13 eskiden beri).
- Mod varsayılanları: genel durumdan deprem kataloğu çıktı (yalnız risk modunda); ekipler modundan toplanma çıktı, kapanmalar girdi.
- Bilgi kartı: tür (simgeyle), başlık, ad-değer satırları, kaynak, tıklayınca ne olacağı; her türde aynı düzen. Kart sayfanın üstünde (portal), ekran kenarında yön değiştiriyor. Metin kaçışlı (`kacis`).
- Katman paneli: satırda haritadakiyle aynı işaret (panel lejant da), ad, sayı, anahtar; kaynaklar en altta "Veri kaynakları"nda. Tatbikat ve analiz katmanları yalnız kendi modlarında. Eşiğin altındaki katman "yakınlaşınca görünür" yazıyor. "Önerilene dön" düğmesi.
- Isı örtücülüğü z ≤ 13'te 0,72 → 0,55, z ≥ 16'da 0,30 → 0,22.
- Kaynak ağırlıkları: her kaynak için dört seçenek (Çıkar / Kapalı / Normal / Güçlü), altında anlamı; verisi olmayan kaynak "bu aralıkta yok" ve kapalı. Hazır karışımların ara değerleri en yakın seçenekte gösterilir; karışım değerleri değişmedi.
- Grup F: P-3 (PostGIS denemesi, 4,3 sn → 44 ms), P-4 (görüntü önbelleği, 2,75 → 0,03 sn; yol ağı zaten 0–1 sn), P-6 (J-166'da yapılmıştı), P-1 ölçüldü ve ertelendi. Ayrıntı J-167'de.
- Güvenlik: rota uçlarına hesap başına dakikada 60 sınırı (`hiz_siniri.rota_kontrol`).

**Doğrulama.**
- `tests/test_harita_katmanlari.py` (4: sağlık ucu yetki ve süzme, görüntü diskten, Google saklanmaz, eksik görüntü saklanmaz), `test_arac_rotasi.py` hız sınırı. `pytest -q` 123/123; `npx tsc -b`, `kontrol:token` temiz.
- Tarayıcıda: genel durumda ihbar ve ekip simgeleri, bilgi kartı panellerin üstünde ve tam okunuyor; SOS modunda hastane simgeleri ve sade katman paneli. Otomasyonun fare olayı haritaya ölçekli gittiği için kart, harita tuvaline gönderilen olayla denendi.

**Canlıya alırken (Deha).** PostGIS kullanılacaksa `POSTGIS_URL` tanımlanmalı (yoksa denenmez). Tatbikat için yerel bölge dosyası kurulu olmalı (`araclar_yerel_osm_kur.py`).

**Açık kalan.**
- P-1: afetzede haritasını deck.gl'siz yazmak (altlık çizimi dahil); karar kullanıcıda.
- Simgelerin renk körlüğünde ayırt edilmesi şekil ve glife dayanıyor; ayrıca sınanmadı.

## J-173 🔴 Deprem riski: eşzamanlı istekte başka ilin sonucu, şişkin uzun vadeli tehlike, açık uçlar; ekran soruya cevap vermiyordu
**Durum:** KAPALI · **Ölçüldü** · **İlgili:** J-152, J-56, CLAUDE.md §1, §5, §8

**Bulgu (18 Kasım, kullanıcı "doğru, güvenli, performanslı, net mi" diye sordu).**
- **Yarış durumu.** Motor hesaplanan koordinatı ortak nesnede (`self.last_lat`) tutuyor, köprü (`quakemind/tool/risk_bridge.build_payload`) oradan geri okuyordu. Ölçüldü `[Ö]`: 8 paralel kullanıcıyla 40 istekte **35 yanıt başka ilin koordinatıyla** döndü.
- Her istek bütün sürecin çalışma klasörünü (`os.chdir`) ve `sys.path`'i değiştiriyordu; aynı anda koşan başka uçları da etkiler.
- Kısa ve uzun vadeli bileşen iki kez hesaplanıyor, skor metinden ayrıştırılıyordu. Sıralı ortanca 162 ms, paralel 629 ms.
- **Uzun vadeli tehlike şişkindi.** "10 yılda 200 km'de M≥6 olasılığı" artçılar dahil sayılıyor (motorun ayıklaması 1 gün / 50 km, 2023'te 14 gün sonraki M6,4 ana şok sayılıyordu) ve oran kataloğun süresine değil, o çevredeki ilk ve son deprem arasına bölünüyordu (Konya'da tek ana şok varken 0,28 çıkıyordu).
- Kısa vadeli bileşen, şehrin 150 km'sinde son bir yılda 7 deprem yoksa sessizce ülke genelinin son 7 depremini kullanıyordu; ekran bunu söylemiyordu.
- `/api/risk/fault_lines` ve `/api/risk/all_quakes` oturumsuz açıktı (CLAUDE.md §5); `predict` hata olunca ham Python hata metnini döndürüyordu; koordinatsız istekte Nominatim'e (dış servis) gidiliyordu.
- Ekran "hangi bölgede risk daha yüksek?" diye soruyor ama yalnız tek tek il soruyordu; harita boştu, bileşenlerin dayanağı yazmıyordu.

**Yapılan.**
- `QuakeMindBackend/risk_hizmeti.py`: iş parçacığı güvenli hesap. Motor yalnız okunur; sonuç yerel değişkenlerden kurulur; veri sürümü değişmedikçe önbellekten; veri tazelenince yeni motor hazırlanıp tek atamayla devreye girer. Çerçeve ve model açılışta arka planda yüklenir.
- Uzun vadeli: M≥6 depremler Gardner & Knopoff (1974) pencereleriyle ayıklanır [A], oran kataloğun bütün süresine bölünür. Kısa vadeli model ve eğitimi DEĞİŞMEDİ (gerçek sınama olmadan değiştirilmez); yanıt `dayanak` alanında kaynağını ("yerel" / "ülke") yazar.
- `uclar/risk.py`: `/api/risk/siralama` (81 il, skora göre); `fault_lines` ve `all_quakes` giriş ister; `all_quakes` satır döngüsü yerine toplu dönüşüm, parametre doğrulaması (tarih 422); `predict` Türkiye kutusu dışında 422, koordinatsız istekte il merkezleri listesinden (dış servis yok), hatada genel ileti (ayrıntı sunucu kaydında).
- Konsol `modlar/risk.tsx`: solda 81 il riske göre sıralı (arama, operasyon bölgesi kısayolları); haritada il merkezleri risk renginde, seçili ilin hesap alanı halkaları (150 / 200 km), il üzerinde bilgi kartı; sağda skor ve üç bileşen çubuğu — her biri neyi ölçtüğü, dayanağı ("1933–2026 kataloğunda 12 ana şok", "en yakın fay 4,9 km") ve skordaki payıyla; kısa vadede zayıf model ve ülke geneline düşme uyarısı.

**Ölçüm** `[Ö]` (gerçek API, gerçek model, aynı betik):

| | Önce | Sonra |
|---|---|---|
| Paralel 40 istekte yanlış ilin koordinatı | 35 | **0** |
| Sıralı istek, ortanca | 162 ms | **30 ms** |
| Paralel istek, ortanca | 629 ms | **107 ms** |
| Uzun vadeli tehlike, 81 il ortancası | 0,63 | **0,53** |

- Katalog 1933–2026 (93,6 yıl): 84 adet M≥6 olayın 71'i ana şok. Hiçbir ilde artmadı; en çok düşenler Şanlıurfa 0,54 → 0,35, Konya 0,28 → 0,10, Isparta 0,62 → 0,47. 81 ilin tablosu `QuakeMindBackend/benchmark/reports/risk_uzun_vade_kiyas.json`.
- `tests/test_risk.py` (4: eşzamanlı istekte doğru il, skor = bileşenlerin ağırlıklı toplamı, yetki ve sınırlar, sıralama). `pytest -q` 127/127.
- Tarayıcıda: sıralama, Bolu ve Hatay seçimi, halkalar, bileşen kartları.

**Makale.** Makalede risk skorundan söz ediliyorsa uzun vadeli bileşenin değerleri değişti (ortanca 0,63 → 0,53); kontrol edilmeli.

**Açık kalan.**
- Ağırlıklar (0,4 / 0,3 / 0,3) ve fay basamakları uzman tanımlı; ölçülmedi.
- Kısa vadeli model zayıf (ROC-AUC 0,61); eğitimdeki "son 7 deprem" özellikleri ülke geneli sıradan, çıkarımda yerel — tutarsız. Düzeltmek modeli yeniden eğitip ölçmek demek.
- Eski web ve mobil risk ekranları J-152'den beri kimliksiz istek attığı için 401 alıyor; şimdi `fault_lines` ve `all_quakes` da.

## J-174 🔴 Uçtan uca akış: canlı akış ilk jeton yenilemesinde kalıcı kapanıyordu; ihtiyaç geçen yazılı ihbar ihtiyaç sayfasına düşmüyordu
**Durum:** KAPALI · **Ölçüldü** · **İlgili:** J-42, J-51, J-54, J-167 S-6, CLAUDE.md §4, §5

**İstek (18 Kasım).** Kullanıcı ihbar iletimini, metin analizinden ihbara, enkaz, erzak ve yardım iletimini, ihbarların oluşup düşmesini bütün rollerde ve ekranlarda doğrulamamızı istedi.

**Sınama.** `QuakeMindBackend/araclar_akis_senaryosu.py` (yeni) gerçek API'de dört hesapla (koordinatör, saha, iki afetzede) ve her birinin canlı akışını dinleyerek 48 adımı sınar:
- SOS;
- metin analizi ve yazılı ihbar;
- ihtiyaç talebi;
- fotoğraf analizi ve ihbarı;
- "görüldü";
- SOS'a ve ihbara ekip sevki;
- saha "yolda", "olay yerinde", konum, "bitti";
- talebin karşılanması;
- kapanan kaydın yeniden açılamaması (409);
- afetzede B'nin başkasının hiçbir kaydını almaması.

Veritabanının kopyasında koşar (`--api http://127.0.0.1:8001`), canlı veriye yazmaz. Ardından üç rolün ekranlarına tarayıcıda bakıldı.

**Bulunan ve düzeltilen.**
1. **Canlı akış ilk jeton yenilemesinde kalıcı kapanıyordu (bütün roller).**
   - Akış, açıldığı yenileme çerezini 15 sn'de bir denetliyor (J-167 S-6). Yenileme jetonu ise her yenilemede dönüyor ve eskisi iptal ediliyor.
   - Sonuç: istemci 15 dakikada bir erişim jetonunu yenileyince sunucu "oturum-bitti" gönderiyor, istemci akışı kalıcı kapatıyordu. Ekran o andan sonra yeni SOS'u, görev ve ihbar durumunu almıyordu; yalnız sayfa yenilenince düzeliyordu.
   - Düzeltme `konsol/src/canli/canliAkis.ts`: "oturum-bitti" gelince bir kez tarayıcıdaki güncel çerezle yeniden bağlanılır. Açılırsa jeton dönmüştür. Açılmazsa (çıkış, askı: 401) eskisi gibi kapanır.
   - Tarayıcıda doğrulandı `[Ö]`: jeton iki kez elle döndürüldü, akış 200 ile yeniden bağlandı, ardından koordinatörün "görüldü"sü afetzede ekranına anında düştü.
2. **Saha akışına işlem kaydı işareti gidiyordu.** Saha `islem-kayitlari` uçlarını okuyamaz (403). `uclar/canli.py` `role_gore`: `islem-kaydi` yalnız koordinatöre ve yöneticiye gider. Ölçüldü `[Ö]`: senaryoda saha akışı 9 → 0.
3. **İhtiyaç geçen yazılı ihbar ihtiyaç sayfasına düşmüyordu.**
   - Örnek: "çadırkentte 30 kişiyiz, suyumuz ve bebek maması bitti". Model su, gıda, barınma ve 30 kişi çıkarıyor, ama bunlar yalnız analizin içinde kalıyordu. İhtiyaç sayfası yalnız formdan gelen talepleri sayıyordu.
   - `uclar/ihbar.py` `_cikti` artık yazılı ihbarda `ihtiyaclar` ve `kisiSayisi` alanlarını analizden üretir. Okuma anında üretildiği için eski kayıtlarda da çalışır.
   - Konsolda ihtiyaç sayfası bu ihbarları da sayar ve listeler (`ihtiyacTalebiMi`). Teknik notta ve harita kartında bu alanların "metinden" çıkarıldığı yazar.
4. **Afetzede, ihbarına ekip gelip bitirince kimin geldiğini görmüyordu.** SOS'ta "AKUT 1 işini bitirdi" yazıyor, ihbarda yalnız "İhbar işlendi" yazıyordu. Ekip bir kez gittiyse ihbar da ekipten anlatılır (`afetzede/Bildirimlerim.tsx`).
5. **Ekip "olay sürüyor" diyerek bitirince afetzede yanlış cümle okuyordu:** "henüz ekip görevlendirilmedi". Artık "AKUT 1 işini bitirdi ama olay sürüyor; koordinasyon başka ekip gönderecek" yazar (`afetzede/GelenEkip.tsx`). Saha geçmişinde de "olay sürüyordu" yazar.
6. **Yüklenirken "veri yok" yazılıyordu.** Genel durum kartları, SOS kuyruğu ve ihtiyaç sayfası sorgu sürerken "veri yok", "uç yanıt vermiyor" ya da "talep yok" diyordu. Bu cümleler sorgunun hata verdiği ya da gerçekten kayıt olmadığı anlamına gelir (kural 1). Artık yüklenirken "yükleniyor…" yazar.
7. SOS kuyruğu cümlesi "3 çağrı: 0 bekliyor, 0 gidiyor" diyordu; kalan 3'ün kapandığını söylemiyordu. Artık söylüyor.

**Doğru çalıştığı görülenler (değişiklik yok).**
- Afetzede yalnız kendi kayıtlarını ve kendi olayına giden ekibi alır.
- Kapanan ihbar yeniden açılmaz (409).
- Açık SOS varken yeni SOS aynı kaydı günceller (200, S-2).
- Ekipte kişi sayısı kayıtlı değilse sevk kişi sayısı ister (422).
- İhbarın kapanışı afetzedeye "gorev" mesajıyla gelir; istemci o mesajda kendi ihbarını yeniden çeker.

**Ölçüm** `[Ö]`:
- `araclar_akis_senaryosu.py` 48/48.
- Akış özetleri: koordinatör {yeni-sos 1, ihbar 5, gorev 7, ekip-konumu 1, islem-kaydi 13}; saha aynısı, islem-kaydi yok; afetzede A yalnız kendi olayları; afetzede B {} (hiçbir şey).
- `tests/test_akis_rolleri.py` (4).
- `pytest -q` 131/131; `npx tsc -b` ve `kontrol:token` temiz.

**Açık kalan.**
- Akış hâlâ tek süreç içi yayın (`canli_yayin.py`). Birden çok worker'da `LISTEN/NOTIFY` gerekir (CLAUDE.md §4).
- Yazılı ihbardan çıkan kişi sayısı model çıkarımıdır, doğrulanmamıştır. Metinde birden çok sayı varsa en büyüğü alınır.

---

## J-175 🟠 Genel durum: ısı haritası kaynak ayırmıyor ve az veriyi yoğun gösteriyordu; sağ panel bir sonraki adımı söylemiyordu; gereksiz veri iniyordu
**Durum:** KAPALI (18 Kasım 2026) · **Ölçüldü** · **Bulundu:** 18 Kasım 2026 (kullanıcı: "renkler hepsi aynı, fark oluşturmuyor, doğru bilgi vermiyor; sağdaki kısım kullanışlı değil; performansı artıralım") · **İlgili:** J-46, J-172, MIMARI §5, ARAYUZ §6

**Bulgu.**
- **Renk kaynak söylemiyordu.** Dört kanalın ızgarası ağırlıkla toplanıp tek mor→sarı skalayla boyanıyordu (`harita/isiDokusu.ts`); hangi lekenin SOS'tan, hangisinin kameradan geldiği okunmuyordu.
- **Az veri yoğun görünüyordu.** Skala en düşük değeri bile koyu ve opak boyuyordu (0,12'de alfa 150). Sunucunun 0,5 km çekirdeği tek bildirimi ~1,2 km yarıçapa yayıyor; 3 bildirim Antakya merkezini "yoğun hasar" gibi kaplıyordu.
- **Pencere tutarsızdı.** Isı ve özet sayıları 15 dakikalık çapadan (J-46), listeler tam pencereden soruluyordu: kenardaki kayıt ısıda ve "SOS 1 nokta"da görünüp "Son ihbarlar 0" listesinde görünmüyordu.
- **Sağ panel:** altı sayı kartının çoğu 0'dı, altında boş liste ve teknik not; hiçbiri bir sonraki adımı söylemiyordu. Kapanan kayıtlar açıklarla karışıktı.
- **Gereksiz veri:** genel modda açılışta 755 KB deprem kataloğu (başlangıç katman ayarında `depremler: true`; mod kendi katmanlarını bir sonraki etkide yazıyordu), her modda 81 il risk sıralaması (sunucuda 345 ms) ve tatbikat alanları iniyordu.

**Yapılan.**
- `harita/isiDokusu.ts`: **renk = kaynak** (katkı veren kaynakların token renklerinin katkı oranıyla karışımı; tek kaynaklı yer saf renk), **koyuluk = yoğunluk** (saydamlık mutlak yoğunlukla doğrusal; eşik 0,08). "Çıkar" ağırlıkları yoğunluktan düşülür. Hücre dökümü (`hucre`) tutulur.
- Isının üzerine gelince bilgi kartı (`harita/katmanlar.ts`, `HaritaKabugu.tsx`): kaynak payları ("Kamera %52 · SOS %48"), yoğunluk, yaklaşık bildirim sayısı (ölçek dolduysa "3 ya da daha çok"), "Çıkar" ile düşülen.
- Sol panel: ölçek açıklaması (renk kaynak, koyuluk 1 → 3+ bildirim); 10 bildirimin altında "ısı yoğunluk göstermek için az, noktalara bak" uyarısı.
- `durum/zamanDurumu.ts`: canlıda listeler, sayılar ve ısı **aynı pencere** (çapa); zaman şeridi gerçek başlangıcı yazar. Sorgu aralığı nesnesi artık dakikada bir değil çapa değişince yenilenir.
- `modlar/genel.tsx` sağ panel: **Şimdi** (bekleyen SOS + en uzun bekleme + "Kuyruğa git"; görülmemiş ihbar türleriyle + "Listede göster"; ekipler + "Ekipler"), **Uydu hasarı** (analiz yoksa tek satır + "Hasar analizi"), **Açık ihbarlar** (kapananlar isteğe bağlı; boşsa "Son 24 saate genişlet").
- `konsolDurumu.ts` `depremler: false`; `useRiskSiralamasi` yalnız risk modunda; `useSimAlanlar` yalnız koşu varken ya da tatbikat modunda.

**Ölçüm** `[Ö]` (birleşik dal, kopya veritabanı, genel mod, sayfa açılışı, bu makine):

| | Önce | Sonra |
|---|---|---|
| İstek (akış hariç) | 16 | **13** |
| İnen veri | 993 KB | **201 KB** |
| Isı dokusu üretimi (istemci, 4 kanal) | ortanca 0,6 ms | değişmedi (yükü taşımıyor) |

- Bilgi kartı tarayıcıda denendi: "Kamera tespiti %52 · SOS çağrıları %48", "Metin ihbarı %98".
- `npx tsc -b` ve `kontrol:token` temiz.

**Açık kalan.**
- Harita sürüklenirken kare süresi ölçülemedi (tarayıcı paneli ekranda değildi, sayfa kare çizmiyordu).
- Sunucunun 0,5 km çekirdeği değişmedi: aynı noktada çok bildirim olunca leke ~1,2 km'ye yayılıyor. Daraltmak (ör. 0,25 km) tasarım kararı; kullanıcıya soruldu.
- Geliştirme sunucusunda kod sıcak yüklenince harita tuvali kayboluyor (sayfa yenilenince geliyor); yalnız geliştirmede, derlemede yok.

---

## J-176 🟡 Giriş ekranı: hesap açarken üç kapı seçilebilir duruyordu; şifre görünür yapılamıyordu; zemin boştu
**Durum:** KAPALI (18 Kasım 2026) · **Ölçüldü** · **Bulundu:** 18 Kasım 2026 (kullanıcı: "hesap aç diyince hâlâ 3 user type açık duruyor ama yazıda afetzede hesabı aç diyor"; "şifreler varsayılan gizli ama isterse görülebilir olmalı"; "arkaya güzel bir tasarım, bize uygun") · **İlgili:** J-156, CLAUDE.md §1, §5, §6, ARAYUZ §7

**Bulgu.**
- Hesap açma kipinde başlık "Afetzede hesabı aç" derken Afetzede / Saha ekibi / Koordinasyon seçicisi seçilebilir duruyordu. Sunucu zaten rolü istemciden almıyor: kayıt isteğine elle `"rol":"koordinator"` eklendi, hesap **afetzede** açıldı `[Ö]` (kopya veritabanı). Sorun ekranın yanıltıcı olmasıydı, yetki değil.
- Şifre alanları (giriş 1, şifre değiştirme 3) görünür yapılamıyordu; büyük harf kilidi uyarısı yoktu.

**Yapılan.**
- `kimlik/GirisEkrani.tsx`: hesap açma kipinde kapı seçicisi gizlenir; yerine "Burada yalnız afetzede hesabı açılır. Saha ekibi ve koordinasyon hesaplarını koordinasyon merkezi açar." yazar. "Giriş yap" ile seçici geri gelir.
- `kimlik/SifreAlani.tsx` (yeni), giriş ve şifre değiştirme ekranlarındaki 4 alanda: varsayılan gizli; göz düğmesi (`aria-label` "Şifreyi göster/gizle", `aria-pressed`, `aria-controls`, `type="button"`); kip ya da kapı değişince ve her gönderimde yeniden gizlenir; büyük harf kilidi açıksa uyarı; `autocomplete` (current/new-password) korunur.
- Zemin (ikinci tur; ilk tur tek renkli fay çizgileri ve il noktalarıydı, kullanıcı: "hiç güzel olmamış", formun altındaki kaynak paragrafı da yersizdi): gerçek veriden okunur bir Türkiye haritası.
  - Silüet: OSM ana yol iskeleti (`veri/altlik/ulke.json.gz`, ODbL 1.0), birleştirilip sadeleştirilmiş, soluk gri.
  - Etkin faylar (GEM, CC BY-SA 4.0): **renk = tür** (doğrultu atımlı / normal / ters; yeni token `--color-fay-*`, soğuk tonlar), **kalınlık ve parlaklık = kayma hızı** (`net_slip_rate`: < 3, 3–10, ≥ 10 mm/yıl). Kuzey ve Doğu Anadolu fayları bu yüzden öne çıkar.
  - 6 Şubat 2023 ana şokları projenin kataloğundan (`query.csv`): Mw 7,8 Pazarcık 04.17 ve Mw 7,5 Elbistan 13.24 (TSİ); kırmızı nokta (yıkıcı deprem, §6'ya uygun) ve açılışta bir kez genişleyip soluk kalan halka.
  - Sağ altta lejant: türler, sayıları, kalınlığın anlamı, depremler; kaynaklar lejantın son satırında tek satır (lisans gereği zorunlu, formun altındaki paragraf kaldırıldı).
  - Düzen: 1280 px ve üstünde form solda (2/5), harita sağda tam görünür; 768–1279 px'te formun arkasında soluk; telefonda inmez.
  - Üretim: `backend/araclar_giris_haritasi_uret.py` → `konsol/src/kimlik/girisHaritasiVerisi.ts` (412 fay, 950 yol hattı, 2 deprem; 49 KB, ~2 sn).
  - Hareket yalnız açılışta bir kez: önce silüet, sonra yavaştan hızlıya faylar, en son depremler (yalnız opacity + transform; "hareketi azalt" açıksa anında). Gradyan, cam efekti, sürekli hareket yok (CLAUDE.md §6, ARAYUZ §7).
- Harita ayrı parça olarak tembel yüklenir ve yalnız 768 px ve üstü ekranda istenir: telefonda formun arkasında görünmüyordu, afet bölgesinde mobil veriyle giren afetzedeye yük olurdu.

**Ölçüm** `[Ö]`:
- Derlemede harita parçası `GirisHaritasi-*.js` 51,7 KB, **gzip 20,2 KB**; ana pakete girmiyor (ana paket 111 KB gzip, değişmedi).
- 375 px genişlikte harita modülü **istenmedi** (0 istek); 1024 px'te istendi. Formun modülü 36 ms'de, harita 786 ms'de indi: form haritayı beklemiyor.
- Tarayıcıda denendi: göz düğmesi tip/etiket/basılı durumunu değiştiriyor; hesap açma kipinde seçici yok; girişe dönünce geri geliyor; kip değişince şifre yeniden gizli.
- `npx tsc -b` ve `kontrol:token` temiz.

**Açık kalan.**
- Kullanıcılar ekranında koordinatörün gördüğü tek seferlik geçici şifre bir giriş alanı değil, gösterim; bu işin kapsamında değil.

---

## J-177 🟠 Konsol yazısı küçüktü (U-5); acil bildirim saha ekibi ekranında hiç görünmüyordu
**Durum:** KAPALI (18 Kasım 2026) · **Ölçüldü** · **Bulundu:** 17 Kasım 2026 (J-167 U-5), 18 Kasım 2026 (acil bildirim incelemesi) · **İlgili:** J-45, J-167, ARAYUZ §4, §12

**Yazı ölçeği (Grup G, U-5).**
- Ölçüldü `[Ö]` (1024 px, görünen metin düğümleri): genel durumda 127 metnin 115'i (%91), acil bildirimde 138 metnin 120'si (%87) 11–12 px.
- Konsolda ölçek bir kademe büyütüldü: micro 11 → 12, small 12 → 13, body 13 → 14, subtitle 15 → 16; title ve metric aynı. `konsol/src/stil/token.css` ortak dosyanın üzerine yazar; tanıtım sitesi etkilenmez. `ARAYUZ_KARARLARI.md` §4 ve §12 güncellendi.
- Sonra `[Ö]`: 12 px'te yalnız büyük harfli bölüm etiketleri kaldı — genel %13 (17/127), acil bildirim %17 (24/138). 1440 px'te üst çubuk ve paneller sığıyor; taşan öğe bulunmadı.

**Acil bildirim.**
- Uçtan uca sınandı `[Ö]`: `araclar_akis_senaryosu.py`'ye 13 adım eklendi (afetzede ve saha yayınlayamaz 403; koordinasyon yayınlar 201; dört rol de canlı akışla alır; afetzede ve saha aktif listede görür; afetzede yayınlayanın adını görmez; geri çekilince akışla düşer; ikinci geri çekme 409). Senaryo **61/61**. Sunucu doğruydu.
- **Hata:** sayfa "bütün afetzede ve ekip ekranlarına gider" diyordu ama saha ekibi ekranında bildirim gösteren bileşen yoktu; sunucu ve akış saha rolüne gönderiyordu, ekran göstermiyordu. Tahliye ya da artçı uyarısı sahadaki ekibe ulaşmıyordu. `ekip/EkipEkrani.tsx`: üstte en yeni duyuru bandı, yeni duyuru uyarısı ve açılır duyuru listesi (afetzede ekranının bileşenleri). Tarayıcıda saha hesabıyla doğrulandı.
- Sayfa iyileştirmeleri (`modlar/bildirim.tsx`): seçili önem kendi renginde (acil kırmızı, uyarı turuncu); bölge alanında operasyon bölgeleri önerisi; yayındaki her bildirimde yayın süresi ve 24 saati geçende "hâlâ geçerli mi?"; 5'ten fazla bildirim yayındaysa "afetzede en yeni 5'i gösterir, N tanesi görünmüyor" uyarısı ve ilgili satırda işaret (sunucu `/aktif` sınırı 5); geri çekilenler ilk 3, "Tümünü göster"; boş durum düz cümle; amaç ve teknik notlar saha ekranını da anıyor.

**Açık kalan.**
- Bildirim kendiliğinden kalkmıyor (süre yok); arayüz uzun süredir yayında olanı soruyor. Otomatik süre için depo alanı gerekir; ayrı iş.
- Bölge alanı yalnız bilgi; bildirim bölgeye göre hedeflenmiyor, herkese gider.

---

## J-167 🟠 Uçtan uca tarama (17 Kasım): giriş ve SOS sınırsız, birkaç ölü ekran, saha ana düğmesi ekran dışında
**Durum:** KAPALI (18 Kasım 2026) — Grup A–G tamam (G: J-177) · **Bulundu:** 17 Kasım 2026 · **İlgili:** J-158, J-162, J-165, CLAUDE.md §1, §5, §8

> Not: J-166 kimliği kodda (ekip konum geçmişi, işlem kaydı hash zinciri) başka bir iş için
> kullanılıyor ama bu dosyada henüz maddesi yok; çakışmasın diye bu tarama J-167 aldı.

**Nasıl ölçüldü.**
- Çalışma ağacının o anki hâli (J-165 + J-166 commit edilmemiş).
- Gerçek veritabanının kopyasında ayrı bir API (8001) ve konsol (3201). Gerçek veritabanına yazılmadı.
- Demo hesaplarıyla dört rol, tarayıcıda (1440×900 ve 375×812) ve betikle (54 kontrol).
- Bu makinede ölçüldü (Windows, GPU yok).

**Geçenler.**
- Testler:
  - `tsc -b` ve `kontrol:token` temiz.
  - Backend 66/68 (kalan ikisi aşağıda T-1).
- Uçtan uca zincir:
  - afetzede SOS → koordinatör sevk → saha "yola çıktık / vardık / bitti" → afetzede "kapandı";
  - ihtiyaç, metin ve fotoğraf ihbarı;
  - duyuru yayını ve geri çekme;
  - hepsi işlem kaydında, zincir doğrulaması sağlam.
- Yetki:
  - 100 yolun yalnız 10'u oturumsuz (giriş, kayıt, yenile, çıkış, durum, deprem ve fay katmanı).
  - Rol istemciden alınmıyor.
  - Koordinatör yönetici hesabı açamıyor, kendi rolünü yükseltemiyor (409).
  - Kurcalanmış JWT ve `alg=none` 401 alıyor.
  - Başka afetzedenin fotoğrafı 404, SOS'u 403 dönüyor; yol geçişi denemeleri 404/422.
  - 20 MB gövde 422 ile reddediliyor.
- Canlı akış:
  - API'den atılan SOS 1,5 sn içinde konsolda.
  - Boşta 67 sn'de 8 istek (§4'teki eski ölçüm dakikada ~65'ti).
- Tatbikat ("Hızlı", Elektrik): 33,8 sn sürdü; bu sırada `/api/ozet` p95 12 ms (API donmuyor).
- Mobil: afetzede ve saha ekranında yatay taşma yok.

**Bulgular.**

*Güvenlik*
- **S-1 🟠 Giriş denemesi sınırı yok.**
  - Aynı hesaba 15 yanlış şifre gönderildi; hepsi 401 döndü, kilit ya da 429 yok.
  - Tek engel bcrypt (~370 ms).
  - ✅ Düzeltildi (17 Kasım, Grup B): `hiz_siniri.py`, `uclar/oturum.py` giriş ucu.
    - Aynı e-postaya 15 dakikada 5 hatalı deneme → 6.'da **429** + `Retry-After`. Kilit sürerken
      doğru şifre de 429 alır (şifre hiç denenmez). Başarılı giriş sayacı sıfırlar.
    - Aynı adresten 15 dakikada 30 hatalı deneme (çok hesaba yayılan) → 429.
    - Olmayan e-posta da aynı sayıda denemede aynı iletiyle kilitlenir; hesabın varlığı sızmaz.
    - Konsol iletisi: "Çok fazla hatalı deneme. 15 dakika sonra yeniden dene."
    - **Karar `[T]`: sayaç SQLite'ta** (`hiz_sayaclari`), bellekte değil. Sunucu yeniden
      başlatılınca kilit sıfırlanmaz, ileride birden çok worker'a geçilirse ortak kalır.
      Bedeli deneme başına bir yazma. Bir günden eski satırlar silinir. Sorgular
      `(anahtar, zaman)` indeksinden okunuyor; `EXPLAIN QUERY PLAN` tablo taramıyor.
    - **Vekil:** `X-Forwarded-For` geliyorsa yalnız `QUAKEMIND_VEKIL_GUVENILIR=1` iken
      adres sınırı uygulanır. Yoksa Nginx arkasında herkes aynı adresten görünür ve bir kişi
      herkesi kilitlerdi. Canlıda Nginx arkasında bu değişken açılmalı (Deha).
    - Tarayıcıda (veritabanı kopyasında) denendi: olmayan bir e-postayla 5 kez "E-posta veya
      şifre hatalı", 6.'da 429 iletisi.
- **S-2 🟠 SOS sınırı yok.**
  - Tek afetzede hesabı 0,2 sn'de 30 SOS attı; hepsi 201 döndü.
  - Kuyrukta 30 ayrı satır oldu ve ısı haritasında tek başına "en acil bölge" lekesi çıktı.
  - Kayıt açık, doğrulama yok: çok hesapla sel de mümkün.
  - Öneri:
    - hesap başına tek açık SOS; yenisi var olanı güncellesin;
    - hesap ve IP başına dakikalık sınır;
    - kayıtta IP sınırı.
  - ✅ Düzeltildi (17 Kasım, Grup B, U-3 ile): `depo/sqlite_surucu.py` `sos_ac_ya_da_guncelle`,
    `uclar/sozlesme.py` SOS ucu.
    - **Hesap başına tek açık SOS.** Açık çağrı varken yeniden basılırsa yeni satır açılmaz:
      konum, not ve kişi sayısı güncellenir; öncelik yalnız daha acile çıkar; ihtiyaçlar
      birleşir.
    - Yanıt 200 + mevcut kimlik (yeni çağrı 201).
    - Bekleme süresi bozulmasın diye çağrının geldiği an (`zaman`) değişmez; kaç kez ve en son
      ne zaman güncellendiği `ek`te durur.
    - Kontrol ve yazma aynı kilitte: aynı anda iki basış iki satır açamaz.
    - Isı haritasına güncellemede nokta yazılmaz: kişi bir kez sayılır.
    - Hesap başına dakikada 6, adres başına dakikada 30 basış → 429 ("Çağrın zaten
      iletildi… şebeke varsa 112'yi ara").
    - Hesap açmaya adres başına saatte 10 sınırı (aile, aynı Wi-Fi payı).
    - Yeni sorgu `ix_sos_kullanici_zaman` indeksinden okunuyor (`EXPLAIN QUERY PLAN`).
    - Ekranda:
      - konsol kuyruğu tek satır, "N kez yeniden gönderdi";
      - ayrıntıda "Yeni çağrı açılmadı; konum ve bilgiler güncellendi";
      - afetzede ekranı "Çağrın zaten iletilmişti… güncellendi (N kez)" diyor; açık çağrı
        varken form bunu önceden söylüyor.
    - Kopyada 8 hızlı SOS: 201, 200×5, 429×2 → tek açık satır, `guncellemeSayisi` 5. Konsolda
      tek satır göründü.
- **S-3 🟡 Kamera ucu bilinmeyen `modelType`'ta model çalıştırmıyor ama "temiz" diyor.**
  - `"ikisi"` gönderilince 28 ms'de 200 `NO_DETECTION` dönüyor.
  - `activeModels` iki modeli de çalışmış gibi yazıyor (`uclar/kamera.py:255`). Kural §1'e aykırı ve yanlış negatif üretiyor.
  - Bilinmeyen değer 422 almalı.
  - ✅ Düzeltildi (J-166): `cekirdek.py` `CameraAnalysisRequest.modelType` Literal; `uclar/kamera.py` model yoksa 503, `activeModels` yalnız koşanlar.
- **S-4 🟡 Belgeler oturumsuz açık.** `/docs`, `/redoc`, `/openapi.json` 200 dönüyor; üretimde kapatılmalı.
  - ✅ Düzeltildi (17 Kasım, Grup B): `fastapi_app.py`. Varsayılan **kapalı** (404); geliştirmede
    `QUAKEMIND_BELGELER=1` ile açılır. Konsol ve araçlar bunlara bağlı değil (tarandı).
- **S-5 🟡 Metin ihbarındaki adres dış servise gidiyor.**
  - Adres, kamuya açık OSM Nominatim'e gönderiliyor (`apps/disaster_nlp/src/ner_extraction.py:120`).
  - Afetzedenin yazdığı adres üçüncü tarafa çıkıyor.
  - Nominatim saniyede 1 istek kuralı koyuyor; internet zayıfsa adres bulunamıyor. Yerel mahalle/sokak dizini önerilir.
  - ✅ Düzeltildi (17 Kasım, J-170): adres yerel dizinden çözülüyor, metin dışarı gitmiyor.
- **S-6 ⚪ Canlı akış kimliği yalnız bağlanırken denetliyor** (`uclar/canli.py`). Hesap askıya alınsa da açık akış sürer. Kodda görüldü, ölçülmedi.
  - ✅ Düzeltildi (17 Kasım, Grup B): `uclar/canli.py`, `konsol/src/canli/canliAkis.ts`.
    - Açık akış oturumu 15 saniyede bir yeniden denetliyor.
    - Hesap askıya alınırsa, oturum kapanırsa ya da rol değişirse akış `oturum-bitti` olayıyla
      kapanıyor. İstemci yeniden bağlanmayı bırakıyor, sonraki istek giriş ekranına götürüyor.
    - Kopyada: saha konsolu açıkken hesap askıya alındı; ~24 sn içinde giriş ekranına düştü,
      canlı akışa yeniden bağlanma denemesi olmadı.

*İşlev ve doğruluk*
- **F-1 🟠 Metin modeli kendi örnek cümlesini çözemiyor.**
  - Kutudaki örnek, "Armutlu Mahallesi 5. Sokak'ta bina çöktü, iki kişi enkaz altında…", "metinde adres bulunamadı" sonucu verdi.
  - Kategori "Acil Yardım İhtiyacı" çıktı (enkaz cümlesi).
  - İlk istek 31,8 sn sürdü.
  - ✅ Düzeltildi (17 Kasım, J-170): aynı cümle "5. Sokak, Armutlu Mah., Hatay" (sokak düzeyi, ±400 m), kategori "Enkaz Bildirimi".
- **F-2 🟡 Koordinatla gelen SOS'ta mahalle boş.**
  - Konsolda "Mahalle bilinmiyor", saha ekranında yalnız ham koordinat (`36.19250, 36.14150`) görünüyor.
  - Sunucu koordinattan mahalleyi bulabilir (altlıkta mahalle var).
- **F-3 🟡 "Yol ve Rota" sayfası ölü.** "Rota ucu (A*) henüz bağlı değil" diyor, oysa görev ekranında rota var (J-162). Ya bağlanmalı ya menüden kalkmalı.
  - ✅ Düzeltildi (18 Kasım, J-171): kullanıcı kararı "bağla". Sayfa rota motoruna bağlandı, motor da yenilendi.
- **F-4 🟡 Zaman şeridi histogramı hiç yazılmamış.**
  - Şerit canlı bağlıyken ve 35 SOS varken de "canlı akış bağlanınca şerit dolacak" diyor (`konsol/src/kabuk/ZamanSeridi.tsx:114-119`).
  - Metin ya düzeltilmeli ya histogram yazılmalı.
  - ✅ Düzeltildi (18 Kasım, J-171): `/api/olay-yogunlugu` (saat başına SOS ve ihbar, SQL'de sayım, zaman indeksiyle) ve şeritte yığılmış çubuklar. Yoklama yok; canlı akışla tazelenir.
- **F-5 ⚪ Afetzede "Nereye" kartında İtfaiye 0, Polis 0.** Antakya merkezi, 5 km içinde. Yerel OSM kopyasında bu türler var mı bakılmalı; doğrulanmadı.
  - ✅ Bakıldı (18 Kasım, J-171): yerel OSM kopyasında Antakya kutusunda polis ve itfaiye istasyonu **yok** (geniş aramada yalnız "Hatay Polis Evi" misafirhanesi). Çıkarım doğru, veri eksik. Kart artık "0" yerine "—" yazıyor ve "haritada kayıtlı yok; yakında olmadığı anlamına gelmez, acil durumda 112" diyor.
- **F-6 ⚪ Tatbikat ilerleme metinlerinde Türkçe karakter yok.**
  - "Uydu goruntusu indiriliyor", "Analiz tamamlandi" gibi.
  - Drone katmanında da "Uydu" yazıyor.
  - ✅ Düzeltildi (18 Kasım, J-171): `apps/road_damage/worker.py` ilerleme ve not metinleri, `utils/tatbikat.py` uyarısı Türkçe karakterle; drone kaynağında "Drone görüntüsü indiriliyor", tatbikat aşama adı "Görüntü (drone ya da uydu)".
- **F-7 ⚪ Hasar sayfası kapsaması %0 olan görüntüleri de listeliyor.**
  - ✅ Düzeltildi (18 Kasım, J-171): alanı kapsamayan görüntü listenin altında ve sönük; "%0" yerine "alanın dışında; seçersen alan bu görüntüye taşınır" yazıyor (seçilince alan taşındığı için listeden atılmadı).

*Arayüz*
- **U-1 🟠 Saha ekranının ana düğmesi telefonda ekranın dışında.**
  - 375×812'de "Yola çıktık" 800. pikselde başlıyor; görmek için kaydırmak gerekiyor.
  - Üstteki "Rotayı haritada göster" aynı birincil vurguda, dikkati bölüyor.
  - Öneri: adım düğmeleri yapışkan bir alt çubukta.
  - ✅ Düzeltildi (17 Kasım, Grup C): `konsol/src/ekip/EkipEkrani.tsx`, `stil/token.css` (`.alt-guvenli`),
    `index.html` (`viewport-fit=cover`).
    - Adım düğmeleri görev kartının altında yapışkan bir çubukta: kart boyunca ekranın altında durur.
    - Birincil adım tam genişlikte; "İşimiz bitti…" ve "Gidemiyoruz…" yan yana.
    - iPhone'un alt güvenli alanı hesaba katılır.
    - "Rotayı haritada göster" ikincil görünüme indi.
    - 375×812'de `saha-demo` ile ölçüldü: "Yola çıktık" 700–748 px'te, kaydırmadan görünüyor (önce ~800).
- **U-2 🟡 API ayakta değilken giriş ekranı ham hata gösteriyor:** "/api/oturum/giris → HTTP 500". API'nin açılışı ~30 sn sürüyor; bu sürede insan diliyle bir ileti gerekir.
  - ✅ Düzeltildi (17 Kasım, Grup C): `konsol/src/kimlik/GirisEkrani.tsx`.
    - 5xx ve ağ hatasında "Sunucu şu an yanıt vermiyor; açılıyor olabilir (yaklaşık 30 sn).
      Birkaç saniye sonra yeniden dene." yazıyor.
    - Yoklama yok: kişi yeniden basınca dener (§4).
    - API açılırken tarayıcıda denendi; ham ileti görünmedi.
    - Kök neden: uvicorn açılış bitene kadar bağlantı kabul etmiyor, vekil o sırada 500/502 dönüyor.
- **U-3 🟡 Aynı kişinin art arda SOS'ları kuyrukta ayrı satır.** S-2 ile birlikte birleştirilmeli.
  - ✅ Düzeltildi (S-2 ile): kuyrukta tek satır, "N kez yeniden gönderdi".
- **U-4 🟡 Tatbikat lejantı haritanın yaklaşık üçte birini kapatıyor.** "Haritada ne var" kutusu varsayılan olarak kapalı açılmalı.
  - ✅ Düzeltildi (17 Kasım, Grup C): `konsol/src/kabuk/HaritaGostergesi.tsx`. Varsayılan kapalı; başlık
    görünür, tek tıkla açılır. Tatbikat koşturulup tarayıcıda bakılmadı (değişiklik tek satır, başlangıç değeri).
- **U-5 ⚪ Konsol metni küçük.** Görünen metnin %87'si 11–12 px (169/194 öğe), operasyon ekranı için küçük.
- **U-6 ⚪ Afetzede ekranında adsız düğmeler var.** Yer listesi satırları ve alt kartlar ekran okuyucuya ad vermiyor. Konsolda adsız düğme yok.
  - ✅ Düzeltildi (17 Kasım, Grup C): `afetzede/BildirDugmeleri.tsx`, `afetzede/NereyeKarti.tsx`.
    - Erişilebilirlik ağacında ölçüldü: üç ihbar kartı artık "Hasar fotoğrafı: Fotoğraf çek, modele
      incelet, ihbar et" gibi okunuyor.
    - Yer satırları "Toplanma alanı, Turunçlu, yürüyerek 650 m, yön batı" diye okunuyor.
    - 375×812, afetzede ekranında adsız düğme kalmadı.

*Performans*
- **P-1 Harita parçası büyük.**
  - Üretim derlemesinde 2,08 MB (gzip 574 KB).
  - Afetzede ekranı da deck.gl yüklüyor (`afetzede/haritaKatmanlari.ts`); toplam ≈ 711 KB gzip JS.
  - Öneri:
    - afetzede haritasını yalnız maplibre ile çiz;
    - yavaş 3G'de "SOS'a basılabilir" süresini ölç.
  - ⏸ Ölçüldü, ertelendi (18 Kasım, J-172): SOS'un kritik yolu **153 KB** gzip (giriş + afetzede ekranı); 560 KB'lık harita parçası kritik yolda değil, sonra iner (toplam 731 KB). Karo katmanını (`@deck.gl/geo-layers`) ayırmak yalnız 6,6 KB kazandırdı. Afetzede altlığı da deck.gl ile çizildiği için "yalnız MapLibre" altlık çiziminin baştan yazılması demek; kullanıcıyla konuşulmadan yapılmadı.
- **P-2 Metin analizinin ilk isteği 31,8 sn.** Model tembel yükleniyor, üstüne Nominatim bekleniyor. Model işçide açılışta ısıtılmalı; adres çözümü yerelde yapılmalı (S-5).
  - ✅ Düzeltildi (17 Kasım, J-170): model ayrı işçide, açılışta ısınıyor. Isınma sürerken gelen ilk istek ~7 sn, sonrakiler ~65 ms.
- **P-3 Isı haritası soğukken yavaş.**
  - İlk açılışta 4 paralel istek 4,3 sn sürüyor; ısınınca 28 ms.
  - Öneri: açılışta ısıt ya da 4 kaynağı tek istekte dön.
  - ✅ Düzeltildi (18 Kasım, J-172): sebep ısı değil PostGIS denemesiydi. `utils/postgis_manager.py` her sunucuda varsayılan adrese bağlanmayı deniyordu: deneme 4,0 sn, sonuç 30 sn saklandığı için **her 30 sn'de bir** gelen ilk istek 4 sn bekliyordu. Bağlantı artık yalnız `POSTGIS_URL` açıkça verilmişse denenir. Soğuk 4 kanal: 4,3 sn → **44 ms**; sıcak 28 ms `[Ö]`.
- **P-4 Tatbikatta yol ağı 12,4 sn, görüntü 12,6 sn sürdü.** `DEMO_CALISTIRMA.md` §4'e göre önbellekten 0–1 sn olmalıydı. Katalog alanları önceden indirilmeli.
  - ✅ (18 Kasım, J-172) Yol ağı: bu makinede 4 tatbikat alanında 0,0–1,1 sn `[Ö]`. Önbellek tutmasa da yerel bölge dosyası (`araclar_yerel_osm_kur.py`) devreye giriyor; 12,4 sn bölge dosyası olmayan ortamda ölçülmüştü. Canlı sunucuda bu dosya kurulu olmalı.
  - ✅ Görüntü: açık lisanslı kaynakların (OpenAerialMap, Esri Wayback) birleşik görüntüsü `veri/goruntu_onbellek/`'te saklanıyor (en çok 40 dosya). Defne/Elektrik sahnesi ilk 2,75 sn, ikinci **0,03 sn** `[Ö]`. Google karoları lisans gereği saklanmaz; eksik inen görüntü (geçici hata, J-89) saklanmaz.
- **P-5 Hazır olma ucu yok.** API açılışı ~30 sn, `/health` 404. Hazır ucu eklenmeli, konsol beklerken bunu göstermeli (U-2).
  - ✅ Düzeltildi (17 Kasım, Grup C): `uclar/genel.py` `GET /api/hazir`.
    - Oturumsuz; yalnız evet/hayır döner.
    - Veritabanı okunuyor ve analiz işçisi havuzu kurulmuşsa 200, değilse 503.
    - Not: açılış sürerken uvicorn bağlantı almadığı için bu uç da yanıt veremez. Açılıştan sonraki
      eksikleri ayırt eder.
    - Bu makinede açılış ~45–60 sn sürdü (30 değil).
- **P-6 Zincir doğrulaması bütün tabloyu okuyor.**
  - `/api/islem-kayitlari/dogrula` her istekte bütün `islem_kayitlari`'nı tarıyor.
  - Kayıt büyüdükçe doğrusal büyür. Artımlı doğrulama ya da sınır gerekir.
  - ✅ Düzeltildi (J-166): artımlı doğrulama, 100 bin kayıttan sonra 100 yeni kayıt 2,9 ms; tam tarama `?tam=true`.

*Test*
- **T-1 İki test kırık.**
  - `test_konum_gecmisi_tutulur` sıraya bağlı: tek başına geçiyor, dosyanın tamamında kalıyor. `test_islem_kaydi.py:116` saha hesabını başka ekibe taşıyor.
  - `test_heatmap_offline_fallback_returns_200` eskimiş: uç artık giriş istiyor (401), test oturumsuz çağırıyor.
  - ✅ Düzeltildi (J-166): ikisi de geçiyor, `pytest -q` 76/76.
- **T-2 8000'deki API eski kodla çalışıyor.** 14:24'te açılmış, J-166 dosyaları 14:49'da değişti. Yeniden başlatılmadan denenen her şey eski kodu sınar.

**Açık.**
- Fotoğraf yükleme tarayıcıda denenmedi (dosya seçici sürülemedi); yalnız API ile denendi.
- Hasar analizi (uydu) ve risk tahmini tarayıcıda koşulmadı.
- Yavaş ağ ve düşük cihaz ölçümü yapılmadı.

**Temizlik (18 Kasım 2026).** Grup A–C `kamera-analiz-gelistirme`, D J-170, E J-171, F J-172'de kapandı; J-173 ve J-174 ayrıca risk ve uçtan uca akış. Kalan tek madde U-5: konsol metninin %87'si 11–12 px; token ölçeği (`ARAYUZ_KARARLARI.md`) kullanıcıyla konuşulmadan değiştirilmez.

**Kapanış (18 Kasım 2026).** Son kalan Grup G (U-5, konsol yazı boyutu) J-177'de yapıldı.

## J-178 🟡 Haritada mahalle, sokak ve cadde adları okunmuyordu
**Durum:** KAPALI (20 Kasım 2026) · **Bulundu:** 18 Kasım 2026 (kullanıcı ekran görüntüsüyle: "mahalle sokak cadde isimleri gibi isimler okunmuyor hiç") · **İlgili:** J-41, J-177, ARAYUZ §11

**Bulgu.** `harita/katmanlar.ts` `etiketKatmani`: sokak adları en küçük boy (micro) ve en sönük griyle (ink-3), mahalle ve köy adları small ve ink-2 ile yazılıyordu. Hale (`outlineWidth` 3) yazı atlasının dar boşluğu (deck.gl varsayılanı radius 12, buffer 4) yüzünden inceydi; koyu yapı çokgenlerinin üstünde ad zeminle karışıyordu.

**Yapılan.**
- Sokak ve cadde: body (14 px) + ink-2. Mahalle ve köy: body + ink + kalın (600). Şehir ve ilçe: subtitle + ink + kalın. Bölge adları: title + kalın.
- Yazı atlası `buffer` 8, `radius` 16; hale `outlineWidth` 6 (zemin renginde). Kalın hale adı yapıların ve yolların üstünde ayırır.
- Büyüyen ad daha çok yer kapladığı için çakışma süzgeci yakın adlardan birini yazmaz; okunur az ad, okunmayan çok addan iyi.

**Doğrulama.** Tarayıcıda Antakya merkezinde mahalle ölçeğinde ve sokak ölçeğinde bakıldı: Meydan, Antakya, Yenicami, Habib-i Neccar; General Şükrü Kanatlı Caddesi, Kemal Paşa Caddesi okunur. `npx tsc -b` ve `kontrol:token` temiz. Ölçüm (kare süresi) yapılmadı; yazı atlası bir kez üretilir.

---

## J-180 🟠 Afetzede çevresindeki kapalı yolları ve hasarı görmüyordu; toplanma alanları hiç yüklenmiyordu
**Durum:** KAPALI (23 Kasım 2026) · **Bulundu:** 23 Kasım 2026 (kullanıcı: "afetzede ekranında ısı haritası görünmüyor, kapalı yollar da görünmüyor"; toplanma hatası kendi tarayıcı sınamamızda) · **İlgili:** J-42, J-58, J-175, ARAYUZ §6

**Bulgu.**
- Afetzede haritasında yalnız yakın yerler, kendi çağrıları ve rota vardı. Koordinatörün ısı haritası (`/api/road_damage/heatmap`) ve kapanma katmanı afetzedeye kapalı: ısı SOS konumlarından da beslenir, afetzede başkasının çağrısını göremez (J-42). Yani afetzede nereden geçmemesi gerektiğini görmüyordu.
- Konsolda toplanma alanları hiçbir modda yüklenmiyordu: `veri/katman.ts` `useToplanmaAlanlari` kutuyu görünen altlık bölgelerinden kuruyordu; her zaman görünen ülke iskeleti (`tur: 'ulke'`) bütün Türkiye'yi kapsadığı için kutu 8°'yi aşıyor, sunucu 422 veriyordu.

**Yapılan.**
- Yeni uç `GET /api/afetzede/cevre` (`uclar/afetzede_cevre.py`), giriş yapmış her rol. Konumun en çok 5 km çevresi (varsayılan 3 km), son 30 gün:
  - Kapalı yollar: uydu analizinden bulunan kapalı yol parçaları, çizgisiyle. Aynı parça birden çok analizde kaydedildiyse bir kez döner (Antakya kopyasında 66 kayıt → 21 parça).
  - Hasar bölgeleri: ~250 m'lik sabit ızgara karelerinde bildirim sayısı. **SOS sayılmaz**; yalnız uydu, fotoğraf ve metin. Yalnız en az 3 bildirimli kareler döner (tek kişinin bildirimi konum olarak açılmaz). Sayım SQL'de (`depo.hasar_hucreleri`, `EXPLAIN QUERY PLAN` indeks kullanıyor).
- Afetzede haritası: hasar kareleri (3–5 / 6–14 / 15+ bildirime göre koyulaşan turuncu-kırmızı), kapalı yollar zemin renginde kenarlıklı kırmızı çizgi. Üzerine gelince bilgi kartı: kaç bildirim, kaynakları, son bildirim saati, "binalara girme"; kapalı yolda kaynağı ve "yürüme rotası bilinen kapalı yollardan kaçınır" (`uclar/yerler.py` rota bunu yapıyor). Sol üstte tek satırlık lejant sayılarla ve aç/kapa kutusuyla; kaynak ve uyarı metni üzerine gelince.
- Toplanma: ülke iskeleti kutuya katılmıyor (`b.tur !== 'ulke'`).

**Doğrulama.** `tests/test_afetzede_cevre.py` 6/6 (oturumsuz 401, SOS ve 3'ten az bildirimli kare dönmüyor, zaman penceresi, sınırlar 422, indeks, kapanma tekrarı). `pytest -q` 153/153. Tarayıcıda afetzede hesabıyla Antakya Cumhuriyet mahallesi: lejant "Kapalı yol 21 · Hasar 6", kırmızı çizgi ve kare çiziliyor, bilgi kartı "8 bildirim · uydu 8", kapatınca katman gidiyor. Toplanma isteği 200, simgeler görünüyor. `npx tsc -b` ve `kontrol:token` temiz. Konum seçilmemişse tehlike gösterilmez (uç konum ister); kare süresi ölçülmedi.

---

## J-181 🟠 Yürüme rotası kapanmanın yalnız orta noktasına bakıyordu, her istekte bütün hasar kayıtlarını okuyordu; dış servis yedeği kapanmayı hiç denetlemiyordu
**Durum:** KAPALI (24 Kasım 2026) · **Bulundu:** 24 Kasım 2026 (kullanıcı: "yol isterken dış servisten nereden istiyoruz, kapalı yolları kullanabilecek miyiz; performanslı, güvenilir ve doğru çözmeliyiz") · **İlgili:** J-34, J-44, J-58, J-180

**Bulgu.** Sayma birimi: Antakya yol ağı, kopya veritabanı (356 kapanma kaydı, 303 hasar noktası); ölçek denemesi aynı kopyaya 100 000 yapay hasar noktası eklenmiş geçici veritabanında. Cihaz: geliştirme dizüstü, CPU.
- Asıl rota kendi yol ağımızda (`yol_agi.py`, Dijkstra, J-44). Kapanma eşleşmesi kapalı parçanın **orta noktasına** 25 m bakıyordu. Parçaların çizgisi J-58'den beri saklanıyor ama kullanılmıyordu: çizgiye 25 m içindeki 47 kenarın 4'ü kaçıyordu (%8,5). [Ö]
- `hasar_verisi` her rota isteğinde kutudaki bütün hasar satırlarını (en çok 100 000) Python'a çekip süzüyor, "veri değişti mi"ye ondan sonra bakıyordu. 100 000 kayıtla bu okuma 1240 ms. Ayrıca sınır süzmeden önce uygulandığı için kayıt 100 000'i aşınca hasar noktaları sessizce eksik kalıyordu (50 233 yerine 49 951). [Ö]
- Aynı kapalı parça eski analizlerde tekrar tekrar kaydedilmiş: 356 kayıt, 48 ayrı parça. Yanıt "356 kapanma" diyordu.
- Yol ağı olmayan bölgede yedek, FOSSGIS'in OSRM sunucusu (`routing.openstreetmap.de`, yaya profili). OSRM istekte "şu noktadan geçme" kabul etmez; tek rota alınıyor ve kapanmalara karşı hiç denetlenmiyordu.
- Afetzede haritası (J-180) son 30 günün kapanmalarını, rota bütün kapanmaları kullanıyordu: haritada görünen ile rotanın kaçındığı farklıydı.

**Yapılan.**
- Kapanma, çizgisi 5 m'de bir örneklenerek eşleşir (`yol_agi._ornekle`); çizgisiz kayıt orta noktayla. Hem yürüme hem araç rotası (aynı `carpanlar`).
- Depo: `rota_tehlike_imzasi` (kapanma ve hasar için sayı + son zaman, SQL'de) ve `rota_tehlike_noktalari` (süzme SQL'de, yalnız lon/lat/ek). Satırlar yalnız imza değişince okunur, kutu başına önbellek. `yol_kapanmalari(lon, lat)` indeksi eklendi.
- Aynı parça (aynı orta nokta) bir kez sayılır (`yol_agi.kapanma_listesi`).
- Dış servis yedeği (`/api/afetzede/sokak-rotasi`):
  - en çok 3 alternatif istenir, her biri kapanma çizgilerine karşı denetlenir (`yol_agi.rotadaki_kapanmalar`);
  - hepsi kapanmadan geçiyorsa ilk geçilen kapanmanın iki yanına 150 m dik ara noktayla en çok iki istek daha atılır;
  - en az kapanmadan geçen, eşitse en kısa rota seçilir;
  - temiz rota yoksa yanıt ve ekran kırmızıyla "bu rota bilinen N kapalı yoldan geçiyor" der.
  - Servis korunur: istekler arası en az 1 sn, aynı istek 10 dk önbellekte, 429'da açık hata. Hasarı ve bilinmeyen yıkık yolu hâlâ bilmez; ekran bunu yazar.
- Afetzede çevre ucu kapanmaları zaman sınırsız verir; harita ile rota aynı kümeye bakar. Hasar bölgelerinde 30 gün kalır.

**Doğrulama.**
- Sonra, aynı birimlerle [Ö]:
  - işaretlenen kenar 43 → 47;
  - rota isteği (Arama + rota, ortanca) kopya veritabanında 35 → 29 ms;
  - 100 000 kayıtla tehlike verisi her istekte 1240 ms okunuyordu; şimdi veri değişmedikçe 36 ms (imza sorgusu), değişince bir kez 128 ms. Rota isteği 100 000 kayıtla 66 ms.
- `tests/test_yurume_rotasi_kapanma.py` 7 test, yapay yol ağıyla:
  - orta noktası 35 m uzakta, ucu 10 m yakında olan kapanma;
  - süzme, tekrar ve önbellek;
  - imza sorgusunda indeks;
  - rota–kapanma kesişimi;
  - yedekte sapmayla kaçınma, temiz yol yoksa uyarı, kapanma yoksa tek istek, servis boşsa 503.
- `test_afetzede_cevre.py` eski kapanmayı da sınar.
- Tarayıcıda afetzede, Antakya Cumhuriyet → Gazi toplanma alanı: rota 760 m, yanıtta "kapanma 48, rotadaKapanma 0"; lejant da 48.
- Yedek, sahte servisle sınandı; gerçek servisle uçtan uca denenmedi (konum dışarı gider). Servisin yaya profilinin alternatif verdiği elle bakıldı: kısa yolda 1, Kahramanmaraş'ta 2 rota.

---

## J-182 🔴 Boş sunucuda (canlıya ilk çıkış) hiçbir rolde girilemiyordu; ilk yöneticiyi açmanın güvenli ve belgeli yolu yoktu
**Durum:** KAPALI (24 Kasım 2026) · **Bulundu:** 24 Kasım 2026 (kullanıcı: "diğer hesapları kim açacak; Deha canlıya aldığında hesaplar orada oluşmuyor, hiçbir rolde girilemiyor") · **İlgili:** J-155, J-156, J-157, CLAUDE.md kural 5

**Bulgu.**
- Hesap düzeni doğruydu: kayıt ekranı yalnız afetzede açar, istemci rol seçemez. Saha, koordinatör ve yönetici hesaplarını konsoldaki Kullanıcılar sayfası açar: yönetici her rolü, koordinatör saha hesabını; geçici şifre bir kez görünür ve ilk girişte değiştirilmek zorunda.
- Ama bu zincir bir yöneticiyle başlıyor. Boş veritabanında yönetici olmadığı için kimse hesap açamıyordu. Tek yol sunucuda `araclar_kullanici.py ekle` idi ve:
  - kurulum belgesinde (`deploy/README.md`) hiç geçmiyordu;
  - şifre verilmezse depoda açık yazan `degistir1234` şifresini kullanıyordu;
  - şifre değiştirme zorunluluğu koymuyor, hesap kayıt defterine yazmıyordu;
  - şifreyi komut satırından alıyordu (kabuk geçmişine düşer).
- Tek yönetici şifresini unutursa sıfırlayacak kimse yoktu.
- Konsolda yöneticinin düğmesi "Yeni ekip hesabı" yazıyordu; oysa aynı formdan koordinatör ve yönetici de açılıyor.

**Yapılan.**
- `araclar_kullanici.py` yeniden yazıldı:
  - `ilk-yonetici`: yalnız hiç yönetici yokken çalışır. Kayıtlı bir afetzede e-postası verilirse o hesap yükseltilir ve şifresi yenilenir.
  - `sifre-sifirla`: açık oturumları da kapatır.
  - `ekle` ve `listele` korundu; `listele` geçici şifresi duranları gösterir.
  - Şifre her zaman rastgele üretilir (`kimlik.gecici_sifre`, konsolla aynı tek kaynak), yalnız bir kez ekrana yazılır, ilk girişte değiştirilmesi zorunludur. İşlem hesap kayıt defterine yazılır.
  - Komut satırından şifre kabul edilmez.
- `deploy/README.md`: "İlk hesaplar (canlıya ilk çıkış)" bölümü. Çalışan konteynerde `docker exec … python araclar_kullanici.py ilk-yonetici …`, ardından konsoldan hesap açma, şifre sıfırlama; demo aracının canlıda çalıştırılmayacağı.
- Konsol: yöneticide düğme ve çekmece "Yeni hesap", koordinatörde "Yeni ekip hesabı".

**Doğrulama.**
- `tests/test_araclar_kullanici.py` 4 test:
  - ilk yönetici bir kez açılır, şifre rastgele ve geçicidir, defterde kayıt var;
  - kayıtlı afetzede yükseltilir, eski şifresi geçersiz olur;
  - şifre sıfırlama; komut satırı şifresi reddedilir;
  - **boş sunucuda uçtan uca:** önce kimse giremez → araçla ilk yönetici → geçici şifreyle girer → şifre değiştirmeden hesap açamaz (403) → değiştirir → koordinatör ve saha hesabı açar → koordinatör aldığı şifreyle girer.
- `pytest -q` 164/164.
- Araç boş geçici veritabanında elle çalıştırıldı: ikinci `ilk-yonetici` reddedildi, Türkçe ad doğru kaydedildi.
- Konsolda yerel demo yöneticiyle "Yeni hesap" çekmecesinde üç tür göründü.
- `tsc` ve `kontrol:token` temiz.
- Canlı sunucuda çalıştırılmadı (Deha'da).

---

## J-183 🟡 Ortak örnek hesap yoktu; profil simgesi tıklanınca doğrudan çıkış yapıyordu, hesap ayarları yoktu
**Durum:** KAPALI (24 Kasım 2026) · **Bulundu:** 24 Kasım 2026 (kullanıcı: "her type için örnek hesaplar, herkes oradan girse; profil simgesi hesap ayarlarına götürsün, çıkış altında olsun") · **İlgili:** J-182, J-155, J-157

**Bulgu.**
- Tanıtım ve teslimde ekip ve değerlendiriciler her rol için ayrı hesap istiyordu. Yerel demo aracının şifresi depoda açık olduğu için canlıda kullanılamıyordu.
- Sağ üstteki baş harf simgesine tıklamak onaysız çıkış yapıyordu. Hesap ayarları sayfası yoktu; şifre değiştirme yalnız zorunlu geçici şifre ekranındaydı.
- Saha ekibi ve afetzede ekranlarında ayrı "Çıkış" düğmeleri vardı. Afetzede ekranının üst şeridi telefonda (375 px) 422 px'e taşıyor, sayfa yana kayıyordu.

**Yapılan.**
- `ornek_hesaplar.py`: dört rol için ortak hesap. API açılırken yalnız `QUAKEMIND_ORNEK_HESAP_SIFRESI` tanımlıysa kurulur ve şifre bu değere çekilir. Şifre en az 10 karakter olmalı ve depodaki demo şifresi olamaz; şifre depoda yazmaz.
- Ortak hesabın şifresi uygulamadan değiştirilemez (403); konsoldan da sıfırlanamaz (409, ekranda açıklama). Biri değiştirseydi herkes dışarıda kalırdı.
- `araclar_demo_hesaplari.py` aynı listeyi kullanır (yalnız yerel).
- Profil menüsü (`kimlik/ProfilMenusu.tsx`): konsol, saha ve afetzede ekranlarında aynı. Ad, e-posta ve rol (ortak hesapsa belirtilir), "Hesap ayarları", altında "Çıkış yap".
- Hesap ayarları (`/hesap`): kim olduğun, rolün ne yapabildiği, şifre değiştirme (ortak hesapta açıklama), çıkış. Şifre formu zorunlu şifre ekranıyla ortak (`SifreFormu`).
- Telefonda afetzede ve saha ekranında logo yazısı gizlenir; taşma gitti (375 → 375 px).
- `deploy/README.md`: "Ortak örnek hesaplar" bölümü.

**Doğrulama.**
- `tests/test_ornek_hesaplar.py` 2 test: değişken yok ya da zayıfsa kurulmaz; dört rol kurulur ve girilir, saha ekibe bağlı, ikinci açılışta tekrar yazılmaz, şifre değiştirme 403, sıfırlama 409, değişken değişince şifre değişir.
- Tarayıcıda:
  - menü konsolda, saha ekranında ve afetzede ekranında açılıyor;
  - hesap ayarlarında ortak hesap açıklaması ve normal hesapta şifre formu görünüyor;
  - menüden çıkış giriş ekranına götürüyor;
  - telefon genişliğinde taşma yok.
- `tsc` ve `kontrol:token` temiz.

---

## J-184 🔴 Canlıda hasar analizi kapalı yol bulamıyordu ("Yol katmanı alınamadı"); model listesinde 4 yerine 1 model vardı
**Durum:** KOD TARAFI KAPALI (24 Kasım 2026); sunucuya dosya kurulumu Deha'da · **Bulundu:** 24 Kasım 2026 (kullanıcı ekran görüntüsü: canlıda Antakya Elektrik'te "Kapalı yol 0, açık yol 0 segment, yol katmanı alınamadı"; aynı alan yerelde kapalı yol buluyor) · **İlgili:** J-68, J-79, J-36

**Bulgu.** Canlı sürüm `671dad0` (yanıt başlığı `x-quakemind-revision`), kod main ile aynı. Fark sunucudaki dosyalarda:
- Yol maskesi önce yerel `roads.gpkg` (164 MB, `araclar_yerel_osm_kur.py` çıktısı) ile çizilir. Dosya `.gitignore`'da ve imajın içindeki `apps/road_damage/data/osm/` altında aranıyordu. İmaj temiz Git arşivinden kurulduğu için canlıda yok; elle kopyalansa her dağıtımda silinirdi.
- Dosya yoksa analiz Overpass'a sorar; sunucudan yanıt gelmedi, maske boş kaldı. Sonuç "yol katmanı alınamadı" oldu ama nedeni yazmıyordu.
- Dört uydu modeli künyesinden yalnız etkin olanın (MiT-B4) Hugging Face kaynağı var. MiT-B0, MiT-B2 ve U-Net MiT-B4 ağırlıkları yalnız geliştirici makinesinde; ağırlığı olmayan model konsolda listelenmez.
- `/api/hazir` bu eksikleri göstermiyordu ("hazır: evet").

**Yapılan.**
- `yerel_yol.osm_dizini()`: `QUAKEMIND_OSM_DIZINI`, kalıcı veri dizini `veri/osm/` (canlıda `quakemind-data` birimi) ve eski yer sırayla; `roads.gpkg` içeren ilki. `local_osm` aynı dizini kullanır.
- Yol katmanı boşsa sonuç ve not nedeni yazar: "sunucuda yerel yol dosyası kurulu değil, dış yol servisi yanıt vermedi" ya da "dosya bu alanı kapsamıyor".
- `/api/hazir`: `yerelYolVerisi` (evet/hayır) ve `uyduModeli` (hazır/tanımlı sayısı); dosya yolu dönmez.
- `deploy.sh`: künyesinde `hf` kaynağı olan bütün modeller indirilip SHA ile doğrulanır (bugün yalnız etkin model).
- `deploy/README.md` "Analiz dosyaları": `roads.gpkg` ve üç ağırlığın canlı birimlere `docker cp` ile bir kez kopyalanması. Kalıcı çözüm Hugging Face.

**Doğrulama.**
- `tests/test_yerel_osm_dizini.py` 2 test; `test_hazir_ucu` yeni alanlarla.
- Yerelde `/api/hazir`: `yerelYolVerisi: true`, `uyduModeli 4/4`; eski yerdeki dosya bulunmaya devam ediyor.
- Canlıda **denenmedi**: dosyaların kopyalanması ve yeniden başlatma Deha'da. Kopyalandıktan sonra canlı `/api/hazir` `true` ve `4/4` demeli, Elektrik analizi kapalı yol bulmalı.
- Overpass'ın sunucudan neden yanıt vermediği ölçülmedi (sunucuya erişimimiz yok).

---

## J-185 🟠 Tatbikat: canlıda koşmuyordu; sonuç paneli okunmuyor ve etkileşimsizdi, harita çizgileri üst üste biniyordu, iki yanlış değer
**Durum:** KAPALI (24 Kasım 2026; canlı tarafı J-184'teki dosya kurulumuna bağlı) · **Bulundu:** 24 Kasım 2026 (kullanıcı ekran görüntüsü, Defne / Elektrik: "çok karmaşık çizgiler, sağ ekran aşağı uzayan okunaksız, etkileşimsiz; canlıda çalışmıyor") · **İlgili:** J-184, J-95, J-108, J-62

**Bulgu.**
- **Canlı.** Tatbikatın üç modeli (Hızlı = MiT-B0, Dengeli = MiT-B2, U-Net MiT-B4) ve yol ağının dayandığı `roads.gpkg` sunucuda yok (J-184). Ekran ağırlığı olmayan modelle de "başlat"a izin veriyordu.
- **Yanlış değer 1.** Her görevde ekip üssü "gerçek tesis" yazıyordu (`tatbikat.py`'de sabit `True`). Oysa bu ekiplerin başlangıcı OSM'deki mahalle giriş ağzı (`ekipler[].gercekTesis: false`).
- **Yanlış değer 2.** Kapanma kuralı "yalnız yolun üstündeki hasar kapatır" (r_h = 0) iken panel "Kapanma yarıçapı 0 m; hasar noktasına bu kadar yakın kenar kapalı sayıldı" yazıyordu.
- **Harita.** 5 görev × 3 planlanan rota + sürülen yollar + kapalı ve cezalı kenarlar aynı anda açıktı: 20'ye yakın çizgi üst üste. Gösterge 11 satırdı ve kapalı çizgileri de listeliyordu.
- **Görev seçme yok.** Sürülen yollar görev bilgisi taşımıyordu (ulaşılamayan görev listeden düşüyordu); bir görev seçilip yalnız o gösterilemezdi.
- **Sağ panel.** Dokuz bölüm alt alta diziliyordu (kaynak, hasar, kapanma, kamera, metin, arama, süreler, ölçüm, kollar, görevler). Tatbikatın cevabı ("kapanmayı bilmek ne kazandırdı") en altta "Kıyas kolları"nda kalıyordu; hiçbir satır tıklanmıyordu.

**Yapılan.**
- **Backend.**
  - `kiyas_kollari` görev başına her kolun sonucunu döner (`gorevKollari`: süre, mesafe, çıkmaz, U dönüşü, sürülen yol).
  - Görevin `gercekTesis` alanı ekibin kaydından gelir.
- **Sağ panel** soruya göre dört bölüm:
  1. Sonuç: "kapanmaları önceden bilen ekip ortalama X daha erken ulaştı (%Y)", bilmeyen ekibin çıkmaz ve U dönüşü sayısı, üç kolun süre çubukları, modelin doğruluğunu ölçmediği notu.
  2. Görevler: tıklanır; seçilen görevde harita yalnız o çifti çizer ve oraya yaklaşır. Satırda QuakeMind ve bilmeyen ekip süresi ile çıkmaz sayısı, açılınca mesafeler ve ekibin türü. "Tümünü göster" seçimi kaldırır.
  3. Bulgular: dört kutu (hasar, kapalı yol, kamera, metin); kutu katmanı açıp kapatır. Kapanma kuralı doğru cümleyle.
  4. Ayrıntılar katlanır (kapalı başlar): kamera tespitleri, metin ihbarları, görüntü ve model, ölçüm ve süreler.
- **Harita.**
  - Varsayılan iki çizgi: QuakeMind güzergâhı ve bilmeyen ekibin sürdüğü yol. "Kapanma olmasaydı" ve "Enkazdan uzak" sol panelde "Haritada göster" altından açılır.
  - Etiketler kısa ("Ekip 4", "Afetzede 1").
  - Gösterge yalnız açık çizgileri listeler.
- **Sol panel.** "Fiilen sürülen yol" bölümü kaldırıldı (sağa taşındı). Ağırlığı kurulu olmayan modelle başlatma kapalı ve nedeni yazıyor.

**Doğrulama.**
- Yerelde Defne / Elektrik, Dengeli model, 5 ekip, 5 afetzede, tohum 42: koşu 23 sn.
- Panel: "40 sn daha erken (%33)"; bilmeyen ekip 2,0 dk, telsizle paylaşan filo 1,7 dk, QuakeMind 1,3 dk; 10 çıkmaz, 2 U dönüşü.
- Ekip 1'i seçince harita yalnız o çifte yaklaştı: bilmeyen 3,5 dk, 1 çıkmaz; QuakeMind 1,9 dk.
- Hasar kutusu katmanı kapatıp açtı (`aria-pressed`).
- Ham yanıtta `gorevKollari` 3 kol × 5 görev, `gercekTesis` hepsi `false` (ekip kayıtlarıyla aynı).
- `pytest -q` 168/168, `tsc` ve `kontrol:token` temiz.
- Canlıda denenmedi; dosyalar kurulunca canlıda da koşmalı.

---

## J-186 🔴 Tatbikatı kapatmanın görünür yolu yoktu; sunucu yeniden başlayınca tatbikat noktaları gerçek veriye karışıyordu
**Durum:** KAPALI (24 Kasım 2026) · **Bulundu:** 24 Kasım 2026 (kullanıcı: "bu simülasyonu kapatacak bir mekanizmamız yok") · **İlgili:** J-185, J-74, J-104, CLAUDE.md kural 1

**Bulgu.**
- "Tatbikatı bitir" düğmesi yalnız tatbikat panelinin dibindeydi; ancak sol panel kaydırılınca görünüyordu. Bütün modlarda duran sarı TATBİKAT şeridinde yalnız "Tatbikat paneli" bağlantısı vardı. Başka moddaki kullanıcı tatbikatı kapatmanın yolunu bulamıyordu.
- Tatbikat koşuları yalnız API sürecinin belleğinde yaşıyor. Süreç yeniden başlayınca (her dağıtım dahil) `/api/simulasyon/bitir` 404 veriyordu. Panel hata durumunda da ekranı temizliyordu; böylece tatbikat "bitti" görünüyor ama koşunun veritabanına yazdığı hasar noktaları gerçek olay verisinin içinde kalıyordu.
- Kopya veritabanında API açılışında **296 sahipsiz tatbikat hasar noktası** bulundu [Ö]; ısı haritası ve genel durum bunları gerçek veri gibi sayıyordu.
- Bitirince sol panelde "Koşu %0 · Tatbikat bitirildi" artığı kalıyordu.
- İstemcinin gönderdiği kimlik doğrudan `LIKE` kalıbına giriyordu.

**Yapılan.**
- TATBİKAT şeridinde (her modda) "Tatbikatı bitir": tek satırda onay ("Bitirilsin mi? Koşunun hasar noktaları silinir." · Evet, bitir · Vazgeç). Yalnız tatbikatı yönetebilen rollere görünür; uyarının kendisi yine susturulamaz.
- `/api/simulasyon/bitir`: sunucu koşuyu tanımasa da (yeniden başlatma) o koşunun noktalarını siler. Kimlik `sim_` + onaltılık biçiminde olmalı, yoksa 422.
- API açılışında sahipsiz bütün tatbikat noktaları silinir (`depo.hasar_sil_tatbikat_hepsi`); tatbikat verisi onu üreten süreçten uzun yaşamaz.
- Panel bitirme hata verirse ekranı temizlemez ve hatayı yazar.
- Bitince ilerleme artığı görünmez.

**Doğrulama.**
- `tests/test_tatbikat_bitir.py` 3 test: tanınmayan koşunun noktaları silinir, gerçek analiz noktası kalır; geçersiz kimlikler (`%`, `sim_%`, boş) 422 alır ve hiçbir şey silinmez; açılış temizliği yalnız tatbikat noktalarını siler.
- `pytest -q` 171/171.
- Tarayıcıda Defne tatbikatı koşturuldu, SOS moduna geçildi, şeritten bitirildi: şerit kalktı, koşunun 15 noktası silindi (15 → 0).
- Açılış günlüğü: "Önceki süreçten kalan 296 tatbikat hasar noktası silindi".
- `tsc` ve `kontrol:token` temiz.

---

## J-187 🟠 Üç uydu modeli ve yerel OSM kesiti hiçbir yerden indirilemiyordu; sunucuya elle kopyalamak gerekiyordu
**Durum:** KAPALI (24 Kasım 2026) · **Bulundu:** 24 Kasım 2026 (J-184'ün kalıcı çözümü; kullanıcı: "Hugging Face'e benim hesabımla yükle") · **İlgili:** J-184, J-185, J-36

**Bulgu.**
- MiT-B0, MiT-B2 ve U-Net MiT-B4 ağırlıklarının künyesinde indirme kaynağı yoktu; dosyalar yalnız geliştirici makinesindeydi.
- `roads.gpkg` ve `tesisler.gpkg` de yalnız yerelde üretilmişti (`araclar_yerel_osm_kur.py`).
- Yeni kurulan ya da sıfırlanan bir sunucuda bunlar ancak elle kopyalanabiliyordu.

**Yapılan.**
- Ağırlıklar `Furkei/quakemind-uydu-modelleri` deposuna yüklendi (herkese açık; lisans: projenin `LICENSE`'ı, tüm hakları saklı; kartta sınama ve dış küme ölçümleri). Sürüm `0230b29`.
- OSM kesiti `Furkei/quakemind-osm-yollar` veri kümesine yüklendi (ODbL, "© OpenStreetMap katkıcıları"). Sürüm `0d4df25`.
- Üç künyeye `hf` kaynağı ve sabit sürüm (`surum`) yazıldı. `agirligi_hazirla` sürümü kullanır: depoya aynı adla başka dosya yüklense de sabit commit iner.
- `araclar_osm_indir.py`: kesiti kalıcı veri dizinine indirir. Dosya varsa ve parmak izi tutuyorsa atlar; tutmazsa kurmaz.
- `deploy.sh` bu aracı ve künyesinde kaynak olan bütün modelleri hazırlar. `deploy/README.md` tablo ve elle kurulum yedeğiyle güncellendi.
- Not: etkin model `Utbird` deposunda MIT lisansıyla duruyor; depodaki `LICENSE` ise "tüm hakları saklı". Bu çelişki ekibe bildirildi, karar ekibin.

**Doğrulama.**
- Yükleme öncesi yerel dosyaların SHA-256'sı künyelerle tuttu.
- Yükleme sonrası beş dosya anahtarsız (sunucunun yapacağı gibi) boş klasöre indirildi; beşinin de parmak izi tuttu.
- `araclar_osm_indir.py` gerçek depodan indirdi, ikinci çalıştırmada atladı.
- `agirligi_hazirla` MiT-B0'ı künyedeki sürümle indirdi, parmak izi tuttu.
- `tests/test_osm_indir.py` 2 test (sahte indirici: indirme, atlama, bozuk dosya kurulmaz).

---
