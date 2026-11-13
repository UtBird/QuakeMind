# Kapanma katmanı için elle yer gerçeği — Defne / Elektrik Mah.

**Neden.** Tatbikatta dünya modelin kendi çıktısıdır; "kapalı dediğimiz yol
gerçekten kapalı mıydı" sorusu tatbikatla cevaplanamaz (J-88). EMSR
kullanılmıyor (J-87): onun tanımı *yolun kendisinin bozulması*, bizimki
*yolun molozla kapanması* — farklı soru.

**Yöntem.** Yol parçaları, modelin ne dediği **görülmeden** (kör), gerçek drone
ortofotosunun kesitleri üzerinden işaretlendi. Modelin kapalı dediği parçaların
tamamı + açık dediklerinden rastgele bir örnek etiketlendi; örnekleme oranı
anahtarda yazılı, duyarlılık kestirimi bununla ölçeklendi.

**Ölçüt.**
- `kapali` — parçanın belirgin bir bölümünü moloz/enkaz kütlesi örtüyor
- `acik` — boyunca sürekli, geçilebilir bir koridor görülüyor (asfalt/toprak, araç)
- `kararsiz` — gölge, çözünürlük ya da **geometri**: çizgi görünür bir sokağı takip etmiyor

**Yeniden üretme.** Kesitler tohumla belirlenir, aynı komut aynı 33 kesiti verir:

```bash
python araclar_kapanma_etiketle.py --cikti <dizin>
```

**Sınırlar — makalede aynen yazılmalı.**
1. **Tek etiketleyici** (Claude), ikinci görüş yok, etiketleyiciler arası uyum ölçülmedi.
2. Parçaların **%30'u yargılanamadı** (10/33): gölge, çözünürlük, ya da çizginin
   görünür bir sokağı takip etmemesi.
3. Modelin 12 kapanmasından yalnız **5'i** uçuş izinin dolu olduğu yere düşüyor;
   gerisi değerlendirilemedi.
4. Kesinlik yalnız **3 karar verilebilir** parçaya dayanıyor — %95 Wilson aralığı
   %44–100. Nokta kestirimi tek başına kullanılmamalı.
5. Yalnız **yukarıdan görünen** moloz yakalanır; içeriden kapalı bir sokak
   açık görünebilir.
6. Görüntü 2023-02-09, depremden 3 gün sonra: bir miktar açma çalışması
   başlamış olabilir.
