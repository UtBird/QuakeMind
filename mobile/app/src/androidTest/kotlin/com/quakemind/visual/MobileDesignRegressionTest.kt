package com.quakemind.visual

import android.graphics.Bitmap
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.StateRestorationTester
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.Density
import androidx.test.platform.app.InstrumentationRegistry
import com.quakemind.core.designsystem.QuakeMindTheme
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.Earthquake
import com.quakemind.feature.auth.AuthScreen
import com.quakemind.feature.checklist.ChecklistScreen
import com.quakemind.feature.home.HomeScreen
import com.quakemind.feature.home.HomeUiState
import com.quakemind.feature.profile.ProfileScreen
import com.quakemind.feature.profile.ProfileUiState
import com.quakemind.feature.report.ReportScreen
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import java.io.File

class MobileDesignRegressionTest {
    @get:Rule val compose = createComposeRule()

    private val home = HomeUiState(
        earthquakes = List(30) { index ->
            Earthquake(
                id = "review-$index", magnitude = 4.4, depthKm = 7.2,
                epicenter = "Marmara Denizi · Silivri açıkları",
                occurredAt = "13.11.2026 14:32", distanceKm = 34.0,
                source = "Katalog kaynağı",
            )
        },
        online = false, pendingCount = 2,
    )

    @Test fun homeLightAndUrgentAction() {
        var reports = 0
        compose.setContent {
            QuakeMindTheme(darkTheme = false) {
                HomeScreen(home, {}, { reports++ }, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
            }
        }
        compose.onNodeWithText("İhbar oluştur").assertIsDisplayed()
        capture("home-light-phone")
        compose.onNodeWithText("İhbar oluştur").performClick()
        compose.runOnIdle { assertTrue("Report action must open the reporting flow", reports == 1) }
        compose.onNodeWithText("Saha operasyonları").assertDoesNotExist()
        compose.onNodeWithTag("home_lazy_column").performScrollToNode(hasText("İnceleme araçları"))
        compose.onNodeWithText("İnceleme araçları").assertIsDisplayed()
    }

    @Test fun darkHomeWithLargeText() {
        compose.setContent {
            val density = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(density.density, 1.6f)) {
                QuakeMindTheme(darkTheme = true) {
                    HomeScreen(home, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
                }
            }
        }
        compose.onNodeWithText("İhbar oluştur").assertIsDisplayed()
        capture("home-dark-large-type")
        compose.onNodeWithTag("home_lazy_column").performScrollToNode(hasText("Son depremler"))
        compose.onNodeWithText("Son depremler").assertIsDisplayed()
    }

    @Test fun checklistExposesToggleStateAndUpdates() {
        val checked = mutableStateOf(false)
        compose.setContent {
            QuakeMindTheme(darkTheme = true) {
                ChecklistScreen(
                    listOf(ChecklistItem("water", "İçme suyu", "Su ve gıda", checked.value, true)),
                    onToggle = { checked.value = !checked.value }, onBack = {},
                )
            }
        }
        compose.onNodeWithTag("checklist_item_water").assertIsOff().performClick().assertIsOn()
        capture("checklist-dark-phone")
    }

    @Test fun reportDraftSurvivesStateRestoration() {
        val restoration = StateRestorationTester(compose)
        restoration.setContent {
            QuakeMindTheme(darkTheme = false) {
                ReportScreen(null, { _, _, _, _, _, _, _ -> }, {})
            }
        }
        capture("report-light-phone")
        compose.onNodeWithText("Koordinatları elle gir").performScrollTo().performClick()
        compose.onNodeWithText("Enlem (ör. 39.92)").performScrollTo().performTextInput("39.92")
        restoration.emulateSavedInstanceStateRestore()
        compose.onNodeWithText("39.92").assertExists()
    }

    @Test fun guestProfileDoesNotClaimUnsupportedFeatures() {
        compose.setContent {
            QuakeMindTheme(darkTheme = true) { ProfileScreen(ProfileUiState(), {}) }
        }
        compose.onNodeWithText("Misafir oturumu").assertIsDisplayed()
        compose.onNodeWithText("Saha operasyonları").assertDoesNotExist()
        compose.onNodeWithText("e-Devlet Doğrulanmış Hesap").assertDoesNotExist()
        compose.onNode(isToggleable()).assertDoesNotExist()
        capture("profile-dark-phone")
    }

    @Test fun profileThemeSwitchUpdatesBothWays() {
        val dark = mutableStateOf(false)
        compose.setContent {
            QuakeMindTheme(darkTheme = dark.value) {
                ProfileScreen(ProfileUiState(), {}, darkTheme = dark.value, onDarkThemeChange = { dark.value = it })
            }
        }
        val theme = compose.onNodeWithText("Koyu tema")
        theme.assertIsOff().performClick().assertIsOn().performClick().assertIsOff()
    }

    @Test fun registrationAndPasswordControlsAreAccessible() {
        compose.setContent {
            QuakeMindTheme { AuthScreen({ _, _ -> }, { _, _, _ -> }, {}) }
        }
        compose.onNodeWithText("Giriş yap").assertIsNotEnabled()
        capture("auth-light-phone")
        compose.onNodeWithText("Kayıt").performClick().assertIsSelected()
        compose.onNodeWithText("Ad soyad").assertIsDisplayed()
        compose.onNodeWithContentDescription("Şifreyi göster").performClick()
        compose.onNodeWithContentDescription("Şifreyi gizle").assertIsDisplayed()
        compose.onNodeWithText("Giriş").performClick().assertIsSelected()
        compose.onNodeWithText("Ad soyad").assertDoesNotExist()
        compose.onNodeWithContentDescription("Şifreyi göster").assertIsDisplayed()
    }

    @Test fun themeForegroundPairsMeetContrast() {
        val dark = mutableStateOf(false)
        val ratios = mutableListOf<Double>()
        compose.setContent {
            QuakeMindTheme(darkTheme = dark.value) {
                val scheme = MaterialTheme.colorScheme
                val pairs = listOf(
                    com.quakemind.core.designsystem.AfetOrange to com.quakemind.core.designsystem.AfetAmberMuted,
                    androidx.compose.material3.LocalContentColor.current to scheme.background,
                    scheme.onSurface to scheme.surface,
                    scheme.onSurfaceVariant to scheme.background,
                    scheme.primary to scheme.background,
                    scheme.onPrimary to scheme.primary,
                    scheme.onSecondaryContainer to scheme.secondaryContainer,
                    scheme.onError to scheme.error,
                    scheme.onErrorContainer to scheme.errorContainer,
                )
                androidx.compose.runtime.SideEffect {
                    ratios.clear()
                    pairs.forEach { (foreground, background) ->
                        val a = foreground.luminance().toDouble()
                        val b = background.luminance().toDouble()
                        ratios += (maxOf(a, b) + .05) / (minOf(a, b) + .05)
                    }
                }
                Box(Modifier.fillMaxSize())
            }
        }
        compose.runOnIdle { ratios.forEach { assertTrue("Light contrast: $it", it >= 4.5) }; dark.value = true }
        compose.runOnIdle { ratios.forEach { assertTrue("Dark contrast: $it", it >= 4.5) } }
    }

    @Test fun onboardingProgressesThroughRealCapabilities() {
        var continued = false
        compose.setContent {
            QuakeMindTheme(darkTheme = true) {
                com.quakemind.feature.onboarding.OnboardingScreen({ continued = true }, {})
            }
        }
        compose.onNodeWithText("Deprem kayıtlarını takip et").assertIsDisplayed()
        compose.onNodeWithText("Devam Et").performClick()
        compose.onNodeWithText("Yakınındaki alanları bul").assertIsDisplayed()
        compose.onNodeWithText("Devam Et").performClick()
        compose.onNodeWithText("İhtiyacını bildir, durumunu paylaş").assertIsDisplayed()
        capture("onboarding-dark-phone")
        compose.onNodeWithText("Başlayın").performClick()
        compose.runOnIdle { assertTrue(continued) }
    }

    @Test fun analysisRequiresPhotoAndShowsServiceError() {
        compose.setContent {
            QuakeMindTheme(darkTheme = true) {
                com.quakemind.feature.damage.DamageScreen(
                    onBack = {}, onReport = {},
                    state = com.quakemind.feature.damage.DamageLiveUiState(error = "Analiz servisine ulaşılamadı."),
                    onPhotoSelected = {}, onAnalyze = {},
                )
            }
        }
        compose.onNodeWithText("Fotoğrafı Analiz Et").assertIsNotEnabled()
        compose.onNodeWithText("Analiz servisine ulaşılamadı.").assertIsDisplayed()
        capture("damage-dark-error")
    }

    @Test fun unknownAlertDoesNotDisplayUnrelatedEvent() {
        compose.setContent {
            QuakeMindTheme(darkTheme = true) {
                com.quakemind.feature.alerts.AlertDetailScreen(
                    id = "missing", state = com.quakemind.feature.alerts.AlertsUiState(),
                    onBack = {}, onSafety = {}, onMap = {},
                )
            }
        }
        compose.onNodeWithText("Uyarı bulunamadı.").assertIsDisplayed()
    }

    @Test fun darkAnalysisFieldKeepsTextAndInvokesAnalysis() {
        var analyzed = ""
        compose.setContent {
            QuakeMindTheme(darkTheme = true) {
                com.quakemind.feature.damage.NlpScreen(null, {}, { analyzed = it }, {})
            }
        }
        compose.onNode(hasSetTextAction()).performTextInput("İçme suyuna ihtiyaç var.")
        compose.onNodeWithText("Metni Yapay Zekâ ile Ayrıştır").performScrollTo().performClick()
        compose.runOnIdle { assertTrue(analyzed == "İçme suyuna ihtiyaç var.") }
        capture("nlp-dark-input")
    }

    private fun capture(name: String) {
        val directory = File(InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null), "ui-review")
        directory.mkdirs()
        File(directory, "$name.png").outputStream().use { output ->
            compose.onRoot().captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, output)
        }
    }
}
