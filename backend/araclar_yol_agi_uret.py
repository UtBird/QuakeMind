"""Yurume yol agi uretimi (J-44): afetzede rotasi icin yerel OSM kopyasindan.

Afetzede ekrani toplanma alanina ve hastaneye rotayi eskiden kus ucusu cizgi
olarak gosteriyordu; yol tarifi dis servisten (OSRM) geliyordu ve bilinen
kapanmalari bilmiyordu. Bu arac bes bolge icin yurunebilir yol agini bir kez
uretir ve dosyaya yazar. Sunucu dosyayi bir kez bellege alir, rotayi kendi
motorumuzla (Dijkstra, hasar cezali) hesaplar. Istek yolunda calismaz (kural 3).

Grafin kurulusu:
  * GDAL'in OSM surucusu her yolu (way) tam cozunurluklu bir cizgi olarak
    verir. Iki yolun ortak dugumu ayni koordinattadir; koordinatlar 1e-7
    derecede birlestirilerek kavsaklar kurulur (OSM'nin kendi hassasiyeti).
  * Yurunebilir yol turleri asagida; `foot=no`, `access=no/private` (foot
    izni yoksa) atilir. Tek yon yayaya uygulanmaz.
  * En buyuk bagli parca tutulur: kopuk parcadaki (ornegin bir site ici
    yolu) bir dugume oturan konumdan rota bulunamaz.

Cikti: veri/yol_agi/<bolge>.npz (dugumler, CSR komsuluk, kenar uzunlugu,
kenarin yolu) ve veri/yol_agi/katalog.json (kaynak, sayilar, sure).

    python araclar_yol_agi_uret.py                 # butun bolgeler
    python araclar_yol_agi_uret.py antakya maras   # yalniz bunlar
"""
import datetime
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent
CIKTI = BACKEND / "veri" / "yol_agi"
# Altlik +-8 km; rota altligin kenarindan disari tasabilecegi icin ag daha genis.
YARICAP_KM = 12.0
HASSASIYET = 10_000_000  # 1e-7 derece: OSM'nin koordinat hassasiyeti

# Yurunebilir yollar. Otoyol yayaya kapali; insaat ve proje halindeki yollar yok.
YURUNUR = {
    "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
    "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service",
    "road", "pedestrian", "footway", "path", "steps", "track", "cycleway", "bridleway",
    "corridor",
}


def kutu_of(b):
    dlat = YARICAP_KM / 110.574
    dlon = YARICAP_KM / (111.32 * math.cos(math.radians(b["lat"])))
    return (b["lon"] - dlon, b["lat"] - dlat, b["lon"] + dlon, b["lat"] + dlat)


def yurunur_mu(tip, other_tags, etiket):
    if tip not in YURUNUR:
        return False
    foot = etiket(other_tags, "foot")
    if foot == "no":
        return False
    access = etiket(other_tags, "access")
    if access in ("no", "private") and foot not in ("yes", "designated", "permissive"):
        return False
    return True


def cizgiler(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [list(geom.coords)]
    if geom.geom_type == "MultiLineString":
        return [list(g.coords) for g in geom.geoms]
    return []


def ag_uret(b, pbf):
    import pyogrio
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    from araclar_altlik_uret import _etiket

    kutu = kutu_of(b)
    t0 = time.perf_counter()
    df = pyogrio.read_dataframe(
        pbf, layer="lines", bbox=kutu, columns=["highway", "name", "other_tags"],
        where="highway IS NOT NULL")
    t1 = time.perf_counter()

    secili = [yurunur_mu(t, o, _etiket) for t, o in zip(df["highway"], df["other_tags"])]
    df = df[secili].reset_index(drop=True)

    anahtar = {}          # (x, y) tamsayi -> dugum no
    lon, lat = [], []
    a_list, b_list, yol_list = [], [], []
    for yol_no, geom in enumerate(df.geometry.values):
        for dizi in cizgiler(geom):
            onceki = None
            for x, y in dizi:
                k = (round(x * HASSASIYET), round(y * HASSASIYET))
                n = anahtar.get(k)
                if n is None:
                    n = len(lon)
                    anahtar[k] = n
                    lon.append(x)
                    lat.append(y)
                if onceki is not None and onceki != n:
                    a_list.append(onceki)
                    b_list.append(n)
                    yol_list.append(yol_no)
                onceki = n
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    a = np.asarray(a_list, dtype=np.int64)
    c = np.asarray(b_list, dtype=np.int64)
    yol = np.asarray(yol_list, dtype=np.int32)

    # Kenar uzunlugu (haversine, metre).
    r = math.pi / 180.0
    dlat = (lat[c] - lat[a]) * r
    dlon = (lon[c] - lon[a]) * r
    h = np.sin(dlat / 2) ** 2 + np.cos(lat[a] * r) * np.cos(lat[c] * r) * np.sin(dlon / 2) ** 2
    uzunluk = 2 * 6_371_000.0 * np.arcsin(np.sqrt(h))

    # Ayni iki dugum arasindaki mukerrer kenar (ust uste binen yollar): en kisasi.
    u = np.minimum(a, c)
    v = np.maximum(a, c)
    sira = np.lexsort((uzunluk, v, u))
    u, v, uzunluk, yol = u[sira], v[sira], uzunluk[sira], yol[sira]
    ilk = np.ones(len(u), dtype=bool)
    ilk[1:] = (u[1:] != u[:-1]) | (v[1:] != v[:-1])
    u, v, uzunluk, yol = u[ilk], v[ilk], uzunluk[ilk], yol[ilk]

    # En buyuk bagli parca.
    N = len(lon)
    komsuluk = coo_matrix((np.ones(len(u)), (u, v)), shape=(N, N)).tocsr()
    parca_sayisi, etiket = connected_components(komsuluk, directed=False)
    buyuk = np.bincount(etiket).argmax()
    tut = etiket == buyuk
    yeni_no = np.full(N, -1, dtype=np.int64)
    yeni_no[tut] = np.arange(int(tut.sum()))
    kenar_tut = tut[u] & tut[v]
    u, v, uzunluk, yol = yeni_no[u[kenar_tut]], yeni_no[v[kenar_tut]], uzunluk[kenar_tut], yol[kenar_tut]
    lon, lat = lon[tut], lat[tut]
    N = len(lon)
    kenar_sayisi = len(u)

    # Yonsuz ag -> CSR (her kenar iki yonde). `kenar`: CSR girdisinin yonsuz
    # kenar numarasi; hasar carpani iki yone birlikte uygulanir.
    satir = np.concatenate([u, v])
    sutun = np.concatenate([v, u])
    kenar = np.concatenate([np.arange(kenar_sayisi), np.arange(kenar_sayisi)])
    sira = np.lexsort((sutun, satir))
    satir, sutun, kenar = satir[sira], sutun[sira], kenar[sira]
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(np.bincount(satir, minlength=N), out=indptr[1:])

    kullanilan_yol = np.unique(yol)
    yol_yeni = np.full(len(df), -1, dtype=np.int64)
    yol_yeni[kullanilan_yol] = np.arange(len(kullanilan_yol))
    adlar = [str(x) if isinstance(x, str) else "" for x in df["name"].values[kullanilan_yol]]
    tipler = [str(x) for x in df["highway"].values[kullanilan_yol]]
    t2 = time.perf_counter()

    return {
        "dugum_lon": lon, "dugum_lat": lat,
        "indptr": indptr.astype(np.int32), "indices": sutun.astype(np.int32),
        "kenar": kenar.astype(np.int32),
        "kenar_u": u.astype(np.int32), "kenar_v": v.astype(np.int32),
        "kenar_uzunluk": uzunluk.astype(np.float32),
        "kenar_yol": yol_yeni[yol].astype(np.int32),
        "yol_adi": np.array(adlar, dtype=str), "yol_tipi": np.array(tipler, dtype=str),
    }, {
        "kutu": [round(x, 5) for x in kutu],
        "sayilar": {"yol": int(len(kullanilan_yol)), "dugum": int(N), "kenar": int(kenar_sayisi),
                    "parca": int(parca_sayisi), "enBuyukParcaOrani": round(float(tut.mean()), 4),
                    "toplamKm": round(float(uzunluk.sum()) / 1000, 1)},
        "sure": {"okuma": round(t1 - t0, 1), "kurulum": round(t2 - t1, 1)},
    }


def main(secilen):
    sys.path.insert(0, str(BACKEND))
    from apps.road_damage.utils.network import LOCAL_PBF_PATH
    from araclar_altlik_uret import BOLGELER

    os.environ.setdefault("OSM_MAX_TMPFILE_SIZE", "3000")  # dugum indeksi RAM'de (MB)
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
    katalog_yolu = CIKTI / "katalog.json"
    katalog = {k["id"]: k for k in (json.loads(katalog_yolu.read_text(encoding="utf-8"))
                                    if katalog_yolu.exists() else [])}

    for b in BOLGELER:
        if secilen and b["id"] not in secilen:
            continue
        diziler, bilgi = ag_uret(b, str(pbf))
        yol = CIKTI / f"{b['id']}.npz"
        np.savez_compressed(yol, **diziler)
        katalog[b["id"]] = {"id": b["id"], "ad": b["ad"], **bilgi, "boyutBayt": yol.stat().st_size,
                            "kaynak": kaynak,
                            "uretim": datetime.datetime.now().isoformat(timespec="seconds")}
        katalog_yolu.write_text(json.dumps(list(katalog.values()), ensure_ascii=False, indent=1),
                                encoding="utf-8")
        print(f"{b['id']}: {bilgi['sayilar']} | {yol.stat().st_size / 1e6:.2f} MB | "
              f"okuma {bilgi['sure']['okuma']} + kurulum {bilgi['sure']['kurulum']} sn", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
