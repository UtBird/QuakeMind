package com.quakemind.feature.home

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.statusBars
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

private val HOME_FILTERS = listOf("Tümü", "M ≥ 4.0", "M ≥ 3.5", "Yakındakiler")
private val HomeBackground = Color(0xFFF5F6F8)
private val TurkishLocale = Locale.forLanguageTag("tr-TR")
private val HeroCrimson = Color(0xFF72161D)
private val HeroCrimsonDark = Color(0xFF521016)
private val HeroWhiteMuted = Color(0xFFEFDDE0)
private val CardShape = RoundedCornerShape(20.dp)

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
) {
    val listState = rememberLazyListState()
    val headerCollapsed by remember { derivedStateOf { listState.firstVisibleItemIndex > 0 || listState.firstVisibleItemScrollOffset > 48 } }
    val headerMargin by animateDpAsState(if (headerCollapsed) 0.dp else 16.dp, label = "headerMargin")
    val headerRadius by animateDpAsState(if (headerCollapsed) 0.dp else 18.dp, label = "headerRadius")
    val statusInset = WindowInsets.statusBars.asPaddingValues().calculateTopPadding()
    val headerTop by animateDpAsState(if (headerCollapsed) 0.dp else statusInset + 8.dp, label = "headerTop")
    val headerInnerTop by animateDpAsState(if (headerCollapsed) statusInset + 8.dp else 8.dp, label = "headerInnerTop")
    var earthquakeFilter by rememberSaveable { mutableStateOf("Tümü") }
    var showAllEarthquakes by rememberSaveable { mutableStateOf(false) }

    val earthquakesWithDistance = remember(state.earthquakes, state.deviceLocation) {
        val origin = state.deviceLocation
        if (origin == null) state.earthquakes
        else state.earthquakes.map { quake ->
            quake.copy(distanceKm = haversineKm(origin, GeoPoint(quake.latitude, quake.longitude)))
        }
    }
    val nearestEarthquake = remember(earthquakesWithDistance, state.deviceLocation) {
        if (state.deviceLocation == null) earthquakesWithDistance.firstOrNull()
        else earthquakesWithDistance.minByOrNull(Earthquake::distanceKm)
    }
    val filteredEarthquakes = remember(earthquakeFilter, earthquakesWithDistance, state.deviceLocation) {
        when (earthquakeFilter) {
            "M ≥ 4.0" -> earthquakesWithDistance.filter { it.magnitude >= 4.0 }
            "M ≥ 3.5" -> earthquakesWithDistance.filter { it.magnitude >= 3.5 }
            "Yakındakiler" -> if (state.deviceLocation == null) emptyList()
                else earthquakesWithDistance.filter { it.distanceKm <= 350.0 }.sortedBy(Earthquake::distanceKm)
            else -> earthquakesWithDistance
        }
    }
    val visibleEarthquakes = remember(filteredEarthquakes, showAllEarthquakes) {
        if (showAllEarthquakes) filteredEarthquakes else filteredEarthquakes.take(8)
    }
    val hasUnreadAlerts = remember(state.alerts) { state.alerts.any { !it.isRead } }
    val recentAlerts = remember(state.alerts) { state.alerts.take(2) }

    Box(Modifier.fillMaxSize().background(HomeBackground)) {
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .testTag("home_lazy_column"),
            state = listState,
            contentPadding = PaddingValues(start = 16.dp, top = statusInset + 92.dp, end = 16.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {

        if (!state.online || state.pendingCount > 0) {
            item(key = "home_offline_banner", contentType = "banner") {
                OfflineModeBanner(pendingCount = state.pendingCount)
            }
        }

        item(key = "home_location", contentType = "location") {
            HomeLocationCard(
                location = state.deviceLocation,
                accuracyMetres = state.accuracyMetres,
                isLocating = state.isLocating,
                error = state.locationError,
                onRequestLocation = onRequestLocation,
            )
        }

        if (nearestEarthquake != null) {
            item(key = "home_nearby_earthquake", contentType = "earthquake_hero") {
                NearbyEarthquakeHero(
                    earthquake = nearestEarthquake,
                    hasLocation = state.deviceLocation != null,
                    onMap = onMap,
                    onRisk = onRisk,
                )
            }
        } else {
            item(key = "home_earthquake_empty", contentType = "empty_state") {
                EarthquakeEmptyCard(onMap = onMap)
            }
        }

        if (recentAlerts.isNotEmpty()) {
            item(key = "home_alerts", contentType = "alerts") {
                RegionalAlertsCard(
                    alerts = recentAlerts,
                    onAlerts = onAlerts,
                    onSelectAlert = onIncident,
                )
            }
        }

        item(key = "home_quick_actions", contentType = "quick_actions") {
            QuickActionsGrid(
                onReport = onReport,
                onSafety = onSafety,
                onRouting = onRouting,
                onChecklist = onChecklist,
            )
        }

        item(key = "home_earthquakes_header", contentType = "section_header") {
            EarthquakeSectionHeader(
                selectedFilter = earthquakeFilter,
                onSelectFilter = {
                    earthquakeFilter = it
                    showAllEarthquakes = false
                },
                availableCount = filteredEarthquakes.size,
                shownCount = visibleEarthquakes.size,
                showAll = showAllEarthquakes,
                onToggleShowAll = { showAllEarthquakes = !showAllEarthquakes },
                onMap = onMap,
            )
        }

        if (visibleEarthquakes.isEmpty()) {
            item(key = "home_earthquakes_empty", contentType = "empty_state") {
                EarthquakeListEmpty(
                    needsLocation = earthquakeFilter == "Yakındakiler" && state.deviceLocation == null,
                    onRequestLocation = onRequestLocation,
                )
            }
        } else {
            items(
                items = visibleEarthquakes,
                key = { it.id },
                contentType = { "earthquake_row" },
            ) { earthquake ->
                EarthquakeRow(
                    earthquake = earthquake,
                    showDistance = state.deviceLocation != null,
                    onClick = onMap,
                )
            }
        }

        item(key = "home_analysis_tools", contentType = "analysis_tools") {
            AnalysisToolsCard(onDamage = onDamage, onNlp = onNlp, onOperations = onOperations)
        }
        }

        HomeHeader(
            userName = state.session?.displayName?.takeIf(String::isNotBlank),
            hasUnreadAlerts = hasUnreadAlerts,
            onAlerts = onAlerts,
            onProfile = onProfile,
            collapsed = headerCollapsed,
            cornerRadius = headerRadius,
            innerTop = headerInnerTop,
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .padding(horizontal = headerMargin)
                .padding(top = headerTop),
        )
    }
}

@Composable
private fun HomeHeader(
    userName: String?,
    hasUnreadAlerts: Boolean,
    onAlerts: () -> Unit,
    onProfile: () -> Unit,
    collapsed: Boolean,
    cornerRadius: androidx.compose.ui.unit.Dp,
    innerTop: androidx.compose.ui.unit.Dp,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.shadow(elevation = if (collapsed) 4.dp else 8.dp, shape = RoundedCornerShape(cornerRadius)),
        shape = RoundedCornerShape(cornerRadius),
        color = Color.White,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(start = 16.dp, end = 12.dp, top = innerTop, bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            AfetLogoMark(size = 36.dp, color = AfetCrimson)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                Text(
                    text = "QuakeMind",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = Zinc900,
                    maxLines = 1,
                )
                userName?.takeIf(String::isNotBlank)?.let { name ->
                    Text(
                        text = "Merhaba, $name",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = Zinc600,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            HeaderIconButton(
                icon = Icons.Outlined.Notifications,
                label = if (hasUnreadAlerts) "Okunmamış uyarılar" else "Uyarılar",
                onClick = onAlerts,
                showDot = hasUnreadAlerts,
            )
            HeaderIconButton(icon = Icons.Outlined.Person, label = "Profil", onClick = onProfile)
        }
    }
}

@Composable
private fun HeaderIconButton(
    icon: ImageVector,
    label: String,
    onClick: () -> Unit,
    showDot: Boolean = false,
) {
    Surface(
        modifier = Modifier
            .size(48.dp)
            .clickable(onClick = onClick)
            .semantics { contentDescription = label },
        shape = RoundedCornerShape(13.dp),
        color = Color.White,
        border = BorderZinc200,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(icon, contentDescription = null, tint = Zinc700, modifier = Modifier.size(19.dp))
            if (showDot) {
                Box(
                    Modifier
                        .align(Alignment.TopEnd)
                        .padding(7.dp)
                        .size(6.dp)
                        .clip(CircleShape)
                        .background(AfetCrimson),
                )
            }
        }
    }
}

@Composable
private fun HomeLocationCard(
    location: GeoPoint?,
    accuracyMetres: Float?,
    isLocating: Boolean,
    error: String?,
    onRequestLocation: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = Color.White,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(shape = CircleShape, color = AfetCrimsonMuted) {
                Box(Modifier.size(30.dp), contentAlignment = Alignment.Center) {
                    Icon(Icons.Outlined.MyLocation, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(16.dp))
                }
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                Text(
                    text = when {
                        isLocating -> "Konum alınıyor…"
                        location != null -> "Konum hazır${accuracyMetres?.let { " · ±${it.toInt()} m" }.orEmpty()}"
                        else -> "Konumunu bul"
                    },
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Medium,
                    color = if (error == null) Zinc800 else AfetCrimson,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                if (error != null) {
                    Text(error, fontSize = 10.sp, color = AfetCrimson, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
            IconButton(onClick = onRequestLocation, enabled = !isLocating, modifier = Modifier.size(48.dp)) {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = if (location == null) "Konumu bul" else "Konumu yenile",
                    tint = AfetCrimson,
                    modifier = Modifier.size(19.dp),
                )
            }
        }
    }
}

@Composable
private fun NearbyEarthquakeHero(
    earthquake: Earthquake,
    hasLocation: Boolean,
    onMap: () -> Unit,
    onRisk: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = HeroCrimson,
        shadowElevation = 4.dp,
    ) {
        Column(
            modifier = Modifier
                .padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Yakındaki depremler", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text(
                        if (hasLocation) "Konumuna en yakın kayıt" else "Son kaydedilen deprem",
                        fontSize = 11.sp,
                        color = HeroWhiteMuted,
                    )
                }
                Surface(color = Color.White.copy(alpha = 0.12f), shape = RoundedCornerShape(30.dp)) {
                    Text(
                        earthquake.source.ifBlank { "Deprem kataloğu" },
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color.White,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                Text(
                    text = magnitudeLabel(earthquake.magnitude),
                    fontSize = 30.sp,
                    lineHeight = 34.sp,
                    fontWeight = FontWeight.Black,
                    letterSpacing = (-1).sp,
                    color = Color.White,
                )
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(
                        earthquake.epicenter,
                        fontSize = 15.sp,
                        lineHeight = 19.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = if (hasLocation) distanceLabel(earthquake.distanceKm) else "Konum açılınca mesafe gösterilir",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = HeroWhiteMuted,
                    )
                }
            }

            HorizontalDivider(color = Color.White.copy(alpha = 0.18f))

            Row(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                HeroMeta(Modifier.weight(1f), Icons.Outlined.LocationOn, "Derinlik", "${earthquake.depthKm.toInt()} km")
                HeroMeta(Modifier.weight(1f), Icons.Outlined.Notifications, "Zaman", compactTimestamp(earthquake.occurredAt))
            }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(
                    onClick = onMap,
                    modifier = Modifier.weight(1f).height(48.dp),
                    shape = RoundedCornerShape(13.dp),
                    border = BorderStroke(1.dp, Color.White.copy(alpha = 0.45f)),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
                ) {
                    Text("Haritada aç", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                }
                Button(
                    onClick = onRisk,
                    modifier = Modifier.weight(1f).height(48.dp),
                    shape = RoundedCornerShape(13.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = HeroCrimsonDark),
                ) {
                    Text("Zemin analizine bak", fontSize = 11.sp, fontWeight = FontWeight.Bold, maxLines = 1)
                }
            }
        }
    }
}

@Composable
private fun HeroMeta(modifier: Modifier, icon: ImageVector, label: String, value: String) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Icon(icon, contentDescription = null, tint = HeroWhiteMuted, modifier = Modifier.size(14.dp))
        Column(verticalArrangement = Arrangement.spacedBy(1.dp)) {
            Text(label, fontSize = 9.sp, color = HeroWhiteMuted)
            Text(value, fontSize = 10.5.sp, fontWeight = FontWeight.SemiBold, color = Color.White, maxLines = 1)
        }
    }
}

@Composable
private fun EarthquakeEmptyCard(onMap: () -> Unit) {
    Surface(shape = CardShape, color = Color.White, border = BorderZinc200) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(22.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(Icons.Outlined.LocationOn, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(24.dp))
            Text("Deprem kaydı henüz alınmadı", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
            Text("Bağlantı geldiğinde güncel katalog burada görünecek.", fontSize = 12.sp, color = Zinc500)
            TextButton(onClick = onMap) { Text("Haritayı aç", color = AfetCrimson) }
        }
    }
}

@Composable
private fun RegionalAlertsCard(
    alerts: List<Alert>,
    onAlerts: () -> Unit,
    onSelectAlert: (String) -> Unit,
) {
    Surface(shape = CardShape, color = Color.White, border = BorderZinc200) {
        Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Bölgesel uyarılar", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Text("Güncel ve doğrulanmış bildirimler", fontSize = 11.sp, color = Zinc500)
                }
                TextButton(onClick = onAlerts, contentPadding = PaddingValues(horizontal = 6.dp, vertical = 4.dp)) {
                    Text("Tümünü gör", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = AfetCrimson)
                    Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(15.dp))
                }
            }
            alerts.forEachIndexed { index, alert ->
                if (index > 0) HorizontalDivider(color = Zinc100)
                AlertPreview(alert = alert, onClick = { onSelectAlert(alert.id) })
            }
        }
    }
}

@Composable
private fun AlertPreview(alert: Alert, onClick: () -> Unit) {
    val accent = when (alert.severity) {
        AlertSeverity.CRITICAL -> AfetCrimson
        AlertSeverity.WARNING -> AfetAmber
        AlertSeverity.INFO -> AfetBlue
    }
    Row(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(Modifier.size(8.dp).clip(CircleShape).background(accent))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(alert.title, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Zinc900, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text("${alert.category} · ${alert.location}", fontSize = 10.5.sp, color = Zinc500, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Text(alert.occurredAt, fontSize = 10.sp, color = Zinc400, maxLines = 1)
        Icon(Icons.Outlined.ChevronRight, contentDescription = "Uyarı ayrıntısı", tint = Zinc400, modifier = Modifier.size(16.dp))
    }
}

@Composable
private fun QuickActionsGrid(
    onReport: () -> Unit,
    onSafety: () -> Unit,
    onRouting: () -> Unit,
    onChecklist: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(verticalAlignment = Alignment.Bottom) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("Hızlı erişim", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text("Acil durumda ihtiyaç duyacağın araçlar", fontSize = 11.sp, color = Zinc500)
            }
            Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Zinc400, modifier = Modifier.size(17.dp))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuickActionCard("İhbar oluştur", "Durumu bildir", Icons.Outlined.Report, AfetCrimson, onReport, Modifier.weight(1f))
            QuickActionCard("Güvendeyim", "Durumunu paylaş", Icons.Outlined.CheckCircle, Zinc700, onSafety, Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuickActionCard("Güvenli rota", "Yaya güzergâhı", Icons.Outlined.Directions, Zinc700, onRouting, Modifier.weight(1f))
            QuickActionCard("Afet çantası", "Hazırlık listesi", Icons.Outlined.Inventory2, Zinc700, onChecklist, Modifier.weight(1f))
        }
    }
}

@Composable
private fun QuickActionCard(
    title: String,
    detail: String,
    icon: ImageVector,
    accent: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier
            .height(92.dp)
            .clickable(onClick = onClick)
            .semantics { contentDescription = "$title. $detail" },
        shape = RoundedCornerShape(17.dp),
        color = Color.White,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.fillMaxSize().padding(horizontal = 12.dp, vertical = 13.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(shape = RoundedCornerShape(12.dp), color = accent.copy(alpha = 0.10f)) {
                Box(Modifier.size(38.dp), contentAlignment = Alignment.Center) {
                    Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.size(20.dp))
                }
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(title, fontSize = 11.5.sp, fontWeight = FontWeight.Bold, color = Zinc900, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(detail, fontSize = 9.5.sp, color = Zinc500, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun EarthquakeSectionHeader(
    selectedFilter: String,
    onSelectFilter: (String) -> Unit,
    availableCount: Int,
    shownCount: Int,
    showAll: Boolean,
    onToggleShowAll: () -> Unit,
    onMap: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("Son depremler", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text(
                    if (showAll) "$shownCount kayıt gösteriliyor" else "En son 8 kayıt · Resmî katalog",
                    fontSize = 11.sp,
                    color = Zinc500,
                )
            }
            when {
                availableCount > 8 -> TextButton(
                    onClick = onToggleShowAll,
                    contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp),
                ) {
                    Text(
                        if (showAll) "Daha az göster" else "Tümünü gör",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = AfetCrimson,
                    )
                    Icon(
                        Icons.Outlined.ChevronRight,
                        contentDescription = null,
                        tint = AfetCrimson,
                        modifier = Modifier.size(15.dp),
                    )
                }
                else -> TextButton(onClick = onMap, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp)) {
                    Text("Haritayı aç", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = AfetCrimson)
                }
            }
        }

        LazyRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            items(items = HOME_FILTERS, key = { it }, contentType = { "earthquake_filter" }) { filter ->
                FilterChip(
                    selected = selectedFilter == filter,
                    onClick = { onSelectFilter(filter) },
                    label = { Text(filter, fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                    shape = RoundedCornerShape(30.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = AfetCrimson,
                        selectedLabelColor = Color.White,
                        containerColor = Color.White,
                        labelColor = Zinc700,
                    ),
                    border = FilterChipDefaults.filterChipBorder(
                        enabled = true,
                        selected = selectedFilter == filter,
                        borderColor = Zinc200,
                        selectedBorderColor = AfetCrimson,
                    ),
                )
            }
        }
    }
}

@Composable
private fun EarthquakeRow(
    earthquake: Earthquake,
    showDistance: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(17.dp),
        color = Color.White,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 13.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(11.dp),
        ) {
            val severityColor = if (earthquake.magnitude >= 4.0) AfetCrimson else AfetAmber
            Surface(shape = RoundedCornerShape(12.dp), color = severityColor.copy(alpha = 0.10f)) {
                Column(
                    modifier = Modifier.width(55.dp).padding(vertical = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(1.dp),
                ) {
                    Text("M", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = severityColor)
                    Text(magnitudeLabel(earthquake.magnitude), fontSize = 17.sp, fontWeight = FontWeight.Black, color = severityColor)
                }
            }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(
                    earthquake.epicenter,
                    fontSize = 12.5.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Zinc900,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    "${compactTimestamp(earthquake.occurredAt)} · ${earthquake.depthKm.toInt()} km derinlik",
                    fontSize = 10.5.sp,
                    color = Zinc500,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            if (showDistance) {
                Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Icon(Icons.Outlined.LocationOn, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(15.dp))
                    Text(distanceLabel(earthquake.distanceKm), fontSize = 10.sp, fontWeight = FontWeight.SemiBold, color = Zinc700)
                }
            }
            Icon(Icons.Outlined.ChevronRight, contentDescription = "Haritada göster", tint = Zinc400, modifier = Modifier.size(17.dp))
        }
    }
}

@Composable
private fun EarthquakeListEmpty(needsLocation: Boolean, onRequestLocation: () -> Unit) {
    Surface(shape = RoundedCornerShape(17.dp), color = Color.White, border = BorderZinc200) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(15.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Icon(Icons.Outlined.LocationOn, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(20.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(
                    if (needsLocation) "Yakınındaki depremler için konum gerekli" else "Bu filtrede deprem yok",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Zinc900,
                )
                Text(
                    if (needsLocation) "Konumunu alıp yakınlık hesabını yapalım." else "Başka bir filtre deneyebilirsin.",
                    fontSize = 10.5.sp,
                    color = Zinc500,
                )
            }
            if (needsLocation) TextButton(onClick = onRequestLocation) { Text("Konumu aç", color = AfetCrimson, fontSize = 11.sp) }
        }
    }
}

@Composable
private fun AnalysisToolsCard(onDamage: () -> Unit, onNlp: () -> Unit, onOperations: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text("Analiz ve saha", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Zinc950)
            Text("İhtiyaç duyduğunda araçlara buradan ulaş", fontSize = 11.sp, color = Zinc500)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuickActionCard("Hasar analizi", "Fotoğrafla incele", Icons.Outlined.Warning, AfetAmber, onDamage, Modifier.weight(1f))
            QuickActionCard("Metin analizi", "Yardım çağrılarını tara", Icons.Outlined.Report, AfetBlue, onNlp, Modifier.weight(1f))
        }
        Surface(
            modifier = Modifier.fillMaxWidth().clickable(onClick = onOperations),
            shape = RoundedCornerShape(15.dp),
            color = Color.White,
            border = BorderZinc200,
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(9.dp),
            ) {
                Icon(Icons.Outlined.Report, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(18.dp))
                Text("Saha operasyonlarını görüntüle", fontSize = 11.5.sp, fontWeight = FontWeight.SemiBold, color = Zinc800, modifier = Modifier.weight(1f))
                Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Zinc400, modifier = Modifier.size(16.dp))
            }
        }
    }
}

private fun magnitudeLabel(magnitude: Double): String = String.format(Locale.ROOT, "%.1f", magnitude)

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
