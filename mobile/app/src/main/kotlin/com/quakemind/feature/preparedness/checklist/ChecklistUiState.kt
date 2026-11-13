package com.quakemind.feature.preparedness.checklist

import com.quakemind.core.model.ChecklistItem

data class ChecklistUiState(
    val items: List<ChecklistItem> = emptyList(),
    val completedCount: Int = 0,
    val progress: Float = 0f,
)
