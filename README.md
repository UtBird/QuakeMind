# 🛸 QuakeMind — Afet İkaz, Karar Destek & Yapay Zeka Platformu

QuakeMind; deprem ve afet anlarında **internetli veya internetsiz (WiFi Hotspot / P2P Mesh)** ortamlarda çalışabilen, uydu görüntülerinden yol hasarını tespit eden, sosyal medya/saha ihbarlarından adres ve aciliyet çıkaran, deprem risk skorlarını hesaplayan ve SOS sinyallerini arama-kurtarma ekiplerine ileten bütünleşik bir afet yönetim ekosistemidir.

Proje üç ana bileşenden oluşur:

| Bileşen | Klasör | Teknoloji | Açıklama |
|---|---|---|---|
| **Web Platformu** | `quakemind-web/` | Next.js 14/15 (App Router, TypeScript) | Vatandaş ve komuta merkezi için çift portallı modern arayüz |
| **AI Backend** | `backend/` | FastAPI (Python) | NLP, risk skorlama, uydu analizi ve kamera tespiti servisleri |
| **Mobil Uygulama** | `mobile/` | Kotlin + Jetpack Compose | Room/WorkManager kullanan Android istemcisi |

Ayrıca `backend/main.py` ve `apps/` altında, backend modüllerinin tek tek Streamlit arayüzleriyle de çalıştırılabildiği bağımsız bir sürüm bulunur (geliştirme/deneme amaçlı).

---

## 📚 İçindekiler

1. [Mimari Genel Bakış](#-mimari-genel-bakış)
2. [Özellikler](#-özellikler)
3. [Repo Yapısı](#-repo-yapısı)
4. [Kurulum](#-kurulum)
5. [Çalıştırma](#-çalıştırma)
6. [Kullanım Kılavuzu](#-kullanım-kılavuzu)
7. [API Referansı](#-api-referansı)
8. [Hotspot / İnternetsiz Kullanım](#-hotspot--internetsiz-kullanım)
9. [Model Kaynakları](#-model-kaynakları)
10. [Sorun Giderme](#-sorun-giderme)
11. [Yol Haritası (Phase 2)](#-yol-haritası-phase-2)
12. [Lisans](#-lisans)

---

## 🏗 Mimari Genel Bakış

```
                          ┌──────────────────────────────┐
                          │   FastAPI AI Backend (:8000)  │
                          │  - BERTurk NLP                │
                          │  - CatBoost Risk Motoru        │
                          │  - Segformer Uydu Analizi      │
                          │  - YOLO Kamera Tespiti          │
                          └──────────────┬───────────────┘
                                         │ REST / JSON
                 ┌───────────────────────┼───────────────────────┐
                 │                                                │
     ┌───────────▼────────────┐                     ┌────────────▼────────────┐
     │  Next.js Web Platformu │                     │  Kotlin Android Uygulama │
     │  (http://localhost:3000)│                     │  (WiFi Hotspot üzerinden)│
     │  - /survivor portalı   │                     │  - Risk / Uydu / NLP     │
     │  - /command portalı    │                     │  - Kamera (yerel)        │
     └─────────────────────────┘                     └──────────────────────────┘
```

- **Online modda:** Web platformu ve backend aynı makinede veya ağda çalışır, tarayıcı üzerinden erişilir.
- **Offline/afet modunda:** Backend'in çalıştığı bilgisayar bir **WiFi Hotspot** açar, telefonlar internete ihtiyaç duymadan bu hotspot'a bağlanıp yerel ağ üzerinden backend'e erişir.

---

## ✨ Özellikler

### 🔴 Vatandaş & Afetzede Portalı (`/survivor`)
- Tek tıkla GPS destekli **SOS sinyali gönderme**
- En yakın güvenli sığınağı ve açık/kapalı yolları gösteren harita (`SafeEvacuationMap`)
- Canlı kamera ile duvar çatlağı / bina hasarı tarama (`SurvivorCameraScanner`, 60 FPS)
- Acil malzeme talebi arayüzü

### 🔵 Arama-Kurtarma & Komuta Portalı (`/command`)
- **War Room Dashboard:** Gelen SOS sinyallerinin canlı takibi ve ekip atama
- **Uydu Yol Hasarı (`/command/road-damage`):** Segformer tabanlı segmentasyon ile hasar oranı, açık/kapalı yol tespiti
- **Deprem Risk Paneli (`/command/risk`):** CatBoost ile şehir bazlı risk skoru, fay hattı ve son deprem verileri
- **Afet NLP (`/command/nlp`):** BERTurk ile sosyal medya/saha metinlerinden kategori, aciliyet (P1–P5) ve konum çıkarımı
- **Kamera Tespiti (`/command/camera`):** `catlak.pt` ve `bina.pt` YOLO modelleriyle canlı kamera veya fotoğraf yükleyerek çatlak/bina hasarı tespiti (dual mode: canlı kamera + foto yükleme)
- **SOS Yönetimi (`/command/sos`):** Gelen acil çağrıların listelenmesi ve sevk edilmesi

### 🌟 Diğer
- **Onboarding (`/onboarding`):** 3 adımlı karşılama akışı
- **Auth (`/login`, `/register`):** Rol bazlı giriş/kayıt arayüzleri
- **Tema:** Koyu (dark) glassmorphic arayüz, Tailwind CSS + Framer Motion animasyonları, Recharts grafikleri, React-Leaflet harita katmanları

---

## 📁 Repo Yapısı

```text
QuakeMind/
├── start.sh                       # Backend + frontend'i tek komutla başlatan script
├── HANDOFF.md                     # Proje bağlam/devir dokümanı
├── KULLANIM_KILAVUZU.md           # Detaylı kullanım kılavuzu (hotspot, mobil vb.)
├── PROJE_YOL_HARITASI.md          # Phase 2 yol haritası
│
├── quakemind-web/                 # Next.js web platformu
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Ana giriş / yönlendirme sayfası
│   │   │   ├── onboarding/        # Karşılama akışı
│   │   │   ├── login/             # Giriş ekranı
│   │   │   ├── survivor/          # Vatandaş portalı + /camera
│   │   │   └── command/           # Komuta portalı
│   │   │       ├── risk/          # Deprem risk paneli
│   │   │       ├── road-damage/   # Uydu yol hasarı analizi
│   │   │       ├── nlp/           # Afet metin analizi
│   │   │       ├── camera/        # YOLO kamera tespiti
│   │   │       └── sos/           # SOS sevk yönetimi
│   │   ├── components/            # map/, camera/, layout/ altında paylaşılan bileşenler
│   │   ├── context/                # React context'leri
│   │   ├── lib/                    # api.ts vb. yardımcı fonksiyonlar
│   │   └── types/                  # TypeScript tip tanımları
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/               # FastAPI AI backend
│   ├── fastapi_app.py             # Ana API sunucusu (tüm endpoint'ler burada)
│   ├── main.py                    # Bağımsız Streamlit giriş noktası
│   ├── requirements.txt
│   └── apps/
│       ├── disaster_nlp/          # BERTurk NLP pipeline
│       ├── earthquake_risk/       # CatBoost risk motoru + fay/deprem verisi
│       ├── road_damage/           # Segformer uydu segmentasyonu
│       └── camera_detection/      # YOLO (catlak.pt, bina.pt) kamera tespiti
│
└── mobile/                      # Kotlin/Jetpack Compose Android uygulaması
    ├── app/                        # Android Activity, Compose ekranları ve ViewModel'ler
    ├── core/network/               # FastAPI istemcisi ve servis sözleşmeleri
    ├── core/data/                  # Repository'ler ve veri kaynakları
    ├── core/database/              # Room yerel veri deposu
    ├── sync/                       # WorkManager eşitleme
    ├── gradlew.bat                  # Windows Gradle wrapper
    └── settings.gradle.kts
```

---

## ⚙️ Kurulum

### Ön Gereksinimler

| Gereksinim | Detay |
|---|---|
| **İşletim sistemi** | Ubuntu 24.04 (veya Windows 10+) |
| **Python** | 3.12+ |
| **Node.js** | 20+ (önerilen: `nvm` ile 24.18.0) |
| **RAM** | Minimum 8 GB (16 GB önerilir) |
| **Disk** | ~5 GB (modeller + bağımlılıklar) |
| **GPU** | Opsiyonel (CUDA destekli — uydu/kamera modülünü hızlandırır) |
| **Android** | Android Studio, JDK 17+, Android SDK 37 (mobil geliştirme) |

### 1. Backend Kurulumu

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> GPU (CUDA) ile PyTorch kurmak için:
> `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

Segformer (uydu) ve BERTurk (NLP) modelleri ilk kullanımda Hugging Face'den otomatik indirilir, elle bir işlem gerekmez (bkz. [Model Kaynakları](#-model-kaynakları)).

### 2. Web Platformu Kurulumu

```bash
cd quakemind-web
npm install
```

### 3. Mobil Uygulama Kurulumu (opsiyonel)

Android Studio ile `mobile/` klasörünü açın. Windows'ta debug APK oluşturmak için:

```powershell
cd mobile
.\gradlew.bat :app:assembleDebug
```

Emülatörde varsayılan debug backend adresi `http://10.0.2.2:8000/`'dir. Fiziksel cihazda bilgisayarın LAN/hotspot IP'sini debug derlemesine verin:

```powershell
.\gradlew.bat -PquakemindApiBaseUrl=http://192.168.137.1:8000/ :app:assembleDebug
```

Buradaki IP örnektir; bilgisayarın gerçek IP adresini kullanın. Android istemci ağ ayarları ve bağlantı sözleşmeleri `mobile/docs/` altındadır. Release derlemesi için gerçek HTTPS backend URL'si ayrıca yapılandırılmalıdır.

---

## ▶️ Çalıştırma

### Yöntem A — Tek Komutla Başlatma (önerilen)

Repo kökünde bulunan `start.sh`, backend ve frontend'i birlikte başlatır, loglarını `.logs/` klasörüne yazar ve `Ctrl+C` ile ikisini birden düzgünce kapatır:

```bash
./start.sh
```

Başarılı başlangıçta göreceğiniz çıktı:

```
Backend : http://127.0.0.1:8000   (log: .logs/backend.log)
Frontend: http://localhost:3000   (log: .logs/web.log)
Durdurmak icin: Ctrl+C
```

### Yöntem B — Ayrı Ayrı Başlatma

**Backend (FastAPI):**
```bash
cd backend
source venv/bin/activate
python3 fastapi_app.py
```
- API: `http://127.0.0.1:8000`
- Swagger/OpenAPI dokümantasyonu: `http://127.0.0.1:8000/docs`

**Web Platformu (Next.js):**
```bash
cd quakemind-web
npm run dev
```
- Arayüz: `http://localhost:3000`

**Mobil Uygulama (Kotlin / Android):**
```powershell
cd mobile
.\gradlew.bat :app:installDebug
```
Debug APK üretmek için `:app:assembleDebug`, release APK üretmek için `:app:assembleRelease` kullanın. APK konumu: `mobile/app/build/outputs/apk/debug/app-debug.apk`. Release dağıtımı için ayrıca geçerli imzalama yapılandırması gerekir.

### Yöntem C — Bağımsız Streamlit Modülleri

Backend'in her AI modülü ayrıca kendi Streamlit arayüzüyle bağımsız çalıştırılabilir:

```bash
cd backend
streamlit run main.py          # Birleşik arayüz (tüm modüller sidebar'dan seçilir)

# veya tek tek:
streamlit run apps/disaster_nlp/app.py
streamlit run apps/road_damage/app.py
python3 apps/earthquake_risk/main.py
```

---

## 🖱 Kullanım Kılavuzu

### Web Platformu Akışı

1. `http://localhost:3000` adresine gidin, karşılama (`/onboarding`) akışını tamamlayın.
2. Rolünüze göre portal seçin:
   - **Vatandaş/Afetzede (`/survivor`):** SOS gönder, güvenli tahliye rotasını gör, kamera ile çevrenizi tarayın.
   - **Arama-Kurtarma/Komuta (`/command`):** War Room dashboard üzerinden gelen SOS'ları izleyin, uydu/NLP/risk/kamera modüllerini kullanın.

### Deprem Risk Modülü (`/command/risk`)
1. Şehir seçin (81 il mevcut) veya manuel koordinat girin.
2. "Deprem Riskini Hesapla" butonuna basın.
3. Sonuçlar: risk skoru/seviyesi (Düşük/Orta/Yüksek/Çok Yüksek), fay hatları + deprem odaklarını gösteren harita, yakın faylar ve son deprem kayıtları.

### Uydu Yol Hasarı Modülü (`/command/road-damage`)
1. Şehir seçin (ör. Antakya, Kahramanmaraş, Gaziantep, Malatya, Adıyaman).
2. Uydu kaynağı seçin: **Google Maps** (güncel), **OpenAerialMap** (afet sonrası özel görüntüler), **Esri Wayback** (tarihsel görüntüler).
3. Hasar hassasiyeti (1-10), tespit eşiği (0.05-0.95) ve post-processing seviyesini ayarlayın.
4. "Analizi Başlat" — süre ~1-2 dakika (uydu indirme + AI inference).
5. Sonuçlar: hasar oranı (%), açık/kapalı yol sayısı, analiz günlüğü, önerilen aksiyon.

> Bu modül uydu görüntüsü indirmek için **internet gerektirir**.

### Afet NLP Modülü (`/command/nlp`)
1. Örnek metin seçin veya serbest Türkçe metin girin (sosyal medya paylaşımı, saha raporu vb.).
2. "Analizi Çalıştır" butonuna basın.
3. Sonuçlar: kategori (Enkaz Bildirimi / Acil Yardım / Yol Kapanma / Lojistik / Alakasız), güven skoru, P1-P5 aciliyet seviyesi, NER ile çıkarılan konum + geocoding koordinatları.

### Kamera Tespiti Modülü (`/command/camera`, `/survivor/camera`)
1. Model seçin: `catlak.pt` (duvar çatlağı) veya `bina.pt` (bina hasarı).
2. Mod seçin: **canlı kamera** veya **fotoğraf yükleme**.
3. Tespit sonuçları görüntü üzerinde işaretlenerek listelenir.

> Canlı kamera modu tarayıcı/cihaz kamerasını kullanır; fotoğraf yükleme modu backend'deki `/api/camera/analyze` endpoint'ine istek atar.

### SOS Akışı
1. Vatandaş portalından GPS ile SOS gönderilir → backend'e `POST /api/sos/alert`.
2. Komuta portalı (`/command/sos`) `GET /api/sos/alerts` ile gelen sinyalleri listeler ve ekip atar.

Daha ayrıntılı hotspot/mobil kullanım adımları için bkz. **`KULLANIM_KILAVUZU.md`**.

---

## 🔌 API Referansı

Backend `http://127.0.0.1:8000` üzerinde çalışır, tüm endpoint'ler için otomatik Swagger dokümantasyonu `/docs` altında mevcuttur.

| Endpoint | Metod | Açıklama |
|---|---|---|
| `/` | GET | Sağlık kontrolü |
| `/api/status` | GET | Modül durumu (nlp, risk, road_damage vb.) |
| `/api/nlp/analyze` | POST | Afet metni analizi (kategori, aciliyet, konum) |
| `/api/risk/predict` | POST | Şehir/koordinat bazlı deprem risk tahmini |
| `/api/risk/fault_lines` | GET | Fay hattı verisi |
| `/api/risk/all_quakes` | GET | Tüm deprem kayıtları |
| `/api/risk/refresh_live_data` | POST | Canlı deprem verisini güncelle |
| `/api/road_damage/wayback_versions` | GET | Esri Wayback görüntü sürümleri |
| `/api/road_damage/oam_search` | GET | OpenAerialMap görüntü arama |
| `/api/road_damage/analyze` | POST | Uydu görüntüsünden yol hasarı analizi |
| `/api/road_damage/route` | POST | Açık yollara göre rota hesaplama |
| `/api/road_damage/assembly` | GET | Analiz sonrası birleştirilmiş görüntü/rapor |
| `/api/sos/alert` | POST | Yeni SOS sinyali gönderme |
| `/api/sos/alerts` | GET | Gönderilmiş SOS sinyallerini listeleme |
| `/api/camera/analyze` | POST | Fotoğraf/kare üzerinde YOLO tespiti (çatlak/bina) |

### Örnek İstekler

**NLP Analizi:**
```bash
curl -X POST http://127.0.0.1:8000/api/nlp/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hatay Antakya Cebrail mahallesi yıkıldı enkaz altında kalanlar var"}'
```

**Risk Tahmini:**
```bash
curl -X POST http://127.0.0.1:8000/api/risk/predict \
  -H "Content-Type: application/json" \
  -d '{"city": "Istanbul", "refreshData": false}'
```

**Uydu Yol Hasarı:**
```bash
curl -X POST http://127.0.0.1:8000/api/road_damage/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Antakya (Hatay)",
    "latitude": 36.20,
    "longitude": 36.16,
    "source": "google",
    "damageBooster": 3.5,
    "threshold": 0.40,
    "useImagenetNorm": true,
    "postProcessLevel": 2
  }'
```

---

## 📡 Hotspot / İnternetsiz Kullanım

QuakeMind'in en kritik özelliği, **internet olmadan** da çalışabilmesidir:

```
+---------------------------+          WiFi Hotspot           +------------------+
|      BİLGİSAYAR (PC)      |  <---------------------------> |   TELEFON (App)  |
|  FastAPI Sunucu (:8000)   |        (internet gerekmez)      |  QuakeMind App   |
+---------------------------+                                 +------------------+
```

1. **Hotspot açma:**
   - Linux: `nmcli device wifi hotspot ifname <arayüz> ssid QuakeMindNet password quakemind123` → IP genelde `10.42.0.1`
   - Windows: Ayarlar > Ağ ve İnternet > Mobil Etkin Nokta → IP genelde `192.168.137.1`
2. Telefonu bu ağa bağlayın (internet gerekmez, sadece yerel ağ üzerinden iletişim).
3. Backend'i `python3 fastapi_app.py` ile başlatın (`0.0.0.0:8000` üzerinden tüm ağ arayüzlerinden erişilebilir).
4. Android istemcisinin backend adresini bilgisayarın gerçek LAN/hotspot IP'sine (`10.42.0.1:8000` veya `192.168.137.1:8000` yaygın örneklerdir) ayarlayın.
5. Aynı hotspot'a birden fazla telefon bağlanabilir; hepsi aynı backend'e erişir.

> Yalnızca uydu görüntüsü indirme ve canlı deprem verisi güncelleme gibi işlemler internet gerektirir; NLP, risk hesaplama ve kamera tespiti tamamen yerel ağda çalışır.

Detaylı adımlar (hotspot kurulumu, firewall ayarları, çoklu telefon senaryosu) için **`KULLANIM_KILAVUZU.md`** dosyasına bakın.

---

## 🧠 Model Kaynakları

Bazı büyük model dosyaları repo dışında (Hugging Face) barındırılır ve eksikse otomatik indirilir:

| Model | Kullanım | Kaynak | Otomatik indirme |
|---|---|---|---|
| BERTurk sınıflandırma | Afet NLP | `Utbird/EqTwitterTr` | ✅ |
| NER modeli | Konum çıkarımı | `yhaslan/turkish-earthquake-tweets-ner` | ✅ |
| Segformer (MiT-B4) | Uydu yol hasarı | `Utbird/dispath_optimized_mitb4_focal_dice30` | ✅ |
| YOLO `catlak.pt` | Duvar çatlağı tespiti | Repo içinde (`apps/camera_detection/models/`) | — |
| YOLO `bina.pt` | Bina hasarı tespiti | Repo içinde (`apps/camera_detection/models/`) | — |
| CatBoost risk modeli | Deprem risk skorlama | Repo içinde (`apps/earthquake_risk/models/`) | — |

Deprem risk modülü için tarihsel veri `backend/apps/earthquake_risk/data/query.csv` içinde hazır bulunur; güncel veri "Veriyi Güncelle" ile çekilebilir (internet gerektirir).

---

## 🛠 Sorun Giderme

| Sorun | Çözüm |
|---|---|
| Sunucuya bağlanamıyorum | Terminalde `Uvicorn running on http://0.0.0.0:8000` çıktısını kontrol edin |
| Telefon/tarayıcı backend'e erişemiyor | Aynı ağda olduğunuzdan ve IP/port'un doğru girildiğinden emin olun |
| Firewall engelliyor | `sudo ufw allow 8000` (Linux) veya Windows Firewall'da 8000 portunu açın |
| Port meşgul | `lsof -i :8000` ile kontrol edip gerekirse süreci sonlandırın |
| `nlp`/`risk` modülü `false` dönüyor | `curl http://127.0.0.1:8000/api/status` ile kontrol edin; eksik bağımlılık için `pip install -r requirements.txt` |
| Uydu analizi çok yavaş/başarısız | GPU + CUDA destekli PyTorch kurun; internet bağlantısını kontrol edin; daha küçük bir alan seçin |
| Web arayüzü açılmıyor | `cd quakemind-web && rm -rf node_modules .next && npm install && npm run dev` |
| Mobil uygulama derlenmiyor | `cd mobile && .\gradlew.bat :app:assembleDebug --stacktrace` (Windows); Android SDK/JDK sürümünü doğrulayın |

---

## 🚀 Yol Haritası (Phase 2)

Detaylar için `PROJE_YOL_HARITASI.md` ve `HANDOFF.md` dosyalarına bakın. Öne çıkanlar:

- **MLOps Admin Paneli (`/command/admin`):** Model versiyonlama, eğitim hiperparametreleri ve başarım metrikleri (mIoU, Dice, F1, Precision/Recall) grafikleri; sunucuyu yeniden başlatmadan model sürümü değiştirme.
- **Çift Modlu Ekip Mesajlaşma (`/command/chat`):** Online/offline (P2P Mesh, store-and-forward) taktik sohbet.
- **Kullanıcı Kayıt & Kimlik Doğrulama:** `POST /api/auth/register`, `/api/auth/login`, `/api/auth/me`.
- **Firebase Entegrasyonu:** SMS OTP ile telefon doğrulama, FCM push bildirimleri.
- **PostGIS & pgRouting:** PostgreSQL 16 + PostGIS 3 ile çevrimdışı rota hesaplama (`pgr_dijkstra`).
- **Backend Performans Optimizasyonları:** `lru_cache` önbellekleme, async paralel inference.

---

## 📄 İlgili Dokümanlar

- `HANDOFF.md` — Proje bağlam ve devir dokümanı
- `KULLANIM_KILAVUZU.md` — Hotspot/mobil odaklı ayrıntılı kullanım kılavuzu
- `PROJE_YOL_HARITASI.md` — Phase 2 mimari planlama
- `backend/README.md` — Bağımsız Streamlit modülleri için İngilizce teknik doküman
- `backend/OPTIMIZASYON_ANALIZI.md` — Backend performans analizi notları

---

## ⚖️ Lisans

Bu proje **tescillidir ve tüm hakları saklıdır** (All Rights Reserved). Açık kaynak bir lisans **değildir**.

Telif hakkı sahibinin önceden yazılı izni olmaksızın bu depodaki kodun, belgelerin, model dosyalarının veya herhangi bir materyalin kopyalanması, dağıtılması, değiştirilmesi veya herhangi bir amaçla (ticari veya değil) kullanılması **yasaktır**.

Ayrıntılar için bkz. [`LICENSE`](./LICENSE).
