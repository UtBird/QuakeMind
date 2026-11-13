# -*- coding: utf-8 -*-
"""Makale icin HARITA sekilleri: tatbikat goruntusu ve oncesi/sonrasi/etiketli.

Hicbir sey uydurulmaz: butun katmanlar o alanin gercek kosusundan gelir.
"""
import argparse
import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
CIK = Path(__file__).resolve().parent / "benchmark" / "makale_sekilleri"


def _gorsel(r, alan):
    ham = r.get(alan)
    return Image.open(io.BytesIO(base64.b64decode(str(ham).split(",")[-1]))) if ham else None


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


def _gosterge(im, satirlar, baslik=""):
    """Sekle alt gosterge seridi ekler (makalede tek basina okunabilsin).

    Kunye (baslik) satiri sarmalanir: tek satir cizildiginde sagdan kirpiliyordu
    ve Sekil 5 kunyesi kesik bir surumle makaleye konmustu."""
    boy = max(15, im.width // 58)
    sat_h = int(boy * 2.0)
    f_kunye = _yazitipi(int(boy * 0.92))
    kunye = _sar(ImageDraw.Draw(Image.new("RGB", (8, 8))), baslik, f_kunye,
                 im.width - 2 * boy) if baslik else []
    kunye_h = int(boy * 1.35) * max(1, len(kunye))
    yuk = sat_h * ((len(satirlar) + 1) // 2) + kunye_h + int(boy * 1.85)
    y = Image.new("RGB", (im.width, im.height + yuk), (255, 255, 255))
    y.paste(im.convert("RGB"), (0, 0))
    d = ImageDraw.Draw(y)
    f = _yazitipi(boy)
    for i, s in enumerate(kunye):
        d.text((boy, im.height + int(boy * 0.6) + i * int(boy * 1.35)), s, fill=(60, 60, 60), font=f_kunye)
    y0 = im.height + int(boy * 1.05) + kunye_h
    sut = im.width // 2
    for i, (renk, bicim, metin) in enumerate(satirlar):
        cx = boy + (i % 2) * sut
        cy = y0 + (i // 2) * sat_h
        m = boy
        if bicim == "cizgi":
            d.line([(cx, cy + m // 2), (cx + m * 2, cy + m // 2)], fill=renk, width=max(2, boy // 5))
        elif bicim == "cizgi-kalin":
            d.line([(cx, cy + m // 2), (cx + m * 2, cy + m // 2)], fill=renk, width=max(5, boy // 2))
        elif bicim == "alan":
            d.rectangle([cx, cy, cx + m * 2, cy + m], fill=renk + (150,) if len(renk) == 3 else renk)
        elif bicim == "daire":
            d.ellipse([cx + m // 2, cy, cx + m * 3 // 2, cy + m], fill=renk, outline=(255, 255, 255), width=2)
        elif bicim == "kare":
            d.rectangle([cx + m // 2, cy, cx + m * 3 // 2, cy + m], fill=(255, 255, 255), outline=renk, width=3)
        d.text((cx + m * 2 + boy // 2, cy - 1), metin, fill=(20, 20, 20), font=f)
    return y


def _yazitipi(boy):
    """Makale sekli icin okunur yazi; sistemde yoksa varsayilana duser."""
    from PIL import ImageFont
    for ad in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(ad, boy)
        except OSError:
            continue
    return ImageFont.load_default()


def _etiket(im, metin, yuk=None):
    # Etiket goruntuyle ORANTILI: 1280 px'lik kareye 12 px'lik yazi okunmuyordu.
    boy = max(16, im.width // 44)
    yuk = yuk or int(boy * 2.1)
    y = Image.new("RGB", (im.width, im.height + yuk), (255, 255, 255))
    y.paste(im.convert("RGB"), (0, yuk))
    ImageDraw.Draw(y).text((boy // 2, (yuk - boy) // 2 - 2), metin,
                           fill=(20, 20, 20), font=_yazitipi(boy))
    return y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alan", default="Nurdagi")
    ap.add_argument("--model", default="unet_mitb4_p2_t42")
    a = ap.parse_args()

    from apps.road_damage.utils import model_kunyesi, tatbikat
    from apps.road_damage.worker import _init_worker, run_analysis_job

    CIK.mkdir(parents=True, exist_ok=True)
    alan = next(x for x in json.loads(
        (Path(__file__).resolve().parent / "apps/road_damage/data/tatbikat_alanlari.json")
        .read_text(encoding="utf-8")) if a.alan.lower() in x["parca"].lower())
    k = alan["analizBbox"]
    _init_worker(model_kunyesi.kunye_oku(model_kunyesi.etkin_model_adi()))
    r = run_analysis_job({
        "_analysisId": "sekil", "city": alan["il"], "source": "oam",
        "latitude": alan["merkez"]["lat"], "longitude": alan["merkez"]["lon"],
        "bboxWest": k[0], "bboxSouth": k[1], "bboxEast": k[2], "bboxNorth": k[3],
        "oamTileUrl": alan["tmsUrl"] + "/{z}/{x}/{y}.png",
        "oamPreferredTitle": alan["sahneAdi"], "oncesiGoruntusu": True,
        "modelAdi": a.model, "radiusKm": 2.5})
    ham = _gorsel(r, "imageOriginalB64").convert("RGB")
    maske = (np.asarray(_gorsel(r, "imageDamageMaskB64").convert("L")) > 127)
    oncesi = _gorsel(r, "imageOncesiB64")
    s = r["bounds"]; B = (s["west"], s["south"], s["east"], s["north"])
    W, H = ham.size
    gecerli = (np.asarray(ham.convert("L")) > 12).astype(np.uint8)
    G, sg, kapali, _kt, kapsama, _c = tatbikat.mahalle_grafigi(maske.astype(np.uint8), B,
                                                               gecerli_maske=gecerli)
    ekip = tatbikat.giris_noktalari(G, B, sayi=5)
    kurban = tatbikat.afetzedeler(maske.astype(np.uint8), B, sayi=15, tohum=42)
    kurban, _e, ekip = tatbikat.ulasilabilir_afetzedeler(G, ekip, kurban)
    n = min(len(ekip), len(kurban)); ekip, kurban = ekip[:n], kurban[:n]
    rota = tatbikat.rota_kosusu(G, sg, ekip, kurban, hiz_kmh=15.0)

    def pik(lat, lon):
        return ((lon - B[0]) / (B[2] - B[0]) * W, (B[3] - lat) / (B[3] - B[1]) * H)

    # --- Sekil: tatbikat katmanlari ---
    tv = ham.copy()
    arr = np.asarray(tv).copy()
    arr[maske] = (0.42 * arr[maske] + 0.58 * np.array([209, 51, 46])).astype(np.uint8)
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
        # Kapali yol KOYU kirmizi: hasar kutlesinin kirmizisiyla karismasin.
        d.line(p, fill=(150, 20, 18, 255) if kap else (0, 200, 240, 95), width=9 if kap else 2)
    for g in (rota.get("gorevler") or []):
        c = ((g.get("varyantlar") or {}).get("kapanmali") or {}).get("cizgi") or []
        if len(c) >= 2:
            d.line([pik(la, lo) for la, lo in c], fill=(31, 111, 235, 235), width=4)
    # Giris agizlari mahallenin +150 m marjinda; bir kismi goruntu karesinin
    # DISINDA kalir. Karedekiler cizilir, disarda kalanin sayisi kunyeye yazilir.
    ekip_icerde = 0
    for e in ekip:
        x, y = pik(e["lat"], e["lon"])
        if 0 <= x < W and 0 <= y < H:
            ekip_icerde += 1
            d.ellipse([x-11, y-11, x+11, y+11], fill=(31, 111, 235, 255),
                      outline=(255, 255, 255, 255), width=3)
    for kb in kurban:
        x, y = pik(kb["lat"], kb["lon"])
        d.rectangle([x-8, y-8, x+8, y+8], fill=(255, 255, 255, 235), outline=(209, 51, 46, 255), width=3)
    # GOSTERGE. Sekil makalede tek basina okunmali; kapali yol ile hasar
    # kutlesi ayni kirmizidan ayrilsin diye kapali yol KOYU kirmizi ve kalin.
    tv = _gosterge(tv, [
        ((0, 200, 240), "cizgi", "Açık yol (OSM)"),
        ((150, 20, 18), "cizgi-kalin", f"Kapalı yol — modelin bulduğu ({len(kapali)} kenar)"),
        ((209, 51, 46), "alan", "Hasarlı piksel (model çıktısı)"),
        ((31, 111, 235), "cizgi", "Ekip güzergâhı (kapanmalara göre)"),
        ((31, 111, 235), "daire",
         f"Mahalle giriş ağzı — {len(ekip)} ekip"
         + ("" if ekip_icerde == len(ekip) else
            ", hepsi kare dışında" if ekip_icerde == 0 else
            f", {ekip_icerde}'i karede")),
        ((209, 51, 46), "kare", f"Afetzede — senaryo ({len(kurban)})"),
    ], baslik=f"{alan['il']} / {alan['yer']} · {alan['saglayici']} · {alan['tarih']} · "
             f"model {a.model} · kapsama %{kapsama['edgesObservedFraction']*100:.0f}"
             + (f" · giriş ağızları mahallenin +150 m dışında, {len(ekip)-ekip_icerde}'i kare dışında"
                if ekip_icerde < len(ekip) else ""))
    tv.save(CIK / f"sekil_tatbikat_{alan['parca'].split()[0].lower()}.png")

    # --- Sekil: oncesi / sonrasi / etiketli ---
    if oncesi is not None:
        oncesi = oncesi.convert("RGB").resize(ham.size, Image.LANCZOS)
        etiketli = Image.fromarray(arr)
        uc = [(_etiket(oncesi, f"(a) Deprem öncesi — Esri Wayback"), ),
              (_etiket(ham, f"(b) Deprem sonrası — {alan['saglayici']}, {alan['tarih']}"), ),
              (_etiket(etiketli, f"(c) Modelin hasar maskesi — {a.model}"), )]
        im = [x[0] for x in uc]
        t = Image.new("RGB", (sum(i.width for i in im) + 16, im[0].height), (255, 255, 255))
        x = 0
        for i in im:
            t.paste(i, (x, 0)); x += i.width + 8
        t.save(CIK / f"sekil_oncesi_sonrasi_{alan['parca'].split()[0].lower()}.png")

    print(f"alan      : {alan['il']} / {alan['yer']}")
    print(f"TANI      : zoom {r.get('imageryZoom')} (istenen {r.get('imageryRequestedZoom')}) | "
          f"{r.get('imageWidth')}x{r.get('imageHeight')} | gecerli piksel %{(r.get('validPixelRatio') or 0)*100:.0f} | "
          f"hasar kare %{(r.get('damageRate') or 0)*100:.2f} gecerli %{(r.get('damageRateValid') or 0)*100:.2f} | "
          f"sahne {r.get('imageryLabel')}")
    print(f"TANI kutu : {[round(float(x),6) for x in (B)]}")
    print(f"kapsama   : %{kapsama['edgesObservedFraction']*100:.1f}")
    print(f"kapali    : {len(kapali)} kenar | ekip {len(ekip)} | afetzede {len(kurban)}")
    print(f"oncesi    : {'var' if oncesi is not None else 'YOK'}")
    print(f"cikti     : {CIK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
