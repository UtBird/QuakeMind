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
| **Android** | 6.0+ (API 23+) |
| **Flutter** | 3.41+ (sadece gelistirme icin) |

---

## 2. Backend Kurulumu (Tek Seferlik)

### 2.1. Python Bagimliklarini Kur

```bash
cd /home/utku/Desktop/appdeneme/QuakeMindBackend
pip install -r requirements.txt
```

> **Not:** PyTorch GPU surumuyle kurmak icin: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

### 2.2. Segformer Modeli (Uydu Yol Hasari icin - Otomatik)

Uydu modulu ilk kullanildiginda `optimized_mitb4_focal_dice30.pth` modeli HuggingFace'den otomatik indirilir. Elle indirmek icin:

```bash
cd /home/utku/Desktop/appdeneme/QuakeMindBackend/apps/road_damage/models/
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
QuakeMindBackend/apps/earthquake_risk/data/query.csv
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
cd /home/utku/Desktop/appdeneme/QuakeMindBackend
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

### 5.1. Gelistirme Ortaminda (Flutter)

```bash
cd /home/utku/Desktop/appdeneme/quakemind
flutter run
```

### 5.2. APK Olusturma (Dagitim icin)

```bash
cd /home/utku/Desktop/appdeneme/quakemind
flutter build apk --release
```

APK konumu: `build/app/outputs/flutter-apk/app-release.apk`

Bu APK'yi telefonlara yukleyerek dagitabilirsiniz.

---

## 6. Uygulamayi Kullanma

### 6.1. Ilk Baglanti

1. Uygulamayi ac
2. **Panel** sekmesinde "Sunucu Ayari" butonuna bas
3. PC'nin hotspot IP'sini gir:
   - Linux: `10.42.0.1:8000`
   - Windows: `192.168.137.1:8000`
4. **Kaydet** butonuna bas
5. "Baglantiyi Test Et" butonuna bas
6. Yesil durum gosterilirse baglanti basarili

### 6.2. Deprem Risk Modulu

1. **Risk** sekmesine gec
2. Dropdown'dan sehir sec (81 il mevcut)
3. Opsiyonel: "Manuel koordinat kullan" ile ozel konum gir
4. **"Deprem Riskini Hesapla"** butonuna bas
5. Sonuclar:
   - Risk skoru ve seviyesi (Dusuk / Orta / Yuksek / Cok Yuksek)
   - Folium harita (fay hatlari + deprem odaklari)
   - Risk faktorleri (kisa vadeli, uzun vadeli, fay yakinligi)
   - Yakin faylar ve son deprem kayitlari
6. Harita modlari: Genel Harita / Isi Haritasi / Teknik Katman

### 6.3. Uydu Yol Hasari Modulu

1. **Uydu** sekmesine gec
2. Sehir sec (Antakya, Kahramanmaras, Gaziantep, Malatya, Adiyaman)
3. Uydu kaynagi sec:
   - **Google Maps** - En guncel, yuksek cozunurluk
   - **OpenAerialMap** - Afet sonrasi ozel goruntular
   - **Esri Wayback** - Tarihsel goruntular
4. Analiz ayarlarini yap:
   - **Hasar hassasiyeti** (1-10): Yuksek = daha fazla hasar tespit eder
   - **Tespit esigi** (0.05-0.95): Dusuk = daha hassas ama daha fazla yanlis alarm
   - **ImageNet normalizasyonu**: Genelde acik birakin
   - **Post-processing**: Guclu onerilen
5. **"Analizi Baslat"** butonuna bas
6. Bekleme suresi: ~1-2 dakika (uydu indirme + AI inference)
7. Sonuclar:
   - Hasar orani (%)
   - Acik / kapali yol sayisi
   - Analiz gunlugu
   - Onerilen aksiyon

> **Not:** Bu modul uydu goruntusu indirmek icin internet gerektirir. PC hotspot ile calisirken telefon uzerinden internet paylasimi aktifse calisir, degilse onceden indirilmis verilerle sinirlidir.

### 6.4. Afet NLP Modulu

1. **NLP** sekmesine gec
2. Ornek metin sec veya serbest metin gir
   - Turkce afet ile ilgili sosyal medya paylasimlari, saha raporlari vb.
3. **"Analizi calistir"** butonuna bas
4. Sonuclar:
   - **Kategori**: Enkaz Bildirimi / Acil Yardim / Yol Kapanma / Lojistik / Alakasiz
   - **Guven skoru**: %0-100
   - **P-5 Aciliyet**: 1 (dusuk) - 5 (kritik)
   - **Konum cikarimi**: NER ile bulunan adres + geocoding koordinatlari
   - **JSON cikti**: Ham pipeline sonucu

### 6.5. Kamera Modulu

1. **Kamera** sekmesine gec
2. Goruntu kaynagi sec (arka/on kamera)
3. Canli kamera goruntusu otomatik baslar
4. Tespit akisi listesinde anlam sonuclari goruntulenir

> **Not:** Kamera modulu yerel cihaz uzerinde calisir, backend baglantisi gerektirmez.

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

```bash
# Temiz baslangic
cd /home/utku/Desktop/appdeneme/quakemind
flutter clean
flutter pub get
flutter run
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
appdeneme/
├── QuakeMindBackend/              # Python backend
│   ├── fastapi_app.py             # Ana API sunucusu
│   ├── requirements.txt           # Python bagimliliklari
│   └── apps/
│       ├── disaster_nlp/          # BERTurk NLP pipeline
│       ├── earthquake_risk/       # CatBoost risk motoru
│       ├── road_damage/           # Segformer uydu analizi
│       └── camera_detection/      # YOLO kamera tespiti
│
└── quakemind/                     # Flutter mobil uygulama
    ├── lib/
    │   ├── main.dart              # Uygulama giris noktasi
    │   ├── screens/home_shell.dart # Ana ekran (5 sekme)
    │   ├── services/              # Backend API servisleri
    │   ├── models/                # Veri modelleri
    │   ├── widgets/               # UI bilesenleri
    │   └── data/mock_data.dart    # Sehir ve ornek verileri
    ├── android/                   # Android konfigurasyonu
    └── pubspec.yaml               # Flutter bagimliliklari
```
