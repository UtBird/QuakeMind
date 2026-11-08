package com.quakemind.feature.report

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Domain
import androidx.compose.material.icons.outlined.LocalFireDepartment
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.MedicalServices
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material.icons.outlined.Traffic
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Urgency

private data class ReportCategory(
    val type: IncidentType,
    val label: String,
    val icon: ImageVector,
)

private val REPORT_CATEGORIES = listOf(
    ReportCategory(IncidentType.DEBRIS, "Enkaz / Mahsur", Icons.Outlined.Report),
    ReportCategory(IncidentType.BUILDING_DAMAGE, "Ağır Bina Hasarı", Icons.Outlined.Domain),
    ReportCategory(IncidentType.FIRE, "Yangın / Gaz Kaçağı", Icons.Outlined.LocalFireDepartment),
    ReportCategory(IncidentType.ROAD_CLOSURE, "Yol Kapanması", Icons.Outlined.Traffic),
    ReportCategory(IncidentType.MEDICAL, "Acil Tıbbi İhtiyaç", Icons.Outlined.MedicalServices),
)

private val URGENCY_OPTIONS = listOf(
    Pair(Urgency.LOW, "Düşük"),
    Pair(Urgency.MEDIUM, "Orta"),
    Pair(Urgency.HIGH, "Yüksek"),
    Pair(Urgency.CRITICAL, "Kritik"),
)

@Composable
fun ReportScreen(
    trackingCode: String?,
    onSubmit: (description: String, type: IncidentType, urgency: Urgency, peopleCount: Int, injuredCount: Int, location: GeoPoint) -> Unit,
    onBack: () -> Unit,
    isSubmitting: Boolean = false,
    submissionError: String? = null,
    syncWarning: String? = null,
) {
    var selectedType by remember { mutableStateOf(IncidentType.DEBRIS) }
    var selectedUrgency by remember { mutableStateOf(Urgency.CRITICAL) }
    var description by remember { mutableStateOf("") }
    var peopleCount by remember { mutableIntStateOf(1) }
    var injuredCount by remember { mutableIntStateOf(0) }
    var latitude by remember { mutableStateOf("") }
    var longitude by remember { mutableStateOf("") }
    val location = remember(latitude, longitude) {
        val lat = latitude.trim().replace(',', '.').toDoubleOrNull()
        val lon = longitude.trim().replace(',', '.').toDoubleOrNull()
        if (lat != null && lon != null && lat in -90.0..90.0 && lon in -180.0..180.0) {
            GeoPoint(lat, lon)
        } else null
    }

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
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
            }
            Spacer(Modifier.width(6.dp))
            Column {
                Text(
                    text = "Acil Durum İhbar Masası",
                    color = Zinc950,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = "İhbar cihazınıza kaydedilir, bağlantı varsa sunucuya eşitlenir",
                    color = Zinc500,
                    fontSize = 12.sp,
                )
            }
        }

        if (trackingCode != null) {
            // Success Screen
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Surface(
                    modifier = Modifier.size(64.dp),
                    shape = CircleShape,
                    color = AfetGreenMuted,
                    border = BorderAfetGreenBorder,
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.CheckCircle, contentDescription = null, tint = AfetGreen, modifier = Modifier.size(32.dp))
                    }
                }
                Spacer(Modifier.height(16.dp))
                Text("İhbarınız Başarıyla Kaydedildi", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Spacer(Modifier.height(6.dp))
                Text(
                    "İhbarınız cihazınıza kaydedildi. Sunucuya ulaştığı henüz doğrulanmadı.",
                    fontSize = 13.5.sp,
                    color = Zinc500,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                )
                Spacer(Modifier.height(20.dp))
                ShadcnCard {
                    Text("Takip Kodu", fontSize = 11.5.sp, color = Zinc400, fontWeight = FontWeight.SemiBold)
                    Text(
                        text = trackingCode,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Black,
                        color = AfetCrimson,
                        letterSpacing = 2.sp,
                    )
                }
                if (syncWarning != null) {
                    Text(syncWarning, color = AfetCrimson, fontSize = 12.sp, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                }
                Spacer(Modifier.height(24.dp))
                Button(
                    onClick = onBack,
                    modifier = Modifier.fillMaxWidth().height(46.dp),
                    shape = Shape8dp,
                    colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                ) {
                    Text("Ana Sayfaya Dön", fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                }
            }
        } else {
            // Form Screen
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(horizontal = 18.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // Require a user-supplied location; the app does not yet capture GPS for incident forms.
                item(key = "report_gps_chip", contentType = "gps_chip") {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = Shape8dp,
                        color = Zinc50,
                        border = BorderZinc200,
                    ) {
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("İhbar Konumu (Elle Girin)", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                            Text("GPS bu formda otomatik alınmıyor. İhbar konumunun enlem ve boylamını girin; yanlış konum yardımın gecikmesine neden olabilir.", fontSize = 12.sp, color = Zinc600)
                            OutlinedTextField(
                                value = latitude,
                                onValueChange = { latitude = it },
                                label = { Text("Enlem (ör. 39.92)") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth(),
                            )
                            OutlinedTextField(
                                value = longitude,
                                onValueChange = { longitude = it },
                                label = { Text("Boylam (ör. 32.85)") },
                                singleLine = true,
                                modifier = Modifier.fillMaxWidth(),
                            )
                            Text(
                                if (location != null) "Girilen koordinatlar biçim olarak geçerli; gerçek konumu kontrol edin."
                                else "Enlem -90 ile 90, boylam -180 ile 180 arasında olmalı.",
                                fontSize = 11.5.sp,
                                color = if (location != null) AfetGreen else Zinc600,
                            )
                        }
                    }
                }

                // 2. Category Header
                item(key = "report_category_header", contentType = "section_header") {
                    Text("İhbar Kategorisi", fontWeight = FontWeight.Bold, fontSize = 13.5.sp, color = Zinc950)
                }

                // 2. Category Items (Recycled)
                items(
                    items = REPORT_CATEGORIES,
                    key = { it.type.name },
                    contentType = { "report_category_tile" },
                ) { cat ->
                    val selected = selectedType == cat.type
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { selectedType = cat.type },
                        shape = Shape8dp,
                        color = if (selected) AfetCrimsonMuted else Color.White,
                        border = if (selected) BorderAfetCrimsonBorder else BorderZinc200,
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Icon(
                                cat.icon,
                                contentDescription = null,
                                tint = if (selected) AfetCrimson else Zinc600,
                                modifier = Modifier.size(20.dp),
                            )
                            Text(
                                text = cat.label,
                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                color = if (selected) AfetCrimson else Zinc900,
                                fontSize = 13.5.sp,
                                modifier = Modifier.weight(1f),
                            )
                            if (selected) {
                                Box(Modifier.size(6.dp).background(AfetCrimson, CircleShape))
                            }
                        }
                    }
                }

                // 3. Urgency Level
                item(key = "report_urgency_selector", contentType = "urgency_selector") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Aciliyet Seviyesi", fontWeight = FontWeight.Bold, fontSize = 13.5.sp, color = Zinc950)
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            URGENCY_OPTIONS.forEach { (urg, label) ->
                                val selected = selectedUrgency == urg
                                Surface(
                                    modifier = Modifier
                                        .weight(1f)
                                        .height(38.dp)
                                        .clickable { selectedUrgency = urg },
                                    shape = Shape6dp,
                                    color = if (selected) AfetCrimson else Zinc50,
                                    border = if (selected) BorderAfetCrimsonBorder else BorderZinc200,
                                ) {
                                    Box(contentAlignment = Alignment.Center) {
                                        Text(
                                            text = label,
                                            fontSize = 12.5.sp,
                                            fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                            color = if (selected) Color.White else Zinc700,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                // 4. Steppers: People and Injured
                item(key = "report_steppers", contentType = "steppers") {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        // People Count
                        Surface(
                            modifier = Modifier.weight(1f),
                            shape = Shape8dp,
                            color = Color.White,
                            border = BorderZinc200,
                        ) {
                            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("Mahsur Kişi", fontSize = 12.sp, color = Zinc500, fontWeight = FontWeight.Medium)
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    IconButton(
                                        onClick = { if (peopleCount > 1) peopleCount -= 1 },
                                        modifier = Modifier.size(28.dp).background(Zinc100, CircleShape),
                                    ) {
                                        Icon(Icons.Outlined.Remove, contentDescription = null, modifier = Modifier.size(14.dp))
                                    }
                                    Text("$peopleCount", fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Zinc950)
                                    IconButton(
                                        onClick = { peopleCount += 1 },
                                        modifier = Modifier.size(28.dp).background(Zinc100, CircleShape),
                                    ) {
                                        Icon(Icons.Outlined.Add, contentDescription = null, modifier = Modifier.size(14.dp))
                                    }
                                }
                            }
                        }

                        // Injured Count
                        Surface(
                            modifier = Modifier.weight(1f),
                            shape = Shape8dp,
                            color = Color.White,
                            border = BorderZinc200,
                        ) {
                            Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("Yaralı Sayısı", fontSize = 12.sp, color = Zinc500, fontWeight = FontWeight.Medium)
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    IconButton(
                                        onClick = { if (injuredCount > 0) injuredCount -= 1 },
                                        modifier = Modifier.size(28.dp).background(Zinc100, CircleShape),
                                    ) {
                                        Icon(Icons.Outlined.Remove, contentDescription = null, modifier = Modifier.size(14.dp))
                                    }
                                    Text("$injuredCount", fontWeight = FontWeight.Bold, fontSize = 16.sp, color = AfetCrimson)
                                    IconButton(
                                        onClick = { injuredCount += 1 },
                                        modifier = Modifier.size(28.dp).background(Zinc100, CircleShape),
                                    ) {
                                        Icon(Icons.Outlined.Add, contentDescription = null, modifier = Modifier.size(14.dp))
                                    }
                                }
                            }
                        }
                    }
                }

                // 5. Description TextField
                item(key = "report_description", contentType = "description_field") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Durum Açıklaması", fontWeight = FontWeight.Bold, fontSize = 13.5.sp, color = Zinc950)
                        OutlinedTextField(
                            value = description,
                            onValueChange = { description = it },
                            modifier = Modifier.fillMaxWidth().height(100.dp),
                            placeholder = { Text("Bina katı, adres detayı veya yardım ihtiyacını yazın...", fontSize = 13.sp, color = Zinc400) },
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

                // 6. Submit Button
                item(key = "report_submit_button", contentType = "cta") {
                    Button(
                        onClick = {
                            location?.let { onSubmit(description, selectedType, selectedUrgency, peopleCount, injuredCount, it) }
                        },
                        enabled = !isSubmitting && description.isNotBlank() && location != null,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                            .navigationBarsPadding(),
                        shape = Shape8dp,
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    ) {
                        Text(if (isSubmitting) "Cihaza kaydediliyor..." else "İhbarı Kaydet ve Gönderime Al", fontSize = 14.5.sp, fontWeight = FontWeight.Bold)
                    }
                    if (submissionError != null) {
                        Text(submissionError, color = AfetCrimson, fontSize = 12.sp)
                    }
                }
            }
        }
    }
}
