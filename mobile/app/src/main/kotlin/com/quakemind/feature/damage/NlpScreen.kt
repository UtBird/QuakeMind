package com.quakemind.feature.damage

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.TextSnippet
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
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
    var rawText by rememberSaveable { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
    ) {
        // Header
        ScreenHeader(title = "Metin analizi", onBack = onBack, subtitle = "Yardım çağrısındaki ihtiyaçları incele.")

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
                    OutlinedTextField(
                        value = rawText,
                        onValueChange = { rawText = it },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 110.dp),
                            label = { Text("Yardım mesajı") },
                            minLines = 3,
                            maxLines = 6,
                        placeholder = { Text("Serbest formatta yardım mesajını buraya yapıştırın...", fontSize = 14.sp, color = Zinc400) },
                        shape = Shape8dp,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AfetCrimson,
                            unfocusedBorderColor = Zinc200,
                            focusedContainerColor = MaterialTheme.colorScheme.surface,
                            unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                        ),
                    )
                }
            }

            // Analyze Button
            item(key = "nlp_analyze_button", contentType = "button") {
                Button(
                    onClick = { onAnalyze(rawText) },
                    enabled = !isAnalyzing && rawText.isNotBlank(),
                    modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                    shape = Shape8dp,
                    colors = ButtonDefaults.buttonColors(containerColor = Zinc950),
                ) {
                    Icon(Icons.Outlined.TextSnippet, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(if (isAnalyzing) "Metin analiz ediliyor..." else "Metni Yapay Zekâ ile Ayrıştır", fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                }
            }

            if (error != null) {
                item(key = "nlp_error", contentType = "nlp_error") { Text(error, color = AfetCrimson, fontSize = 14.sp) }
            }


            // Result Card
            if (analysis != null) {
                item(key = "nlp_result_card", contentType = "result") {
                    QuakeCard {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text("Ayrıştırılan Varlıklar", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
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
                            .heightIn(min = 52.dp)
                            .navigationBarsPadding(),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                    ) {
                        Icon(Icons.Outlined.Report, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("İhbar Formunu Aç", fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
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
        Text(label, fontSize = 14.sp, color = Zinc500)
        Text(value, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
    }
}
