package com.quakemind.feature.preparedness.risk

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.checklist.RiskScreen
import com.quakemind.feature.location.rememberDeviceLocationRequest

@Composable
fun RiskRoute(
    onBack: () -> Unit,
    viewModel: RiskViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val requestLocation = rememberDeviceLocationRequest { granted ->
        if (granted) viewModel.analyzeCurrentLocation() else viewModel.locationPermissionDenied()
    }
    var requestedLocationOnEntry by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        if (!requestedLocationOnEntry) {
            requestedLocationOnEntry = true
            requestLocation()
        }
    }

    RiskScreen(
        onBack = onBack,
        result = state.result,
        isLoading = state.isLoading,
        isLocating = state.isLocating,
        location = state.location,
        accuracyMetres = state.accuracyMetres,
        error = state.error,
        onAnalyze = viewModel::analyze,
        onRequestLocation = requestLocation,
    )
}
