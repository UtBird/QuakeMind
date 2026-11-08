package com.quakemind.core.designsystem

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
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
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.unit.sp
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.Urgency

// ---------------------------------------------------------------------------
// SHADCN CORE ATOMS
// ---------------------------------------------------------------------------

@Composable
fun ShadcnCard(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier),
        shape = Shape12dp,
        color = Color.White,
        border = BorderZinc200,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            content = content,
        )
    }
}

@Composable
fun ShadcnBadge(
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
        border = androidx.compose.foundation.BorderStroke(1.dp, borderColor),
    ) {
        Text(
            text = text,
            color = textColor,
            fontSize = 11.5.sp,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}

// ---------------------------------------------------------------------------
// MODERN GEOMETRIC LOGO MARK (#800E13) - ZERO ALLOCATION ON DRAW
// ---------------------------------------------------------------------------

@Composable
fun AfetLogoMark(
    modifier: Modifier = Modifier,
    size: Dp = 32.dp,
    color: Color = AfetCrimson,
) {
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
                    .size(size * 0.58f)
                    .drawWithCache {
                        val w = this.size.width
                        val h = this.size.height
                        val path = Path().apply {
                            moveTo(w * 0.15f, h * 0.85f)
                            lineTo(w * 0.50f, h * 0.15f)
                            lineTo(w * 0.85f, h * 0.85f)
                            lineTo(w * 0.65f, h * 0.85f)
                            lineTo(w * 0.50f, h * 0.50f)
                            lineTo(w * 0.35f, h * 0.85f)
                            close()
                        }
                        onDrawBehind {
                            drawPath(path = path, color = Color.White)
                        }
                    }
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
        AfetLogoMark(size = 44.dp, color = AfetCrimson)
        Spacer(Modifier.height(10.dp))
        Text(
            text = "AFET",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Black,
            color = textColor,
            letterSpacing = 3.sp,
        )
        if (showSubtitle) {
            Spacer(Modifier.height(2.dp))
            Text(
                text = "Deprem & Acil Durum Karar Destek Ağı",
                fontSize = 12.5.sp,
                color = Zinc500,
                fontWeight = FontWeight.Normal,
            )
        }
    }
}

// ---------------------------------------------------------------------------
// E-DEVLET BUTTON
// ---------------------------------------------------------------------------

@Composable
fun EDevletButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier
            .fillMaxWidth()
            .height(44.dp),
        shape = Shape8dp,
        border = BorderZinc200,
        colors = ButtonDefaults.outlinedButtonColors(
            containerColor = Color.White,
            contentColor = Zinc950,
        ),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
        ) {
            Surface(
                shape = CircleShape,
                color = AfetCrimson,
                modifier = Modifier.size(20.dp),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = "e",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                    )
                }
            }
            Spacer(Modifier.width(10.dp))
            Text(
                text = "e-Devlet Kapısı ile Giriş Yap",
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.5.sp,
                color = Zinc950,
            )
        }
    }
}

// ---------------------------------------------------------------------------
// SEISMIC MAGNITUDE BADGE
// ---------------------------------------------------------------------------

@Composable
fun SeismicMagnitudeBadge(
    magnitude: Double,
    modifier: Modifier = Modifier,
    size: Dp = 48.dp,
    showPulse: Boolean = false,
) {
    val (bgColor, textColor, border) = when {
        magnitude >= 6.0 -> Triple(AfetCrimsonMuted, AfetCrimson, BorderAfetCrimsonBorder)
        magnitude >= 4.5 -> Triple(AfetCrimsonMuted, AfetCrimson, BorderAfetCrimsonBorder)
        magnitude >= 3.5 -> Triple(AfetAmberMuted, AfetAmber, BorderAfetAmberBorder)
        else -> Triple(AfetGreenMuted, AfetGreen, BorderAfetGreenBorder)
    }

    Surface(
        modifier = modifier.size(size),
        shape = Shape8dp,
        color = bgColor,
        border = border,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = magnitude.formatMagnitude(),
                fontSize = 16.sp,
                fontWeight = FontWeight.Black,
                color = textColor,
            )
        }
    }
}

// ---------------------------------------------------------------------------
// CONNECTION & SYNC STATUS
// ---------------------------------------------------------------------------

@Composable
fun ConnectionStatusChip(online: Boolean, modifier: Modifier = Modifier) {
    val (dotColor, label) = if (online) Pair(AfetGreen, "Çevrimiçi") else Pair(AfetAmber, "Kuyrukta")
    Surface(
        modifier = modifier,
        shape = Shape6dp,
        color = Zinc50,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.size(6.dp).background(dotColor, CircleShape))
            Spacer(Modifier.width(6.dp))
            Text(
                text = label,
                fontSize = 11.5.sp,
                fontWeight = FontWeight.Medium,
                color = Zinc700,
            )
        }
    }
}

@Composable
fun OfflineModeBanner(pendingCount: Int, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = Shape8dp,
        color = AfetAmberMuted,
        border = BorderAfetAmberBorder,
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Icon(
                Icons.Outlined.CloudOff,
                contentDescription = null,
                tint = AfetAmber,
                modifier = Modifier.size(18.dp),
            )
            Column(Modifier.weight(1f)) {
                Text(
                    text = "Çevrimdışı Mod",
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = Zinc950,
                )
                Text(
                    text = if (pendingCount > 0) "$pendingCount ihbar yerel hafızada kayıtlı, bağlantı gelince aktarılacak."
                    else "İnternet bağlantınız kısıtlı. Veriler yerel hafızada güvenle saklanır.",
                    fontSize = 11.5.sp,
                    color = Zinc600,
                )
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
    ShadcnBadge(
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
        Urgency.HIGH -> Quadruple("Yüksek", AfetOrange, Color(0xFFFFF7ED), Color(0xFFFED7AA))
        Urgency.MEDIUM -> Quadruple("Orta", AfetAmber, AfetAmberMuted, AfetAmberBorder)
        Urgency.LOW -> Quadruple("Düşük", AfetGreen, AfetGreenMuted, AfetGreenBorder)
    }

    ShadcnBadge(
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
    Column(modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                "Model Güveni",
                fontSize = 12.sp,
                color = Zinc500,
                fontWeight = FontWeight.Medium,
            )
            Text(
                "%${(confidence * 100).toInt()}",
                fontWeight = FontWeight.Bold,
                color = AfetCrimson,
                fontSize = 12.sp,
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
    ShadcnCard(modifier = modifier) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(route.label, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Zinc950)
            RiskLevelBadge("Risk", route.riskScore)
        }
        Spacer(Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("${route.distanceKm} km", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Zinc900)
            Text("~${route.durationMinutes} dk", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Zinc500)
            Text(route.reliability, fontSize = 12.sp, color = AfetGreen, fontWeight = FontWeight.Medium)
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
        CircularProgressIndicator(color = AfetCrimson, strokeWidth = 2.dp, modifier = Modifier.size(24.dp))
    }
}

@Composable
fun EmptyState(title: String, detail: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Icon(
            Icons.Outlined.CheckCircle,
            contentDescription = null,
            tint = Zinc400,
            modifier = Modifier.size(24.dp),
        )
        Text(title, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Zinc950)
        Text(detail, fontSize = 12.5.sp, color = Zinc500, textAlign = TextAlign.Center)
    }
}

@Composable
fun ErrorState(message: String, onRetry: () -> Unit, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(Icons.Outlined.ErrorOutline, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(28.dp))
        Text(message, color = Zinc950, fontSize = 13.5.sp, fontWeight = FontWeight.Medium, textAlign = TextAlign.Center)
        OutlinedButton(
            onClick = onRetry,
            shape = Shape8dp,
            border = BorderZinc200,
        ) {
            Icon(Icons.Outlined.Refresh, contentDescription = null, modifier = Modifier.size(14.dp), tint = Zinc900)
            Spacer(Modifier.width(6.dp))
            Text("Tekrar Dene", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Zinc900)
        }
    }
}
