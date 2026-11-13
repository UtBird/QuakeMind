"""Bolum C ekran goruntulerini yerel backend+frontend'den ceker.

On kosul: backend http://127.0.0.1:8000, frontend http://localhost:3000 calisiyor
olmali (bkz. makale/DEVAM_NOTU_2026-09-24.md kurulum adimlari). Playwright ayri bir
venv'de kurulu olmali:
    <python3.12> -m venv .playwright_venv
    ./.playwright_venv/Scripts/python.exe -m pip install playwright
    ./.playwright_venv/Scripts/python.exe -m playwright install chromium

Calistirma (repo kokunden):
    ./.playwright_venv/Scripts/python.exe backend/capture_app_screenshots.py

Ciktilar makale/sekiller_hazir/ altina yazilir:
    1_catlak_tespit.png   (Sekil 21) -- yalniz QM_CRACK_PHOTO env degiskeni bir
                                         foto yolu gosteriyorsa cekilir
    2_risk_skoru.png      (Sekil 22)
    3_nlp_harita.png      (Sekil 23)
    4_isi_haritasi_guzergah.png (Sekil 24)

Sekil 21 icin gercek bir catlak/bina hasari fotografi gerektigi icin, o foto
QM_CRACK_PHOTO env degiskeni ile verilir; yoksa o adim atlanir.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "makale" / "sekiller_hazir"
OUT.mkdir(parents=True, exist_ok=True)

CRACK_PHOTO = os.environ.get("QM_CRACK_PHOTO", "").strip()

# Harita kosesindeki Leaflet atif/filigran rozetini (ör. "Leaflet | Zemin: Esri",
# "© Google (Simülasyon)") makale gorsellerinden gizler. Atif, makale metninde/
# altyazida verildigi icin gorselden kaldirilmasi tercih ediliyor.
HIDE_ATTRIBUTION = ".leaflet-control-attribution{display:none !important;}"


def hide_map_badges(page):
    try:
        page.add_style_tag(content=HIDE_ATTRIBUTION)
    except Exception as exc:
        print("   (atif rozeti gizlenemedi:", exc, ")")


def login(page):
    page.goto("http://localhost:3000/login", wait_until="load", timeout=60000)
    page.click("text=Demo Hesaplarla Hızlı Giriş (Test Amaçlı)")
    page.wait_for_timeout(500)
    page.click("text=Afet Saha Ekibi")
    page.wait_for_url("**/command**", timeout=15000)
    page.wait_for_timeout(1500)
    print("Logged in, current url:", page.url)


def capture_risk(page):
    """Sekil 22 -- Deprem risk & fay hatti analizi."""
    page.goto("http://localhost:3000/command/risk", wait_until="load", timeout=60000)
    page.wait_for_timeout(1000)
    page.click("text=Deprem Riskini Hesapla")
    # Sonuca ozel bir etiket bekle (backend model yukluyorsa istek gecikebilir)
    page.wait_for_selector("text=Maks Büyüklük", timeout=180000)
    page.wait_for_timeout(3000)  # harita tile'larinin (Esri Dark Gray) tam yuklenmesi
    hide_map_badges(page)
    page.screenshot(path=str(OUT / "2_risk_skoru.png"), full_page=True)
    print("risk screenshot saved ->", OUT / "2_risk_skoru.png")


def capture_nlp(page):
    """Sekil 23 -- Afet metin NLP + harita."""
    page.goto("http://localhost:3000/command/nlp", wait_until="load", timeout=60000)
    page.wait_for_timeout(1000)
    page.click("text=NLP İhbar Analizini Çalıştır")
    # Ilk NLP isteginde BERTurk indirilebilir -> uzun timeout
    page.wait_for_selector("text=Yapay Zeka Analiz Çıktısı", timeout=240000)
    page.wait_for_timeout(2500)
    hide_map_badges(page)
    page.screenshot(path=str(OUT / "3_nlp_harita.png"), full_page=True)
    print("nlp screenshot saved ->", OUT / "3_nlp_harita.png")


def capture_road_damage(page):
    """Sekil 24 -- Isi haritasi + guvenli/tikali yol agi.

    Gercek Segformer analizi CPU'da dakikalarca surer ve uydu/OSM erisimi
    gerektirir; makale gorseli icin uygulamanin yerlesik "Ornek Verilerle
    Simule Et" (demo) senaryosu kullanilir -- isi haritasi + acik/tikali yol
    agini gercekci bicimde doldurur. Modellerin kendisi gercektir; bu yalniz
    arayuzu tanitan bir ekran goruntusudur.
    """
    page.goto("http://localhost:3000/command/road-damage", wait_until="load", timeout=60000)
    page.wait_for_timeout(1500)
    # Navbar'daki global demo dugmesi -> road-damage sayfasi useEffect ile
    # handleLoadDemo cagirir (isi haritasi + yol agi + showHeatmap=true).
    page.click("text=Örnek Verilerle Simüle Et")
    # Isi haritasi yuklenene ve yol agi cizilene kadar bekle
    page.wait_for_selector("text=Analiz Sonuçları", timeout=30000)
    page.wait_for_timeout(3500)  # heatmap + Esri tile'lari otursun
    hide_map_badges(page)
    page.screenshot(path=str(OUT / "4_isi_haritasi_guzergah.png"), full_page=True)
    print("road-damage screenshot saved ->", OUT / "4_isi_haritasi_guzergah.png")


def capture_crack(page):
    """Sekil 21 -- Kamera ile catlak/bina hasar tespiti (gercek YOLO cikarimi).

    QM_CRACK_PHOTO bir foto yolu gosteriyorsa "Galeriden Yükle" moduna gecip
    fotografi yukler, catlak.pt/bina.pt hibrit YOLO cikarimini calistirir ve
    sonucu (annotate edilmis goruntu + tespit kutulari) yakalar.
    """
    if not CRACK_PHOTO:
        print("QM_CRACK_PHOTO tanimli degil -> Sekil 21 atlaniyor.")
        return
    photo = Path(CRACK_PHOTO)
    if not photo.exists():
        print(f"QM_CRACK_PHOTO bulunamadi: {photo} -> Sekil 21 atlaniyor.")
        return
    page.goto("http://localhost:3000/command/camera", wait_until="load", timeout=60000)
    page.wait_for_timeout(1000)
    page.click("text=Galeriden Yükle")
    page.wait_for_timeout(500)
    # Gizli file input'a fotografi yukle
    page.set_input_files("input[type=file]", str(photo))
    page.wait_for_timeout(1000)
    page.click("text=FOTOĞRAFI YOLO İLE ANALİZ ET")
    # Gercek YOLO cikarimi sonucu -> tespit karti gorunene kadar bekle
    page.wait_for_selector("text=MODEL TESPİT ÇIKTILARI", timeout=120000)
    page.wait_for_selector("text=Tespit Edilen YOLO Kutuları", timeout=120000)
    page.wait_for_timeout(2000)
    page.screenshot(path=str(OUT / "1_catlak_tespit.png"), full_page=True)
    print("crack screenshot saved ->", OUT / "1_catlak_tespit.png")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        login(page)

        # QM_ONLY=crack,risk gibi bir liste verilirse yalniz o adimlar calisir.
        only = [s.strip() for s in os.environ.get("QM_ONLY", "").split(",") if s.strip()]
        steps = [("crack", capture_crack), ("risk", capture_risk),
                 ("nlp", capture_nlp), ("road_damage", capture_road_damage)]
        if only:
            steps = [(n, f) for (n, f) in steps if n in only]
        for name, fn in steps:
            try:
                fn(page)
            except Exception as exc:
                print(f"!! {name} BASARISIZ: {exc}")
                try:
                    page.screenshot(path=str(OUT / f"_debug_{name}.png"), full_page=True)
                    print(f"   teshis screenshot -> _debug_{name}.png")
                except Exception:
                    pass

        browser.close()


if __name__ == "__main__":
    main()
