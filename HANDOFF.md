# 🛸 QuakeMind Proje Devir ve Bağlam Dokümanı (HANDOFF.md)

Bu doküman, **QuakeMind** projesinin mevcut mimarisini, yapılan tüm geliştirmeleri, teknik kararları, gelecek planlarını ve sohbetler arası bağlamı (context) kaybetmemek için hazırlanmış **ana rehberdir**.

---

## 📌 1. Proje Özeti ve Bağlamı (Context)

- **Proje Adı:** QuakeMind - Afet İkaz, Karar Destek & Yapay Zeka Platformu
- **Amaç:** Deprem ve afet anlarında internetli veya internetsiz (Hotspot / P2P Mesh) ortamlarda çalışan; uydudan yol hasarı tespit eden, sosyal medya mesajlarından adres ve aciliyet çıkaran, deprem risk skorlarını hesaplayan ve acil SOS sinyallerini ekiplere ileten bütünleşik afet ekosistemi.
- **Aktif Git Depoları:**
  - **Ana Depo (Upstream):** `https://github.com/UtBird/QuakeMind.git`
  - **Geliştirici Deposu (Origin):** `https://github.com/Femrei/QuakeMindDev.git`

---

## 🟢 2. Tamamlanan ve Çalışan Sistemler (Phase 1)

### 🖥️ A. Modern Next.js 15 Web Platformu (`quakemind-web/`)
- **Teknoloji:** Next.js 14/15 (App Router, TypeScript), Tailwind CSS, React-Leaflet (60 FPS GPU Harita), Shadcn UI bileşen dili, Framer Motion animasyonları, Recharts grafik kütüphanesi.
- **Erişim Adresi:** `http://localhost:3000`
- **Çift Portallı (Dual-Portal) UI/UX Mimarisi:**
  1. 🔴 **Vatandaş & Afetzede Portalı (`/survivor`):** Tek tıkla GPS destekli **Dev SOS Sinyali Gönderme**, en yakın güvenli sığınak bulma, acil malzeme talebi.
  2. 🔵 **Arama-Kurtarma & Ekip Komuta Portalı (`/command`):** War Room Dashboard, SOS Sevk & Ekip atama, Segformer uydu yol analizi, CatBoost deprem riski & fay hatları, BERTurk NLP ihbar madenciliği, Canlı kamera tespiti.
  3. 🌟 **Onboarding Akışı (`/onboarding`):** 3 adımlı karşılama simülasyonu.
  4. 🔐 **Auth Ekranları (`/login`, `/register`):** Rol bazlı giriş ve kayıt ol arayüzleri.

### ⚙️ B. FastAPI Yapay Zeka Backend (`backend/fastapi_app.py`)
- **Erişim Adresi:** `http://127.0.0.1:8000` (Swagger UI: `http://127.0.0.1:8000/docs`)
- **CORS Middleware:** Next.js (`http://localhost:3000`) erişimi için etkinleştirildi.

---

## 🚀 3. Gelecek Planlar ve Not Alınan Geliştirmeler (Phase 2 Roadmap)

### 🧠 1. Geliştirici & Admin MLOps Modülü (Model Registry & Versiyonlama)
- **Ekran:** `/command/admin` (Developer MLOps & Model Yönetim Paneli).
- **Özellikler:**
  - **Eğitim Parametreleri & Hiperparametreler:** Learning Rate, Batch Size, Epochs, Loss Fonksiyonları (Focal + Dice Loss vb.).
  - **Başarım Metrikleri Grafikleri (Recharts):** mIoU %, Dice Skoru, Accuracy %, Macro F1, Precision, Recall, Confusion Matrix.
  - **Model Versiyonlama & Geriye Dönük Seçim:** Segformer v1.0, v2.1 veya BERTurk v1.2 versiyonları arasında sunucuyu yeniden başlatmadan **canlı model sürümü değiştirme** (`POST /api/admin/models/activate`).

### 💬 2. Çift Modlu (Online / Offline P2P) Ekip Mesajlaşma Sistemi
- **Ekran:** `/command/chat` (Taktik Ekip Sohbet Konsolu).
- **İnternetsiz (Store-and-Forward):** Cihaz hafızasında saklanan mesajların Hotspot (`10.42.0.1:8000`) veya P2P Mesh menziline girince otomatik senkronize edilmesi.

### 🔐 3. Kullanıcı Kayıt & Kimlik Doğrulama (Auth System)
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` endpoints & Next.js `/register` arayüzü.

### 🔥 4. Firebase Entegrasyonu (Auth & Push Bildirimleri)
- Firebase Auth (SMS OTP ile Telefon Numarası Doğrulaması) ve FCM Canlı Push İkaz Bildirimleri.

### 🐘 5. PostGIS & Mekânsal Veritabanı Katmanı
- PostgreSQL 16 + PostGIS 3 + `pgRouting` entegrasyonu (`pgr_dijkstra` çevrimdışı rota hesabı).

### ⚡ 6. Backend Performans & Hız Optimizasyonları
- API önbellekleme (`lru_cache`), async paralel çıkarım ve JSON serialization hızlandırmaları.

---

## 💡 4. Çalıştırma Komutları

- **Web Sunucusu:** `cd quakemind-web && npm run dev` (Port 3000)
- **Backend Sunucusu:** `cd backend && venv\Scripts\python.exe fastapi_app.py` (Port 8000)
