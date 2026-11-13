package com.quakemind.core.network.api

import com.quakemind.core.model.Alert
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.UserSession
import com.quakemind.core.model.MapPoint
import kotlinx.coroutines.flow.Flow

/**
 * Backend-neutral contracts. Concrete endpoint paths belong in a future remote data
 * source generated from the approved OpenAPI document.
 */
interface AuthService {
    suspend fun createGuestSession(): UserSession
    suspend fun refreshSession(refreshToken: String): UserSession
    suspend fun login(email: String, password: String): UserSession =
        throw UnsupportedOperationException("Gerçek kimlik servisi gerekli.")
    suspend fun register(email: String, fullName: String, password: String): UserSession =
        throw UnsupportedOperationException("Gerçek kimlik servisi gerekli.")
    suspend fun logout() {}
}

interface EarthquakeService {
    suspend fun nearby(location: GeoPoint?): List<Earthquake>
    fun liveEvents(): Flow<Earthquake>
}

interface IncidentService {
    suspend fun create(draft: IncidentDraft, idempotencyKey: String): Incident
    suspend fun nearby(location: GeoPoint?): List<Incident>
}

interface NlpAnalysisService {
    suspend fun analyze(text: String): NlpAnalysis
}

interface DamageDetectionService {
    suspend fun analyze(uploadId: String, analysisType: String): DamageResult
}

interface RoadStatusService {
    suspend fun roadSegments(bounds: String): List<RoadSegment>
}

interface MapService {
    suspend fun nearby(location: GeoPoint, radiusKm: Double = 5.0): List<MapPoint>
}

interface RoutingService {
    suspend fun routes(origin: GeoPoint, destination: GeoPoint, vehicle: String): List<RouteOption>
}

interface RiskAssessmentService {
    suspend fun regionalRisk(location: GeoPoint): RiskResult
}

interface NotificationService {
    suspend fun inbox(): List<Alert>
    suspend fun registerPushToken(token: String)
}

interface UserSafetyService {
    suspend fun updateStatus(status: String, location: GeoPoint?, note: String?)
}

interface SosService {
    /** Returns the server-issued SOS identifier after the call has been accepted. */
    suspend fun send(
        location: GeoPoint,
        priority: String = "kritik",
        message: String? = null,
        peopleCount: Int? = null,
    ): String
}

interface UploadService {
    suspend fun createUpload(fileName: String, contentLength: Long): UploadTicket
    suspend fun cancel(uploadId: String)
}

data class DamageResult(val type: String, val confidence: Float, val risk: String, val riskScore: Int = 0)
data class RoadSegment(val id: String, val status: String, val updatedAt: String)
data class RiskResult(val score: Int, val factors: List<String>, val updatedAt: String)
data class UploadTicket(val id: String, val uploadUrl: String)
