package com.quakemind.feature.analysis.nlp

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.damage.NlpScreen

@Composable
fun NlpRoute(
    onBack: () -> Unit,
    onReport: () -> Unit,
    viewModel: NlpViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    NlpScreen(
        analysis = state.analysis,
        isAnalyzing = state.isAnalyzing,
        error = state.error,
        onBack = onBack,
        onAnalyze = { viewModel.analyze(it) },
        onReport = onReport,
    )
}
