# QuakeMind — Afet Karar Destek Sistemi

QuakeMind, deprem sonrası ilk saatlerde koordinasyon merkezinin tek ekrandan karar
vermesine yardım eden bir karar destek sistemidir. Uydu/drone görüntüsünden hasar ve yol
kapanması, afetzede fotoğrafından çatlak ve yapı hasarı, Türkçe ihbar metninden kategori,
adres ve aciliyet çıkarır; bunları SOS çağrıları ve ekip konumlarıyla aynı haritada
birleştirir ve ekiplerin geçebileceği güzergâhı hesaplar.

Bütün modeller tek bir çıktı biçimine iner:

```
(konum, hasar/aciliyet skoru, güven, zaman damgası, kaynak tipi)
```

Arayüz modellere değil bu sözleşmeye bağlıdır; yeni bir model eklemek bu biçime uymak
demektir.

> Proje TÜBİTAK 2209-A kapsamında geliştirilmektedir. Kurallar `CLAUDE.md`'de, mimari
> `MIMARI.md`'de, tasarım sistemi `ARAYUZ_KARARLARI.md`'de, açık sorunlar
> `EKSIKLER_VE_SORUNLAR.md`'de kimlikli (J-…) olarak tutulur.

---

## İçindekiler

1. [Bileşenler](#bileşenler)
2. [Mimari](#mimari)
3. [Roller ve ekranlar](#roller-ve-ekranlar)
4. [Kurulum](#kurulum)
5. [Çalıştırma](#çalıştırma)
6. [Modeller](#modeller)
7. [Testler ve denetimler](#testler-ve-denetimler)
8. [Ortam değişkenleri](#ortam-değişkenleri)
9. [Repo yapısı](#repo-yapısı)
10. [Bilinen sınırlar](#bilinen-sınırlar)
11. [Belgeler](#belgeler)
12. [Lisans](#lisans)

---

## Bileşenler

| Bileşen | Klasör | Teknoloji | Durum |
|---|---|---|---|
| **API** | `backend/` | FastAPI, Python 3.10 (sunucu imajı 3.12), SQLite (WAL) | Çalışıyor; canlıda https://quakemind-api.dehaozcan.online |
| **Konsol** | `konsol/` | Vite + React 19 + TypeScript, MapLibre + deck.gl, Tailwind v4 | Çalışıyor; yeni arayüz |
| Tanıtım sitesi | `tanitim/` | Astro | İskelet |
| Eski web | `quakemind-web/` | Next.js | Olduğu gibi duruyor; yalnız kritik düzeltme. Onaydan sonra konsol devralır |
| Mobil uygulama | `mobile/` | Kotlin + Jetpack Compose, Room, WorkManager | Android istemcisi; ayrıntı `mobile/README.md` ve `mobile/docs/` |
| Streamlit modülleri | `backend/main.py`, `apps/` | Streamlit | Modellerin tek tek denendiği eski geliştirme arayüzü |
| Canlı kurulum | `deploy/` | Docker, Nginx | Sunucu kurulumu ve dağıtım adımları (`deploy/README.md`) |

Raspberry Pi ve internetsiz (hotspot) çalışma **ertelendi**; ayrı bir iş olarak ele
alınacak. Bugünkü sistem web + API, yanında Android istemcisi.

---

## Mimari

```
 Konsol (Vite + React, :3200)                   API (FastAPI, :8000)
 ─────────────────────────────                  ─────────────────────────────────────
 tek kalıcı harita (MapLibre + deck.gl)  ─REST→ uclar/  (uç modülleri, Depends ile yetki)
 tek canlı akış  GET /api/live (SSE)    ←SSE──  canli_yayin.py  (yalnız değişince mesaj)
 TanStack Query (tazeleme yalnız SSE ile)              │
                                                       ▼
                                                depo/sqlite_surucu.py  ── veri/quakemind.sqlite3
                                                       ▲
                                  işçi süreçler (uydu bölütleme, metin, kamera)
                                  ProcessPoolExecutor — modeller API'de değil işçide
```

Temel kurallar (ayrıntı `CLAUDE.md` ve `MIMARI.md`):

- **Pahalı iş istek yolunda çalışmaz.** Model çıkarımı işçi süreçte koşar; uzun işler
  HTTP 202 + iş kimliği döner, ilerleme canlı akıştan gelir. Model eğitimi ayrı bir
  komuttur (ör. `araclar_risk_egit.py`); API yalnız eğitilmiş modeli yükler.
- **Yoklama yok.** Konsol `setInterval` ile uç sorgulamaz; tek SSE akışı vardır.
  Bugün yayın süreç içidir ve tek uvicorn worker'ı varsayar.
- **Depo deseni.** Uçlar SQL görmez, yalnız depo yöntemlerini çağırır. ORM yok,
  parametreli SQL. Tek yazma bağlantısı + iş parçacığı başına okuma bağlantısı.
- **Veritabanı bugün SQLite'tır.** PostGIS hedef mimaridir; sürücüsü
  (`depo/postgis_surucu.py`) henüz yazılmadı. Eski `utils/postgis_manager.py` yalnız eski
  yol hasarı uçlarında, PostgreSQL olmadığı için yedek kipte çalışır.
- **Kimlik.** Rol asla istemciden gelmez. Kısa ömürlü (15 dk) HS256 erişim jetonu +
  httpOnly çerezde yenileme jetonu; jeton URL'de taşınmaz. Konsoldaki rol kapısı yalnız
  görünümdür, yetkiyi sunucu denetler.
- **Veri dürüstlüğü.** Her katman kaynağını yazar; senaryo/tatbikat verisi "senaryo"
  etiketiyle gösterilir, gerçek ölçümle aynı görünmez. Veri yoksa uydurulmaz, eksik
  olduğu yazılır.

---

## Roller ve ekranlar

Giriş ekranının üç kapısı vardır: **Afetzede · Saha ekibi · Koordinasyon**. Hesabın rolü
kapıya uymazsa sunucu girişi reddeder. Hesap açma yalnız Afetzede kapısındadır; ekip
hesaplarını koordinatör, koordinatör ve yönetici hesaplarını yönetici konsoldaki
**Kullanıcılar** ekranından açar. Boş bir sunucuda ilk yönetici
`araclar_kullanici.py ilk-yonetici` ile açılır (`deploy/README.md`).

Her ekranın sağ üstündeki profil simgesi **Hesap ayarları**na (`/hesap`: rol, şifre
değiştirme) ve **Çıkış yap**a götürür.

| Rol | Ekran | Ne yapar |
|---|---|---|
| `afetzede` | Afetzede ekranı (`src/afetzede/`) | SOS gönderir; fotoğraf, yazılı ihbar ya da ihtiyaç talebi bildirir; bildirimlerinin durumunu, gelen ekibi ve duyuruları canlı görür |
| `saha` | Ekip ekranı (`src/ekip/`) + konsol | Atanan görevi ve güzergâhı görür, görev adımlarını (yolda → olay yerinde → tamamlandı) bildirir; konsolu acil bildirim, kullanıcılar ve tatbikat modları olmadan görür |
| `koordinator` | Konsol | Aşağıdaki modlar; ekip hesaplarını yönetir |
| `yonetici` | Konsol | Koordinatörün yaptıkları + koordinatör/yönetici hesapları |

Konsolda sayfa yok, **mod** var: harita yerinde kalır, yalnız paneller ve katmanlar
değişir (`konsol/src/modlar/modlar.ts`).

| Mod | Amaç |
|---|---|
| Genel durum | Bütün kaynaklardan gelen hasar bilgisi ve ihbarlar tek haritada |
| SOS kuyruğu | Ekip bekleyen çağrılar, ekip gönderme (araç ağında ETA) |
| Ekipler | Hangi ekip nerede, neye gidiyor; ekip tanımları |
| İhtiyaç talepleri | Su, gıda, barınma gibi talepler; nerede ne eksik |
| Acil bildirim | Afetzede ekranlarına duyuru yayınlama / geri çekme |
| Kullanıcılar | Hesap açma, rol/ekip atama, askıya alma, işlem kaydı |
| Hasar analizi | Uydu/drone görüntüsünden yol kapanması çıkaran analiz |
| Kamera tespiti | İhbar fotoğraflarında çatlak ve yapı hasarı |
| Metin analizi | Türkçe ihbardan kategori, adres ve aciliyet |
| Deprem riski | 81 il için sismik geçmiş, fay uzaklığı ve son hareketliliğe dayalı risk |
| Simülasyon (tatbikat) | Gerçek görüntüde model koşturup rotaları tatbikat olarak dener |
| Yol ve rota | Kapalı yollar ve ekiplerin geçebileceği güzergâh |

---

## Kurulum

### Gereksinimler

| Gereksinim | Not |
|---|---|
| Python | 3.10 (depo kökündeki `venv/` bu sürümle kurulu) |
| Node.js | 20+ |
| RAM | 8 GB en az, 16 GB önerilir (uydu modeli işçide bellekte durur) |
| GPU | Gerekmez; çıkarım CPU'da koşar (en iyi model ile tatbikat ~78 sn) |

### API

Sanal ortam depo kökündedir:

```bash
python -m venv venv
venv/Scripts/python.exe -m pip install -r backend/requirements.txt   # Linux/macOS: venv/bin/python
```

Bir kez yapılacaklar:

```bash
# Risk modelini eğit (API modeli eğitmez; dosya yoksa risk uçları hata verir)
venv/Scripts/python.exe backend/araclar_risk_egit.py

# Yerel OSM yol ve tesis kesitini indir (hasar analizinin yol maskesi, tatbikatın yol ağı)
venv/Scripts/python.exe backend/araclar_osm_indir.py

# Demo hesaplarını aç (veritabanı depoya girmez, herkes kendi makinesinde kurar)
venv/Scripts/python.exe backend/araclar_demo_hesaplari.py
```

Yol dosyası (`roads.gpkg`) yoksa analiz yolları Overpass'a sorar; o da yanıt vermezse
sonuç "yol katmanı alınamadı" olur. Uydu modellerinin ağırlıkları ilk kullanımda
künyedeki Hugging Face kaynağından iner (bkz. [Modeller](#modeller)).

### Konsol

```bash
npm --prefix konsol install
```

### Mobil uygulama (isteğe bağlı)

Android Studio ile `mobile/` klasörünü açın. Windows'ta debug APK:

```powershell
cd mobile
.\gradlew.bat :app:assembleDebug
```

Emülatörde varsayılan backend adresi `http://10.0.2.2:8000/`'dir. Fiziksel cihazda
bilgisayarın LAN/hotspot IP'sini verin:
`.\gradlew.bat -PquakemindApiBaseUrl=http://<ip>:8000/ :app:assembleDebug`.
Bağlantı sözleşmeleri `mobile/docs/` altındadır.

---

## Çalıştırma

İki süreç:

```bash
venv/Scripts/python.exe -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000 --app-dir backend
```

```bash
npm --prefix konsol run dev
```

- Konsol: **http://localhost:3200** — `/api/*` istekleri 8000'e vekillenir. Başka bir
  API adresi için `QM_API=http://127.0.0.1:8001`.
- API belgeleri (Swagger): http://127.0.0.1:8000/docs
- API'nin açılması ~20 sn sürer; uydu modeli ilk analize kadar belleğe girmez.

Demo hesapları (yerelde `araclar_demo_hesaplari.py` açar; şifresi depoda açık olduğu
için yalnız yerel geliştirme içindir). Canlıda aynı dört hesap, sunucudaki
`QUAKEMIND_ORNEK_HESAP_SIFRESI` ile ve depoda yazmayan bir şifreyle kurulur; şifreleri
uygulamadan değiştirilemez (`deploy/README.md`):

| Rol | E-posta | Kapı |
|---|---|---|
| Yönetici | `yonetici-demo@quakemind.local` | Koordinasyon |
| Koordinatör | `demo@quakemind.local` | Koordinasyon |
| Saha ekibi | `saha-demo@quakemind.local` | Saha ekibi |
| Afetzede | `afetzede-demo@quakemind.local` | Afetzede |

Şifreler ve tatbikat sunum sırası: **`DEMO_CALISTIRMA.md`**.

> Kökteki `start.sh` eski düzeni (Next.js web) başlatır; konsol için yukarıdaki iki
> komutu kullanın.

---

## Modeller

Ağır model dosyaları depoya girmez; Hugging Face'ten indirilir ya da yerel yoldan yüklenir.

| Model | Görev | Kaynak |
|---|---|---|
| SegFormer MiT-B4 (etkin) | Uydu/drone görüntüsünde hasar bölütleme | `Utbird/dispath_optimized_mitb4_focal_dice30` |
| SegFormer B0 / B2 · U-Net MiT-B4 | Kıyas modelleri; tatbikattaki Hızlı / Dengeli / En iyi | `Furkei/quakemind-uydu-modelleri` |
| BERTurk sınıflandırıcı (`2kveri`) | İhbar metninin kategorisi ve aciliyeti | `Utbird/EqTwitterTr` (eksikse indirilir) |
| Adres dizini (kural tabanlı) | Metinden mahalle/sokak çözümü | `metin_analizi/adres.py`, yerel; ağa çıkmaz |
| YOLO `catlak.pt`, `bina.pt` | Fotoğrafta çatlak ve yapı hasarı | Depoda (`apps/camera_detection/models/`) |
| CatBoost risk modeli | 81 il deprem risk skoru | `araclar_risk_egit.py` üretir (`risk_catboost.cbm`) |
| Harita altlığı | Konsol zemin karoları | `Utbird/quakemind-altlik` (HF veri kümesi) |
| OSM yol ve tesis kesiti | Yol maskesi, tatbikat yol ağı, ekip üsleri | `Furkei/quakemind-osm-yollar` (HF veri kümesi, ODbL) |
| İl merkezleri | 81 il risk sıralaması | Depoda (`apps/earthquake_risk/data/il_merkezleri.json`, OSM) |

Uydu modellerinin künyeleri `backend/modeller/uydu/*.json`'dadır: mimari, ölçümler,
ağırlığın SHA-256'sı ve Hugging Face kaynağı (sabit sürüm). Ağırlık
`apps/road_damage/models/` altına iner; parmak izi tutmazsa yüklenmez. Etkin model
`QM_UYDU_MODELI` ile seçilir. Yeni model teslim süreci: `backend/modeller/README.md`.

Model doğruluğuyla ilgili sınırlar (duyarlılık, kalibrasyon) `DEMO_CALISTIRMA.md` §7 ve
`EKSIKLER_VE_SORUNLAR.md`'de yazılıdır; ölçülmemiş bir başarım iddiası yapılmaz.

---

## Testler ve denetimler

```bash
cd backend && ../venv/Scripts/python.exe -m pytest -q     # API testleri (~2 dk)
```

```bash
cd konsol && npx tsc -b --noEmit         # tip denetimi
npm --prefix konsol run kontrol:token    # keyfi değer denetimi (text-[13px], bg-[#…] yasak)
```

Dağıtım hazırlığı aynı testleri sunucu imajının içinde de koşturur (`deploy/deploy.sh`).

---

## Ortam değişkenleri

| Değişken | Ne işe yarar |
|---|---|
| `QUAKEMIND_JWT_ANAHTARI` | Jeton imza anahtarı. Tanımlı değilse her açılışta yenisi üretilir (oturumlar düşer) |
| `QUAKEMIND_SQLITE` | Veritabanı dosyası yolu (deneme için kopya DB) |
| `QUAKEMIND_CORS` | Geliştirme adreslerine eklenecek izinli kaynaklar, virgülle (yıldız kullanılmaz) |
| `QUAKEMIND_CEREZ_GUVENLI` | `1` ise yenileme çerezi `Secure` bayrağıyla yazılır (HTTPS altında) |
| `QUAKEMIND_ESKI_UCLAR` | Eski web'in kullandığı uçları açar; varsayılan kapalı |
| `QM_UYDU_MODELI` | Etkin uydu modeli künyesinin adı |
| `QUAKEMIND_LOCAL_OSM_PBF` | Yerel OSM PBF dosyası yolu (`araclar_yerel_osm_kur.py`) |
| `QUAKEMIND_OSM_DIZINI` | `roads.gpkg`'nin aranacağı dizin; yoksa `veri/osm`, sonra `apps/road_damage/data/osm` |
| `QUAKEMIND_ORNEK_HESAP_SIFRESI` | Tanımlıysa API açılışta dört ortak örnek hesabı bu şifreyle kurar (en az 10 karakter) |
| `QM_API` | Konsolun vekillediği API adresi (geliştirme) |

---

## Repo yapısı

```text
QuakeMind_Proje_Repo/
├── CLAUDE.md, MIMARI.md, ARAYUZ_KARARLARI.md   # kurallar, mimari, tasarım sistemi
├── PROJE_DOSYASI.md                            # akademik tanıtım (kanıt etiketli)
├── EKSIKLER_VE_SORUNLAR.md                     # açık sorunlar (J-…)
├── DEMO_CALISTIRMA.md                          # demo ve tatbikat sunumu
│
├── backend/
│   ├── fastapi_app.py        # uygulama girişi (uçları uclar/'dan bağlar)
│   ├── cekirdek.py           # işçi havuzu, iş kaydı, paylaşılan durum
│   ├── uclar/                # uç modülleri: oturum, sos, ihbar, gorev, ekip, kamera,
│   │                         #   metin, risk, rota, simulasyon, katmanlar, canli, …
│   ├── depo/sqlite_surucu.py # depo deseni; tablolar ve indeksler
│   ├── kimlik.py             # jeton, şifre, rol bağımlılıkları
│   ├── canli_yayin.py        # SSE yayını
│   ├── metin_analizi/        # metin işçisi: sınıflandırma + adres + çıkarım
│   ├── risk_hizmeti.py       # iş parçacığı güvenli risk hesabı
│   ├── apps/                 # modeller: road_damage, disaster_nlp, camera_detection,
│   │                         #   earthquake_risk
│   ├── modeller/uydu/        # uydu modeli künyeleri
│   ├── ornek_hesaplar.py     # ortak örnek hesaplar
│   ├── araclar_*.py          # tek seferlik komutlar (eğitim, ölçüm, veri hazırlama,
│   │                         #   ilk yönetici, OSM kesitini indirme)
│   ├── tests/, testler/      # pytest
│   └── veri/                 # SQLite, altlık, yol ağı, OSM kesiti (depoya girmez)
│
├── konsol/                   # yeni arayüz (Vite + React)
│   └── src/
│       ├── kimlik/           # giriş, rol kapısı, oturum, profil menüsü, hesap ayarları
│       ├── kabuk/            # üst çubuk, paneller, zaman şeridi, Ctrl+K
│       ├── harita/           # tek MapLibre örneği + deck.gl katmanları
│       ├── modlar/           # konsol modları
│       ├── afetzede/         # afetzede ekranı
│       ├── ekip/             # saha ekibi ekranı
│       ├── canli/            # tek SSE istemcisi
│       ├── veri/             # TanStack Query sorguları
│       └── stil/token.css    # tasarım token'ları (tek kaynak)
│
├── mobile/                   # Android istemcisi (Kotlin + Jetpack Compose)
├── deploy/                   # canlı sunucu kurulumu (Docker, Nginx, dağıtım betiği)
├── tanitim/                  # tanıtım sitesi (Astro)
├── prototip/                 # komuta konsolu prototipi
├── makale/                   # makale çalışma dosyaları
└── quakemind-web/            # eski web (Next.js)
```

---

## Bilinen sınırlar

- **Tek süreç varsayımı.** İş kuyruğu ve SSE yayını süreç içidir; sunucu yeniden
  başlarsa koşan işler kaybolur, birden çok worker desteklenmez. Hedef: Postgres tablosu
  + `FOR UPDATE SKIP LOCKED` ve `LISTEN/NOTIFY`.
- **PostGIS yok.** Mekânsal sorgular SQLite'ta `(lon, lat)` b-tree indeksiyle kutu
  sorgusudur.
- **Uydu modeli bina hasarı bulur**; yol kapanması bundan türetilir (yol hasarı etiketi
  yok). Duyarlılığı düşüktür.
- **Tatbikatın afetzede konumları üretilmiş veridir** ve arayüzde "senaryo" etiketiyle
  gösterilir. Tatbikat noktaları koşu bitince ya da API yeniden açılınca silinir; gerçek
  veriye karışmaz.
- **Süre tahmini** yol türüne göre ortalama hız varsayımıdır; anlık trafik yoktur.

Güncel ve ayrıntılı liste: `EKSIKLER_VE_SORUNLAR.md`.

---

## Belgeler

| Belge | İçerik |
|---|---|
| `CLAUDE.md` | Geliştirme kuralları (veri dürüstlüğü, sözleşme, kuyruk, yoklama yasağı, kimlik) |
| `MIMARI.md` | Katmanlar, veri sözleşmesi, ölçek eşikleri, ölçüm bütçeleri |
| `ARAYUZ_KARARLARI.md` | Renk ve tip token'ları, bileşenler, panel kuralı |
| `PROJE_DOSYASI.md` | Sistem ve veri mimarisinin akademik tanıtımı |
| `EKSIKLER_VE_SORUNLAR.md` | Açık sorunların kimlikli (J-…) takibi |
| `DEMO_CALISTIRMA.md` | Demo hesapları, tatbikat sunumu, ölçülen süreler |
| `konsol/README.md` | Konsolun yapısı ve kuralları |
| `backend/modeller/README.md` | Uydu modeli künyesi ve teslim süreci |
| `deploy/README.md` | Canlı sunucu: dağıtım, ilk hesaplar, analiz dosyaları |
| `mobile/README.md` | Android istemcisi |

---

## Lisans

Bu proje **tescillidir ve tüm hakları saklıdır** (All Rights Reserved). Açık kaynak bir
lisans **değildir**.

Telif hakkı sahibinin önceden yazılı izni olmaksızın bu depodaki kodun, belgelerin, model
dosyalarının veya herhangi bir materyalin kopyalanması, dağıtılması, değiştirilmesi veya
herhangi bir amaçla (ticari veya değil) kullanılması **yasaktır**.

Ayrıntılar için bkz. [`LICENSE`](./LICENSE).
