package com.quakemind.feature.alerts

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Directions
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.ui.state.AppUiState

@Composable
fun AlertDetailScreen(
    id: String,
    state: AppUiState,
    onBack: () -> Unit,
    onSafety: () -> Unit,
    onMap: () -> Unit,
) {
    AlertDetailScreen(
        id = id,
        state = AlertsUiState(alerts = state.alerts),
        onBack = onBack,
        onSafety = onSafety,
        onMap = onMap,
    )
}

private val ALERT_SAFETY_GUIDELINES = listOf(
    "Asansörleri kesinlikle kullanmayın, merdivenleri tercih edin.",
    "Doğalgaz ve elektrik ana vanalarını derhal kapatın.",
    "Hasarlı veya çatlak binalara kesinlikle girmeyin.",
    "En yakın toplanma alanına güvenli yaya koridorunu kullanarak intikal edin.",
)

@Composable
fun AlertDetailScreen(
    id: String,
    state: AlertsUiState,
    onBack: () -> Unit,
    onSafety: () -> Unit,
    onMap: () -> Unit,
) {
    val alert = state.alerts.find { it.id == id } ?: state.alerts.firstOrNull()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .statusBarsPadding()
    ) {
        // Top App Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
                }
                Spacer(Modifier.width(6.dp))
                Text(
                    text = "Uyarı Detayı",
                    color = Zinc950,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                )
            }

            IconButton(onClick = {}) {
                Icon(Icons.Outlined.Share, contentDescription = "Paylaş", tint = Zinc800, modifier = Modifier.size(20.dp))
            }
        }

        if (alert == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Uyarı bulunamadı.", color = Zinc500)
            }
        } else {
            val (badgeBg, badgeText, badgeBorder) = when (alert.severity) {
                AlertSeverity.CRITICAL -> Triple(AfetCrimsonMuted, AfetCrimson, AfetCrimsonBorder)
                AlertSeverity.WARNING -> Triple(AfetAmberMuted, AfetAmber, AfetAmberBorder)
                AlertSeverity.INFO -> Triple(AfetBlueMuted, AfetBlue, AfetBlueBorder)
            }
            val (riskText, riskColor) = when (alert.severity) {
                AlertSeverity.CRITICAL -> Pair("Kritik Afet Protokolü", AfetCrimson)
                AlertSeverity.WARNING -> Pair("Yüksek Dikkat & Uyarı", AfetAmber)
                AlertSeverity.INFO -> Pair("Genel Bilgilendirme", AfetBlue)
            }

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(horizontal = 18.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {

                // Header Card
                item(key = "alert_detail_header", contentType = "header_card") {
                    ShadcnCard {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            ShadcnBadge(
                                text = alert.category.uppercase(),
                                backgroundColor = badgeBg,
                                textColor = badgeText,
                                borderColor = badgeBorder,
                            )
                            Text(alert.occurredAt, fontSize = 12.sp, color = Zinc400)
                        }

                        Spacer(Modifier.height(10.dp))

                        Text(
                            text = alert.title,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Zinc950,
                            lineHeight = 24.sp,
                        )

                        Spacer(Modifier.height(8.dp))

                        Text(
                            text = alert.detail,
                            fontSize = 13.5.sp,
                            color = Zinc700,
                            lineHeight = 20.sp,
                        )

                        Spacer(Modifier.height(14.dp))
                        HorizontalDivider(color = Zinc100)
                        Spacer(Modifier.height(10.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Column {
                                Text("Etkilenen Bölge", fontSize = 11.5.sp, color = Zinc400)
                                Text(alert.location, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Zinc900)
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text("Risk Seviyesi", fontSize = 11.5.sp, color = Zinc400)
                                Text(riskText, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = riskColor)
                            }
                        }
                    }
                }

                // Action Guidelines Header
                item(key = "alert_guidelines_header", contentType = "section_header") {
                    Text("Güvenlik Yönergeleri", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Zinc950)
                }

                // Action Guidelines Items (Recycled)
                itemsIndexed(
                    items = ALERT_SAFETY_GUIDELINES,
                    key = { index, _ -> index },
                    contentType = { _, _ -> "guideline_item" },
                ) { index, guide ->
                    val step = index + 1
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = Shape8dp,
                        color = Zinc50,
                        border = BorderZinc200,
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Surface(
                                shape = CircleShape,
                                color = if (alert.severity == AlertSeverity.CRITICAL) AfetCrimsonMuted else Zinc200,
                                border = if (alert.severity == AlertSeverity.CRITICAL) BorderAfetCrimsonBorder else BorderZinc300,
                                modifier = Modifier.size(20.dp),
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Text(
                                        text = "$step",
                                        fontSize = 10.5.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = if (alert.severity == AlertSeverity.CRITICAL) AfetCrimson else Zinc700,
                                    )
                                }
                            }
                            Text(guide, fontSize = 12.5.sp, color = Zinc800, lineHeight = 17.sp)
                        }
                    }
                }

                // CTA Buttons
                item(key = "alert_detail_cta_buttons", contentType = "cta") {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .navigationBarsPadding(),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Button(
                            onClick = onSafety,
                            modifier = Modifier.fillMaxWidth().height(46.dp),
                            shape = Shape8dp,
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                        ) {
                            Icon(Icons.Outlined.CheckCircle, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("Durumumu Bildir (Güvendeyim)", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold)
                        }

                        OutlinedButton(
                            onClick = onMap,
                            modifier = Modifier.fillMaxWidth().height(46.dp),
                            shape = Shape8dp,
                            border = BorderZinc200,
                        ) {
                            Icon(Icons.Outlined.Directions, contentDescription = null, modifier = Modifier.size(18.dp), tint = Zinc950)
                            Spacer(Modifier.width(8.dp))
                            Text("Bölgeyi Haritada Aç", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                        }
                    }
                }
            }
        }
    }
}
