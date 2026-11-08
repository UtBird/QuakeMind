# Yapılacaklar: Furkan'a devir (28 Eylül 2026, 23:20)

> **Güncelleme (29 Eylül):** Bölüm 2 ve 3 tamamlandı. Oturum 5 ve 6 bitti, sonuçları alındı ve §4.4 üç
> tohumla kesinleştirildi (`makale/analiz_arsivi/revize17.py`). Görülmemiş ilde IoU_hasar üç tohum
> ortalamasında 0,04–0,08 düşük; düşüş 12 eşleşmenin 11'inde. Makalede ölçülebilir eksik kalmadı. Senden
> beklenen yalnız Bölüm 5'teki karar ve insan işleri.
> **Güncel kalan işler listesi:** `makale/KALAN_ISLER_2026-09-27.md` → "KALAN İŞLER (29 Eylül)". Bölüm 5
> onun özetidir. `makale/arsiv/` yedekleri 29 Eylül'de temizlendi; betiği yeniden koşmak için güncel docx'i
> yedek olarak kopyala.

Bu dosya, Utku'nun Claude Code oturumunda yarıda kalan işin devridir. Oturum burada durduruldu.
Aşağıdaki sırayla ilerlenirse kaldığı yerden devam edilir. Her sayının kaynağı dosya yoluyla verildi.
Kural gereği hiçbir sayı kestirimle doldurulmaz (CLAUDE.md §1, §8).

**Güncel makale:** `makale/QuakeMind_Makale_Taslak_2026-09-16_sekillieklendi_v3_LOCAL_2026-09-21.docx`

- 72 sayfa, 23 tablo, 23 şekil, 68 kaynak, 17 denklem.
- Atıf ve sayfa düzeni denetimi temiz.
- Vurgusuz gönderim kopyası: `makale/QuakeMind_Makale_GONDERIM_vurgusuz.docx`.

---

## 0. Şu anki durum, tek bakışta

| İş | Durum |
|---|---|
| Kapanma yer gerçeği insan etiketiyle (§4.3, Tablo 13; revize14) | ✅ bitti |
| Bölgeler arası genelleme, tek tohum (§4.4, yeni Tablo 14; revize15) | ✅ makalede |
| Çoklu tohum, üç mimari × üç tohum (Tablo 12 dipnotu, sınırlılık o; revize16) | ✅ makalede |
| Genellemenin çoklu tohumla yinelenmesi (Kaggle oturum 5, 6) | ✅ bitti, §4.4 ve Tablo 14 üç tohumlu (revize17, 29 Eylül) |
| Commit / push | ✅ 28 Eylül işleri `makale` dalında (68a1cf3); 29 Eylül (revize17) işleri ayrıca push'lanacak |

---

## 1. Önce: dosyalar sana nasıl ulaşır

Bu oturumun bütün değişiklikleri Utku'nun makinesinde, `makale` dalında, **commit'lenmemiş** duruyor.
Sana ulaşmaları için Utku'nun push etmesi gerekiyor. Önerilen commit grupları:

1. `docs(makale)`: makale docx, gönderim kopyası, `makale/KALAN_ISLER_2026-09-27.md`, bu dosya.
2. `feat(ölçüm)`: kapanma için insan etiketi ve uyum.
   - `backend/benchmark/kapanma_yer_gercegi/etiketler_insan_1.json`
   - `backend/benchmark/kapanma_yer_gercegi/uyum.json`
   - `backend/benchmark/kapanma_yer_gercegi/insan_kiti/*`
3. `feat(metin)`: `backend/araclar_metin_maskele.py` ve `backend/benchmark/reports/metin_maskeleme_raporu.json` (yalnız sayı içerir).
4. `feat(gpu)`: bütün `makale/analiz_arsivi/kaggle/` (defterler, `gunluk_ayikla.py`, `sonuclar/`) ve `makale/analiz_arsivi/GPU_IS_PAKETI_2026-09-28.md`.
5. `feat(şekil)`:
   - `backend/araclar_makale_sekilleri.py`
   - `backend/araclar_makale_semalar.py`
   - üç png: `sekil_protokol`, `sekil_kesif_kazanc`, `sekil_model_secimi`
6. `docs(makale)`: betikler (`makale/analiz_arsivi/revize13–16.py`, `yardimci.py`, `cikar.py`, `atif.py`) ve `EKSIKLER_VE_SORUNLAR.md`.

**Depoya girmeyenler:**
- `makale/arsiv/*_pre_revize*.docx` yedekleri (~26 MB/adet), yalnız Utku'nun makinesinde. Eski sürümler git geçmişinde var.
- Kişisel veri içeren maskeli metin kopyası `C:/Users/utkuc/quakemind_ozel/` (depo dışı, bilerek).

---

## 2. Koşan Kaggle işlerini toplamak

Hesap: `furkanemrence` (senin hesabın). İki defter koşuyor. Tarayıcıyı kapatsan da sürer.

| Oturum | Kaggle adresi | Koşulan deneyler | Tahmini bitiş |
|---|---|---|---|
| 5 | `kaggle.com/code/furkanemrence/03-kaggle-protokol-oturum5-unet-haric-tohumlar` | U-Net MiT-B4 · Hatay hariç · tohum 7, 2026 → Kahramanmaraş hariç · tohum 7, 2026 | ~02:40 |
| 6 | `kaggle.com/code/furkanemrence/03-kaggle-protokol-oturum6-segformer-haric-tohumla` (adres Kaggle'ca kısaltıldı) | SegFormer-B4 · aynı dört deney | ~02:35 |

Adımlar (her oturum için):

1. Defter sayfası → **Logs**. "Successfully ran" ve günlükte `KUYRUK BİTTİ` olmalı; `HATA` ya da `Traceback` olmamalı.
   - Koşarken günlük "Version History → ⋯ → View logs" yolundan da görülür.
   - O menüdeki **Cancel**'a basma.
2. **Download Logs**. İnen dosya `indir.txt` adıyla Downloads'a düşer. Çıktının tamamını (yüzlerce MB) indirme; defter her sonucu günlüğe de basıyor.
3. Dosyayı yerleştir ve sonuçları çıkar:

   ```
   mkdir makale/analiz_arsivi/kaggle/sonuclar/oturum5_unet_haric_tohumlar
   move indir.txt makale/analiz_arsivi/kaggle/sonuclar/oturum5_unet_haric_tohumlar/gunluk.txt
   python makale/analiz_arsivi/kaggle/gunluk_ayikla.py <o klasör>/gunluk.txt <o klasör>
   ```

4. Beklenen çıktı, oturum başına dört dosya:
   - `P2_haric_hatay__unet_mitb4__tohum_7.json`, `…tohum_2026.json`
   - `P2_haric_maras__unet_mitb4__tohum_7.json`, `…tohum_2026.json`

   Oturum 6'da `segformer_mitb4` adlarıyla. Her birinde `ayarlar.artirim_tohumlu == true`, `ayarlar.girdi == "sonrasi"` ve doğru `bolge_egitimi` olmalı.

---

## 3. §4.4'ü çoklu tohumla kesinleştirmek (revize17, yazılacak)

### Şu an makalede ne yazıyor

- Tablo 14 tek tohumlu (42).
- Metin şunu söylüyor: "Görülmemiş ilde IoU_hasar 0,05–0,10 düşük. Tek tohumla bu, tohum oynaması mertebesinde. Tutarlı olan örüntü: dört koşunun üçünde yalnız çıkarılan il düşüyor. Kesinleştirmek için çoklu tohum gerekir."
- ÖZ ve Abstract'ta "(tek tohum; tohum oynaması mertebesinde)" notu var.

### Karşılaştırma tabanı: birleşik eğitim, üç tohum

Aynı kod ve ayar, `artirim_tohumlu=True`. Sınama IoU_hasar; Hatay 34, Kahramanmaraş 32, tümü 91 karo.

| Model | İl | Tohum 42 | Tohum 7 | Tohum 2026 | Ortalama ± SS |
|---|---|---|---|---|---|
| U-Net | Hatay | 0,3658 | 0,3779 | 0,3272 | 0,357 ± 0,027 |
| U-Net | Kahramanmaraş | 0,4559 | 0,4263 | 0,3561 | 0,413 ± 0,051 |
| SegFormer-B4 | Hatay | 0,3867 | 0,3818 | 0,3172 | 0,362 ± 0,039 |
| SegFormer-B4 | Kahramanmaraş | 0,3987 | 0,4286 | 0,3860 | 0,404 ± 0,022 |

Kaynak dosyalar (`makale/analiz_arsivi/kaggle/sonuclar/`):
- U-Net: `birlesik_P2/unet_mitb4__tohum_42.json`, `oturum1_coklu_tohum/P2__unet_mitb4__tohum_{7,2026}.json`.
- SegFormer: `birlesik_P2/segformer_mitb4__tohum_42__2.json` (Tablo 12'deki 0,407), `oturum4_segformer_tohum7/P2__segformer_mitb4__tohum_7.json`, `oturum1_coklu_tohum/P2__segformer_mitb4__tohum_2026.json`.

⚠ Eski `segformer_mitb4__tohum_42.json` ve `__tohum_7.json` eski kodla koşmuş (artırım tohumsuz, EKSIKLER J-130). Kullanma.

**İl dışarıda bırakma, tohum 42 (zaten var):** `sonuclar/oturum2_bolgeler_arasi/`, `sonuclar/oturum3_segformer_haric_maras/`

| Model | Çıkarılan il | Hatay | Kahramanmaraş |
|---|---|---|---|
| U-Net | Hatay | 0,3145 | 0,4013 |
| U-Net | Kahramanmaraş | 0,3635 | 0,3815 |
| SegFormer-B4 | Hatay | 0,2892 | 0,3947 |
| SegFormer-B4 | Kahramanmaraş | 0,3878 | 0,3220 |

### Yapılacak

1. Oturum 5 ve 6 sonuçlarıyla her (model, çıkarılan il) için üç tohumun ortalama ± SS'sini hesapla, iki il için ayrı ayrı.
2. Kaybı hesapla: birleşik üç tohum ortalaması − il dışarıda üç tohum ortalaması, görülmemiş ilde.
   - Kayıp SS'lerin toplamını açıkça aşıyorsa, ya da tohum aralıkları örtüşmüyorsa, "kayıp ölçüldü" diye yaz.
   - Aşmıyorsa "tohum oynaması içinde" diye yaz.
   - Karar dilini ölçülen sayıya göre kur. `revize16.py`'deki `ayrik / her_tohumda` mantığı örnek.
3. Tablo 14'ü ortalama ± SS'li yeniden kur. Satırlar: model × {birleşik, Hatay hariç, Kahramanmaraş hariç}. Sütunlar: Hatay, Kahramanmaraş, Tüm sınama. Kalın hücre görülmemiş il. Başlıktaki "tohum 42" → "üç tohum (42, 7, 2026), ortalama ± SS".
4. Metinde değişecek yerler. Hepsi `revize15.py`'nin yazdığı cümleler; o betiği temel al:
   - §4.4'te "Eğitimde görülmemiş ilde IoU_hasar birleşik eğitime göre …" paragrafı ve "Sınırlar: deney tek tohumludur …" paragrafı.
   - ÖZ ve Abstract: "… görülmemiş ilde IoU_hasar 0,05–0,10 düşmüştür (tek tohum; tohum oynaması mertebesinde)."
   - Tablo 23'ün "Bölgeler arası genelleme" satırı (dördüncü hücre).
   - "Ölçülen ve ölçülmeyenlerin ayrımı" paragrafı: "Bölüm 4.4'teki genelleme deneyi iki mimaride ve tek tohumla koşulmuştur."
   - Tablo 23'ün altındaki paragraf: "… bölgeler arası genelleme iki mimaride tek tohumla ölçülmüştür."
   - §6: "… bölgeler arası genelleme ise iki mimaride ve tek tohumla ölçülebilmiştir;"
5. Denetim:
   - `python makale/analiz_arsivi/cikar.py <docx> makale.txt`, sonra `python makale/analiz_arsivi/atif.py`. Bütün tablo, şekil ve kaynaklar 1..N sıralı ve atıflı olmalı.
   - PDF'e çevir: Word COM, PowerShell'de `ExportAsFixedFormat(<pdf>, 17)`.
   - Sayfa düzenini PyMuPDF ile tara: tablo başlığı sayfa sonunda kalmasın. PyMuPDF `backend/venv` içinde.
6. Gönderim kopyasını yenile. `revize13.py`'nin sonundaki "vurgu kaldır" bloğu bunu yapıyor.
7. `EKSIKLER_VE_SORUNLAR.md`'ye bir satır, `makale/KALAN_ISLER_2026-09-27.md`'ye tur özeti ekle.

### Betiklerle ilgili uyarılar

- `makale/analiz_arsivi/revize*.py` betiklerinde `sys.path` ve `SRC/DST` Utku'nun geçici klasörüne göre yazılı.
  - `sys.path`'i `makale/analiz_arsivi`'ye çevir.
  - `SRC` yedekten başlar ve yedekler yalnız Utku'da. Sende yoksa güncel docx'in bir kopyasını yedek al, revize17'yi ondan başlat. revize15'i yeniden koşma.
- Her revize betiği işe yedek alarak başlar: `makale/arsiv/QuakeMind_Makale_YEDEK_pre_revize17_<tarih>.docx`.
- `yardimci.py` → `Duzenleyici.degistir` biçimi korur. 28 Eylül'de bir hata düzeltildi: birden çok run'a yayılan değişimde kalan metin artık kalın başlık run'ına taşınmıyor.
  - Yine de değişecek metni, kalın bir başlık run'ından ("Gözlemler.", "Tablo N.") başlatmamaya dikkat et.
- Tablo numarası eklemek, sonraki bütün tabloları kaydırır. `revize15.py`'nin 1. bölümü bunu Türkçe ekleriyle birlikte yapıyor. Şekillerin içine gömülü tablo numaraları da var: Şekil 6 (`araclar_makale_semalar.py`) ve Şekil 12 (`araclar_makale_sekilleri.py`).

---

## 4. Kaggle çalışma notları (tuzaklar)

- **En çok iki GPU koşusu aynı anda.** Üçüncüsü "Maximum batch GPU session count of 2 reached" der ve sürüm oluşmaz.
- **Yükleme:**
  - Kaggle → Code → New Notebook'un yanındaki ok → **Import Notebook** → dosya.
  - **Advanced Settings** → "Run with GPU for this session" → Save → Import.
  - Bu, doğrudan GPU'lu "Save & Run All" başlatır.
- **Veri paketinin kendiliğinden bağlanması** için defterin `metadata.kaggle` alanında şu olmalı (oturum 3–6 defterlerinde var):

  ```
  {"accelerator": "nvidiaTeslaT4", "dataSources": [{"sourceType": "datasetVersion", "sourceId": 19876899}], "isInternetEnabled": true}
  ```

- **Kuyruk tuzağı (J-129):** Defterin 9. hücresi (kuyruk), 0. hücreyi değil, deftere gömülü eski ayarları çalıştırıyor. O ayarlarda `MODEL_ADI="unet_mitb4"`, `TOHUMLAR=[42]`, `BOLGE_EGITIMI=None`, `AGIRLIK_SAKLA=True`, `GORSEL=True` var.
  - Kuyruk öğesine bütün farklı ayarları açık yaz, ya da tek deneylik defter kullan.
  - Kalıcı çözüm üreteçte (`QuakeMind_veri/araclar/defter_dokuz_model.py`) yapılmalı.
- **Hesaptaki artıklar:**
  - İlk denemeden kalan boş taslak `notebook2195d8897c` (silinebilir).
  - Her defterin kod koşmadan kaydolmuş "sürüm 1"i (zararsız).
- **Kota:** Oturum 5–6 bitince bu hafta ~21 GPU saati kullanılmış olacak (30 saatten).

---

## 5. Makalede kalan öteki işler (ölçüm değil, karar ya da insan işi)

| # | İş | Kimde |
|---|---|---|
| 1 | Metin kümesinde kişisel veri (J-127): paylaşım politikası, etik kurul / KVKK. Maskeli kopya hazır. | ekip kararı |
| 2 | ORCID numaraları ve sorumlu yazar (başlıkta yer tutucu) | yazarlar |
| 3 | Hedef dergi seçimi. Ardından kaynak stili ve sayfa sınırına göre kısaltma (72 sayfa uzun). | ekip kararı |
| 4 | GitHub deposunun görünürlüğü (Veri Erişilebilirliği'ndeki bağlantı özel depoda açılmıyor) | depo sahibi |
| 5 | Roboflow API anahtarının iptali ve yenilenmesi (git geçmişinde açık) | Roboflow hesabı sahibi |
| 6 | **Önerilir:** ikinci insan etiketleyici. Başka bir yazar aynı 33 kesiti etiketlesin (~20 dk), insanlar arası κ ölçülsün. Kit: `backend/benchmark/kapanma_yer_gercegi/insan_kiti/etiketle.html`; ölçüm: `araclar_kapanma_uyum.py`. | yazarlardan biri (Utku değil) |
| 7 | İsteğe bağlı: i7 makinesinde `pip freeze` (Tablo 11 sürümleri, J-118) ve `python araclar_kanal_olc.py` (Tablo 15 metin gecikmesi) | i7 makinesi |
| 8 | YOLO için bağımsız saha sınama kümesi (etiketli fotoğraf). Makalede şimdilik eğitim doğrulama değeri var; iyimser olduğu yazılı. | insan işi |
| 9 | Son adım: yazar gözüyle bütün makalenin içerik okuması | yazarlar |

Makalede açıkça **sınırlılık** olarak duranlar (eksik değil):
- Yol hasarı için çok mimarili kıyas yok (etiketli küme yok).
- Metin modeli yol kapanmasını tanımıyor (J-123).
- Üretimdeki metin ağırlığında sınama sızıntısı var (J-128).
- Veri miktarıyla eşlenmiş genelleme kıyası yok.
- Tatbikat modelleri tek eğitim tohumundan.

---

## 6. Bu oturumda ne yapıldı (bağlam)

- **revize14:** Kapanma yer gerçeği insan etiketiyle.
  - Kesinlik 4/5, duyarlılık ≈%9; Claude ikinci görüş, κ = 0,13.
  - "Model yanlış alarm üretmiyor" cümlesi düştü, yerine "az yanlış alarm" geldi (J-126 kapandı).
- **revize15:**
  - §4.4 ve yeni Tablo 14 (il dışarıda bırakma, tek tohum).
  - Eski Tablo 14–22 → 15–23; Türkçe ekler ile Şekil 6 ve 12 güncellendi.
  - Tablo 14'ün SegFormer tabanı Tablo 12 ile aynı kayda (0,407) bağlandı.
- **revize16:** Çoklu tohum.

  | Model | Ortalama ± SS |
  |---|---|
  | U-Net | 0,398 ± 0,043 |
  | UPerNet | 0,392 ± 0,034 |
  | SegFormer-B4 | 0,412 ± 0,024 |

  - Sıralama tohuma göre değişiyor.
  - MiT-B4 içinde üstünlük iddiası kaldırıldı; "kodlayıcı belirleyici" iddiası ön bulguya indi.
  - Yedi yerde "bölütleme başarımını artırmak kazancı orantılı artırmıyor" yerine "sınama IoU farkları kazancı öngörmüyor" geldi.
  - Tatbikattaki U-Net etiketi "En iyi" → "Büyük".
  - Yeni sınırlılık: tatbikat modelleri tek eğitim tohumundan.
  - Ayrıntı: EKSIKLER J-131.
- **Yeni bulgular (EKSIKLER):**
  - J-129: Kaggle kuyruğu.
  - J-130: Eski ±0,02 bandı iki kod sürümünü karşılaştırıyordu.
  - J-131: Tohum oynaması büyük.
- **Bütün tur özeti:** `makale/KALAN_ISLER_2026-09-27.md` (8. tur). GPU ayrıntısı: `makale/analiz_arsivi/GPU_IS_PAKETI_2026-09-28.md`.

---

## 7. Yeni bir Claude Code oturumunda devam etmek için

Oturumu depo kökünde aç ve şunu söyle:

> "makale/YAPILACAKLAR_FURKAN_2026-09-28.md'yi oku; Bölüm 2'den devam et."

Claude'un okuması gerekenler:
1. `CLAUDE.md`: kurallar; özellikle §1 veri dürüstlüğü ve §9 commit/push yalnız açık izinle.
2. Bu dosya.
3. `makale/KALAN_ISLER_2026-09-27.md`.
4. `EKSIKLER_VE_SORUNLAR.md`'nin son satırları (J-126…J-131).
5. `makale/analiz_arsivi/GPU_IS_PAKETI_2026-09-28.md`.

Bu oturumun tam dökümü yalnız Utku'nun makinesinde:
`C:\Users\utkuc\.claude\projects\D--quakemind-final-QuakeMind\4779ac37-74b5-4aeb-8690-74d7792eedc5.jsonl`.
Devam için gerekmez; bu dosya kendi başına yeterli olacak şekilde yazıldı.
