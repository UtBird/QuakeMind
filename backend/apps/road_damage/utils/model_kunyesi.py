"""Uydu hasar modelinin kunyesi (J-36): hangi agirlik, hangi mimari, hangi karar ayarlari.

Eskiden yukleyici tek mimariye sabitti (`inference.load_simple_model`:
smp.Segformer, mit_b4) ve karar ayarlari (esik, guclendirme, son isleme) dort
yere dagilmisti. Egitim defterindeki 11 adaydan yalniz biri yuklenebiliyordu;
otekiler `load_state_dict`'te duser, isci havuzu kurulamaz, butun analizler
hata verirdi. Kunye bunlari tek dosyada toplar:

    backend/modeller/uydu/<ad>.json

Etkin model `QM_UYDU_MODELI` ortam degiskeniyle secilir (varsayilan
VARSAYILAN_MODEL = bugunku model; davranis degismez). Agirlik dosyasi depoya
girmez (CLAUDE.md 9): kunyedeki yoldadir ya da Hugging Face'ten indirilir;
yuklemeden once SHA-256'si kunyedekiyle karsilastirilir, farkliysa yuklenmez.

Yeni model eklemek: `araclar_model_kunye.py` egitim defterinin kosu klasorunden
(sonuc.json + model_en_iyi.pth) kunyeyi uretir, `araclar_model_teslim.py`
yukleyip olcer. Ayrinti: modeller/README.md.
"""
import hashlib
import json
import os
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
KUNYE_DIZINI = BACKEND / "modeller" / "uydu"
VARSAYILAN_MODEL = "segformer_mitb4_dice30"

# Egitim defterinin kurdugu smp siniflari (QuakeMind_veri/araclar/defter_dokuz_model.py).
MIMARILER = ("Segformer", "Unet", "FPN", "DeepLabV3Plus", "UPerNet")
NORMALIZASYONLAR = ("imagenet", "yok")


def etkin_model_adi() -> str:
    return os.environ.get("QM_UYDU_MODELI") or VARSAYILAN_MODEL


def kunye_oku(ad_ya_da_yol=None) -> dict:
    """Ad (modeller/uydu/<ad>.json) ya da dosya yolu; None -> etkin model."""
    hedef = ad_ya_da_yol or etkin_model_adi()
    yol = Path(hedef)
    if yol.suffix != ".json":
        yol = KUNYE_DIZINI / f"{hedef}.json"
    if not yol.exists():
        mevcut = sorted(p.stem for p in KUNYE_DIZINI.glob("*.json"))
        raise FileNotFoundError(f"Model kunyesi yok: {yol}. Mevcut kunyeler: {mevcut}")
    kunye = json.loads(yol.read_text(encoding="utf-8"))
    hatalar = kunye_dogrula(kunye)
    if hatalar:
        raise ValueError(f"Kunye gecersiz ({yol.name}): " + "; ".join(hatalar))
    return kunye


def kunye_dogrula(k: dict) -> list:
    """Eksik ya da tutarsiz alanlar; bos liste = gecerli."""
    hatalar = []

    def al(yol):
        d = k
        for parca in yol.split("."):
            if not isinstance(d, dict) or parca not in d:
                hatalar.append(f"'{yol}' eksik")
                return None
            d = d[parca]
        return d

    if al("ad") is not None and not str(k["ad"]).replace("_", "").replace("-", "").isalnum():
        hatalar.append("'ad' yalniz harf, rakam, '_' ve '-' icermeli")
    sinif = al("mimari.sinif")
    if sinif is not None and sinif not in MIMARILER:
        hatalar.append(f"'mimari.sinif' {MIMARILER} icinden olmali, '{sinif}' verildi")
    al("mimari.kodlayici")
    siniflar = al("mimari.siniflar")
    if siniflar is not None and siniflar != 1:
        hatalar.append("yalniz tek kanalli (ikili hasar) cikti destekleniyor: 'mimari.siniflar' = 1")
    norm = al("girdi.normalizasyon")
    if norm is not None and norm not in NORMALIZASYONLAR:
        hatalar.append(f"'girdi.normalizasyon' {NORMALIZASYONLAR} icinden olmali")
    gsd = al("girdi.egitimGsdM")
    if gsd is not None and not (isinstance(gsd, list) and len(gsd) == 2 and 0 < gsd[0] <= gsd[1]):
        hatalar.append("'girdi.egitimGsdM' [en kucuk, en buyuk] metre olmali")
    esik = al("karar.esik")
    if esik is not None and not 0 < esik < 1:
        hatalar.append("'karar.esik' 0 ile 1 arasinda olmali")
    guc = al("karar.guclendirme")
    if guc is not None and not guc >= 1:
        hatalar.append("'karar.guclendirme' en az 1 olmali")
    son = al("karar.sonIsleme")
    if son is not None and son not in (0, 1, 2):
        hatalar.append("'karar.sonIsleme' 0, 1 ya da 2 olmali")
    al("agirlik.dosya")
    sha = al("agirlik.sha256")
    if sha is not None and (len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)):
        hatalar.append("'agirlik.sha256' 64 haneli kucuk harf onaltilik olmali")
    return hatalar


def agirlik_yolu(k: dict) -> Path:
    yol = Path(k["agirlik"]["dosya"])
    return yol if yol.is_absolute() else BACKEND / yol


def sha256(yol) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def agirligi_hazirla(k: dict) -> Path:
    """Dosya yoksa ve kunyede Hugging Face kaynagi varsa indirir."""
    yol = agirlik_yolu(k)
    if yol.exists():
        return yol
    hf = k["agirlik"].get("hf")
    if not hf:
        raise FileNotFoundError(f"Agirlik dosyasi yok ve kunyede indirme kaynagi yok: {yol}")
    from huggingface_hub import hf_hub_download

    yol.parent.mkdir(parents=True, exist_ok=True)
    return Path(hf_hub_download(repo_id=hf["repo"], filename=hf["dosya"], local_dir=str(yol.parent)))


def model_kur(k: dict):
    """Kunyedeki mimariyi agirliksiz kurar (egitim defteriyle ayni cagri)."""
    import segmentation_models_pytorch as smp

    m = k["mimari"]
    return getattr(smp, m["sinif"])(
        encoder_name=m["kodlayici"], encoder_weights=None,
        in_channels=m.get("girdiKanal", 3), classes=m["siniflar"],
    )


def model_yukle(k: dict, cihaz=None):
    """Agirligi dogrular ve modeli yukler: (model, cihaz).

    Parmak izi kunyedekinden farkliysa YUKLENMEZ: sonuc kunyesi baska bir
    agirligin adini tasirdi. Anahtarlar birebir eslesmeli (strict)."""
    import torch

    yol = agirligi_hazirla(k)
    bulunan = sha256(yol)
    if bulunan != k["agirlik"]["sha256"]:
        raise RuntimeError(
            f"Model agirligi kunyeyle uyusmuyor ({k['ad']}): beklenen {k['agirlik']['sha256'][:12]}..., "
            f"bulunan {bulunan[:12]}... ({yol})")
    cihaz = cihaz or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model_kur(k).to(cihaz)
    durum = torch.load(yol, map_location=cihaz)
    if isinstance(durum, dict) and "state_dict" in durum and isinstance(durum["state_dict"], dict):
        durum = durum["state_dict"]
    model.load_state_dict(durum, strict=True)
    model.eval()
    return model, cihaz


def ozet(k: dict) -> dict:
    """Sonuca ve konsola giden kunye ozeti (agirlik yolu gibi yerel ayrintilar haric)."""
    return {
        "ad": k["ad"],
        "etiket": k.get("etiket") or k["ad"],
        "mimari": k["mimari"]["sinif"],
        "kodlayici": k["mimari"]["kodlayici"],
        "esik": k["karar"]["esik"],
        "guclendirme": k["karar"]["guclendirme"],
        "sonIsleme": k["karar"]["sonIsleme"],
        "kararKaynagi": k["karar"].get("kaynak"),
        "egitimGsdM": k["girdi"]["egitimGsdM"],
        "sha256Kisa": k["agirlik"]["sha256"][:12],
        "olcum": k.get("olcum") or {},
    }


def gsd_uyarisi(k: dict, kullanilan_gsd_m: float, pay: float = 1.5) -> bool:
    """Analiz goruntusu egitim cozunurlugunden belirgin kabaysa (J-20) True."""
    return kullanilan_gsd_m > pay * k["girdi"]["egitimGsdM"][1]
