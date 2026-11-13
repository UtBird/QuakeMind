package com.quakemind.feature.profile

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.quakemind.core.designsystem.*
import com.quakemind.core.ui.state.AppUiState

@Composable
fun ProfileScreen(state: AppUiState, onOperations: () -> Unit, onBack: (() -> Unit)? = null) {
    ProfileScreen(ProfileUiState(session = state.session), onOperations, onBack)
}

@Composable
fun ProfileScreen(state: ProfileUiState, onOperations: () -> Unit, onBack: (() -> Unit)? = null) {
    val session = state.session
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        ScreenHeader("Profil", subtitle = "Hesabın ve erişimlerin", onBack = onBack)
        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = PaddingValues(horizontal = 20.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            item(key = "account", contentType = "account") {
                QuakeCard {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        Icon(Icons.Outlined.Person, null, tint = AfetAccent, modifier = Modifier.size(36.dp))
                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(session?.displayName?.takeIf { it.isNotBlank() } ?: "Misafir",
                                style = MaterialTheme.typography.titleLarge)
                            Text(if (session?.isGuest != false) "Misafir oturumu" else "Hesap oturumu",
                                style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                            session?.city?.takeIf { it.isNotBlank() }?.let {
                                Text(it, style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                            }
                        }
                    }
                }
            }
            if (session?.capabilities?.contains("operations.view") == true) {
                item(key = "operations", contentType = "action") {
                    QuakeCard(onClick = onOperations) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Icon(Icons.Outlined.SupportAgent, null, tint = AfetAccent)
                            Column(Modifier.weight(1f)) {
                                Text("Saha operasyonları", style = MaterialTheme.typography.titleMedium)
                                Text("İhbarlar ve gönderim kuyruğu", style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                            }
                            Icon(Icons.Outlined.ChevronRight, null)
                        }
                    }
                }
            }
            item(key = "offline_information", contentType = "information") {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Bağlantı kesildiğinde", style = MaterialTheme.typography.titleMedium)
                    Text("İhbarların cihazında tutulur. İnternet bağlantısı sağlandığında gönderim yeniden denenir. Yerel kayıt, sunucu onayı veya ekip görevlendirmesi anlamına gelmez.",
                        style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                    HorizontalDivider(Modifier.padding(vertical = 12.dp), color = Zinc200)
                    Text("Hayati tehlikede 112", style = MaterialTheme.typography.titleMedium)
                    Text("QuakeMind üzerinden bildirim göndermek, acil çağrı merkezini aramanın yerini tutmaz.",
                        style = MaterialTheme.typography.bodyMedium, color = Zinc500)
                }
            }
        }
    }
}
