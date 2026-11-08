# QuakeMind — Demo Senaryo Metni
### Kahramanmaraş (Ekmekçi) + Hatay (Elektrik / Armutlu)

Bu senaryo, [AKIS_DIYAGRAM_KOD_ESLESTIRME_RAPORU.md](AKIS_DIYAGRAM_KOD_ESLESTIRME_RAPORU.md) raporunda çıkarılan gerçek/kısmi/kurgusal ayrımına sadık kalınarak yazılmıştır. Konum ve hasar verisi **gerçek** (6 Şubat 2023 Kahramanmaraş depremi, Copernicus EMSR648 hasar tespiti, gerçek AFAD toplanma alanları); ekip/afetzede kimlikleri ve olay örgüsü bu senaryo için **kurgulanmıştır**; rota mesafeleri mümkün olan yerde `backend/benchmark/` altındaki **gerçek, tekrarlanabilir sistem çıktılarından** alınmıştır (kaynak run-id'leriyle işaretli), kalanı gerçek koordinatlar arası **kuş uçuşu mesafe** olarak hesaplanmıştır (bu da gerçek matematik, sadece henüz yol ağı üzerinden rotalanmamış).

Anlatı çerçevesi: bugünkü tarihte (12 Ağustos), Kahramanmaraş ve Hatay için düzenlenen bir **tatbikat/demo senaryosu** — 6 Şubat 2023'te gerçekten hasar görmüş EKMEKÇİ (Kahramanmaraş) ve ELEKTRİK/ARMUTLU (Hatay/Defne) mahallelerinin gerçek koordinatları ve gerçek hasar haritası üzerine kurulu.

---

## 1) Sahne — T+0'dan itibaren zaman çizelgesi

| Zaman | Olay | Diyagram Adımı | Sistemdeki Karşılığı |
|---|---|---|---|
| T+0 | Deprem. Ekipler saha konuşlanmasında, afetzedeler telefonlarını çıkarıyor. | 🏚️ DEPREM MEYDANA GELDİ | — |
| T+1dk | İlk afetzede QuakeMind'ı açıyor, rolünü seçiyor (Afetzede). | Uygulamayı Aç | `screens/splash_screen.dart` → `AuthController` |
| T+2dk | Komuta merkezinde operatör `/command` sayfasını açıp **SİMÜLASYON MODU**'nu aktive ediyor. | Bölüm 00 — Başlangıç & Kimlik | `command/page.tsx`, 2.5sn polling başlar |
| T+3dk | Operatör önce `/command/road-damage` → Ekmekçi (Kahramanmaraş) için gerçek SegFormer uydu analizini başlatıyor. | ⚙️ Uydu tiles → SegFormer → Enkaz Isı Haritası | `POST /api/road_damage/analyze` (async job, ilerleme % ile) |
| T+3dk | Aynı ekranda **Toplanma Alanları** sekmesinden Ekmekçi ve Elektrik/Armutlu için toplanma alanı araması yapılıyor — bu adım **`/command/map`'te Toplanma Alanları katmanının dolması için şart** (otomatik gelmiyor). | 🏥 Hastane & toplanma | `GET /api/road_damage/assembly` → `setAssemblyAreas()` |
| T+5dk | İlk SOS: Armutlu'da enkaz altında kalan bir afetzede büyük kırmızı SOS butonuna basıyor. | 🚨 SOS BUTONU BASILDI | `sos_page.dart` → `POST /api/sos/alert` |
| T+6-15dk | Sırayla 20 afetzede bildirimi geliyor (10 Kahramanmaraş + 10 Hatay) — bir kısmı SOS, bir kısmı yazılı metin (NLP), bir kısmı kamera ile enkaz/çatlak fotoğrafı. Her biri haritada tek tek beliriyor. | 🆘/📸/🛣️ üç paralel giriş kolu | `/api/sos/alert`, `/api/nlp/analyze`, `/api/camera/analyze` |
| T+16dk | Komuta merkezi operatörü `/command/sos` sayfasında gelen ihbarları görüyor, en kritik 5+5'i inceliyor. | 🗺️ Paylaşılan Canlı Operasyon Haritası | `command/sos/page.tsx` |
| T+17-30dk | Sırayla 5 ekip (Kahramanmaraş) + 5 ekip (Hatay), en yakın oldukları ihbara **"BEN GİDİYORUM"** diyerek claim atıyor. Her claim anında o ihbarın pin'i renk değiştiriyor, diğer ekiplerin ekranında "başka ekip müdahale ediyor" görünüyor. | Bölüm 03 — Görev Orkestrasyonu & Çakışma Önleme | `POST /api/team/claim` (409 = kilitli) |
| T+18-31dk | Her claim'in hemen ardından güvenli rota hesaplanıp ekibin claim'ine ekleniyor; ekip ikonu haritada rota boyunca ilerlemeye başlıyor (zaman-bazlı interpolasyon). | Bölüm 04 — GNN Navigasyon | `POST /api/road_damage/route` + `POST /api/team/claim/{id}/route` |
| T+35dk | İlk ekip hedefe ulaşıyor, görevi tamamlıyor. | Bölüm 05 — Kapanış Döngüsü | `POST /api/team/claim/{id}/release` → pin YEŞİLE döner |
| T+40dk | Kalan 5+5 "bekleyen" ihbar hâlâ haritada duruyor — bütün ekipler meşgul olduğu için henüz kimse claim etmemiş; operatör bunu `/command/sos` üzerinde "OPEN" filtresiyle görüyor. | "BOŞTA" durumu | `GET /api/sos/alerts`, `GET /api/team/claims` |

---

## 2) KAHRAMANMARAŞ — Ekmekçi Mahallesi

**Gerçek konum**: bbox 36.9175–36.9239 E / 37.5731–37.5782 N (9 Şubat 2023 tarihli gerçek OpenAerialMap görüntüsü, Help.NGO — "Şubat Stadyumu" görüntüsü). Hasar zemin verisi: Copernicus EMSR648_AOI04.

### 2.1 — 5 Ekip (gerçek hastane/itfaiye konumlarından)

| Ekip | Rol / Birim | Başlangıç Noktası | Koordinat |
|---|---|---|---|
| ekip-1 | Arama-Kurtarma / **AKUT Saha Ekibi** | Sütçü İmam Üniversitesi Tıp Fakültesi | 37.5879, 36.8261 |
| ekip-2 | Lojistik-İlk Yardım / **Kızılay Lojistik Ekibi** | Kadın Doğum ve Çocuk Hastalıkları Hastanesi | 37.5940, 36.8834 |
| ekip-3 | Arama-Kurtarma / **Jandarma Arama Kurtarma** | Yenişehir Devlet Hastanesi | 37.5781, 36.9315 |
| ekip-5 | Arama-Kurtarma / **İtfaiye Arama Kurtarma** | İtfaiye (mahalle merkezi) | 37.5891, 36.9423 |
| ekip-6 | Lojistik-İlk Yardım / **AFAD Lojistik Ekibi** | Hayat Hastanesi | 37.5776, 36.9288 |

### 2.2 — 5 AKTİF İhbar (ekip atanmış, harita pin'i kilitli/renkli)

| # | Kaynak | Durum | Konum | Metin | Atanan Ekip | Mesafe |
|---|---|---|---|---|---|---|
| A1 | 🚨 SOS | Mahsur | 37.5765, 36.9231 | *"Merdivenler çöktü, üst katta mahsuruz Ekmekçi'de"* | ekip-6 | **1.397 m / 5,6 dk** — gerçek sistem çıktısı ⭐ |
| A2 | 🚨 SOS | Mahsur | 37.5758, 36.9226 | *"Binada mahsur kaldık, kapı açılmıyor, çıkamıyoruz Ekmekçi'de"* | ekip-3 | **1.798 m / 7,2 dk** — gerçek sistem çıktısı ⭐ |
| A3 | 🚨 SOS | Kritik | 37.5792, 36.9215 | *"Ağır yaralı var burada, kan kaybediyor, acil ekip lazım Ekmekçi'de"* | ekip-5 | 2.133 m (kuş uçuşu) |
| A4 | 📸 Enkaz modeli (bina.pt, %81 güven) | — | 37.5744, 36.9237 | *(fotoğraf, metin yok — "yıkık bina" tespiti)* | ekip-2 | 4.168 m (kuş uçuşu) |
| A5 | 📝 NLP metni | Yaralı | 37.5732, 36.9195 | *"Yaşlı annem yaralı, yürüyemiyor, sağlık ekibi lazım Ekmekçi'de"* | ekip-1 | 8.399 m (kuş uçuşu) |

**⭐ Gerçek kanıt — "biz size söylemeseydik ulaşamazdınız":** A1 ve A2, `benchmark/runs/kahramanmaras-fixed3/naive_baseline_comparison.json` dosyasındaki **gerçek, tekrarlanabilir bir test koşusunun** birebir çıktısıdır. Bu test, `benchmark/naive_baseline.py` ile şunu simüle eder: kapalı yolları bilmeyen bir ekip en kısa yoldan gitmeye çalışırsa (hasarı ancak yolun üzerine geldiğinde fark eder) ne olur? Sonuç: **her iki hedef için de naive (sistemsiz) ajan hedefe HİÇ ULAŞAMIYOR** — mahalle ölçeğindeki yol grafiği gerçek hasarla o kadar parçalanmış ki, bilmeden giden bir ekip döngüye girip sıkışıyor. QuakeMind'ın hasar-farkında Dijkstra/A* motoru ise güvenli yolu buluyor ve ekip **5,6 dk ve 7,2 dk içinde hedefe ulaşıyor.** Bu, "ekibiniz kapalı yolda kalıp geri dönüp yeni yol arayacaktı" anlatısının uydurma değil, ölçülmüş bir örneği.

*(Not: A3-A5 için rota bu belgede henüz hesaplanmadı — gerçek sistemde ekip claim ettiği an `POST /api/road_damage/route` çağrılır ve gerçek güvenli mesafe/dakika o an üretilir; demo sırasında canlı gösterilebilir.)*

### 2.3 — 5 BEKLEYEN İhbar (ekip yok, henüz açık)

| # | Kaynak | Durum | Konum | Metin |
|---|---|---|---|---|
| B1 | 📝 NLP | Yaralı | 37.5787, 36.9243 | *"Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var Ekmekçi'de"* |
| B2 | 🚨 SOS | Yaralı | 37.5787, 36.9220 | *"Yaralılar var evde, ambulans gelemedi henüz Ekmekçi'de"* |
| B3 | 📝 NLP | Hafif | 37.5767, 36.9241 | *"Suyumuz bitti, temiz suya ihtiyacımız var Ekmekçi'de"* |
| B4 | 📝 NLP | Hafif | 37.5772, 36.9224 | *"Yiyecek sıkıntısı var, birkaç gündür erzak gelmedi Ekmekçi'de"* |
| B5 | 📸 Çatlak modeli (catlak.pt, %64 güven) | — | 37.5779, 36.9206 | *(fotoğraf, metin yok — "orta seviye yapısal çatlak" tespiti)* |

Beş ekip de A1-A5'e kilitli olduğu için bu 5 ihbar `/command/sos` ekranında **OPEN** filtresinde bekliyor — tam AFAD'ın gerçek yaşadığı "kapasite doldu" darboğazını yansıtıyor. Bir ekip A1-A5'ten birini `POST /api/team/claim/{id}/release` ile tamamlayınca (Bölüm 05), müsait hâle gelip B-listesinden birini alabilir.

### 2.4 — Kapalı yollar

Gerçek Copernicus verisiyle, ağır hasar yarıçapında (**32 kapalı yol segmenti**) tespit edilmiş — örnekler: **Haydar Aliyev Bulvarı** (Damaged), **64005. Sokak** (Damaged), **64009. Sk.** (Damaged). Bunlar `/command/road-damage` analizinde kırmızı, açık yollar yeşil çiziliyor; aynı katman `/command/map`'te "Yol Hasarı" toggle'ıyla, mobilde `unified_map_screen.dart`'ta "Yol Hasarı" çipiyle görünüyor.

---

## 3) HATAY — Elektrik / Armutlu Mahalleleri (Antakya/Defne)

**Gerçek konum**: ELEKTRİK bbox 36.1468–36.1519 E / 36.1955–36.1999 N, ARMUTLU bbox 36.1430–36.1509 E / 36.1927–36.1954 N (9 Şubat 2023, Help.NGO + Portekiz GRU görüntüleri). Hasar zemin verisi: Copernicus EMSR648_AOI11.

### 3.1 — 5 Ekip

| Ekip | Rol / Birim | Başlangıç Noktası | Koordinat |
|---|---|---|---|
| ekip-1 | Arama-Kurtarma / **İtfaiye Arama Kurtarma** | Hatay Devlet Hastanesi | 36.2699, 36.2245 |
| ekip-2 | Lojistik-İlk Yardım / **AFAD Lojistik Ekibi** | Saha üssü | 36.3359, 36.1991 |
| ekip-3 | Arama-Kurtarma / **İtfaiye Arama Kurtarma** | Özel Antakya Akademi Hastanesi | 36.2358, 36.1697 |
| ekip-4 | Lojistik-İlk Yardım / **UMKE Sahra Sağlık** | Özel Antakya Akademi Hastanesi | 36.2358, 36.1697 |
| ekip-5 | Arama-Kurtarma / **Jandarma Arama Kurtarma** | Antakya Devlet Hastanesi | 36.2145, 36.1368 |

*Not: Hatay'daki gerçek hastaneler mahalleden 2-16 km uzakta — Antakya'daki büyük hastanelerin depremde ağır hasar görüp bir kısmının hizmet dışı kalmasının gerçek bir yansıması; bu yüzden Hatay'daki mesafeler Kahramanmaraş'a göre belirgin şekilde daha uzun (bkz. tablo).*

### 3.2 — 5 AKTİF İhbar

| # | Kaynak | Durum | Konum | Metin | Atanan Ekip | Mesafe (kuş uçuşu) |
|---|---|---|---|---|---|---|
| A1 | 🚨 SOS | **Kritik** | 36.1964, 36.1457 | *"Ağır yaralı var burada, kan kaybediyor, acil ekip lazım Armutlu'da"* | ekip-5 | 2.165 m |
| A2 | 🚨 SOS | **Kritik** | 36.1967, 36.1450 | *"Bina üstümüze çöktü, arama kurtarma ekibi bekliyoruz Armutlu'da"* | ekip-3 | 4.889 m |
| A3 | 🚨 SOS | Yaralı | 36.1942, 36.1511 | *"Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var Elektrik'te"* | ekip-4 | 4.921 m |
| A4 | 🚨 SOS | Yaralı | 36.1990, 36.1485 | *"Düşen enkazdan yaralandım, kanama var Elektrik'te"* | ekip-1 | 10.427 m |
| A5 | 🚨 SOS | Yaralı | 36.1967, 36.1457 | *"Yaralılar var evde, ambulans gelemedi henüz Armutlu'da"* | ekip-2 | 16.212 m |

### 3.3 — 5 BEKLEYEN İhbar

| # | Kaynak | Durum | Konum | Metin |
|---|---|---|---|---|
| B1 | 🚨 SOS (henüz atanmadı) | Yaralı | 36.1971, 36.1457 | *"Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var Elektrik'te"* |
| B2 | 📝 NLP | Yaralı | 36.1999, 36.1491 | *"Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var Elektrik'te"* |
| B3 | 📝 NLP | Hafif | 36.1994, 36.1482 | *"Çadıra ihtiyacımız var, çok soğukta kaldık Elektrik'te"* |
| B4 | 📝 NLP | Hafif | 36.1974, 36.1454 | *"Suyumuz bitti, temiz suya ihtiyacımız var Armutlu'da"* |
| B5 | 📸 Enkaz modeli (bina.pt) | — | 36.1961, 36.1461 | *(fotoğraf, metin yok — Armutlu'da yıkık bina tespiti)* |

⚠️ **Dürüstlük notu:** Bu senaryonun mevcut Copernicus eşleştirmesinde Elektrik/Armutlu için **0 kapalı yol** tespit edildi (gerçek veri kısıtı — `AKIS_DIYAGRAM_KOD_ESLESTIRME_RAPORU.md` Part E'de not edildi). Yani Hatay'da "kapalı yoldan dönme" dramasını göstermeyin — Hatay'ın gücü **SOS yoğunluğu, mesafe/kapasite darboğazı ve toplanma alanı rotalaması**; "biz olmasaydık ulaşamazdınız" örneğini Kahramanmaraş/Ekmekçi'de gösterin.

### 3.4 — Toplanma alanı mesafeleri (afetzede ekranı için)

Her iki mahalle için en yakın 2 gerçek AFAD toplanma alanı **AKEVLER** (36.2086, 36.1547) ve **ALTINÇAY** (36.2124, 36.1407). Örnek — afetzede ekranında "en yakın toplanma alanı" kartı:

| Afetzede konumu | En yakın nokta | Mesafe |
|---|---|---|
| Armutlu-4 (kritik) | AKEVLER | 1.586 m |
| Elektrik-2 (yaralı) | AKEVLER | 1.203 m |
| Elektrik-1 (bekleyen) | AKEVLER | 1.092 m |

Bu, `screens/survivor/assembly_page.dart` → `GET /api/road_damage/assembly` ile **gerçek zamanlı, gerçek OSRM yürüyüş rotası** olarak hesaplanıyor — demo sırasında canlı gösterilebilir (afetzede "en yakın toplanma alanına git" dediğinde harita üzerinde çizilen yürüyüş rotası).

---

## 4) Ekranlarda nerede görünüyor — kontrol listesi

| Veri | Afetzede telefonu | Ekip telefonu | Web `/command` | Web `/command/map` | Web `/command/sos` |
|---|---|---|---|---|---|
| SOS pin'leri | `unified_map_screen.dart` (SOS çipi) | aynı ekran, `isResponder=true` | dashboard listesi + mini harita | "SOS" toggle | liste + harita, OPEN/EN_ROUTE/RESOLVED filtre |
| NLP ihbarları | — (afetzede kendi SOS'unu görür) | `unified_map_screen.dart` üzerinden dolaylı (SOS ile birleşik) | — | "NLP İhbarları" toggle | — |
| Kamera/enkaz tespiti | kendi fotoğrafı, sonucu | `/command/camera` ile ayrı test edilebilir | — | (heatmap prop var ama render edilmiyor — 🟡) | — |
| Kapalı/açık yollar | "Toplanma Alanlari" ekranı + `unified_map_screen.dart` | aynı | — (road-damage ayrı sayfada) | "Yol Hasarı" toggle | — |
| **Toplanma alanları** | ✅ `unified_map_screen.dart`, varsayılan **açık** | ✅ aynı bileşen, varsayılan **açık** | — | ✅ "Toplanma Alanları" toggle, varsayılan **kapalı** — açılınca yeşil çadır pinleri | — |
| Ekip claim/rota | — | kendi görevini görür | Simülasyon modunda ekip ikonu rota boyunca ilerler | — | — |

---

## 5) Dashboard istatistik kartları — bu senaryoya göre gerçek sayılar

Ekran görüntüsündeki 4 kart şu an `command/page.tsx`'te büyük ölçüde **sabit kodlanmış** (bkz. eşleştirme raporu Part D.4). Bu senaryoyu kullanacaksanız, gerçek sayılarla eşleşmesi için önerilen değerler (iki şehir toplamı):

| Kart | Şu anki (sabit) değer | Bu senaryoya göre gerçek değer |
|---|---|---|
| Aktif SOS İhbarları | `2` / "2 Kritik Enkaz Çağrısı Aktif" | **9 SOS** (KM: A1,A2,A3,B2 = 4 + Hatay: A1-A5,B1 = 6 → toplam 9, "Vaka Bekliyor" = 10 bekleyen ihbarın tamamı) / "4 Kritik Mahsur Çağrısı Aktif" |
| Arama Kurtarma Ekipleri | `18` / "12 Ekip Görevde, 6 Hazırda" | **10 Ekip** / "10 Ekip Görevde, 0 Hazırda" (5+5, hepsi A-listesine kilitli) |
| Uydu Hasar Oranı | `%34.8` | Ekmekçi analizinde gerçek `blockedRoadPct` (canlı analiz sonucundan — demo sırasında gerçek yüzde otomatik gelir, örn. son gerçek koşuda 502 segmentten 2'si kapalı = **%0,4** küçük ölçekte / ağır senaryoda 32 segment ile daha yüksek) |
| Yapay Zeka Modülleri | `3/3` / "Tümü Aktif" | Gerçek: **4 modül** çalışıyor (SegFormer, YOLOv8, NLP/BERTurk+NER, Risk/CatBoost) — kart metnini `4/4 Tümü Aktif` yapmak daha doğru olur |

Bu kartları gerçek veriye bağlamak (`alerts.length`, `teamClaims.length`, canlı `damageRate`) ayrı bir iyileştirme — istersen bunu da yapabiliriz.

---

## 6) Sunum sırası (demo script)

1. **`/command` → Simülasyon Modu AÇ.** (Bölüm 00-01)
2. **`/command/road-damage` → Ekmekçi için "Hasar Analizi" çalıştır** (gerçek SegFormer, ~1-3 dk sürer, ilerleme % görünür). Bitince kapalı/açık yollar kırmızı/yeşil çizilir.
3. **Aynı sayfada "Toplanma Alanları" sekmesi → Ekmekçi ve Elektrik/Armutlu için ara**, sonuçları kaydet (bu adım `/command/map`'in Toplanma Alanları katmanını doldurur).
4. **Mobil afetzede cihazında** SOS gönder (A1: "Merdivenler çöktü, üst katta mahsuruz") → `/command/sos`'ta anında beliriyor.
5. **Mobil afetzede cihazında** kamera ile enkaz fotoğrafı çek (A4) → gerçek YOLOv8 tespiti, haritada işaretlenir.
6. Sırayla kalan 18 ihbarı gönder (script/`live_simulation.py` mantığıyla, ya elle ya da script'i uyarlayarak).
7. **`/command/sos`'ta** operatör A1'i seç, ekip-6'ya ata (claim) → pin renk değiştirir.
8. **Başka bir tarayıcı sekmesinde ekip-3 rolüyle giriş yapıp** A1'e claim atmayı dene → **409 hatası, "Bu hedefe zaten ekip-6 müdahale ediyor"** — çakışma önleme canlı gösterilir.
9. Kalan 4 aktif ihbara sırayla ekip ata, her birinde rota çizilsin.
10. **`/command/map`'i aç, "Toplanma Alanları" toggle'ını AÇ** → yeşil çadır pinleri belirir.
11. **Flagship anı:** A1/A2 için ekrana `benchmark/runs/kahramanmaras-fixed3/naive_baseline_comparison.json`'daki gerçek sayıyı getir: *"Bu ekip, sistemimiz olmasaydı bu mahalledeki gerçek hasarlı yollar yüzünden hedefe HİÇ ULAŞAMAYACAKTI — biz 5,6 dakikada güvenli rotayı bulduk."*
12. Bir görevi tamamla (`release`) → pin yeşile döner, ekip B-listesinden yeni bir ihbara atanabilir hale gelir.
13. Aynı akışı Hatay için tekrarla, bu kez toplanma-alanı-mesafe anlatısına ağırlık ver (bkz. §3.4).

---

## 7) Bilinen sınırlamalar (senaryoyu sunarken bilinçli olun)

- Sistem şu an **rol/uzmanlık eşleştirmesi yapmıyor** — en yakın müsait ekip ne olursa olsun atanıyor (lojistik ekip bazen "mahsur" vakasına gidiyor). Bu senaryoda da düzeltilmedi, gerçek davranış yansıtıldı.
- A3-A5 (Kahramanmaraş) ve tüm Hatay mesafeleri **kuş uçuşu** — gerçek güvenli rota mesafesi demo sırasında canlı hesaplanmalı (`/api/road_damage/route`), bu belgede yer almıyor.
- SOS durumu (`OPEN→EN_ROUTE→RESOLVED`) `/command/sos`'ta **sadece ön yüzde** tutuluyor, backend'e kalıcı yazılmıyor (bkz. eşleştirme raporu) — demo sırasında sayfa yenilenirse durum sıfırlanır.
- Dashboard'daki 4 istatistik kartı gerçek veriye bağlanmadıkça yukarıdaki "düzeltilmiş" sayılar sadece **önerdiğimiz** değerler, otomatik gelmiyor.

---

**Sonraki adım önerisi:** İstersen (a) dashboard kartlarını gerçek `alerts`/`teamClaims`/`damageRate` state'ine bağlayan küçük bir kod değişikliği yapalım, (b) bu 20 ihbarı otomatik gönderen bir demo-seed script'i (`live_simulation.py`'ye benzer ama bu senaryonun tam 5+5/5+5 yapısına uyarlanmış) yazalım, ya da (c) doğrudan canlı demo'yu birlikte prova edelim.
