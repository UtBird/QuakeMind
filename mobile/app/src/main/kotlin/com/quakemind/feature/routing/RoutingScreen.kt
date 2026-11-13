package com.quakemind.feature.routing

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.GeoPoint

@Composable
fun RoutingScreen(
    state: RoutingRequestUiState,
    onBack: () -> Unit,
    onRequestRoutes: (GeoPoint, GeoPoint) -> Unit,
    modifier: Modifier = Modifier,
) {
    var startLatitude by rememberSaveable { mutableStateOf("") }
    var startLongitude by rememberSaveable { mutableStateOf("") }
    var endLatitude by rememberSaveable { mutableStateOf("") }
    var endLongitude by rememberSaveable { mutableStateOf("") }

    fun parseCoordinate(latInput: String, lonInput: String): GeoPoint? {
        val lat = latInput.trim().replace(',', '.').toDoubleOrNull()
        val lon = lonInput.trim().replace(',', '.').toDoubleOrNull()
        if (lat == null || lon == null || lat !in -90.0..90.0 || lon !in -180.0..180.0) return null
        return GeoPoint(lat, lon)
    }

    val origin = parseCoordinate(startLatitude, startLongitude)
    val destination = parseCoordinate(endLatitude, endLongitude)
    val validRequest = origin != null && destination != null && origin != destination

    Column(modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        ScreenHeader(title = "Tahliye rotası", onBack = onBack, subtitle = "Başlangıç ve hedef konumunu belirle.")

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "routing_query", contentType = "routing_query") {
                QuakeCard {
                    Text("Başlangıç koordinatları", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = startLatitude, onValueChange = { startLatitude = it },
                        label = { Text("Enlem (ör. 39.92)") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = startLongitude, onValueChange = { startLongitude = it },
                        label = { Text("Boylam (ör. 32.85)") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(Modifier.height(12.dp))
                    Text("Hedef koordinatları", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = endLatitude, onValueChange = { endLatitude = it },
                        label = { Text("Hedef enlem") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = endLongitude, onValueChange = { endLongitude = it },
                        label = { Text("Hedef boylam") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Enlem -90 ile 90, boylam -180 ile 180 arasında olmalı. Harita üzerinden konum seçimi henüz desteklenmiyor.",
                        fontSize = 12.sp, color = Zinc600,
                    )
                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = {
                            if (origin != null && destination != null) onRequestRoutes(origin, destination)
                        },
                        enabled = validRequest && !state.isLoading,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                    ) {
                        Text(if (state.isLoading) "Rota hesaplanıyor..." else "Rota Sorgula")
                    }
                }
            }

            item(key = "routing_feedback", contentType = "routing_feedback") {
                if (state.error != null) {
                    Text(state.error.orEmpty(), fontSize = 14.sp, color = AfetCrimson)
                } else if (!state.isLoading && state.routes.isEmpty()) {
                    Text(
                        if (state.hasRequested) "Bu başlangıç ve hedef için rota üretilmedi."
                        else "Henüz başlangıç ve hedef konumu girilerek rota istenmedi.",
                        fontSize = 14.sp, color = Zinc600,
                    )
                }
            }

            items(
                items = state.routes,
                key = { it.id },
                contentType = { "route_option" },
            ) { route ->
                QuakeCard {
                    Text(route.label, fontSize = 15.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    Text("Mesafe: ${route.distanceKm} km", fontSize = 14.sp, color = Zinc700)
                    Text("Tahmini süre: ${route.durationMinutes} dakika", fontSize = 14.sp, color = Zinc700)
                    Text("Model risk skoru: ${route.riskScore}", fontSize = 14.sp, color = Zinc700)
                    Text("Kaynak: ${route.reliability}", fontSize = 12.sp, color = Zinc600)
                    Text(route.description, fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Bu hizmet geçişin güvenli veya açık olduğunu garanti etmez. Yol ve afet uyarılarını yerel yetkililerden doğrulayın.",
                        fontSize = 12.sp, color = AfetCrimson,
                    )
                }
            }
        }
    }
}
