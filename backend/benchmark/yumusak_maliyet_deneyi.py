"""Surekli yumusak maliyet: A* planlamasinda modelin kapanma OLASILIGI.

J-30 (Tablo 18) modelin IKILI kapanmalarini sert (kenar silinir) ve kaba
yumusak (x3, x10) kullanmis, hicbir ayarda tutarli kazanc bulmamisti. Iki
yontemsel fark burada sinanir:

  1. Olasilik: kenar, hasarli piksel gordugu anda kapanmaz; kenar boyunca
     orneklerin hasarli ORANI p(e) kullanilir.
  2. Simetri: yer gercegi bir kenari orneklerinin %50'si hasarli cizgiye
     yakinsa kapali sayar; bugunku model kurali TEK hasarli piksel yeter
     diyor. Simetrik kural ayni esigi (p >= 0,5) modele de uygular.

ON KAYIT -- protokol veriye bakmadan once sabitlendi (21 Eylul 2026):

  Dunya     EMSR648 gevsek kural, tampon 8 m, min ortusme 0,5 (J-30 ile ayni)
  Ajanlar   hepsi dunyada yurur, kapali kenara girmez, kavsakta ogrenir,
            kesif basina t_u oder (Algoritma 1, simulate_reference_fleet):
              R0        bilgisiz
              R3        kusursuz bilgi (EMSR)
              M-sert    bugunku kural: p > 0 ise kapali (canli sistem, r_h = 0)
              M-simetrik  p >= 0,5 ise kapali (yer gercegiyle ayni esik)
              M-y<λ>    yumusak: planlama maliyeti = uzunluk x (1 + λ p),
                        λ ∈ {0,5, 1, 2, 4, 8, 16}; kenar gizlenmez
  λ secimi  Bir ilde (AYAR) ortalama gorev suresini en aza indiren λ secilir,
            obur ilde (SINAMA) YALNIZ o λ raporlanir. Iki yon da raporlanir.
            Tum λ egrisi seffaflik icin yazilir; iddia yalniz sinama degerine
            dayanir (en iyi ayari secip raporlamak J-30'da uyarilan coklu
            karsilastirma hatasi olurdu).
  Gorevler  Her hucrede her tohumda 3 gorev, tohum 42..51.
            ekip: hucre sinirina 150 m icindeki rastgele dugum (disaridan gelir)
            afetzede: hasarli EMSR yol cizgisine 60 m icindeki rastgele dugum
            kosul: kusursuz bilgiyle (R3) ulasilabilir; degilse yeniden cekilir
  t_u       20 dk (J-30 ile ayni); 5 dk duyarlilik olarak ayrica
  Olcutler  ortalama gorev suresi (dk), R0->R3 kazancinin yakalanan payi,
            kesif sayisi, "rota bulunamadi" (sert kurallar), kesim duzeyinde
            kesinlik / duyarlilik / IoU.

Maskeler: benchmark/data/model_masks_emsr/<hucre>/ (make_model_masks.py,
z18, OpenAerialMap Maxar deprem sonrasi). Hucreler: emsr_hucreleri.py.

    python benchmark/yumusak_maliyet_deneyi.py
"""
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

BENCH = Path(__file__).resolve().parent
BACKEND = BENCH.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BENCH))

from apps.road_damage.utils.network import (  # noqa: E402
    build_local_graph_from_pbf, closures_from_lines, edge_closure_probability, haversine,
    simulate_reference_fleet,
)
from benchmark.copernicus_ground_truth import aoi_rings, damaged_road_lines  # noqa: E402
from naive_baseline import AVERAGE_SPEED_KMH  # noqa: E402

VERI = BENCH / "data"
MASKE_KOK = VERI / "model_masks_emsr"
HUCRELER = VERI / "emsr_hucreleri.json"
CIKTI = BENCH / "runs" / "yumusak_maliyet"

TOHUMLAR = list(range(42, 52))
GOREV_SAYISI = 3
LAMBDALAR = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
SIMETRIK_ESIK = 0.5
T_U = 20.0
T_U_DUYARLILIK = 5.0
EMSR_KURAL = "loose"
EMSR_TAMPON_M = 8.0
EKIP_SINIR_M = 150.0
AFETZEDE_HASAR_M = 60.0


def maske_oku(hucre_id):
    d = MASKE_KOK / hucre_id
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    hasar = (np.array(Image.open(d / "damage_mask.png").convert("L")) > 0).astype(np.uint8)
    gecerli = (np.array(Image.open(d / "valid_mask.png").convert("L")) > 0).astype(np.uint8)
    return meta, hasar, gecerli


def fiziksel(anahtarlar):
    return {(min(u, v), max(u, v), k) for (u, v, k) in anahtarlar}


def iki_yon(anahtarlar):
    out = set()
    for (u, v, k) in anahtarlar:
        out.add((u, v, k))
        out.add((v, u, k))
    return out


def karmasiklik(model, dunya, tum):
    m, e, n = fiziksel(model), fiziksel(dunya), fiziksel(tum)
    tp, fp, fn = len(m & e), len(m - e), len(e - m)
    return {"kesim": len(n), "modelKapali": len(m), "dunyaKapali": len(e), "tp": tp, "fp": fp, "fn": fn}


def oranlar(c):
    tp, fp, fn = c["tp"], c["fp"], c["fn"]
    return {
        "kesinlik": tp / (tp + fp) if tp + fp else None,
        "duyarlilik": tp / (tp + fn) if tp + fn else None,
        "iou": tp / (tp + fp + fn) if tp + fp + fn else None,
    }


def yolculuk_dk(m):
    return m / 1000.0 / AVERAGE_SPEED_KMH * 60.0


# Yol agi YEREL PBF'ten kurulur (D:/quakemind_osm_data/turkey-latest.osm.pbf,
# J-30'daki drone sahneleriyle ayni kaynak). Hucre basina PBF taramasi ~230 sn
# surdugu icin il basina TEK tarama yapilir, hucre graflari ondan kesilir:
# hucre kutusu icindeki dugumlerin olusturdugu alt graf. Canli Overpass
# kullanilmaz (DNS duzeyinde 300 sn+ donabiliyor, sonuc da zamana bagli olurdu).
_IL_GRAFLARI = {}


def il_grafi(il, hucreler):
    if il in _IL_GRAFLARI:
        return _IL_GRAFLARI[il]
    import pickle

    yol = VERI / f"emsr_graf_{il}_walk.pkl"
    if yol.exists():
        with open(yol, "rb") as f:
            G = pickle.load(f)
    else:
        # Kutu, maskesi o an var olanlardan degil TUM hucre listesinden: sonradan
        # biten hucreler de grafin icinde kalsin (maske ureticisiyle ayni kutu).
        from apps.road_damage.utils.assembly import bbox_from_center

        tum = json.loads(HUCRELER.read_text(encoding="utf-8"))
        kutular = [bbox_from_center(h["center"][0], h["center"][1], h["radiusKm"])
                   for h in tum if h["city"] == il]
        pay = 0.003
        kutu = (min(k[0] for k in kutular) - pay, min(k[1] for k in kutular) - pay,
                max(k[2] for k in kutular) + pay, max(k[3] for k in kutular) + pay)
        print(f"  {il}: PBF taraniyor {tuple(round(v, 4) for v in kutu)} (birkac dakika) ...", flush=True)
        G = build_local_graph_from_pbf(kutu, network_type="walk", cache=False)
        with open(yol, "wb") as f:
            pickle.dump(G, f)
    _IL_GRAFLARI[il] = G
    return G


def hucre_grafi(G_il, kutu):
    bati, guney, dogu, kuzey = kutu
    icerde = [n for n, d in G_il.nodes(data=True)
              if bati <= d["x"] <= dogu and guney <= d["y"] <= kuzey]
    return G_il.subgraph(icerde).copy()


def hucre_hazirla(hucre, tum_hucreler):
    meta, hasar, gecerli = maske_oku(hucre["id"])
    zb = meta["zoneBbox"]
    kutu = (zb["west"], zb["south"], zb["east"], zb["north"])
    G = hucre_grafi(il_grafi(hucre["city"], tum_hucreler), kutu)
    if G.number_of_edges() == 0:
        raise RuntimeError(f"{hucre['id']}: hucrede yol yok")

    cizgiler = damaged_road_lines(hucre["emsrPackage"], EMSR_KURAL, kutu)
    _, _, dunya, dstat = closures_from_lines(
        G, cizgiler, buffer_m=EMSR_TAMPON_M, min_overlap=0.5,
        observed_polygons=aoi_rings(hucre["emsrPackage"]))

    mb = meta["bounds"]
    p, gorulmeyen = edge_closure_probability(
        G, (mb["west"], mb["south"], mb["east"], mb["north"]), hasar, gecerli)

    tum = set(G.edges(keys=True))
    sert = {e for e, v in p.items() if v > 0}
    simetrik = {e for e, v in p.items() if v >= SIMETRIK_ESIK}
    return {
        "hucre": hucre, "G": G, "kutu": kutu, "dunya": set(dunya), "dunyaIstat": dstat,
        "p": p, "gorulmeyen": gorulmeyen, "tum": tum, "cizgiler": cizgiler,
        "modeller": {
            "M-sert": {"anahtar": sert, **karmasiklik(sert, dunya, tum)},
            "M-simetrik": {"anahtar": simetrik, **karmasiklik(simetrik, dunya, tum)},
        },
        "sahneler": meta.get("scenes", []),
    }


def gorev_uret(h, tohum):
    """Onceden sabit kural; tohum + hucre kimligi ile belirlenimci."""
    G, (bati, guney, dogu, kuzey) = h["G"], h["kutu"]
    rng = random.Random(f"{tohum}-{h['hucre']['id']}")
    dugumler = list(G.nodes(data=True))

    def sinira_m(d):
        y, x = d["y"], d["x"]
        return min(
            haversine(y, x, y, bati), haversine(y, x, y, dogu),
            haversine(y, x, guney, x), haversine(y, x, kuzey, x),
        )

    kenar_adaylari = [n for n, d in dugumler if sinira_m(d) <= EKIP_SINIR_M]
    hasar_noktalari = [(lat, lon) for c in h["cizgiler"] for lon, lat in c]
    afet_adaylari = [
        n for n, d in dugumler
        if any(haversine(d["y"], d["x"], la, lo) <= AFETZEDE_HASAR_M for la, lo in hasar_noktalari[::3])
    ]
    if not kenar_adaylari or not afet_adaylari:
        return []

    dunya = iki_yon(h["dunya"])
    gorevler = []
    deneme = 0
    while len(gorevler) < GOREV_SAYISI and deneme < 50:
        deneme += 1
        s, t = rng.choice(kenar_adaylari), rng.choice(afet_adaylari)
        if s == t:
            continue
        gorev = {"id": f"{h['hucre']['id']}-s{tohum}-{len(gorevler)}",
                 "startLat": G.nodes[s]["y"], "startLon": G.nodes[s]["x"],
                 "endLat": G.nodes[t]["y"], "endLon": G.nodes[t]["x"]}
        # Kosul: kusursuz bilgiyle ulasilabilir.
        r = simulate_reference_fleet(G, dunya, [gorev], speed_kmh=AVERAGE_SPEED_KMH,
                                     prior_closed=h["dunya"])[0]
        if r is not None:
            gorevler.append(gorev)
    return gorevler


def ajan_adlari():
    return ["R0", "R3", "M-sert", "M-simetrik"] + [f"M-y{l:g}" for l in LAMBDALAR]


def ajan_kos(h, ad, gorevler):
    G, dunya = h["G"], iki_yon(h["dunya"])
    ortak = {"speed_kmh": AVERAGE_SPEED_KMH}
    if ad == "R0":
        return simulate_reference_fleet(G, dunya, gorevler, **ortak)
    if ad == "R3":
        return simulate_reference_fleet(G, dunya, gorevler, prior_closed=h["dunya"], **ortak)
    if ad in ("M-sert", "M-simetrik"):
        return simulate_reference_fleet(G, dunya, gorevler, prior_closed=h["modeller"][ad]["anahtar"], **ortak)
    lam = float(ad[len("M-y"):])
    carpan = {e: 1.0 + lam * v for e, v in h["p"].items() if v > 0}
    return simulate_reference_fleet(G, dunya, gorevler, prior_multiplier=carpan, **ortak)


def kos(yalniz=None, tohumlar=None):
    t0 = time.perf_counter()
    tum_hucreler = json.loads(HUCRELER.read_text(encoding="utf-8"))
    tum_hucreler = [h for h in tum_hucreler if (MASKE_KOK / h["id"] / "meta.json").exists()]
    hucreler = [h for h in tum_hucreler if not yalniz or h["id"] in yalniz]
    tohumlar = tohumlar or TOHUMLAR
    hazir = {}
    for hucre in hucreler:
        if not (MASKE_KOK / hucre["id"] / "meta.json").exists():
            continue
        try:
            print(f"hazirlaniyor {hucre['id']} ...", flush=True)
            hazir[hucre["id"]] = hucre_hazirla(hucre, tum_hucreler)
            h = hazir[hucre["id"]]
            print(f"hazir {hucre['id']}: {len(h['tum'])} kenar, dunyada kapali {len(h['dunya'])}, "
                  f"M-sert {len(h['modeller']['M-sert']['anahtar'])}, M-simetrik {len(h['modeller']['M-simetrik']['anahtar'])} "
                  f"({time.perf_counter() - t0:.0f} sn)", flush=True)
        except Exception as e:
            print(f"ATLANDI {hucre['id']}: {e}", flush=True)

    satirlar = []
    for tohum in tohumlar:
        for hid, h in hazir.items():
            gorevler = gorev_uret(h, tohum)
            if not gorevler:
                continue
            for ad in ajan_adlari():
                sonuc = ajan_kos(h, ad, gorevler)
                for g, r in zip(gorevler, sonuc):
                    satirlar.append({
                        "tohum": tohum, "hucre": hid, "il": h["hucre"]["city"], "ajan": ad, "gorev": g["id"],
                        "ulasti": r is not None,
                        "mesafeM": r["distanceMeters"] if r else None,
                        "kesif": r["discoveries"] if r else None,
                        "geriDondu": bool(r and r.get("fallback")),
                    })
        print(f"tohum {tohum} bitti ({time.perf_counter() - t0:.0f} sn)", flush=True)
    return hazir, satirlar, round(time.perf_counter() - t0, 1)


def ortalama(degerler):
    d = [v for v in degerler if v is not None]
    if not d:
        return None
    m = sum(d) / len(d)
    sd = math.sqrt(sum((v - m) ** 2 for v in d) / (len(d) - 1)) if len(d) > 1 else 0.0
    return {"n": len(d), "ort": m, "ss": sd}


def ozet(hazir, satirlar, t_u):
    iller = sorted({h["hucre"]["city"] for h in hazir.values()})
    sonuc = {}
    for il in iller:
        il_s = [s for s in satirlar if s["il"] == il]
        ajanlar = {}
        for ad in ajan_adlari():
            ss = [s for s in il_s if s["ajan"] == ad]
            sureler = [yolculuk_dk(s["mesafeM"]) + s["kesif"] * t_u for s in ss if s["ulasti"]]
            ajanlar[ad] = {
                "sure": ortalama(sureler),
                "ulasilamayan": sum(1 for s in ss if not s["ulasti"]),
                "geriDonus": sum(1 for s in ss if s["geriDondu"]),
                "kesifOrt": (sum(s["kesif"] or 0 for s in ss if s["ulasti"]) / max(1, sum(1 for s in ss if s["ulasti"]))),
            }
        r0 = ajanlar["R0"]["sure"]["ort"] if ajanlar["R0"]["sure"] else None
        r3 = ajanlar["R3"]["sure"]["ort"] if ajanlar["R3"]["sure"] else None
        for ad, a in ajanlar.items():
            if a["sure"] and r0 is not None and r3 is not None and r0 - r3 > 1e-9:
                a["yakalananPay"] = (r0 - a["sure"]["ort"]) / (r0 - r3)
            else:
                a["yakalananPay"] = None
        # algilama olcutleri (il toplami)
        alg = {}
        for m in ("M-sert", "M-simetrik"):
            top = {"tp": 0, "fp": 0, "fn": 0, "kesim": 0, "modelKapali": 0, "dunyaKapali": 0}
            for h in hazir.values():
                if h["hucre"]["city"] == il:
                    for k in top:
                        top[k] += h["modeller"][m][k]
            alg[m] = {**top, **oranlar(top)}
        sonuc[il] = {"ajanlar": ajanlar, "algilama": alg,
                     "hucre": sum(1 for h in hazir.values() if h["hucre"]["city"] == il),
                     "gorev": len({s["gorev"] for s in il_s})}

    # Bolgeler arasi λ secimi: ayar ilinde en iyi λ, sinama ilinde raporlanir.
    capraz = []
    if len(iller) == 2:
        for ayar, sinama in ((iller[0], iller[1]), (iller[1], iller[0])):
            adaylar = [(f"M-y{l:g}", sonuc[ayar]["ajanlar"][f"M-y{l:g}"]["sure"]) for l in LAMBDALAR]
            adaylar = [(a, s["ort"]) for a, s in adaylar if s]
            if not adaylar:
                continue
            secilen = min(adaylar, key=lambda x: x[1])[0]
            capraz.append({"ayar": ayar, "sinama": sinama, "secilenLambda": secilen,
                           "sinamaPayi": sonuc[sinama]["ajanlar"][secilen]["yakalananPay"],
                           "sinamaSure": sonuc[sinama]["ajanlar"][secilen]["sure"]})
    return {"iller": sonuc, "capraz": capraz, "tU": t_u}


def yaz(hazir, satirlar, sure_sn):
    CIKTI.mkdir(parents=True, exist_ok=True)
    ana = ozet(hazir, satirlar, T_U)
    duy = ozet(hazir, satirlar, T_U_DUYARLILIK)
    hucre_bilgi = [{
        "id": hid, "il": h["hucre"]["city"], "kesim": len(fiziksel(h["tum"])),
        "dunyaKapali": len(fiziksel(h["dunya"])), "gorulmeyenKenar": len(h["gorulmeyen"]),
        "sahneler": [f"{s.get('provider')} {s.get('date')}" for s in h["sahneler"]],
        "M-sert": oranlar(h["modeller"]["M-sert"]), "M-simetrik": oranlar(h["modeller"]["M-simetrik"]),
    } for hid, h in hazir.items()]
    (CIKTI / "summary.json").write_text(json.dumps(
        {"ana": ana, "duyarlilik": duy, "hucreler": hucre_bilgi, "sureSn": sure_sn,
         "protokol": {"lambdalar": LAMBDALAR, "simetrikEsik": SIMETRIK_ESIK, "tU": T_U,
                      "tohumlar": TOHUMLAR, "gorevSayisi": GOREV_SAYISI}},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (CIKTI / "satirlar.json").write_text(json.dumps(satirlar, ensure_ascii=False), encoding="utf-8")
    return ana, duy


def yazdir(ozet_, baslik):
    print(f"\n=== {baslik} (t_u = {ozet_['tU']:g} dk) ===")
    for il, v in ozet_["iller"].items():
        print(f"\n{il}: {v['hucre']} hucre, {v['gorev']} gorev")
        for m, a in v["algilama"].items():
            k, d, i = a["kesinlik"], a["duyarlilik"], a["iou"]
            print(f"  {m:11} kesinlik {k if k is None else round(k,3)}  duyarlilik {d if d is None else round(d,3)}  IoU {i if i is None else round(i,3)}  (model {a['modelKapali']}, dunya {a['dunyaKapali']})")
        for ad, a in v["ajanlar"].items():
            s = a["sure"]
            pay = a["yakalananPay"]
            print(f"  {ad:11} sure {s['ort']:6.2f} ± {s['ss']:5.2f} dk  pay {'—' if pay is None else f'{100*pay:6.1f}%'}"
                  f"  kesif {a['kesifOrt']:.2f}  ulasilamayan {a['ulasilamayan']}  geri donus {a['geriDonus']}" if s else f"  {ad:11} veri yok")
    for c in ozet_["capraz"]:
        pay = c["sinamaPayi"]
        print(f"\n  λ secimi {c['ayar']} -> sinama {c['sinama']}: secilen {c['secilenLambda']}, "
              f"sinamada yakalanan pay {'—' if pay is None else f'{100*pay:.1f}%'}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--hucreler", nargs="*", default=None, help="yalniz bu hucreler (hata ayiklama)")
    ap.add_argument("--tohumlar", nargs="*", type=int, default=None)
    ap.add_argument("--cikti", default=None, help="cikti klasoru (varsayilan runs/yumusak_maliyet)")
    a = ap.parse_args()
    global CIKTI
    if a.cikti:
        CIKTI = Path(a.cikti)
    hazir, satirlar, sure = kos(a.hucreler, a.tohumlar)
    if not hazir:
        print("Maske bulunan hucre yok; once make_model_masks.py kosulmali.")
        return 1
    ana, duy = yaz(hazir, satirlar, sure)
    yazdir(ana, "ANA SONUC")
    yazdir(duy, "DUYARLILIK")
    print(f"\ncikti: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
