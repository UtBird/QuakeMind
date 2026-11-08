package com.quakemind.feature.alerts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.AlertRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AlertsViewModel @Inject constructor(
    private val alertRepository: AlertRepository,
) : ViewModel() {

    val state: StateFlow<AlertsUiState> = alertRepository.alerts().map { alertList ->
        AlertsUiState(alerts = alertList)
    }.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        AlertsUiState(alerts = alertRepository.currentAlerts()),
    )

    fun markAllRead() {
        viewModelScope.launch {
            alertRepository.markAllAlertsRead()
        }
    }
}
