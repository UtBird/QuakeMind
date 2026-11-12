# Vurgulu (revize edilmiş) cümleler — 29 Eylül 2026

Sarı vurgular makale dosyasından KALDIRILDI (kullanıcı isteği). Hangi cümlelerin
revizyonlarda değiştiği kaybolmasın diye buraya çıkarıldı; yazar okumasında
(`KALAN_ISLER` B) iç tutarlılık denetimi bu liste üzerinden yapılabilir.

Toplam 180 parça.

1. **paragraf 2** — Furkan Emre İnce1, Utku Ceylan1, Esra Uray2

2. **paragraf 3** — 1 KTO Karatay Üniversitesi, Bilgisayar Mühendisliği Bölümü, Konya, Türkiye

3. **paragraf 4** — 2 KTO Karatay Üniversitesi, İnşaat Mühendisliği Bölümü, Konya, Türkiye

4. **paragraf 5** — [ORCID NUMARALARI VE SORUMLU YAZAR BİLGİSİ EKLENECEK — çift kör hakemlik uygulayan dergide bu blok ayrı başlık sayfasına taşınacaktır]

5. **paragraf 8** — 6 Şubat 2023 Kahramanmaraş depremlerinde yol ağı kapanmaları, arama-kurtarma ekiplerinin erişilebilirliğini belirleyen temel kısıtlardan biri olmuştur. Yazında hasar tespiti ile ekip sevki büyük ölçüde ayrı ele alınmakta; bölütleme başarımındaki bir değişimin operasyonel sonuca ne ölçüde yansıdığı nicel olarak gösterilmemektedir. Bu çalışmada, uydu ve drone görüntüsünden hasar bölütlemesi ve yol ağıyla piksel-düzeyi kesişim (SegFormer/U-Net, MiT kodlayıcı; odaksal ve Dice kayıplarının bileşimi), yer seviyesi hasar tespiti (YOLOv8), Türkçe ihbar metni çözümlemesi (BERTurk ve varlık ismi tanıma) ile kapanma-farkında güzergâh planlamasını (süre tabanlı ve dönüş maliyetli A*, sert kapatma) tek bir sevk zincirinde bütünleştirmek üzere tasarlanan QuakeMind platformu sunulmaktadır. Değerlendirme, Hatay ve Gaziantep'te üç gerçek mahallede (Defne/Elektrik, İslahiye, Nurdağı), mahalle başına en çok 25 ekip–afetzede çifti (beş giriş ağzı × en çok beş afetzede, beş turda döndürülerek), beş rastgelelik tohumu ve üç model üzerinde yürütülmüştür. Kapanmalar tek kaynaktan alınmıştır: açık drone ortofotosu üzerinde koşan kendi hasar modelimizin çıktısının OpenStreetMap yol ağıyla piksel düzeyinde kesişimi. Kapanmaları önceden bilmek, modelin bulduğu kapanmaların ekip rotalarına fiilen düştüğü alanlarda erişim süresini kısaltmıştır; ölçülen bant alan ve modele göre %8–60, en sağlam alanda (Nurdağı, üç model × beş tohum) %54–60'tır; kapanmanın rotaya düşmediği alanlarda fark yoktur. Kapanmaya varan ekibin kaybettiği süre, önceki sürümdeki 20 dakikalık sabit yerine 1,0 dakikalık değerlendirme süresine indirilmiş, geri dönüş manevrası yol çizgesinde fiilen yapılan dönüş olarak fiyatlanmıştır; buna karşın farkın %68–78'i hâlâ bu beyan edilmiş süreden gelmektedir, bu nedenle sonuç cezanın değerine duyarlılığıyla birlikte bant olarak raporlanmıştır. Tatbikatta yer gerçeği bir kapanma katmanı bulunmadığından, dünya modelin kendi çıktısıdır; bu nedenle ölçülen büyüklük kapanmayı önceden bilmenin kazandırdığı süredir, kapanmaların doğruluğu değildir. Kapanma katmanının doğruluğu bir mahallede bir insan etiketleyicinin kör etiketlemesiyle ayrıca sınanmış; kesinlik 4/5, duyarlılık ≈%9 ölçülmüştür (yüksek kesinlik, düşük duyarlılık). Çok mimarili karşılaştırma protokolü, yol hasarını piksel düzeyinde etiketleyen açık bir Türkiye kümesi bulunmadığından bina hasarı bölütlemesinde yürütülmüş; kodlayıcısı MiT-B4'te sabitlenmiş kıyaslama mimarileri arasında en yüksek hasar sınıfı kesişim/birleşim oranı (IoU) değeri tek tohumda U-Net ile elde edilmiştir (0,433); üç tohumla yinelendiğinde MiT-B4 mimarileri arasındaki fark tohum oynaması mertebesinde kalmıştır. Bir ilin eğitimden çıkarıldığı genelleme deneyinde görülmemiş ilde IoU_hasar üç tohumun ortalamasında 0,04–0,08 düşmüştür. Türkçe metin sınıflandırmada sekiz model çok etiketli alt kategori kümesinde karşılaştırılmış; BERTurk mikro-F₁'de öne çıkarken (0,8247) klasik bir TF-IDF taban çizgisi makro-F₁'de BERTurk'ü geçmiştir (0,5024 ve 0,4725). Çalışmanın katkısı, bölütleme kalitesini operasyonel sonuca bağlayan yeniden üretilebilir bir görev tabanlı değerlendirme protokolünün tanımlanıp uygulanması ve kapanmayı önceden bilmenin kazancının kapanmaların yol ağı topolojisindeki konumuna bağlı olduğunun, modeller arasındaki sınama IoU farklarının ise bu kazancı öngörmediğinin gösterilmesidir.

6. **paragraf 13** — During the 6 February 2023 Kahramanmaraş earthquakes, road network blockages were among the decisive constraints on the accessibility of search-and-rescue teams. In the literature, damage detection and team dispatch are largely treated in isolation, and the extent to which a change in segmentation performance propagates to the operational outcome is not quantified. This study presents QuakeMind, a platform designed to integrate damage segmentation from satellite and drone imagery intersected pixel-wise with the road network (SegFormer/U-Net with a MiT encoder; combined focal and Dice loss), ground-level damage detection (YOLOv8), Turkish report-text analysis (BERTurk and named entity recognition), and blockage-aware route planning (time-based, turn-aware A* with hard edge removal) into a single dispatch chain. The evaluation was conducted in three real neighborhoods in Hatay and Gaziantep (Defne/Elektrik, İslahiye, Nurdağı), with up to 25 affected-individual/team pairs per neighborhood (five entry mouths × up to five individuals, rotated over five turns), five random seeds, and three models. Blockages were taken from a single source: the pixel-wise intersection, with the OpenStreetMap road network, of our own damage model run on open drone orthophotos. Knowing the blockages in advance shortened access time in areas where the model's blockages actually fell on team routes; the measured band is 8–60% depending on area and model, and 54–60% in the most robust area (Nurdağı, three models × five seeds); where blockages did not fall on routes, there was no difference. The time lost by a team reaching a blockage was reduced from the previous 20-minute constant to a 1.0-minute assessment time, with the turn-back manoeuvre priced as the actual turn on the road graph; 68–78% of the difference nevertheless still comes from this declared time, so the result is reported as a band together with its sensitivity to the penalty value. Because the exercise has no ground-truth blockage layer — the world is the model's own output — the measured quantity is the value of foreknowledge, not the accuracy of the blockages. Blockage-layer accuracy was separately probed by blind human labeling in one neighborhood, yielding precision of 4/5 but low recall (≈9%). Because no open Turkish dataset annotates road damage at the pixel level, the multi-architecture comparison protocol was applied to building damage segmentation; among architectures with the encoder fixed to MiT-B4, the highest damage-class Intersection over Union (IoU) was obtained by U-Net with a single seed (0.433); with three seeds, differences among MiT-B4 architectures stayed within seed variation. When one province was held out of training, IoU on that unseen province dropped by 0.04–0.08 on average over three seeds. For Turkish text classification, eight models were compared on a multi-label subcategory set; BERTurk led on micro-F₁ (0.8247), while a classical TF-IDF baseline surpassed it on macro-F₁ (0.5024 versus 0.4725). The contribution is the definition and application of a reproducible task-based evaluation protocol linking segmentation quality to operational outcome, and the demonstration that the gain from foreknowledge of blockages depends on their position in the road network topology, while differences in test IoU between models do not predict this gain.

7. **paragraf 19** — depremdir [1, 2]. Olay adları AFAD'ı [1] izler; Kandilli aynı iki depremin dış merkezini Sofalaca–Şehitkamil (Gaziantep) ve Ekinözü (Kahramanmaraş) olarak vermektedir [2].

8. **paragraf 29** — Görev tabanlı değerlendirme protokolünün tanımlanması ve uygulanması. Üç gerçek mahallede, kapanmayı önceden bilen ve bilmeyen ekiplerin erişim süreleri karşılaştırılarak kapanma farkındalığının operasyonel değeri ölçülmüş; ölçülen kazancın kapanmaların ekip rotalarına düşüp düşmemesine bağlı olduğu, modeller arasındaki sınama IoU farklarının bu kazancı öngörmediği gösterilmiştir.

9. **paragraf 87** — Her sahnenin uçuş izi taranarak gerçekten dolu olan en iyi yaklaşık 500 m'lik pencere seçilmiş ve künyesiyle kaydedilmiştir; üç alanın künyesi (sahne, çekim tarihi, uçuş izi doluluğu, pencere boyu ve OSM yol oranı) Tablo 4'te verilmektedir.

10. **paragraf 142** — Tablo 21'deki

11. **paragraf 178** — Girdi : G(V,E) yönlü yol çizgesi (kenar uzunluğu w(e), kenar hızı v(e), dönüş süresi τ);

12. **paragraf 179** — B gerçek kapalı kenar kümesi (ekibe gizli); s başlangıç düğümü; g hedef düğüm;

13. **paragraf 180** — I_max = 60 en çok yol hesabı (ilk plan dahil)

14. **paragraf 181** — Çıktı : toplam süre T ve keşfedilen kapanma sayısı k; ya da ULAŞILAMAZ

15. **paragraf 182** — 1: K <- boş küme ; c <- s ; e_g <- yok ; T <- 0 ; k <- 0   // K: ekibin bildiği kapalı kenarlar

16. **paragraf 183** — 2: i = 1 .. I_max döngüsü

17. **paragraf 184** — 3:     P <- A*(G \ K, c, g, maliyet = w(e)/v(e) + τ, giriş kenarı = e_g)

18. **paragraf 185** — 4:     P boş ise ULAŞILAMAZ döndür

19. **paragraf 186** — 5:     engel <- yanlış

20. **paragraf 187** — 6:     P üzerindeki her ardışık kenar e = (u, v) için

21. **paragraf 188** — 7:         e ∈ B ise

22. **paragraf 189** — 8:             K <- K ∪ {e, ters(e)} ; k <- k + 1 ; c <- u   // kenara girilmez, kavşakta öğrenilir

23. **paragraf 190** — 9:             T <- T + c_kapanma ; engel <- doğru ; iç döngüden çık

24. **paragraf 191** — 10:        T <- T + w(e)/v(e) + τ(e_g, e) ; e_g <- e ; c <- v

25. **paragraf 192** — 11:    engel = yanlış ise T, k döndür                  // c = g: hedefe varıldı

26. **paragraf 193** — 12: ULAŞILAMAZ döndür                                   // I_max yol hesabı aşıldı

27. **paragraf 194** — c_kapanma = değerlendirme 1,0 dk. Geri dönüş manevrası sabit olarak eklenmez: satır 3'teki yeniden planlama, ekibin fiilen yaptığı dönüşü (çoğunlukla 25 sn'lik U dönüşü) çizgenin dönüş maliyetiyle fiyatlar. Taslağın önceki hâlinde 25 sn'lik manevra ayrıca sabite de ekleniyor, yani iki kez sayılıyordu (Bölüm 5.3(b)). Dönüş maliyeti kapatıldığında (duyarlılık koşusu, Bölüm 4.9) manevra sabit olarak eklenir: c_kapanma = 1,0 dk + 25 sn.

28. **paragraf 200** — Tatbikatın 'dünyası' görüntülenen mahalledir (+150 m marj). İlk kurguda ekipler gerçek tesislere (hastane, itfaiye; 1,3–3,8 km uzakta) konuşlandırılıyordu; o ölçekte model rota ağındaki kenarların yalnız %0,64'ünü görüyor ve üç kol birebir aynı sonucu veriyordu: 500 m'lik bir enkaz haritası 3 km'lik rotayı değiştiremez. Bu nedenle ekipler mahalleye giren gerçek yol ağızlarında (OSM düğümleri; ana yol sınıfı önce, ağızlar arası en az 120 m) konuşlandırılır. Ölçülen soru şudur: mahalleye giren ekip içerideki enkaza ne kadar sürede ulaşır ve moloz haritasını önceden bilmek bunu değiştirir mi? Aynı alanda kapsama %0,64'ten %15,2'ye çıkmıştır. Alan kutuları elle yazılmaz; her açık drone sahnesinin uçuş izi taranarak gerçekten dolu olan en iyi ~500 m'lik pencere seçilir ve künyesiyle kaydedilir (Tablo 4).

29. **paragraf 204** — Atama kuralı. Tasarımda atama her ilçe bölgesi için ayrı yapılır ve Algoritma 2'deki açgözlü, rol-farkında kuralı izler. Bölgedeki ihbarlar önce durum önceliğine (kritik, mahsur, yaralı, hafif), eşitlik hâlinde kanala göre (konum bilgili acil çağrı önce) sıralanır. Her ihbar için hedeflenen ekip rolü belirlenir: kritik ve mahsur durumlarda afetzede profilindeki rol (arama-kurtarma, medikal ya da lojistik) esas alınır; diğer durumlarda Türkçe metin sınıflandırıcısının çıkardığı üst kategori role eşlenir (Enkaz Bildirimi → arama-kurtarma, Acil Yardım İhtiyacı → medikal, Lojistik İhtiyaç Bildirimi → lojistik), kategori yoksa profil rolü kullanılır. Bu ayrımın gerekçesi, metin kategorisinin vakanın hayati aciliyetini değil ihtiyaç tipini anlatmasıdır: "bina yan yattı, içeride üç kişi var, hilti ve jeneratör lazım" ihbarına sınıflandırıcı ekipman ihtiyacını yansıtan "Elektrik Kaynağı" alt etiketini vermektedir (üst kategori Acil Yardım İhtiyacı, rol medikal), ancak oraya gitmesi gereken ekip arama-kurtarma ekibidir. Hedeflenen rolde boşta ekip varsa bunlar arasından, yoksa bölgedeki tüm boşta ekipler arasından, karargâhı ihbara kuş uçuşu (haversine) mesafesi en küçük olan ekip seçilir. Seçilen ekip havuzdan çıkarılır; her ekip en çok bir hedef alır ve görev tamamlandıktan sonra yeniden atama yapılmaz.

30. **paragraf 205** — Algoritma 2. Bölge içi rol-farkında açgözlü ekip ataması.

31. **paragraf 206** — Girdi : V bölgedeki ihbarlar; T bölgedeki boşta ekipler (karargâh konumlarıyla)

32. **paragraf 207** — Çıktı : A atama kümesi

33. **paragraf 208** — 1: V'yi (durum önceliği, kanal) anahtarına göre sırala   // kritik < mahsur < yaralı < hafif; acil çağrı önce

34. **paragraf 209** — 2: A <- boş küme

35. **paragraf 210** — 3: her v ∈ V için

36. **paragraf 211** — 4:     T boş ise döngüyü kır

37. **paragraf 212** — 5:     v.durum ∈ {kritik, mahsur} ise ρ <- v.profil_rolü

38. **paragraf 213** — 6:     değilse ρ <- rol(v.metin_kategorisi); kategori yoksa ρ <- v.profil_rolü

39. **paragraf 214** — 7:     H <- {t ∈ T : t.rol = ρ};  H boş ise H <- T

40. **paragraf 215** — 8:     t* <- H içinde haversine(v, t.karargâh) değeri en küçük ekip

41. **paragraf 216** — 9:     T <- T \ {t*}

42. **paragraf 217** — 10:    v hedefini t* için kilitle; kilit alınamazsa sonraki ihbara geç   // HTTP 409

43. **paragraf 218** — 11:    A <- A ∪ {(t*, v)}

44. **paragraf 219** — 12: A döndür

45. **paragraf 220** — Bu atama kuralı ve iplik-güvenli görev kilitleme (TaskLock), sistemin sevk katmanının tasarımını tanımlar; ancak Bölüm 4'teki tatbikat değerlendirmesi ekip–afetzede eşlemesini turların döndürülmesiyle yapar (mahalle başına beş giriş ağzı × en çok beş afetzede, beş turda en çok 25 çift) ve bu atama algoritmasını çağırmaz. Karşılaştırma kolları aynı çiftleri ve aynı başlangıç–hedef noktalarını kullanır; kollar yalnız güzergâh hesabında ayrışır, dolayısıyla ölçülen fark atama kuralından değil kapanma bilgisinin kullanımından kaynaklanır. Rol-farkında atama ile küresel atama eniyilemesi bu değerlendirmede koşulmamış, Bölüm 5.4'te gelecek çalışma olarak konumlandırılmıştır.

46. **paragraf 221** — hedef kilitleme bir eşzamanlılık denetimi, Algoritma 2 ise yerel ve açgözlü bir kuraldır; ikisi de bir atama eniyilemesi değildir.

47. **paragraf 249** — Deneysel ortamın donanım ve yazılım yapılandırması ile tatbikat varsayımları.

48. **paragraf 251** — Bölüm 4.5'teki gecikme ölçümleri ve Tablo 17'deki çıkarım süreleri, grafik işlemci hızlandırması kullanılmadan bir dizüstü bilgisayarda (Intel Core i7-12700H) ölçülmüştür. Bölüm 4.6–4.9'daki tatbikat sayıları, tatbikat kodunda bulunan üç kusurun düzeltilmesinden sonra ikinci bir masaüstü bilgisayarda (AMD Ryzen 5 5500) yeniden üretilmiştir (Bölüm 5.3(b)); bu sayılar benzetim içindeki ulaşım süreleridir ve aynı model ağırlıklarıyla hasar oranı, kapalı kenar ve kapsama değerleri ilk makinedekiyle birebir aynı çıkmıştır. Her iki makinede de çıkarım modelleri merkezî işlemci üzerinde çalışmıştır. Bölüm 4.2'deki bölütleme karşılaştırması Kaggle üzerinde bir NVIDIA Tesla T4 (16 GB) ile, Python 3.12.13 ve PyTorch 2.10.0+cu128 altında, segmentation_models_pytorch 0.5.0, albumentations 2.0.8 ve timm 1.0.26 sürümleriyle eğitilmiştir (Tablo 11). Afet sonrası hasar tespitinde kullanılan derin öğrenme modellerinin mütevazı donanımla eğitilebildiği yazında gösterilmiştir: [22] numaralı çalışma, 6 Şubat 2023 depremleri sonrası göçmüş binaların bölütlenmesinde bir masaüstü sınıfı işlemci ve 8 GB bellekli bir grafik işlemcisi kullanmıştır.

49. **paragraf 291** — Bu bölümde platformun bir müdahale döngüsünü uçtan uca tamamlayabildiği ve üç veri kanalının aynı mahalleye inip zincirin sonunda güzergâha dönüştüğü gösterilmektedir. Değerlendirme, Hatay ve Gaziantep'te üç gerçek mahallede (Defne/Elektrik, İslahiye, Nurdağı) yürütülmüştür. Her mahallede ekipler, mahalleye giren gerçek yol ağızlarında (OSM düğümleri) konuşlanır; beş giriş ağzı ile beş afetzede beş turda döndürülerek eşlenir (en çok 25 çift). Kapanmalar, o mahallenin açık drone ortofotosu üzerinde koşan kendi hasar modelimizin çıktısının OSM yol ağıyla piksel kesişiminden gelir.

50. **paragraf 292** — Tatbikat üç kanal koşturur. (i) Uydu/drone kanalı: hasar bölütlemesi ve yol ağı kesişiminden kapanmalar (Bölüm 3.4). (ii) Kamera kanalı: gerçek deprem fotoğraflarında catlak.pt ve bina.pt YOLO modellerinin çıkarımı. (iii) Metin kanalı: Türkçe ihbar metinlerinde BERTurk sınıflandırması. Üç kanalın çıktıları ortak bir sözleşmeye iner ve arayüzün ısı haritasında ayrı katmanlar olarak gösterilir. Kamera fotoğrafları 6 Şubat 2023 depremlerinin ardından (Şubat–Ağustos 2023) çekilmiş, Wikimedia Commons'ta kamu malı ya da CC BY-SA 4.0 lisansıyla yayımlanmış gerçek karelerdir (künye ve SHA-256 ile kayıtlı; çoğu Hatay/Antakya) ve gösterilen mahallenin fotoğrafı değildir; ihbar metinleri tatbikat için elle yazılmış sentetik metinlerdir; her iki kanalın harita üzerindeki konumları modelin hasarlı bulduğu alanlardan tohumla üretilir ve her kayıt sentetik konum etiketi taşır.

51. **paragraf 293** — Ekip–afetzede eşlemesi. Tatbikatta eşleme, beş giriş ağzı ile beş afetzede arasında turların döndürülmesiyle yapılır (mahalle başına en çok 25 çift); bir atama eniyilemesi ya da rol-farkında açgözlü atama bu değerlendirmede koşulmaz. Rol-farkında atama ve iplik-güvenli görev kilitleme (TaskLock) ile eşzamanlılık güvencesi ayrı bir bileşen olarak tanımlıdır ancak tatbikat koşum yoluna bağlı değildir; bu bileşen ve küresel atama eniyilemesi Bölüm 5.4'te gelecek çalışma olarak sunulmuştur.

52. **paragraf 294** — Güzergâh iç tutarlılığı. Rotalanan güzergâhların hiçbiri kapalı olarak işaretlenmiş bir kenar içeremez: QuakeMind kolunda kapalı kenarlara sonsuz ağırlık verilir, harita varyantlarında ise bu kenarlar çizge görünümünden (nx.restricted_view) tümüyle dışlanır; en kısa yol araması bu kenarları yapısal olarak kullanamaz. A* aramasının kendisi bağımsız bir çözücüyle çapraz doğrulanmıştır: üç alanın beş tohumundaki bütün ekip–afetzede çiftlerinde, kapanmasız ve kapanmalı iki görünümde (248 ayrı sorgu) A*'ın bulduğu süre, aynı maliyet modeliyle açıkça kurulan kenar grafiği üzerinde networkx Dijkstra'sının bulduğu süreyle birebir aynıdır (en büyük fark 5,7·10⁻¹⁴ sn; 8 sorguda ikisi de hedefe yol bulamamıştır). Tatbikat mahallelerinde en yüksek kenar hızı 45–70 km/sa olduğundan taslağın önceki hâlindeki sabit 80 km/sa sezgiseli bu alanlarda da kabul edilebilir kalmış ve sonuçları etkilememiştir. Sahadaki geçilebilirliğin doğrulanması ayrı bir konudur ve burada iddia edilmemektedir.

53. **paragraf 295** — Kanal ölçümleri. Kamera kanalında 13 gerçek fotoğrafın tamamı tespit vermiş (toplam 47 çatlak, 65 bina); hibrit çıkarım medyanı 307,9 ms, en uzunu 383,0 ms'dir. Metin kanalında 18 ihbar metninin sınıflandırma medyanı 48,2 ms, en uzunu 58,9 ms'dir (düzeltilmiş sınıflandırma katmanıyla, beş koşumun medyanı 47,8–48,5 ms; ilk koşum soğuk başlangıç nedeniyle 62,3 ms verdiği için raporlanan değer kararlı banttır); aynı katmanla metinlerin on biri yazarın niyetiyle örtüşmüş (düzeltmeden önce dokuzu), örtüşmeyen yedisinin dördü 'Acil Yardım İhtiyacı', üçü 'Enkaz Bildirimi' sınıfına gitmiştir. Bu sayılar tespit sayısı ve gecikmedir, doğruluk (mAP, F₁) değildir: fotoğraflarda kutu düzeyinde yer gerçeği, metinlerde bağımsız etiket bulunmamaktadır (Bölüm 3.10). Coğrafi kodlama, tam hatta iki metinde 3,3 ve 4,4 saniyeye çıktığından tatbikat isteğinde çağrılmamaktadır. Ölçümler tek bir dizüstü bilgisayarda, grafik işlemci hızlandırması olmadan yapılmıştır.

54. **paragraf 300** — Metin kanalında bir eğilim gözlenmiştir. On sekiz ihbar metninden on biri yazarın niyetiyle örtüşmüştür. Bu bir doğruluk ölçüsü değildir ('beklenen' etiket tek kişinin yargısıdır ve 'Enkaz Bildirimi' ile 'Acil Yardım İhtiyacı' sınırı gerçekten bulanıktır). Sınıflandırma katmanının ilk hâlinde örtüşme 9/18'di ve on sekiz çıktının on ikisini model değil anahtar sözcük kurtarma katmanı belirliyordu (Bölüm 3.6); katman düzeltildikten sonra kararların on beşini model, üçünü kurtarma katmanı vermektedir. Örtüşmeyen yedi metnin üçünde model ihtiyaç tipine ait bir alt etiket vermiş ("su ve bebek maması" için Yemek, "soba ve yakacak" için Isınma, "jeneratör ve aydınlatma" için Arama Ekipmanı), eşleme ise bu alt etiketleri Acil Yardım'a bağlamıştır (Tablo 8); yazar üçünü de lojistik ihtiyaç olarak etiketlemiştir. Üçünde model "Enkaz Kaldırma" demiştir: enkaz altındaki bir yakınını bildiren, kanaması durmayan bir yaralıyı bildiren ve çökmüş duvarın kapattığı bir caddeyi bildiren metinler. Kalan birinde, ambulansın giremediği bir sokağı bildiren metin kurtarma katmanında önceliği yüksek "ambulans" sözcüğüyle Acil Yardım'a atanmıştır. Dikkat çekici bir bulgu, modelin dört yol kapanması metninin hiçbirini ulaşım etiketiyle tanımamasıdır: üçüne "Alakasız" (skor 0,58–0,65), birine "Enkaz Kaldırma" demiştir; üç metin ancak kurtarma katmanı sayesinde zincirde kalmıştır. Yol kapanması bilgisi bu hatta bugün modelden değil anahtar sözcüklerden gelmektedir. Modelin 13 etiketli ham çıktısının başarımı bu ölçümle değerlendirilemez; F₁ iddiası için 13 etiket düzeyinde etiketli bir küme gereklidir.

55. **paragraf 305** — Kapanmayı önceden bilmenin operasyonel katkısını niceliklendirmek için tatbikat üç kıyas koluyla koşulmuştur (Bölüm 3.8): kapanmayı bilmeyen ekip (yola çıkar, kapalı sokağa varınca öğrenir, değerlendirir, döner), telsizle paylaşan filo (bir ekibin öğrendiği kapanma anında bütün ekiplere yayılır) ve QuakeMind (analizin çıkardığı kapanmalar baştan bilinir). Değerlendirme üç gerçek mahalle × üç model × beş tohum üzerinde yürütülmüştür; ortalamalar yalnızca bütün kolların ulaştığı ortak görevlerden alınmıştır. Tatbikatta yer gerçeği bir kapanma katmanı bulunmadığından dünya modelin kendi çıktısıdır; bu nedenle QuakeMind kolu tanım gereği kusursuz bilgiye sahiptir ve bu tablo modelin doğruluğunu değil, kapanmayı önceden bilmenin kazandırdığı süreyi ölçer. Modelin doğruluğu ayrı ve etiketli veriyle değerlendirilir (Bölüm 4.3).

56. **paragraf 306** — Her yapılandırma beş rastgelelik tohumuyla koşulmuştur. Çıkarım tohumdan bağımsız olduğundan analiz alan-model başına bir kez, tatbikat tohum başına tekrarlanır. Raporlanan değerler görev başına ortalama ± standart sapmadır; 'küme' sütunu kaç tohumun farklı afetzede kümesi ürettiğini gösterir. Modelin fiilen değerlendirebildiği kenar oranı (kapsama) görüntünün uçuş izine ve mahalle çizgisine bağlıdır, modelden bağımsızdır: Defne'de %19, İslahiye'de %46, Nurdağı'nda %44; modelin görmediği kenar açık sayılır ama ölçülmemiştir.

57. **paragraf 307** — Ana sonuçlar Tablo 16'da verilmektedir. Kazanç keşif sayısını izler: ekip kaç kapanmaya fiilen denk gelirse kazanç o kadar büyüktür. Bu ilişkinin bir bölümü yapısaldır: farkın büyük bölümü keşif başına beyan edilen değerlendirme süresinden geldiğinden (aşağıda, Farkın ayrıştırılması), keşif sayısı ile kazanç arasındaki bağ ölçülen yol farkından çok bu süreyi yansıtır. Nurdağı'nda üç modelin üçü de beş farklı tohum kümesiyle koşabilmiş ve kazanç %54–60 bandında kalmıştır; Defne'de blob sayısı az olduğundan beş tohum tek kurulum vermekte (küme 1/5), oradaki sıfır yayılım sağlamlık değil tek örneklem anlamına gelmektedir. Daha çok hasar bulmak daha çok operasyonel fayda demek değildir: İslahiye'de dengeli model %2,06 hasarla %33,7 kazandırırken en büyük model %1,34 hasarla yalnız %8,3 kazandırmıştır. Belirleyici olan bulunan hasarın miktarı değil, kapanmaların ekip rotalarına düşüp düşmediğidir; bu, bölütleme başarımı ile operasyonel sonucun doğrudan orantılı olmadığını gösteren ölçülmüş bir bulgudur.

58. **paragraf 310** — Farkın ayrıştırılması. Kapanmayı bilmeyen ekip ile QuakeMind arasındaki süre farkı iki bileşenden oluşur (Denklem 11): ekibin fiilen fazladan sürdüğü yol ve dönüşlerden gelen fark ile kapanmaya her varışta yüklenen beyan edilmiş değerlendirme süresi (1,0 dk). Tablo 16'nın ceza payı sütunu bu ayrımı ölçer: her tohumda, kapanmayı bilmeyen ekibin ortak görevlerde ödediği toplam değerlendirme süresinin iki kol arasındaki toplam süre farkına oranı. Pay %68–78 aralığındadır (Nurdağı'nda %73–76); yani keşif başına yalnız 1,0 dakikalık bir değerlendirme süresiyle bile farkın büyük bölümü bu beyan edilmiş süreden, kalanı çizgede fiilen fazladan sürülen yol ve dönüşlerden gelmektedir. 20 dakikalık sabit kaldırılmış olsa da sonuç bu nedenle değerlendirme süresine duyarlılığıyla birlikte bant olarak verilmiştir (Bölüm 4.9, Tablo 20). Kapanmayı bilmeyen ekip her kapalı koridoru tek tek keşfettiğinden yoğun hasarlı alanlarda keşif sayısı yükselir; bu nedenle bu kola göre hesaplanan fark bir üst sınır olarak okunmalı, telsizle paylaşan filoyla birlikte değerlendirilmelidir.

59. **paragraf 311** — Telsizle paylaşan filo. Bir ekibin keşfettiği kapanmanın anında tüm ekiplere yayıldığı bu kol, kapanmayı bilmeyen ekip ile QuakeMind arasında bir orta noktadır ve kazancın bir bölümünü yakalar (Nurdağı, en büyük model: kapanmayı bilmeyen 3,82 dk → telsizle paylaşan 3,24 dk → QuakeMind 1,51 dk); paylaşım keşif sayısını da düşürür (43,8 → 32,0). Bilgi paylaşımı her zaman kazandırmaz: ilk keşfeden ekip yine kendi maliyetini öder ve bilinmeyen yolu açık sayan bir ekip telsizle erken yön değiştirip daha kötü bir koridora sapabilir.

60. **paragraf 314** — Tablo 17, model seçiminin karşılığını göstermektedir. Çıkarım süresini 5,5 kat artırmak (1,91 → 10,50 sn) sınama IoU'sunu tek tohumda yalnız 0,051 yükseltmekte ve operasyonel kazancı tek yönlü artırmamaktadır (U-Net'in üç tohum arasındaki oynaması 0,084 olduğundan bu IoU farkı oynamanın içindedir): orta boy model (MiT-B2) üç alanın üçünde de en iyi ya da en iyiye yakındır ve İslahiye'de en büyük modelin yaklaşık dört katı kazanç verir. Saniye başına operasyonel değeri en yüksek olan orta boy modeldir.

61. **paragraf 315** — Kazancın dağılımı. Toplam fark alanlar ve görevler arasında eşit dağılmaz; kazanç, kapanmaların ekip rotalarına düştüğü alanlarda (Nurdağı) toplanır, düşmediği alanlarda sıfıra yaklaşır. Bu nedenle mutlak süre farkları alandan alana büyük ölçüde değişir ve ortalamalar yalnız bütün kolların ulaştığı ortak görevlerden alınır.

62. **paragraf 331** — Sonucun moloz yayılım yarıçapına (r_h) duyarlılığı üç alanda dört yarıçapla, U-Net MiT-B4 modeli ve tohum 42 ile ölçülmüştür (Tablo 19). r_h, hasarın yoldan ne kadar uzağa yayıldığını varsayan bir yarıçaptır; 0 değeri yalnız yolun tam üstündeki hasarın kapatması demektir (uygulamanın kuralı ve taban çizgi) ve makaledeki bütün sayılar bu değerle üretilmiştir. r_h çıkarımı etkilemez, yalnız maskeden kapanma türetmesini etkiler; bu yüzden model bir kez koşar, her yarıçap için kapanma ve kollar yeniden hesaplanır.

63. **paragraf 334** — Buradaki tuzak görünür kazancın artmasıdır: r_h büyüdükçe 'kazanç' yükselir (%18→20, %6→56, %59→79) ama bu bir iyileşme değildir. Ortak görev sayısı çöker (6→3, 20→5, 25→6) ve iki alanda r_h=25'te sıfıra düşer; yarıçap büyüdükçe kapanma sayısı artar, mahalle kopar, geriye yalnız kolay çiftler kalır ve ortalama onların üzerinden alınır. Yüzde, giderek daralan ve yanlı bir örneklemden gelmektedir. Bu bulgu r_h'nin uzamayı değil aracın girebilmesini belirlediğini göstermekte; varsayılan r_h=0 değiştirilmemiştir.

64. **paragraf 351** — 'te doğrudan görülmektedir.

65. **paragraf 355** — Kategori bazında F₁ değerleri: BERTurk ve TF-IDF + lojistik regresyon (kategoriler sınama kümesindeki kayıt sayısına göre sıralıdır). BERTurk sık kategorilerde belirgin biçimde öndedir. Seyrek kategorilerden Su ve Elektrik kaynağında BERTurk'ün F₁ değeri sıfıra inerken klasik taban çizgisi bu iki kategoride sıfırdan farklı değer üretmektedir; Sağlık kategorisinde de taban çizgisi öndedir. En seyrek üç kategoride (n ≤ 6) iki model de sıfırdadır. Makro-F₁ sıralamasının tersine dönmesinin kaynağı budur.

66. **paragraf 373** — – üzerinde izlenebilmektedir.

67. **paragraf 375** — Yedi risk skorlama modelinin ölçüt bazında karşılaştırması (beş katlı ileri yürüyen bölme; ortalama ± standart sapma). Kesik çizgi rastgele sınıflandırıcıya (ROC-AUC = 0,5) karşılık gelir.

68. **paragraf 382** — 0,04–0,08 aralığındadır. Yedi modelin beşinde en düşük ROC-AUC değeri 1. kattadır.

69. **paragraf 396** — Tatbikat, uydu/drone hasar bölütlemesinden türetilen kapanmalar, yer seviyesi (kamera) ve Türkçe metin kanallarını üç gerçek mahallede tek bir sevk zincirinde birleştirmiş ve bir müdahale döngüsünü uçtan uca tamamlamıştır. Ekip–afetzede eşlemesi turların döndürülmesiyle yapılmış (mahalle başına en çok 25 çift); rol-farkında atama ve iplik-güvenli görev kilitleme sistemin tasarımında tanımlı olmakla birlikte bu değerlendirmede koşulmamıştır (Bölüm 5.4).

70. **paragraf 397** — Rotalanan güzergâhların hiçbiri kapanma kümesindeki bir kenardan geçmemektedir. Bölüm 4.5'te belirtildiği üzere bu sonuç, sert kapatmanın ilgili kenarları çizgeden çıkarması nedeniyle yapısal olarak beklenendir ve planlayıcının kendi kapanma modeline iç tutarlılığını gösterir.

71. **paragraf 398** — Kapanmayı önceden bilmenin katkısı, modelin bulduğu kapanmaların ekip rotalarına düştüğü alanlarda ortaya çıkmaktadır: ölçülen kazanç alan ve modele göre %8–60, en sağlam alanda (Nurdağı, üç model × beş tohum) %54–60'tır; kapanmanın rotaya düşmediği alanlarda fark yoktur. Bu kazanç, tatbikatta dünya modelin kendi çıktısı olduğundan kapanmayı önceden bilmenin değerini ölçer, modelin doğruluğunu değil. Kapanmaya varan ekibin kaybettiği süre önceki sürümdeki 20 dakikalık sabitten 1,0 dakikalık değerlendirme süresine indirilmiş, geri dönüş manevrası çizgede fiilen yapılan dönüş olarak fiyatlanmıştır; buna karşın ölçülen ceza payına göre farkın %68–78'i hâlâ bu beyan edilmiş süreden gelmektedir (Bölüm 4.6), bu nedenle kazanç cezanın değerine duyarlılığıyla birlikte bant olarak okunmalıdır. Telsizle paylaşan filo kolu kazancın bir bölümünü yakalamaktadır (Nurdağı, en iyi model: 3,82 dk → 3,24 dk).

72. **paragraf 399** — Sınama IoU'su operasyonel faydanın iyi bir göstergesi değildir: İslahiye'de dengeli model (sınama IoU 0,409) en büyük modelden (0,433) yaklaşık dört kat fazla kazanç sağlamıştır (%33,7'e karşı %8,3). Bu IoU değerleri tek tohumludur; üç tohumla yinelendiğinde U-Net'in sınama IoU'su 0,349-0,433 arasında değiştiğinden modeller arasında kesin bir bölütleme kalitesi sıralaması da kurulamamaktadır (Bölüm 4.2). Belirleyici olan bulunan hasarın miktarı değil, kapanmaların ekip rotalarına düşüp düşmediğidir; saniye başına operasyonel değeri en yüksek olan orta boy modeldir.

73. **paragraf 400** — Kapanma katmanının doğruluğu, bir mahallede kör insan etiketlemesiyle sınanmış ve kesinlik 4/5 ancak düşük duyarlılık (≈%9) bulunmuştur (Bölüm 4.3): model az yanlış alarm üretmekte ama gerçek kapanmaların çoğunu kaçırmaktadır. Bu, sistemin sahada tek başına güvenilecek bir kapanma haritası vermediğini, ancak tatbikattaki kazanç sayılarının iyimser olmadığını gösterir.

74. **paragraf 408** — (a) Tatbikatta dünya modelin kendi çıktısıdır; bu nedenle Bölüm 4.6'daki süre farkları kapanmayı önceden bilmenin değerini ölçer, bölütleme doğruluğunun değil. Kapanma katmanının doğruluğu yalnızca bir mahallede, tek insan etiketleyiciyle ve küçük örneklemle sınanmıştır (Bölüm 4.3): kesinlik 4/5, duyarlılık ≈%9; ikinci görüş olan büyük dil modeliyle uyum zayıftır (κ = 0,13).

75. **paragraf 411** — (d) Metin zincirinin yanıt süresi bileşenlerine ayrıştırılmamıştır. Tam hatta coğrafi kodlama iki metinde 3,3 ve 4,4 saniyeye çıkmıştır (önbellek ıskası, ağ çağrısı); bu nedenle tatbikat coğrafi kodlamayı çağırmaz. Ölçümler tek bir dizüstü bilgisayarda, grafik işlemci hızlandırması olmadan yapılmıştır.

76. **paragraf 414** — (g) Değerlendirme üç mahalle × üç model × beş tohumdan oluşmaktadır; üç alan on bir ölçülen alandan, kolların en az iki modelde ayrıştığı alanlar olarak seçilmiştir (kalan sekizin beşinde ayrışma yoktur, üçünde yalnız tek modelde; Bölüm 4.7). Defne'de blob azlığından beş tohum tek kurulum vermekte (küme 1/5); oradaki sıfır yayılım sağlamlık değil tek örneklemdir. Görevler aynı mahalle ağını paylaştığından tam bağımsız değildir.

77. **paragraf 423** — (p) Görev tabanlı değerlendirmede modeller uydu görüntüsüyle (0,3–0,5 m/piksel) eğitilmiş ve drone ortofotolarında, eğitim ölçeğine yakın z18 çözünürlüğünde (yaklaşık 0,48 m/piksel) çalıştırılmıştır. Çözünürlük eşlenmiş olsa da platform ve sensör farkı (İHA ortofoto mozaiği ile uydu görüntüsü arasındaki bakış açısı, ışık ve işleme farkları) bir alan kayması oluşturur; bu, kapanma katmanının düşük duyarlılığının olası nedenlerinden biridir.

78. **paragraf 424** — (q) Yer seviyesi hasar tespiti (çatlak ve bina hasarı YOLOv8 modelleri) için bağımsız bir sınama kümesinde nesne tespiti başarımı ölçülmemiştir; raporlanan mAP değerleri (Bölüm 3.5) en iyi ağırlığın seçiminde de kullanılan doğrulama bölmesine aittir ve iyimser bir üst kestirimdir.

79. **paragraf 427** — Öncelikli iş, algılama katmanının kapanma duyarlılığını yükseltmektir: modelin drone ve yüksek çözünürlüklü görüntüyle yeniden eğitilmesi ve yol hasarına özgü etiketli bir kümeyle doğrudan yol hasarı sınıfında eğitilmesi. İkincisi, kapanma katmanının doğruluğunun tek mahalle ve tek insan etiketleyicinin ötesinde, birden çok insan etiketleyiciyle ve etiketleyiciler arası uyum raporlanarak ve daha geniş bir örneklemle ölçülmesidir. Üçüncüsü, kamera kanalının bağımsız bir saha sınama kümesinde mAP cinsinden ve metin kanalının DepremKit/TSEqD gibi dış bir kümede F₁ cinsinden ölçülmesi ve yol kapanması ihbarlarının anahtar sözcük yerine modelden tanınabilmesi için eğitim kümesine bu tür ihbarların eklenmesidir. Dördüncüsü, sevk katmanının turların döndürülmesinden gerçek bir rol-farkında atama eniyilemesine geçirilmesi ve üretim API'sindeki görev kilidinin (HTTP 409) yetki denetimiyle birlikte tatbikata bağlanmasıdır. Beşincisi, bulut ve duman koşulları için radar tabanlı her hava tespitinin optik kanalla birleştirilmesi ile belirsizliğin niceliklendirilmesi ve açıklanabilirlik bileşenlerinin eklenmesidir.

80. **paragraf 434** — Ölçülen sonuçlar üç başlıkta toplanmaktadır. Birincisi, kapanmayı önceden bilmenin operasyonel değeridir: üç gerçek mahallede, kapanmanın ekip rotalarına düştüğü alanlarda erişim süresi %8–60 kısalmış, en sağlam alanda (Nurdağı) %54–60 kazanç ölçülmüştür; kapanmanın rotaya düşmediği alanlarda fark yoktur. Ölçülen ceza payına göre farkın %68–78'i keşif başına beyan edilen değerlendirme süresinden geldiğinden sonuç, cezanın değerine duyarlılığıyla birlikte bant olarak okunmalıdır. Bu büyüklük, tatbikatta dünya modelin kendi çıktısı olduğundan kapanmayı önceden bilmenin değerini ölçer, modelin doğruluğunu değil. İkincisi, modeller arasındaki sınama IoU farklarının bu kazancı öngörmediğidir: saniye başına operasyonel değeri en yüksek olan orta boy modeldir. Üçüncüsü, kapanma katmanının doğruluğunun bir mahallede kör insan etiketlemesiyle sınanması ve kesinlik 4/5 ile düşük duyarlılık (≈%9) bulunmasıdır.

81. **paragraf 437** — bir protokolün tanımlanıp uygulanması olarak sunulmaktadır. Protokolün ilk uygulaması, kapanmayı önceden bilmenin kazancının bölütleme başarımıyla değil kapanmaların ekip rotalarına düşmesiyle belirlendiğini göstermiş ve algılama katmanının hangi yönde iyileştirilmesi gerektiğini ortaya koymuştur: bugünkü model az yanlış alarm üretmekte, ancak gerçek kapanmaların çoğunu kaçırmaktadır; öncelik duyarlılığın artırılmasıdır.

82. **paragraf 447** — Yazar katkıları CRediT (Contributor Roles Taxonomy) sınıflamasına göre verilmiştir.

83. **paragraf 448** — Furkan Emre İnce: Kavramsallaştırma, yöntem, yazılım, doğrulama, biçimsel çözümleme, araştırma, kaynaklar, veri düzenleme, özgün taslağın yazımı, gözden geçirme ve düzenleme, görselleştirme, proje yönetimi.

84. **paragraf 449** — Utku Ceylan: Kavramsallaştırma, yöntem, yazılım, doğrulama, biçimsel çözümleme, araştırma, kaynaklar, veri düzenleme, özgün taslağın yazımı, gözden geçirme ve düzenleme, görselleştirme, proje yönetimi.

85. **paragraf 450** — Esra Uray: Denetim, finansman temini.

86. **paragraf 451** — Furkan Emre İnce ve Utku Ceylan yukarıdaki rolleri ortaklaşa yürütmüştür.

87. **paragraf 459** — Ankara, https://deprem.afad.gov.tr/assets/pdf/Kahramanmaras%20%20Depremleri_%20On%20Degerlendirme%20Raporu.pdf (Erişim tarihi: 27.09.2026), (2023).

88. **paragraf 460** — Bölgesel Deprem-Tsunami İzleme ve Değerlendirme Merkezi, "06 Şubat 2023 Mw=7.7 Sofalaca Şehitkamil Gaziantep Depremi" ve "06 Şubat 2023 Mw=7.6 Ekinözü Kahramanmaraş Depremi", Basın bültenleri, İstanbul, http://www.koeri.boun.edu.tr/sismo/2/06-subat-2023-ml7-4-sofalaca-sehitkamil-gaziantep-depremi/ ve http://www.koeri.boun.edu.tr/sismo/2/06-subat-2023-ml7-5-ekinozu-kahramanmaras-depremi/ (Erişim tarihi: 27.09.2026), (2023).

89. **paragraf 462** — technical_manual_4-2.pdf (Erişim tarihi: 16.09.2026), (2020).

90. **paragraf 464** — Séismologie, 15, Luxembourg, doi:10.2312/EMS-98.full.en, (1998).

91. **paragraf 466** — https://mapping.emergency.copernicus.eu/activations/EMSR648/ (Erişim tarihi: 27.09.2026), (

92. **paragraf 488** — turkiye-syria-earthquake/ (Erişim tarihi: 27.09.2026), (

93. **paragraf 498** — https://github.com/ultralytics/ultralytics (Erişim tarihi: 27.09.2026), (

94. **paragraf 502** — https://www.openstreetmap.org (Erişim tarihi: 27.09.2026), (

95. **paragraf 503** — https://livingatlas.arcgis.com/wayback (Erişim tarihi: 27.09.2026), (

96. **paragraf 504** — CC BY-NC 4.0, https://vantor.com/company/open-data-program/ (Maxar Intelligence 1 Ekim 2025'te Vantor adını almıştır; eski adres https://www.maxar.com/open-data bu sayfaya yönlenmektedir; Erişim tarihi: 16.09.2026), (2023).

97. **paragraf 505** — https://openaerialmap.org (Erişim tarihi: 27.09.2026), (

98. **paragraf 515** — doi:10.3390/data9070088, (2024). Veri kümesi: https://doi.org/10.5281/zenodo.11647956 (2. sürüm, CC BY-NC 4.0).

99. **paragraf 516** — (Erişim tarihi: 27.09.2026).

100. **paragraf 518** — https://github.com/qubvel-org/segmentation_models.pytorch (Erişim tarihi: 27.09.2026), (2020).

101. **paragraf 521** — (Erişim tarihi: 27.09.2026).

102. **paragraf 522** — [64] Help.NGO, "Hatay - Defne - Elektrik Mah."; "Islahiye, Turkey - Feb 15, 2023"; "Nurdagi - Feb 15, 2023 (Warning Low Quality)", İnsansız hava aracı ortofotoları, OpenAerialMap, görüntü kimlikleri 63eb78a0ca43600005f4d920, 63eef9a4525f0700077ed49a, 63ef697b525f0700077ed4a2, lisans CC BY 4.0, https://map.openaerialmap.org (Erişim tarihi: 27.09.2026), (2023).

103. **paragraf 523** — [65] Xiao, T., Liu, Y., Zhou, B., Jiang, Y., Sun, J., "Unified perceptual parsing for scene understanding", Proceedings of the European Conference on Computer Vision (ECCV), 418-434, doi:10.1007/978-3-030-01228-1_26, (2018).

104. **paragraf 524** — [66] Liu, Z., Mao, H., Wu, C. Y., Feichtenhofer, C., Darrell, T., Xie, S., "A ConvNet for the 2020s", Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 11976-11986, doi:10.1109/CVPR52688.2022.01167, (2022).

105. **paragraf 525** — [67] Sun, Y., Wang, Y., Eineder, M., "QuickQuakeBuildings: Post-earthquake SAR-optical dataset for quick damaged-building detection", IEEE Geoscience and Remote Sensing Letters, 21: 1-5, doi:10.1109/LGRS.2024.3406966, (2024).

106. **paragraf 526** — [68] Humanitarian OpenStreetMap Team, "HOTOSM", https://www.hotosm.org (Erişim tarihi: 27.09.2026), (2023).

107. **tablo 3, satır 2** — Açık veri deposu; CC BY-NC 4.0

108. **tablo 3, satır 4** — Help.NGO İHA ortofotoları [64] (OpenAerialMap üzerinden)

109. **tablo 3, satır 4** — İnsansız hava aracı ortofotosu, üç sahne (Tablo 3–4)

110. **tablo 3, satır 4** — 9 ve 14 Şubat 2023 (deprem sonrası)

111. **tablo 3, satır 4** — Hatay (Defne/Elektrik), Gaziantep (İslahiye, Nurdağı)

112. **tablo 3, satır 4** — Özgün 3,4–7,9 cm/piksel; analizde z18 karolarıyla yaklaşık 0,48 m/piksel

113. **tablo 3, satır 4** — Açık karo servisi; CC BY 4.0

114. **tablo 3, satır 8** — KATE-PD [56]

115. **tablo 3, satır 8** — Deprem sonrası optik uydu görüntüsü (Maxar 193, Airbus Pléiades 639 karo) ve hasarlı bina maskeleri; bina hasarı bölütlemesinin eğitim, doğrulama ve sınama kümesi (Bölüm 4.2)

116. **tablo 3, satır 8** — 2023 (deprem sonrası)

117. **tablo 3, satır 8** — Adıyaman, Gaziantep, Hatay, Kahramanmaraş, Kilis, Malatya, Osmaniye

118. **tablo 3, satır 8** — 0,375–0,5 m; 512 × 512 piksel; 832 karo

119. **tablo 3, satır 8** — Hugging Face veri deposu (CSCRS/kate-pd); veri kartında lisans belirtilmemiş

120. **tablo 3, satır 9** — KATE-CD [56]

121. **tablo 3, satır 9** — Deprem öncesi ve sonrası optik uydu görüntü çiftleri (Maxar Open Data, Airbus Pléiades) ve elle çizilmiş ikili hasar maskeleri; bu çalışmada yalnız deprem öncesi görüntüleri hasarsız (negatif) örnek olarak kullanılmıştır (Bölüm 4.2)

122. **tablo 3, satır 9** — 2023 (deprem öncesi ve sonrası)

123. **tablo 3, satır 9** — Adıyaman, Gaziantep, Hatay, Kahramanmaraş, Kilis, Malatya, Osmaniye

124. **tablo 3, satır 9** — 0,3–0,5 m; 512 × 512 piksel; 486 çift; sonrası görüntüleri KATE-PD ile özdeş olduğundan yalnız öncesi görüntüleri alınmıştır

125. **tablo 3, satır 9** — Hugging Face veri deposu (CSCRS/kate-cd); veri kartında lisans belirtilmemiş

126. **tablo 3, satır 10** — MEDBFS [57], Türkiye alt kümesi

127. **tablo 3, satır 10** — Deprem öncesi (WorldView) ve sonrası (Jilin-1) optik uydu görüntüsü; piksel düzeyinde ağır hasar ve yıkılma etiketleri; bu çalışmada eğitime katılmamış, yalnız dış sınamada kullanılmıştır (Bölüm 4.2)

128. **tablo 3, satır 10** — 6 Şubat 2023 depremi (öncesi ve sonrası)

129. **tablo 3, satır 10** — Kahramanmaraş, Gaziantep

130. **tablo 3, satır 10** — 0,5 m (dış sınamada 0,75 m); 512 × 512 piksel; 438 deprem öncesi + 438 deprem sonrası görüntü

131. **tablo 3, satır 10** — Zenodo (doi:10.5281/zenodo.11647956, 2. sürüm); CC BY-NC 4.0

132. **tablo 3, satır 11** — Türkçe afet metni kümesi (deprem-private/intent_test_v13_anonymized)

133. **tablo 3, satır 11** — Deprem sonrası Türkçe afet metinleri, çok etiketli sınıflar; metin sınıflandırma (Bölüm 3.6)

134. **tablo 3, satır 11** — 12–14 Şubat 2023 (kayıt zaman damgaları)

135. **tablo 3, satır 11** — Belirtilmemiş

136. **tablo 3, satır 11** — 2 028 kayıt (1 418 eğitim / 305 doğrulama / 305 sınama)

137. **tablo 3, satır 11** — Özel Hugging Face deposu; istek üzerine sorumlu yazardan temin edilebilir (bkz. Veri Erişilebilirliği)

138. **tablo 12, satır 0** — Bileşen

139. **tablo 12, satır 0** — Gecikme ve çıkarım süresi ölçümü (Tablo 15, 17)

140. **tablo 12, satır 0** — Tatbikat koşumu (Bölüm 4.6–4.9; düzeltilmiş kod, 28 Eylül 2026)

141. **tablo 12, satır 0** — Model eğitimi (Bölüm 4.2)

142. **tablo 12, satır 1** — Ortam

143. **tablo 12, satır 1** — Dizüstü bilgisayar (yerel)

144. **tablo 12, satır 1** — Masaüstü bilgisayar (yerel)

145. **tablo 12, satır 2** — İşlemci

146. **tablo 12, satır 2** — Intel Core i7-12700H (14 çekirdek, 20 iş parçacığı)

147. **tablo 12, satır 2** — AMD Ryzen 5 5500 (6 çekirdek, 12 iş parçacığı)

148. **tablo 12, satır 2** — Kayıt altına alınmamıştır

149. **tablo 12, satır 3** — Grafik işlemci

150. **tablo 12, satır 3** — Hesaplamada kullanılmadı (tümleşik Intel Iris Xe)

151. **tablo 12, satır 3** — Hesaplamada kullanılmadı (AMD Radeon RX 6600)

152. **tablo 12, satır 3** — NVIDIA Tesla T4 (16 GB)

153. **tablo 12, satır 4** — Sistem belleği

154. **tablo 12, satır 4** — 16 GB

155. **tablo 12, satır 4** — 16 GB

156. **tablo 12, satır 4** — Kayıt altına alınmamıştır

157. **tablo 12, satır 5** — Depolama

158. **tablo 12, satır 5** — 512 GB SSD

159. **tablo 12, satır 5** — Kayıt altına alınmamıştır

160. **tablo 12, satır 5** — —

161. **tablo 12, satır 6** — İşletim sistemi

162. **tablo 12, satır 6** — Windows 11, 64 bit (sürüm 10.0.26200)

163. **tablo 12, satır 6** — Windows 11 Pro, 64 bit (sürüm 10.0.26200)

164. **tablo 12, satır 6** — Kayıt altına alınmamıştır

165. **tablo 12, satır 7** — Python / PyTorch

166. **tablo 12, satır 7** — Python 3.12.6 / PyTorch 2.13.0 (yalnız CPU)

167. **tablo 12, satır 7** — Python 3.12.10 / PyTorch 2.11.0 (yalnız CPU)

168. **tablo 12, satır 8** — Temel kitaplıklar

169. **tablo 12, satır 8** — Ultralytics 8.4.116; Transformers 5.14.1; NetworkX 3.6.1; OSMnx 2.1.1; pyrosm 0.13.1; FastAPI 0.141.1; segmentation_models_pytorch 0.5.0

170. **tablo 12, satır 8** — NetworkX 3.6.1; OSMnx 2.1.0; pyrosm 0.13.1; segmentation_models_pytorch 0.5.0; Ultralytics 8.4.57; Transformers 5.8.0

171. **tablo 12, satır 9** — Kenar hızı v(e)

172. **tablo 12, satır 9** — —

173. **tablo 12, satır 10** — Kapanma cezası t_u

174. **tablo 12, satır 10** — —

175. **tablo 12, satır 11** — Tatbikat ve ölçüm ortamlarındaki sürümler, koşumların yürütüldüğü arka uç sanal ortamlarından okunmuştur. Tatbikat sayıları benzetim içindeki ulaşım süreleridir; ikinci makinede aynı model ağırlıklarıyla (SHA-256 doğrulandı) hasar oranı, kapalı kenar ve kapsama değerleri ilk makinedekiyle birebir aynı çıkmıştır. Eğitim oturumlarında grafik işlemci dışındaki bilgiler kaydedilmemiştir.

176. **tablo 12, satır 11** — Tatbikat ve ölçüm ortamlarındaki sürümler, koşumların yürütüldüğü arka uç sanal ortamlarından okunmuştur. Tatbikat sayıları benzetim içindeki ulaşım süreleridir; ikinci makinede aynı model ağırlıklarıyla (SHA-256 doğrulandı) hasar oranı, kapalı kenar ve kapsama değerleri ilk makinedekiyle birebir aynı çıkmıştır. Eğitim oturumlarında grafik işlemci dışındaki bilgiler kaydedilmemiştir.

177. **tablo 12, satır 11** — Tatbikat ve ölçüm ortamlarındaki sürümler, koşumların yürütüldüğü arka uç sanal ortamlarından okunmuştur. Tatbikat sayıları benzetim içindeki ulaşım süreleridir; ikinci makinede aynı model ağırlıklarıyla (SHA-256 doğrulandı) hasar oranı, kapalı kenar ve kapsama değerleri ilk makinedekiyle birebir aynı çıkmıştır. Eğitim oturumlarında grafik işlemci dışındaki bilgiler kaydedilmemiştir.

178. **tablo 12, satır 11** — Tatbikat ve ölçüm ortamlarındaki sürümler, koşumların yürütüldüğü arka uç sanal ortamlarından okunmuştur. Tatbikat sayıları benzetim içindeki ulaşım süreleridir; ikinci makinede aynı model ağırlıklarıyla (SHA-256 doğrulandı) hasar oranı, kapalı kenar ve kapsama değerleri ilk makinedekiyle birebir aynı çıkmıştır. Eğitim oturumlarında grafik işlemci dışındaki bilgiler kaydedilmemiştir.

179. **tablo 26, satır 2** — Bağımsız sınama yok; eğitimdeki doğrulama bölmesinde (en iyi ağırlığın seçiminde de kullanıldı): bina mAP@0,5 = 0,592, mAP@0,5:0,95 = 0,394; çatlak 0,731 / 0,584

180. **tablo 26, satır 5** — Ölçülmedi (küme yok)
