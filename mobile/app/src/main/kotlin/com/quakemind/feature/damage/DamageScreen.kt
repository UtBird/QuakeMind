package com.quakemind.feature.damage

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*

@Composable
fun DamageScreen(
    onBack: () -> Unit,
    onReport: () -> Unit,
    state: DamageLiveUiState,
    onPhotoSelected: (android.net.Uri?) -> Unit,
    onAnalyze: () -> Unit,
) {
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) {
        onPhotoSelected(it)
    }
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        ScreenHeader(title = "Hasar ön incelemesi", onBack = onBack, subtitle = "Seçtiğin fotoğrafı analiz et.")

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "damage_photo_selection", contentType = "damage_photo_selection") {
                QuakeCard {
                    Text("1. Hasarı gösteren fotoğrafı seçin", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        if (state.imageSelected) "Fotoğraf seçildi. Henüz bir hasar tespiti yapılmadı."
                        else "Henüz fotoğraf seçilmedi. Önceden hazırlanmış örnek analiz kullanılmıyor.",
                        color = Zinc600, fontSize = 14.sp,
                    )
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(
                        onClick = { picker.launch("image/*") },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !state.isAnalyzing,
                    ) {
                        Icon(Icons.Outlined.PhotoLibrary, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text(if (state.imageSelected) "Başka Fotoğraf Seç" else "Fotoğraf Seç")
                    }
                    Spacer(Modifier.height(8.dp))
                    Button(
                        onClick = onAnalyze,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                        enabled = state.imageSelected && !state.isAnalyzing,
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                    ) {
                        Text(if (state.isAnalyzing) "Sunucuda analiz ediliyor..." else "Fotoğrafı Analiz Et")
                    }
                    if (state.error != null) {
                        Spacer(Modifier.height(10.dp))
                        Text(state.error.orEmpty(), color = AfetCrimson, fontSize = 12.sp)
                    }
                }
            }

            item(key = "damage_result", contentType = "damage_result") {
                QuakeCard {
                    Text("2. Analiz sonucu", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    val result = state.result
                    if (result == null) {
                        Text("Sunucudan doğrulanmış model sonucu alınmadı.", fontSize = 14.sp, color = Zinc600)
                    } else {
                        Text("Modelin belirttiği sınıf: ${result.type}", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc900)
                        Spacer(Modifier.height(6.dp))
                        Text("Analiz notu: ${result.risk}", fontSize = 14.sp, color = Zinc700)
                        Text("Model skoru: ${result.riskScore}/100", fontSize = 14.sp, color = Zinc700)
                        Text("Güven: %${(result.confidence.coerceIn(0f, 1f) * 100).toInt()}", fontSize = 14.sp, color = Zinc700)
                        Spacer(Modifier.height(8.dp))
                        Text("Bu sonuç bir ön incelemedir; yerinde mühendislik hasar tespiti değildir.", fontSize = 12.sp, color = Zinc600)
                    }
                }
            }

            item(key = "damage_report", contentType = "damage_report") {
                QuakeCard {
                    Text("3. İhbar oluşturun", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
                    Text(
                        "İhbar formu ayrı açılır. Fotoğraf ve analiz sonucu şu anda otomatik olarak ihbara eklenmez.",
                        fontSize = 12.sp, color = Zinc600,
                    )
                    Spacer(Modifier.height(10.dp))
                    Button(
                        onClick = onReport,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                    ) {
                        Text("İhbar Formunu Aç")
                    }
                }
            }
        }
    }
}
