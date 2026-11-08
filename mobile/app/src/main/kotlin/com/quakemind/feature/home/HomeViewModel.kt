package com.quakemind.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.AlertRepository
import com.quakemind.core.data.repository.EarthquakeRepository
import com.quakemind.core.data.repository.IncidentRepository
import com.quakemind.core.data.repository.SessionRepository
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.network.monitor.NetworkMonitor
import com.quakemind.feature.location.DeviceLocationProvider
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    sessionRepository: SessionRepository,
    earthquakeRepository: EarthquakeRepository,
    alertRepository: AlertRepository,
    incidentRepository: IncidentRepository,
    networkMonitor: NetworkMonitor,
    private val deviceLocationProvider: DeviceLocationProvider,
) : ViewModel() {

    private data class LocationState(
        val point: GeoPoint? = null,
        val accuracyMetres: Float? = null,
        val isLocating: Boolean = false,
        val error: String? = null,
    )

    private val locationState = MutableStateFlow(LocationState())

    private val feedFlow = combine(
        sessionRepository.session(),
        earthquakeRepository.earthquakes(),
        alertRepository.alerts(),
    ) { session, earthquakes, alerts ->
        Triple(session, earthquakes, alerts)
    }

    private val initialState = HomeUiState(
        session = sessionRepository.currentSession(),
        earthquakes = earthquakeRepository.currentEarthquakes(),
        alerts = alertRepository.currentAlerts(),
        pendingCount = 0,
        online = true,
    )

    val state: StateFlow<HomeUiState> = combine(
        feedFlow,
        incidentRepository.pendingCount().distinctUntilChanged(),
        networkMonitor.isOnline,
        locationState,
    ) { feed, pending, isOnline, location ->
        HomeUiState(
            session = feed.first,
            earthquakes = feed.second,
            alerts = feed.third,
            pendingCount = pending,
            online = isOnline,
            deviceLocation = location.point,
            accuracyMetres = location.accuracyMetres,
            isLocating = location.isLocating,
            locationError = location.error,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initialState)

    fun locationPermissionDenied() {
        locationState.update {
            it.copy(point = null, accuracyMetres = null, isLocating = false,
                error = "Yakındaki depremleri ve konum tabanlı analizi görmek için konum izni gerekli.")
        }
    }

    fun refreshLocation() {
        if (locationState.value.isLocating) return
        viewModelScope.launch {
            locationState.update { it.copy(isLocating = true, error = null) }
            try {
                val fix = deviceLocationProvider.currentFix()
                locationState.update {
                    it.copy(
                        point = fix.point,
                        accuracyMetres = fix.accuracyMetres,
                        isLocating = false,
                        error = null,
                    )
                }
            } catch (cancel: CancellationException) {
                locationState.update { it.copy(isLocating = false) }
                throw cancel
            } catch (_: Exception) {
                locationState.update {
                    it.copy(
                        isLocating = false,
                        error = "Cihaz konumu alınamadı. Konum iznini ve GPS ayarlarını kontrol edin.",
                    )
                }
            }
        }
    }
}
