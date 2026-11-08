# Simülasyon Güncellemesi — Devir Belgesi

**Hazırlandığı tarih:** 15 Eylül 2026
**Kime:** Simülasyon güncellemesinin yapılacağı ayrı sohbete
**Neden var:** Makale çalışması bu sohbette sürüyor; simülasyon güncellemesi ayrı
bir sohbette yapılacak. Bu belge, o sohbetin sıfırdan başlamaması içindir.

> **Dikkat.** 12–15 Eylül arasında `makale` dalı bu sohbetten habersiz iki commit
> ilerledi ve bu sohbet üç gün boyunca eski duruma göre konuştu — 48 kapanmış
> maddeyi "açık" sandı. Aynı hata tekrar etmesin: **iş bitince bu belgenin
> "Geri dönüşte" bölümündeki bilgiler bu sohbete aktarılmalıdır.**

---

## 1. Depo durumu (15 Eylül 2026)

| | Durum |
|---|---|
| Ana çalışma ağacı | `Desktop\2209-A Afet\QuakeMind_Proje_Repo` — dal `main` |
| Makale çalışma ağacı | `Desktop\2209-A Afet\QuakeMind_makale` — dal `makale`, commit `55a50d1` |
| `origin` | `github.com/Femrei/QuakeMindDev` — `main` ile birebir aynı |
| `upstream` | `github.com/UtBird/QuakeMind` — yerel `main` 15 commit ileride |
| **Gönderim** | **Kullanıcı şu an push istemiyor.** Yerelde çalışılacak. |

Simülasyon kodu `main` dalındaki çalışma ağacındadır; makale `makale` dalındadır.
İkisi **ayrı klasörlerdir**, karıştırılmamalıdır.

---

## 2. Simülasyon nedir, nasıl çalışır

Senaryo v2, dokuz ilçe bölgesinde 18 afetzede / 18 ekip / 12 karargâh üzerinde
uçtan uca koşan bir değerlendirmedir.

### Giriş noktası

```bash
python backend/benchmark/full_scenario.py all --seed 42
```

Argümanlar: `city` (`hatay` · `kahramanmaras` · `all`), `--run-id`, `--seed`
(varsayılan **42**), `--speed` (zaman hızlandırma), `--closure-ratio`
(varsayılan **0,18**).

**Önkoşul:** Backend ayakta olmalı (`API_BASE`). Senaryo HTTP üzerinden gerçek
uç noktaları çağırır — sahte bir iç simülasyon değildir.

### Dosya haritası

| Dosya | Görevi |
|---|---|
| `benchmark/full_scenario.py` | Orkestratör. Bölge döngüsü, kanallar, atama, karşılaştırma, raporlama. |
| `benchmark/scenario_dataset.py` | **Tek doğruluk kaynağı.** Bölge, karargâh, ekip, afetzede tanımları. Hiç hesap yapmaz. |
| `benchmark/naive_baseline.py` | Naif ajan süre hesabı; `AVERAGE_SPEED_KMH`, `U_TURN_PENALTY_MIN`. |
| `benchmark/pipeline_runner.py` | `RunLogger`, `DURUM_PRIORITY`, `_haversine_m`, API tabanı. |
| `benchmark/scenario_v2_report.py` | Koşum çıktısından rapor üretir. |
| `benchmark/warm_scenario_v2_cache.py` | Çizgeleri PBF'ten önceden ısıtır (koşumdan önce çalıştırılır). |
| `apps/road_damage/utils/network.py` | `simulate_random_closures` — sentetik kapanma üreticisi. `simulate_naive_agent` — R0 referansı. |
| `fastapi_app.py` | `/api/road_damage/simulate_closures`, `/route`, `/naive_compare`, `/api/team/claim`. |

### Bölge başına akış (`run_zone`)

1. `POST /api/road_damage/simulate_closures` → çizge + kapalı/açık kenarlar + `analysisId`
2. Karargâhlar çizge sınırlarına çekilir (`_clamp_into_bounds`)
3. Afetzede konumları örneklenir — **kapanma uygulanmış gerçek çizge üzerinde
   ulaşılabilirlik sınanarak** (`_sample_reachable_point`)
4. Kanallar koşar: YOLOv8 (moloz görüntüsü), BERTurk (Türkçe ihbar metni), SOS
5. `assign_zone` → rol-farkında atama + `POST /api/team/claim` kilidi + çakışma testi
6. Gerçek güzergâh hesabı + `naive_compare` (R0)

---

## 3. Ölçülmüş parametreler — **makalede eksik olanlar dahil**

| Parametre | Değer | Nerede | Makalede var mı |
|---|---|---|---|
| **Ortalama hız `v_ort`** | **15,0 km/sa** | `naive_baseline.py:48` | ❌ **YOK — M-22** |
| U-dönüşü cezası `t_u` | 20,0 dk | `naive_baseline.py:61` | ✓ var |
| Naif ajan en çok yineleme | 60 | `naive_baseline.py:49` | ✓ var (I_max) |
| İstenen kapanma oranı ρ₀ | 0,18 | `full_scenario.py:54` | ✓ (3.8.1'e yazıldı) |
| Rastgelelik tohumu | 42 | `full_scenario.py:731` | ✓ (3.8.1'e yazıldı) |
| Bölge yarıçapı | 3,0 km | `scenario_dataset.py` | ✓ var |
| Bağlantılılık tabanı α | 0,92 | `network.py:367` | ✓ (3.8.1'e yazıldı) |
| Sert kapatma yarıçapı `r_h` | 25 m | `fastapi_app.py` | ✓ var |

> **`v_ort = 15,0 km/sa`**, "afet sonrası molozlu sokakta ortalama saha ilerleme
> hızı varsayımı" olarak kodda yorumlanmıştır. Makalede hiçbir yerde
> geçmemektedir; 206,6 dk ve 1 641,0 dk değerlerinin tamamı bu sayıdan
> türetilmektedir. Bu bir **ölçüm değil varsayımdır** ve makalede öyle
> sunulmalıdır.

---

## 4. Atama kuralı — koddan çıkarılmış tam hâli (M-05)

`full_scenario.py → assign_zone` (satır 360) ve `_priority_key` (satır 356).

**Adım 1 — sıralama.** Afetzedeler şu anahtara göre sıralanır:

```
_priority_key(v) = ( DURUM_PRIORITY[v.durum] , 0 if v.channel == "sos" else 1 )
DURUM_PRIORITY = { kritik: 0, mahsur: 1, yaralı: 2, hafif: 3 }
```

Yani önce durum ağırlığı, eşitlikte **SOS kanalından gelen ihbar önce**.

**Adım 2 — rol seçimi.** Her afetzede için hedeflenen ekip rolü:

| Afetzede durumu | Seçilen rol |
|---|---|
| `kritik` veya `mahsur` | Profilin `preferredRole`'u (hayat kurtarma önceliği) |
| Diğerleri | NLP'nin çıkardığı `derivedRole`, yoksa `preferredRole` |

Gerekçe koddaki yorumda: NLP kategorisi **ihtiyaç tipini** anlatır, vakanın
**hayati aciliyetini** değil. *"Bina yan yattı, içeride 3 kişi var, hilti ve
jeneratör lazım"* metnini model doğru biçimde lojistik/ekipman sayar — ama oraya
gitmesi gereken ekip arama-kurtarmadır.

**Adım 3 — ekip seçimi.**

```
havuz = [uygun rolde boşta ekipler]  ya da boşsa  [tüm boşta ekipler]
ekip  = havuzda afetzedeye haversine mesafesi EN KÜÇÜK olan
```

**Adım 4 — kilit.** `POST /api/team/claim`. Ekip havuzdan çıkarılır — yani
**her ekip en çok bir hedef alır**, yeniden atama yoktur.

**Adım 5 — çakışma testi.** İkinci bir ekip bilinçli olarak aynı hedefi almaya
çalışır; beklenen yanıt **HTTP 409**. Bu, "mükerrer sevk engellendi" iddiasının
ölçülmüş kanıtıdır.

> **Makale için kritik not.** Naif referans R0 **aynı atamayı** kullanır; yalnızca
> güzergâh hesabı farklıdır. Yani karşılaştırma atama kuralı bakımından adildir ve
> bu, makalede açıkça yazılmalıdır. Kazanç atama zekâsından değil, kapanma
> farkındalığından gelmektedir.

---

## 5. Süre ve karşılaştırma formülü

`compute_comparison` (satır 523):

```
bizim_süre  = mesafe_m / 1000 / 15,0 * 60                      [dk]
naif_süre   = naif_mesafe_m / 1000 / 15,0 * 60 + keşif × 20,0  [dk]
kazanç      = naif_süre − bizim_süre
```

Toplamlarda bir asimetri vardır ve makalede zaten kaydedilmiştir:
`totalOurEngineTimeMin` **tüm** atamaları toplar, `totalNaiveTimeMinReachableOnly`
yalnızca naif ajanın ulaşabildiklerini toplar.

---

## 6. Şu anki koşumun sonuçları (makalede raporlanan)

Koşumlar: `runs/canli-gosterim-hatay` ve `runs/canli-gosterim-kahramanmaras`,
tohum 42, ρ₀ = 0,18.

| | Hatay | Kahramanmaraş | Toplam |
|---|---|---|---|
| Bölge | 5 | 4 | 9 |
| Atama | 9 | 9 | 18 |
| Bizim motor | 98,5 dk | 108,1 dk | **206,6 dk** |
| Naif (ulaşabilenler) | — | — | **1 641,0 dk** |
| Engellenen U-dönüşü | — | — | 68 |
| Naifin ulaşamadığı | — | — | 0 |

Üretilen kapanmalar (etkin oran, istenen %18 değil):

| Bölge | Toplam kenar | Kapalı | Etkin oran | Yarılama |
|---|---|---|---|---|
| H-Z1 Antakya–Defne | 40 950 | 920 | %2,25 | 3 |
| H-Z2 İskenderun | 26 376 | 1 186 | %4,50 | 2 |
| H-Z3 Kırıkhan | 18 916 | 212 | %1,12 | 4 |
| H-Z4 Samandağ | 27 250 | 612 | %2,25 | 3 |
| H-Z5 Belen | 18 484 | 102 | %0,55 | 5 |
| K-Z1 Merkez | 49 666 | 2 234 | %4,50 | 2 |
| K-Z2 Elbistan | 19 490 | 876 | %4,49 | 2 |
| K-Z3 Pazarcık | 8 064 | 90 | %1,12 | 4 |
| K-Z4 Göksun | 13 102 | 146 | %1,11 | 4 |
| **Toplam** | **222 298** | **6 378** | **%2,87** | — |

Karşılaştırma için EMSR648 yer gerçeği: Hatay %1,58 · Kahramanmaraş %1,71.

---

## 7. Açık senaryo maddeleri

| Kimlik | Konu | Not |
|---|---|---|
| **E-01 / M-23** 🔴 | Kapanma katmanı EMSR648'e bağlanmadı | Veri **hazır**: `benchmark/data/copernicus/` altında paketler indirilmiş, `*_copernicus_ground_truth.json` üretilmiş. Bağlanmayı bekliyor. Karar gerekiyor: derece → geçilebilirlik kuralı. |
| **M-20** 🔴 | Görev tabanlı değerlendirme (Tablo 18) | **Makalenin merkezî katkı iddiası.** M-23'e bağlı. |
| **M-25** 🟠 | R1 (görüş mesafeli ajan) ve R2 (bilgi paylaşan filo) | Tanımlı, koşulmamış. R0 tek başına "straw man" okunuyor. |
| **M-26** 🟠 | Tablo 19 operasyonel sütunlar | Üç geçilebilirlik kuralı için senaryoyu üç kez koşmak gerek. |
| **E-06** 🟡 | Tek tohum, 18 afetzede | Çoklu tohum protokolü tanımlı, koşulmamış. Öneri: 10 tohum, ortalama ± ss. |
| **M-27** 🟡 | Bileşen çıkarma / parametre duyarlılığı (Tablo 20) | `r_h`, λ(d) basamakları, morfoloji seviyesi öncelikli. |
| **E-02** 🟠 | `t_u = 20 dk` varsayım | Kazancın %94,8'i bundan geliyor. Tablo 17'de tarama var — kısmen kapalı. |

---

## 8. Güncelleme yapılırsa makalede NE DEĞİŞİR

Bu liste, koşum yenilendiğinde elden geçirilmesi gereken yerlerdir:

| Makale yeri | Neden |
|---|---|
| Öz · Abstract | 206,6 / 1 641,0 / %87,4 sayıları |
| **Bölüm 3.8.1** (15 Eylül'de eklendi) | Kapanmalar artık sentetik değilse bölüm **yeniden konumlanır**: "bu sürümde sentetik kullanıldı" → "önceki sürümde sentetikti, bu sürümde EMSR648'e bağlandı" |
| Bölüm 4.5 · 4.6 | Tüm senaryo sonuçları |
| Tablo 16 (referans karşılaştırması) | R1/R2 eklenirse satırlar dolar |
| Tablo 17 (`t_u` taraması) | Taban sayılar değişir |
| Tablo 18 (görev tabanlı) | M-23 bağlanırsa doldurulabilir |
| Tablo 19 (geçilebilirlik duyarlılığı) | Üç kural koşulursa dolar |
| Şekil 10 · 11 · 12 | Senaryo verisinden üretiliyor |
| Bölüm 5.3 sınırlılıklar | "Kapanmalar sentetiktir" maddesi kalkabilir |

---

## 9. Ortam kısıtları

| | |
|---|---|
| Senaryo koşum makinesi | Kullanıcının kişisel bilgisayarı — Intel Core i7 14. nesil, 16 GB RAM, 512 GB SSD, Intel Iris Xe (tümleşik). **GPU hızlandırma yok.** |
| Model eğitimi | Google Colab, NVIDIA Tesla T4 |
| Çizge büyüklüğü | 3 km yarıçapta ~20 600 düğüm / ~49 700 kenar. Tüm ili tek grafa almak milyonlarca kenar demek — bu yüzden bölge mimarisi var. |
| Bellek uyarısı | `simulate_random_closures` içinde `nx.restricted_view` kullanılıyor; eskiden `G.copy()` vardı ve 6 denemede backend belleği tükeniyordu. **Kopya almaya geri dönülmemeli.** |
| Push | **Yapılmayacak.** Kullanıcı şu an gönderim istemiyor. |

---

## 10. Geri dönüşte bu sohbete getirilecekler

Simülasyon işi bitince makale sohbetine şunlar bildirilmelidir:

1. **Hangi commit'te kalındı** (`git log -1` çıktısı) ve hangi dalda
2. **Kod değişti mi** — değiştiyse hangi dosyalar, hangi davranış
3. **Yeni koşum sonuçları** — `runs/<run-id>/summary.json` yolu
4. Yeni **toplam süreler** (bizim / naif), U-dönüşü sayısı, ulaşılamayan hedef
5. Kapanma kaynağı **sentetik mi EMSR648 mi** oldu
6. `v_ort` ve `t_u` **değişti mi**
7. Hangi açık maddeler **kapandı** (E-01, E-06, M-20, M-23, M-25, M-26, M-27)

Bunlar `EKSIKLER_VE_SORUNLAR.md` ve
`QuakeMind_makale/makale/MAKALE_DUZELTME_LISTESI.md` dosyalarına işlenecektir.

## 11. ARA DURUM NOTU — 16 Eylül 2026 (simülasyon işi BİTMEDİ)

> Kullanıcı bu noktada makaleye dönüyor. Bölüm 10'un istediği yedi bilgi,
> **iş bitmemiş olsa da** aşağıda — makale sohbeti eski duruma göre konuşmasın.
> Ayrıntılar ve ölçümler: `EKSIKLER_VE_SORUNLAR.md`, **J bölümü** (J-01 … J-24).

| # | Soru | Cevap |
|---|---|---|
| 1 | Hangi commit / dal | `main`, **`32d45a3`** — bu oturumda **commit yapılmadı** (push yok kararı sürüyor). Değişiklikler çalışma ağacında. |
| 2 | Kod değişti mi | **Evet** — ayrıntı aşağıda. Aynı dosyalarda bu oturumdan önce de commit edilmemiş değişiklikler vardı; `git diff` ikisini birlikte gösterir. |
| 3 | Yeni koşum sonucu | **YOK.** Senaryo yeniden koşulmadı; `summary.json` değişmedi. |
| 4 | Yeni toplamlar | **Değişmedi:** 206,6 dk / 1 641,0 dk / 68 U-dönüşü / 0 ulaşılamayan hâlâ geçerli. |
| 5 | Kapanma kaynağı | **Hâlâ sentetik** (`full_scenario.py:582` → `/simulate_closures` → `rng.sample`). Model tabanlı yol artık kapanma üretebiliyor (J-19) ama senaryoya **bağlanmadı** (J-23). |
| 6 | `v_ort`, `t_u` değişti mi | **Hayır.** 15,0 km/sa ve 20,0 dk. |
| 7 | Kapanan açık maddeler | E-01, E-06, M-20, M-23, M-25, M-26, M-27: **hiçbiri kapanmadı.** E-01/M-23 için belirleyici yeni bilgi var (aşağıda). |

### Kod değişiklikleri (bu oturum)

**Performans — davranış değişmedi, hepsi eski/yeni karşılaştırmalı doğrulandı:**
J-01 `/recent` 1,27 MB → 264 bayt (+ ayrı `/segments/{id}` ucu) · J-02 naif ajan
`G.copy()` → `restricted_view` (18×, sonuç birebir) · J-03 geocoding önbelleği
(tekrar eden metin 7,28 → 0,55 sn) · J-04 kullanılmayan Zeyrek çağrısı (NLP import
60,8 → 20,6 sn) · J-05 `/route` yalnız A* (maliyet farkı 0) · J-06 önbellekli en
yakın düğüm (541×) · J-08 `apply_risk_penalties` vektörize (gerçek EMSR648
yüküyle 139 → 3,5 sn, bit düzeyinde aynı) · J-14 SegFormer HTTP sürecinden
çıkarıldı (−502 MB) · J-17 oturum deposuna süre aşımı + bellek bütçesi.

**Davranış değişikliği — J-19:** `/analyze` artık bir yolu, **yakınında (r_h)**
hasar varsa kapatıyor; eskiden hasarın yolun merkez çizgisi pikselinin tam üstünde
olması gerekiyordu (bu yüzden model hiç kapanma üretmiyordu). Varsayılan r_h = 25 m;
`blockageRadiusM` ile ayarlanır, `0` eski kurala döner. **Senaryo sayılarını
etkilemez** (senaryo bu ucu kullanmıyor).

### Makale için belirleyici yeni bulgular

1. **EMSR648 açık erişim** — public S3, kayıt/token yok (HTTP 200). Kaynak
   gösterimi sorunsuz. 20 AOI var; 3'ü daha indirildi (AOI08, AOI18, AOI20).
2. **Esri Wayback'te Antakya'nın deprem sonrası görüntüsü YOK** (J-21) —
   "2023-02-23" karosu deprem öncesiyle bayt bayt aynı. Deprem sonrası görüntü
   **Maxar Open Data**'da var (gözle doğrulandı). Makale deprem sonrası analizi
   Wayback ile yapılmış gibi anlatıyorsa **yanlıştır** (D-01 ile bağlantılı).
3. **Senaryo modele 3,86 m/px veriyor** (J-20) — Maxar'ın doğalı 0,3-0,5 m/px.
   z=18'de model **25 kat** daha fazla hasar buluyor. Ama CPU'da bu, 3 km'lik
   bölge başına saatler demek.
4. **r_h = 25 m gerçeğin ~8 katı kapanma üretiyor** (J-22) — aynı alanda model
   %25,7, EMSR648 %3,2. Makalede belgelenen r_h değeri kalibre edilmemiş.
   (Tek 389 kenarlık örneklem; kesin sonuç değil, uyarı.)
5. **Kapsama iki ayrı soru** (J-24): model tabanlı kapanma için Maxar görüntüsü
   **8/9** bölgede var (yalnız Göksun'da yok); EMSR648 doğrulaması **4/9**
   bölgede mümkün (Antakya, Kırıkhan, Maraş Merkez, Elbistan).

### Kalan iş (kritik yol) — tahmini 5-6 iş günü

| Sıra | İş | Madde | Süre | Engel |
|---|---|---|---|---|
| 1 | İşçi `G` + kapalı kenarları döndürsün; `/naive_compare` `/analyze` oturumlarında çalışsın; `full_scenario.py` `/analyze` + bölge başına Maxar sahnesi kullansın | J-23 | ~1 gün | — |
| 2 | Çözünürlük/hesap kararı ve kurulumu (Colab T4 GPU önerilir) | J-20 | ~1 gün + koşum | **Karar: GPU mu, küçük bölge mi** |
| 3 | r_h kalibrasyonu (4 EMSR bölgesi) | J-22 | ~1 gün + koşum | 2'ye bağlı |
| 4 | Göksun kararı (görüntü yok) | J-24 | yarım saat | **Karar: çıkar mı, sentetik+etiketli mi** |
| 5 | Senaryoyu yeniden koş → yeni `summary.json` | E-01 | yarım gün | 1-4'e bağlı |
| 6 | Model kapanmaları × EMSR648 → Tablo 18 | M-20 | ~1 gün | 5'e bağlı |
| 7 | Bu belgeyi ve takip dosyasını güncelle | — | yarım gün | — |

**Risk:** J-22'nin iki olası sebebi ayrıştırılmadı — r_h fazla büyük **veya**
model yanlış pozitif üretiyor (A-01: IoU_hasar 0,37-0,43). İkincisiyse
kalibrasyon yetmez; model kalitesi sorunu olur ve plan değişir.

## 12. EK — 16 Eylül 2026 öğleden sonra: Göksun çıkarıldı, drone sahneleri denendi

**Senaryo v2 değişti:** K-Z4 Göksun çıkarıldı (deprem sonrası hiç görüntü yok).
Afetzedesi KMS-06 ve ekibi MARAS-AK5 K-Z1'e taşındı (`relocatedFrom` ile
kayıtlı). Yeni sayılar: **8 bölge / 18 afetzede / 18 ekip / 11 karargâh**; il
başına 3/3/3 kanal dağılımı korundu. Makaledeki "9 bölge / 12 karargâh"
ifadeleri güncellenmeli. **Hatay sonuçları değişmedi** (regresyon birebir);
Kahramanmaraş sonuçları yeniden koşulunca değişecek.

**Model tabanlı kapanma altyapısı hazır:** `/closures_from_mask`,
`full_scenario.py --closure-source model`, Colab defteri
(`benchmark/colab/QuakeMind_model_masks.ipynb`). Senaryo v2'nin varsayılanı
hâlâ `synthetic`; her çıktı kaynağını `summary.json`'a yazıyor.

**Drone sahneleri denemesi** (kullanıcının modeli test ettiği üç yer, 3,4–3,9 cm/px):
- EMSR648'e karşı model: zoom arttıkça gerçek hasar tespiti artıyor ama yanlış
  alarm daha hızlı artıyor. Yol kararında en iyi dengeli doğruluk **%59,1**
  (z=19, r_h=15) — şansa yakın; model kapanmalarının ~%80'i EMSR'e göre açık yol.
- Model kapanmalarıyla drone simülasyonunda **9 atamadan yalnız 1'i**
  rotalanabildi (ağ parçalanıyor). Sentetik kapanmayla 9/9.
- Ayrıntı: `EKSIKLER_VE_SORUNLAR.md` **J-25, J-26, J-27**.

**Makale için anlamı:** model tabanlı kapanmanın bugünkü başarımı makalede
"sistem kazancı" iddiasını taşıyacak düzeyde değil. M-20 (Tablo 18) için gereken
doğrulama altyapısı ve ilk sayılar hazır; bu sayılar olumsuz, olduğu gibi
raporlanmalı ya da model iyileştirilmeli (kullanıcı kararı).

## 13. EK — 16 Eylül 2026 akşam: EMSR648 kapanma katmanı ve eşleştirilmiş deney

> Bu bölüm Bölüm 11'deki yedi maddelik tabloyu **geçersiz kılar**.

| # | Soru | Cevap |
|---|---|---|
| 1 | Hangi commit / dal | `main`, **`32d45a3`** — hâlâ **commit yok, push yok**. Tüm değişiklikler çalışma ağacında. |
| 2 | Kod değişti mi | **Evet.** Bölüm 11–12'dekilere ek: `network.py` → `closures_from_lines`; `fastapi_app.py` → `POST /api/road_damage/closures_from_emsr`; `copernicus_ground_truth.py` → derece kuralları (katı/orta/gevşek), yol çizgisi ve AOI okuma; `full_scenario.py` → `--closure-source emsr`, `--emsr-rule`, `--zones`; yeni `compare_closure_sources.py`. `scenario_dataset*.py` → HQ-K1 ve HQ-HD2 çıkmaz yoldan kavşağa taşındı. Uygulamanın `/analyze` varsayılanı **eski davranışta** (`blockageRadiusM = 0`). |
| 3 | Yeni koşum sonucu | **Var:** `backend/benchmark/runs/{v2-sentetik-8ilce, v2-sentetik-4ilce, v2-emsr-strict, v2-emsr-medium, v2-emsr-loose, drone-sentetik, drone-emsr-loose, drone-model-z18-r0, drone-model-z19-r15}-{hatay,kahramanmaras}/summary.json`; karşılaştırma `runs/closure_source_comparison.json`. Karargâh düzeltmesinden önceki koşular `runs/_superseded/2026-09-16-karargah-duzeltmesi-oncesi/`. |
| 4 | Yeni toplamlar | **8 ilçe, sentetik:** 222,2 / 1 744,8 dk, 73 U-dönüşü, 0 ulaşılamayan (eski 206,6 / 1 641,0 / 68 geçersiz). **4 ilçe, EMSR gevşek:** 189,5 / 2 006,7 dk, 87 U-dönüşü, 0 ulaşılamayan. Diğer satırlar aşağıda ve J-28'de. |
| 5 | Kapanma kaynağı | **Üçü de var ve koşuldu:** sentetik, **EMSR648** (4 ilçe: H-Z1, H-Z3, K-Z1, K-Z2) ve model (yalnız drone sahneleri). Makalenin ana sonucu için EMSR648 satırları önerilir. |
| 6 | `v_ort`, `t_u` değişti mi | **Hayır.** 15,0 km/sa ve 20,0 dk. |
| 7 | Kapanan açık maddeler | **J-12 kapandı** (kapsam dışı 4 ilçe için kısıt sürüyor); **E-01 kısmen kapandı** (4 ilçede bağlı). M-26 (Tablo 19) operasyonel sütunları artık J-28'deki üç kural koşusundan doldurulabilir. M-20/M-23 için model tabanlı kapanma **olumsuz** sonuç veriyor (J-25, J-26). E-06 (tek tohum), M-25 (R1/R2), M-27 açık. |

**Makale için en önemli değişiklik:** kapanmalar artık üç kaynaktan
üretilebiliyor ve **gerçek hasarla (EMSR648) koşulmuş sonuç var**:

| Senaryo v2, EMSR kapsamındaki 4 ilçe (13 afetzede) | QuakeMind | Klasik |
|---|---|---|
| Sentetik | 180,3 dk | 1 600,3 dk |
| **EMSR648, gevşek kural** | **189,5 dk** | **2 006,7 dk** |
| EMSR648, katı kural (yalnız Destroyed) | 177,6 dk | 238,0 dk |

- Kazancın **%96'sı** U-dönüşü ceza varsayımından (t_u = 20 dk) geliyor; gerçek
  yol farkından gelen kazanç **77,2 dk**. İkisi ayrı raporlanmalı (E-02).
- Geçilebilirlik kuralı sonucu belirliyor → Tablo 19 (M-26) artık doldurulabilir.
- **Senaryo v2 yeni sentetik taban (8 ilçe): 222,2 / 1 744,8 dk** — eski 206,6 /
  1 641,0 dk yerine. Hatay yarısı değişmedi.
- Model tabanlı kapanma bugün kazanç üretmiyor (J-25, J-26) → Tablo 18'de
  olumsuz sonuç olarak raporlanmalı ya da model iyileştirilmeli.
- Karargâh düzeltmesi: HQ-K1 ve HQ-HD2 çıkmaz yoldan ~40 m ötedeki kavşağa
  taşındı (veri setlerinde gerekçesiyle).

Ayrıntı ve tam tablolar: `EKSIKLER_VE_SORUNLAR.md` **J-12 (kapanış), J-28**.
Koşular: `backend/benchmark/runs/{v2-*, drone-*}`.

## 14. EK — 16 Eylül 2026 gece: çoklu tohum (10 tohum)

> Bu bölüm Bölüm 13'ün 3., 4. ve 7. satırlarını günceller; diğer satırlar geçerli.

| # | Soru | Cevap |
|---|---|---|
| 1 | Hangi commit / dal | `main`, **`32d45a3`** — hâlâ **commit yok, push yok**. |
| 2 | Kod değişti mi | Yalnız yeni betik: `backend/benchmark/multi_seed.py` (koşturucu + özet). Sistem kodu değişmedi. |
| 3 | Yeni koşum sonucu | `backend/benchmark/runs/multi_seed/` — 90 koşu (9 yapılandırma × tohum 42–51); tablo `multi_seed_tablo.md`, ham özet `multi_seed_summary.json`. Tohum 42, Bölüm 13'teki koşuları birebir yeniden üretti. |
| 4 | Yeni toplamlar (ortalama ± ss, 10 tohum) | **8 ilçe sentetik:** QuakeMind 203,5 ± 18,9 / klasik 1 552,0 ± 252,0 dk, U-dönüşü 64,7 ± 11,4, ulaşılamayan 0 (rotalanan 17,8 / 18). **4 ilçe EMSR gevşek:** 154,1 ± 23,3 / 1 433,0 ± 607,8 dk, U-dönüşü 61,4 ± 28,3, ulaşılamayan 0. Yalnız yol farkı: 54,5 ± 15,2 ve 50,9 ± 31,1 dk. Tam tablo: `EKSIKLER_VE_SORUNLAR.md` **J-29**. |
| 5 | Kapanma kaynağı | Değişmedi (sentetik, EMSR648, model — üçü de 10 tohumla koşuldu). |
| 6 | `v_ort`, `t_u` değişti mi | **Hayır** (15,0 km/sa, 20,0 dk). t_u = 0–30 dk duyarlılığı aynı koşulardan hesaplandı. |
| 7 | Kapanan açık maddeler | **E-06 kapandı.** Yeni: **J-29** (çoklu tohum bulguları), **J-30** (model koşuları algılama hatasını ölçmüyor → M-20 için tasarım önerisi). M-25 (R1/R2) daha da önemli hale geldi: kazancın çoğu tek bölgedeki birkaç görevden geliyor. |

**Makale için en önemli üç nokta:**
- Tek koşu (tohum 42) kazancı olduğundan yüksek gösteriyordu; ortalama ± ss kullanılmalı.
- Görev düzeyi Wilcoxon p değeri yapı gereği anlamlı (klasik ajanın yolu en kısa yoldan kısa
  olamaz) — kazanç kanıtı olarak sunulmamalı; büyüklük ve sıklık raporlanmalı.
- Model tabanlı kapanmanın kazancı için %95 GA sıfırı içeriyor; üstelik bu koşular
  algılama hatasını ölçmüyor (J-30).

## 15. EK — 16 Eylül 2026 gece: Tablo 18 deneyi (J-30) ve ara referanslar R1/R2 (M-25)

### 15.1 Tablo 18 — "modelle planla, gerçek (EMSR648) dünyada yürü" (J-30 kapandı)

Önceki model koşularında klasik ekip de modelin kapanmalarını gerçek sayıyordu; modelin
hataları ölçülmüyordu. Yeni deney `backend/benchmark/model_in_real_world.py`
(backend gerektirmez) dünyayı her zaman EMSR648 (gevşek, 8 m) kapanmaları yapar:
R3 bunları bilir, **model-bilgili QuakeMind** SegFormer'ın kapanmalarını bilir (yanlış alarmı
sorgulamaz, kaçırdığı kapanmayı sahada keşfeder), R0 hiçbir şey bilmez. 3 drone sahnesi ×
3 görev × 10 tohum; SegFormer 3 zoom × 5 r_h (sert) + aynı 15 ayar yumuşak ×3 / ×10.
Çıktı: `benchmark/runs/model_gercek_dunya/tablo18.md`.

| | Görev başına ulaşım süresi |
|---|---|
| R3 — kusursuz bilgi | **2,05 ± 0,15 dk** |
| R0 — naif | **6,52 ± 1,92 dk** |
| SegFormer, 15 sert ayar | 6,52 – 6,97 dk (R0→R3 kazancının **%0 ile %−11**'i) |
| SegFormer, 30 yumuşak ayar | 5,66 – 7,84 dk (tutarlı kazanç yok; 2 ayar %18 ± 23, diğerleri %+2 … %−26) |

- Küçük r_h'de model gerçek kapanmaları kaçırıyor (kesim duyarlılığı ≤ 0,13); büyük r_h'de
  duyarlılık 0,92'ye çıkıyor ama kesinlik ~0,10 → yanlış alarmlar 9 görevin 9'unda hedefi
  ağdan koparıyor, ekip modeli bırakıp R0 gibi gidiyor.
- **Tablo 18'in SegFormer satırı olumsuz sonuç**; Bölüm 4.7'deki "duyarlılık kesinlikten
  belirleyici" hipotezi bu düzende desteklenmiyor (makalenin öngördüğü alternatif —
  kapanmaların ağdaki konumu — veriyle uyumlu).
- IoU/duyarlılık/kesinlik **kesim düzeyinde** (piksel IoU_hasar değil); yalnız SegFormer
  var; gerçek yol hasarı yalnız K-D1 sahnesinde (H-D1/H-D2'de EMSR hasar işaretlememiş).
- Doğrulama: R0 90/90 birebir, R3 mesafesi = A* (0,00 m fark), kapanma sayıları önceki
  koşularla aynı. Ayrıntı: `EKSIKLER_VE_SORUNLAR.md` **J-30**.

### 15.2 Ara referanslar R1 / R2 (Tablo 16, M-25)

R1 (yol boyunca 100 m görüş, aynı kavşaktaki gözlemler tek ceza) ve R2 (bölge içi filo, keşif
o anda telsizle herkese; telsizle öğrenilen kapanma cezasız; kafilede öndeki keşfeder) aynı
oturum ve aynı atamalarla, 10 tohumla koşuldu. Tablo: `backend/benchmark/runs/
multi_seed_refs/multi_seed_tablo.md`; ayrıntı ve yorum: `EKSIKLER_VE_SORUNLAR.md` **J-31**.

| t_u = 20 dk, 10 tohum | 8 ilçe sentetik (dk) | kazanç | EMSR648 gevşek (dk) | kazanç |
|---|---|---|---|---|
| QuakeMind (R3) | 203,5 ± 18,9 | — | 154,1 ± 23,3 | — |
| R0 | 1 552,0 ± 252,0 | %86,7 | 1 433,0 ± 607,8 | %86,8 |
| **R1** | **1 357,1 ± 185,2** | **%84,9** | **942,4 ± 340,5** | **%81,6** |
| **R2** | **1 409,5 ± 251,0** | **%85,3** | **1 062,6 ± 297,5** | **%84,1** |
| R1 + R2 (ek) | 1 264,1 ± 203,2 | %83,7 | 763,8 ± 175,0 | %78,7 |

- Güçlü referanslara karşı kazancın %55–90'ı kalıyor; yalnız yol farkı en güçlü referansa
  karşı %14 (sentetik) / %17 (EMSR) — büyüklük hâlâ t_u'dan.
- R1'in R0'a üstünlüğünün EMSR'de yarısından fazlası (272 / 491 dk) sayım kuralından.
- Bilgi paylaşımı bazen süreyi uzatıyor (R2 sentetikte 10 tohumun 1'inde R0'dan yavaş).
- Doğrulama: R0 986/986 görev birebir, taban J-29 taramasıyla 90/90 koşu aynı.

### 15.3 Bölüm 10'un yedi maddesi (Bölüm 14'ü günceller)

| # | Soru | Cevap |
|---|---|---|
| 1 | Hangi commit / dal | **`simulasyon-gercek-veri`** dalı (`main` = `32d45a3` üstünde; `main` değişmedi). **GitHub'a gönderildi:** `origin` (Femrei/QuakeMindDev) üzerinde aynı adlı dal; takım deposuna (`upstream`, UtBird/QuakeMind) gönderilmedi, PR açılmadı. Makale dosyaları (kökteki `MAKALE_*`, `PROJE_DOSYASI.md`) ve eski `benchmark/reports/senaryo_v2_raporu.*` bilinçli olarak commit dışında; ham koşu klasörleri `.gitignore`'da, özet tablolar izleniyor. |
| 2 | Kod değişti mi | **Evet.** `network.py`: `simulate_reference_fleet` (R0/R1/R2, başlangıç bilgisi, yumuşak ceza) ve `_shortest_path_avoiding`; `simulate_naive_agent` **değişmedi**. `fastapi_app.py`: `POST /api/road_damage/reference_compare`. `full_scenario.py`: `--references` (varsayılan kapalı). `multi_seed.py`: `--references`, `--out`, `--compare-with`. Yeni: `model_in_real_world.py`. |
| 3 | Yeni koşum sonucu | `runs/multi_seed_refs/` (R1/R2, 90 koşu) ve `runs/model_gercek_dunya/` (Tablo 18). |
| 4 | Yeni toplamlar | QuakeMind/R0 toplamları Bölüm 14 ile aynı; R1/R2 yukarıda. Tablo 18: görev başına R3 2,05 / R0 6,52 dk, SegFormer 6,52–6,97 dk. |
| 5 | Kapanma kaynağı | Değişmedi (sentetik, EMSR648, model). Tablo 18'de dünya her zaman EMSR648. |
| 6 | `v_ort`, `t_u` değişti mi | **Hayır** (15,0 km/sa, 20,0 dk). |
| 7 | Kapanan açık maddeler | **J-30 kapandı** (Tablo 18 verisi). **M-25 verisi hazır** (J-31). M-20 için SegFormer satırı olumsuz sonuç. Açık: M-27, diğer beş segmentasyon modeli (Tablo 13/18 satırları). |

---

*İlgili belgeler: `MAKALE_KUNYE_BILGILERI.md` (künye ve kapsam kararları),
`EKSIKLER_VE_SORUNLAR.md` (proje geneli takip),
`QuakeMind_makale/makale/MAKALE_DUZELTME_LISTESI.md` (76 maddelik makale listesi)*
