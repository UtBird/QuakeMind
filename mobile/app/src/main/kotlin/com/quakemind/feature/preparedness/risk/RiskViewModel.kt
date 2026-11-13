package com.quakemind.feature.preparedness.risk

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.network.api.RiskAssessmentService
import com.quakemind.core.network.api.RiskResult
import com.quakemind.feature.location.DeviceLocationProvider
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RiskUiState(
    val isLocating: Boolean = false,
    val isLoading: Boolean = false,
    val location: GeoPoint? = null,
    val accuracyMetres: Float? = null,
    val result: RiskResult? = null,
    val error: String? = null,
)

@HiltViewModel
class RiskViewModel @Inject constructor(
    private val riskService: RiskAssessmentService,
    private val deviceLocationProvider: DeviceLocationProvider,
) : ViewModel() {
    private val _state = MutableStateFlow(RiskUiState())
    val state: StateFlow<RiskUiState> = _state.asStateFlow()

    fun locationPermissionDenied() {
        _state.update {
            it.copy(
                isLocating = false,
                error = "Zemin analizi için konum izni gerekli. İzin verip tekrar deneyin.",
            )
        }
    }

    fun analyzeCurrentLocation() {
        if (_state.value.isLoading || _state.value.isLocating) return
        viewModelScope.launch {
            _state.update { it.copy(isLocating = true, isLoading = false, result = null, error = null) }
            try {
                val fix = deviceLocationProvider.currentFix()
                loadRisk(fix.point, fix.accuracyMetres)
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isLocating = false, isLoading = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(
                        isLocating = false,
                        isLoading = false,
                        error = "Cihaz konumu alınamadı. Konum iznini ve GPS ayarlarını kontrol edin.",
                    )
                }
            }
        }
    }

    fun analyze(latitude: String, longitude: String) {
        val lat = latitude.trim().replace(',', '.').toDoubleOrNull()
        val lon = longitude.trim().replace(',', '.').toDoubleOrNull()
        if (lat == null || lon == null || lat !in -90.0..90.0 || lon !in -180.0..180.0) {
            _state.update { it.copy(result = null, error = "Geçerli enlem ve boylam girin.") }
            return
        }
        if (_state.value.isLoading) return
        viewModelScope.launch { loadRisk(GeoPoint(lat, lon), accuracyMetres = null) }
    }

    private suspend fun loadRisk(location: GeoPoint, accuracyMetres: Float?) {
        _state.update {
            it.copy(isLocating = false, isLoading = true, location = location, accuracyMetres = accuracyMetres, result = null, error = null)
        }
        try {
            val result = riskService.regionalRisk(location)
            _state.update { it.copy(isLoading = false, result = result) }
        } catch (cancel: CancellationException) {
            _state.update { it.copy(isLoading = false) }
            throw cancel
        } catch (_: Exception) {
            _state.update {
                it.copy(isLoading = false, error = "Bölgesel risk verisi alınamadı. Sunucu bağlantısını kontrol ederek tekrar deneyin.")
            }
        }
    }
}
