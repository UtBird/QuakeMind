package com.quakemind.feature.report

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.location.rememberDeviceLocationRequest

@Composable
fun ReportRoute(
    onBack: () -> Unit,
    viewModel: ReportViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val requestLocation = rememberDeviceLocationRequest { granted ->
        if (granted) viewModel.locate() else viewModel.locationPermissionDenied()
    }
    LaunchedEffect(Unit) {
        if (state.lastTrackingCode == null && state.locationFix == null && state.locationError == null) {
            requestLocation()
        }
    }
    ReportScreen(
        trackingCode = state.lastTrackingCode,
        isSubmitting = state.isSubmitting,
        submissionError = state.submissionError,
        syncWarning = state.syncWarning,
        locationFix = state.locationFix,
        isLocating = state.isLocating,
        locationError = state.locationError,
        onRequestLocation = requestLocation,
        onSubmit = { desc, type, urg, people, injured, location, fix ->
            viewModel.submitIncident(
                description = desc,
                type = type,
                urgency = urg,
                peopleCount = people,
                injuredCount = injured,
                location = location,
                locationSource = if (fix == null) "manuel" else "gps",
                locationAccuracyMetres = fix?.accuracyMetres,
            )
        },
        onBack = onBack,
    )
}
