package com.quakemind.feature.operations

import com.quakemind.core.model.Incident

data class OperationsUiState(
    val incidents: List<Incident> = emptyList(),
    val pendingCount: Int = 0,
)
