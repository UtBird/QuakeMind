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

    def classify(self, text):
        """
        Metni sınıflandırır ve P-5 standardındaki üst kategoriye eşler.
        En yüksek güvene sahip etiketi ve skorunu döndürür.
        """
        if not text or len(text.strip()) < 5:
            return "Alakasız", 0.0

        try:
            predictions = self.classifier(text[:512])[0]
            predictions = sorted(predictions, key=lambda item: item["score"], reverse=True)

            top_pred = predictions[0]
            raw_label = top_pred["label"]
            normalized_label = _normalize_label(raw_label)
            score = top_pred["score"]

            lowered_text = text.lower()
            road_keywords = ["yol", "köprü", "ulasim", "ulaşım", "kapalı", "kapandi", "kapandı", "gecemiyor", "geçemiyor"]

            if normalized_label == "Alakasiz" and any(keyword in lowered_text for keyword in road_keywords):
                return "Yol Kapanma Bilgisi / Lojistik", max(score, 0.50)

            if score < 0.30 or normalized_label == "Alakasiz":
                return "Alakasız", score

            p5_label = CATEGORY_MAPPING.get(normalized_label, "Diğer")

            if normalized_label == "Lojistik":
                if any(keyword in lowered_text for keyword in road_keywords):
                    p5_label = "Yol Kapanma Bilgisi / Lojistik"
                else:
                    p5_label = "Lojistik İhtiyaç Bildirimi"

            return p5_label, score
        except Exception:
            return "Hata", 0.0

if __name__ == "__main__":
    clf = DisasterClassifier()
    sample = "Avcılar caddesi yol çöktü, iş makinesi giremiyor acil lojistik lazım."
    cat, score = clf.classify(sample)
    print(f"Text: {sample}")
    print(f"Kategori: {cat} (Skor: {score:.4f})")
