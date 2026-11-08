package com.quakemind.feature.preparedness.checklist

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.checklist.ChecklistScreen

@Composable
fun ChecklistRoute(
    onBack: () -> Unit,
    viewModel: ChecklistViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    ChecklistScreen(
        items = state.items,
        onToggle = { viewModel.toggleChecklistItem(it) },
        onBack = onBack,
    )
}
