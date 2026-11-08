# QuakeMind — Akış Diyagramları ↔ Mevcut Kod Eşleştirme Raporu

Bu rapor iki kaynağı esas alır:

1. **Afetzede Akış Diyagramı** (`quakemind-flow`, draw.io) — telefon uygulamasını açan afetzedenin izlediği yol.
2. **QuakeMind Bağlantılı Akış Şeması / Flowchart** (39 syf PDF, "0-05 Bölüm" yapısı) — ekip/AFAD tarafının izlediği yol.

Her adım için üç şey verilmiştir: **diyagramda ne yazıyor**, **kodda tam olarak nerede ve nasıl karşılığı var** (dosya + fonksiyon/endpoint adıyla), ve **somut sayısal/isim/konum verisi** (gerçek çalıştırma çıktılarından). Durum etiketleri:

- 🟢 **GERÇEK** — çalışıyor, uçtan uca test edilmiş
- 🟡 **KISMİ** — bir parçası gerçek, bir parçası simüle/placeholder
- 🔴 **KURGUSAL** — sadece diyagramda var, kodda hiç yok

---

## PART A — Afetzede Akışı ↔ Kod

| # | Diyagram Adımı | Kod Karşılığı | Durum |
|---|---|---|---|
| 1 | Deprem oldu → QuakeMind'ı aç | `mobile/lib/screens/splash_screen.dart` → rol seçimi (survivor/responder) → `AuthController` | 🟢 |
| 2 | 🚨 SOS Butonu (Acil Durum) | `screens/survivor/sos_page.dart` — büyük kırmızı daire buton, `SosService.sendAlert()` → `POST /api/sos/alert` | 🟢 |
| 3 | 📸 Hasar Bildirimi (kamera ile çatlak/enkaz) | `screens/survivor/camera_page.dart` + `widgets/live_camera_view.dart` — **canlı, cihaz-üstü** YOLOv8 (`ultralytics_yolo` paketi, `assets/models/bina.tflite` + `catlak.tflite`) **VEYA** fotoğraf çekip `POST /api/camera/analyze` (bulut YOLOv8, `catlak.pt`/`bina.pt`) | 🟢 (iki yol da gerçek) |
| 4 | 🆘 Yardım İhtiyaçları (metinsel, "yaşlı, ilk yardım vb.") | Backend `POST /api/nlp/analyze` — BERTurk tabanlı sınıflandırma (`Utbird/EqTwitterTr`) + NER lokasyon çıkarımı (`yhaslan/turkish-earthquake-tweets-ner`) + geopy/Nominatim geokodlama | 🟢 |
| 5 | 🛣️ Yol Durumu bildirimi | `POST /api/road_damage/report_blockage` (kullanıcı bildirimi) — ama gerçek "kapalı yol" katmanı asıl olarak SegFormer uydu analizinden geliyor, kullanıcı bildirimi ek bir kaynak | 🟡 |
| 6 | 👥 Komşu Arama (Mesh ağında yakındaki afetzedeleri bul) | **Kodda hiç yok.** Ne Flutter'da ne backend'de Bluetooth/BLE/mesh/P2P kodu bulunamadı (`bluetooth`, `ble`, `mesh`, `p2p` için tüm proje grep edildi, sıfır sonuç) | 🔴 |
| 7 | 1️⃣ GPS Konumu otomatik yakalanır | `Geolocator.getCurrentPosition()` her ekranda (sos_page, assembly_page, road_damage_page, unified_map_screen) — gerçek cihaz GPS'i | 🟢 |
| 8 | 2️⃣ Profil bilgileri (Ad, Yaş, Durum) | `AuthController.instance.user` (id/email/rol) SOS mesajına ekleniyor; "kaç kişi / aciliyet" seçimi `sos_page.dart`'ta `[KISI SAYISI: N] [ACILIYET: KRITIK/YUKSEK/NORMAL]` olarak mesaja gömülüyor — ayrı yaş alanı yok | 🟡 |
| 9 | Görüntü Analizi (YOLOv8) → Çatlak Tespiti (Hasar Derecesi) | `apps/camera_detection` — gerçek YOLOv8 inference, `_severityFromConfidence()` ile confidence→şiddet eşlemesi (`camera_page.dart:206`) | 🟢 |
| 10 | NLP Analizi (BERTurk+NER) → İhtiyaç Kategorileri (Tıbbi, Gıda, Su vb.) | `apps/disaster_nlp/src/pipeline.py` — kategori + 1-5 arası aciliyet skoru (P1-P5) döndürüyor | 🟢 |
| 11 | Yol Kapanma (OSM Karşılaştırması) → Çevredeki yol ağı güncellenir | `apps/road_damage/utils/network.py::analyze_road_network_graph` — SegFormer maskesini OSMnx grafiğiyle kesiştirip `safe_edges`/`blocked_edges` üretiyor | 🟢 |
| 12 | Mesh Ağı (Bluetooth/BLE) → Yakındaki cihazları bul (P2P) | Kodda yok | 🔴 |
| 13 | "Tüm veriler toplanır ve sisteme gönderilir" / "150 byte'lık JSON paketleri, mesh + Raspberry Pi Hotspot" | Gerçek veri gönderimi var (HTTP POST'lar) ama **150 byte / mesh / Raspberry Pi kısmı yok** — her istek normal boyutlu JSON (SOS mesajı örneğin 100-300 byte olabilir ama bu bir tasarım hedefi, ölçülüp uygulanmış bir sınır değil) | 🟡 (veri gönderimi gerçek, taşıma katmanı iddiası kurgusal) |
| 14 | Backend Sunucu → Uydu Görüntüsü Doğrulama (SegFormer) | `apps/road_damage/utils/inference.py::run_inference` — gerçek `optimized_mitb4_focal_dice30.pth` (MiT-B4/SegFormer) checkpoint, patch-based inference | 🟢 |
| 15 | Multimodal Füzyon (S = w1·P_seg + w2·P_nlp) | **Bu formül kodda yok.** SegFormer sonucu ve NLP sonucu ayrı ayrı üretiliyor, ağırlıklı bir füzyon skoru hesaplanmıyor — ikisi de haritada ayrı katman olarak duruyor | 🔴 |
| 16 | GNN Rota Motoru (En Güvenli Yol, <10sn) | `apps/road_damage/utils/network.py::calculate_route` — **gerçek çalışıyor ama GNN değil**: `networkx.shortest_path` (Dijkstra) + `networkx.astar_path`, hasarlı kenarlar graftan çıkarılmış "safe subgraph" üzerinde. Süre gerçekten saniyeler mertebesinde | 🟡 (fonksiyonel olarak diyagramla aynı sonucu veriyor, algoritma markası farklı) |
| 17 | Yardım Merkezi Koordinasyonu (Harita Tabanlı Görev Dağıtımı) | `POST /api/team/claim` + `/command` sayfası (SİMÜLASYON MODU) | 🟢 |
| 18 | 🎯 Afetzedeyi Alan Çıktılar — Harita (konum, yakın yardım noktaları, komşu afetzedeler) | `unified_map_screen.dart` — SOS/toplanma/yol katmanları var; "komşu afetzedeler" katmanı yok (SOS pinleri var ama "yakındaki diğer afetzedeler" ayrı bir görünürlük değil) | 🟡 |
| 19 | Güvenli Rota (A'dan B'ye, tehlikeli bölgeler işaretli) | `screens/survivor/assembly_page.dart` → `GET /api/road_damage/assembly` — en yakın AFAD toplanma alanına gerçek yürüyüş rotası (OSRM, yoksa OSMnx, yoksa düz çizgi) | 🟢 |
| 20 | Komşu İletişim (yakın afetzedelerle mesajlaş) | Kodda yok (chat sadece responder/admin rolüne kapalı — `TeamChatWidget`/`team_chat_sheet.dart`, afetzedeler chate giremiyor) | 🔴 |
| 21 | Gerçek Zamanlı Güncelleme Döngüsü | `/command` sayfası simülasyon modunda 2.5sn'de bir polling (WebSocket değil) | 🟡 |

### Enkaz Altında / Dışarıda senaryo dallanması, güç tasarrufu, otomatik siren, mikrofon dinleme

Bu ikinci diyagramdaki (2BSNZ0X2cUNYynoWwmcM serisi) tüm "Enerji Koruma: ekran kararır, GPS kilitlenir", "Akıllı Siren: hoparlör 100dB düdük çalar, mikrofon açılır" ve "şarj seviyesine göre frekans" özellikleri **kodda hiçbir şekilde yok** — ne pil-tasarruf modu, ne otomatik sesli sinyal, ne mikrofon-dinleme mantığı bulunamadı (`battery`/`pil` için proje genelinde grep sıfır sonuç verdi). 🔴 Tamamen kurgusal.

---

## PART B — Ekip/AFAD Akışı ↔ Kod (Bölüm 00-05)

### Bölüm 00 — Başlangıç & Kimlik

"Role göre başlangıç harita katmanı belirlenir" → `AuthContext.tsx` (web) / `AuthController` (mobil): rol `survivor`/`responder`/`admin`, `RouteGuard` ile `/command/*` sadece responder+admin'e, `/survivor/*` sadece survivor'a açık. 🟢

### Bölüm 01 — Ağ, Donanım & Pil

| Diyagram | Kod | Durum |
|---|---|---|
| ☁️ Bulut Yolu, HTTPS/JWT oturumu | `POST /api/auth/login` bcrypt+PostgreSQL, token tabanlı | 🟢 |
| 🛰️ Otonom Fallback (Mesh var mı? / Offline mod) | Kodda yok | 🔴 |
| 📡 Mesh Aktif · 4 cihaz / Offline mod (lokal GPS+YOLOv8) | Offline-lokal YOLOv8 kısmen doğru — `LiveCameraView` gerçekten cihaz-üstü çalışıyor ve internet gerektirmiyor (bkz. Part A #3). Ama bunun "mesh'e otomatik geçiş" ile bağlantısı yok, ayrı bir özellik | 🟡 |
| 🔋 PİL: Standart / GPS 1sn | Kodda pil-moduna göre GPS sıklığı ayarı yok; `Geolocator` her çağrıda `LocationAccuracy.high` ile tek seferlik konum alıyor | 🔴 |

### Bölüm 02 — Harita & İstihbarat

"Afetzede 'YARDIM EDİN' → 150 byte doğrulanmış → ihtiyaç katmanını besler → Paylaşılan Canlı Operasyon Haritası" → `POST /api/sos/alert` + `POST /api/nlp/analyze` sonuçları `/command/map` sayfasında `MapLayersContext` üzerinden birleşiyor. **"150 byte doğrulanmış" kısmı yok**, ama "tüm ekiplerin aynı haritayı görmesi" gerçek (aynı backend'e her istemci fetch atıyor). 🟡

### Bölüm 03 — Görev Orkestrasyonu & Çakışma Önleme — **En net eşleşen bölüm**

Bu, kodda birebir ve tam çalışan bir mekanizma:

```
POST /api/team/claim  {teamId, targetId, targetType, lat, lon}
```
- `fastapi_app.py:1081-1100`: eğer `targetId` zaten başka bir `teamId` tarafından `status="active"` ile claim edilmişse → **HTTP 409**, mesaj: `"Bu hedefe zaten {ekip} ekibi mudahale ediyor."`
- Değilse claim oluşur, `status: "active"`, `claimedAt` zaman damgası ile.
- `POST /api/team/claim/{id}/release` → `status: "completed"` (= diyagramın "Pin YEŞİLE döner").

Diyagram dili → kod karşılığı:
- "BOŞTA" → claim yok veya `status="completed"`
- "BEN GİDİYORUM" → `POST /api/team/claim`
- "İhbar KİLİTLENİR" → `team_claims[targetId] = {..., status: "active"}`
- "Diğer ekiplerde 'müdahale ediliyor' görünür" → `GET /api/team/claims` her ekibin ekranında (web `getTeamClaims`, mobilde henüz UI'a bağlanmamış — bkz. aşağıdaki not)
- "Yığılma önlendi" → 409 hatası gerçekten bunu engelliyor

⚠️ **Kalıcılık notu**: `team_claims` **process-bellekte** tutuluyor (dict), PostgreSQL'de `teams`/`incidents` tablosu yok — backend restart olursa tüm claim'ler sıfırlanır. Demo için sorun değil, üretim için not edilmeli.

🟢 (WebSocket yerine polling ile, ama iş mantığı birebir gerçek)

### Bölüm 04 — GNN Navigasyon & Aktif Haberleşme

- Rota adımları (GPS→graf→risk puanı→<10sn en güvenli rota) → `network.py::calculate_route`, gerçek Dijkstra/A*, gerçek süre saniyeler mertebesinde (bkz. Part A #16 notu — "GNN" markalaması gerçek algoritmayı yansıtmıyor).
- 🔗 Ekipler arası saha telsizi (şifreli mesh chat) → `POST /api/chat/send` + `GET /api/chat/messages`, `TeamChatWidget.tsx` (web, 4sn poll) / `team_chat_sheet.dart` (mobil) — **gerçek, çalışan bir grup sohbeti**, ama mesh/P2P/BLE üzerinden değil, normal backend üzerinden, sadece responder/admin rolüne açık. 🟡
- "Yeni tehlike → Otonom yeniden rota" → Kodda otomatik tetiklenen bir yeniden-rotalama yok; kullanıcı manuel olarak tekrar `/api/road_damage/route` çağırmalı. 🔴

### Bölüm 05 — Ulaşım, Geri Bildirim & Kapanış Döngüsü

"GÖREV TAMAMLANDI → ihbar temizlenir → Pin YEŞİLE döner" → `POST /api/team/claim/{id}/release`. 🟢
"Ekstra çağrı: takviye/ağır iş makinesi" → Kodda özel bir "takviye iste" endpoint'i yok; chat üzerinden serbest metinle yapılabilir ama yapısal bir alan değil. 🔴

### ⚙️ Sistem — 4 Paralel Harita Katmanı

| Katman | Diyagram | Kod | Durum |
|---|---|---|---|
| Uydu → SegFormer → Enkaz Isı Haritası | ✓ | `run_inference` gerçek segmentasyon maskesi üretiyor, ama "ısı haritası" (heatmap) görselleştirmesi web'de **prop olarak var (`heatData`) ama render edilmiyor** (LeafletContainer'da kullanılmıyor) | 🟡 |
| Sosyal medya + SOS → BERTurk+NER → İhtiyaç pinleri | ✓ | `/api/nlp/analyze` gerçek, ama "sosyal medya" kaynağı yok — sadece elle girilen metin (SOS mesajı veya `/command/nlp` demo metinleri) | 🟡 |
| OSM yol vektörleri → kesişim>%15 → Açık/Kapalı yollar | ✓ | `network.py` gerçek kesişim analizi yapıyor (yüzde eşiği kod içinde farklı olabilir, ama mantık aynı) | 🟢 |
| PostGIS → Hastane & toplanma | ✓ | `afad_assembly_points` tablosu, ~72.000 gerçek AFAD toplanma alanı (JSON'dan seed) | 🟢 |

---

## PART C — Toplanma Alanları Haritada Görünürlüğü (özellikle sorduğunuz konu)

**Web — `/command/map` (Birleşik Komuta Haritası):**
- Katman anahtarı: `assemblyAreas`, etiket: **"Toplanma Alanları"**, ikon: çadır (Tent), renk: yeşil (`text-emerald-400`).
- `MapLayersContext.tsx:73` → varsayılan görünürlük **`false`** — yani **toggle kapalı başlıyor, ekip haritayı açtığında elle açması gerekiyor** (tam sizin istediğiniz gibi: "toggle açıksa gözüksün").
- Toggle açıldığında (`layerVisibility.assemblyAreas === true`) → `assemblyAreas` dizisindeki her kayıt haritada yeşil pin olarak beliriyor, popup'ta "Toplanma Alanları Ekranına Git" linki var (`command/map/page.tsx:116-132`).
- ⚠️ **Önemli operasyonel not**: `assemblyAreas` verisi sayfa açılışında otomatik çekilmiyor — sadece biri `/command/road-damage` sayfasının "Toplanma Alanları" sekmesinde bir arama yaptıysa dolar (`road-damage/page.tsx:786-816`, `getAssemblyAreas()` → `setAssemblyAreas()`). **Senaryoda bunu bir adım olarak eklemek gerekiyor** (örn. "operatör önce Ekmekçi/Kahramanmaraş için toplanma alanı araması yapar, sonra /command/map'te toggle'ı açar").

**Mobil — `unified_map_screen.dart` (hem responder hem survivor kullanıyor):**
- `_LayerChip` listesinde **"Toplanma Alanlari (N)"** filtre çipi var, varsayılan görünür (`?? true`), `MapLayersController.instance.assemblyAreas` üzerinden geliyor.
- Bu ekran hem `isResponder=true` hem `isResponder=false` modunda aynı — yani **afetzede telefonunda da, ekip telefonunda da toplanma alanları aynı harita bileşeninde görünüyor**, sadece açıklama metni değişiyor.

Sonuç: İstediğiniz "toplanma alanları haritada işaretli, ekip tarafında toggle açıksa görünsün" davranışı **hem webde hem mobilde gerçek ve çalışan bir özellik**, tek eksik otomatik veri yüklemesi (yukarıdaki not).

---

## PART D — Tamamen Kurgusal Kalan Unsurlar (özet liste)

Senaryoyu yazarken bunları **anlatı/vizyon** olarak kullanabilirsiniz ama "sistem şunu yapıyor" diye sunmayın, çünkü kodda karşılığı yok:

1. **Mesh ağı / BLE / P2P / Raspberry Pi Hotspot** — hiçbir yerde yok (backend + mobil, tam grep edildi).
2. **Pil tasarrufu modu, GPS sıklığı ayarı (1sn/10sn), otomatik siren, mikrofon dinleme** — yok.
3. **"GNN Rota Motoru"** markası — gerçek algoritma Dijkstra/A* (networkx), gerçek GNN (graph neural network) modeli yok. Sonuç kalitesi/hızı diyagramla örtüşüyor, sadece teknik isim yanlış.
4. **Multimodal füzyon formülü (S = w1·P_seg + w2·P_nlp)** — kodda böyle bir ağırlıklı skor birleştirme yok.
5. **WebSocket / 150 byte paket** — gerçek mekanizma polling (web: 2.5sn simülasyon modu, chat 4-15sn) + istemci-taraflı zaman-bazlı interpolasyon.
6. **Komşu afetzede keşfi / afetzedeler arası mesajlaşma** — chat sadece ekip/admin rolüne kapalı.
7. **Otomatik yeniden-rotalama (yeni tehlike algılanınca)** — manuel tetiklenmesi gerekiyor.

---

## PART E — Senaryo İçin Hazır, Gerçek Sayısal Veri Seti

Bu veriler `backend/benchmark/` altında zaten üretilmiş durumda ve gerçek Copernicus EMSR648 hasar tespiti + gerçek AFAD toplanma alanı verisiyle eşleşiyor:

### Kahramanmaraş (merkez)
- **Mahalle**: EKMEKÇİ (gerçek 9 Şubat 2023 uydu görüntüsü, Help.NGO/OpenAerialMap, bbox: 36.9175–36.9239 E, 37.5731–37.5782 N)
- **Toplanma alanları (4)**: BAHÇELİ EVLER (37.571655, 36.937853), DİVANLI (37.588945, 36.933927), EGEMENLİK (37.567825, 36.932737), EKMEKÇİ (37.586551, 36.928225)
- **6 afetzede** (EKMEKÇİ-1..6), durum dağılımı: 2 yaralı+SOS, 1 yaralı, 1 hafif, 2 hafif — örnek metin: *"Bacağım kırıldı sanırım, tıbbi yardıma ihtiyacım var Ekmekçi̇"*
- **6 ekip**, gerçek hastane/itfaiye konumlarından başlıyor:
  - ekip-1, AKUT Saha Ekibi, Sütçü İmam Üniversitesi Tıp Fakültesi (37.5879, 36.8261)
  - ekip-2, Kızılay Lojistik Ekibi, Kadın Doğum ve Çocuk Hastalıkları Hastanesi (37.5940, 36.8834)
  - ekip-3, Jandarma Arama Kurtarma, Yenişehir Devlet Hastanesi (37.5781, 36.9315)
  - ekip-4, Kızılay Lojistik Ekibi, İtfaiye (37.5603, 36.9543)
  - ekip-5, İtfaiye Arama Kurtarma, İtfaiye (37.5891, 36.9423)
  - ekip-6, AFAD Lojistik Ekibi, Hayat Hastanesi (37.5776, 36.9288)
- **32 kapalı yol** (ağır senaryo, örnek: Haydar Aliyev Bulvarı — Damaged, 64005. Sokak — Damaged)

**Gerçek çalıştırma örneği** (`benchmark/runs/kahramanmaras-watch2`, bugünkü tarihli canlı simülasyon çıktısı):
- Uydu analizinde 502 yol segmenti tarandı → **2 kapalı, 500 açık**
- 6 ekip-afetzede eşleşmesi, gerçek Dijkstra/A* mesafeleri:

| Ekip | Afetzede | Mesafe |
|---|---|---|
| ekip-6 | EKMEKÇİ-5 | 663 m |
| ekip-4 | EKMEKÇİ-4 | 1.155 m |
| ekip-5 | EKMEKÇİ-2 | 1.608 m |
| ekip-1 | EKMEKÇİ-1 | 1.801 m |
| ekip-2 | EKMEKÇİ-3 | 1.963 m |
| ekip-3 | EKMEKÇİ-6 | 2.127 m |

Bu tablo, "biz size söylemeseydik kapalı yoldan gidecektiniz" anlatısı için **gerçek bir referans**: aynı sistem hem güvenli rotayı hem mesafeyi zaten üretiyor. "Kapalı yoldan gidilseydi ne kadar fazla yol/zaman kaybedilirdi" kıyası şu an otomatik hesaplanmıyor (🔴 kurgusal) — bunu senaryo anlatımında siz hesaplayıp sunacaksınız (örn. güvenli rota vs. düz/kapalı-yol-dahil rota mesafesi farkı).

### Hatay (Antakya/Defne)
- **2 mahalle**: ELEKTRİK (bbox 36.1468–36.1519 E, 36.1955–36.1999 N), ARMUTLU (bbox 36.1430–36.1509 E, 36.1927–36.1954 N)
- **Toplanma alanları (2, her iki mahallede de aynı en yakın ikisi)**: AKEVLER, ALTINÇAY
- **12 afetzede** (6+6), örnek kritik: *"Bina üstümüze çöktü, arama kurtarma ekibi bekliyoruz Armutlu"* (ARMUTLU-4, SOS=true), *"Ağır yaralı var burada, kan kaybediyor, acil ekip lazım"* (ARMUTLU-6, SOS=true)
- **6 ekip**: ekip-1 İtfaiye Arama Kurtarma @ Hatay Devlet Hastanesi (36.2699, 36.2245); ekip-2 AFAD Lojistik @ (36.3359, 36.1991); ekip-3 İtfaiye Arama Kurtarma @ Özel Antakya Akademi Hastanesi (36.2358, 36.1697); ekip-4 UMKE Sahra Sağlık @ aynı hastane; ekip-5 Jandarma Arama Kurtarma @ Antakya Devlet Hastanesi (36.2145, 36.1368); ekip-6 AFAD Lojistik @ (36.3359, 36.1991)
- ⚠️ **Kapalı yol sayısı bu senaryoda 0** — Hatay için Copernicus ground-truth eşleşmesi mahalle yarıçapında hasarlı yol bulamamış (veri kalitesi kısıtı, EKMEKÇİ kadar zengin değil). Demo için Hatay'ı kullanacaksanız ya farklı bir mahalle/yarıçap denenmeli ya da bu şehirde "yol kapanması" anlatısını Kahramanmaraş'a yükleyip Hatay'ı "SOS + NLP + toplanma" ağırlıklı göstermek daha gerçekçi olur.

### İstediğiniz "her şehir için 5 ekip, 5 aktif + 5 bekleyen ihbar" hedefiyle farkı
Mevcut üretici (`scenario_generator.py`) şu an **6 ekip / mahalle başına 6 afetzede** üretiyor (Kahramanmaraş 1 mahalle → 6 afetzede toplam; Hatay 2 mahalle → 12 afetzede toplam), "aktif" ve "bekleyen" diye ayrı bir sayaç yok — hepsi tek listede duruyor, hangisinin ekip tarafından claim edildiğine göre "aktif/bekleyen" ayrımı yapılabilir olur. Sizin istediğiniz **tam 5+5** düzenini elde etmek için `VICTIMS_PER_MAHALLE`/`TEAMS_PER_REGION` sabitlerini değiştirmek ya da senaryo JSON'unu elle 5/5'e kırpmak gerekir — bu, bir sonraki adımda (senaryo yazımında) yapılabilir, altyapı buna hazır.

---

## Sonuç

İki diyagramın da **iskeleti** (SOS → tespit modelleri → rota motoru → ekip ataması → çakışma önleme → harita) kodda gerçekten var ve bugün (12 Ağustos 2026) gerçek API'lere karşı çalıştırılmış durumda (`benchmark/runs/`). Asıl kurgusal/pazarlama katmanı **mesh ağı, pil yönetimi, WebSocket, GNN markası ve multimodal füzyon formülü** — bunlar ya "gelecek vizyon" olarak senaryoda sözle geçebilir ya da senaryodan tamamen çıkarılıp sadece gerçek çalışan kısımlar üzerinden anlatılabilir. Toplanma alanları katmanı, hem mobilde hem webde, tam istediğiniz gibi toggle-bağımlı olarak çalışıyor.

**Önerilen sonraki adım**: Bu rapordaki gerçek veri setini (Kahramanmaraş/EKMEKÇİ + Hatay/ELEKTRİK-ARMUTLU, ekip isimleri, toplanma alanları, mesafe örnekleri) temel alarak, 5 ekip/5 aktif/5 bekleyen ihbar yapısına uyarlanmış tam senaryo metnini birlikte yazalım.
