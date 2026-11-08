# QuakeMind — Geliştirme Kuralları

Bu dosya proje genelinde uyulacak kuralları içerir. Claude Code ve insan geliştiriciler
bu kuralları **istisnasız** uygular. Ayrıntılar iki belgede:

| Belge | İçerik |
|---|---|
| `MIMARI.md` | Yazılım mimarisi: katmanlar, veri sözleşmesi, işin nerede yapıldığı, ölçek eşikleri, ölçüm bütçeleri |
| `ARAYUZ_KARARLARI.md` | Tasarım sistemi: renk ve tip token'ları, bileşenler, hareket, düzen, panel kuralı |
| `PROJE_DOSYASI.md` | Sistem ve veri mimarisinin akademik tanıtımı (kanıt etiketli) |
| `EKSIKLER_VE_SORUNLAR.md` | Açık sorunların kimlikli takibi |

Son güncelleme: 20 Eylül 2026.

---

## 1. Veri dürüstlüğü — her sayının bir kaynağı vardır

Bu projenin çıktısı bir makale ve bir karar destek sistemi. İkisinde de uydurma veri
kabul edilmez.

- Gerçek bölge, gerçek görüntü, kendi modelimizin çıktısı ya da açık lisanslı veri kullanılır.
- Sentetik veri **yalnızca** etiketli ve gerçeğiyle eşleştirilmiş olarak kullanılır.
- **Arayüzde her katman kaynağını yazar.** Senaryo verisi "senaryo verisi" diye etiketlenir,
  gerçek ölçümle aynı görünmez. Prototipte SOS çağrılarının saatleri üretildiği için bu
  durum veri kaynakları panelinde açıkça yazılıdır — aynı disiplin üründe de sürer.
- Bir halka için gerçek veri yoksa uydurulmaz, eksik olduğu söylenir.
- Kanıt etiketleri `[Ö]` ölçülmüş · `[K]` kodda · `[A]` atıfla · `[T]` tasarım kararı ·
  `[Y]` yapılmadı (bkz. `PROJE_DOSYASI.md`). Makaleye yalnız `[Ö]` ve `[K]` taşınır.

## 2. Ortak çıktı sözleşmesi — bütün modeller aynı biçime iner

Uydu bölütlemesi, kamera tespiti, metin analizi ve acil çağrı; hepsi tek biçime indirgenir:

```
(konum, hasar/aciliyet skoru, güven, zaman damgası, kaynak tipi)
```

Bu kayıtlar PostGIS `damage_points` tablosunda toplanır. **Yeni bir model eklemek, bu
sözleşmeye uymak demektir.** Arayüz modellere değil bu sözleşmeye bağlanır; bu yüzden
arayüz, modeller bitmeden geliştirilebilir.

## 3. Pahalı iş kullanıcı isteğinin içinde çalışmaz

Model çıkarımı, model eğitimi, ızgara hesabı ve karo üretimi istek yolunda yapılmaz.

```
İstek  →  iş kuyruğu (Postgres tablosu + SKIP LOCKED)  →  işçi süreç
                                                        ↓
arayüz  ←  SSE "yeni veri var"  ←  sonuç tabloya yazılır
```

- Modeller API sürecinde değil, tek bir çıkarım işçisinde bellekte durur.
- Eğitim ayrı bir komuttur; model dosyaya yazılır, API yalnız yükler.
  (Bugün ihlal ediliyor: `apps/earthquake_risk/risk_engine.py:408` ilk risk isteğinde
  CatBoost eğitiyor ve diske yazmıyor.)
- Uzun işler HTTP 202 + iş kimliği döner; istemci yoklamaz, SSE dinler.

## 4. Canlı veri tek akıştan gelir — yoklama yasak

`setInterval` ile uç nokta yoklamak yasaktır. Tek bir SSE akışı vardır, sunucu yalnızca
değişiklik olduğunda mesaj gönderir (Postgres `LISTEN/NOTIFY`).

Ölçüm: bugünkü `quakemind-web/src/app/command/map/page.tsx` sekme başına dakikada ~65
istek atıyor, hiçbir şey değişmese bile.

## 5. Kimlik ve yetki

- **Rol asla istemciden gelmez.** Kayıt ve giriş uçları istemcinin gönderdiği rolü kabul
  etmez. (Bugün ihlal ediliyor: `backend/fastapi_app.py:2333`.)
- Her uç noktada yetki kontrolü bir bağımlılıkla (`Depends`) yapılır. Bugün 43 uç noktanın
  yalnız 3'ünde var.
- Kısa ömürlü erişim token'ı + httpOnly çerezde yenileme token'ı. Token URL'de taşınmaz.
- Arayüzdeki yönlendirme koruması yalnız görünümdür, güvenlik değildir.

## 6. Arayüz kuralları (özet — ayrıntısı `ARAYUZ_KARARLARI.md`)

- Tasarım token'ları tek dosyada; **keyfi değer yasak** (`text-[13px]`, `bg-[#0b0f17]`).
  CI bunu kontrol eder. Bugünkü web'de 139 keyfi piksel yazı boyutu var.
- Cam efekti (backdrop-blur), neon parlama, gradyan zemin ve sürekli yanıp sönen öğe yok.
- **Her panel ne işe yaradığını kendi yazar:** tek cümlelik amaç, altında gerçek soruları
  temsil eden hazır seçenekler, ince ayar en altta.
- Kırmızı, turuncu ve sarı yalnız hasar ve aciliyet içindir; marka rengi olamaz.
- Harita tek örnektir, sayfa değişiminde yeniden kurulmaz.

## 7. Yeni konsol ayrı geliştirilir

Yeni arayüz `konsol/` altında sıfırdan yazılır (Vite + React). Mevcut `quakemind-web/`
(Next.js) **olduğu gibi kalır**; onay verilene kadar ikisi yan yana durur, onaydan sonra
yeni konsol devralır. Eski web'de yalnız kritik düzeltme yapılır.

## 8. Ölçmeden iddia yok

- Performans, doğruluk ve "hızlandı" iddiaları ölçümle kanıtlanır.
- Ölçümden önce **sayma birimi ve hedef** yazılır (ne ölçüyoruz, hangi cihazda, kaç kayıtla).
- Taban çizgi (baseline) alınmadan iyileştirmeye başlanmaz.
- Modelde nicemleme veya mimari değişikliği yapılırsa doğruluk (IoU / F1) yeniden ölçülür;
  makaledeki model ile üründe koşan model farklıysa bu makalede belirtilir.

## 9. Dal, commit ve dağıtım

- Bu çalışma kopyasında `origin` `geniusprr/QuakeMind`, `upstream` `UtBird/QuakeMind`; aktif geliştirme dalı `deha/backend-gelistirme`.
- İş, konusuna göre ayrı bir dalda yapılır; `main` doğrudan değiştirilmez.
- **Commit, push ve dağıtım kullanıcı o an açıkça söylemeden yapılmaz.**
- Ağır model dosyaları depoya girmez, Hugging Face'ten indirilir (bkz. `backend/README.md`).

## 10. Kapsam notları (20 Eylül 2026)

- Raspberry Pi ve internetsiz çalışma **ertelendi**, ayrı bir iş olarak ele alınacak.
  `backend/OPTIMIZASYON_ANALIZI.md`'nin Pi/offline bölümleri şu an geçerli değil.
- 7 Kasım 2026 itibarıyla eski Flutter klasörü yerini `mobile/` altındaki Kotlin/Compose Android uygulamasına bıraktı; Android-backend entegrasyonu geliştirme kapsamındadır.
- `OPTIMIZASYON_ANALIZI.md` içindeki durum alanları bayat (hepsi "Bekliyor" görünüyor ama
  bazıları yapılmış). Oradan madde kullanmadan önce koda bak.
