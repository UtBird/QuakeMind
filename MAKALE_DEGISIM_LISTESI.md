# Makalede değişecek yerler — bölüm bölüm

_27 Eylül 2026. **Bu belge makaleye dokunmaz**, yalnız neyin nereye gideceğini
söyler. Bütün yeni sayılar `SIMULASYON_OLCUM_KAYDI.md`den gelir ve orada
ölçümüyle birlikte durur._

Etkilenen bölüm sayısı **30**. Kaynak sayımı: EMSR/Copernicus 159 geçiş,
R0–R3 148, "8 bölge / 48 çift" 157, t_u / 20 dk 79, sentetik 41,
"10 tohum" 34, HAZUS 7.

---

## A. ÖZ ve ABSTRACT — manşet iddialarının tamamı değişiyor

| Taslakta yazan | Sorun | Ne olacak |
|---|---|---|
| "Hatay ve Kahramanmaraş'ta **sekiz bölgede**, bölge başına 6 afetzede-ekip çifti (**toplam 48**), **on rastgelelik tohumu**" | Sekiz bölge sentetik üreteçten; artık yok | "Hatay ve Gaziantep'te **üç gerçek mahallede**, mahalle başına **25 ekip–afetzede çifti**, **beş tohum**, **üç model**" |
| "Kapanmalar iki kaynaktan: sekiz ilçede **sentetik bir üreticiden** ve **Copernicus EMS EMSR648**…" | İkisi de bırakıldı | "Kapanmalar tek kaynaktan: **açık drone ortofotosu üzerinde koşan kendi hasar modelimizin** çıktısının OSM yol ağıyla piksel kesişimi" |
| "…müdahale süresini **184,9 ± 200,2 dk'dan 12,8 ± 8,3 dk'ya** indirmiştir; ancak **farkın %97,4'ü** 20 dakikalık yeniden yönlenme cezasından" | Sonucu tek başına uydurma bir sabit üretiyordu | "Kapanmaları önceden bilmek erişim süresini **%13–66** kısaltmıştır (alan ve modele göre); en sağlam alanda (Nurdağı, üç model × beş tohum) **%59–66**. Ceza sabiti **20 dk'dan 1,42 dk'ya** indirilmiş ve ayrıştırılmıştır" |
| "Görüş mesafeli ve bilgi paylaşan referanslara karşı… (%2,3 ve %5,1)" | R0–R3 adlandırması kalkıyor | Telsizle paylaşan filo kolu: Nurdağı 4,58 → **3,80 dk**; kazancın bir bölümünü yakalıyor |
| "Gerçek hasarla (EMSR648) Kahramanmaraş'ta… **44,4 dakika**" | EMSR kullanılmıyor | **Cümle tamamen kalkar.** Yerine sınırlılık: kapanma katmanı için yer gerçeği doğrulaması yapılmamıştır |
| "…**15 ayarın hiçbiri** kapanma bilgisi olmayan ajandan daha kısa ulaşım süresi sağlamamıştır" | EMSR karşılaştırmasına dayanıyordu | **Kalkar.** Yerine: bölütleme başarımı ile operasyonel fayda doğru orantılı değil |
| "her tohumda **48 atamanın 48'i** tamamlanmış" | Atama algoritması tatbikatta yok | **Kalkar** ya da tatbikata atama eklenene kadar "gelecek çalışma" |

**ABSTRACT** aynı cümlelerin İngilizcesi; birebir aynı değişiklikler.

---

## B. Bölüm bölüm

### 3.2 Çalışma Alanı ve Veri Kaynakları
- Copernicus EMS / EMSR648 veri kaynağı olarak **çıkar**.
- **Tablo 4** (Copernicus EMS derecesi → EMS-98 / HAZUS → geçilebilirlik kuralı) **tamamen çıkar**: üç geçilebilirlik kuralı da EMSR derecelerine bağlıydı.
- Yerine: üç gerçek drone alanının künyesi (§8.1) — sahne adı, sağlayıcı, çekim tarihi, uçuş izi doluluğu, pencere boyu, OSM yol oranı.
- Eklenecek: yol verisi artık **yerel OSM bölge dosyasından** (756.623 kenar, tek geçiş); Overpass'a bağımlılık yok.

### 3.2.1 Etiketli Yol Hasarı Eğitim Kümesi
- **Doğru, kalıyor:** eğitim KATE-CD + KATE-PD (Protokol P2). Değişiklik gerekmez.

### 3.5 Yer Seviyesi Hasar Tespiti
- **Tablo 8** bina hasar sınıflarını EMS-98 ve HAZUS ile eşliyor. HAZUS kullanılmıyorsa bu eşleme de kalkmalı ya da yalnız EMS-98 bırakılmalı. **Karar gerekiyor** — bu, kapanma zincirinden bağımsız bir bölüm.

### 3.8 Kapanma-Farkında Güzergâh Planlaması
- **R0/R1/R2/R3 adlandırması kalkar.** Yerine: "Kapanmayı bilmeyen ekip", "Telsizle paylaşan filo", "QuakeMind" (isteğe bağlı dördüncü: "Görüş mesafeli ekip").
- t_u = 20 dk **kalkar**; yerine ayrışık ve beyan edilmiş **değerlendirme 1,0 dk + manevra 25 sn = 1,42 dk**.
- **EKLENECEK — yeni alt bölüm: sağdan trafik.** Arama kenar tabanlıdır (satır grafiği); düğüm tabanlı Dijkstra/A* kavşağa nasıl girildiğini bilmez ve sola dönüşü sağa dönüşle aynı fiyata alır. Dönüş maliyetleri: düz 0, sağ 3, sol 10, U 25 sn. Tek yön uygulanır (bölgede 3.083 tek yönlü kenar). Hızlar maxspeed/yol sınıfından (20–70 km/sa), düz varsayım değil.

### 3.8.1 Senaryo Koşumlarında Kullanılan Sentetik Kapanma Kümesi
- **Bölüm tamamen çıkar.** Kapanmalar artık gerçek görüntüden, kendi modelimizle türetiliyor.
- Yerine: "Dünyanın ölçeği" (§2) — neden mahalle ölçeği: ekipler gerçek tesislerde iken model rota ağının **%0,64'ünü** görüyordu ve üç kol birebir aynı çıkıyordu.

### 3.9 Görev Orkestrasyonu ve Çakışma Önleme
- Tatbikat eşlemeyi **tur döndürerek** yapıyor; Algoritma 3 (atama) tatbikata bağlı değil. Ya bölüm "gelecek çalışma"ya taşınır ya da atama tatbikata eklenir. **Karar gerekiyor.**

### 3.10 Değerlendirme Ölçütleri ve Protokolü
- EMSR referanslı ölçütler çıkar. Yeni protokol: 3 alan × 3 model × 5 tohum, mahalle başına 5 giriş ağzı × 5 afetzede, 5 turda döndürülerek 25 çift; ortalamalar yalnız bütün kolların ulaştığı ortak görevlerden.
- Eklenecek: **kapsama oranı** — modelin fiilen değerlendirebildiği kenar oranı (%19–46). Görmediği kenar "açık" sayılır ama ölçülmemiştir.

### 4.1.1 Donanım ve Yazılım Ortamı
- Güncellenecek: 20 çekirdekli CPU, **GPU yok**, PyTorch 2.10 CPU, 6 iş parçacığı. Tatbikat toplam **15,0 sn** (soğuk 35 sn).

### 4.3 Kapanma Katmanının Yer Gerçeğine Göre Değerlendirilmesi
- **Bölüm tamamen çıkar** (EMSR'a dayanıyordu; karar: EMSR kullanılmayacak).
- **Yerine hiçbir şey konmuyor.** §5.3'e sınırlılık girer: kapanma katmanı için yer gerçeği doğrulaması yapılmamıştır; tatbikatta dünya modelin kendi çıktısıdır, bu yüzden ölçülen şey kapanmayı önceden bilmenin kazandırdığı süredir, kapanmaların doğruluğu değildir.

### 4.5 Uçtan Uca Senaryo Değerlendirmesi
- Sekiz bölge / 48 çift / 10 tohum → **üç mahalle / 25 çift / 5 tohum / 3 model**.
- **Tablo 16–17** (YOLOv8 ve BERTurk gecikmeleri) — tatbikat tek kanallı olduğu için bu senaryo içinde yer alamaz. Ya kanallar eklenir ya da senaryo "uydu → sevk zinciri" olarak daraltılır. **Karar gerekiyor.**
- Toplanma alanı yönlendirmesi tatbikatta yok; çıkar ya da ayrı sunulur.

### 4.6 Karşılaştırma Referanslarıyla Değerlendirme
- **Tablo 18** (R0–R3 × sentetik/EMSR) **tamamen değişir.** Yerine §8.2 tablosu: 3 alan × 3 model, üç kol, ortalama ± standart sapma, keşif sayısı ve kaç tohumun farklı kurulum verdiği.
- **Şekil:** `sekil_kiyas_kollari.png`

### 4.7 Görev Tabanlı Değerlendirme
- 480 atama iddiası kalkar (atama algoritması tatbikata bağlı değil).

### 4.8 Geçilebilirlik Kuralının Duyarlılığı
- EMSR'ın üç geçilebilirlik kuralı (katı/orta/gevşek) kalkar.
- **KOŞULDU, hazır:** yerine **r_h duyarlılığı** gelir (§10). Üç alan × dört yarıçap.
  Bulgu makaleye değer: r_h büyüdükçe "kazanç" yükseliyor (%41→%56, %9→%59, %64→%81)
  ama bu iyileşme değil — **ortak görev sayısı çöküyor** (6→3, 20→5, 25→7) ve iki
  alanda r_h = 25'te sıfıra düşüyor. Yüzde, daralan ve yanlı bir örneklemden geliyor.
  Varsayılan **r_h = 0** değiştirilmedi; makaledeki bütün sayılar bu değerle üretildi.

### 4.9 Bileşen Çıkarma ve Parametre Duyarlılığı
- Yerine §9: ceza süresi 0,5–2,0 dk, dönüş maliyeti açık/kapalı, ve eski 20 dk sabitinin ne yaptığı.
- **Şekil:** `sekil_duyarlilik.png` (eski sabitin sütunu taralı ve "kullanılmıyor" etiketli)

### YENİ ALT BÖLÜM — model seçimi
- 5,5 kat çıkarım süresi (1,91 → 10,50 sn) yalnız **+0,051 IoU** veriyor ve operasyonel kazancı tek yönlü artırmıyor: orta boy model İslahiye'de %40,9, en büyük model %9,9. Saniye başına operasyonel değer en yüksek olan orta boy modeldir.
- **Şekil:** `sekil_model_secimi.png`, `sekil_sure_dagilimi.png`

### 5.1 · 5.3 · 5.4 · 6. SONUÇ
- EMSR, sentetik ve R0–R3'e yaslanan bütün cümleler yeniden yazılır.
- **5.3'e girecek yeni sınırlılıklar:** (a) kapanma katmanı için yer gerçeği doğrulaması yok; (b) kapsama %19–46, modelin görmediği kenar "açık" sayılıyor; (c) tatbikat tek kanallı; (d) üç alan 11 ölçülen alandan **seçildi** — kalan 8'inde kollar ayrışmadı, bu cümle olmadan üç alan raporlamak kiraz toplamaktır; (e) Defne'de blob azlığından beş tohum tek kurulum veriyor, oradaki sıfır yayılım sağlamlık değil tek örneklemdir; (f) Nurdağı sahnesine sağlayıcının kendi "Low Quality" uyarısı var.

### KISALTMALAR · KAYNAKLAR · VERİ ERİŞİLEBİLİRLİĞİ
- EMSR, Copernicus EMS, HAZUS kısaltmaları ve kaynakçadaki FEMA HAZUS ile Copernicus atıfları kullanılmıyorsa **çıkar**.
- Veri erişilebilirliği: yeni tatbikat verisi ve şekiller eklenir; yerel OSM bölge dosyası depoya girmiyor, komutla üretiliyor.

---

## C. Hazır olanlar — hiçbir şey yapılmadan kullanılabilir

| Ne | Nerede |
|---|---|
| Yöntem metni (zincir, dünyanın ölçeği, kıyas kolları, sağdan trafik, ceza) | §1–7 |
| Alan künyeleri tablosu | §8.1 |
| Ana sonuç tablosu (3 alan × 3 model × 5 tohum) | §8.2 |
| Duyarlılık tablosu | §9 |
| Uçtan uca doğrulama | §10 |
| Başarım tablosu ve model seçimi | §13 |
| On şekil + önerilen alt yazılar | §14, `benchmark/makale_sekilleri/` |
| Yeniden üretme komutları | §15 |

## D. Karar bekleyenler

1. **Tablo 8** (bina sınıfları ↔ EMS-98/HAZUS) kalsın mı? HAZUS gidiyorsa eşleme de gitmeli.
2. **3.9 / 4.7 görev ataması** — tatbikata eklensin mi, yoksa "gelecek çalışma" mı?
3. ~~**4.5 çok kanallı senaryo** — YOLOv8/BERTurk tatbikata eklensin mi?~~ — **eklendi, kısmen kapandı (27 Eylül, J-108).** Tatbikat artık üç kanal koşturuyor: uydu (SegFormer/U-Net), kamera (`catlak.pt` + `bina.pt`) ve metin (BERTurk). Ölçümler `SIMULASYON_OLCUM_KAYDI.md` §17'de.
   **Kalan karar makalede nasıl yazılacağı:** bu ölçümler *tespit sayısı* ve *örtüşme*dir, **mAP ve F1 değildir** — fotoğraflarda kutu düzeyinde yer gerçeği, metinlerde bağımsız etiket yok. İki seçenek: (a) §4.5 bu hâliyle "uçtan uca çalıştığının gösterimi" olarak yazılır, başarım iddiası kurulmaz; (b) mAP/F1 için etiketli küme (DepremKit / TSEqD) ile ayrı bir ölçüm yapılır. Önerim (a) + metin kanalı için (b): özgünlük iddiasının yarısı Türkçe ihtiyaç çıkarımında, orada ölçülmüş bir sayı gerekiyor.
4. ~~4.8 r_h duyarlılığı~~ — **koşuldu, kapandı** (§10).

## E. Şekil altyazılarında düzeltilmesi gereken iki şey

27 Eylül 2026'da `QuakeMindBackend/capture_app_screenshots.py` incelenirken bulundu.
Kod hatası değil, makale altyazısı eksiği — ama kural 1 gereği zorunlu.

1. **Şekil 4 (`4_isi_haritasi_guzergah.png`) demo modunda çekilmiş.** Betik
   sayfayı açıp **"Örnek Verilerle Simüle Et"** düğmesine basıyor
   (`capture_app_screenshots.py:94`), yani görseldeki ısı haritası ve yol ağı
   **sentetik veriyle** üretilmiş. Betiğin kendi açıklaması da bunu
   "arayüzü tanıtan bir ekran görüntüsü" diye niteliyor. Altyazıda bunun
   **simüle veri** olduğu açıkça yazmalı; şu hâliyle okuyucu gerçek analiz
   çıktısı sanır. Görselin kendisinde "Simülasyon Modu Aktif" etiketi kalıyor
   (`hide_map_badges` yalnız Leaflet atıf kutusunu gizliyor), ama altyazı bunu
   tekrarlamazsa yetmez.

2. **Harita atıf kutusu görsellerden silinmiş.** `HIDE_ATTRIBUTION` ile
   `.leaflet-control-attribution` gizleniyor; betikteki yorum "atıf, makale
   metninde/altyazıda verildiği için görselden kaldırılması tercih ediliyor"
   diyor. O hâlde altyazı **gerçekten** atfı taşımalı (hangi altlık: Esri
   Wayback / Google / OAM ve yakalama tarihi). Taşımıyorsa atıf hiç verilmemiş
   olur.

Kontrol edilecek diğer arayüz şekilleri: Şekil 21 (kamera, gerçek YOLO
çıkarımı — `QM_CRACK_PHOTO` ile), Şekil 22 (risk, gerçek model), Şekil 23
(metin analizi). Bunlar gerçek çıkarımla üretiliyor; yalnız Şekil 4 demo
verisiyle.

## F. Üç kanal şekli — §4.5 için önerilen görsel

`benchmark/makale_sekilleri/sekil_uc_kanal_{defne,islahiye,nurdagi}.png`
(27 Eylül 2026). **KARAR: `sekil_uc_kanal_nurdagi.png` kullanılacak**
(Furkan, 27 Eylül). Gerekçe: 26 kapalı kenarla en okunaklı kare ve kazanımın
en yüksek olduğu alan (%59–66). Diğer iki şekil dosyada duruyor; istenirse ek
görsel olarak kullanılabilir ama makaleye giren bu.

**Önerilen altyazı:**

> **Şekil X.** Üç veri kanalının tek mahalle karesinde birleşmesi ve zincirin
> sonu. Zemin: (alan) için (sağlayıcı), (tarih) görüntüsü. Kırmızı alanlar
> uydu bölütlemesinin hasarlı bulduğu pikseller; sarı kareler kamera
> kanalının, mor daireler metin kanalının kayıtları. Koyu kırmızı kalın
> çizgiler hasarın yola taştığı ve kapalı sayılan kenarlar, mavi çizgiler bu
> kapanmalara göre hesaplanan ekip güzergâhı. Sağ alttaki iç görüntü, sarı
> noktalardan birinin gerçek fotoğrafı ve modelin üzerinde bulduğu kutulardır.
> Görüntü, fotoğraflar ve bütün model çıktıları gerçektir; ihbar metinleri ile
> kamera ve metin kayıtlarının harita konumları üretilmiştir. Fotoğraflar aynı
> depremlerin ardından çekilmiş gerçek kareleridir (dokuzu Hatay/Antakya'da,
> dördünün ili kaynakta belirtilmemiş), gösterilen
> mahallenin fotoğrafı değildir.

**Neden bu şekil gerekli:** §1'de "yazında hasar algılama, yol erişilebilirliği
ve ihtiyaç çıkarımı ayrı ayrı çözülmüş, tek karar zincirinde birleştirilmemiştir"
deniyor. Katkı iddiası bu. Şekil onun tek karelik kanıtı — okuyucu üç kanalın
aynı mahalleye indiğini ve sonucun güzergâha döndüğünü bir bakışta görür.

## G. Şekil dengesi — yeni şekil değil, sıralama önerisi

29 Eylül 2026'da yapılan bakışta çıktı. **Yeni şekil üretilmesi gerekmiyor**; öneri
yalnızca vurguyla ilgili ve yazar okumasında (KALAN_ISLER B) değerlendirilmeli.

### Gözlem

23 şeklin dağılımı:

| Ne gösteriyor | Şekil | Sayı |
|---|---|---|
| **Zincir — çalışmanın özgünlük iddiası** | 5, 9, 10, 11, 12 | **5** |
| Bileşen kıyası (bölütleme 7–8, metin 13–15, risk 16–20) | 7, 8, 13, 14, 15, 16, 17, 18, 19, 20 | **10** |
| Yöntem ve bağlam | 1, 2, 3, 4, 6 | 5 |
| Arayüz | 21, 22, 23 | 3 |

Bileşen kıyasına zincirin **iki katı** yer ayrılmış. Oysa §2 ve §5'te açıkça yazıldığı
gibi katkı, bileşenlerin tek tek başarımında değil, üçünün tek karar zincirinde
birleştirilmesindedir; bileşen düzeyinde emsaller çoğu ölçütte önde. Şekil bütçesi
bu yüzden iddianın zayıf olduğu tarafa ağırlık veriyor.

### Zincir şekilleri güçlü, sorun onlarda değil

- **Şekil 10** (üç kanal tek haritada) tek karede uydu + kamera + metin kanallarını,
  kapanan yolları ve güzergâhı gösteriyor; altyazısı neyin gerçek neyin üretilmiş
  olduğunu da yazıyor. Katkı iddiasının tek karelik kanıtı budur.
- **Şekil 11** (kolların erişim süresi) Nurdağı'da 3,82 → 1,51 dk farkını hata
  çubuklarıyla veriyor ve **zayıf durumu saklamıyor**: İslahiye'de 1,26 → 1,15.
  Ayrıca Defne ve İslahiye'de "kapanmayı bilmeyen" ile "telsizle paylaşan" kolların
  **birebir aynı** çıktığı (2,35 = 2,35 · 1,26 = 1,26), yani telsizle paylaşmanın o iki
  alanda katkısının sıfır olduğu grafikten okunuyor. Olumsuz sonuç görünür durumda.

### Öneri (karar yazarlarda)

1. **Sıralama.** Hakem çoğu zaman önce şekillere bakar; şu an ilk gördüğü şey on tane
   model kıyası grafiği. Şekil 10 ve 11'in metin içindeki konumu öne alınabilir ya da
   §4.5–4.6'ya yapılan atıflar erken bölümlerden (ÖZ sonrası, §1 sonu) güçlendirilebilir.
2. **Anlatı bağı.** §5.1'deki *"sınama IoU'su operasyonel faydanın iyi bir göstergesi
   değildir"* cümlesini şekille destekleyen tek görsel **Şekil 12**. Bu karşıtlık
   makalenin en aktarılabilir bulgusu; okuma turunda Şekil 12'ye yapılan atıfların
   yeterli olup olmadığına bakılmalı.

**Yapılmaması gereken:** bu gözlem yüzünden bileşen şekillerini çıkarmak. Onlar
ölçülmüş sonuçlar ve hakem kıyas ister; mesele hangisinin önce görüldüğü.
