package com.quakemind.feature.routing

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.RouteOption
import com.quakemind.core.network.api.RoutingService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RoutingRequestUiState(
    val routes: List<RouteOption> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val hasRequested: Boolean = false,
)

@HiltViewModel
class RoutingRequestViewModel @Inject constructor(
    private val routingService: RoutingService,
) : ViewModel() {
    private val _state = MutableStateFlow(RoutingRequestUiState())
    val state = _state.asStateFlow()

    fun requestRoutes(origin: GeoPoint, destination: GeoPoint) {
        if (_state.value.isLoading || origin == destination) return
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null, routes = emptyList(), hasRequested = true) }
            try {
                val routes = routingService.routes(origin, destination, "WALK")
                _state.update { it.copy(isLoading = false, routes = routes) }
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isLoading = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(
                        isLoading = false,
                        routes = emptyList(),
                        error = "Bu koordinatlar için rota alınamadı. Bağlantıyı ve girilen konumları kontrol edin.",
                    )
                }
            }
        }
    }
}
