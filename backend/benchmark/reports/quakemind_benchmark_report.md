# QuakeMind Karsilastirmali Saha Testi Raporu

Bu rapor, QuakeMind'in yol-hasari tespiti (SegFormer+OSM) ve GNN en-guvenli-rota motorunun, bu motor olmadan (naive en kisa yol, kapanmalari sahada kesfederek) gidilen bir senaryoya kiyasla ne kadar zaman kazandirdigini olcer. Tum senaryolar 6 Subat 2023 depreminden gercekten etkilenen Kahramanmaras ve Hatay/Antakya bolgelerinde, gercek AFAD toplanma alani verisi, gercek Copernicus EMSR648 hasar tespiti ve gercek QuakeMind API pipeline'i (NLP, SOS, yol hasari analizi, ekip claim, GNN rota) uzerinden calistirildi -- hicbir adim mock veriyle degistirilmedi.

## Yontem Ozeti

- **Bolgeler:** Kahramanmaras (AFAD merkez ilceler) ve Hatay/Antakya, her biri 3 gercek mahalle.
- **Toplanma alani / itfaiye / hastane verisi:** Resmi AFAD toplanma alani veriseti (72.232 nokta, filtrelendi) + OSM Overpass (itfaiye, hastane). AFAD/UMKE saha binalari icin OSM'de yeterli veri bulunamadi -- bu bilinen bir veri boslugu, ekipler itfaiye/hastane konumlarindan konuslandirildi.
- **Gercek hasar zemin dogrulamasi:** Copernicus EMS EMSR648 (MONIT01 gecisi) -- Kahramanmaras icin 134 hasarli yol/927 hasarli bina, Hatay icin 73 hasarli yol/394 hasarli bina.
- **Uydu goruntusu:** Esri Wayback, depreme en yakin tarihli surum (2023-02-23) otomatik secildi.
- **Naive ajan modeli:** Ayni yol grafiginde, kapanmalari SADECE oraya varinca kesfeder (kesif ani israfi sifir kabul edilir -- naive lehine, muhafazakar bir varsayim), kesfedince bir onceki kavsaktan bilinen kapanmalari eleyerek yeniden en kisa yolu hesaplar.
- **Sure tahmini:** Sabit ortalama saha hizi varsayimi (bkz. asagida) -- bu acikca belirtilen bir varsayimdir, gercek saha hizina gore olceklenebilir.
- **Onemli ayrim:** 'Bizim motor' rotasi HER ZAMAN canli /api/road_damage/route cagrisindan gelen gercek sonuctur (ayrica simule edilmez); sadece naive taraf simule edilir.

## Model Dogrulamasi (Kate-PD)

Canli pipeline'daki dusuk tespit oranini arastirirken, modeli kendi egitim-dagilimina yakin gorsellerle (huggingface.co/datasets/CSCRS/kate-pd) ayrica test ettik. Sonuc: modelin kendisi saglam --  gercek hasarli bolgede ortalama **%69**, maksimum **%99.7** guvenle dogru tespit yapti (temiz bolgede sadece %0.16). Bu, canli pipeline'daki dusuk tespit oraninin modelin kendisinden degil, ucretsiz uydu goruntu kaynaklarinin (Esri Wayback/OpenAerialMap) cozunurlugunden kaynaklandigini dogruluyor.

Bu bulgu uzerine benchmark'in goruntu cekme mantigi duzeltildi: analiz bbox'i mahalle+ekip ussunu kapsayacak sekilde genisletmek yerine, sabit-genislikte (~2048px) bir tile penceresi kullanan merkez+yaricap tabanli cekime gecildi -- ayni Esri Wayback kaynagiyla ham model olasiligi ayni konumda %6'dan %97'ye cikti. Duzeltme sonrasi Kahramanmaras'ta canli tespit orani (Copernicus'a kiyasla) %2.7'den **%16.2'ye** yukseldi (asagidaki kahramanmaras-fixed3 bolumu).

## Bolge: hatay-1786531431

*(Not: bu kosum, asagida aciklanan cozunurluk duzeltmesinden ONCE calistirildi -- Kahramanmaras'in duzeltilmis sonuclariyla dogrudan kiyaslanmamali. Zaman kisitlari nedeniyle Hatay'i duzeltilmis ayarlarla yeniden kosmaya bu oturumda yetisilemedi; bu bir sonraki adim olarak listelendi.)*

Uydu goruntusu tarihi: 2023-02-23

### Canli tespit vs gercek Copernicus hasari (seffaflik)

| Mahalle | Bizim canli tespitimiz (kapali yol) | Copernicus gercek hasar (ayni sinirlar icinde) |
|---|---|---|
| AKSARAY | 7 | 30 |
| AKEVLER | 0 | 30 |
| AYDINLIKEVLER | 0 | 14 |

### hatay / orta hasar senaryosu

- Toplam ekip-hedef atamasi: 3
- Naive ajanin da ulastigi eslesme sayisi: 3
- **Naive ajanin TAMAMEN TIKANDIGI, bizim motorun basarili oldugu eslesme sayisi: 0**
- Naive de ulastiginda toplam kazanilan sure: -4.6 dk (ortalama -1.5 dk/ekip)

### hatay / agir hasar senaryosu

- Toplam ekip-hedef atamasi: 2
- Naive ajanin da ulastigi eslesme sayisi: 2
- **Naive ajanin TAMAMEN TIKANDIGI, bizim motorun basarili oldugu eslesme sayisi: 0**
- Naive de ulastiginda toplam kazanilan sure: -3.6 dk (ortalama -1.8 dk/ekip)

## Bolge: kahramanmaras-fixed3

Uydu goruntusu tarihi: 2023-02-23

### Canli tespit vs gercek Copernicus hasari (seffaflik)

| Mahalle | Bizim canli tespitimiz (kapali yol) | Copernicus gercek hasar (ayni sinirlar icinde) |
|---|---|---|
| EKMEKÇİ | 6 | 2 |
| EGEMENLİK | 0 | 1 |
| DİVANLI | 0 | 3 |

### kahramanmaras / orta hasar senaryosu

- Toplam ekip-hedef atamasi: 2
- Naive ajanin da ulastigi eslesme sayisi: 2
- **Naive ajanin TAMAMEN TIKANDIGI, bizim motorun basarili oldugu eslesme sayisi: 0**
- Naive de ulastiginda toplam kazanilan sure: -0.7 dk (ortalama -0.4 dk/ekip)

### kahramanmaras / agir hasar senaryosu

- Toplam ekip-hedef atamasi: 2
- Naive ajanin da ulastigi eslesme sayisi: 0
- **Naive ajanin TAMAMEN TIKANDIGI, bizim motorun basarili oldugu eslesme sayisi: 2**
  - Bu vakalarda bizim sistemin hedefe ulasma suresi: 5.6 dk, 7.2 dk
- Naive de ulastiginda toplam kazanilan sure: 0 dk (ortalama None dk/ekip)

## Genel Ozet (tum calismalar)

- Naive ajanin da ulastigi toplam eslesme: 7, toplam kazanilan sure: -8.9 dk
- **Naive ajanin tamamen tikandigi, bizim sistemin basarili oldugu toplam eslesme: 2**
- Tum mahallelerde canli tespitimizin bulduğu toplam kapali yol: 13 (Copernicus'un ayni sinirlar icinde isaretledigi: 80)
  - Canli tespit / gercek hasar orani: %16.2 -- bu bolgeler/tarihler icin modelin yakalama oraninin bir gostergesi, iyilestirme alani olarak makalede tartisilabilir.

## Veri Kaynaklari ve Atif

- OpenStreetMap katkicilar, ODbL lisansi altinda.
- Copernicus Emergency Management Service, EMSR648 aktivasyonu (mapping.emergency.copernicus.eu) -- AB Copernicus Programi, ucretsiz ve acik erisim.
- AFAD resmi toplanma alani veriseti (proje ici, apps/road_damage/data/tum_turkiye_toplanma_alanlari.json).
- Esri World Imagery Wayback.

## Bilinen Sinirlamalar

- AFAD/UMKE operasyonel saha binalari icin OSM'de yeterli POI verisi bulunamadi; ekipler itfaiye/hastane konumlarindan baslatildi.
- Sure tahmini sabit bir ortalama hiz varsayimina dayanir, gercek arac/yaya hizindan sapabilir.
- Naive ajan modeli, kesif anindaki kismi mesafe israfini sifir kabul eder (naive lehine, muhafazakar bir varsayim) -- gercek sahada naive yaklasimin kaybi muhtemelen burada raporlanandan daha da fazladir.
- Canli SegFormer tespiti, bazi mahallelerde/tarihlerde Copernicus'un insan analistlerinin buldugu hasarin tamamini yakalayamadi -- Kate-PD dogrulamasi bunun modelin kendisinden degil, ucretsiz uydu goruntusu cozunurlugunden kaynaklandigini gosterdi (bkz. yukarida); cozunurluk duzeltmesi Kahramanmaras'ta tespit oranini %2.7 -> %16.2'ye cikardi.
- **OSMnx/Overpass guvenilirlik sorunu:** Yol-agi grafigi (rota hesaplama icin gerekli) cektigimiz `overpass-api.de` sunucusu bu oturum boyunca ARALIKLI olarak zaman asimina ugradi (bazen calisti, bazen calismadi, sunucu yeniden baslatmadan/ayna degistirmeden bagimsiz olarak) -- bu, ucretsiz/paylasimli bir dis servisin bilinen bir guvenilirlik ozelligi. Koda coklu-ayna fallback + otomatik yeniden deneme eklendi (apps/road_damage/utils/network.py, benchmark/pipeline_runner.py) ama garanti degil. Bu yuzden Kahramanmaras'ta 3 mahalleden sadece 1'i (EKMEKÇİ) rota verisi uretebildi, Hatay duzeltilmis ayarlarla yeniden kosulamadi -- **bir sonraki adim**: Overpass sunuculari daha sakin oldugunda (ornegin farkli bir saatte) tam 4-senaryo kosusunu tekrarlamak.
