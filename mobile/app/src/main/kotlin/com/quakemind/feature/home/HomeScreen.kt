package com.quakemind.feature.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.automirrored.outlined.ShortText
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.ui.state.AppUiState
import java.util.Locale
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

private val HomeFilters = listOf("Tümü", "M ≥ 4.0", "M ≥ 3.5", "Yakındakiler")
private val TurkishLocale = Locale.forLanguageTag("tr-TR")

@Composable
fun HomeScreen(
    state: AppUiState,
    onMap: () -> Unit,
    onReport: () -> Unit,
    onSos: () -> Unit,
    onSafety: () -> Unit,
    onAlerts: () -> Unit,
    onRouting: () -> Unit,
    onDamage: () -> Unit,
    onNlp: () -> Unit,
    onRisk: () -> Unit,
    onChecklist: () -> Unit,
    onOperations: () -> Unit,
    onProfile: () -> Unit,
    onIncident: (String) -> Unit,
    onRequestLocation: () -> Unit = {},
) {
    HomeScreen(
        state = HomeUiState(
            session = state.session,
            earthquakes = state.earthquakes,
            alerts = state.alerts,
            pendingCount = state.pendingCount,
            online = state.online,
        ),
        onMap = onMap,
        onReport = onReport,
        onSos = onSos,
        onSafety = onSafety,
        onAlerts = onAlerts,
        onRouting = onRouting,
        onDamage = onDamage,
        onNlp = onNlp,
        onRisk = onRisk,
        onChecklist = onChecklist,
        onOperations = onOperations,
        onProfile = onProfile,
        onIncident = onIncident,
        onRequestLocation = onRequestLocation,
    )
}

@Composable
fun HomeScreen(
    state: HomeUiState,
    onMap: () -> Unit,
    onReport: () -> Unit,
    onSos: () -> Unit,
    onSafety: () -> Unit,
    onAlerts: () -> Unit,
    onRouting: () -> Unit,
    onDamage: () -> Unit,
    onNlp: () -> Unit,
    onRisk: () -> Unit,
    onChecklist: () -> Unit,
    onOperations: () -> Unit,
    onProfile: () -> Unit,
    onIncident: (String) -> Unit,
    onRequestLocation: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()
    var filter by rememberSaveable { mutableStateOf("Tümü") }
    var showAll by rememberSaveable { mutableStateOf(false) }
    val earthquakes = remember(state.earthquakes, state.deviceLocation) {
        val origin = state.deviceLocation
        if (origin == null) state.earthquakes
        else state.earthquakes.map {
            it.copy(distanceKm = haversineKm(origin, GeoPoint(it.latitude, it.longitude)))
        }
    }
    val nearest = remember(earthquakes, state.deviceLocation) {
        if (state.deviceLocation == null) earthquakes.firstOrNull()
        else earthquakes.minByOrNull(Earthquake::distanceKm)
    }
    val filtered = remember(filter, earthquakes, state.deviceLocation) {
        when (filter) {
            "M ≥ 4.0" -> earthquakes.filter { it.magnitude >= 4.0 }
            "M ≥ 3.5" -> earthquakes.filter { it.magnitude >= 3.5 }
            "Yakındakiler" -> if (state.deviceLocation == null) emptyList()
                else earthquakes.filter { it.distanceKm <= 350.0 }.sortedBy(Earthquake::distanceKm)
            else -> earthquakes
        }
    }
    val visible = remember(filtered, showAll) { if (showAll) filtered else filtered.take(8) }
    val alerts = remember(state.alerts) { state.alerts.take(2) }
    val unread = remember(state.alerts) { state.alerts.any { !it.isRead } }

    Column(modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        HomeHeader(state.session?.displayName, unread, onAlerts, onProfile)
        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f).testTag("home_lazy_column"),
            state = listState,
            contentPadding = PaddingValues(start = 20.dp, top = 8.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            if (!state.online || state.pendingCount > 0) {
                item(key = "offline", contentType = "status") { OfflineModeBanner(state.pendingCount) }
            }
            item(key = "location", contentType = "location") {
                LocationSummary(state, onRequestLocation)
            }
            item(key = "urgent_actions", contentType = "actions") {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Surface(
                        onClick = onReport,
                        shape = MaterialTheme.shapes.large,
                        color = MaterialTheme.colorScheme.errorContainer,
                        contentColor = MaterialTheme.colorScheme.onErrorContainer,
                    ) {
                        Row(
                            Modifier.fillMaxWidth().padding(20.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(14.dp),
                        ) {
                            Icon(Icons.Outlined.Report, contentDescription = null, modifier = Modifier.size(28.dp))
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                                Text("İhbar oluştur", style = MaterialTheme.typography.titleMedium)
                                Text("Hasar veya yardım ihtiyacını bildir", style = MaterialTheme.typography.bodyMedium)
                            }
                            Icon(Icons.Outlined.ChevronRight, contentDescription = null)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        HomeAction("Güvendeyim", Icons.Outlined.CheckCircle, onSafety, Modifier.weight(1f))
                        HomeAction("Acil yardım", Icons.Outlined.Call, onSos, Modifier.weight(1f))
                    }
                }
            }
            item(key = "earthquake_summary", contentType = "summary") {
                if (nearest != null) {
                    EarthquakeSummary(nearest, state.deviceLocation != null, onMap, onRisk)
                } else {
                    QuakeCard {
                        Text("Deprem kayıtları", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(8.dp))
                        Text("Katalog henüz alınmadı. Bağlantı geldiğinde kayıtlar burada görünür.",
                            style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                        TextButton(onClick = onMap) { Text("Haritayı aç") }
                    }
                }
            }
            if (alerts.isNotEmpty()) {
                item(key = "alerts", contentType = "alerts") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        HomeSectionTitle("Bölgesel uyarılar", "Tümü", onAlerts)
                        QuakeCard {
                            alerts.forEachIndexed { index, alert ->
                                if (index > 0) HorizontalDivider(Modifier.padding(vertical = 12.dp), color = Zinc200)
                                AlertPreview(alert, onClick = { onIncident(alert.id) })
                            }
                        }
                    }
                }
            }
            item(key = "preparedness", contentType = "tools") {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    HomeSectionTitle("Hazırlık ve ulaşım")
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        HomeAction("Tahliye rotası", Icons.Outlined.Directions, onRouting, Modifier.weight(1f))
                        HomeAction("Afet çantası", Icons.Outlined.Inventory2, onChecklist, Modifier.weight(1f))
                    }
                }
            }
            item(key = "earthquake_filters", contentType = "filters") {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    HomeSectionTitle("Son depremler", if (showAll) "Daha az" else "Tümü", {
                        if (filtered.size > 8) showAll = !showAll else onMap()
                    })
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        HomeFilters.forEach { option ->
                            FilterChip(
                                selected = filter == option,
                                onClick = { filter = option; showAll = false },
                                label = { Text(option) },
                            )
                        }
                    }
                }
            }
            if (visible.isEmpty()) {
                item(key = "empty_filter", contentType = "empty") {
                    EmptyState(
                        "Bu filtrede kayıt yok",
                        if (filter == "Yakındakiler" && state.deviceLocation == null)
                            "Yakınındaki kayıtları görmek için üstteki konum düğmesini kullan."
                        else "Başka bir filtre seçerek kayıtları inceleyebilirsin.",
                    )
                }
            }
            items(visible, key = { "earthquake_${it.id}" }, contentType = { "earthquake" }) { earthquake ->
                EarthquakeListRow(earthquake, state.deviceLocation != null, onMap)
            }
            item(key = "analysis_tools", contentType = "tools") {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    HomeSectionTitle("İnceleme araçları")
                    QuakeCard {
                        ToolRow("Fotoğrafla hasar incelemesi", Icons.Outlined.PhotoCamera, onDamage)
                        HorizontalDivider(Modifier.padding(vertical = 4.dp), color = Zinc200)
                        ToolRow("Yardım çağrısını analiz et", Icons.AutoMirrored.Outlined.ShortText, onNlp)
                        if (state.session?.capabilities?.contains("operations.view") == true) {
                            HorizontalDivider(Modifier.padding(vertical = 4.dp), color = Zinc200)
                            ToolRow("Saha operasyonları", Icons.Outlined.SupportAgent, onOperations)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HomeHeader(name: String?, unread: Boolean, onAlerts: () -> Unit, onProfile: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        AfetLogoMark(size = 40.dp)
        Column(Modifier.weight(1f)) {
            Text("QuakeMind", style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.semantics { heading() })
            Text(name?.takeIf { it.isNotBlank() }?.let { "Merhaba, $it" } ?: "Afete hazır, birlikte güvende",
                style = MaterialTheme.typography.bodySmall, color = Zinc500,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        BadgedBox(badge = { if (unread) Badge() }) {
            IconButton(onClick = onAlerts) {
                Icon(Icons.Outlined.Notifications, if (unread) "Okunmamış uyarılar" else "Uyarılar")
            }
        }
        IconButton(onClick = onProfile) { Icon(Icons.Outlined.Person, "Profil") }
    }
}

@Composable
private fun LocationSummary(state: HomeUiState, onRequest: () -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Icon(Icons.Outlined.MyLocation, null, tint = AfetAccent, modifier = Modifier.size(20.dp))
        Column(Modifier.weight(1f)) {
            Text(when {
                state.isLocating -> "Konum alınıyor…"
                state.deviceLocation != null -> "Konumun hazır"
                else -> "Yakınındaki noktaları keşfet"
            }, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
            state.locationError?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = AfetCrimson) }
            if (state.deviceLocation != null && state.accuracyMetres != null) {
                Text("Yaklaşık ±${state.accuracyMetres.toInt()} m doğruluk", style = MaterialTheme.typography.bodySmall, color = Zinc500)
            }
        }
        TextButton(onClick = onRequest, enabled = !state.isLocating) {
            Text(if (state.deviceLocation == null) "Konumu bul" else "Yenile")
        }
    }
}

@Composable
private fun HomeAction(title: String, icon: ImageVector, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Surface(onClick = onClick, modifier = modifier, shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surface) {
        Column(Modifier.padding(16.dp).heightIn(min = 64.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Icon(icon, null, tint = AfetAccent, modifier = Modifier.size(24.dp))
            Text(title, style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun HomeSectionTitle(title: String, action: String? = null, onAction: () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().heightIn(min = 40.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f).semantics { heading() })
        if (action != null) TextButton(onClick = onAction) { Text(action) }
    }
}

@Composable
private fun EarthquakeSummary(earthquake: Earthquake, hasLocation: Boolean, onMap: () -> Unit, onRisk: () -> Unit) {
    QuakeCard {
        Text(if (hasLocation) "Konumuna en yakın deprem" else "Son deprem kaydı", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(18.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            SeismicMagnitudeBadge(earthquake.magnitude, size = 64.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(earthquake.epicenter, style = MaterialTheme.typography.titleMedium)
                Text(compactTimestamp(earthquake.occurredAt), style = MaterialTheme.typography.bodySmall, color = Zinc500)
                Text("${earthquake.depthKm.toInt()} km derinlik" +
                    if (hasLocation) " · ${distanceLabel(earthquake.distanceKm)} uzakta" else "",
                    style = MaterialTheme.typography.bodySmall, color = Zinc500)
            }
        }
        Spacer(Modifier.height(16.dp))
        Text(earthquake.source.ifBlank { "Kaynak belirtilmedi" }, style = MaterialTheme.typography.bodySmall, color = Zinc500)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = onMap) { Text("Haritada gör") }
            TextButton(onClick = onRisk) { Text("Bölgesel risk") }
        }
    }
}

@Composable
private fun AlertPreview(alert: Alert, onClick: () -> Unit) {
    val color = when (alert.severity) {
        AlertSeverity.CRITICAL -> AfetCrimson
        AlertSeverity.WARNING -> AfetAmber
        AlertSeverity.INFO -> AfetBlue
    }
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).heightIn(min = 64.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Icon(Icons.Outlined.NotificationsActive, null, tint = color, modifier = Modifier.size(22.dp))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(alert.title, style = MaterialTheme.typography.titleSmall)
            Text("${alert.category} · ${alert.occurredAt}", style = MaterialTheme.typography.bodySmall, color = Zinc500)
        }
        Icon(Icons.Outlined.ChevronRight, null, tint = Zinc500)
    }
}

@Composable
private fun EarthquakeListRow(earthquake: Earthquake, hasLocation: Boolean, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
        SeismicMagnitudeBadge(earthquake.magnitude)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(earthquake.epicenter, style = MaterialTheme.typography.titleSmall)
            Text("${compactTimestamp(earthquake.occurredAt)} · ${earthquake.depthKm.toInt()} km",
                style = MaterialTheme.typography.bodySmall, color = Zinc500)
            if (hasLocation) Text(distanceLabel(earthquake.distanceKm), style = MaterialTheme.typography.bodySmall, color = Zinc500)
        }
        Icon(Icons.Outlined.ChevronRight, null, tint = Zinc500)
    }
}

@Composable
private fun ToolRow(label: String, icon: ImageVector, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick).heightIn(min = 56.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Icon(icon, null, tint = AfetAccent, modifier = Modifier.size(22.dp))
        Text(label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
        Icon(Icons.Outlined.ChevronRight, null, tint = Zinc500)
    }
}

@Preview(name = "Home · light", showBackground = true)
@Composable
private fun HomePreview() {
    QuakeMindTheme(darkTheme = false) {
        HomeScreen(HomeUiState(), {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
    }
}

@Preview(name = "Home · dark", showBackground = true)
@Composable
private fun HomeDarkPreview() {
    QuakeMindTheme(darkTheme = true) {
        HomeScreen(HomeUiState(online = false, pendingCount = 2), {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
    }
}

private fun distanceLabel(distanceKm: Double): String =
    if (distanceKm < 1.0) "${(distanceKm * 1_000).toInt()} m" else String.format(TurkishLocale, "%.1f km", distanceKm)

private fun compactTimestamp(value: String): String = value
    .replace('T', ' ')
    .removeSuffix("Z")
    .take(16)

private fun haversineKm(from: GeoPoint, to: GeoPoint): Double {
    val lat1 = Math.toRadians(from.latitude)
    val lat2 = Math.toRadians(to.latitude)
    val dLat = lat2 - lat1
    val dLon = Math.toRadians(to.longitude - from.longitude)
    val a = sin(dLat / 2).let { it * it } + cos(lat1) * cos(lat2) * sin(dLon / 2).let { it * it }
    return 6_371.0 * 2 * asin(sqrt(a.coerceIn(0.0, 1.0)))
}
