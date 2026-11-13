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

Sunucu varsayılan olarak `127.0.0.1:8000` üzerinde dinler. Bilgisayarda
`http://127.0.0.1:8000/docs`, Android emülatöründe `http://10.0.2.2:8000/` kullanılır.
Fiziksel telefon için PowerShell'de başlatmadan önce `$env:QUAKEMIND_HOST = '0.0.0.0'`
ayarlayın veya Git Bash'te repo kökünden `./start.sh --telefon` çalıştırın.

## API sunucu adresi

Debug ve release varsayılanı: `https://quakemind-api.dehaozcan.online/`.
Ek bir Gradle parametresi olmadan mobil istekler bu HTTPS sunucusuna gider.

Fiziksel telefonda bilgisayarın yerel ağ IP adresini bul, telefon ve bilgisayarın
birbirine erişebildiğini doğrula ve şu komutu çalıştır:

    .\gradlew.bat :app:assembleDebug -PquakemindDebugApiBaseUrl=http://192.168.1.50:8000/

192.168.1.50 yerine gerçek bilgisayar IP adresini yaz. Emülatör için aynı
debug özelliğine `http://10.0.2.2:8000/` verilebilir. `QUAKEMIND_DEBUG_API_BASE_URL`
yalnız debug adresini değiştirir. Genel `quakemindApiBaseUrl` özelliği veya
`QUAKEMIND_API_BASE_URL` ortam değişkeni iki yapının HTTPS adresini değiştirir;
Gradle özelliği önceliklidir. URL içinde kullanıcı bilgisi, query veya fragment
kabul edilmez. Release HTTP kabul etmez; TLS sertifika kontrolü kapatılmaz.
Sunucu adresi açık kaynakta bulunabilir; parola, SSH/JWT anahtarı veya API
sırrı uygulamaya ve Gradle dosyalarına yazılmaz. Backend yayını için
`$quakemind-backend-deploy` kullanılır; push tek başına dağıtım başlatmaz.

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

Android, erişim ve yenileme jetonlarını Android Keystore anahtarıyla şifreleyerek
saklar. HTTP 401 sonrasında yenilemeyi bir defa dener ve çıkışta oturum bilgilerini
temizler. Yeni misafir hesapları IP başına dakikada beş, yeni SOS çağrıları hesap
başına on dakikada beş istekle sınırlıdır.

İhbar formu önce cihaz konumunu ister ve elle koordinat girişine de izin verir.
WorkManager, kategori, aciliyet, mahsur ve yaralı sayıları ile konum bilgilerini
kuyrukta saklar. Geçici hatada aynı Idempotency-Key ile bekleyerek yeniden dener.

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
