# Simülasyon (tatbikat) — yöntem ve ölçülen sayılar

_Son güncelleme: 26 Eylül 2026._

Bu belge **makaleye girecek sayıların kaynağıdır**. Word belgesi bu oturumda
değiştirilmedi; makale revizyonunu yapan kişi sayıları buradan alır.

> **Bu simülasyonda ne YOK:** Copernicus EMS / EMSR648 (hiçbir rolde — ne motor
> ne cetvel; karar 26 Eylül, gerekçe §12), HAZUS eşlemesi, sentetik kapanma
> üreteci, R0–R3 kod adları. Eski taslakta bunlardan gelen tablolar ve
> iddialar var; hiçbiri bu ölçümlerle desteklenmiyor ve kullanılmamalıdır.

---

## 1. Zincir

```
gerçek açık drone ortofotosu  (Help.NGO / OpenAerialMap, Şubat 2023)
  → kendi hasar modelimiz      (modeller/uydu/<künye>.json, SHA-256 doğrulanır)
  → OSM yol kenarlarının merkez çizgisi boyunca ~5 m aralıkla maske örneklemesi
  → kapalı yollar
  → mahalle giriş ağzındaki ekip  →  içerideki afetzede rotaları
  → kıyas kolları
```

Eğitim verisi **KATE-CD + KATE-PD** (Protokol P2). Model çıkarımı, ürünün
`/api/road_damage/analyze` yolunun kullandığı kodun aynısıdır.

## 2. Dünyanın ölçeği — neden "mahalle"

İlk kurgu ekipleri gerçek tesislere (hastane, itfaiye; 1,3–3,8 km uzakta)
koyuyordu. O kurguda **model, rota ağındaki kenarların yalnız %0,64'ünü
görüyordu** (25.323 kenarın 162'si) ve üç kıyas kolu da birebir aynı sonucu
veriyordu: kapanma hiçbir rotaya denk gelmiyordu. 500 m'lik bir enkaz haritası
3 km'lik rotayı değiştiremez.

Bu yüzden dünya **görüntülenen mahalle** (+150 m marj). Ekipler mahalleye giren
**gerçek yol ağızlarında** konuşlanır (OSM düğümleri, ana yol sınıfı önce,
ağızlar arası en az 120 m). Ölçülen soru şu: *mahalleye giren ekip içerideki
enkaza ne kadar sürede ulaşıyor ve moloz haritasını önceden bilmek bunu
değiştiriyor mu?* Aynı alanda kapsama %0,64 → %15,2 çıktı.

## 3. Kıyas kolları

| Kol | Ne demek |
|---|---|
| **Kapanmayı bilmeyen ekip** | Bugünkü durum: yola çıkar, kapalı sokağa varınca öğrenir, değerlendirir, döner |
| **Telsizle paylaşan filo** | Bir ekibin öğrendiği kapanma anında bütün ekiplere yayılır |
| **QuakeMind** | Analizin çıkardığı kapanmalar baştan bilinir |

**Dürüstlük notu — makalede aynen yer almalı.** Tatbikatta yer gerçeği bir
kapanma katmanı yoktur; dünya **modelin kendi çıktısıdır**. Bu yüzden QuakeMind
kolu tanım gereği kusursuz bilgiye sahiptir ve bu tablo **modelin doğruluğunu
ölçmez** — kapanmayı önceden bilmenin kazandırdığı süreyi ölçer. Modelin
doğruluğu ayrı ve etiketli veriyle ölçülür.

Ortalamalar yalnız **bütün kolların ulaştığı ortak görevler** üzerinden alınır;
kollar farklı sayıda görevi tamamlayabiliyor ve farklı kümeler üzerinden
ortalama kıyaslamak yanıltır.

## 4. Trafik sağdan akar

Tek yön uygulanır (bölgede 3.083 tek yönlü kenar). Sola dönüş karşı akımı
kestiği için maliyetlidir; U dönüşü manevradır. Arama **kenar tabanlıdır**
(satır grafiği): düğüm tabanlı Dijkstra/A* kavşağa nasıl girildiğini bilmez ve
sola dönüşü sağa dönüşle aynı fiyata alır.

| Dönüş | Maliyet |
|---|---|
| düz | 0 sn |
| sağ | 3 sn |
| sol | 10 sn |
| U | 25 sn |

Bunlar **beyan edilmiş tasarım parametreleridir**, ölçüm değil. Dört sınama
davranışı doğruluyor (`testler/test_donus.py`): sol > sağ > düz, eşit uzunlukta
sağ dönüşlü yol seçiliyor, U en pahalı, tek yönlü kenara ters girilemiyor.

Hızlar da düz bir varsayım değil: `maxspeed` etiketi varsa o, yoksa yol sınıfı
(20–90 km/sa; `maxspeed` 5–130 km/sa aralığında kabul edilir). Eskiden bütün ağda
düz 15 km/sa kullanılıyordu.

## 5. Kapanmaya varmanın bedeli — eski 20 dakikalık sabit kaldırıldı

Eski tatbikatta kapanmaya varan ekip **20 dakika** sabit ceza yiyordu ve
makaledeki "farkın %97,4'ü bu cezadan geliyor" sonucu bunun doğrudan eseriydi:
ölçüm, sabitin kendisini ölçüyordu.

Şimdi ayrışık ve beyan edilmiş: **değerlendirme 1,0 dk + manevra 25 sn = 1,42 dk**.
Asıl bedel ekibin fiilen fazladan sürdüğü yoldan gelir ve onu çizge hesaplar.
Sonuçta hem sabit (`kapanmaCezasiDk`) hem ondan gelen süre (`cezadanGelenDk`)
yazılır ki okuyan payını görsün. Mekanizma sınamasında cezanın süredeki payı
**%97,4 → %30** düştü.

> **Düzeltme (27 Eylül, tarama).** %30, bu tatbikatın değil *rastgele kapanma
> kümesiyle yapılan bir mekanizma sınamasının* sonucudur (EKSIKLER, 26 Eylül
> kaydı); betiği ve çıktısı depoda yok. §8.2'den kaba kestirim (keşfin
> bilmeyen kola ait olduğu ve 25 ortak görev varsayımıyla): Nurdağı U-Net
> 44,4 × 1,4167 ≈ 62,9 dk / 25 × 3,04 ≈ 76,0 dk → **≈ %83**. Yani sabit
> 1,42 dk'ya inse de kazancın çoğu hâlâ cezadan geliyor; makaleye %30 değil
> bu kestirim ve duyarlılık bandı (§9) girdi. Kesin pay için koşu
> `cezadanGelenDk` ile tekrarlanmalı. Ayrıca kapanmada geri dönüş, cezanın
> içindeki 25 sn manevraya ek olarak yeniden planlamada 25 sn U dönüşü
> olarak da fiyatlanıyor (manevra iki kez sayılıyor).

## 6. Yol verisi Overpass'a bağlı değil

Overpass'ın dört aynası da ulaşılamaz ölçüldü (bağlantı hatası, 21–30 sn).
Yol ağı ve yol maskesi artık yerel Türkiye PBF'inden tek geçişle çıkarılan
bölge dosyasından geliyor: **756.623 yol kenarı, 718.564 düğüm, 205 tesis**.
Graf ve maske **aynı** kaynaktan — eskiden iki ayrı kaynak kullanıldığında
kenarlar birbirini tutmuyordu. Maske 1,13 sn, graf 2,7 sn.

Dosya depoya girmez (164 MB); `araclar_yerel_osm_kur.py` ile yeniden üretilir.

## 7. Alanlar

Alan kutuları **elle yazılmaz**. `araclar_alan_katalogu.py` her açık drone
sahnesinin uçuş izini tarar, gerçekten dolu olan en iyi ~500 m'lik pencereyi
ölçerek seçer ve künyesiyle kaydeder. Drone mozaiğinin OAM kutusu bütün uçuş
zarfıdır ve içinin büyük bölümü siyahtır; kutuyu elle yazmak "görüntünün %61'i
boş" durumunu yeniden üretiyordu.

## 8. Ölçülen sonuçlar — makaleye giren üç alan

**Kapsam kararı.** 11 ölçülen alandan **üçü** raporlanıyor: Defne / Elektrik Mah.,
İslahiye, Nurdağı. Bunlar kıyas kollarının ayrıştığı alanlardır. **Seçimin kendisi
makalede yazılmalı:** kalan 8 alanda kollar ayrışmadı, çünkü ya model kapanma
bulmadı ya da bulduğu kapanmalar 25 rotanın hiçbirinin üzerine düşmedi. Bu cümle
olmadan üç alan raporlamak kiraz toplamaktır.

### 8.1 Alan künyeleri (ölçüldü)

| Alan | İl | Sahne | Çekim | Uçuş izi | Pencere | OSM yol oranı |
|---|---|---|---|---|---|---|
| Defne / Elektrik Mah. | Hatay | Hatay - Defne - Elektrik Mah. | 2023-02-09 | %59 | 499,3 m | 0,302 |
| İslahiye | Gaziantep | Islahiye, Turkey - Feb 15, 2023 | 2023-02-14 | %100 | 499,7 m | 0,218 |
| Nurdağı | Gaziantep | Nurdagi - Feb 15, 2023 (Warning Low Quality) | 2023-02-14 | %100 | 500,5 m | 0,220 |

Pencere değerleri katalogdan (`tatbikat_alanlari.json`, `pencereM`); önceki
sürümde Defne için yazılan 468 m başka bir alana aitti (27 Eylül düzeltmesi).
Sağlayıcının üçü de Help.NGO; OAM kimlikleri 63eb78a0…920 / 63eef9a4…49a /
63ef697b…4a2, lisans CC-BY 4.0, özgün çözünürlük 3,41 / 7,85 / 7,10 cm. Model
bu ortofotoları z18 karolarıyla (~0,48 m/piksel) işler.

Nurdağı sahnesine sağlayıcı kendi kalite uyarısını koymuş ("Warning Low Quality");
bu makalede belirtilmeli.

### 8.2 Üç alan × üç model × beş tohum

Her alanda 5 giriş ağzı × 5 afetzede, 5 turda döndürülerek **25 çift**. Çıkarım
tohumdan bağımsız olduğu için analiz alan-model başına bir kez koşar, tatbikat
tohum başına tekrarlanır. Süreler dakika, `ortalama ± standart sapma`.
"küme" sütunu kaç tohumun **farklı** afetzede kümesi ürettiğini söyler.

| Alan | Model | Hasar | Kapalı kenar | Afetzede | Kapanmayı bilmeyen | Telsizle paylaşan | QuakeMind | Kazanç | Keşif | Küme |
|---|---|---|---|---|---|---|---|---|---|---|
| Defne / Elektrik | Hızlı (MiT-B0) | %0,67 | 4 | 1 | — | — | — | **araç rotası yok** | — | 1/5 |
| Defne / Elektrik | Dengeli (MiT-B2) | %1,26 | 10 | 5 | 2,20 ± 0,00 | 1,78 ± 0,04 | 1,30 ± 0,00 | **%40,9** | 10,0 | 1/5 |
| Defne / Elektrik | En iyi (U-Net MiT-B4) | %1,49 | 12 | 3 | 2,70 ± 0,00 | 2,40 ± 0,00 | 1,60 ± 0,00 | **%40,7** | 4,0 | 1/5 |
| İslahiye | Hızlı | %0,93 | 10 | 4 | 1,40 ± 0,00 | 1,40 ± 0,00 | 1,30 ± 0,00 | %7,1 | 1,0 | 1/5 |
| İslahiye | Dengeli | %2,06 | 16 | 5 | 2,04 ± 0,15 | 1,98 ± 0,13 | 1,20 ± 0,00 | **%40,9 ± 4,6** | 9,8 | 5/5 |
| İslahiye | En iyi | %1,34 | 12 | 5 | 1,20 ± 0,10 | 1,20 ± 0,10 | 1,08 ± 0,08 | %9,9 ± 3,1 | 1,8 | 5/5 |
| Nurdağı | Hızlı | %3,80 | 22 | 5 | 3,42 ± 0,62 | 2,84 ± 0,34 | 1,36 ± 0,09 | **%59,5 ± 5,3** | 29,4 | 5/5 |
| Nurdağı | Dengeli | %5,60 | 40 | 5 | 3,62 ± 0,68 | 3,18 ± 0,60 | 1,24 ± 0,09 | **%64,9 ± 5,7** | 33,8 | 5/5 |
| Nurdağı | En iyi | %3,55 | 26 | 5 | 4,58 ± 0,87 | 3,80 ± 0,76 | 1,54 ± 0,13 | **%65,8 ± 3,6** | 44,4 | 5/5 |

**Keşif sütunu** (27 Eylül notu): kod `toplamKesif`'i kol başına, tohum başına ve
yalnız ortak görevler üzerinden toplar (`tatbikat.py`); tablonun hangi kolun
keşfini gösterdiği ve 5 tohum ortalamasını üreten birleştirici betik depoda yok.
Defne'de afetzede sayısı modelden gelir (1–5), yani çift sayısı 25'ten azdır.
Kapsama modelden bağımsızdır: Defne %19, İslahiye %46, Nurdağı %44.

**Tekrar üretilebilirlik.** Bütün kod değişiklikleri bittikten sonra aynı komut
baştan koşuldu (3 alan × 3 model × 5 tohum) ve yukarıdaki tablonun **tek sayısı
bile oynamadı**. Aynı tohum aynı tatbikatı, aynı görüntü aynı maskeyi veriyor.

### 8.3 Bu tablo ne söylüyor

1. **Kazanç, keşif sayısını izler.** Ekip kaç kapanmaya fiilen denk gelirse kazanç
   o kadar büyük: Nurdağı'nda 29–44 keşif → %59–66; İslahiye'de En iyi modelle
   1,8 keşif → %10. Kapanmanın rotaya düşmediği yerde fark yoktur.

2. **Nurdağı sağlam, diğer ikisi ihtiyatlı okunmalı.** Yalnız Nurdağı'nda üç
   modelin üçü de beş farklı tohum kümesiyle koşabildi ve sonuç %59–66 bandında
   kaldı. Defne'de blob sayısı az olduğu için beş tohum tek kurulum veriyor
   (küme 1/5); yayılım 0,00 **sağlamlık değil, tek örneklem** demektir.

3. **Daha çok hasar bulmak daha çok operasyonel fayda demek değil.** İslahiye'de
   "Dengeli" model %2,06 hasar ve 16 kapalı kenarla **%40,9** kazandırıyor; "En
   iyi" model %1,34 hasar ve 12 kapalı kenarla yalnız **%9,9**. Belirleyici olan
   bulunan hasarın miktarı değil, **kapanmaların ekip rotalarına düşüp
   düşmediği**. Bu, bölütleme başarımı ile operasyonel sonucun doğrudan orantılı
   olmadığını gösteren ölçülmüş bir bulgudur.

4. **Model seçimi tatbikatın kurulabilmesini belirliyor.** Defne'de Hızlı model
   %0,67 hasar buluyor, tek afetzede çıkıyor ve çıkardığı 4 kapanma o afetzedeyi
   araç yolundan **tamamen kesiyor** — kapanmasız çizgede aynı hedefe 92 saniyede
   varılıyor. Bu satır hata değil, sonucun kendisidir: zayıf model hem az hasar
   bulur hem de bulduğu azı yanlış yere koyarsa mahalleyi kâğıt üzerinde
   ulaşılamaz kılar.

<!-- DUYARLILIK -->

## 9. Duyarlılık — sonuç hangi varsayıma ne kadar bağlı?

Defne / Elektrik, İslahiye ve Nurdağı; aynı model (`segformer_mitb4_dice30`),
aynı maske, tek tohum (42). Yalnız beyan edilmiş sabitler değiştirildi.
Hücreler: *kapanmayı bilmeyen ekip → QuakeMind (kazanç)*, dakika.

| Koşu | Defne / Elektrik | İslahiye | Nurdağı |
|---|---|---|---|
| **ANA** — ceza 1,42 dk, dönüş maliyetli | 1,80 → 1,30 (**%28**) | 1,50 → 1,30 (**%13**) | 3,30 → 1,40 (**%58**) |
| Dönüş maliyeti kapalı | 1,40 → 1,00 (%29) | 1,50 → 1,10 (%27) | 2,50 → 1,10 (%56) |
| Değerlendirme 0,5 dk | 1,70 → 1,30 (%24) | 1,50 → 1,30 (%13) | 2,80 → 1,40 (%50) |
| Değerlendirme 2,0 dk | 2,20 → 1,30 (%41) | 1,60 → 1,30 (%19) | 4,30 → 1,40 (%67) |
| **ESKİ SABİT — toplam 20 dk** | 8,30 → 1,30 (%84) | 3,40 → 1,30 (%62) | 22,60 → 1,40 (**%94**) |

**Okunuşu.**

1. **Dönüş maliyeti sonucu büyük ölçüde belirlemiyor — İslahiye hariç.** İslahiye'de
   kazanç %13 → %27 değişiyor (aşağıdaki cümle yalnız Defne ve Nurdağı için doğru).
   Not: bu tablo `segformer_mitb4_dice30` ile koşuldu, §8.2'deki modellerle değil;
   ANA satırı §8.2 ile bu yüzden farklıdır. Sağdan trafik kuralı mutlak süreleri
   ~%30 artırıyor (gerçekçi olan da bu) ama göreli kazancı bırakıyor: %28↔%29,
   %58↔%56. "Kapanmayı bilmek şu kadar kazandırıyor" cümlesi bu parametreye
   yaslanmıyor.
2. **Değerlendirme süresi ölçülü bir etki yapıyor.** 0,5–2,0 dk aralığında kazanç
   %24–41 (Defne), %13–19 (İslahiye), %50–67 (Nurdağı). Alanların **sıralaması
   değişmiyor**; sonuç tek sayı değil, bant olarak raporlanmalı.
3. **Eski 20 dakikalık sabit tek başına sonucu üretiyor.** Aynı alan, aynı model,
   aynı kapanmalarla Nurdağı "22,6 dk → 1,4 dk, **%94 iyileşme**" diye okunuyor.
   Eski taslaktaki "184,9 dk → 12,8 dk" mertebesindeki iddialar bu sınıftandır:
   ölçülen şey sistemin katkısı değil, sabitin kendisidir. **Bu satır makalede
   sonuç olarak kullanılmamalı; yalnız neden bıraktığımızı göstermek için durur.**

Makalede verilecek cümle şu olmalı: *kapanmaları önceden bilmek, modelin bulduğu
kapanmaların ekip rotalarına fiilen düştüğü alanlarda erişim süresini kısaltır;
ölçülen bant alan ve modele göre %7–66, en sağlam alanda (Nurdağı, üç model ×
beş tohum) %59–66'dır. Kapanmanın rotaya düşmediği alanlarda fark yoktur.*

## 10. Moloz yayılım yarıçapı (r_h) — ölçüldü, varsayılan değiştirilmedi

`r_h`, hasarın yoldan ne kadar uzağa yayıldığını varsayan bir yarıçaptır:
0 = yalnız yolun tam üstündeki hasar kapatır (uygulamanın kuralı, taban çizgi).
Çıkarımı etkilemez, yalnız maskeden kapanma türetmesini etkiler; bu yüzden model
bir kez koşar, her yarıçap için kapanma ve kollar yeniden hesaplanır.

| Alan | r_h | Kapalı kenar | Ortak görev | Bilmeyen | QuakeMind | Görünür kazanç |
|---|---|---|---|---|---|---|
| Defne / Elektrik | **0** | 12 | **6** | 2,70 | 1,60 | %41 |
| | 10 | 32 | 3 | 3,40 | 1,50 | %56 |
| | 15 | 34 | 3 | 3,00 | 1,50 | %50 |
| | 25 | 40 | **0** | — | — | — |
| İslahiye | **0** | 12 | **20** | 1,10 | 1,00 | %9 |
| | 10 | 62 | 5 | 3,20 | 1,30 | %59 |
| | 15 | 75 | 5 | 3,20 | 1,30 | %59 |
| | 25 | 86 | **0** | — | — | — |
| Nurdağı | **0** | 26 | **25** | 4,40 | 1,60 | %64 |
| | 10 | 114 | 7 | 10,10 | 1,90 | %81 |
| | 15 | 140 | 6 | 7,30 | 1,80 | %75 |
| | 25 | 164 | 5 | 6,80 | 1,70 | %75 |

**Okunuşu — buradaki tuzak görünür kazancın ARTMASI.** r_h büyüdükçe "kazanç"
yükseliyor (%41 → %56, %9 → %59, %64 → %81) ama bu bir iyileşme değil:
**ortak görev sayısı çöküyor** (6 → 3, 20 → 5, 25 → 7) ve iki alanda r_h = 25'te
**sıfıra** düşüyor. Yani yarıçap büyüdükçe kapanma sayısı artıyor, mahalle
kopuyor, geriye yalnız kolay çiftler kalıyor ve ortalama onların üzerinden
alınıyor. Yüzde, giderek daralan ve yanlı bir örneklemden geliyor.

Bu, daha önce başka bir kurulumda ölçülen sonucu doğruluyor: **r_h uzamayı
değil aracın girebilmesini belirliyor.** Varsayılan **r_h = 0** değiştirilmedi;
makaledeki bütün sayılar bu değerle üretilmiştir.

## 10.1 Üç rota varyantı ne anlatıyor

Harita aynı ekip–afetzede çifti için **üç** güzergâh çizer; üçü aynı çiftin üç
farklı planlama kuralıyla hesaplanmış hâlidir.

| Çizgi | Kural | Ne demek |
|---|---|---|
| Gri kesik | Kapanmalar **yok sayılır**, bütün yollar açık | Kıyas çizgisi: bilmeseydik buradan giderdik |
| **Mavi** | Kapalı kenarlar çizgeden **çıkarılır** | **Ekibin fiilen gittiği yol** |
| Sarı | Kapalılar çıkarılır **ve** hasara yakın kenarlar pahalılaşır (kapatılmaz) | Molozun dibinden geçme, biraz dolaş |

Nurdağı, U-Net MiT-B4, tohum 42 (uzunluklar):

| Görev | gri | mavi | sarı | okunuşu |
|---|---|---|---|---|
| Ekip 1 | 467 m | 462 m | 462 m | kapanma rotayı değiştiriyor: metrede kısa, sürede uzun (0,9 → 1,0 dk) |
| Ekip 2 | 463 m | **820 m** | 820 m | kapanma 357 m dolaştırıyor |
| Ekip 3 | 822 m | 822 m | **975 m** | yol kapalı değil ama sarı enkazdan uzak duruyor |
| Ekip 5 | 449 m | 400 m | 466 m | metrede kısa, **sürede uzun** (aşağıya bakınız) |

**Uzama hangi birimde ölçülmeli?** Rotalar **süreye** göre seçiliyor (kenar
hızları + dönüş maliyeti), uzunluğa göre değil. Bu yüzden bir rota metrede
kısalıp sürede uzayabilir — Ekip 1'de tam olarak bu oluyor (466,6 → 462,1 m
ama 0,9 → 1,0 dk). Ölçüt her iki birimde de verilir ve **fark büyüktür**:

| | Ortalama uzama | En büyük |
|---|---|---|
| Metre | 101,7 m (%32,8) | 634,7 m |
| **Süre** | **0,43 dk (%61,6)** | 1,8 dk |

Süre uzaması mesafe uzamasının neredeyse iki katı: dolaşmak yavaş sokaklara ve
fazladan dönüşe sokuyor. **Makalede süre cinsinden uzama asıl ölçüt olmalı;**
metre yanında verilebilir ama tek başına okunmamalı.

## 11. Uçtan uca doğrulama (konsolun kullandığı uçlardan)

Nurdağı, "En iyi" model, `POST /api/simulasyon/kos`:

| | |
|---|---|
| Süre | **35 saniye** (202 + iş kimliği, canlı durum) |
| Graf | 296 düğüm / 715 kenar, 26 kapalı kenar |
| Kapsama | **%44,1** (modelin fiilen baktığı kenar oranı) |
| Ekipler | mahallenin gerçek giriş ağızları: `tertiary girişi 1…3`, `residential girişi 4…5` |
| Görev | ekranda 5, ölçüm 25 çiftten |
| Kapanmayı bilmeyen ekip | 4,4 dk · 6 U dönüşü |
| Telsizle paylaşan filo | 3,8 dk · 6 U dönüşü |
| **QuakeMind** | **1,6 dk · 0 U dönüşü** (%64) |

**Araç ve uç aynı sayıyı veriyor.** Bütün kod değişiklikleri bittikten sonra
Nurdağı hem koşu aracıyla hem uçtan koşuldu: 26 kapalı kenar, kapsama %44,06,
kollar 4,4 / 3,8 / 1,6 dk, U dönüşü 6 / 6 / 0 — **birebir aynı**. Yani makaleye
hangi yoldan sayı alınırsa alınsın aynı sonuç çıkar.

**J-83 kapandı — hata yoktu.** Araçla ucun farklı sayı vermesinin sebebi farklı
**model**di (araç etkin modeli, uç "En iyi"yi koşuyordu). Aynı modelle yan yana
koşulduğunda iki yol birebir aynı sonucu veriyor: aynı sınırlar, aynı karar ayarı,
aynı hasar oranı (%3,550), aynı kapalı yol (26) ve hasar maskesinin **1.638.400
pikselinin tamamı** aynı. Analiz yolu tekrar üretilebilir. Ders: kıyas tablosuna
model adı yazılmadan sayı konulmamalı.

## 12. Makaledekilerin yerini tutuyor mu? (denetim, 26 Eylül)

Makaleye **dokunulmadı**; bu yalnız bir kapsam denetimidir. Taslaktaki
simülasyon kaynaklı her bölüm tek tek karşılaştırıldı.

| Makale bölümü | Taslaktaki içerik | Yeni simülasyon karşılığı | Durum |
|---|---|---|---|
| §3.8.1 | Sentetik kapanma üreteci | Yok; kapanmalar gerçek drone görüntüsünden, kendi modelimizden türetiliyor | **Yerini tutar** (ve daha sağlam) |
| §4.6 | R0–R3 referans ajanları, `t_u = 20 dk` | Üç kol (bilmeyen / telsizle paylaşan / QuakeMind), ayrışık ceza 1,42 dk | **Yerini tutar** |
| §4.9 | Bileşen çıkarma, parametre duyarlılığı | Dönüş maliyeti ve değerlendirme süresi duyarlılığı (§9) | **Yerini tutar** |
| §4.5 | 8 bölge × 6 çift × 10 tohum = 480 atama (sentetik) | 3 gerçek mahalle × 25 çift × 5 tohum × 3 model | **Kısmen** — veri gerçek ama bölge/tohum sayısı düşük |
| §4.8 | Geçilebilirlik kuralı (r_h) duyarlılığı | `yaricapKiyasi` kodda var, arayüzden kaldırıldı (J-70) | **Yapılabilir, koşulmadı** |
| §4.3 | Kapanma katmanının **yer gerçeğine** göre değerlendirilmesi (EMSR648) | **Yok** — EMSR kullanılmayacak (karar, 26 Eylül; gerekçe aşağıda) | **BOŞLUK — kritik** |
| §4.7 | Görev ataması (Algoritma 3, 480/480) | Tatbikat ekip–afetzede eşlemesini tur döndürerek yapıyor; atama algoritması `benchmark/full_scenario.py`'de kaldı, tatbikata bağlı değil | **Kapsamıyor** |
| §4.5 (Tablo 16–17) | YOLOv8 ve BERTurk gecikmeleri | Tatbikat yalnız uydu → kapanma → rota zinciri; yer seviyesi ve metin kanalları koşmuyor | **Kapsamıyor** |
| §4.5 | Toplanma alanı yönlendirmesi | Yok | **Kapsamıyor** |

### En kritik boşluk: doğruluk doğrulaması yok

Taslaktaki §4.3, kapanma katmanını **EMSR648 yer gerçeğiyle** karşılaştırıyordu.
EMSR bırakıldığına göre yerine hiçbir şey konmadı. Bugünkü tatbikatta **dünya =
modelin kendi çıktısıdır**; bu yüzden ölçtüğümüz şey "kapanmayı önceden bilmenin
kazandırdığı süre"dir, "kapanmaları doğru bulduğumuz" değil. Bu ayrım raporda ve
makalede zaten açıkça yazılı (§3), ama **makalede kapanma katmanının doğruluğuna
dair hiçbir iddia kalamaz** — dayanağı yok.

**EMSR kullanılmayacak — karar verildi (26 Eylül) ve gerekçesi ölçüldü.**
EMSR648 yalnız bina vermiyor; `transportationL` katmanında yollar da hasar
dereceli. Ama bizim Defne / Elektrik kutumuzda **62 yolun 62'sine "görünür hasar
yok"** diyor, 74 binanın 72'sini sağlam sayıyor — aynı kutuda bizim model 9.474
hasar pikseli ve 12 kapalı kenar buluyor, drone fotoğrafında mahalle dümdüz.
Antakya'nın tamamında EMSR yalnız 39 yolu "yıkık", 31'ini "hasarlı" işaretlemiş
(4.613 yolun %1,5'i).

Sebep **tanım farkı**: EMSR uzmanı uydudan, şehir ölçeğinde yorumlamış ve "yol
hasarlı" derken *yolun kendisinin bozulmasını* (köprü çökmesi, asfalt yarılması)
kastediyor; bizim sorumuz *yanındaki bina çöküp yolu molozla kapatması*. Bu,
daha önceki EMSR kalibrasyonunun neden kötü çıktığını da açıklıyor (F1
0,098–0,205): model başarısızlığı değil, farklı bir soruyu ölçen cetvele göre
not almak. EMSR'ı cetvel yapmak sistemi **yanlış sebepten** kötü gösterirdi.

Geriye iki yol kalıyor:
1. **Sınırlılık olarak beyan et.** En ucuzu: §4.3 tamamen kalkar, §5.3'e
   "kapanma katmanı için yer gerçeği doğrulaması yapılmamıştır" cümlesi girer.
   Simülasyonun iddiası operasyonel değere daralır.
2. **Kendi yer gerçeğimizi üret.** Üç alanın drone görüntüsü üzerinde kapalı
   yollar elle işaretlenir (bir mahalle ~1–2 saat), kesinlik/duyarlılık ölçülür.
   Sınırı da yazılır: tek etiketleyici, yalnız yukarıdan görünen moloz.

### Kapsamıyor diye işaretlenenler

Tatbikat **tek kanallıdır**: uydu/drone görüntüsü → hasar → kapanma → rota. Yer
seviyesi (YOLOv8), Türkçe metin (BERTurk), risk skorlama ve toplanma alanı
yönlendirmesi tatbikatın içinde koşmuyor. Taslaktaki §4.5 bunları tek bir senaryo
içinde sunuyordu; yeni simülasyon bu iddiayı desteklemez. Ya bu kanallar tatbikata
eklenir, ya da makalede senaryo "uydu → sevk zinciri" olarak daraltılır.

Görev ataması da tatbikatta yok: ekip–afetzede eşlemesi tur döndürmeyle yapılıyor
(ölçüm 25 çift üzerinden). Atama algoritması eski senaryo koşucusunda duruyor ama
yeni tatbikata bağlı değil.

## 13. Kapanma katmanının doğruluğu — kendi yer gerçeğimizle (deneme, 1 mahalle)

EMSR kullanılmadığına göre (§11) cetveli kendimiz ürettik. **Bu bir denemedir:**
tek mahalle, tek etiketleyici, küçük örneklem. Sayılar makaleye *bu sınırlarla*
taşınmalı.

**Yöntem.** Yol parçaları, modelin ne dediği **görülmeden** (kör), gerçek drone
ortofotosunun kesitleri üzerinden işaretlendi. Modelin kapalı dediklerinin
tamamı + açık dediklerinden %24,8'lik rastgele örnek. Ölçüt: `kapalı` (molozun
parçayı belirgin biçimde örtmesi), `açık` (sürekli geçilebilir koridor),
`kararsız` (gölge / çözünürlük / çizginin görünür sokağı takip etmemesi).

Alan: Hatay / Defne – Elektrik Mah., Help.NGO drone ortofotosu (2023-02-09),
model U-Net MiT-B4. Etiketlenebilir parça: 118 (modelin 5'i kapalı, 113'ü açık).

| | etiket: kapalı | açık | kararsız |
|---|---|---|---|
| **Model KAPALI dedi** (5) | **3** | 0 | 2 |
| **Model AÇIK dedi** (28 örnek) | **6** | 14 | 8 |

**Çıkan sayılar.**

| Ölçüt | Değer | Not |
|---|---|---|
| Kesinlik (kararsız hariç) | **3/3 = %100** | %95 Wilson aralığı **%44–100** — n=3, tek başına kullanılamaz |
| Kesinlik (kararsız hata sayılırsa) | 3/5 = %60 | alt sınır |
| Kaçırılan kapanma kestirimi | ~24 parça | örnekte 6, %24,8 oranla ölçeklendi |
| Gerçek kapanma kestirimi | ~27 / 118 (%23) | |
| **Duyarlılık kestirimi** | **3/27 ≈ %11** | |
| Yargılanamayan parça | 10/33 (%30) | |

**Okunuşu.** Model **yanlış alarm üretmiyor** — kapalı dediği 3 karar verilebilir
parçanın 3'ü de gerçekten kapalı, hiçbiri açık çıkmadı. Ama **çok azını
buluyor**: mahallede tahminen 27 kapanma varken 3'ünü işaretliyor. Yani
*yüksek kesinlik, düşük duyarlılık*. Bu, daha önce etiketli karolarda ölçülen
tablo ile tutarlı (J-65: "model yıkıntıları doğru işaretliyor, azını buluyor").

**Operasyonel anlamı.** Düşük duyarlılık, tatbikattaki kazanç sayılarının
*iyimser* olmadığını gösterir: gerçekte daha çok kapanma var, yani kapanmayı
bilmenin değeri ölçtüğümüzden büyük olabilir. Ama aynı düşük duyarlılık,
sistemin sahada tek başına güvenilecek bir kapanma haritası vermediği anlamına
da gelir — bu cümle makalede yer almalı.

**Sınırlar (makalede aynen yazılmalı).** Tek etiketleyici, ikinci görüş yok,
etiketleyiciler arası uyum ölçülmedi. Parçaların %30'u yargılanamadı. Modelin 12
kapanmasından yalnız 5'i uçuş izinin dolu olduğu yere düşüyor. Kesinlik 3 karar
verilebilir parçaya dayanıyor. Yalnız yukarıdan görünen moloz yakalanır.
Görüntü depremden 3 gün sonrasına ait; bir miktar açma çalışması başlamış olabilir.

Veri ve araç: `backend/benchmark/kapanma_yer_gercegi/`,
üretici `araclar_kapanma_etiketle.py` (tohumla yeniden üretilebilir).

## 14. Başarım — nereye ne kadar süre gidiyor

Ölçüm ortamı: 20 çekirdekli CPU (GPU yok), PyTorch 2.10 CPU, 6 iş parçacığı,
1280×1280 görüntü (z18, 0,482 m/piksel). Üç alan × iki tekrar.

| Aşama | Ortalama | En az – en çok | Pay |
|---|---|---|---|
| **Model çıkarımı** | **9,12 sn** | 8,17 – 10,46 | **%61** |
| Lojistik (kapanma türetme, seri hâle getirme) | 1,63 sn | 0,26 – 4,37 | %11 |
| Kıyas kolları (3 kol × 25 çift) | 0,49 sn | 0,37 – 0,75 | %3 |
| Rota koşusu (Dijkstra + A*) | 0,38 sn | 0,26 – 0,62 | %3 |
| Mahalle grafiği | 0,32 sn | 0,27 – 0,36 | %2 |
| Ekip/afetzede kurulumu | 0,01 sn | | — |
| Uydu karosu, OSM yolu (önbellekten) | ~0 sn | | — |
| **Toplam** | **15,01 sn** | 12,05 – 18,11 | |

Soğuk koşuda (karo ve yol önbellekte yokken) uçtan uca ölçülen süre **35 sn**
(uydu 2,8 · yol 8,7 · çıkarım 7,7 + rota). Karolar indikten sonra aynı alan
15 sn'de koşar; aynı alan+model ikinci kez istenirse parmak izi önbelleği
çıkarımı hiç koşturmaz.

### 14.1 Denenip BIRAKILAN iyileştirmeler

Üçü de ölçüldü; hiçbiri varsayılan yapılmadı, gerekçesi yazıldı.

| Deneme | Sonuç | Karar |
|---|---|---|
| Parçaları toplu koşturmak (yığın 2/4/8) | Çıktı **birebir aynı** (maske özdeş, ham olasılıkta en büyük fark 6·10⁻⁶) ama **%18 daha yavaş**: 8,49 → 10,02 sn | Varsayılan 1. PyTorch tek çağrı içinde zaten paralel; yığın yalnız bellek baskısı ekliyor. GPU'da tersi beklenir, knob duruyor (`QM_CIKARIM_YIGINI`) |
| İş parçacığı sayısı (2–20) | 2: 17,8 · 4: 12,2 · **6: 9,9** · 8: 14,0 · 10: 13,2 · 14: 12,1 · 20: 12,2 sn. Hasar pikseli hepsinde aynı | Mevcut sınır (6) zaten en iyisi; değiştirilmedi |
| Parça örtüşmesini azaltmak (adım 256→384) | Süre **%40 düşüyor** (8,8→5,6 sn) ama maske değişiyor: taban maskeyle IoU 0,84 (Defne) / 0,87 (Nurdağı) | **Alınmadı.** Doğruluk bedeli ölçüldü ve kabul edilmedi; knob duruyor (`QM_CIKARIM_ADIMI`) |

**Sonuç: çıkarım bu kurulumda pratik optimumunda.** Kalan tek gerçek kaldıraç
model seçimi.

### 14.2 Model seçimi — süre, doğruluk ve operasyonel karşılığı

Aynı görüntü, aynı ayar, 6 iş parçacığı.

| Model | Parametre | Sınama IoU | Çıkarım | Nurdağı kazanç | İslahiye kazanç | Defne kazanç |
|---|---|---|---|---|---|---|
| Hızlı (SegFormer MiT-B0) | 3,7 M | 0,382 | **1,91 sn** | %59,5 ± 5,3 | %7,1 | araç rotası yok |
| **Dengeli (SegFormer MiT-B2)** | 24,7 M | 0,409 | **4,71 sn** | %64,9 ± 5,7 | **%40,9 ± 4,6** | **%40,9** |
| En iyi (U-Net MiT-B4) | 64,1 M | 0,433 | **10,50 sn** | %65,8 ± 3,6 | %9,9 ± 3,1 | %40,7 |

**Okunuşu — makaleye değer.** Çıkarım süresini **5,5 kat** artırmak (1,91 →
10,50 sn) sınama IoU'sunu yalnız **+0,051** yükseltiyor, operasyonel kazancı ise
**tek yönlü artırmıyor**: orta boy model (MiT-B2, 4,71 sn) üç alanın üçünde de
en iyi ya da en iyiye yakın, İslahiye'de en büyük modelin dört katı kazanç
veriyor (%40,9 ↔ %9,9). **Saniye başına operasyonel değer en yüksek olan orta
boy modeldir.** Bölütleme başarımını artırmak, sevk zincirindeki faydayı
orantılı artırmıyor.

## 15. Makale şekilleri — dosyalar ve önerilen alt yazılar

Dizin: `backend/benchmark/makale_sekilleri/`. Üreticiler
`araclar_makale_sekilleri.py` (grafikler) ve `araclar_makale_haritalari.py`
(haritalar). **Şekillerdeki her sayı bu belgedeki ölçümden gelir;** sayı
değişirse önce buradaki tablo, sonra şekil güncellenir.

| Dosya | Önerilen alt yazı |
|---|---|
| `sekil_kiyas_kollari.png` | **Şekil X.** Kapanmayı önceden bilmenin erişim süresine etkisi. Üç gerçek mahalle, U-Net MiT-B4, mahalle başına 25 ekip–afetzede çifti, beş tohum; çubuklar ortalama, çizgiler standart sapma. Ortalamalar yalnız bütün kolların ulaştığı ortak görevlerden alınmıştır. |
| `sekil_duyarlilik.png` | **Şekil X.** Sonucun beyan edilen ceza süresine duyarlılığı. Kapanmaya varan ekibin kaybettiği süre 0,5–2,0 dk aralığında değiştirilmiştir; alanların sıralaması değişmemektedir. Taralı sütun, önceki taslakta kullanılan 20 dakikalık sabiti gösterir: aynı veriyle kazanç %94'e çıkmaktadır. Bu sütun sonuç olarak kullanılmamıştır. |
| `sekil_model_secimi.png` | **Şekil X.** Model seçiminin süre, bölütleme başarımı ve sevk zincirindeki karşılığı. Çıkarım süresini 5,5 kat artırmak sınama IoU'sunu 0,051 yükseltmekte, operasyonel kazancı ise tek yönlü artırmamaktadır. |
| `sekil_sure_dagilimi.png` | **Şekil X.** Bir tatbikat koşusunda sürenin aşamalara dağılımı (20 çekirdekli CPU, altı iş parçacığı, GPU yok; toplam 15,0 sn). Süre model çıkarımında yoğunlaşmaktadır (%61). |
| `sekil_tatbikat_<alan>.png` | **Şekil X.** \<Alan\> tatbikat koşusu. Zemin, modelin analiz ettiği drone ortofotosudur; kırmızı alanlar modelin hasarlı bulduğu pikseller, koyu kırmızı çizgiler bunlardan türetilen kapalı yollar, mavi çizgiler kapanmalara göre hesaplanan ekip güzergâhlarıdır. Künye satırında kapsama oranı yazılıdır: modelin fiilen değerlendirebildiği kenar oranı. |
| `sekil_oncesi_sonrasi_<alan>.png` | **Şekil X.** Aynı alanın (a) deprem öncesi görüntüsü (Esri Wayback), (b) deprem sonrası drone ortofotosu, (c) modelin hasar maskesi. Üç kare birebir aynı coğrafi çerçevededir. |

**Uyarı — şekil künyelerinde kalmalı.** Tatbikat haritasında ekip giriş ağızları
mahallenin +150 m marjındadır; bir bölümü görüntü karesinin dışında kalır ve
künyede kaç tanesinin kare dışında olduğu yazılıdır. Kapsama oranı da künyededir:
modelin görmediği kenar "açık" sayılır ama **ölçülmemiştir**, bu şekilde
okunmalıdır.

## 16. Yeniden üretme

Bütün komutlar `backend/` içinden, kök `venv/` ortamıyla koşar.

```bash
venv/Scripts/python.exe araclar_yerel_osm_kur.py
```

```bash
python araclar_alan_katalogu.py --cikti apps/road_damage/data/tatbikat_alanlari.json
```

```bash
python araclar_tatbikat_kos.py --alanlar apps/road_damage/data/tatbikat_alanlari.json --sec "Defne - Elektrik" "Islahiye" "Nurdagi" --model unet_mitb4_p2_t42 --tohum 42 43 44 45 46 --cikti sonuc.json
```

```bash
python araclar_makale_sekilleri.py
```

```bash
python araclar_makale_haritalari.py --alan Nurdagi
```

```bash
python testler/test_donus.py
```

Yerel OSM bölge verisi (~164 MB) depoya girmez; ilk komut onu yeniden üretir
(~18 dk, tek geçiş). Kapanma yer gerçeği etiketleme kesitleri için
`araclar_kapanma_etiketle.py`.

## 17. Yer seviyesi kanallar — kamera (YOLO) ve metin (BERTurk)

27 Eylül 2026'da eklendi (J-108). Uydu kanalı mahalleye yukarıdan bakıyordu;
bu ikisi aynı mahalleye yerden bakar. Üçü de ortak sözleşmeye iner
(CLAUDE.md kural 2) ve konsolun ısı haritasındaki kendi kanallarını besler.

### 17.1 Neyin gerçek, neyin üretildiği

| Parça | Durum | Kanıt |
|---|---|---|
| Fotoğraflar | **Gerçek** — 6 Şubat 2023 depremi, 13 adet, çoğu Hatay | `[Ö]` Wikimedia Commons; Public domain (VOA) ve CC BY-SA 4.0; künye + SHA-256: `apps/camera_detection/data/tatbikat_foto/KUNYE.json` |
| YOLO çıkarımı (`catlak.pt` + `bina.pt`) | **Gerçek** — kendi modellerimiz | `[Ö]` §17.2 |
| İhbar metinleri | **Üretildi** — elle yazıldı, gerçek çağrı değil | `[K]` `apps/disaster_nlp/data/tatbikat_metinleri.json` |
| BERTurk sınıflandırma + NER | **Gerçek** — model metinlerin üstünde koştu | `[Ö]` §17.3 |
| Her ikisinin **haritadaki konumu** | **Üretildi** — tohumla, modelin hasarlı bulduğu alanlardan | `[K]` `tatbikat_kanallar._hasar_konumlari` |

Konum neden üretiliyor, iki ölçülmüş sebep:

1. Fotoğrafların EXIF konumu yok, Commons kayıtları da sokak düzeyinde konum
   vermiyor. Tatbikat alanı 500 m'lik bir mahalle; "Hatay" bilgisi bu ölçekte
   hiçbir işe yaramıyor.
2. Metin hattının coğrafi kodlayıcısı **mahalle merkezine** düşürüyor: "Defne
   Elektrik Mahallesi" → (36,17 / 36,13). Tatbikat kutusunun merkezi ise
   (36,1977 / 36,1494) — yaklaşık **2 km** ötede ve kutunun tamamen dışında.
   Yani modelin kendi coğrafi kodu bu ölçekte kullanılamıyor.

Her kayıt `sentetikKonum: true` taşır; harita göstergesi, panel ve depo kaydı
bunu ayrı ayrı yazar.

### 17.2 Kamera kanalı — ölçüm

Birim: fotoğraf. Cihaz: yerel CPU (kullanıcıda GPU yok). Isınma çağrısı
ölçüme girmez. Koşum: `araclar_kanal_olc.py`, rapor
`benchmark/reports/kanal_olcumu.json`.

| Ölçüt | Değer |
|---|---|
| Fotoğraf sayısı | 13 |
| **Tespit veren fotoğraf** | **13 / 13** |
| Toplam çatlak tespiti | 47 |
| Toplam bina tespiti | 65 |
| Hibrit çıkarım, medyan | 307.9 ms |
| Hibrit çıkarım, en uzun | 383.0 ms |

| Fotoğraf | Çatlak | Bina | En yüksek güven | Lisans |
|---|---|---|---|---|
| after_the_7_8_magnitude_earthquake | 5 | 1 | %77 | CC BY-SA 4.0 |
| after_the_7_8_magnitude_earthquake | 1 | 3 | %67 | CC BY-SA 4.0 |
| after_the_earthquake_hatay_provinc | 3 | 4 | %65 | CC BY-SA 4.0 |
| antakya_city_center_after_7_8_magn | 2 | 37 | %88 | Public domain |
| city_of_antakya_after_7_8_magnitud | 0 | 11 | %86 | Public domain |
| damage_in_hatay_caused_by_the_eart | 4 | 2 | %49 | Public domain |
| damage_of_the_hatay_province_after | 3 | 3 | %83 | Public domain |
| exterior_of_a_damaged_building_aft | 4 | 1 | %67 | CC BY-SA 4.0 |
| exterior_of_a_damaged_building_aft | 5 | 0 | %74 | CC BY-SA 4.0 |
| exterior_of_a_damaged_building_aft | 7 | 0 | %84 | CC BY-SA 4.0 |
| hatay_after_the_earthquake.jpg | 7 | 1 | %70 | CC BY-SA 4.0 |
| hatay_in_the_2023_gaziantep_kahram | 2 | 2 | %41 | Public domain |
| interior_of_a_damaged_building_aft | 4 | 0 | %55 | CC BY-SA 4.0 |

Not: bu sayılar **tespit sayısıdır, doğruluk değildir.** Fotoğraflarda kutu
düzeyinde yer gerçeği yok; mAP ölçülmedi ve makalede ölçülmüş gibi
sunulmamalıdır (kural 8).

### 17.3 Metin kanalı — ölçüm

Birim: ihbar metni. 18 sentetik metin, üç il havuzu.

| Ölçüt | Değer |
|---|---|
| Metin sayısı | 18 |
| Yazarın niyetiyle örtüşen | **9 / 18** |
| Sınıflandırma, medyan | 36.6 ms |
| Sınıflandırma, en uzun | 43.0 ms |
| Örtüşmeyenlerin gittiği sınıf | {"Acil Yardım İhtiyacı": 8, "Enkaz Bildirimi": 1} |

**Bu bir doğruluk değildir.** "Beklenen" alanı metni yazan tek kişinin
etiketidir, yer gerçeği değil; "Enkaz Bildirimi" ile "Acil Yardım İhtiyacı"
sınırı gerçekten bulanıktır (çöken binada mahsur kalan kişi ikisidir birden).
Görülen eğilim şudur: örtüşmeyen 9 metnin **8'i "Acil Yardım İhtiyacı"na**
kayıyor, üstelik yüksek güvenle (0,92 ve 0,97 dahil). Model aciliyet taşıyan
her metni bu sınıfa çekiyor. Makalede F1 iddiası için etiketli bir küme
gerekir (DepremKit / TSEqD); bu ölçüm onun yerine geçmez.

> **Düzeltme (27 Eylül 2026, J-111/J-116):** Yukarıdaki "model aciliyet taşıyan
> her metni bu sınıfa çekiyor" yorumu YANLIŞTI. Kaymayı model değil, 13→5
> katmanındaki anahtar sözcük kurtarması yapıyordu: 18 çıktının 12'sini anahtar
> sözcük belirlemişti (5'i "ekip lazım", "ambulans", "arama kurtarma" ve iki kez
> "araç" içindeki "aç"). Katman düzeltildi ve metinler yeniden ölçüldü (ikinci
> makine, yalnız kategori; gecikme yukarıdaki i7 değeri):
>
> | Ölçüt | Eski katman | Düzeltilmiş katman |
> |---|---|---|
> | Yazarın niyetiyle örtüşen | 9 / 18 | **11 / 18** |
> | Kararı veren | anahtar sözcük 12, model 6 | model 15, anahtar sözcük 3 |
> | Örtüşmeyenlerin gittiği sınıf | Acil Yardım 8, Enkaz 1 | Acil Yardım 4, Enkaz 3 |
>
> Rapor: `backend/benchmark/reports/kanal_olcumu_metin_duzeltilmis.json`
> (satır başına ham 13 etiketli çıktı ve kararın kaynağı yazılı). Kalan 7 ayrılığın
> 3'ü eşlemeden (Yemek/Isınma/Arama Ekipmanı → Acil Yardım), 3'ü modelin "Enkaz
> Kaldırma"sından, 1'i kurtarma önceliğinden ("ambulans giremiyor"). Model 4 yol
> kapanması metninin hiçbirine ulaşım etiketi vermiyor (J-123).

**Coğrafi kodlama gecikmesi:** tam hat (sınıflandırma + NER + coğrafi kodlama)
ölçüldüğünde 18 metnin ikisi **3,3 sn** ve **4,4 sn** sürdü (önbellek ıskası,
ağ çağrısı), medyan 47 ms. Yalnız sınıflandırma ölçüldüğünde medyan
36.6 ms, en uzun 43.0 ms. Tatbikat bu yüzden coğrafi
kodlamayı **çağırmıyor** (kural 3: pahalı iş istek yolunda çalışmaz).

### 17.4 Tatbikat koşusunda (Defne/Elektrik · U-Net MiT-B4 · tohum 42)

| | |
|---|---|
| Yerleştirilen fotoğraf | 4 → 14 çatlak, 40 bina tespiti |
| Yerleştirilen ihbar | 5 |
| Ortak sözleşmeye yazılan | `kamera` 4 · `metin` 5 · `uydu` 41 kayıt |
| Konum | hepsi tatbikat kutusunun içinde, dokuzu da ayrı nokta |

Kayıtlar `ek.tatbikat` taşır: koşu bitirilince `hasar_sil_tatbikat` bunları
siler, tatbikat verisi gerçek olay verisiyle karışmaz.

### 17.5 Üç kanal tek haritada — makale şekli

`araclar_makale_uc_kanal.py --hepsi` üç alan için tek karede üç kanalı ve
zincirin sonunu (kapalı yollar + güzergâh) çizer. Çıktı
`benchmark/makale_sekilleri/sekil_uc_kanal_{defne,islahiye,nurdagi}.png`.

| Alan | Kapalı kenar | Ekip | Afetzede | Kamera | Metin |
|---|---|---|---|---|---|
| Hatay / Defne — Elektrik Mah. | 12 | 3 | 3 | 4 foto → 14 çatlak, 40 bina | 5 |
| Gaziantep / İslahiye | 12 | 5 | 5 | 4 foto → 12 çatlak, 41 bina | 5 |
| Gaziantep / Nurdağı | 26 | 5 | 5 | 4 foto → 15 çatlak, 41 bina | 5 |

**Fotoğraf seçimi alana bağlıdır.** Önce yalnız tohuma bağlıydı ve üç alanın
şeklinde de aynı dört fotoğraf çıkıyordu. Artık alan adı kararlı bir sayıya
(`zlib.crc32`) çevrilip tohuma karışır — aynı alan + aynı tohum yine aynı
sonucu verir, farklı alanlar farklı fotoğraf alır. (`hash` kullanılamaz:
Python'da süreç başına tuzlanır.)

**Şekle yazılan uyarı:** katalogdaki fotoğrafların dokuzu **Hatay/Antakya**'dan,
dördünün ili kaynakta belirtilmemiş ("in Turkiye"; 27 Eylül düzeltmesi — önceki
"Hatay ve Adıyaman" ifadesinin dayanağı yoktu). Çekim tarihleri Şubat–Ağustos 2023. Gaziantep alanlarına yerleştirildiklerinde aynı depremin
gerçek fotoğraflarıdır ama **o mahallenin** fotoğrafı değildirler. Bu, hem
göstergenin künye satırında hem de kanal çıktısının `not` alanında yazılıdır.
Makale altyazısında da tekrarlanmalıdır.

## 18. Düzeltilmiş kodla yeniden koşu (28 Eylül 2026)

**Neden.** 27 Eylül taramasında tatbikat kodunda üç kusur bulundu ve düzeltildi
(EKSIKLER J-112 manevra iki kez sayılıyordu, J-113 `oneway=-1` ileri yön
sayılıyordu, J-114 A* sezgiseli sabit 80 km/sa). Makalenin bütün tatbikat
sayıları düzeltilmiş kodla yeniden üretildi. Kapanma cezası artık yalnız
değerlendirme süresi (1,0 dk); geri dönüş manevrası çizgede fiilen yapılan dönüş
olarak ödeniyor.

**Nerede, neyle.** İkinci makine (AMD Ryzen 5 5500, 6 çekirdek; Python 3.12.10,
PyTorch 2.11.0 CPU). Tek komut: `backend/araclar_b0_kos.sh` (17 dk).
Çıktılar `backend/benchmark/reports/tatbikat_b0/` altında: `sonuc_*.json`,
`duy_*.json`, `tatbikat_ozet.json`, `guzergah_nurdagi_unet_t42.json`, `gunluk.txt`,
`pip_freeze.txt`.

- **Model ağırlıkları.** Kaggle `furkanemrence/quakemind-modeller`: `segformer_mitb0.pth`,
  `segformer_mitb2.pth` ve `unet_mitb4.pth`. SHA-256 değerleri künyelerle
  (`modeller/uydu/*_p2_t42.json`) birebir aynı.
- **Yol verisi.** `araclar_yerel_osm_kur.py` ile 30 Mayıs 2026'da indirilen
  Türkiye PBF'inden üretildi (1.230 sn):
  - Bu makine: 755.236 kenar, 717.341 düğüm, 201 tesis.
  - i7: 756.623 / 718.564 / 205; fark yaklaşık %0,2, PBF tarihinden.
  - Tatbikat alanlarında fark yok: hasar oranı, kapalı kenar, afetzede, küme
    ve kapsama değerleri eskisiyle aynı. Nurdağı mahalle çizgesi de aynı
    (296 düğüm / 715 kenar).
  - Bölge dosyasında 43.821 tek yönlü kenar var; `oneway=-1` etiketli kenar
    yok. Bu yüzden J-113'ün bu veride etkisi yok.
  - `pyrosm` 0.13.1 kuruldu. Bağımlılığı `cykhash` Windows'ta derlenemediği için
    conda-forge'un derlenmiş paketi (`cykhash-2.0.1-py312hbb81ca0_3`, SHA-256
    doğrulandı) venv'e elle kondu.
- **Gecikmeler i7'de kalıyor.** Tablo 14 ve 16'daki süreler i7 ölçümüdür.
  Tatbikat sayıları ise benzetim süresidir, donanımdan bağımsızdır.

### 18.1 Ana sonuç (Tablo 15; üç model × üç alan × beş tohum)

| Alan | Model | Hasar | Kapalı k. | Afetzede | Bilmeyen | Telsizle paylaşan | QuakeMind | Kazanç | Keşif (bilmeyen) | Keşif (telsiz) | Ortak görev | Ceza payı | Kapsama | Küme |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Defne / Elektrik Mah. | segformer_mitb0_p2_t42 | %0,67 | 4 | 1 | — | — | — | araç rotası yok | — | — | — | — | %19 | 1/5 |
| İslahiye | segformer_mitb0_p2_t42 | %0,93 | 10 | 4 | 1,40 ± 0,00 | 1,40 ± 0,00 | 1,28 ± 0,00 | %8,7 ± 0,0 | 1,0 ± 0,0 | 1,0 ± 0,0 | 12,0 ± 0,0 | %68 ± 0 | %46 | 1/5 |
| Nurdağı | segformer_mitb0_p2_t42 | %3,80 | 22 | 5 | 2,93 ± 0,48 | 2,53 ± 0,26 | 1,33 ± 0,09 | %53,9 ± 5,3 | 29,4 ± 8,8 | 21,2 ± 4,0 | 25,0 ± 0,0 | %73 ± 4 | %44 | 5/5 |
| Defne / Elektrik Mah. | segformer_mitb2_p2_t42 | %1,26 | 10 | 5 | 2,03 ± 0,00 | 1,79 ± 0,00 | 1,47 ± 0,00 | %27,5 ± 0,0 | 8,0 ± 0,0 | 5,0 ± 0,0 | 20,0 ± 0,0 | %71 ± 0 | %19 | 1/5 |
| İslahiye | segformer_mitb2_p2_t42 | %2,06 | 16 | 5 | 1,94 ± 0,11 | 1,89 ± 0,09 | 1,28 ± 0,02 | %33,7 ± 3,4 | 9,8 ± 3,5 | 9,2 ± 3,3 | 21,0 ± 4,2 | %69 ± 3 | %46 | 5/5 |
| Nurdağı | segformer_mitb2_p2_t42 | %5,60 | 40 | 5 | 3,06 ± 0,52 | 2,70 ± 0,43 | 1,21 ± 0,07 | %59,6 ± 5,5 | 34,2 ± 7,5 | 27,4 ± 6,5 | 25,0 ± 0,0 | %74 ± 3 | %44 | 5/5 |
| Defne / Elektrik Mah. | unet_mitb4_p2_t42 | %1,49 | 12 | 3 | 2,35 ± 0,00 | 2,35 ± 0,00 | 1,92 ± 0,00 | %18,3 ± 0,0 | 2,0 ± 0,0 | 2,0 ± 0,0 | 6,0 ± 0,0 | %78 ± 0 | %19 | 1/5 |
| İslahiye | unet_mitb4_p2_t42 | %1,34 | 12 | 5 | 1,26 ± 0,09 | 1,26 ± 0,09 | 1,15 ± 0,06 | %8,3 ± 2,6 | 1,8 ± 0,8 | 1,8 ± 0,8 | 22,0 ± 2,7 | %75 ± 2 | %46 | 5/5 |
| Nurdağı | unet_mitb4_p2_t42 | %3,55 | 26 | 5 | 3,82 ± 0,67 | 3,24 ± 0,59 | 1,51 ± 0,14 | %60,0 ± 3,2 | 43,8 ± 10,0 | 32,0 ± 7,7 | 25,0 ± 0,0 | %76 ± 2 | %44 | 5/5 |

r_h duyarliligi (Tablo 18; ilk tohum):
| Alan | Model | r_h (m) | Kapalı kenar | Ortak görev | Bilmeyen (dk) | QuakeMind (dk) | Görünür kazanç | Keşif (bilmeyen) |
|---|---|---|---|---|---|---|---|---|
| Defne / Elektrik Mah. | unet_mitb4_p2_t42 | 0 | 12 | 6 | 2,35 | 1,92 | %18 | 2 |
| Defne / Elektrik Mah. | unet_mitb4_p2_t42 | 10 | 32 | 3 | 2,28 | 1,82 | %20 | 1 |
| Defne / Elektrik Mah. | unet_mitb4_p2_t42 | 15 | 34 | 3 | 2,28 | 1,82 | %20 | 1 |
| Defne / Elektrik Mah. | unet_mitb4_p2_t42 | 25 | 40 | 0 | — | — | — | 0 |
| İslahiye | unet_mitb4_p2_t42 | 0 | 12 | 20 | 1,16 | 1,09 | %6 | 1 |
| İslahiye | unet_mitb4_p2_t42 | 10 | 62 | 5 | 2,95 | 1,30 | %56 | 5 |
| İslahiye | unet_mitb4_p2_t42 | 15 | 75 | 5 | 2,86 | 1,30 | %55 | 5 |
| İslahiye | unet_mitb4_p2_t42 | 25 | 86 | 0 | — | — | — | 0 |
| Nurdağı | unet_mitb4_p2_t42 | 0 | 26 | 25 | 3,70 | 1,53 | %59 | 40 |
| Nurdağı | unet_mitb4_p2_t42 | 10 | 114 | 6 | 8,53 | 1,77 | %79 | 29 |
| Nurdağı | unet_mitb4_p2_t42 | 15 | 140 | 6 | 6,05 | 1,77 | %71 | 18 |
| Nurdağı | unet_mitb4_p2_t42 | 25 | 164 | 5 | 5,64 | 1,74 | %69 | 14 |

**Eskisiyle karşılaştırma:**

| Ölçüt | Eski kod | Düzeltilmiş kod |
|---|---|---|
| Kazanç bandı | %7–66 | %8–60 |
| Nurdağı bandı | %59–66 | %54–60 |
| Defne | %41 | %18–28 |
| İslahiye (dengeli / en iyi) | %40,9 / %9,9 | %33,7 / %8,3 |

- **Ceza payı artık ölçülüyor.** Tanımı: kapanmayı bilmeyen ekibin toplam
  değerlendirme süresinin, iki kol arasındaki toplam farka oranı. Değeri
  %68–78, Nurdağı'nda %73–76. Eski "kaba kestirim" %83'tü.
- **Keşif sütunu (J-117).** Eski Tablo 15'teki "Keşif" sütunu kapanmayı bilmeyen
  ekibe aitmiş: eski ve yeni sayılar birbirine yakın (Nurdağı 29,4 / 33,8 /
  44,4 → 29,4 / 34,2 / 43,8). Telsizle paylaşan filonun keşfi daha az
  (21,2 / 27,4 / 32,0).

### 18.2 Duyarlılık (Tablo 19; U-Net MiT-B4, tohum 42)

Hücreler: kapanmayı bilmeyen ekip → QuakeMind (dk) ve kazanç.

| Koşu | Defne | İslahiye | Nurdağı |
|---|---|---|---|
| ANA (değerlendirme 1,0 dk, dönüşlü) | 2,35 → 1,92 (%18) | 1,16 → 1,09 (%6) | 3,70 → 1,53 (%59) |
| Dönüşsüz (ceza 1,42 dk) | 2,04 → 1,55 (%24) | 1,04 → 0,94 (%9) | 3,30 → 1,20 (%64) |
| Değerlendirme 0,5 dk | 2,18 → 1,92 (%12) | 1,13 → 1,09 (%4) | 2,90 → 1,53 (%47) |
| Değerlendirme 2,0 dk | 2,68 → 1,92 (%28) | 1,21 → 1,09 (%10) | 5,30 → 1,53 (%71) |
| Eski sabit 20 dk | 8,68 → 1,92 (%78) | 2,11 → 1,09 (%48) | 34,10 → 1,53 (%96) |

Önceki duyarlılık koşusu `segformer_mitb4_dice30` ile yapılmıştı; bu kez U-Net
kullanıldı, yani ANA satırı Tablo 15'in tohum 42 değeridir.

### 18.3 Güzergâh varyantları (Tablo 17; Nurdağı, U-Net, tohum 42)

- Artık koşucunun `--guzergah` seçeneğiyle üretiliyor. Eskiden simülasyon
  ucunun yanıtından elle okunuyordu.
- Ekip 1, 2, 3 ve 5'in uzunlukları eskisiyle aynı. Eski kayıtta eksik olan
  Ekip 4 eklendi: 542 → 704 → 724 m.
- Ortalama uzama 25 çiftin tamamından hesaplandı: 95,0 m (%32,5), süre
  cinsinden 0,43 dk (%61,4); en büyük uzama 1,8 dk. Eski değer 101,7 m
  (%32,8) idi.

### 18.4 Şekiller

- Şekil 5 (`sekil_tatbikat_nurdagi.png`): künye artık sarmalanıyor.
- Şekil 10 (`sekil_uc_kanal_nurdagi.png`): düzeltilmiş metin sınıflandırıcısıyla
  yeniden üretildi.
- Şekil 11 ve 12 (`sekil_kiyas_kollari`, `sekil_duyarlilik`, `sekil_kesif_kazanc`):
  `araclar_makale_sekilleri.py` artık sayıları elle yazılmış sabitlerden değil,
  doğrudan `tatbikat_b0` JSON'larından okuyor.

## 19. Eksiklerin kapatılması (28 Eylül 2026)

### 19.1 Kalan sekiz alan, düzeltilmiş kodla (üç model × beş tohum)

Çıktılar `tatbikat_b0/sekiz_alan_*.json`, günlük `sekiz_alan_gunluk.txt`. Eski cümle ("kalan
sekizinde kollar ayrışmadı") düzeltilmiş kodla **doğrulanmadı**:

| Alan | Ayrışma |
|---|---|
| Narlıca (ortaokul), Narlıca, Mansurlu, Şekeroba kuzeybatı, Gökçedere | Hiçbir modelde yok. Model ya kapanma bulmadı ya da bulduğu kapanmalar rotalara düşmedi; bazı model–alan eşlerinde hasar blobu da yok. |
| Kahramanmaraş Şubat Stadyumu çevresi | Yalnız MiT-B2: %40,4 ± 7,6 (5/5 küme) |
| Kahramanmaraş Şekeroba orta | Yalnız MiT-B2: %13,7 ± 12,5 (5/5 küme) |
| Hatay Türünçlü | Yalnız U-Net: tek ortak görevde %32,5 |

Makaleye giren üç alan, kolların **en az iki modelde** ayrıştığı alanlar. Tek modelde ayrışan
üç alanın kazancı raporlanan bandın (%8–60) içinde kalıyor.

### 19.2 A* bağımsız çapraz doğrulama

Aracı `araclar_astar_capraz.py`, çıktısı `tatbikat_b0/astar_capraz.json`. Üç alan × beş tohum
× bütün çiftler, kapanmasız ve kapanmalı görünüm: 248 ayrı sorgu. Karşılaştırılan iki yöntem:
A* (`donus.en_kisa_yol`) ve açıkça kurulan kenar grafiği üzerinde `networkx` Dijkstra.

- Ulaşılabilir 240 sorguda aynı süre; en büyük fark 5,7·10⁻¹⁴ sn.
- 8 sorguda iki yöntem de yol bulamadı.
- Uyumsuz sorgu yok.
- Mahalle çizgelerinde en yüksek kenar hızı 45–70 km/sa. Eski sabit 80 km/sa sezgiseli bu
  alanlarda da kabul edilebilir kalıyordu; J-114'ün etkisi sıfır.
