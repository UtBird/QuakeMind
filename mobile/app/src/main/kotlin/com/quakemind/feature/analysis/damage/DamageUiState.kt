package com.quakemind.feature.analysis.damage

import com.quakemind.core.model.DamageAssessment

data class DamageUiState(
    val isAnalyzing: Boolean = false,
    val assessment: DamageAssessment? = null,
)
