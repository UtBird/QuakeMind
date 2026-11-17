"""Harita altligi (J-40): `araclar_altlik_uret.py`'nin urettigi bolge paketleri.

Altlik kendi verimizden cizilir (ARAYUZ 11, MIMARI 8): yerel OSM kopyasindan
bir kez uretilir (kural 3), bu uc yalniz hazir ve sikistirilmis dosyayi verir.
Tarayici bir bolgeyi bir kez indirir ve onbellekte tutar.

Uretim 634 MB'lik Turkiye PBF'i ve ~2 saatlik GDAL/pyogrio okumasi ister; her
gelistirme makinesinde tekrarlanmasin diye uretilmis paketler bir kez
`Utbird/quakemind-altlik` HF veri kumesine yuklenir (model agirliklarinin
indirilme deseniyle ayni, bkz. apps/road_damage/utils/inference.py). Dosya
yerelde yoksa buradan indirilir ve diske yazilir; sonraki istekler diskten
gelir, her seferinde HF'e gidilmez."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError, HfHubHTTPError

import kimlik

yonlendirici = APIRouter()

ALTLIK_DIZINI = Path(__file__).resolve().parents[1] / "veri" / "altlik"
ALTLIK_HF_DEPOSU = "Utbird/quakemind-altlik"


def _indir(ad: str) -> Path | None:
    """`ad` HF veri kumesinde varsa indirir ve yerel yolunu doner; yoksa None."""
    try:
        indirilen = hf_hub_download(
            repo_id=ALTLIK_HF_DEPOSU,
            repo_type="dataset",
            filename=ad,
            local_dir=str(ALTLIK_DIZINI),
        )
        return Path(indirilen)
    except (HfHubHTTPError, EntryNotFoundError):
        return None


def _al(ad: str) -> Path | None:
    """Dosya yerelde varsa onu, yoksa HF'ten indirilmis halini doner."""
    yol = ALTLIK_DIZINI / ad
    if yol.exists():
        return yol
    return _indir(ad)


@yonlendirici.get("/api/altlik")
def altlik_katalogu(_kul: dict = Depends(kimlik.kullanici)):
    """Uretilmis bolgeler: kutu, nesne sayilari, boyut ve kaynak kunyesi."""
    yol = _al("katalog.json")
    if yol is None:
        return {"bolgeler": [], "not": "Altlik uretilmedi: python araclar_altlik_uret.py"}
    return {"bolgeler": json.loads(yol.read_text(encoding="utf-8"))}


@yonlendirici.get("/api/altlik/yerler")
def altlik_yerleri(_kul: dict = Depends(kimlik.kullanici)):
    """Butun bolgelerin yer adlari (sehir, ilce, koy, mahalle) ve merkezleri.

    Afetzede ekrani konum alinamazsa mahallesini sectirir (J-43); bunun icin
    megabaytlik bolge paketini indirmez. `/api/altlik/{bolge}`'den ONCE
    tanimli: yoksa "yerler" bolge adi sanilirdi."""
    yol = _al("yerler.json")
    if yol is None:
        return {"yerler": []}
    return {"yerler": json.loads(yol.read_text(encoding="utf-8"))}


@yonlendirici.get("/api/altlik/{bolge}")
def altlik_paketi(bolge: str, _kul: dict = Depends(kimlik.kullanici)):
    """Bolgenin yollari, yapilari, su alanlari ve nehirleri (gzip JSON, delta kodlu)."""
    if not bolge.isalnum():
        raise HTTPException(status_code=422, detail="Gecersiz bolge adi.")
    yol = _al(f"{bolge}.json.gz")
    if yol is None:
        raise HTTPException(status_code=404, detail="Bu bolgenin altligi uretilmedi.")
    return FileResponse(
        yol,
        media_type="application/json",
        headers={"Content-Encoding": "gzip", "Cache-Control": "private, max-age=86400"},
    )
