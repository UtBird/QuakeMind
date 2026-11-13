# Makale Künye Bilgileri — Kullanıcıdan Alınan Veriler

**Alındığı tarih:** 15 Eylül 2026
**Amaç:** `[EKLENECEK]` ve `[ÖLÇÜLECEK]` alanlarının doldurulması için kullanıcının
verdiği bilgiler. Makaleye işlenirken buradan okunur.

---

## Eğitim ortamı (Tablo 11 — M-16, M-22)

| Alan | Değer |
|---|---|
| Ortam | Google Colab |
| GPU | **NVIDIA Tesla T4** |
| Kullanım | Model eğitimi (bölütleme mimarileri, SegFormer, YOLO) |

## Senaryo koşum ortamı (Tablo 11 — M-22)

| Alan | Değer |
|---|---|
| Makine | Kullanıcının kişisel bilgisayarı (yerel) |
| İşlemci | **Intel Core i7-12700H (12. nesil)** — 16 Eylül 2026'da makineden ölçüldü; kullanıcı "14. nesil" bildirmişti |
| Bellek | **16 GB RAM** (Windows'ta 15,7 GB görünür) |
| Depolama | **512 GB SSD** |
| Grafik | **Intel Iris Xe** (tümleşik) |
| GPU hızlandırma | Yok — senaryo CPU üzerinde koşuyor |

> **Not (kullanıcı beyanı, 15 Eylül 2026):** Senaryo güncellenecek ve yeniden
> koşulacaktır. Şu anki hâliyle yazılacak; koşum yenilendiğinde bu alanlar ve
> bağlı tüm sayılar (206,6 dk · 1 641,0 dk · Tablo 16–19) güncellenecektir.

---

## Yazarlar (M-45, M-46)

| # | Ad | Not |
|---|---|---|
| 1 | **Furkan Emre İnce** | KTO Karatay Üniversitesi, Bilgisayar Mühendisliği Bölümü, Konya |
| 2 | **Utku Ceylan** | KTO Karatay Üniversitesi, Bilgisayar Mühendisliği Bölümü, Konya |
| 3 | **Dr. Öğr. Üyesi Esra Uray** | KTO Karatay Üniversitesi, İnşaat Mühendisliği Bölümü, Konya |

> Görüntü işleme alanından ek yazarlar sonra eklenecektir; yazar sırası ve CRediT
> katkı beyanı o aşamada yeniden düzenlenecektir.


## CRediT katkı beyanı (M-46) — kullanıcı beyanı, 15 Eylül 2026

| CRediT rolü | Türkçe karşılığı | Yazar(lar) |
|---|---|---|
| Conceptualization | Kavramsallaştırma | Furkan Emre İnce, Utku Ceylan |
| Methodology | Yöntem | Furkan Emre İnce, Utku Ceylan |
| Software | Yazılım | Furkan Emre İnce, Utku Ceylan |
| Validation | Doğrulama | Furkan Emre İnce, Utku Ceylan |
| Formal analysis | Biçimsel çözümleme | Furkan Emre İnce, Utku Ceylan |
| Investigation | Araştırma | Furkan Emre İnce, Utku Ceylan |
| Data curation | Veri düzenleme | Furkan Emre İnce, Utku Ceylan |
| Writing – original draft | Özgün taslağın yazımı | Furkan Emre İnce, Utku Ceylan |
| Writing – review & editing | Gözden geçirme ve düzenleme | Furkan Emre İnce, Utku Ceylan |
| Visualization | Görselleştirme | Furkan Emre İnce, Utku Ceylan |
| **Supervision** | **Denetim / danışmanlık** | **Esra Uray** |
| **Funding acquisition** | **Finansman temini** | **Esra Uray** |
| Project administration | Proje yönetimi | Furkan Emre İnce, Utku Ceylan |
| Resources | Kaynaklar | Furkan Emre İnce, Utku Ceylan |

> Kullanıcı beyanı: *"Supervision ve Funding acquisition danışman Esra Uray;
> gerisini Utku ve Furkan ortak yaptık, ikimizin ismini de yaz."*
> Görüntü işleme uzmanı hocalar eklendiğinde bu tablo yeniden düzenlenecektir.
>
> **Düzeltme (16 Eylül 2026):** ilk sürümde "Project administration" ve "Writing – review & editing" rolleri Esra Uray'a da yazılmıştı; bu, kullanıcının talimatını aşıyordu. Talimata birebir uyularak bu iki rol Furkan Emre İnce ve Utku Ceylan'a verildi. Makaleye bu hâli işlendi.

---

## Kapsam kararları

| Konu | Karar | Tarih |
|---|---|---|
| **Hedef dergi** (M-42) | **Belirlenmedi.** Elimizdeki her şey tüm detayıyla yazılacak; dergi seçildikten sonra biçim revizyonu yapılacak. Öz kısaltma işi de o aşamaya bırakıldı. | 15 Eylül 2026 |
| **Yol hasarı etiketli kümesi** (M-21) | **Belirlenmedi.** Konuşulacak: kendi kümemizi mi etiketleyeceğiz, CAU-RoadDamage'ı harici test kümesi mi yapacağız, yoksa yol eksenini gelecek çalışmaya mı bırakacağız. | 15 Eylül 2026 |
| Çalışma yöntemi | **Adım adım, madde madde.** Aynı anda birden çok maddeye dağılmadan ilerlenecek. | 15 Eylül 2026 |
| İnceleme kapsamı | Hem dal sürümündeki hem kullanıcıdaki listede yer alan **tüm** maddelere bakılacak; hiçbiri atlanmayacak. | 15 Eylül 2026 |

---

## Belge sürümü uyarısı

15 Eylül 2026'da kullanıcının gönderdiği `MAKALE_TASLAK_TR (1) (1).docx`
(1 368 221 bayt, SHA-1 `e5378c9b3f899cf5`), depodaki
`makale/MAKALE_TASLAK_TR (1) - YEDEK_grup1_oncesi.docx` yedeğiyle **bayt bayt
aynıdır** — yani birkaç düzeltme turu öncesine ait eski bir kopyadır.

**Geçerli sürüm:** `QuakeMind_makale/makale/MAKALE_TASLAK_TR (1).docx`
(1 614 150 bayt) — 17 gerçek Word denklemi, 315 çapraz başvuru alanı, 24 tablo.

Tüm düzenlemeler **geçerli sürüm** üzerinde yapılmalıdır.

---

## Yazılım sürümleri (arka uç `backend/venv`, 16 Eylül 2026'da okundu)

Python 3.12.6 · PyTorch 2.13.0 (yalnız CPU, CUDA yok) · Ultralytics 8.4.116 · Transformers 5.14.1 ·
NetworkX 3.6.1 · OSMnx 2.1.1 · pyrosm 0.13.1 · FastAPI 0.141.1 · uvicorn 0.52.1 ·
segmentation-models-pytorch 0.5.0 · CatBoost 1.2.10 · Shapely 2.1.2 · zeyrek 0.1.3.
İşletim sistemi: Windows 11 Home Single Language, 64 bit, 10.0.26200.

> Sistem Python'u (3.10.11) farklı sürümler içerir ve arka uç onunla çalışmaz (`pyrosm` yok).
> Arka uç `.bat` dosyalarında `venv/Scripts/python.exe` ile başlatılıyor.

---

## Künye bilgileri (16 Eylül 2026, ikinci tur)

| Bilgi | Makaledeki yeri | Durum |
|---|---|---|
| TÜBİTAK 2209-A başvuru numarası | Teşekkür | **1919B012547445** — işlendi ("başvuru numaralı proje") |
| Depo adresi | Veri Erişilebilirliği | **https://github.com/UtBird/QuakeMind** — işlendi. Depo şu an **özel**; yayından önce açılmalı |
| Kurum | Başlık altı | **KTO Karatay Üniversitesi** — Bilgisayar Müh. (Furkan, Utku), İnşaat Müh. (Esra Uray) — işlendi |
| ORCID numaraları | Başlık altı | **Bekleniyor** — kullanıcı ORCID'i bilmiyordu, açıklandı |
| Sorumlu yazar ve e-postası | Başlık altı | **Bekleniyor** |
| Özel Türkçe metin kümesinin erişim politikası (M-47) | Veri Erişilebilirliği | **Sonra konuşulacak** (kullanıcı kararı) |

## Drone görüntüleri (M-83, OpenAerialMap meta verisinden doğrulandı)

| Sahne | Görüntü kimliği | Sağlayıcı | Çekim | Çözünürlük | Lisans |
|---|---|---|---|---|---|
| H-D1 Defne – Elektrik Mah. | 63eb78a0ca43600005f4d920 | Help.NGO | 2023-02-09, İHA | 3,41 cm/px | CC BY 4.0 |
| H-D2 Defne – Turunçlu/Akdeniz/Armutlu | 63eb829fca43600005f4d927 | Help.NGO, Portugese GRU | 2023-02-09, İHA | 3,86 cm/px | CC BY 4.0 |
| K-D1 12 Şubat Stadyumu, Kahramanmaraş | 63eb7f38ca43600005f4d924 | Help.NGO | 2023-02-09, İHA | 3,76 cm/px | CC BY 4.0 |
