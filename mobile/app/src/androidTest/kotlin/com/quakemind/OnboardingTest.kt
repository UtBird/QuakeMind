package com.quakemind

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Rule
import org.junit.Test

class OnboardingTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun guestCanReachHomeFromOnboarding() {
        // Wait for Splash delay to complete and Onboarding to be displayed
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("Anlık Deprem ve Sismik Bilgilendirme"))
                .fetchSemanticsNodes().isNotEmpty() ||
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("Atla"))
                .fetchSemanticsNodes().isNotEmpty()
        }

        // Skip onboarding or click continue
        val skipNode = composeRule.onNodeWithText("Atla")
        skipNode.performClick()

        // In Auth screen, click Guest button
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("Giriş Yapmadan Devam Et (Acil Mod)"))
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Giriş Yapmadan Devam Et (Acil Mod)").performClick()

        // In Home screen, assert Home content & bottom nav are displayed
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodes(androidx.compose.ui.test.hasText("Ana Sayfa"))
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Ana Sayfa").assertIsDisplayed()
    }
}
