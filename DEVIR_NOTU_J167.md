# Devir notu — J-167 bulgularını düzelt (17 Kasım 2026)

Bu not, 17 Kasım'daki uçtan uca taramanın (J-167) bulgularını düzeltecek bir sonraki
Claude oturumu içindir. Bulguların tam metni: `EKSIKLER_VE_SORUNLAR.md` → **J-167**
başlığı. Bu not onu tekrarlamaz; **ne sırayla, nasıl düzeltileceğini ve neyin "bitti"
sayılacağını** söyler.

---

## Durum — 17 Kasım akşamı (önce bunu oku)

**Bitti: Grup A, B, C.** Ayrıntı ve ölçümler `EKSIKLER_VE_SORUNLAR.md` J-167 içinde, her maddenin
altında "✅ Düzeltildi" satırıyla.
- **A** (testler): T-1a, T-1b.
- **B** (güvenlik): S-1, S-2 + U-3, S-3, S-4, S-6. S-5 bilerek Grup D'ye bırakıldı.
- **C** (saha ve giriş arayüzü): U-1, U-2 + P-5, U-4, U-6.
- Ek olarak P-6 (artımlı zincir doğrulaması) J-166'da yapıldı.

**Bu notun eskiyen satırları:**
- "J-166'nın EKSIKLER'de maddesi yok" → artık var (J-166).
- "66/68" → `pytest -q` **89/89**.
- "T-2 eski kod" → API yeniden başlatıldı.
- Sıradaki boş kimlik **J-170**. J-168 (eski web uydurma kamera sonucu, karar kullanıcıda) ve J-169
  (başarısız yazma kilidi, kapalı) açıldı.

**Canlıya alırken (Deha):**
- Nginx arkasında `QUAKEMIND_VEKIL_GUVENILIR=1`; yoksa adres başına sınırlar uygulanmaz.
- `QUAKEMIND_BELGELER` açılmamalı.

**Grup D yapıldı (17 Kasım, J-170; `metin-analizi` dalı, commit edilmedi):** yerel adres
dizini, model işçide, metin ekranları yeniden. Kategori kararı gerçek sınama kümesi olmadan
değiştirilmedi. Ayrıntı ve açık kalanlar `EKSIKLER_VE_SORUNLAR.md` J-170'te.

**Grup E yapıldı (18 Kasım, J-171; `rota-ve-grup-e` dalı):** Yol ve rota bağlandı, araç rotası
kenar tabanlı; zaman şeridi, Nereye kartı, Türkçe metinler, kapsamasız görüntüler.

**Sıradaki iş: Grup F**, sonra G. Aşağıdaki sıra geçerli.

Commit durumu: A, B ve C, J-165 ve J-166 ile birlikte `kamera-analiz-gelistirme` dalında,
**commit edilmedi** (kullanıcı söyleyince).

---

## 0. Başlamadan önce oku

1. `CLAUDE.md` (kurallar — istisnasız), `MIMARI.md`, `ARAYUZ_KARARLARI.md`.
2. `EKSIKLER_VE_SORUNLAR.md` → J-167 (bulgular), J-162…J-165 (son işler).

### Çalışma ağacında commit edilmemiş iş var — KAYBETME

Dal `kamera-analiz-gelistirme`. Ağaçta J-165 ve J-166 (ekip konum geçmişi, işlem kaydı
hash zinciri: `islem_kaydi.py`, `uclar/islem.py`, `konsol/src/modlar/islemKaydi.tsx` …)
**commit edilmemiş** duruyor.
- `git stash`, `git reset`, `git checkout -- …`, dal değiştirme **yapma**.
- J-166'nın kodda kullanıldığı hâlde `EKSIKLER`'de maddesi yok; istersen kısa bir madde aç.

### Ekip kuralları (kullanıcının yerleşik tercihleri)

- **Türkçe** yaz (yanıtlar, commit mesajları, EKSIKLER maddeleri).
- **Commit / push / dağıtım yok** — kullanıcı o an açıkça söylemedikçe.
- Commit'e ve PR'a **`Co-Authored-By` ya da "Generated with Claude Code" ekleme**
  (GitHub katkıcı listesine düşüyor).
- `EKSIKLER_VE_SORUNLAR.md`'yi başka sohbetler de aynı anda düzenliyor; commit'e yalnız
  kendi bloğun girsin (`git add -p`).
- Bulduğun her yeni sorunu `EKSIKLER`'e kimlikli yaz (sıradaki boş kimlik J-168).
  Düzelttiğin bulguyu J-167 içinde "✅ düzeltildi (dosya:satır)" diye işaretle ve
  değişiklik günlüğüne satır ekle.
- **Prettier çalıştırma** (`npx prettier` tırnakları/noktalı virgülleri değiştirip diff'i bozar).
- Konsol kontrolü: `npx tsc -b` ve `npm run kontrol:token` (konsol/ içinde).
  `npm run kontrol` **kullanma** — src'ye `.js` döküyor (J-57).
- Tasarım token'ları dışında keyfi değer yok (`text-[13px]` gibi) — CI kontrol eder.
- Kimlik/istemci tarafına dokunduysan oturumsuz açılışı da dene (çerezsiz `127.0.0.1`,
  J-49 "Yükleniyor…" kilidi).
- "Hızlandı" demek için önce/sonra ölçüm (CLAUDE.md §8).
- Kullanıcının makinesinde GPU yok; uzun CPU işlerinde süreyi önceden söyle.

### Ortam

- Backend: `venv/Scripts/python.exe -m uvicorn fastapi_app:app --app-dir QuakeMindBackend --port 8000`
  (`.claude/launch.json` → `api`). Açılış ~30 sn.
- **8000'de koşan API eski kodla çalışıyor olabilir (T-2)** — denemeden önce yeniden başlat.
- Konsol: `npm --prefix konsol run dev` → 3200 (`launch.json` → `konsol`).
- Gerçek veritabanını kirletme: denemeyi DB kopyasında yap
  (`QUAKEMIND_SQLITE=<kopya yolu>` ile ayrı port; `launch.json`'da `konsol-8001` hazır,
  8001 için API girdisini geçici ekle, işin bitince geri al).
- Demo hesapları (`araclar_demo_hesaplari.py`, şifre `degistir1234`):
  `yonetici-demo@`, `demo@` (koordinatör), `saha-demo@` (ekip EKP-01), `afetzede-demo@`
  — hepsi `@quakemind.local`.
- Testler: `cd QuakeMindBackend && ../venv/Scripts/python.exe -m pytest -q` (~90 sn;
  şu an 66/68, kırık ikisi T-1).

---

## 1. İş sırası

Her grup ayrı, küçük, kendi başına doğrulanmış bir adım olsun. Kullanıcı "commit et"
derse grup başına bir commit uygundur.

### Grup A — Testler (ilk, çünkü sonraki her şey bunlara dayanır)

**T-1a** `tests/test_islem_kaydi.py::test_konum_gecmisi_tutulur` sıraya bağlı.
`test_islem_kaydi.py:116` civarındaki test saha hesabını başka ekibe taşıyor, 220'deki
test EKP-K'ya yazamayıp 403 alıyor.
- Düzelt: testler fixture'ı paylaşmasın (fixture kapsamını `function` yap ya da taşıyan
  test sonunda geri alsın ya da konum testi kendi saha hesabını kursun).
- Bitti: dosyanın tamamı ve tek tek koşunca geçiyor.

**T-1b** `tests/test_road_damage_api.py::test_heatmap_offline_fallback_returns_200`
uç artık oturum istiyor (401). Testi oturumlu çağırmaya çevir **ve** oturumsuzken 401
döndüğünü ayrı bir testle sabitle. Ucu tekrar açma.

Bitti: `pytest -q` 68/68.

### Grup B — Güvenlik (öncelikli)

**S-1 Giriş denemesi sınırı.** (`kimlik.py`, giriş ucu)
- Hesap + IP başına kayan pencere sayacı (ör. 15 dk'da 5 yanlış → 429 + `Retry-After`).
- Tek uvicorn worker varsayımı geçerli (CLAUDE.md §4); bellek içi sayaç yeter, ama
  SQLite'a yazmak yeniden başlatmada da korur — kararı gerekçesiyle EKSIKLER'e yaz.
- Hesap var/yok farkı sızdırılmasın (aynı ileti, benzer süre).
- Konsol giriş ekranı 429'u insan diliyle göstersin ("Çok fazla deneme, X dk sonra").
- Test: 6. yanlış denemede 429; doğru şifre de kilit süresince 429; süre sonunda açılıyor.

**S-2 + U-3 SOS seli.** (`uclar/sozlesme.py` / SOS ucu, `depo/sqlite_surucu.py`)
- Hesap başına **tek açık SOS**: açık SOS varken yenisi gelirse yeni satır açma, mevcut
  olanı güncelle (konum, zaman damgası, varsa not) ve 200 + mevcut kimliği dön.
- Ek olarak hesap ve IP başına dakikalık sınır (429). Kayıt ucuna IP sınırı.
- Isı haritası ve kuyruk bir kişiyi bir kez saysın.
- Konsol kuyruğunda aynı kişinin satırı tek görünsün ("3 kez güncellendi" bilgisiyle).
- Afetzede ekranı ikinci basışta "SOS'un zaten iletildi, konum güncellendi" desin.
- Test: 30 hızlı SOS → tabloda 1 açık satır; kapandıktan sonra yeni SOS yeni satır açar.
- Yeni sorguda `EXPLAIN QUERY PLAN` ile tablo taranmadığını doğrula (CLAUDE.md §10).

**S-3 Kamera bilinmeyen `modelType`.** (`uclar/kamera.py:255` civarı)
- Yalnız `catlak | bina | hybrid` kabul et; başka değer → 422 (Pydantic `Literal`).
- `activeModels` yalnız gerçekten çalışan modelleri yazsın; sahte yedek liste kalksın.
- Test: `modelType="ikisi"` → 422; `hybrid` → iki model de gerçekten listede.

**S-4 Belgeler açık.** `/docs`, `/redoc`, `/openapi.json`'u ortam değişkenine bağla
(ör. `QUAKEMIND_BELGELER=1` değilse kapalı). Varsayılanı geliştirmede açık bırakmak
istersen bunu açıkça yaz; üretimde kapalı olmalı. Konsol `openapi.json`'a bağımlı mı,
bak (bağımlıysa kırma).

**S-6 Canlı akışta askıya alma.** (`uclar/canli.py`)
- Akış döngüsü belirli aralıkla (ör. her 60 sn ya da her mesajda ucuz kontrol)
  kullanıcının hâlâ etkin olduğunu doğrulasın; askıya alındıysa akışı kapatsın.
- Ya da askıya alma işlemi o kullanıcının açık akışlarını kapatsın (yayın süreç içi).
- Test: akış açıkken hesabı askıya al → akış kapanıyor.

**S-5 Nominatim'e adres gitmesi** (`apps/disaster_nlp/src/ner_extraction.py:120`)
— büyük iş, **P-2 ve F-1 ile birlikte** Grup D'de.

### Grup C — Saha ve giriş arayüzü

**U-1 Saha ana düğmesi ekran dışında.** 375×812'de "Yola çıktık" y≈800.
- Adım düğmeleri (yola çıktık / vardık / bitti) yapışkan alt çubukta, her zaman görünür.
- "Rotayı haritada göster" ikincil vurguya insin.
- Bitti: 375×812'de birincil düğme kaydırmadan görünür; güvenli alan (`env(safe-area-inset-bottom)`) hesaba katılmış.

**U-2 + P-5 API açılırken ham "HTTP 500".**
- Backend: `/api/hazir` (ya da `/health`) ucu — modeller/DB hazır olunca 200, değilse 503.
  Oturumsuz uç listesine gerekçesiyle ekle.
- Konsol giriş ekranı 5xx/ağ hatasında "Sunucu açılıyor, birkaç saniye…" desin; ham yol ve
  HTTP kodu göstermesin. Yoklama yasağına (§4) dikkat: kullanıcı tekrar bastığında dene ya
  da tek seferlik geri sayımlı yeniden deneme; `setInterval` ile sürekli yoklama yok.

**U-4 Tatbikat lejantı haritayı kapatıyor.** "Haritada ne var" kutusu varsayılan kapalı.

**U-6 Afetzede adsız düğmeler.** Yer listesi satırları ve alt kartlara `aria-label`.

### Grup D — Metin modeli ve adres (en büyük iş) — ✅ J-170

**F-1 + P-2 + S-5** birlikte ele alınmalı:
- Örnek cümle "Armutlu Mahallesi 5. Sokak'ta bina çöktü, iki kişi enkaz altında…"
  adres bulamıyor, kategori "Acil Yardım İhtiyacı" çıkıyor (enkaz olmalı), ilk istek 31,8 sn.
- Yapılacak:
  1. Model API sürecinde tembel yükleniyor → çıkarım işçisinde açılışta ısıt
     (CLAUDE.md §3: modeller işçide durur).
  2. Adres çözümünü yerel yap: altlıktaki mahalle/sokak verisinden (repoda Hatay mahalle
     sınırları var, bul) bulanık eşleme. Nominatim çağrısı kalksın ya da bayrak arkasına girsin.
  3. NER kuralını "X Mahallesi", "N. Sokak", "Cad." kalıplarını yakalayacak şekilde
     güçlendir; kategori için enkaz anahtar kelimelerini gözden geçir.
- Ölç: önce/sonra, en az 20 Türkçe örnek cümleyle (DepremKit / TSEqD'den ya da gerçek
  ihbar örneklerinden — **uydurma veri yok**, sentetikse etiketli). Adres bulma oranı ve
  ilk/sıcak istek süresi EKSIKLER'e `[Ö]` etiketiyle yazılsın.

**F-2 Koordinatla gelen SOS'ta mahalle boş.** Sunucu SOS'u yazarken koordinattan
mahalleyi (nokta-çokgen) bulup kayda eklesin. Konsol ve saha ekranı ham koordinat yerine
mahalle adını göstersin (koordinat ikincil).

### Grup E — Ölü ve yanıltıcı ekranlar — ✅ J-171

**F-3 "Yol ve Rota" sayfası ölü.** Görev ekranındaki rota (J-162) zaten var.
Ya o ucu bu sayfaya bağla ya da sayfayı menüden kaldır. Hangisi olacağını **kullanıcıya sor**.

**F-4 Zaman şeridi.** `konsol/src/kabuk/ZamanSeridi.tsx:114-119` histogram hiç yazılmamış,
metin "canlı akış bağlanınca dolacak" diyerek yanıltıyor.
- En az: metni doğrula ("Olay yoğunluğu grafiği henüz yok").
- Doğrusu: saat başına olay sayısı ucu (sayım SQL'de, §10 — satırları Python'a çekme)
  ve şeritte çubuk grafik. Yeni zaman pencereli sorgu → `EXPLAIN QUERY PLAN`.

**F-6** Tatbikat ilerleme metinlerinde Türkçe karakter ("Uydu goruntusu", "tamamlandi");
drone katmanında "Uydu" yazısı.

**F-7** Hasar sayfası kapsaması %0 olan görüntüleri listelemesin (ya da altta, soluk, "kapsam yok").

**F-5** Afetzede "Nereye" kartında İtfaiye 0, Polis 0 (Antakya merkezi). Önce yerel OSM
kopyasında bu türler var mı bak; yoksa kartta "veri yok" de, 0 deme (CLAUDE.md §1).

### Grup F — Performans (ölçerek)

Her madde için önce taban ölçüm, sonra iyileştirme, sonra yeniden ölçüm.
- **P-1** Harita parçası 2,08 MB (gzip 574 KB); afetzede de deck.gl yüklüyor
  (`konsol/src/afetzede/haritaKatmanlari.ts`). Afetzede haritasını yalnız maplibre ile çiz,
  deck.gl'i yalnız konsolda yükle. Ölç: afetzede gzip JS toplamı (şu an ≈ 711 KB).
- **P-3** Isı haritası soğukken 4 istek 4,3 sn, sıcakken 28 ms. Açılışta ısıt ya da 4
  kaynağı tek uçta dön.
- **P-4** Tatbikatta yol ağı 12,4 sn, görüntü 12,6 sn; `DEMO_CALISTIRMA.md` §4'e göre
  önbellekten 0–1 sn olmalı. Katalog alanlarının önbelleğini kontrol et / önceden indir.
- **P-6** `/api/islem-kayitlari/dogrula` her seferinde bütün tabloyu tarıyor. Son
  doğrulanan kimliği sakla, yalnız sonrasını doğrula (artımlı) ya da sayfalı yap.

### Grup G — Küçük

**U-5** Konsol metninin %87'si 11–12 px. Token ölçeğini (`ARAYUZ_KARARLARI.md`)
kullanıcıyla konuşmadan değiştirme; öneri olarak sun.

---

## 2. Her grup sonunda

1. Backend: `pytest -q` yeşil (yeni testler dahil).
2. Konsol: `npx tsc -b` ve `npm run kontrol:token` temiz.
3. Arayüz değiştiyse tarayıcıda dene: 1440×900 ve 375×812, oturumlu ve oturumsuz.
4. `EKSIKLER` J-167'de ilgili satırı "✅ düzeltildi" yap, günlüğe satır ekle.
5. Kullanıcıya ne değiştiğini ve neyin doğrulanmadığını söyle; commit için izin bekle.

## 3. Kullanıcıya sorulacaklar

- F-3: "Yol ve Rota" sayfası bağlansın mı, kaldırılsın mı?
- S-4: Belgeler geliştirmede açık kalsın mı?
- S-1: Kilit sayacı bellekte mi, SQLite'ta mı?
- Grup D büyük; başlamadan önce yaklaşımı (yerel adres dizini) onaylat.

## 4. Taramada denenmeyenler (fırsat olursa)

- Fotoğraf yükleme tarayıcıda denenmedi (yalnız API ile).
- Uydu hasar analizi ve risk tahmini tarayıcıda koşulmadı.
- Yavaş ağ (3G) ve düşük cihaz ölçümü yapılmadı.
