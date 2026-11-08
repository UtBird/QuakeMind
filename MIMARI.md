# QuakeMind — Yazılım Mimarisi

Bu belge sistemin nasıl kurulacağını anlatır: katmanlar, veri sözleşmesi, işin nerede
yapıldığı, ölçek eşikleri ve ölçüm bütçeleri. Kurallar `CLAUDE.md`'de, tasarım sistemi
`ARAYUZ_KARARLARI.md`'de.

Son güncelleme: 20 Eylül 2026 · Kapsam: web + backend (Pi/offline ve mobil ertelendi)

---

## 1. Bugünkü bileşenler

| Bileşen | Yer | Durum |
|---|---|---|
| API | `backend/fastapi_app.py` (61 satır) + `cekirdek.py` + `uclar/` (14 modül, 61 uç) | 21 Eyl'de bölündü (Faz 5), davranış farkı 0 |
| Uydu bölütleme (SegFormer MiT-B4) | `apps/road_damage/` | Çalışıyor, ayrı işçiye taşınacak |
| Metin sınıflandırma + NER (BERTurk) | `apps/disaster_nlp/` | Çalışıyor |
| Deprem riski (CatBoost) | `apps/earthquake_risk/` | İstek yolunda eğitiliyor — düzeltilecek |
| Kamera tespiti (YOLO ×2) | `apps/camera_detection/` | Çalışıyor |
| Yol ağı ve rota (OSM + A\*) | `apps/road_damage/utils/network.py` | Bölge bazlı çizge, önbellekli |
| Mekânsal depo (PostGIS, 6 tablo) | `utils/postgis_manager.py` | Çalışıyor |
| Web (Next.js 14 + Leaflet) | `quakemind-web/` | Yerini yeni konsol alacak |
| Tanıtım sitesi (Astro) | `tanitim/` | İskelet kuruldu (20 Eyl): tek sayfa, sıfır istemci JS, ekran görüntüleri eklenecek |
| Yeni konsol (Vite + React) | `konsol/` | İskelet kuruldu (20 Eyl): token'lar, giriş, kalıcı harita kabuğu, modlar, tek SSE istemcisi. Uçlar bağlı değil |

> `HANDOFF.md`'de web için "React-Leaflet (60 FPS GPU harita)" yazıyor. Leaflet GPU'da
> çizmez; her nesneyi DOM/Canvas 2D üzerinden işler. Bu ifade düzeltilmeli.

---

## 2. Temel ilke: iş nerede yapılır

Performansı belirleyen şey kütüphane değil, işin yapıldığı yerdir.

```
ÖNCEDEN (ağır iş, bir kez)        SUNUCU (her istek, hafif)      TARAYICI (GPU)
────────────────────────────      ─────────────────────────      ──────────────
model işçileri (ONNX, kuyruk)  →  FastAPI + PostGIS           →  olay katmanları (ikili veri)
yoğunluk ızgarası (veri değişince) → ızgara dosyası (4 kanal) →  birleşik ısı (ağırlık GPU'da)
karo üretimi (tek seferlik)    →  statik karo (CPU harcamaz)  →  altlık + uydu (MapLibre)
```

Üç kural:

1. Model hiçbir zaman kullanıcı isteğinin içinde koşmaz.
2. Sunucu istek anında hesap yapmaz, hazır olanı dağıtır.
3. Tarayıcı çizimi GPU'da yapar, ana iş parçacığı yalnız arayüzle uğraşır.

---

## 3. Veri sözleşmesi ve depo

Bütün çıkarım çıktıları tek biçime iner:

```
(konum, hasar/aciliyet skoru, güven, zaman damgası, kaynak tipi)
```

PostGIS tabloları (GIST mekânsal indeksli): `damage_points`, `road_blockages`,
`sos_alerts`, `afad_assembly_points`, `osm_safety_polygons`, `users`.

Afetzede ihbarları (22 Eylül 2026, J-51) ayrı tabloda durur: `ihbarlar` ve
`ihbar_fotograflari`. Afetzede önce fotoğrafını ya da metnini modele inceletir; bu adım kayıt
açmaz. İhbarı gönderince kayıt açılır. Modelin çıktısı sunucudaki incelemeden okunur,
istemciden alınmaz. Model hasar ya da aciliyet çıkardıysa ihbar bu sözleşmeye de nokta
olarak düşer (kaynak `kamera` / `metin`). İhtiyaç talebi hasar değildir; ısıya yazılmaz.

Sevk görevi (22 Eylül 2026, J-54): her sevk `gorevler` tablosunda bir kayıttır. Kayıtta
şunlar var: olay (SOS ya da ihbar), ekip, giden kişi sayısı, atayan, durum ve her adımın
zamanı (atandı → yolda → olay yerinde → tamamlandı; her an iptal). `gorev_adimlari` her
adımı kimden geldiğiyle tutar: ekibin telefonu ya da koordinasyon. Kurallar
veritabanındadır:
- Bir ekibin tek açık görevi olur (kısmi benzersiz indeks). Aynı ekip iki yere birden
  gönderilemez.
- Olaya zaten ekip gidiyorsa ikincisi yalnız "ek destek" olarak gider.
- Olaydaki son görev bitince olayın durumu eşitlenir. İş bitti ise olay kapanır; iptal ya
  da "olay sürüyor" ise SOS kuyruğa döner.
- Olay kapatılınca açık görevler biter.

Ekipten olaya uzaklık ve süre (J-55) araç ağından gelir. Ağ, yerel OSM kopyasından
bölge başına bir kez üretilir (`araclar_arac_agi_uret.py`). Tek yönlere uyar ve bellekte
durur. Arama olaydan ters ağda tek Dijkstra'dır (medyan 22 ms) ve önbellektedir. Süre, yol
türüne göre ortalama hız varsayımıyla hesaplanır; anlık trafik yok.

Ekip ve olay farklı şehirlerdeyse bölgeler arası ağ kullanılır. Bu ağda beş şehir ve
aralarındaki ana yollar birliktedir (513 bin düğüm, arama medyan 111 ms). Şehir dışında ayrı
bir hız varsayımı vardır. Beş şehri kapsayan kutunun dışındaki ekip için kuş uçuşu yazılır.

API iki ara katmanla sarılıdır (25 Eylül 2026). **CORS** en dışta ve adres listesiyle
çalışır (J-60); yıldız değil, çünkü kimlik bilgisiyle birlikte yıldız her siteye kapı açar.
**Gzip** onun içindedir ve 500 bayttan büyük yanıtları 6. seviyede sıkıştırır (J-61); canlı
akış bunun dışındadır, çünkü akışlı yanıtta sıkıştırma olayları tamponlar ve kural 4'ü
çiğner. Ölçüm: konsolun açılışta istediği 16 ucun toplamı 660 KB → 134 KB.

Yetki durumu (24 Eylül 2026, J-53): 91 ucun 51'i rol ya da kimlik ister, 6'sı yalnız eski
webin kullandığı uçlardır ve varsayılanı kapalı bir bayrağın arkasındadır
(`QUAKEMIND_ESKI_UCLAR`), 34'ü hâlâ açıktır (dökümü J-59'da). Model koşturan uçlar —
kamera, metin ve uydu analizi — kimliksiz çalıştırılamaz.

Haritanın başvuru katmanları (24 Eylül 2026, J-56) tek bir modülden gelir
(`uclar/katmanlar.py`): yol kapanmaları depodan, depremler `query.csv` katalogundan
(Kandilli + USGS), fay hatları GEM etkin fay veri setinden, toplanma alanları AFAD
listesinden. Hepsi kutuyla sorulur, kimlik ister ve yanıtında kendi kaynağını taşır; arayüz
kaynağı koda gömmez. Dosyalar açılışta bir kez belleğe alınır, istek yolunda ayrıştırma
yoktur (kural 3). Bu katmanlar bölgeye göre değişmediği için istemci bir kez ister ve
önbellekte tutar; yalnız kapanmalar, analiz bitince gelen canlı mesajla tazelenir.

Ekibin görevde olup olmadığı saklanmaz, görevlerden okunur. Eskiden ekip üç çağrıya atanmış
iken "müsait" görünüyordu. `ekipler` tablosu kurum, tür ve kişi sayısı alanlarını kazandı.
`kullanicilar.ekip_id` saha hesabını ekibe bağlar. Eski veritabanı açılışta tamamlanır
(`ALTER TABLE ... ADD COLUMN`), veri kaybolmaz.

Eklenecek indeksler: zaman kolonlarında BRIN (append-only), `source_type` için kısmi
indeks, bölge kimliği için b-tree.

Arayüz modellere değil bu sözleşmeye bağlanır.

---

## 4. Çıkarım mimarisi

**Kuyruk.** İş kuyruğu için ek servis kurulmaz; Postgres tablosu + `FOR UPDATE SKIP LOCKED`
yeterlidir. İş kaydı: `(id, tip, parametreler, durum, ilerleme, sonuç, hata, zaman)`.

**İşçi süreç.** Modeller tek bir çıkarım işçisinde yüklenir. Bugün modeller
`fastapi_app.py:123-145` içinde, import sırasında yükleniyor; uvicorn birden çok worker ile
çalıştığında her worker aynı modelleri kendi belleğine ayrıca yükler.

**Model yükleme.** Tembel yükleme + uzun süre kullanılmayanı bellekten atma (LRU).
Hangi modüllerin açık olduğu yapılandırmayla belirlenir.

**Hız ve bellek.** Sıra: (1) ONNX Runtime'a geçiş, (2) BERT için dinamik int8 nicemleme,
(3) SegFormer pencerelerini toplu işleme, (4) iş parçacığı sayısını fiziksel çekirdeğe
sabitleme. Her adımdan sonra doğruluk (F1 / IoU) yeniden ölçülür ve kaydedilir.

**Eğitim.** Ayrı komut, çıktı dosyaya yazılır, API yalnızca yükler. CatBoost bugün
`risk_engine.py:408` → `:294` yolunda istek sırasında eğitiliyor (800 iterasyon, derinlik 8)
ve diske yazılmıyor.

---

## 5. Birleşik ısı haritası

Rapor 2.4.3'teki Gauss çekirdekli yoğunluk haritası, dört kanal (uydu, kamera, metin, SOS)
için **ayrı ayrı** üretilir.

**Hesap.** Noktaları metrik ızgarada say (`np.histogram2d`, ağırlık = skor × güven × zaman
sönümü), sonra tek bir Gauss bulanıklaştırması uygula (`scipy.ndimage.gaussian_filter`).
Maliyet "nokta × hücre" yerine "nokta + hücre" olur; nokta sayısından bağımsız hale gelir.
Bugünkü `apps/road_damage/utils/heatmap.py` her nokta için tüm ızgarayı Python döngüsüyle
geziyor.

**Geçiş şartı.** Yeni yöntem, eski fonksiyonla aynı girdide karşılaştırılır (hücre başına
en büyük fark raporlanır). Makaledeki sayılar değişmemeli.

**Ölçek.** Normalizasyon **mutlak** olur; istek başına maksimuma göre ölçeklenmez. Aksi
halde aynı mahalle, harita kaydırılınca başka renkte görünür (bugünkü davranış).

**Taşıma.** Dört kanal hücre başına 4 bayt olarak tek ikili dosyada gider. 25 m hücreli
10 × 10 km'lik bölge = 400 × 400 hücre = 640 KB (sıkıştırmasız).

**Karışım.** Ağırlıklı toplama ve renklendirme tarayıcıda, ekran kartında yapılır. Kullanıcı
ağırlığı değiştirince sunucuya istek gitmez. Negatif ağırlık desteklenir: "uydu yıkık
gösteriyor ama çağrı yok" sorusu böyle sorulur.

**Ekranda görünen = makaledeki.** Bant genişliği tanımı sunucuda kalır; istemci ikinci kez
bulanıklaştırma yapmaz. Bugünkü `leaflet.heat` sunucunun ızgarasını 28 piksel yarıçapla
yeniden bulanıklaştırıyor.

---

## 6. Canlı veri

Tek bir SSE akışı: `/api/live`. Sunucu yalnızca değişiklik olduğunda mesaj gönderir;
mesaj tipleri: yeni SOS, iş durumu, yeni analiz, ısı sürümü, ekip konumu.

**Durum (20 Eyl):** uç kuruldu — `backend/canli_yayin.py` (süreç içi olay yolu) +
`GET /api/live`. Bugün yayınlananlar: hasar analizi iş durumu (ilerleme, bitti, hata),
yeni analiz ve yeni SOS. Tek uvicorn worker'ı varsayar; çok worker'a geçilince
`yayinla` gövdesi Postgres `LISTEN/NOTIFY`'a bağlanacak, abonelik ve uç aynı kalacak.

Çoklu worker'da yayın için Postgres `LISTEN/NOTIFY` kullanılır; Redis gerekmez.

İstemci tarafında SSE mesajı ilgili sorguyu tazeler (TanStack Query). Yoklama yapılmaz.

**Durum (22 Eyl):**
- Mesaj tiplerine `bildirim` (J-45) ve `ihbar` (J-51: afetzede fotoğraf, yazılı ve ihtiyaç
  ihbarı ile durum değişikliği) eklendi.
- Afetzede yalnız kendi kaydının kimliğini ve durumunu alır.
- İstemci mesaja göre yalnız değişen sorguyu tazeler. Örnek: ihbar ısıya nokta yazdıysa
  yalnız o kanalın ızgarası tazelenir.
- Canlı modda sorguların bitişi açıktır. Eskiden son dakikaya bağlıydı ve yeni kayıt 60 sn'ye
  kadar geç düşüyordu (J-52). Başlangıç 15 dakikalık çapaya yuvarlanır (J-46).
- `gorev` mesajı eklendi (J-54): görev açıldı ya da durumu değişti. Konsol olayı, ekip
  listesini ve aday ekipleri tazeler.
- Afetzedeye gidenler: kendi olayının `gorev` mesajı ve o olaya giden ekibin `ekip-konumu`
  mesajı. Bu mesajlar koordinat taşımaz; istemci kendi çağrısını yeniden ister. Başka
  ekiplerin konumu gitmez.
- Ekibin telefonu konumunu sayfa açıkken gönderir: en çok 30 sn'de bir ya da 25 m'den fazla
  yer değişince. Bu yoklama değildir; cihaz konum verdikçe gider.

---

## 7. Arayüz mimarisi

- **Vite + React + TypeScript**, tek sayfa uygulaması. Statik dosyalara derlenir; çalıştırmak
  için Node sunucusu gerekmez.
- **Tek kalıcı harita.** Harita uygulama iskeletinde bir kez kurulur. Sayfalar yerine
  **modlar** vardır (genel durum, SOS, yol ve rota, hasar analizi, metin, risk); mod
  değişince yan paneller ve açık katmanlar değişir, harita yerinde kalır.
- **Rota bazlı kod bölme.** Afetzede ekranı analiz modüllerini indirmez. Harita motoru SOS formu
  çizildikten sonra tembel yüklenir. Form ilk açılışta 137 KB (gzip) JS ile çalışır; harita
  ~560 KB ile arkadan gelir. İhbar pencereleri de yalnız açılınca iner (J-51). Karar 22 Eylül
  2026'da kullanıcıdan geldi (J-50); önceki kural haritayı hiç indirmemekti.
- **Büyük veri ikili formatta** gelir (Arrow / typed array); JSON yalnız küçük yanıtlar için.
- **Ağır çözümleme Web Worker'da** yapılır; ana iş parçacığı bloklanmaz.
- Durum: sunucu verisi TanStack Query, arayüz durumu Zustand.

---

## 8. Harita veri hattı ve ölçek eşikleri

**Altlık bizim.** Yollar, yapılar ve su kendi verimizden çizilir (OSM + Copernicus).
Dışarıdan karo servisi zorunlu değildir; kullanılırsa yalnız kolaylık içindir.

**Yürüme yol ağı da bizim (22 Eylül 2026, J-44).** Beş bölgenin yürünebilir yolları
yerel OSM kopyasından bir kez üretilir: `araclar_yol_agi_uret.py` → `veri/yol_agi/`.
- Sunucu ağı bir kez belleğe alır (`yol_agi.py`).
- Afetzede rotası tek bir Dijkstra koşusudur (~25 ms). Araç motorunun hasar cezası
  (`risk_weight`) kullanılır; bilinen kapanmalar yumuşak maliyetle dolaşılır.
- Dış rota servisine yalnız yol ağı olmayan bölgede ve afetzede isteyince gidilir.

**Eşikler:**

| Katmandaki nesne sayısı | Yöntem |
|---|---|
| ≤ ~100 bin | Doğrudan gönder (ikili), tek katmanda çiz |
| > ~100 bin | Vektör karo (MVT): tarayıcı yalnız ekrandaki karoyu ve o zoom seviyesindeki ayrıntıyı ister |
| Zaman süzmesi, yüz binlerce olay | Süzmeyi ekran kartına taşı (deck.gl DataFilterExtension) ya da karo seviyesinde yap |
| Uydu görüntüsü | Bir kez karoya çevir (WebP piramidi / PMTiles); istek anında görüntü işleme yapma |

Isı haritası bu eşiklerden bağımsızdır: tarayıcı nokta sayısı ne olursa olsun tek bir doku
çizer.

**Bilinen kırılma noktaları:** büyük veriyi JSON ile göndermek (asıl darboğaz ayrıştırma),
düşük zoomda her nesneyi çizmek, çok sayıda etiketi aynı anda yerleştirmek, veriyi JS
nesneleri olarak bellekte tutmak.

---

## 9. Kimlik ve yetki

- Kimlik tek yerden verilir: FastAPI + kendi `users` tablosu + JWT. (Bugün web'de Firebase
  ile backend token'ı birbirini tanımıyor.)
- Şifre: bcrypt/Argon2. Erişim token'ı kısa ömürlü, yenileme token'ı httpOnly çerezde.
- Roller: afetzede · saha ekibi · koordinatör · yönetici. Rol yalnızca veritabanından okunur.
- Kayıt düzeyinde kontrol: afetzede yalnız kendi çağrısını görür; ekip yalnız kendi görevini
  bırakabilir.
- Sevk (J-54, 22 Eyl):
  - Koordinatör ve yönetici her ekibi gönderir, her görevi günceller.
  - Saha hesabı yalnız bağlı olduğu ekip adına çalışır: kendi ekibini gönderir, kendi
    görevini ve konumunu günceller.
  - Hesabı ekibe koordinasyon bağlar.
  - Afetzede kendi olayına giden ekibin adını, kişi sayısını, aşamasını ve görev açıkken
    konumunu görür (kullanıcı kararı). Kimin atadığını ve iç notu görmez.
- Bölge bazlı yetki (ekip yalnız atandığı bölgeleri görür) ikinci aşamada eklenir.

---

## 10. Ölçüm bütçeleri

Taban çizgi alınmadan iyileştirme yapılmaz. Ölçülecekler:

| Ölçüm | Hedef |
|---|---|
| Etkileşime tepki (INP) | < 200 ms |
| Mod geçişi | < 200 ms |
| Harita kaydırırken kare hızı (10 bin nokta) | 60 fps |
| İlk açılışta ana içerik (LCP) | < 2,5 s |
| Uç nokta gecikmesi (p95) | ölç, sonra hedef koy |
| Süreç başına RAM | ölç, sonra hedef koy |
| Sekme başına istek/dakika | SSE sonrası ~0 (yalnız değişiklikte) |

2209-A başvurusunun başarı ölçütlerinde bir `<500 ms` gecikme hedefi var
(`OPTIMIZASYON_ANALIZI.md` madde 47) ve bugüne kadar izlenmiyor.

---

## 11. Bugünkü kod ile hedef arasındaki fark

> **Durum notu (21 Eylül).** Aşağıdaki satırların çoğu kapatıldı; ölçümler
> `TASIMA_PLANI.md` Faz 1-4'te. Eski web'in kendi sorunları (yoklama, kendi
> harita örnekleri, keyfi yazı boyutları) devam ediyor — o taraf devralınana
> kadar dokunulmuyor.

| Bulgu | Yer | Ölçüm | Durum |
|---|---|---|---|
| Giriş, istemcinin gönderdiği rolle hesap açıyor | `fastapi_app.py:2333` | `"role":"admin"` gönderen admin oluyor | Yeni `/api/oturum/*` akışında kapatıldı; eski uç duruyor |
| Yetki kontrolü neredeyse hiç yok | `fastapi_app.py` | 44 uç noktanın 0'ında | Yeni uçların hepsinde `Depends` var |
| CatBoost istek yolunda eğitiliyor, diske yazılmıyor | `risk_engine.py` | 38,8 sn ilk istek | **Kapandı**: eğitim ayrı komut, istek ortanca 168 ms |
| Modeller her worker'da ayrı yükleniyor | `fastapi_app.py:123-145` | import sırasında | YOLO tembel yüklemeye alındı: API süreci 932 → 571 MB |
| Isı haritası nokta başına Python döngüsü | `utils/heatmap.py` | 20 bin noktada 15,8 sn | **Kapandı**: 14,7 ms (1.079×) |
| Isı, istek başına maksimuma göre ölçekleniyor | `utils/heatmap.py` | aynı yer farklı renkte | **Kapandı**: mutlak ölçek, referans yanıtta |
| `leaflet.heat` sunucunun ızgarasını yeniden bulanıklaştırıyor | `components/map/HeatmapLayer.tsx:19` | 28 px yarıçap + 22 px blur |
| Yoklama | `app/command/map/page.tsx` | sekme başına ~65 istek/dk |
| Her sayfa kendi haritasını kuruyor | `app/command/**` | 6 sayfada 8 harita örneği |
| Keyfi yazı boyutları | `quakemind-web/src` | 139 adet `text-[Npx]` |

---

## 12. Geçiş planı

1. **Ölç.** Yukarıdaki bütün satırlar için taban çizgi al.
2. **Backend düzeltmeleri** (yeni arayüzden bağımsız, eski web de faydalanır):
   kimlik ve yetki, modelleri işçiye taşıma, CatBoost'u dosyaya yazma, ısı haritasının
   hızlı yolu, `fastapi_app.py`'nin `APIRouter`'lara bölünmesi, tek SSE akışı.
3. **Yeni konsol iskeleti** (`konsol/`): giriş, kalıcı harita kabuğu, SSE, tasarım token'ları.
4. **Modları tek tek taşı:** en ağır ikisi (genel durum haritası, yol ve rota) önce.
5. **Devralma:** onay verilince `quakemind-web` yerini `konsol`a bırakır.

---

## 13. Karar günlüğü

| Tarih | Karar |
|---|---|
| 19 Eyl 2026 | Raspberry Pi ve internetsiz çalışma ertelendi; odak web + backend |
| 19 Eyl 2026 | Yeni arayüz Vite + React; Astro yalnız tanıtım sayfası için uygun (uygulama için değil), Next.js'in sunucu tarafı bu işte kazanç sağlamıyor |
| 19 Eyl 2026 | Harita: MapLibre + deck.gl, kendi harita stilimiz |
| 19 Eyl 2026 | Tek SSE akışı; yoklama kaldırılacak |
| 20 Eyl 2026 | Koyu tema; referans: Linear uygulaması + Zoom Earth |
| 20 Eyl 2026 | Isı haritası: kanal başına ızgara sunucuda, ağırlıklı karışım GPU'da, mutlak ölçek, negatif ağırlık desteklenir |
| 20 Eyl 2026 | Zaman aralığı varsayılan **canlı**: pencere şimdiye kilitli, geri çekilince geçmiş moduna geçer |
| 20 Eyl 2026 | Yeni konsol ayrı klasörde geliştirilir, onaydan sonra devralır |
| 22 Eyl 2026 | Ekip-olay uzaklığı araç yolundan (J-55): kendi araç ağımız, tek yöne uyar; süre yol türü hız varsayımıyla, trafik verisi yok. Konum 10 dakikadan eskiyse afetzedeye süre gösterilmez |
| 22 Eyl 2026 | Sevk bir görev kaydıdır (J-54). Ekip durumu görevden okunur. Durumu hem ekip telefonundan hem koordinasyon işaretler. Afetzede kendi olayına gelen ekibin adını, kişi sayısını ve konumunu görür |
