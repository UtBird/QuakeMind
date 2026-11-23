"""Yerel OSM yol ve tesis kesitini Hugging Face'ten indirir (J-187).

Hasar analizinin yol maskesi ve tatbikatin yol agi `roads.gpkg`'den gelir.
Dosya buyuk (~164 MB) oldugu icin depoya girmez; canli sunucuda yoktu ve
analiz "yol katmani alinamadi" diyordu (J-184). Dagitim bu araci kalici veri
dizinine (`veri/osm`, canlida `quakemind-data` birimi) bir kez calistirir.

    python araclar_osm_indir.py                 # veri/osm altina
    python araclar_osm_indir.py /baska/dizin

Dosya varsa ve parmak izi tutuyorsa indirilmez. Indirilen dosyanin parmak izi
tutmazsa silinir ve arac hata verir: yanlis yol verisiyle analiz yapilmaz.
Sabit surum: ayni adla yeni dosya yuklense de burada yazili commit iner.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

DEPO = "Furkei/quakemind-osm-yollar"
SURUM = "0d4df2588a087c95d013ac6bae5f650a33919fd0"
DOSYALAR = {
    "roads.gpkg": "7da51873421cb370ce0b6dea174d3f3a6e7306524c12eea6e4f3e97a31cfb449",
    "tesisler.gpkg": "50f098b04c6add5554b7672d735ff99ca006f9ab17760665af071e4eb141ca26",
}
VARSAYILAN_DIZIN = Path(__file__).resolve().parent / "veri" / "osm"


def _sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def indir(hedef: Path) -> list[str]:
    from huggingface_hub import hf_hub_download

    hedef.mkdir(parents=True, exist_ok=True)
    olanlar = []
    for ad, beklenen in DOSYALAR.items():
        yol = hedef / ad
        if yol.exists() and _sha256(yol) == beklenen:
            olanlar.append(f"{ad}: zaten var")
            continue
        # Ayni birimdeki gecici klasore iner (HF onbellegine degil: dosya iki
        # kez yer kaplamasin); parmak izi tutunca yerine tasinir.
        gecici_dizin = hedef / ".indiriliyor"
        try:
            inen = Path(hf_hub_download(repo_id=DEPO, filename=ad, repo_type="dataset",
                                        revision=SURUM, local_dir=str(gecici_dizin)))
            if _sha256(inen) != beklenen:
                raise RuntimeError(f"{ad}: parmak izi tutmuyor, dosya kurulmadi")
            inen.replace(yol)
        finally:
            shutil.rmtree(gecici_dizin, ignore_errors=True)
        olanlar.append(f"{ad}: indirildi")
    return olanlar


def main(argv: list[str]) -> int:
    hedef = Path(argv[0]) if argv else VARSAYILAN_DIZIN
    for satir in indir(hedef):
        print(satir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
