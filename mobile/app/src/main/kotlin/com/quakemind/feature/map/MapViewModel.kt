package com.quakemind.feature.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.EarthquakeRepository
import com.quakemind.core.data.repository.MapRepository
import com.quakemind.core.model.GeoPoint
import com.quakemind.feature.location.DeviceLocationProvider
import com.quakemind.feature.location.distanceMetres
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

private data class LocationState(
    val location: GeoPoint? = null,
    val accuracyMetres: Float? = null,
    val isLocating: Boolean = false,
    val isRefreshingPoints: Boolean = false,
    val locationError: String? = null,
    val pointsError: String? = null,
)

@HiltViewModel
class MapViewModel @Inject constructor(
    private val mapRepository: MapRepository,
    private val earthquakeRepository: EarthquakeRepository,
    private val deviceLocationProvider: DeviceLocationProvider,
) : ViewModel() {
    private val locationState = MutableStateFlow(LocationState())

    val state: StateFlow<MapUiState> = combine(
        mapRepository.mapPoints(),
        earthquakeRepository.earthquakes(),
        locationState,
    ) { points, earthquakes, location ->
        val earthquakesWithDistance = location.location?.let { origin ->
            earthquakes.map { quake ->
                quake.copy(distanceKm = distanceMetres(origin, GeoPoint(quake.latitude, quake.longitude)) / 1_000.0)
            }
        } ?: earthquakes
        MapUiState(
            mapPoints = if (location.pointsError == null && !location.isRefreshingPoints) points else emptyList(),
            earthquakes = earthquakesWithDistance,
            deviceLocation = location.location,
            accuracyMetres = location.accuracyMetres,
            isLocating = location.isLocating,
            isRefreshingPoints = location.isRefreshingPoints,
            locationError = location.locationError,
            pointsError = location.pointsError,
        )
    }.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        MapUiState(
            mapPoints = mapRepository.currentMapPoints(),
            earthquakes = earthquakeRepository.currentEarthquakes(),
        ),
    )

    fun locationPermissionDenied() {
        locationState.update {
            it.copy(
                location = null,
                accuracyMetres = null,
                isLocating = false,
                locationError = "Konum izni verilmedi. Yakınındaki noktalar için izin gerekiyor.",
            )
        }
    }

    fun refreshDeviceLocation() {
        if (locationState.value.isLocating || locationState.value.isRefreshingPoints) return
        viewModelScope.launch {
            locationState.update {
                it.copy(isLocating = true, locationError = null, pointsError = null)
            }
            try {
                val fix = deviceLocationProvider.currentFix()
                val coordinates = fix.point
                locationState.update {
                    it.copy(
                        location = coordinates,
                        accuracyMetres = fix.accuracyMetres,
                        isLocating = false,
                        isRefreshingPoints = true,
                    )
                }
                try {
                    mapRepository.refresh(coordinates)
                    locationState.update { it.copy(pointsError = null) }
                } catch (cancel: CancellationException) {
                    throw cancel
                } catch (_: Exception) {
                    locationState.update {
                        it.copy(pointsError = "Yakındaki yerler sunucudan alınamadı. Bağlantıyı kontrol ederek tekrar deneyin.")
                    }
                } finally {
                    locationState.update { it.copy(isRefreshingPoints = false) }
                }
            } catch (cancel: CancellationException) {
                locationState.update { it.copy(isLocating = false, isRefreshingPoints = false) }
                throw cancel
            } catch (_: Exception) {
                locationState.update {
                    it.copy(
                        isLocating = false,
                        isRefreshingPoints = false,
                        locationError = "Cihaz konumu alınamadı. Konum iznini ve GPS ayarlarını kontrol edin.",
                    )
                }
            }
        }
    }
}
