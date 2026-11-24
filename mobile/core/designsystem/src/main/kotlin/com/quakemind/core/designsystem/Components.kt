package com.quakemind.core.designsystem

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Bluetooth
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.Urgency

// ---------------------------------------------------------------------------
// SHARED SURFACES AND STATUS
// ---------------------------------------------------------------------------

@Composable
fun QuakeCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    containerColor: Color = MaterialTheme.colorScheme.surface,
    border: BorderStroke = BorderZinc200,
    contentPadding: PaddingValues = PaddingValues(20.dp),
    content: @Composable ColumnScope.() -> Unit,
) {
    val cardContent: @Composable () -> Unit = {
        Column(modifier = Modifier.padding(contentPadding), content = content)
    }
    if (onClick == null) {
        Surface(
            modifier = modifier.fillMaxWidth(),
            shape = Shape16dp,
            color = containerColor,
            border = border,
            content = cardContent,
        )
    } else {
        Surface(
            onClick = onClick,
            modifier = modifier.fillMaxWidth(),
            shape = Shape16dp,
            color = containerColor,
            border = border,
            content = cardContent,
        )
    }
}

@Composable
fun StatusBadge(
    text: String,
    modifier: Modifier = Modifier,
    backgroundColor: Color = Zinc100,
    textColor: Color = Zinc900,
    borderColor: Color = Zinc200,
) {
    Surface(
        modifier = modifier,
        shape = Shape6dp,
        color = backgroundColor,
        border = BorderStroke(1.dp, borderColor),
    ) {
        Text(
            text = text,
            color = textColor,
            style = MaterialTheme.typography.labelMedium.tabular(),
            fontWeight = FontWeight.SemiBold,
            maxLines = 1,
            softWrap = false,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}

// ---------------------------------------------------------------------------
// GEOMETRIC LOGO MARK — ZERO ALLOCATION ON DRAW
// ---------------------------------------------------------------------------

@Composable
fun AfetLogoMark(
    modifier: Modifier = Modifier,
    size: Dp = 32.dp,
    color: Color = AfetAccent,
) {
    val markForeground = androidx.compose.material3.contentColorFor(color)
    Surface(
        modifier = modifier.size(size),
        shape = RoundedCornerShape(size * 0.28f),
        color = color,
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {
            Box(
                modifier = Modifier
                    .size(size * 0.56f)
                    .drawWithCache {
                        val w = this.size.width
                        val h = this.size.height
                        val path = Path().apply {
                            moveTo(w * 0.14f, h * 0.86f)
                            lineTo(w * 0.50f, h * 0.14f)
                            lineTo(w * 0.86f, h * 0.86f)
                            lineTo(w * 0.66f, h * 0.86f)
                            lineTo(w * 0.50f, h * 0.50f)
                            lineTo(w * 0.34f, h * 0.86f)
                            close()
                        }
                        onDrawBehind {
                            drawPath(path = path, color = markForeground)
                        }
                    },
            )
        }
    }
}

@Composable
fun AfetLogoHeader(
    modifier: Modifier = Modifier,
    textColor: Color = Zinc950,
    showSubtitle: Boolean = true,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        AfetLogoMark(size = 44.dp, color = AfetAccent)
        Spacer(Modifier.height(12.dp))
        Text(
            text = "QuakeMind",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.SemiBold,
            color = textColor,
        )
        if (showSubtitle) {
            Spacer(Modifier.height(4.dp))
            Text(
                text = "Deprem ve Acil Durum Karar Destek Ağı",
                style = MaterialTheme.typography.bodyMedium,
                color = Zinc500,
            )
        }
    }
}

// ---------------------------------------------------------------------------
// SEISMIC MAGNITUDE BADGE & INTENSITY METER
// ---------------------------------------------------------------------------

@Composable
fun SeismicMagnitudeBadge(
    magnitude: Double,
    modifier: Modifier = Modifier,
    size: Dp = 48.dp,
    showPulse: Boolean = false,
) {
    val (bgColor, textColor, border) = when {
        magnitude >= 4.5 -> Triple(AfetCrimsonMuted, AfetCrimson, BorderAfetCrimsonBorder)
        magnitude >= 3.5 -> Triple(AfetAmberMuted, AfetAmber, BorderAfetAmberBorder)
        else -> Triple(AfetGreenMuted, AfetGreen, BorderAfetGreenBorder)
    }

    val cornerRadius = if (size >= 60.dp) Shape14dp else Shape10dp

    Surface(
        modifier = modifier.size(size),
        shape = cornerRadius,
        color = bgColor,
        border = border,
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier.align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                if (size >= 60.dp) {
                    Text(
                        text = "Mw",
                        style = MaterialTheme.typography.labelSmall,
                        color = textColor.copy(alpha = 0.78f),
                    )
                }
                Text(
                    text = magnitude.formatMagnitude(),
                    style = if (size >= 60.dp) {
                        MaterialTheme.typography.headlineSmall.tabular()
                    } else {
                        MaterialTheme.typography.titleMedium.tabular()
                    },
                    fontWeight = FontWeight.SemiBold,
                    color = textColor,
                )
            }
            Box(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .height(3.dp)
                    .background(textColor.copy(alpha = 0.85f)),
            )
        }
    }
}

/**
 * Five-segment horizontal intensity gauge so earthquake severity is conveyed
 * through both proportion and semantic color (never color alone).
 */
@Composable
fun RichterIntensityMeter(
    magnitude: Double,
    modifier: Modifier = Modifier,
) {
    val activeSegments = when {
        magnitude >= 6.0 -> 5
        magnitude >= 5.0 -> 4
        magnitude >= 4.0 -> 3
        magnitude >= 3.0 -> 2
        else -> 1
    }
    val activeColor = when {
        magnitude >= 4.5 -> AfetCrimson
        magnitude >= 3.5 -> AfetAmber
        else -> AfetGreen
    }
    val inactiveColor = MaterialTheme.colorScheme.surfaceContainerHigh

    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        for (segment in 1..5) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height(4.dp)
                    .clip(Shape2dp)
                    .background(if (segment <= activeSegments) activeColor else inactiveColor),
            )
        }
    }
}

// ---------------------------------------------------------------------------
// CONNECTION, P2P MESH & SYNC STATUS
// ---------------------------------------------------------------------------

@Composable
fun ConnectionStatusChip(online: Boolean, modifier: Modifier = Modifier) {
    val (dotColor, label) = if (online) Pair(AfetGreen, "Çevrimiçi") else Pair(AfetAmber, "Çevrimdışı")
    Surface(
        modifier = modifier,
        shape = Shape8dp,
        color = MaterialTheme.colorScheme.surfaceContainerLow,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Box(Modifier.size(6.dp).background(dotColor, CircleShape))
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
fun MeshStatusChip(
    label: String = "BLE Düşük Enerji",
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = Shape8dp,
        color = AfetBlueMuted,
        border = BorderAfetBlueBorder,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Icon(
                imageVector = Icons.Outlined.Bluetooth,
                contentDescription = null,
                tint = AfetBlue,
                modifier = Modifier.size(14.dp),
            )
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onTertiaryContainer,
            )
        }
    }
}

@Composable
fun OfflineModeBanner(
    pendingCount: Int,
    modifier: Modifier = Modifier,
    onOpenMesh: (() -> Unit)? = null,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = Shape14dp,
        color = AfetAmberMuted,
        border = BorderAfetAmberBorder,
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                verticalAlignment = Alignment.Top,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Surface(
                    shape = Shape8dp,
                    color = MaterialTheme.colorScheme.surface.copy(alpha = 0.65f),
                    modifier = Modifier.size(34.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            Icons.Outlined.CloudOff,
                            contentDescription = null,
                            tint = AfetAmber,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        text = "Çevrimdışı Mod",
                        style = MaterialTheme.typography.titleSmall,
                        color = Zinc950,
                    )
                    Text(
                        text = if (pendingCount > 0) {
                            "$pendingCount ihbar yerel hafızada kayıtlı, bağlantı gelince aktarılacak."
                        } else {
                            "İnternet bağlantısı kısıtlı. Veriler cihazda saklanır."
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = Zinc700,
                    )
                }
            }
            if (onOpenMesh != null) {
                Surface(
                    onClick = onOpenMesh,
                    shape = Shape10dp,
                    color = MaterialTheme.colorScheme.surface,
                    border = BorderAfetAmberBorder,
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Icon(
                            Icons.Outlined.Bluetooth,
                            contentDescription = null,
                            tint = AfetBlue,
                            modifier = Modifier.size(16.dp),
                        )
                        Text(
                            text = "Yakın Ağ (P2P) tasarımını aç",
                            style = MaterialTheme.typography.labelLarge,
                            color = Zinc950,
                            modifier = Modifier.weight(1f),
                        )
                        Icon(
                            Icons.Outlined.ChevronRight,
                            contentDescription = null,
                            tint = Zinc500,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// BADGES & HELPERS
// ---------------------------------------------------------------------------

@Composable
fun RiskLevelBadge(label: String, level: Int, modifier: Modifier = Modifier) {
    val (color, bg, border) = when {
        level >= 70 -> Triple(AfetCrimson, AfetCrimsonMuted, AfetCrimsonBorder)
        level >= 40 -> Triple(AfetAmber, AfetAmberMuted, AfetAmberBorder)
        else -> Triple(AfetGreen, AfetGreenMuted, AfetGreenBorder)
    }
    StatusBadge(
        text = "$label · $level/100",
        modifier = modifier,
        backgroundColor = bg,
        textColor = color,
        borderColor = border,
    )
}

@Composable
fun UrgencyBadge(urgency: Urgency, modifier: Modifier = Modifier) {
    val (text, color, bg, border) = when (urgency) {
        Urgency.CRITICAL -> Quadruple("Kritik", AfetCrimson, AfetCrimsonMuted, AfetCrimsonBorder)
        Urgency.HIGH -> Quadruple("Yüksek", AfetOrange, AfetAmberMuted, AfetAmberBorder)
        Urgency.MEDIUM -> Quadruple("Orta", AfetAmber, AfetAmberMuted, AfetAmberBorder)
        Urgency.LOW -> Quadruple("Düşük", AfetGreen, AfetGreenMuted, AfetGreenBorder)
    }

    StatusBadge(
        text = text,
        modifier = modifier,
        backgroundColor = bg,
        textColor = color,
        borderColor = border,
    )
}

private data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)

@Composable
fun AiConfidenceIndicator(confidence: Float, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                "Model Güveni",
                style = MaterialTheme.typography.labelMedium,
                color = Zinc500,
            )
            Text(
                "%${(confidence * 100).toInt()}",
                style = MaterialTheme.typography.labelMedium.tabular(),
                fontWeight = FontWeight.SemiBold,
                color = AfetCrimson,
            )
        }
        LinearProgressIndicator(
            progress = { confidence },
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(CircleShape),
            color = AfetCrimson,
            trackColor = Zinc100,
        )
    }
}

@Composable
fun SafeRouteSummaryCard(route: RouteOption, modifier: Modifier = Modifier) {
    QuakeCard(modifier = modifier) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                route.label,
                style = MaterialTheme.typography.titleSmall,
                color = Zinc950,
                modifier = Modifier.weight(1f),
            )
            Spacer(Modifier.width(8.dp))
            RiskLevelBadge("Risk", route.riskScore)
        }
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("${route.distanceKm} km", style = MaterialTheme.typography.labelLarge.tabular(), color = Zinc900)
            Text("~${route.durationMinutes} dk", style = MaterialTheme.typography.labelLarge.tabular(), color = Zinc500)
            Text(route.reliability, style = MaterialTheme.typography.labelMedium, color = AfetGreen)
        }
    }
}

@Composable
fun LoadingSkeleton(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(100.dp),
        contentAlignment = Alignment.Center,
    ) {
        CircularProgressIndicator(color = AfetAccent, strokeWidth = 2.dp, modifier = Modifier.size(24.dp))
    }
}

@Composable
fun EmptyState(title: String, detail: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Icon(
            Icons.Outlined.CheckCircle,
            contentDescription = null,
            tint = Zinc400,
            modifier = Modifier.size(24.dp),
        )
        Text(title, style = MaterialTheme.typography.titleSmall, color = Zinc950)
        Text(detail, style = MaterialTheme.typography.bodyMedium, color = Zinc500, textAlign = TextAlign.Center)
    }
}

@Composable
fun ErrorState(message: String, onRetry: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Icon(Icons.Outlined.ErrorOutline, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(28.dp))
        Text(
            message,
            color = Zinc950,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            textAlign = TextAlign.Center,
        )
        OutlinedButton(
            onClick = onRetry,
            shape = Shape10dp,
            border = BorderZinc200,
        ) {
            Icon(Icons.Outlined.Refresh, contentDescription = null, modifier = Modifier.size(16.dp), tint = Zinc900)
            Spacer(Modifier.width(6.dp))
            Text("Tekrar Dene", style = MaterialTheme.typography.labelLarge, color = Zinc900)
        }
    }
}
