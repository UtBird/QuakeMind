# QuakeMind Backend — Optimizasyon ve Mimari Analiz Raporu

> **Revizyon notu:** Bu dokümanın ilk versiyonu backend'i "bir yerlerde çalışan Python
> servisi" varsayımıyla incelemişti. Asıl dağıtım hedefinin **Raspberry Pi** olduğu,
> Pi'nin hem **kendi WiFi yayınıyla (AP modu) yakındaki telefonlara offline hizmet**
> vereceği hem de **internet üzerinden merkezi bir sunucuya bağlı** çalışacağı ve amacın
> "afet öncesi/sonrası, internet olsun olmasın kullanıcıya hizmet" olduğu öğrenilince,
> tüm rapor bu bağlamda yeniden değerlendirildi. Madde numaraları korunmuştur (birebir
> referans vermeye devam edebiliriz); ilgili maddelerin altına **"📡 Pi/Offline Notu"**
> eklendi, yeni bölümler (9-12) eklendi, öncelik sırası bu gerçeğe göre yeniden yazıldı.

> **Revizyon notu 2 (donanım gerçeği):** Şu an elimizde fiziksel bir Raspberry Pi yok.
> **Nihai dağıtım hedefi hâlâ Pi** — bu değişmedi — ama geliştirme, test ve arayüz
> çalışması gerçekte **PC üzerinden** yürütülmek zorunda. Bu, raporun Pi'ye özgü
> donanım varsayımlarının (ARM mimarisi, kısıtlı RAM, SD kart I/O, GPU yokluğu, headless
> çalışma) bir kısmının **şu an fiilen doğrulanamadığı, ertelendiği** anlamına geliyor.
> Bu nedenle rapor artık iki fazlı okunmalı:
> - **Faz 1 (şimdi — Pi yok, PC üzerinde geliştirme/arayüz):** Donanımdan bağımsız
>   mimari kararlar (offline-first tasarım, senkronizasyon/outbox, özellik matrisi,
>   kod tekrarının giderilmesi, model persist etme) aynen geçerli ve **şimdi**
>   ilerletilebilir/ilerletilmeli. Buna karşılık Pi'ye özgü donanım kısıtları (Bölüm 10)
>   ve bunlara dayanan kararlar (ör. madde 18'deki kuantizasyon kararı, madde 23'teki
>   ARM wheel doğrulaması) **PC'de test edilemez**, tahmine dayalı kalır ve gerçek
>   donanım gelene kadar ⚠️ **"doğrulanamadı"** olarak işaretlenmelidir.
> - **Faz 2 (Pi temin edildiğinde):** Bölüm 10'daki tüm ölçümler (madde 34) ve buna bağlı
>   kararlar gerçek donanımda tekrar doğrulanmalı; PC'de alınmış hiçbir performans/RAM
>   sonucu Pi için "kanıt" sayılmamalı, sadece yön gösterici bir taban çizgi (baseline)
>   olarak kullanılmalı.
> Faz 1/Faz 2 ayrımının pratik sonucu Bölüm 0 ve Bölüm 12'de somutlaştırıldı (özellikle
> "PC üzerinde hangi arayüzle ilerleyeceğiz" sorusuna Bölüm 12'de doğrudan cevap var).

Durum lejantı: 🔴 Kritik · 🟠 Önemli · 🟡 Orta · ⚪ Düşük · **Durum:** Bekliyor / Devam Ediyor / Tamamlandı / Reddedildi

---

## Bölüm 0 — Dağıtım Bağlamı (yeni: bunu bilmeden yapılan her analiz eksik kalır)

**Hedef mimari (konuşmamızdan çıkardığım özet — yanlışsa düzelt):**

```
                     ┌─────────────────────────┐
                     │   Merkezi Sunucu (Cloud) │  ← internet varsa senkron
                     │  (tüm Pi'lerden veri     │
                     │   toplar, model/veri     │
                     │   günceller, koordinasyon)│
                     └────────────┬─────────────┘
                                  │ internet (aralıklı, garantisiz)
                    ┌─────────────┴─────────────┐
                    │                           │
             ┌──────▼──────┐             ┌──────▼──────┐
             │ Raspberry Pi │             │ Raspberry Pi │   ← afet bölgesinde
             │  (Bölge A)   │             │  (Bölge B)   │     saha ekipmanı
             │ WiFi AP+FastAPI            │ WiFi AP+FastAPI
             └──┬───────┬──┘             └─────────────┘
                │       │
          ┌─────▼──┐ ┌──▼─────┐
          │Telefon 1│ │Telefon 2│  ← hotspot'a bağlanan afetzedeler/gönüllüler
          └────────┘ └────────┘
```

Bunun kod/mimari üzerindeki etkileri, aşağıdaki maddelerde tek tek işleniyor, ama
üst düzey ilkeler şunlar:

1. **"Offline-first" bir zorunluluk, opsiyon değil.** Pi, internet olmadan da bölgesindeki
   telefonlara tam hizmet verebilmeli (madde 3, 16, 21, 33 ile ilişkili).
2. **Raspberry Pi = sınırlı CPU/RAM, GPU yok, ARM mimarisi, SD kart I/O yavaş/aşınmaya
   hassas.** Şu ana kadarki analiz büyük ölçüde "geliştirici PC'sinde x86_64 + muhtemelen
   GPU" varsayımıyla yapılmıştı — bu artık geçersiz (bkz. Bölüm 10).
3. **Streamlit, bu senaryoda yanlış araç.** Hem kaynak ağırlığı hem çoklu-kullanıcı
   modeli (her tarayıcı sekmesi = ayrı tam Python script rerun'u) Pi'de birden fazla
   telefonun aynı anda bağlandığı bir ortamda ciddi darboğaz (bkz. Bölüm 12 — somut
   öneri var).
4. **Senkronizasyon mimarisi eksik/hiç düşünülmemiş.** Şu an kod, "internet var" veya
   "internet yok" ikiliğini bazı yerlerde (offline OSM modu) ele alıyor ama "internet
   geldiğinde merkezi sunucuyla veri alışverişi yap" diye bir mekanizma hiç yok
   (bkz. Bölüm 9 — yeni).
5. **(yeni) Pi şu an elimizde yok — geliştirme/arayüz PC üzerinden ilerliyor, ama hedef
   değişmedi.** Yukarıdaki diyagram hâlâ *nihai* mimari. Ama "Raspberry Pi" kutusunun
   yerine bugün fiilen bir **geliştirici PC'si** koyup ilerlemek zorundayız — WiFi AP
   yayını, ARM CPU, kısıtlı RAM/SD kart gibi Pi'ye özgü unsurlar PC'de ya hiç yok ya da
   çok farklı davranıyor. Bu maddelerin her biri aşağıda tek tek işleniyor; kısa özet:
   **mimari/yazılım kararları (offline-first, senkron, kod tekrarının giderilmesi) şimdi
   de geçerli ve ilerletilmeli; donanım-bağımlı kararlar (Bölüm 10, madde 18/23) Pi
   gelene kadar "doğrulanamadı" statüsünde bekler.** PC'de hangi arayüzle çalışılacağı
   sorusunun somut cevabı **Bölüm 12**'de.

---

## Bölüm 1 — Kritik: Şu an gerçekten kırık veya çalışmayan şeyler

### 1. 🔴 Kamera Tespiti modülü `ultralytics` eksikliğinden çöküyor
**Durum:** Bekliyor
Kök `requirements.txt` içinde `ultralytics` hiç yok, ama `apps/camera_detection/camera_manager.py`
`from ultralytics import YOLO` import ediyor ve hem `main.py` (unified arayüz →
"Kamera Tespiti" sekmesi) hem `apps/camera_detection/app.py` bunu çağırıyor. Şu an kurulu
venv'de doğruladım: `import ultralytics` → `ModuleNotFoundError`.
**Öneri:** `ultralytics`'i kök `requirements.txt`'e ekle (versiyon pinle, madde 23).
**📡 Pi/Offline Notu:** İki YOLO modelini gerçek zamanlı Pi CPU'sunda aynı anda
koşturmak muhtemelen gerçekçi değil; Pi'de gerçekten kullanılabilir olup olmadığı
madde 34'teki gerçek donanım ölçümü olmadan bilinemez.
**💻 Faz 1 (PC) notu:** Bu madde Pi'yi beklemeden **şimdi** çözülebilir/çözülmeli —
`ultralytics` eksikliği Pi'ye özgü bir sorun değil, PC'deki venv'de de kırık. PC'de
(muhtemelen daha güçlü CPU, belki GPU) iki YOLO modelini aynı anda koşturmanın hiç
sorun çıkarmaması olası, bu da "Pi'de olur mu" sorusunu ayrıca **belirsiz** bırakır —
PC'de çalışması Pi'de çalışacağının kanıtı değildir. Paketi ekleyip PC'de geliştirmeye/
teste devam et; Pi'ye özgü "ikisi aynı anda gerçek zamanlı sığar mı" kararını madde 34
ile ertele.

### 2. 🔴 Earthquake Risk masaüstü GUI'si (`customtkinter`) kök requirements'ta yok
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bu madde Pi *dağıtımı* için **önemsiz/kaldırılabilir** kalıyor —
`customtkinter` bir masaüstü (X11/Wayland) GUI kütüphanesi, Pi başsız çalışacaksa bu
GUI'nin Pi'de hiç çalıştırılma ihtimali yok. `apps/earthquake_risk/gui_app.py` +
`main.py` (tkinter giriş noktası) **Pi'ye giden `requirements.txt`'e hiç girmemeli.**
**💻 Faz 1 (PC) notu:** Ama Pi yokken çalıştığımız yer zaten PC — yani bu madde şu an
"kaldır" değil, "kök `requirements.txt`'ten ayır" maddesi olarak okunmalı. `customtkinter`
(ve varsa diğer sadece-PC bağımlılıkları) `requirements-dev.txt`'e taşınmalı; böylece
(a) geliştirici PC'sinde bu GUI hâlâ çalışır ve debug/demo için kullanılabilir, (b) kök
`requirements.txt` şimdiden Pi'ye gidecek "temiz" listeye yaklaşır. Bu ayrım, madde 24
ve Bölüm 12'deki karara doğrudan bağlı — orada nihai olarak hangi arayüzün Pi'ye,
hangisinin sadece PC'ye ait kalacağı netleştiriliyor.

### 3. 🔴 `QUAKEMIND_OFFLINE_ONLY` process-genelinde global env var — çoklu kullanıcıda birbirini eziyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bu madde artımızda kritik seviyeye çıktı. Pi senaryosunda
"offline mi online mu" **her istekte otomatik algılanması gereken bir sistem durumu**
olmalı — kullanıcının elle işaretlediği bir checkbox değil. Bir telefon hotspot'a
bağlanıp uygulamayı kullanırken Pi'nin internet'i gidip gelebilir (mobil şebeke/uydu
üzerinden aralıklı bağlantı gibi düşünülebilir). **Öneri (genişletildi):**
- Global env var'ı tamamen kaldır.
- Pi'de arka planda çalışan basit bir "connectivity monitor" (ör. her 15-30 saniyede
  bir bilinen bir merkezi sunucu endpoint'ine ping/HEAD isteği) internet durumunu bir
  paylaşılan duruma (in-memory + gerekiyorsa `/api/status`'ta expose edilen bir alan)
  yazsın.
- Her istek bu anlık durumu okusun, kullanıcı bir şey işaretlemek zorunda kalmasın
  ("Offline OSM modu" checkbox'ı "zorla offline'a geç" anlamına gelen bir override'a
  dönüşebilir, varsayılan davranış otomatik olmalı).

### 4. 🔴 Aynı Python modülü iki farklı "qualified name" ile import ediliyor → state paylaşılmıyor, model iki kez yüklenebilir
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Pi'de RAM son derece kısıtlı (bkz. Bölüm 10) — aynı Segformer
modelinin **iki kez** belleğe yüklenmesi ihtimali, x86_64 geliştirici makinesinde
"israf ama tolere edilebilir" iken Pi'de **OOM (out-of-memory) kilitlenmesine** yol
açabilecek somut bir risk haline geliyor. Bu maddenin önceliği yükseldi.

### 5. 🔴 Risk motoru (CatBoost) ilk `/api/risk/predict` isteğinde senkron eğitiliyor — diğer modüller gibi ön-ısıtılmıyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Pi CPU'su (ör. Cortex-A72/A76, GPU yok) geliştirici PC'sinden
kat kat yavaş. 800 iterasyonluk CatBoost eğitimi + declustering/label-building
(madde 16'daki O(n·k) döngüler) Pi'de saniyeler değil **onlarca saniye/dakikalar**
sürebilir. Bu, ilk kullanıcıyı (belki de afet anında acil bir sorgu yapan biri) uzun
süre bekletir. **Öneri güçlendirildi:** Sadece "açılışta eager çağır" yetmez —
**eğitilmiş modeli Pi imajına önceden gömülü olarak dahil et** (bkz. madde 15 ve
Bölüm 9), Pi ilk açılışında sıfırdan eğitim yapmasın.

### 6. 🔴 `nlp_bridge_server.py` (port 8766) muhtemelen kullanılmayan, unutulmuş ikinci bir NLP sunucusu
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Pi'de her MB RAM ve her CPU cycle değerli — kullanılmayan bir
BERT modeli instance'ının yanlışlıkla ayağa kalkması (ör. bir systemd servisi olarak
otomatik başlatılırsa) Pi'nin kaynaklarının önemli bir kısmını boşuna tüketebilir.
**Öneri:** Sadece kod tabanından silmek yetmez — Pi provisioning/deployment script'lerinde
(varsa) bu servisin hiçbir yerde systemd unit/autostart olarak tanımlanmadığından emin ol.

---

## Bölüm 2 — Mimari: Kod tekrarı ve tutarsızlık

### 7. 🟠 Aynı iş mantığı 3-4 yerde birbirinden bağımsız kopyalanmış
**Durum:** Bekliyor
(İçerik değişmedi — bkz. önceki analiz.)
**📡 Pi/Offline Notu:** Pi'ye kod deploy ederken (muhtemelen `git pull` + servis
restart şeklinde bir dağıtım olacak) her kopyanın senkron kalması gerekiyor — sahada,
internet kısıtlı bir Pi'ye "hatalı/eksik güncellenmiş" bir kopya gitme riski, ofis
ortamındaki bir sunucudan çok daha maliyetli (saha ziyareti gerektirebilir). Bu tek
başına, kod tekrarını **acilen** ortadan kaldırmak için ekstra bir gerekçe.

### 8. 🟠 `main.py` (unified Streamlit) açılışta TÜM modelleri eager-load ediyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bölüm 12'deki karara bağlı olarak muhtemelen tamamen
**tartışmasız hale gelecek** — Streamlit prod'dan kalkarsa bu madde de kendiliğinden
çözülür. Ama FastAPI tarafında da benzer bir prensip geçerli: Pi'nin RAM bütçesi
muhtemelen "4 modülün hepsini aynı anda belleğe almaya" yetmeyebilir (Bölüm 10).
Prod FastAPI için de **modül bazlı lazy-load + LRU tahliye** (kullanılmayan modelin
belirli bir süre sonra bellekten atılıp tekrar gerektiğinde yüklenmesi) değerlendirilmeli.

### 9. 🟠 main.py / fastapi_app.py / apps/*/app.py — üç paralel "gerçek backend" adayı, hangisi asıl belli değil
**Durum:** Bekliyor
**📡 Pi/Offline Notu (karar netleşti):** Artık netlik var — **Pi'ye deploy edilecek
tek şey `fastapi_app.py` (+ ortak iş mantığı modülleri) olmalı.** Streamlit dosyaları
(`main.py`, `apps/*/app.py`) ve tkinter GUI (`apps/earthquake_risk/gui_app.py`)
Pi imajına hiç dahil edilmemeli — sadece geliştirici masaüstünde model/algoritma
denemesi için bir `dev-tools/` klasörüne taşınmalı. Bkz. Bölüm 12 için Streamlit'in
tam olarak neyle/nasıl değiştirileceği.

### 10. 🟡 `main.py`'daki road_damage ekranı, `apps/road_damage/app.py`'den geride
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Madde 9 kararı uygulanırsa (Streamlit prod'dan kalkarsa) bu
madde otomatik olarak anlamsızlaşır — ekstra iş gerektirmez.

---

## Bölüm 3 — FastAPI performans / eşzamanlılık

### 11. 🟠 Sync endpoint'ler + `reload=True` + tek worker
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Pi'de `reload=True`'nun dosya-izleme overhead'i, zaten kısıtlı
CPU'da orantısız pahalı. Ayrıca "kaç worker" sorusu Pi'de dikkatli düşünülmeli: çok
worker açmak (her biri kendi model kopyasını RAM'e yüklerse) RAM'i katlar; **tek worker
+ CPU-bound işler için ayrı bir process havuzu** (ör. `ProcessPoolExecutor`, sadece
inference için, modelin kendisi ana process'te bir kez yüklü kalacak şekilde
paylaşılan bellek/IPC ile) muhtemelen Pi'de "N worker" yaklaşımından daha az bellek
yakar. Ayrıca **backpressure şart:** Pi aynı anda 10-20 telefonun isteğini
karşılayamayabilir; sınırı aşan istekleri 503/429 ile nazikçe reddet, sunucuyu
çökertme/thermal-throttle'a sürükleme.

### 12. 🟠 Aynı bbox için OSM verisi iki ayrı yoldan iki kez çekiliyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Online modda gereksiz ağ trafiği zaten kötüydü; offline modda
(local `roads.gpkg` okuma) bu iki kez **SD kart I/O** demek — SD kart hem yavaş hem
sınırlı yazma/okuma ömrüne sahip. Tek okumaya indirmek burada iki kat önemli.

### 13. 🟠 Satellite tile indirme seri (sıralı) yapılıyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bu özellik **sadece internet varken anlamlı** (uydu görüntüsü
indirme). Paralel indirme önerisi geçerliliğini koruyor ama daha önemlisi: bu tür
"sadece online'da işe yarayan" özellikler kod içinde **açıkça** işaretlenmeli
(bkz. madde 33 — yeni, "özellik matrisi") ki offline modda kullanıcıya "şu an bu
özellik yok" net biçimde söylensin, sessizce/yarım hata vermesin.

### 14. 🟡 Hata detayları (`str(e)`) doğrudan istemciye sızdırılıyor
**Durum:** Bekliyor
(Pi bağlamı bu maddeyi değiştirmiyor, öneri aynı kalıyor.)

---

## Bölüm 4 — Model / Inference optimizasyonu

### 15. 🟠 CatBoost modeli diske persist edilmiyor, her process açılışında sıfırdan eğitiliyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Artık sadece "performans iyileştirmesi" değil, **dağıtım
gereksinimi**: Eğitilmiş `model.cbm` dosyası, Pi'nin SD kart imajına (veya provisioning
adımında) **önceden yerleştirilmiş** olarak gelmeli. Pi ilk açıldığında (belki hiç
internet olmadan) modelin zaten hazır olması gerekiyor — sıfırdan eğitim, hem yavaş
hem "ilk kurulumda internet lazım mı?" gibi gereksiz bir bağımlılık yaratıyor
(veri `query.csv` da yerelde gömülü olmalı zaten, bkz. Bölüm 9).

### 16. 🟠 `query.csv` hiç budanmıyor — declustering/label üretimi zamanla yavaşlar
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** SD kart I/O ve sınırlı RAM göz önüne alınca bu daha da önemli:
(a) CSV yerine **SQLite** kullan (tek dosya, indeksli, kısmi okuma yapılabilir, flat
CSV'yi her seferinde tamamen belleğe okumak zorunda kalmazsın); (b) periyodik olarak
(ör. cron/systemd timer ile, düşük öncelikli bir arka plan görevi olarak — Pi'nin CPU'su
meşgulken değil) eski veriyi arşivle; (c) declustering/label üretimini **sadece Pi'ye
ilk kurulumda / cloud'da bir kez** çalıştırıp sonucu (hazır eğitilmiş model + işlenmiş
feature tablosu) Pi'ye dağıtmayı düşün — Pi'nin bunu kendi başına yeniden hesaplaması
hiç gerekmeyebilir (bkz. Bölüm 9, "cloud'da eğit, Pi'ye dağıt" modeli).

### 17. 🟠 `_nearest_graph_node` (local_osm.py) tüm graph düğümlerini O(n) lineer tarıyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bu, tam olarak "offline modda Pi'nin CPU'suna en çok yük
bindirecek" türden bir fonksiyon — internet yokken (yani KDTree'ye en çok ihtiyaç
duyulacağı an) devrede. Öncelik yükseltildi.

### 18. 🟡 GPU/CPU inference'ta fp32 kullanılıyor, fp16/autocast değerlendirilmemiş
**Durum:** Bekliyor
**📡 Pi/Offline Notu (önemli revizyon):** Pi'de **GPU/CUDA yok**, dolayısıyla
`torch.autocast("cuda", ...)` önerisi bu bağlamda **geçersiz**. Asıl yapılması gereken:
- **INT8 kuantizasyon + ARM'a özel bir runtime**: `onnxruntime` (ARM64 için resmi
  wheel'leri var) veya `openvino` (Intel dışı ARM desteği sınırlı, dikkatli
  değerlendirilmeli) ya da YOLO modelleri için `ncnn`/`TFLite` export'u — bunlar Pi'de
  saf PyTorch CPU inference'ından kayda değer ölçüde (2-4x) hızlı olabiliyor.
- Segformer (mit_b4 encoder, patch-based 512x512 + %50 overlap) gibi ağır bir model
  Pi CPU'sunda muhtemelen **tek görüntü için onlarca saniye** sürecektir — gerçek Pi
  donanımında erken bir benchmark şart (bkz. Bölüm 10, madde 31).
- BERTurk sınıflandırma + NER modelleri için `distilbert`/daha küçük bir Türkçe model
  varyantına geçmek (mümkünse) veya mevcut modeli `optimum`/ONNX ile kuantize etmek
  ciddi kazanç sağlar.
**💻 Faz 1 (PC) notu:** Bu maddede **dikkat edilmesi gereken bir tuzak** var: eğer
geliştirme PC'sinde GPU varsa, `torch.autocast("cuda", ...)` PC'de gerçekten işe
yarar ve cazip görünebilir — ama bu kazanım **Pi'ye taşınmaz** (Pi'de CUDA yok).
PC'de "GPU ile hızlandırdık" diye rahatlayıp bu maddeyi kapatılmış saymayın; Pi için
tek geçerli yol yukarıdaki ONNX/ncnn/TFLite + INT8 kuantizasyon hattı. Şimdiden
yapılabilecek: ONNX export adımlarını PC'de (CPU modunda, GPU'suz) deneyip modelin
doğruluğunu (accuracy/mAP farkı var mı) PC'de doğrulamak — bu, Pi'ye özgü hız kazancını
ölçmez ama "kuantize model hâlâ doğru tahmin ediyor mu" sorusunu donanımdan bağımsız
şimdi cevaplar.

### 19. 🟡 Zeyrek lemmatization kelime bazlı cache'lenmiyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Pi CPU'sunda her cycle değerli — bu ucuz ve kolay bir kazanım,
Pi bağlamında önceliği hafifçe yükseldi (düşük efor / yüksek+ kazanç oranı iyi).

### 20. 🟡 Nominatim rate-limit + çok sayıda query varyasyonu → analiz gecikmesi ve ban riski
**Durum:** Bekliyor
**📡 Pi/Offline Notu (kritik ek):** Nominatim **internet gerektirir** — offline modda
bu adım tamamen devre dışı kalmalı ve **yerel bir geocoding tablosuna** (il/ilçe/mahalle
merkez koordinatları — zaten `tr_locations.py`'de il/ilçe isim listesi var ama
koordinat yok, bunu eklemek gerekiyor) düşmeli. Bu, hem online'daki Nominatim
ban/gecikme riskini azaltır hem de **offline çalışmayı gerçekten mümkün kılar** —
şu anki haliyle offline modda NLP pipeline "konum bulamadı" diye boş dönecektir,
bu da temel bir kullanılabilirlik eksikliği.

---

## Bölüm 5 — Dış servis güvenilirliği

### 21. 🟡 Overpass cache'i sadece process-memory'de, disk'e yazılmıyor
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Bu maddenin çözümü artık **zorunlu ön-koşul**: Pi'ye
dağıtılmadan önce, hedeflenen bölgeler (Hatay, Kahramanmaraş, Gaziantep, Malatya,
Adıyaman — kodda zaten bu 5 şehir hardcoded) için Overpass/OSM verisi **önceden
indirilip Pi imajına gömülmeli** (`build_local_osm_dataset.py` / `download_cities_osm.py`
/ `download_turkey_overpass.py` script'leri tam olarak bunun için var, ama bunların
"Pi provisioning pipeline"ının resmi bir parçası olması gerekiyor, elle bir kerelik
çalıştırılan yardımcı script olarak kalmamalı — bkz. Bölüm 9).

### 22. 🟡 Dış servis çağrılarında tutarlı retry/backoff yok
**Durum:** Bekliyor
(Pi bağlamı önceliği değiştirmiyor, öneri aynı.)

---

## Bölüm 6 — Bağımlılık yönetimi

### 23. 🟠 Hiçbir requirements.txt'te versiyon pin'i yok
**Durum:** Bekliyor
**📡 Pi/Offline Notu — bu madde artık 🔴 KRİTİK'e yükseltilmeli:** Windows'ta
`cykhash` derleme hatasıyla bizzat karşılaştığımız şeyin **aynısı, çok daha yüksek
ihtimalle Raspberry Pi'nin ARM64 (aarch64) mimarisinde de yaşanır.** PyPI'da birçok
paketin (özellikle bilimsel hesaplama/geo yığını: `numpy`, `pandas`, `scipy`,
`shapely`, `pyproj`, `opencv-python`, `torch`) x86_64 için hazır wheel'i olsa da
ARM64 için ya hiç yok ya da farklı/eski bir sürümde var — bu da Pi üzerinde
**saatlerce süren kaynak derlemesi denemeleri veya doğrudan kurulum hatası**
anlamına gelir (SD kart + sınırlı RAM ile derleme büyük ihtimalle pratik değil/
imkânsız). Özellikle **PyTorch**, Raspberry Pi için resmi PyPI yerine
`https://download.pytorch.org/whl/cpu` gibi ayrı bir index'ten veya topluluk
(`piwheels.org` — Raspberry Pi'ye özel önceden derlenmiş wheel deposu) üzerinden
kurulmalı.
**Öneri (genişletildi):**
- Sürüm pinlemeyi Pi'de **fiilen test edilmiş** bir sürüm setiyle yap (masaüstünde
  çalışan sürümler değil).
- `pip install` öncesi **piwheels.org**'u ek index olarak kullanmayı değerlendir
  (`--extra-index-url https://www.piwheels.org/simple`), birçok ağır paket için
  ARM'a özel önceden derlenmiş wheel sağlıyor.
- Pi imajını "altın imaj" (golden image) olarak hazırlayıp SD kart klonlamak,
  her Pi'de sıfırdan `pip install` yapmaktan çok daha güvenilir olur (bkz. Bölüm 9).
- **Bunu erken bir aşamada, gerçek bir Raspberry Pi üzerinde bizzat doğrula** —
  şu an bu risk teorik, ama masaüstünde her şey "sorunsuz" göründüğü için Pi'ye
  geçilene kadar fark edilmeme ihtimali yüksek (tıpkı Windows/cykhash gibi).
**💻 Faz 1 (PC) notu:** Pi olmadan bu maddenin "doğrulama" kısmı **yapılamaz** —
piwheels.org'ta bir paketin ARM64 wheel'inin var olup olmadığı web üzerinden kontrol
edilebilir (bu bir ön-araştırma, gerçek kurulum testi değil) ama "gerçekten kurulur mu,
gerçekten çalışır mı" sorusunun tek cevabı fiziksel/emüle Pi'de `pip install` denemek.
Şimdiden yapılabilecekler: (a) hedef paket listesini (`numpy`, `pandas`, `scipy`,
`shapely`, `pyproj`, `opencv-python`, `torch` + versiyonları) netleştirip piwheels.org'ta
tek tek ARM64 desteğini web'den kontrol ederek bir ön-risk listesi çıkar; (b) alternatif
olarak QEMU ile ARM64 emülasyonu (`docker run --platform linux/arm64`) üzerinden bir
kurulum denemesi yapılabilir — bu gerçek Pi'nin yerini tutmaz ama en azından "wheel yok,
kaynaktan derleme gerekiyor" tespitini Pi gelmeden önce yakalayabilir ve saha ziyareti
riskini azaltır.

### 24. 🟡 4 ayrı requirements.txt birbiriyle senkron değil, "kaynak of truth" belirsiz
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Madde 9 kararıyla (Streamlit/tkinter prod'dan çıkınca) bu
zaten büyük ölçüde sadeleşir — Pi'nin ihtiyaç duyduğu tek bir "prod requirements"
listesi kalır (road_damage'ın eğitim-amaçlı `rasterio`/`albumentations`/`datasets`
paketleri Pi'ye hiç gitmemeli, onlar sadece cloud'daki eğitim ortamında olmalı).

---

## Bölüm 7 — Güvenlik

### 25. 🟡 FastAPI'de CORS/kimlik doğrulama yok, `0.0.0.0:8000`'de açık
**Durum:** Bekliyor
**📡 Pi/Offline Notu:** Artık senaryo netleşti — Pi kendi WiFi'ini yayınlıyor ve
"bağlanan herkese" hizmet verecek. Bu, kısmen **bilinçli bir tasarım** (afet anında
kimlik doğrulama engeliyle insanları geciktirmek istemezsiniz) ama iki risk kalıyor:
(1) Pi'nin hotspot'una bağlanan kötü niyetli biri **ağır endpoint'leri** (road-damage
analizi, risk hesaplama) spam'leyip Pi'nin kısıtlı CPU/RAM'ini tüketip **gerçek
afetzedelerin** hizmete erişimini engelleyebilir (yerel DoS) — bu senaryoda normal
internet güvenliğinden farklı olarak **kaynak korumalı rate-limiting** kritik hale
geliyor (kimlik doğrulama değil, ama "kişi/IP başına dakikada N istek" sınırı şart).
(2) Pi aynı zamanda internet'e bağlıysa, `0.0.0.0:8000`'in yanlışlıkla WAN tarafına
da açık kalmaması için firewall/iptables kuralı gerekiyor (sadece hotspot arayüzünde
dinlemeli, WAN arayüzünde değil — bu bir deployment/infra maddesi, kod değil, ama
mutlaka provisioning checklist'ine girmeli).

### 26. 🟡 Hata mesajı sızıntısı
**Durum:** Bekliyor
(Değişmedi.)

---

## Bölüm 8 — Kod kalitesi / küçük iyileştirmeler

### 27-30. ⚪ (Değişmedi — bkz. önceki analiz: camera_manager thread overhead, logging eksikliği,
map_visualizer.py kopyala-yapıştır, TimeSeriesSplit döngü israfı.)
**📡 Pi/Offline Notu (madde 27 için):** camera_manager.py'deki "her frame yeni thread"
deseni Pi'de daha da pahalı (ARM'da thread oluşturma maliyeti orantısız değil ama
zaten kıt olan CPU bütçesinden çalıyor) — Pi bağlamında bu maddenin önceliği hafifçe
yükseliyor.

---

## Bölüm 9 — (YENİ) Offline/Online Hibrit Mimari ve Senkronizasyon

Şu anki kod, "internet var/yok" ikiliğini **sadece road_damage'ın offline-OSM
checkbox'ında** kısmen ele alıyor. Geri kalan her şey (NLP konum çözümleme, risk
motoru, model eğitimi) internet olduğunu varsayıyor ya da internet yokken sessizce
bozuluyor. Sıfırdan tasarlanması gereken parçalar:

### 31. 🔴 (yeni) "Outbox" desenli senkronizasyon katmanı yok
**Durum:** Bekliyor
Bir telefon, Pi'nin hotspot'una bağlıyken bir afet ihbarı/NLP analizi gönderdiğinde,
bu kayıt **sadece o Pi'nin yerel diskinde** kalıyor. Pi internete çıktığında bu
kayıtların merkezi sunucuya iletilmesi gerekiyor ama böyle bir mekanizma yok.
**Öneri:**
- Pi'de yerel SQLite'ta bir `outbox` tablosu: her yerel olayda (NLP raporu, risk
  sorgusu, road-damage analiz sonucu) bir satır eklenir, `synced=false` ile işaretlenir.
- Arka planda çalışan bir görev (systemd timer / basit bir `asyncio` task), belirli
  aralıklarla internet durumunu kontrol eder; varsa `synced=false` kayıtları merkezi
  sunucuya toplu (batch) gönderir, başarılı olanları `synced=true` yapar.
- Merkezi sunucu tarafında, farklı Pi'lerden gelen benzer/çakışan raporların
  (ör. aynı binanın iki farklı telefon tarafından bildirilmesi) **dedup/birleştirme**
  mantığı gerekiyor — bu Pi'de değil, merkezi sunucuda yapılmalı (Pi'nin görevi
  sadece "gördüğünü ilet", karar merkezi sunucuda).

### 32. 🟠 (yeni) "Cloud'da eğit, Pi'ye dağıt" modeli resmileştirilmeli
**Durum:** Bekliyor
Model eğitimi (CatBoost risk modeli, gelecekte fine-tune edilecek BERT/Segformer/YOLO
modelleri) **Pi üzerinde değil, cloud/geliştirici makinesinde** yapılmalı; Pi sadece
**eğitilmiş, dondurulmuş model dosyalarını** çalıştırmalı. Bunun için:
- Model + işlenmiş-veri artefaktları (`.cbm`, `.pth`, `.pt`, işlenmiş `safety_areas.geojson`/
  `roads.gpkg`, offline geocoding tablosu) için bir **versiyonlama ve dağıtım kanalı**
  gerekiyor (zaten Hugging Face kullanılıyor bazı modeller için — bunu tüm "Pi'ye
  gömülecek statik varlıklar" için standart pratik yap).
- Pi, internet bulduğunda bu kanaldan **"yeni model/veri versiyonu var mı?"** diye
  sorup varsa indirip yerel kopyayı günceller (ama mevcut eski kopya asla silinmemeli/
  bozulmamalı ki güncelleme yarıda kesilirse Pi çalışır durumda kalsın — atomik
  dosya değişimi: yeni dosyayı `.tmp` olarak indir, tamamlanınca `rename` ile değiştir).

### 33. 🟡 (yeni) "Özellik matrisi" — hangi özellik offline'da çalışır, hangisi çalışmaz?
**Durum:** Bekliyor
Şu an kodda hangi özelliğin internete bağımlı olduğu **örtük** (bazı fonksiyonlar
`try/except` ile sessizce boş dönüyor, kullanıcı neden bir şey görmediğini anlamıyor).
Açıkça tanımlanmış bir tablo faydalı olur, örnek:

| Özellik | Internetsiz çalışır mı? | Notlar |
|---|---|---|
| NLP sınıflandırma (BERTurk) | ✅ Evet | Model yerelde |
| NLP konum çözümleme | ⚠️ Kısmi | Nominatim internet ister → madde 20'deki yerel geocoding tablosu şart |
| Risk motoru (CatBoost) | ✅ Evet | Model + veri yerelde (madde 15, 32) |
| Risk verisi güncelleme (Kandilli API) | ❌ Hayır | Sadece internet varken |
| Road damage — uydu görüntüsü | ❌ Hayır | Google/Esri/OAM internet ister |
| Road damage — yol maskesi | ⚠️ Kısmi | Local `roads.gpkg` varsa evet, yoksa Overpass ister |
| Toplanma alanı bulma | ⚠️ Kısmi | Local `safety_areas.geojson` varsa evet |
| Kamera tespiti (YOLO) | ✅ Evet (donanım yeterse) | Tamamen yerel, internet gerekmez |

Bu tablo hem geliştirmeye rehberlik eder hem de (istenirse) `/api/status` endpoint'i
üzerinden mobil uygulamaya döndürülüp Flutter tarafında "şu an bu özellik kullanılamaz"
uyarısı göstermek için kullanılabilir.

---

## Bölüm 10 — (YENİ) Raspberry Pi Kaynak Bütçesi ve Model Uygunluğu

> **⚠️ Faz durumu:** Bu bölümdeki her şey Pi donanımı **gerektirir** ve şu an elimizde
> Pi olmadığı için **hiçbiri fiilen doğrulanamıyor**. Aşağıdaki madde 34-36, Pi temin
> edilene kadar teorik/tahmini kalacak — bunları "PC'de aynı testi yapıp Pi'ye eşliyoruz"
> gibi bir kısayolla kapatmaya çalışmayın, PC'nin x86_64 CPU'su (muhtemelen çok daha
> güçlü, muhtemelen farklı komut seti — SIMD/NEON farkları dahil) Pi'nin ARM CPU'suna
> performans açısından **güvenilir bir vekil değil**. Yine de aşağıda her maddeye,
> Pi gelene kadar **şimdiden** yapılabilecek bir "Faz 1 hazırlığı" eklendi — amaç,
> Pi ulaştığında bocalamadan doğrudan ölçüme geçebilmek.

### 34. 🔴 (yeni) Gerçek Pi donanımında erken benchmark yapılmadı (varsayım: yapılmadı)
**Durum:** Bekliyor — **⚠️ şu an bloklu, Pi donanımı yok**
Şu ana kadarki tüm performans varsayımları muhtemelen x86_64 geliştirici makinesinde
ölçüldü/varsayıldı. Pi temin edildiğinde **öncelik #1 olmalı:** Hedef Pi modelini
(Pi 4 4GB/8GB mi, Pi 5 mi?) netleştirip üzerinde şu ölçümleri erken yap:
- BERTurk sınıflandırma + NER: tek istek başına gerçek gecikme (ms).
- Segformer mit_b4: tek 512x512 patch başına ve tam bir uydu görüntüsü (birden fazla
  patch, %50 overlap) için gerçek süre.
- YOLO x2 (catlak.pt + bina.pt): frame başına gerçek FPS.
- CatBoost eğitimi: mevcut `query.csv` boyutuyla gerçek süre.
- Aynı anda 3-5 telefon bağlıyken RAM/CPU/sıcaklık (thermal throttling var mı?).
Bu ölçümler olmadan Bölüm 4'teki (madde 18) kuantizasyon/ONNX önerilerinin ne kadar
gerekli olduğu bile netleşmez — belki bazı modeller Pi'de zaten kabul edilebilir
hızda çalışır, belki hiçbiri çalışmaz. **Varsayımla ilerlemek yerine ölç.**
**💻 Faz 1 (PC) notu:** Pi yokken elde edilebilecek tek şey **PC üzerinde göreli bir
taban çizgi** — yukarıdaki aynı beş ölçümü PC'de de kaydedin (özellikle "aynı anda
3-5 istek" eşzamanlılık testi PC'de de anlamlı, çünkü FastAPI'nin sync/async/worker
davranışı donanımdan bağımsız). Bu sayılar Pi'de "kaç kat yavaş olur" sorusuna cevap
vermez ama en azından hangi modülün PC'de bile en yavaş/en ağır olduğunu (görece
sıralama) gösterir ve madde 18/35 için hazırlık sağlar. Ayrıca **Pi modelini şimdiden
netleştirmek** (Pi 4 4GB mi, 8GB mi, Pi 5 mi olacak — satın alma kararı) bu maddenin
önündeki en büyük belirsizlik; donanım seçimi netleşmeden "hangi model sığar" sorusu
zaten cevaplanamaz.

### 35. 🟠 (yeni) RAM bütçesi planlaması yok
**Durum:** Bekliyor — **⚠️ kesin sayılar Pi'de doğrulanmalı**
Pi 4 (4GB varsayımıyla, işletim sistemi + diğer servisler ~500MB-1GB alır) kullanılabilir
RAM ~3-3.5GB civarı. Yüklenmesi düşünülen modeller: BERTurk sınıflandırma (~500MB-1GB
fp32), BERTurk/harici NER modeli (~500MB-1GB), Segformer mit_b4 (encoder büyük, muhtemelen
300-500MB+), YOLO x2 (küçük modellerse ~50-100MB her biri). Toplamı kolayca 2-3GB'ı bulur
— **hepsi aynı anda belleğe yüklüyse Pi 4 4GB modelinde swap'a düşme/OOM-kill riski
yüksek.**
**Öneri:** Madde 8'deki lazy-load + LRU tahliye burada zorunlu hale geliyor; ayrıca
düşük-RAM Pi modelleri için "hangi modüller aktif" konusunda bir yapılandırma
(ör. `.env` ile `ENABLE_CAMERA_DETECTION=false` gibi) sunmayı düşün — her Pi'nin her
özelliği aynı anda çalıştırması şart olmayabilir (saha ihtiyacına göre bir Pi sadece
"NLP + Risk", başka bir Pi "+ Road Damage" çalıştırabilir).
**💻 Faz 1 (PC) notu:** Model boyutları (fp32 disk/checkpoint boyutu) donanımdan
bağımsız ölçülebilir — PC'de her modelin `du -h`/dosya boyutu ve process RSS'i (ör.
`psutil` ile) şimdiden kaydedilebilir, bu yukarıdaki tahmini sayıları gerçek verilerle
değiştirir. Lazy-load + LRU tahliye mimarisi de PC'de tasarlanıp yazılabilir/test
edilebilir; sadece "tetiklenme eşiği" (kaç MB'ta tahliye başlasın) Pi'nin gerçek RAM
bütçesi netleşince ayarlanacak bir parametre olarak bırakılmalı.

### 36. 🟡 (yeni) SD kart aşınması ve I/O yavaşlığı
**Durum:** Bekliyor
Şu an kodda SD kart'a sık/gereksiz yazan noktalar var: `catboost_info/` (proje kökünde
zaten oluşmuş, her eğitimde ayrıntılı log/event dosyaları yazıyor — `verbose=False`
olsa da CatBoost bazı meta dosyaları hâlâ yazabilir, kontrol edilmeli), sürekli büyüyen
`query.csv`, process-memory olmayan her türlü dosya-tabanlı cache (madde 21'in çözümü
dahil — dikkatli tasarlanmalı, "her istekte diske yaz" değil "toplu/aralıklı yaz").
**Öneri:** Mümkünse Pi'ye harici bir USB SSD bağlanıp gerçek veritabanı/cache orada
tutulmalı (SD kart sadece OS + salt-okunur statik varlıklar için); en azından sık
yazılan geçici veriler (`/tmp` benzeri) `tmpfs` (RAM-disk) üzerinde tutulmalı.
**💻 Faz 1 (PC) notu:** PC'de bu madde neredeyse hiç görünmez — normal bir SSD/HDD'nin
aşınma/hız profili SD kartla kıyaslanamayacak kadar iyi, yani PC'de "gereksiz sık yazma"
davranışını fark etmeden geliştirme yapmak kolay. Tam bu yüzden risk var: kod PC'de
"sorunsuz" görünüp Pi'ye gidince I/O darboğazı sürpriz olabilir. Öneri: `query.csv`'yi
SQLite'a taşıma (madde 16) ve "toplu/aralıklı yaz" prensibi PC'de bile **şimdiden**
uygulanmalı — bunlar Pi'ye özel değil, genel olarak daha doğru bir tasarım; sadece
Pi'de faydası çok daha somut ortaya çıkacak.

---

## Bölüm 11 — (YENİ) Ağ/Erişim Mimarisi (WiFi AP + Keşif)

### 37. 🟡 (yeni) Mobil uygulama Pi'yi IP tahmin ederek buluyor — kırılgan
**Durum:** Bekliyor
`mobile/lib/services/api_config.dart`, sabit bir IP listesi deniyor
(`10.42.0.1:8000`, `192.168.137.1:8000` vb.) — bu, "hangi işletim sistemi hotspot
açtıysa o IP" varsayımına dayanıyor, kırılgan.
**Öneri:** Pi üzerinde **mDNS/Bonjour** (Avahi, Raspberry Pi OS'ta genelde hazır gelir)
ile `quakemind.local` gibi sabit bir hostname yayınla; Flutter tarafında IP tahmini
yerine (ya da ona ek olarak) mDNS keşfi kullan. Bu, Pi'nin hangi ağ yapılandırmasıyla
hotspot açtığından bağımsız, çok daha sağlam bir çözüm.

### 38. 🟡 (yeni) Uygulamayı yüklememiş kullanıcılar için tarayıcı erişimi / captive portal
**Durum:** Bekliyor
Amaç "afet öncesi/sonrası herkese hizmet" ise, Flutter uygulamasını **yüklememiş**
biri de Pi'nin hotspot'una bağlanıp bir şeyler görebilmeli. **Öneri (bkz. Bölüm 12):**
Pi, FastAPI üzerinden statik olarak **Flutter Web build'ini** serve etsin; isteğe
bağlı olarak bir **captive portal** (telefonun "bu WiFi'ye bağlandın, giriş yapmak
için tıkla" bildirimini otomatik açması) kurulumu, bağlanan herkesin uygulamayı hiç
aramadan doğrudan arayüzle karşılaşmasını sağlar. Bu bir altyapı (hostapd/dnsmasq
+ DNS-yönlendirme) konusu, kod değil, ama ürün hedefiyle doğrudan ilgili.

---

## Bölüm 12 — (YENİ) Streamlit Kararı — Ne İle Değiştirelim? / PC'de Hangi Arayüzle İlerleyelim?

> **⚠️ Bu bölüm, Pi elimizde olmadığı için şu an en çok "gündelik karar"a dönüşen
> bölüm — "PC üzerinde bir arayüzden ilerleme" ihtiyacının doğrudan cevabı burada.**
> Aşağıdaki analiz **iki ayrı soruyu** birbirinden ayırıyor: (1) *Pi'ye nihayetinde ne
> deploy edilecek* (bu, alttaki orijinal analizde değişmedi) ve (2) *Pi yokken, şimdi,
> PC üzerinde hangi arayüzle çalışacağız* (bu, aşağıda yeni eklenen "Faz 1" kısmı).

### Faz 1 (şimdi — Pi yok, PC üzerinden ilerleme)

Pi olmadığı sürece Streamlit'in yukarıdaki tüm dezavantajları (rerun-on-interaction
maliyeti, tek-worker session-state) **önemsiz** — bunlar Pi'nin kısıtlı CPU/RAM'i ve
"aynı anda çok sayıda telefon" senaryosu yüzünden sorun; PC'de tek geliştirici/birkaç
test kullanıcısı için Streamlit'in maliyeti fark edilmez. Dolayısıyla:
- **Streamlit'i (main.py + apps/*/app.py) şimdilik atmaya gerek yok.** PC'de model/
  algoritma denemesi, demo, iç değerlendirme için kullanmaya devam edilebilir —
  bu, "PC üzerinde bir arayüzden ilerleme" ihtiyacını bugün en az efor ile karşılayan
  yol (zaten yazılmış, çalışıyor).
- **Tek şart:** Bu Faz 1 kullanımının **iş mantığını Streamlit'in içine sızdırmaması**
  — madde 7 ve 9'daki "aynı mantık 3-4 yerde kopyalanmış" sorunu tam olarak böyle
  büyüyor. Streamlit dosyaları sadece `fastapi_app.py`'nin (+ ortak modüllerin)
  **ince bir istemcisi/görünümü** olarak kalmalı; risk hesaplama, NLP, road-damage gibi
  gerçek işi hep FastAPI/ortak modüller yapmalı. Böylece Pi geldiğinde arayüz katmanı
  değişse bile alttaki mantık zaten tek yerde, taşınabilir durumda olur.
- Bu Faz 1 kararı, madde 2'deki `customtkinter` GUI için de geçerli: PC'de debug/demo
  aracı olarak kalabilir, sadece kök `requirements.txt`'e değil `requirements-dev.txt`'e
  girmeli (bkz. madde 2, madde 24).

### Faz 2 (Pi temin edildiğinde) — orijinal analiz, değişmedi

Pi eline geçtiğinde geçerli olacak nihai karar hâlâ şu: **Evet, Streamlit'i prod/Pi
dağıtımından tamamen çıkar.** Gerekçe ve alternatif:

**Neden Streamlit Pi senaryosunda yanlış araç:**
- Her tarayıcı sekmesi/kullanıcısı için **tam bir Python script'i yeniden çalıştırma**
  modeli var (rerun-on-interaction) — Pi'nin kısıtlı CPU'sunda birden fazla telefon
  aynı anda bağlıyken bu model orantısız pahalı.
- Session-state yönetimi tek-process, tek-worker'a göre tasarlanmış; yatay ölçekleme
  ya da "N kullanıcıyı hafif şekilde ağırlama" için değil.
- Zaten mobil uygulama (Flutter) gerçek istemci — Streamlit'in insan kullanıcıya
  gösterdiği arayüz, prod akışında **hiç kullanılmıyor** (madde 9'da tespit edildiği
  gibi zaten main.py ile apps/*/app.py arasında drift var, bakımı da ihmal ediliyor).

**Somut öneri — iki parça:**

1. **Backend:** Sadece `fastapi_app.py` (+ ortak modüller). Zaten mobil istemci bunu
   kullanıyor, ekstra bir şey gerekmiyor — sadece Streamlit'i devre dışı bırakmak
   yeterli.

2. **Tarayıcıdan erişim (uygulamayı yüklememiş kullanıcılar için, madde 38):**
   Flutter zaten **web'e derlenebiliyor** (`flutter build web`). Yani ayrı bir
   frontend teknolojisi öğrenmeye/yazmaya gerek yok — **aynı Flutter kod tabanını
   web'e derleyip statik dosyalar olarak FastAPI'nin kendisinden
   (`fastapi.staticfiles.StaticFiles`) serve edebilirsin.** Bu şu avantajları sağlar:
   - Sıfır ekstra sunucu/servis (Node.js gerekmez), sadece FastAPI zaten çalışıyor.
   - UI mantığı **tek yerde** yaşar (bugün main.py/apps/*/app.py arasındaki drift
     sorununun web tarafında hiç yaşanmayacağı anlamına gelir).
   - Statik dosya servisi, Streamlit'in aksine Pi'de neredeyse sıfır ek CPU/RAM
     maliyetiyle çalışır (dosya okuyup gönderiyor, Python script koşturmuyor).
   - Aynı anda bağlanan çok sayıda telefon için doğal olarak çok daha hafif.
   - Faz 1'de Flutter Web build'ini **PC'de de** deneyip erken doğrulamak mümkün —
     bu adımın Pi'yi beklemesi gerekmiyor, PC'de `flutter build web` + FastAPI
     static serve zaten bugün test edilebilir.

   *Alternatif (Flutter Web istenmezse):* Çok basit, framework'süz bir statik
   HTML/JS sayfası (fetch ile `fastapi_app.py` endpoint'lerini çağıran) da yeterli
   olur — durumun karmaşıklığına göre.

**Streamlit'i Faz 2'de de tamamen atmak istemezsen (geliştirme/demo amaçlı elde
tutmak istiyorsan):** O zaman en azından **açıkça "sadece geliştirici masaüstü için,
asla Pi'ye deploy edilmez"** diye işaretleyip `dev-tools/` gibi ayrı bir klasöre
taşı; kök `requirements.txt`'ten Streamlit'i çıkarıp `requirements-dev.txt`'e taşı
ki Pi imajı yanlışlıkla Streamlit'i de kurmasın. Faz 1'de zaten bu şekilde
kullanılıyor olacağı için, Faz 2'ye geçiş fiilen sadece "kök requirements'tan çıkar
+ klasör taşı" işlemine indirgenmiş olur — kod yeniden yazmaya gerek kalmaz.

---

## Bölüm 13 — (YENİ) Resmi TÜBİTAK 2209-A Başvurusu ile Kapsam Karşılaştırması

> Bu bölüm, projenin resmi araştırma öneri formu (2209-A başvurusu, IP1-IP7 iş
> paketleri) okunduktan sonra eklendi. Bölüm 0-12'deki analiz, sohbetimizden
> çıkardığım "Pi + hotspot + FastAPI" mimarisi varsayımıyla sınırlıydı — başvuru
> formu okununca, bunun proje kapsamının sadece bir kesiti olduğu, resmi öneride
> tanımlanmış bazı iş paketlerinin kodda **hiç karşılığı olmadığı** ortaya çıktı.
> Aşağıdaki her madde, kodda gerçekten arayarak (grep + dosya okuma) doğrulandı;
> varsayıma dayalı değil.

### 39. 🔴 (yeni) P2P / BLE Mesh / Raspberry Pi Broadcast (IP5) — kodda hiçbir karşılığı yok
**Durum:** Bekliyor
Başvurunun 2.5 bölümü (IP5), projenin belirtilen hedeflerinden biri olarak resmi
öneride önemli bir yer kaplıyor: Raspberry Pi üzerinde hotspot + broadcast mesajlaşma,
**Bluetooth Low Energy (BLE) ile peer discovery ve köprüleme** (hotspot menzili dışında
kalan kullanıcının, menzildeki başka bir kullanıcı üzerinden BLE ile veri iletmesi),
JSON tabanlı mesaj kuyruğu, internetsiz harita modu ve konum/hasar bildirimi paylaşımı.
`bluetooth|BLE|p2p|mesh|broadcast|raspberry` anahtar kelimeleriyle hem `backend/`
hem `mobile/lib/` içinde arama yapıldı — **backend'de veya Flutter tarafında bu
mimariye ait tek bir satır kod, paket bağımlılığı veya stub bile yok.** Bölüm 0-12'deki
analiz Pi'yi yalnızca "tek hotspot + FastAPI" (yıldız topolojisi) olarak ele almıştı;
oysa öneri **BLE mesh ile hotspot menzili dışını da kapsayan** bir mimari istiyor. Bu,
"düşünemediğim" değil, konuşma bağlamımızda hiç gündeme gelmemiş bağımsız bir iş
paketi — kapsam ciddiyeti nedeniyle danışmanla süre/öncelik açısından netleştirilmeli
(gerçek bir BLE mesh + hotspot hibrit protokolü, kalan diğer tüm işlerden bağımsız,
başlı başına önemli bir mühendislik yükü).

### 40. 🔴 (yeni) Test altyapısı (IP7) tamamen yok — hiçbir başarı kriteri doğrulanamıyor
**Durum:** Bekliyor
`backend` içinde `test` geçen tek bir dosya bulunamadı (birim testi, API testi,
yük testi — hiçbiri yok; `mobile/test/` sadece Flutter'ın varsayılan boilerplate
widget testini içeriyor). Ama resmi Çalışma Takvimi'nde (bkz. `2209-A ... .pdf`, s. 17)
her iş paketine **somut, ölçülebilir başarı kriterleri** bağlanmış: kısa vadeli risk
modeli **%75+ doğruluk**, çatlak/yıkım YOLOv8 modelleri **%85+ doğruluk**, yol maskesi
segmentasyonu **%80+ doğruluk**, P2P mesajlaşma **%90+ başarı**, API yanıt süresi
**<500ms**. Şu anki kod tabanında bunların **hiçbiri otomatik/tekrarlanabilir biçimde
ölçülmüyor** — ne `pytest`/`unittest` klasörü, ne Postman/Newman koleksiyonu, ne de
bir benchmark script'i var. Bölüm 3'teki (madde 11) performans notları teorikti;
gerçek bir ölçüm altyapısı olmadan proposal'daki hiçbir yüzdelik hedefin karşılanıp
karşılanmadığı bilinemez. **Öneri:** En azından (a) üç modelin (CatBoost, YOLOv8 x2,
Segformer) accuracy/precision/recall/F1'ini hesaplayan basit bir `eval/` script seti,
(b) 5 API endpoint'i için Postman/Newman koleksiyonu, (c) `/api/*` endpoint'leri için
basit bir latency-ölçüm scripti (locust veya benzeri) eklenmeli.

### 41. 🟠 (yeni) Uydu görüntüsü ön işleme (NDVI/NDBI/CLAHE) ve çok sınıflı segmentasyon (2.4.1) yok
**Durum:** Bekliyor
Öneri, uydu görüntüsü ön işlemesi için NDVI (bitki örtüsü maskeleme), NDBI (yapılaşmış
alan belirginleştirme), CLAHE kontrast iyileştirme ve kenar belirginleştirme adımlarını,
ardından "yol", "bina", "açık alan", "enkaz" sınıflarını piksel seviyesinde ayıran
**çok sınıflı** bir semantic segmentation modeli tanımlıyor. Kodda (`apps/road_damage/utils/inference.py:39`)
`smp.Segformer(..., classes=1)` — yani **tek sınıflı (binary hasar/hasar-değil)** bir
model kullanılıyor; NDVI/NDBI/CLAHE hesaplaması hiçbir yerde yok (aratıldı, sıfır sonuç).
Şu anki uydu modülü, öneride tarif edilenden çok daha dar kapsamlı: sadece "hasarlı mı
değil mi" tespit ediyor, "bu bir yol mu bina mı açık alan mı" ayrımını yapmıyor.

### 42. 🟠 (yeni) Değişim tespiti / change detection (2.4.2) yok
**Durum:** Bekliyor
Öneri, tarihsel ve güncel uydu görüntüleri arasında fark analizi yaparak yeni oluşmuş
engelleri otomatik işaretlemeyi tarif ediyor (madde 2.4.2, "change detection"). Kodda
bu adıma dair hiçbir iz yok — `apps/road_damage` yalnızca **tek bir zaman noktasındaki**
görüntüyü işliyor (kaynak: Google Maps/OpenAerialMap/Esri Wayback'ten seçilen tek kare),
iki zaman noktasını karşılaştıran bir mantık hiç yazılmamış.

### 43. 🟠 (yeni) Yıkım yoğunluğu ısı haritası — Gaussian kernel ile (2.4.3) yok; sadece deprem-epicenter heatmap'i var
**Durum:** Bekliyor
`map_visualizer.py`'deki `HeatMap` (folium.plugins), yalnızca **geçmiş deprem
odaklarının** yoğunluğunu gösteriyor (earthquake_risk modülü). Öneride tarif edilen
ısı haritası ise farklı bir şey: yıkım tespiti + kullanıcı raporlarından gelen
konumsal işaretçilerin, **güven skoru ağırlıklı bir Gaussian çekirdek** ile
yumuşatılarak "yıkım yoğunluğu" yüzeyine dönüştürülmesi ve bunun güvenli rota
motorunda ceza katsayısı olarak kullanılması (2.4.3-2.4.4). Bu confidence-weighted
destruction-density heatmap'i, road_damage modülünde **hiç yok** — road_damage şu an
sadece bir ikili maske (`blockage_mask`) üretiyor, yoğunluk yüzeyine dönüştürmüyor.

### 44. 🟠 (yeni) Güvenli rota: ceza-katsayılı çok faktörlü maliyet fonksiyonu (2.4.4) yerine ikili kenar silme var
**Durum:** Bekliyor
`apps/road_damage/utils/network.py:51-120` (`analyze_road_network_graph`), bir yol
segmentini blockage_mask'e göre **tamamen bloklu ya da tamamen açık** olarak
sınıflandırıp bloklu kenarları graf'tan **siliyor**; ardından `calculate_route`
(satır 16-49) kalan graf üzerinde düz `nx.shortest_path`/`nx.astar_path` (weight='length',
yani sadece mesafe) çalıştırıyor. Öneri ise (2.4.4) yıkım yoğunluğu ısı haritası,
kapalı yol, engel segmentleri ve **kullanıcı raporlarını** bir araya getiren bir
"ceza katsayısı" (penalty) ile ağırlıklandırılmış, sadece en kısa değil **en güvenli**
rotayı hesaplayan bir maliyet fonksiyonu tarif ediyor. Şu anki uygulamada: (a) kullanıcı
raporları (kapalı yol/enkaz bildirimi) rota hesaplamasına **hiç girmiyor** — sadece
uydu tabanlı `blockage_mask` kullanılıyor; (b) kısmen hasarlı/riskli ama tam kapalı
olmayan segmentler için bir ara "ceza" kavramı yok, ikili (binary) bir karar var.
**Not:** Bu, Bölüm 0-12'de fark edilmemişti çünkü önceki analiz "Dijkstra/A* var mı"
sorusuna odaklanmıştı (var), "nasıl ağırlıklandırıldığı" sorusunu sormamıştı.

### 45. 🟡 (yeni) JWT tabanlı kimlik doğrulama (2.6.4) — proposal'da açıkça isteniyor, kodda yok, önceki analiz bunu bilinçli tercih sanmıştı
**Durum:** Bekliyor
Öneri metni (2.6.4, "Güvenli Veri Aktarımı"), HTTPS + **JWT (JSON Web Token) ile
kullanıcı doğrulama/yetkilendirme** + rate limiting + IP bazlı erişim kontrolünü resmi
yöntem olarak tanımlıyor. Bölüm 7'deki (madde 25) önceki analiz, kimlik doğrulamasının
eksikliğini "afet anında insanları geciktirmemek için **bilinçli bir tasarım tercihi**
olabilir" diye yorumlamıştı — ama resmi öneri **JWT'yi doğrudan yöntem olarak taahhüt
ediyor**. Bu bir çelişki: ya öneri metni güncel mimariyi yansıtmıyor (TÜBİTAK'a
taahhüt edilmiş ama sahada gevşetilmesi planlanan bir madde), ya da JWT gerçekten
eklenmesi gereken bir eksik. **Bu, kod değil, kullanıcıyla netleştirilmesi gereken bir
karar maddesi** — hangisi olduğu netleşmeden madde 25'teki öneri revize edilmemeli.

### 46. ⚪ (bilgi amaçlı) `disaster_nlp` (BERTurk sınıflandırma + NER) modülü resmi IP1-IP7 iş paketlerinin hiçbirinde tanımlı değil
**Durum:** Bekliyor
Başvuru formunun yöntem bölümü (IP1-IP7) hiçbir yerde sosyal medya/metin tabanlı afet
sınıflandırması veya NER'den bahsetmiyor — kod tabanındaki `apps/disaster_nlp` (BERTurk
+ NER pipeline, mobil uygulamada ayrı bir "NLP" sekmesi) resmi kapsamın **dışında**
geliştirilmiş bir modül gibi görünüyor. Bu bir hata değil (muhtemelen ekstra bir
değer katma çabası), ama şunu gösteriyor: mühendislik efor dağılımı resmi taahhütlerle
tam örtüşmüyor — kapsam dışı bir modüle emek verilirken, kapsam içi IP5 (P2P/BLE) ve
IP7 (test) gibi taahhüt edilmiş parçalar hiç başlanmamış durumda. Danışmanla/başvuru
sahibiyle önceliklendirme netleştirilmeli: rapor teslimi öncesi IP1-IP7'nin kapsamı
mı önce tamamlanmalı, yoksa NLP eklentisi de "yaygın etki" bölümündeki ek çıktı olarak
mı sunulacak?

### 47. 🟡 (yeni) Çalışma Takvimi'ndeki nicel hedefler (%75/%85/%80/%90/<500ms) hiçbir yerde izlenmiyor
**Durum:** Bekliyor
Madde 40 ile doğrudan ilişkili: proposal'ın "Başarı Ölçütü" sütunu (s. 17-18) somut
yüzdelik/gecikme hedefleri veriyor, ama bunları raporlayan tek bir dashboard, log
metriği veya CI adımı yok. Test altyapısı (madde 40) kurulduktan sonra, bu hedeflerin
her biri için basit bir "hedefe karşı mevcut durum" tablosu (ör. bu dosyanın bir
sonraki revizyonunda) tutulması, hem ilerleme takibini hem de sonuç raporu (IP7)
hazırlığını kolaylaştırır.

**Bölüm 13 özet değerlendirmesi:** Önceki analiz (Bölüm 0-12) "var olan kodu Pi'de
nasıl daha iyi çalıştırırız" sorusuna odaklanmıştı ve bu soruyu iyi cevaplıyor. Ama
resmi başvuruyla karşılaştırınca görülüyor ki üç büyük iş paketi parçası (BLE/P2P mesh,
çok-sınıflı+NDVI/NDBI+change-detection uydu ön işleme, ceza-katsayılı rota) **var olan
kodun optimize edilmesiyle çözülemez — sıfırdan yazılması gereken yeni özellikler.**
Test altyapısının tam yokluğu da ayrı bir kör nokta. Bunlar "eksikler" listesinde en
üste (madde 39, 40) eklendi çünkü kalan tüm optimizasyon önerileri (Bölüm 0-12),
bu parçalar hiç var olmadığı sürece zaten teorik kalıyor.

---

## Öncelik Sırası (Pi/offline-first bağlamına göre yeniden yazıldı)

> **⚠️ Bu sıralama, Pi donanımının elde olduğu varsayımıyla yazılmıştı.** Şu an
> geçerli olmadığı için aşağıda önce **Faz 1 (Pi yokken, şimdi PC'de yapılabilecekler)**
> sıralaması var; orijinal 8 maddelik sıralama onun altında **Faz 2 (Pi temin
> edildiğinde)** olarak korundu — Pi eline geçtiğinde doğrudan o listeye geç.

### Faz 1 — şimdi, Pi yokken, PC üzerinde yapılabilecekler (öncelik sırasıyla)

1. **Madde 1, 3, 4, 6, 7, 9** — donanımdan tamamen bağımsız kod/mimari düzeltmeleri:
   `ultralytics` eksikliğini gider, global `QUAKEMIND_OFFLINE_ONLY` env var'ını kaldır,
   çift-import/çift-model-yükleme sorununu çöz, unutulmuş `nlp_bridge_server.py`'yi
   temizle, kod tekrarını (madde 7) azalt, "hangi dosya gerçek backend" belirsizliğini
   (madde 9) `fastapi_app.py` lehine netleştir. Bunların hiçbiri Pi beklemiyor, PC'de
   bugün bitebilir ve Pi geldiğinde üzerine inşa edilecek temel bunlar.
2. **Madde 15 + 16** — CatBoost modelini diske persist et, `query.csv`'yi SQLite'a
   taşı. Donanımdan bağımsız, PC'de tamamen tamamlanabilir; Faz 2'de "Pi'ye önceden
   eğitilmiş model gömülü gelsin" hedefinin ön koşulu zaten bu.
3. **Madde 31 + 32** — Senkronizasyon (outbox) mimarisi ve "cloud'da eğit, Pi'ye
   dağıt" modelinin **tasarımı ve kod iskeleti**. Pi olmadan uçtan uca test edilemez
   (gerçek "iki cihaz arası senkron" senaryosu) ama mimari/kod PC'de yazılıp iki ayrı
   PC-process/iki ayrı port ile simüle edilebilir.
4. **Madde 3 + 20 + 33** — Offline/online otomatik algılama, yerel geocoding tablosu,
   özellik matrisi. Bunlar da donanımdan bağımsız; PC'de WiFi'yi kapatıp açarak
   "internet var/yok" geçişleri simüle edilebilir.
5. **Madde 12 (Faz 1 kısmı)** — PC'de hangi arayüzle ilerlenileceği: Streamlit'i
   Faz 1'de koru, ama iş mantığını FastAPI'ye sızdırmadan ince istemci olarak kullan
   (yukarıdaki Bölüm 12'ye bkz.).
6. **Madde 23 (kısmi)** — Pi'de gerçek kurulum testi yapılamasa da, hedef paket
   listesinin piwheels.org'ta ARM64 desteğini şimdiden araştırıp bir risk listesi
   çıkar; mümkünse QEMU/ARM64 emülasyonuyla ön-deneme yap.
7. **Madde 40 (kısmi)** — Test altyapısının PC'de kurulabilecek kısmı (CatBoost/YOLO/
   Segformer için `eval/` script seti, API endpoint testleri) — bunlar donanımdan
   bağımsız, Pi beklemeden şimdi yazılabilir; sadece "Pi'de <500ms" gibi donanıma
   bağlı hedefler Faz 2'yi bekler.

### Faz 2 — Pi temin edildiğinde (orijinal sıralama, korunmuştur)

1. **Madde 34** — Gerçek Pi donanımında erken benchmark. Bunu yapmadan diğer birçok
   karar (madde 18 kuantizasyon, madde 35 RAM bütçesi, hatta madde 1'in "ultralytics
   ekle" kararı) varsayıma dayalı kalır.
2. **Madde 23** — Bağımlılık/ARM wheel riski. Pi'ye geçmeden önce doğrulanmazsa,
   cykhash/Windows tekrarı ama saha ortamında yaşanır.
3. **Madde 9 + 12** — Streamlit/tkinter'ı prod kapsamından çıkarma kararı ve
   Flutter Web ile değiştirme. Bu karar netleşince madde 8, 10, 24'ün çoğu
   kendiliğinden sadeleşiyor.
4. **Madde 31 + 32** — Senkronizasyon mimarisi ve "cloud'da eğit, Pi'ye dağıt"
   modeli. Bunlar olmadan "afet öncesi/sonrası, internet olsun olmasın" hedefi
   kâğıt üzerinde kalır.
5. **Madde 3 + 20 + 33** — Offline/online geçişinin otomatik algılanması, yerel
   geocoding, özellik matrisi. Kullanıcı deneyiminin "internet yokken de tutarlı"
   olmasını sağlayan üçlü.
6. **Madde 5 + 15 + 16** — Risk motorunun Pi'de sıfırdan eğitilmemesi (önceden
   eğitilmiş model + budanmış veri seti gömülü gelmeli).
7. **Madde 4 + 35** — RAM bütçesi ve modül tekilleştirme (OOM riskini azaltmak).
8. Geri kalan performans/güvenlik/kod-kalitesi maddeleri (11-14, 17-22, 25-30,
   36-38) bu temeller oturunca çok daha az riskli ve hızlı ilerler.

**Not:** Faz 1'deki maddeler (1-7 numaralı Faz 1 listesi) Faz 2'nin önünü açacak
şekilde seçildi — yani Faz 1'i bitirmek, Faz 2'ye geçildiğinde madde 34/23 dışındaki
çoğu işin zaten yapılmış olması anlamına gelir.

**Bölüm 13 eklendikten sonra revize edilmiş not:** Yukarıdaki 8 maddelik sıralama
hâlâ geçerli ama sadece "mevcut kodu Pi'de optimize etme" eksenini kapsıyor. Resmi
proje kapsamıyla karşılaştırıldığında (Bölüm 13), bunlara paralel/önce
değerlendirilmesi gereken üç ayrı eksen daha var:
- **Madde 40** (test altyapısı) — mümkünse madde 34 (Pi benchmark) ile birlikte en
  başta ele alınmalı; ölçüm olmadan hiçbir hedefin karşılanıp karşılanmadığı bilinemez.
- **Madde 39** (BLE/P2P mesh) — kapsam/süre açısından danışmanla ayrı bir konuşma
  gerektiren, listedeki diğer her şeyden bağımsız, büyük bir iş paketi.
- **Madde 41-44** (uydu ön işleme, change detection, yoğunluk ısı haritası,
  ceza-katsayılı rota) — bunlar mevcut kodun "optimize edilmesiyle" değil, kısmen
  sıfırdan yazılmasıyla kapanacak eksikler; madde 32'deki ("cloud'da eğit, Pi'ye
  dağıt") modelin kapsamına bunların da girmesi gerekiyor.
- **Madde 45** kod değil bir karar maddesi — JWT'nin proposal'da taahhüt edildiği
  hâlde kodda/analizde göz ardı edilmiş olması, kullanıcıyla netleştirilmeden
  kapatılmamalı.
