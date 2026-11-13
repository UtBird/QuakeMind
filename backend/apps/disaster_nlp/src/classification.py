import os
os.environ["HF_HUB_DISABLE_HTTP2"] = "1"

from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from transformers import pipeline


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL_MODEL = BASE_DIR / "models" / "2kveri"
REMOTE_MODEL_ENV = "DISASTER_MODEL_NAME"
DEFAULT_HF_REPO = "Utbird/EqTwitterTr"
REQUIRED_MODEL_FILES = (
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
)

# P-5 standardında göstermek istediğimiz üst kategoriler
CATEGORY_MAPPING = {
    "Alakasiz": "Alakasız",
    "Arama Ekipmani": "Acil Yardım İhtiyacı",
    "Barinma": "Lojistik İhtiyaç Bildirimi",
    "Cenaze": "Acil Yardım İhtiyacı",
    "Elektrik Kaynagi": "Acil Yardım İhtiyacı",
    "Enkaz Kaldirma": "Enkaz Bildirimi",
    "Giysi": "Lojistik İhtiyaç Bildirimi",
    "Isinma": "Acil Yardım İhtiyacı",
    "Lojistik": "Yol Kapanma Bilgisi / Lojistik",
    "Saglik": "Acil Yardım İhtiyacı",
    "Su": "Acil Yardım İhtiyacı",
    "Tuvalet": "Acil Yardım İhtiyacı",
    "Yemek": "Acil Yardım İhtiyacı",
}

# E-04 duzeltmesi (Bolum 3.6): eski kural yalniz yol/ulasim terimleri icin bir
# "kurtarma" (rescue) mekanizmasina sahipti -- bu asimetri, hayati saglik/enkaz
# ihbarlarinin (dusuk model guveniyle "Alakasiz" tahmin edilince) sessizce
# elenmesine yol acti (6 test ihbarinin 2'si, ikisi de hayati medikal cagriydi).
# Kurtarma kumesi artik P-5'teki BES ilgili kategorinin tumunu kapsiyor.
RESCUE_KEYWORDS = {
    # Hayati oncelik: saglik/tibbi acil durum + arama-kurtarma
    # "aç" cikarildi: alt dizgi olarak "araç, ağaç, ilaç, açık" icinde eslesiyordu
    # (J-111); acligi anlatan kalip ifadeler kullanilir.
    "Acil Yardım İhtiyacı": [
        "yaralı", "yarali", "kanama", "bilinci kapalı", "bilinci kapali", "nefes al",
        "kalp krizi", "ambulans", "ilaç", "ilac", "doktor", "hasta", "ölüyor", "oluyor",
        "can çekişiyor", "can cekisiyor", "arama kurtarma", "kurtarın", "kurtarin",
        "ekip lazım", "ekip lazim", "hipotermi", "donuyoruz", "aç kaldık", "aç kaldı",
        "açız", "susuz", "yiyecek yok", "su yok", "elektrik yok", "ısınamıyoruz", "isinamiyoruz",
    ],
    "Enkaz Bildirimi": [
        "enkaz", "çöktü", "coktu", "yıkıldı", "yikildi", "göçük", "gocuk",
        "altında kaldı", "altinda kaldi", "bina yıkık", "bina yikik", "duvar çöktü",
        "duvar coktu", "ses geliyor", "sesi geliyor",
    ],
    "Lojistik İhtiyaç Bildirimi": [
        "çadır", "cadir", "battaniye", "barınma", "barinma", "giysi", "kıyafet",
        "kiyafet", "malzeme lazım", "malzeme lazim", "yardım malzemesi", "yardim malzemesi",
    ],
    "Yol Kapanma Bilgisi / Lojistik": [
        # "yol" kisa oldugu icin tam sozcuk + cekimleriyle (yollayın/yolcu eslesmesin)
        "yol", "yolu", "yolda", "yoldan", "yollar", "yolları", "yollari",
        "köprü", "kopru", "ulasim", "ulaşım", "kapalı", "kapandi", "kapandı",
        "gecemiyor", "geçemiyor", "tır geçemiyor", "tir gecemiyor",
    ],
}
# Model bu guvenin altindaysa kararsiz sayilir (Belirsiz ya da anahtar sozcukle
# kurtarma). Deger degismedi; yalniz adlandirildi.
GUVEN_ESIGI = 0.30
# Bu uzunluktan kisa anahtar sozcukler yalniz TAM sozcuk olarak eslesir; daha
# uzunlar sozcuk BASINDAN eslesir (Turkce ekler: enkaz -> enkazda, köprü -> köprüde).
TAM_ESLESME_UZUNLUGU = 4


def turkce_kucuk(metin):
    """Turkceye duyarli kucuk harf: str.lower() 'I'yi 'i' yapar (Isınamıyoruz ->
    isınamıyoruz) ve eslesme kacar (J-116)."""
    return str(metin).replace("I", "ı").replace("İ", "i").lower()


def _sozcukler(metin):
    import re
    return re.findall(r"\w+", turkce_kucuk(metin))


def anahtar_eslesir(sozcukler, anahtar):
    """Anahtar sozcuk (tek ya da cok sozcuklu) metinde sozcuk sinirina gore var mi.

    Eskiden `anahtar in metin` alt dizgi aramasiydi: "aç" -> "araç", "yol" ->
    "yollayın" eslesiyordu (J-111). Simdi: son sozcuk haric tam eslesme, son
    sozcuk kisa anahtarlarda tam, uzunlarda sozcuk basindan (Turkce ek alir)."""
    parca = _sozcukler(anahtar)
    if not parca:
        return False
    n = len(parca)
    for i in range(len(sozcukler) - n + 1):
        pencere = sozcukler[i:i + n]
        if pencere[:-1] != parca[:-1]:
            continue
        son, hedef = pencere[-1], parca[-1]
        if son == hedef or (len(hedef) >= TAM_ESLESME_UZUNLUGU and son.startswith(hedef)):
            return True
    return False
# Onceki "road_keywords" adiyla, geriye donuk uyumluluk icin ayrica tutulur.
road_keywords = RESCUE_KEYWORDS["Yol Kapanma Bilgisi / Lojistik"]


def _has_required_local_model_files(model_dir):
    return all((model_dir / filename).exists() for filename in REQUIRED_MODEL_FILES)


def _download_default_model():
    DEFAULT_LOCAL_MODEL.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=DEFAULT_HF_REPO,
        local_dir=str(DEFAULT_LOCAL_MODEL),
        allow_patterns=list(REQUIRED_MODEL_FILES),
    )


def _resolve_model_path(model_name=None):
    if model_name:
        return model_name
    if _has_required_local_model_files(DEFAULT_LOCAL_MODEL):
        return str(DEFAULT_LOCAL_MODEL)
    _download_default_model()
    if _has_required_local_model_files(DEFAULT_LOCAL_MODEL):
        return str(DEFAULT_LOCAL_MODEL)
    remote_model_name = os.getenv(REMOTE_MODEL_ENV)
    if remote_model_name:
        return remote_model_name
    raise ValueError(
        "Siniflandirma modeli bulunamadi. "
        f"Yerel olarak '{DEFAULT_LOCAL_MODEL}' klasorunu ekleyin, "
        f"varsayilan Hugging Face reposu '{DEFAULT_HF_REPO}' erisilebilir olsun veya "
        f"{REMOTE_MODEL_ENV} ortam degiskenini Hugging Face model adi ile ayarlayin."
    )


def _normalize_label(label):
    replacements = str(label).strip().replace("ı", "i").replace("İ", "I")
    replacements = replacements.replace("ş", "s").replace("Ş", "S")
    replacements = replacements.replace("ğ", "g").replace("Ğ", "G")
    replacements = replacements.replace("ü", "u").replace("Ü", "U")
    replacements = replacements.replace("ö", "o").replace("Ö", "O")
    replacements = replacements.replace("ç", "c").replace("Ç", "C")
    return replacements


class DisasterClassifier:
    def __init__(self, model_name=None):
        self.model_name = _resolve_model_path(model_name)
        device = 0 if torch.cuda.is_available() else -1
        # Multilabel modellerde tüm skorları almak için top_k=None kullanıyoruz.
        self.classifier = pipeline(
            "text-classification",
            model=self.model_name,
            tokenizer=self.model_name,
            device=device,
            top_k=None,
        )

    @staticmethod
    def _keyword_rescue(text):
        """E-04: 5 P-5 kategorisinin tumunde anahtar kelime kurtarmasi dener.
        Oncelik sirasi hayati onem sirasina gore (saglik/enkaz > lojistik > yol)
        -- birden fazla kategori eslesirse en oncelikli olan donulur. Eslesme
        sozcuk sinirina gore yapilir (anahtar_eslesir)."""
        sozcukler = _sozcukler(text)
        for category in ("Acil Yardım İhtiyacı", "Enkaz Bildirimi",
                          "Lojistik İhtiyaç Bildirimi", "Yol Kapanma Bilgisi / Lojistik"):
            if any(anahtar_eslesir(sozcukler, keyword) for keyword in RESCUE_KEYWORDS[category]):
                return category
        return None

    @staticmethod
    def _kategori_guveni(predictions, kategori):
        """Gosterilen kategoriye eslenen etiketlerin en yuksek model skoru.
        Eskiden kurtarma `max(skor, 0.50)` donduruyordu; skor BASKA bir etikete
        aitti ve arayuzde gosterilen 'guven' gosterilen kategorinin degildi (J-111)."""
        eslesen = [p["score"] for p in predictions
                   if CATEGORY_MAPPING.get(_normalize_label(p["label"])) == kategori
                   or (kategori == "Lojistik İhtiyaç Bildirimi" and _normalize_label(p["label"]) == "Lojistik")]
        return max(eslesen) if eslesen else 0.0

    def classify_detay(self, text):
        """Sınıflandırmanın ayrıntısı: gösterilen kategori, KENDİ güveni, modelin
        ham (13 etiketli) en yüksek etiketi ve kararı kimin verdiği.

        Karar sırası (J-111 düzeltmesi):
          1. Model yeterince eminse (skor >= GUVEN_ESIGI) ve 'Alakasız' demiyorsa
             modelin etiketi eşlenir; anahtar sözcük onu EZMEZ.
          2. Model kararsızsa ya da 'Alakasız' diyorsa anahtar sözcük kurtarması
             dener (E-04: hayati ihbar sessizce elenmesin).
          3. Kurtarılamayan kararsız kayıt 'Belirsiz', kurtarılamayan emin
             'Alakasız' kaydı 'Alakasız' olur.
        """
        if not text or len(text.strip()) < 5:
            return {"kategori": "Alakasız", "guven": 0.0, "hamEtiket": None, "hamSkor": 0.0,
                    "kaynak": "kisa_metin"}
        predictions = self.classifier(text[:512])[0]
        predictions = sorted(predictions, key=lambda item: item["score"], reverse=True)
        top = predictions[0]
        ham = _normalize_label(top["label"])
        skor = float(top["score"])
        detay = {"hamEtiket": top["label"], "hamSkor": skor}

        if skor >= GUVEN_ESIGI and ham != "Alakasiz":
            kategori = CATEGORY_MAPPING.get(ham, "Diğer")
            if ham == "Lojistik":
                yol = any(anahtar_eslesir(_sozcukler(text), k)
                          for k in RESCUE_KEYWORDS["Yol Kapanma Bilgisi / Lojistik"])
                kategori = "Yol Kapanma Bilgisi / Lojistik" if yol else "Lojistik İhtiyaç Bildirimi"
            return {**detay, "kategori": kategori, "guven": skor, "kaynak": "model"}

        kurtarilan = self._keyword_rescue(text)
        if kurtarilan is not None:
            return {**detay, "kategori": kurtarilan,
                    "guven": float(self._kategori_guveni(predictions, kurtarilan)),
                    "kaynak": "anahtar_sozcuk"}
        if skor < GUVEN_ESIGI:
            # Kurtarilamayan dusuk guvenli kayit: sessizce elenmez, incelenir.
            return {**detay, "kategori": "Belirsiz", "guven": skor, "kaynak": "belirsiz"}
        return {**detay, "kategori": "Alakasız", "guven": skor, "kaynak": "model"}

    def classify(self, text):
        """(kategori, güven) döndürür; ayrıntı için `classify_detay`."""
        try:
            d = self.classify_detay(text)
            return d["kategori"], d["guven"]
        except Exception:
            return "Hata", 0.0

if __name__ == "__main__":
    clf = DisasterClassifier()
    sample = "Avcılar caddesi yol çöktü, iş makinesi giremiyor acil lojistik lazım."
    cat, score = clf.classify(sample)
    print(f"Text: {sample}")
    print(f"Kategori: {cat} (Skor: {score:.4f})")
