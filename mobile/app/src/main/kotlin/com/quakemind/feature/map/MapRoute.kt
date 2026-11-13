package com.quakemind.feature.map

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.location.rememberDeviceLocationRequest

@Composable
fun MapRoute(
    onIncident: (String) -> Unit,
    viewModel: MapViewModel = hiltViewModel(),
) {
    val requestLocation = rememberDeviceLocationRequest { granted ->
        if (granted) viewModel.refreshDeviceLocation() else viewModel.locationPermissionDenied()
    }
    var requestedLocationOnEntry by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        if (!requestedLocationOnEntry) {
            requestedLocationOnEntry = true
            requestLocation()
        }
    }
    val state by viewModel.state.collectAsStateWithLifecycle()
    MapScreen(
        state = state,
        onIncident = onIncident,
        onRequestLocation = requestLocation,
    )
}
