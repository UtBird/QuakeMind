package com.quakemind.feature.operations

import androidx.compose.foundation.background
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.SyncStatus

@Composable
fun OperationsScreen(
    state: OperationsUiState,
    onBack: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
    ) {
        // Header
        ScreenHeader(title = "Saha operasyonları", onBack = onBack, subtitle = "İhbarlar ve yerel gönderim kuyruğu")

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(horizontal = 18.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Stats Row
            item(key = "operations_stats_row", contentType = "stats") {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Surface(
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(8.dp),
                        color = Zinc50,
                        border = androidx.compose.foundation.BorderStroke(1.dp, Zinc200),
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Yerel Gönderim Kuyruğu", fontSize = 12.sp, color = Zinc500)
                            Text("${state.pendingCount}", fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = AfetCrimson)
                        }
                    }
                    Surface(
                        modifier = Modifier.weight(1f),
                        shape = Shape8dp,
                        color = Zinc50,
                        border = BorderZinc200,
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Listelenen İhbar", fontSize = 12.sp, color = Zinc500)
                            Text("${state.incidents.size}", fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                        }
                    }
                    Surface(
                        modifier = Modifier.weight(1f),
                        shape = Shape8dp,
                        color = Zinc50,
                        border = BorderZinc200,
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Sunucuya Eşitlenen", fontSize = 12.sp, color = Zinc500)
                            Text("${state.incidents.count { it.syncStatus == SyncStatus.SYNCED }}", fontSize = 20.sp, fontWeight = FontWeight.SemiBold, color = AfetGreen)
                        }
                    }
                }
            }

            // Triage Queue Items
            item(key = "operations_queue_header", contentType = "header") {
                Text("İhbar Kayıtları", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
            }

            if (state.incidents.isEmpty()) {
                item(key = "operations_empty", contentType = "operations_empty") {
                    Text("Gösterilecek doğrulanmış ihbar bulunmuyor. Yeni kayıtlar geldiğinde burada listelenecek.", fontSize = 14.sp, color = Zinc600)
                }
            }

            items(
                items = state.incidents,
                key = { it.id },
                contentType = { "triage_card" },
            ) { incident ->
                QuakeCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(incident.id, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = AfetCrimson)
                        UrgencyBadge(incident.urgency)
                    }

                    Spacer(Modifier.height(6.dp))
                    Text(incident.title, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(4.dp))
                    Text(incident.locationLabel, fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(10.dp))
                    Text("Durum: ${incident.status}", fontSize = 12.sp, color = Zinc600)
                    if (incident.syncStatus != SyncStatus.SYNCED) {
                        Text("Bu ihbar henüz sunucuya iletilmedi.", fontSize = 12.sp, color = AfetCrimson)
                    }
                    Text("Bu ekrandan ekip sevki veya ihbar doğrulaması yapılamıyor.", fontSize = 12.sp, color = Zinc500)
                }
            }

        }
    }
}
