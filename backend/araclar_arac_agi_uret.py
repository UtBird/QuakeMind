"""Arac yol agi uretimi (J-55): ekibin olaya yoldan uzakligi ve tahmini suresi.

Sevk ekraninda ekibin olaya uzakligi kus ucusuydu (J-54). Kullanici: "normal
yolda, normal trafigin aktigi sekilde yoldan yapamaz misin". Yurume agi
(J-44) araca uymaz: tek yonu bilmez, yaya yollarini icerir. Bu arac bes bolge
icin arac agini yerel OSM kopyasindan bir kez uretir; sunucu dosyayi bir kez
bellege alir (kural 3: ag istek yolunda kurulmaz).

Grafin kurulusu:
  * Motorlu aracin girdigi yol turleri asagida. Yaya yolu, patika, merdiven,
    bisiklet yolu ve toprak yol (track) yok.
  * Erisim: en ozel etiket gecerlidir (motorcar > motor_vehicle > vehicle >
    access). `no` ve `private` olan yol atilir.
  * Tek yon: `oneway=yes/1/true` ileri, `-1/reverse` geri; kavsak halkasi
    (`junction=roundabout/circular`) ve otoyol, etiket yoksa ileri. Acil
    arac da tek yone uyar varsayilir ("normal trafigin aktigi sekilde").
  * Hiz: dosyaya yolun turu ve varsa yasal siniri (`maxspeed`) yazilir. Yol
    turune gore ortalama hiz varsayimi sunucudadir (`arac_rotasi.HIZ_KMS`):
    varsayim degisince ag yeniden uretilmez. Anlik trafik verisi YOK.
  * En buyuk GUCLU bagli parca tutulur: tek yon yuzunden girilip cikilamayan
    parcadaki dugumden rota bulunamazdi.

Okuma bolge bolgedir: OSM surucusu her okumada butun Turkiye dosyasini gezer
(~45 sn), ama bes bolgeyi kapsayan tek kutu (~57.000 km^2) bellege fazla gelir.

Cikti: veri/yol_agi/arac/<bolge>.npz ve veri/yol_agi/arac/katalog.json.

Bolgeler arasi ag (`--genel`): sehir aglari ayri ayri yalniz sehrin 12 km
cevresini kapsar; Antakya'daki ekip Kahramanmaras'taki olaya rota bulamiyor,
ekran kus ucusuna dusuyordu (J-55 ek). Genel ag, bes sehir agini (dosyadan) ve
sehirleri baglayan ana yollari (otoyol, devlet ve il yolu; OSM'den tek okuma)
kavsaklarindan birlestirir. Her kenar sehir ici mi disi mi isaretlenir: hiz
varsayimi sehir disinda baskadir (`arac_rotasi`).

    python araclar_arac_agi_uret.py                 # butun bolgeler
    python araclar_arac_agi_uret.py antakya maras   # yalniz bunlar
    python araclar_arac_agi_uret.py --genel         # bolgeler arasi ag (once bolgeler)
"""
import datetime
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent
CIKTI = BACKEND / "veri" / "yol_agi" / "arac"

# Motorlu aracin girdigi yol turleri (OSM `highway`).
ARAC_YOLU = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified", "road",
    "residential", "living_street", "service",
}

# Turkiye'nin yasal sinir kisaltmalari (OSM `maxspeed=TR:...`).
TR_SINIR = {"tr:urban": 50, "tr:rural": 90, "tr:trunk": 110, "tr:motorway": 120, "tr:living_street": 20}


def arac_girer_mi(tip, other_tags, etiket):
    if tip not in ARAC_YOLU:
        return False
    for anahtar in ("motorcar", "motor_vehicle", "vehicle", "access"):
        deger = etiket(other_tags, anahtar)
        if deger:
            return deger not in ("no", "private")
    return True


def yon(tip, other_tags, etiket):
    """'iki' | 'ileri' | 'geri'"""
    tek = (etiket(other_tags, "oneway") or "").lower()
    if tek in ("yes", "true", "1"):
        return "ileri"
    if tek in ("-1", "reverse"):
        return "geri"
    if tek == "no":
        return "iki"
    if (etiket(other_tags, "junction") or "").lower() in ("roundabout", "circular"):
        return "ileri"
    if tip in ("motorway", "motorway_link"):
        return "ileri"
    return "iki"


def yasal_sinir(other_tags, etiket):
    """`maxspeed` (km/sa); yazilmamis ya da okunamiyorsa NaN."""
    ham = (etiket(other_tags, "maxspeed") or "").strip().lower()
    if ham in TR_SINIR:
        return float(TR_SINIR[ham])
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(mph)?$", ham)
    if not m or float(m.group(1)) <= 0:
        return float("nan")
    return float(m.group(1)) * (1.609 if m.group(2) else 1.0)


def ag_uret(df):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    from araclar_altlik_uret import _etiket
    from araclar_yol_agi_uret import HASSASIYET, cizgiler

    t0 = time.perf_counter()
    secili = [arac_girer_mi(t, o, _etiket) for t, o in zip(df["highway"], df["other_tags"])]
    df = df[secili].reset_index(drop=True)
    yonler = [yon(t, o, _etiket) for t, o in zip(df["highway"], df["other_tags"])]
    sinirlar = np.array([yasal_sinir(o, _etiket) for o in df["other_tags"]], dtype=np.float64)

    anahtar = {}
    lon, lat = [], []
    a_list, c_list, yol_list = [], [], []
    for yol_no, geom in enumerate(df.geometry.values):
        y = yonler[yol_no]
        for dizi in cizgiler(geom):
            onceki = None
            for x, yy in dizi:
                k = (round(x * HASSASIYET), round(yy * HASSASIYET))
                n = anahtar.get(k)
                if n is None:
                    n = len(lon)
                    anahtar[k] = n
                    lon.append(x)
                    lat.append(yy)
                if onceki is not None and onceki != n:
                    if y != "geri":
                        a_list.append(onceki)
                        c_list.append(n)
                        yol_list.append(yol_no)
                    if y != "ileri":
                        a_list.append(n)
                        c_list.append(onceki)
                        yol_list.append(yol_no)
                onceki = n
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    a = np.asarray(a_list, dtype=np.int64)
    c = np.asarray(c_list, dtype=np.int64)
    yol = np.asarray(yol_list, dtype=np.int64)

    r = math.pi / 180.0
    dlat = (lat[c] - lat[a]) * r
    dlon = (lon[c] - lon[a]) * r
    h = np.sin(dlat / 2) ** 2 + np.cos(lat[a] * r) * np.cos(lat[c] * r) * np.sin(dlon / 2) ** 2
    uzunluk = 2 * 6_371_000.0 * np.arcsin(np.sqrt(h))

    # Ayni yonlu mukerrer kenar (ust uste binen yollar): en kisasi.
    sira = np.lexsort((uzunluk, c, a))
    a, c, uzunluk, yol = a[sira], c[sira], uzunluk[sira], yol[sira]
    ilk = np.ones(len(a), dtype=bool)
    ilk[1:] = (a[1:] != a[:-1]) | (c[1:] != c[:-1])
    a, c, uzunluk, yol = a[ilk], c[ilk], uzunluk[ilk], yol[ilk]

    # En buyuk guclu bagli parca: her dugumden her dugume yol var.
    N = len(lon)
    komsuluk = coo_matrix((np.ones(len(a)), (a, c)), shape=(N, N)).tocsr()
    parca_sayisi, etiket = connected_components(komsuluk, directed=True, connection="strong")
    buyuk = np.bincount(etiket).argmax()
    tut = etiket == buyuk
    yeni_no = np.full(N, -1, dtype=np.int64)
    yeni_no[tut] = np.arange(int(tut.sum()))
    kenar_tut = tut[a] & tut[c]
    a, c = yeni_no[a[kenar_tut]], yeni_no[c[kenar_tut]]
    uzunluk, yol = uzunluk[kenar_tut], yol[kenar_tut]
    lon, lat = lon[tut], lat[tut]
    N = len(lon)

    # CSR sirasi: kenarlar (a, c) sirasina dizilir; CSR girdisi j = kenar j.
    sira = np.lexsort((c, a))
    a, c, uzunluk, yol = a[sira], c[sira], uzunluk[sira], yol[sira]
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(np.bincount(a, minlength=N), out=indptr[1:])

    kullanilan = np.unique(yol)
    yol_yeni = np.full(len(df), -1, dtype=np.int64)
    yol_yeni[kullanilan] = np.arange(len(kullanilan))
    adlar = [str(x) if isinstance(x, str) else "" for x in df["name"].values[kullanilan]]
    tipler = [str(x) for x in df["highway"].values[kullanilan]]
    tek_yonlu = sum(1 for i in kullanilan if yonler[i] != "iki")
    t1 = time.perf_counter()

    return {
        "dugum_lon": lon, "dugum_lat": lat,
        "indptr": indptr.astype(np.int32), "indices": c.astype(np.int32),
        "kenar": np.arange(len(a), dtype=np.int32),
        "kenar_u": a.astype(np.int32), "kenar_v": c.astype(np.int32),
        "kenar_uzunluk": uzunluk.astype(np.float32),
        "kenar_yol": yol_yeni[yol].astype(np.int32),
        "yol_adi": np.array(adlar, dtype=str), "yol_tipi": np.array(tipler, dtype=str),
        "yol_sinir": sinirlar[kullanilan].astype(np.float32),
    }, {
        "sayilar": {"yol": int(len(kullanilan)), "tekYonluYol": int(tek_yonlu), "dugum": int(N),
                    "yonluKenar": int(len(a)), "gucluParca": int(parca_sayisi),
                    "enBuyukParcaOrani": round(float(tut.mean()), 4),
                    "toplamKm": round(float(uzunluk.sum()) / 1000, 1)},
        "kurulumSn": round(t1 - t0, 1),
    }


# Sehirleri baglayan yollar. Il yolundan (secondary) kucuk yollar genel aga
# yalniz sehir aglarinin icinden girer.
ANA_YOL = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link",
}
GENEL_PAY = 0.15  # derece; sehirleri baglayan yol sehir kutularinin disindan gecer


def genel_uret(pbf, kaynak):
    import pyogrio
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    from araclar_altlik_uret import BOLGELER, _etiket
    from araclar_yol_agi_uret import HASSASIYET, cizgiler, kutu_of

    kutular = [kutu_of(b) for b in BOLGELER]
    genel = (min(k[0] for k in kutular) - GENEL_PAY, min(k[1] for k in kutular) - GENEL_PAY,
             max(k[2] for k in kutular) + GENEL_PAY, max(k[3] for k in kutular) + GENEL_PAY)
    anahtar = {}
    lon, lat = [], []
    yollar = []  # (ad, tip, sinir)
    a_parca, c_parca, y_parca = [], [], []

    def dugum(kx, ky, x, y):
        n = anahtar.get((kx, ky))
        if n is None:
            n = len(lon)
            anahtar[(kx, ky)] = n
            lon.append(x)
            lat.append(y)
        return n

    # 1) Sehir aglari: dosyadan, oldugu gibi (tek yon ve erisim zaten uygulandi).
    t0 = time.perf_counter()
    for b in BOLGELER:
        z = np.load(CIKTI / f"{b['id']}.npz")
        xs, ys = z["dugum_lon"], z["dugum_lat"]
        kx = np.round(xs * HASSASIYET).astype(np.int64).tolist()
        ky = np.round(ys * HASSASIYET).astype(np.int64).tolist()
        gid = np.array([dugum(i, j, x, y) for i, j, x, y in zip(kx, ky, xs.tolist(), ys.tolist())],
                       dtype=np.int64)
        ofset = len(yollar)
        yollar.extend(zip(z["yol_adi"].tolist(), z["yol_tipi"].tolist(), z["yol_sinir"].tolist()))
        a_parca.append(gid[z["kenar_u"]])
        c_parca.append(gid[z["kenar_v"]])
        y_parca.append(z["kenar_yol"].astype(np.int64) + ofset)
    t1 = time.perf_counter()

    # 2) Ana yollar: bes sehri kapsayan kutu, tek okuma.
    turler = ",".join(f"'{t}'" for t in sorted(ANA_YOL))
    df = pyogrio.read_dataframe(pbf, layer="lines", bbox=genel, columns=["highway", "name", "other_tags"],
                                where=f"highway IN ({turler})")
    t2 = time.perf_counter()
    secili = [arac_girer_mi(t, o, _etiket) for t, o in zip(df["highway"], df["other_tags"])]
    df = df[secili].reset_index(drop=True)
    a_list, c_list, y_list = [], [], []
    for geom, tip, tags, ad in zip(df.geometry.values, df["highway"], df["other_tags"], df["name"]):
        yol_no = len(yollar)
        yollar.append((ad if isinstance(ad, str) else "", str(tip), yasal_sinir(tags, _etiket)))
        yn = yon(tip, tags, _etiket)
        for dizi in cizgiler(geom):
            onceki = None
            for x, y in dizi:
                n = dugum(round(x * HASSASIYET), round(y * HASSASIYET), x, y)
                if onceki is not None and onceki != n:
                    if yn != "geri":
                        a_list.append(onceki)
                        c_list.append(n)
                        y_list.append(yol_no)
                    if yn != "ileri":
                        a_list.append(n)
                        c_list.append(onceki)
                        y_list.append(yol_no)
                onceki = n
    a = np.concatenate(a_parca + [np.asarray(a_list, dtype=np.int64)])
    c = np.concatenate(c_parca + [np.asarray(c_list, dtype=np.int64)])
    yol = np.concatenate(y_parca + [np.asarray(y_list, dtype=np.int64)])
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)

    r = math.pi / 180.0
    h = (np.sin((lat[c] - lat[a]) * r / 2) ** 2
         + np.cos(lat[a] * r) * np.cos(lat[c] * r) * np.sin((lon[c] - lon[a]) * r / 2) ** 2)
    uzunluk = 2 * 6_371_000.0 * np.arcsin(np.sqrt(h))

    # Sehir aglarinda da bulunan ana yol kenari iki kez gelir: en kisasi kalir.
    sira = np.lexsort((uzunluk, c, a))
    a, c, uzunluk, yol = a[sira], c[sira], uzunluk[sira], yol[sira]
    ilk = np.ones(len(a), dtype=bool)
    ilk[1:] = (a[1:] != a[:-1]) | (c[1:] != c[:-1])
    a, c, uzunluk, yol = a[ilk], c[ilk], uzunluk[ilk], yol[ilk]

    N = len(lon)
    komsuluk = coo_matrix((np.ones(len(a)), (a, c)), shape=(N, N)).tocsr()
    parca_sayisi, etiket = connected_components(komsuluk, directed=True, connection="strong")
    buyuk = np.bincount(etiket).argmax()
    tut = etiket == buyuk
    yeni_no = np.full(N, -1, dtype=np.int64)
    yeni_no[tut] = np.arange(int(tut.sum()))
    kenar_tut = tut[a] & tut[c]
    a, c = yeni_no[a[kenar_tut]], yeni_no[c[kenar_tut]]
    uzunluk, yol = uzunluk[kenar_tut], yol[kenar_tut]
    lon, lat = lon[tut], lat[tut]
    N = len(lon)

    sira = np.lexsort((c, a))
    a, c, uzunluk, yol = a[sira], c[sira], uzunluk[sira], yol[sira]
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(np.bincount(a, minlength=N), out=indptr[1:])

    # Kenar sehir ici mi: orta noktasi bir sehir kutusunun icinde.
    ox, oy = (lon[a] + lon[c]) / 2, (lat[a] + lat[c]) / 2
    sehir = np.zeros(len(a), dtype=bool)
    for w, s, e, n in kutular:
        sehir |= (ox >= w) & (ox <= e) & (oy >= s) & (oy <= n)

    kullanilan = np.unique(yol)
    yol_yeni = np.full(len(yollar), -1, dtype=np.int64)
    yol_yeni[kullanilan] = np.arange(len(kullanilan))
    adlar = [str(yollar[i][0]) for i in kullanilan]
    tipler = [str(yollar[i][1]) for i in kullanilan]
    sinirlar = np.array([yollar[i][2] for i in kullanilan], dtype=np.float32)
    t3 = time.perf_counter()

    diziler = {
        "dugum_lon": lon, "dugum_lat": lat,
        "indptr": indptr.astype(np.int32), "indices": c.astype(np.int32),
        "kenar": np.arange(len(a), dtype=np.int32),
        "kenar_u": a.astype(np.int32), "kenar_v": c.astype(np.int32),
        "kenar_uzunluk": uzunluk.astype(np.float32),
        "kenar_yol": yol_yeni[yol].astype(np.int32),
        "kenar_sehir": sehir.astype(np.uint8),
        "yol_adi": np.array(adlar, dtype=str), "yol_tipi": np.array(tipler, dtype=str),
        "yol_sinir": sinirlar,
    }
    cikti = CIKTI / "genel.npz"
    np.savez_compressed(cikti, **diziler)
    bilgi = {
        "id": "genel", "ad": "Bölgeler arası (beş şehir ve aralarındaki ana yollar)",
        "kutu": [round(x, 5) for x in genel],
        "sayilar": {"dugum": int(N), "yonluKenar": int(len(a)), "anaYol": int(len(df)),
                    "gucluParca": int(parca_sayisi), "enBuyukParcaOrani": round(float(tut.mean()), 4),
                    "sehirDisiKm": round(float(uzunluk[~sehir].sum()) / 1000, 1),
                    "toplamKm": round(float(uzunluk.sum()) / 1000, 1)},
        "sure": {"sehirAglari": round(t1 - t0, 1), "okuma": round(t2 - t1, 1), "kurulum": round(t3 - t2, 1)},
        "boyutBayt": cikti.stat().st_size, "kaynak": kaynak,
        "uretim": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    (CIKTI / "genel.json").write_text(json.dumps(bilgi, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"genel: {bilgi['sayilar']} | {cikti.stat().st_size / 1e6:.2f} MB | {bilgi['sure']}", flush=True)


def main(secilen):
    sys.path.insert(0, str(BACKEND))
    import pyogrio

    from apps.road_damage.utils.network import LOCAL_PBF_PATH
    from araclar_altlik_uret import BOLGELER
    from araclar_yol_agi_uret import kutu_of

    os.environ.setdefault("OSM_MAX_TMPFILE_SIZE", "3000")
    pbf = Path(LOCAL_PBF_PATH)
    if not pbf.exists():
        print(f"OSM kopyasi yok: {pbf} (QUAKEMIND_LOCAL_OSM_PBF)")
        return 1
    kaynak = {
        "ad": "OpenStreetMap", "atif": "© OpenStreetMap katkıcıları", "lisans": "ODbL 1.0",
        "dosya": pbf.name,
        "dosyaTarihi": datetime.date.fromtimestamp(pbf.stat().st_mtime).isoformat(),
    }
    CIKTI.mkdir(parents=True, exist_ok=True)
    if "--genel" in secilen:
        genel_uret(str(pbf), kaynak)
        return 0
    bolgeler = [b for b in BOLGELER if not secilen or b["id"] in secilen]
    tur_listesi = ",".join(f"'{t}'" for t in sorted(ARAC_YOLU))

    katalog_yolu = CIKTI / "katalog.json"
    katalog = {k["id"]: k for k in (json.loads(katalog_yolu.read_text(encoding="utf-8"))
                                    if katalog_yolu.exists() else [])}
    for b in bolgeler:
        kutu = kutu_of(b)
        t0 = time.perf_counter()
        df = pyogrio.read_dataframe(
            str(pbf), layer="lines", bbox=kutu, columns=["highway", "name", "other_tags"],
            where=f"highway IN ({tur_listesi})")
        okuma = round(time.perf_counter() - t0, 1)
        diziler, bilgi = ag_uret(df)
        yol = CIKTI / f"{b['id']}.npz"
        np.savez_compressed(yol, **diziler)
        katalog[b["id"]] = {
            "id": b["id"], "ad": b["ad"], "kutu": [round(x, 5) for x in kutu],
            **bilgi, "okumaSn": okuma, "boyutBayt": yol.stat().st_size, "kaynak": kaynak,
            "uretim": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        katalog_yolu.write_text(json.dumps(list(katalog.values()), ensure_ascii=False, indent=1),
                                encoding="utf-8")
        print(f"{b['id']}: {bilgi['sayilar']} | {yol.stat().st_size / 1e6:.2f} MB | "
              f"okuma {okuma} + kurulum {bilgi['kurulumSn']} sn", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
