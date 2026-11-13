package com.quakemind.feature.analysis.routing

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.routing.RoutingRequestViewModel
import com.quakemind.feature.routing.RoutingScreen

@Composable
fun RoutingRoute(
    onBack: () -> Unit,
    viewModel: RoutingRequestViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    RoutingScreen(
        state = state,
        onBack = onBack,
        onRequestRoutes = viewModel::requestRoutes,
    )
}
