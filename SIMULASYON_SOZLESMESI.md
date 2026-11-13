# Simülasyon (tatbikat) modu — arayüz/backend sözleşmesi

Bu belge **konsol arayüzü ile backend arasındaki sınırı** sabitler. İki iş paralel yürüyor:

| Taraf | Kim | Nerede |
|---|---|---|
| Konsol arayüzü (yeni, sıfırdan) | "Konsol arayüzü iskeletini kur" oturumu | `konsol/` |
| Backend: kuyruk, çıkarım işçisi, simülasyon uçları | bu oturum | `backend/` |

Kural: **arayüz modele değil bu sözleşmeye bağlanır** (CLAUDE.md md.2). Uçlar hazır olmadan
arayüz yazılabilir; alanlar bu belgede sabittir, değişirse burası önce güncellenir.

Son güncelleme: 25 Eylül 2026.

---

## 1. Tatbikatın kurgusu (tek paragraf)

Kullanıcı **Simülasyon** moduna girer, bir alan ve bir model seçer. Backend o alanın
**gerçek** deprem sonrası görüntüsünü çeker, seçilen modeli **gerçekten** koşturur, çıkan hasar
maskesinden yol kapanmalarını türetir, OSM yol grafiği üzerinde **Dijkstra ve A\*** ile rotaları
hesaplar, mahallenin **gerçek giriş ağızlarındaki** ekipleri içerideki afetzedelere bağlar. Arayüz
bu sonucu katman katman gösterir. Gerçek olan ne, üretilen ne — her katman kendi kaynağını yazar
(CLAUDE.md md.1).

**Dünyanın ölçeği (26 Eylül, ölçüldü).** Ekipler önce gerçek tesislerdi (1,3–3,8 km uzakta) ve rota
grafiği onları kapsıyordu; o kurguda model rota ağının **yalnız %0,64'ünü** görüyor, kapanma hiçbir
rotaya denk gelmiyor ve üç kıyas kolu da birebir aynı çıkıyordu — tatbikat hiçbir şey ölçmüyordu.
500 m'lik bir drone enkaz haritası 3 km'lik rotayı değiştiremez. Bu yüzden dünya **görüntülenen
mahalle** (+150 m marj); ekipler mahalleye giren gerçek yolların ağzında konuşlanır. Aynı alanda
kapsama %0,64 → %15,2 ve kollar ayrıştı (J-80).

**Trafik sağdan akar.** Tek yön uygulanır; sola dönüş karşı akımı kestiği için maliyetlidir, U
dönüşü manevradır. Arama kenar tabanlıdır (düğüm tabanlı Dijkstra/A\* kavşağa nasıl girildiğini
bilmez ve sola dönüşü bedava alır). Maliyetler beyan edilen tasarım parametresidir: düz 0, sağ 3,
sol 10, U 25 saniye.

## 2. Uçlar

Hepsi `Depends` ile yetki kontrollü; rol istemciden gelmez (md.5).

### `GET /api/simulasyon/alanlar`

Tatbikat alanlarının listesi. Arayüz bunu mod açılışında bir kez ister.

```json
[
  {
    "id": "hatay-elektrik",
    "ad": "Hatay / Defne — Elektrik Mah.",
    "bbox": [36.146753, 36.195466, 36.15189, 36.199922],
    "alanKm2": 0.229,
    "katmanlar": [
      { "id": "yakin",   "ad": "Drone ortofoto",  "saglayici": "Help.NGO (OpenAerialMap)", "cekimTarihi": "2023-02-09", "yaricapKm": 0.30, "gercek": true },
      { "id": "genis",   "ad": "Uydu — geniş",    "saglayici": "Maxar (OpenAerialMap)",    "cekimTarihi": "2023-02-08", "yaricapKm": 0.45, "gercek": true },
      { "id": "oncesi",  "ad": "Deprem öncesi",   "saglayici": "Esri Wayback",             "cekimTarihi": "2021-09-27", "yaricapKm": 0.45, "gercek": true }
    ]
  }
]
```

`oncesi` katmanı kontrol koşusu içindir: aynı model, hasarsız görüntü → yanlış alarm tabanı.

**Alan neden bu büyüklükte:** yakınlaştırma `zoom_for_radius` ile seçilir ve yarıçap büyüdükçe
düşer. Modeller 0,3–0,5 m/piksel ile eğitildi; z18 (0,48 m) sınırda kalmak için geniş katmanın
yarıçapı 0,45 km, yani **≈ 0,92 × 0,92 km**. Daha geniş bir alan zoom'u z17'ye (0,96 m) düşürür
ve model eğitim çözünürlüğünün dışına çıkar (J-20) — bu yüzden "2 km" hedefinden vazgeçildi.

### `GET /api/simulasyon/modeller`

```json
[
  { "id": "hizli",   "ad": "Hızlı",   "kunye": "segformer_mitb0_p2_t42", "mimari": "Segformer (mit_b0)",
    "sinamaIoU": 0.382, "esik": 0.5, "agirlikSha256": "a29a2e85c068", "ileriGecis512Sn": 0.14, "hazir": true },
  { "id": "dengeli", "ad": "Dengeli", "kunye": "segformer_mitb2_p2_t42", "mimari": "Segformer (mit_b2)",
    "sinamaIoU": 0.409, "esik": 0.5, "agirlikSha256": "05fabc05b960", "ileriGecis512Sn": 0.30, "hazir": true },
  { "id": "eniyi",   "ad": "En iyi",  "kunye": "unet_mitb4_p2_t42",     "mimari": "Unet (mit_b4)",
    "sinamaIoU": 0.433, "esik": 0.5, "agirlikSha256": "2ddcc7d24981", "ileriGecis512Sn": 0.61, "hazir": true }
]
```

`ileriGecis512Sn` **ölçüldü** (512×512 tek ileri geçiş, CPU i7-12700H, torch 2.11.0 — API'nin
koştuğu kök venv; 25 Eylül 2026). Değer model künyesinden gelir, `olcumNotu` yöntemi yazar.
Ölçülmemiş bir alan `null` döner ve arayüz `null` ise süre yazmaz (md.8). `hazir: false` gelen
model seçilemez (ağırlık ya da künye yok).

Yama sayısı: yakın katman ≈ 16, geniş katman ≈ 25 (512 yama / 256 adım). Yani bir tatbikat
koşusunun çıkarım süresi **Hızlı ~2–4 sn, Dengeli ~5–8 sn, En iyi ~10–15 sn**; geri kalan süre
görüntü indirme ve OSM yol ağıdır. Üç model de arayüzde rahatça seçilebilir.

### `POST /api/simulasyon/kos`

```json
{
  "alanId": "hatay-elektrik",
  "katmanId": "yakin",
  "modelId": "dengeli",
  "esik": 0.5,
  "kapanmaYaricapiM": 0,
  "yumusakMaliyet": false,
  "lambda": null,
  "ekipSayisi": 5,
  "afetzedeSayisi": 5,
  "tohum": 42,
  "hizKmh": 15.0,
  "kontrolKosusu": true,
  "karsilastirYaricaplar": [0, 10, 25]
}
```

> **Arayüzde r_h YOK.** `kapanmaYaricapiM` ve `karsilastirYaricaplar` birer **araştırma
> alanıdır**; seçim paneline konmaz, ince ayarda da görünmez. Gerekçe ölçüldü (J-70): EMSR648 yer
> gerçeğiyle kalibrasyonda r_h'yi büyütmek duyarlılığı artırırken kesinliği 0,10–0,18 bandından
> çıkarmıyor — yani operatöre sonucu düzeltmeyen bir düğme sunulmuş olurdu. Tatbikat ürünün
> kuralıyla (r_h = 0) koşar; iki alan API'de ölçüm ve makale için durur.
> `karsilastirYaricaplar` varsayılanı **boş listedir** (ek süre yok).

**`kapanmaYaricapiM` varsayılanı 0'dır** — ürünün kuralı budur: "yalnız yolun üstündeki hasar
kapatır". Yarıçap kuralı (moloz yayılımı) bir **deneydir** (J-26) ve ancak açıkça istenince
devreye girer; tatbikat uygulamanın varsayılanını değiştirmez (J-19). Arayüz bunu "Moloz
yayılımı: Yok (varsayılan) · 10 m · 25 m" diye sunmalı, seçilen değer sonuçta `kapanma.yaricapM`
ve `kapanma.kural` alanlarında geri gelir.

**`karsilastirYaricaplar`** kıyas kutusunu doldurur: aynı maske, farklı r_h. Model **bir kez**
koşar; her yarıçap yalnız kapanma + rota hesabı ekler (ölçüldü: yarıçap başına ~16 sn). Boş
liste = kıyas yok. Sonuçta `yaricapKiyasi.satirlar` döner:

```json
"yaricapKiyasi": {
  "toplamYolM": 831600.0, "ciftSayisi": 25,
  "satirlar": [
    { "yaricapM": 0,  "kural": "on_road_pixel", "kapaliKenar": 29,  "kapaliYolM": 2217,
      "kapaliYolYuzde": 0.27, "ortalamaUzamaM": 23.2, "ortalamaUzamaYuzde": 1.5,
      "yurumeGerekenCift": 5,  "ortalamaYurumeM": 17.1, "ulasilamayanCift": 0 },
    { "yaricapM": 10, "kural": "radius", "kapaliKenar": 72,  "kapaliYolM": 4740,
      "yurumeGerekenCift": 20, "ortalamaYurumeM": 47.1 },
    { "yaricapM": 25, "kural": "radius", "kapaliKenar": 148, "kapaliYolM": 11674,
      "yurumeGerekenCift": 25, "ortalamaYurumeM": 55.0 }
  ]
}
```

**Uzama ortalaması yalnız TAM araç rotası olan çiftlerden alınır** (`olcum.uzamaHesabindakiCift`).
Yürüme yedeği devreye giren çiftte `kapanmaliM` hedefe değil, aracın gidebildiği en yakın noktaya
olan kısmi mesafedir; ikisini aynı ortalamaya katmak metriği bozuyordu. r_h ≥ 15 m'de tam araç
rotası kalmadığı için uzama `null` gelir — arayüz bu durumda "araçla ulaşılamıyor" yazmalı.

**Yanıt: HTTP 202.** İstek yolunda çıkarım yok (md.3).

```json
{ "isId": "sim_7f3a…", "parmakIzi": "sha1:…", "onbellekten": false }
```

`onbellekten: true` ise iş kuyruğa girmez, sonuç hazırdır — arayüz doğrudan sonucu ister.
Parmak izi = alan + katman + model ağırlığı SHA-1 + eşik + yarıçap + λ + tohum + görüntü tarihi.

### `POST /api/simulasyon/bitir`

```json
{ "isId": "sim_7f3a…" }
```

Tatbikatı **bitirir**; konsol normal akışa döner. Yanıt
`{ "isId": …, "durum": "bitti", "silinenHasarNoktasi": 3 }`.

Tatbikat gerçek görüntüde gerçek model koşturur ama sonucu **canlı olay değildir**: koşu
bitirilince o koşunun yazdığı hasar noktaları silinir, yoksa tatbikat verisi gerçek olay
verisiyle karışırdı (CLAUDE.md 1). Analizin kendi kaydı (görseller, sonuç JSON'u) durur.

Sunucu canlı akışa `is-durumu` mesajını **`durum: "iptal"`** ile yayınlar: açık olan bütün
istemciler aynı anda tatbikat modundan çıkar — bitiren sekmeyi temizlemek yetmez.

**Kontrol koşusu hasar noktası yazmaz.** Deprem öncesi görüntüde bulunan şey yanlış alarm
tabanıdır, olay değildir; haritaya düşmez.

### `GET /api/simulasyon/kosu/{isId}`

Sonuç (aşağıda §4).

### `GET /api/road_damage/gorsel/{isId}/imageDamageMask`

Hasar maskesi PNG. **Yeni uç açılmadı**: analiz görselleri zaten bu uçtan tek tek ve
önbelleklenebilir biçimde veriliyordu (J-32), simülasyon da aynısını kullanır. Harita ham raster
katmanı olarak bindirir; poligon çıkarma yükü arayüze bırakılmaz. Sonuçtaki `hasar.maskeUrl`
alanı bu adresi hazır verir. Aynı yoldan `imageOriginal`, `imageDamageOverlay`,
`imageSegmentationOverlay` da alınabilir.

## 3. Canlı akış (SSE)

**Yeni akış yok, yoklama yok** (md.4). Var olan tek akışa iki mesaj eklenir
(`konsol/src/canli/mesajlar.ts` içindeki `CanliMesaj` birleşimine):

```ts
| { tip: 'is-durumu'            // ZATEN VAR — isTipi: 'simulasyon' ile kullanılır
    isId: string
    isTipi: 'simulasyon'
    durum: 'kuyrukta' | 'calisiyor' | 'bitti' | 'hata'
    ilerleme?: number           // YÜZDE, 0–100
    mesaj?: string }            // "Segformer AI modeli calisiyor (12/25 parca)"

| { tip: 'simulasyon-katman'    // YENİ — bir katman çizilmeye hazır
    isId: string
    katman: 'hasar' | 'kapanma' | 'rota' | 'gorev'
    sayi?: number }             // kaç poligon / kenar / rota
```

**İlerleme ölçeği: yüzde (0–100)** — hem SSE'de hem `GET …/kosu/{isId}` yanıtında aynı.
(J-62/1 kapandı: iki ölçek vardı, mevcut `is-durumu` yüzde gönderdiği için yüzde seçildi.)

Akış sırası: `hasar` → `kapanma` → `rota` → `gorev`. Arayüz her mesajda **yalnız o katmanı**
ister; sonucun tamamını baştan beklemez. İlk hasar katmanı hedefi < 5 sn.

**Kısmi sonuç (J-62/3 kapandı).** Tek sonuç ucu vardır ve **her zaman çağrılabilir**: hazır olan
bölümler dolu, hazır olmayanlar `null` gelir. İş bitmeden `hasar` ve `kapanma` dolu, `gorevler`
ve `olcum` `null` olabilir. Arayüz eldekini çizer.

## 4. Sonuç yapısı

`GET /api/simulasyon/kosu/{isId}`. Aşağıdaki değerler **25 Eylül 2026'da gerçekten koşulmuş bir
tatbikattan** alınmıştır (Hatay/Elektrik, `genis` katman = Maxar 2023-02-08, model `eniyi`,
eşik 0,5, r_h 25 m, tohum 42) — uydurma örnek değildir, büyüklükler gerçekçidir.

**Koordinat sırası:** çizgiler `[[lat, lon], …]`, noktalar `{lat, lon}` alanlarıyla. (J-62/2:
harita `[lon, lat]` istiyor, çevrim arayüzde tek yerde yapılır; backend'in bütün çizgi
üreticileri — `blockedRoadSegments` dahil — `[lat, lon]` verdiği için sözleşme böyle kaldı.)

```json
{
  "isId": "sim_7f3a…",
  "durum": "bitti",
  "ilerleme": 100,
  "parmakIzi": "sha1:…",
  "alan": { "id": "hatay-elektrik", "ad": "Hatay / Defne — Elektrik Mah.",
            "bbox": { "west": …, "south": …, "east": …, "north": … } },

  "kaynak": { "katmanId": "genis", "saglayici": "Maxar (OpenAerialMap)",
              "cekimTarihi": "2023-02-08", "gsdM": 0.482, "gercek": true,
              "gsdUyarisi": false, "not": "Depremden 2 gün sonra…" },

  "model": { "id": "eniyi", "kunye": "unet_mitb4_p2_t42", "mimari": "Unet (mit_b4)",
             "sinamaIoU": 0.433, "esik": 0.5, "agirlikSha256": "2ddcc7d24981",
             "ileriGecis512Sn": 0.61 },

  "hasar": {
    "maskeUrl": "/api/road_damage/gorsel/sim_7f3a…/imageDamageMask",
    "bbox": { … },
    "hasarliPikselOrani": 0.0069,
    "hasarliPikselOraniGecerli": 0.0069,
    "gecerliAlanOrani": 0.99,
    "oncesiKontrol": { "katmanId": "oncesi", "cekimTarihi": "2021-09-27",
                       "hasarliPikselOrani": 0.0012, "kapaliKenarSayisi": 3 }
  },

  "kapanma": {
    "yaricapM": 25.0, "kural": "radius",
    "kapaliKenarSayisi": 87,
    "kapaliKenarlar": [ { "coords": [[lat, lon], …] } ]
  },

  "grafik": { "kutu": [w, s, e, n], "dugum": 4410, "kenar": 12108, "kapaliKenar": 87,
              "maskeKapsamasi": { "edgesTotal": 12108, "edgesObserved": 3140,
                                  "edgesObservedFraction": 0.259 } },

  "referansAjanlar": {
    "varyantlar": {
      "Kapanmayı bilmeyen ekip": { "gorevSayisi": 5, "ulasanGorev": 4, "ortakGorev": 4,
            "ortalamaSureDk": 2.9, "ortalamaMesafeM": 612.0, "toplamKesif": 3, "cezaliOlay": 3,
            "kapanmaCezasiDk": 1.417, "cezadanGelenDk": 0.85, "donusSuresiDk": 0.42,
            "donusler": { "duz": 31, "sag": 15, "sol": 5, "u": 2 }, "uDonusuSayisi": 2 },
      "Telsizle paylaşan filo": { "ulasanGorev": 4, "ortalamaSureDk": 2.4, "uDonusuSayisi": 1 },
      "QuakeMind":              { "ulasanGorev": 4, "ortalamaSureDk": 1.3, "uDonusuSayisi": 0 }
    },
    "gorusMesafesiM": 0.0,
    "donusMaliyetli": true,
    "degerlendirmeDk": null,
    "not": "Tatbikatta dünya = modelin kapanmaları olduğu için QuakeMind kolu tanım gereği…"
  },

  "ekipler": [
    { "id": "e1", "ad": "secondary girişi 1", "tur": "giris",
      "lat": 36.199312, "lon": 36.147880, "dugum": 1234567,
      "gercekTesis": false, "kaynak": "OpenStreetMap (mahalle giriş ağzı)" }
  ],
  "afetzedeler": [
    { "id": "a3", "ad": "Afetzede 3", "lat": …, "lon": …, "hasarBlobPiksel": 4280,
      "senaryo": true, "kaynak": "senaryo — modelin hasarlı bulduğu alandan seçildi" }
  ],

  "gorevler": [
    {
      "id": "g3", "ekipId": "e3", "ekipAd": "Antakya Devlet Hastanesi", "gercekTesis": true,
      "afetzedeId": "a3", "afetzedeAd": "Afetzede 3", "senaryo": true,
      "baslangic": { "lat": …, "lon": …, "ad": "Antakya Devlet Hastanesi" },
      "hedef":     { "lat": …, "lon": …, "ad": "Afetzede 3" },
      "varyantlar": {
        "depremOncesi": { "cizgi": [[lat, lon], …], "uzunlukM": 3704.2, "sureDk": 14.8 },
        "kapanmali":    { "cizgi": [[lat, lon], …], "uzunlukM": 3931.4, "sureDk": 15.7 },
        "riskli":       { "cizgi": [[lat, lon], …], "uzunlukM": 3931.4, "sureDk": 15.7 }
      },
      "arama": {
        "dijkstra": { "uzunlukM": 3931.4, "sureSn": 0.0447 },
        "astar":    { "uzunlukM": 3931.4, "sureSn": 0.0245 },
        "ayniYol": true
      },
      "etaDk": 15.7,
      "sonAdimYurumeM": null,
      "sonAdimYurumeDk": null,
      "durum": "atandi"
    }
  ],

  "olcum": {
    "ciftSayisi": 25,
    "ortalamaUzamaM": 69.2,
    "ortalamaUzamaYuzde": 6.8,
    "enBuyukUzamaM": 761.3,
    "ulasilamayanCift": 0,
    "yurumeGerekenCift": 15,
    "ortalamaYurumeM": 56.4,
    "hizKmh": 15.0,
    "satirlar": [ { "ekipId": "e1", "afetzedeId": "a1", "oncesiM": …, "kapanmaliM": …,
                    "riskliM": …, "yurumeM": …, "ulasilamadi": false } ]
  },

  "sureler": { "satellite": 10500, "roads": 700, "inference": 26600, "logistics": 5100, "total": 42900 },
  "gunluk": [ "1/4 Uydu goruntusu indirildi", … ]
}
```

**Üç rota varyantının tanımı** (J-62'nin sorduğu):

| Varyant | Grafik | Ağırlık |
|---|---|---|
| `depremOncesi` | tam grafik, hiçbir kenar kapalı değil | `length` |
| `kapanmali` | kapalı kenarlar çıkarılmış (`restricted_view`) | `length` |
| `riskli` | kapalı kenarlar çıkarılmış **+ kalan kenarlara ceza** | `risk_cost` |

`risk_cost = length × risk_weight(en yakın hasar noktasına uzaklık)`; kademe: <50 m ×3,0 ·
<150 m ×1,5 · <400 m ×1,1 · ötesi ×1,0. Yani **"riskli kenar cezalı"** doğru okuma: kapanmadan
kaçınma zaten `kapanmali`da yapılmıştır, `riskli` bunun üstüne enkaza yakın yolu pahalılaştırır.
Rota bulunamazsa varyant `null` gelir.

**Son adım yaya.** Kapalı yollar yüzünden araç hedefe hiç giremiyorsa "ulaşılamaz" denmez: araç
gidebildiği en yakın noktaya kadar gider, kalan mesafe `sonAdimYurumeM` olarak yazılır (yaya hızı
5 km/sa). Ölçülen koşuda 25 çiftin 15'i böyleydi, ortalama 56 m — bu olmadan hepsi "ulaşılamaz"
görünüyordu.

**Hasar oranının paydası.** `hasarliPikselOrani` KARE üzerinden; `hasarliPikselOraniGecerli`
görüntünün boş olmayan kısmına göre. Drone ortofotosunda kare %61 siyah (`gecerliAlanOrani`
0,39) ve iki sayı üç kat farklı çıkıyor — **arayüz geçerli alana göre olanı göstermeli**, yanına
`gecerliAlanOrani`'nı yazmalı.

**`oncesiKontrol`** aynı modelin deprem öncesi görüntüdeki (2021-09-27) sonucudur: yanlış alarm
tabanı. İstekte `kontrolKosusu: false` ile kapatılabilir; koşu bitmediyse `null` gelir.

**`maskeKapsamasi`** modelin gerçekten baktığı kenar oranı. Maskenin dışında ya da görüntünün boş
kısmında kalan kenar "açık" sayılır ama **ölçülmemiştir** — arayüz bunu "%X kenarda değerlendirildi"
diye yazmalı, yoksa "her yer açık" gibi okunur.

**`referansAjanlar` — dikkatle okunacak.** Tatbikatta yer gerçeği bir kapanma katmanı yok; dünya
**modelin kendi çıktısıdır**. Bu yüzden **QuakeMind** kolu tanım gereği kusursuz bilgiye sahiptir ve
bu tablo modelin doğruluğunu ölçmez, **kapanmayı önceden bilmenin kazandırdığı süreyi** ölçer.
Ortalamalar yalnız bütün kolların ulaştığı `ortakGorev` üzerinden alınır (kollar farklı sayıda
görevi tamamlıyor; farklı kümeler üzerinden ortalama kıyaslamak yanıltır). Kolların "son adım yaya"
düzeltmesi yoktur, bu yüzden ulaşan görev sayıları görev listesindekinden düşüktür.

Kol adları **R0–R3 değil**; sahadaki durumu anlatır: "Kapanmayı bilmeyen ekip", "Telsizle paylaşan
filo", "QuakeMind" (isteğe bağlı dördüncü: "Görüş mesafeli ekip", `gorus_m > 0` ile).

**`kapanmaCezasiDk` — beyan edilen sabit, açıkça yazılır.** Kapanmaya varan ekibin kaybettiği süre
eskiden tek bir 20 dakikalık sabitti ve sonucu tek başına belirliyordu (farkın %97,4'ü oradan
geliyordu — yani ölçüm sabitin kendisini ölçüyordu). Artık ayrışık: değerlendirme (1,0 dk) +
manevra (25 sn) = 1,42 dk; asıl bedel ekibin fazladan sürdüğü yoldan gelir ve onu çizge hesaplar.
Sonuçta hem sabit hem ondan gelen süre (`cezadanGelenDk`) yazılır ki okuyan payını görebilsin.

**Maske PNG yetki ister.** `<img src>` ile çekilemez; jetonla indirilip `createImageBitmap` ile
çözülür (konsol bunu `veri/simulasyon.ts` içinde yapıyor).

## 5. Arayüzün karşılaması gerekenler

1. **TATBİKAT şeridi** — mod açıkken kalıcı, kapanmaz, sayfa değişince kaybolmaz.
2. **Seçim paneli** — tek cümlelik amaç, altında hazır seçenekler (alan, model), ince ayar
   (eşik, yarıçap, tohum, ekip/afetzede sayısı) en altta (md.6).
3. **Kaynak paneli** — her katmanın sağlayıcısı, çekim tarihi, GSD'si; `gercek: false` olan her
   şey (afetzede konumları) **"senaryo"** etiketiyle, gerçek ölçümle aynı görünmeden.
4. **Katmanlar** — hasar (raster PNG), kapalı kenar (kırmızı), cezalı kenar (turuncu), üç rota.
   Kırmızı/turuncu/sarı yalnız hasar ve aciliyet için (md.6).
5. **Dijkstra / A\* kartı** — iki arama, uzunluk ve süre yan yana; `ayniYol: true` ise bunu yazar.
6. **İlerleme** — SSE `is-durumu.ilerleme`'den; yoklama yok, `setInterval` yok.
7. **Harita tek örnek** — mod geçişinde yeniden kurulmaz (< 200 ms).
8. **Token'lar** — keyfi değer yok (`text-[13px]`, `bg-[#0b0f17]` yasak); CI kontrol ediyor.
9. **Ana iş parçacığı** — çıkarım koşarken tek görev 50 ms'yi geçmez; ağır dönüşüm Web Worker'da.
   Sonuç: simülasyon koşarken INP, boştaki INP ile aynı bantta kalır.

## 6. Gerçek ne, üretilen ne

| Öğe | Durum |
|---|---|
| Uydu/drone görüntüsü | **Gerçek**, tarihli, sağlayıcısı yazılı |
| Hasar maskesi | **Gerçek** — kendi modelimizin çıktısı |
| Yol ağı | **Gerçek** — OpenStreetMap |
| Ekip üsleri | **Gerçek** — OSM'deki hastane/sağlık ocağı, adıyla |
| Afetzede konumları | **Üretilen** — modelin hasarlı dediği binalardan seçilir, "senaryo" etiketli |
| Ekip sayısı, görev zamanlaması | **Üretilen** — tatbikat parametresi |

## 7. Açık madde

Esri Wayback'te bu alanın enkazlı hâli **yok**: sürüm tarihi ≠ çekim tarihi; 2023-12-07 sürümü
bile 2021-09-27 çekimini veriyor, 2024 sürümleri 2023-04-04 çekimini veriyor ve o tarihte moloz
kaldırılmış durumda. Bu yüzden geniş katman **Maxar (OAM, 2023-02-08)**, öncesi katmanı
**Esri Wayback (2021-09-27)**. `EKSIKLER_VE_SORUNLAR.md`'ye kimlikli madde olarak yazılacak.
