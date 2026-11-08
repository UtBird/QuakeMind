package com.quakemind.feature.sos

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.LocationOn
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
import java.util.Locale

@Composable
fun SosScreen(
    onBack: () -> Unit,
    viewModel: SosViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsStateWithLifecycle()
    var permissionDenied by remember { mutableStateOf(false) }
    val locationPermissions = arrayOf(
        Manifest.permission.ACCESS_FINE_LOCATION,
        Manifest.permission.ACCESS_COARSE_LOCATION,
    )
    val requestPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { result ->
        if (result.values.any { it }) {
            permissionDenied = false
            viewModel.requestCurrentLocation()
        } else {
            permissionDenied = true
        }
    }
    val coordinateText = state.location?.let {
        String.format(Locale.US, "%.5f, %.5f", it.latitude, it.longitude)
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
                Text("Acil Durum SOS", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                Text("Acil yardım için 112'yi arayabilir veya sunucuya SOS gönderebilirsiniz", fontSize = 11.5.sp, color = Zinc500)
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxWidth().weight(1f),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 18.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item(key = "sos_emergency_call") {
                ShadcnCard {
                    Text("Hayati tehlikede 112'yi arayın", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    Text("Uygulama üzerinden SOS göndermek acil çağrı merkezini aramanın yerini tutmaz.", fontSize = 12.5.sp, color = Zinc600)
                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = {
                            val dial = Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
                            try { context.startActivity(dial) } catch (_: Exception) {}
                        },
                        modifier = Modifier.fillMaxWidth().height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    ) {
                        Icon(Icons.Outlined.Call, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("112 Acil Çağrı Merkezi'ni Ara", fontWeight = FontWeight.Bold)
                    }
                }
            }

            item(key = "sos_location") {
                ShadcnCard {
                    Text("1. Konumunuzu alın ve kontrol edin", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(6.dp))
                    Text("GPS koordinatlarınız yalnızca onaylayıp SOS gönderdiğinizde sunucuya iletilir.", fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(10.dp))
                    if (coordinateText != null) {
                        Text("Alınan konum: $coordinateText", fontSize = 13.5.sp, fontWeight = FontWeight.Bold, color = Zinc900)
                        Text(
                            "Ölçülen doğruluk: ${state.accuracyMeters?.let { "yaklaşık ${it.toInt()} metre" } ?: "bilinmiyor"}",
                            fontSize = 11.5.sp, color = Zinc600,
                        )
                    } else {
                        Text("Güncel GPS konumu henüz alınmadı.", fontSize = 12.5.sp, color = Zinc600)
                    }
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(
                        onClick = {
                            val allowed = locationPermissions.any {
                                context.checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
                            }
                            if (allowed) viewModel.requestCurrentLocation()
                            else requestPermission.launch(locationPermissions)
                        },
                        enabled = !state.isLocating && !state.isSending && state.serverId == null,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Icon(Icons.Outlined.LocationOn, contentDescription = null)
                        Spacer(Modifier.width(6.dp))
                        Text(if (state.isLocating) "Konum alınıyor..." else "Güncel GPS Konumunu Al")
                    }
                    if (permissionDenied) {
                        Text("Konum izni verilmedi. Uygulama SOS gönderimi için konuma ihtiyaç duyuyor.", fontSize = 12.sp, color = AfetCrimson)
                    }
                }
            }

            item(key = "sos_submit") {
                ShadcnCard {
                    Text("2. SOS çağrısını sunucuya gönderin", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Spacer(Modifier.height(8.dp))
                    if (state.serverId != null) {
                        Text("SOS sunucuya kaydedildi.", fontWeight = FontWeight.Bold, color = AfetGreen)
                        Text("Kayıt numarası: ${state.serverId}", fontSize = 12.5.sp, color = Zinc700)
                        Text("Bir kurtarma ekibinin görevlendirildiği henüz doğrulanmadı.", fontSize = 12.sp, color = Zinc600)
                    } else {
                        Text("Sunucunun kayıt onayı olmadan SOS gönderilmiş sayılmaz.", fontSize = 12.sp, color = Zinc600)
                        Spacer(Modifier.height(12.dp))
                        Button(
                            onClick = { viewModel.sendSos() },
                            enabled = state.location != null && !state.isLocating && !state.isSending,
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                        ) {
                            Text(if (state.isSending) "Sunucu onayı bekleniyor..." else "SOS Gönder", fontWeight = FontWeight.Bold)
                        }
                    }
                    if (state.error != null) {
                        Spacer(Modifier.height(8.dp))
                        Text(state.error.orEmpty(), fontSize = 12.5.sp, color = AfetCrimson)
                    }
                }
            }

            item(key = "sos_sms") {
                ShadcnCard {
                    Text("SMS ile alternatif iletişim", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Zinc950)
                    Text("Mesaj, SMS uygulamasında alıcı seçip gönderince iletilir.", fontSize = 12.sp, color = Zinc600)
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(
                        onClick = {
                            val freshLocation = state.location.takeIf {
                                val measuredAt = state.locationTimeMillis
                                measuredAt != null && System.currentTimeMillis() - measuredAt <= 120_000
                            }
                            val locationSuffix = freshLocation?.let {
                                " Konumum: https://maps.google.com/?q=${it.latitude},${it.longitude}"
                            } ?: " Konumum alınamadı."
                            val sms = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:")).apply {
                                putExtra("sms_body", "ACİL DURUM! Yardıma ihtiyacım var.$locationSuffix")
                            }
                            try { context.startActivity(sms) } catch (_: Exception) {}
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Icon(Icons.Outlined.Sms, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Text("Acil SMS Taslağı Hazırla")
                    }
                }
            }
        }
    }
}
