package com.quakemind.feature.location

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
import androidx.core.content.getSystemService
import com.quakemind.core.model.GeoPoint
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

data class DeviceLocationFix(
    val point: GeoPoint,
    val accuracyMetres: Float?,
    val timestampMillis: Long,
)

@Singleton
class DeviceLocationProvider @Inject constructor(
    @param:ApplicationContext private val context: Context,
) {
    @SuppressLint("MissingPermission")
    suspend fun currentFix(): DeviceLocationFix {
        val fineGranted = context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED
        val coarseGranted = context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED
        if (!fineGranted && !coarseGranted) throw SecurityException("Konum izni yok.")

        val manager = context.getSystemService<LocationManager>()
            ?: throw IllegalStateException("Konum servisi kullanılamıyor.")
        val providers = buildList {
            if (fineGranted && manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                add(LocationManager.GPS_PROVIDER)
            }
            if (manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                add(LocationManager.NETWORK_PROVIDER)
            }
        }
        if (providers.isEmpty()) throw IllegalStateException("Konum servisi kapalı.")

        val recentFix = providers
            .mapNotNull { provider -> runCatching { manager.getLastKnownLocation(provider) }.getOrNull() }
            .filter(::isRecentAndValid)
            .minByOrNull { location -> if (location.hasAccuracy()) location.accuracy else Float.MAX_VALUE }
        if (recentFix != null) return recentFix.toDeviceFix()

        providers.forEach { provider ->
            val timeoutMillis = if (provider == LocationManager.GPS_PROVIDER) 12_000L else 8_000L
            val fix = withTimeoutOrNull(timeoutMillis) { requestCurrentLocation(manager, provider) }
            if (fix != null && isRecentAndValid(fix)) return fix.toDeviceFix()
        }
        throw IllegalStateException("Güncel konum alınamadı.")
    }

    @SuppressLint("MissingPermission")
    @Suppress("DEPRECATION")
    private suspend fun requestCurrentLocation(manager: LocationManager, provider: String): Location? =
        suspendCancellableCoroutine { continuation ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val cancellation = CancellationSignal()
                continuation.invokeOnCancellation { cancellation.cancel() }
                manager.getCurrentLocation(provider, cancellation, context.mainExecutor) { fix ->
                    if (continuation.isActive) continuation.resume(fix)
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

    private fun isRecentAndValid(location: Location): Boolean {
        val ageMillis = System.currentTimeMillis() - location.time
        return ageMillis in 0..120_000L && location.latitude.isFinite() &&
            location.longitude.isFinite() && location.latitude in -90.0..90.0 &&
            location.longitude in -180.0..180.0
    }

    private fun Location.toDeviceFix() = DeviceLocationFix(
        point = GeoPoint(latitude, longitude),
        accuracyMetres = if (hasAccuracy()) accuracy else null,
        timestampMillis = time,
    )
}

fun distanceMetres(from: GeoPoint, to: GeoPoint): Float {
    val distance = FloatArray(1)
    Location.distanceBetween(from.latitude, from.longitude, to.latitude, to.longitude, distance)
    return distance[0]
}
