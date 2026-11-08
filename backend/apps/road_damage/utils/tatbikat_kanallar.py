"""Tatbikatın yer seviyesi kanalları: kamera (YOLO) ve metin (BERTurk).

Uydu kanalı mahalleyi yukarıdan görür; bu iki kanal aynı mahalleye yerden
bakar. Üçü de CLAUDE.md kural 2'deki ortak sözleşmeye iner:

    (konum, hasar/aciliyet skoru, güven, zaman damgası, kaynak tipi)

NEYİN GERÇEK, NEYİN ÜRETİLDİĞİ (kural 1 — her sayının bir kaynağı vardır):

| Parça                          | Durum                                       |
|--------------------------------|---------------------------------------------|
| Fotoğraflar                    | GERÇEK — 6 Şubat 2023 depremi, çoğu Hatay.   |
|                                | Wikimedia Commons, Public domain (VOA) ve    |
|                                | CC BY-SA 4.0. Künye: `KUNYE.json`, SHA-256'lı|
| YOLO çıkarımı (çatlak + bina)   | GERÇEK — kendi modellerimiz, kendi ağırlık   |
|                                | dosyalarımız, koşuda hesaplanır              |
| İhbar metinleri                | ÜRETİLDİ — elle yazıldı, gerçek çağrı değil  |
| BERTurk sınıflandırma + NER     | GERÇEK — model metinlerin üstünde koşar      |
| Her ikisinin HARİTADAKİ KONUMU  | ÜRETİLDİ — tohumla, modelin hasarlı bulduğu  |
|                                | alanlardan seçilir                           |

Konum neden üretiliyor? İki sebep, ikisi de ölçülmüş:

1. Fotoğrafların EXIF konumu yok; Commons kayıtları da sokak düzeyinde konum
   vermiyor. Tatbikat alanı 500 m'lik bir mahalle, o yüzden "Hatay" bilgisi
   hiçbir işe yaramıyor.
2. Metin kanalındaki coğrafi kodlayıcı MAHALLE MERKEZİNE düşürüyor: "Defne
   Elektrik Mahallesi" → (36,17 / 36,13), tatbikat kutusunun merkezi ise
   (36,1977 / 36,1494) — yaklaşık 2 km ötede ve kutunun tamamen dışında.
   Yani modelin kendi coğrafi kodu bu ölçekte kullanılamıyor. Koşuda ikisi de
   saklanır: modelin çözdüğü nokta `modelKonumu`, haritaya konan nokta
   `lat/lon`; aradaki fark ölçülebilsin diye.

Her kayıt `sentetikKonum: True` taşır ve arayüz bunu yazar.
"""

from __future__ import annotations

import json
import math
import random
import time
import zlib
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]  # .../backend/apps
FOTO_DIZINI = KOK / "camera_detection" / "data" / "tatbikat_foto"
METIN_DOSYASI = KOK / "disaster_nlp" / "data" / "tatbikat_metinleri.json"

# Alan kimliğinden metin havuzuna. Alan katalogundaki `il` alanı Türkçe yazılı.
IL_ANAHTARI = {
    "hatay": "hatay",
    "gaziantep": "gaziantep",
    "kahramanmaraş": "kahramanmaras",
    "kahramanmaras": "kahramanmaras",
}


# --- ortak yerleştirme -----------------------------------------------------

def _hasar_konumlari(hasar_maskesi, bounds, sayi, tohum, en_az_piksel=40,
                     en_az_ayrim_m=25.0, kacinilacak=None):
    """Modelin hasarlı dediği yerlerden `sayi` kadar konum.

    Önce en büyük blobların ağırlık merkezleri alınır (büyük enkaz kütlesi her
    koşuda temsil edilsin), yetmezse HASARLI PİKSELLERDEN tohumla örneklenir.
    Nokta sayısını blob sayısıyla sınırlamamak için böyle: bir mahallede model
    çoğu zaman 3-5 blob buluyor, oysa kanal başına daha çok ihbar/fotoğraf
    yerleştirmek gerekiyor (ölçüldü: Defne/Elektrik koşusunda 9.474 hasarlı
    piksel ama yalnız 3 blob).

    Noktalar birbirine `en_az_ayrim_m` metreden yakın konmaz; aksi hâlde aynı
    enkaz yığınının üstünde üst üste binip haritada tek nokta gibi görünüyorlar.

    `tatbikat.afetzedeler` ile aynı ön-ek kararlılığı (J-81): aday listesi
    tohumla bir kez karılır, baştan alınır. Farklı kanallar farklı tohum
    kayması kullanır ki fotoğraf, ihbar ve afetzede üst üste binmesin.
    """
    import cv2
    import numpy as np

    maske = (np.asarray(hasar_maskesi) > 0).astype(np.uint8)
    h, w = maske.shape[:2]
    bati, guney, dogu, kuzey = bounds
    if not maske.any() or h == 0 or w == 0:
        return []

    # Piksel -> metre (kutunun ortasındaki enlemde).
    orta_lat = (guney + kuzey) / 2.0
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * max(0.05, math.cos(math.radians(orta_lat)))

    def cevir(cx, cy):
        return (round(kuzey - (cy / h) * (kuzey - guney), 6),
                round(bati + (cx / w) * (dogu - bati), 6))

    def uzak_mi(lat, lon, secilenler, esik):
        for s_lat, s_lon, _ in secilenler:
            dy = (lat - s_lat) * m_per_deg_lat
            dx = (lon - s_lon) * m_per_deg_lon
            if (dx * dx + dy * dy) ** 0.5 < esik:
                return False
        return True

    # Blob ETİKETLERİ konumun hangi enkaz kütlesine düştüğünü söylesin diye
    # tutulur; konumun kendisi blob merkezinden DEĞİL hasarlı piksellerden
    # gelir. Merkez kullanılsaydı üç kanal da (kamera, metin, afetzede) aynı
    # birkaç merkeze düşerdi -- ölçüldü: Defne/Elektrik'te üçü de aynı 3
    # noktaya biniyordu.
    _n, etiketler, istatistik, _merkezler = cv2.connectedComponentsWithStats(maske, connectivity=8)
    ys, xs = np.nonzero(maske)
    if len(xs) == 0:
        return []
    sira = list(range(len(xs)))
    random.Random(tohum).shuffle(sira)

    # Ayrım kademeli gevşer: mahalledeki enkaz 40 m çapında birkaç kütleyse
    # 25 m'lik ayrım hiçbir ikinci nokta bırakmıyor (ölçüldü). Önce geniş
    # ayrımı dene, dolmazsa daralt; en sonda ayrımsız doldur.
    # KANALLAR ARASI AYRIM (J-110): ayrım kuralı yalnız kanalın kendi içinde
    # çalışıyordu; kamera ve metin ayrı tohum kullandığı için iki ayrı kanalın
    # işareti 16 piksel arayla düşebiliyor ve haritada tek nokta gibi
    # görünüyordu. Önceki kanalın noktaları `kacinilacak` ile verilir: mesafe
    # kontrolüne girer ama sonuca dönmez.
    onceki = [(la, lo, 0) for la, lo in (kacinilacak or [])]
    secilen = []
    for esik in (en_az_ayrim_m, en_az_ayrim_m / 2.0, en_az_ayrim_m / 4.0, 0.0):
        if len(secilen) >= sayi:
            break
        for idx in sira:
            if len(secilen) >= sayi:
                break
            cx, cy = float(xs[idx]) + 0.5, float(ys[idx]) + 0.5
            lat, lon = cevir(cx, cy)
            if esik > 0 and not uzak_mi(lat, lon, secilen + onceki, esik):
                continue
            if esik == 0 and any(abs(lat - a) < 1e-9 and abs(lon - b) < 1e-9
                                 for a, b, _ in secilen):
                continue
            blob = int(etiketler[int(ys[idx]), int(xs[idx])])
            alan = int(istatistik[blob, cv2.CC_STAT_AREA]) if blob > 0 else 0
            if alan < en_az_piksel:
                continue
            secilen.append((lat, lon, alan))
    return secilen


def _alan_kaymasi(anahtar):
    """Alan adindan KARARLI bir tamsayi (surecten surece degismez)."""
    if not anahtar:
        return 0
    return zlib.crc32(str(anahtar).encode("utf-8")) % 10_000


def _kunye_oku():
    if not FOTO_DIZINI.exists():
        return []
    dosya = FOTO_DIZINI / "KUNYE.json"
    if not dosya.exists():
        return []
    try:
        return json.loads(dosya.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


# --- kamera kanalı ---------------------------------------------------------

def kamera_kanali(hasar_maskesi, bounds, sayi=4, tohum=42, model_tipi="hybrid",
                  alan_anahtari=""):
    """Gerçek deprem fotoğraflarında gerçek YOLO; konum tohumla üretilir.

    Dönüş: her fotoğraf için bir kayıt. `tespitler` modelin gerçekten bulduğu
    kutulardır; hiçbir şey bulamazsa kayıt yine döner ve `tespitSayisi: 0`
    yazar — "bulamadı" da bir ölçümdür (kural 8).
    """
    import cv2

    kunye = _kunye_oku()
    if not kunye:
        return {"kayitlar": [], "not": "Fotoğraf kataloğu yok (KUNYE.json bulunamadı)."}

    # Fotoğraf seçimi de tohuma bağlı: aynı tohum aynı tatbikat.
    # ALAN TOHUMA KARISIR: aksi hâlde üç alanın şeklinde de aynı dört fotoğraf
    # çıkıyordu. Alan adı kararlı bir sayıya çevrilir (`hash` süreç başına
    # tuzlanır, kullanılamaz); aynı alan + aynı tohum yine aynı sonucu verir.
    kayma = _alan_kaymasi(alan_anahtari)
    sirali = sorted(kunye, key=lambda k: k["dosya"])
    karisik = list(sirali)
    random.Random(tohum + 101 + kayma).shuffle(karisik)
    secilen = karisik[:sayi]

    konumlar = _hasar_konumlari(hasar_maskesi, bounds, len(secilen), tohum + 101 + kayma)
    if not konumlar:
        return {"kayitlar": [], "not": "Model hasarlı alan bulamadı; kamera kanalı yerleştirilemedi."}

    from uclar.kamera import yolo_tespit  # ağır import: yalnız koşuda

    kayitlar = []
    simdi = time.time()
    for sira, (k, (lat, lon, blob)) in enumerate(zip(secilen, konumlar), 1):
        yol = FOTO_DIZINI / k["dosya"]
        img = cv2.imread(str(yol))
        t0 = time.perf_counter()
        tespitler, modeller, kritik = yolo_tespit(img, model_tipi)
        gecen_ms = round((time.perf_counter() - t0) * 1000, 1)

        catlak = [d for d in tespitler if d["model"] == "catlak.pt"]
        bina = [d for d in tespitler if d["model"] == "bina.pt"]
        en_iyi = max(tespitler, key=lambda d: d["confidence"]) if tespitler else None
        guven = round(en_iyi["confidence"] / 100.0, 3) if en_iyi else 0.0
        # Skor = aciliyet. Ağır hasar ve kritik çatlak en üstte; hiçbir şey
        # bulunmadıysa 0 -- uydurulmuş bir taban değer konmaz.
        skor = 0.0
        if tespitler:
            agir = any("VeryHeavy" in d.get("sinif", "") for d in bina)
            orta = any("Moderate" in d.get("sinif", "") for d in bina)
            skor = 1.0 if agir else (0.7 if (orta or kritik) else 0.4)

        kayitlar.append({
            "id": f"kam{sira}",
            "lat": lat,
            "lon": lon,
            "skor": skor,
            "guven": guven,
            "zaman": simdi,
            "kaynak": "kamera",
            "etiket": en_iyi["label"] if en_iyi else "Tespit yok",
            # --- köken: neyin gerçek neyin üretilmiş olduğu kaydın içinde ---
            "sentetikKonum": True,
            "konumNotu": "konum üretildi — modelin hasarlı bulduğu blobdan, tohumla",
            "hasarBlobPiksel": blob,
            "foto": {
                "dosya": k["dosya"],
                "baslik": k["baslik"],
                "lisans": k["lisans"],
                "yazar": k["yazar"],
                "kaynakSayfa": k["kaynakSayfa"],
                "sha256": k["sha256"][:16],
                "gercek": True,
            },
            "tespitSayisi": len(tespitler),
            "catlakSayisi": len(catlak),
            "binaSayisi": len(bina),
            "kritik": bool(kritik),
            "cikarimMs": gecen_ms,
            "modeller": modeller,
            "tespitler": tespitler[:12],
        })
    return {
        "kayitlar": kayitlar,
        "fotoKaynagi": "Wikimedia Commons — 6 Şubat 2023 depremi, Public domain (VOA) ve CC BY-SA 4.0",
        "not": ("Fotoğraflar ve model çıktısı gerçek; haritadaki konumları üretildi. "
                "Katalogdaki fotoğrafların dokuzu Hatay/Antakya'dan, dördünün ili kaynakta "
                "belirtilmemiş (KUNYE.json); başka bir ildeki alana "
                "yerleştirildiklerinde aynı depremin fotoğrafıdırlar ama O MAHALLENİN "
                "fotoğrafı değildirler."),
        "ilUyarisi": True,
    }


# --- metin kanalı ----------------------------------------------------------

def metin_kanali(hasar_maskesi, bounds, il, sayi=5, tohum=42, cografi_kodla=False,
                 alan_anahtari="", kacinilacak=None):
    """Sentetik Türkçe ihbarlarda gerçek BERTurk; konum tohumla üretilir.

    `cografi_kodla=False` (varsayılan): NER'in bulduğu yer adı saklanır ama
    coğrafi kodlayıcı ÇAĞRILMAZ. Sebebi ikili: (a) ağ çağrısı istek yolunda
    saniyelere çıkıyor (ölçüldü: 18 metnin ikisi 3,3 ve 4,4 sn, medyan 47 ms),
    (b) sonucu mahalle merkezi olduğu için 500 m'lik tatbikat kutusunun dışına
    düşüyor. True verilirse model konumu da hesaplanır ve `modelKonumu` olarak
    kaydın içinde raporlanır; haritadaki nokta yine üretilmiş olandır.
    """
    if not METIN_DOSYASI.exists():
        return {"kayitlar": [], "not": "Metin havuzu yok (tatbikat_metinleri.json bulunamadı)."}
    try:
        havuz = json.loads(METIN_DOSYASI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"kayitlar": [], "not": "Metin havuzu okunamadı."}

    anahtar = IL_ANAHTARI.get((il or "").strip().lower(), "hatay")
    liste = havuz.get("iller", {}).get(anahtar) or havuz.get("iller", {}).get("hatay") or []
    if not liste:
        return {"kayitlar": [], "not": f"'{il}' için sentetik metin yok."}

    kayma = _alan_kaymasi(alan_anahtari)
    karisik = list(liste)
    random.Random(tohum + 202 + kayma).shuffle(karisik)
    secilen = karisik[:sayi]

    konumlar = _hasar_konumlari(hasar_maskesi, bounds, len(secilen), tohum + 202 + kayma,
                                kacinilacak=kacinilacak)
    if not konumlar:
        return {"kayitlar": [], "not": "Model hasarlı alan bulamadı; metin kanalı yerleştirilemedi."}

    import sys
    nlp_kok = str(KOK / "disaster_nlp")
    if nlp_kok not in sys.path:
        sys.path.insert(0, nlp_kok)
    from src.classification import DisasterClassifier
    from src.ner_extraction import LocationExtractor
    from src.preprocessing import clean_text

    siniflandirici = DisasterClassifier()
    ner = LocationExtractor()

    # Aciliyet eşlemesi pipeline.py ile AYNI -- iki yerde iki farklı kural
    # olmasın diye buraya kopyalanmadı, oradaki sıra birebir yansıtıldı.
    ACILIYET = {
        "Enkaz Bildirimi": 5,
        "Acil Yardım İhtiyacı": 4,
        "Yol Kapanma Bilgisi / Lojistik": 3,
        "Lojistik İhtiyaç Bildirimi": 2,
    }

    kayitlar = []
    simdi = time.time()
    for sira, (kayit, (lat, lon, blob)) in enumerate(zip(secilen, konumlar), 1):
        ham = kayit["metin"]
        t0 = time.perf_counter()
        temiz = clean_text(ham, lowercase=False)
        kategori, guven = siniflandirici.classify(temiz)
        elendi = kategori == "Alakasız"
        adaylar, model_konumu, konum_metni = [], None, None
        if not elendi:
            varliklar = ner.extract_entities(temiz)
            adaylar = ner.extract_location_candidates(temiz, varliklar)
            if cografi_kodla and adaylar:
                model_konumu, konum_metni = ner.get_coordinates(adaylar, raw_text=temiz)
        gecen_ms = round((time.perf_counter() - t0) * 1000, 1)

        aciliyet = ACILIYET.get(kategori, 1)
        kayitlar.append({
            "id": f"met{sira}",
            "lat": lat,
            "lon": lon,
            "skor": round(aciliyet / 5.0, 3),
            "guven": round(float(guven), 3),
            "zaman": simdi,
            "kaynak": "metin",
            "etiket": kategori,
            # --- köken ---
            "sentetikMetin": True,
            "sentetikKonum": True,
            "konumNotu": "metin de konum da üretildi — model çıktısı gerçektir",
            "metin": ham,
            "beklenen": kayit.get("beklenen"),
            "ortusuyor": kategori == kayit.get("beklenen"),
            "elendi": elendi,
            "aciliyet": aciliyet,
            "hasarBlobPiksel": blob,
            "yerAdaylari": adaylar[:4],
            "modelKonumu": model_konumu,
            "modelKonumMetni": konum_metni,
            "cikarimMs": gecen_ms,
        })
    return {
        "kayitlar": kayitlar,
        "not": ("Metinler uydurmadır, model çıktısı gerçektir; haritadaki "
                "konumları üretildi. 'beklenen' yazarın niyetidir, doğru cevap değil."),
    }
