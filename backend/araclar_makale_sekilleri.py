# -*- coding: utf-8 -*-
"""Makaleye girecek grafikleri uretir (Word'e dokunmadan, dosya olarak).

Tatbikat grafikleri (kollar, duyarlilik, model secimi, kesif-kazanc) sayilari
DOGRUDAN kosu ciktilarindan okur (`araclar_b0_kos.sh` klasoru): eskiden sayilar
buraya elle yaziliyordu ve kod duzeltilip yeniden kosulunca sekiller eskide
kaliyordu. Cikarim sureleri ve sure dagilimi i7-12700H olcumudur
(SIMULASYON_OLCUM_KAYDI.md §14); onlar sabit kalir.

    python araclar_makale_sekilleri.py [--sonuc benchmark/reports/tatbikat_b0]
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CIK = Path(__file__).resolve().parent / "benchmark" / "makale_sekilleri"
CIK.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "figure.dpi": 200, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
    # Turkce ondalik ayirici: butun eksenlerde virgul.
    "axes.formatter.use_locale": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
})
# Renk: kirmizi/turuncu YALNIZ hasar ve aciliyet icin (ARAYUZ §6).
GRI, ORTA, VURGU = "#6b7280", "#9ca3af", "#1f6feb"
HASAR = "#d1332e"

ALAN = ["Defne / Elektrik", "İslahiye", "Nurdağı"]
MODEL = {"segformer_mitb0_p2_t42": "MiT-B0", "segformer_mitb2_p2_t42": "MiT-B2",
         "unet_mitb4_p2_t42": "U-Net MiT-B4"}
B_, T_, Q_ = "Kapanmayı bilmeyen ekip", "Telsizle paylaşan filo", "QuakeMind"

_ap = argparse.ArgumentParser()
_ap.add_argument("--sonuc", default=str(Path(__file__).resolve().parent / "benchmark" / "reports" / "tatbikat_b0"))
SONUC = Path(_ap.parse_args().sonuc)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from araclar_tatbikat_ozet import alan_ozeti  # noqa: E402


def _alan_adi(ad):
    return "Defne / Elektrik" if ad.startswith("Defne") else ad


def _ozet():
    """(alan, model) -> alan_ozeti satiri; uc modelin ana kosusundan."""
    d = {}
    for f in ("sonuc_b0.json", "sonuc_b2.json", "sonuc_unet.json"):
        for s in json.loads((SONUC / f).read_text(encoding="utf-8")):
            r = alan_ozeti(s)
            d[(_alan_adi(r["alan"]), MODEL.get(r["model"], r["model"]))] = r
    return d


def _tohum_kazanci(dosya, tohum="42"):
    """Tek tohumlu duyarlilik kosusu: alan -> QuakeMind kazanci (%)."""
    k = {}
    for s in json.loads((SONUC / dosya).read_text(encoding="utf-8")):
        v = ((s.get("kollarTohum") or {}).get(tohum) or {}).get("varyantlar") or {}
        b, q = (v.get(B_) or {}).get("ortalamaSureDk"), (v.get(Q_) or {}).get("ortalamaSureDk")
        k[_alan_adi(s["alan"])] = 100.0 * (b - q) / b if b and q is not None else np.nan
    return k


OZET = _ozet()

# --- Sekil 1: kiyas kollari (ana kosu, buyuk model, 25 cift) ---------------
def sekil_kollar():
    kol = ["Kapanmayı bilmeyen\nekip", "Telsizle paylaşan\nfilo", "QuakeMind"]
    veri = {a: [OZET[(a, "U-Net MiT-B4")][k][0] for k in ("bilmeyen", "telsiz", "quakemind")]
            for a in ALAN}
    hata = {a: [OZET[(a, "U-Net MiT-B4")][k][1] for k in ("bilmeyen", "telsiz", "quakemind")]
            for a in ALAN}
    f, ax = plt.subplots(figsize=(6.2, 3.1))
    x = np.arange(len(ALAN)); g = 0.26
    for i, (k, renk) in enumerate(zip(kol, [GRI, ORTA, VURGU])):
        d = [veri[a][i] for a in ALAN]; e = [hata[a][i] for a in ALAN]
        ax.bar(x + (i - 1) * g, d, g * 0.92, yerr=e, capsize=3, label=k,
               color=renk, edgecolor="white", linewidth=0.6)
        for xi, v, h in zip(x + (i - 1) * g, d, e):
            # etiket hata cubugunun USTUNE: cubugun ortasina binince okunmuyordu
            ax.text(xi, v + h + 0.10, f"{v:.2f}".replace(".", ","), ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(ALAN)
    ax.set_ylabel("Ortalama erişim süresi (dk)")
    ax.set_title("Kapanmayı önceden bilmenin erişim süresine etkisi\n"
                 "(U-Net MiT-B4, 5 giriş ağzı × en çok 5 afetzede, 5 tohum)", pad=8)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.16))
    ax.set_ylim(0, max(veri[a][i] + hata[a][i] for a in ALAN for i in range(3)) * 1.18)
    f.savefig(CIK / "sekil_kiyas_kollari.png"); plt.close(f)


# --- Sekil 2: duyarlilik, eski 20 dk sabitinin etkisi -----------------------
def sekil_duyarlilik():
    kosu = ["Değerlendirme\n0,5 dk", "ANA\n(1,0 dk)", "Değerlendirme\n2,0 dk",
            "ESKİ SABİT\n(20 dk)"]
    sirali = [_tohum_kazanci("duy_deg_0.5.json"), _tohum_kazanci("sonuc_unet.json"),
              _tohum_kazanci("duy_deg_2.0.json"), _tohum_kazanci("duy_deg_20.json")]
    kazanc = {a: [k[a] for k in sirali] for a in ALAN}
    f, ax = plt.subplots(figsize=(6.2, 3.1))
    x = np.arange(len(kosu))
    for a, isaret in zip(ALAN, ["o", "s", "^"]):
        ax.plot(x, kazanc[a], marker=isaret, color=VURGU if a == "Nurdağı" else GRI,
                linewidth=1.6, markersize=5, label=a,
                alpha=1.0 if a == "Nurdağı" else 0.75)
    ax.axvspan(2.5, 3.5, color=HASAR, alpha=0.07)
    ax.text(3, 99, "kullanılmıyor", ha="center", fontsize=7.5, color=HASAR)
    ax.set_xticks(x); ax.set_xticklabels(kosu, fontsize=8)
    ax.set_ylabel("QuakeMind kolunun kazancı (%)"); ax.set_ylim(0, 105)
    ax.set_title("Sonuç, beyan edilen değerlendirme süresine ne kadar bağlı?\n"
                 "(U-Net MiT-B4, tohum 42 — eski 20 dk'lık sabit sonucu tek başına üretiyor)",
                 pad=8, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="center left")
    f.savefig(CIK / "sekil_duyarlilik.png"); plt.close(f)


# --- Sekil 3: model secimi, sure - dogruluk - operasyonel kazanc ------------
def sekil_model():
    ad = ["Hızlı\nMiT-B0", "Dengeli\nMiT-B2", "Büyük\nU-Net MiT-B4"]
    sure = [1.91, 4.71, 10.50]
    iou = [0.382, 0.409, 0.433]
    kazanc = {a: [(OZET[(a, m)]["kazanc"][0]
                   if OZET[(a, m)].get("kazanc") and OZET[(a, m)]["kazanc"][0] is not None else np.nan)
                  for m in ("MiT-B0", "MiT-B2", "U-Net MiT-B4")] for a in ALAN}
    f, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.0))
    # Iki panel arasi bosluk: ikiz eksenin "Sinama IoU" etiketi sag panelin
    # y etiketine biniyordu.
    f.subplots_adjust(wspace=0.52)
    a1.bar(ad, sure, 0.5, color=ORTA, edgecolor="white")
    a1.set_ylabel("Çıkarım süresi (sn)")
    for i, (s, v) in enumerate(zip(sure, iou)):
        a1.text(i, s + 0.25, f"{s:.2f} sn".replace(".", ","), ha="center", fontsize=8)
    b = a1.twinx(); b.plot(ad, iou, marker="o", color=VURGU, linewidth=1.6)
    b.set_ylabel("Sınama IoU", color=VURGU, labelpad=2)
    b.tick_params(axis="y", colors=VURGU, pad=1)
    b.set_ylim(0.35, 0.46); b.grid(False)
    # Tik cizgileri kucuk olcekte eksi isareti gibi okunuyordu; ice alindi.
    b.tick_params(axis="y", direction="in", length=2)
    b.set_yticks([0.36, 0.38, 0.40, 0.42, 0.44, 0.46])
    b.set_yticklabels([f"{v:.2f}".replace(".", ",") for v in
                       (0.36, 0.38, 0.40, 0.42, 0.44, 0.46)])
    a1.set_title("5,5 kat süre → +0,051 IoU", pad=6)
    for a, isaret in zip(ALAN, ["o", "s", "^"]):
        a2.plot(ad, kazanc[a], marker=isaret, linewidth=1.6, markersize=5, label=a,
                color=VURGU if a == "İslahiye" else GRI,
                alpha=1.0 if a == "İslahiye" else 0.75)
    a2.set_ylabel("QuakeMind kazancı (%)"); a2.set_ylim(0, 75)
    a2.set_title("Operasyonel kazanç tek yönlü artmıyor", pad=6)
    a2.legend(frameon=False, fontsize=7.5, loc="lower right")
    f.suptitle("Model seçimi: süre, doğruluk ve sevk zincirindeki karşılığı", y=1.02)
    f.savefig(CIK / "sekil_model_secimi.png", bbox_inches="tight"); plt.close(f)


# --- Sekil 4: sure dagilimi -------------------------------------------------
def sekil_sure():
    asama = ["Model çıkarımı", "Lojistik", "Kıyas kolları", "Rota koşusu",
             "Mahalle grafiği", "Kurulum"]
    sn = [9.12, 1.63, 0.49, 0.38, 0.32, 0.01]
    f, ax = plt.subplots(figsize=(5.6, 2.6))
    y = np.arange(len(asama))[::-1]
    renk = [VURGU] + [ORTA] * (len(asama) - 1)
    ax.barh(y, sn, 0.62, color=renk, edgecolor="white")
    for yi, v in zip(y, sn):
        ax.text(v + 0.18, yi, f"{v:.2f} sn".replace(".", ","), va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels(asama)
    ax.set_xlabel("Süre (sn) — 20 çekirdekli CPU, 6 iş parçacığı, GPU yok")
    ax.set_xlim(0, 11.4)
    ax.set_title("Tatbikat koşusunda süre nereye gidiyor?  (toplam 15,0 sn)", pad=6)
    f.savefig(CIK / "sekil_sure_dagilimi.png"); plt.close(f)


# --- Sekil 12: kesif sayisi - kazanc (Tablo 16'nin sekiz satiri) -----------
def sekil_kesif():
    # (alan, model, kesif [kapanmayi bilmeyen ekip], kazanc %, s.s. %, kume)
    satir = []
    for (a, m), r in sorted(OZET.items()):
        if not r.get("gecerliTohum"):
            continue  # arac rotasi yok (Defne, MiT-B0)
        tek = r["kume"].startswith("1/")
        satir.append((a, m, r["kesifBilmeyen"][0], r["kazanc"][0],
                      None if tek else r["kazanc"][1], r["kume"]))
    isaret = {"Defne / Elektrik": "o", "İslahiye": "s", "Nurdağı": "^"}
    global ETIKET_KESIF
    # Etiket kaydirmalari 28 Eylul yeniden kosusunun noktalarina gore (nokta
    # konumu degisirse burasi da gozden gecirilmeli: MiT-B0 ve U-Net
    # Islahiye'de ust uste).
    ETIKET_KESIF = {
        ("Defne / Elektrik", "MiT-B2"): ("MiT-B2 (Defne)", (-66, -3)),
        ("Defne / Elektrik", "U-Net MiT-B4"): ("U-Net MiT-B4 (Defne)", (7, -2)),
        ("İslahiye", "MiT-B2"): ("MiT-B2 (İslahiye)", (8, 2)),
        ("İslahiye", "MiT-B0"): ("MiT-B0 (İslahiye)", (-4, -15)),
        ("İslahiye", "U-Net MiT-B4"): ("U-Net MiT-B4 (İslahiye)", (8, 3)),
    }
    f, ax = plt.subplots(figsize=(6.2, 3.2))
    for a in ALAN:
        r = [x for x in satir if x[0] == a]
        ax.errorbar([x[2] for x in r], [x[3] for x in r],
                    yerr=[x[4] or 0 for x in r], fmt=isaret[a], ms=6, capsize=3,
                    color=VURGU if a == "Nurdağı" else GRI, label=a,
                    mfc="white" if a == "Defne / Elektrik" else None)
        for x in r:
            # Defne ve Islahiye MiT-B2 noktalari neredeyse ust uste; etiketler
            # nokta bazinda kaydirilir.
            yazi, kay = ETIKET_KESIF.get((a, x[1]), (x[1], (6, 4)))
            ax.annotate(yazi, (x[2], x[3]), textcoords="offset points", xytext=kay,
                        fontsize=6.8, color="#374151")
    ax.set_xlabel("Keşif sayısı, kapanmayı bilmeyen ekip (makale Tablo 16)")
    ax.set_ylabel("QuakeMind kolunun kazancı (%)")
    ax.set_xlim(-1, 50); ax.set_ylim(0, 80)
    ax.set_title("Kazanç, kapanmaların ekip rotalarına düşme sıklığını izler\n"
                 "(boş işaret: Defne, beş tohum tek kurulum veriyor — küme 1/5)", pad=8)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    f.savefig(CIK / "sekil_kesif_kazanc.png"); plt.close(f)


for f in (sekil_kollar, sekil_duyarlilik, sekil_model, sekil_sure, sekil_kesif):
    f(); print("uretildi:", f.__name__)
print("dizin:", CIK)
