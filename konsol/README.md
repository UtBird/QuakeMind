# QuakeMind Konsol

QuakeMind'ın arayüzü: koordinasyon konsolu, afetzede ekranı ve saha ekibi ekranı tek
uygulamada. Vite + React 19 + TypeScript + Tailwind v4; tek kalıcı harita (MapLibre +
deck.gl), tek SSE akışı. Eski `quakemind-web/` (Next.js) olduğu gibi durur; onay verilene
kadar ikisi yan yanadır (CLAUDE.md kural 7).

Kaynak belgeler: `../CLAUDE.md` · `../MIMARI.md` · `../ARAYUZ_KARARLARI.md`
Referans prototip: `../prototip/komuta-konsolu/`

## Çalıştırma

```bash
npm --prefix konsol install
npm --prefix konsol run dev      # http://localhost:3200
```

API (FastAPI) ayrıca çalışmalı; nasıl başlatılacağı kök `README.md`'de. Geliştirmede
`/api/*` istekleri `http://127.0.0.1:8000` adresine vekillenir. Başka bir adres için:
`QM_API=http://127.0.0.1:8001 npm --prefix konsol run dev`.

> Aynı anda iki backend çalışıyorsa (biri `0.0.0.0:8000`, diğeri `127.0.0.1:8000`)
> istekler ikisi arasında bölünür: bir uçta açılan iş öbür uçta "bilinmeyen kimlik"
> olur. Böyle bir durumda backend'i ayrı bir porta alıp `QM_API` ile göster.

Giriş için demo hesapları `../DEMO_CALISTIRMA.md` §2'de.

```bash
npm --prefix konsol run build          # dist/ — statik dosyalar, Node sunucusu gerekmez
npx --prefix konsol tsc -b --noEmit     # tip denetimi (`kontrol` betiği src'ye .js döküyor)
npm --prefix konsol run kontrol:token  # yalnız keyfi değer denetimi
```

## Ekranlar ve roller

Rota bazlı kod bölme vardır: afetzede ve ekip ekranları harita motorunu indirmez.

| Yol | Ekran | Rol |
|---|---|---|
| `/giris` | Üç kapılı giriş: Afetzede · Saha ekibi · Koordinasyon | herkes |
| `/sifre-degistir` | Tek seferlik şifreyle açılan hesabın ilk girişi | herkes |
| `/konsol/:mod` | Koordinasyon konsolu | `saha`, `koordinator`, `yonetici` (acil bildirim, kullanıcılar ve tatbikat yalnız `koordinator`/`yonetici`) |
| `/afetzede` | SOS, fotoğraf/metin/ihtiyaç ihbarı, bildirimlerim, gelen ekip, duyurular | `afetzede` (koordinasyon da açabilir) |
| `/ekip` | Atanan görev, güzergâh, görev adımları | `saha` (koordinasyon da açabilir) |

Rol kapısı (`src/kimlik/RolKapisi.tsx`) yalnız görünümdür; yetkiyi sunucu denetler
(kural 5). Bir modun hangi rollere görüneceği `src/modlar/modlar.ts`'teki `roller`
alanındadır.

Konsol modları: genel durum · SOS kuyruğu · ekipler · ihtiyaç talepleri · acil bildirim ·
kullanıcılar · hasar analizi · kamera tespiti · metin analizi · deprem riski · simülasyon
(tatbikat) · yol ve rota. Sayfa yok, mod var: mod değişince harita yerinde kalır, yalnız
paneller ve açık katmanlar değişir. Yeni mod eklemek `MODLAR` listesine bir satır
eklemektir.

## Yapı

| Parça | Yer | Not |
|---|---|---|
| Tasarım token'ları | `src/stil/token.css` | **Tek kaynak.** Renk, yazı ölçeği, köşe, boşluk. Tailwind'in hazır renk/yazı ölçekleri `initial` ile kapatıldı |
| Oturum | `src/kimlik/oturum.tsx`, `oturumUcu.ts` | Gerçek `/api/oturum/*` uçları. Erişim jetonu yalnız bellekte; sekme yenilenince httpOnly çerezdeki yenileme jetonuyla geri alınır. 401'de sessizce yenilenir. Rol sunucudan gelir |
| Kalıcı harita kabuğu | `src/harita/HaritaKabugu.tsx` | Tek MapLibre örneği + deck.gl `MapboxOverlay`; mod değişince yeniden kurulmaz |
| Altlık | `src/harita/altlikGorunumu.ts`, `src/veri/altlik.ts` | Kendi altlığımız (OSM'den üretilen bölge paketleri, `/api/altlik/`); yalnız görünen bölgelerin paketleri iner |
| Katmanlar | `src/harita/katmanlar.ts`, `simKatmanlari.ts` | Olaylar, ekipler, kapanmalar, rotalar, faylar, depremler, toplanma ve sağlık yerleri; tatbikat katmanları ayrı |
| Isı | `src/harita/isiDokusu.ts` | Sunucu her kanalın ızgarasını ayrı üretir; ağırlıklı karışım tarayıcıda yapılır, ağırlık değişince istek gitmez |
| Kabuk | `src/kabuk/` | Üst çubuk, sol/sağ panel, zaman şeridi (olay yoğunluğu histogramı), Ctrl+K paleti, TATBİKAT şeridi |
| Panel kuralı | `src/kabuk/Panel.tsx` | `Amac` → `HazirSecenekler` → `InceAyar` → `SuAn` → `Teknik` (ARAYUZ §9) |
| Zaman aralığı | `src/durum/zamanDurumu.ts` | Varsayılan canlı; şerit geri çekilince geçmiş; oynat yalnız geçmişte |
| Tek canlı akış | `src/canli/` | `GET /api/live`, üstel geri çekilme; **yoklama yok** |
| Sunucu verisi | `src/veri/` | TanStack Query; `staleTime: Infinity`, odak/yeniden bağlanma tazelemesi kapalı. Tazeleme yalnız SSE mesajıyla |
| İstemci durumu | `src/durum/` | Zustand: konsol, seçim, zaman, rota, işler, simülasyon |

## Canlı akış

Sunucu yalnız değişiklik olduğunda mesaj gönderir (`src/canli/mesajlar.ts`):

| Mesaj | Ne zaman |
|---|---|
| `yeni-sos` | Yeni SOS ya da durum değişikliği |
| `ihbar` | Yeni afetzede ihbarı ya da durum değişikliği |
| `gorev` | Sevk görevi açıldı ya da adımı değişti |
| `ekip-konumu` | Ekibin konumu değişti |
| `is-durumu` | Hasar analizi / tatbikat ilerlemesi (`iptal` yalnız tatbikat bitince) |
| `simulasyon-katman` | Tatbikatın bir katmanı hazır (hasar → kapanma → rota → görev) |
| `yeni-analiz`, `isi-surumu` | Yeni hasar noktaları yazıldı, ısı ızgarası yenilendi |
| `bildirim` | Acil durum duyurusu yayınlandı ya da geri çekildi |
| `hesap`, `islem-kaydi` | Hesap değişti, işlem kaydına satır eklendi (yalnız konsol rolleri) |

Afetzedeye yalnız **kendi** çağrısının ve ihbarının durumu gider; başkasının kaydı ve ekip
koordinatları gitmez.

## Bağlı uçlar (başlıcaları)

| Alan | Uçlar |
|---|---|
| Oturum ve hesaplar | `/api/oturum/giris`, `kayit`, `yenile`, `cikis`, `sifre`, `kullanicilar`, `hesap-kayitlari` |
| Olaylar | `/api/sos`, `/api/ihbarlar`, `/api/hasar-noktalari`, `/api/ozet`, `/api/olay-yogunlugu` |
| Sevk | `/api/gorevler`, `/api/gorevler/aday-ekipler`, `/api/ekipler`, `/api/ekibim`, `/api/guzergah` |
| Analiz | `/api/road_damage/analyze` (HTTP 202 + iş kimliği), `/api/camera/analyze`, `/api/nlp/analyze`, `/api/risk/predict`, `/api/risk/siralama` |
| Tatbikat | `/api/simulasyon/alanlar`, `modeller`, `kos`, `kosu/{id}`, `bitir` |
| Harita | `/api/katman/{kapanmalar,depremler,faylar,toplanma,saglik}`, `/api/altlik/`, `/api/goruntu/karo` |
| Duyuru ve kayıt | `/api/bildirimler`, `/api/bildirimler/aktif`, `/api/islem-kayitlari` |

Tam liste ve şemalar için API'nin `/docs` sayfası.

## Kurallar (kısa)

- **Keyfi değer yasak.** `text-[13px]`, `bg-[#0b0f17]`, `p-[7px]` yazılmaz; değer token
  dosyasına eklenir. `npm run kontrol:token` bunu denetler.
- Cam efekti, neon parlama, gradyan zemin, sürekli yanıp sönen öğe yok. Paneller opaktır.
- Kırmızı/turuncu/sarı yalnız hasar ve aciliyet için.
- Her panel kendini anlatır: amaç cümlesi → hazır seçenekler → ince ayar → "şu an ne
  görüyorum" → teknik not.
- Her katman kaynağını yazar; senaryo/tatbikat verisi "senaryo" etiketiyle gösterilir.
  Veri yoksa uydurulmaz, eksik olduğu yazılır.
- Kod biçimlendirici ayarı yok; `npx prettier` dosyaları başka biçime çevirip diff'i
  bozar, çalıştırma.
