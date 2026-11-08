package com.quakemind.feature.checklist

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.EditLocationAlt
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.network.api.RiskResult
import com.quakemind.feature.map.OsmMapPreview
import java.util.Locale

@Composable
fun RiskScreen(
    onBack: () -> Unit,
    result: RiskResult? = null,
    isLoading: Boolean = false,
    error: String? = null,
    onAnalyze: (String, String) -> Unit = { _, _ -> },
    isLocating: Boolean = false,
    location: GeoPoint? = null,
    accuracyMetres: Float? = null,
    onRequestLocation: () -> Unit = {},
) {
    var latitude by rememberSaveable { mutableStateOf("") }
    var longitude by rememberSaveable { mutableStateOf("") }
    var manualEntryVisible by rememberSaveable { mutableStateOf(false) }

    Column(Modifier.fillMaxSize().background(Color(0xFFF5F6F8)).statusBarsPadding()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
            }
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("Zemin ve bölgesel risk", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text("Cihaz konumuna göre değerlendirme", fontSize = 11.sp, color = Zinc500)
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item(key = "risk_location", contentType = "location_card") {
                Surface(shape = RoundedCornerShape(20.dp), color = Color.White, border = BorderZinc200) {
                    Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Surface(shape = RoundedCornerShape(13.dp), color = AfetCrimsonMuted) {
                                Icon(
                                    Icons.Outlined.MyLocation,
                                    contentDescription = null,
                                    tint = AfetCrimson,
                                    modifier = Modifier.padding(11.dp).size(19.dp),
                                )
                            }
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                                Text(
                                    when {
                                        isLocating -> "Konumun bulunuyor"
                                        location != null -> "Analiz konumu hazır"
                                        else -> "Konumunu kullan"
                                    },
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Zinc950,
                                )
                                Text(
                                    when {
                                        isLocating -> "Güncel GPS veya ağ konumu alınıyor"
                                        location != null -> coordinateLabel(location)
                                        else -> "İzin verdiğinde risk puanını otomatik sorgulayacağız"
                                    },
                                    fontSize = 11.sp,
                                    color = Zinc600,
                                )
                            }
                            TextButton(onClick = onRequestLocation, enabled = !isLocating && !isLoading) {
                                Icon(Icons.Outlined.Refresh, contentDescription = null, modifier = Modifier.size(15.dp))
                                Text(if (location == null) "Bul" else "Yenile", fontSize = 11.sp)
                            }
                        }

                        if (location != null) {
                            Text(
                                accuracyMetres?.let { "Konum doğruluğu yaklaşık ±${it.toInt()} m" }
                                    ?: "Konum doğruluğu cihaz tarafından belirtilmedi",
                                fontSize = 10.5.sp,
                                color = Zinc500,
                            )
                            OsmMapPreview(
                                earthquakes = emptyList(),
                                mapPoints = emptyList(),
                                location = location,
                                modifier = Modifier.fillMaxWidth().height(190.dp),
                            )
                        }

                        Button(
                            onClick = onRequestLocation,
                            enabled = !isLocating && !isLoading,
                            modifier = Modifier.fillMaxWidth().height(46.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                        ) {
                            Text(
                                when {
                                    isLocating -> "Konum alınıyor…"
                                    isLoading -> "Bölgesel risk sorgulanıyor…"
                                    location != null -> "Konumumu yenile ve tekrar analiz et"
                                    else -> "Konumumu bul ve analiz et"
                                },
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                            )
                        }
                    }
                }
            }

            if (error != null) {
                item(key = "risk_error", contentType = "error") {
                    Surface(shape = RoundedCornerShape(14.dp), color = AfetCrimsonMuted, border = BorderAfetCrimsonBorder) {
                        Text(error, modifier = Modifier.padding(14.dp), fontSize = 12.sp, color = AfetCrimsonDark)
                    }
                }
            }

            if (result != null) {
                item(key = "risk_score", contentType = "risk_score") {
                    Surface(shape = RoundedCornerShape(20.dp), color = Color.White, border = BorderZinc200) {
                        Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Bölgesel risk puanı", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                            Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("${result.score}", fontSize = 42.sp, fontWeight = FontWeight.Black, color = AfetCrimson)
                                Text("/ 100", modifier = Modifier.padding(bottom = 8.dp), fontSize = 13.sp, color = Zinc500)
                            }
                            Text("Güncelleme: ${result.updatedAt}", fontSize = 11.sp, color = Zinc500)
                            Text(
                                "Bu bölgesel model sonucu bina güvenliği veya yerinde zemin etüdü yerine geçmez.",
                                fontSize = 11.sp,
                                color = Zinc600,
                            )
                        }
                    }
                }
                item(key = "risk_factors_title", contentType = "section_header") {
                    Text("Değerlendirmede kullanılan etkenler", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                }
                if (result.factors.isEmpty()) item(key = "risk_factors_empty", contentType = "empty_state") {
                    Text("Servis bu analiz için ek etken bildirmedi.", color = Zinc600, fontSize = 12.sp)
                }
                itemsIndexed(
                    items = result.factors,
                    key = { index, _ -> index },
                    contentType = { _, _ -> "risk_factor" },
                ) { _, factor ->
                    Surface(shape = RoundedCornerShape(14.dp), color = Color.White, border = BorderZinc200) {
                        Text(factor, modifier = Modifier.fillMaxWidth().padding(14.dp), fontSize = 12.sp, color = Zinc800)
                    }
                }
            }

            item(key = "risk_manual_toggle", contentType = "secondary_action") {
                Row(
                    modifier = Modifier.fillMaxWidth().clickable { manualEntryVisible = !manualEntryVisible }.padding(vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Icon(Icons.Outlined.EditLocationAlt, contentDescription = null, tint = Zinc600, modifier = Modifier.size(17.dp))
                    Text(
                        if (manualEntryVisible) "Elle koordinat gir" else "Başka bir konumu elle analiz et",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Zinc700,
                        modifier = Modifier.weight(1f),
                    )
                    Icon(
                        Icons.Outlined.ChevronRight,
                        contentDescription = null,
                        tint = Zinc400,
                        modifier = Modifier.size(16.dp),
                    )
                }
            }

            if (manualEntryVisible) {
                item(key = "risk_manual_form", contentType = "manual_coordinates") {
                    Surface(shape = RoundedCornerShape(18.dp), color = Color.White, border = BorderZinc200) {
                        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                            Text("Koordinatları gir", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                            OutlinedTextField(
                                value = latitude,
                                onValueChange = { latitude = it },
                                label = { Text("Enlem") },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                            )
                            OutlinedTextField(
                                value = longitude,
                                onValueChange = { longitude = it },
                                label = { Text("Boylam") },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                            )
                            Button(
                                onClick = { onAnalyze(latitude, longitude) },
                                enabled = !isLoading && !isLocating && latitude.isNotBlank() && longitude.isNotBlank(),
                                colors = ButtonDefaults.buttonColors(containerColor = Zinc800),
                                modifier = Modifier.fillMaxWidth(),
                            ) { Text("Bu konumu analiz et") }
                        }
                    }
                }
            }
        }
    }
}

private fun coordinateLabel(location: GeoPoint): String = String.format(
    Locale.US,
    "%.5f°, %.5f°",
    location.latitude,
    location.longitude,
)
