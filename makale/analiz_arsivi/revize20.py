# -*- coding: utf-8 -*-
"""Revizyon 20: Sekil 21-23'teki amber bildirim seridi kirpildi (J-135).

Sorun: Uc arayuz ekran goruntusunun (Sekil 21 catlak, 22 risk, 23 metin) ustunde
tam genislikte bir AMBER BILDIRIM SERIDI var:

    "Afet Ikaz Bildirimleri Kapali: Deprem aninda anlik acil durum push
     bildirimi alabilmek icin bildirim izni veriniz."   [Bildirim Iznini Ac]
                                                        [Test Alarmi Cal]

Bu, tarayicinin bildirim izni durumundan dogan bir uyari; makalenin konusuyla
ilgisi yok, uc sekilde de ayni yeri kapliyor ve okuyucunun dikkatini dagitiyor.

Serit sinirlari OLCULDU (2_risk_skoru.png, x=760 sutunu ve satir medyanlari):
    y <= 64    navbar zemini      (15, 22, 36)
    y  = 65    ayirici cizgi      (39, 45, 58)
    y  66-113  serit zemini       (21, 24, 40)
    y  = 114   serit amber kenari (84, 62, 29)
    y >= 115   sayfa zemini       (11, 15, 23)

Kirpma: satir 65-114 (50 piksel) atilir, navbar ile sayfa dogrudan birlesir.
Dikis gozle denetlendi, iz birakmiyor. Goruntu 1600x1050 -> 1600x1000.

EN-BOY ORANI: belgedeki `wp:extent` sabit kalirsa Word resmi %5 dikey ezer.
cy = cx * 1000/1600 ile yeniden hesaplanir (2628000 -> 1642500 EMU).

Ayni serit `4_isi_haritasi_guzergah.png`'de de var ama o goruntu belgede
KULLANILMIYOR (rId46, kullanim 0); yine de dosya tutarli olsun diye kirpilir.

Kosum:  python makale/analiz_arsivi/revize20.py
"""
import os
import re
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
HAZIR = os.path.join(KOK, "makale", "sekiller_hazir")
DST = os.path.join(KOK, "makale",
                   "QuakeMind_Makale_Taslak_2026-09-16_sekillieklendi_v3_LOCAL_2026-09-21.docx")
SRC = os.path.join(KOK, "makale", "arsiv",
                   "QuakeMind_Makale_YEDEK_pre_revize20_2026-09-29.docx")

UST, ALT = 65, 115          # kirpilacak bant: [UST, ALT)
YENI_CY = 1642500           # cx 2628000 icin 1600x1000 oranindaki yukseklik

# dosya adi -> docx icindeki medya parcasi
ESLEME = {
    "1_catlak_tespit.png": "word/media/image36.png",
    "2_risk_skoru.png": "word/media/image37.png",
    "3_nlp_harita.png": "word/media/image38.png",
    "4_isi_haritasi_guzergah.png": "word/media/image39.png",   # belgede kullanilmiyor
}


def serit_var_mi(a):
    """Kirpilacak bant gercekten serit mi (iki kez kosmaya karsi koruma)."""
    if a.shape[0] < ALT + 10:
        return False
    ayirici = tuple(np.median(a[65], axis=0).astype(int))
    kenar = tuple(np.median(a[114], axis=0).astype(int))
    return ayirici[0] > 30 and kenar[0] > kenar[2] + 30


def kirp(yol):
    im = Image.open(yol).convert("RGB")
    a = np.asarray(im)
    if not serit_var_mi(a):
        print(f"  ATLANDI (serit bulunamadi): {os.path.basename(yol)}")
        return False
    yeni = np.vstack([a[:UST], a[ALT:]])
    Image.fromarray(yeni).save(yol)
    print(f"  kirpildi: {os.path.basename(yol)}  {im.height} -> {yeni.shape[0]} piksel")
    return True


def main():
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    if not os.path.exists(SRC):
        shutil.copyfile(DST, SRC)
        print(f"yedek alindi: {os.path.basename(SRC)}")
    else:
        shutil.copyfile(SRC, DST)
        print(f"yedekten baslatildi: {os.path.basename(SRC)}")

    print("\n--- goruntuler ---")
    kirpilan = [ad for ad in ESLEME if kirp(os.path.join(HAZIR, ad))]
    if not kirpilan:
        raise SystemExit("hicbir goruntu kirpilmadi -- betik zaten kosulmus olabilir")

    print("\n--- docx ---")
    gecici = DST + ".yeni"
    with zipfile.ZipFile(DST) as girdi, \
            zipfile.ZipFile(gecici, "w", zipfile.ZIP_DEFLATED) as cikti:
        for ogre in girdi.infolist():
            ham = girdi.read(ogre.filename)
            ters = {v: k for k, v in ESLEME.items()}
            if ogre.filename in ters and ters[ogre.filename] in kirpilan:
                with open(os.path.join(HAZIR, ters[ogre.filename]), "rb") as f:
                    ham = f.read()
                print(f"  degistirildi: {ogre.filename} <- {ters[ogre.filename]}")
            elif ogre.filename == "word/document.xml":
                metin = ham.decode("utf-8")
                n = 0
                for rid in ("rId43", "rId44", "rId45"):
                    i = metin.find(f'r:embed="{rid}"')
                    if i < 0:
                        continue
                    # o cizime ait en yakin onceki extent/ext ciftini duzelt
                    bas = max(0, i - 3000)
                    parca = metin[bas:i]
                    yeni_parca, k = re.subn(
                        r'(cx="2628000" cy=")1724625(")',
                        r"\g<1>%d\g<2>" % YENI_CY, parca)
                    if k:
                        metin = metin[:bas] + yeni_parca + metin[i:]
                        n += k
                print(f"  document.xml: {n} yukseklik degeri 1724625 -> {YENI_CY}")
                ham = metin.encode("utf-8")
            cikti.writestr(ogre, ham)
    os.replace(gecici, DST)
    print(f"\nkaydedildi: {DST}")


if __name__ == "__main__":
    main()
