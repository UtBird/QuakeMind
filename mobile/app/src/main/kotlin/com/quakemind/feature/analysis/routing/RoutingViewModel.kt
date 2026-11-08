package com.quakemind.feature.analysis.routing

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.RoutingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RoutingViewModel @Inject constructor(
    private val routingRepository: RoutingRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(RoutingUiState())
    val state: StateFlow<RoutingUiState> = _state.asStateFlow()

    fun loadRoutes() {
        viewModelScope.launch {
            if (_state.value.isLoading) return@launch
            _state.update { it.copy(isLoading = true, routes = emptyList(), selectedRoute = null, error = null) }
            try {
                val routeList = routingRepository.routeOptions()
                _state.update { it.copy(routes = routeList, selectedRoute = routeList.firstOrNull(), isLoading = false) }
            } catch (cancel: CancellationException) {
                throw cancel
            } catch (_: Exception) {
                _state.update { it.copy(isLoading = false, error = "Tahliye rota verisi alınamadı. Konum ve bağlantı durumunu kontrol ederek tekrar deneyin.") }
            }
        }
    }
}
