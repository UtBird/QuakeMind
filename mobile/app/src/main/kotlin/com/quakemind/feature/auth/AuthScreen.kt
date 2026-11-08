package com.quakemind.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*

@Composable
fun AuthScreen(
    onLogin: (String, String) -> Unit,
    onRegister: (String, String, String) -> Unit,
    onGuest: () -> Unit,
    isBusy: Boolean = false,
    error: String? = null,
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    var identity by remember { mutableStateOf("") }
    var fullName by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .statusBarsPadding()
            .navigationBarsPadding()
            .imePadding()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp, vertical = 20.dp),
        verticalArrangement = Arrangement.SpaceBetween,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        // Header
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.height(16.dp))
            AfetLogoHeader(textColor = Zinc950, showSubtitle = true)
        }

        // Form Card
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            // Segmented Control Tabs
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(42.dp),
                shape = RoundedCornerShape(8.dp),
                color = Zinc100,
                border = androidx.compose.foundation.BorderStroke(1.dp, Zinc200),
            ) {
                Row(Modifier.padding(3.dp)) {
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                            .clickable(
                                interactionSource = remember { MutableInteractionSource() },
                                indication = null,
                                onClick = { selectedTab = 0 },
                            ),
                        shape = RoundedCornerShape(6.dp),
                        color = if (selectedTab == 0) Color.White else Color.Transparent,
                        border = if (selectedTab == 0) androidx.compose.foundation.BorderStroke(1.dp, Zinc200) else null,
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text(
                                text = "Giriş Yap",
                                fontWeight = if (selectedTab == 0) FontWeight.Bold else FontWeight.Medium,
                                color = if (selectedTab == 0) AfetCrimson else Zinc500,
                                fontSize = 13.5.sp,
                            )
                        }
                    }
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                            .clickable(
                                interactionSource = remember { MutableInteractionSource() },
                                indication = null,
                                onClick = { selectedTab = 1 },
                            ),
                        shape = RoundedCornerShape(6.dp),
                        color = if (selectedTab == 1) Color.White else Color.Transparent,
                        border = if (selectedTab == 1) androidx.compose.foundation.BorderStroke(1.dp, Zinc200) else null,
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text(
                                text = "Kayıt Ol",
                                fontWeight = if (selectedTab == 1) FontWeight.Bold else FontWeight.Medium,
                                color = if (selectedTab == 1) AfetCrimson else Zinc500,
                                fontSize = 13.5.sp,
                            )
                        }
                    }
                }
            }

            if (selectedTab == 1) {
                OutlinedTextField(
                    value = fullName,
                    onValueChange = { fullName = it },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("Ad Soyad", fontSize = 13.5.sp, color = Zinc400) },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                )
            }
            // Input Fields
            OutlinedTextField(
                value = identity,
                onValueChange = { identity = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("E-posta Adresi", fontSize = 13.5.sp, color = Zinc400) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = AfetCrimson,
                    unfocusedBorderColor = Zinc200,
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = Color.White,
                ),
            )

            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Şifre", fontSize = 13.5.sp, color = Zinc400) },
                trailingIcon = {
                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                        Icon(
                            if (passwordVisible) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,
                            contentDescription = "Şifre göster",
                            tint = Zinc400,
                            modifier = Modifier.size(18.dp),
                        )
                    }
                },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = AfetCrimson,
                    unfocusedBorderColor = Zinc200,
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = Color.White,
                ),
            )

            Button(
                onClick = {
                    if (selectedTab == 0) onLogin(identity, password)
                    else onRegister(identity, fullName, password)
                },
                enabled = !isBusy && identity.isNotBlank() && password.isNotBlank() && (selectedTab == 0 || fullName.isNotBlank()),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(46.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AfetCrimson,
                    contentColor = Color.White,
                ),
            ) {
                Text(
                    text = if (isBusy) "Sunucuyla bağlantı kuruluyor..." else if (selectedTab == 0) "Giriş Yap" else "Hesap Oluştur",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp,
                )
            }

            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                HorizontalDivider(modifier = Modifier.weight(1f), color = Zinc200)
                Text("  veya  ", color = Zinc400, fontSize = 12.sp)
                HorizontalDivider(modifier = Modifier.weight(1f), color = Zinc200)
            }

            Text("e-Devlet kimlik doğrulaması bu sürümde kullanılamıyor.", fontSize = 12.sp, color = Zinc500, textAlign = TextAlign.Center)

            if (error != null) {
                Text(error, fontSize = 12.sp, color = AfetCrimson, textAlign = TextAlign.Center)
            }

            TextButton(
                onClick = onGuest,
                enabled = !isBusy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = "Misafir Oturumu Aç (Acil Mod)",
                    color = Zinc600,
                    fontWeight = FontWeight.Medium,
                    fontSize = 13.sp,
                )
            }
        }

        // Footer
        Text(
            text = "KVKK Aydınlatma Metni ve Kullanım Şartları",
            fontSize = 11.5.sp,
            color = Zinc400,
        )
    }
}
