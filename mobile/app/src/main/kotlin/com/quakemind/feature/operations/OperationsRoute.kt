package com.quakemind.feature.operations

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun OperationsRoute(
    onBack: () -> Unit,
    viewModel: OperationsViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    OperationsScreen(
        state = state,
        onBack = onBack,
    )
}
