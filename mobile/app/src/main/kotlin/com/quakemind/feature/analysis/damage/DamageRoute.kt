package com.quakemind.feature.analysis.damage

import androidx.compose.runtime.Composable
import com.quakemind.feature.damage.DamageScreen

@Composable
fun DamageRoute(
    onBack: () -> Unit,
    onReport: () -> Unit,
) {
    DamageScreen(
        onBack = onBack,
        onReport = onReport,
    )
}
