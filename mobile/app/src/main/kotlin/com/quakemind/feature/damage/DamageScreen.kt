package com.quakemind.feature.damage

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.PhotoLibrary
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.core.designsystem.*

@Composable
fun DamageScreen(
    onBack: () -> Unit,
    onReport: () -> Unit,
    viewModel: DamageLiveViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) {
        viewModel.selectPhoto(it)
    }
    Column(Modifier.fillMaxSize().background(Color.White).statusBarsPadding()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
            }
            Spacer(Modifier.width(8.dp))
            Column {
                Text("Fotoğrafla Hasar Ön İncelemesi", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text("Yalnızca seçtiğiniz fotoğraf analiz servisine gönderilir", fontSize = 12.sp, color = Zinc500)
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "damage_photo_selection") {
                ShadcnCard {
                    Text("1. Hasarı gösteren fotoğrafı seçin", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        if (state.imageSelected) "Fotoğraf seçildi. Henüz bir hasar tespiti yapılmadı."
                        else "Henüz fotoğraf seçilmedi. Önceden hazırlanmış örnek analiz kullanılmıyor.",
                        color = Zinc600, fontSize = 12.5.sp,
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
                        onClick = viewModel::analyzePhoto,
                        modifier = Modifier.fillMaxWidth().height(46.dp),
                        enabled = state.imageSelected && !state.isAnalyzing,
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    ) {
                        Text(if (state.isAnalyzing) "Sunucuda analiz ediliyor..." else "Fotoğrafı Analiz Et")
                    }
                    if (state.error != null) {
                        Spacer(Modifier.height(10.dp))
                        Text(state.error.orEmpty(), color = AfetCrimson, fontSize = 12.sp)
                    }
                }
            }

            item(key = "damage_result") {
                ShadcnCard {
                    Text("2. Analiz sonucu", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    val result = state.result
                    if (result == null) {
                        Text("Sunucudan doğrulanmış model sonucu alınmadı.", fontSize = 12.5.sp, color = Zinc600)
                    } else {
                        Text("Modelin belirttiği sınıf: ${result.type}", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc900)
                        Spacer(Modifier.height(6.dp))
                        Text("Analiz notu: ${result.risk}", fontSize = 12.5.sp, color = Zinc700)
                        Text("Model skoru: ${result.riskScore}/100", fontSize = 12.5.sp, color = Zinc700)
                        Text("Güven: %${(result.confidence.coerceIn(0f, 1f) * 100).toInt()}", fontSize = 12.5.sp, color = Zinc700)
                        Spacer(Modifier.height(8.dp))
                        Text("Bu sonuç bir ön incelemedir; yerinde mühendislik hasar tespiti değildir.", fontSize = 12.sp, color = Zinc600)
                    }
                }
            }

            item(key = "damage_report") {
                ShadcnCard {
                    Text("3. İhbar oluşturun", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Zinc950)
                    Text(
                        "İhbar formu ayrı açılır. Fotoğraf ve analiz sonucu şu anda otomatik olarak ihbara eklenmez.",
                        fontSize = 12.sp, color = Zinc600,
                    )
                    Spacer(Modifier.height(10.dp))
                    Button(
                        onClick = onReport,
                        modifier = Modifier.fillMaxWidth().height(46.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    ) {
                        Text("İhbar Formunu Aç")
                    }
                }
            }
        }
    }
}
