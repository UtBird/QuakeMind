package com.quakemind.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.quakemind.core.designsystem.AfetLogoHeader

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AuthScreen(
    onLogin: (String, String) -> Unit,
    onRegister: (String, String, String) -> Unit,
    onGuest: () -> Unit,
    isBusy: Boolean = false,
    error: String? = null,
    onClearError: () -> Unit = {},
) {
    var registering by rememberSaveable { mutableStateOf(false) }
    var email by rememberSaveable { mutableStateOf("") }
    var fullName by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    val colors = MaterialTheme.colorScheme
    val focusManager = LocalFocusManager.current
    val canSubmit = !isBusy && email.isNotBlank() && password.isNotBlank() &&
        (!registering || fullName.isNotBlank())

    fun submit() {
        if (!canSubmit) return
        focusManager.clearFocus()
        if (registering) onRegister(email, fullName, password) else onLogin(email, password)
    }

    Box(
        modifier = Modifier.fillMaxSize().background(colors.background).statusBarsPadding(),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = 460.dp)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 28.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            AfetLogoHeader(showSubtitle = false)

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                    listOf("Giriş", "Kayıt").forEachIndexed { index, label ->
                        val isRegistration = index == 1
                        SegmentedButton(
                            selected = registering == isRegistration,
                            onClick = {
                                if (registering != isRegistration) {
                                    focusManager.clearFocus()
                                    registering = isRegistration
                                    password = ""
                                    passwordVisible = false
                                    onClearError()
                                }
                            },
                            enabled = !isBusy,
                            shape = SegmentedButtonDefaults.itemShape(index = index, count = 2),
                            label = { Text(label) },
                        )
                    }
                }

                if (registering) {
                    OutlinedTextField(
                        value = fullName,
                        onValueChange = { fullName = it; onClearError() },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text("Ad soyad") },
                        enabled = !isBusy,
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                    )
                }
                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it; onClearError() },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("E-posta adresi") },
                    enabled = !isBusy,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next),
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it; onClearError() },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Şifre") },
                    enabled = !isBusy,
                    trailingIcon = {
                        IconButton(enabled = !isBusy, onClick = { passwordVisible = !passwordVisible }) {
                            Icon(
                                imageVector = if (passwordVisible) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,
                                contentDescription = if (passwordVisible) "Şifreyi gizle" else "Şifreyi göster",
                            )
                        }
                    },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
                    keyboardActions = KeyboardActions(onDone = { submit() }),
                    visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                )

                if (error != null) {
                    Surface(
                        modifier = Modifier.fillMaxWidth().semantics { liveRegion = LiveRegionMode.Polite },
                        shape = MaterialTheme.shapes.medium,
                        color = colors.errorContainer,
                        contentColor = colors.onErrorContainer,
                    ) {
                        Text(error, Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
                    }
                }

                Button(
                    onClick = { submit() },
                    enabled = canSubmit,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                    shape = MaterialTheme.shapes.medium,
                ) {
                    Text(
                        text = when {
                            isBusy -> "Bağlanılıyor…"
                            registering -> "Hesap oluştur"
                            else -> "Giriş yap"
                        },
                        modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                        textAlign = TextAlign.Center,
                    )
                }
                TextButton(
                    onClick = {
                        focusManager.clearFocus()
                        onGuest()
                    },
                    enabled = !isBusy,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                ) {
                    Text("Misafir Oturumu Aç (Acil Mod)", textAlign = TextAlign.Center)
                }
            }

            Text(
                text = "Hayati tehlikede 112’yi arayın.",
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }
}
