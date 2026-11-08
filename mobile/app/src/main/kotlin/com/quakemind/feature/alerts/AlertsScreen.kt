package com.quakemind.feature.alerts

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.DoneAll
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Notifications
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.runtime.saveable.rememberSaveable
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.ui.state.AppUiState

@Composable
fun AlertsScreen(
    state: AppUiState,
    onMarkAllRead: () -> Unit,
    onSelectAlert: (String) -> Unit,
) {
    AlertsScreen(
        state = AlertsUiState(alerts = state.alerts),
        onMarkAllRead = onMarkAllRead,
        onSelectAlert = onSelectAlert,
    )
}

private val ALERT_CATEGORIES = listOf("Tümü", "Kritik", "Deprem", "Tahliye", "Hava Durumu")

@Composable
fun AlertsScreen(
    state: AlertsUiState,
    onMarkAllRead: () -> Unit,
    onSelectAlert: (String) -> Unit,
) {
    val listState = rememberLazyListState()
    var selectedCategory by rememberSaveable { mutableStateOf("Tümü") }

    val filteredAlerts = remember(selectedCategory, state.alerts) {
        when (selectedCategory) {
            "Kritik" -> state.alerts.filter { it.severity == AlertSeverity.CRITICAL }
            "Deprem" -> state.alerts.filter { it.category.contains("Deprem", ignoreCase = true) }
            "Tahliye" -> state.alerts.filter { it.category.contains("Tahliye", ignoreCase = true) }
            else -> state.alerts
        }
    }
    val unreadCount = remember(state.alerts) { state.alerts.count { !it.isRead } }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .statusBarsPadding()
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 18.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column {
                Text(
                    text = "Bölgesel Bildirimler & Uyarılar",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = Zinc950,
                )
                Text(
                    text = "$unreadCount okunmamış kritik uyarı",
                    fontSize = 12.sp,
                    color = Zinc500,
                )
            }

            TextButton(onClick = onMarkAllRead) {
                Icon(Icons.Outlined.DoneAll, contentDescription = null, modifier = Modifier.size(16.dp), tint = AfetCrimson)
                Spacer(Modifier.width(4.dp))
                Text("Okundu Say", fontSize = 12.5.sp, fontWeight = FontWeight.SemiBold, color = AfetCrimson)
            }
        }

        // Category Filter Chips
        LazyRow(
            modifier = Modifier.fillMaxWidth(),
            contentPadding = PaddingValues(horizontal = 18.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            items(
                items = ALERT_CATEGORIES,
                key = { it },
                contentType = { "filter_chip" },
            ) { cat ->
                FilterChip(
                    selected = selectedCategory == cat,
                    onClick = { selectedCategory = cat },
                    label = { Text(cat, fontSize = 12.sp, fontWeight = FontWeight.Medium) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = AfetCrimson,
                        selectedLabelColor = Color.White,
                        containerColor = Zinc50,
                        labelColor = Zinc700,
                    ),
                    border = FilterChipDefaults.filterChipBorder(
                        enabled = true,
                        selected = selectedCategory == cat,
                        borderColor = Zinc200,
                        selectedBorderColor = AfetCrimson,
                    ),
                )
            }
        }

        Spacer(Modifier.height(10.dp))

        // Alerts List
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .testTag("alerts_lazy_column"),
            state = listState,
            contentPadding = PaddingValues(start = 18.dp, end = 18.dp, top = 4.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {

            if (filteredAlerts.isEmpty()) {
                item(key = "empty_alerts_state", contentType = "empty_state") {
                    EmptyState(
                        title = "Aktif Uyarı Yok",
                        detail = "Bölgenizde şu an için bildirilmiş bir acil durum uyarısı bulunmamaktadır.",
                    )
                }
            } else {
                items(
                    items = filteredAlerts,
                    key = { it.id },
                    contentType = { "alert_item" },
                ) { alert ->
                    AlertItemCard(
                        alert = alert,
                        onClick = { onSelectAlert(alert.id) },
                    )
                }
            }
        }
    }
}

@Composable
private fun AlertItemCard(
    alert: Alert,
    onClick: () -> Unit,
) {
    val (badgeBg, badgeText, badgeBorder) = when (alert.severity) {
        AlertSeverity.CRITICAL -> Triple(AfetCrimsonMuted, AfetCrimson, AfetCrimsonBorder)
        AlertSeverity.WARNING -> Triple(AfetAmberMuted, AfetAmber, AfetAmberBorder)
        AlertSeverity.INFO -> Triple(AfetBlueMuted, AfetBlue, AfetBlueBorder)
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = Shape12dp,
        color = Color.White,
        border = if (!alert.isRead && alert.severity == AlertSeverity.CRITICAL) BorderAfetCrimsonBorder else BorderZinc200,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            // Top Row: Category + Unread dot + Timestamp
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Surface(
                        shape = Shape4dp,
                        color = badgeBg,
                        border = androidx.compose.foundation.BorderStroke(1.dp, badgeBorder),
                    ) {
                        Text(
                            text = alert.category.uppercase(),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = badgeText,
                            letterSpacing = 0.5.sp,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                        )
                    }

                    if (!alert.isRead) {
                        Surface(
                            shape = Shape4dp,
                            color = AfetCrimsonMuted,
                            border = BorderAfetCrimsonBorder,
                        ) {
                            Text(
                                text = "YENİ",
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                color = AfetCrimson,
                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp),
                            )
                        }
                    }
                }

                Text(
                    text = alert.occurredAt,
                    fontSize = 11.5.sp,
                    color = Zinc400,
                )
            }

            // Title
            Text(
                text = alert.title,
                fontSize = 14.5.sp,
                fontWeight = FontWeight.Bold,
                color = Zinc950,
                lineHeight = 20.sp,
            )

            // Detail description excerpt
            Text(
                text = alert.detail,
                fontSize = 12.5.sp,
                color = Zinc600,
                lineHeight = 18.sp,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )

            HorizontalDivider(color = Zinc100)

            // Bottom action row: Affected location + View directives CTA
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.weight(1f, fill = false),
                ) {
                    Icon(
                        imageVector = Icons.Outlined.LocationOn,
                        contentDescription = null,
                        tint = Zinc400,
                        modifier = Modifier.size(13.dp),
                    )
                    Text(
                        text = alert.location,
                        fontSize = 11.5.sp,
                        color = Zinc500,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Text(
                        text = "Detayları Oku",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = AfetCrimson,
                    )
                    Icon(
                        imageVector = Icons.Outlined.ChevronRight,
                        contentDescription = null,
                        tint = AfetCrimson,
                        modifier = Modifier.size(14.dp),
                    )
                }
            }
        }
    }
}
