# QuakeMind — Uçtan Uca Çift Taraflı Afet Simülasyonu (Senaryo v2)

**Kapsam:** Hatay, Kahramanmaras · 9 operasyon bölgesi · 18 afetzede · 18 ekip ataması


## Yöntem ve Dürüstlük Notu

- **Gerçekten çalıştırılan:** OSM yol grafiği (yerel PBF), rota motoru (A*/Dijkstra), naive-ajan karşılaştırması, YOLOv8 `bina.pt` görüntü çıkarımı, BERTurk NLP sınıflandırma + NER konum çıkarımı, görev kilitleme (409), AFAD toplanma alanı sorgusu.
- **Temsili (gerçek pipeline'dan geçen ama sentetik) veri:** yol kapanmaları, cihaz pil/güç modu/siren/haberleşme durumu, afetzede koordinatları.
- **Bu koşuda SegFormer çalıştırılmamıştır.** Yol kapanmaları rastgele atanmıştır; bu nedenle Tablo 2'de mIoU / piksel-çakışma sütunu **yoktur** — yazılacak gerçek bir ölçüm olmadığı için. Modelin kendi doğruluğu aşağıdaki ayrı bölümde raporlanır.
- **Modellenen (ölçüm değil):** hayatta kalma olasılığı artışı — bkz. Etki Modellemesi.


## Akış Diyagramlarıyla Bağlantı

Bu koşu, orijinal **Afetzede Akışı** ve **Ekip/AFAD Akışı** diyagramlarının (sıraları hiç değiştirilmeden) gerçek bir canlandırmasıdır. Aşağıda önce bir afetzedenin, sonra bir ekibin hikâyesi üzerinden diyagramın adımları bu koşudaki gerçek karşılıklarıyla anlatılıyor.


### Afetzede Akışı — Selim, Ali ve Burak'ın sabahı

Antakya–Defne bölgesinde sabah aynı anda üç telefon çalışmaya başlıyor. **Selim Kaya**, İnönü Caddesi'nde 5 katlı bir binanın kolonunun çöktüğünü görüyor — hareket edebiliyor, kamerayı çekip gönderiyor. **Ahmet Yılmaz**, Armutlu Mahallesi'nde toplanmış bir grubun içinde; su ve battaniye lazım, bunu yazıyla anlatıyor. **Ali Öztürk**, Cebrail Mahallesi'nde; bina yan yatmış, içeride üç kişi var. Aynı sabah İskenderun'da **Burak Şahin** enkaz altında — telefonuna dokunamıyor bile, cihaz kendi başına otonom hayatta kalma moduna geçiyor. Bu dördü diyagramın 'beş paralel eylem' kutusunun üç farklı kanaldan (kamera, metin, SOS) aynı anda dolduğunu gösteriyor.


| # | Diyagram Adımı | Durum | Bu koşudaki karşılığı |
|---|---|---|---|
| 1 | Deprem oldu → QuakeMind'ı aç | GERÇEK | Rol seçimi → RouteGuard, /survivor ve /command ayrı korumalı |
| 2 | 🆘 SOS Butonu | GERÇEK | Burak Şahin: %14 pil, Tasarruf Modu, Siren aktif, BLE Mesh, 83 B ölçülen paket |
| 3 | 📸 Hasar Bildirimi (Kamera) | GERÇEK | Selim Kaya: model 158 ms'de cevap verdi — Bina Ağır Hasarlı, %78,8 güven |
| 4 | 🆘 NLP İhtiyaç Metni | GERÇEK | Ali Öztürk: kategori Acil Yardım İhtiyacı, aciliyet 4/5 — model cevabı 7,98 sn sürdü |
| 5 | 🛣️ Yol Durumu Bildirimi | KISMİ | Endpoint var; kapalı-yol katmanı bu koşuda temsili (bkz. Tablo 2 sonrası bölüm) |
| 6 | 👥 Mesh Komşu Arama | KURGUSAL | Kodda hiçbir iz yok |
| 7 | GPS Konumu Otomatik Yakalanır | GERÇEK | Her ihbar en az 700 m arayla, rastgele ama ayrık dağıtılıyor |
| 8 | Profil Bilgileri (Durum/Aciliyet) | KISMİ | Durum (kritik/mahsur/yaralı/hafif) + buna bağlı pil aralığı temsili |
| 9 | Görüntü Analizi → Hasar Derecesi | GERÇEK | 3 gerçek sınıf: NoDamage / ModerateDamage / VeryHeavyDamage |
| 10 | NLP Analizi → İhtiyaç Kategorileri | GERÇEK | Kategori + 1-5 aciliyet — 2 ihbarda model hiç sınıflandırmadı (aşağıda) |
| 11 | Yol Kapanma (OSM Karşılaştırması) | KISMİ | Graf gerçek; kapanma kararı temsili — bkz. Tablo 2 sonrası bölüm |
| 12 | Mesh Ağı (BLE) → Yakındaki Cihazlar | KURGUSAL | Kodda yok |
| 13 | "150 byte paket, mesh + Raspberry Pi" | KISMİ | Taşıma iddiası kurgusal; paket boyutu artık gerçekten ölçülüyor: 81–85 B |
| 14 | Backend → Uydu Doğrulama (SegFormer) | KISMİ | Model gerçek ve ayrıca doğrulanmış (Kate-PD); bu koşuda çalıştırılmadı |
| 15 | Multimodal Füzyon (S = w1·P_seg + w2·P_nlp) | KURGUSAL | Böyle bir ağırlıklı formül kodda yok |
| 16 | GNN Rota Motoru (<10sn) | KISMİ | Gerçek algoritma Dijkstra/A*; 18 rotanın hiçbiri kapalı segmentten geçmedi |
| 17 | Yardım Merkezi Koordinasyonu | GERÇEK | POST /api/team/claim + /command simülasyon modu |
| 18 | Afetzedeyi Alan Çıktılar — Harita | KISMİ | SOS/toplanma/yol katmanları var; 'komşu afetzedeler' katmanı yok |
| 19 | Güvenli Rota (toplanma alanına) | GERÇEK | Örnek: Ali Öztürk'ün en yakın toplanma alanı Ulucami, 108 m |
| 20 | Komşu İletişim (afetzedeler arası) | KURGUSAL | Chat sadece ekip/admin rolüne kapalı |
| 21 | Gerçek Zamanlı Güncelleme Döngüsü | KISMİ | WebSocket değil, 2,5 sn polling — kullanıcı için gerçek zamanlı hissediyor |

**Bir düzeltme:** Bu diyagramın daha önceki eşleştirme raporunda 'Enerji Koruma', 'Akıllı Siren' ve 'Mesh Aktif · N cihaz' maddeleri tamamen kurgusal işaretlenmişti. Bu artık doğru değil — bu koşuda pil yüzdesi, güç modu, siren ve haberleşme durumunun hepsinin gerçek bir karşılığı var (bkz. Tablo 1'deki 'Pil / Güç Modu' ve 'Ağ Fallback' sütunları).


### Ekip/AFAD Akışı — İki ekibin aynı hedefe koşması

Onikişubat İtfaiye Merkezi'nden aynı anda iki ekip harekete geçiyor: **MARAS-AK1** ve **MARAS-AK2**. İkisi de haritada aynı kritik ihbarı görüyor — **Aylin Kurt**, Dulkadiroğlu'nda ağır enkaz altında. MARAS-AK1 önce davranıp hedefi kilitliyor; MARAS-AK2'nin bir saniye sonra attığı 'BEN GİDİYORUM' isteği backend'den **409 Conflict** ile geri dönüyor. MARAS-AK2 hemen bir sonraki hedefe yöneliyor: **Serkan Tan**. Bu, diyagramın 'BOŞTA → AKTİF → 409 Engellendi' durum döngüsünün bu koşudaki tam karşılığı.


| Bölüm | Diyagram Adımı | Durum | Bu koşudaki karşılığı |
|---|---|---|---|
| 00 | Başlangıç & Kimlik | GERÇEK | RouteGuard ile /command/* sadece responder+admin'e açık |
| 01 | Ağ, Donanım & Pil | KISMİ | Bulut/HTTPS gerçek; mesh-fallback kodda yok. Kenar çubuğu artık gerçek SOS verisinden sayıyor: 11 Şebeke, 7 BLE Mesh, 0 çevrimdışı |
| 02 | Harita & İstihbarat | KISMİ | Tüm ekipler aynı haritayı görüyor: 18 ihbar, 18 ekip, 9 bölge, 2 şehir aynı anda |
| 03 | Görev Orkestrasyonu & Çakışma Önleme | GERÇEK — en net eşleşen bölüm | 18 atamanın hepsi başarılı; 9 mükerrer sevk denemesinin 9'u da 409 ile engellendi |
| 04 | GNN Navigasyon & Aktif Haberleşme | KISMİ | Gerçek Dijkstra/A*; en büyük fark MARAS-AK2→Serkan Tan: bizim 16,9 dk, naif 352,5 dk |
| 05 | Ulaşım, Geri Bildirim & Kapanış | GERÇEK | POST /api/team/claim/{id}/release → 'GÖREV TAMAMLANDI' |

## Tablo 1 — Afetzede İhbarları ve Model Çıkarım Matrisi

| Sehir | Bolge | Isim | Konum | Kanal | Pil / Guc Modu | Ag Fallback (olculen) | Model Yanit (ms) | Model Ham Ciktisi | Pin |
|---|---|---|---|---|---|---|---|---|---|
| Hatay | Antakya - Defne | Selim Kaya | Antakya, Inonu Cad. | YOLOv8 Hasar Ihbari | %65 / Normal | P2P BLE Mesh (hafif JSON) (85 B) | 158.3 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %78.8 · 2 tespit | turuncu |
| Hatay | Antakya - Defne | Ahmet Yilmaz | Defne, Armutlu Mah. | NLP Ihtiyac Ihbari | %55 / Normal | HTTPS/REST API (tam veri) (83 B) | 11419.4 | Lojistik İhtiyaç Bildirimi · aciliyet 2/DUSUK · guven 0.848 | sari |
| Hatay | Antakya - Defne | Ali Ozturk | Antakya, Cebrail Mah. | NLP Ihtiyac Ihbari | %47 / Normal | P2P BLE Mesh (hafif JSON) (84 B) | 7976.2 | Acil Yardım İhtiyacı · aciliyet 4/YUKSEK · guven 0.467 | sari |
| Hatay | Iskenderun | Caner Yildiz | Iskenderun, Liman Cad. | YOLOv8 Hasar Ihbari | %75 / Normal | HTTPS/REST API (tam veri) (84 B) | 171.6 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %85.5 · 2 tespit | turuncu |
| Hatay | Iskenderun | Burak Sahin | Iskenderun, Cay Mah. | Acil SOS Cagrisi | %14 / Tasarruf (GPS 10sn) + Siren | P2P BLE Mesh (hafif JSON) (83 B) |  | Enkaz alti, otonom hayatta kalma modu aktif, BLE sinyali | kirmizi flasor |
| Hatay | Kirikhan | Elif Demir | Kirikhan, Cumhuriyet Meydani | YOLOv8 Hasar Ihbari | %18 / Tasarruf (GPS 10sn) | HTTPS/REST API (tam veri) (84 B) | 173.3 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %78.8 · 2 tespit | turuncu |
| Hatay | Kirikhan | Emre Aydin | Kirikhan, Pasali Cad. | Acil SOS Cagrisi | %35 / Normal | P2P BLE Mesh (hafif JSON) (84 B) |  | Merdiven boslugunda sikisma, Mesh P2P | kirmizi flasor |
| Hatay | Samandag | Merve Sen | Samandag, Ataturk Cad. | NLP Ihtiyac Ihbari | %40 / Normal | HTTPS/REST API (tam veri) (84 B) | 58.0 | **ELENDI** — model metni afetle iliskisiz saydi (yanlis negatif) | sari |
| Hatay | Belen | Sevgi Kaya | Belen, Fatih Mah. (tasindi: Antakya, Harbiye Cad.) | Acil SOS Cagrisi | %50 / Normal | HTTPS/REST API (tam veri) (84 B) |  | Yikinti yani mahsur, AFAD REST API | kirmizi flasor |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Mustafa Yildiz | Onikisubat, Trabzon Bulvari | YOLOv8 Hasar Ihbari | %82 / Normal | HTTPS/REST API (tam veri) (84 B) | 168.4 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %78.8 · 2 tespit | turuncu |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Aylin Kurt | Dulkadiroglu, Ismetpasa Mah. | YOLOv8 Hasar Ihbari | %22 / Normal | HTTPS/REST API (tam veri) (85 B) | 153.6 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %85.5 · 2 tespit | turuncu |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Zeynep Celik | Dulkadiroglu, Azerbaycan Bulvari | NLP Ihtiyac Ihbari | %38 / Normal | HTTPS/REST API (tam veri) (84 B) | 48.8 | **ELENDI** — model metni afetle iliskisiz saydi (yanlis negatif) | sari |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Hakan Koc | Onikisubat, Haydarbey Mah. | NLP Ihtiyac Ihbari | %71 / Normal | HTTPS/REST API (tam veri) (81 B) | 9765.8 | Lojistik İhtiyaç Bildirimi · aciliyet 2/DUSUK · guven 0.763 | sari |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Serkan Tan | Dulkadiroglu, Istasyon Mah. (tasindi: Turkoglu, Istasyon Mah.) | Acil SOS Cagrisi | %42 / Normal | P2P BLE Mesh (hafif JSON) (83 B) |  | Merdiven cokmesi sonucu mahsur, BLE Mesh | kirmizi flasor |
| Kahramanmaras | Merkez (Onikisubat - Dulkadiroglu) | Derya Uysal | Onikisubat, Binevler Mah. | Acil SOS Cagrisi | %68 / Normal | HTTPS/REST API (tam veri) (83 B) |  | Kismi gocuk, 4.5G | kirmizi flasor |
| Kahramanmaras | Elbistan | Tolga Erdem | Elbistan, Gunesli Mah. | YOLOv8 Hasar Ihbari | %60 / Normal | P2P BLE Mesh (hafif JSON) (85 B) | 155.9 | Bina Ağır Hasarlı (2_VeryHeavyDamage) · guven %78.8 · 2 tespit | turuncu |
| Kahramanmaras | Pazarcik | Fatma Dogan | Pazarcik, Merkez Mah. | Acil SOS Cagrisi | %11 / Tasarruf (GPS 10sn) + Siren | P2P BLE Mesh (hafif JSON) (84 B) |  | Agir enkaz altinda, otonom hayatta kalma modu aktif | kirmizi flasor |
| Kahramanmaras | Goksun | Fatma Arslan | Goksun, Ataturk Cad. (tasindi: Afsin, Ataturk Cad.) | NLP Ihtiyac Ihbari | %29 / Normal | P2P BLE Mesh (hafif JSON) (84 B) | 9796.7 | Enkaz Bildirimi · aciliyet 5/KRITIK · guven 0.473 | sari |


## Afetzede Uygulamaya Erişip Ne Kadar Sürede Cevap Aldı?

Üç kanalın üçü de farklı bir hızda cevap veriyor — diyagramın söylemediği, ölçülünce ortaya çıkan bir gerçek.


| Kanal | Ölçülen yanıt süresi | Ne oluyor |
|---|---|---|
| SOS | anında | Model adımı yok — tek dokunuş doğrudan POST /api/sos/alert'e gidiyor |
| YOLO | ~155–173 ms | Gerçek bina.pt çıkarımı — 6 ihbarın hepsinde neredeyse sabit |
| NLP (sınıflandırılan) | 7,98 – 11,42 sn | BERTurk + NER + gerçek Nominatim coğrafi kodlama ağ çağrısı |
| NLP (elenen) | 49 – 58 ms | Model 'afetle ilişkisiz' derse NER/geokodlamaya hiç geçmiyor — hızlı ret |

Sahada anlamı şöyle: Burak Şahin düğmeye bastığı anda ihbarı gitti. Selim Kaya fotoğrafı gönderdiğinde göz açıp kapayana kadar (158 ms) hasar sınıfı geldi. Ama Ahmet Yılmaz metnini gönderdiğinde ekranında 'gönderiliyor' yazısı **11,4 saniye** boyunca kaldı — model konumunu metinden çıkarıp gerçek bir harita servisine sorup cevap bekledi.



## Tablo 2 — Bölge Bazlı Yol Ağı Durumu

| Bolge | Analiz Kimligi | Kapali Segment | Acik Segment | Kapanma Orani (%) | Ekip Rotalarinin Bypass Ettigi Kapali Segment |
|---|---|---|---|---|---|
| Antakya - Defne | cab2db4b | 920 | 40030 | 2.2 | 3 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Iskenderun | ee9eddf3 | 1186 | 25190 | 4.5 | 2 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Kirikhan | 95a2e41f | 212 | 18704 | 1.1 | 2 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Samandag | 94591142 | 612 | 26638 | 2.2 | 1 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Belen | 2ce5b2e9 | 102 | 18382 | 0.6 | 1 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Merkez (Onikisubat - Dulkadiroglu) | 583bb573 | 2234 | 47432 | 4.5 | 6 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Elbistan | 0cfc73d5 | 876 | 18614 | 4.5 | 1 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Pazarcik | 6c691a1a | 90 | 7974 | 1.1 | 1 rotanin tamami kapali segmentlere girmeden hesaplandi |
| Goksun | 18641b7f | 146 | 12956 | 1.1 | 1 rotanin tamami kapali segmentlere girmeden hesaplandi |

> Kapanmalar temsilidir (rastgele atanmış). Segment sayıları ve geometriler **gerçek OSM yol grafiğinden** gelir; rotalar bu gerçek graf üzerinde, kapalı kenarlar çıkarılarak hesaplanmıştır.


### Yol Kapalılıklarının Kaynağı

Bu, raporun en sık sorulan sorusu olduğu için açıkça yazılmıştır: **kapanmalar ne hazır bir veri setinden alınmıştır, ne de bu koşuda çalıştırılan bir bilgisayarlı görü modelinden üretilmiştir.** Süreç iki katmanlıdır:


**1. Yol ağının kendisi — GERÇEK.** Her operasyon bölgesi için OpenStreetMap'in Türkiye veri dökümünden (`turkey-latest.osm.pbf`, Geofabrik) yerel olarak çıkarılmış gerçek bir yaya yolu grafı kullanılır. Hiçbir canlı internet sorgusu yapılmaz; graf `pyrosm` ile PBF'ten okunur, `OSMnx`/`NetworkX` yapılarına dönüştürülür ve önbelleğe alınır. Düğüm ve kenar sayıları (Tablo 2) bu gerçek grafın sayılarıdır — örneğin Antakya–Defne bölgesi 18.060 düğüm, 40.950 yönlü kenar içerir. Sokak adları, geometriler ve bağlantı topolojisi gerçektir.


**2. Hangi yolun kapalı olduğu — TEMSİLİ.** Bu grafın kenarlarının bir kısmı, sabit bir rastgele tohumla (seed) 'kapalı' işaretlenir. Bu bilinçli bir sadeleştirmedir: bu senaryonun kanıtlamak istediği şey görüntü modelinin doğruluğu değil, **rota motorunun davranışıdır** (gerçek graf + gerçek Dijkstra/A* + gerçek naive-ajan karşılaştırması). Kapatma işlemi kenar değil *fiziksel yol* bazında yapılır: iki yönlü bir sokağın grafta iki ayrı yönlü kenarı vardır ve ikisi birlikte kapatılır — aksi halde rota motoru 'kapalı' görünen bir sokaktan ters yönden geçebilirdi (bu, geliştirme sırasında bulunup düzeltilmiş gerçek bir hatadır).


**Neden SegFormer bu koşuda çalıştırılmadı:** Modelin kendisi projede mevcuttur ve doğruluğu **ayrı ve bağımsız olarak** Kate-PD veri setinin gerçek hasarlı bina görselleriyle kanıtlanmıştır. Uydu görüntüsünden yol kapanması çıkarımı, görüntü çözünürlüğüne aşırı duyarlıdır ve önceki denemelerde otomatik seçilen görüntülerin çoğu bu iş için yetersiz çözünürlükte kalmıştı. Bu koşuda amaç rota motorunu ölçmek olduğu için kapanmalar temsili tutulmuş, model doğrulaması ayrı bölüme bırakılmıştır. **Bu koşudaki YOLOv8 çıktıları (Tablo 1) ise gerçek model çıkarımıdır** — sadece yol-kapanma kararı temsilidir.


**Projede duran, bu koşuda kullanılmayan gerçek hasar verisi:** Copernicus Acil Durum Yönetimi Servisi'nin 6 Şubat 2023 depremleri için ürettiği EMSR648 aktivasyonuna ait resmî hasar derecelendirme haritaları (Kahramanmaraş AoI-04, Hatay/Antakya AoI-11) projede mevcuttur. İleri bir çalışmada kapanmalar rastgele yerine bu zemin-doğruluk verisinden türetilebilir; bu, mevcut altyapıyla uyumludur.


**İstenen %18 neden gerçekleşmedi:** Senaryonun ilk tasarımında kapanma oranı %18 hedeflenmişti. Antakya grafında ölçüldü: %18 kapanmada grafın en büyük bağlı bileşeni tabanın **%24'üne** çöküyor — rota motoru çoğu ekip-hedef çifti için hiç yol bulamaz hale geliyor. Motor bu yüzden oranı otomatik olarak yarılayarak yeniden dener, ta ki bağlantı korunana kadar. Sonuç: bu koşuda gerçekleşen oran **%0,6 – %4,5** arasında kaldı (yukarıdaki tablonun son sütunu). Eşik gevşetilebilir (bağlantı tabanı %92'den %90'a çekilirse kapanmalar iki katına çıkar) — bu, sonucu doğrudan etkilediği için ayrıca karar verilmesi gereken bir parametredir.


## Tablo 3 — Ekip Dağılımı, Görev Kilitleri ve Rotalar

| Ekip | Rol | Karargah | Kilitlenen Ihbar | Kanal | Mukerrer Sevk Denemesi (409) | Rota (m) | Intikal (dk) | Tahliye Hedefi |
|---|---|---|---|---|---|---|---|---|
| HATAY-AK1 | Arama-Kurtarma | Antakya AFAD Ana Koordinasyon Merkezi | Ali Ozturk (Antakya, Cebrail Mah.) | NLP | HATAY-AK2 -> 409 ENGELLENDI | 3611.0 | 14.4 | ULUCAMİİ (108 m) |
| HATAY-AK2 | Arama-Kurtarma | Antakya AFAD Ana Koordinasyon Merkezi | Selim Kaya (Antakya, Inonu Cad.) | YOLO | HATAY-LOJ1 -> 409 ENGELLENDI | 6149.0 | 24.6 | HARBİYE (802 m) |
| HATAY-LOJ1 | Lojistik | Defne Sahra Hastanesi | Ahmet Yilmaz (Defne, Armutlu Mah.) | NLP | - | 3608.0 | 14.4 | DURSUNLU (675 m) |
| HATAY-AK3 | Arama-Kurtarma | Iskenderun Itfaiye Grup Amirligi | Burak Sahin (Iskenderun, Cay Mah.) | SOS | HATAY-MED1 -> 409 ENGELLENDI | 2349.0 | 9.4 | GÜRSEL (217 m) |
| HATAY-MED1 | Medikal | Iskenderun Itfaiye Grup Amirligi | Caner Yildiz (Iskenderun, Liman Cad.) | YOLO | - | 3001.0 | 12.0 | MEYDAN (124 m) |
| HATAY-AK4 | Arama-Kurtarma | Kirikhan Acil Mudahale Istasyonu | Emre Aydin (Kirikhan, Pasali Cad.) | SOS | HATAY-LOJ2 -> 409 ENGELLENDI | 1083.0 | 4.3 | KURTULUŞ (164 m) |
| HATAY-LOJ2 | Lojistik | Kirikhan Acil Mudahale Istasyonu | Elif Demir (Kirikhan, Cumhuriyet Meydani) | YOLO | - | 1039.0 | 4.2 | GAZİ (903 m) |
| HATAY-MED2 | Medikal | Samandag Kizilay Afet Deposu | Merve Sen (Samandag, Ataturk Cad.) | NLP | - | 1699.0 | 6.8 | ATATÜRK (964 m) |
| HATAY-AK5 | Arama-Kurtarma | Belen Gecidi Taktik Lojistik Ussu | Sevgi Kaya (Belen, Fatih Mah.) | SOS | - | 2102.0 | 8.4 | BAKRAS (336 m) |
| MARAS-AK1 | Arama-Kurtarma | Onikisubat Itfaiye Merkezi | Aylin Kurt (Dulkadiroglu, Ismetpasa Mah.) | YOLO | MARAS-AK2 -> 409 ENGELLENDI | 4163.0 | 16.7 | EGEMENLİK (307 m) |
| MARAS-MED1 | Medikal | Dulkadiroglu Sahra Hastanesi | Zeynep Celik (Dulkadiroglu, Azerbaycan Bulvari) | NLP | MARAS-AK2 -> 409 ENGELLENDI | 3093.0 | 12.4 | SAKARYA (246 m) |
| MARAS-AK2 | Arama-Kurtarma | Onikisubat Itfaiye Merkezi | Serkan Tan (Dulkadiroglu, Istasyon Mah.) | SOS | MARAS-MED2 -> 409 ENGELLENDI | 4218.0 | 16.9 | KARACAOĞLAN (117 m) |
| MARAS-MED2 | Medikal | Dulkadiroglu Sahra Hastanesi | Derya Uysal (Onikisubat, Binevler Mah.) | SOS | MARAS-LOJ1 -> 409 ENGELLENDI | 1820.0 | 7.3 | SÜMER (704 m) |
| MARAS-LOJ1 | Lojistik | Maras Fuar Alani AFAD Cadirkenti | Mustafa Yildiz (Onikisubat, Trabzon Bulvari) | YOLO | MARAS-LOJ2 -> 409 ENGELLENDI | 3555.0 | 14.2 | BARBAROS (1099 m) |
| MARAS-LOJ2 | Lojistik | Maras Fuar Alani AFAD Cadirkenti | Hakan Koc (Onikisubat, Haydarbey Mah.) | NLP | - | 3541.0 | 14.2 | MOLLA GÜRANİ (246 m) |
| MARAS-AK3 | Arama-Kurtarma | Elbistan Kriz Koordinasyon Ussu | Tolga Erdem (Elbistan, Gunesli Mah.) | YOLO | - | 1732.0 | 6.9 | KÖPRÜBAŞI (1037 m) |
| MARAS-AK4 | Arama-Kurtarma | Pazarcik Kizilay Acil Destek | Fatma Dogan (Pazarcik, Merkez Mah.) | SOS | - | 2686.0 | 10.7 | FATİH (314 m) |
| MARAS-AK5 | Arama-Kurtarma | Goksun Ileri Mudahale Noktasi | Fatma Arslan (Goksun, Ataturk Cad.) | NLP | - | 2211.0 | 8.8 | PINARBAŞI (984 m) |

> **Çakışma önleme kanıtı:** 9 mükerrer sevk denemesi yapıldı, 9 tanesi HTTP 409 ile engellendi (tamamı).


## Tablo 4 — QuakeMind vs. Klasik Navigasyon

| Ekip | Afetzede | Klasik Sure (dk) |   - yol |   - U-donusu cezasi | QuakeMind Sure (dk) | Kazanilan (dk) | U-Donusu Sayisi | Tahmini Hayatta Kalma Artisi (puan) |
|---|---|---|---|---|---|---|---|---|
| HATAY-AK1 | Ali Ozturk | 96.5 | 16.5 | 80.0 | 14.4 | 82.1 | 4 | 0.68 |
| HATAY-AK2 | Selim Kaya | 188.8 | 28.8 | 160.0 | 24.6 | 164.2 | 8 | 1.37 |
| HATAY-LOJ1 | Ahmet Yilmaz | 217.0 | 37.0 | 180.0 | 14.4 | 202.6 | 9 | 1.69 |
| HATAY-AK3 | Burak Sahin | 51.1 | 11.1 | 40.0 | 9.4 | 41.7 | 2 | 0.35 |
| HATAY-MED1 | Caner Yildiz | 32.0 | 12.0 | 20.0 | 12.0 | 20.0 | 1 | 0.17 |
| HATAY-AK4 | Emre Aydin | 4.3 | 4.3 | 0.0 | 4.3 | 0.0 | 0 | 0.0 |
| HATAY-LOJ2 | Elif Demir | 4.2 | 4.2 | 0.0 | 4.2 | 0.0 | 0 | 0.0 |
| HATAY-MED2 | Merve Sen | 47.7 | 7.7 | 40.0 | 6.8 | 40.9 | 2 | 0.34 |
| HATAY-AK5 | Sevgi Kaya | 8.4 | 8.4 | 0.0 | 8.4 | 0.0 | 0 | 0.0 |
| MARAS-AK1 | Aylin Kurt | 180.0 | 20.0 | 160.0 | 16.7 | 163.3 | 8 | 1.36 |
| MARAS-MED1 | Zeynep Celik | 113.2 | 13.2 | 100.0 | 12.4 | 100.9 | 5 | 0.84 |
| MARAS-AK2 | Serkan Tan | 352.5 | 32.5 | 320.0 | 16.9 | 335.7 | 16 | 2.8 |
| MARAS-MED2 | Derya Uysal | 27.4 | 7.4 | 20.0 | 7.3 | 20.2 | 1 | 0.17 |
| MARAS-LOJ1 | Mustafa Yildiz | 78.7 | 18.7 | 60.0 | 14.2 | 64.5 | 3 | 0.54 |
| MARAS-LOJ2 | Hakan Koc | 95.5 | 15.5 | 80.0 | 14.2 | 81.3 | 4 | 0.68 |
| MARAS-AK3 | Tolga Erdem | 27.0 | 7.0 | 20.0 | 6.9 | 20.0 | 1 | 0.17 |
| MARAS-AK4 | Fatma Dogan | 87.7 | 27.7 | 60.0 | 10.7 | 76.9 | 3 | 0.64 |
| MARAS-AK5 | Fatma Arslan | 29.0 | 9.0 | 20.0 | 8.8 | 20.2 | 1 | 0.17 |

**Toplam:** Klasik navigasyon 1641.0 dk (yalnızca hedefe ulaşabilen 18 ekip) · QuakeMind 206.6 dk (tüm 18 ekip) · **kazanılan 1434.5 dk** (%87.4). Engellenen U-dönüşü: 68. Klasik yaklaşımın **hiç ulaşamadığı** hedef sayısı: 0.


### ⚠️ Bu kazanç neyden geliyor? (ölçüm / varsayım ayrımı)

| Bileşen | Süre (dk) | Payı | Kaynağı |
|---|---|---|---|
| Salt yol uzunluğu farkı | 74.4 | %5.2 | **ÖLÇÜM** — gerçek graf üzerinde hesaplanan mesafeler |
| U-dönüşü cezası | 1360.1 | %94.8 | **VARSAYIM** — 68 keşif × 20.0 dk |
| **Toplam** | 1434.5 | %100 |  |

Sadece ölçülen mesafe farkına bakıldığında karşılaştırma **281.0 dk → 206.6 dk** (%26.5 tasarruf) olur. U-dönüşü cezası dahil edildiğinde oran %87.4'e çıkar. **Her iki rakam da raporlanmalıdır**; cezanın büyüklüğü (dakika/U-dönüşü) tartışmaya açık bir parametredir ve sonucu doğrudan belirler.


### Varsayımlar (açıkça belirtilmiştir)

- Ortalama saha ilerleme hızı: **15.0 km/s** (afet sonrası molozlu sokak).

- Kapalı yola varış başına U-dönüşü kaybı: **20.0 dk** (durma, değerlendirme, araç çevirme, telsizle bildirme). Yalnızca klasik navigasyona uygulanır; QuakeMind kapalı yola hiç varmaz.

- Naive ajanın keşif anında israf ettiği mesafe **sıfır** kabul edilir — yani karşılaştırma naive ajanın *lehine* kuruludur, abartılmamıştır.


## Model Doğrulaması (ayrı — bu koşudan bağımsız)

YOLOv8 `bina.pt` sınıfları: `0_NoDamage`, `1_ModerateDamage`, `2_VeryHeavyDamage`. Senaryo metnindeki 'Total Collapse / Major Structural' ayrımı modelde **yoktur**; tablolarda modelin gerçek sınıf adları kullanılmıştır. Görüntü havuzu: kate_pd_0_image.png, kate_pd_1_image.png (Kate-PD, doğrulanmış gerçek hasar görselleri).


### ⚠️ NLP yanlış-negatif bulgusu (ölçüm)

6 NLP ihbarının **2 tanesi** model tarafından 'afetle ilişkisiz' sayılarak elendi (`{"status":"ignored"}`) — %33.3 yanlış negatif. Elenen metinler:

- **Merve Sen** (Samandag, Ataturk Cad.): "Hatay Samandag Ataturk Caddesi'nde apartman boslugunda kanamali kazazede var, acil doktor ve ambulans!"

- **Zeynep Celik** (Dulkadiroglu, Azerbaycan Bulvari): "Kahramanmaras Dulkadiroglu Azerbaycan Bulvari'nda girste 2 kisi sikisti, yasli teyzemize oksijen tupu ve sedye lazim acil!"


Her ikisi de açıkça afet içi, hayati aciliyeti olan medikal çağrılardır. Bu, modelin gerçek ve raporlanması gereken bir sınırıdır: sahada böyle bir ihbarın elenmesi doğrudan can kaybına yol açabilir. Örneklem küçüktür (ihbar başına tek deneme); oran kesin bir başarım metriği değil, giderilmesi gereken bir bulgudur. Bu ihbarlar yine de SOS kaydına düşmüş ve ekip atanmıştır — sınıflandırma başarısızlığı sevk zincirini durdurmamaktadır.


NLP modelinin gerçek üst kategorileri (`Acil Yardım İhtiyacı`, `Enkaz Bildirimi`, `Lojistik İhtiyaç Bildirimi`, `Yol Kapanma Bilgisi / Lojistik`) senaryodaki operasyonel etiketlerle birebir aynı değildir. Tablo 1 modelin **kendi çıktısını** gösterir; ekip rolü ataması bunun üzerine kurulan ayrı bir eşleme katmanıdır.


## Etki Modellemesi — Hayatta Kalma Olasılığı

> ⚠️ **Bu bir ölçüm değil, modeldir.** Sistem süre ve mesafe ölçer; 'kaç can kurtarıldı' verisi üretmez.


Enkaz altında geçen süreye bağlı hayatta kalma olasılığı için kademeli bir eğri kullanılmıştır. Referans enkaz-altı süresi **6.0 saat** alınmış, kazanılan her dakika bu eğriye uygulanmıştır.


| Saat | Hayatta kalma olasılığı |
|---|---|
| 0.5 | %95 |
| 6.0 | %90 |
| 24.0 | %81 |
| 48.0 | %37 |
| 72.0 | %26 |
| 96.0 | %19 |
| 120.0 | %7 |


**Kaynak notu:** Macintyre, Barbera & Smith (2006), 'Time-to-Rescue' analizi buyukluk mertebesi olarak alinmistir; capa degerleri makale oncesi kaynaktan birebir dogrulanmalidir.


### Bu Eğri Nedir, Nereden Geliyor?

Afet tıbbı literatüründeki en yerleşik bulgulardan biri, enkaz altında kalan bir kişinin hayatta kalma olasılığının zamanla **doğrusal değil, basamaklı ve hızlanarak** düşmesidir. İlk saatler görece düz bir plato oluşturur; ardından ilk 24–48 saat arasında keskin bir düşüş yaşanır. Sahada 'altın saatler' (ilk 72 saat) kavramı tam olarak bu düşüşü anlatır.


Bu raporda kullanılan eğri, bu literatürün **sadeleştirilmiş, çapa noktalarına indirgenmiş bir temsilidir**. Yedi çapa noktası arasında doğrusal interpolasyon yapılır. Ana referans, yıkılmış yapılarda 'kurtarılma süresi' ile sağkalım arasındaki ilişkiyi inceleyen Macintyre, Barbera ve Smith'in (2006) çalışmasıdır; eğrinin **büyüklük mertebesi** bu çalışmadan alınmıştır.


**Hesap nasıl yapılıyor:**


1. Referans enkaz-altı süresi **6.0 saat** kabul edilir (ilk müdahale penceresi).
2. Bir ekibin kazandığı süre (Tablo 4'teki 'Kazanılan') bu referansa eklenir — yani 'QuakeMind olmasaydı afetzede ne kadar daha uzun enkaz altında kalacaktı' hesaplanır.
3. İki noktadaki hayatta kalma olasılığı farkı, o ekip için **tahmini artış** olarak raporlanır.


**Bu yaklaşımın bilinçli olarak muhafazakâr yanı:** Referans nokta olarak eğrinin en dik olduğu bölge (24–48 saat) değil, görece düz olan 6. saat seçilmiştir. Eğer afetzedelerin daha uzun süre enkaz altında kaldığı varsayılsaydı, aynı dakika kazancı çok daha büyük bir olasılık artışı üretirdi. Yani buradaki sayılar üst sınır değil, **alt sınıra yakın** tahminlerdir.


**Bu eğrinin sınırları — makalede mutlaka belirtilmelidir:**


- Çapa değerleri kaynaktan **birebir alıntı değildir**; büyüklük mertebesi temsilidir ve yayın öncesi kaynaktan doğrulanmalıdır.
- Eğri; yaş, yaralanma türü, enkaz boşluğu hacmi, sıcaklık, su erişimi gibi sağkalımı belirleyen değişkenlerin **hiçbirini** içermez.
- Çıktı bir **can sayısı değil**, olasılık puanıdır. 'X kişi kurtarıldı' şeklinde yorumlanamaz.
- Model, sistemin ölçtüğü bir büyüklük değildir; süre ölçümünün üzerine sonradan uygulanan bir yorum katmanıdır.


Toplam tahmini hayatta kalma olasılığı artışı: **11.95 yüzde puan** (tüm ekipler toplamı, yukarıdaki varsayımlar altında).


**Serkan Tan örneği:** Dulkadiroğlu'nda merdiven çökmesi sonucu mahsur kalan Serkan Tan'a gönderilen ekip, kapanmaları önceden bilmeseydi 16 kez kapalı bir sokağa varıp geri dönmek zorunda kalırdı — kazandığı 335,7 dakika, tahmini hayatta kalma olasılığını **+2,8 yüzde puan** artırıyor, koşudaki en yüksek tekil katkı. Üç sıfır-kazançlı ekip (Emre Aydın, Elif Demir, Sevgi Kaya) bu toplama hiç katkı vermiyor, çünkü onların rotasında zaten kapalı yol yoktu.


## Bilinen Kısıtlar

1. Her ekip **kendi bölgesinin** yol grafı içinde rota alır; iller arası intikal modellenmez (74 km'lik tek graf teknik olarak mümkün değil — 3 km'lik bir graf bile ~20.000 düğüm).

2. Karargâh koordinatlarının bir kısmı gerçek OSM altyapı noktasına snap edilmiştir, bir kısmı ilçe merkezine yerleştirilmiştir (senaryo kurgusu) — hangisinin hangisi olduğu veri setinde `coordSource` alanında işaretlidir.

3. Kullanıcının onayıyla iki afetzede yeniden konumlandırılmıştır (karargâh–afetzede eşleşmesini tamamlamak için); Tablo 1'de 'taşındı' notuyla gösterilir.


## Kaynakça

> **Not:** Aşağıdaki künyeler, kullanılan yöntem ve verilerin dayandığı kaynakları göstermek için derlenmiştir. Yayın öncesinde her birinin cilt/sayfa/DOI bilgisi orijinal kaynaktan doğrulanmalıdır.


**Hayatta kalma modeli**


1. Macintyre, A. G., Barbera, J. A., & Smith, E. R. (2006). *Surviving collapsed structure entrapment after earthquakes: A "time-to-rescue" analysis.* Prehospital and Disaster Medicine, 21(1), 4–17.


**Yol ağı verisi ve graf işleme**


2. OpenStreetMap katkıcıları. *OpenStreetMap Türkiye veri dökümü* (`turkey-latest.osm.pbf`). Geofabrik GmbH üzerinden erişildi. Lisans: Open Database License (ODbL) v1.0.
3. Boeing, G. (2017). *OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks.* Computers, Environment and Urban Systems, 65, 126–139.
4. Tenkanen, H. *pyrosm: Python library for reading OpenStreetMap PBF data.* Açık kaynak yazılım.
5. Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). *Exploring network structure, dynamics, and function using NetworkX.* Proceedings of the 7th Python in Science Conference (SciPy2008), 11–15.


**Rota algoritmaları**


6. Dijkstra, E. W. (1959). *A note on two problems in connexion with graphs.* Numerische Mathematik, 1(1), 269–271.
7. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). *A formal basis for the heuristic determination of minimum cost paths.* IEEE Transactions on Systems Science and Cybernetics, 4(2), 100–107.


**Yapay öğrenme modelleri**


8. Xie, E., Wang, W., Yu, Z., Anandkumar, A., Álvarez, J. M., & Luo, P. (2021). *SegFormer: Simple and efficient design for semantic segmentation with transformers.* Advances in Neural Information Processing Systems (NeurIPS) 34.
9. Jocher, G., Chaurasia, A., & Qiu, J. (2023). *Ultralytics YOLOv8.* Açık kaynak yazılım.
10. Schweter, S. (2020). *BERTurk — BERT models for Turkish.* Zenodo.


**Afet hasar verisi (projede mevcut, bu koşuda kullanılmadı)**


11. Copernicus Emergency Management Service. *EMSR648: Earthquake in Türkiye* (6 Şubat 2023 aktivasyonu), Rapid Mapping ürünleri. Avrupa Komisyonu, Ortak Araştırma Merkezi (JRC).
12. AFAD. *Türkiye Toplanma Alanları veri seti* — bu çalışmada tahliye hedeflerinin belirlenmesinde kullanılmıştır.


**Veri seti (model doğrulaması)**


13. Kate-PD — deprem sonrası bina hasarı görsel veri seti; YOLOv8 `bina.pt` modelinin bağımsız doğrulamasında kullanılmıştır.
