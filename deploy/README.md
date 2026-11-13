# QuakeMind ev sunucusu

API: https://quakemind-api.dehaozcan.online

SSH hedefi kullanıcının yerel SSH yapılandırmasından belirlenir. Bu bilgisayarda
`home-server` alias'ı kullanılır; varsayılan sunucu kurulum kökü `$HOME/opt/quakemind`.
Bu klasör, çalışan sunucu yapılandırmasının kaynak kopyasıdır. Anahtarlar ve
veritabanları burada tutulmaz. Kurulum dosyaları sunucuya ayrıca yüklenir;
uygulama kodu yalnız `UtBird/QuakeMind` deposunun `main` dalından alınır.
Yerel geliştirme dalındaki commit edilmemiş değişiklikler dağıtılmaz.

## Dağıtım

Push/commit sonrasında otomatik dağıtım yapılmaz. Eski dağıtım servisi ve
zamanlayıcısı devre dışıdır ve mevcut sunucuda maskelenmiştir. İş akışı
`$quakemind-backend-deploy` skill'i ile yürütülür. İlk adım yerel SSH erişimi
kontrolüdür; SSH yoksa uzaktan dağıtım durur.

`deploy.sh --prepare TAM_MAIN_SHA`, temiz Git arşivinden imaj üretir ve testleri
çalıştırır. Çalışan sürüm, Nginx rotası ve kalıcı üretim verisi değişmez.
Hazırlanan imaj kimliği ve araçların SHA-256 özetleri `prepared/SHA/` altında
saklanır. Kullanıcı bu somut sonucu onaylamadan aktivasyona geçilmez.

Yalnız açık kullanıcı onayından sonra `deploy.sh --apply TAM_MAIN_SHA --approve
AYNI_TAM_SHA` çalıştırılır. Onaysız/eski komut biçimi reddedilir. Ana dal,
imaj veya dağıtım girdileri değiştiyse yeni hazırlık ve onay gerekir. Araç
önce yedek alır; sağlık/risk kontrolünden geçen yeni konteynere Nginx trafiğini
aktarır. Başarısızlıkta eski sürüm korunur veya rota geri yüklenir.
Eşzamanlı işlemler `flock` ile engellenir. CLI bayrağı bir erişim kontrolü
veya kullanıcı onayının yerine geçen bir sır değildir; onayı skill uygular.

Kaynak deponun eski `tests/test_road_damage_api.py` dosyası bağımsız
çalıştırmada başarısızdır: ısı haritası için oturumsuz 200 ve eski
`offline_fallback` kaynak adını bekler. Güncel API saha oturumu ve SQLite
verisi için `yerel_depo` kullanır. Dağıtımda bu dosyanın dört vakası
`checks/test_road_api.py` içinde güncel sözleşmeyle çalıştırılır; orijinal
dosya aynı koşuda ikinci kez toplanmaz. Bu eşleme yalnız dosyanın bilinen
Git nesne kimliği için geçerlidir; upstream dosya değişirse normal çalışır.
Diğer upstream testleri normal
çalışır. Yetki bağımlılıkları değiştirilmez. Ayrı `test_authorization.py`,
oturumsuz isteğin 401, vatandaş oturumunun 403 döndüğünü ve kayıt isteğinin
yönetici rolü seçemediğini doğrular. Upstream test düzeltmesi ana dala
alınmamıştır; ham upstream test takımının geçtiği iddia edilmemelidir.

`main` içindeki `QuakeMindBackend/` ve sonraki `backend/` klasör adları
desteklenir. Çalışan imaj commit SHA ile etiketlidir; yanıt başlığında
`X-QuakeMind-Revision` bulunur. Başarılı geçiş sonrasında önceki konteyner
durdurulur; yeniden başlatılabilir. Veritabanı şeması değişikliklerinin geri
uyumluluğu uygulama geliştiricisinin sorumluluğundadır.

Mevcut `main` risk API'si `quakemind/tool/risk_bridge.py` dosyasına da
bağlıdır. İmaj bu araçları aynı commit'ten alır ve özgün göreli klasör
yapısını korur.

```bash
git -C ~/opt/quakemind/repo fetch origin main
git -C ~/opt/quakemind/repo rev-parse origin/main
# Yukarıda görülen TAM SHA ile yalnız hazırlık:
~/opt/quakemind/deploy.sh --prepare TAM_MAIN_SHA
# Sonraki komut SADECE bu sürüm için açık kullanıcı onayından sonra:
~/opt/quakemind/deploy.sh --apply TAM_MAIN_SHA --approve AYNI_TAM_SHA
cat ~/opt/quakemind/deployed-commit
docker logs --tail 100 "$(cat ~/opt/quakemind/active-container)"
curl -i http://127.0.0.1:8086/
curl https://quakemind-api.dehaozcan.online/api/status
```

`verify.py` HTTPS, sürüm başlığı, katalog ve yetkisiz erişim kontrollerini
yapar. İsteğe bağlı `--models` kontrolü API konteynerinin içinde çalışır;
geçici bir doğrulama hesabı oluşturur, oturum/risk/NLP/kamera yollarını
gerçek modellerle sınar ve hesabı `finally` bloğunda temizler. Konumlu ihbar
veya SOS üretmez.

Docker servisleri `unless-stopped` ile çöken süreçleri yeniden başlatır.
Kullanıcı linger ayarı günlük yedeğin oturum açılmadan çalışmasını sağlar.
Kod dağıtan veya yeni commit'i kendiliğinden aktive eden zamanlayıcı yoktur.
Konteyner logları döndürülür.
API tek worker kullanır; süreç içi SSE ve iş durumu paylaşımı korunur.

## Veri ve sırlar

- `quakemind-data`: SQLite, analiz dosyaları ve Hugging Face önbelleği.
- Harita altlığı ilk dağıtımda sabit Hugging Face veri kümesi sürümünden
  `quakemind-data` içindeki `altlik/` dizinine kurulur. `prepare_basemap.py`
  katalogdaki bütün paketleri kontrol eder ve kataloğu en son yayımlar.
  Yerel üretimden gelen mevcut katalog ve dosyalar korunur.
- `quakemind-road-models`: SHA-256 ile doğrulanan uydu ağırlığı.
- `quakemind-nlp-models`: indirilen NLP ağırlıkları.
- `quakemind-ner-models`: upstream yükleyicinin ayrı `apps/models/ner`
  konumuna yazdığı NER ağırlıkları. NLP modelleri trafik geçişinden önce hazırlanır.
- `backend.env`: sunucuda üretilen sabit JWT anahtarı, Secure çerez ve CORS
  ayarları; izin `0600`. Bu dosya depoya eklenmez.
- Her dağıtımdan önce ve günlük 03:20'de SQLite backup API ile tutarlı yedek
  alınır; `~/opt/quakemind/backups` altında 14 gün saklanır. Saat sunucunun
  yerel saatidir. Analiz dosyaları ve model önbellekleri bu DB yedeğine girmez.

```bash
~/opt/quakemind/backup.sh
ls -lh ~/opt/quakemind/backups
```

Bu uygulamanın mevcut kalıcı depo sürücüsü SQLite'tır. PostGIS yapılandırılmadı;
ilgili özellikler uygulamanın mevcut çevrimdışı veri yolunu kullanır.
Üretim bağımlılıkları `requirements.txt` ile sınırlandırılır; PyTorch CPU
sürümü kullanılır. Masaüstü Streamlit ve çevrimdışı veri üreticileri imaja
girmez. Kaynak kod yeni bir bağımlılık gerektirdiğinde bu liste de güncellenip
sunucuya yüklenmelidir. `pip check` imaj oluşturulurken çalışır.

Risk CatBoost modeli Git'te tutulmadığı için `araclar_risk_egit.py`, imajın
oluşturulması sırasında depodaki CSV ve mevcut eğitim ayarlarıyla çalıştırılır.
Model, künye ve veri çerçevesi önbelleği imaja girer; API istek sırasında
eğitim yapmaz. Trafik geçişinden önce gerçek bir risk tahmini de doğrulanır.

## HTTPS ve ağ

QuakeMind için ayrı `quakemind-api` Cloudflare tüneli kullanılır.
Konteyner: `quakemind-tunnel`, yapılandırma: `tunnel.yml`; kimlik dosyası
sunucunun `.cloudflared` klasöründedir ve depoya alınmaz. Açık kaynakta yalnız
`tunnel.example.yml` şablonu bulunur; gerçek `tunnel.yml` Git dışında kalır. Nginx yalnız
`127.0.0.1:8086` üzerinden yayımlanır; API doğrudan host portu açmaz.
Ana alan adının ve diğer uygulamaların tünel yapılandırması değiştirilmez.
SSE için Nginx tamponlaması kapalıdır.

Komuta Konsolu aynı alan adında `/konsol` altında sunulur. Canlı backend ile
uyumlu Git sürümünden `konsol` ve `tasarim` klasörlerini çıkarın. `konsol`
içinde `npm ci`, `npm run kontrol` ve `npm run build` çalıştırın. `dist/`
çıktısını sunucuda `gateway/console/releases/` altında sürüme özel klasöre
yükleyin. `gateway/console/current` bağlantısını yeni sürüme yöneltin.
Nginx'in sunucu bloğu `gateway/console/console.inc` dosyasını yükler.
`docker exec quakemind-gateway nginx -t` ile doğrulayın ve Nginx'i yeniden
yükleyin. Hata halinde `current` bağlantısını önceki sürüme döndürün.
Panel ayrı derlenir. Backend sürümü için mevcut onay akışı geçerlidir.

## Kurulum dosyalarını güncelleme

Dosyaları çalışan dağıtım sırasında değiştirmeyin. `deploy.sh`, `backup.sh`,
`Dockerfile`, `requirements.txt`, `prepare_basemap.py` ve `verify.py` dosyalarını kurulum köküne ve
`test_*.py` dosyalarını `checks/` altına kopyalayın. Yalnız günlük yedek için
`quakemind-backup.service` ve `.timer` dosyalarını kullanıcı systemd dizinine yükleyin:

```bash
chmod 700 ~/opt/quakemind/{deploy,backup}.sh
bash -n ~/opt/quakemind/deploy.sh
systemctl --user daemon-reload
systemctl --user enable --now quakemind-backup.timer
```

Aynı commit'i yeniden hazırlamak için tekrar `--prepare SHA` kullanın;
`deployed-commit` dosyasını silmeyin. Yeniden aktivasyon yine yeni onay
gerektirir. DB yedeği olmadan şema düşürmeyin. Sır/JWT/SSH/Cloudflare
anahtarlarını veya veritabanı yedeklerini açık kaynak depoya eklemeyin.

## 13 Kasım 2026 kabul kaydı

- Onaysız veya farklı SHA için aktivasyon komutları reddedildi. Hazırlık
  komutu altı sunucu testini geçip çalışan konteyneri değiştirmeden sonlandı.
- Mobil/backend çalışma kopyasının ilgili 21 testi, bağımlılıkları hazır
  izole Docker ortamında geçti; üretim verisi testlere bağlanmadı. Yerel
  Python'da `networkx` eksik olduğundan bu takım o ortamda çalıştırılamadı.
- Android debug APK derlendi; app/core:data toplam 17 birim testi geçti.
  Debug ve release BuildConfig dosyalarında yeni HTTPS adresi doğrulandı.
  HTTP release ve URL içine gömülü kimlik bilgisi denemeleri reddedildi.
- Canlı HTTPS üzerinden kayıt/giriş/yenileme/çıkış, risk, NLP ve kamera
  kontrolleri geçti. Yedek bütünlük kontrolü ve önceki dağıtımdaki JWT'nin
  sürüm geçişinden sonra çalıştığı doğrulandı. Geçici hesaplar temizlendi.
- Canlı `main` OpenAPI'sinde `/api/oturum/misafir` ve
  `/api/afetzede/guvende-durumu` bulunmuyor. Yerel backend'deki mobil uyum
  değişiklikleri henüz bu sunucuda yayımlanmadı; bunun için ayrı onay gerekir.
  Mobil URL değişikliği bu iki endpoint'i kendiliğinden oluşturmaz.

Bu kayıt bir test anını belgeler; sonraki dağıtımda SSH, sürüm ve sözleşme
kontrolleri yeniden yapılmalıdır. APK cihazda bu çalışma kapsamında kurulmadı.
