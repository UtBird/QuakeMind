# Lisans teyidi için e-posta taslakları (B-1 madde 4)

Gönderim senin sorumluluğunda; aşağıdaki iki taslak doğrudan kopyalanıp
kullanılabilir. Yazar iletişim adresleri ilgili makalelerin "Corresponding
Author" bölümünden alınmalı (adresler burada tahmin edilmedi).

---

## 1. TE23D — YANIT GELDİ (Can Ekkazan, ~11 Ekim 2026). Yazılacak cevap aşağıda.

**Durum:** ilk e-posta gönderildi, Can Ekkazan ayrıntılı yanıt verdi. Yanıtın özü:

| Bileşen | Koşul |
|---|---|
| Uydu görüntüleri | Telif **Planet Labs PBC**; Planet'in yazılı izniyle, yalnız ticari olmayan bilimsel araştırma |
| Etiketler | **CC BY-NC-ND 4.0**, TE23D yazarlarınca lisanslı |

**İzin verilenler:** ticari olmayan akademik çalışmada model eğitimi, doğrulama ve test; görüntüleri
yeniden boyutlandırma; **kendi bölmemize göre yeniden ayırma**; sonuçları (metrik, kıyas, örnek çıktı)
akademik yayında paylaşma.

**Yasaklar:** (1) veri kümesi, görüntüler ya da değiştirilmiş hâlleri **yeniden dağıtılamaz**;
(2) Planet görüntülerini yeniden üretmeye yönelik modellerde (süper çözünürlük, görüntü üretimi)
kullanılamaz — bölütleme bu kapsamda **değil**, yani serbest; (3) **TE23D ile eğitilmiş model
ağırlıkları kamuya açık paylaşılacaksa Planet Labs PBC'den yazılı onay gerekiyor.**

**Sahne konum kodları** (dosya adının ilk üç hanesi): 001–002 Adıyaman-Merkez · 003 Gaziantep-İslahiye ·
004 Gaziantep-Nurdağı · 005 Hatay-İskenderun · 006–008 Hatay-Antakya · 010 Hatay-Payas ·
011 Hatay-Dörtyol · 013 Hatay-İskenderun · 014–015 Kahramanmaraş-Merkez.
→ **009 ve 012 listede yok**, makale ise 15 GeoTIFF diyor (listede 13 kod var).

**Can'ın bize sorduğu:** *"© 2025 TE23D, All rights reserved" ifadesi tam olarak makalede nerede
yazılmış göremedim, onu sormak istiyorum düzelttirmemiz gerekebilir.*
→ **Bizim hatamız.** O ifade makalede DEĞİL; veri sayfasının alt bilgisindeydi. İlk e-postamız iki
kaynağı karıştırıp "aynı sayfanın iki yerinde" demişti. Cevabın ilk maddesi bu olmalı, yoksa Can
makalesinde olmayan bir şeyi düzeltmeye çalışacak.

---

**Konu:** Re: TE23D veri kümesi — lisans teyidi ve birkaç soru

**Gövde:**

> Merhaba Can Bey,
>
> Ayrıntılı ve çok açık yanıtınız için teşekkür ederiz. Önce sorduğunuz noktayı netleştirmek
> istiyoruz, çünkü hata bizde.
>
> **"© 2025 TE23D, All rights reserved" ifadesi makalenizde geçmiyor.** Makalenin on iki sayfasının
> tam metnini yeniden taradık; "rights reserved" ifadesi hiçbir yerde yok. Makaledeki tek lisans
> ifadesi birinci sayfanın dipnotundaki IEEE açık erişim bildirimi: *"© 2025 The Authors. This work is
> licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 License."* Yani
> makalenizde düzeltilmesi gereken bir şey yok.
>
> Gördüğümüz ifade **veri kümesinin dağıtım sayfasının alt bilgisindeydi**
> (isl.ce.yildiz.edu.tr/datasets/te23d, yaklaşık Eylül 2026). İlk e-postamızda bunu makalenin
> lisansıyla aynı yere koyup "aynı sayfanın iki ayrı yerinde" biçiminde yazmışız; bu ifade hatalıydı
> ve kafa karışıklığına yol açtığı için özür dileriz. Doğrusu şu: makale CC BY-NC-ND, sayfanın alt
> bilgisi ise tüm hakları saklı tutuyordu ve veri kümesinin lisansı hiçbir yerde yazılı değildi —
> yanıtınız bu boşluğu zaten doldurdu.
>
> Bu arada muhtemelen sizin de haberiniz olması gereken bir durum var: **isl.ce.yildiz.edu.tr şu an
> erişilemiyor.** 11 Ekim 2026 itibarıyla 80 numaralı port zaman aşımına uğruyor, 443 bağlantıyı
> reddediyor (alan adı 95.183.138.64'e çözülüyor, yani DNS sağlam). Wayback Machine'de de o sayfanın
> arşiv kaydı yok. Bu yüzden alt bilgiyi ekran görüntüsüyle gösteremiyoruz; sayfa açıldığında şablon
> alt bilgisini kontrol etmek isteyebilirsiniz.
>
> Lisans koşullarını şöyle anladık, teyit ederseniz memnun oluruz: görüntüler Planet Labs PBC telifli
> ve yalnız ticari olmayan bilimsel araştırmada kullanılabilir; etiketler CC BY-NC-ND 4.0; veri kümesi
> ya da türevleri yeniden dağıtılamaz; Planet görüntülerini yeniden üretmeye yönelik modellerde
> kullanılamaz (bölütleme bu kapsamda değil); ve TE23D ile eğitilmiş ağırlıklar kamuya açık
> paylaşılacaksa Planet'ten yazılı onay gerekiyor.
>
> Son madde bizim için doğrudan bağlayıcı, onun için planımızı açıkça yazmak isteriz. Bölütleme model
> ağırlıklarımızı Hugging Face üzerinde **açık** paylaşıyoruz
> (huggingface.co/Utbird/dispath_optimized_mitb4_focal_dice30); bu ağırlıklar KATE-PD ve KATE-CD
> kümeleriyle eğitildi, TE23D ile eğitilmedi. Bu nedenle:
>
> 1. Birincil planımız TE23D'yi **yalnız dış sınama kümesi** olarak kullanmak: mevcut ağırlıklarımızla
>    çıkarım yapıp metrikleri raporlamak. Bu durumda TE23D ile eğitilmiş bir ağırlık ortaya çıkmıyor
>    ve Planet onayı gerekmiyor.
> 2. Ek olarak sizin protokolünüzü yeniden üretmeyi (TE23D eğitim bölmesinde eğitip TE23D sınamasında
>    ölçmeyi) değerlendiriyoruz. Bu durumda **yalnız metriği** yayımlar, o ağırlıkları kamuya açık
>    paylaşmayız. Bu okumanın doğru olduğunu onaylarsanız rahat ederiz.
>
> Üç küçük sorumuz kaldı:
>
> **(a) Erişim.** Site kapalı olduğu için veriyi indiremiyoruz. Alternatif bir indirme adresi var mı,
> yoksa kesinti geçici mi?
>
> **(b) Eksik iki kod.** Gönderdiğiniz tabloda 13 kod var (001–008, 010, 011, 013, 014, 015); makalede
> ise 15 GeoTIFF görüntüden söz ediliyor. **009 ve 012** yayımlanan kümede var mı, varsa konumları
> nedir?
>
> **(c) Bölme yöntemi.** Makalede 1024 × 1024 yamaların 256 × 256 karolara ayrıldığı ve veri kümesinin
> 80:10:10 oranında üçe bölündüğü (Tablo III) yazıyor. Bölme doğrudan 256'lık karolar üzerinden mi
> yapıldı, yoksa aynı 1024'lük yamadan ya da aynı sahneden gelen karolar tek bir kümede kalacak
> biçimde gruplanarak mı? Bunu sormamızın nedeni şu: makalemizde değerlendirme protokolünün sonuçlara
> etkisini ayrı bir tabloyla inceliyoruz ve sizin protokolünüzü **doğru** tarif etmek istiyoruz.
> Şu an elimizde yalnız kendi çıkarımımız var, onun yerine sizin tarifinizi yazmayı tercih ederiz.
>
> Son olarak, konum kodları için ayrıca teşekkür ederiz — bu bizim için en büyük engeli kaldırdı.
> Kendi eğitim verimiz (KATE-PD/KATE-CD) ve değerlendirme sahnelerimiz Antakya/Defne, İslahiye ve
> Nurdağı'yı kapsıyor; yani 003, 004 ve 006–008 kodlu sahneler bizim alanlarımızla örtüşüyor. Dış
> sınama yapmadan önce örtüşen sahneleri dışarıda bırakacağız. Mümkünse **GeoTIFF sahne ayak izlerini
> (ya da karoların coğrafi dönüşüm bilgisini)** paylaşabilir misiniz? Üç haneli kod ilçe düzeyinde
> ayıklama sağlıyor, ayak izi ise piksel düzeyinde temiz bir ayrım sağlar.
>
> Çalışmamız yayına hazırlandığında ön baskıyı sizinle paylaşmaktan memnuniyet duyarız. Yardımınız ve
> açıklığınız için tekrar teşekkürler.
>
> Saygılarımızla,
> [İsim] — [KTO Karatay Üniversitesi]

---

## 1b. Danışman bilgilendirmesi (11 Ekim 2026)

> **GÜNCELLEME:** danışman, bilgilendirmeyi aldıktan sonra **yazarlara kendi adına
> göndereceği** metni istedi. Gönderilecek sürüm artık §1 değil, **§1c**'dir (danışman
> ağzından, Can Ekkazan + Karslıgil hocaya hitaplı). §1'deki öğrenci ağzından yazılmış
> taslak kayıt olarak bırakıldı.


**Durum:** yazışmanın arka planındaki planlama kullanıcıda olduğu için danışmana
WhatsApp'tan kısa bilgi verildi; danışman *"konuyu anlatan bir mail metni"* istedi ve
yazılı bilgilendirme gönderildi.

**İçerik başlıkları:** lisans durumu (iki bileşen, iki koşul) · Planet ağırlık kısıtı ve
iki yol (dış sınama / protokol reprodüksiyonu) · sahne konum kodları ve örtüşme uyarısı ·
"all rights reserved" karışıklığının düzeltilmesi · sitenin kapalı olması · makaleye etkisi
(şu an yok; veri kullanılırsa Veri Erişilebilirliği'ne Planet atfı eklenecek) · sıradaki adım.

**Dikkat edilen iki nokta:**
1. WhatsApp'ın kısa sürümünden çıkarılan iki konu (Planet ağırlık kısıtı, konum kodları)
   bu metne **geri konuldu** — ikisi de yayın planını bağlıyor, danışmanın bilmesi gerekiyor.
2. Son paragraf, yazarlara gidecek cevabın gönderilmeden önce danışmana gösterilmesini
   öneriyor; ilk e-postadaki karışıklık (J-139) bir ön okumayla yakalanabilirdi.

---

## 2. TUE-CD (Liu vd., IEEE TGRS 2024)

**Neden gerekli:** README'de lisans hiç belirtilmemiş.

**Konu:** License information request — TUE-CD dataset (IEEE TGRS 2024)

**Gövde:**

> Dear authors,
>
> We are preparing a manuscript on satellite-imagery damage segmentation
> for the 6 February 2023 Kahramanmaraş earthquakes and would like to use
> the TUE-CD dataset ("Building change detection in earthquake: A
> multiscale interaction network with offset calibration and a dataset,"
> IEEE TGRS, 2024, doi:10.1109/TGRS.2024.3437470) as an external test set.
>
> We could not find explicit licensing terms in the dataset's repository/
> README. Could you kindly let us know under what license TUE-CD is
> released, and whether it may be used for academic, non-commercial
> research and benchmarking purposes?
>
> Thank you for making this dataset available, and best regards,
> [İsim] — [KTO Karatay Üniversitesi]

---

**Not:** Her iki e-postada da `[İsim]` yerine gönderen adı/unvanı,
gerekirse ORCID veya kurumsal web sayfası eklenebilir. Yanıt geldiğinde
`DURUM.md` B-1 madde 4'ü kapatıp docx'teki ilgili sınırlılık notunu
güncellememiz gerekecek.
