"""Tatbikat (simulasyon modu) cekirdegi: ekipler, afetzedeler ve rota kosusu.

Simulasyonun sirasi SIMULASYON_SOZLESMESI.md'de: gercek goruntu -> kendi
modelimiz -> hasar maskesi -> yol kapanmalari -> rotalar -> gorevler. Bu modul
o zincirin SON iki halkasini kurar; hasar ve kapanma zaten `worker.py`'nin
uretip `road_damage_sessions`'a biraktigi grafikten gelir.

Buradaki hicbir sey yeni bir arama algoritmasi yazmaz: rotalar `network.py`'nin
`calculate_route`'u ile (Dijkstra ve A*) hesaplanir, ceza `apply_risk_penalties`
ile uygulanir. Modulun isi, ayni OD ciftini UC farkli grafik uzerinde kosturup
farki olcmektir:

    deprem oncesi  tam grafik, weight='length'      -- hicbir sey olmamis gibi
    kapanmali      safe_G (kapali kenarlar yok)     -- modelin bulduguna gore
    riskli         safe_G + risk_cost               -- hasara yakin yol pahali

Gercek olan ne, uretilen ne (CLAUDE.md 1):
  ekipler     GERCEK  -- OSM'deki hastane/saglik ocagi/itfaiye, adiyla
  afetzedeler URETILEN -- modelin hasarli dedigi bolgelerden secilir, "senaryo"
"""
import json
import math
import random
import time
from pathlib import Path

import requests

from apps.road_damage.utils.network import (
    apply_risk_penalties,
    calculate_route,
    haversine,
    nearest_node,
)

# network.py'deki ayna listesiyle ayni: tek sunucu yogun oldugunda (olculdu:
# ReadTimeout) tatbikat kurulamiyordu. Sonuc ayrica diske yazilir -- ekip usleri
# gun icinde degismez, tatbikat Overpass'in o anki haline baglanmamali.
OVERPASS_UCLARI = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
ONBELLEK_DIZINI = Path(__file__).resolve().parents[3] / "veri" / "tatbikat_onbellek"
BASLIK = {"User-Agent": "QuakeMind/1.0 (TUBITAK 2209-A arastirma projesi)"}
# Ekip ussu olabilecek gercek tesisler, tercih sirasiyla: once mudahale
# birimleri, sonra saglik tesisleri.
TESIS_ONCELIGI = ("fire_station", "hospital", "police", "clinic", "ambulance_station")
# Ekipler hasar alaninin DISINDA olmali: icine koyarsak rota birkac yuz metre
# kalir ve kapanmanin etkisi hic gorunmez.
EN_YAKIN_EKIP_M = 250.0

_ekip_onbellegi: dict = {}


def _overpass(sorgu: str, zaman_asimi: float = 90.0):
    son_hata = None
    for uc in OVERPASS_UCLARI:
        try:
            yanit = requests.post(uc, data={"data": sorgu}, headers=BASLIK, timeout=zaman_asimi)
            if yanit.status_code == 200 and yanit.text.lstrip().startswith("{"):
                return yanit.json()
            son_hata = f"{uc}: HTTP {yanit.status_code}"
        except Exception as e:  # ag hatasi, zaman asimi
            son_hata = f"{uc}: {type(e).__name__}"
    raise RuntimeError(f"Overpass yanit vermedi ({son_hata})")


def _yerel_tesisler(merkez_lat, merkez_lon, yaricap_km):
    """Yerel tesis dosyasindan Overpass bicimli yanit; dosya yoksa None."""
    from apps.road_damage.utils import yerel_yol

    yol = yerel_yol.VERI / "tesisler.gpkg"
    if not yol.exists():
        return None
    try:
        import geopandas as gpd

        d = yaricap_km / 111.32
        dlon = d / max(0.1, math.cos(math.radians(merkez_lat)))
        g = gpd.read_file(yol, bbox=(merkez_lon - dlon, merkez_lat - d,
                                     merkez_lon + dlon, merkez_lat + d))
    except Exception:
        return None
    ogeler = []
    for _, r in g.iterrows():
        nokta = r.get("geometry")
        if nokta is None or nokta.is_empty:
            continue
        etiket = {}
        for alan in ("amenity", "emergency", "name"):
            deger = r.get(alan)
            if deger is not None and str(deger) not in ("None", "nan", ""):
                etiket[alan] = str(deger)
        ogeler.append({"lat": float(nokta.y), "lon": float(nokta.x), "tags": etiket})
    return {"elements": ogeler}


def ekipler(merkez_lat, merkez_lon, sayi=5, yaricap_km=3.5):
    """Merkez cevresindeki GERCEK tesislerden ekip usleri.

    Adi ve koordinati OSM'den gelir; uydurulmaz. Alan icindekiler elenir
    (bkz. EN_YAKIN_EKIP_M) ve tur onceligine, sonra uzakliga gore siralanir.
    """
    anahtar = (round(merkez_lat, 4), round(merkez_lon, 4), round(yaricap_km, 2))
    disk = ONBELLEK_DIZINI / ("ekip_%s_%s_%s.json" % anahtar)
    if anahtar not in _ekip_onbellegi and disk.exists():
        try:
            _ekip_onbellegi[anahtar] = json.loads(disk.read_text(encoding="utf-8"))
        except Exception:
            pass
    if anahtar not in _ekip_onbellegi:
        d = yaricap_km / 111.32
        dlon = d / max(0.1, math.cos(math.radians(merkez_lat)))
        kutu = f"{merkez_lat - d},{merkez_lon - dlon},{merkez_lat + d},{merkez_lon + dlon}"
        sorgu = (
            "[out:json][timeout:60];("
            f'nwr["amenity"~"fire_station|hospital|police|clinic"]({kutu});'
            f'nwr["emergency"="ambulance_station"]({kutu});'
            ");out center tags;"
        )
        # Once YEREL tesis dosyasi (araclar_yerel_osm_kur.py); Overpass yalniz
        # o dosya yoksa denenir. Overpass'in dort aynasi da dusebiliyor
        # (olculdu 26 Eylul) ve tatbikat dis servise bagli kalmamali.
        d_json = _yerel_tesisler(merkez_lat, merkez_lon, yaricap_km)
        if d_json is None:
            d_json = _overpass(sorgu)
        bulunan = []
        for e in d_json.get("elements", []):
            etiket = e.get("tags", {})
            lat = e.get("lat") or (e.get("center") or {}).get("lat")
            lon = e.get("lon") or (e.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            tur = etiket.get("amenity") or etiket.get("emergency")
            if tur not in TESIS_ONCELIGI:
                continue
            bulunan.append({
                "ad": etiket.get("name") or "(isimsiz tesis)",
                "tur": tur,
                "lat": round(float(lat), 6),
                "lon": round(float(lon), 6),
                "uzaklikM": round(haversine(merkez_lat, merkez_lon, float(lat), float(lon)), 1),
                "gercekTesis": True,
                "kaynak": "OpenStreetMap",
            })
        _ekip_onbellegi[anahtar] = bulunan
        try:
            ONBELLEK_DIZINI.mkdir(parents=True, exist_ok=True)
            disk.write_text(json.dumps(bulunan, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    aday = [e for e in _ekip_onbellegi[anahtar] if e["uzaklikM"] >= EN_YAKIN_EKIP_M]
    aday.sort(key=lambda e: (TESIS_ONCELIGI.index(e["tur"]), e["uzaklikM"]))
    secilen = aday[:sayi]
    for i, e in enumerate(secilen, 1):
        e["id"] = f"e{i}"
    return secilen


def afetzedeler(hasar_maskesi, bounds, sayi=5, tohum=42, en_az_piksel=40):
    """Modelin hasarli dedigi blobların icinden `sayi` kadar senaryo konumu.

    Rastgele nokta serpilmez: konumlar modelin KENDI ciktisina baglanir, boylece
    tatbikat kendi tespitini takip eder. "Orada biri var" varsayimi uretilendir
    ve sonucta `senaryo: True` ile isaretlenir.

    `hasar_maskesi` ikili (0/1) numpy dizisi, `bounds` (bati, guney, dogu, kuzey).
    """
    import cv2
    import numpy as np

    maske = (np.asarray(hasar_maskesi) > 0).astype(np.uint8)
    h, w = maske.shape[:2]
    bati, guney, dogu, kuzey = bounds
    n, _etiketler, istatistik, agirlik_merkezleri = cv2.connectedComponentsWithStats(maske, connectivity=8)
    bloblar = [
        (int(istatistik[i, cv2.CC_STAT_AREA]), i)
        for i in range(1, n)
        if istatistik[i, cv2.CC_STAT_AREA] >= en_az_piksel
    ]
    if not bloblar:
        return []
    bloblar.sort(reverse=True)
    # En buyuk 40 blob aday; icinden tohumla secilir -- ayni tohum ayni tatbikat.
    #
    # ON EK KARARLI olmali (olculdu, 26 Eylul). Once `random.sample(aday, sayi)`
    # kullaniliyordu; o zaman 15 afetzede isteyip ilk 5'ini almak, dogrudan 5
    # istemekten BAMBASKA bir kume veriyordu. Yolun ulasamadigi noktalari
    # elemek icin fazladan aday istemek gerektiginden bu, ayni tohumla ayni
    # tatbikatin kurulmasini bozuyordu (Islahiye'de kazanc %44 -> %0 gorundu,
    # model ya da kapanma degismedigi halde). Bu yuzden aday listesi tohumla
    # BIR KEZ karilir ve bastan `sayi` kadari alinir: N buyudukce liste yalniz
    # uzar, bastaki secim degismez.
    aday = bloblar[: max(sayi, 40)]
    rastgele = random.Random(tohum)
    karisik = list(aday)
    rastgele.shuffle(karisik)
    secilen = karisik[:sayi]
    sonuc = []
    for sira, (alan, i) in enumerate(secilen, 1):
        cx, cy = agirlik_merkezleri[i]
        sonuc.append({
            "id": f"a{sira}",
            "ad": f"Afetzede {sira}",
            "lat": round(kuzey - (cy / h) * (kuzey - guney), 6),
            "lon": round(bati + (cx / w) * (dogu - bati), 6),
            "hasarBlobPiksel": alan,
            "senaryo": True,
            "kaynak": "senaryo — modelin hasarlı bulduğu alandan seçildi",
        })
    return sonuc


def tatbikat_grafigi(ekip_listesi, afetzede_listesi, hasar_maskesi, bounds,
                     kapanma_yaricapi_m=0.0, marj_km=0.6, gecerli_maske=None):
    """Rota grafigi: ekipleri ve afetzedeleri KAPSAYAN kutu, kapanmalar maskeden.

    Analizin kendi grafigi kullanilamaz: o yalnizca goruntu kutusunu (yakin
    katmanda ~500 m) kapsar, ekip usleri ise 1,3-3,8 km uzakta gercek
    tesislerdir. Olculdu (25 Eylul, ilk kosu): analiz grafigi 120 dugum / 340
    kenar, ekiplerin hepsi kutu disinda kaliyor, 25 OD ciftinin 25'i
    "ulasilamadi" donuyordu -- rota kismi aslinda hic calismamis oluyordu.

    Bu yuzden graf ayri cekilir; kapanmalar maskeden `closures_from_damage_mask`
    ile turetilir (canli /analyze ile ayni kural ve ayni ornekleme). Maskenin
    disinda kalan kenarlar acik sayilir; `kapsama` bunun ne kadarini maskenin
    gordugunu soyler -- tatbikat raporunda bu yazilir, "her yer acik" gibi
    okunmasin.
    """
    import networkx as nx

    from apps.road_damage.utils.network import closures_from_damage_mask, fetch_osm_road_graph
    from apps.road_damage.utils.serialization import serialize_segments

    enlemler = [e["lat"] for e in ekip_listesi] + [a["lat"] for a in afetzede_listesi] + [bounds[1], bounds[3]]
    boylamlar = [e["lon"] for e in ekip_listesi] + [a["lon"] for a in afetzede_listesi] + [bounds[0], bounds[2]]
    d_lat = marj_km / 111.32
    d_lon = marj_km / (111.32 * max(0.1, math.cos(math.radians(sum(enlemler) / len(enlemler)))))
    kutu = (min(boylamlar) - d_lon, min(enlemler) - d_lat, max(boylamlar) + d_lon, max(enlemler) + d_lat)

    G, hata = fetch_osm_road_graph(kutu)
    if G is None:
        raise RuntimeError(f"Tatbikat yol grafigi cekilemedi (yerel onbellek yok, Overpass: {hata}).")
    # `gecerli_maske` verilirse kapsama hesaplanir: hangi kenarlarin uzerine
    # model gercekten BAKTI? Drone ortofotosunda karenin %61'i bos oldugu icin
    # bu sayi kritik -- gorulmeyen kenar "acik" sayilir ama olculmemistir.
    _acik, kapali_kenarlar, kapali_anahtarlar, kapsama = closures_from_damage_mask(
        G, bounds, hasar_maskesi, valid_mask=gecerli_maske,
        blockage_radius_m=kapanma_yaricapi_m,
    )
    # Haritada cizilecek kapali kenarlarin geometrisi de doner: arayuz analizin
    # (goruntu kutusuyla sinirli) kapanmalarini degil TATBIKATIN kapanmalarini
    # cizmeli, yoksa kirmizi katman rotalarla tutarsiz gorunur.
    return (G, nx.restricted_view(G, [], kapali_anahtarlar), kapali_anahtarlar, kutu, kapsama,
            serialize_segments(kapali_kenarlar))


# Yol sinifi onceligi: mahalleye giris noktasi secilirken ana yol tercih edilir.
GIRIS_ONCELIGI = ["primary", "secondary", "tertiary", "unclassified", "residential",
                  "living_street", "service"]


def mahalle_grafigi(hasar_maskesi, bounds, marj_m=150.0, kapanma_yaricapi_m=0.0,
                    gecerli_maske=None):
    """SON ADIM grafigi: yalniz goruntulenen mahalle + dar bir marj.

    NEDEN BU GEREKTI (olculdu, 26 Eylul). Once ekip usleri gercek tesisler
    (1,3-3,8 km uzakta) alinip rota grafigi onlari kapsayacak sekilde
    kuruluyordu. Sonuc: model rota agindaki kenarlarin YALNIZ %0,64'unu
    goruyordu (25.323 kenarin 162'si), kapanma hicbir rotaya denk gelmiyordu
    (kesif 0) ve uc kiyas kolu da BIREBIR ayni cikiyordu -- yani tatbikat
    hicbir sey olcmuyordu.

    Sebep basit: drone mozaigi ~500 m, rota ~3 km. 500 metrelik bir enkaz
    haritasi 3 kilometrelik bir rotayi degistiremez.

    Dogru soru, verinin destekledigi sorudur: **mahalleye giren ekip, icerideki
    enkaza ne kadar surede ulasiyor ve moloz haritasini bilmek bunu degistiriyor
    mu?** Bu yuzden dunya goruntulenen alana daraltilir; ekipler mahallenin
    GIRISINDE konuslanir (gercek yollarin kareyi kestigi noktalar), afetzedeler
    icerideki hasar bloblaridir. Boylece modelin gordugu alan ile rotanin
    gectigi alan ORTUSUR ve kapsama ~%100 olur.

    Donus: `tatbikat_grafigi` ile ayni sozlesme.
    """
    import networkx as nx

    from apps.road_damage.utils.network import closures_from_damage_mask, fetch_osm_road_graph
    from apps.road_damage.utils.serialization import serialize_segments

    bati, guney, dogu, kuzey = bounds
    d_lat = marj_m / 111320.0
    d_lon = marj_m / (111320.0 * max(0.1, math.cos(math.radians((guney + kuzey) / 2))))
    kutu = (bati - d_lon, guney - d_lat, dogu + d_lon, kuzey + d_lat)

    G, hata = fetch_osm_road_graph(kutu)
    if G is None:
        raise RuntimeError(f"Mahalle yol grafigi cekilemedi: {hata}")
    _acik, kapali_kenarlar, kapali_anahtarlar, kapsama = closures_from_damage_mask(
        G, bounds, hasar_maskesi, valid_mask=gecerli_maske,
        blockage_radius_m=kapanma_yaricapi_m,
    )
    return (G, nx.restricted_view(G, [], kapali_anahtarlar), kapali_anahtarlar, kutu, kapsama,
            serialize_segments(kapali_kenarlar))


def giris_noktalari(G, bounds, sayi=5):
    """Mahalleye arac girisi olan gercek yol dugumleri (ekip konuslanma yeri).

    Ekip usu "uydurma bir nokta" degildir: goruntulenen karenin DISINDA kalan
    ama kareye giren gercek yollarin uzerindeki dugumlerdir -- yani ekibin
    mahalleye gerçekte girecegi agizlar. Ana yol sinifi once gelir; ayni
    agizdan bes ekip cikmasin diye noktalar birbirinden ayrilir.
    """
    bati, guney, dogu, kuzey = bounds

    def icerde(n):
        d = G.nodes[n]
        return bati <= d["x"] <= dogu and guney <= d["y"] <= kuzey

    agizlar = {}
    for u, v, _k, d in G.edges(keys=True, data=True):
        if u not in G.nodes or v not in G.nodes:
            continue
        try:
            u_ic, v_ic = icerde(u), icerde(v)
        except KeyError:
            continue
        if u_ic == v_ic:
            continue
        dis = v if u_ic else u
        sinif = str(d.get("highway") or "residential")
        oncelik = GIRIS_ONCELIGI.index(sinif) if sinif in GIRIS_ONCELIGI else len(GIRIS_ONCELIGI)
        if dis not in agizlar or oncelik < agizlar[dis][0]:
            agizlar[dis] = (oncelik, sinif)

    aday = sorted(agizlar.items(), key=lambda kv: kv[1][0])
    secilen, konumlar = [], []
    for n, (_o, sinif) in aday:
        la, lo = G.nodes[n]["y"], G.nodes[n]["x"]
        # Ayni agizdan birden fazla ekip cikmasin: en az 120 m ara.
        if any(haversine(la, lo, a, b) < 120.0 for a, b in konumlar):
            continue
        konumlar.append((la, lo))
        # AD EKRANA YAZILIYOR, JARGON OLMAMALI. Önce "tertiary girişi 1" gibi
        # OSM yol sınıfı adı kullanılıyordu; kullanıcı haritada ne olduğunu
        # anlamıyordu (27 Eylül). Sınıf bilgisi ayrı alanda duruyor, ekranda
        # insanın tanıdığı ad var.
        secilen.append({
            "id": f"e{len(secilen) + 1}",
            "ad": f"Ekip {len(secilen) + 1} · mahalle girişi",
            "yolSinifi": sinif,
            "tur": "giris",
            "lat": round(la, 6), "lon": round(lo, 6),
            "dugum": n,
            "gercekTesis": False,
            "kaynak": "OpenStreetMap (mahalle giriş ağzı)",
        })
        if len(secilen) >= sayi:
            break
    return secilen


def ulasilabilir_afetzedeler(G, ekip_listesi, afetzede_listesi):
    """Kapanmasiz cizgede BUTUN ekiplerin ulasabildigi afetzedeler.

    NEDEN "BUTUN" (olculdu, 26 Eylul). Tatbikat turlari her ekibi her
    afetzedeyle esliyor (n ekip x n tur). Bu yuzden "herhangi bir ekipten
    ulasilabilir" yetmez: afetzede 3 numarali ekipten ulasilabilir ama 1
    numaradan ulasilamiyorsa, 1 numarayla eslesen tur bos doner ve ORTAK
    gorev sayisi sifira duser -- olculdu: Defne/Elektrik + hizli modelde tek
    afetzede elemeden geciyor, uc kolun ucu de 0/1 ile bitiyordu.

    Ayrica hicbir afetzedeye ulasamayan EKIP de elenir (kopuk bir yol
    parcasindaki giris agzi butun turleri bosa dusururdu).

    Baslangic dugumu filonun kullandigi yolla (`nearest_node`) bulunur; kayitli
    `dugum` alanina bakmak ikisini ayri dugume dusurebiliyordu.

    Donus: (kalan_afetzedeler, elenen_afetzedeler, kalan_ekipler)
    """
    import networkx as nx

    from apps.road_damage.utils.network import nearest_node

    if not ekip_listesi or not afetzede_listesi:
        return list(afetzede_listesi), [], list(ekip_listesi)

    erisim = {}
    for e in ekip_listesi:
        try:
            n = nearest_node(G, e["lat"], e["lon"])
            erisim[e["id"]] = set(nx.descendants(G, n)) | {n}
        except Exception:
            erisim[e["id"]] = set()

    hedefler = {}
    for a in afetzede_listesi:
        try:
            hedefler[id(a)] = nearest_node(G, a["lat"], a["lon"])
        except Exception:
            hedefler[id(a)] = None

    # Once hicbir afetzedeye ulasamayan ekipleri ele.
    kalan_ekip = [e for e in ekip_listesi
                  if any(h is not None and h in erisim[e["id"]] for h in hedefler.values())]
    if not kalan_ekip:
        return [], list(afetzede_listesi), []

    ortak = set.intersection(*(erisim[e["id"]] for e in kalan_ekip))
    kalan, elenen = [], []
    for a in afetzede_listesi:
        h = hedefler[id(a)]
        (kalan if (h is not None and h in ortak) else elenen).append(a)
    return kalan, elenen, kalan_ekip


def hasar_noktalari(hasar_maskesi, bounds, en_az_piksel=20, en_fazla=300):
    """Maskedeki hasar bloblarinin agirlik merkezleri (lat, lon).

    Rota cezasi (`apply_risk_penalties`) bunlari kullanir: kenarin en yakin
    hasar noktasina uzakligi cezayi belirler. Ust sinir, gurultulu bir maskenin
    ceza hesabini sisirmemesi icin.
    """
    import cv2
    import numpy as np

    maske = (np.asarray(hasar_maskesi) > 0).astype(np.uint8)
    h, w = maske.shape[:2]
    bati, guney, dogu, kuzey = bounds
    n, _e, istatistik, merkezler = cv2.connectedComponentsWithStats(maske, connectivity=8)
    bloblar = [i for i in range(1, n) if istatistik[i, cv2.CC_STAT_AREA] >= en_az_piksel]
    bloblar.sort(key=lambda i: istatistik[i, cv2.CC_STAT_AREA], reverse=True)
    noktalar = []
    for i in bloblar[:en_fazla]:
        cx, cy = merkezler[i]
        noktalar.append((kuzey - (cy / h) * (kuzey - guney), bati + (cx / w) * (dogu - bati)))
    return noktalar


def yaricap_kiyasi(G, bounds, hasar_maskesi, ekip_listesi, afetzede_listesi, yaricaplar,
                   gecerli_maske=None, hiz_kmh=15.0):
    """Ayni maske, farkli r_h: "moloz yayilimi yokken / varken" karsilastirmasi.

    r_h CIKARIMI etkilemez, yalnizca maskeden kapanma turetmesini etkiler --
    bu yuzden model BIR KEZ kosar, her yaricap icin yalnizca kapanma + rota
    yeniden hesaplanir. Olculdu (25 Eylul, geniş katman, 25 cift, 876 km graf):
    yaricap basina ~16 sn -- ucu birlikte 47 sn. Maliyetin tamami rota
    gecisidir (25 cift x 3 varyant x 2 arama), kapanma turetmesi degil.

    r_h = 0 "kapali" degil, BASKA BIR KURAL: yalnizca yolun tam ustundeki hasar
    kapatir (uygulamanin eski davranisi, taban cizgi).

    Donus: her yaricap icin bir satir; `benchmark/rh_duyarlilik.py` ile ayni
    alanlar, boylece tatbikattan cikan sayi olcum kaydiyla dogrudan kiyaslanir.
    """
    import networkx as nx

    from apps.road_damage.utils.network import closures_from_damage_mask

    toplam_m = sum(d.get("length", 0.0) for _u, _v, d in G.edges(data=True))
    noktalar = hasar_noktalari(hasar_maskesi, bounds)
    satirlar = []
    for rh in yaricaplar:
        rh = float(rh)
        _a, _b, kapali, _kapsama = closures_from_damage_mask(
            G, bounds, hasar_maskesi, valid_mask=gecerli_maske, blockage_radius_m=rh)
        kapali_m = 0.0
        for (u, v, k) in kapali:
            try:
                kapali_m += G[u][v][k].get("length", 0.0)
            except KeyError:
                pass
        sonuc = rota_kosusu(G, nx.restricted_view(G, [], kapali), ekip_listesi, afetzede_listesi,
                            hasar_noktalari=noktalar, hiz_kmh=hiz_kmh,
                            ceza_yaricapi_m=rh, ekranda=0)
        o = sonuc["olcum"]
        satirlar.append({
            "yaricapM": rh,
            "kural": "radius" if rh > 0 else "on_road_pixel",
            "kapaliKenar": len(kapali),
            "kapaliYolM": round(kapali_m, 1),
            "kapaliYolYuzde": round(100 * kapali_m / toplam_m, 2) if toplam_m else None,
            "ortalamaUzamaM": o["ortalamaUzamaM"],
            "ortalamaUzamaYuzde": o["ortalamaUzamaYuzde"],
            "enBuyukUzamaM": o["enBuyukUzamaM"],
            "yurumeGerekenCift": o["yurumeGerekenCift"],
            "ortalamaYurumeM": o["ortalamaYurumeM"],
            "ulasilamayanCift": o["ulasilamayanCift"],
        })
    return {"toplamYolM": round(toplam_m, 1), "ciftSayisi": len(ekip_listesi) * len(afetzede_listesi),
            "satirlar": satirlar}


def kiyas_kollari(G, kapali_anahtarlar, ekip_listesi, afetzede_listesi,
                  hiz_kmh=15.0, gorus_m=0.0, donus_maliyetli=True,
                  kenar_hizlari=True, degerlendirme_dk=None):
    """Ayni tatbikat, uc gercek operasyonel durumda.

    Kollar (eski R0/R2/R3 adlandirmasi birakildi -- kod adi degil, sahadaki
    durumu anlatan ad kullanilir):

      "Kapanmayi bilmeyen ekip"   Bugunku durum: ekip yola cikar, kapali
          sokaga varinca ogrenir, durum degerlendirir ve doner.
      "Telsizle paylasan filo"    Bir ekibin ogrendigi kapanma o anda butun
          ekiplere yayilir; digerleri kapanmaya varmadan yon degistirir.
      "QuakeMind"                 Analizin cikardigi kapanmalar bastan bilinir.

    Istege bagli dorduncu kol, `gorus_m > 0` verilirse: ekip planli yolu
    `gorus_m` metre onunden gorur.

    **Dikkat -- bu tatbikatta DUNYA modelin kapanmalaridir.** Yer gercegi bir
    kapanma katmanimiz yok; kapanmalar modelin hasar maskesinden turetiliyor.
    Dolayisiyla "QuakeMind" kolu TANIM GEREGI kusursuz bilgiye sahiptir ve bu
    kiyas modelin DOGRULUGUNU olcmez -- kapanmayi onceden bilmenin kazandirdigi
    zamani olcer. Modelin dogrulugu ayri ve etiketli veriyle olculur (J-65).
    Bu cumle raporda ve makalede aynen yer almali, yoksa "sistemimiz kusursuz"
    diye okunur.

    Donus maliyeti varsayilan olarak ACIKTIR: Turkiye'de trafik sagdan akar,
    sola donus karsi akimi keser ve U donusu manevradir (bkz. `donus.py`).
    """
    from apps.road_damage.utils.network import simulate_reference_fleet

    # TUR: her turda ekip i -> afetzede (i+tur) mod n. n ekip x n tur = n^2 cift
    # olcum, ama her tur icinde filo yine n ekiptir -- "telsizle paylasan filo"
    # kolunun anlami bozulmaz (25 ajani ayni anda kosturmak paylasimi yapay
    # olarak guclendirirdi). Tek turda olcmek sonucu 5 ciftin sansina
    # birakiyordu: olculdu (26 Eylul), ayni alanda kapanma varken bile kollar
    # ayrismayabiliyor cunku izgara alternatif yol sunuyor.
    n = min(len(ekip_listesi), len(afetzede_listesi))
    if n == 0:
        return None
    turlar = [
        [{"startLat": ekip_listesi[i]["lat"], "startLon": ekip_listesi[i]["lon"],
          "endLat": afetzede_listesi[(i + t) % n]["lat"],
          "endLon": afetzede_listesi[(i + t) % n]["lon"]}
         for i in range(n)]
        for t in range(n)
    ]
    dunya = set(kapali_anahtarlar or ())
    kosular = {
        "Kapanmayı bilmeyen ekip": {},
        "Telsizle paylaşan filo": {"share": True},
        "QuakeMind": {"prior_closed": dunya},
    }
    if gorus_m and gorus_m > 0:
        kosular["Görüş mesafeli ekip"] = {"sight_m": gorus_m}

    ortak_ayar = dict(speed_kmh=hiz_kmh, turn_costs=donus_maliyetli,
                      edge_speeds=kenar_hizlari)
    if degerlendirme_dk is not None:
        ortak_ayar["assessment_min"] = float(degerlendirme_dk)
    ham = {}
    ilk_tur = {}
    for ad, ek in kosular.items():
        try:
            birlesik = []
            for t, gorevler in enumerate(turlar):
                sonuc = simulate_reference_fleet(G, dunya, gorevler, **ortak_ayar, **ek)
                if t == 0:
                    ilk_tur[ad] = sonuc
                birlesik.extend(sonuc)
            ham[ad] = birlesik
        except Exception as e:
            ham[ad] = {"hata": f"{type(e).__name__}: {e}"}
    gorevler = [g for tur in turlar for g in tur]

    # ORTAK KUME: her kol farkli sayida gorevi tamamlayabiliyor (kapali yollar
    # bazi hedefleri o kol icin baglantisiz birakiyor). Ortalamalari farkli
    # gorev kumeleri uzerinden kiyaslamak yaniltir -- olculdu: bir kol 1/5
    # gorevde 38,5 dk, baskasi 2/5 gorevde 11,8 dk; ikisi ayni gorevler degildi.
    ortak = [
        i for i in range(len(gorevler))
        if all(isinstance(s, list) and s[i] for s in ham.values())
    ]
    cikti = {}
    for ad, sonuc in ham.items():
        if not isinstance(sonuc, list):
            cikti[ad] = sonuc
            continue
        varan = [r for r in sonuc if r]
        o = [sonuc[i] for i in ortak]
        def _ort(alan):
            # 3 basamak: 0,1 dk'ya yuvarlamak kucuk farklarda (ör. Islahiye 1,20 -> 1,08)
            # kazanci +-5 puan belirsiz birakiyordu (J-117).
            return round(sum(r[alan] for r in o) / len(o), 3) if o else None
        donus_toplam = {"duz": 0, "sag": 0, "sol": 0, "u": 0}
        for r in o:
            for t, n in (r.get("donusler") or {}).items():
                donus_toplam[t] = donus_toplam.get(t, 0) + n
        cikti[ad] = {
            "gorevSayisi": len(gorevler),
            "ulasanGorev": len(varan),
            "ortakGorev": len(ortak),
            "ortalamaSureDk": _ort("arrivalMin"),
            "ortalamaMesafeM": _ort("distanceMeters"),
            "toplamKesif": sum(r["discoveries"] for r in o),
            "cezaliOlay": sum(r["penaltyEvents"] for r in o),
            # Sonucun beyan edilen sabitlere ne kadar bagli oldugu ACIKCA yazilir:
            # eski tatbikatta farkin %97,4'u tek bir 20 dk'lik sabitten geliyordu.
            "kapanmaCezasiDk": (o[0].get("kapanmaCezasiDk") if o else None),
            "cezadanGelenDk": round(sum(r.get("cezadanGelenDk", 0.0) for r in o) / len(o), 2) if o else None,
            "donusSuresiDk": round(sum(r.get("donusSuresiDk", 0.0) for r in o) / len(o), 2) if o else None,
            # Ortak gorevler uzerinden TOPLAMLAR: ceza payi = bilmeyen kolun toplam
            # cezasi / (bilmeyen toplam sure - QuakeMind toplam sure). Ortalamalardan
            # geri hesaplamak yuvarlama yuzunden %100'u asabiliyordu (J-112).
            "toplamSureDk": round(sum(r["arrivalMin"] for r in o), 3) if o else None,
            "toplamCezaDk": round(sum(r.get("cezadanGelenDk", 0.0) for r in o), 3) if o else None,
            "donusler": donus_toplam,
            "uDonusuSayisi": donus_toplam.get("u", 0),
        }
    # FIILEN SURULEN yollar (ilk tur): harita "bilmeseydik boyle surerdik"i
    # cizebilsin diye. Planlanan varyantlar bunu gostermiyor; manset sayi ise
    # buradan geliyor.
    izlenen = {}
    for ad in ("Kapanmayı bilmeyen ekip", "QuakeMind"):
        satirlar = ilk_tur.get(ad) or []
        hatlar = []
        for r in satirlar:
            if not r or not r.get("izlenenKenar"):
                continue
            # Burada da GERCEK geometri kullanilir; dugumleri duz birlestirmek
            # rotayi binalarin ustunden geciriyordu (bkz. _kenarlardan_cizgi).
            nokta = _kenarlardan_cizgi(G, [tuple(e) for e in r["izlenenKenar"]])
            if nokta:
                hatlar.append(nokta)
        if hatlar:
            izlenen[ad] = hatlar

    return {
        "varyantlar": cikti,
        "izlenenYollar": izlenen,
        "gorusMesafesiM": gorus_m,
        "donusMaliyetli": donus_maliyetli,
        "degerlendirmeDk": degerlendirme_dk,
        "not": ("Tatbikatta dünya = modelin kapanmaları olduğu için QuakeMind kolu tanım "
                "gereği kusursuz bilgiye sahiptir. Bu kıyas modelin doğruluğunu değil, "
                "kapanmayı önceden bilmenin kazandırdığı süreyi ölçer. Ortalamalar yalnız "
                "bütün kolların ulaştığı ortak görevler üzerinden alınmıştır (ortakGorev). "
                "Trafik sağdan akar: sola dönüş ve U dönüşü maliyetlidir."),
    }


# Eski ad: dis betikler kirilmasin diye korunuyor.
referans_ajanlar = kiyas_kollari


def _rota_olc(G, baslangic, hedef, agirlik, yonler=None):
    """Tek bir OD cifti: Dijkstra ve A* ayri ayri kosar, ikisi de olculur.

    calculate_route ikisini birlikte kosabiliyor ama o zaman sureleri ayirmak
    mumkun olmuyor; tatbikat kartinda iki aramayi yan yana gosterdigimiz icin
    burada bilerek iki ayri cagri yapilir.

    `yonler` verilirse DONUS MALIYETLI kenar tabanli arama kullanilir: haritada
    cizilen rota ile kiyas kollarinin kullandigi rota AYNI kuralla bulunur.
    Ayni tatbikatta iki farkli "en iyi yol" tanimi olmasi tutarsizlikti --
    kollar sureye (donus dahil), harita ise duz uzunluga gore hesapliyordu.
    """
    if yonler is not None:
        return _rota_olc_donuslu(G, baslangic, hedef, yonler)
    t0 = time.perf_counter()
    d_hat, _a, d_maliyet, _am = calculate_route(
        G, baslangic["lat"], baslangic["lon"], hedef["lat"], hedef["lon"],
        weight=agirlik, algorithms=("dijkstra",),
    )
    d_sn = time.perf_counter() - t0
    t1 = time.perf_counter()
    _d, a_hat, _dm, a_maliyet = calculate_route(
        G, baslangic["lat"], baslangic["lon"], hedef["lat"], hedef["lon"],
        weight=agirlik, algorithms=("astar",),
    )
    a_sn = time.perf_counter() - t1
    return {
        "cizgi": d_hat or a_hat,
        "maliyet": d_maliyet if d_maliyet is not None else a_maliyet,
        "arama": {
            "dijkstra": {"maliyet": d_maliyet, "sureSn": round(d_sn, 4)},
            "astar": {"maliyet": a_maliyet, "sureSn": round(a_sn, 4)},
            # Iki aramanin AYNI yolu bulup bulmadigi: uzunluk degil, cizginin
            # kendisi karsilastirilir (esit uzunlukta farkli yol olabilir).
            # Yol yoksa "ayni" da "farkli" da denemez -> None.
            "ayniYol": (d_hat == a_hat) if (d_hat is not None and a_hat is not None) else None,
        },
    }


def _kenarlardan_cizgi(G, kenarlar):
    """Kenar dizisinden GERCEK geometriyle rota cizgisi [(lat, lon), ...].

    NEDEN (27 Eylul). Cizgi once yalniz KAVSAK DUGUMLERI arasina duz cekiliyordu
    (`[G.nodes[n]["y"], G.nodes[n]["x"]] for n in dugumler`). OSM'de iki kavsak
    arasindaki sokak cogu zaman kivrimli bir cok-noktali cizgidir; uclarini duz
    birlestirmek kosevi kesiyor ve rota **binanin ustunden geciyor** gibi
    gorunuyordu. Kullanici bunu ekranda yakaladi. Kenarin kendi `geometry`si
    varsa o kullanilir, yoksa dugumlere duser.

    Geometri yonu garanti degil: ilk nokta `u`ya mi `v`ye mi yakin diye bakilip
    gerekirse ters cevrilir, yoksa rota ileri geri zikzak yapar.
    """
    if not kenarlar:
        return None

    def konum(n):
        d = G.nodes.get(n) or {}
        if "y" in d and "x" in d:
            return (float(d["y"]), float(d["x"]))
        return None

    nokta = []
    for u, v, k in kenarlar:
        d = G.get_edge_data(u, v, k) or {}
        g = d.get("geometry")
        parca = None
        if g is not None:
            try:
                parca = [(float(la), float(lo)) for lo, la in g.coords]
            except Exception:
                parca = None
        if not parca or len(parca) < 2:
            a, b = konum(u), konum(v)
            parca = [x for x in (a, b) if x is not None]
        else:
            a = konum(u)
            if a is not None:
                bas = (parca[0][0] - a[0]) ** 2 + (parca[0][1] - a[1]) ** 2
                son = (parca[-1][0] - a[0]) ** 2 + (parca[-1][1] - a[1]) ** 2
                if son < bas:
                    parca = parca[::-1]
        for pnt in parca:
            yuvarlak = [round(pnt[0], 6), round(pnt[1], 6)]
            if not nokta or nokta[-1] != yuvarlak:
                nokta.append(yuvarlak)
    return nokta if len(nokta) >= 2 else None


def _rota_olc_donuslu(G, baslangic, hedef, yonler):
    """`_rota_olc`nin donus maliyetli surumu (Dijkstra = sezgisiz A*)."""
    from apps.road_damage.utils import donus
    from apps.road_damage.utils.network import nearest_node

    try:
        bas = nearest_node(G, baslangic["lat"], baslangic["lon"])
        son = nearest_node(G, hedef["lat"], hedef["lon"])
    except Exception:
        return {"cizgi": None, "maliyet": None,
                "arama": {"dijkstra": {"maliyet": None, "sureSn": None},
                          "astar": {"maliyet": None, "sureSn": None}, "ayniYol": None}}

    def _sn(u, v, k, d):
        h = float(d.get("hizKmh") or 30.0)
        return d.get("length", 0.0) / (h / 3.6)

    sonuc = {}
    for ad, a_yildiz in (("dijkstra", False), ("astar", True)):
        t0 = time.perf_counter()
        maliyet, dugumler, _kenarlar, _sayac = donus.en_kisa_yol(
            G, bas, son, _sn, yonler=yonler, a_yildiz=a_yildiz)
        sonuc[ad] = {
            "maliyet": round(maliyet, 2) if maliyet is not None else None,
            "sureSn": round(time.perf_counter() - t0, 4),
            "_dugumler": dugumler,
            "_kenarlar": _kenarlar,
        }
    d_d, a_d = sonuc["dijkstra"].pop("_dugumler"), sonuc["astar"].pop("_dugumler")
    d_k, a_k = sonuc["dijkstra"].pop("_kenarlar"), sonuc["astar"].pop("_kenarlar")
    dugumler = d_d or a_d
    # Cizgi KENARLARIN GERCEK GEOMETRISINDEN kurulur, dugumleri duz
    # birlestirerek degil (gerekcesi `_kenarlardan_cizgi`de).
    cizgi = _kenarlardan_cizgi(G, d_k or a_k)
    return {
        "cizgi": cizgi,
        "_donusMaliyetli": True,
        "maliyet": sonuc["dijkstra"]["maliyet"] if sonuc["dijkstra"]["maliyet"] is not None
                   else sonuc["astar"]["maliyet"],
        "arama": {**sonuc,
                  "ayniYol": (d_d == a_d) if (d_d is not None and a_d is not None) else None},
    }


def son_adim_yurume(G, baslangic, hedef):
    """Aracin gidebildigi en yakin nokta + kalan mesafe yaya.

    Kapali yollar yuzunden arac hic gidemiyorsa "ulasilamaz" demek gercekci
    degil: ekip aracla gidebildigi yere kadar gider, kalan kismi yurur. Bu
    fonksiyon `safe_G` uzerinde ekipten ULASILABILIR butun dugumleri bulur
    (tek kaynakli Dijkstra) ve afetzedeye kus ucusu en yakin olani secer.

    Donus: (cizgi, arac_mesafesi_m, yurume_mesafesi_m) ya da (None, None, None).
    """
    import networkx as nx

    kaynak = nearest_node(G, baslangic["lat"], baslangic["lon"])
    try:
        uzakliklar = nx.single_source_dijkstra_path_length(G, kaynak, weight="length")
    except Exception:
        return None, None, None
    if not uzakliklar:
        return None, None, None
    en_iyi, en_yakin = None, float("inf")
    for dugum in uzakliklar:
        d = G.nodes[dugum]
        mesafe = haversine(d["y"], d["x"], hedef["lat"], hedef["lon"])
        if mesafe < en_yakin:
            en_yakin, en_iyi = mesafe, dugum
    if en_iyi is None:
        return None, None, None
    varis = G.nodes[en_iyi]
    hat, _a, maliyet, _am = calculate_route(
        G, baslangic["lat"], baslangic["lon"], varis["y"], varis["x"],
        weight="length", algorithms=("dijkstra",),
    )
    return hat, (_hat_uzunlugu(hat) if hat else None), round(en_yakin, 1)


def _hat_uzunlugu(hat):
    if not hat:
        return None
    return round(sum(
        haversine(hat[i][0], hat[i][1], hat[i + 1][0], hat[i + 1][1])
        for i in range(len(hat) - 1)
    ), 1)


def _sure_dk(uzunluk_m, hiz_kmh):
    if uzunluk_m is None:
        return None
    return round(uzunluk_m / 1000.0 / hiz_kmh * 60.0, 1)


def _varyant_suresi(olcum, uzunluk_m, hiz_kmh):
    """Bir rota varyantinin suresi (dk).

    DONUS MALIYETLI aramada sure, aramanin KENDI maliyetinden gelir: o maliyet
    kenar hizlarini (`maxspeed` / yol sinifi, 20-70 km/sa) ve donus surelerini
    zaten icerir. Uzunlugu duz bir hiza bolmek AYNI YOLCULUK ICIN IKINCI BIR
    SURE uretiyordu -- olculdu (27 Eylul): kiyas kollari kenar hizlariyla,
    ekrandaki gorev ETA'si duz 15 km/sa ile hesaplaniyordu ve ikisi ~2 kat
    ayrisiyordu. Makaleye giren sayi ile ekrandaki sayi ayni olmali.

    Donus maliyeti kapaliysa eski davranis surer (uzunluk / duz hiz).
    """
    if olcum and olcum.get("maliyet") is not None and olcum.get("_donusMaliyetli"):
        return round(float(olcum["maliyet"]) / 60.0, 1)
    return _sure_dk(uzunluk_m, hiz_kmh)


def rota_kosusu(tam_G, guvenli_G, ekip_listesi, afetzede_listesi, hasar_noktalari=None,
                hiz_kmh=15.0, ceza_yaricapi_m=0.0, ekranda=5, donus_maliyetli=True):
    """Butun ekip x afetzede ciftlerini uc varyantta kosar.

    EKRANDA `ekranda` kadar gorev gosterilir (ekip i -> afetzede i), ama OLCUM
    butun ciftlerden gelir: 5 rotadan cikan "yol %18 uzadi" sayisi gurultudur,
    25 cift ise dagilim verir (A* 13 ms, maliyeti yok).
    """
    riskli_G = None
    if hasar_noktalari:
        try:
            riskli_G = apply_risk_penalties(
                guvenli_G.copy(), hasar_noktalari, blockage_hard_radius_m=ceza_yaricapi_m,
            )
        except Exception:
            riskli_G = None

    # Donus yonleri BIR KEZ hesaplanir; her OD cifti icin yeniden cikarmak
    # 25 cift x iki arama = 50 kez ayni isi yapmak olurdu.
    yonler = None
    if donus_maliyetli:
        from apps.road_damage.utils import donus as _d
        try:
            yonler = _d.kenar_yonleri(tam_G)
        except Exception:
            yonler = None

    gorevler, olcum_satirlari = [], []
    for i, ekip in enumerate(ekip_listesi):
        for j, afetzede in enumerate(afetzede_listesi):
            oncesi = _rota_olc(tam_G, ekip, afetzede, "length", yonler=yonler)
            kapanmali = _rota_olc(guvenli_G, ekip, afetzede, "length", yonler=yonler)
            riskli = (_rota_olc(riskli_G, ekip, afetzede, "risk_cost")
                      if riskli_G is not None else None)

            o_uz = _hat_uzunlugu(oncesi["cizgi"])
            k_uz = _hat_uzunlugu(kapanmali["cizgi"])
            r_uz = _hat_uzunlugu(riskli["cizgi"]) if riskli else None

            # Arac hic giremiyorsa "ulasilamaz" demek gercekci degil: ekip
            # gidebildigi yere kadar surer, kalani yurur. Olculdu (25 Eylul,
            # Maxar katmani): 25 ciftin 15'inde arac rotasi yoktu; hepsinde
            # enkazin kenarina kadar arac yolu var, kalan son adim yaya.
            yurume_m = None
            if k_uz is None:
                y_hat, y_arac_m, y_yurume_m = son_adim_yurume(guvenli_G, ekip, afetzede)
                if y_hat is not None:
                    kapanmali = {**kapanmali, "cizgi": y_hat}
                    k_uz, yurume_m = y_arac_m, y_yurume_m

            olcum_satirlari.append({
                "ekipId": ekip["id"], "afetzedeId": afetzede["id"],
                "oncesiM": o_uz, "kapanmaliM": k_uz, "riskliM": r_uz,
                # SURE de tasinir: rotalar SUREYE gore seciliyor, uzunluga
                # gore degil. Yalniz metreye bakmak yaniltiyordu -- guvenli
                # cizge tam cizgenin ALT KUMESI oldugu halde "kapanmali" rota
                # griden KISA cikabiliyor (olculdu: 400 m ile 449 m), cunku
                # kisa olan yol daha yavas. Uzama artik ikisinde de verilir.
                "oncesiDk": _varyant_suresi(oncesi, o_uz, hiz_kmh),
                "kapanmaliDk": _varyant_suresi(kapanmali, k_uz, hiz_kmh),
                "yurumeM": yurume_m,
                "ulasilamadi": k_uz is None,
            })

            if i == j and len(gorevler) < ekranda:
                gorevler.append({
                    "id": f"g{i + 1}",
                    "ekipId": ekip["id"], "ekipAd": ekip["ad"], "gercekTesis": True,
                    "afetzedeId": afetzede["id"], "afetzedeAd": afetzede["ad"], "senaryo": True,
                    "baslangic": {"lat": ekip["lat"], "lon": ekip["lon"], "ad": ekip["ad"]},
                    "hedef": {"lat": afetzede["lat"], "lon": afetzede["lon"], "ad": afetzede["ad"]},
                    "varyantlar": {
                        "depremOncesi": {"cizgi": oncesi["cizgi"], "uzunlukM": o_uz,
                                         "sureDk": _varyant_suresi(oncesi, o_uz, hiz_kmh)},
                        "kapanmali": {"cizgi": kapanmali["cizgi"], "uzunlukM": k_uz,
                                      "sureDk": _varyant_suresi(kapanmali, k_uz, hiz_kmh)},
                        "riskli": ({"cizgi": riskli["cizgi"], "uzunlukM": r_uz,
                                    "sureDk": _varyant_suresi(riskli, r_uz, hiz_kmh)}
                                   if riskli else None),
                    },
                    "arama": {
                        "dijkstra": {"uzunlukM": k_uz, "sureSn": kapanmali["arama"]["dijkstra"]["sureSn"]},
                        "astar": {"uzunlukM": k_uz, "sureSn": kapanmali["arama"]["astar"]["sureSn"]},
                        "ayniYol": kapanmali["arama"]["ayniYol"],
                    },
                    "etaDk": _varyant_suresi(kapanmali, k_uz, hiz_kmh),
                    # Araç son noktaya giremiyorsa kalan mesafe yaya (5 km/sa).
                    "sonAdimYurumeM": yurume_m,
                    "sonAdimYurumeDk": _sure_dk(yurume_m, 5.0) if yurume_m else None,
                    "durum": "atandi",
                })

    # Uzama YALNIZ tam arac rotasi olan ciftlerden hesaplanir. Yurume yedegi
    # devreye girdiginde `kapanmaliM` hedefe degil, aracin gidebildigi en yakin
    # noktaya olan mesafedir -- bu KISMI mesafeyi tam rotalarla ayni ortalamaya
    # katmak metrigi bozuyordu: olculdu (25 Eylul), r_h = 0'da uzama %8,7,
    # r_h = 10'da %3,4 cikiyordu, yani yaricap buyudukce uzama azaliyor
    # goruntusu veriyordu. Yurume gereken ciftler ayri sayilir.
    tam = [s for s in olcum_satirlari
           if s["kapanmaliM"] is not None and s["oncesiM"] and not s.get("yurumeM")]
    uzamalar = [(s["kapanmaliM"] - s["oncesiM"]) for s in tam]
    oranlar = [(s["kapanmaliM"] - s["oncesiM"]) / s["oncesiM"] for s in tam]
    # SUREYE gore uzama: asil olculmesi gereken bu, cunku rota sureye gore
    # seciliyor. Metre cinsinden uzama tutarli bir sekilde raporlanmaya devam
    # ediyor ama tek basina okunmamali.
    tam_sure = [s for s in tam if s.get("oncesiDk") and s.get("kapanmaliDk") is not None]
    uzama_dk = [(s["kapanmaliDk"] - s["oncesiDk"]) for s in tam_sure]
    oran_dk = [(s["kapanmaliDk"] - s["oncesiDk"]) / s["oncesiDk"] for s in tam_sure]
    return {
        "gorevler": gorevler,
        "olcum": {
            "ciftSayisi": len(olcum_satirlari),
            # Uzama ortalamasının kaç çift üzerinden alındığı: yürüme gerektiren
            # çiftler dışarıda kalır, bu yüzden bu sayı ciftSayisi'ndan küçüktür.
            "uzamaHesabindakiCift": len(uzamalar),
            "ortalamaUzamaM": round(sum(uzamalar) / len(uzamalar), 1) if uzamalar else None,
            "ortalamaUzamaYuzde": round(100 * sum(oranlar) / len(oranlar), 1) if oranlar else None,
            "enBuyukUzamaM": round(max(uzamalar), 1) if uzamalar else None,
            # Rota SUREYE gore seciliyor; asil uzama olcutu budur.
            "ortalamaUzamaDk": round(sum(uzama_dk) / len(uzama_dk), 2) if uzama_dk else None,
            "ortalamaUzamaSureYuzde": (round(100 * sum(oran_dk) / len(oran_dk), 1)
                                       if oran_dk else None),
            "enBuyukUzamaDk": round(max(uzama_dk), 2) if uzama_dk else None,
            "ulasilamayanCift": sum(1 for s in olcum_satirlari if s["ulasilamadi"]),
            "yurumeGerekenCift": sum(1 for s in olcum_satirlari if s.get("yurumeM")),
            "ortalamaYurumeM": (round(sum(s["yurumeM"] for s in olcum_satirlari if s.get("yurumeM"))
                                      / max(1, sum(1 for s in olcum_satirlari if s.get("yurumeM"))), 1)
                                if any(s.get("yurumeM") for s in olcum_satirlari) else None),
            # Donus maliyetli aramada sureler KENAR HIZLARINDAN gelir; duz hiz
            # yalnizca son adim yurume ve donussuz kip icindir. Ekran hangisinin
            # kullanildigini yazabilsin diye ikisi de doner (kural 1).
            "hizKmh": hiz_kmh,
            "kenarHizlari": bool(yonler is not None),
            "satirlar": olcum_satirlari,
        },
    }

def goruntu_eksik_mi(sonuc, alan_kunyesi, pay=0.7):
    """Goruntu beklenenden AZ mi indi? (None = sorun yok, str = uyari)

    NEDEN (olculdu, 26 Eylul). Ayni alan ayni modelle arka arkaya kosuldu ve
    bir kosuda kapsama %44,1 yerine %13,9, kapali kenar 26 yerine 6 cikti.
    Sebep gecici karo indirme hatasi: goruntunun bir bolumu bos geldi, hasar
    ve kapanma da onunla birlikte dustu. Kosu HATA VERMEDI, sessizce daha
    zayif bir sonuc uretti -- olcumu bozan tam olarak bu.

    Alan katalogu her alanin ucus izi DOLULUGUNU olcerek saklar; kosudaki
    gecerli piksel orani bunun cok altina duserse goruntu eksik inmistir.
    """
    # Referans ANALIZ ZOOM'undaki oran olmali. Once tarama zoom'undaki
    # `doluluk` kullanildi ve saglam kosu reddedildi (Defne: z16'da %59,
    # z18'de kararli %39). Katalogda z18 olcumu yoksa kontrol atlanir --
    # yanlis alarm, kacirilan uyaridan kotudur.
    beklenen = (alan_kunyesi or {}).get("gecerliPikselOraniZ18")
    gercek = (sonuc or {}).get("validPixelRatio")
    if beklenen is None or gercek is None:
        return None
    if gercek < beklenen * pay:
        return (f"Goruntu eksik indi: gecerli piksel %{gercek*100:.0f}, "
                f"bu alanda olculen %{beklenen*100:.0f}. Kosu tekrarlanmali.")
    return None
