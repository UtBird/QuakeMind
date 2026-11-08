package com.quakemind.feature.sos

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.CancellationSignal
import android.os.Looper
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.network.api.SosService
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeout
import kotlin.coroutines.resume
import javax.inject.Inject

data class SosUiState(
    val location: GeoPoint? = null,
    val accuracyMeters: Float? = null,
    val locationTimeMillis: Long? = null,
    val isLocating: Boolean = false,
    val isSending: Boolean = false,
    val serverId: String? = null,
    val error: String? = null,
)

@HiltViewModel
class SosViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val sosService: SosService,
) : ViewModel() {
    private val _state = MutableStateFlow(SosUiState())
    val state = _state.asStateFlow()

    fun requestCurrentLocation() {
        if (_state.value.isLocating || _state.value.isSending || _state.value.serverId != null) return
        viewModelScope.launch {
            _state.update { it.copy(isLocating = true, location = null, locationTimeMillis = null, error = null) }
            try {
                val location = withTimeout(20_000) { acquireLocation() }
                    ?: throw IllegalStateException("Konum sağlayıcısı yeni konum üretemedi.")
                // Only use a fresh provider fix. Do not silently send a cached location.
                if (System.currentTimeMillis() - location.time > 120_000) {
                    throw IllegalStateException("GPS konumu güncel değil.")
                }
                _state.update {
                    it.copy(
                        location = GeoPoint(location.latitude, location.longitude),
                        accuracyMeters = if (location.hasAccuracy()) location.accuracy else null,
                        locationTimeMillis = location.time,
                        isLocating = false,
                        error = null,
                    )
                }
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isLocating = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(isLocating = false, error = "Güncel konum alınamadı. Konum iznini ve GPS'i kontrol edin; acil durumda 112'yi arayın.")
                }
            }
        }
    }

    fun sendSos() {
        val snapshot = _state.value
        val point = snapshot.location ?: return
        val measuredAt = snapshot.locationTimeMillis ?: return
        if (snapshot.serverId != null || snapshot.isSending) return
        if (System.currentTimeMillis() - measuredAt > 120_000) {
            _state.update { it.copy(error = "Konum güncelliğini yitirdi; SOS göndermeden önce konumu yenileyin.", location = null) }
            return
        }
        viewModelScope.launch {
            _state.update { it.copy(isSending = true, error = null) }
            try {
                val serverId = sosService.send(location = point, priority = "kritik")
                _state.update { it.copy(isSending = false, serverId = serverId) }
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isSending = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(
                        isSending = false,
                        error = "Sunucudan SOS kayıt onayı alınamadı. 112'yi arayın veya SMS hazırlayın.",
                    )
                }
            }
        }
    }

    @SuppressLint("MissingPermission")
    private suspend fun acquireLocation(): Location? {
        val fine = context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarse = context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (!fine && !coarse) throw SecurityException("Konum izni verilmedi.")
        val manager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val provider = when {
            fine && manager.isProviderEnabled(LocationManager.GPS_PROVIDER) -> LocationManager.GPS_PROVIDER
            manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER
            else -> throw IllegalStateException("Konum servisi kapalı.")
        }
        return suspendCancellableCoroutine { continuation ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val cancelSignal = CancellationSignal()
                continuation.invokeOnCancellation { cancelSignal.cancel() }
                manager.getCurrentLocation(provider, cancelSignal, context.mainExecutor) { location ->
                    if (continuation.isActive) continuation.resume(location)
                }
            } else {
                val listener = object : LocationListener {
                    override fun onLocationChanged(location: Location) {
                        manager.removeUpdates(this)
                        if (continuation.isActive) continuation.resume(location)
                    }
                    override fun onProviderDisabled(provider: String) {
                        manager.removeUpdates(this)
                        if (continuation.isActive) continuation.resume(null)
                    }
                }
                continuation.invokeOnCancellation { manager.removeUpdates(listener) }
                manager.requestSingleUpdate(provider, listener, Looper.getMainLooper())
            }
        }
    }
}
