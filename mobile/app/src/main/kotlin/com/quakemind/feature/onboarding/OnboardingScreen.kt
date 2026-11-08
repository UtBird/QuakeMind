package com.quakemind.feature.onboarding

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
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
            title = "Anlık Deprem ve Sismik Bilgilendirme",
            description = "Kandilli Rasathanesi ve AFAD resmi veri akışları ile konumunuza yakın sarsıntıları saniyeler içinde takip edin.",
            tag = "01 / 03 · SİSMİK TAKİP",
            icon = Icons.Outlined.Notifications,
        ),
        OnboardingStep(
            title = "Toplanma Alanları ve Güvenli Rotalar",
            description = "Evinize ve iş yerinize en yakın afet toplanma alanlarını ve hasarlı yollardan kaçınan tahliye yollarını görüntüleyin.",
            tag = "02 / 03 · TAHLİYE VE ROTA",
            icon = Icons.Outlined.LocationOn,
        ),
        OnboardingStep(
            title = "Çevrimdışı İhbar ve Aile Güvenlik Ağı",
            description = "İnternet bağlantısı koptuğunda dahi durumunuzu yerel kuyruğa kaydedin ve tek dokunuşla SMS ile ailenize bildirin.",
            tag = "03 / 03 · ACİL SOS",
            icon = Icons.Outlined.Emergency,
        ),
    )

    var currentStep by remember { mutableIntStateOf(0) }
    val step = steps[currentStep]

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
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
            ShadcnBadge(
                text = step.tag,
                backgroundColor = AfetCrimsonMuted,
                textColor = AfetCrimson,
                borderColor = AfetCrimsonBorder,
            )
            TextButton(onClick = onSkip) {
                Text("Atla", color = Zinc500, fontWeight = FontWeight.Medium, fontSize = 13.5.sp)
            }
        }

        // Center Content
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Surface(
                modifier = Modifier.size(52.dp),
                shape = RoundedCornerShape(10.dp),
                color = AfetCrimsonMuted,
                border = androidx.compose.foundation.BorderStroke(1.dp, AfetCrimsonBorder),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(step.icon, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(26.dp))
                }
            }

            Text(
                text = step.title,
                fontSize = 24.sp,
                color = Zinc950,
                fontWeight = FontWeight.Bold,
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
                            .background(if (index <= currentStep) AfetCrimson else Zinc200),
                    )
                }
            }

            Button(
                onClick = {
                    if (currentStep == steps.lastIndex) onContinue() else currentStep += 1
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AfetCrimson,
                    contentColor = Color.White,
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
