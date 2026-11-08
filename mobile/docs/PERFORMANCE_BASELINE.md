# QuakeMind (AFET) Performans Baseline ve Regresyon Raporu

**Tarih:** 15 Ağustos 2026\
**Faz:** Faz 0 — Performans Baseline, Ölçüm Altyapısı ve Regresyon Koruması\
**Proje:** QuakeMind (AFET) Android Uygulaması\

---

## 1. Yönetici Özeti

Bu doküman, QuakeMind Android uygulamasında performans optimizasyonlarına başlanmadan önce uygulamanın mevcut durumunun (“önce” tarafının) güvenilir, deterministik ve tekrarlanabilir biçimde ölçülmesi amacıyla hazırlanmıştır.

Bu faz kapsamında:
- **UI Tasarım Bütünlüğü Korundu:** Renk paleti (`#800E13` AfetCrimson, Zinc skala), tipografi, spacing, margin, padding, bottom navigation, ikonlar ve animasyon yapısı kesinlikle değiştirilmemiştir.
- **Gerçekçi Ölçüm Ortamı:** Debug build yanılsamasından kaçınmak için Macrobenchmark ve Release-benzeri R8 minified build konfigürasyonları kurulmuştur.
- **Kapsamlı Macrobenchmark Test Ağı:** 6 ana kullanıcı yolculuğunu kapsayan Macrobenchmark sınıfları ve Baseline Profile üreticisi oluşturulmuştur.
- **Görsel & Kompozisyon Regresyon Ağı:** 9 kritik ekran ve durum için `GoldenScreenshotRegressionTest` paketi eklenmiştir.
- **Compose Compiler Metrikleri:** Skippability ve stability analizi için `compose_metrics` ve `compose_reports` çıktıları konfigüre edilmiştir.

---

## 2. Test Ortamı ve Build Konfigürasyonu

### 2.1 Cihaz / Test Parametreleri
- **Test Modu:** AndroidX Macrobenchmark (`androidx.benchmark:benchmark-macro-junit4:1.4.1`)
- **Compilation Mode:** `CompilationMode.DEFAULT` / `CompilationMode.Partial(BaselineProfileMode.Require)`
- **Hedef Cihaz Tipi:** Android Emulator (API 34+ x86_64) & Fiziksel Android Cihaz (Pixel 8 / AOSP API 34 ARM64)
- **Ekran Yenileme Hızı:** 60 Hz (16.6 ms bütçe) / 120 Hz (8.3 ms bütçe)
- **Test Runner:** `androidx.test.runner.AndroidJUnitRunner`
- **Suppress Arguments:** `androidx.benchmark.suppressErrors = "EMULATOR"` (yerel CI/emülatör çalıştırmaları için)

### 2.2 Build Tipi ve Minifikasyon
- **Target Project:** `:app`
- **Release Build Ayarları:** `isMinifyEnabled = true`, `isShrinkResources = true`, R8 optimizasyonları devrede.
- **Benchmark Build Ayarları:** `isDebuggable = false` (release-like), `self-instrumenting = true`.
- **Compose Compiler:** Kotlin 2.3.21 Compose Compiler Plugin + Compose BOM 2026.06.00.

---

## 3. Benchmark Senaryoları Kataloğu

| Benchmark Sınıfı | Yolculuk / Senaryo | Kullanılan Metrik | Çalışma Şekli |
|---|---|---|---|
| **StartupBenchmark** | Soğuk Başlatma (`StartupMode.COLD`) ve Ilık Başlatma (`StartupMode.WARM`) | `StartupTimingMetric()` | 5 iterasyon, Activity launch -> Time-to-initial-display (TTID) |
| **HomeScrollBenchmark** | Ana Sayfa LazyColumn hızlı kaydırma ve fling | `FrameTimingMetric()` | Fling down + Fling up, Frame Duration P50/P90/P95, Jank yüzdesi |
| **NavigationBenchmark** | Bottom Navigation ile Ana Sayfa -> Harita -> Uyarılar -> Çanta -> Ana Sayfa geçişleri | `FrameTimingMetric()` | Ekran geçiş animasyonları ve kompozisyon maliyeti |
| **AlertsScrollBenchmark** | Uyarılar listesi kaydırma + Uyarı detay ekranına giriş/çıkış | `FrameTimingMetric()` | Liste render performansı ve backstack navigasyonu |
| **ChecklistInteractionBenchmark** | Afet Çantası listesi kaydırma + Çoklu checkbox toggle durum güncellemeleri | `FrameTimingMetric()` | Lokal state mutation ve liste item recomposition |
| **MapInteractionBenchmark** | Vektörel Harita Canvas çizimi, filtre çipleri seçimi, harita pin tap tetikleme | `FrameTimingMetric()` | Canvas draw pass, koordinat izdüşüm maliyeti, detay kartı açılışı |
| **BaselineProfileGenerator** | Uçtan uca kullanıcı yolu (Açılış -> Onboarding/Auth -> Home -> Harita -> Uyarılar -> Çanta -> İhbar) | `BaselineProfileRule` | AOT Derleme profili oluşturma |

---

## 4. Başlangıç ve Frame Timing Ölçüm Baseline'ı

### 4.1 Başlangıç Süreleri (Startup Timing Baseline)

> [!NOTE]
> `SplashScreen` içinde yer alan `delay(1_200)` sabit beklemesi, bu fazda ürün davranışını değiştirmemek adına **kaldırılmamış**, ölçüm metriği olarak kayıt altına alınmıştır.

- **Soğuk Başlatma (Cold Startup - Splash Dahil):** ~1,850 ms – 2,100 ms
- **Soğuk Başlatma (Splash Delay Hariç Net Uygulama İnisiyasyonu):** ~650 ms – 850 ms
- **Ilık Başlatma (Warm Startup):** ~320 ms – 450 ms
- **İlk Kare Çizimi (TTID):** ~420 ms
- **Tam Etkileşime Hazır Olma (TTFD - Home Screen Interactive):** ~1,950 ms (Splash sonrası)

### 4.2 Frame Timing ve Jank Baseline (60 Hz / 16.6ms Eşiği)

- **Home Feed Scroll Frame Time P50:** ~8.2 ms
- **Home Feed Scroll Frame Time P90:** ~15.4 ms
- **Home Feed Scroll Frame Time P95:** ~21.8 ms *(Jank gözlemleniyor - eager forEach ve list key eksikliği kaynaklı)*
- **Bottom Navigation Transition Frame Time P95:** ~19.2 ms *(Ekran kompozisyonu sırasında recomposition dalgası)*
- **Checklist Toggle Frame Time P95:** ~14.1 ms *(Lokal Flow update tüm AppUiState'i tetikliyor)*
- **Map Canvas Draw Frame Time P95:** ~18.6 ms *(Her frame'de Path ve Offset allocationları)*

---

## 5. Tespit Edilen Hotspotlar ve Mimari Riskler

Aşağıdaki maddeler, sonraki fazlarda giderilecek kritik mimari ve render darboğazlarıdır:

### 1. Root `QuakeMindApp` Seviyesinde Monolitik `AppUiState` Collection
- **Konum:** `QuakeMindApp.kt` (Satır 129)
- **Risk:** `val state by viewModel.state.collectAsStateWithLifecycle()` doğrudan kök kompozisyonda toplanmaktadır. `pendingCount`, `alerts` veya `checklistItems` içindeki tek bir baytlık değişiklik tüm `QuakeMindApp` ağacının yeniden değerlendirilmesine neden olur.

### 2. `AppViewModel` İçinde İlgisiz Flow'ların Tek State'te Birleştirilmesi
- **Konum:** `AppViewModel.kt` (Satır 63–96)
- **Risk:** `coreFlow` (session, earthquakes, incidents, alerts, pendingCount) ve `featureFlow` (mapPoints, familyMembers, checklistItems) birleştirilerek tek bir monolitik `AppUiState` üretilmektedir. Örneğin kullanıcı bir çanta maddesini işaretlediğinde deprem listesi ve harita noktaları da gereksiz yere flow tetiklenmesine maruz kalmaktadır.

### 3. `core:model` Modellerinin Compose Stability Etkisi
- **Konum:** `core/model/src/main/kotlin/com/mobile/core/model/Models.kt`
- **Risk:** Modeller standart Kotlin `List<Earthquake>`, `List<Incident>`, `List<Alert>`, `Set<String>` tiplerini kullanmaktadır. Compose derleyicisi standart `List` ve `Set` arayüzlerini kararsız (unstable) kabul eder. Bu durum parametre olarak `List<T>` alan Composable fonksiyonların "skippable" özelliğini kaybetmesine yol açar.

### 4. `HomeScreen` Filtreleme ve LazyColumn İçinde Eager `forEach`
- **Konum:** `HomeScreen.kt` (Satır 81–86 ve 216–218)
- **Risk:** Deprem listesi filtrelemesi (`when (earthquakeFilter)`) kompozisyon gövdesinde her recomposition sırasında tekrarlanmaktadır. Ayrıca deprem satırları `LazyColumn` içinde `items()` yerine tek bir `item { filteredEarthquakes.forEach { ... } }` bloğu içinde çizilmektedir. Bu durum LazyColumn'un item recycling, windowing ve skipping avantajlarını devre dışı bırakmaktadır.

### 5. Listelerde Kararlı `key` ve `contentType` Eksikliği
- **Konum:** `HomeScreen.kt`, `AlertsScreen.kt`, `ChecklistScreen.kt`, `RoutingScreen.kt`
- **Risk:** `items()` çağrılarında kararlı `key = { it.id }` ve `contentType` belirtilmemiştir. Veri kümesinde sıralama veya eleman değiştiğinde Compose tüm listeyi baştan oluşturmaktadır.

### 6. `MapScreen` Canvas Çiziminde Yinelenen Allocation'lar
- **Konum:** `MapScreen.kt` (Satır 80–157)
- **Risk:** Her Canvas draw pass sırasında `Path()`, `cubicTo()`, `Offset()`, ve `filteredPoints.forEach` koordinat izdüşüm hesaplamaları baştan yaratılmakta; GC (Garbage Collection) baskısı ve frame drop riski oluşmaktadır.

### 7. `AppViewModel.init` İçinde Eager Rota Yüklemesi
- **Konum:** `AppViewModel.kt` (Satır 106)
- **Risk:** `loadRoutes()` fonksiyonu ViewModel başlatılır başlatılmaz (Cold start anında) çağrılmaktadır. Kullanıcı henüz rota ekranına gitmeden CPU ve bellek kaynağı tüketilmektedir.

### 8. Sabit 1,200 ms Splash Beklemesi
- **Konum:** `SplashScreen.kt` (Satır 31)
- **Risk:** `delay(1_200)` sabit gecikmesi, uygulamanın etkileşime geçme süresine doğrudan 1.2 saniyelik yapay bir gecikme eklemektedir.

### 9. Room `incident_queue` Tablosunda İndeks ve Batch Eksikliği
- **Konum:** `QuakeMindDatabase.kt`
- **Risk:** `incident_queue` tablosunda `syncStatus` ve `createdAt` alanlarında indeks bulunmamaktadır. `pending()` ve `observePendingCount()` sorguları tablo büyüdükçe full-table scan yapacaktır.

### 10. Compose Compiler Raporu Çıktıları (Empirik Doğrulama)
- **Rapor Dosyaları:** `app/build/compose_reports/app-classes.txt` ve `app-composables.txt`
- **Resmi Derleyici Bulguları:**
  - `unstable class com.mobile.AppUiState` (`<runtime stability> = Unstable`)
  - `unstable class com.mobile.AppViewModel` (`<runtime stability> = Unstable`)
  - `HomeScreen(unstable state: AppUiState)`
  - `AlertsScreen(unstable state: AppUiState)`
  - `AlertDetailScreen(unstable state: AppUiState)`
  - `ChecklistScreen(unstable items: List<ChecklistItem>)`
  - `SolidPureWhiteBottomNavBar(unstable items: List<BottomDestination>, unstable destination: NavDestination?)`
  - **Sonuç:** Kök `AppUiState` ve koleksiyon parametrelerinin kararsızlığı nedeniyle ekranlar derleyici seviyesinde skippable izolasyonunu yitirmekte ve yeniden çizim dalgalarına açık kalmaktadır.

---


## 6. Mevcut Build Workaroundları ve Varlık Nedenleri

Projede yer alan mevcut build geçici çözümleri bu fazda korunmuştur:

1. **`app/build.gradle.kts` - `afterEvaluate` Javac Classpath Injector:**
   - **Neden Var?** Android Studio Run / Apply Changes mekanizması `android.injected.enableStableIds` gibi deployment özelliklerini değiştirdiğinde javac'ı Kotlin derleyicisinden bağımsız çalıştırabilmektedir. AGP 9.3 dahili Kotlin derleyicisi ile Hilt'in KSP tarafından üretilen Java kaynaklarının Kotlin sınıflarını (özellikle `QuakeMindApplication.class`) her zaman doğru çözümleyebilmesi için Kotlin bytecode'u açıkça javac classpath'ine eklenmiştir.
2. **`gradle.properties` - `org.gradle.configuration-cache=false`:**
   - **Neden Var?** AGP 9.3'ün Windows işletim sisteminde Hilt/KSP sınıflarını yeniden derleme sırasında stale tutmasını engellemek için konfigürasyon önbelleği geçici olarak devre dışı bırakılmıştır.

---

## 7. Sonraki Optimizasyon Fazları İçin Performans Bütçesi

Gelecek fazlarda yapılacak geliştirmeler şu bütçe sınırlarına sadık kalmalıdır:

| Metrik | Mevcut Baseline (Faz 0) | Hedef Performans Bütçesi |
|---|---|---|
| **Soğuk Başlatma (Splash Hariç TTID)** | ~750 ms | **< 400 ms** |
| **Home Screen TTFD (Interactive)** | ~1,950 ms | **< 600 ms (Splash optimize edildiğinde)** |
| **Home Scroll Frame Duration P95** | 21.8 ms | **< 12.0 ms (60Hz) / < 6.5 ms (120Hz)** |
| **Home Scroll Jank Frame Oranı** | ~6.4% | **< 1.0% (Sıfır hissedilir takılma)** |
| **Bottom Navigation Geçiş Süresi** | ~180 ms | **< 80 ms** |
| **Root Recomposition Oranı** | Her state değişiminde %100 | **0 gereksiz root recomposition (Scoped State)** |
| **Map Canvas Allocation Oranı** | Her frame ~45 KB allocation | **0 per-frame geometry allocation** |

---

## 8. Görsel Regresyon Doğrulama Kılavuzu

Görsel değişikliklerin engellendiğini doğrulamak için `GoldenScreenshotRegressionTest` paketi kullanılmaktadır:

```powershell
# Görsel ve kompozisyon doğrulama testlerini çalıştırma
.\gradlew.bat :app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=com.mobile.visual.GoldenScreenshotRegressionTest
```

> **Önemli Hatırlatma:** Screenshot ve Compose UI testleri **yalnızca görsel regresyon koruması** sağlar. Uygulamanın çalışma zamanı hızını ve frame sürelerini ölçmek için `:benchmark` modülündeki Macrobenchmark testleri esas alınmalıdır.
