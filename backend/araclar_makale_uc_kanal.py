"""Makale şekli: üç kanal tek haritada (J-108).

Makalenin asıl iddiası, yazında ayrı ayrı çözülmüş üç işin TEK karar zincirinde
birleştirilmesi. Şimdiye kadarki şekiller bunu göstermiyordu: uydu kanalı ve
rotalar vardı, kamera ile metin yoktu. Bu araç üçünü aynı mahalle karesine
koyar ve zincirin sonunu da çizer (kapalı yollar + ekip güzergâhı).

Karede ne var:
  · zemin      — gerçek ortofoto/uydu görüntüsü (tarihli, sağlayıcısı yazılı)
  · kırmızı    — modelin hasarlı bulduğu piksel  (uydu kanalı)
  · sarı kare  — kamera kanalı: gerçek deprem fotoğrafı, gerçek YOLO tespiti
  · mor daire  — metin kanalı: sentetik ihbar, gerçek BERTurk sınıfı
  · koyu kırmızı kalın — kapanan yol
  · mavi       — ekibin güzergâhı (kapanmalara göre)
  · sağ altta  — bir kamera fotoğrafının kendisi, tespit kutuları çizili

DÜRÜSTLÜK: fotoğraflar ve bütün model çıktıları gerçektir; ihbar METİNLERİ ve
kamera/metin kanallarının HARİTADAKİ KONUMU üretilmiştir. Bu, göstergenin
üstündeki künye satırında ve şeklin altındaki notta yazılıdır (kural 1).

Koşum:
    venv/Scripts/python.exe araclar_makale_uc_kanal.py --alan Defne
    venv/Scripts/python.exe araclar_makale_uc_kanal.py --hepsi
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from araclar_makale_haritalari import _gorsel, _gosterge, _yazitipi  # noqa: E402

CIK = KOK / "benchmark" / "makale_sekilleri"
ALANLAR_DOSYASI = KOK / "apps" / "road_damage" / "data" / "tatbikat_alanlari.json"

# Konsoldaki renklerle AYNI (tasarim/token.css): okuyucu ekranda gördüğünü
# makalede de tanısın.
R_HASAR = (209, 51, 46)
R_KAPALI = (150, 20, 18)
R_ACIK = (0, 200, 240)
R_ROTA = (31, 111, 235)
R_KAMERA = (242, 193, 78)   # --color-ch-cam
R_METIN = (176, 140, 255)   # --color-ch-nlp


def _sar(d, metin, font, en):
    """Metni `en` pikseli asmayacak satirlara boler."""
    kelimeler, satirlar, suan = metin.split(), [], ""
    for k in kelimeler:
        deneme = (suan + " " + k).strip()
        if d.textlength(deneme, font=font) <= en or not suan:
            suan = deneme
        else:
            satirlar.append(suan); suan = k
    if suan:
        satirlar.append(suan)
    return satirlar


def _gosterge_sarmali(im, satirlar, baslik=""):
    """Alt gosterge seridi -- ORTAK `_gosterge`den farki: metni sarmalar ve
    seridin yuksekligini icerige gore hesaplar.

    Ortak fonksiyon tek satir cizip tasani kesiyordu; kunyedeki
    "URETILEN: ..." uyarisi sagdan kirpiliyordu (J-110). Bu sekilde o uyari
    seklin en onemli parcasi, kirpilmamali.
    """
    boy = max(15, im.width // 62)
    f_kunye = _yazitipi(int(boy * 0.92))
    f_satir = _yazitipi(boy)
    kenar, isaret_en = boy, boy * 2
    metin_en = im.width - 2 * kenar - isaret_en - boy // 2

    olcer = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    kunye_satirlari = _sar(olcer, baslik, f_kunye, im.width - 2 * kenar) if baslik else []
    coz = [(r, b, _sar(olcer, m, f_satir, metin_en)) for r, b, m in satirlar]

    kunye_h = int(boy * 1.35) * len(kunye_satirlari)
    govde_h = sum(int(boy * 1.35) * len(s[2]) + int(boy * 0.55) for s in coz)
    yuk = kunye_h + govde_h + int(boy * 1.6)

    y = Image.new("RGB", (im.width, im.height + yuk), (255, 255, 255))
    y.paste(im.convert("RGB"), (0, 0))
    d = ImageDraw.Draw(y)

    yy = im.height + int(boy * 0.5)
    for s in kunye_satirlari:
        d.text((kenar, yy), s, fill=(60, 60, 60), font=f_kunye)
        yy += int(boy * 1.35)
    yy += int(boy * 0.6)

    for renk, bicim, metin_satirlari in coz:
        cx, cy, m = kenar, yy, boy
        if bicim == "cizgi":
            d.line([(cx, cy + m // 2), (cx + m * 2, cy + m // 2)], fill=renk, width=max(2, boy // 5))
        elif bicim == "cizgi-kalin":
            d.line([(cx, cy + m // 2), (cx + m * 2, cy + m // 2)], fill=renk, width=max(5, boy // 2))
        elif bicim == "alan":
            d.rectangle([cx, cy, cx + m * 2, cy + m], fill=renk + (150,) if len(renk) == 3 else renk)
        elif bicim == "daire":
            d.ellipse([cx + m // 2, cy, cx + m * 3 // 2, cy + m], fill=renk,
                      outline=(90, 90, 90), width=2)
        elif bicim == "kare":
            d.rectangle([cx + m // 2, cy, cx + m * 3 // 2, cy + m], fill=renk,
                        outline=(40, 40, 40), width=2)
        for i, s in enumerate(metin_satirlari):
            d.text((cx + isaret_en + boy // 2, cy - 2 + i * int(boy * 1.35)), s,
                   fill=(20, 20, 20), font=f_satir)
        yy += int(boy * 1.35) * len(metin_satirlari) + int(boy * 0.55)
    return y


def _etiket_koy(d, yerlesenler, x, y, metin, font):
    """Isaret etiketini CAKISMADAN koyar (J-110: M4 ile K1 ust uste biniyordu).

    Once saga, sonra sola, sonra ust/alta denenir; hicbiri bos degilse yine
    saga konur (kaybolmasin, uzerine binsin).
    """
    en = d.textlength(metin, font=font)
    yuk = font.size + 4
    for dx, dy in ((18, -12), (-en - 18, -12), (0, -yuk - 14), (0, 14)):
        kutu = (x + dx, y + dy, x + dx + en, y + dy + yuk)
        if all(kutu[2] < o[0] or kutu[0] > o[2] or kutu[3] < o[1] or kutu[1] > o[3]
               for o in yerlesenler):
            yerlesenler.append(kutu)
            d.text((kutu[0], kutu[1]), metin, font=font, fill=(255, 255, 255, 255),
                   stroke_width=4, stroke_fill=(0, 0, 0, 225))
            return
    d.text((x + 18, y - 12), metin, font=font, fill=(255, 255, 255, 255),
           stroke_width=4, stroke_fill=(0, 0, 0, 225))


def _foto_seridi(im, foto, baslik, alt_satirlar):
    """Haritanin ALTINA fotograf seridi ekler (haritayi kapatmaz)."""
    boy = max(15, im.width // 62)
    kenar = boy
    yuk = foto.height + 2 * kenar
    y = Image.new("RGB", (im.width, im.height + yuk), (248, 248, 248))
    y.paste(im.convert("RGB"), (0, 0))
    d = ImageDraw.Draw(y)
    fy = im.height + kenar
    d.rectangle([kenar - 4, fy - 4, kenar + foto.width + 4, fy + foto.height + 4],
                fill=(30, 30, 30), outline=R_KAMERA, width=4)
    y.paste(foto, (kenar, fy))
    mx = kenar + foto.width + int(boy * 1.4)
    d.text((mx, fy + 2), baslik, fill=(20, 20, 20), font=_yazitipi(int(boy * 1.05)))
    yy = fy + int(boy * 2.0)
    for s in alt_satirlar:
        d.text((mx, yy), s, fill=(70, 70, 70), font=_yazitipi(int(boy * 0.9)))
        yy += int(boy * 1.35)
    return y


def _alan_bul(ad):
    kayitlar = json.loads(ALANLAR_DOSYASI.read_text(encoding="utf-8"))
    return next(x for x in kayitlar if ad.lower() in x["parca"].lower())


def _foto_ic_gorsel(kayit, yukseklik):
    """Kamera kaydının fotoğrafı, üstünde modelin bulduğu kutular."""
    import cv2

    from uclar.kamera import yolo_tespit

    yol = KOK / "apps" / "camera_detection" / "data" / "tatbikat_foto" / kayit["foto"]["dosya"]
    img = cv2.imread(str(yol))
    if img is None:
        return None
    dets, _m, _k = yolo_tespit(img, "hybrid")
    for d in dets:
        x1, y1, x2, y2 = [int(v) for v in d["box"]]
        renk = (224, 200, 78) if d["model"] == "catlak.pt" else (140, 224, 78)  # BGR
        cv2.rectangle(img, (x1, y1), (x2, y2), renk, max(2, img.shape[1] // 350))
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    oran = yukseklik / pil.height
    return pil.resize((int(pil.width * oran), yukseklik), Image.LANCZOS)


def tek_alan(alan_adi, model_adi, tohum=42):
    from apps.road_damage.utils import model_kunyesi, tatbikat, tatbikat_kanallar
    from apps.road_damage.worker import _init_worker, run_analysis_job

    alan = _alan_bul(alan_adi)
    k = alan["analizBbox"]
    _init_worker(model_kunyesi.kunye_oku(model_kunyesi.etkin_model_adi()))
    r = run_analysis_job({
        "_analysisId": "uckanal", "city": alan["il"], "source": "oam",
        "latitude": alan["merkez"]["lat"], "longitude": alan["merkez"]["lon"],
        "bboxWest": k[0], "bboxSouth": k[1], "bboxEast": k[2], "bboxNorth": k[3],
        "oamTileUrl": alan["tmsUrl"] if "{z}" in alan["tmsUrl"] else alan["tmsUrl"] + "/{z}/{x}/{y}.png",
        "oamPreferredTitle": alan["sahneAdi"], "modelAdi": model_adi, "radiusKm": 2.5,
    })
    ham = _gorsel(r, "imageOriginalB64").convert("RGB")
    maske = (np.asarray(_gorsel(r, "imageDamageMaskB64").convert("L")) > 127)
    s = r["bounds"]
    B = (s["west"], s["south"], s["east"], s["north"])
    W, H = ham.size
    gecerli = (np.asarray(ham.convert("L")) > 12).astype(np.uint8)

    G, sg, kapali, _kt, kapsama, _c = tatbikat.mahalle_grafigi(
        maske.astype(np.uint8), B, gecerli_maske=gecerli)
    ekip = tatbikat.giris_noktalari(G, B, sayi=5)
    kurban = tatbikat.afetzedeler(maske.astype(np.uint8), B, sayi=15, tohum=tohum)
    kurban, _e, ekip = tatbikat.ulasilabilir_afetzedeler(G, ekip, kurban)
    n = min(len(ekip), len(kurban))
    ekip, kurban = ekip[:n], kurban[:n]
    rota = tatbikat.rota_kosusu(G, sg, ekip, kurban, hiz_kmh=15.0)

    anahtar = alan["parca"]
    kam = tatbikat_kanallar.kamera_kanali(maske.astype(np.uint8), B, sayi=4, tohum=tohum,
                                          alan_anahtari=anahtar)
    met = tatbikat_kanallar.metin_kanali(
        maske.astype(np.uint8), B, il=alan["il"], sayi=5, tohum=tohum,
        alan_anahtari=anahtar,
        # Kameranın noktaları metne kapalı: iki kanal üst üste binmesin (J-110).
        kacinilacak=[(z["lat"], z["lon"]) for z in kam["kayitlar"]])

    def pik(lat, lon):
        return ((lon - B[0]) / (B[2] - B[0]) * W, (B[3] - lat) / (B[3] - B[1]) * H)

    arr = np.asarray(ham).copy()
    arr[maske] = (0.42 * arr[maske] + 0.58 * np.array(R_HASAR)).astype(np.uint8)
    tv = Image.fromarray(arr)
    d = ImageDraw.Draw(tv, "RGBA")

    kk = set(kapali)
    for u, v, key, dd in G.edges(keys=True, data=True):
        g = dd.get("geometry")
        koord = ([(la, lo) for lo, la in g.coords] if g is not None
                 else [(G.nodes[u]["y"], G.nodes[u]["x"]), (G.nodes[v]["y"], G.nodes[v]["x"])])
        p = [pik(la, lo) for la, lo in koord]
        if len(p) < 2:
            continue
        kap = (u, v, key) in kk or (v, u, key) in kk
        d.line(p, fill=(*R_KAPALI, 255) if kap else (*R_ACIK, 95), width=9 if kap else 2)
    for g in (rota.get("gorevler") or []):
        c = ((g.get("varyantlar") or {}).get("kapanmali") or {}).get("cizgi") or []
        if len(c) >= 2:
            d.line([pik(la, lo) for la, lo in c], fill=(*R_ROTA, 235), width=4)

    ekip_icerde = 0
    for e in ekip:
        x, y = pik(e["lat"], e["lon"])
        if 0 <= x < W and 0 <= y < H:
            ekip_icerde += 1
            d.ellipse([x-11, y-11, x+11, y+11], fill=(*R_ROTA, 255),
                      outline=(255, 255, 255, 255), width=3)
    for kb in kurban:
        x, y = pik(kb["lat"], kb["lon"])
        d.rectangle([x-8, y-8, x+8, y+8], fill=(255, 255, 255, 235),
                    outline=(*R_HASAR, 255), width=3)

    # --- yeni iki kanal ---
    yt = _yazitipi(22)
    yerlesenler = []
    for i, kayit in enumerate(kam["kayitlar"], 1):
        x, y = pik(kayit["lat"], kayit["lon"])
        d.rectangle([x-13, y-13, x+13, y+13], fill=(*R_KAMERA, 245),
                    outline=(20, 20, 20, 255), width=3)
        _etiket_koy(d, yerlesenler, x, y, f"K{i}", yt)
    for i, kayit in enumerate(met["kayitlar"], 1):
        x, y = pik(kayit["lat"], kayit["lon"])
        rr = 9 + kayit["aciliyet"] * 1.6
        d.ellipse([x-rr, y-rr, x+rr, y+rr], fill=(*R_METIN, 245),
                  outline=(20, 20, 20, 255), width=3)
        _etiket_koy(d, yerlesenler, x, y, f"M{i}", yt)

    # --- kamera fotoğrafı KENDİ ŞERİDİNDE ---
    # Eskiden haritanın sağ altına gömülüydü ve altında kalan işaretleri
    # gizliyordu: gösterge "5 ihbar" derken haritada 3 tanesi görünüyordu
    # (J-110). Artık haritanın altına, kendi şeridine konur; harita hiçbir
    # yerde kapanmaz.
    if kam["kayitlar"]:
        en_iyi = max(kam["kayitlar"], key=lambda z: z["tespitSayisi"])
        sira = kam["kayitlar"].index(en_iyi) + 1
        ic = _foto_ic_gorsel(en_iyi, yukseklik=max(220, H // 5))
        if ic is not None:
            tv = _foto_seridi(
                tv, ic,
                f"K{sira} işaretinin GERÇEK fotoğrafı — {en_iyi['etiket']}",
                [f"kaynak: {en_iyi['foto']['lisans']} · {en_iyi['foto']['yazar']}",
                 f"modelin bulduğu: {en_iyi['catlakSayisi']} çatlak, "
                 f"{en_iyi['binaSayisi']} bina  (kutular fotoğrafın üstünde)",
                 "camgöbeği kutu = çatlak (catlak.pt) · yeşil kutu = bina hasarı (bina.pt)"])

    catlak = sum(z["catlakSayisi"] for z in kam["kayitlar"])
    bina = sum(z["binaSayisi"] for z in kam["kayitlar"])
    rota_sayisi = sum(1 for g in (rota.get("gorevler") or [])
                      if len((((g.get("varyantlar") or {}).get("kapanmali") or {}).get("cizgi")) or []) >= 2)
    tv = _gosterge_sarmali(tv, [
        (R_ACIK, "cizgi", "Açık yol (OpenStreetMap)"),
        (R_KAPALI, "cizgi-kalin", f"Kapalı yol — modelin bulduğu ({len(kapali)} kenar)"),
        (R_HASAR, "alan", "Hasarlı piksel — UYDU kanalı (bölütleme çıktısı)"),
        (R_KAMERA, "kare",
         f"KAMERA kanalı — {len(kam['kayitlar'])} gerçek fotoğraf, YOLO: "
         f"{catlak} çatlak + {bina} bina  (konum üretildi)"),
        (R_METIN, "daire",
         f"METİN kanalı — {len(met['kayitlar'])} ihbar, BERTurk sınıfı  "
         f"(metin ve konum üretildi)"),
        (R_ROTA, "cizgi", f"Ekip güzergâhı — kapanmalara göre ({rota_sayisi} rota)"),
        # GIRIS AGIZLARI KAREDE OLMAYABILIR: mahalle grafigi goruntu karesinin
        # +150 m disina tasar, agizlar cogu zaman orada kalir. Cizilmeyen sey
        # gostergede "var" gibi yazilmaz (kural 1).
        (R_ROTA, "daire",
         (f"Mahalle giriş ağzı — {len(ekip)} ekip" if ekip_icerde == len(ekip)
          else f"Mahalle giriş ağzı — {len(ekip)} ekip; {len(ekip)-ekip_icerde}'i "
               f"kare dışında (grafik mahallenin +150 m dışına taşar)"
          if ekip_icerde else
          f"Mahalle giriş ağzı — {len(ekip)} ekip, HEPSİ KARE DIŞINDA "
          f"(grafik mahallenin +150 m dışına taşar); güzergâhlar oradan giriyor")),
        (R_HASAR, "kare", f"Afetzede — senaryo ({len(kurban)})"),
    ], baslik=(f"{alan['il']} / {alan['yer']} · {alan['saglayici']} · {alan['tarih']} · "
               f"model {model_adi} · kapsama %{kapsama['edgesObservedFraction']*100:.0f} · "
               f"GERÇEK: görüntü, fotoğraflar, bütün model çıktıları — "
               f"ÜRETİLEN: ihbar metinleri ve kamera/metin konumları. "
               f"Fotoğraflar aynı depremlerden (dokuzu Hatay/Antakya, dördünün ili belirtilmemiş); "
               f"bu mahallenin fotoğrafı DEĞİLDİR."))

    ad = alan["parca"].split()[0].lower().replace("ı", "i")
    hedef = CIK / f"sekil_uc_kanal_{ad}.png"
    CIK.mkdir(parents=True, exist_ok=True)
    tv.save(hedef)
    print(f"  {alan['il']} / {alan['yer']}")
    print(f"    kapali {len(kapali)} · ekip {len(ekip)} (karede {ekip_icerde}) · "
          f"afetzede {len(kurban)} · rota cizilen {rota_sayisi} · "
          f"kamera {len(kam['kayitlar'])} ({catlak} çatlak, {bina} bina) · "
          f"metin {len(met['kayitlar'])}")
    print(f"    -> {hedef.name}  ({hedef.stat().st_size//1024} KB)")
    return hedef


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alan", default="Defne")
    ap.add_argument("--model", default="unet_mitb4_p2_t42")
    ap.add_argument("--tohum", type=int, default=42)
    ap.add_argument("--hepsi", action="store_true",
                    help="Defne, Islahiye ve Nurdagi icin uretir")
    a = ap.parse_args()
    alanlar = ["Defne", "Islahiye", "Nurdagi"] if a.hepsi else [a.alan]
    for ad in alanlar:
        try:
            tek_alan(ad, a.model, a.tohum)
        except Exception as e:
            print(f"  {ad}: HATA {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
