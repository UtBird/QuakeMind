package com.quakemind.feature.analysis.nlp

import com.quakemind.core.model.NlpAnalysis

data class NlpUiState(
    val isAnalyzing: Boolean = false,
    val analysis: NlpAnalysis? = null,
    val error: String? = null,
)
