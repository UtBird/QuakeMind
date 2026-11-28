"""Internetsiz kip ve ozellik matrisi (OPTIMIZASYON_ANALIZI madde 3, 33).

Neden. Kod hangi ozelligin internete bagli oldugunu ortuk biciminde tasiyordu:
dis servise giden uclar internet yokken zaman asimina kadar bekliyor (OSRM
10 sn, karo vekili 20 sn), sonra genel bir hata veriyordu; Hugging Face
istemcisi diskte duran model icin bile aga soruyordu. Saha sunucusunda
(Pi ya da dizustu, afet bolgesinde, hotspot) bu bekleme her istekte odenir.

Kip. `QUAKEMIND_INTERNETSIZ=1` ile acilir; sunucu acilmadan, `fastapi_app`
ilk satirlarinda uygulanir (`kipi_uygula`), cunku huggingface_hub
`HF_HUB_OFFLINE`'i ice aktarilirken okur ve analiz iscisi surecleri ortami
acilista devralir. Acikken:

  * Model ve altlik dosyalari yalniz diskten okunur; eksikse indirme denenmez.
  * Yol maskesi yalniz yerel OSM kopyasindan (`QUAKEMIND_OFFLINE_ONLY=1`).
  * Yalniz dis serviste calisan uclar (asagidaki DIS_SERVISLER) beklemeden
    503 ve neden doner. Karo vekili onbellekte olan acik lisansli karoyu
    vermeye devam eder (`uclar/goruntu.py`).

Kip merkez sunucuyla esitlemeyi KAPATMAZ (`esitleme.py`): o bizim kendi
baglantimiz, internet geldiginde zaten denenir. Kip "kamuya acik dis
servislere gitme" demektir.

Ozellik matrisi. `durum()` her ozellik icin internetsiz calisip calismadigini
ve bunun dayandigi yerel dosyanin bu makinede olup olmadigini SIMDI olcer;
tablo elle yazilmis bir iddia degildir. `/api/internetsiz` bunu doner.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parent
VERI = BACKEND / "veri"

# Yalniz dis serviste calisan isler. Anahtar uclarda `dis_servis_gerekli`e
# verilir; metin 503 yanitinda kullaniciya yazilir.
DIS_SERVISLER = {
    "uydu_goruntusu": "Uydu görüntüsü (Esri Wayback, Google, OpenAerialMap) internetten gelir.",
    "oam_arama": "OpenAerialMap görüntü araması internet ister.",
    "wayback": "Esri Wayback arşivi internet ister.",
    "osrm": "Yedek yaya rotası dış servisten (OSRM) gelir; yerel yol ağı olan bölgelerde /api/afetzede/rota kullanılır.",
    "deprem_verisi": "Deprem kataloğunu tazelemek internet ister; eldeki katalog kullanılmaya devam eder.",
}


def etkin() -> bool:
    """Kip acik mi. Her cagrida ortamdan okunur (testler degistirebilsin)."""
    return os.environ.get("QUAKEMIND_INTERNETSIZ", "0") == "1"


def kipi_uygula() -> bool:
    """Kip aciksa model/veri kitapliklarinin aga cikmasini kapatir.

    Ice aktarmalardan ONCE cagrilmali. Donus: kip acik mi."""
    if not etkin():
        return False
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    # Yol maskesi: yerel kopya yoksa Overpass'a gitmez, bos maske + uyari.
    os.environ["QUAKEMIND_OFFLINE_ONLY"] = "1"
    return True


def uydu_iscisi_gerekli() -> bool:
    """Uydu analizi isci sureci acilsin mi. Internetsiz kipte hayir (goruntu
    internetten gelir; surec ~1,2 GB tutar). QUAKEMIND_UYDU_ISCISI=1 zorlar."""
    return not etkin() or os.environ.get("QUAKEMIND_UYDU_ISCISI", "0") == "1"


def dis_servis_gerekli(ad: str) -> None:
    """Kip aciksa 503 ile durur; degilse hicbir sey yapmaz."""
    if etkin():
        raise HTTPException(
            status_code=503,
            detail=f"İnternetsiz kip: {DIS_SERVISLER.get(ad, 'Bu iş internet ister.')}",
        )


# ---- ozellik matrisi -------------------------------------------------------

def _json(yol: Path):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _bolge_dosyalari(katalog: Path, dizin: Path, uzanti: str) -> dict:
    """Katalogdaki bolgelerden kacinin dosyasi diskte."""
    k = _json(katalog)
    if not isinstance(k, list):
        return {"tanimli": 0, "yerelde": 0, "bolgeler": []}
    var = [b["id"] for b in k if isinstance(b, dict) and (dizin / f"{b['id']}{uzanti}").exists()]
    return {"tanimli": len(k), "yerelde": len(var), "bolgeler": var}


def _uydu_modelleri() -> dict:
    try:
        from apps.road_damage.utils import model_kunyesi
    except Exception:  # noqa: BLE001
        return {"tanimli": 0, "yerelde": 0}
    tanimli = yerelde = 0
    for yol in sorted(model_kunyesi.KUNYE_DIZINI.glob("*.json")):
        tanimli += 1
        try:
            yerelde += model_kunyesi.agirlik_yolu(model_kunyesi.kunye_oku(yol.stem)).exists()
        except Exception:  # noqa: BLE001
            pass
    return {"tanimli": tanimli, "yerelde": yerelde}


def _yerel_dosyalar() -> dict:
    """Ozelliklerin dayandigi yerel dosyalar; yalniz var/yok ve sayi."""
    metin_modeli = BACKEND / "apps" / "disaster_nlp" / "models" / "2kveri"
    kamera = BACKEND / "apps" / "camera_detection" / "models"
    risk_modeli = BACKEND / "apps" / "earthquake_risk" / "models"
    try:
        from apps.road_damage.utils import yerel_yol

        yol_verisi = bool(yerel_yol.veri_var())
    except Exception:  # noqa: BLE001
        yol_verisi = False
    katalog = BACKEND / "apps" / "earthquake_risk" / "data" / "query.csv"
    return {
        "metinModeli": (metin_modeli / "config.json").exists(),
        "kameraModeli": (kamera / "catlak.pt").exists() or (kamera / "bina.pt").exists(),
        "riskModeli": risk_modeli.is_dir() and any(risk_modeli.glob("*.cbm")),
        "depremKatalogu": katalog.exists(),
        "yerelYolVerisi": yol_verisi,
        "toplanmaAlanlari": (BACKEND / "apps" / "road_damage" / "data" / "tum_turkiye_toplanma_alanlari.json").exists(),
        "uyduModeli": _uydu_modelleri(),
        "altlik": _bolge_dosyalari(VERI / "altlik" / "katalog.json", VERI / "altlik", ".json.gz"),
        "yuruyusAgi": _bolge_dosyalari(VERI / "yol_agi" / "katalog.json", VERI / "yol_agi", ".npz"),
        "aracAgi": _bolge_dosyalari(VERI / "yol_agi" / "arac" / "katalog.json", VERI / "yol_agi" / "arac", ".npz"),
    }


def _ozellik(ad, calisir, kosul=None, not_=None) -> dict:
    """calisir: "evet" | "kismen" | "hayir". kosul: yerel dosya hazir mi
    (None: dosyaya dayanmiyor)."""
    if kosul is False and calisir != "hayir":
        calisir = "hayir"
    return {"ozellik": ad, "internetsiz": calisir, "yerelVeriHazir": kosul, "not": not_}


def matris(y: dict | None = None) -> list[dict]:
    y = y or _yerel_dosyalar()
    altlik, yuruyus, arac, uydu = y["altlik"], y["yuruyusAgi"], y["aracAgi"], y["uyduModeli"]
    return [
        _ozellik("Giriş, hesaplar, roller", "evet", None, "Kimlik ve oturum yerel veritabanında."),
        _ozellik("SOS, ihbar, görev, ekip, bildirim", "evet", None,
                 "Yerel SQLite; canlı akış (SSE) aynı sunucudan. Merkeze eşitleme bağlantı gelince."),
        _ozellik("Metin analizi (sınıflandırma + adres)", "evet", y["metinModeli"],
                 "Model diskte; adres yerel dizinden (J-170), dışarı gitmez."),
        _ozellik("Fotoğraf / kamera tespiti (YOLO)", "evet", y["kameraModeli"], "Model diskte."),
        _ozellik("Deprem riski hesabı", "evet", y["riskModeli"] and y["depremKatalogu"],
                 "Model ve katalog diskte; katalog tazelemesi internet ister."),
        _ozellik("Deprem kataloğunu tazeleme", "hayir", None, DIS_SERVISLER["deprem_verisi"]),
        _ozellik("Deprem, fay, toplanma alanı katmanları", "evet", y["depremKatalogu"] and y["toplanmaAlanlari"], None),
        _ozellik("Harita altlığı", "kismen" if altlik["yerelde"] < altlik["tanimli"] else "evet",
                 altlik["yerelde"] > 0,
                 f"{altlik['yerelde']}/{altlik['tanimli']} bölge diskte; eksik bölge internetsiz açılmaz."),
        _ozellik("Yürüme rotası (kendi yol ağımız)", "kismen", yuruyus["yerelde"] > 0,
                 f"Yalnız yol ağı üretilmiş {yuruyus['yerelde']} bölgede: {', '.join(yuruyus['bolgeler']) or '—'}. "
                 "Diğer yerlerde yedek OSRM rotası internet ister."),
        _ozellik("Araç rotası (ekip güzergâhı)", "kismen", arac["yerelde"] > 0,
                 f"Yalnız {arac['yerelde']} bölgede: {', '.join(arac['bolgeler']) or '—'}."),
        _ozellik("Uydu hasar analizi", "hayir", None,
                 f"Uydu görüntüsü internetten gelir. Model {uydu['yerelde']}/{uydu['tanimli']} diskte; "
                 "sonuçlar merkezden eşitlemeyle gelir."),
        _ozellik("Tatbikat", "evet" if uydu_iscisi_gerekli() else "hayir", None,
                 "Önbellekteki görüntüyle koşar; internetsiz kipte uydu işçisi bellek için açılmaz "
                 "(QUAKEMIND_UYDU_ISCISI=1 açar)."),
        _ozellik("Uydu / drone görüntü karoları", "kismen", None,
                 "Daha önce açılmış OpenAerialMap ve Esri Wayback karoları sunucunun önbelleğinden "
                 "(analiz görüntüsüyle aynı kural, J-172). Google karoları lisansı gereği saklanmaz, internet ister."),
        _ozellik("Yol maskesi (analiz içinde)", "evet" if y["yerelYolVerisi"] else "hayir", y["yerelYolVerisi"],
                 "Yerel OSM kopyası (roads.gpkg) varsa; yoksa Overpass internet ister."),
    ]


def durum() -> dict:
    y = _yerel_dosyalar()
    return {"kip": etkin(), "ozellikler": matris(y), "yerelDosyalar": y}
