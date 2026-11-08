package com.quakemind.feature.auth.splash

import androidx.compose.runtime.Composable
import com.quakemind.feature.splash.SplashScreen

@Composable
fun SplashRoute(
    onFinished: () -> Unit,
) {
    SplashScreen(onFinished = onFinished)
}
