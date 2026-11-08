# QuakeMind - Kullanim Kilavuzu

Afet mudahale destek sistemi. Bilgisayarda calisan yapay zeka backend'i ile mobil uygulama arasinda hotspot uzerinden internetsiz veri alisverisi yapilir.

---

## Sistem Mimarisi

```
+---------------------------+          WiFi Hotspot           +------------------+
|      BILGISAYAR (PC)      |  <---------------------------> |   TELEFON (App)  |
|                           |        (internet gerekmez)      |                  |
|  FastAPI Sunucu (:8000)   |                                 |  QuakeMind App   |
|  - NLP (BERTurk)          |   HTTP: 10.42.0.1:8000         |  - Risk Paneli   |
|  - Risk (CatBoost)        |  -----------------------------> |  - Uydu Analizi  |
|  - Uydu (Segformer)       |  <-----------------------------  |  - NLP Analizi   |
|  - Kamera modelleri       |         JSON veri               |  - Kamera        |
+---------------------------+                                 +------------------+
```

---

## 1. On Gereksinimler

### Bilgisayar (Backend)

| Gereksinim | Detay |
|---|---|
| **Isletim sistemi** | Ubuntu 24.04 (veya Windows 10+) |
| **Python** | 3.12+ |
| **RAM** | Minimum 8 GB (16 GB onerilen) |
| **Disk** | ~5 GB (modeller + bagimliliklar) |
| **GPU** | Opsiyonel (CUDA destekli - Uydu modulu icin hizlandirir) |

### Telefon (Mobil Uygulama)

| Gereksinim | Detay |
|---|---|
| **Android** | 8.0+ (API 26+) |
| **Gelistirme** | Kotlin, Jetpack Compose, JDK 17+, Android SDK 37 ve Gradle Wrapper |

---

## 2. Backend Kurulumu (Tek Seferlik)

### 2.1. Python Bagimliklarini Kur

```bash
cd backend
pip install -r requirements.txt
```

> **Not:** PyTorch GPU surumuyle kurmak icin: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

### 2.2. Segformer Modeli (Uydu Yol Hasari icin - Otomatik)

Uydu modulu ilk kullanildiginda `optimized_mitb4_focal_dice30.pth` modeli HuggingFace'den otomatik indirilir. Elle indirmek icin:

```bash
cd backend/apps/road_damage/models/
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='Utbird/dispath_optimized_mitb4_focal_dice30',
                filename='optimized_mitb4_focal_dice30.pth',
                local_dir='.')
"
```

### 2.3. NLP Modeli (Afet Metin Analizi icin - Otomatik)

BERTurk siniflandirma modeli (`Utbird/EqTwitterTr`) ve NER modeli (`yhaslan/turkish-earthquake-tweets-ner`) ilk kullanildiginda otomatik indirilir.

### 2.4. Deprem Verisi

Risk modulu icin tarihsel deprem verisi zaten mevcut:
```
backend/apps/earthquake_risk/data/query.csv
```

Guncel veri cekmek icin uygulama icinden "Veriyi Guncelle" butonu kullanilabilir (internet gerektirir).

---

## 3. Hotspot Baglantisi Kurma

### 3.1. PC Uzerinden Hotspot Acma

#### Linux (Ubuntu)

**Yontem 1 - Ayarlar:**
```
Ayarlar > Wi-Fi > sag ustteki uc nokta > Wi-Fi Hotspot Noktasini Ac
```

**Yontem 2 - Terminal:**
```bash
# Hotspot olustur
nmcli device wifi hotspot ifname wlp0s20f3 ssid QuakeMindNet password quakemind123

# Hotspot IP'ni ogren (genelde 10.42.0.1)
ip addr show | grep "10.42"
```

**Linux Hotspot IP:** `10.42.0.1` (sabit)

#### Windows

```
Ayarlar > Ag ve Internet > Mobil etkin nokta > Ac
```

**Windows Hotspot IP:** `192.168.137.1` (sabit)

### 3.2. Telefonu Hotspot'a Bagla

1. Telefonun WiFi ayarlarindan PC'nin olusturdugu agi bul (orn: `QuakeMindNet`)
2. Sifreyi gir ve baglan
3. Bu noktada telefon ve PC ayni yerel agda

> **Onemli:** Internet erisimi gerekmez. Tum islemler yerel ag uzerinden yapilir. Sadece uydu goruntusu indirme (Road Damage) ve deprem verisi guncelleme icin internet gerekir.

---

## 4. Backend Sunucusunu Baslatma

```bash
cd backend
python3 fastapi_app.py
```

Beklenen cikti:
```
Loading models...
NLP Pipeline loaded.
Risk Engine loaded.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> **Not:** NLP ve Risk modelleri yuklenirken 30-60 saniye bekleyebilir. `0.0.0.0:8000` ifadesi sunucunun tum ag arayuzlerinden erisilebilir oldugu anlamina gelir.

### Sunucuyu Dogrulama (PC'den)

```bash
# Saglik kontrolu
curl http://localhost:8000/

# Modul durumu
curl http://localhost:8000/api/status
```

Beklenen yanit:
```json
{
  "status": "ok",
  "modules": {
    "nlp": true,
    "risk": true,
    "road_damage": true
  }
}
```

---

## 5. Mobil Uygulamayi Calistirma

### 5.1. Gelistirme Ortaminda (Android Studio / Gradle)

Android Studio'da `mobile/` klasorunu acin. Windows PowerShell ile bagli
cihaza debug derlemesini kurun:

```powershell
cd mobile
.\gradlew.bat :app:installDebug
```

### 5.2. APK Olusturma (Dagitim icin)

```powershell
cd mobile
.\gradlew.bat :app:assembleDebug
```

Debug APK konumu: `mobile/app/build/outputs/apk/debug/app-debug.apk`.
Dagitim icin `:app:assembleRelease` ve release imzalama ayarlari gerekir.

Bu APK'yi telefonlara yukleyerek dagitabilirsiniz.

---

## 6. Uygulamayi Kullanma

### 6.1. Ilk Baglanti

1. Uygulamayi ac
2. Android uygulamasinin backend URL ayarini bilgisayarin LAN/hotspot IP'sine gore yapilandir:
   - Linux: `10.42.0.1:8000`
   - Windows: `192.168.137.1:8000`
3. Telefonla backend sunucusunu ayni ağa bagla. Android emulatoru kullaniyorsan
   host makine icin `10.0.2.2:8000` adresi kullanilabilir.
4. Sunucuyu `http://<sunucu-ip>:8000/api/status` uzerinden dogrula;
   yetki gerektiren islevler icin uygulamada gercek kimlik dogrulama gerekir.

### 6.2. Deprem Risk Modulu

1. Android uygulamasinda **Risk** ekranini ac.
2. Degerlendirilecek konumun gercek enlem ve boylamini gir.
3. Sunucuya `POST /api/risk/predict` istegi gonderilir.
4. Yalnizca modelin dondurdugu risk puani gosterilir. Bu skor deprem tahmini degildir.

### 6.3. Uydu Yol Hasari Modulu

Uydu yol hasari analizi backend tarafindaki `/api/road_damage/*` API'sinde
bulunur. Eski Flutter uygulamasindaki uydu kaynak secimi ve Folium ekrani
Kotlin/Compose Android uygulamasina tasinmamistir. Android'deki **Hasar Analizi**
ekrani kullanicinin sectigi fotografi `/api/afetzede/fotograf-analiz` servisine
gonderir; uydu analizinin yerine gecmez. Uydu goruntusu indirmek internet gerektirebilir.

### 6.4. Afet NLP Modulu

1. Gercek afet metnini NLP ekranina gir.
2. Analizi baslat; istek `POST /api/afetzede/metin-analiz` uzerinden gonderilir.
3. Sunucu kategori, aciliyet, guven ve varsa konum bilgisini dondurur.
4. Bir hata olursa basari yerine hata durumu gosterilir.

### 6.5. Fotografla Hasar Analizi

1. Hasar analizi ekranindan JPEG/PNG fotografini sec.
2. Gorsel sunucuda `catlak` ve/veya `bina` modeliyle analiz edilir.
3. Gercek tespitler ve guven degerleri gosterilir. Resmi bina guvenligi raporu degildir.

> **Not:** Fotograf analizi backend baglantisi ve model dosyalari gerektirir.

---

## 7. Birden Fazla Telefon Kullanma

PC hotspot'a birden fazla telefon ayni anda baglanabilir. Her telefon ayni backend sunucusuna erisir:

```
         [Telefon 1] ---+
                        |
[PC Hotspot + Backend] -+--- 10.42.0.1:8000
                        |
         [Telefon 2] ---+
                        |
         [Telefon 3] ---+
```

Her telefondaki uygulamada ayni IP ayari yapilir.

---

## 8. Sorun Giderme

### Sunucuya baglanamiyorum

| Kontrol | Cozum |
|---|---|
| Sunucu calisiyor mu? | Terminal ciktisinda `Uvicorn running on http://0.0.0.0:8000` var mi kontrol et |
| Telefon dogru aga bagli mi? | WiFi ayarlarindan PC hotspot'una bagli oldugundan emin ol |
| IP dogru mu? | Linux: `10.42.0.1:8000`, Windows: `192.168.137.1:8000` |
| Firewall engelliyor mu? | `sudo ufw allow 8000` (Linux) veya Windows Firewall'da 8000 portunu ac |
| Port mesgul mu? | `lsof -i :8000` ile kontrol et, gerekirse `kill` et |

### NLP veya Risk modulu yuklenemiyor

```bash
# Modullerin durumunu kontrol et
curl http://localhost:8000/api/status
```

Eger `"nlp": false` veya `"risk": false` ise:
- Terminal ciktisinda hata mesajina bak
- Eksik bagimlilik varsa: `pip install -r requirements.txt`
- Model dosyalari eksik olabilir (ilk calistirmada otomatik indirilir, internet gerekir)

### Uydu analizi cok yavas / basarisiz

- **GPU varsa** PyTorch CUDA surumunu kurun (10x hizlandirir)
- **Internet yoksa** uydu goruntusu indirilemez - bu modul internet gerektirir
- Timeout hatasi aliyorsaniz, daha kucuk bir alan secin

### Uygulama acilmiyor / crash

```powershell
cd mobile
.\gradlew.bat :app:assembleDebug --stacktrace
```

---

## 9. API Endpoint Referansi

| Endpoint | Metod | Aciklama |
|---|---|---|
| `/` | GET | Saglik kontrolu |
| `/api/status` | GET | Modul durumu (nlp, risk, road_damage) |
| `/api/nlp/analyze` | POST | Afet metin analizi |
| `/api/risk/predict` | POST | Deprem risk tahmini |
| `/api/road_damage/analyze` | POST | Uydu yol hasar analizi |

### NLP Analizi

```bash
curl -X POST http://10.42.0.1:8000/api/nlp/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hatay antakya cebrail mahallesi yikildi enkaz altinda kalanlar var"}'
```

### Risk Tahmini

```bash
curl -X POST http://10.42.0.1:8000/api/risk/predict \
  -H "Content-Type: application/json" \
  -d '{"city": "Istanbul", "refreshData": false}'
```

### Uydu Yol Hasari

```bash
curl -X POST http://10.42.0.1:8000/api/road_damage/analyze \
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

## 10. Dosya Yapisi

```
QuakeMinds/
├── backend/              # Python backend
│   ├── fastapi_app.py             # Ana API sunucusu
│   ├── requirements.txt           # Python bagimliliklari
│   └── apps/
│       ├── disaster_nlp/          # BERTurk NLP pipeline
│       ├── earthquake_risk/       # CatBoost risk motoru
│       ├── road_damage/           # Segformer uydu analizi
│       └── camera_detection/      # YOLO kamera tespiti
│
└── mobile/                     # Kotlin/Compose Android uygulama
    ├── app/                       # Activity, ekranlar ve ViewModel'ler
    ├── core/network/              # HTTP servis sozlesmeleri ve istemci
    ├── core/data/                 # Veri kaynaklari / repository
    ├── core/database/             # Room yerel veritabani
    ├── sync/                      # WorkManager senkronizasyon
    └── settings.gradle.kts        # Gradle modul ayarlari
```
