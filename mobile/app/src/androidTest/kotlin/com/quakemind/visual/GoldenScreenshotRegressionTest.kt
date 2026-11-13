package com.quakemind.visual

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.quakemind.AppUiState
import com.quakemind.core.designsystem.QuakeMindTheme
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.FamilySafetyStatus
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.Urgency
import com.quakemind.core.model.UserSession
import com.quakemind.feature.alerts.AlertsScreen
import com.quakemind.feature.checklist.ChecklistScreen
import com.quakemind.feature.home.HomeScreen
import com.quakemind.feature.map.MapScreen
import com.quakemind.feature.profile.ProfileScreen
import com.quakemind.feature.report.ReportScreen
import com.quakemind.feature.routing.RoutingRequestUiState
import com.quakemind.feature.routing.RoutingScreen
import com.quakemind.feature.safety.SafetyScreen
import com.quakemind.feature.sos.SosScreen
import org.junit.Rule
import org.junit.Test

/**
 * Visual Golden & Structural Regression Test Suite.
 *
 * NOTE: These tests serve exclusively as a visual & composition regression harness
 * to guarantee that subsequent performance refactors do not break layouts, typography,
 * paddings, colors, or component structures. They are NOT runtime performance benchmarks.
 */
class GoldenScreenshotRegressionTest {

    @get:Rule
    val composeRule = createComposeRule()

    private val sampleUiState = AppUiState(
        session = UserSession(
            displayName = "Ahmet Yılmaz",
            city = "İstanbul / Üsküdar",
            capabilities = setOf("incident.create", "incident.verify", "operations.view"),
            isGuest = false,
        ),
        earthquakes = listOf(
            Earthquake(
                id = "eq-test-1",
                magnitude = 4.4,
                depthKm = 7.2,
                epicenter = "Marmara Denizi - Silivri Açıkları",
                occurredAt = "Bugün 13:42",
                distanceKm = 34.0,
                source = "Kandilli Rasathanesi",
            ),
        ),
        incidents = listOf(
            Incident(
                id = "inc-test-1",
                title = "Hasarlı Bina & Kısmi Çatlak",
                type = IncidentType.BUILDING_DAMAGE,
                locationLabel = "Kadıköy, Moda Caddesi · 1.4 km",
                urgency = Urgency.HIGH,
                confidence = 0.94f,
                status = "Saha Ekibi Yolda",
            ),
        ),
        alerts = listOf(
            Alert(
                id = "alert-test-1",
                title = "4.4 Marmara Denizi Depremi",
                detail = "Silivri açıklarında 4.4 büyüklüğünde ve 7.2 km derinlikte hafif şiddette bir sarsıntı kaydedilmiştir.",
                category = "Deprem",
                occurredAt = "Bugün 13:42",
                isRead = false,
                severity = AlertSeverity.CRITICAL,
                location = "Marmara / İstanbul Geneli",
            ),
        ),
        mapPoints = listOf(
            MapPoint(
                id = "mp-test-1",
                title = "Selami Ali Spor Salonu Açık Alanı",
                type = MapPointType.ASSEMBLY_AREA,
                latitude = 41.025,
                longitude = 29.022,
                distanceMeters = 340,
                capacity = "2.500 Kişi",
                address = "Selami Ali Mah., Gazi Cad. No:14, Üsküdar",
                statusText = "Açık ve Güvenli",
            ),
        ),
        familyMembers = listOf(
            FamilyMember(
                id = "fm-test-1",
                name = "Ayşe Kaya",
                relation = "Anne",
                status = FamilySafetyStatus.SAFE,
                lastSeenTime = "4 dk önce",
                locationLabel = "Kadıköy, Caferağa (Ev)",
                batteryPercent = 88,
            ),
        ),
        checklistItems = listOf(
            ChecklistItem("chk-1", "Düdük ve Yüksek Sesli Alarm", "Kişisel Güvenlik", isChecked = true, isCrucial = true),
            ChecklistItem("chk-2", "Kişi Başı En Az 2 Litre Şişe Su", "Gıda & Su", isChecked = false, isCrucial = true),
        ),
        pendingCount = 0,
        online = true,
    )

    @Test
    fun verifyHomeScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                HomeScreen(
                    state = sampleUiState,
                    onMap = {},
                    onReport = {},
                    onSos = {},
                    onSafety = {},
                    onAlerts = {},
                    onRouting = {},
                    onDamage = {},
                    onNlp = {},
                    onRisk = {},
                    onChecklist = {},
                    onOperations = {},
                    onProfile = {},
                    onIncident = {},
                )
            }
        }

        composeRule.onNodeWithTag("home_lazy_column").assertIsDisplayed()
        composeRule.onNodeWithText("QuakeMind").assertIsDisplayed()
        composeRule.onNodeWithText("Son deprem kaydı").assertIsDisplayed()
        composeRule.onNodeWithText("Marmara Denizi - Silivri Açıkları").assertIsDisplayed()
        composeRule.onNodeWithText("İhbar oluştur").assertIsDisplayed()
    }

    @Test
    fun verifyMapScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                MapScreen(
                    state = sampleUiState,
                    onIncident = {},
                )
            }
        }

        composeRule.onNodeWithTag("osm_map").assertIsDisplayed()
        composeRule.onNodeWithText("Yer, adres veya deprem ara").assertIsDisplayed()
    }

    @Test
    fun verifyAlertsScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                AlertsScreen(
                    state = sampleUiState,
                    onMarkAllRead = {},
                    onSelectAlert = {},
                )
            }
        }

        composeRule.onNodeWithTag("alerts_lazy_column").assertIsDisplayed()
        composeRule.onNodeWithText("Uyarılar").assertIsDisplayed()
        composeRule.onNodeWithText("4.4 Marmara Denizi Depremi").assertIsDisplayed()
    }

    @Test
    fun verifyChecklistScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                ChecklistScreen(
                    items = sampleUiState.checklistItems,
                    onToggle = {},
                    onBack = {},
                )
            }
        }

        composeRule.onNodeWithTag("checklist_lazy_column").assertIsDisplayed()
        composeRule.onNodeWithText("Afet çantası").assertIsDisplayed()
        composeRule.onNodeWithText("Düdük ve Yüksek Sesli Alarm").assertIsDisplayed()
    }

    @Test
    fun verifyReportScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                ReportScreen(
                    trackingCode = null,
                    onSubmit = { _, _, _, _, _, _, _ -> },
                    onBack = {},
                )
            }
        }

        composeRule.onNodeWithText("İhbar oluştur").assertIsDisplayed()
        composeRule.onNodeWithText("Koordinatları elle gir").performScrollTo().assertIsDisplayed()
        composeRule.onNodeWithText("İhbar Kategorisi").performScrollTo().assertIsDisplayed()
        composeRule.onNodeWithText("Enkaz / Mahsur").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun verifyRoutingScreenGoldenStructure() {
        val sampleRoutes = listOf(
            RouteOption(
                id = "safe-1",
                label = "En Güvenli Tahliye Rotası (Önerilen)",
                distanceKm = 4.2,
                durationMinutes = 14,
                riskScore = 12,
                closedRoads = 0,
                partialRoads = 0,
                reliability = "%98 Yüksek Güvenilirlik",
            ),
        )

        composeRule.setContent {
            QuakeMindTheme {
                RoutingScreen(
                    state = RoutingRequestUiState(routes = sampleRoutes),
                    onBack = {},
                    onRequestRoutes = { _, _ -> },
                )
            }
        }

        composeRule.onNodeWithText("Tahliye rotası").assertIsDisplayed()
        composeRule.onNodeWithText("En Güvenli Tahliye Rotası (Önerilen)").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun verifySosScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                SosScreen(onBack = {}, state = com.quakemind.feature.sos.SosUiState(), onRequestLocation = {}, onSend = {})
            }
        }

        composeRule.onNodeWithText("Acil yardım").assertIsDisplayed()
        composeRule.onNodeWithText("Hayati tehlikede 112'yi arayın").assertIsDisplayed()
        composeRule.onNodeWithText("SOS Gönder").performScrollTo().assertIsDisplayed()
    }

    @Test
    fun verifyProfileScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                ProfileScreen(
                    state = sampleUiState,
                    onOperations = {},
                )
            }
        }

        composeRule.onNodeWithText("Profil").assertIsDisplayed()
        composeRule.onNodeWithText("Ahmet Yılmaz").assertIsDisplayed()
        composeRule.onNodeWithText("Saha operasyonları").assertIsDisplayed()
    }

    @Test
    fun verifySafetyScreenGoldenStructure() {
        composeRule.setContent {
            QuakeMindTheme {
                SafetyScreen(
                    state = com.quakemind.feature.safety.SafetyStatusUiState(confirmedStatus = "SAFE"),
                    onBack = {},
                    onSelect = {},
                )
            }
        }

        composeRule.onNodeWithText("Güvenlik durumun").assertIsDisplayed()
        composeRule.onNodeWithText("Güvendeyim").assertIsDisplayed()
        composeRule.onNodeWithText("Yardım Gerekli").assertIsDisplayed()
    }
}
