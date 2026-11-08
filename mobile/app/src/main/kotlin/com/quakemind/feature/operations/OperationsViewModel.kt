package com.quakemind.feature.operations

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.IncidentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class OperationsViewModel @Inject constructor(
    incidentRepository: IncidentRepository,
) : ViewModel() {

    val state: StateFlow<OperationsUiState> = combine(
        incidentRepository.incidents(),
        incidentRepository.pendingCount(),
    ) { incidents, pending ->
        OperationsUiState(
            incidents = incidents,
            pendingCount = pending,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), OperationsUiState())
}
