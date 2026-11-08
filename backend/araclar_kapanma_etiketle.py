# -*- coding: utf-8 -*-
"""Kapanma yer gercegi icin ETIKETLEME KESITLERI uretir (kor).

NEDEN. Tatbikatta dunya modelin kendi ciktisidir; bu yuzden "kapali dedigimiz
yol gercekten kapali miydi" sorusu tatbikatla cevaplanamaz (J-88). EMSR
kullanilmiyor (J-87) cunku tanimi farkli: o yolun KENDISININ bozulmasina
bakiyor, biz yolun MOLOZLA kapanmasina.

YONTEM. Yol parcalari, modelin ne dedigi GORULMEDEN, gercek drone goruntusunun
kesitleri uzerinden elle isaretlenir. Kor olmasi sart: etiketleyici tahmini
bilirse etiket ona dogru kayar.

ORNEKLEME. Modelin KAPALI dedigi parcalarin TAMAMI (kesinlik tam sayilir) +
acik dediklerinden rastgele bir ornek (duyarlilik bu ornekten kestirilir).
Ornekleme orani ciktiya yazilir ki kestirim dogru olcekletilebilsin.

KESIT. Parca, yuzeyi kapatmasin diye ince ve yari saydam cizilir; iki ucuna
dik cizgi konur. Boylece HANGI yol oldugu bellidir ama uzerindeki moloz
gorunur kalir.
"""
import argparse
import io
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _b64(sonuc, alan):
    import base64
    ham = sonuc.get(alan)
    if not ham:
        return None
    return Image.open(io.BytesIO(base64.b64decode(str(ham).split(",")[-1])))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alanlar", default="apps/road_damage/data/tatbikat_alanlari.json")
    ap.add_argument("--alan", default="Defne - Elektrik")
    ap.add_argument("--model", default="unet_mitb4_p2_t42")
    ap.add_argument("--acik-ornek", type=int, default=28, help="acik dediklerinden kac parca")
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--cikti", required=True, help="kesitlerin yazilacagi dizin")
    a = ap.parse_args()

    from apps.road_damage.utils import model_kunyesi, tatbikat
    from apps.road_damage.worker import _init_worker, run_analysis_job

    cikti = Path(a.cikti)
    (cikti / "kesit").mkdir(parents=True, exist_ok=True)

    alan = next(x for x in json.loads(Path(a.alanlar).read_text(encoding="utf-8"))
                if a.alan.lower() in x["parca"].lower())
    k = alan["analizBbox"]
    _init_worker(model_kunyesi.kunye_oku(model_kunyesi.etkin_model_adi()))
    r = run_analysis_job({
        "_analysisId": "etiket", "city": alan["il"], "source": "oam",
        "latitude": alan["merkez"]["lat"], "longitude": alan["merkez"]["lon"],
        "bboxWest": k[0], "bboxSouth": k[1], "bboxEast": k[2], "bboxNorth": k[3],
        "oamTileUrl": alan["tmsUrl"] + "/{z}/{x}/{y}.png",
        "oamPreferredTitle": alan["sahneAdi"],
        "oncesiGoruntusu": False, "modelAdi": a.model, "radiusKm": 2.5})
    ham = _b64(r, "imageOriginalB64").convert("RGB")
    maske = (np.asarray(_b64(r, "imageDamageMaskB64").convert("L")) > 127).astype(np.uint8)
    gecerli = (np.asarray(ham.convert("L")) > 12).astype(np.uint8)
    s = r["bounds"]
    B = (s["west"], s["south"], s["east"], s["north"])
    W, H = ham.size
    G, _sg, kapali, _kt, kapsama, _c = tatbikat.mahalle_grafigi(
        maske, B, gecerli_maske=gecerli)
    kapali_kume = {(u, v, kk) for (u, v, kk) in kapali} | {(v, u, kk) for (u, v, kk) in kapali}

    def pik(lat, lon):
        return ((lon - B[0]) / (B[2] - B[0]) * W, (B[3] - lat) / (B[3] - B[1]) * H)

    # Yalniz GORUNTUNUN DOLU oldugu yerdeki parcalar etiketlenebilir: ucus izi
    # disi siyah, orada hicbir sey gorulmez.
    adaylar = []
    gorulen = set()
    for u, v, kk, dd in G.edges(keys=True, data=True):
        if (v, u, kk) in gorulen:
            continue
        gorulen.add((u, v, kk))
        g = dd.get("geometry")
        koord = ([(la, lo) for lo, la in g.coords] if g is not None
                 else [(G.nodes[u]["y"], G.nodes[u]["x"]), (G.nodes[v]["y"], G.nodes[v]["x"])])
        p = [pik(la, lo) for la, lo in koord]
        if len(p) < 2:
            continue
        ic = [(x, y) for x, y in p if 0 <= x < W and 0 <= y < H]
        if len(ic) < 2:
            continue
        dolu = sum(1 for x, y in ic if gecerli[int(y), int(x)]) / len(ic)
        if dolu < 0.8:
            continue          # parcanin bes'te biri bile bossa yargilanamaz
        adaylar.append({"kenar": (u, v, kk), "nokta": p,
                        "uzunlukM": float(dd.get("length") or 0),
                        "sinif": str(dd.get("highway") or "?"),
                        "modelKapali": (u, v, kk) in kapali_kume})

    kapali_aday = [x for x in adaylar if x["modelKapali"]]
    acik_aday = [x for x in adaylar if not x["modelKapali"]]
    rast = random.Random(a.tohum)
    acik_sec = rast.sample(acik_aday, min(a.acik_ornek, len(acik_aday)))
    secilen = kapali_aday + acik_sec
    rast.shuffle(secilen)      # kor: sira ipucu vermesin

    print(f"alan       : {alan['il']} / {alan['yer']}")
    print(f"goruntu    : {W}x{H} | gecerli piksel %{gecerli.mean()*100:.0f}")
    print(f"graf       : {G.number_of_nodes()} dugum / {G.number_of_edges()} kenar")
    print(f"kapsama    : %{kapsama['edgesObservedFraction']*100:.1f}")
    print(f"etiketlenebilir parca: {len(adaylar)} (model: {len(kapali_aday)} kapali / {len(acik_aday)} acik)")
    print(f"secilen    : {len(secilen)} kesit -> {cikti/'kesit'}")

    anahtar = {}
    for i, x in enumerate(secilen, 1):
        kod = f"P{i:03d}"
        xs = [p[0] for p in x["nokta"]]
        ys = [p[1] for p in x["nokta"]]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        # Dar sokaklarda yuzeyi gorebilmek icin SIKI kirpma: parca cercevesi +
        # az bir pay. Genis kesitte moloz mu golge mi ayirt edilemiyordu.
        yari = max(45, int(max(max(xs) - min(xs), max(ys) - min(ys)) * 0.55) + 26)
        x0, y0 = int(cx - yari), int(cy - yari)
        x1, y1 = int(cx + yari), int(cy + yari)
        kesit = ham.crop((x0, y0, x1, y1))
        olcek = 760 / max(1, kesit.width)
        kesit = kesit.resize((int(kesit.width * olcek), int(kesit.height * olcek)), Image.LANCZOS)
        d = ImageDraw.Draw(kesit, "RGBA")
        yp = [((px - x0) * olcek, (py - y0) * olcek) for px, py in x["nokta"]]
        d.line(yp, fill=(0, 230, 255, 110), width=2)          # ince, yari saydam
        for ux, uy in (yp[0], yp[-1]):                         # uc isaretleri
            d.ellipse([ux - 9, uy - 9, ux + 9, uy + 9], outline=(0, 230, 255, 235), width=3)
        kesit.save(cikti / "kesit" / f"{kod}.jpg", quality=93)
        anahtar[kod] = {"kenar": list(x["kenar"]), "modelKapali": x["modelKapali"],
                        "uzunlukM": round(x["uzunlukM"], 1), "sinif": x["sinif"]}

    (cikti / "ANAHTAR_ACMADAN_ETIKETLE.json").write_text(
        json.dumps({
            "alan": f"{alan['il']} / {alan['yer']}", "sahne": alan["sahneAdi"],
            "tarih": alan["tarih"], "model": a.model, "tohum": a.tohum,
            "toplamAday": len(adaylar), "modelKapaliAday": len(kapali_aday),
            "modelAcikAday": len(acik_aday), "acikOrneklemOrani":
                round(len(acik_sec) / max(1, len(acik_aday)), 4),
            "kesitler": anahtar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"anahtar    : {cikti/'ANAHTAR_ACMADAN_ETIKETLE.json'}  (etiketleme bitmeden ACMA)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
