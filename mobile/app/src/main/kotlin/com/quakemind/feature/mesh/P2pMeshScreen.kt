package com.quakemind.feature.mesh

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.BluetoothSearching
import androidx.compose.material.icons.outlined.BatteryChargingFull
import androidx.compose.material.icons.outlined.Bluetooth
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.LocalHospital
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Sensors
import androidx.compose.material.icons.outlined.Sos
import androidx.compose.material.icons.outlined.WaterDrop
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
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
import com.quakemind.core.designsystem.AfetCrimsonBorder
import com.quakemind.core.designsystem.AfetCrimsonMuted
import com.quakemind.core.designsystem.AfetGreen
import com.quakemind.core.designsystem.AfetGreenMuted
import com.quakemind.core.designsystem.BorderAfetBlueBorder
import com.quakemind.core.designsystem.BorderAfetCrimsonBorder
import com.quakemind.core.designsystem.BorderZinc200
import com.quakemind.core.designsystem.QuakeCard
import com.quakemind.core.designsystem.QuakeMindTheme
import com.quakemind.core.designsystem.ScreenHeader
import com.quakemind.core.designsystem.Shape10dp
import com.quakemind.core.designsystem.Shape12dp
import com.quakemind.core.designsystem.Shape14dp
import com.quakemind.core.designsystem.Shape6dp
import com.quakemind.core.designsystem.Shape8dp
import com.quakemind.core.designsystem.StatusBadge
import com.quakemind.core.designsystem.Zinc200
import com.quakemind.core.designsystem.Zinc500
import com.quakemind.core.designsystem.Zinc950
import com.quakemind.core.designsystem.tabular

private data class BlePowerProfile(
    val id: String,
    val title: String,
    val interval: String,
    val batteryRate: String,
    val maxHops: String,
    val summary: String,
)

private data class QuickPacketTemplate(
    val id: String,
    val title: String,
    val subtitle: String,
    val payloadBytes: Int,
    val icon: ImageVector,
    val urgent: Boolean = false,
)

private data class SampleRelayNode(
    val code: String,
    val label: String,
    val hopsLabel: String,
    val distanceLabel: String,
    val rssiDbm: Int,
    val bars: Int,
)

private val PowerProfiles = listOf(
    BlePowerProfile(
        id = "ultra_low",
        title = "Ultra Düşük",
        interval = "30 sn aralık",
        batteryRate = "~%0.7 / sa",
        maxHops = "2 röle",
        summary = "Uzun süreli kesintilerde 48+ saat pil koruması için pasif BLE işaretçi taraması.",
    ),
    BlePowerProfile(
        id = "balanced",
        title = "Dengeli",
        interval = "15 sn aralık",
        batteryRate = "~%1.2 / sa",
        maxHops = "3 röle",
        summary = "Afet sonrası yakın çevre keşfi ve kısa durum paketleri için önerilen profil.",
    ),
    BlePowerProfile(
        id = "relay",
        title = "Aktif Röle",
        interval = "5 sn aralık",
        batteryRate = "~%2.8 / sa",
        maxHops = "5 röle",
        summary = "Yakındaki cihazlardan gelen acil paketleri şifreli olarak diğer düğümlere iletir.",
    ),
)

private val QuickPackets = listOf(
    QuickPacketTemplate("safe", "Güvendeyim", "Konum + pil", 20, Icons.Outlined.CheckCircle),
    QuickPacketTemplate("water", "Su ve gıda", "Bölge ihtiyacı", 24, Icons.Outlined.WaterDrop),
    QuickPacketTemplate("medical", "Tıbbi destek", "İlk yardım", 24, Icons.Outlined.LocalHospital),
    QuickPacketTemplate("sos", "Acil konum", "Enkaz / mahsur", 28, Icons.Outlined.Sos, urgent = true),
)

private val SampleNodes = listOf(
    SampleRelayNode("QM-48A", "Yakın cihaz · Doğrudan", "Doğrudan", "~18 m", -58, 4),
    SampleRelayNode("QM-19C", "Gönüllü düğüm", "1 röle", "~42 m", -74, 3),
    SampleRelayNode("TA-04", "Toplanma alanı rölesi", "2 röle", "~85 m", -86, 2),
)

/**
 * UI/UX design preview for the upcoming Offline BLE Low-Energy P2P Mesh feature.
 * No live Bluetooth radio or peer networking is executed yet; preview state stays local.
 */
@Composable
fun P2pMeshScreen(
    onBack: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    var previewListening by rememberSaveable { mutableStateOf(true) }
    var selectedProfileIndex by rememberSaveable { mutableIntStateOf(1) }
    var selectedPacketId by rememberSaveable { mutableStateOf("safe") }

    val activeProfile = PowerProfiles[selectedProfileIndex]
    val selectedPacket = QuickPackets.firstOrNull { it.id == selectedPacketId } ?: QuickPackets.first()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding(),
    ) {
        ScreenHeader(
            title = "Yakın Ağ (P2P)",
            subtitle = "İnternetsiz Bluetooth Low Energy mesh",
            onBack = onBack,
            actions = {
                StatusBadge(
                    text = "Tasarım",
                    backgroundColor = AfetBlueMuted,
                    textColor = MaterialTheme.colorScheme.onTertiaryContainer,
                    borderColor = AfetBlueBorder,
                )
            },
        )

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .testTag("p2p_mesh_lazy_column"),
            contentPadding = PaddingValues(start = 20.dp, top = 4.dp, end = 20.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item(key = "preview_notice") {
                Surface(
                    shape = Shape12dp,
                    color = MaterialTheme.colorScheme.surfaceContainerLow,
                    border = BorderZinc200,
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 14.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.Top,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Icon(
                            imageVector = Icons.Outlined.Info,
                            contentDescription = null,
                            tint = AfetBlue,
                            modifier = Modifier
                                .padding(top = 1.dp)
                                .size(18.dp),
                        )
                        Text(
                            text = "Altyapı hazırlık aşamasında. Bu ekran BLE 5.0+ düşük enerjili çevrimdışı haberleşme akışının arayüz tasarımıdır; gerçek cihaz taraması sonraki sürümde etkinleşecektir.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }

            item(key = "radar_hero") {
                QuakeCard(contentPadding = PaddingValues(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Surface(
                            shape = Shape10dp,
                            color = if (previewListening) AfetBlueMuted else MaterialTheme.colorScheme.surfaceContainerHigh,
                            modifier = Modifier.size(40.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = if (previewListening) Icons.AutoMirrored.Outlined.BluetoothSearching else Icons.Outlined.Bluetooth,
                                    contentDescription = null,
                                    tint = if (previewListening) AfetBlue else Zinc500,
                                    modifier = Modifier.size(20.dp),
                                )
                            }
                        }
                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text(
                                text = if (previewListening) "Mesh dinleme görünümü" else "Bekleme görünümü",
                                style = MaterialTheme.typography.titleMedium,
                                color = Zinc950,
                            )
                            Text(
                                text = if (previewListening) "Şebeke yokken yakındaki cihazlarla paket aktarımı" else "Radyo beklemede · Pil koruma modu",
                                style = MaterialTheme.typography.bodySmall,
                                color = Zinc500,
                            )
                        }
                        Switch(
                            checked = previewListening,
                            onCheckedChange = { previewListening = it },
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = MaterialTheme.colorScheme.onTertiary,
                                checkedTrackColor = AfetBlue,
                            ),
                        )
                    }

                    Spacer(Modifier.height(16.dp))

                    BleMeshFieldDiagram(
                        active = previewListening,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(184.dp),
                    )

                    Spacer(Modifier.height(16.dp))
                    HorizontalDivider(color = Zinc200)
                    Spacer(Modifier.height(14.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        TelemetryCell(
                            label = "Protokol",
                            value = "BLE 5.0",
                            modifier = Modifier.weight(1f),
                        )
                        TelemetryCell(
                            label = "Enerji",
                            value = activeProfile.batteryRate,
                            modifier = Modifier.weight(1f),
                        )
                        TelemetryCell(
                            label = "Kapsama",
                            value = activeProfile.maxHops,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }

            item(key = "power_profiles") {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(
                            text = "Düşük enerji profili",
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.semantics { heading() },
                        )
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.BatteryChargingFull,
                                contentDescription = null,
                                tint = AfetGreen,
                                modifier = Modifier.size(16.dp),
                            )
                            Text(
                                text = activeProfile.interval,
                                style = MaterialTheme.typography.labelMedium.tabular(),
                                color = Zinc500,
                            )
                        }
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        PowerProfiles.forEachIndexed { index, profile ->
                            val selected = index == selectedProfileIndex
                            Surface(
                                onClick = { selectedProfileIndex = index },
                                modifier = Modifier
                                    .weight(1f)
                                    .heightIn(min = 68.dp),
                                shape = Shape12dp,
                                color = if (selected) AfetBlueMuted else MaterialTheme.colorScheme.surface,
                                border = if (selected) BorderStroke(1.5.dp, AfetBlue) else BorderZinc200,
                            ) {
                                Column(
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 12.dp),
                                    verticalArrangement = Arrangement.spacedBy(4.dp),
                                ) {
                                    Text(
                                        text = profile.title,
                                        style = MaterialTheme.typography.labelLarge,
                                        color = if (selected) MaterialTheme.colorScheme.onTertiaryContainer else Zinc950,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                    Text(
                                        text = profile.batteryRate,
                                        style = MaterialTheme.typography.bodySmall.tabular(),
                                        color = if (selected) MaterialTheme.colorScheme.onTertiaryContainer else Zinc500,
                                        maxLines = 1,
                                    )
                                }
                            }
                        }
                    }

                    Text(
                        text = activeProfile.summary,
                        style = MaterialTheme.typography.bodySmall,
                        color = Zinc500,
                    )
                }
            }

            item(key = "quick_broadcasts") {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        text = "Hızlı çevrimdışı paketler",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.semantics { heading() },
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        QuickPackets.chunked(2).forEach { row ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp),
                            ) {
                                row.forEach { packet ->
                                    val selected = packet.id == selectedPacket.id
                                    val accentTint = if (packet.urgent) AfetCrimson else AfetAccent
                                    val selectedContainer = if (packet.urgent) AfetCrimsonMuted else AfetAccentMuted
                                    val selectedBorder = if (packet.urgent) BorderStroke(1.5.dp, AfetCrimson) else BorderStroke(1.5.dp, AfetAccent)

                                    Surface(
                                        onClick = { selectedPacketId = packet.id },
                                        modifier = Modifier
                                            .weight(1f)
                                            .heightIn(min = 84.dp),
                                        shape = Shape14dp,
                                        color = if (selected) selectedContainer else MaterialTheme.colorScheme.surface,
                                        border = if (selected) selectedBorder else BorderZinc200,
                                    ) {
                                        Column(
                                            modifier = Modifier.padding(14.dp),
                                            verticalArrangement = Arrangement.spacedBy(8.dp),
                                        ) {
                                            Row(
                                                modifier = Modifier.fillMaxWidth(),
                                                verticalAlignment = Alignment.CenterVertically,
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                            ) {
                                                Icon(
                                                    imageVector = packet.icon,
                                                    contentDescription = null,
                                                    tint = accentTint,
                                                    modifier = Modifier.size(20.dp),
                                                )
                                                Text(
                                                    text = "${packet.payloadBytes} B",
                                                    style = MaterialTheme.typography.labelSmall.tabular(),
                                                    color = Zinc500,
                                                )
                                            }
                                            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                                Text(
                                                    text = packet.title,
                                                    style = MaterialTheme.typography.titleSmall,
                                                    color = Zinc950,
                                                )
                                                Text(
                                                    text = packet.subtitle,
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = Zinc500,
                                                    maxLines = 1,
                                                    overflow = TextOverflow.Ellipsis,
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Packet format preview box
                    Surface(
                        shape = Shape14dp,
                        color = MaterialTheme.colorScheme.surface,
                        border = if (selectedPacket.urgent) BorderAfetCrimsonBorder else BorderAfetBlueBorder,
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                                ) {
                                    Icon(
                                        imageVector = Icons.Outlined.Lock,
                                        contentDescription = null,
                                        tint = AfetBlue,
                                        modifier = Modifier.size(16.dp),
                                    )
                                    Text(
                                        text = "Seçili paket önizlemesi",
                                        style = MaterialTheme.typography.titleSmall,
                                        color = Zinc950,
                                    )
                                }
                                Text(
                                    text = "${selectedPacket.payloadBytes} byte · Şifreli",
                                    style = MaterialTheme.typography.labelSmall.tabular(),
                                    color = Zinc500,
                                )
                            }
                            Text(
                                text = "İçerik: \"${selectedPacket.title}\" · GPS koordinatı + zaman damgası · En fazla ${activeProfile.maxHops} üzerinden aktarılır.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            Surface(
                                shape = Shape10dp,
                                color = MaterialTheme.colorScheme.surfaceContainerHigh,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 48.dp),
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 14.dp, vertical = 12.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.Center,
                                ) {
                                    Icon(
                                        imageVector = Icons.Outlined.Sensors,
                                        contentDescription = null,
                                        tint = Zinc500,
                                        modifier = Modifier.size(18.dp),
                                    )
                                    Spacer(Modifier.width(8.dp))
                                    Text(
                                        text = "BLE yayın altyapısı sonraki aşamada eklenecek",
                                        style = MaterialTheme.typography.labelLarge,
                                        color = Zinc500,
                                    )
                                }
                            }
                        }
                    }
                }
            }

            item(key = "sample_nodes") {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(
                            text = "Yakındaki düğümler",
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.semantics { heading() },
                        )
                        Text(
                            text = "Örnek görünüm",
                            style = MaterialTheme.typography.labelMedium,
                            color = Zinc500,
                        )
                    }
                    QuakeCard(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)) {
                        SampleNodes.forEachIndexed { index, node ->
                            if (index > 0) HorizontalDivider(color = Zinc200)
                            RelayNodeRow(node = node, active = previewListening)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun BleMeshFieldDiagram(
    active: Boolean,
    modifier: Modifier = Modifier,
) {
    val surfaceContainer = MaterialTheme.colorScheme.surfaceContainerLow
    val ringColor = MaterialTheme.colorScheme.outlineVariant
    val activeAccent = if (active) AfetBlue else MaterialTheme.colorScheme.outline
    val centerFill = if (active) AfetAccent else MaterialTheme.colorScheme.outline
    val nodeFill = if (active) AfetGreen else MaterialTheme.colorScheme.outline
    val textColor = MaterialTheme.colorScheme.onSurfaceVariant

    Surface(
        modifier = modifier,
        shape = Shape12dp,
        color = surfaceContainer,
        border = BorderZinc200,
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val center = Offset(size.width / 2f, size.height / 2f)
                val maxRadius = (minOf(size.width, size.height) / 2f) - 16.dp.toPx()
                val radii = listOf(maxRadius * 0.36f, maxRadius * 0.68f, maxRadius)

                // Subtle crosshair axes
                val axisColor = ringColor.copy(alpha = 0.65f)
                drawLine(
                    color = axisColor,
                    start = Offset(center.x - maxRadius, center.y),
                    end = Offset(center.x + maxRadius, center.y),
                    strokeWidth = 1.dp.toPx(),
                )
                drawLine(
                    color = axisColor,
                    start = Offset(center.x, center.y - maxRadius),
                    end = Offset(center.x, center.y + maxRadius),
                    strokeWidth = 1.dp.toPx(),
                )

                // Concentric distance rings
                radii.forEachIndexed { idx, r ->
                    drawCircle(
                        color = if (active && idx == 0) activeAccent.copy(alpha = 0.35f) else ringColor,
                        radius = r,
                        center = center,
                        style = Stroke(
                            width = 1.dp.toPx(),
                            pathEffect = if (idx == 2) PathEffect.dashPathEffect(floatArrayOf(8f, 8f)) else null,
                        ),
                    )
                }

                // Sample peer positions (design preview)
                val peerA = Offset(center.x + maxRadius * 0.34f, center.y - maxRadius * 0.24f)
                val peerB = Offset(center.x - maxRadius * 0.56f, center.y + maxRadius * 0.26f)
                val peerC = Offset(center.x + maxRadius * 0.62f, center.y + maxRadius * 0.44f)

                if (active) {
                    // Mesh hop links (crisp dashed telemetry lines)
                    val dash = PathEffect.dashPathEffect(floatArrayOf(10f, 6f))
                    drawLine(activeAccent.copy(alpha = 0.55f), center, peerA, strokeWidth = 1.5.dp.toPx(), pathEffect = dash)
                    drawLine(activeAccent.copy(alpha = 0.45f), center, peerB, strokeWidth = 1.5.dp.toPx(), pathEffect = dash)
                    drawLine(activeAccent.copy(alpha = 0.35f), peerA, peerC, strokeWidth = 1.5.dp.toPx(), pathEffect = dash)
                }

                // Peer dots
                listOf(peerA, peerB, peerC).forEach { pos ->
                    drawCircle(color = nodeFill.copy(alpha = 0.20f), radius = 9.dp.toPx(), center = pos)
                    drawCircle(color = nodeFill, radius = 4.dp.toPx(), center = pos)
                }

                // Local device node at center
                drawCircle(color = centerFill.copy(alpha = 0.20f), radius = 12.dp.toPx(), center = center)
                drawCircle(color = centerFill, radius = 5.5.dp.toPx(), center = center)
            }

            // Distance scale markers
            Text(
                text = "100 m menzil",
                style = MaterialTheme.typography.labelSmall.tabular(),
                color = textColor,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(10.dp),
            )
            Surface(
                shape = Shape6dp,
                color = MaterialTheme.colorScheme.surface,
                border = BorderZinc200,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(10.dp),
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(5.dp),
                ) {
                    Box(
                        Modifier
                            .size(6.dp)
                            .background(if (active) AfetGreen else AfetAmber, CircleShape),
                    )
                    Text(
                        text = if (active) "3 örnek düğüm" else "Pasif",
                        style = MaterialTheme.typography.labelSmall.tabular(),
                        color = Zinc950,
                    )
                }
            }
        }
    }
}

@Composable
private fun TelemetryCell(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = Zinc500,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleSmall.tabular(),
            color = Zinc950,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun RelayNodeRow(
    node: SampleRelayNode,
    active: Boolean,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 60.dp)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Surface(
            shape = Shape10dp,
            color = if (active) AfetGreenMuted else MaterialTheme.colorScheme.surfaceContainerHigh,
            modifier = Modifier.size(38.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = Icons.Outlined.LocationOn,
                    contentDescription = null,
                    tint = if (active) AfetGreen else Zinc500,
                    modifier = Modifier.size(18.dp),
                )
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text(
                    text = node.code,
                    style = MaterialTheme.typography.titleSmall.tabular(),
                    color = Zinc950,
                )
                Text(
                    text = "· ${node.hopsLabel}",
                    style = MaterialTheme.typography.labelMedium,
                    color = AfetBlue,
                )
            }
            Text(
                text = "${node.label} · ${node.distanceLabel}",
                style = MaterialTheme.typography.bodySmall.tabular(),
                color = Zinc500,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Column(
            horizontalAlignment = Alignment.End,
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            SignalBars(activeBars = if (active) node.bars else 0)
            Text(
                text = if (active) "${node.rssiDbm} dBm" else "-- dBm",
                style = MaterialTheme.typography.labelSmall.tabular(),
                color = Zinc500,
            )
        }
    }
}

@Composable
private fun SignalBars(
    activeBars: Int,
    modifier: Modifier = Modifier,
) {
    val activeColor = AfetGreen
    val mutedColor = MaterialTheme.colorScheme.surfaceContainerHighest
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(2.dp),
        verticalAlignment = Alignment.Bottom,
    ) {
        listOf(6.dp, 9.dp, 12.dp, 15.dp).forEachIndexed { idx, height ->
            Box(
                modifier = Modifier
                    .width(3.dp)
                    .height(height)
                    .clip(Shape6dp)
                    .background(if (idx < activeBars) activeColor else mutedColor),
            )
        }
    }
}

@Preview(name = "P2P Mesh · Light", showBackground = true)
@Composable
private fun P2pMeshLightPreview() {
    QuakeMindTheme(darkTheme = false) {
        P2pMeshScreen()
    }
}

@Preview(name = "P2P Mesh · Dark", showBackground = true)
@Composable
private fun P2pMeshDarkPreview() {
    QuakeMindTheme(darkTheme = true) {
        P2pMeshScreen()
    }
}
