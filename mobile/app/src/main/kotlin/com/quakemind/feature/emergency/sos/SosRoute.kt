package com.quakemind.feature.emergency.sos

import androidx.compose.runtime.Composable
import com.quakemind.feature.sos.SosScreen

@Composable
fun SosRoute(
    onBack: () -> Unit,
) {
    SosScreen(onBack = onBack)
}
