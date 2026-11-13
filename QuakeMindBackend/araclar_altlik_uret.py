"""Harita altligi uretimi (J-40): yerel OSM kopyasindan bolge paketleri.

ARAYUZ 11 / MIMARI 8: altlik kendi verimizden cizilir, hazir karo servisine
bagimlilik yok. Bu arac yerel Turkiye PBF'inden (QUAKEMIND_LOCAL_OSM_PBF) her
bolge icin yollari (5 sinif), yapilari, su alanlarini ve nehirleri okur,
sadelestirir, tamsayi-delta kodlar ve veri/altlik/<bolge>.json.gz olarak
yazar. Istek yolunda calismaz (kural 3): bir kez uretilir, sunucu hazir dosyayi
verir (uclar/altlik.py). Kodlama prototipinkiyle ayni fikir: 1e-5 derece
tamsayi, butun dizi boyunca ardisik fark.

    python araclar_altlik_uret.py                 # butun bolgeler
    python araclar_altlik_uret.py antakya maras   # yalniz bunlar
    python araclar_altlik_uret.py --hizmetler     # hastane, eczane vb. (J-50)
    python araclar_altlik_uret.py --iller         # 81 il merkezinin sehir altligi

Iki tur bolge vardir. `operasyon`: asagidaki bes bolge; hizmet noktalari, yol
aglari ve afetzede mahalle listesi yalniz bunlar icin uretilir. `il`: risk
ekraninin 81 il secicisi icin il merkezlerinin altligi (il merkezleri
araclar_il_merkezleri_uret.py'den). Merkezi bir operasyon bolgesinin icinde
kalan il atlanir. `--iller` uretilmis paketi yeniden uretmez; yarida kalirsa
ayni komut kaldigi yerden devam eder. Il altliginin yaricapi nufusa gore
10 / 15 / 20 km (IL_YARICAPI); yaricap degisirse paket yeniden uretilir.
Iller alan butcesine gore gruplanir: OSM dosyasi grup basina bir kez gezilir.

Olculdu (21 Eylul 2026, Antakya +-8 km, GDAL 3.11 OSM surucusu): yollar
36,9 sn (10 298 nesne), yapilar ve su 92 sn (59 476 nesne). Bolge basina ~2 dk.
"""
import datetime
import gzip
import json
import math
import os
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
CIKTI = BACKEND / "veri" / "altlik"
OLCEK = 100000  # 1e-5 derece ~ 1,1 m
YARICAP_KM = 8.0

# Konsoldaki bolge listesiyle ayni kimlikler (konsol/src/veri/analiz.ts BOLGELER).
BOLGELER = [
    {"id": "antakya", "ad": "Antakya (Hatay)", "lat": 36.202, "lon": 36.161},
    {"id": "maras", "ad": "Kahramanmaraş", "lat": 37.57, "lon": 36.93},
    {"id": "antep", "ad": "Gaziantep", "lat": 37.06, "lon": 37.38},
    {"id": "malatya", "ad": "Malatya", "lat": 38.35, "lon": 38.3},
    {"id": "adiyaman", "ad": "Adıyaman", "lat": 37.76, "lon": 38.27},
]

IL_MERKEZLERI = BACKEND / "veri" / "il_merkezleri.json"
# Il altliginin yaricapi il nufusuna gore (OSM `population`; buyuksehirde ilin
# tamami). 8 km'lik kare Konya gibi sehirleri kenardan kesiyordu (20 Ekim).
IL_YARICAPI = ((300_000, 10.0), (1_000_000, 15.0), (float("inf"), 20.0))
# Tek gecisle okunan grubun alan butcesi, 8 km'lik bolge cinsinden. 12 x 8 km
# 7,6 GB RAM makinede bellegi bitirdi (19 Ekim); 6 x 8 km sorunsuz gecti.
GRUP_ALANI = 6.5
TR_ASCII = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")


def il_bolgeleri():
    """81 il merkezinden `il` turu bolgeler; kimlik ASCII (uc yalniz harf ve
    rakam kabul eder): Kırklareli -> kirklareli."""
    if not IL_MERKEZLERI.exists():
        print(f"Il merkezleri yok: {IL_MERKEZLERI} (python araclar_il_merkezleri_uret.py)")
        return []
    operasyon = [kutu_of(b) for b in BOLGELER]
    bolgeler = []
    for il in json.loads(IL_MERKEZLERI.read_text(encoding="utf-8"))["iller"]:
        if any(k[0] <= il["lon"] <= k[2] and k[1] <= il["lat"] <= k[3] for k in operasyon):
            continue
        kimlik = "".join(c for c in il["il"].translate(TR_ASCII).lower() if c.isalnum())
        nufus = il.get("nufus")
        yaricap = next(r for ust, r in IL_YARICAPI if nufus < ust) if nufus else 15.0
        bolgeler.append({"id": kimlik, "ad": il["il"], "lat": il["lat"], "lon": il["lon"], "tur": "il",
                         "yaricapKm": yaricap, "nufus": nufus})
    return bolgeler


# Yol hiyerarsisi (ARAYUZ 3 / 11): 0 otoyol ... 4 patika. Listede olmayan
# (construction, proposed, raceway...) cizilmez.
YOL_SINIFI = {
    **dict.fromkeys(("motorway", "motorway_link", "trunk", "trunk_link"), 0),
    **dict.fromkeys(("primary", "primary_link"), 1),
    **dict.fromkeys(("secondary", "secondary_link", "tertiary", "tertiary_link"), 2),
    **dict.fromkeys(("residential", "unclassified", "living_street", "service", "road", "pedestrian"), 3),
    **dict.fromkeys(("track", "path", "footway", "cycleway", "steps", "bridleway"), 4),
}


# Haritada ad yazilan yer turleri (OSM `place`): sehir/ilce, koy, mahalle.
YER_TURLERI = ("city", "town", "village", "suburb", "quarter", "neighbourhood")
SOKAK_EN_KISA_M = 80.0      # daha kisa yola ad yazilmaz
SOKAK_TEKRAR_M = 250.0      # ayni ad bu mesafeden sik yazilmaz


def sokak_etiketleri(cizgi, lat0):
    """Sokak adi yerlesimi: adli yolun ortasi ve yol yonundeki aci (derece,
    saat yonunun tersi, ters yazi olmasin diye -90..90). Once buyuk yol ve
    uzun parca; ayni ad SOKAK_TEKRAR_M'den yakin tekrar edilmez."""
    from shapely.geometry import LineString

    k = math.cos(math.radians(lat0))
    adaylar = []
    for ad, tip, geom in zip(cizgi["name"], cizgi["highway"], cizgi.geometry.values):
        sinif = YOL_SINIFI.get(tip)
        if not isinstance(ad, str) or not ad.strip() or sinif is None or sinif > 3:
            continue
        for parca in parcalar(geom, 2):
            uzunluk = sum(math.hypot((x2 - x1) * k * 111320.0, (y2 - y1) * 110574.0)
                          for (x1, y1), (x2, y2) in zip(parca, parca[1:]))
            if uzunluk < SOKAK_EN_KISA_M:
                continue
            cizgi_ = LineString(parca)
            orta = cizgi_.interpolate(0.5, normalized=True)
            a = cizgi_.interpolate(0.45, normalized=True)
            b = cizgi_.interpolate(0.55, normalized=True)
            aci = math.degrees(math.atan2(b.y - a.y, (b.x - a.x) * k))
            aci = aci - 180 if aci > 90 else aci + 180 if aci < -90 else aci
            adaylar.append((sinif, -uzunluk, str(ad), orta.x, orta.y, aci))
    adaylar.sort(key=lambda a: (a[0], a[1]))
    konan, cikti = {}, {"ad": [], "lon": [], "lat": [], "aci": [], "sinif": []}
    for sinif, _u, ad, x, y, aci in adaylar:
        if any(math.hypot((x - px) * k * 111320.0, (y - py) * 110574.0) < SOKAK_TEKRAR_M
               for px, py in konan.get(ad, [])):
            continue
        konan.setdefault(ad, []).append((x, y))
        cikti["ad"].append(ad)
        cikti["lon"].append(round(x, 5))
        cikti["lat"].append(round(y, 5))
        cikti["aci"].append(round(aci))
        cikti["sinif"].append(sinif)
    return cikti


def kutu_of(b):
    r = b.get("yaricapKm", YARICAP_KM)
    dlat = r / 110.574
    dlon = r / (111.32 * math.cos(math.radians(b["lat"])))
    return (b["lon"] - dlon, b["lat"] - dlat, b["lon"] + dlon, b["lat"] + dlat)


def parcalar(geom, en_az):
    """Geometriden koordinat dizileri (cizgi ya da cokgenin dis halkasi)."""
    if geom is None or geom.is_empty:
        return []
    tip = geom.geom_type
    if tip in ("MultiLineString", "MultiPolygon", "GeometryCollection"):
        return [p for g in geom.geoms for p in parcalar(g, en_az)]
    if tip == "LineString":
        k = list(geom.coords)
    elif tip == "Polygon":
        k = list(geom.exterior.coords)
    else:
        return []
    return [k] if len(k) >= en_az else []


def kodla(diziler, en_az):
    """Tamsayi-delta kodlama: butun dizi boyunca ardisik fark; yuvarlamada
    ust uste dusen koseler atilir. Donus: {adet, baslangic, koord}."""
    baslangic, koord = [], []
    px = py = n = 0
    for d in diziler:
        noktalar, son = [], None
        for x, y in d:
            p = (round(x * OLCEK), round(y * OLCEK))
            if p != son:
                noktalar.append(p)
                son = p
        if len(noktalar) < en_az:
            continue
        baslangic.append(n)
        for xi, yi in noktalar:
            koord.extend((xi - px, yi - py))
            px, py = xi, yi
            n += 1
    return {"adet": len(baslangic), "baslangic": baslangic, "koord": koord}


def oku(pbf, kutular):
    """Uc katmani okur: OSM surucusu her okumada butun dosyayi gezer (~45-80 sn)
    ve bu sure kutudan bagimsizdir. Birden fazla kutu verilirse birlesimleri
    tek gecisle okunur; bolgelere `paketle` boler."""
    import pyogrio
    import shapely

    suzgec = ({"bbox": kutular[0]} if len(kutular) == 1
              else {"mask": shapely.union_all([shapely.box(*k) for k in kutular])})
    t0 = time.perf_counter()
    cizgi = pyogrio.read_dataframe(
        pbf, layer="lines", columns=["highway", "waterway", "name"],
        where="highway IS NOT NULL OR waterway IN ('river','canal')", **suzgec)
    t1 = time.perf_counter()
    alan = pyogrio.read_dataframe(
        pbf, layer="multipolygons", columns=["building", "natural", "landuse"],
        where="building IS NOT NULL OR natural = 'water' OR landuse IN ('reservoir','basin')", **suzgec)
    t2 = time.perf_counter()
    yer = pyogrio.read_dataframe(
        pbf, layer="points", columns=["name", "place"],
        where="name IS NOT NULL AND place IN (" + ",".join(f"'{t}'" for t in YER_TURLERI) + ")", **suzgec)
    t3 = time.perf_counter()
    return (cizgi, alan, yer), {"cizgi": round(t1 - t0, 1), "alan": round(t2 - t1, 1), "yer": round(t3 - t2, 1)}


def bolge_uret(b, pbf):
    katmanlar, sure = oku(pbf, [kutu_of(b)])
    return paketle(b, *katmanlar), sure


def paketle(b, cizgi, alan, yer):
    import shapely

    kutu = kutu_of(b)
    # Toplu okumada katmanlar birden fazla bolgeyi tasir: kutuyla kesisenler.
    cizgi = cizgi.cx[kutu[0]:kutu[2], kutu[1]:kutu[3]].copy()
    alan = alan.cx[kutu[0]:kutu[2], kutu[1]:kutu[3]]
    yer = yer.cx[kutu[0]:kutu[2], kutu[1]:kutu[3]]

    # Kutu disina tasan cizgi ve su kirpilir; yapilar tam kalir.
    cizgi["geometry"] = shapely.clip_by_rect(cizgi.geometry.values, *kutu)
    yollar = []
    for sinif in range(5):
        tipler = [t for t, s in YOL_SINIFI.items() if s == sinif]
        secim = cizgi[cizgi["highway"].isin(tipler)]
        diziler = [p for g in shapely.simplify(secim.geometry.values, 1e-5) for p in parcalar(g, 2)]
        kod = kodla(diziler, 2)
        if kod["adet"]:
            yollar.append({"sinif": sinif, **kod})
    nehir = cizgi[cizgi["waterway"].isin(["river", "canal"]) & cizgi["highway"].isna()]
    nehirler = kodla([p for g in shapely.simplify(nehir.geometry.values, 2e-5) for p in parcalar(g, 2)], 2)

    yapi = alan[alan["building"].notna()]
    yapilar = kodla([p for g in yapi.geometry.values for p in parcalar(g, 4)], 4)
    su = alan[(alan["natural"] == "water") | alan["landuse"].isin(["reservoir", "basin"])]
    su_geom = shapely.simplify(shapely.clip_by_rect(su.geometry.values, *kutu), 2e-5)
    sular = kodla([p for g in su_geom for p in parcalar(g, 4)], 4)

    yerler = [{"ad": str(a), "tur": str(t), "lon": round(g.x, 5), "lat": round(g.y, 5)}
              for a, t, g in zip(yer["name"], yer["place"], yer.geometry.values)]
    sokaklar = sokak_etiketleri(cizgi, b["lat"])

    return {"kutu": [round(v, 5) for v in kutu], "yollar": yollar, "nehirler": nehirler,
            "su": sular, "yapilar": yapilar, "yerler": yerler, "sokaklar": sokaklar}


def yerler_yaz():
    """Butun paketlerdeki yer adlarini tek hafif listeye yazar (veri/altlik/
    yerler.json, ~40 KB): afetzede ekrani konum alinamadiginda mahalle
    sectirir, bunun icin megabaytlik paket indirmez (J-43)."""
    import unicodedata

    yerler = []
    for b in BOLGELER:  # yalniz operasyon bolgeleri: afetzede rotasi yalniz orada var
        yol = CIKTI / f"{b['id']}.json.gz"
        if not yol.exists():
            continue
        with gzip.open(yol, "rt", encoding="utf-8") as f:
            paket = json.load(f)
        for y in paket.get("yerler", []):
            yerler.append({**y, "bolge": paket["bolge"], "bolgeAd": paket["ad"]})
    anahtar = lambda y: (y["bolgeAd"], unicodedata.normalize("NFKD", y["ad"]).casefold())
    yerler.sort(key=anahtar)
    (CIKTI / "yerler.json").write_text(json.dumps(yerler, ensure_ascii=False), encoding="utf-8")
    return len(yerler)


# Afetzede haritasindaki hizmet noktalari (J-50). OSM `amenity` / `healthcare`
# etiketi -> bizim tur adimiz. Toplanma alanlari buradan DEGIL, AFAD'in resmi
# listesinden gelir (uclar/yerler.py).
HIZMET_TURU = {
    "hospital": "hastane",
    "clinic": "saglik",
    "doctors": "saglik",
    "centre": "saglik",       # healthcare=centre (aile sagligi merkezi vb.)
    "doctor": "saglik",
    "pharmacy": "eczane",
    "fire_station": "itfaiye",
    "police": "polis",
}


def _etiket(other_tags, anahtar):
    """GDAL'in `other_tags` alani: "anahtar"=>"deger","..."=>"..." bicimi."""
    import re

    if not isinstance(other_tags, str):
        return None
    m = re.search(r'"' + anahtar + r'"=>"([^"]*)"', other_tags)
    return m.group(1) if m else None


def hizmetler_uret(pbf):
    """Bes bolgenin hastane, saglik merkezi, eczane, itfaiye ve polis noktalari.

    Iki okuma yapilir (noktalar, alanlar) ve butun bolgeleri kapsayan tek kutu
    kullanilir: OSM surucusu her okumada dosyanin tamamini gezdigi icin bolge
    basina okumak bes kat surerdi. Alan olarak cizilmis yerin (hastane
    yerleskesi gibi) temsil noktasi alinir. Kayit, yerel OSM kopyasinin
    tarihindeki haritadir; yerin su an acik olup olmadigini soylemez."""
    import pyogrio

    kutular = {b["id"]: kutu_of(b) for b in BOLGELER}
    birlesik = (
        min(k[0] for k in kutular.values()), min(k[1] for k in kutular.values()),
        max(k[2] for k in kutular.values()), max(k[3] for k in kutular.values()),
    )
    amenity = ",".join(f"'{a}'" for a in HIZMET_TURU)
    t0 = time.time()
    nokta = pyogrio.read_dataframe(
        pbf, layer="points", bbox=birlesik, columns=["osm_id", "name", "other_tags"],
        where="other_tags LIKE '%\"amenity\"=>%' OR other_tags LIKE '%\"healthcare\"=>%'")
    t1 = time.time()
    alan = pyogrio.read_dataframe(
        pbf, layer="multipolygons", bbox=birlesik,
        columns=["osm_id", "osm_way_id", "name", "amenity", "other_tags"],
        where=f"amenity IN ({amenity}) OR other_tags LIKE '%\"healthcare\"=>%'")
    t2 = time.time()

    def bolgesi(lon, lat):
        for bid, k in kutular.items():
            if k[0] <= lon <= k[2] and k[1] <= lat <= k[3]:
                return bid
        return None

    yerler, gorulen = [], set()
    kayitlar = []
    for _, r in nokta.iterrows():
        a = _etiket(r["other_tags"], "amenity") or _etiket(r["other_tags"], "healthcare")
        kayitlar.append((a, r["name"], r.geometry, f"node/{r['osm_id']}"))
    for _, r in alan.iterrows():
        a = r["amenity"] if isinstance(r["amenity"], str) else _etiket(r["other_tags"], "healthcare")
        osm = f"way/{r['osm_way_id']}" if isinstance(r["osm_way_id"], str) else f"relation/{r['osm_id']}"
        kayitlar.append((a, r["name"], r.geometry.representative_point() if r.geometry is not None else None, osm))

    for a, ad, nokta_geo, osm in kayitlar:
        tur = HIZMET_TURU.get(a or "")
        if tur is None or nokta_geo is None or osm in gorulen:
            continue
        lon, lat = round(nokta_geo.x, 6), round(nokta_geo.y, 6)
        bid = bolgesi(lon, lat)
        if bid is None:
            continue
        gorulen.add(osm)
        yerler.append({"tur": tur, "ad": ad if isinstance(ad, str) and ad.strip() else None,
                       "lon": lon, "lat": lat, "bolge": bid, "osm": osm})
    return yerler, {"nokta": round(t1 - t0, 1), "alan": round(t2 - t1, 1)}


def main(secilen):
    sys.path.insert(0, str(BACKEND))
    from apps.road_damage.utils.network import LOCAL_PBF_PATH

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

    if "--hizmetler" in secilen:
        yerler, sure = hizmetler_uret(str(pbf))
        cikti = {"kaynak": kaynak, "uretim": datetime.datetime.now().isoformat(timespec="seconds"),
                 "bolgeler": [b["id"] for b in BOLGELER], "yerler": yerler}
        (CIKTI / "hizmetler.json").write_text(json.dumps(cikti, ensure_ascii=False), encoding="utf-8")
        from collections import Counter
        print(f"hizmet noktalari: {dict(Counter(y['tur'] for y in yerler))} | "
              f"okuma {sure['nokta']} + {sure['alan']} sn", flush=True)
        return 0

    katalog_yolu = CIKTI / "katalog.json"
    katalog = {k["id"]: k for k in (json.loads(katalog_yolu.read_text(encoding="utf-8"))
                                    if katalog_yolu.exists() else [])}

    iller = "--iller" in secilen
    hedefler = il_bolgeleri() if iller else BOLGELER
    def hazir(b):
        k = katalog.get(b["id"])
        return ((CIKTI / f"{b['id']}.json.gz").exists() and k is not None
                and k.get("yaricapKm", YARICAP_KM) == b.get("yaricapKm", YARICAP_KM))

    bekleyen = [b for b in hedefler
                if not (iller and hazir(b)) and (iller or not secilen or b["id"] in secilen)]
    # Iller gruplarla okunur: dosya grup basina bir kez gezilir (il basina gezmek
    # il basina ~140 sn ediyordu). Grup, alani GRUP_ALANI'ni asmayacak kadar.
    gruplar = []
    for b in sorted(bekleyen, key=lambda x: x.get("yaricapKm", YARICAP_KM)):
        alan = (b.get("yaricapKm", YARICAP_KM) / 8.0) ** 2
        if iller and gruplar and gruplar[-1][0] + alan <= GRUP_ALANI:
            gruplar[-1][0] += alan
            gruplar[-1][1].append(b)
        else:
            gruplar.append([alan, [b]])
    tamam = len(hedefler) - len(bekleyen)
    print(f"{len(bekleyen)} bolge, {len(gruplar)} grup", flush=True)
    for _, grup in gruplar:
        katmanlar, sure = oku(str(pbf), [kutu_of(b) for b in grup])
        print(f"okuma ({len(grup)} bolge): {sure['cizgi']} + {sure['alan']} + {sure['yer']} sn", flush=True)
        for b in grup:
            paket = paketle(b, *katmanlar)
            paket = {"bolge": b["id"], "ad": b["ad"], "olcek": OLCEK, "kaynak": kaynak,
                     "uretim": datetime.datetime.now().isoformat(timespec="seconds"), **paket}
            yol = CIKTI / f"{b['id']}.json.gz"
            with gzip.open(yol, "wt", encoding="utf-8", compresslevel=9) as f:
                json.dump(paket, f, ensure_ascii=False, separators=(",", ":"))
            sayilar = {"yol": sum(y["adet"] for y in paket["yollar"]), "yapi": paket["yapilar"]["adet"],
                       "su": paket["su"]["adet"], "nehir": paket["nehirler"]["adet"],
                       "yerAdi": len(paket["yerler"]), "sokakAdi": len(paket["sokaklar"]["ad"])}
            katalog[b["id"]] = {"id": b["id"], "ad": b["ad"], "tur": b.get("tur", "operasyon"),
                                "yaricapKm": b.get("yaricapKm", YARICAP_KM),
                                "kutu": paket["kutu"], "sayilar": sayilar,
                                "boyutBayt": yol.stat().st_size, "kaynak": kaynak, "uretim": paket["uretim"]}
            katalog_yolu.write_text(json.dumps(list(katalog.values()), ensure_ascii=False, indent=1),
                                    encoding="utf-8")
            tamam += 1
            print(f"[{tamam}/{len(hedefler)}] {b['id']}: {sayilar} | {yol.stat().st_size / 1e6:.2f} MB",
                  flush=True)
        del katmanlar
    print(f"yer adlari listesi: {yerler_yaz()} ad", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
