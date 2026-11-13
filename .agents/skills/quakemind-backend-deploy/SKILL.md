---
name: quakemind-backend-deploy
description: "QuakeMind backend'ini SSH üzerinden test edip belirli bir commit için kullanıcı onaylı dağıtım hazırlar. Backend yayını veya mobil API uyumu istendiğinde kullan; push/commit olayını dağıtım izni sayma."
---

# QuakeMind backend dağıtımı

## Önce SSH erişimini doğrula

İlk işlem, kullanıcının bilgisayarında SSH istemcisi ve yapılandırılmış sunucu
bağlantısı bulunup bulunmadığını kontrol etmektir. Yerel kurulum notları,
`QUAKEMIND_SSH_HOST` veya kullanıcının belirttiği SSH alias'ını kullan.
Bu bilgisayardaki alias `home-server` olabilir; başka bilgisayarda aynı
alias'ın veya erişimin bulunduğunu varsayma.

`ssh -o BatchMode=yes -o ConnectTimeout=10 HOST 'id -un; command -v docker'`
ile doğrula. Sunucu parmak izi güvenilir biçimde doğrulanmamışsa anahtar
denetimini kapatma. SSH istemcisi, host veya kimlik doğrulaması yoksa uzaktan
dağıtımı durdur ve eksik olanı açıkla. Parola/özel anahtar/tokenı sohbetten
isteme; yerel SSH kurulumunu kullan. Anahtarları, `.env` değerlerini veya
Docker ortam değişkenlerini yazdırma. SSH erişimi dağıtım onayı değildir.

## Kaynağı ve kapsamı belirle

`AGENTS.md` dosyalarını ve `deploy/README.md` belgesini oku. Git durumunu,
remote'u, çalışan sürümü ve ana dalın güncel tam SHA'sını incele. İlgisiz
veya commit edilmemiş değişiklikleri koru. Varsayılan kaynak temiz
`origin/main` commit'idir; çalışma ağacını gizlice yayımlama. İstenen düzeltme
ana dalda değilse bildir; commit/push/merge için mevcut kullanıcı yetkisini
kontrol et ve başka işleri birleştirme.

Backend klasörü `backend/` veya eski `QuakeMindBackend/` olabilir. Eski risk
API'sinin `quakemind/tool` köprüsünü ve CatBoost dosyasını unutma. API tek
worker kullanır. Mobil etkileniyorsa kullanılan endpoint'leri yerel testlerle
ve canlı OpenAPI sözleşmesiyle karşılaştır; yalnız URL değiştirmeyi uçtan
uca kabul testi olarak sunma.

## Test et ve incelemeye hazırla

Yerel backend testlerini mevcut Python ortamında çalıştır. Mobil değişiyorsa
ilgili Gradle testlerini/derlemesini de yap. Migration'ları, kimlik/yetki
değişikliklerini ve sırların Git'e girmediğini incele.

Sunucu kurulum kökü varsayılan olarak `$HOME/opt/quakemind` olabilir; gerçek
yolu doğrula. `deploy/` araçlarının sır içermeyen güncel kopyalarını kurulum
köküne, `test_*.py` dosyalarını `checks/` altına yükle. Çalışan bir
hazırlık/dağıtım sırasında kurulum araçlarını değiştirme.

Sunucuda yalnız `deploy.sh --prepare TAM_SHA` çalıştır. Bu temiz Git
arşivinden imaj üretir, risk modelini hazırlar ve backend/yetki testlerini
çalıştırır. Çalışan konteyneri veya Nginx rotasını değiştirmez. İmaj kimliği
ve girdi özetleri `prepared/TAM_SHA/` altında tutulur. Eski upstream test
sözleşmesiyle ilgili sınırlamayı README'den oku; başarısız veya eşlenen
testleri gizleme. Hazırlık başarısızsa aktivasyona geçme.

Kullanıcıya tam SHA'yı, değişiklik özetini, test sonuçlarını, canlı sözleşme
eksiklerini ve migration/yedek/geri dönüş risklerini bildir.

## Açık onaydan sonra aktive et

**Hazırlanan belirli sürüm için açık kullanıcı onayı gelmeden `--apply`
çalıştırma. Push, commit, skill çağrısı, sessizlik veya önceki bir sürümün
onayı yeni sürüm için onay değildir.** Onayı istemeden önce test edilmiş,
somut ve incelenebilir sonucu hazırla. Kullanıcı bekletmeni istiyorsa hazır
sürümü koru ve çalışan backend'e dokunma.

Onaydan sonra `deploy.sh --apply TAM_SHA --approve AYNI_TAM_SHA` çalıştır.
Commit, imaj kimliği veya girdiler değiştiyse yeniden hazırla ve yeni sonuç
için onay iste. `--approve` bayrağı kendi kendine yetki vermek değildir;
yalnız kullanıcının açık onayını komuta yansıtır.

Araç tutarlı DB yedeği alır, kalıcı model alanlarını hazırlar ve yeni
konteynerin sağlık/risk kontrollerinden sonra Nginx trafiğini aktarır.
Başarısızlıkta eski sürüm korunur. Mevcut JWT anahtarını/veritabanını silme
veya değiştirme. Otomatik deploy timer'ı, webhook, GitHub workflow'u veya
push tetikleyicisi kurma/açma. Günlük yedek kod dağıtımından ayrıdır.

## Canlı kabul ve güvenlik

HTTPS sertifikasını, sürüm başlığını, yetkisiz isteğin reddini, gerçek risk
tahminini, NLP/kamera analizini ve yedeğin `PRAGMA integrity_check` sonucunu
doğrula. `deploy/verify.py --models` API konteynerinde geçici hesap kullanır
ve temizler; gerçek SOS/konumlu ihbar oluşturma. Mobil kapsamındaysa gerçek
istekleri/cihazı ayrıca doğrula; APK derlemesi cihaz kabulü yerine geçmez.

Sırlar yalnız sunucudaki `0600` veya daha dar izinli dosyalarda kalır.
Public API alan adı sır değildir; APK'ya SSH/JWT/Cloudflare anahtarı koyma,
TLS doğrulamasını kapatma. Nginx yalnız loopback'te, API izole Docker ağında
kalmalı. İlgisiz sunucu servislerine dokunma.

Sonuçta değişiklikleri, kök nedeni, dosyaları, gerçekten çalıştırılan
kontrolleri, yayımlanan/onay bekleyen SHA'yı ve kalan kısıtları bildir.
