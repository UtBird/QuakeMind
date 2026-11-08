package com.quakemind.feature.emergency.safety

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.safety.SafetyScreen

@Composable
fun SafetyRoute(
    onBack: () -> Unit,
    viewModel: SafetyViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    SafetyScreen(
        confirmation = state.confirmation,
        onBack = onBack,
        onSelect = { viewModel.updateSafety(it) },
    )
}
