package com.quakemind.feature.report

import androidx.compose.foundation.background
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.ui.semantics.Role
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.Domain
import androidx.compose.material.icons.outlined.LocalFireDepartment
import androidx.compose.material.icons.outlined.MedicalServices
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.Report
import androidx.compose.material.icons.outlined.Traffic
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Urgency
import com.quakemind.feature.location.DeviceLocationFix

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
    onSubmit: (description: String, type: IncidentType, urgency: Urgency, peopleCount: Int, injuredCount: Int, location: GeoPoint, deviceFix: DeviceLocationFix?) -> Unit,
    onBack: () -> Unit,
    isSubmitting: Boolean = false,
    submissionError: String? = null,
    syncWarning: String? = null,
    locationFix: DeviceLocationFix? = null,
    isLocating: Boolean = false,
    locationError: String? = null,
    onRequestLocation: () -> Unit = {},
) {
    var selectedType by rememberSaveable { mutableStateOf(IncidentType.DEBRIS) }
    var selectedUrgency by rememberSaveable { mutableStateOf(Urgency.CRITICAL) }
    var description by rememberSaveable { mutableStateOf("") }
    var peopleCount by rememberSaveable { mutableIntStateOf(0) }
    var injuredCount by rememberSaveable { mutableIntStateOf(0) }
    var latitude by rememberSaveable { mutableStateOf("") }
    var longitude by rememberSaveable { mutableStateOf("") }
    var manualLocation by rememberSaveable { mutableStateOf(false) }
    val selectedFix = locationFix.takeUnless { manualLocation }
    val manualPoint = remember(latitude, longitude) {
        val lat = latitude.trim().replace(',', '.').toDoubleOrNull()
        val lon = longitude.trim().replace(',', '.').toDoubleOrNull()
        if (lat != null && lon != null && lat in -90.0..90.0 && lon in -180.0..180.0) {
            GeoPoint(lat, lon)
        } else null
    }

    val location = if (manualLocation) manualPoint else selectedFix?.point

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
    ) {
        // Top App Bar
        ScreenHeader(title = "İhbar oluştur", onBack = onBack, subtitle = "Bağlantı kesilse de ihbarın cihazına kaydedilir.")

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
                Text("İhbarınız Başarıyla Kaydedildi", fontSize = 18.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                Spacer(Modifier.height(6.dp))
                Text(
                    "İhbarınız cihazınıza kaydedildi. Sunucuya ulaştığı henüz doğrulanmadı.",
                    fontSize = 14.sp,
                    color = Zinc500,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                )
                Spacer(Modifier.height(20.dp))
                QuakeCard {
                    Text("Takip Kodu", fontSize = 12.sp, color = Zinc400, fontWeight = FontWeight.SemiBold)
                    Text(
                        text = trackingCode,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.SemiBold,
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
                    modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                    shape = Shape8dp,
                    colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
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
                item(key = "report_gps_chip", contentType = "gps_chip") {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = Shape8dp,
                        color = Zinc50,
                        border = BorderZinc200,
                    ) {
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("İhbar Konumu", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                            if (!manualLocation) {
                                val message = when {
                                    isLocating -> "Cihaz konumu alınıyor…"
                                    selectedFix != null -> selectedFix.accuracyMetres?.let {
                                        "Cihaz konumu hazır · ±${it.toInt()} m"
                                    } ?: "Cihaz konumu hazır"
                                    else -> locationError ?: "Cihaz konumu bekleniyor."
                                }
                                Text(message, fontSize = 12.sp, color = Zinc600)
                                if (!isLocating) {
                                    TextButton(onClick = onRequestLocation) {
                                        Text(if (selectedFix != null) "Konumu güncelle" else "Cihaz konumunu al")
                                    }
                                }
                                TextButton(onClick = { manualLocation = true }) { Text("Koordinatları elle gir") }
                            } else {
                                val coordinatesKeyboard = KeyboardOptions(
                                    keyboardType = KeyboardType.Decimal,
                                    autoCorrectEnabled = false,
                                )
                                OutlinedTextField(
                                    value = latitude,
                                    onValueChange = { latitude = it },
                                    label = { Text("Enlem (ör. 39.92)") },
                                    singleLine = true,
                                    keyboardOptions = coordinatesKeyboard,
                                    modifier = Modifier.fillMaxWidth(),
                                )
                                OutlinedTextField(
                                    value = longitude,
                                    onValueChange = { longitude = it },
                                    label = { Text("Boylam (ör. 32.85)") },
                                    singleLine = true,
                                    keyboardOptions = coordinatesKeyboard,
                                    modifier = Modifier.fillMaxWidth(),
                                )
                                Text(
                                    if (manualPoint != null) "Girilen koordinatların gerçek konumu gösterdiğini kontrol edin."
                                    else "Enlem -90 ile 90, boylam -180 ile 180 arasında olmalı.",
                                    fontSize = 12.sp,
                                    color = Zinc600,
                                )
                                TextButton(onClick = {
                                    manualLocation = false
                                    if (locationFix == null && !isLocating) onRequestLocation()
                                }) { Text("Cihaz konumunu kullan") }
                            }
                        }
                    }
                }

                // 2. Category Header
                item(key = "report_category_header", contentType = "section_header") {
                    Text("İhbar Kategorisi", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
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
                        color = if (selected) AfetCrimsonMuted else MaterialTheme.colorScheme.surface,
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
                                fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                                color = if (selected) AfetCrimson else Zinc900,
                                fontSize = 14.sp,
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
                        Text("Aciliyet Seviyesi", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
                        FlowRow(
                            modifier = Modifier.fillMaxWidth().selectableGroup(),
                            maxItemsInEachRow = 2,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            URGENCY_OPTIONS.forEach { (urg, label) ->
                                val selected = selectedUrgency == urg
                                Surface(
                                    modifier = Modifier
                                        .weight(1f)
                                        .heightIn(min = 52.dp)
                                        .selectable(selected = selected, role = Role.RadioButton, onClick = { selectedUrgency = urg }),
                                    shape = Shape6dp,
                                    color = if (selected) AfetCrimson else Zinc50,
                                    border = if (selected) BorderAfetCrimsonBorder else BorderZinc200,
                                ) {
                                    Box(contentAlignment = Alignment.Center) {
                                        Text(
                                            text = label,
                                            fontSize = 14.sp,
                                            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                                            color = if (selected) MaterialTheme.colorScheme.onError else Zinc700,
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
                            color = MaterialTheme.colorScheme.surface,
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
                                        onClick = { if (peopleCount > 0) peopleCount -= 1 },
                                        modifier = Modifier.size(28.dp).background(Zinc100, CircleShape),
                                    ) {
                                        Icon(Icons.Outlined.Remove, contentDescription = null, modifier = Modifier.size(14.dp))
                                    }
                                    Text("$peopleCount", fontWeight = FontWeight.SemiBold, fontSize = 16.sp, color = Zinc950)
                                    IconButton(
                                        onClick = { if (peopleCount < 500) peopleCount += 1 },
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
                            color = MaterialTheme.colorScheme.surface,
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
                                    Text("$injuredCount", fontWeight = FontWeight.SemiBold, fontSize = 16.sp, color = AfetCrimson)
                                    IconButton(
                                        onClick = { if (injuredCount < 500) injuredCount += 1 },
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
                        OutlinedTextField(
                            value = description,
                            onValueChange = { if (it.length <= 1000) description = it },
                            modifier = Modifier.fillMaxWidth().heightIn(min = 100.dp),
                            label = { Text("Durum açıklaması") },
                            minLines = 3,
                            maxLines = 6,
                            placeholder = { Text("Bina katı, adres detayı veya yardım ihtiyacını yazın...", fontSize = 14.sp, color = Zinc400) },
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

                // 6. Submit Button
                item(key = "report_submit_button", contentType = "cta") {
                    Button(
                        onClick = {
                            location?.let { onSubmit(description, selectedType, selectedUrgency, peopleCount, injuredCount, it, selectedFix) }
                        },
                        enabled = !isSubmitting && description.isNotBlank() && location != null,
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 52.dp)
                            .navigationBarsPadding(),
                        shape = Shape8dp,
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                    ) {
                        Text(if (isSubmitting) "Cihaza kaydediliyor..." else "İhbarı Kaydet ve Gönderime Al", fontSize = 14.5.sp, fontWeight = FontWeight.SemiBold)
                    }
                    if (submissionError != null) {
                        Text(submissionError, color = AfetCrimson, fontSize = 12.sp)
                    }
                }
            }
        }
    }
}
