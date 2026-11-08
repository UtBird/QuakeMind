package com.quakemind.feature.analysis.routing

import com.quakemind.core.model.RouteOption

data class RoutingUiState(
    val routes: List<RouteOption> = emptyList(),
    val selectedRoute: RouteOption? = null,
    val isLoading: Boolean = false,
    val error: String? = null,
)
