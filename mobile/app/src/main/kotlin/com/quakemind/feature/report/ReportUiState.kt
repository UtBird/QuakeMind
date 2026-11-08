package com.quakemind.feature.report

data class ReportUiState(
    val isSubmitting: Boolean = false,
    val lastTrackingCode: String? = null,
    val submissionError: String? = null,
    val syncWarning: String? = null,
)
