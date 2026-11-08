"""05 Deprem Risk Skoru - makale formatinda detayli Word raporu uretir.

    python build_docx_report_risk.py

Girdi: results/*.json + results/*.png (run_all_risk.py cikisi)
Cikti: results/05_Deprem_Risk_Skoru_Rapor.docx
"""
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

ORDER = ["catboost", "random_forest", "xgboost", "logistic_regression",
         "lightgbm", "stacking_ensemble", "mlp"]

FEATURE_DESC = {
    "latitude": "Enlem", "longitude": "Boylam", "depth": "Derinlik (km)",
    "rolling_mean_7d": "Son 7 olayin ortalama buyuklugu",
    "rolling_std_7d": "Son 7 olayin buyukluk std sapmasi",
    "rolling_max_7d": "Son 7 olayin maksimum buyuklugu",
    "event_count_7d": "Son 7 olay penceresindeki olay sayisi",
    "year": "Yil", "month": "Ay", "day": "Gun", "hour": "Saat",
    "day_of_year": "Yilin gunu", "days_since_start": "Baslangictan bu yana gecen gun",
    "sin_month": "Ay (dongusel sin)", "cos_month": "Ay (dongusel cos)",
    "sin_hour": "Saat (dongusel sin)", "cos_hour": "Saat (dongusel cos)",
    "distance_to_fault": "En yakin bilinen fay hattina mesafe (km)",
}


def load_results():
    out = {}
    for n in ORDER:
        p = RESULTS / f"{n}.json"
        if p.exists():
            out[n] = json.load(open(p, encoding="utf-8"))
    return out


def load_dataset_info():
    return json.load(open(RESULTS / "dataset_info.json", encoding="utf-8"))


def set_cell_shading(cell, color_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): color_hex})
    tc_pr.append(shd)


def add_table(doc, headers, rows, col_widths_cm=None, header_color="4472C4"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = str(h)
        for p in hdr[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
        set_cell_shading(hdr[i], header_color)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for p in cells[i].paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if col_widths_cm:
        for i, w in enumerate(col_widths_cm):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


def add_figure(doc, img_path, caption, width_cm=15):
    if not img_path.exists():
        return
    doc.add_picture(str(img_path), width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(caption)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)


def fmt(x, nd=4):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def main():
    results = load_results()
    ds = load_dataset_info()

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    title = doc.add_heading(
        "30 Günlük Deprem Riski Sınıflandırmasında Makine Öğrenmesi Modellerinin "
        "Karşılaştırmalı Değerlendirmesi", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("QuakeMind Projesi — Yerel Deneysel Çalışma Raporu")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True

    # ---- Ozet ----
    doc.add_heading("Özet", level=1)
    doc.add_paragraph(
        f"Bu çalışmada, USGS/Kandilli deprem kataloğundan türetilen {ds['n_total']} kayıt ve "
        f"{ds['n_features']} özellik kullanılarak, bir noktada önümüzdeki 30 gün içinde 100 km "
        "yarıçapında M≥4,0 büyüklüğünde bir deprem meydana gelip gelmeyeceğini öngören ikili "
        "sınıflandırma problemi ele alınmıştır. Zaman-serisi doğasına uygun olarak walk-forward "
        "(TimeSeriesSplit, 5 kat) çapraz doğrulama protokolü kullanılmış; CatBoost, XGBoost, "
        "LightGBM, Random Forest, Lojistik Regresyon, çok katmanlı algılayıcı (MLP) ve bu üç ağaç "
        "tabanlı modelin yığınlanmasıyla oluşturulan bir topluluk modeli AYNI protokolle "
        "karşılaştırılmıştır. CatBoost (ROC-AUC ort.=" +
        fmt(results["catboost"]["roc_auc_mean"], 3) + ") ve Random Forest "
        "(ROC-AUC ort.=" + fmt(results["random_forest"]["roc_auc_mean"], 3) +
        ") en iyi performansı gösterirken, MLP (ROC-AUC ort.=" +
        fmt(results["mlp"]["roc_auc_mean"], 3) + ") tesadüfi tahminin altında kalarak bu küçük "
        "tablo veri setinde derin öğrenmenin dezavantajlı olduğunu göstermiştir."
    )

    # ---- 1. Giris ----
    doc.add_heading("1. Giriş ve Görev Tanımı", level=1)
    doc.add_paragraph(
        "Hedef değişken (`label_30d`): bir depremin, kendisinden sonraki 30 gün içinde 100 km "
        "yarıçapında M≥4,0 büyüklüğünde başka bir deprem tetiklenip tetiklenmediğini gösteren "
        "ikili etikettir. Ana şoklara odaklanmak için basit bir artçı-şok ayıklama (declustering) "
        "adımı (1 gün / 50 km penceresi, küçük-büyüklük kriteriyle) uygulanmıştır. Bu görev, "
        "üretim ortamındaki `backend/apps/earthquake_risk/risk_engine.py` modülündeki "
        "özellik mühendisliğini birebir yeniden üretmektedir; böylece bu çalışmanın sonuçları "
        "üretim modeliyle doğrudan karşılaştırılabilir."
    )

    doc.add_heading("1.1 Özellikler", level=2)
    doc.add_paragraph(
        f"Modellere verilen {ds['n_features']} özellik dört kategoriye ayrılır: (i) konumsal "
        "(enlem, boylam, derinlik, en yakın fay hattına mesafe), (ii) kısa vadeli sismik aktivite "
        "(son 7 olayın ortalama/std/maksimum büyüklüğü, olay sayısı), (iii) zamansal (yıl, ay, gün, "
        "saat, yılın günü, başlangıçtan bu yana gün) ve (iv) döngüsel kodlama (ay ve saatin "
        "sinüs/kosinüs dönüşümleri)."
    )
    add_table(doc, ["Özellik", "Açıklama"],
              [[f, FEATURE_DESC.get(f, "-")] for f in ds["feature_names"]],
              col_widths_cm=[5, 10])

    doc.add_paragraph(
        f"Veri kümesindeki pozitif sınıf oranı %{100*ds['positive_rate']:.1f} olup zaman aralığı "
        f"{ds['time_min'][:10]} ile {ds['time_max'][:10]} arasındadır."
    )

    # ---- 2. Protokol ----
    doc.add_heading("2. Deneysel Protokol", level=1)
    doc.add_paragraph(
        "Örnekler zamana göre sıralanmış ve sklearn `TimeSeriesSplit` ile 5 kata bölünmüştür; "
        "her katta EĞİTİM verisi test verisinden KRONOLOJİK OLARAK ÖNCE gelir — bu, geleceği "
        "kullanarak geçmişi tahmin etme (veri sızıntısı) riskini ortadan kaldırır ve üretim "
        "koşullarını (yalnızca geçmiş veriyle geleceği tahmin etme) taklit eder. Her model, "
        "AYNI 5 kat üzerinde, kat-dışı (out-of-fold, OOF) tahminler üretecek şekilde eğitilmiş; "
        "raporlanan tüm metrikler bu OOF tahminlerden hesaplanmıştır."
    )
    doc.add_paragraph(
        "Değerlendirme ölçütleri: ROC-AUC, PR-AUC (average precision), doğruluk, dengelenmiş "
        "doğruluk, kesinlik, duyarlılık, F1, Matthews korelasyon katsayısı (MCC) ve Brier skoru "
        "(olasılık kalibrasyon hatası). Karar eşiği tüm modeller için 0,5 olarak sabitlenmiştir."
    )

    # ---- 3. Yontem ----
    doc.add_heading("3. Modeller ve Hiperparametreler", level=1)
    param_rows = []
    for n in ORDER:
        if n not in results:
            continue
        p = results[n]["params"]
        param_rows.append([results[n]["title"], ", ".join(f"{k}={v}" for k, v in p.items())])
    add_table(doc, ["Model", "Hiperparametreler"], param_rows, col_widths_cm=[4, 11])
    doc.add_paragraph(
        "Lojistik Regresyon ve MLP için özellikler `StandardScaler` ile ölçeklenmiştir "
        "(her katta yalnızca o katın eğitim verisiyle uyumlanır — sızıntı yoktur). Ağaç tabanlı "
        "modeller ham özelliklerle çalışır. Yığınlanmış topluluk modeli, CatBoost + LightGBM + "
        "Random Forest çıktılarını 3-kat iç çapraz doğrulamayla bir Lojistik Regresyon "
        "meta-öğreniciye besler."
    )

    # ---- 4. Sonuclar ----
    doc.add_heading("4. Sonuçlar", level=1)
    rows = []
    for n in ORDER:
        if n not in results:
            continue
        d = results[n]
        rows.append([d["title"], f"{fmt(d['roc_auc_mean'],3)} ± {fmt(d['roc_auc_std'],3)}",
                     fmt(d["pr_auc_mean"], 3), fmt(d["f1_mean"], 3),
                     fmt(d["balanced_accuracy_mean"], 3), fmt(d["mcc_mean"], 3),
                     fmt(d["brier_mean"], 3), f"{d['train_seconds']:.1f} sn"])
    rows.sort(key=lambda r: -float(r[1].split(" ±")[0]))
    add_table(doc, ["Model", "ROC-AUC (ort±std)", "PR-AUC", "F1", "Dengeli Doğruluk",
                     "MCC", "Brier", "Eğitim Süresi"],
              rows, col_widths_cm=[3.2, 2.3, 1.5, 1.3, 2.0, 1.3, 1.3, 1.8])
    doc.add_paragraph("Tablo: 5 kat walk-forward çapraz doğrulama sonuçları (ortalama ± std).").runs[0].italic = True

    add_figure(doc, RESULTS / "00_comparison_chart.png",
               "Şekil 1: Model başına ROC-AUC ve F1 karşılaştırması (hata çubukları = 5 kat arası std).")
    add_figure(doc, RESULTS / "roc_overlay.png",
               "Şekil 2: Tüm modeller için ROC eğrileri (birleştirilmiş OOF tahminler).")
    add_figure(doc, RESULTS / "pr_overlay.png",
               "Şekil 3: Tüm modeller için Kesinlik-Duyarlılık eğrileri.")

    doc.add_heading("4.1 Fold Varyansı", level=2)
    doc.add_paragraph(
        "Walk-forward protokolünde erken katlar daha az/daha homojen veriyle çalıştığından, "
        "kat-bazlı performans önemli ölçüde dalgalanabilir. Aşağıdaki kutu grafiği, her modelin "
        "5 kattaki ROC-AUC dağılımını göstermektedir; özellikle Yığınlanmış Topluluk ve LightGBM "
        "modellerinde gözlenen yüksek varyans (std>0,2), bu modellerin ortalama skorlarının tek "
        "başına güvenilir bir gösterge olmadığına işaret etmektedir."
    )
    add_figure(doc, RESULTS / "fold_variance.png",
               "Şekil 4: Model başına 5 kat ROC-AUC dağılımı (kutu grafiği).")

    doc.add_heading("4.2 Kalibrasyon", level=2)
    doc.add_paragraph(
        "Bir risk skorunun operasyonel kullanımı (ör. eşik-tabanlı uyarı sistemleri) için, "
        "üretilen olasılıkların gerçek frekanslarla ne ölçüde örtüştüğü (kalibrasyon) en az "
        "ayrım gücü (ROC-AUC) kadar önemlidir. Brier skoru düşük olan modeller (Tablo, "
        "sütun “Brier”) daha güvenilir olasılık tahminleri üretmektedir."
    )
    add_figure(doc, RESULTS / "calibration_overlay.png",
               "Şekil 5: Model başına kalibrasyon eğrileri (10 kova, kantil tabanlı).")

    doc.add_heading("4.3 En İyi Model: Karışıklık Matrisi", level=2)
    best_key = max(results, key=lambda k: results[k]["roc_auc_mean"])
    cm_path = RESULTS / f"{best_key}_confusion.png"
    if cm_path.exists():
        add_figure(doc, cm_path,
                   f"Şekil 6: {results[best_key]['title']} — karışıklık matrisi (OOF, eşik=0,5).",
                   width_cm=9)

    # ---- 5. Oznitelik onemi ----
    doc.add_heading("5. Özellik Önemi", level=1)
    doc.add_paragraph(
        "Ağaç tabanlı modeller için, 5 kat boyunca ortalanan (Gini/split tabanlı) özellik "
        "önemleri hesaplanmıştır. Aşağıdaki grafikler en etkili 15 özelliği göstermektedir."
    )
    for n in ["catboost", "random_forest", "xgboost", "lightgbm"]:
        img = RESULTS / f"{n}_feature_importance.png"
        if img.exists():
            title = results.get(n, {}).get("title", n)
            add_figure(doc, img, f"Şekil: {title} — özellik önem sıralaması.", width_cm=13)

    # ---- 6. Tartisma ----
    doc.add_heading("6. Tartışma", level=1)
    doc.add_paragraph(
        "Sonuçlar, bu görev için ağaç tabanlı topluluk yöntemlerinin (CatBoost, Random Forest, "
        "XGBoost) hem en yüksek ortalama performansı hem de görece daha düşük fold varyansını "
        "birlikte sağladığını göstermektedir. MLP'nin belirgin biçimde zayıf kalması "
        "(ROC-AUC≈0,43, rastgele tahminin altında), küçük tablo veri setlerinde (454 örnek/18 "
        "özellik) derin sinir ağlarının aşırı öğrenmeye (overfitting) yatkın olduğunu ve yeterli "
        "düzenlileştirme/hiperparametre araması olmadan güvenilir sonuç vermediğini "
        "doğrulamaktadır — bu, literatürdeki genel gözlemle (küçük tablo verilerde GBM > derin "
        "öğrenme) örtüşmektedir. Yığınlanmış topluluk modelinin, bileşenlerinden (özellikle "
        "CatBoost) daha iyi performans GÖSTEREMEMESİ dikkat çekicidir; bunun olası nedeni, "
        "meta-öğreniciyi eğitmek için kullanılan iç 3-kat çapraz doğrulamanın, zaten küçük olan "
        "eğitim kümesini daha da parçalayarak meta-öğreniciye yetersiz sinyal bırakmasıdır."
    )

    # ---- 7. Sinirlamalar ----
    doc.add_heading("7. Sınırlamalar", level=1)
    doc.add_paragraph(
        f"(1) Veri kümesi küçüktür ({ds['n_total']} kayıt); katalog genişledikçe (özellikle "
        "backend'deki güncel veriyle) modellerin yeniden çalıştırılması önerilir. "
        "(2) Walk-forward katları arasında gözlenen yüksek varyans (bkz. Şekil 4), bazı "
        "modellerin ortalama skorlarının istikrarsız olduğuna işaret etmektedir; tek bir "
        "ortalama değer yerine daima std ile birlikte raporlanmalıdır. (3) Kısa vadeli "
        "aktivite özellikleri (`rolling_*`, `event_count_7d`) global ölçekte (bölgeye özel "
        "olmayan) hesaplanmaktadır; bölgesel bir pencereleme gelecekteki bir iyileştirme "
        "konusu olabilir. (4) Artçı-şok ayıklama basitleştirilmiş bir kural tabanlı yöntemdir "
        "(Reasenberg/Gardner-Knopoff gibi standart algoritmalar değildir)."
    )

    # ---- 8. Sonuc ----
    doc.add_heading("8. Sonuç", level=1)
    doc.add_paragraph(
        "Bu karşılaştırmalı çalışma, 30 günlük deprem riski sınıflandırmasında CatBoost tabanlı "
        "üretim modelinin seçiminin sağlam bir zemine oturduğunu; Random Forest'ın da benzer "
        "performansla rekabetçi bir alternatif olduğunu; MLP tabanlı derin yaklaşımların ise bu "
        "veri ölçeğinde önerilmediğini göstermektedir. Sonuçlar makale için gerekli kıyaslama "
        "tablosu, ROC/PR eğrileri, kalibrasyon analizi ve özellik önem sıralamasının temelini "
        "oluşturmaktadır."
    )

    out_path = RESULTS / "05_Deprem_Risk_Skoru_Rapor.docx"
    doc.save(str(out_path))
    print("yazildi:", out_path)


if __name__ == "__main__":
    main()
