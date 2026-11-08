# -*- coding: utf-8 -*-
"""Makale semalari: Sekil 2 (mimari), Sekil 4 (karolama / harmanlama /
morfoloji) ve Sekil 6 (uc duzeyli degerlendirme protokolu).

Onceki surumler eski senaryoyu gosteriyordu (EMSR648 ile kesim duzeyi
karsilastirma, R0-R3 kollari, 'yol hasari bolutleme', HTTP 202 + yoklama,
seviye 1-2-3). Bu betik semalari bugunku koda gore cizer:
  - Sekil 4 (b) ve (d) dogrudan `apps/road_damage/utils/inference.py`
    fonksiyonlariyla uretilir (_create_weight_window, _postprocess_mask).
  - Eszamansiz uclar yalniz /api/road_damage/analyze ve /api/simulasyon/kos
    (HTTP 202); ilerleme SSE ile izlenir.

Cikti: benchmark/makale_sekilleri/sekil_mimari.png, sekil_karolama.png,
sekil_protokol.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

KOK = Path(__file__).resolve().parent
CIK = KOK / "benchmark" / "makale_sekilleri"
CIK.mkdir(parents=True, exist_ok=True)

MAVI, GRI, KOYU = "#1f6feb", "#6b7280", "#111827"
ZEMIN_VERI, ZEMIN_ORTAK, ZEMIN_VT = "#eaf1fb", "#fbeee6", "#eaf1fb"
KILIT = "#b42318"  # kirmizi yalniz aciliyet/kilit vurgusu icin
plt.rcParams.update({"font.size": 9, "savefig.dpi": 300, "savefig.bbox": "tight"})


def _kutu(ax, x, y, w, h, metin, zemin="white", kenar=KOYU, lw=1.2, boy=8.5, kalin=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.01",
                                facecolor=zemin, edgecolor=kenar, linewidth=lw))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center", fontsize=boy,
            fontweight="bold" if kalin else "normal", color=KOYU, wrap=True)


def _ok(ax, x0, y0, x1, y1, kesik=False, renk=KOYU):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=renk, lw=1.1,
                                linestyle=(0, (4, 3)) if kesik else "-", shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ Sekil 2
def sekil_mimari():
    f, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.set_xlim(-0.01, 1.05); ax.set_ylim(0, 1); ax.axis("off")
    for x, t in ((0.10, "VERİ EDİNME KATMANI"), (0.40, "ÇIKARIM KATMANI"), (0.86, "KARAR KATMANI")):
        ax.text(x, 0.97, t, ha="center", va="center", fontsize=10, fontweight="bold", color=MAVI)
    kanallar = [
        ("Uydu / İHA görüntüsü\n(OAM, Esri Wayback)", "Hasar bölütleme (MiT kodlayıcı)\n+ yol kenarı örneklemesi → kapanma", True),
        ("Yer seviyesi\nfotoğraf", "Çatlak + bina hasarı\nnesne tespiti (YOLOv8s)", False),
        ("Türkçe serbest\nmetin ihbarları", "BERTurk sınıflandırma\n+ varlık ismi tanıma", False),
        ("Konumlu tek dokunuşluk\nacil çağrılar", "Konum ayrıştırma\n(model gerekmez)", False),
        ("Sismik olay\nkatalogları", "Risk skorlaması\n(CatBoost)", False),
    ]
    ys = [0.78, 0.62, 0.46, 0.30, 0.14]
    for (veri, model, eszamansiz), y in zip(kanallar, ys):
        _kutu(ax, 0.01, y - 0.055, 0.18, 0.11, veri, zemin=ZEMIN_VERI, boy=8)
        _kutu(ax, 0.26, y - 0.055, 0.28, 0.11, model, boy=8)
        _ok(ax, 0.19, y, 0.26, y, kesik=eszamansiz)
        _ok(ax, 0.54, y, 0.60, 0.46, kesik=eszamansiz)
    _kutu(ax, 0.60, 0.36, 0.13, 0.20,
          "Ortak çıktı\nsözleşmesi:\nkonum – skor –\ngüven – zaman –\nkaynak tipi", zemin=ZEMIN_ORTAK,
          kenar="#e07a3f", boy=8)
    _kutu(ax, 0.76, 0.39, 0.09, 0.14, "Mekânsal\nveri tabanı\n(PostGIS)", zemin=ZEMIN_VT, kenar=MAVI, boy=8)
    _ok(ax, 0.73, 0.46, 0.76, 0.46)
    kararlar = [(0.74, "Kapanma-farkında\ngüzergâh"), (0.46, "En yakın toplanma\nalanı önerisi"),
                (0.18, "Isı haritası\n(çekirdek yoğunluk)")]
    for y, t in kararlar:
        _kutu(ax, 0.885, y - 0.06, 0.145, 0.12, t, boy=7.6)
        _ok(ax, 0.85, 0.46, 0.885, y)
    _kutu(ax, 0.875, 0.865, 0.165, 0.08, "Görev kilidi: aynı hedefe\nikinci talep → HTTP 409",
          kenar=KILIT, boy=7.2)
    _ok(ax, 0.9575, 0.865, 0.9575, 0.80, renk=KILIT)
    ax.plot([0.02, 0.07], [0.015, 0.015], color=KOYU, lw=1.1)
    ax.text(0.075, 0.015, "Eşzamanlı istek (HTTP 200)", va="center", fontsize=8)
    ax.plot([0.36, 0.41], [0.015, 0.015], color=KOYU, lw=1.1, linestyle=(0, (4, 3)))
    ax.text(0.415, 0.015, "Eşzamansız iş (HTTP 202 + iş kimliği; ilerleme SSE akışından)",
            va="center", fontsize=8)
    f.savefig(CIK / "sekil_mimari.png", facecolor="white"); plt.close(f)


# ------------------------------------------------------------------ Sekil 4
def sekil_karolama():
    from apps.road_damage.utils.inference import _create_weight_window, _postprocess_mask
    import cv2

    f = plt.figure(figsize=(11, 3.5))
    g = f.add_gridspec(1, 4, width_ratios=[1, 1, 1.1, 1.6], wspace=0.35)

    # (a) 1280 px goruntu, 512 px pencere, 256 px adim
    a = f.add_subplot(g[0]); a.set_xlim(0, 1280); a.set_ylim(1280, 0); a.set_aspect("equal")
    a.add_patch(Rectangle((0, 0), 1280, 1280, fill=False, lw=1.4, color=KOYU))
    for i, x in enumerate(range(0, 1280 - 512 + 1, 256)):
        for j, y in enumerate(range(0, 1280 - 512 + 1, 256)):
            a.add_patch(Rectangle((x, y), 512, 512, fill=True, alpha=0.07, color=MAVI, lw=0))
            a.add_patch(Rectangle((x, y), 512, 512, fill=False, lw=0.6, color=MAVI, alpha=0.6))
    a.add_patch(Rectangle((0, 0), 512, 512, fill=False, lw=1.8, color=MAVI))
    a.add_patch(Rectangle((256, 0), 512, 512, fill=False, lw=1.8, color="#e07a3f", linestyle="--"))
    a.annotate("", xy=(256, -40), xytext=(0, -40), arrowprops=dict(arrowstyle="<->", lw=1), annotation_clip=False)
    a.text(128, -80, "adım 256 px", ha="center", fontsize=7.5)
    a.set_xticks([]); a.set_yticks([]); a.set_title("(a) Örtüşmeli karolama (%50)", fontsize=9, pad=22)
    a.set_xlabel("1280 × 1280 px görüntü,\n512 px pencere (16 pencere)", fontsize=7.5)

    # (b) koddaki agirlik penceresi
    b = f.add_subplot(g[1])
    w = _create_weight_window(512)
    im = b.imshow(w, cmap="Blues", extent=(0, 1, 1, 0), vmin=0, vmax=1)
    b.contour(np.linspace(0, 1, 512), np.linspace(0, 1, 512), w, levels=[0.25, 0.5, 0.75], colors="k",
              linewidths=0.5)
    b.set_xlabel("u = i / (S − 1)", fontsize=8); b.set_ylabel("v = j / (S − 1)", fontsize=8)
    b.tick_params(labelsize=7)
    b.set_xticks([0, 0.5, 1]); b.set_xticklabels(["0", "0,5", "1"])
    b.set_yticks([0, 0.5, 1]); b.set_yticklabels(["0", "0,5", "1"])
    b.set_title("(b) Ağırlık penceresi (Denk. 5)", fontsize=9)
    cb = f.colorbar(im, ax=b, fraction=0.046, pad=0.03); cb.ax.tick_params(labelsize=7)

    # (c) tek boyutta iki komsu karonun agirliklari ve normalize toplam
    c = f.add_subplot(g[2])
    x = np.arange(0, 768)
    w1 = np.zeros(768); w1[:512] = w[256, :]
    w2 = np.zeros(768); w2[256:] = w[256, :]
    top = w1 + w2
    c.plot(x, w1, color=MAVI, lw=1.4, label="karo A ağırlığı")
    c.plot(x, w2, color="#e07a3f", lw=1.4, linestyle="--", label="karo B ağırlığı")
    with np.errstate(invalid="ignore", divide="ignore"):
        pa, pb = 0.3, 0.7  # iki karonun ayni piksel icin farkli kestirimi
        birlesik = np.where(top > 0, (pa * w1 + pb * w2) / np.maximum(top, 1e-6), np.nan)
    c.plot(x, birlesik, color=KOYU, lw=1.6, label="birleşik olasılık (Denk. 6)")
    c.axvspan(256, 512, color=GRI, alpha=0.08)
    c.set_ylim(-0.05, 1.1); c.set_xlabel("piksel (tek satır)", fontsize=8); c.tick_params(labelsize=7)
    c.legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    c.set_title("(c) Örtüşme bölgesinde harmanlama", fontsize=9)

    # (d) koddaki morfolojik son isleme, seviye 0/1/2
    rng = np.random.default_rng(42)
    m = np.zeros((160, 160), np.uint8)
    cv2.ellipse(m, (80, 80), (52, 34), 20, 0, 360, 1, -1)
    gurultu = rng.random(m.shape)
    m[(gurultu < 0.06)] = 1           # daginik yanlis pozitif pikseller
    m[(gurultu > 0.93) & (m == 1)] = 0  # blob icinde delikler
    cv2.circle(m, (22, 130), 5, 1, -1)  # kucuk ayri bilesen
    d = g[3].subgridspec(1, 3, wspace=0.08)
    for k, (sev, ad) in enumerate(((0, "Seviye 0\n(ham)"), (1, "Seviye 1"), (2, "Seviye 2"))):
        ax = f.add_subplot(d[k])
        out = _postprocess_mask(m.copy(), level=sev)
        ax.imshow(1 - out, cmap="gray", vmin=0, vmax=1)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(ad, fontsize=7.5)
        if k == 1:
            ax.text(0.5, 1.45, "(d) Morfolojik son işleme", transform=ax.transAxes, ha="center", fontsize=9)
        ax.set_xlabel({0: "değişiklik yok", 1: "3×3 aç/kapa\n<30 px sil",
                       2: "5×5 aç/7×7 kapa\n<150 px sil"}[sev], fontsize=6.3)
    f.text(0.5, -0.27, "Paneller şematiktir; (b) ve (d) doğrudan çıkarım kodunun fonksiyonlarıyla "
           "(inference.py) üretilmiştir, (d)'deki maske sentetik bir örnektir.", ha="center", fontsize=7.5, color=GRI)
    f.savefig(CIK / "sekil_karolama.png", facecolor="white"); plt.close(f)


# ------------------------------------------------------------------ Sekil 6
def sekil_protokol():
    f, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    kutular = [
        (0.80, "#eaf1fb", MAVI, "(i) Bileşen düzeyi",
         "Her model kendi ölçütüyle, kendi ayrık sınama kümesinde değerlendirilir: bölütleme IoU_hasar\n"
         "(Tablo 12), metin sınıflandırma mikro/makro-F₁ (Tablo 21), risk skorlaması PR-AUC (Tablo 22)."),
        (0.57, "#fbeee6", "#e07a3f", "(ii) Kapanma düzeyi",
         "Kapanma katmanı, drone ortofotosu üzerinde kör olarak elle işaretlenen yol parçalarıyla\n"
         "karşılaştırılır (Bölüm 4.3): kesinlik ve duyarlılık; yargılanamayan parçalar ayrıca sayılır."),
    ]
    for y, zemin, kenar, bas, govde in kutular:
        ax.add_patch(FancyBboxPatch((0.02, y - 0.09), 0.96, 0.18, boxstyle="round,pad=0.005,rounding_size=0.01",
                                    facecolor=zemin, edgecolor=kenar, lw=1.6))
        ax.text(0.04, y + 0.045, bas, fontsize=11, fontweight="bold", color=kenar, va="center")
        ax.text(0.04, y - 0.025, govde, fontsize=8.6, va="center", color=KOYU)
    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.43, boxstyle="round,pad=0.005,rounding_size=0.01",
                                facecolor="#eef6ee", edgecolor="#3f8f5a", lw=1.6))
    ax.text(0.04, 0.415, "(iii) Görev tabanlı düzey", fontsize=11, fontweight="bold", color="#3f8f5a", va="center")
    ax.text(0.04, 0.32,
            "Aynı ekip–afetzede çiftleri (beş giriş ağzı × en çok beş afetzede, beş tur) üç kolla koşulur; kollar\n"
            "yalnız güzergâh hesabında ayrışır. Raporlanan: görev başına erişim süresi, ulaşılamayan görev ve keşif\n"
            "sayısı; ortalamalar yalnız bütün kolların ulaştığı ortak görevlerden alınır.",
            fontsize=8.6, va="center", color=KOYU)
    xs = [0.16, 0.50, 0.84]
    adlar = [("Kapanmayı bilmeyen ekip", "kapalı kenarı varınca öğrenir;\nkeşif başına 1,42 dk"),
             ("Telsizle paylaşan filo", "bir ekibin öğrendiği kapanma\nbütün ekiplere yayılır"),
             ("QuakeMind", "analizin kapanmaları baştan\nbilinir (dünya = model çıktısı)")]
    ax.plot([0.10, 0.90], [0.155, 0.155], color=KOYU, lw=1.6)
    ax.annotate("", xy=(0.93, 0.155), xytext=(0.88, 0.155), arrowprops=dict(arrowstyle="-|>", lw=1.6, color=KOYU))
    ax.text(0.10, 0.19, "artan kapanma bilgisi →", fontsize=8.5, color=KOYU)
    for x, (ad, alt), renk in zip(xs, adlar, (GRI, GRI, MAVI)):
        ax.plot([x], [0.155], "o", ms=11, color=renk, mec=KOYU)
        ax.text(x, 0.105, ad, ha="center", fontsize=9, fontweight="bold")
        ax.text(x, 0.05, alt, ha="center", fontsize=7.6, color="#374151")
    f.savefig(CIK / "sekil_protokol.png", facecolor="white"); plt.close(f)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(KOK))
    for fn in (sekil_mimari, sekil_karolama, sekil_protokol):
        fn(); print("uretildi:", fn.__name__)
