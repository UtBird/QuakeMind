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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Sms
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.core.designsystem.*

@Composable
fun SafetyScreen(
    confirmation: String?,
    onBack: () -> Unit,
    onSelect: (String) -> Unit,
    viewModel: SafetyStatusViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val status by viewModel.state.collectAsStateWithLifecycle()
    var selectedMessage by remember { mutableStateOf("SAFE") }
    val message = if (selectedMessage == "NEED_HELP") {
        "ACİL DURUM! Yardıma ihtiyacım var. Konum bilgimi ayrıca paylaşacağım."
    } else {
        "Güvendeyim. Konum bilgimi ayrıca paylaşacağım."
    }

    Column(Modifier.fillMaxSize().background(Color.White).statusBarsPadding()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Geri", tint = Zinc950)
            }
            Spacer(Modifier.width(8.dp))
            Column {
                Text("Güvenlik Durum Bildirimi", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text("Durumunuzu sunucuya bildirin veya yakınlarınıza mesaj hazırlayın", fontSize = 11.5.sp, color = Zinc500)
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "safety_status") {
                ShadcnCard {
                    Text("Durumunuzu seçin", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(6.dp))
                    Text("Bu işlem sunucuda yalnızca sizin durumunuzu kaydeder; yakınlarınıza otomatik mesaj göndermez.", fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = {
                                selectedMessage = "SAFE"
                                viewModel.sendStatus("SAFE")
                            },
                            enabled = !status.isSending,
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetGreen),
                        ) {
                            Text("Güvendeyim", fontSize = 12.5.sp)
                        }
                        Button(
                            onClick = {
                                selectedMessage = "NEED_HELP"
                                viewModel.sendStatus("NEED_HELP")
                            },
                            enabled = !status.isSending,
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                        ) {
                            Text("Yardım Gerekli", fontSize = 12.5.sp)
                        }
                    }
                    Spacer(Modifier.height(10.dp))
                    if (status.isSending) {
                        Text("Sunucu kayıt onayı bekleniyor...", fontSize = 12.5.sp, color = Zinc600)
                    } else if (status.confirmedStatus != null) {
                        Text(
                            if (status.confirmedStatus == "SAFE") "Güvendeyim durumunuz sunucuya kaydedildi."
                            else "Yardım gerekli durumunuz sunucuya kaydedildi.",
                            fontSize = 12.5.sp,
                            color = AfetGreen,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text("Ailenizin veya bir ekibin bilgilendirildiği doğrulanmadı.", fontSize = 12.sp, color = Zinc600)
                    } else if (status.error != null) {
                        Text(status.error.orEmpty(), fontSize = 12.5.sp, color = AfetCrimson)
                    } else {
                        Text("Henüz bu oturumda sunucuya kaydedilmiş durum yok.", fontSize = 12.sp, color = Zinc600)
                    }
                }
            }

            item(key = "safety_share") {
                ShadcnCard {
                    Text("Yakınlarınıza mesaj gönderin", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
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
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
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

            item(key = "safety_family") {
                ShadcnCard {
                    Text("Aile Güvenlik Çemberi", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Yakınlarınızın güncel konum ve güvenlik durumları bu sürümde doğrulanamıyor. Bağlı aile üyeleri listesi sunucudan sağlanana kadar gösterilmiyor.",
                        fontSize = 12.5.sp, color = Zinc600,
                    )
                }
            }
        }
    }
}
