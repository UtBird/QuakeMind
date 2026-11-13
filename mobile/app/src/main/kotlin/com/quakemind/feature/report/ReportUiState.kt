package com.quakemind.feature.report

import com.quakemind.feature.location.DeviceLocationFix

data class ReportUiState(
    val isSubmitting: Boolean = false,
    val lastTrackingCode: String? = null,
    val submissionError: String? = null,
    val syncWarning: String? = null,
    val locationFix: DeviceLocationFix? = null,
    val isLocating: Boolean = false,
    val locationError: String? = null,
)
