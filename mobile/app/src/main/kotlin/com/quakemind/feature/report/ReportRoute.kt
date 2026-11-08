package com.quakemind.feature.report

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ReportRoute(
    onBack: () -> Unit,
    viewModel: ReportViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    ReportScreen(
        trackingCode = state.lastTrackingCode,
        isSubmitting = state.isSubmitting,
        submissionError = state.submissionError,
        syncWarning = state.syncWarning,
        onSubmit = { desc, type, urg, people, injured, location ->
            viewModel.submitIncident(
                description = desc,
                type = type,
                urgency = urg,
                peopleCount = people,
                injuredCount = injured,
                location = location,
            )
        },
        onBack = onBack,
    )
}
