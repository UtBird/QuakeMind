package com.quakemind.feature.profile

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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material.icons.outlined.VerifiedUser
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
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
import com.quakemind.core.ui.state.AppUiState

@Composable
fun ProfileScreen(
    state: AppUiState,
    onOperations: () -> Unit,
) {
    ProfileScreen(
        state = ProfileUiState(session = state.session),
        onOperations = onOperations,
    )
}

@Composable
fun ProfileScreen(
    state: ProfileUiState,
    onOperations: () -> Unit,
) {
    var highSensSms by remember { mutableStateOf(state.highSensSms) }
    var offlineMapOffline by remember { mutableStateOf(state.offlineMapOffline) }
    var volunteerActive by remember { mutableStateOf(state.volunteerActive) }

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
                .padding(horizontal = 18.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "Profil & Sistem Ayarları",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Zinc950,
            )
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(start = 18.dp, end = 18.dp, top = 6.dp, bottom = 100.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // User Card (#800E13 Avatar)
            item(key = "profile_user_card", contentType = "user_card") {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = Shape12dp,
                    color = Color.White,
                    border = BorderZinc200,
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        Surface(
                            modifier = Modifier.size(52.dp),
                            shape = CircleShape,
                            color = AfetCrimsonMuted,
                            border = BorderAfetCrimsonBorder,
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text(
                                    text = (state.session?.displayName?.take(1) ?: "V").uppercase(),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 20.sp,
                                    color = AfetCrimson,
                                )
                            }
                        }

                        Column(Modifier.weight(1f)) {
                            Text(
                                text = state.session?.displayName ?: "Volkan Demir",
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp,
                                color = Zinc950,
                            )
                            Text(
                                text = "T.C. Kimlik No: 284*******4",
                                fontSize = 12.sp,
                                color = Zinc500,
                            )
                            Spacer(Modifier.height(4.dp))
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                Icon(Icons.Outlined.VerifiedUser, contentDescription = null, tint = AfetGreen, modifier = Modifier.size(14.dp))
                                Text("e-Devlet Doğrulanmış Hesap", fontSize = 11.5.sp, color = AfetGreen, fontWeight = FontWeight.SemiBold)
                            }
                        }
                    }
                }
            }

            // Responder Dispatch Desk Entry
            item(key = "profile_responder_entry", contentType = "responder_entry") {
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(onClick = onOperations),
                    shape = Shape10dp,
                    color = Zinc950,
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Surface(
                                modifier = Modifier.size(36.dp),
                                shape = Shape8dp,
                                color = Color(0xFF27272A),
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(Icons.Outlined.SupportAgent, contentDescription = null, tint = Color.White, modifier = Modifier.size(20.dp))
                                }
                            }
                            Column {
                                Text("Saha Operasyon Masası", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.5.sp)
                                Text("Yetkili müdahale ekipleri ve triyaj", color = Zinc400, fontSize = 11.5.sp)
                            }
                        }
                        Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Zinc400, modifier = Modifier.size(18.dp))
                    }
                }
            }

            // Preferences
            item(key = "profile_preferences_card", contentType = "preferences") {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Acil Durum & Veri Tercihleri", fontWeight = FontWeight.Bold, fontSize = 13.5.sp, color = Zinc950)

                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = Shape10dp,
                        color = Color.White,
                        border = BorderZinc200,
                    ) {
                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            // Offline Maps
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text("Çevrimdışı Harita İndirimi", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Zinc950)
                                    Text("İstanbul Marmara Bölgesi (142 MB hazır)", fontSize = 11.5.sp, color = Zinc500)
                                }
                                Switch(
                                    checked = offlineMapOffline,
                                    onCheckedChange = { offlineMapOffline = it },
                                    colors = SwitchDefaults.colors(checkedThumbColor = Color.White, checkedTrackColor = AfetCrimson),
                                )
                            }

                            HorizontalDivider(color = Zinc100)

                            // High Sensitivity SMS
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text("Otomatik Konum SMS Yayını", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Zinc950)
                                    Text("Şiddetli sarsıntı (M ≥ 5.0) anında acil SMS at", fontSize = 11.5.sp, color = Zinc500)
                                }
                                Switch(
                                    checked = highSensSms,
                                    onCheckedChange = { highSensSms = it },
                                    colors = SwitchDefaults.colors(checkedThumbColor = Color.White, checkedTrackColor = AfetCrimson),
                                )
                            }
                        }
                    }
                }
            }

        }
    }
}
