package com.quakemind.feature.safety

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Sms
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*

@Composable
fun SafetyScreen(
    state: SafetyStatusUiState,
    onBack: () -> Unit,
    onSelect: (String) -> Unit,
) {
    val context = LocalContext.current
    var selectedMessage by remember { mutableStateOf("SAFE") }
    val message = if (selectedMessage == "NEED_HELP") {
        "ACİL DURUM! Yardıma ihtiyacım var. Konum bilgimi ayrıca paylaşacağım."
    } else {
        "Güvendeyim. Konum bilgimi ayrıca paylaşacağım."
    }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        ScreenHeader(title = "Güvenlik durumun", onBack = onBack, subtitle = "Durumunu bildir, yakınlarınla paylaş.")

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "safety_status", contentType = "safety_status") {
                QuakeCard {
                    Text("Durumunuzu seçin", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(6.dp))
                    Text("Bu işlem sunucuda yalnızca sizin durumunuzu kaydeder; yakınlarınıza otomatik mesaj göndermez.", fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(12.dp))
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = {
                                selectedMessage = "SAFE"
                                onSelect("SAFE")
                            },
                            enabled = !state.isSending,
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetGreen, contentColor = MaterialTheme.colorScheme.background),
                        ) {
                            Text("Güvendeyim", fontSize = 14.sp)
                        }
                        Button(
                            onClick = {
                                selectedMessage = "NEED_HELP"
                                onSelect("NEED_HELP")
                            },
                            enabled = !state.isSending,
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                        ) {
                            Text("Yardım Gerekli", fontSize = 14.sp)
                        }
                    }
                    Spacer(Modifier.height(10.dp))
                    if (state.isSending) {
                        Text("Sunucu kayıt onayı bekleniyor...", fontSize = 14.sp, color = Zinc600)
                    } else if (state.confirmedStatus != null) {
                        Text(
                            if (state.confirmedStatus == "SAFE") "Güvendeyim durumunuz sunucuya kaydedildi."
                            else "Yardım gerekli durumunuz sunucuya kaydedildi.",
                            fontSize = 14.sp,
                            color = AfetGreen,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text("Ailenizin veya bir ekibin bilgilendirildiği doğrulanmadı.", fontSize = 12.sp, color = Zinc600)
                    } else if (state.error != null) {
                        Text(state.error.orEmpty(), fontSize = 14.sp, color = AfetCrimson)
                    } else {
                        Text("Henüz bu oturumda sunucuya kaydedilmiş durum yok.", fontSize = 12.sp, color = Zinc600)
                    }
                }
            }

            item(key = "safety_share", contentType = "safety_share") {
                QuakeCard {
                    Text("Yakınlarınıza mesaj gönderin", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Zinc950)
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "Hazır mesaj: $message Konum otomatik eklenmez. Göndermeden önce uygulamada kontrol edebilirsiniz.",
                        fontSize = 12.sp, color = Zinc600,
                    )
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = {
                                val share = Intent(Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(Intent.EXTRA_TEXT, message)
                                }
                                try { context.startActivity(Intent.createChooser(share, "Durumu Paylaş")) } catch (_: Exception) {}
                            },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson, contentColor = MaterialTheme.colorScheme.onError),
                        ) {
                            Icon(Icons.Outlined.Share, contentDescription = null)
                            Spacer(Modifier.width(4.dp))
                            Text("Paylaş", fontSize = 12.sp)
                        }
                        OutlinedButton(
                            onClick = {
                                val sms = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:")).apply {
                                    putExtra("sms_body", message)
                                }
                                try { context.startActivity(sms) } catch (_: Exception) {}
                            },
                            modifier = Modifier.weight(1f),
                        ) {
                            Icon(Icons.Outlined.Sms, contentDescription = null)
                            Spacer(Modifier.width(4.dp))
                            Text("SMS Hazırla", fontSize = 12.sp)
                        }
                    }
                }
            }

        }
    }
}
