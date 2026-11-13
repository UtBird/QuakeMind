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
        val guestLabel = "Misafir Oturumu Aç (Acil Mod)"
        fun visible(text: String) = composeRule.onAllNodes(
            androidx.compose.ui.test.hasText(text),
        ).fetchSemanticsNodes(atLeastOneRootRequired = false).isNotEmpty()

        // A persisted session may legitimately skip onboarding and authentication.
        composeRule.waitUntil(timeoutMillis = 10_000) {
            visible("Ana Sayfa") || visible("Atla") || visible(guestLabel)
        }
        if (visible("Atla")) {
            composeRule.onNodeWithText("Atla").performClick()
            composeRule.waitUntil(timeoutMillis = 5_000) { visible(guestLabel) }
        }
        if (visible(guestLabel)) composeRule.onNodeWithText(guestLabel).performClick()
        composeRule.waitUntil(timeoutMillis = 10_000) { visible("Ana Sayfa") }
        composeRule.onNodeWithText("Ana Sayfa").assertIsDisplayed()
    }
}
