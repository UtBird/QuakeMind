import hashlib
import math
import os
import pickle
import weakref
from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
from shapely.geometry import LineString

# Overpass (canli) tamamen erisilemez oldugu donemler icin yerel yedek: bir
# kez indirilmis Turkiye OSM PBF'i (D: -- boyutu ~611MB, C: diskinde yer
# yoktu) uzerinden pyrosm ile SADECE istenen kucuk bbox'i cikarip
# osmnx-uyumlu bir networkx grafi olusturuyoruz. Bu, Overpass'a hic
# bagimli degil -- tek seferlik pyrosm cikarimi ~230sn surebiliyor (PBF'in
# tamami taraniyor), bu yuzden onceden (benchmark/warm_local_graph_cache.py)
# bilinen konumlar icin pickle'lanip cache'leniyor; canli cagrida sadece
# cache'ten hizli yukleme yapiliyor (build DEGIL) -- worker.py'nin 45sn'lik
# dis timeout'unu asmamak icin.
# Kapanmaya varan ekibin kaybettigi sure, iki ayrisik bilesen (dakika).
# BEYAN EDILEN tasarim parametreleridir (olcum degil); duyarliligi tatbikat
# raporunda ayrica verilir. Manevra suresi donus.py'deki U donusu maliyetiyle
# ayni olsun diye oradan okunur.
DEGERLENDIRME_DK = 1.0
try:
    from apps.road_damage.utils.donus import DONUS_SN as _DONUS_SN
    MANEVRA_DK = _DONUS_SN["u"] / 60.0
except Exception:  # donus.py yoksa makul bir taban
    MANEVRA_DK = 25.0 / 60.0

LOCAL_PBF_PATH = os.environ.get("QUAKEMIND_LOCAL_OSM_PBF", "D:/quakemind_osm_data/turkey-latest.osm.pbf")
LOCAL_GRAPH_CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "osm_graph_cache"


# pyrosm'un network_type sozlugu osmnx'ten farkli isimler kullanir ('driving'
# vs 'drive' gibi) -- canli Overpass yolundaki (fetch_osm_road_graph) osmnx
# stiliyle tutarli kalinsin diye burada tek bir yerde eslenir.
_PYROSM_NETWORK_TYPE = {"drive": "driving", "walk": "walking", "bike": "cycling", "all": "all"}


def _local_graph_cache_path(bounds, network_type: str = "drive") -> Path:
    raw = ",".join(f"{v:.5f}" for v in bounds)
    # 'drive' TARIHSEL varsayilandi -- mevcut on-isitilmis cache dosyalarinin
    # (osm_graph_cache/*.pkl) gecersiz kalmamasi icin sadece 'drive' DISINDAKI
    # network_type'lar anahtara eklenir, 'drive' anahtari eskisiyle birebir ayni kalir.
    if network_type != "drive":
        raw += f":{network_type}"
    key = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return LOCAL_GRAPH_CACHE_DIR / f"{key}.pkl"


def load_local_graph_from_cache(bounds, network_type: str = "drive"):
    """Sadece onceden pre-warm edilmis (bkz. warm_local_graph_cache.py)
    pickle dosyasini okur -- hicbir zaman canli PBF taramasi baslatmaz."""
    path = _local_graph_cache_path(bounds, network_type)
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def build_local_graph_from_pbf(bounds, network_type: str = "drive", cache: bool = True):
    """PBF'ten canli cikarim yapar (~230sn surebilir) -- SADECE onceden
    calistirilan pre-warm script'i icin, canli istek yolunda DEGIL."""
    from pyrosm import OSM

    west, south, east, north = bounds
    osm = OSM(LOCAL_PBF_PATH, bounding_box=[west, south, east, north])
    pyrosm_type = _PYROSM_NETWORK_TYPE.get(network_type, network_type)
    nodes, edges = osm.get_network(network_type=pyrosm_type, nodes=True)
    if nodes is None or edges is None or nodes.empty or edges.empty:
        raise RuntimeError("Yerel PBF'te bu bbox icin yol verisi bulunamadi.")
    G = osm.to_graph(nodes, edges, graph_type="networkx")
    if cache:
        LOCAL_GRAPH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_local_graph_cache_path(bounds, network_type), "wb") as f:
            pickle.dump(G, f)
    return G

# Without an explicit cap, osmnx falls back to its own default Overpass
# timeout/retry policy, which can wait far longer than the mobile client's
# fixed 300s HTTP timeout for /api/road_damage/analyze -- the backend
# eventually finishes and logs success, but the request already timed out
# on the phone. Cache responses so repeated analyses of the same area don't
# re-hit Overpass at all.
ox.settings.use_cache = True
ox.settings.requests_timeout = 30

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# ox.distance.nearest_nodes, HER cagrida grafin tum dugumlerinden yeni bir
# dizi + BallTree uretir -- olculdu: ilk cagri 0,265sn, sonraki cagrilar
# 0,088sn (18.004 dugumlu graf). Rota hesabi ve naif-ajan karsilastirmasi
# nokta basina iki kez cagirdigi icin tek bir senaryo kosumunda ~70 cagri
# ediyor, yani ~6sn yalnizca AYNI agaci tekrar tekrar kurmaya gidiyordu.
# Agac grafa GORE bir kez kurulup zayif referansla (graf cop toplandiginda
# kendiliginden dusen) saklanir. Metrik osmnx'in kendi projeksiyonsuz-graf
# yolunun BIREBIR aynisidir (radyan haversine BallTree), dolayisiyla
# dondurulen dugum de aynidir.
_NODE_INDEX_CACHE: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _node_index(G):
    entry = _NODE_INDEX_CACHE.get(G)
    if entry is not None:
        return entry

    from sklearn.neighbors import BallTree

    node_ids = list(G.nodes)
    coords = np.deg2rad(
        np.array([[G.nodes[n]['y'], G.nodes[n]['x']] for n in node_ids], dtype=float)
    )
    entry = (node_ids, BallTree(coords, metric='haversine'))
    _NODE_INDEX_CACHE[G] = entry
    return entry


def nearest_node(G, lat, lon):
    """ox.distance.nearest_nodes'un onbellekli esdegeri."""
    node_ids, tree = _node_index(G)
    _, idx = tree.query(np.deg2rad([[float(lat), float(lon)]]), k=1)
    return node_ids[int(idx[0][0])]


def calculate_route(G, start_lat, start_lon, end_lat, end_lon, weight='length',
                    algorithms=('dijkstra', 'astar')):
    """weight='length' (default) preserves the plain shortest-path behavior
    used by /api/road_damage/route. Pass weight='risk_cost' (after running
    apply_risk_penalties on G) to get a risk-aware route instead.

    `algorithms` hangi arama(lar)in KOSULACAGINI secer. Eskiden ikisi de
    kosulurdu ve /route yalnizca Dijkstra sonucunu kullanip A* sonucunu
    ATIYORDU -- olculdu: Dijkstra 0,039sn, A* 0,013sn, ikisi de AYNI yolu
    buluyor (haversine sezgisi kabul edilebilir oldugu icin A*'in optimalligi
    garantilidir). /safe_route ikisini bilerek KARSILASTIRDIGI icin varsayilan
    degismedi; tek algoritma isteyen cagrilar algorithms=('astar',) gecer ve
    kullanilmayan aramanin bedelini odemez.
    """
    start_node = nearest_node(G, start_lat, start_lon)
    end_node = nearest_node(G, end_lat, end_lon)

    def astar_heuristic(u, v):
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        return haversine(u_node['y'], u_node['x'], v_node['y'], v_node['x'])

    path_dijkstra = None
    if 'dijkstra' in algorithms:
        try:
            path_dijkstra = nx.shortest_path(G, start_node, end_node, weight=weight)
        except nx.NetworkXNoPath:
            path_dijkstra = None

    path_astar = None
    if 'astar' in algorithms:
        try:
            path_astar = nx.astar_path(G, start_node, end_node, heuristic=astar_heuristic, weight=weight)
        except nx.NetworkXNoPath:
            path_astar = None

    def get_route_line(path):
        if not path:
            return None
        route_coords = []
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            edge_data = min(G[u][v].values(), key=lambda d: d.get('length', float('inf')))
            if 'geometry' in edge_data:
                coords = [(lat, lon) for lon, lat in edge_data['geometry'].coords]
                # pyrosm/osmnx grafiklerinde bir kenarin geometry LineString'i
                # HER ZAMAN (u,v) yonunde saklanmis olmayabilir -- bazi
                # kenarlarda OSM way'in orijinal cizim yonu (v,u) ise,
                # geometry TERS kaydedilir. Bunu varsaymadan duz eklemek,
                # ardisik kenarlar arasinda GERCEKTE OLMAYAN buyuk bir
                # "sicrama" yaratiyordu (bir kenarin sonundan, bir sonraki
                # kenarin YANLIS ucuna atlama) -- bu da rotanin gercek
                # (safe_G uzerindeki en kisa) mesafeden onemli olcude daha
                # uzun gorunmesine yol aciyordu. Duzeltme: geometrinin
                # baslangic noktasi v'ye u'dan daha yakinsa, listeyi ters
                # cevirerek ekle.
                u_node, v_node = G.nodes[u], G.nodes[v]
                start_to_u = haversine(coords[0][0], coords[0][1], u_node['y'], u_node['x'])
                start_to_v = haversine(coords[0][0], coords[0][1], v_node['y'], v_node['x'])
                if start_to_v < start_to_u:
                    coords = coords[::-1]
                route_coords.extend(coords)
            else:
                route_coords.extend([(G.nodes[u]['y'], G.nodes[u]['x']), (G.nodes[v]['y'], G.nodes[v]['x'])])
        return route_coords

    def get_route_cost(path):
        if not path:
            return None
        total = 0.0
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge_data = min(G[u][v].values(), key=lambda d: d.get(weight, float('inf')))
            total += edge_data.get(weight, 0.0)
        return total

    return (
        get_route_line(path_dijkstra),
        get_route_line(path_astar),
        get_route_cost(path_dijkstra),
        get_route_cost(path_astar),
    )


def risk_weight(min_dist_m):
    """Basamaklı ceza kademesi: bir kenarın en yakın hasar/tehlike noktasına
    uzaklığına göre 'length' üzerine uygulanacak çarpan."""
    if min_dist_m < 50:
        return 3.0
    if min_dist_m < 150:
        return 1.5
    if min_dist_m < 400:
        return 1.1
    return 1.0


def _edge_midpoint(G, u, v, data):
    if 'geometry' in data:
        coords = list(data['geometry'].coords)
        mid_lon, mid_lat = coords[len(coords) // 2]
        return mid_lat, mid_lon
    u_node = G.nodes[u]
    v_node = G.nodes[v]
    return (u_node['y'] + v_node['y']) / 2.0, (u_node['x'] + v_node['x']) / 2.0


def _as_latlon_list(items):
    """Normalizes damage_points/blockages (dicts with lat/lon, [lat, lon]
    pairs, or [[lat, lon], ...] polylines) into a flat list of (lat, lon)."""
    points = []
    for item in items or []:
        if isinstance(item, dict):
            lat, lon = item.get('lat'), item.get('lon')
            if lat is not None and lon is not None:
                points.append((float(lat), float(lon)))
        elif isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], (int, float)):
            points.append((float(item[0]), float(item[1])))
        elif isinstance(item, (list, tuple)) and item:
            # A blockage polyline ([[lat, lon], ...]) -- use its midpoint.
            mid = item[len(item) // 2]
            points.append((float(mid[0]), float(mid[1])))
    return points


def apply_risk_penalties(G, damage_points, blockages=None, blockage_hard_radius_m=25.0):
    """Kapalı yol maskeleri + yıkım yoğunluğu + tehlikeli noktaları tek bir
    ceza-katsayılı grafta birleştirir (mutates G in place, returns G).

    - `blockages` içindeki her noktaya `blockage_hard_radius_m` metre içinde
      kalan kenarlar tamamen kaldırılır (hard-block).
    - Kalan her kenara `risk_cost = length * risk_weight(min_dist_to_damage_point)`
      atanır.

    Mesafe aramasi VEKTORIZE'dir. Eskiden her kenar icin TUM hasar noktalarina
    ve TUM kapanma noktalarina tek tek saf-Python `haversine` cagriliyordu,
    yani O(kenar x nokta). Kucuk nokta kumelerinde bu gizli kaliyordu; EMSR648
    gercek hasar katmani baglandiginda (394 + 927 hasarli bina) 39 285 kenar x
    1 321 nokta ~ 52 MILYON haversine cagrisi demek olacakti. Onun yerine nokta
    kumelerinden birer BallTree (radyan haversine -- kurenin uzerinde gercek
    buyuk-daire mesafesi, `haversine()` ile ayni R = 6 371 000 m) kurulur ve tum
    kenar orta noktalari TEK toplu sorguda islenir.
    """
    damage_coords = _as_latlon_list(damage_points)
    blockage_coords = _as_latlon_list(blockages)

    edges = list(G.edges(keys=True, data=True))
    if not edges:
        return G

    midpoints = np.empty((len(edges), 2), dtype=float)
    for i, (u, v, _key, data) in enumerate(edges):
        midpoints[i] = _edge_midpoint(G, u, v, data)
    midpoints_rad = np.deg2rad(midpoints)

    def _nearest_distances_m(points):
        """Her kenar orta noktasi icin `points` kumesindeki en yakin noktaya
        metre cinsinden buyuk-daire mesafesi."""
        from sklearn.neighbors import BallTree

        tree = BallTree(np.deg2rad(np.asarray(points, dtype=float)), metric='haversine')
        distances, _ = tree.query(midpoints_rad, k=1)
        return distances[:, 0] * 6371000.0

    if blockage_coords:
        blocked_mask = _nearest_distances_m(blockage_coords) <= blockage_hard_radius_m
    else:
        blocked_mask = np.zeros(len(edges), dtype=bool)

    if damage_coords:
        min_distances = _nearest_distances_m(damage_coords)
    else:
        min_distances = np.full(len(edges), float('inf'))

    edges_to_remove = []
    for i, (u, v, key, data) in enumerate(edges):
        if blocked_mask[i]:
            edges_to_remove.append((u, v, key))
            continue
        # float() sarmalayicilari SART: numpy skalerleri JSON'a serilestirilemez
        # ve risk_cost, /safe_route'un dondurdugu `riskScore`'a kadar tasiniyor.
        data['risk_cost'] = float(data.get('length', 0.0)) * risk_weight(float(min_distances[i]))

    for u, v, key in edges_to_remove:
        if G.has_edge(u, v, key):
            G.remove_edge(u, v, key)

    return G

# osmnx varsayılan olarak TEK bir sabit Overpass sunucusuna (overpass-api.de)
# bağlanır ve yedek sunucusu yoktur -- bu sunucu yoğun/erişilemez olduğunda
# (gözlemlenen: connect timeout=30, ~100sn'de exception) tüm lojistik analizi
# sessizce boş dönüyordu. get_osm_roads_overpass (fetcher.py) zaten aynı sorun
# için çoklu-ayna (mirror) fallback kullanıyor -- aynı deseni burada da
# uyguluyoruz.
_OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api",
    "https://overpass.kumi.systems/api",
    "https://lz4.overpass-api.de/api",
    "https://overpass.private.coffee/api",
]


def fetch_osm_road_graph(bounds, network_type='drive'):
    """Gercek OSM yol grafigini ceker: once yerel pre-warm cache (ms
    mertebesinde), yoksa cok-ayna Overpass fallback. `analyze_road_network_graph`
    (SegFormer hasar kesisimi) ve `simulate_random_closures` (rastgele
    kapanma simulasyonu, worker.py'de fastapi_app.py) ikisi de bu tek
    fonksiyonu paylasir -- graf edinme mantigi tek bir yerde.

    Bunu Overpass denemesinden ONCE cache'e bakarak yapiyoruz cunku canli
    Overpass, DNS cozumlemesi seviyesinde donabiliyor -- requests_timeout
    SADECE soket connect/read fazini kapsiyor, DNS asamasini kapsamiyor, bu
    yuzden 4 ayna x 10sn = 40sn hedeflesek de gercekte 300sn+ surebiliyor
    (bkz. oturum notlari)."""
    G = load_local_graph_from_cache(bounds, network_type)
    if G is not None:
        print(f"OSMnx: yerel PBF cache'inden yuklendi ({G.number_of_nodes()} dugum), Overpass'a hic gidilmedi.")
        return G, None

    # Bolge dosyasi (araclar_yerel_osm_kur.py). Onbellek anahtari kutunun TAM
    # esitligine bagli oldugu icin tatbikatin her kosusunda isabet etmiyor --
    # kutu ekip/afetzede konumlarindan turedigi icin biraz oynuyor. Bolge
    # dosyasi herhangi bir kutuyu karsilayabilir ve Overpass'a hic gitmez.
    if network_type == "drive":
        try:
            from apps.road_damage.utils import yerel_yol
            if yerel_yol.veri_var():
                Gy = yerel_yol.graf(bounds)
                if Gy.number_of_edges() > 0:
                    print(f"Yol agi yerel bolge dosyasindan ({Gy.number_of_nodes()} dugum).")
                    return Gy, None
        except Exception as e:
            print(f"Yerel bolge dosyasi okunamadi: {type(e).__name__}: {e}")

    last_error = None
    original_timeout = ox.settings.requests_timeout
    ox.settings.requests_timeout = 10
    try:
        for endpoint in _OVERPASS_ENDPOINTS:
            try:
                ox.settings.overpass_endpoint = endpoint
                # 'drive' varsayılanı araç lojistiği için; yaya tahliye rotası 'walk' geçer
                G = ox.graph_from_bbox(bbox=bounds, network_type=network_type, simplify=True)
                return G, None
            except Exception as e:
                last_error = e
                continue
    finally:
        ox.settings.requests_timeout = original_timeout

    return None, last_error


def simulate_random_closures(bounds, closure_ratio=0.15, network_type='drive', seed=None):
    """`analyze_road_network_graph`'in SegFormer/hasar-maskesi olmayan
    versiyonu: gercek bir OSM yol grafigi ceker, kenarlarin rastgele
    closure_ratio kadarini 'kapali' isaretler. Senkron ve hizli (worker
    pool gerektirmez) -- canli CV modeli calistirmadan, gercek senaryo
    kurgusu icin (bkz. oturum notlari: kullanicinin onayladigi basitlestirme).

    Kapatma miktari, kapatma SONRASI grafin en buyuk GUCLU-BAGLI (strongly
    connected) bileseninin dugumlerin en az %92'sini kapsamasini saglayacak
    sekilde otomatik ayarlanir (istenen closure_ratio'dan baslayip, yetersiz
    kalirsa yarilanarak birkac kez yeniden dener). Deneysel olarak
    dogrulandi: tamamen rastgele secim (kisitlamasiz), dar/tek-yonlu sokak
    agirlikli gercek sehir topolojilerinde %18 gibi dusuk bir oranda bile
    grafi 287 parcaya bolup rota motorunu (Dijkstra/A*) HICBIR ZAMAN
    calistiramaz hale getiriyordu (18004 dugumlu Kahramanmaras grafinda
    dogrulandi) -- salt undirected spanning-tree korumasi da yetersiz kaldi
    (yonlu/tek-yonlu sokaklarda undirected baglantiligi korumak, yonlu
    erisilebilirligi garanti etmiyor). Bu yaklasim, rota motorunun HER ZAMAN
    (buyuk olasilikla) bir yol bulabilmesini saglar -- sadece HANGI yolun
    kapali oldugu rastgele kalir (kullanicinin istedigi basitlestirme budur,
    'rota bulunamiyor' hatasi degil)."""
    import random as _random

    G, error = fetch_osm_road_graph(bounds, network_type=network_type)
    if G is None:
        return None, None, None, None, error

    rng = _random.Random(seed)
    # G.edges(keys=True)'in dondurdugu SIRA, networkx'in ic adjacency dict'i
    # uzerinden gelir -- dugum ID'leri hashlenirken Python'un SURECE-OZGU
    # PYTHONHASHSEED'i devreye girebiliyor, yani AYNI seed ile rng.sample
    # cagrilsa bile FARKLI bir surecte (orn. bu API endpoint'i vs bagimsiz
    # bir dogrulama script'i) TAMAMEN FARKLI kenarlar secilebiliyordu --
    # deneysel olarak dogrulandi (ayni parametrelerle iki ayri surec, ayni
    # kapanma SAYISI ama FARKLI kenar KUMESI, bu da rota motorunun ayni
    # (bounds, seed) icin surece bagli farkli sonuclar vermesine yol
    # aciyordu). Ornekleme oncesi sabit bir siraya (u,v,key) gore sort
    # etmek, "ayni seed = ayni kapanma" garantisini surecler arasi da
    # gecerli kilar.
    all_edges = sorted(G.edges(keys=True))

    # KRITIK: iki-yonlu her sokak, MultiDiGraph'ta IKI AYRI yonlu kenar olarak
    # tutulur -- (u,v,k) ve onun fiziksel olarak AYNI yolu temsil eden ters
    # yonlu esi (v,u,k). Bunlari BAGIMSIZ tek tek ornekleyip sadece BIRINI
    # kapatirsak, rota motoru "kapali" isaretlenen yolu ters yonden gecen
    # hala-acik esini kullanarak fiilen o yoldan gecebiliyor -- haritada
    # kirmizi gorunen bir yoldan ekip rotasinin GECTIGI, kullanici tarafindan
    # gozlemlenip bildirilen gercek bir bug buydu (dogrulandi: pyrosm yerel
    # PBF-cache grafinde 40950 kenarin TAMAMI 20475 boyle cift olusturuyordu,
    # ve kapali secilen kenarlarin ~%99'unun ters-yonlu esi acik kalmisti).
    # Duzeltme: kapatma islemi kenar degil "fiziksel yol" (ayni dugum cifti +
    # ayni osmid) bazinda yapilir, secilen fiziksel yolun TUM yonlu kenar
    # kopyalari birlikte kapatilir.
    def _physical_road_key(u, v, k):
        osmid = G[u][v][k].get('osmid')
        if isinstance(osmid, list):
            osmid = tuple(sorted(str(o) for o in osmid))
        node_pair = f"{min(u, v)}:{max(u, v)}"
        return f"{node_pair}:{osmid}" if osmid is not None else f"{node_pair}:{u}-{v}-{k}"

    physical_groups: dict = {}
    for u, v, k in all_edges:
        physical_groups.setdefault(_physical_road_key(u, v, k), []).append((u, v, k))
    physical_keys = sorted(physical_groups.keys())

    # Esik, grafin KENDI baslangic baglantiligina GORE olculur -- mutlak
    # "tum dugumlerin %92'si" degil. Neden: gercek yaya/yol aglarinda pek cok
    # bolge zaten dogal olarak parcalidir (cikmaz sokaklar, tek yonlu
    # merdivenler, kopru/gecit topolojileri). Belen Gecidi grafinde en buyuk
    # guclu-bagli bilesen HICBIR kapanma olmadan bile toplam dugumlerin
    # %92'sinin altindaydi; mutlak esik bu yuzden 6 denemenin HEPSINDE
    # basarisiz oluyor ve fonksiyon sessizce SIFIR kapanma dondurüyordu
    # (dogrulandi: 18484 kenarli Belen grafinda 0 kapali segment).
    # Goreli esik, "kapanmalar mevcut baglantiligi ciddi olcude BOZMASIN"
    # seklindeki asil niyeti korur ve zaten parcali graflarda da calisir.
    base_scc_size = (len(max(nx.strongly_connected_components(G), key=len))
                     if G.number_of_nodes() else 0)
    connectivity_floor = base_scc_size * 0.92

    closed_keys: set = set()
    candidate_ratio = closure_ratio
    for _attempt in range(6):
        n_closed_roads = max(1, int(len(physical_keys) * candidate_ratio)) if physical_keys else 0
        n_closed_roads = min(n_closed_roads, len(physical_keys))
        trial_closed_roads = rng.sample(physical_keys, n_closed_roads) if n_closed_roads else []
        trial_closed = {edge for road_key in trial_closed_roads for edge in physical_groups[road_key]}

        # nx.restricted_view: kenarlari GIZLEYEN salt-okunur bir gorunum
        # dondurur, grafi KOPYALAMAZ. Onceden burada G.copy() vardi ve dongu
        # 6 kez calisabildigi icin 40.950 kenarlik bir MultiDiGraph'in tam
        # kopyasi arka arkaya 6 kez cikariliyordu -- backend'in bellegini
        # tuketip MemoryError'a dusuruyordu (olculdu: Antakya grafinda ilk
        # istekte cokme, ardindan 503). Gorunum ile ayni SCC hesabi bellekte
        # ek yer kaplamadan yapilir.
        trial_G = nx.restricted_view(G, [], trial_closed)
        largest_scc_size = len(max(nx.strongly_connected_components(trial_G), key=len)) if trial_G.number_of_nodes() else 0

        if not trial_closed or largest_scc_size >= connectivity_floor:
            closed_keys = trial_closed
            break
        candidate_ratio /= 2
    else:
        # 6 denemenin hepsi esigi gecemediyse ELI BOS DONME -- eskiden
        # closed_keys bos kaliyordu ve "kapanma yok" gibi gorunuyordu, ki bu
        # sessiz bir basarisizlik. Bunun yerine son (en kucuk) denemeyi
        # kullaniriz: az sayida da olsa gercek bir kapanma kumesi, hic
        # kapanma olmamasindan daha dogru bir sonuctur.
        closed_keys = trial_closed

    blocked_edges = []
    safe_edges = []
    for u, v, key in all_edges:
        data = G[u][v][key]
        line = data.get('geometry')
        if line is None:
            u_node, v_node = G.nodes[u], G.nodes[v]
            line = LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])
        target = blocked_edges if (u, v, key) in closed_keys else safe_edges
        target.append((u, v, key, line))

    # Burada da kopya yerine gorunum: safe_G yalnizca rota hesaplamak icin
    # OKUNUYOR, uzerinde degisiklik yapilmiyor. Ikinci bir tam graf kopyasi
    # cikarmak bellegi gereksiz yere ikiye katliyordu.
    safe_G = nx.restricted_view(G, [], {(u, v, k) for (u, v, k, _) in blocked_edges})

    return G, safe_G, safe_edges, blocked_edges, None


MAX_NAIVE_ITERATIONS = 60


def simulate_naive_agent(G, real_closed_edges: set, start_lat, start_lon, end_lat, end_lon):
    """Naive ajan: kapaliligi bilmiyor, en kisa yolu dener; bilinmeyen bir
    kapali kenara varinca onu 'ogrenir' ve o kavsaktan itibaren yeniden
    hesaplar. Toplam yuruncen mesafeyi (metre) ve 'ogrenilen' kapali kenar
    sayisini doner; yol bulunamazsa None doner.

    (Aslinda benchmark/naive_baseline.py'de tanimliydi -- BURAYA tasindi
    cunku naive-ajan karsilastirmasinin backend'in KENDI SURECINDE, session'da
    saklanan GERCEK G/real_closed_edges ile calismasi gerekiyordu: ayri bir
    Python surecinde (orn. bir benchmark script'i) simulate_random_closures'i
    AYNI seed/bounds/ratio ile TEKRAR cagirmak, TEORIDE deterministik olmasi
    beklenirken PRATIKTE surecler arasi FARKLI bir kapanma kumesi
    uretebiliyordu (nx.strongly_connected_components'in ic sira/hash
    davranisina bagli oldugu dusunuluyor) -- bu da naive-ajan karsilastirmasini
    GECERSIZ kilan (bazen naive'in bizim motordan 'daha kisa' cikmasi gibi
    imkansiz olmasi gereken sonuclar) bir sinif hataya yol aciyordu.)"""
    start_node = nearest_node(G, start_lat, start_lon)
    end_node = nearest_node(G, end_lat, end_lon)

    known_closed: set = set()
    current = start_node
    total_length = 0.0
    discoveries = 0
    # Naif ajanin FIILEN yurudugu koordinat izi -- haritada bizim rotamizla
    # karsilastirmali gosterebilmek icin (kullanicinin istedigi gorsel
    # kanit). calculate_route/get_route_line'daki ayni ters-geometri
    # duzeltmesi burada da uygulanir.
    route_coords: list = [(G.nodes[start_node]['y'], G.nodes[start_node]['x'])]

    for _ in range(MAX_NAIVE_ITERATIONS):
        # nx.restricted_view: kenarlari GIZLEYEN salt-okunur gorunum -- grafi
        # KOPYALAMAZ. Burada eskiden dongunun HER yinelemesinde G.copy()
        # vardi; olculdu: 39.285 kenarli MultiDiGraph'ta kopya 0,91sn,
        # gorunum 0,0001sn (~9000 kat). Tek bir senaryo kosumu 18 atama + 68
        # kesif = ~86 yineleme ettigi icin bu, ~78 SANIYE saf kopyalama
        # demekti. simulate_random_closures'ta ayni duzeltme zaten yapilmis
        # ve "kopya almaya geri donulmemeli" notu dusulmustu (bellek de
        # tukeniyordu) -- bu fonksiyon o gecişte atlanmisti.
        # Dongu G_view uzerinde hicbir degisiklik yapmadigi icin (yalnizca
        # shortest_path ve okuma) gorunum birebir ayni sonucu verir.
        hidden = {(u, v, k) for (u, v, k) in known_closed if G.has_edge(u, v, k)}
        G_view = nx.restricted_view(G, [], hidden) if hidden else G
        try:
            path = nx.shortest_path(G_view, current, end_node, weight="length")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        blocked_here = False
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            # DIKKAT: key, path'in FIILEN hesaplandigi G_view uzerinden
            # secilmeli, TAM graf G'den DEGIL. (u,v) arasinda birden fazla
            # paralel kenar varsa, G uzerinden 'en kisa' key secmek bazen
            # HENUZ BILINMEYEN (ama gercekte kapali) bir paralel kenari
            # secebiliyordu -- path aslinda G_view'deki (acik) baska bir
            # paralel kenari kullanmisken, mesafeye YANLISLIKLA o kapali
            # kenarin (genelde daha kisa oldugu icin secilen) uzunlugunu
            # ekliyor, hem de onu "kesfedilmis" sayip erken duruyordu. Bu,
            # naive ajanin bazen GERCEK motorumuzdan daha kisa/gecerli
            # gorunen ama ASLINDA path'in hic kullanmadigi bir kenara
            # dayanan yanlis bir mesafe bulmasina yol aciyordu.
            key = min(G_view[u][v], key=lambda k: G_view[u][v][k].get("length", float("inf")))
            if (u, v, key) in real_closed_edges:
                known_closed.add((u, v, key))
                known_closed.add((v, u, key))
                current = u
                blocked_here = True
                discoveries += 1
                break
            total_length += G[u][v][key].get("length", 0.0)
            edge_data = G[u][v][key]
            if 'geometry' in edge_data:
                coords = [(lat, lon) for lon, lat in edge_data['geometry'].coords]
                u_node, v_node = G.nodes[u], G.nodes[v]
                start_to_u = haversine(coords[0][0], coords[0][1], u_node['y'], u_node['x'])
                start_to_v = haversine(coords[0][0], coords[0][1], v_node['y'], v_node['x'])
                if start_to_v < start_to_u:
                    coords = coords[::-1]
                route_coords.extend(coords[1:])
            else:
                route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))
            current = v

        if not blocked_here:
            return {
                "distanceMeters": round(total_length, 1),
                "discoveries": discoveries,
                "routeCoords": route_coords,
            }

    return None  # cok fazla kesif dongusu -- pratikte yol bulunamadi kabul edilir


def _shortest_path_avoiding(G, source, target, hidden: set, penalized: set | None = None,
                            factor: float = 1.0, multiplier: dict | None = None):
    """nx.shortest_path(nx.restricted_view(G, [], hidden), ..., weight="length")
    ve ardindan ayni gorunumde en kisa paralel kenar secimi -- gorunum KURMADAN.

    Gizli kenar, agirlik fonksiyonunun None dondurmesiyle atlanir. networkx
    (3.6) iki nokta arasinda bidirectional_dijkstra kullanir ve geri yonde
    agirligi weight(w, v, d) ile, yani kenarin GERCEK yonuyle sorar; komsu
    sirasi ve esitlik bozma gorunumle aynidir. Esdegerlik her kosuda R0
    kontrolu ile dogrulanir (simulate_naive_agent gorunum kullanir).

    `penalized` verilirse bu kenarlar gizlenmez, uzunluklari `factor` ile
    carpilir (yumusak kapanma -- makale Denklem 8).

    `multiplier` verilirse her kenarin uzunlugu kendi carpaniyla carpilir
    (surekli yumusak maliyet: 1 + lambda * p(kenar)); verilmeyen kenar 1."""
    penalized = penalized or set()
    multiplier = multiplier or {}

    def cost(u, v, k, attr, default):
        w = attr.get("length", default)
        if multiplier:
            return w * multiplier.get((u, v, k), 1.0)
        return w * factor if (u, v, k) in penalized else w

    if hidden or penalized or multiplier:
        def weight(u, v, keydict):
            best = None
            for k, attr in keydict.items():
                if (u, v, k) in hidden:
                    continue
                w = cost(u, v, k, attr, 1)
                if best is None or w < best:
                    best = w
            return best
    else:
        weight = "length"
    path = nx.shortest_path(G, source, target, weight=weight)
    keys = []
    for u, v in zip(path, path[1:]):
        visible = [k for k in G[u][v] if (u, v, k) not in hidden]
        keys.append(min(visible, key=lambda k, u=u, v=v: cost(u, v, k, G[u][v][k], float("inf"))))
    return path, keys


def simulate_reference_fleet(G, real_closed_edges: set, tasks: list, sight_m: float = 0.0,
                             share: bool = False, speed_kmh: float = 15.0,
                             u_turn_penalty_min: float | None = None,
                             assessment_min: float = DEGERLENDIRME_DK,
                             manoeuvre_min: float = MANEVRA_DK,
                             turn_costs: bool = False,
                             edge_speeds: bool = False,
                             max_iterations: int = MAX_NAIVE_ITERATIONS,
                             pathfinder: str = "weight",
                             simultaneous_known: bool = True,
                             prior_closed: set | None = None,
                             prior_fallback: bool = True,
                             prior_penalty_factor: float | None = None,
                             prior_multiplier: dict | None = None) -> list:
    """Karsilastirma referanslari R0 / R1 / R2 (makale Bolum 3.8) -- tek bir
    zaman sirali simulasyon.

    Her ajan Algoritma 1'in ajanidir: kapanmalari bilmez, bildigi cizgede en
    kisa yolu izler, kapali kenara girmez, kapanmayi kavsakta ogrenir ve orada
    yeniden planlar. Iki anahtar onu R1/R2'ye cevirir:

      sight_m = 0, share = False -> R0. simulate_naive_agent ile BIREBIR ayni
          sonucu vermelidir (mesafe ve kesif sayisi) -- dogrulama bununla yapilir.
      sight_m > 0 -> R1 (gorus mesafeli ajan). Her kavsakta, planli yol uzerinde
          onundeki sight_m metre icinde BASLAYAN kapali kenarlari gorur. Ayni
          kavsakta gorulen kapanmalar TEK bir durum degerlendirmesidir: ceza
          (t_u) kesif basina degil durak basina islenir -- aksi halde daha cok
          gormek ajani cezalandirirdi. Gorus yol boyunca olculur (kose
          donusleri gorusu kesmez) -- R1 icin iyimser bir varsayim.
      share = True -> R2 (bilgi paylasan filo). Bir ajanin ogrendigi kapanma o
          anda ayni gorevler kumesindeki tum ajanlara yayilir. Telsizle ogrenilen
          kapanma ajanin planli yolundaysa ajan bir sonraki kavsakta CEZASIZ
          yeniden planlar (kapanmaya varmadi, durum degerlendirmesi yok).
          Ajanin kendi kesfi R0'daki gibi cezalidir.
      prior_closed -> ajan yola bu kenarlari KAPALI bilerek cikar (J-30: model
          bilgili ekip; prior = modelin kapanmalari, dunya = real_closed_edges =
          EMSR648). Yanlis alarmlar hic sorgulanmaz (ekip o yollara girmez);
          modelin kacirdigi gercek kapanmaya varinca kesfeder (t_u). prior =
          dunya ise R3 (kusursuz bilgi). Yanlis alarmlar hedefi baglantisiz
          birakirsa ("rota bulunamadi") prior_fallback=True iken ekip modeli
          birakir, kendi kesifleriyle R0 gibi devam eder (sonucta fallback=True).
      prior_penalty_factor -> prior kenarlari GIZLENMEZ, planlamada uzunluklari bu
          carpanla pahalilasir (yumusak kullanim; ag hicbir zaman kopmaz).
      prior_multiplier -> {kenar: carpan}. Surekli yumusak kullanim: her kenarin
          planlama maliyeti uzunluk x carpan (ornegin 1 + lambda * p, p = modelin
          o kenar icin kapanma olasiligi). Hicbir kenar gizlenmez; ekip yine
          yalniz dunyadaki gercek kapanmaya varinca kesfeder. prior_closed ve
          prior_penalty_factor ile birlikte kullanilmaz.

    Zaman yalniz paylasimda sonucu etkiler (kim once ogrendi): ajan saati
    L / v + ceza, olaylar saat sirasiyla islenir (en erken saatli ajan bir kenar
    ilerler). Ayni karargahtan ayni anda cikan ekipler ortak yol basinda ayni
    anda ilerler; simultaneous_known=True (varsayilan, "aninda yayilir"):
    baskasinin AYNI anda ogrendigi kapanma bilinir -- kafilede one dusen
    kesfeder, digerleri cezasiz yon degistirir. False: ayni anda varan her
    ajan kendisi kesfeder (duyarlilik; bu durumda R2 kafilede R0'a esitlenir).

    Donus: tasks ile ayni sirada, ulasilamayan gorev icin None.
    """
    import heapq

    # KAPANMAYA VARMANIN BEDELI. Eskiden tek bir sabitti (`u_turn_penalty_min`
    # = 20 dk) ve sonucu TEK BASINA belirliyordu: kapanma bilgisi olan ve
    # olmayan ekip arasindaki farkin %97,4'u bu sabitten geliyordu, yani olcum
    # aslinda sabitin kendisini olcuyordu. Simdi iki ayrisik ve beyan edilmis
    # sure var; asil bedel, ekibin fiilen fazladan surdugu yoldan gelir ve onu
    # cizge hesaplar.
    #   degerlendirme  ekip durur, kapanmayi gorur, telsizle bildirir
    #   manevra        donus manevrasinin kendisi (donus.py ile ayni deger)
    # Geriye donuk uyumluluk: eski betikler `u_turn_penalty_min` gonderirse o
    # deger aynen kullanilir (eski tablolar yeniden uretilebilsin diye).
    if u_turn_penalty_min is not None:
        kapanma_cezasi_dk = float(u_turn_penalty_min)
    elif turn_costs:
        # Donus maliyeti acikken manevra sabite AYRICA eklenmez (J-112): kapanmada
        # geri donen ekip yeniden planlamada `gelen_kenar` ile donusunu zaten oduyor
        # ve step() o donusun suresini saate isliyor. Eskiden sabite bir de 25 sn
        # manevra ekleniyordu, yani U donusu iki kez sayiliyordu. Simdi ceza yalniz
        # degerlendirme; manevra, ekibin fiilen yaptigi donusun kendi maliyetidir.
        kapanma_cezasi_dk = float(assessment_min)
    else:
        kapanma_cezasi_dk = float(assessment_min) + float(manoeuvre_min)

    # DONUS MALIYETI. Dugum tabanli arama kavsaga nasil girildigini bilmez ve
    # sola donusu saga donusle ayni fiyata alir; Turkiye'de trafik SAGDAN
    # aktigi icin bu yanlistir. `turn_costs=True` iken planlama kenar tabanli
    # aramaya (donus.en_kisa_yol) gecer ve saat de donus suresini isler.
    _donus = _yonler = None
    _vmax_ms = None
    if turn_costs:
        from apps.road_damage.utils import donus as _donus
        _yonler = _donus.kenar_yonleri(G)
        # A* sezgiseli icin en yuksek hiz: _kenar_dk ile AYNI kural (kenarin kendi
        # hizi, yoksa filo hizi). Bir kez hesaplanir; her yol hesabinda taranmaz.
        if edge_speeds:
            _hizlar = [float(d.get("hizKmh") or speed_kmh) for _, _, d in G.edges(data=True)]
            _vmax_ms = (max(_hizlar) if _hizlar else float(speed_kmh)) / 3.6
        else:
            _vmax_ms = float(speed_kmh) / 3.6

    per_stop = sight_m > 0
    min_per_m = 60.0 / (speed_kmh * 1000.0)

    def _kenar_dk(d):
        """Kenari gecme suresi (dk). `edge_speeds` ile kenarin kendi hizi
        kullanilir (maxspeed / yol sinifi); yoksa filo icin tek hiz."""
        uz = d.get("length", 0.0)
        if edge_speeds:
            v = d.get("hizKmh")
            if v:
                return uz * (60.0 / (float(v) * 1000.0))
        return uz * min_per_m
    fleet_time: dict = {}   # kenar -> filoya ilk bildirildigi an (dk)

    prior = set()
    for (u, v, k) in (prior_closed or ()):
        prior.add((u, v, k))
        prior.add((v, u, k))

    agents = []
    for i, task in enumerate(tasks):
        agents.append({
            "node": nearest_node(G, task["startLat"], task["startLon"]),
            "goal": nearest_node(G, task["endLat"], task["endLon"]),
            "clock": 0.0, "length": 0.0, "own": set(), "prior": prior, "fallback": False,
            "discoveries": 0, "stops": 0, "radioReplans": 0, "iterations": 0,
            "path": None, "keys": None, "idx": 0, "pathEdges": set(), "status": "moving",
            # Ekip kavsaga HANGI kenarla girdi: sagdan trafikte donus maliyetini
            # belirleyen budur. Baslangicta yok (us onunde, yonu serbest).
            "gelen": None,
            "donus": {"duz": 0, "sag": 0, "sol": 0, "u": 0},
            "donusDk": 0.0,
            # FIILEN SURULEN yol: planlanan degil, gercekten gecilen kenarlar.
            # Kapanmayi bilmeyen ekip cikmaza girip geri donuyor; manset sayi
            # (4,4 -> 1,6 dk) bu yoldan geliyor ama harita onu cizmiyordu,
            # yalniz uc planlama varyantini gosteriyordu -- kullanici hangi
            # cizginin "bilmeseydik" oldugunu soramaz hale geliyordu (27 Eylul).
            "izlenen": [],
        })

    soft = prior_penalty_factor is not None
    continuous = bool(prior_multiplier)
    if continuous and (prior_closed or soft):
        raise ValueError("prior_multiplier, prior_closed/prior_penalty_factor ile birlikte kullanilmaz")
    if (soft or continuous) and pathfinder != "weight":
        raise ValueError("yumusak prior yalniz pathfinder='weight' ile desteklenir")

    def known(agent):
        base = (agent["prior"] | agent["own"]) if (agent["prior"] and not soft) else agent["own"]
        if not share:
            return base
        t = agent["clock"]
        if simultaneous_known:
            return base | {e for e, te in fleet_time.items() if te <= t}
        return base | {e for e, te in fleet_time.items() if te < t}

    def plan(agent) -> bool:
        # simulate_naive_agent ile ayni kurallar: en cok max_iterations yol hesabi,
        # ayni gizleme, ayni paralel kenar secimi (ajanin INANDIGI cizge uzerinden).
        if agent["iterations"] >= max_iterations:
            agent["status"] = "unreachable"
            return False
        agent["iterations"] += 1
        hidden = {(u, v, k) for (u, v, k) in known(agent) if G.has_edge(u, v, k)}
        try:
            if pathfinder == "view":
                G_view = nx.restricted_view(G, [], hidden) if hidden else G
                path = nx.shortest_path(G_view, agent["node"], agent["goal"], weight="length")
                keys = [min(G_view[u][v], key=lambda k, u=u, v=v: G_view[u][v][k].get("length", float("inf")))
                        for u, v in zip(path, path[1:])]
            elif continuous:
                path, keys = _shortest_path_avoiding(G, agent["node"], agent["goal"], hidden,
                                                     multiplier=prior_multiplier)
            elif soft:
                path, keys = _shortest_path_avoiding(G, agent["node"], agent["goal"], hidden,
                                                     agent["prior"], prior_penalty_factor)
            elif turn_costs:
                def _sure(u, v, k, d, _h=hidden):
                    if (u, v, k) in _h:
                        return float("inf")
                    return _kenar_dk(d) * 60.0
                _sn, path, kenarlar, _say = _donus.en_kisa_yol(
                    G, agent["node"], agent["goal"], _sure, yonler=_yonler,
                    gelen_kenar=agent["gelen"], en_yuksek_hiz_ms=_vmax_ms)
                if path is None:
                    raise nx.NetworkXNoPath("donus maliyetli yol yok")
                keys = [e[2] for e in kenarlar]
            else:
                path, keys = _shortest_path_avoiding(G, agent["node"], agent["goal"], hidden)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            if agent["prior"] and prior_fallback:
                # Baslangic bilgisi (model) hedefi baglantisiz birakti: ekip modeli birakir.
                agent["prior"] = set()
                agent["fallback"] = True
                return plan(agent)
            agent["status"] = "unreachable"
            return False
        agent["path"], agent["keys"], agent["idx"] = path, keys, 0
        agent["pathEdges"] = set(zip(path, path[1:], keys))
        return True

    def learn(agent, edges, t_obs):
        for (u, v, k) in edges:
            for e in ((u, v, k), (v, u, k)):
                agent["own"].add(e)
                if share and t_obs < fleet_time.get(e, float("inf")):
                    fleet_time[e] = t_obs

    def step(agent):
        """Ajan bulundugu kavsakta: telsiz -> gorus -> bir kenar ilerle."""
        if agent["path"] is None and not plan(agent):
            return
        t_arrive = agent["clock"]
        stopped = False
        while True:
            if agent["node"] == agent["goal"]:
                agent["status"] = "arrived"
                break
            if share:
                pe = agent["pathEdges"]
                if any(e in pe for e in known(agent)):
                    agent["radioReplans"] += 1
                    if not plan(agent):
                        return
                    continue
            path, keys, idx = agent["path"], agent["keys"], agent["idx"]
            seen, dist = [], 0.0
            for j in range(idx, len(path) - 1):
                if dist > sight_m:
                    break
                e = (path[j], path[j + 1], keys[j])
                if e in real_closed_edges:
                    seen.append(e)
                    if not per_stop:
                        break   # R0/R2: yalniz siradaki kenara bakar
                dist += G[path[j]][path[j + 1]][keys[j]].get("length", 0.0)
            if not seen:
                break
            learn(agent, seen, t_arrive)
            agent["discoveries"] += len(seen)
            if per_stop:
                if not stopped:
                    agent["clock"] += kapanma_cezasi_dk
            else:
                agent["clock"] += kapanma_cezasi_dk
            stopped = True
            if not plan(agent):
                return
        if stopped:
            agent["stops"] += 1
        if agent["status"] != "moving":
            return
        j = agent["idx"]
        u, v, k = agent["path"][j], agent["path"][j + 1], agent["keys"][j]
        d = G[u][v][k]
        w = d.get("length", 0.0)
        agent["length"] += w
        if turn_costs and agent["gelen"] is not None:
            t = _donus.donus_tipi(_yonler[agent["gelen"]][1], _yonler[(u, v, k)][0],
                                  geri_mi=(v == agent["gelen"][0]))
            agent["donus"][t] += 1
            ek = _donus.DONUS_SN.get(t, 0.0) / 60.0
            agent["donusDk"] += ek
            agent["clock"] += ek
        agent["clock"] += _kenar_dk(d)
        agent["izlenen"].append((u, v, k))
        agent["gelen"] = (u, v, k)
        agent["node"] = v
        agent["idx"] = j + 1

    heap = [(0.0, i) for i in range(len(agents))]
    heapq.heapify(heap)
    while heap:
        _, i = heapq.heappop(heap)
        agent = agents[i]
        if agent["status"] != "moving":
            continue
        step(agent)
        if agent["status"] == "moving":
            heapq.heappush(heap, (agent["clock"], i))

    out = []
    for agent in agents:
        if agent["status"] != "arrived":
            out.append(None)
            continue
        out.append({
            "distanceMeters": round(agent["length"], 1),
            "discoveries": agent["discoveries"],
            "stops": agent["stops"],
            # t_u ile carpilan olay sayisi: R0/R2 kesif basina, R1 durak basina
            "penaltyEvents": agent["stops"] if per_stop else agent["discoveries"],
            "radioReplans": agent["radioReplans"],
            "arrivalMin": round(agent["clock"], 2),
            "pathComputations": agent["iterations"],
            "fallback": agent["fallback"],
            "kapanmaCezasiDk": round(kapanma_cezasi_dk, 3),
            "donusler": dict(agent["donus"]),
            "donusSuresiDk": round(agent["donusDk"], 2),
            "izlenenKenar": list(agent["izlenen"]),
            "cezadanGelenDk": round(
                (agent["stops"] if per_stop else agent["discoveries"]) * kapanma_cezasi_dk, 2),
        })
    return out


def dilate_mask_by_metres(mask, bounds, w, radius_m):
    """`mask`'taki her hasar pikselini `radius_m` metre yaricapli bir daireye
    genisletir. Metre -> piksel donusumu goruntunun kendi sinirlarindan
    (bounds) hesaplanir, yani zoom seviyesinden bagimsizdir: 0,48 m/px'te
    25 m ~ 52 piksel, 3,86 m/px'te ~ 6 piksel."""
    import cv2

    if radius_m <= 0 or mask is None:
        return mask
    west, south, east, north = bounds
    mid_lat = (south + north) / 2.0
    width_m = haversine(mid_lat, west, mid_lat, east)
    metres_per_px = width_m / max(1, w)
    radius_px = int(round(radius_m / metres_per_px))
    if radius_px < 1:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius_px + 1, 2 * radius_px + 1))
    return cv2.dilate(mask.astype(np.uint8), kernel)


def analyze_road_network_graph(bounds, w, h, blockage_mask, network_type='drive',
                               blockage_radius_m=0.0):
    """Fetches OSM graph, evaluates blockages, and returns safe/blocked lists.

    `blockage_radius_m` (varsayilan 0 = eski davranis): bir kenar, uzerindeki
    orneklenen noktalardan birinin `blockage_radius_m` metre YAKININDA hasar
    varsa kapali sayilir.

    Neden: eski kural hasarin yolun CIZILMIS MERKEZ CIZGISI pikselinin tam
    ustune dusmesini istiyordu. Gercekte baskin kapanma mekanizmasi yandaki
    binanin cokup molozunu sokaga dokmesidir; OSM merkez cizgisi 1-2 piksel
    genisliginde oldugu icin kesisim pratikte hep bos cikiyordu. Olculdu
    (Antakya, Maxar Open Data 2023-02-11, gercek deprem sonrasi goruntu):
    model z=18'de goruntunun %1,26'sini hasarli buldu, ama kapali yol SIFIR.
    Yaricap kurali makaledeki r_h parametresinin (sert kapatma yaricapi)
    tanimiyla aynidir ve `apply_risk_penalties`'teki
    `blockage_hard_radius_m` ile tutarlidir."""
    west, south, east, north = bounds
    G, last_error = fetch_osm_road_graph(bounds, network_type=network_type)

    if G is None:
        print("OSMnx error (yerel cache yok, tum Overpass aynalari denendi):", last_error)
        return None, None, None, None

    blockage_mask = dilate_mask_by_metres(blockage_mask, bounds, w, blockage_radius_m)
    safe_edges, blocked_edges, edges_to_remove, _coverage = _classify_edges(
        G, bounds, w, h, blockage_mask)

    safe_G = G.copy()
    safe_G.remove_edges_from(edges_to_remove)

    return G, safe_G, safe_edges, blocked_edges


def _classify_edges(G, bounds, w, h, blockage_mask, valid_mask=None):
    """Grafin her kenarini `blockage_mask` uzerinde orneklenen noktalara gore
    acik/kapali alt-segmentlere boler.

    `analyze_road_network_graph` (canli /analyze) ve
    `closures_from_damage_mask` (Colab'da uretilmis hazir maske) AYNI
    orneklemeyi kullansin diye tek yerde tutulur -- iki yolun sessizce
    birbirinden ayrismasi, makaledeki kapanma sayilarini hangi yoldan
    uretildigine bagli hale getirirdi.

    `valid_mask` verilirse (goruntunun gercekten GORULEN pikselleri), her
    orneklenen noktanin gorulen bir piksele dusup dusmedigi sayilir ve
    kapsama istatistigi doner. Karar mantigini DEGISTIRMEZ; yalnizca raporlar.

    Donus: (safe_edges, blocked_edges, edges_to_remove, coverage)
    """
    west, south, east, north = bounds
    blocked_edges = []
    safe_edges = []
    edges_to_remove = []
    total_samples = 0
    observed_samples = 0
    edges_observed = 0

    for u, v, key, data in G.edges(keys=True, data=True):
        if 'geometry' in data:
            line = data['geometry']
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            line = LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])

        length = line.length
        # Örnekleme sıklığını ~5 metreye düşürüyoruz (eskiden ~2 metreydi)
        num_samples = max(int(length / 0.00005), 3)

        current_type = None
        current_segment = []
        has_blocked_part = False
        edge_observed = 0

        for i in range(num_samples):
            pt = line.interpolate(float(i) / (num_samples - 1), normalized=True)
            px = int((pt.x - west) / (east - west) * w)
            py = int((north - pt.y) / (north - south) * h)

            is_blocked = False
            if 0 <= px < w and 0 <= py < h:
                if blockage_mask[py, px] > 0:
                    is_blocked = True
                    has_blocked_part = True
                if valid_mask is not None and valid_mask[py, px] > 0:
                    edge_observed += 1

            if current_type is None:
                current_type = is_blocked
                current_segment.append((pt.x, pt.y))
            elif current_type == is_blocked:
                current_segment.append((pt.x, pt.y))
            else:
                current_segment.append((pt.x, pt.y)) # connect lines
                if len(current_segment) > 1:
                    if current_type:
                        blocked_edges.append((u, v, key, LineString(current_segment)))
                    else:
                        safe_edges.append((u, v, key, LineString(current_segment)))

                current_type = is_blocked
                current_segment = [(pt.x, pt.y)]

        if len(current_segment) > 1:
            if current_type:
                blocked_edges.append((u, v, key, LineString(current_segment)))
            else:
                safe_edges.append((u, v, key, LineString(current_segment)))

        if has_blocked_part:
            edges_to_remove.append((u, v, key))

        total_samples += num_samples
        observed_samples += edge_observed
        # Ornek noktalarinin en az yarisi gorulen piksele dusen kenar "gorulmus"
        # sayilir -- kapanma karari bu kenarlar icin anlamlidir.
        if edge_observed * 2 >= num_samples:
            edges_observed += 1

    coverage = None
    if valid_mask is not None:
        n_edges = G.number_of_edges()
        coverage = {
            "edgesTotal": n_edges,
            "edgesObserved": edges_observed,
            "edgesObservedFraction": round(edges_observed / n_edges, 4) if n_edges else 0.0,
            "sampleObservedFraction": round(observed_samples / total_samples, 4) if total_samples else 0.0,
        }
    return safe_edges, blocked_edges, edges_to_remove, coverage


def closures_from_damage_mask(G, mask_bounds, damage_mask, valid_mask=None, blockage_radius_m=25.0):
    """Onceden uretilmis bir hasar maskesinden (Colab/GPU, bkz.
    benchmark/colab/make_model_masks.py) yol kapanmalari cikarir.

    Canli /analyze ile ayni kural ve ayni ornekleme kullanilir
    (`dilate_mask_by_metres` + `_classify_edges`). Tek fark: graf ve maske
    AYRI gelir -- graf senaryonun kendi bolge sinirlariyla onbellekten
    okunur (`mask_bounds`, karo hizali oldugu icin bolge sinirindan biraz
    genistir ve yalnizca piksel izdusumunde kullanilir).

    Donus: (safe_edges, blocked_edges, closed_edge_keys, coverage)
    """
    h, w = damage_mask.shape[:2]
    mask = dilate_mask_by_metres(damage_mask, mask_bounds, w, blockage_radius_m)
    safe_edges, blocked_edges, edges_to_remove, coverage = _classify_edges(
        G, mask_bounds, w, h, mask, valid_mask)
    return safe_edges, blocked_edges, set(edges_to_remove), coverage


def edge_closure_probability(G, mask_bounds, damage_mask, valid_mask=None):
    """Her kenar icin modelin kapanma olasiligi: kenar boyunca orneklenen
    noktalarin hasarli piksele dusen ORANI (0..1).

    Ornekleme `_classify_edges` ile ayni (~5 m adim, en az 3 nokta, ayni
    piksel izdusumu) -- boylece bugunku ikili kural bu olasiligin
    "p > 0" esiklemesine esittir ve iki yol ayrisamaz.

    `valid_mask` verilirse oran yalniz GORULEN orneklerden hesaplanir; hic
    gorulen ornegi olmayan kenar icin olasilik 0 (bugunku kuralla ayni:
    gorulmeyen kenar acik sayilir) ve `unobserved` kumesinde raporlanir.

    Ornekleme vektorlestirilmistir: noktalar kenar kenar dongudeki ayni GEOS
    cagrisiyla (line_interpolate_point), ayni oranlarla uretilir; piksel
    izdusumu ayni islem sirasiyla yapilir ve sifira dogru kirpilir (Python
    int() gibi). Dongulu ilk surumle BIREBIR ayni sonucu verdigi 33 EMSR
    hucresinde ve 31 596 kenarli bir grafta dogrulandi (J-34). Hiz farki
    canli analize eklenebilmesi icin gerekliydi: dongu o grafta 5,8 sn
    suruyordu.

    Donus: ({(u, v, k): p}, unobserved_keys)
    """
    import shapely

    h, w = damage_mask.shape[:2]
    west, south, east, north = mask_bounds
    probs, unobserved = {}, set()
    edges = list(G.edges(keys=True, data=True))
    for start in range(0, len(edges), 4096):
        part = edges[start:start + 4096]
        lines = np.empty(len(part), dtype=object)
        lines[:] = [_edge_geometry(G, u, v, data) for u, v, _k, data in part]
        n = np.maximum((shapely.length(lines) / 0.00005).astype(np.int64), 3)
        edge_idx = np.repeat(np.arange(len(part)), n)
        i = np.arange(edge_idx.size) - np.repeat(np.cumsum(n) - n, n)
        frac = i / np.repeat(n - 1, n)
        xy = shapely.get_coordinates(
            shapely.line_interpolate_point(lines[edge_idx], frac, normalized=True))
        px = ((xy[:, 0] - west) / (east - west) * w).astype(np.int64)
        py = ((north - xy[:, 1]) / (north - south) * h).astype(np.int64)
        ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
        if valid_mask is not None:
            ok[ok] = valid_mask[py[ok], px[ok]] != 0
        damaged = np.zeros_like(ok)
        damaged[ok] = damage_mask[py[ok], px[ok]] > 0
        seen = np.bincount(edge_idx[ok], minlength=len(part))
        hit = np.bincount(edge_idx[damaged], minlength=len(part))
        for j, (u, v, key, _data) in enumerate(part):
            if seen[j] == 0:
                unobserved.add((u, v, key))
                probs[(u, v, key)] = 0.0
            else:
                probs[(u, v, key)] = int(hit[j]) / int(seen[j])
    return probs, unobserved


def soft_cost_route(G, closure_prob: dict, lam: float, start_lat, start_lon, end_lat, end_lon):
    """Yumusak maliyetli rota (J-34): model kapali dedigi kenari SILMEZ,
    planlama maliyetini uzunluk x (1 + lam * p) yapar. `closure_prob`,
    `edge_closure_probability` ciktisidir; yalniz p > 0 kenarlari tasimak
    yeter, eksik kenar p = 0 sayilir.

    Planlayici J-34 deneyindeki M-y ajaninin kullandigiyla ayni
    (`_shortest_path_avoiding`, `multiplier`) -- canli rota olculen kuraldan
    cikar. Hicbir kenar gizlenmedigi icin ag kopmaz: rota ancak iki nokta
    arasinda hic yol yoksa bulunamaz.

    Donus: (route_coords [(lat, lon)] ya da None, exposure_m, risky_edges)
      exposure_m   rotadaki kenarlarda toplam uzunluk x p -- rotanin
                   "beklenen kapali metresi"
      risky_edges  rotada p > 0 olan kenar sayisi
    """
    start_node = nearest_node(G, start_lat, start_lon)
    end_node = nearest_node(G, end_lat, end_lon)
    multiplier = {e: 1.0 + lam * p for e, p in closure_prob.items() if p > 0}
    try:
        path, keys = _shortest_path_avoiding(G, start_node, end_node, set(), multiplier=multiplier)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, 0.0, 0

    route_coords = [(G.nodes[start_node]['y'], G.nodes[start_node]['x'])]
    exposure_m = 0.0
    risky_edges = 0
    for u, v, k in zip(path, path[1:], keys):
        data = G[u][v][k]
        p = closure_prob.get((u, v, k), 0.0)
        if p > 0:
            exposure_m += data.get('length', 0.0) * p
            risky_edges += 1
        if 'geometry' in data:
            # calculate_route/get_route_line'daki ters-geometri duzeltmesi.
            coords = [(lat, lon) for lon, lat in data['geometry'].coords]
            u_node, v_node = G.nodes[u], G.nodes[v]
            start_to_u = haversine(coords[0][0], coords[0][1], u_node['y'], u_node['x'])
            start_to_v = haversine(coords[0][0], coords[0][1], v_node['y'], v_node['x'])
            if start_to_v < start_to_u:
                coords = coords[::-1]
            route_coords.extend(coords[1:])
        else:
            route_coords.append((G.nodes[v]['y'], G.nodes[v]['x']))
    return route_coords, exposure_m, risky_edges


def _edge_geometry(G, u, v, data):
    line = data.get('geometry')
    if line is None:
        u_node, v_node = G.nodes[u], G.nodes[v]
        line = LineString([(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])])
    return line


def closures_from_lines(G, damaged_lines, buffer_m=8.0, min_overlap=0.5,
                        sample_step_m=2.0, observed_polygons=None):
    """Yer gercegi hasarli YOL CIZGILERINDEN (orn. EMSR648 Grading
    `transportationL`) OSM grafinda kapanma cikarir.

    Kural: bir kenar, geometrisi boyunca ~`sample_step_m` arayla orneklenen
    noktalarinin en az `min_overlap` orani herhangi bir hasarli cizginin
    `buffer_m` metre yakinindaysa kapali sayilir. Oran esigi, hasarli yolu
    yalnizca TEK NOKTADA kesen (kavsakta degen) sokaklarin kapanmasini onler.
    Tampon, iki kaynagin geometri farkini karsilar -- olculdu (drone
    sahneleri): EMSR kose noktalarinin en yakin OSM kenarina medyan uzakligi
    0,1-2,2 m, %75'i 3-6 m icinde.

    Iki yonlu bir sokagin iki yonlu kenari ayni geometriyi tasidigi icin
    ikisi birlikte kapanir (J-19 oncesi duzeltilen hata burada yeniden
    olusamaz).

    `damaged_lines`   : [[(lon, lat), ...], ...]
    `observed_polygons`: yer gercegi kaynaginin GERCEKTEN inceledigi alan
                         (EMSR AOI poligonlari, [(lon, lat), ...] halkalari).
                         Verilirse orta noktasi bu alanin disinda kalan kenar
                         sayisi raporlanir -- o kenarlar hakkinda yer gercegi
                         YOKTUR ve acik kabul edilmistir.

    Donus: (safe_edges, blocked_edges, closed_edge_keys, stats)
    """
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree

    edges = list(G.edges(keys=True, data=True))
    stats = {"edgeCount": len(edges), "damagedLineCount": len(damaged_lines),
             "bufferM": buffer_m, "minOverlap": min_overlap}
    if not edges:
        return [], [], set(), stats

    ys = [d['y'] for _, d in G.nodes(data=True)]
    xs = [d['x'] for _, d in G.nodes(data=True)]
    lat0, lon0 = (min(ys) + max(ys)) / 2.0, (min(xs) + max(xs)) / 2.0
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0

    def to_m(coords):
        return [((lon - lon0) * kx, (lat - lat0) * ky) for lon, lat in coords]

    geoms = [_edge_geometry(G, u, v, d) for u, v, _k, d in edges]
    edge_lines_m = [LineString(to_m(g.coords)) for g in geoms]

    damaged_m = [LineString(to_m(l)) for l in damaged_lines if len(l) >= 2]
    closed = set()
    if damaged_m:
        tree = STRtree(damaged_m)
        pairs = tree.query(np.array(edge_lines_m, dtype=object), predicate="dwithin", distance=buffer_m)
        candidates = {}
        for ei, li in zip(pairs[0], pairs[1]):
            candidates.setdefault(int(ei), []).append(damaged_m[int(li)])
        for ei, near_lines in candidates.items():
            line = edge_lines_m[ei]
            n = max(3, int(line.length / sample_step_m) + 1)
            hit = 0
            for i in range(n):
                p = line.interpolate(i / (n - 1), normalized=True)
                if any(dl.distance(p) <= buffer_m for dl in near_lines):
                    hit += 1
            if hit / n >= min_overlap:
                u, v, k, _d = edges[ei]
                closed.add((u, v, k))

    safe_edges, blocked_edges = [], []
    for (u, v, k, _d), g in zip(edges, geoms):
        (blocked_edges if (u, v, k) in closed else safe_edges).append((u, v, k, g))

    stats["closedEdgeCount"] = len(closed)
    if observed_polygons:
        polys = [Polygon(to_m(ring)) for ring in observed_polygons if len(ring) >= 3]
        inside = 0
        for g in edge_lines_m:
            mid = g.interpolate(0.5, normalized=True)
            if any(p.contains(mid) for p in polys):
                inside += 1
        stats["edgesInsideObservedArea"] = inside
        stats["edgesInsideObservedFraction"] = round(inside / len(edges), 4)
    return safe_edges, blocked_edges, closed, stats
