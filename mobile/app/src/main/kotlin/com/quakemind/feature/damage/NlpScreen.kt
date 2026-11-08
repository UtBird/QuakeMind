package com.quakemind.feature.damage

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.NlpAnalysis

@Composable
fun NlpScreen(
    analysis: NlpAnalysis?,
    onBack: () -> Unit,
    onAnalyze: (String) -> Unit,
    onReport: () -> Unit,
    isAnalyzing: Boolean = false,
    error: String? = null,
) {
    var rawText by remember { mutableStateOf("") }

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
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
            }
            Spacer(Modifier.width(6.dp))
            Column {
                Text(
                    text = "Acil Metin & Çağrı Ayrıştırıcı",
                    color = Zinc950,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = "Sosyal medya ve mesajlardan otomatik ihbar çıkarımı",
                    color = Zinc500,
                    fontSize = 12.sp,
                )
            }
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(horizontal = 18.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Input Area
            item(key = "nlp_input_area", contentType = "input") {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Ham Yardım Metni", fontWeight = FontWeight.Bold, fontSize = 13.5.sp, color = Zinc950)
                    OutlinedTextField(
                        value = rawText,
                        onValueChange = { rawText = it },
                        modifier = Modifier.fillMaxWidth().height(110.dp),
                        placeholder = { Text("Serbest formatta yardım mesajını buraya yapıştırın...", fontSize = 13.sp, color = Zinc400) },
                        shape = Shape8dp,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AfetCrimson,
                            unfocusedBorderColor = Zinc200,
                            focusedContainerColor = Color.White,
                            unfocusedContainerColor = Color.White,
                        ),
                    )
                }
            }

            // Analyze Button
            item(key = "nlp_analyze_button", contentType = "button") {
                Button(
                    onClick = { onAnalyze(rawText) },
                    enabled = !isAnalyzing && rawText.isNotBlank(),
                    modifier = Modifier.fillMaxWidth().height(42.dp),
                    shape = Shape8dp,
                    colors = ButtonDefaults.buttonColors(containerColor = Zinc950),
                ) {
                    Icon(Icons.Outlined.AutoAwesome, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(if (isAnalyzing) "Metin analiz ediliyor..." else "Metni Yapay Zekâ ile Ayrıştır", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold)
                }
            }

            if (error != null) {
                item(key = "nlp_error") { Text(error, color = AfetCrimson, fontSize = 12.5.sp) }
            }


            // Result Card
            if (analysis != null) {
                item(key = "nlp_result_card", contentType = "result") {
                    ShadcnCard {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text("Ayrıştırılan Varlıklar", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Zinc950)
                            UrgencyBadge(urgency = analysis.urgency)
                        }

                        Spacer(Modifier.height(10.dp))

                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            EntityRow(label = "Konum", value = analysis.locationText ?: "Metinden belirlenemedi")
                            EntityRow(label = "İhbar Tipi", value = analysis.category.name)
                            EntityRow(label = "Gereksinimler", value = analysis.needs.joinToString(", "))
                        }

                        Spacer(Modifier.height(12.dp))
                        AiConfidenceIndicator(confidence = analysis.confidence)
                    }
                }

                item(key = "nlp_create_incident_btn", contentType = "cta") {
                    Button(
                        onClick = onReport,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(46.dp)
                            .navigationBarsPadding(),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    ) {
                        Icon(Icons.Outlined.Report, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("İhbar Formunu Aç", fontSize = 13.5.sp, fontWeight = FontWeight.SemiBold)
                    }
                    Text(
                        "Analiz sonucu ihbar formuna otomatik aktarılmaz; gerekli açıklamayı kendiniz girin.",
                        fontSize = 12.sp,
                        color = Zinc600,
                    )
                }
            }
        }
    }
}

@Composable
private fun EntityRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, fontSize = 12.5.sp, color = Zinc500)
        Text(value, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
    }
}
