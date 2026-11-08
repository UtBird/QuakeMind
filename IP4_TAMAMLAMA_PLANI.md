# IP4 Tamamlama Planı — Harita, Güvenli Rota, Isı Haritası ve Uydu Görüntüsü İşleme

## Context

TÜBİTAK 2209-A raporunun IP4 iş paketi üç somut teslimat vaat ediyor: (1) yıkım/kapanma
verilerinden Gaussian kernel tabanlı bir **ısı haritası** ve bunu servis eden bir `/heatmap`
API'si, (2) bu ısı haritasını "ceza katsayısı" olarak kullanan **risk-ağırlıklı A*/Dijkstra
rota motoru**, (3) kullanıcı raporlarının (`report_blockage`) bu modele geri beslenmesi.

Mevcut kodda bu üçü **eksik veya kopuk**:
- `/api/road_damage/analyze` içindeki `analyze_road_network_graph` zaten OSM grafiğinden
  hasarlı kenarları **siliyor** (binary blok/açık), ama bu grafik `report_blockage`'ın
  PostGIS'e yazdığı `road_blockages` tablosunu hiç okumuyor — veri tek yönlü akıyor.
- `network.py::calculate_route` hem `nx.shortest_path` (Dijkstra) hem `nx.astar_path`
  (A*, haversine heuristic) hesaplıyor ama **A* sonucu hiç döndürülmüyor/kullanılmıyor**
  (`_astar_coords` dead value) ve rota yalnızca tek bir ephemeral `/analyze` session'ına
  bağlı (`road_damage_sessions`, bellekte, sunucu yeniden başlayınca kaybolur).
- `/api/road_damage/nearest_debris` tamamen **hardcoded sahte veri** (`DEBRIS_SITES`)
  döndürüyor — "PostGIS Mekânsal Analiz" etiketiyle ama gerçek bir PostGIS sorgusu yok.
- Gaussian kernel ısı haritası ve `/heatmap` endpoint'i **hiç yok**. Mobildeki
  `heatmapEvents`/`showHeatmapMode` (app_widgets.dart, risk_module_result.dart) farklı bir
  şey — CatBoost deprem risk olaylarını gösteriyor, yıkım yoğunluğunu değil.

Kullanıcı Raspberry Pi donanımı olmadığı için IP5'i laptop üzerinde simüle ediyor — bu plan
IP5'ten bağımsız, **tamamen yazılım/veritabanı** işi olduğu için donanım gerektirmiyor.

Hedef: rapor + mevcut kod arasındaki farkı kapatıp, hem raporla tutarlı hem gerçekten
çalışan bir "risk-puanlı rota + ısı haritası" alt sistemi kurmak; backend, web ve mobili
aynı yeni API'lere bağlamak.

---

## Faz 1 — PostGIS'te kalıcı hasar/tehlike nokta tablosu

**Amaç:** Şu an sadece analiz cevabında (`/analyze` response) görünüp kaybolan tespitleri
(çatlak, yıkım, hasarlı yol pikselleri) kalıcı, sorgulanabilir noktalara dönüştürmek —
ısı haritası ve rota motoru bu tablodan besleniyor.

- `backend/utils/postgis_manager.py`:
  - `init_spatial_tables()` içine yeni tablo ekle: `damage_points`
    `(id, source_type ['crack'|'destruction'|'road_damage'|'sos'], severity FLOAT,
    label VARCHAR, geom GEOMETRY(Point,4326), created_at)` + GIST index
    (mevcut `afad_assembly_points`/`road_blockages` deseniyle birebir aynı stil).
  - Yeni metodlar: `insert_damage_point(...)`, `query_damage_points_nearby(lat, lon, radius_m)`,
    `query_damage_points_in_bbox(bbox)` — `query_nearby_postgis` ile aynı try/except +
    offline-fallback deseni.
- `fastapi_app.py`:
  - `/api/camera/analyze` (satır ~1310) — YOLO çatlak/yıkım tespiti sonucu, varsa
    request'teki `latitude/longitude` ile `insert_damage_point(source_type="crack"|"destruction", ...)`
    çağır (best-effort, mevcut `report_blockage`'daki try/except deseniyle).
  - `_analyze_road_damage_impl` (satır ~658) — `pred_mask_binary`'den
    `cv2.connectedComponentsWithStats` ile hasar bloblarının centroid'lerini piksel→coğrafi
    koordinata çevirip (`bounds`, `w`, `h` zaten mevcut) `damage_points`'e yaz
    (`source_type="road_damage"`, `severity=boosted_probs` ortalaması).
  - `/api/sos/alert` (satır ~1277) — zaten konum taşıyorsa aynı tabloya `source_type="sos"`
    olarak yaz.

**Doğrulama:** Swagger'dan `/api/road_damage/analyze` çağır, sonra
`psql -c "SELECT count(*), source_type FROM damage_points GROUP BY source_type;"` ile
satırların düştüğünü gör (PostGIS bağlı değilse offline modda sessizce atlanmalı, hata
fırlatmamalı).

---

## Faz 2 — Gerçek `/heatmap` endpoint'i (Gaussian kernel)

**Amaç:** Rapor 2.4.3'te tanımlanan Gaussian kernel yoğunluk ısı haritasını gerçekten
üretmek.

- Yeni dosya `backend/apps/road_damage/utils/heatmap.py`:
  - `build_gaussian_heatmap(points: list[(lat, lon, weight)], bbox, grid_size=100, bandwidth_km=0.5) -> list[[lat, lon, intensity]]`
    — `numpy` ile saf Gaussian kernel smoothing (rapor scipy değil "Gauss çekirdek
    fonksiyonu" diyor; `requirements.txt`'de scipy yok, yeni bağımlılık eklememek için
    numpy ile elle yazılır — `assembly.py`'deki `haversine_m` zaten var, aynı dosyadan
    import edilebilir).
  - Çıktı formatı bilinçli olarak **leaflet.heat**'in beklediği `[lat, lon, intensity]`
    üçlüsü — hem web hem mobil aynı formatı tüketebilir.
- `fastapi_app.py`: yeni `@app.get("/api/road_damage/heatmap")`
  - Params: `latitude, longitude, radiusKm=10.0`.
  - `postgis_engine.query_damage_points_in_bbox(...)` + `LIVE_ROAD_BLOCKAGES`'i (veya
    PostGIS `road_blockages` tablosunu) birleştirip `build_gaussian_heatmap`'e ver.
  - Dönüş: `{"points": [[lat,lon,intensity], ...], "bounds": {...}, "generatedFrom": {...}}`.

**Doğrulama:** `curl "localhost:8000/api/road_damage/heatmap?latitude=36.2&longitude=36.16"`
— Faz 1'de eklenen noktaların etrafında yoğunluk artışı görülmeli.

---

## Faz 3 — Risk-ağırlıklı A*/Dijkstra rota motoru

**Amaç:** Rapor 2.4.4'ün "kapalı yol maskeleri + yıkım yoğunluğu ısı haritası + tehlikeli
noktalar + kullanıcı raporları"nı **tek bir ceza-katsayılı graf**te birleştirmek, ve rotayı
tek bir ephemeral `/analyze` session'ına bağımlı olmaktan çıkarmak.

- `backend/apps/road_damage/utils/network.py`:
  - Yeni fonksiyon `apply_risk_penalties(G, damage_points, blockages, blockage_hard_radius_m=25)`:
    - Blockage'lara `blockage_hard_radius_m` içinde kalan kenarları **kaldır** (bugünkü
      `edges_to_remove` mantığıyla aynı, hard-block).
    - Kalan her kenar için `damage_points`'e olan mesafeye göre yumuşak ceza uygula:
      `edge['risk_cost'] = edge['length'] * (1 + risk_weight(min_dist_to_point))`
      (`risk_weight`: rapordaki fay-mesafe kademesine benzer basamaklı fonksiyon —
      <50m → 3.0, 50-150m → 1.5, 150-400m → 1.1, üstü → 1.0).
  - `calculate_route`'u güncelle: `weight='length'` yerine `weight='risk_cost'` kullan,
    **hem** `path_dijkstra` **hem** `path_astar`'ı (heuristic zaten haversine tabanlı, sadece
    `weight` parametresini `risk_cost`'a çevir) döndür — bugün hesaplanıp atılan A* sonucunu
    artık gerçekten kullan.
- `fastapi_app.py`: yeni `@app.post("/api/road_damage/safe_route")`
  - Body: `startLat, startLon, destLat, destLon, radiusKm=3.0`.
  - `assembly.py`'deki `bbox_from_center` + `ox.graph_from_bbox(network_type="walk")` ile
    graf çek (session'a bağımlı değil — `/analyze` önce çağrılmış olmasını gerektirmez).
  - `postgis_engine.query_damage_points_in_bbox` + `road_blockages` sorgusuyla o bbox'taki
    tüm tehlike noktalarını çek, `apply_risk_penalties` uygula.
  - `calculate_route` çağır, hem Dijkstra hem A* sonucunu, hangisinin daha düşük
    `risk_cost` topladığını da response'a ekleyerek dön (`routeCoords`, `distanceMeters`,
    `algorithm: "astar"|"dijkstra"`, `riskScore`).
  - Mevcut `/api/road_damage/route` (session'a bağlı) ve `/calculate_custom_route` (OSRM/
    düz-çizgi) **korunur** — `safe_route` bunların üçüncü, PostGIS-tabanlı ve session'sız
    alternatifi olur; `SafeEvacuationMap.tsx`'teki "provisional OSRM → damage-aware upgrade"
    deseni burada da uygulanabilir (Faz 5).

**Doğrulama:** Faz 1'de eklenen bir `damage_point`in yakınından geçen iki nokta arasında
`safe_route` çağır; dönen rotanın o noktayı olabildiğince es geçtiğini (blokede kalan
kenarlardan kaçındığını) manuel doğrula.

---

## Faz 4 — `nearest_debris`'i gerçek veriye bağla

- `fastapi_app.py` `/api/road_damage/nearest_debris` (satır ~1250): hardcoded
  `DEBRIS_SITES` listesini kaldır, `postgis_engine.query_damage_points_nearby(latitude,
  longitude, radius_m=5000)` + `road_blockages` sorgusuyla değiştir. PostGIS offline ise
  boş liste + `"source": "offline_fallback"` dön (mevcut `assembly` endpoint'indeki
  offline-fallback deseniyle tutarlı).

**Doğrulama:** Faz 1 test verisi eklendikten sonra `nearest_debris` artık o gerçek
noktaları döndürmeli, sabit 5 kayıt değil.

---

## Faz 5 — Web entegrasyonu (quakemind-web)

- `src/lib/api.ts`: `getSafeRoute(...)` ve `getDamageHeatmap(...)` fonksiyonları ekle
  (mevcut `getRouteBetweenPoints`, `analyzeRoadDamage` ile aynı fetch deseni).
- `src/components/map/SafeEvacuationMap.tsx`: bugünkü "OSRM provisional → damage-aware
  upgrade" state machine'ine (`routeMode: idle|damage-aware|fallback`) üçüncü bir mod
  ekle — `getSafeRoute` sonucu gelince rota bunu kullansın (session gerektirmediği için
  artık `/analyze` çağrılmamış olsa bile risk-farkında rota gösterilebilir).
- Isı haritası için `leaflet.heat` paketini ekle (`npm install leaflet.heat`
  `@types/leaflet.heat` — küçük, bağımlılık riski düşük), `road-damage/page.tsx`'e "Isı
  Haritası" toggle'ı ekleyip `getDamageHeatmap` sonucunu `L.heatLayer` ile render et.

---

## Faz 6 — Mobil entegrasyon (quakemind Flutter)

- `lib/services/road_damage_service.dart`: `fetchSafeRoute(...)` ve
  `fetchDamageHeatmap(...)` metodları ekle (mevcut `analyzeArea`'daki `_apiBridge.request`
  çağrı deseniyle).
- `lib/screens/responder/road_damage_page.dart`: rota çizilen yerlere risk-ağırlıklı
  rota seçeneği ekle.
- `lib/widgets/app_widgets.dart`'taki heatmap widget'ı bugün yalnızca deprem risk
  olaylarına (`heatmapEvents`) bağlı — genel bir `List<[lat,lon,intensity]>` alacak şekilde
  parametreleştirip road-damage sayfasında da yeniden kullan (yeni widget yazmak yerine).

---

## Faz 7 — Testler

- Yeni `backend/tests/test_road_damage_api.py` (proje kökünde hiç test dizini
  yok — bu ilk pytest dosyası olacak): `fastapi.testclient.TestClient` ile
  `/api/road_damage/heatmap`, `/api/road_damage/safe_route`, `/api/road_damage/nearest_debris`
  için smoke testler (PostGIS yokken offline-fallback yolunun da 200 döndüğünü doğrula).
  `requirements.txt`'e `pytest`, `httpx` ekle.

---

## Sıralama ve bağımlılıklar

Faz 1 → Faz 2 & Faz 4 (paralel olabilir) → Faz 3 → Faz 5 & Faz 6 (paralel) → Faz 7.
Faz 1 olmadan 2/3/4'ün beslenecek verisi yok; Faz 3, Faz 2'nin ürettiği risk sinyalini
kullanabildiği için ondan sonra gelmeli.
