package com.quakemind.feature.emergency.sos

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.sos.SosScreen
import com.quakemind.feature.sos.SosViewModel

@Composable
fun SosRoute(onBack: () -> Unit, viewModel: SosViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    SosScreen(onBack, state, viewModel::requestCurrentLocation, viewModel::sendSos)
}
