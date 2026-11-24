package com.quakemind.feature.home

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.BluetoothSearching
import androidx.compose.material.icons.automirrored.outlined.ShortText
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.Inventory2
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.PhotoCamera
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.quakemind.core.designsystem.AfetAccent
import com.quakemind.core.designsystem.AfetAccentMuted
import com.quakemind.core.designsystem.AfetAmber
import com.quakemind.core.designsystem.AfetBlue
import com.quakemind.core.designsystem.AfetBlueBorder
import com.quakemind.core.designsystem.AfetBlueMuted
import com.quakemind.core.designsystem.AfetCrimson
import com.quakemind.core.designsystem.AfetCrimsonMuted
import com.quakemind.core.designsystem.AfetGreen
import com.quakemind.core.designsystem.AfetGreenMuted
import com.quakemind.core.designsystem.AfetLogoMark
import com.quakemind.core.designsystem.BorderAfetBlueBorder
import com.quakemind.core.designsystem.BorderAfetCrimson1_5
import com.quakemind.core.designsystem.BorderZinc200
import com.quakemind.core.designsystem.EmptyState
import com.quakemind.core.designsystem.OfflineModeBanner
import com.quakemind.core.designsystem.QuakeCard
import com.quakemind.core.designsystem.QuakeMindTheme
import com.quakemind.core.designsystem.RichterIntensityMeter
import com.quakemind.core.designsystem.SeismicMagnitudeBadge
import com.quakemind.core.designsystem.Shape10dp
import com.quakemind.core.designsystem.Shape12dp
import com.quakemind.core.designsystem.Shape14dp
import com.quakemind.core.designsystem.Shape16dp
import com.quakemind.core.designsystem.Shape2dp
import com.quakemind.core.designsystem.Shape6dp
import com.quakemind.core.designsystem.Shape8dp
import com.quakemind.core.designsystem.StatusBadge
import com.quakemind.core.designsystem.Zinc200
import com.quakemind.core.designsystem.Zinc500
import com.quakemind.core.designsystem.Zinc950
import com.quakemind.core.designsystem.formatMagnitude
import com.quakemind.core.designsystem.isDarkSurface
import com.quakemind.core.designsystem.tabular
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.ui.state.AppUiState
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

private val HomeFilters = listOf("Tümü", "M ≥ 4.0", "M ≥ 3.5", "Yakındakiler")

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
    onMesh: () -> Unit = {},
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
        onMesh = onMesh,
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
    onMesh: () -> Unit = {},
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
    val visible = remember(filtered, showAll) { if (showAll) filtered else filtered.take(6) }
    val alerts = remember(state.alerts) { state.alerts.take(2) }
    val unread = remember(state.alerts) { state.alerts.any { !it.isRead } }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding(),
    ) {
        HomeHeader(
            online = state.online,
            hasLocation = state.deviceLocation != null,
            city = state.session?.city,
            unread = unread,
            onAlerts = onAlerts,
            onProfile = onProfile,
        )

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .testTag("home_lazy_column"),
            state = listState,
            contentPadding = PaddingValues(start = 20.dp, top = 8.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            if (!state.online || state.pendingCount > 0) {
                item(key = "offline", contentType = "status") {
                    OfflineModeBanner(
                        pendingCount = state.pendingCount,
                        onOpenMesh = onMesh,
                    )
                }
            }

            item(key = "location", contentType = "location") {
                LocationTelemetryBar(state = state, onRequest = onRequestLocation)
            }

            item(key = "urgent_actions", contentType = "actions") {
                UrgentActionCluster(
                    onReport = onReport,
                    onSafety = onSafety,
                    onSos = onSos,
                )
            }

            item(key = "p2p_mesh", contentType = "mesh") {
                P2pMeshEntryCard(onClick = onMesh)
            }

            item(key = "earthquake_summary", contentType = "summary") {
                if (nearest != null) {
                    EarthquakeSummaryCard(
                        earthquake = nearest,
                        hasLocation = state.deviceLocation != null,
                        onMap = onMap,
                        onRisk = onRisk,
                    )
                } else {
                    QuakeCard {
                        Text("Son deprem kaydı", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        Text(
                            text = "Katalog henüz alınmadı. Bağlantı geldiğinde kayıtlar burada görünür.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Zinc500,
                        )
                        Spacer(Modifier.height(10.dp))
                        TextButton(
                            onClick = onMap,
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
                        ) {
                            Text("Haritayı aç")
                        }
                    }
                }
            }

            if (alerts.isNotEmpty()) {
                item(key = "alerts", contentType = "alerts") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        HomeSectionTitle("Bölgesel uyarılar", "Tümü", onAlerts)
                        QuakeCard(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 6.dp)) {
                            alerts.forEachIndexed { index, alert ->
                                if (index > 0) HorizontalDivider(color = Zinc200)
                                AlertPreviewRow(alert = alert, onClick = { onIncident(alert.id) })
                            }
                        }
                    }
                }
            }

            item(key = "preparedness", contentType = "tools") {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    HomeSectionTitle("Hazırlık ve ulaşım")
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        QuickActionTile(
                            title = "Tahliye rotası",
                            subtitle = "Güvenli güzergâh",
                            icon = Icons.Outlined.Directions,
                            iconTint = AfetAccent,
                            iconBg = AfetAccentMuted,
                            onClick = onRouting,
                            modifier = Modifier.weight(1f),
                        )
                        QuickActionTile(
                            title = "Afet çantası",
                            subtitle = "Hazırlık listesi",
                            icon = Icons.Outlined.Inventory2,
                            iconTint = AfetAccent,
                            iconBg = AfetAccentMuted,
                            onClick = onChecklist,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }

            item(key = "earthquake_filters", contentType = "filters") {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    HomeSectionTitle(
                        title = "Son depremler",
                        action = if (showAll) "Daha az" else "Tümü",
                        onAction = { if (filtered.size > 6) showAll = !showAll else onMap() },
                    )
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        HomeFilters.forEach { option ->
                            val selected = filter == option
                            FilterChip(
                                selected = selected,
                                onClick = { filter = option; showAll = false },
                                label = {
                                    Text(
                                        text = option,
                                        style = MaterialTheme.typography.labelMedium,
                                        fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                                    )
                                },
                                shape = Shape10dp,
                                colors = FilterChipDefaults.filterChipColors(
                                    containerColor = MaterialTheme.colorScheme.surface,
                                    labelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                    selectedContainerColor = MaterialTheme.colorScheme.primaryContainer,
                                    selectedLabelColor = MaterialTheme.colorScheme.onPrimaryContainer,
                                ),
                                border = FilterChipDefaults.filterChipBorder(
                                    enabled = true,
                                    selected = selected,
                                    borderColor = MaterialTheme.colorScheme.outlineVariant,
                                    selectedBorderColor = MaterialTheme.colorScheme.primary,
                                ),
                            )
                        }
                    }
                }
            }

            if (visible.isEmpty()) {
                item(key = "empty_filter", contentType = "empty") {
                    QuakeCard(contentPadding = PaddingValues(8.dp)) {
                        EmptyState(
                            title = "Bu filtrede kayıt yok",
                            detail = if (filter == "Yakındakiler" && state.deviceLocation == null) {
                                "Yakınındaki kayıtları görmek için üstteki konum düğmesini kullan."
                            } else {
                                "Başka bir filtre seçerek kayıtları inceleyebilirsin."
                            },
                        )
                    }
                }
            } else {
                item(key = "earthquake_feed_card", contentType = "earthquake_list") {
                    QuakeCard(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 6.dp)) {
                        visible.forEachIndexed { index, earthquake ->
                            if (index > 0) HorizontalDivider(color = Zinc200)
                            EarthquakeListRow(
                                earthquake = earthquake,
                                hasLocation = state.deviceLocation != null,
                                onClick = onMap,
                            )
                        }
                    }
                }
            }

            item(key = "analysis_tools", contentType = "tools") {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    HomeSectionTitle("İnceleme araçları")
                    QuakeCard(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 6.dp)) {
                        ToolRow(
                            label = "Fotoğrafla hasar incelemesi",
                            subtitle = "Yapısal hasar sınıflandırması",
                            icon = Icons.Outlined.PhotoCamera,
                            onClick = onDamage,
                        )
                        HorizontalDivider(color = Zinc200)
                        ToolRow(
                            label = "Yardım çağrısını analiz et",
                            subtitle = "Metinden aciliyet ve ihtiyaç çıkarımı",
                            icon = Icons.AutoMirrored.Outlined.ShortText,
                            onClick = onNlp,
                        )
                        if (state.session?.capabilities?.contains("operations.view") == true) {
                            HorizontalDivider(color = Zinc200)
                            ToolRow(
                                label = "Saha operasyonları",
                                subtitle = "Görev atama ve doğrulama",
                                icon = Icons.Outlined.SupportAgent,
                                onClick = onOperations,
                            )
                        }
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// HEADER — CONTEXT-DRIVEN (NO GENERIC GREETING)
// ---------------------------------------------------------------------------

@Composable
private fun HomeHeader(
    online: Boolean,
    hasLocation: Boolean,
    city: String?,
    unread: Boolean,
    onAlerts: () -> Unit,
    onProfile: () -> Unit,
) {
    val statusDotColor = if (online) AfetGreen else AfetAmber
    val statusText = buildString {
        append(if (online) "Çevrimiçi" else "Çevrimdışı")
        val region = city?.takeIf { it.isNotBlank() }
        if (region != null) {
            append(" · ")
            append(region)
        } else if (hasLocation) {
            append(" · Konum hazır")
        }
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        AfetLogoMark(size = 38.dp)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                text = "QuakeMind",
                style = MaterialTheme.typography.titleLarge,
                color = Zinc950,
                modifier = Modifier.semantics { heading() },
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Box(Modifier.size(6.dp).background(statusDotColor, CircleShape))
                Text(
                    text = statusText,
                    style = MaterialTheme.typography.bodySmall,
                    color = Zinc500,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }

        HeaderIconButton(
            icon = Icons.Outlined.Notifications,
            contentDescription = if (unread) "Okunmamış uyarılar" else "Uyarılar",
            showBadge = unread,
            onClick = onAlerts,
        )
        HeaderIconButton(
            icon = Icons.Outlined.Person,
            contentDescription = "Profil",
            showBadge = false,
            onClick = onProfile,
        )
    }
}

@Composable
private fun HeaderIconButton(
    icon: ImageVector,
    contentDescription: String,
    showBadge: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        onClick = onClick,
        shape = Shape12dp,
        color = MaterialTheme.colorScheme.surface,
        border = BorderZinc200,
        modifier = Modifier
            .size(44.dp)
            .semantics { this.contentDescription = contentDescription },
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Zinc950,
                modifier = Modifier.size(20.dp),
            )
            if (showBadge) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 8.dp, end = 8.dp)
                        .size(7.dp)
                        .clip(CircleShape)
                        .background(AfetCrimson),
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// COMPACT LOCATION TELEMETRY STRIP
// ---------------------------------------------------------------------------

@Composable
private fun LocationTelemetryBar(state: HomeUiState, onRequest: () -> Unit) {
    Surface(
        shape = Shape12dp,
        color = MaterialTheme.colorScheme.surface,
        border = BorderZinc200,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 52.dp)
                .padding(start = 14.dp, end = 6.dp, top = 6.dp, bottom = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Icon(
                imageVector = Icons.Outlined.MyLocation,
                contentDescription = null,
                tint = if (state.deviceLocation != null) AfetGreen else AfetAccent,
                modifier = Modifier.size(18.dp),
            )
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(1.dp)) {
                Text(
                    text = when {
                        state.isLocating -> "Konum alınıyor…"
                        state.deviceLocation != null -> "Konumun hazır"
                        else -> "Yakınındaki noktaları keşfet"
                    },
                    style = MaterialTheme.typography.labelLarge,
                    color = Zinc950,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                state.locationError?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = AfetCrimson)
                } ?: if (state.deviceLocation != null && state.accuracyMetres != null) {
                    Text(
                        text = "Yaklaşık ±${state.accuracyMetres.toInt()} m doğruluk",
                        style = MaterialTheme.typography.bodySmall.tabular(),
                        color = Zinc500,
                    )
                } else Unit
            }
            TextButton(
                onClick = onRequest,
                enabled = !state.isLocating,
                modifier = Modifier.heightIn(min = 44.dp),
            ) {
                Text(
                    text = if (state.deviceLocation == null) "Konumu bul" else "Yenile",
                    style = MaterialTheme.typography.labelLarge,
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// URGENT ACTION CLUSTER — DECISIVE ABOVE-THE-FOLD HIERARCHY
// ---------------------------------------------------------------------------

@Composable
private fun UrgentActionCluster(
    onReport: () -> Unit,
    onSafety: () -> Unit,
    onSos: () -> Unit,
) {
    val dark = isDarkSurface()
    val primaryBg = if (dark) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.error
    val primaryFg = if (dark) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onError
    val primarySub = primaryFg.copy(alpha = 0.85f)
    val primaryIconBg = if (dark) {
        MaterialTheme.colorScheme.error.copy(alpha = 0.22f)
    } else {
        Color.White.copy(alpha = 0.18f)
    }
    val primaryBorder = if (dark) BorderAfetCrimson1_5 else null

    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Surface(
            onClick = onReport,
            shape = Shape16dp,
            color = primaryBg,
            contentColor = primaryFg,
            border = primaryBorder,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 76.dp)
                    .padding(horizontal = 18.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Surface(
                    shape = Shape12dp,
                    color = primaryIconBg,
                    modifier = Modifier.size(44.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Outlined.Report,
                            contentDescription = null,
                            tint = if (dark) MaterialTheme.colorScheme.error else primaryFg,
                            modifier = Modifier.size(24.dp),
                        )
                    }
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        text = "İhbar oluştur",
                        style = MaterialTheme.typography.titleMedium,
                        color = primaryFg,
                    )
                    Text(
                        text = "Hasar veya yardım ihtiyacını bildir",
                        style = MaterialTheme.typography.bodySmall,
                        color = primarySub,
                    )
                }
                Icon(
                    imageVector = Icons.Outlined.ChevronRight,
                    contentDescription = null,
                    tint = primaryFg.copy(alpha = 0.9f),
                    modifier = Modifier.size(22.dp),
                )
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuickActionTile(
                title = "Güvendeyim",
                subtitle = "Durum paylaş",
                icon = Icons.Outlined.CheckCircle,
                iconTint = AfetGreen,
                iconBg = AfetGreenMuted,
                onClick = onSafety,
                modifier = Modifier.weight(1f),
            )
            QuickActionTile(
                title = "Acil yardım",
                subtitle = "112 ve SOS",
                icon = Icons.Outlined.Call,
                iconTint = AfetCrimson,
                iconBg = AfetCrimsonMuted,
                onClick = onSos,
                modifier = Modifier.weight(1f),
            )
        }
    }
}

@Composable
private fun QuickActionTile(
    title: String,
    subtitle: String,
    icon: ImageVector,
    iconTint: Color,
    iconBg: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = Shape14dp,
        color = MaterialTheme.colorScheme.surface,
        border = BorderZinc200,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 96.dp)
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(
                shape = Shape10dp,
                color = iconBg,
                modifier = Modifier.size(36.dp),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconTint,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleSmall,
                    color = Zinc950,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = Zinc500,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// P2P OFFLINE BLE LOW ENERGY ENTRY CARD
// ---------------------------------------------------------------------------

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun P2pMeshEntryCard(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        shape = Shape16dp,
        color = MaterialTheme.colorScheme.surface,
        border = BorderAfetBlueBorder,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Surface(
                    shape = Shape12dp,
                    color = AfetBlueMuted,
                    modifier = Modifier.size(42.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Outlined.BluetoothSearching,
                            contentDescription = null,
                            tint = AfetBlue,
                            modifier = Modifier.size(22.dp),
                        )
                    }
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                        itemVerticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = "Yakın Ağ (P2P)",
                            style = MaterialTheme.typography.titleSmall,
                            color = Zinc950,
                        )
                        StatusBadge(
                            text = "BLE · Tasarım",
                            backgroundColor = AfetBlueMuted,
                            textColor = MaterialTheme.colorScheme.onTertiaryContainer,
                            borderColor = AfetBlueBorder,
                        )
                    }
                    Text(
                        text = "İnternetsiz düşük enerjili Bluetooth mesh iletişimi",
                        style = MaterialTheme.typography.bodySmall,
                        color = Zinc500,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Icon(
                    imageVector = Icons.Outlined.ChevronRight,
                    contentDescription = null,
                    tint = Zinc500,
                    modifier = Modifier.size(20.dp),
                )
            }

            HorizontalDivider(color = Zinc200)

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "Düşük enerji · ~%1.2/sa · 100 m menzil",
                    style = MaterialTheme.typography.labelSmall.tabular(),
                    color = Zinc500,
                    modifier = Modifier.weight(1f),
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Önizle",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = AfetBlue,
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// SEISMIC TELEMETRY HERO CARD
// ---------------------------------------------------------------------------

@Composable
private fun EarthquakeSummaryCard(
    earthquake: Earthquake,
    hasLocation: Boolean,
    onMap: () -> Unit,
    onRisk: () -> Unit,
) {
    val intensityLabel = when {
        earthquake.magnitude >= 6.0 -> "Şiddetli sarsıntı"
        earthquake.magnitude >= 4.5 -> "Hissedilir sarsıntı"
        earthquake.magnitude >= 3.5 -> "Orta sarsıntı"
        else -> "Hafif sarsıntı"
    }

    QuakeCard(contentPadding = PaddingValues(18.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = if (hasLocation) "Konumuna en yakın deprem" else "Son deprem kaydı",
                style = MaterialTheme.typography.titleMedium,
                color = Zinc950,
                modifier = Modifier.weight(1f),
            )
            Spacer(Modifier.width(8.dp))
            StatusBadge(
                text = earthquake.source.ifBlank { "Katalog" },
                backgroundColor = MaterialTheme.colorScheme.surfaceContainerLow,
                textColor = MaterialTheme.colorScheme.onSurfaceVariant,
                borderColor = MaterialTheme.colorScheme.outlineVariant,
            )
        }

        Spacer(Modifier.height(14.dp))

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            SeismicMagnitudeBadge(magnitude = earthquake.magnitude, size = 68.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(
                    text = earthquake.epicenter,
                    style = MaterialTheme.typography.titleMedium,
                    color = Zinc950,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = compactTimestamp(earthquake.occurredAt),
                    style = MaterialTheme.typography.bodySmall.tabular(),
                    color = Zinc500,
                )
                Text(
                    text = buildString {
                        append("${earthquake.depthKm.toInt()} km derinlik")
                        if (hasLocation) {
                            append(" · ")
                            append(distanceLabel(earthquake.distanceKm))
                            append(" uzakta")
                        }
                    },
                    style = MaterialTheme.typography.bodySmall.tabular(),
                    color = Zinc500,
                )
            }
        }

        Spacer(Modifier.height(14.dp))

        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = intensityLabel,
                    style = MaterialTheme.typography.labelSmall,
                    color = Zinc500,
                )
                Text(
                    text = "Mw ${earthquake.magnitude.formatMagnitude()}",
                    style = MaterialTheme.typography.labelSmall.tabular(),
                    color = Zinc500,
                )
            }
            RichterIntensityMeter(magnitude = earthquake.magnitude)
        }

        Spacer(Modifier.height(14.dp))
        HorizontalDivider(color = Zinc200)
        Spacer(Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(
                onClick = onMap,
                shape = Shape10dp,
                color = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                modifier = Modifier
                    .weight(1f)
                    .heightIn(min = 44.dp),
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp, Alignment.CenterHorizontally),
                ) {
                    Icon(Icons.Outlined.Map, contentDescription = null, modifier = Modifier.size(16.dp))
                    Text("Haritada gör", style = MaterialTheme.typography.labelLarge, maxLines = 1)
                }
            }
            Surface(
                onClick = onRisk,
                shape = Shape10dp,
                color = MaterialTheme.colorScheme.surfaceContainerLow,
                contentColor = Zinc950,
                border = BorderZinc200,
                modifier = Modifier
                    .weight(1f)
                    .heightIn(min = 44.dp),
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp, Alignment.CenterHorizontally),
                ) {
                    Icon(Icons.Outlined.Shield, contentDescription = null, modifier = Modifier.size(16.dp), tint = AfetAccent)
                    Text("Bölgesel risk", style = MaterialTheme.typography.labelLarge, maxLines = 1)
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// SECTION HEADER, ALERTS, FEED & TOOLS
// ---------------------------------------------------------------------------

@Composable
private fun HomeSectionTitle(
    title: String,
    action: String? = null,
    onAction: () -> Unit = {},
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 36.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = Zinc950,
            modifier = Modifier
                .weight(1f)
                .semantics { heading() },
        )
        if (action != null) {
            TextButton(
                onClick = onAction,
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
            ) {
                Text(action, style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@Composable
private fun AlertPreviewRow(alert: Alert, onClick: () -> Unit) {
    val barColor = when (alert.severity) {
        AlertSeverity.CRITICAL -> AfetCrimson
        AlertSeverity.WARNING -> AfetAmber
        AlertSeverity.INFO -> AfetBlue
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(role = Role.Button, onClick = onClick)
            .heightIn(min = 60.dp)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            modifier = Modifier
                .width(3.dp)
                .height(34.dp)
                .clip(Shape2dp)
                .background(barColor),
        )
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(
                text = alert.title,
                style = MaterialTheme.typography.titleSmall,
                color = Zinc950,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = "${alert.category} · ${alert.occurredAt}",
                style = MaterialTheme.typography.bodySmall.tabular(),
                color = Zinc500,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Icon(
            imageVector = Icons.Outlined.ChevronRight,
            contentDescription = null,
            tint = Zinc500,
            modifier = Modifier.size(18.dp),
        )
    }
}

@Composable
private fun EarthquakeListRow(
    earthquake: Earthquake,
    hasLocation: Boolean,
    onClick: () -> Unit,
) {
    val formattedTime = remember(earthquake.occurredAt) { compactTimestamp(earthquake.occurredAt) }
    val formattedDistance = remember(earthquake.distanceKm, hasLocation) {
        if (hasLocation) distanceLabel(earthquake.distanceKm) else null
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(role = Role.Button, onClick = onClick)
            .heightIn(min = 64.dp)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SeismicMagnitudeBadge(magnitude = earthquake.magnitude, size = 46.dp)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(
                text = earthquake.epicenter,
                style = MaterialTheme.typography.titleSmall,
                color = Zinc950,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = "$formattedTime · ${earthquake.depthKm.toInt()} km",
                style = MaterialTheme.typography.bodySmall.tabular(),
                color = Zinc500,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            if (formattedDistance != null) {
                Text(
                    text = formattedDistance,
                    style = MaterialTheme.typography.labelMedium.tabular(),
                    color = Zinc500,
                )
            }
            Icon(
                imageVector = Icons.Outlined.ChevronRight,
                contentDescription = null,
                tint = Zinc500,
                modifier = Modifier.size(18.dp),
            )
        }
    }
}

@Composable
private fun ToolRow(
    label: String,
    subtitle: String,
    icon: ImageVector,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(role = Role.Button, onClick = onClick)
            .heightIn(min = 60.dp)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Surface(
            shape = Shape10dp,
            color = AfetAccentMuted,
            modifier = Modifier.size(36.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = AfetAccent,
                    modifier = Modifier.size(18.dp),
                )
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(text = label, style = MaterialTheme.typography.titleSmall, color = Zinc950)
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = Zinc500,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Icon(
            imageVector = Icons.Outlined.ChevronRight,
            contentDescription = null,
            tint = Zinc500,
            modifier = Modifier.size(18.dp),
        )
    }
}

// ---------------------------------------------------------------------------
// PREVIEWS & HELPERS
// ---------------------------------------------------------------------------

private val PreviewEarthquakes = listOf(
    Earthquake("p-1", 4.4, 7.2, "Marmara Denizi · Silivri açıkları", "2026-11-24T14:32:00Z", 34.0, "Kandilli"),
    Earthquake("p-2", 3.3, 5.0, "Çeşme açıkları · İzmir", "2026-11-24T11:15:00Z", 312.4, "AFAD"),
    Earthquake("p-3", 2.1, 11.0, "Sındırgı · Balıkesir", "2026-11-24T09:05:00Z", 188.2, "Kandilli"),
)

@Preview(name = "Home · Light", showBackground = true)
@Composable
private fun HomeLightPreview() {
    QuakeMindTheme(darkTheme = false) {
        HomeScreen(
            state = HomeUiState(earthquakes = PreviewEarthquakes, online = true),
            onMap = {}, onReport = {}, onSos = {}, onSafety = {}, onAlerts = {},
            onRouting = {}, onDamage = {}, onNlp = {}, onRisk = {}, onChecklist = {},
            onOperations = {}, onProfile = {}, onIncident = {},
        )
    }
}

@Preview(name = "Home · Dark", showBackground = true)
@Composable
private fun HomeDarkPreview() {
    QuakeMindTheme(darkTheme = true) {
        HomeScreen(
            state = HomeUiState(earthquakes = PreviewEarthquakes, online = false, pendingCount = 2),
            onMap = {}, onReport = {}, onSos = {}, onSafety = {}, onAlerts = {},
            onRouting = {}, onDamage = {}, onNlp = {}, onRisk = {}, onChecklist = {},
            onOperations = {}, onProfile = {}, onIncident = {},
        )
    }
}

private fun distanceLabel(distanceKm: Double): String {
    if (distanceKm < 1.0) return "${(distanceKm * 1_000).toInt()} m"
    val tenths = (distanceKm * 10.0 + 0.5).toLong()
    return "${tenths / 10}.${tenths % 10} km"
}

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
