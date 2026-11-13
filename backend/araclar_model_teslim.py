"""Model teslim testi (J-36): bir kunyenin urunde dogru kosacagini kanitlar.

    python araclar_model_teslim.py [AD|kunye.json] [--karo-yok] [--esik X] [--guclendirme X] [--son-isleme N]

Adimlar:
  1. Kunye gecerli mi (modeller/uydu/<ad>.json).
  2. Agirlik dosyasi var mi, SHA-256 kunyedekiyle ayni mi.
  3. Egitimdeki yazilim surumleri (torch, smp) yereldekiyle ayni mi -- farkliysa uyari.
  4. Mimari kunyeden kurulup agirlik katı (strict) yukleniyor mu; 512 x 512 ileri
     gecis CPU'da kac saniye.
  5. QQB dis sinama karolari (74; QuakeMind_veri/qqb, deftere gomulen bolmeyle
     ayni liste): URUNUN KENDI cikarim fonksiyonu (`run_inference`) kunyedeki
     karar ayariyla kosar; IoU, kesinlik, duyarlilik 255 (belirsiz) pikseller
     disarida birakilarak defterle ayni formulle hesaplanir. Kunyede defterin
     `dis_qqb` olcumu varsa ikisi karsilastirilir.

  5. adimdaki fark neden sifir olmayabilir: defter QQB karolarini Colab'da
  kaynaktan yeniden uretir ve CUDA'da float16 calisir; burada yerel karolar ve
  CPU float32 kullanilir. Kucuk fark (varsayilan tolerans 0,02) beklenir;
  buyuk fark on islemenin (normalizasyon, esik, son isleme) ayristigini gosterir.

Veri kok dizini: QM_VERI ortam degiskeni, yoksa depo yaninda QuakeMind_veri.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

from apps.road_damage.utils import model_kunyesi as mk

VERI = Path(os.environ.get("QM_VERI") or mk.BACKEND.parents[1] / "QuakeMind_veri")


def qqb_dis_sinama():
    import csv

    liste = VERI / "qqb" / "qqb_bolme.csv"
    with open(liste, encoding="utf-8") as f:
        return [r["ornek"] for r in csv.DictReader(f) if r["grup"] == "dis_sinama"]


def olc(model, cihaz, esik, guclendirme, son_isleme, normalizasyon):
    from PIL import Image

    from apps.road_damage.utils.inference import run_inference

    tp = fp = fn = 0
    karolar = qqb_dis_sinama()
    t0 = time.perf_counter()
    for ad in karolar:
        goruntu = Image.open(VERI / "qqb" / "karolar" / f"{ad}.png").convert("RGB")
        maske = np.array(Image.open(VERI / "qqb" / "karolar" / f"{ad}_maske.png"))
        _ham, _gucl, tahmin, _kes, _img = run_inference(
            goruntu, np.zeros(maske.shape, dtype=np.uint8), model, cihaz,
            guclendirme, esik, use_imagenet_norm=normalizasyon == "imagenet",
            postprocess_level=son_isleme,
        )
        gecerli = maske != 255
        p = tahmin.astype(bool) & gecerli
        g = maske == 1
        tp += int((p & g).sum())
        fp += int((p & ~g).sum())
        fn += int((~p & g).sum())
    e = 1e-9
    return {
        "karo": len(karolar), "sure": time.perf_counter() - t0,
        "iou": tp / (tp + fp + fn + e), "kesinlik": tp / (tp + fp + e), "duyarlilik": tp / (tp + fn + e),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kunye", nargs="?", default=None)
    ap.add_argument("--karo-yok", action="store_true", help="5. adimi atla")
    ap.add_argument("--esik", type=float)
    ap.add_argument("--guclendirme", type=float)
    ap.add_argument("--son-isleme", type=int)
    ap.add_argument("--tolerans", type=float, default=0.02)
    a = ap.parse_args()

    kaldi = []
    k = mk.kunye_oku(a.kunye)  # gecersizse burada durur
    print(f"1. kunye gecerli: {k['ad']} ({k['mimari']['sinif']} / {k['mimari']['kodlayici']})")

    yol = mk.agirligi_hazirla(k)
    iz = mk.sha256(yol)
    if iz == k["agirlik"]["sha256"]:
        print(f"2. agirlik: {yol.name}, SHA-256 kunyeyle ayni ({iz[:12]})")
    else:
        print(f"2. KALDI: agirlik SHA-256 farkli (kunye {k['agirlik']['sha256'][:12]}, dosya {iz[:12]})")
        return 1

    import segmentation_models_pytorch as smp
    import torch

    egitim_yaz = (k.get("egitim") or {}).get("yazilim") or {}
    yerel = {"torch": torch.__version__.split("+")[0], "smp": smp.__version__}
    farklar = [f"{p}: egitim {str(egitim_yaz[p]).split('+')[0]}, yerel {yerel[p]}"
               for p in ("torch", "smp") if p in egitim_yaz and str(egitim_yaz[p]).split("+")[0] != yerel[p]]
    if not egitim_yaz:
        print("3. yazilim: kunyede egitim surumu yok, karsilastirilamadi")
    elif farklar:
        print("3. UYARI yazilim surumu farkli -- " + "; ".join(farklar))
    else:
        print(f"3. yazilim: egitimle ayni (torch {yerel['torch']}, smp {yerel['smp']})")

    t0 = time.perf_counter()
    model, cihaz = mk.model_yukle(k)
    yukleme = time.perf_counter() - t0
    with torch.no_grad():
        x = torch.rand(1, 3, 512, 512, device=cihaz)
        model(x)
        t0 = time.perf_counter()
        cikti = model(x)
        ileri = time.perf_counter() - t0
    if tuple(cikti.shape) != (1, 1, 512, 512):
        print(f"4. KALDI: cikti sekli {tuple(cikti.shape)}, beklenen (1, 1, 512, 512)")
        return 1
    print(f"4. katı yukleme {yukleme:.1f} sn; 512x512 ileri gecis {ileri:.2f} sn ({cihaz})")

    if not a.karo_yok:
        karar = k["karar"]
        esik = a.esik if a.esik is not None else karar["esik"]
        guc = a.guclendirme if a.guclendirme is not None else karar["guclendirme"]
        son = a.son_isleme if a.son_isleme is not None else karar["sonIsleme"]
        ayar_kunyeden = (esik, guc, son) == (karar["esik"], karar["guclendirme"], karar["sonIsleme"])
        s = olc(model, cihaz, esik, guc, son, k["girdi"]["normalizasyon"])
        print(f"5. QQB dis sinama ({s['karo']} karo, esik {esik}, guclendirme {guc}, son isleme {son}"
              f"{'' if ayar_kunyeden else ', kunyeden FARKLI ayar'}): IoU {s['iou']:.4f}, "
              f"kesinlik {s['kesinlik']:.4f}, duyarlilik {s['duyarlilik']:.4f} ({s['sure']:.0f} sn)")
        defter = ((k.get("olcum") or {}).get("disQqb") or {}).get("iou")
        if defter is None:
            print("   kunyede defterin dis_qqb olcumu yok; karsilastirma yapilmadi")
        elif not ayar_kunyeden:
            print("   ayar kunyeden farkli oldugu icin defterle karsilastirilmadi")
        elif abs(s["iou"] - defter) <= a.tolerans:
            print(f"   defter IoU {defter:.4f}, fark {s['iou'] - defter:+.4f} (tolerans {a.tolerans}) -- tutuyor")
        else:
            kaldi.append("QQB IoU defterle tutmuyor")
            print(f"   KALDI: defter IoU {defter:.4f}, fark {s['iou'] - defter:+.4f} > {a.tolerans}")

    print("SONUC:", "GECTI" if not kaldi else "KALDI -- " + "; ".join(kaldi))
    return 0 if not kaldi else 1


if __name__ == "__main__":
    sys.exit(main())
