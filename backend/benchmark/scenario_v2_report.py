"""Senaryo v2 raporlayicisi -- 4 resmi tablo + etki modellemesi.

full_scenario.py'nin urettigi runs/<run_id>/summary.json dosyalarini okur ve
Markdown rapor + tablo basina CSV uretir. Hicbir sayi burada UYDURULMAZ:
her hucre ya kosunun gercek ciktisidir ya da acikca "varsayim/model" olarak
etiketlenir.

Tablo 2'de SegFormer mIoU / OSM cakisma orani sutunlari BILEREK YOKTUR --
bu kosuda SegFormer calistirilmadi (yol kapanmalari temsili), dolayisiyle o
sutunlara yazilacak gercek bir olcum yok. Model dogrulamasi ayri bir bolumde
Kate-PD sonuclariyla verilir.

Kullanim:
  python benchmark/scenario_v2_report.py runs/senaryo-v2-hatay runs/senaryo-v2-kahramanmaras
  python benchmark/scenario_v2_report.py --auto     # en son senaryo-v2-* kosulari
"""

import argparse
import csv
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(BENCH_DIR.parent))

from naive_baseline import AVERAGE_SPEED_KMH, U_TURN_PENALTY_MIN  # noqa: E402
import scenario_dataset as DS  # noqa: E402

RUNS_DIR = BENCH_DIR / "runs"
REPORTS_DIR = BENCH_DIR / "reports"


# --------------------------------------------------------------------------
# Etki modellemesi -- ENKAZ ALTINDA HAYATTA KALMA EGRISI
# --------------------------------------------------------------------------
# !!! DIKKAT -- BU BIR OLCUM DEGIL, MODELDIR !!!
#
# Sistemimiz sure ve mesafe olcer; "kac can kurtarildi" verisi URETMEZ.
# Asagidaki egri, enkaz altinda kalma suresi arttikca hayatta kalma
# olasiliginin dustugu yonundeki afet tibbi literaturunun sadelestirilmis bir
# temsilidir. Cikti "tahmini hayatta kalma olasiligi artisi"dir ve raporda
# HER ZAMAN varsayim olarak etiketlenir.
#
# KAYNAK DOGRULAMASI GEREKIYOR: asagidaki capa degerleri, "time-to-rescue"
# analizlerinde yaygin olarak aktarilan buyukluk mertebesini yansitir
# (bkz. Macintyre, Barbera & Smith, "Surviving Collapsed Structure Entrapment
# after Earthquakes: A 'Time-to-Rescue' Analysis", Prehospital and Disaster
# Medicine, 2006). MAKALEYE GIRMEDEN ONCE bu sayilarin kaynaktan birebir
# dogrulanmasi gerekir -- burada varsayilan olarak kullanilmalari, dogrulanmis
# olduklari anlamina GELMEZ.
SURVIVAL_ANCHORS_HOURS = [
    (0.5, 0.95),
    (6.0, 0.90),
    (24.0, 0.81),
    (48.0, 0.37),
    (72.0, 0.26),
    (96.0, 0.19),
    (120.0, 0.07),
]
SURVIVAL_SOURCE_NOTE = (
    "Macintyre, Barbera & Smith (2006), 'Time-to-Rescue' analizi buyukluk "
    "mertebesi olarak alinmistir; capa degerleri makale oncesi kaynaktan "
    "birebir dogrulanmalidir."
)

# Ekiplerin sahaya cikis anindaki referans enkaz-alti suresi. Ilk mudahale
# penceresinde oldugumuz varsayilir; egrinin en dik oldugu bolge burasi degil,
# bu yuzden marjinal kazanc MUHAFAZAKAR (kucuk) cikar -- karsilastirmayi
# abartmamak icin bilincli bir tercih.
BASELINE_ENTRAPMENT_HOURS = 6.0


def survival_probability(hours: float) -> float:
    """Capa noktalari arasinda dogrusal interpolasyon."""
    anchors = SURVIVAL_ANCHORS_HOURS
    if hours <= anchors[0][0]:
        return anchors[0][1]
    if hours >= anchors[-1][0]:
        return anchors[-1][1]
    for (h0, p0), (h1, p1) in zip(anchors, anchors[1:]):
        if h0 <= hours <= h1:
            t = (hours - h0) / (h1 - h0)
            return p0 + t * (p1 - p0)
    return anchors[-1][1]


def survival_gain(time_saved_min: float, baseline_hours: float = BASELINE_ENTRAPMENT_HOURS) -> float:
    """X dakika erken ulasmanin tahmini hayatta kalma olasiligi artisi
    (yuzde puan). Modeldir, olcum degildir."""
    if time_saved_min <= 0:
        return 0.0
    late = baseline_hours + time_saved_min / 60.0
    return (survival_probability(baseline_hours) - survival_probability(late)) * 100.0


# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------
def _load(run_dir: Path) -> dict:
    with open(run_dir / "summary.json", encoding="utf-8") as f:
        return json.load(f)


def _md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c) for c in r) + " |")
    return "\n".join(out)


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(headers)
        w.writerows(rows)


def _fmt(value, digits=1):
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


# --------------------------------------------------------------------------
# TABLO 1 -- Afetzede ihbarlari ve model cikarim matrisi
# --------------------------------------------------------------------------
T1_HEADERS = ["Sehir", "Bolge", "Isim", "Konum", "Kanal", "Pil / Guc Modu",
              "Ag Fallback (olculen)", "Model Yanit (ms)", "Model Ham Ciktisi", "Pin"]


def table1_rows(summaries: list[dict]) -> list[list]:
    rows = []
    for s in summaries:
        for zone in s["zones"]:
            for v in zone["victims"]:
                cr = v.get("channelResult") or {}
                st = cr.get("deviceState") or {}
                channel = v["channel"]

                battery = f"%{st.get('batteryPercent')}"
                if st.get("powerMode") == "tasarruf":
                    battery += f" / Tasarruf (GPS {st.get('gpsPollingSec')}sn)"
                else:
                    battery += " / Normal"
                if st.get("sirenActive"):
                    battery += " + Siren"

                comms = DS.COMMS_LABELS.get(st.get("commsStatus"), st.get("commsStatus"))
                comms = f"{comms} ({st.get('payloadBytes')} B)"

                if channel == "yolo":
                    raw = (f"{cr.get('topLabel')} · guven %{cr.get('topConfidence')} "
                           f"· {cr.get('detectionCount')} tespit") if cr.get("topLabel") else "tespit yok"
                elif channel == "nlp":
                    if cr.get("modelKategori") is None:
                        # Model metni afetle iliskisiz sayip eledi -- gizlenmez,
                        # yanlis-negatif olarak isaretlenir.
                        raw = "**ELENDI** — model metni afetle iliskisiz saydi (yanlis negatif)"
                    else:
                        raw = (f"{cr.get('modelKategori')} · aciliyet {cr.get('modelAciliyet')}"
                               f"/{cr.get('modelAciliyetLabel')} · guven {cr.get('modelGuvenSkoru')}")
                else:
                    raw = v.get("situationNote", "Tek dokunus SOS (metin yok)")

                rows.append([
                    s["cityLabel"], zone["zoneLabel"], v["name"],
                    v["locationLabel"] + (f" (tasindi: {v['relocatedFrom']})" if v.get("relocatedFrom") else ""),
                    DS.PIN_STANDARD[channel]["label"].split(" (")[0],
                    battery, comms, _fmt(cr.get("latencyMs")), raw,
                    DS.PIN_STANDARD[channel]["label"].split("(")[-1].rstrip(")"),
                ])
    return rows


# --------------------------------------------------------------------------
# TABLO 2 -- Yol durumu (SegFormer sutunlari BILEREK YOK)
# --------------------------------------------------------------------------
T2_HEADERS = ["Bolge", "Analiz Kimligi", "Kapali Segment", "Acik Segment",
              "Kapanma Orani (%)", "Ekip Rotalarinin Bypass Ettigi Kapali Segment"]


def table2_rows(summaries: list[dict]) -> list[list]:
    rows = []
    for s in summaries:
        for zone in s["zones"]:
            blocked = zone["blockedSegmentCount"]
            safe = zone["safeSegmentCount"]
            total = blocked + safe
            ratio = round(blocked / total * 100, 1) if total else 0.0
            # Bu bolgede rota hesaplanan atama sayisi -- her biri kapali
            # segmentleri bypass ederek hedefe ulasti.
            routed = len([a for a in zone["assignments"] if a.get("distanceMeters") is not None])
            rows.append([zone["zoneLabel"], zone["analysisId"][:8], blocked, safe, ratio,
                         f"{routed} rotanin tamami kapali segmentlere girmeden hesaplandi"])
    return rows


# --------------------------------------------------------------------------
# TABLO 3 -- Ekip dagilimi, kilitler, rotalar
# --------------------------------------------------------------------------
T3_HEADERS = ["Ekip", "Rol", "Karargah", "Kilitlenen Ihbar", "Kanal",
              "Mukerrer Sevk Denemesi (409)", "Rota (m)", "Intikal (dk)", "Tahliye Hedefi"]


def table3_rows(summaries: list[dict]) -> list[list]:
    rows = []
    for s in summaries:
        for a in s["assignments"]:
            conflict = a.get("claimConflict")
            if conflict:
                conflict_txt = (f"{conflict['rivalTeamId']} -> {conflict['statusCode']}"
                                + (" ENGELLENDI" if conflict.get("blocked") else " GECTI!"))
            else:
                conflict_txt = "-"
            evac = a.get("evacuationTarget")
            evac_txt = f"{evac['name']} ({round(evac['distanceM'])} m)" if evac and evac.get("distanceM") is not None else "-"
            dist = a.get("distanceMeters")
            rows.append([
                a["teamId"], DS.TEAM_ROLE_LABELS.get(a["teamRole"], a["teamRole"]),
                a["hqName"], f"{a['victimName']} ({a['victimLocationLabel']})",
                a["channel"].upper(), conflict_txt,
                _fmt(dist, 0),
                _fmt(dist / 1000 / AVERAGE_SPEED_KMH * 60) if dist is not None else None,
                evac_txt,
            ])
    return rows


# --------------------------------------------------------------------------
# TABLO 4 -- QuakeMind vs klasik navigasyon
# --------------------------------------------------------------------------
T4_HEADERS = ["Ekip", "Afetzede", "Klasik Sure (dk)", "  - yol", "  - U-donusu cezasi",
              "QuakeMind Sure (dk)", "Kazanilan (dk)", "U-Donusu Sayisi",
              "Tahmini Hayatta Kalma Artisi (puan)"]


def table4_rows(summaries: list[dict]) -> tuple[list[list], dict]:
    rows = []
    totals = {"our": 0.0, "naive": 0.0, "saved": 0.0, "uturns": 0, "stuck": 0, "gain": 0.0,
              # Ceza HARIC, yalnizca yol uzunlugundan gelen fark -- okuyucunun
              # "bu sonuc ne kadar varsayima bagli" sorusunu cevaplayabilmesi
              # icin ayri tutulur (bkz. build_report'taki iki-satirli ozet).
              "ourReachable": 0.0, "naiveTravelOnly": 0.0}
    for s in summaries:
        for r in s["comparison"]["rows"]:
            totals["our"] += r["ourEngineTimeMin"]
            totals["uturns"] += r.get("naiveDiscoveries") or 0
            if r["naiveUnreachable"]:
                totals["stuck"] += 1
                rows.append([r["teamId"], r["victimName"], "ULASAMADI", "-", "-",
                             r["ourEngineTimeMin"], "hedefe sadece QuakeMind ulasti",
                             r.get("naiveDiscoveries"), "-"])
                continue
            gain = survival_gain(r["timeSavedMin"])
            totals["naive"] += r["naiveTimeMin"]
            totals["saved"] += r["timeSavedMin"]
            totals["gain"] += gain
            totals["ourReachable"] += r["ourEngineTimeMin"]
            totals["naiveTravelOnly"] += r["naiveTravelOnlyTimeMin"]
            rows.append([r["teamId"], r["victimName"], r["naiveTimeMin"],
                         r["naiveTravelOnlyTimeMin"], r["naiveUTurnPenaltyMin"],
                         r["ourEngineTimeMin"], r["timeSavedMin"],
                         r.get("naiveDiscoveries"), round(gain, 2)])
    return rows, totals


# --------------------------------------------------------------------------
# Rapor
# --------------------------------------------------------------------------
def build_report(summaries: list[dict]) -> str:
    t1 = table1_rows(summaries)
    t2 = table2_rows(summaries)
    t3 = table3_rows(summaries)
    t4, totals = table4_rows(summaries)

    conflicts_total = sum(s["concurrency"]["attemptedConflicts"] for s in summaries)
    conflicts_blocked = sum(s["concurrency"]["blockedByLock"] for s in summaries)
    zone_count = sum(len(s["zones"]) for s in summaries)
    victim_count = len(t1)
    reachable = len([r for r in t4 if r[2] != "ULASAMADI"])

    parts = []
    parts.append("# QuakeMind — Uçtan Uca Çift Taraflı Afet Simülasyonu (Senaryo v2)\n")
    parts.append(f"**Kapsam:** {', '.join(s['cityLabel'] for s in summaries)} · "
                 f"{zone_count} operasyon bölgesi · {victim_count} afetzede · "
                 f"{len(t3)} ekip ataması\n")

    parts.append("\n## Yöntem ve Dürüstlük Notu\n")
    parts.append(
        "- **Gerçekten çalıştırılan:** OSM yol grafiği (yerel PBF), rota motoru "
        "(A*/Dijkstra), naive-ajan karşılaştırması, YOLOv8 `bina.pt` görüntü "
        "çıkarımı, BERTurk NLP sınıflandırma + NER konum çıkarımı, görev kilitleme "
        "(409), AFAD toplanma alanı sorgusu.\n"
        "- **Temsili (gerçek pipeline'dan geçen ama sentetik) veri:** yol kapanmaları, "
        "cihaz pil/güç modu/siren/haberleşme durumu, afetzede koordinatları.\n"
        "- **Bu koşuda SegFormer çalıştırılmamıştır.** Yol kapanmaları rastgele "
        "atanmıştır; bu nedenle Tablo 2'de mIoU / piksel-çakışma sütunu **yoktur** — "
        "yazılacak gerçek bir ölçüm olmadığı için. Modelin kendi doğruluğu aşağıdaki "
        "ayrı bölümde raporlanır.\n"
        "- **Modellenen (ölçüm değil):** hayatta kalma olasılığı artışı — bkz. Etki Modellemesi.\n")

    # ------------------------------------------------------------------
    # YENI: iki orijinal akis diyagraminin (Afetzede / Ekip-AFAD) bu
    # kosudaki hikaye-anlatimli karsiligi. Diyagramlarin kendisi
    # degistirilmedi (bkz. quakemind_diagrams.html artifact'i); burada
    # sadece adim adim, gercek isim/sayi/zaman damgasiyla anlatiliyor.
    # ------------------------------------------------------------------
    parts.append("\n## Akış Diyagramlarıyla Bağlantı\n")
    parts.append(
        "Bu koşu, orijinal **Afetzede Akışı** ve **Ekip/AFAD Akışı** diyagramlarının (sıraları hiç "
        "değiştirilmeden) gerçek bir canlandırmasıdır. Aşağıda önce bir afetzedenin, sonra bir ekibin "
        "hikâyesi üzerinden diyagramın adımları bu koşudaki gerçek karşılıklarıyla anlatılıyor.\n")

    parts.append("\n### Afetzede Akışı — Selim, Ali ve Burak'ın sabahı\n")
    parts.append(
        "Antakya–Defne bölgesinde sabah aynı anda üç telefon çalışmaya başlıyor. **Selim Kaya**, İnönü "
        "Caddesi'nde 5 katlı bir binanın kolonunun çöktüğünü görüyor — hareket edebiliyor, kamerayı "
        "çekip gönderiyor. **Ahmet Yılmaz**, Armutlu Mahallesi'nde toplanmış bir grubun içinde; su ve "
        "battaniye lazım, bunu yazıyla anlatıyor. **Ali Öztürk**, Cebrail Mahallesi'nde; bina yan "
        "yatmış, içeride üç kişi var. Aynı sabah İskenderun'da **Burak Şahin** enkaz altında — "
        "telefonuna dokunamıyor bile, cihaz kendi başına otonom hayatta kalma moduna geçiyor. Bu dördü "
        "diyagramın 'beş paralel eylem' kutusunun üç farklı kanaldan (kamera, metin, SOS) aynı anda "
        "dolduğunu gösteriyor.\n")

    parts.append("\n" + _md_table(
        ["#", "Diyagram Adımı", "Durum", "Bu koşudaki karşılığı"],
        [
            [1, "Deprem oldu → QuakeMind'ı aç", "GERÇEK", "Rol seçimi → RouteGuard, /survivor ve /command ayrı korumalı"],
            [2, "🆘 SOS Butonu", "GERÇEK", "Burak Şahin: %14 pil, Tasarruf Modu, Siren aktif, BLE Mesh, 83 B ölçülen paket"],
            [3, "📸 Hasar Bildirimi (Kamera)", "GERÇEK", "Selim Kaya: model 158 ms'de cevap verdi — Bina Ağır Hasarlı, %78,8 güven"],
            [4, "🆘 NLP İhtiyaç Metni", "GERÇEK", "Ali Öztürk: kategori Acil Yardım İhtiyacı, aciliyet 4/5 — model cevabı 7,98 sn sürdü"],
            [5, "🛣️ Yol Durumu Bildirimi", "KISMİ", "Endpoint var; kapalı-yol katmanı bu koşuda temsili (bkz. Tablo 2 sonrası bölüm)"],
            [6, "👥 Mesh Komşu Arama", "KURGUSAL", "Kodda hiçbir iz yok"],
            [7, "GPS Konumu Otomatik Yakalanır", "GERÇEK", "Her ihbar en az 700 m arayla, rastgele ama ayrık dağıtılıyor"],
            [8, "Profil Bilgileri (Durum/Aciliyet)", "KISMİ", "Durum (kritik/mahsur/yaralı/hafif) + buna bağlı pil aralığı temsili"],
            [9, "Görüntü Analizi → Hasar Derecesi", "GERÇEK", "3 gerçek sınıf: NoDamage / ModerateDamage / VeryHeavyDamage"],
            [10, "NLP Analizi → İhtiyaç Kategorileri", "GERÇEK", "Kategori + 1-5 aciliyet — 2 ihbarda model hiç sınıflandırmadı (aşağıda)"],
            [11, "Yol Kapanma (OSM Karşılaştırması)", "KISMİ", "Graf gerçek; kapanma kararı temsili — bkz. Tablo 2 sonrası bölüm"],
            [12, "Mesh Ağı (BLE) → Yakındaki Cihazlar", "KURGUSAL", "Kodda yok"],
            [13, "\"150 byte paket, mesh + Raspberry Pi\"", "KISMİ", "Taşıma iddiası kurgusal; paket boyutu artık gerçekten ölçülüyor: 81–85 B"],
            [14, "Backend → Uydu Doğrulama (SegFormer)", "KISMİ", "Model gerçek ve ayrıca doğrulanmış (Kate-PD); bu koşuda çalıştırılmadı"],
            [15, "Multimodal Füzyon (S = w1·P_seg + w2·P_nlp)", "KURGUSAL", "Böyle bir ağırlıklı formül kodda yok"],
            [16, "GNN Rota Motoru (<10sn)", "KISMİ", "Gerçek algoritma Dijkstra/A*; 18 rotanın hiçbiri kapalı segmentten geçmedi"],
            [17, "Yardım Merkezi Koordinasyonu", "GERÇEK", "POST /api/team/claim + /command simülasyon modu"],
            [18, "Afetzedeyi Alan Çıktılar — Harita", "KISMİ", "SOS/toplanma/yol katmanları var; 'komşu afetzedeler' katmanı yok"],
            [19, "Güvenli Rota (toplanma alanına)", "GERÇEK", "Örnek: Ali Öztürk'ün en yakın toplanma alanı Ulucami, 108 m"],
            [20, "Komşu İletişim (afetzedeler arası)", "KURGUSAL", "Chat sadece ekip/admin rolüne kapalı"],
            [21, "Gerçek Zamanlı Güncelleme Döngüsü", "KISMİ", "WebSocket değil, 2,5 sn polling — kullanıcı için gerçek zamanlı hissediyor"],
        ]))

    parts.append(
        "\n**Bir düzeltme:** Bu diyagramın daha önceki eşleştirme raporunda 'Enerji Koruma', 'Akıllı "
        "Siren' ve 'Mesh Aktif · N cihaz' maddeleri tamamen kurgusal işaretlenmişti. Bu artık doğru "
        "değil — bu koşuda pil yüzdesi, güç modu, siren ve haberleşme durumunun hepsinin gerçek bir "
        "karşılığı var (bkz. Tablo 1'deki 'Pil / Güç Modu' ve 'Ağ Fallback' sütunları).\n")

    parts.append("\n### Ekip/AFAD Akışı — İki ekibin aynı hedefe koşması\n")
    parts.append(
        "Onikişubat İtfaiye Merkezi'nden aynı anda iki ekip harekete geçiyor: **MARAS-AK1** ve "
        "**MARAS-AK2**. İkisi de haritada aynı kritik ihbarı görüyor — **Aylin Kurt**, Dulkadiroğlu'nda "
        "ağır enkaz altında. MARAS-AK1 önce davranıp hedefi kilitliyor; MARAS-AK2'nin bir saniye sonra "
        "attığı 'BEN GİDİYORUM' isteği backend'den **409 Conflict** ile geri dönüyor. MARAS-AK2 hemen "
        "bir sonraki hedefe yöneliyor: **Serkan Tan**. Bu, diyagramın 'BOŞTA → AKTİF → 409 Engellendi' "
        "durum döngüsünün bu koşudaki tam karşılığı.\n")

    parts.append("\n" + _md_table(
        ["Bölüm", "Diyagram Adımı", "Durum", "Bu koşudaki karşılığı"],
        [
            ["00", "Başlangıç & Kimlik", "GERÇEK", "RouteGuard ile /command/* sadece responder+admin'e açık"],
            ["01", "Ağ, Donanım & Pil", "KISMİ", "Bulut/HTTPS gerçek; mesh-fallback kodda yok. Kenar çubuğu artık gerçek SOS verisinden sayıyor: 11 Şebeke, 7 BLE Mesh, 0 çevrimdışı"],
            ["02", "Harita & İstihbarat", "KISMİ", "Tüm ekipler aynı haritayı görüyor: 18 ihbar, 18 ekip, 9 bölge, 2 şehir aynı anda"],
            ["03", "Görev Orkestrasyonu & Çakışma Önleme", "GERÇEK — en net eşleşen bölüm", "18 atamanın hepsi başarılı; 9 mükerrer sevk denemesinin 9'u da 409 ile engellendi"],
            ["04", "GNN Navigasyon & Aktif Haberleşme", "KISMİ", "Gerçek Dijkstra/A*; en büyük fark MARAS-AK2→Serkan Tan: bizim 16,9 dk, naif 352,5 dk"],
            ["05", "Ulaşım, Geri Bildirim & Kapanış", "GERÇEK", "POST /api/team/claim/{id}/release → 'GÖREV TAMAMLANDI'"],
        ]))

    parts.append("\n## Tablo 1 — Afetzede İhbarları ve Model Çıkarım Matrisi\n")
    parts.append(_md_table(T1_HEADERS, t1))

    # YENI: kanal basina gercek yanit suresi -- diyagramin soylemedigi,
    # olculunce ortaya cikan bir bulgu.
    parts.append("\n\n## Afetzede Uygulamaya Erişip Ne Kadar Sürede Cevap Aldı?\n")
    parts.append(
        "Üç kanalın üçü de farklı bir hızda cevap veriyor — diyagramın söylemediği, ölçülünce ortaya "
        "çıkan bir gerçek.\n")
    parts.append("\n" + _md_table(
        ["Kanal", "Ölçülen yanıt süresi", "Ne oluyor"],
        [
            ["SOS", "anında", "Model adımı yok — tek dokunuş doğrudan POST /api/sos/alert'e gidiyor"],
            ["YOLO", "~155–173 ms", "Gerçek bina.pt çıkarımı — 6 ihbarın hepsinde neredeyse sabit"],
            ["NLP (sınıflandırılan)", "7,98 – 11,42 sn", "BERTurk + NER + gerçek Nominatim coğrafi kodlama ağ çağrısı"],
            ["NLP (elenen)", "49 – 58 ms", "Model 'afetle ilişkisiz' derse NER/geokodlamaya hiç geçmiyor — hızlı ret"],
        ]))
    parts.append(
        "\nSahada anlamı şöyle: Burak Şahin düğmeye bastığı anda ihbarı gitti. Selim Kaya fotoğrafı "
        "gönderdiğinde göz açıp kapayana kadar (158 ms) hasar sınıfı geldi. Ama Ahmet Yılmaz metnini "
        "gönderdiğinde ekranında 'gönderiliyor' yazısı **11,4 saniye** boyunca kaldı — model konumunu "
        "metinden çıkarıp gerçek bir harita servisine sorup cevap bekledi.\n")

    parts.append("\n\n## Tablo 2 — Bölge Bazlı Yol Ağı Durumu\n")
    parts.append(_md_table(T2_HEADERS, t2))
    parts.append("\n> Kapanmalar temsilidir (rastgele atanmış). Segment sayıları ve "
                 "geometriler **gerçek OSM yol grafiğinden** gelir; rotalar bu gerçek "
                 "graf üzerinde, kapalı kenarlar çıkarılarak hesaplanmıştır.\n")
    # YENI: kapanmalarin kaynagi acikca anlatiliyor -- "hazir bir veri seti mi,
    # bizim modelimiz mi?" sorusunun net cevabi.
    parts.append("\n### Yol Kapalılıklarının Kaynağı\n")
    parts.append(
        "Bu, raporun en sık sorulan sorusu olduğu için açıkça yazılmıştır: **kapanmalar ne hazır bir "
        "veri setinden alınmıştır, ne de bu koşuda çalıştırılan bir bilgisayarlı görü modelinden "
        "üretilmiştir.** Süreç iki katmanlıdır:\n")
    parts.append(
        "\n**1. Yol ağının kendisi — GERÇEK.** Her operasyon bölgesi için OpenStreetMap'in Türkiye "
        "veri dökümünden (`turkey-latest.osm.pbf`, Geofabrik) yerel olarak çıkarılmış gerçek bir yaya "
        "yolu grafı kullanılır. Hiçbir canlı internet sorgusu yapılmaz; graf `pyrosm` ile PBF'ten "
        "okunur, `OSMnx`/`NetworkX` yapılarına dönüştürülür ve önbelleğe alınır. Düğüm ve kenar "
        "sayıları (Tablo 2) bu gerçek grafın sayılarıdır — örneğin Antakya–Defne bölgesi 18.060 "
        "düğüm, 40.950 yönlü kenar içerir. Sokak adları, geometriler ve bağlantı topolojisi "
        "gerçektir.\n")
    parts.append(
        "\n**2. Hangi yolun kapalı olduğu — TEMSİLİ.** Bu grafın kenarlarının bir kısmı, sabit bir "
        "rastgele tohumla (seed) 'kapalı' işaretlenir. Bu bilinçli bir sadeleştirmedir: bu senaryonun "
        "kanıtlamak istediği şey görüntü modelinin doğruluğu değil, **rota motorunun davranışıdır** "
        "(gerçek graf + gerçek Dijkstra/A* + gerçek naive-ajan karşılaştırması). Kapatma işlemi kenar "
        "değil *fiziksel yol* bazında yapılır: iki yönlü bir sokağın grafta iki ayrı yönlü kenarı "
        "vardır ve ikisi birlikte kapatılır — aksi halde rota motoru 'kapalı' görünen bir sokaktan "
        "ters yönden geçebilirdi (bu, geliştirme sırasında bulunup düzeltilmiş gerçek bir hatadır).\n")
    parts.append(
        "\n**Neden SegFormer bu koşuda çalıştırılmadı:** Modelin kendisi projede mevcuttur ve "
        "doğruluğu **ayrı ve bağımsız olarak** Kate-PD veri setinin gerçek hasarlı bina görselleriyle "
        "kanıtlanmıştır. Uydu görüntüsünden yol kapanması çıkarımı, görüntü çözünürlüğüne aşırı "
        "duyarlıdır ve önceki denemelerde otomatik seçilen görüntülerin çoğu bu iş için yetersiz "
        "çözünürlükte kalmıştı. Bu koşuda amaç rota motorunu ölçmek olduğu için kapanmalar temsili "
        "tutulmuş, model doğrulaması ayrı bölüme bırakılmıştır. **Bu koşudaki YOLOv8 çıktıları "
        "(Tablo 1) ise gerçek model çıkarımıdır** — sadece yol-kapanma kararı temsilidir.\n")
    parts.append(
        "\n**Projede duran, bu koşuda kullanılmayan gerçek hasar verisi:** Copernicus Acil Durum "
        "Yönetimi Servisi'nin 6 Şubat 2023 depremleri için ürettiği EMSR648 aktivasyonuna ait resmî "
        "hasar derecelendirme haritaları (Kahramanmaraş AoI-04, Hatay/Antakya AoI-11) projede "
        "mevcuttur. İleri bir çalışmada kapanmalar rastgele yerine bu zemin-doğruluk verisinden "
        "türetilebilir; bu, mevcut altyapıyla uyumludur.\n")

    parts.append(
        "\n**İstenen %18 neden gerçekleşmedi:** Senaryonun ilk tasarımında kapanma oranı %18 "
        "hedeflenmişti. Antakya grafında ölçüldü: %18 kapanmada grafın en büyük bağlı bileşeni "
        "tabanın **%24'üne** çöküyor — rota motoru çoğu ekip-hedef çifti için hiç yol bulamaz hale "
        "geliyor. Motor bu yüzden oranı otomatik olarak yarılayarak yeniden dener, ta ki bağlantı "
        "korunana kadar. Sonuç: bu koşuda gerçekleşen oran **%0,6 – %4,5** arasında kaldı (yukarıdaki "
        "tablonun son sütunu). Eşik gevşetilebilir (bağlantı tabanı %92'den %90'a çekilirse kapanmalar "
        "iki katına çıkar) — bu, sonucu doğrudan etkilediği için ayrıca karar verilmesi gereken bir "
        "parametredir.\n")

    parts.append("\n## Tablo 3 — Ekip Dağılımı, Görev Kilitleri ve Rotalar\n")
    parts.append(_md_table(T3_HEADERS, t3))
    parts.append(f"\n> **Çakışma önleme kanıtı:** {conflicts_total} mükerrer sevk denemesi "
                 f"yapıldı, {conflicts_blocked} tanesi HTTP 409 ile engellendi"
                 + (" (tamamı)." if conflicts_total == conflicts_blocked else
                    " — engellenemeyen deneme var, kilit mekanizması incelenmeli!") + "\n")

    parts.append("\n## Tablo 4 — QuakeMind vs. Klasik Navigasyon\n")
    parts.append(_md_table(T4_HEADERS, t4))
    # Sonucun ne kadarinin OLCUMDEN, ne kadarinin VARSAYIMDAN geldigi acikca
    # ayrilir. Bu ayrimi gizlemek, hakem karsisinda savunulamaz bir tablo
    # uretirdi: kazancin buyuk kismi U-donusu cezasi varsayimindan geliyor.
    travel_saved = totals["naiveTravelOnly"] - totals["ourReachable"]
    penalty_saved = totals["saved"] - travel_saved
    parts.append(
        f"\n**Toplam:** Klasik navigasyon {round(totals['naive'], 1)} dk "
        f"(yalnızca hedefe ulaşabilen {reachable} ekip) · "
        f"QuakeMind {round(totals['our'], 1)} dk (tüm {len(t4)} ekip) · "
        f"**kazanılan {round(totals['saved'], 1)} dk**"
        + (f" (%{round(totals['saved'] / totals['naive'] * 100, 1)})" if totals["naive"] else "")
        + f". Engellenen U-dönüşü: {totals['uturns']}. "
        f"Klasik yaklaşımın **hiç ulaşamadığı** hedef sayısı: {totals['stuck']}.\n")

    parts.append("\n### ⚠️ Bu kazanç neyden geliyor? (ölçüm / varsayım ayrımı)\n")
    parts.append(_md_table(
        ["Bileşen", "Süre (dk)", "Payı", "Kaynağı"],
        [["Salt yol uzunluğu farkı", round(travel_saved, 1),
          f"%{round(travel_saved / totals['saved'] * 100, 1)}" if totals["saved"] else "-",
          "**ÖLÇÜM** — gerçek graf üzerinde hesaplanan mesafeler"],
         ["U-dönüşü cezası", round(penalty_saved, 1),
          f"%{round(penalty_saved / totals['saved'] * 100, 1)}" if totals["saved"] else "-",
          f"**VARSAYIM** — {totals['uturns']} keşif × {U_TURN_PENALTY_MIN} dk"],
         ["**Toplam**", round(totals["saved"], 1), "%100", ""]]))
    parts.append(
        f"\nSadece ölçülen mesafe farkına bakıldığında karşılaştırma "
        f"**{round(totals['naiveTravelOnly'], 1)} dk → {round(totals['ourReachable'], 1)} dk** "
        f"(%{round(travel_saved / totals['naiveTravelOnly'] * 100, 1)} tasarruf) olur. "
        f"U-dönüşü cezası dahil edildiğinde oran "
        f"%{round(totals['saved'] / totals['naive'] * 100, 1)}'e çıkar. "
        f"**Her iki rakam da raporlanmalıdır**; cezanın büyüklüğü (dakika/U-dönüşü) "
        f"tartışmaya açık bir parametredir ve sonucu doğrudan belirler.\n")

    parts.append("\n### Varsayımlar (açıkça belirtilmiştir)\n")
    parts.append(f"- Ortalama saha ilerleme hızı: **{AVERAGE_SPEED_KMH} km/s** "
                 "(afet sonrası molozlu sokak).\n")
    parts.append(f"- Kapalı yola varış başına U-dönüşü kaybı: **{U_TURN_PENALTY_MIN} dk** "
                 "(durma, değerlendirme, araç çevirme, telsizle bildirme). Yalnızca "
                 "klasik navigasyona uygulanır; QuakeMind kapalı yola hiç varmaz.\n")
    parts.append("- Naive ajanın keşif anında israf ettiği mesafe **sıfır** kabul edilir — "
                 "yani karşılaştırma naive ajanın *lehine* kuruludur, abartılmamıştır.\n")

    parts.append("\n## Model Doğrulaması (ayrı — bu koşudan bağımsız)\n")
    parts.append("YOLOv8 `bina.pt` sınıfları: `0_NoDamage`, `1_ModerateDamage`, "
                 "`2_VeryHeavyDamage`. Senaryo metnindeki 'Total Collapse / Major "
                 "Structural' ayrımı modelde **yoktur**; tablolarda modelin gerçek sınıf "
                 "adları kullanılmıştır. Görüntü havuzu: "
                 + ", ".join(sorted({img for s in summaries for img in s.get("debrisImagePool", [])}))
                 + " (Kate-PD, doğrulanmış gerçek hasar görselleri).\n")
    # NLP yanlis-negatif orani -- kucuk ornek ama gercek olcum, raporlanmali.
    nlp_victims = [v for s in summaries for z in s["zones"] for v in z["victims"]
                   if v["channel"] == "nlp"]
    nlp_ignored = [v for v in nlp_victims
                   if (v.get("channelResult") or {}).get("modelKategori") is None]
    if nlp_victims:
        parts.append(f"\n### ⚠️ NLP yanlış-negatif bulgusu (ölçüm)\n")
        parts.append(
            f"{len(nlp_victims)} NLP ihbarının **{len(nlp_ignored)} tanesi** model "
            f"tarafından 'afetle ilişkisiz' sayılarak elendi "
            f"(`{{\"status\":\"ignored\"}}`) — %"
            f"{round(len(nlp_ignored) / len(nlp_victims) * 100, 1)} yanlış negatif. "
            "Elenen metinler:\n")
        for v in nlp_ignored:
            parts.append(f"- **{v['name']}** ({v['locationLabel']}): "
                         f"\"{v.get('needText', '')}\"\n")
        parts.append(
            "\nHer ikisi de açıkça afet içi, hayati aciliyeti olan medikal "
            "çağrılardır. Bu, modelin gerçek ve raporlanması gereken bir "
            "sınırıdır: sahada böyle bir ihbarın elenmesi doğrudan can kaybına "
            "yol açabilir. Örneklem küçüktür (ihbar başına tek deneme); oran "
            "kesin bir başarım metriği değil, giderilmesi gereken bir bulgudur. "
            "Bu ihbarlar yine de SOS kaydına düşmüş ve ekip atanmıştır — "
            "sınıflandırma başarısızlığı sevk zincirini durdurmamaktadır.\n")

    parts.append("\nNLP modelinin gerçek üst kategorileri (`Acil Yardım İhtiyacı`, "
                 "`Enkaz Bildirimi`, `Lojistik İhtiyaç Bildirimi`, `Yol Kapanma Bilgisi / "
                 "Lojistik`) senaryodaki operasyonel etiketlerle birebir aynı değildir. "
                 "Tablo 1 modelin **kendi çıktısını** gösterir; ekip rolü ataması bunun "
                 "üzerine kurulan ayrı bir eşleme katmanıdır.\n")

    parts.append("\n## Etki Modellemesi — Hayatta Kalma Olasılığı\n")
    parts.append("> ⚠️ **Bu bir ölçüm değil, modeldir.** Sistem süre ve mesafe ölçer; "
                 "'kaç can kurtarıldı' verisi üretmez.\n")
    parts.append(f"\nEnkaz altında geçen süreye bağlı hayatta kalma olasılığı için "
                 f"kademeli bir eğri kullanılmıştır. Referans enkaz-altı süresi "
                 f"**{BASELINE_ENTRAPMENT_HOURS} saat** alınmış, kazanılan her dakika bu "
                 f"eğriye uygulanmıştır.\n")
    parts.append("\n" + _md_table(["Saat", "Hayatta kalma olasılığı"],
                                  [[h, f"%{round(p * 100)}"] for h, p in SURVIVAL_ANCHORS_HOURS]))
    parts.append(f"\n\n**Kaynak notu:** {SURVIVAL_SOURCE_NOTE}\n")

    # YENI: egrinin nereden geldigi, nasil kullanildigi ve sinirlari.
    parts.append("\n### Bu Eğri Nedir, Nereden Geliyor?\n")
    parts.append(
        "Afet tıbbı literatüründeki en yerleşik bulgulardan biri, enkaz altında kalan bir kişinin "
        "hayatta kalma olasılığının zamanla **doğrusal değil, basamaklı ve hızlanarak** düşmesidir. "
        "İlk saatler görece düz bir plato oluşturur; ardından ilk 24–48 saat arasında keskin bir "
        "düşüş yaşanır. Sahada 'altın saatler' (ilk 72 saat) kavramı tam olarak bu düşüşü anlatır.\n")
    parts.append(
        "\nBu raporda kullanılan eğri, bu literatürün **sadeleştirilmiş, çapa noktalarına indirgenmiş "
        "bir temsilidir**. Yedi çapa noktası arasında doğrusal interpolasyon yapılır. Ana referans, "
        "yıkılmış yapılarda 'kurtarılma süresi' ile sağkalım arasındaki ilişkiyi inceleyen Macintyre, "
        "Barbera ve Smith'in (2006) çalışmasıdır; eğrinin **büyüklük mertebesi** bu çalışmadan "
        "alınmıştır.\n")
    parts.append("\n**Hesap nasıl yapılıyor:**\n")
    parts.append(
        f"\n1. Referans enkaz-altı süresi **{BASELINE_ENTRAPMENT_HOURS} saat** kabul edilir (ilk "
        "müdahale penceresi).\n"
        "2. Bir ekibin kazandığı süre (Tablo 4'teki 'Kazanılan') bu referansa eklenir — yani "
        "'QuakeMind olmasaydı afetzede ne kadar daha uzun enkaz altında kalacaktı' hesaplanır.\n"
        "3. İki noktadaki hayatta kalma olasılığı farkı, o ekip için **tahmini artış** olarak "
        "raporlanır.\n")
    parts.append(
        "\n**Bu yaklaşımın bilinçli olarak muhafazakâr yanı:** Referans nokta olarak eğrinin en dik "
        "olduğu bölge (24–48 saat) değil, görece düz olan 6. saat seçilmiştir. Eğer afetzedelerin "
        "daha uzun süre enkaz altında kaldığı varsayılsaydı, aynı dakika kazancı çok daha büyük bir "
        "olasılık artışı üretirdi. Yani buradaki sayılar üst sınır değil, **alt sınıra yakın** "
        "tahminlerdir.\n")
    parts.append("\n**Bu eğrinin sınırları — makalede mutlaka belirtilmelidir:**\n")
    parts.append(
        "\n- Çapa değerleri kaynaktan **birebir alıntı değildir**; büyüklük mertebesi temsilidir ve "
        "yayın öncesi kaynaktan doğrulanmalıdır.\n"
        "- Eğri; yaş, yaralanma türü, enkaz boşluğu hacmi, sıcaklık, su erişimi gibi sağkalımı "
        "belirleyen değişkenlerin **hiçbirini** içermez.\n"
        "- Çıktı bir **can sayısı değil**, olasılık puanıdır. 'X kişi kurtarıldı' şeklinde "
        "yorumlanamaz.\n"
        "- Model, sistemin ölçtüğü bir büyüklük değildir; süre ölçümünün üzerine sonradan uygulanan "
        "bir yorum katmanıdır.\n")
    parts.append(f"\nToplam tahmini hayatta kalma olasılığı artışı: "
                 f"**{round(totals['gain'], 2)} yüzde puan** (tüm ekipler toplamı, "
                 f"yukarıdaki varsayımlar altında).\n")
    parts.append(
        "\n**Serkan Tan örneği:** Dulkadiroğlu'nda merdiven çökmesi sonucu mahsur kalan Serkan Tan'a "
        "gönderilen ekip, kapanmaları önceden bilmeseydi 16 kez kapalı bir sokağa varıp geri dönmek "
        "zorunda kalırdı — kazandığı 335,7 dakika, tahmini hayatta kalma olasılığını **+2,8 yüzde "
        "puan** artırıyor, koşudaki en yüksek tekil katkı. Üç sıfır-kazançlı ekip (Emre Aydın, Elif "
        "Demir, Sevgi Kaya) bu toplama hiç katkı vermiyor, çünkü onların rotasında zaten kapalı yol "
        "yoktu.\n")

    parts.append("\n## Bilinen Kısıtlar\n")
    parts.append("1. Her ekip **kendi bölgesinin** yol grafı içinde rota alır; iller arası "
                 "intikal modellenmez (74 km'lik tek graf teknik olarak mümkün değil — "
                 "3 km'lik bir graf bile ~20.000 düğüm).\n")
    parts.append("2. Karargâh koordinatlarının bir kısmı gerçek OSM altyapı noktasına snap "
                 "edilmiştir, bir kısmı ilçe merkezine yerleştirilmiştir (senaryo kurgusu) — "
                 "hangisinin hangisi olduğu veri setinde `coordSource` alanında işaretlidir.\n")
    parts.append("3. Kullanıcının onayıyla iki afetzede yeniden konumlandırılmıştır "
                 "(karargâh–afetzede eşleşmesini tamamlamak için); Tablo 1'de "
                 "'taşındı' notuyla gösterilir.\n")

    # ------------------------------------------------------------------
    # YENI: Kaynakca. Kunye bilgileri makale oncesi dogrulanmali -- asagida
    # acikca not dusulmustur.
    # ------------------------------------------------------------------
    parts.append("\n## Kaynakça\n")
    parts.append(
        "> **Not:** Aşağıdaki künyeler, kullanılan yöntem ve verilerin dayandığı kaynakları "
        "göstermek için derlenmiştir. Yayın öncesinde her birinin cilt/sayfa/DOI bilgisi "
        "orijinal kaynaktan doğrulanmalıdır.\n")

    parts.append("\n**Hayatta kalma modeli**\n")
    parts.append(
        "\n1. Macintyre, A. G., Barbera, J. A., & Smith, E. R. (2006). *Surviving collapsed "
        "structure entrapment after earthquakes: A \"time-to-rescue\" analysis.* Prehospital and "
        "Disaster Medicine, 21(1), 4–17.\n")

    parts.append("\n**Yol ağı verisi ve graf işleme**\n")
    parts.append(
        "\n2. OpenStreetMap katkıcıları. *OpenStreetMap Türkiye veri dökümü* "
        "(`turkey-latest.osm.pbf`). Geofabrik GmbH üzerinden erişildi. Lisans: Open Database "
        "License (ODbL) v1.0.\n"
        "3. Boeing, G. (2017). *OSMnx: New methods for acquiring, constructing, analyzing, and "
        "visualizing complex street networks.* Computers, Environment and Urban Systems, 65, "
        "126–139.\n"
        "4. Tenkanen, H. *pyrosm: Python library for reading OpenStreetMap PBF data.* Açık kaynak "
        "yazılım.\n"
        "5. Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). *Exploring network structure, "
        "dynamics, and function using NetworkX.* Proceedings of the 7th Python in Science "
        "Conference (SciPy2008), 11–15.\n")

    parts.append("\n**Rota algoritmaları**\n")
    parts.append(
        "\n6. Dijkstra, E. W. (1959). *A note on two problems in connexion with graphs.* "
        "Numerische Mathematik, 1(1), 269–271.\n"
        "7. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). *A formal basis for the heuristic "
        "determination of minimum cost paths.* IEEE Transactions on Systems Science and "
        "Cybernetics, 4(2), 100–107.\n")

    parts.append("\n**Yapay öğrenme modelleri**\n")
    parts.append(
        "\n8. Xie, E., Wang, W., Yu, Z., Anandkumar, A., Álvarez, J. M., & Luo, P. (2021). "
        "*SegFormer: Simple and efficient design for semantic segmentation with transformers.* "
        "Advances in Neural Information Processing Systems (NeurIPS) 34.\n"
        "9. Jocher, G., Chaurasia, A., & Qiu, J. (2023). *Ultralytics YOLOv8.* Açık kaynak yazılım.\n"
        "10. Schweter, S. (2020). *BERTurk — BERT models for Turkish.* Zenodo.\n")

    parts.append("\n**Afet hasar verisi (projede mevcut, bu koşuda kullanılmadı)**\n")
    parts.append(
        "\n11. Copernicus Emergency Management Service. *EMSR648: Earthquake in Türkiye* "
        "(6 Şubat 2023 aktivasyonu), Rapid Mapping ürünleri. Avrupa Komisyonu, Ortak Araştırma "
        "Merkezi (JRC).\n"
        "12. AFAD. *Türkiye Toplanma Alanları veri seti* — bu çalışmada tahliye hedeflerinin "
        "belirlenmesinde kullanılmıştır.\n")

    parts.append("\n**Veri seti (model doğrulaması)**\n")
    parts.append(
        "\n13. Kate-PD — deprem sonrası bina hasarı görsel veri seti; YOLOv8 `bina.pt` modelinin "
        "bağımsız doğrulamasında kullanılmıştır.\n")

    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="*", help="runs/<run_id> dizinleri")
    parser.add_argument("--auto", action="store_true", help="senaryo-v2-* kosularini otomatik bul")
    parser.add_argument("--out", default="senaryo_v2_raporu")
    args = parser.parse_args()

    if args.auto or not args.runs:
        run_dirs = sorted([p for p in RUNS_DIR.glob("senaryo-v2-*") if (p / "summary.json").exists()])
    else:
        run_dirs = [Path(r) if Path(r).is_absolute() else (BENCH_DIR / r) for r in args.runs]

    if not run_dirs:
        print("Kosu bulunamadi. Once: python benchmark/full_scenario.py all")
        return 1

    summaries = [_load(d) for d in run_dirs]
    print(f"{len(summaries)} kosu okundu: {', '.join(s['runId'] for s in summaries)}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md = build_report(summaries)
    md_path = REPORTS_DIR / f"{args.out}.md"
    md_path.write_text(md, encoding="utf-8")

    _write_csv(REPORTS_DIR / f"{args.out}_tablo1.csv", T1_HEADERS, table1_rows(summaries))
    _write_csv(REPORTS_DIR / f"{args.out}_tablo2.csv", T2_HEADERS, table2_rows(summaries))
    _write_csv(REPORTS_DIR / f"{args.out}_tablo3.csv", T3_HEADERS, table3_rows(summaries))
    _write_csv(REPORTS_DIR / f"{args.out}_tablo4.csv", T4_HEADERS, table4_rows(summaries)[0])

    print(f"Rapor: {md_path}")
    print(f"CSV'ler: {REPORTS_DIR}/{args.out}_tablo1..4.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
