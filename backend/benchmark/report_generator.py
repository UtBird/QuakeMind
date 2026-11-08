"""benchmark/runs/ altindaki tum calismalari (pipeline_runner.py + naive_baseline.py
ciktilari) tarayip tek bir Markdown rapor + CSV uretir. Makale icin dogrudan
kullanilabilir bir ozet + ham veri tablosu hedefler.

Kullanim:
  python benchmark/report_generator.py
"""

import csv
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

RUNS_DIR = Path(__file__).resolve().parent / "runs"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def discover_runs() -> list[Path]:
    runs = []
    if not RUNS_DIR.exists():
        return runs
    for d in sorted(RUNS_DIR.iterdir()):
        if d.is_dir() and (d / "summary.json").exists() and (d / "naive_baseline_comparison.json").exists():
            runs.append(d)
    return runs


def detection_validation_rows(summary: dict, ground_truth_by_region: dict) -> list[dict]:
    """Bizim canli SegFormer tespitimizin bulduğu kapali yol sayisi ile
    Copernicus gercek zemin dogrulamasindaki (mahalle civarindaki) hasarli
    yol sayisini yan yana koyar -- seffaflik icin."""
    region = summary["region"]
    gt = ground_truth_by_region.get(region)
    rows = []
    for mahalle, rd in summary["roadDamageResults"].items():
        nearby_real = 0
        if gt:
            b = rd["bounds"]
            for road in gt["damagedRoadSegments"]:
                if b["west"] <= road["lon"] <= b["east"] and b["south"] <= road["lat"] <= b["north"]:
                    nearby_real += 1
        rows.append({
            "region": region, "mahalle": mahalle,
            "ourLiveDetectedBlocked": len(rd["blockedRoadSegments"]),
            "copernicusRealDamagedInBounds": nearby_real,
        })
    return rows


def build_report(runs: list[Path]) -> tuple[str, list[dict]]:
    ground_truth_by_region = {}
    for region in ("kahramanmaras", "hatay"):
        gt_path = DATA_DIR / f"{region}_copernicus_ground_truth.json"
        if gt_path.exists():
            ground_truth_by_region[region] = _load_json(gt_path)

    lines = []
    csv_rows = []
    all_detection_rows = []

    lines.append("# QuakeMind Karsilastirmali Saha Testi Raporu\n")
    lines.append(
        "Bu rapor, QuakeMind'in yol-hasari tespiti (SegFormer+OSM) ve GNN "
        "en-guvenli-rota motorunun, bu motor olmadan (naive en kisa yol, "
        "kapanmalari sahada kesfederek) gidilen bir senaryoya kiyasla ne "
        "kadar zaman kazandirdigini olcer. Tum senaryolar 6 Subat 2023 "
        "depreminden gercekten etkilenen Kahramanmaras ve Hatay/Antakya "
        "bolgelerinde, gercek AFAD toplanma alani verisi, gercek Copernicus "
        "EMSR648 hasar tespiti ve gercek QuakeMind API pipeline'i (NLP, SOS, "
        "yol hasari analizi, ekip claim, GNN rota) uzerinden calistirildi -- "
        "hicbir adim mock veriyle degistirilmedi.\n"
    )

    lines.append("## Yontem Ozeti\n")
    lines.append("- **Bolgeler:** Kahramanmaras (AFAD merkez ilceler) ve Hatay/Antakya, her biri 3 gercek mahalle.")
    lines.append("- **Toplanma alani / itfaiye / hastane verisi:** Resmi AFAD toplanma alani veriseti (72.232 nokta, filtrelendi) + OSM Overpass (itfaiye, hastane). AFAD/UMKE saha binalari icin OSM'de yeterli veri bulunamadi -- bu bilinen bir veri boslugu, ekipler itfaiye/hastane konumlarindan konuslandirildi.")
    lines.append("- **Gercek hasar zemin dogrulamasi:** Copernicus EMS EMSR648 (MONIT01 gecisi) -- Kahramanmaras icin 134 hasarli yol/927 hasarli bina, Hatay icin 73 hasarli yol/394 hasarli bina.")
    lines.append("- **Uydu goruntusu:** Esri Wayback, depreme en yakin tarihli surum (2023-02-23) otomatik secildi.")
    lines.append("- **Naive ajan modeli:** Ayni yol grafiginde, kapanmalari SADECE oraya varinca kesfeder (kesif ani israfi sifir kabul edilir -- naive lehine, muhafazakar bir varsayim), kesfedince bir onceki kavsaktan bilinen kapanmalari eleyerek yeniden en kisa yolu hesaplar.")
    lines.append("- **Sure tahmini:** Sabit ortalama saha hizi varsayimi (bkz. asagida) -- bu acikca belirtilen bir varsayimdir, gercek saha hizina gore olceklenebilir.")
    lines.append("- **Onemli ayrim:** 'Bizim motor' rotasi HER ZAMAN canli /api/road_damage/route cagrisindan gelen gercek sonuctur (ayrica simule edilmez); sadece naive taraf simule edilir.\n")

    total_reachable = 0
    total_stuck = 0
    total_saved_min = 0.0
    total_our_detected_blocked = 0
    total_copernicus_nearby = 0

    for run_dir in runs:
        summary = _load_json(run_dir / "summary.json")
        comparison = _load_json(run_dir / "naive_baseline_comparison.json")
        region = summary["region"]

        lines.append(f"## Bolge: {summary.get('runId', region)}\n")
        lines.append(f"Uydu goruntusu tarihi: {(summary.get('wayback') or {}).get('date', 'bilinmiyor')}\n")

        det_rows = detection_validation_rows(summary, ground_truth_by_region)
        all_detection_rows.extend(det_rows)
        lines.append("### Canli tespit vs gercek Copernicus hasari (seffaflik)\n")
        lines.append("| Mahalle | Bizim canli tespitimiz (kapali yol) | Copernicus gercek hasar (ayni sinirlar icinde) |")
        lines.append("|---|---|---|")
        for r in det_rows:
            lines.append(f"| {r['mahalle']} | {r['ourLiveDetectedBlocked']} | {r['copernicusRealDamagedInBounds']} |")
            total_our_detected_blocked += r["ourLiveDetectedBlocked"]
            total_copernicus_nearby += r["copernicusRealDamagedInBounds"]
        lines.append("")

        for severity, comp in comparison["comparisons"].items():
            lines.append(f"### {region} / {severity} hasar senaryosu\n")
            lines.append(f"- Toplam ekip-hedef atamasi: {comp['assignmentCount']}")
            lines.append(f"- Naive ajanin da ulastigi eslesme sayisi: {comp['reachableByNaiveCount']}")
            lines.append(f"- **Naive ajanin TAMAMEN TIKANDIGI, bizim motorun basarili oldugu eslesme sayisi: {comp['naiveStuckCount']}**")
            if comp["naiveStuckOurEngineTimeMin"]:
                times = ", ".join(f"{t} dk" for t in comp["naiveStuckOurEngineTimeMin"])
                lines.append(f"  - Bu vakalarda bizim sistemin hedefe ulasma suresi: {times}")
            lines.append(f"- Naive de ulastiginda toplam kazanilan sure: {comp['totalTimeSavedMin']} dk (ortalama {comp['avgTimeSavedMinPerTeam']} dk/ekip)\n")

            total_reachable += comp["reachableByNaiveCount"]
            total_stuck += comp["naiveStuckCount"]
            total_saved_min += comp["totalTimeSavedMin"]

            for row in comp["rows"]:
                csv_rows.append({
                    "region": region, "severity": severity, "teamId": row["teamId"],
                    "victimId": row["victimId"], "mahalle": row["mahalle"],
                    "ourEngineDistanceMeters": row["ourEngineDistanceMeters"],
                    "ourEngineTimeMin": row["ourEngineTimeMin"],
                    "naiveDistanceMeters": row.get("naiveDistanceMeters"),
                    "naiveTimeMin": row.get("naiveTimeMin"),
                    "timeSavedMin": row.get("timeSavedMin"),
                    "naiveUnreachable": row["naiveUnreachable"],
                    "naiveDiscoveries": row.get("naiveDiscoveries"),
                })

    lines.append("## Genel Ozet (tum calismalar)\n")
    lines.append(f"- Naive ajanin da ulastigi toplam eslesme: {total_reachable}, toplam kazanilan sure: {round(total_saved_min, 1)} dk")
    lines.append(f"- **Naive ajanin tamamen tikandigi, bizim sistemin basarili oldugu toplam eslesme: {total_stuck}**")
    lines.append(f"- Tum mahallelerde canli tespitimizin bulduğu toplam kapali yol: {total_our_detected_blocked} (Copernicus'un ayni sinirlar icinde isaretledigi: {total_copernicus_nearby})")
    if total_copernicus_nearby > 0:
        pct = round(100 * total_our_detected_blocked / total_copernicus_nearby, 1)
        lines.append(f"  - Canli tespit / gercek hasar orani: %{pct} -- bu bolgeler/tarihler icin modelin yakalama oraninin bir gostergesi, iyilestirme alani olarak makalede tartisilabilir.\n")

    lines.append("## Veri Kaynaklari ve Atif\n")
    lines.append("- OpenStreetMap katkicilar, ODbL lisansi altinda.")
    lines.append("- Copernicus Emergency Management Service, EMSR648 aktivasyonu (mapping.emergency.copernicus.eu) -- AB Copernicus Programi, ucretsiz ve acik erisim.")
    lines.append("- AFAD resmi toplanma alani veriseti (proje ici, apps/road_damage/data/tum_turkiye_toplanma_alanlari.json).")
    lines.append("- Esri World Imagery Wayback.\n")

    lines.append("## Bilinen Sinirlamalar\n")
    lines.append("- AFAD/UMKE operasyonel saha binalari icin OSM'de yeterli POI verisi bulunamadi; ekipler itfaiye/hastane konumlarindan baslatildi.")
    lines.append("- Sure tahmini sabit bir ortalama hiz varsayimina dayanir, gercek arac/yaya hizindan sapabilir.")
    lines.append("- Naive ajan modeli, kesif anindaki kismi mesafe israfini sifir kabul eder (naive lehine, muhafazakar bir varsayim) -- gercek sahada naive yaklasimin kaybi muhtemelen burada raporlanandan daha da fazladir.")
    lines.append("- Canli SegFormer tespiti, bazi mahallelerde/tarihlerde Copernicus'un insan analistlerinin buldugu hasarin tamamini yakalayamadi -- bu modelin gercek dunya performansinin dogru bir yansimasidir, iyilestirilebilir bir alandir.\n")

    return "\n".join(lines), csv_rows


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    runs = discover_runs()
    if not runs:
        print("benchmark/runs altinda tamamlanmis (summary.json + naive_baseline_comparison.json) calisma bulunamadi.")
        return

    report_md, csv_rows = build_report(runs)

    md_path = REPORTS_DIR / "quakemind_benchmark_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    csv_path = REPORTS_DIR / "comparison_rows.csv"
    if csv_rows:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

    print(f"Rapor -> {md_path}")
    print(f"Ham veri CSV -> {csv_path}")


if __name__ == "__main__":
    main()
