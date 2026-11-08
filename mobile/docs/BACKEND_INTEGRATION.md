# Android / FastAPI backend bağlantısı

Kotlin uygulamasında Hilt artık core/network/real/BackendServices.kt üzerinden
gerçek REST servislerini kullanır. Önceki DevService örnekleri uygulamaya bağlı değildir.

## Backend'i yerelde başlatma

Repo kökünde sanal ortamı bir kez oluşturup backend bağımlılıklarını yükle:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe fastapi_app.py
```

Sunucu `0.0.0.0:8000` üzerinde dinler; bilgisayarda `http://127.0.0.1:8000/docs`
ile açılır. Android emülatörü için aşağıdaki varsayılan adres yeterlidir. Fiziksel
telefon için aynı Wi-Fi/hotspot ağındaki bilgisayar IP adresini Gradle özelliğiyle
ver.

## API sunucu adresi

Emülatörde debug varsayılanı: http://10.0.2.2:8000/

Fiziksel telefonda bilgisayarın yerel ağ IP adresini bul, telefon ve bilgisayarın
birbirine erişebildiğini doğrula ve şu komutu çalıştır:

    .\gradlew.bat :app:assembleDebug -PquakemindApiBaseUrl=http://192.168.1.50:8000/

192.168.1.50 yerine gerçek bilgisayar IP adresini yaz. QUAKEMIND_API_BASE_URL
ortam değişkeni de desteklenir; Gradle özelliği önceliklidir. Sunucunun ağ
arayüzünde dinlemesi gerekir. Debug yapıda HTTP açık, release yapıda HTTP
kapalıdır. Release'in varsayılan URL'si kasıtlı olarak çalışmayan
https://mobile.invalid/ adresidir; yayımlamadan önce HTTPS sunucu adresi
verilmelidir. Kullanıcı parolaları veya tokenları Gradle dosyalarına yazılmamalıdır.

Windows'ta çalışma klasöründe Türkçe karakter olabildiği için
android.overridePathCheck=true Gradle özelliği ayarlanmıştır.
Windows Gradle test çalıştırıcısı buna rağmen Türkçe yol altında test
sınıflarını yükleyemeyebilir. `powershell -ExecutionPolicy Bypass -File .\\scripts\\run-windows-tests.ps1`
komutu geçici boş Q: sürücü harfini kullanır, app + core:data birim testlerini
çalıştırır ve sürücü eşlemesini her durumda temizler. Kaynak dosyaları taşınmaz.

## Bağlanan servisler

| Servis | Backend endpoint |
| --- | --- |
| Misafir, giriş, kayıt | POST /api/oturum/misafir, /giris, /kayit |
| Oturum yenileme, çıkış | POST /api/oturum/yenile, /cikis |
| Depremler | GET /api/risk/all_quakes |
| İhbar | GET ve POST /api/ihbarlar |
| NLP | POST /api/afetzede/metin-analiz |
| Fotoğraf analizi | POST /api/afetzede/fotograf-analiz |
| SOS | POST /api/sos |
| Yakın hizmetler ve AFAD alanları | GET /api/yakin-yerler |
| Yaya rotası | POST /api/afetzede/rota |
| Bölgesel risk tahmini | POST /api/risk/predict |
| Aktif bildirim | GET /api/bildirimler/aktif |
| Kişisel güvende durumu | POST /api/afetzede/guvende-durumu |
| Kapanmış yollar (saha ve üstü) | GET /api/katman/kapanmalar |

Kimlik doğrulama JSON'dan erişim jetonu ve httpOnly qm_yenileme cookie'si
alır. Android özel uygulama tercihlerinde saklar ve HTTP 401 sonrasında
yenilemeyi bir defa dener. Çıkışta oturum bilgilerini temizler.
WorkManager'ın kuyruğundaki ihbarlar aynı Idempotency-Key ile tekrar
gönderilir. Kullanıcının elle girdiği konum manuel olarak etiketlenir;
GPS etiketi yalnız gerçekten cihaz konum sağlayıcısından geldiğinde kullanılır.

Harita verisi için önce gerçek konum elde edilir ve MapRepository.refresh(location)
çağrılır. Gerçek konum bulunamazsa sahte pin veya İstanbul konumu üretilemez.
Gerçek başlangıç ve hedef olmadan rota verilemez. Rota servisi sadece yaya
yolculuğu için sağlanmaktadır. Fotoğraf analizi için gerçek JPEG/PNG Base64
gerekir; metin tarifinden kamera sonucu üretilemez.

## Mevcut kısıtlar

Push token kaydı ve iki aşamalı yükleme bileti/iptali için backend henüz
API sağlamıyor; ilgili servis metotları açık hata üretir. Aile üyesi durum
paylaşımı henüz sağlanmıyor. Kişisel güvende durumu sadece kayıt tutar,
ekiplere çağrı oluşturmaz; acil yardım talebi için ayrı SOS kullanılmalıdır.
Risk analizi yapının taşıyıcı sistem güvenliğini belgelemez.
