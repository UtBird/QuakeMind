# QuakeMind (AFET) Performans ve Mimari Geliştirme Kuralları (DEVELOPMENT_RULES.md)

**Tarih:** 15 Ağustos 2026\
**Proje:** QuakeMind (AFET) Android Uygulaması\

Bu doküman, QuakeApp kod tabanında gelecekte yapılacak tüm özellik geliştirme, hata düzeltme ve refactoring süreçlerinde performansı, görsel tasarım bütünlüğünü ve çevrimdışı çalışma kararlılığını korumak için uyulması **zorunlu kuralları** içerir.

---

## 1. State Yönetimi ve Compose Kuralları

### Kural 1.1: Feature State Asla Kök Seviyede (Root) Collect Edilmez
- `QuakeMindApp` veya `MainActivity` seviyesinde feature-specific veriler (`pendingCount`, `alerts`, `checklistItems`) toplanmamalıdır.
- Her ekran kendi ViewModel'ine sahip olmalı ve state collection işlemi ilgili feature'ın `*Route.kt` composable'ı seviyesinde `collectAsStateWithLifecycle` ile yapılmalıdır.

### Kural 1.2: Lazy Listelerde Kararlı `key` ve `contentType` Zorunludur
- Tüm `LazyColumn`, `LazyRow` ve `items()` çağrılarında deterministik ve benzersiz bir `key` (`key = { it.id }`) ile `contentType` tanımlanmalıdır.
- Listelerde monolitik `item { list.forEach { ... } }` kullanımı kesinlikle yasaktır; bu yaklaşım Compose pencereleme ve recycling mekanizmasını devre dışı bırakır.

### Kural 1.3: Hot Path'te (Kompozisyon Gövdesinde) Hesaplama ve Filtreleme Yasaktır
- Composable fonksiyon gövdelerinde `.filter()`, `.sortedBy()`, `.groupBy()` gibi koleksiyon operasyonları doğrudan çalıştırılmamalıdır.
- Türetilmiş state'ler ViewModel katmanında dönüştürülmeli veya UI seviyesinde `remember(keys) { ... }` ile sarmalanmalıdır.

### Kural 1.4: Animasyonlar Ölçüm Fazını (Measure Pass) Tetiklememelidir
- Boyut, ölçek ve opaklık animasyonlarında `Modifier.scale()` veya `Modifier.alpha()` yerine doğrudan render katmanında çalışan `Modifier.graphicsLayer { scaleX = ...; scaleY = ...; alpha = ... }` kullanılmalıdır.

### Kural 1.5: Canvas Çizimlerinde Per-Frame Allocation Yasaktır
- Özel `Canvas` çizimlerinde (`MapScreen`, grafikler vb.) her frame'de `Path()`, `Stroke()`, `Offset()` üretilmemeli, `drawWithCache` kullanılarak geometri önbelleğe alınmalıdır.

---

## 2. Veri, Veritabanı ve Senkronizasyon Kuralları

### Kural 2.1: Idempotency Key Asla Değişmez
- Çevrimdışı oluşturulan her ihbar (`IncidentDraft`), tekil bir `idempotencyKey` ile yerel veritabanına kaydedilir. Hiçbir retry veya worker tekrarında bu anahtar yenilenemez.

### Kural 2.2: Sınırsız forEach ve Full Table Scan Yasaktır
- Veritabanı kuyrukları işlenirken tüm kayıtlar tek seferde belleğe alınamaz. Her zaman 50/100'lük kontrollü batch'ler (`claimPendingBatch`) halinde `@Transaction` sınırında atomik durum geçişi yapılmalıdır.
- Sık sorgulanan sütun kombinasyonları (örn. `syncStatus`, `createdAt`) üzerinde composite index tanımlanmalıdır.

### Kural 2.3: `fallbackToDestructiveMigration` Kesinlikle Yasaktır
- Afet durumunda kullanıcının cihazında biriken yerel ihbarların silinmesi kabul edilemez. Şema değişiklikleri mutlaka açık `Migration` nesneleri (`MIGRATION_X_Y`) ile yapılmalı ve Room testleri yazılmalıdır.

### Kural 2.4: Ağ Bağlantısı ile İhbar Kuyruğu Ayrı Modellenmelidir
- `online = pendingCount == 0` gibi semantik olarak hatalı çıkarımlar yapılmamalıdır. Gerçek ağ bağlantısı `NetworkMonitor` ile, yerel kuyruk ise `pendingCount().distinctUntilChanged()` ile yönetilmelidir.

---

## 3. Mimari Sınırlar ve Modül Kuralları

### Kural 3.1: Tek Yönlü Bağımlılık (No Circular Dependencies)
- Katmanlar arasındaki bağımlılık yönü katı şekilde tek yönlüdür:
  `app -> feature -> core:ui -> core:designsystem -> core:data -> core:database & core:network -> core:model`
- `feature` paketleri birbirlerine doğrudan bağımlı olamaz; iletişim navigation rotaları üzerinden sağlanır.

### Kural 3.2: Ağır Bağımlılıklar Lazy Init Yapılmalıdır
- Uygulama başlangıcında (`QuakeMindApplication.onCreate` veya `ViewModel.init`) açılış için elzem olmayan I/O, rota hesaplama veya model yükleme işlemleri eager olarak çalıştırılmamalıdır.

### Kural 3.3: UI Değişikliği ile Performans Refactoring Asla Karıştırılmaz
- Görsel tasarım değişikliği içeren PR'lar ile performans optimizasyonu içeren PR'lar birbirinden tamamen ayrı tutulmalıdır. Performans refactor'larında UI görünümü %100 korunmalıdır.

### Kural 3.4: Her Yeni Büyük Özellik Macrobenchmark Senaryosu Ekler
- Uygulamaya eklenen her yeni kritik kullanıcı yolculuğu (CUJ) için `:benchmark` modülünde ilgili `*Benchmark.kt` sınıfı yazılmalı ve Baseline Profile güncellenmelidir.
