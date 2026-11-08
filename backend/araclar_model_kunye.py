"""Egitim defterinin bir kosusundan model kunyesi uretir (J-36).

02 defteri (QuakeMind_veri/araclar/defter_dokuz_model.py) her kosuyu
`QuakeMind_egitim/<deney>/<model>/tohum_<n>/` klasorune yazar: sonuc.json
(ayarlar, olcutler, yazilim surumleri) ve AGIRLIK_SAKLA acikken
model_en_iyi.pth. Bu arac ikisinden modeller/uydu/<ad>.json kunyesini cikarir.
Karar ayarlari defterin olctugu ayardir: sigmoid > esik, guclendirme ve son
isleme yok -- urun modeli makalede olculdugu gibi kostursun diye.

    python araclar_model_kunye.py <kosu_klasoru> [--ad AD] [--kopyala] [--hf-repo REPO]

  --ad       kunye adi (varsayilan: <model>_<protokol>_t<tohum>)
  --kopyala  agirligi apps/road_damage/models/<ad>.pth'ye kopyalar (depoya girmez)
  --hf-repo  agirlik Hugging Face'e yuklendiyse repo adi (indirme kaynagi olur)

Sonra: python araclar_model_teslim.py <ad>
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from apps.road_damage.utils import model_kunyesi as mk

# Defterin model tablosu (defter_dokuz_model.py:397-407) -- ayni cagri.
DEFTER_MIMARILERI = {
    "segformer_mitb4": ("Segformer", "mit_b4"),
    "unet_mitb4": ("Unet", "mit_b4"),
    "fpn_mitb4": ("FPN", "mit_b4"),
    "deeplabv3plus_mitb4": ("DeepLabV3Plus", "mit_b4"),
    "upernet_mitb4": ("UPerNet", "mit_b4"),
    "deeplabv3plus_resnet101": ("DeepLabV3Plus", "resnet101"),
    "upernet_convnext_small": ("UPerNet", "tu-convnext_small"),
    "segformer_mitb0": ("Segformer", "mit_b0"),
    "segformer_mitb2": ("Segformer", "mit_b2"),
    "unet_resnet18": ("Unet", "resnet18"),
    "unet_resnet152": ("Unet", "resnet152"),
}

# Egitim kumelerinin cozunurlugu (m/piksel), defterin karolama kurallarindan:
# KATE-PD Maxar 0,375 + Pleiades 0,5; QQB Maxar 0,31 -> 0,375; HOTOSM 0,5;
# MEDBFS 0,75; KATE-CD (J-26) Maxar / Pleiades 0,3-0,5.
KUME_GSD_M = {
    "KATE-PD": (0.375, 0.5),
    "QQB": (0.375, 0.375),
    "HOTOSM": (0.5, 0.5),
    "MEDBFS": (0.75, 0.75),
    "KATE-CD": (0.3, 0.5),
}


def _olcut(sonuc, anahtar):
    d = sonuc.get(anahtar)
    if not isinstance(d, dict):
        return None
    return {
        "iou": d.get("iou_hasar"), "f1": d.get("f1"), "kesinlik": d.get("kesinlik"),
        "duyarlilik": d.get("duyarlilik"), "karo": d.get("n_karo"),
    }


def kunye_uret(klasor: Path, ad=None, kopyala=False, hf_repo=None) -> dict:
    sonuc = json.loads((klasor / "sonuc.json").read_text(encoding="utf-8"))
    pth = klasor / "model_en_iyi.pth"
    if not pth.exists():
        raise FileNotFoundError(f"{pth} yok -- defterde AGIRLIK_SAKLA = True olmali.")
    model_adi = sonuc["model"]
    if model_adi not in DEFTER_MIMARILERI:
        raise ValueError(f"'{model_adi}' DEFTER_MIMARILERI'nde yok; tabloya ekleyin.")
    sinif, kodlayici = DEFTER_MIMARILERI[model_adi]

    kumeler = sorted({k.split("/")[0] for k in sonuc["egitim"]["karo"]["egitim_kumeleri"]})
    bilinmeyen = [k for k in kumeler if k not in KUME_GSD_M]
    if bilinmeyen:
        raise ValueError(f"Cozunurlugu bilinmeyen egitim kumesi: {bilinmeyen}; KUME_GSD_M'ye ekleyin.")
    gsd = [min(KUME_GSD_M[k][0] for k in kumeler), max(KUME_GSD_M[k][1] for k in kumeler)]

    ad = ad or f"{model_adi}_{str(sonuc.get('protokol', '')).lower()}_t{sonuc['tohum']}"
    hedef = pth
    if kopyala:
        hedef = mk.BACKEND / "apps" / "road_damage" / "models" / f"{ad}.pth"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pth, hedef)
    dosya = str(hedef.relative_to(mk.BACKEND)).replace("\\", "/") if kopyala else str(hedef)

    kunye = {
        "ad": ad,
        "etiket": f"{model_adi} · {sonuc.get('deney')} · tohum {sonuc['tohum']}",
        "gorev": "uydu görüntüsünde hasar bölütleme (ikili: hasar / değil)",
        "mimari": {"kutuphane": "segmentation_models_pytorch", "sinif": sinif,
                   "kodlayici": kodlayici, "siniflar": 1, "girdiKanal": 3},
        "girdi": {"karoPx": 512, "normalizasyon": "imagenet", "egitimGsdM": gsd,
                  "gsdKaynagi": f"Eğitim kümeleri: {', '.join(kumeler)} (araclar_model_kunye.KUME_GSD_M)."},
        "karar": {"esik": sonuc["ayarlar"]["esik"], "guclendirme": 1.0, "sonIsleme": 0,
                  "kaynak": "02 defterinin ölçtüğü ayar: sigmoid > eşik; güçlendirme ve son işleme yok."},
        "agirlik": {"dosya": dosya, "sha256": mk.sha256(hedef)},
        "egitim": {"deney": sonuc.get("deney"), "protokol": sonuc.get("protokol"), "tohum": sonuc["tohum"],
                   "tarih": sonuc.get("tarih"), "yazilim": sonuc.get("yazilim"),
                   "enIyiDonem": sonuc["egitim"].get("en_iyi_donem"), "kumeler": kumeler,
                   "karo": {k: v for k, v in sonuc["egitim"]["karo"].items() if k != "egitim_kumeleri"}},
        "olcum": {
            "dogrulamaIoU": sonuc["egitim"].get("en_iyi_dogrulama_iou"),
            "sinamaIoU": (_olcut(sonuc, "sinama_sonrasi_tumu") or {}).get("iou"),
            "sinama": _olcut(sonuc, "sinama_sonrasi_tumu"),
            "disQqb": _olcut(sonuc, "dis_qqb"),
            "disMedbfs": _olcut(sonuc, "dis_medbfs"),
            "not": "02 defteri, sinama_sonrasi_tumu / dis_qqb / dis_medbfs (eşik = karar.esik).",
        },
    }
    if hf_repo:
        kunye["agirlik"]["hf"] = {"repo": hf_repo, "dosya": pth.name}
    hatalar = mk.kunye_dogrula(kunye)
    if hatalar:
        raise ValueError("Uretilen kunye gecersiz: " + "; ".join(hatalar))
    return kunye


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("klasor", type=Path)
    ap.add_argument("--ad")
    ap.add_argument("--kopyala", action="store_true")
    ap.add_argument("--hf-repo")
    a = ap.parse_args()
    kunye = kunye_uret(a.klasor, a.ad, a.kopyala, a.hf_repo)
    cikti = mk.KUNYE_DIZINI / f"{kunye['ad']}.json"
    if cikti.exists():
        print(f"{cikti} zaten var; once silin ya da --ad ile baska ad verin.")
        return 1
    cikti.write_text(json.dumps(kunye, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"kunye yazildi: {cikti}")
    print(f"sonra: python araclar_model_teslim.py {kunye['ad']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
