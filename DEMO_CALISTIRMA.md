# Demo çalıştırma — simülasyon (tatbikat) sunumu

26 Eylül 2026'da uçtan uca koşuldu ve doğrulandı. Sunum sırası bu belgede.

## 1. İki sunucu

```bash
backend/venv/Scripts/python.exe -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000 --app-dir backend
```

```bash
npm --prefix konsol run dev
```

API 8000'de, konsol **http://localhost:3200** adresinde. Konsol `/api` isteklerini
8000'e yönlendirir, ayrı bir ayar gerekmez. API'nin açılması ~20 sn sürer (modeller
tembel yüklenir, ilk tatbikata kadar belleğe girmez).

## 2. Giriş

Sunum hesabı: `demo@quakemind.local`, rol **koordinatör**. Şifre
`araclar_kullanici.py` içindeki varsayılandır. Hesap yoksa:

```bash
backend/venv/Scripts/python.exe backend/araclar_kullanici.py ekle demo@quakemind.local "Demo Sunum" koordinator
```

## 3. Tatbikatı koşturma

**Analiz → Simülasyon (tatbikat)** menüsünden gir. Sol panelde sırayla:

1. **Alan:** açılır listede ölçülmüş alan kataloğundan gelir
   (`data/tatbikat_alanlari.json`; 11 gerçek drone alanı, künyeleri ölçülü).
   Demo için: Hatay / Defne — Elektrik Mah.
2. **Görüntü katmanı:** alan başına **tek** katman vardır — `Drone ortofoto`
   (Help.NGO / OpenAerialMap, Defne-Elektrik için 2023-02-09, depremden 3 gün
   sonra). Katman kataloğun `tmsUrl` alanından gelir; her alanın kendi sağlayıcısı
   ve çekim tarihi arayüzde yazar.
   **Uyarı:** bu belge bir ara sürümde `Uydu — geniş` (Maxar) ve
   `Deprem öncesi (kontrol)` (Esri Wayback) katmanlarını da sayıyordu; bu ikisi
   arayüzde **yoktur**. Maxar geniş katmanıyla yapılan ölçümler (ör.
   `benchmark/reports/rh_duyarlilik_hatay_elektrik.json`) uç noktayla değil
   `araclar_tatbikat_kos.py` aracıyla koşulmuştur. Deprem öncesi kontrol görüntüsü
   ise ayrı bir katman değil, koşunun içindeki `kontrolKosusu` adımıdır.
   (J-107, 27 Eylül 2026)
3. **Model:** Hızlı (SegFormer-B0) · Dengeli (SegFormer-B2) · **En iyi** (U-Net MiT-B4)
4. **Tatbikatı başlat**

İnce ayarda yalnız eşik, ekip sayısı, afetzede sayısı ve tohum var. Kapanma yarıçapı
(r_h) bilerek yok — gerekçesi `EKSIKLER_VE_SORUNLAR.md` J-70'te.

## 4. Ölçülen süre (En iyi model, geniş katman)

| Aşama | Süre |
|---|---|
| Uydu görüntüsü | 7–10 sn |
| OSM yol ağı | 0–1 sn (önbellekten) |
| Model çıkarımı | ~63 sn (49 yama × 0,61 sn) |
| Lojistik | ~6 sn |
| **Toplam** | **~78 sn** |

Hızlı model ile çıkarım ~15 sn'ye iner. Arkada koşarken arayüz akıcı kalır: çıkarım ayrı
bir işçi sürecinde ve 6 iş parçacığıyla sınırlı (J-66), kalan çekirdekler API'ye ve
tarayıcıya kalır.

## 5. Sunumda gösterilecek sıra

1. **TATBİKAT şeridi** — "gerçek olay değildir", koşu boyunca ekranın üstünde durur.
2. **Kaynak paneli** — sağlayıcı, çekim tarihi, 0,482 m/piksel; "GERÇEK" rozeti.
   Afetzedelerde "senaryo" rozeti: neyin ölçüm neyin kurgu olduğu ekranda yazıyor.
3. **Hasar katmanı** — modelin kendi çıktısı, maske haritaya bindiriliyor.
4. **Kapanan yollar** — hasardan türetilen kapalı kenarlar (kırmızı).
5. **Üç rota** — deprem öncesi / kapanmalara göre / riskli kenar cezalı, aynı çift için.
6. **Arama kartı** — Dijkstra ~59 ms, A* ~34 ms, "ikisi de aynı yolu buldu".
7. **Ölçüm** — ekranda 5 görev, ölçüm 25 çiftten (ortalama uzama, en çok uzama).
8. **Kıyas kolları** — "Kapanmayı bilmeyen ekip" · "Telsizle paylaşan filo" · "QuakeMind".
   Kod adı (R0–R3) kullanılmıyor; ad sahadaki durumu anlatır. Ölçülen örnek
   (Nurdağı, 25 çift): 3,3 dk · 2,7 dk · 1,4 dk — kapanmayı önceden bilmek erişimi
   %58 kısaltıyor. Fark, ekibin kaç kapanmaya fiilen denk geldiğini izler.
   **Sunumda mutlaka söylenecek:** tatbikatta dünya = modelin kapanmalarıdır, bu yüzden
   QuakeMind kolu tanım gereği kusursuz bilgilidir; bu tablo modelin doğruluğunu değil, kapanmayı
   bilmenin kazandırdığı süreyi ölçer. Modelin doğruluğu ayrı ölçülüyor (J-65, J-70).
9. **Görevler** — mahallenin 5 gerçek giriş ağzı (OSM düğümü, yol sınıfıyla) → 5 senaryo
   afetzedesi, ETA'larıyla. Ekipler artık kilometrelerce uzaktaki tesisler değil: o kurguda
   model rota ağının %0,64'ünü görüyordu ve kapanma hiçbir rotaya denk gelmiyordu (J-80).

## 6. Tatbikat açma ve kapama

Tatbikat bir **moddur, açılır ve kapanır**:

- **Tatbikatı başlat** — koşu kuyruğa girer, TATBİKAT şeridi ekranın üstünde belirir ve
  mod değiştirsen de durur (şerit kapatılamaz: uyarı susturulamamalı).
- Koşunun bulduğu hasar noktaları veritabanına yazılır (`kaynak="uydu"`, "Tatbikat"
  etiketli). **Genel durum** ekranına geçip uydu kanalını açınca tatbikatın çıktısı orada
  da görünür — simülasyon ayrı bir ada değil (J-72).
- **Tatbikatı bitir** — koşunun yazdığı hasar noktaları silinir, şerit kalkar, katmanlar
  düşer, konsol normal akışa döner. Açık olan başka ekranlar da aynı anda çıkar (canlı
  akışa `durum: "iptal"` gider).
- Kontrol koşusu (deprem öncesi görüntü) hasar noktası **yazmaz**: orada bulunan şey
  yanlış alarm tabanıdır, olay değildir.

Doğrulandı (26 Eylül): başlat → 2 nokta yazıldı, şerit açıldı; bitir → şerit kalktı, düğme
"Tatbikatı başlat"a döndü, tatbikatın noktaları silindi, **13 gerçek nokta yerinde kaldı**.

## 7. Bilinen sınırlar (soru gelirse)

- Model **bina hasarı** buluyor; yol kapanması bundan türetiliyor — yol hasarı etiketimiz yok.
- Duyarlılık düşük: drone ortofotosunda en belirgin yıkıntıları buluyor, çoğunu kaçırıyor (J-65).
- EMSR648 yer gerçeğiyle kalibrasyonda en iyi F1 0,205 (J-70) — zayıf; kalibrasyon yeni
  modelle tekrarlanacak.
- Afetzede konumları modelin hasarlı bulduğu alanlardan seçiliyor, üretilmiş veridir.
- Yol ağı ve maskesi yerel bölge dosyasından gelir (`araclar_yerel_osm_kur.py`); Overpass
  kesilse de tatbikat çalışır. Dosya yoksa Overpass'a düşülür ve boş katman `yolKatmaniYok`
  ile yazılır (J-68, J-79).
- Trafik sağdan akar: tek yön uygulanır, sola dönüş ve U dönüşü maliyetlidir (`donus.py`).
- Kapanmaya varan ekibin kaybettiği süre beyan edilmiş bir sabittir (değerlendirme 1,0 dk +
  manevra 25 sn); sonuç bu sabite yaslanmasın diye duyarlılığı ölçülür ve raporda yazılır.
