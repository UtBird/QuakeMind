package com.quakemind.feature.auth.onboarding

import androidx.compose.runtime.Composable
import com.quakemind.feature.onboarding.OnboardingScreen

@Composable
fun OnboardingRoute(
    onContinue: () -> Unit,
    onSkip: () -> Unit,
) {
    OnboardingScreen(
        onContinue = onContinue,
        onSkip = onSkip,
    )
}
