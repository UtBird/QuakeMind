package com.quakemind.feature.alerts

import com.quakemind.core.model.Alert

data class AlertsUiState(
    val alerts: List<Alert> = emptyList(),
    val selectedFilter: String = "Tümü",
    val isMarkingAllRead: Boolean = false,
)
