# -*- coding: utf-8 -*-
"""Makale Sekil 1: Bolum 2'de tartisilan uygulamali calismalarin konumu.

Onceki Sekil 1'in ureticisi depoda yoktu ve ~42 noktanin hicbiri bir kaynaga
bagli degildi; sag ustteki uc nokta metindeki "boyle bir calismaya
rastlanmamistir" iddiasiyla celisiyordu (kural 1: her sayinin kaynagi var).
Bu betikte HER KUTU bir kaynak numarasidir ve yeri asagidaki tabloda
gerekcesiyle yazilidir.

Eksenler (niteliksel, Bolum 2.1-2.4'teki anlatima gore):
  yatay — kullanilan algilama kanali: yok (kapanma elle / sentetik),
          tek kanal (uydu/hava ya da yer seviyesi), iki kanal, uc kanal
  dusey — ciktinin ulastigi karar duzeyi: veri kumesi/kiyaslama, model
          ciktisi (maske/sinif), hasar haritasi, erisilebilirlik/guzergah,
          ekip sevki (atama + guzergah)

Disarida birakilanlar: genel amacli mimariler ve algoritmalar ([14]-[21],
[34]-[36], [40]-[44]), dil modelleri ([32], [33]) ve derleme [7] -- bunlar
bir afet sistemi degil, yapi tasidir.

Cikti: benchmark/makale_sekilleri/sekil_yazin_konumu.png
Kosum: venv/Scripts/python.exe araclar_makale_yazin_konumu.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

KOK = Path(__file__).resolve().parent
CIK = KOK / "benchmark" / "makale_sekilleri"
CIK.mkdir(parents=True, exist_ok=True)

MAVI, GRI, KOYU, ACIK = "#1f6feb", "#6b7280", "#111827", "#e5e7eb"
plt.rcParams.update({"font.size": 9, "savefig.dpi": 300, "savefig.bbox": "tight"})

SUTUNLAR = ["Yok\n(kapanma elle\nya da sentetik)", "Tek kanal:\nuydu / hava", "Tek kanal:\nyer seviyesi",
            "İki kanal", "Üç kanal\n(uydu · yer · metin)"]
SATIRLAR = ["Veri kümesi /\nkıyaslama", "Model çıktısı\n(maske, sınıf)", "Hasar haritası",
            "Erişilebilirlik /\ngüzergâh", "Ekip sevki\n(atama + güzergâh)"]

# kaynak -> (sutun, satir, gerekce: Bolum 2'deki ifade)
KAYNAKLAR = {
    9: (1, 0, "§2.1: xBD, alanın referans veri kümesi"),
    11: (1, 0, "§2.1: TE23D, hasar değerlendirme kümesi ve protokolü"),
    12: (1, 0, "§2.1: BRIGHT, çok kipli (optik + radar) bina hasarı kümesi"),
    37: (1, 0, "§2.2: RescueNet, İHA tabanlı küme"),
    10: (1, 1, "§2.1: TUE-CD, çok ölçekli etkileşim ağıyla bina değişim tespiti"),
    13: (1, 1, "§2.1: radar + mekânsal veriyle hasar çerçevesi"),
    22: (1, 1, "§2.1: dört mimarinin bölütleme karşılaştırması"),
    23: (1, 1, "§2.1: vektör güdümlü yol hasarı çıkarımı"),
    24: (1, 1, "§2.1: SAM gömüleriyle yol hasarı; çıktı maske olarak kalır"),
    25: (1, 1, "§2.1: uydu ile yol hasarı tespiti"),
    29: (1, 2, "§2.1: DamageScope; hasar haritası ve web görselleştirme, güzergâh yok"),
    5: (1, 3, "§2.4: uydudan belirlenen tıkanıklık + en yakın tesis ağ analizi"),
    26: (2, 0, "§2.2: EIDSeg, küme + sekiz mimari kıyası"),
    27: (2, 0, "§2.2: MEDIC, çok görevli küme"),
    28: (2, 0, "§2.2: DSS, yer seviyesi küme"),
    38: (2, 0, "§2.2: PEER Hub ImageNet, kıyaslama kümesi"),
    39: (2, 1, "§2.2: öğrenme aktarımıyla yapısal hasar tanıma"),
    30: (0, 3, "§2.4: openrouteservice afet sürümü; kapanma gönüllülerce elle"),
    31: (0, 3, "§2.4: sentetik kesintilerle Monte Carlo erişilebilirlik"),
}


def _kutu(ax, x, y, metin, zemin, kenar, renk, boy=7.6, kalin=False, w=0.22, h=0.17):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.03",
                                facecolor=zemin, edgecolor=kenar, linewidth=0.9))
    ax.text(x, y, metin, ha="center", va="center", fontsize=boy, color=renk,
            fontweight="bold" if kalin else "normal")


def main() -> int:
    f, ax = plt.subplots(figsize=(7.6, 4.9))
    ns, nr = len(SUTUNLAR), len(SATIRLAR)
    ax.set_xlim(-0.5, ns - 0.5); ax.set_ylim(-0.5, nr - 0.5)
    for i in range(ns + 1):
        ax.axvline(i - 0.5, color=ACIK, lw=0.8, zorder=0)
    for j in range(nr + 1):
        ax.axhline(j - 0.5, color=ACIK, lw=0.8, zorder=0)

    hucre = {}
    for n, (s, r, _g) in sorted(KAYNAKLAR.items()):
        hucre.setdefault((s, r), []).append(n)
    for (s, r), liste in hucre.items():
        sutun_basi = 3
        satir_say = (len(liste) + sutun_basi - 1) // sutun_basi
        for k, n in enumerate(liste):
            i, j = k % sutun_basi, k // sutun_basi
            adet = min(sutun_basi, len(liste) - j * sutun_basi)
            x = s + (i - (adet - 1) / 2) * 0.27
            y = r + ((satir_say - 1) / 2 - j) * 0.22
            _kutu(ax, x, y, f"[{n}]", "white", GRI, KOYU)
    _kutu(ax, 4, 4, "Bu çalışma", "#eaf1fb", MAVI, MAVI, boy=8.2, kalin=True, w=0.62, h=0.2)

    ax.set_xticks(range(ns)); ax.set_xticklabels(SUTUNLAR, fontsize=7.8)
    ax.set_yticks(range(nr)); ax.set_yticklabels(SATIRLAR, fontsize=7.8)
    ax.tick_params(length=0)
    for k in ax.spines.values():
        k.set_color(ACIK)
    ax.set_xlabel("Algılama ekseni: kullanılan algılama kanalı", fontsize=8.6, labelpad=6)
    ax.set_ylabel("Karar ekseni: çıktının ulaştığı düzey", fontsize=8.6, labelpad=6)
    # Siniflamanin niteliksel oldugu ve disarida birakilanlar makaledeki
    # sekil altyazisinda yazili (sekil icine konunca eksen yazisina biniyordu).
    hedef = CIK / "sekil_yazin_konumu.png"
    f.savefig(hedef)
    print(f"{len(KAYNAKLAR)} kaynak -> {hedef}")
    for n, (s, r, g) in sorted(KAYNAKLAR.items()):
        print(f"  [{n:>2}] {SUTUNLAR[s].splitlines()[0]:<12} | {SATIRLAR[r].splitlines()[0]:<16} | {g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
