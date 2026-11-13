package com.quakemind.feature.alerts

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun AlertsRoute(
    onSelectAlert: (String) -> Unit,
    viewModel: AlertsViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    AlertsScreen(
        state = state,
        onMarkAllRead = { viewModel.markAllRead() },
        onSelectAlert = onSelectAlert,
    )
}

@Composable
fun AlertDetailRoute(
    id: String,
    onBack: () -> Unit,
    onSafety: () -> Unit,
    onMap: () -> Unit,
    viewModel: AlertsViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    AlertDetailScreen(
        id = id,
        state = state,
        onBack = onBack,
        onSafety = onSafety,
        onMap = onMap,
    )
}
