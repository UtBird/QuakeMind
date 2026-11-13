package com.quakemind.feature.onboarding

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Emergency
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*

private data class OnboardingStep(
    val title: String,
    val description: String,
    val tag: String,
    val icon: ImageVector,
)

@Composable
fun OnboardingScreen(
    onContinue: () -> Unit,
    onSkip: () -> Unit,
) {
    val steps = listOf(
        OnboardingStep(
            title = "Deprem kayıtlarını takip et",
            description = "Konumunuza yakın deprem kayıtlarını büyüklük, tarih ve kaynak bilgisiyle inceleyin.",
            tag = "1 / 3",
            icon = Icons.Outlined.Notifications,
        ),
        OnboardingStep(
            title = "Yakınındaki alanları bul",
            description = "Haritada toplanma alanlarını ve hizmet noktalarını incele. Tahliye rotasını değerlendirirken yerel uyarıları kontrol et.",
            tag = "2 / 3",
            icon = Icons.Outlined.LocationOn,
        ),
        OnboardingStep(
            title = "İhtiyacını bildir, durumunu paylaş",
            description = "İhbarın bağlantı kesildiğinde cihazında saklanır. Güvenlik durumunu bildirebilir, yakınlarına SMS taslağı hazırlayabilirsin.",
            tag = "3 / 3",
            icon = Icons.Outlined.Emergency,
        ),
    )

    var currentStep by rememberSaveable { mutableIntStateOf(0) }
    val step = steps[currentStep]

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
            .navigationBarsPadding()
            .padding(horizontal = 24.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.SpaceBetween,
    ) {
        // Top Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            StatusBadge(
                text = step.tag,
                backgroundColor = AfetAccentMuted,
                textColor = AfetAccent,
                borderColor = AfetAccentBorder,
            )
            TextButton(onClick = onSkip) {
                Text("Atla", color = Zinc500, fontWeight = FontWeight.Medium, fontSize = 14.sp)
            }
        }

        // Center Content
        Column(
            modifier = Modifier.fillMaxWidth().weight(1f).verticalScroll(rememberScrollState()).padding(vertical = 32.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Surface(
                modifier = Modifier.size(52.dp),
                shape = RoundedCornerShape(10.dp),
                color = AfetAccentMuted,
                border = androidx.compose.foundation.BorderStroke(1.dp, AfetAccentBorder),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(step.icon, contentDescription = null, tint = AfetAccent, modifier = Modifier.size(26.dp))
                }
            }

            Text(
                text = step.title,
                fontSize = 24.sp,
                color = Zinc950,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 30.sp,
            )

            Text(
                text = step.description,
                fontSize = 14.5.sp,
                color = Zinc500,
                lineHeight = 22.sp,
            )
        }

        // Bottom Controls
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Step Progress Bars
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                steps.indices.forEach { index ->
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(3.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(if (index <= currentStep) AfetAccent else Zinc200),
                    )
                }
            }

            Button(
                onClick = {
                    if (currentStep == steps.lastIndex) onContinue() else currentStep += 1
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 52.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AfetAccent,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            ) {
                Text(
                    text = if (currentStep == steps.lastIndex) "Başlayın" else "Devam Et",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.5.sp,
                )
            }
        }
    }
}
