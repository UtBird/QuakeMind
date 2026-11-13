package com.quakemind.feature.emergency.safety

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.safety.SafetyScreen
import com.quakemind.feature.safety.SafetyStatusViewModel

@Composable
fun SafetyRoute(onBack: () -> Unit, viewModel: SafetyStatusViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    SafetyScreen(state = state, onBack = onBack, onSelect = viewModel::sendStatus)
}
