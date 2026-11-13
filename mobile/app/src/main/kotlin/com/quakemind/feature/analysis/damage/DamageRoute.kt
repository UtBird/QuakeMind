package com.quakemind.feature.analysis.damage

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.damage.DamageScreen
import com.quakemind.feature.damage.DamageLiveViewModel

@Composable
fun DamageRoute(onBack: () -> Unit, onReport: () -> Unit, viewModel: DamageLiveViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    DamageScreen(onBack, onReport, state, viewModel::selectPhoto, viewModel::analyzePhoto)
}
