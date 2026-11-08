package com.quakemind.core.model

import kotlinx.serialization.Serializable

@Serializable
data class GeoPoint(val latitude: Double, val longitude: Double)

@Serializable
data class Earthquake(
    val id: String,
    val magnitude: Double,
    val depthKm: Double,
    val epicenter: String,
    val occurredAt: String,
    val distanceKm: Double,
    val source: String,
    val latitude: Double = 40.98,
    val longitude: Double = 29.05,
    val feltCount: Int = 142,
)

@Serializable
enum class IncidentType {
    DEBRIS, INJURED, MISSING_PERSON, FIRE, ROAD_CLOSURE, BUILDING_DAMAGE,
    WATER, FOOD, MEDICAL, SHELTER, COMMUNICATION, OTHER,
}

@Serializable
enum class Urgency { LOW, MEDIUM, HIGH, CRITICAL }

@Serializable
enum class SyncStatus { LOCAL_ONLY, PENDING, UPLOADING, SYNCED, FAILED, CONFLICT }

@Serializable
data class IncidentDraft(
    val localId: String,
    val type: IncidentType,
    val description: String,
    val location: GeoPoint?,
    val peopleCount: Int = 0,
    val injuredCount: Int = 0,
    val urgency: Urgency = Urgency.HIGH,
    val idempotencyKey: String,
    /** "manuel" for a user-entered coordinate; "gps" only for OS location readings. */
    val locationSource: String = "manuel",
)

@Serializable
data class Incident(
    val id: String,
    val title: String,
    val type: IncidentType,
    val locationLabel: String,
    val urgency: Urgency,
    val confidence: Float,
    val status: String,
    val syncStatus: SyncStatus = SyncStatus.SYNCED,
    val latitude: Double = 40.99,
    val longitude: Double = 29.02,
    val timestamp: String = "10 dk önce",
)

@Serializable
enum class AlertSeverity { CRITICAL, WARNING, INFO }

@Serializable
data class Alert(
    val id: String,
    val title: String,
    val detail: String,
    val category: String,
    val occurredAt: String,
    val isRead: Boolean = false,
    val severity: AlertSeverity = AlertSeverity.WARNING,
    val location: String = "Marmara / İstanbul",
)

@Serializable
enum class MapPointType {
    ASSEMBLY_AREA, SHELTER_TENT, SAHRA_HOSPITAL, CLOSED_ROAD, INCIDENT,
    HEALTH_FACILITY, PHARMACY, FIRE_STATION, POLICE_STATION,
}

@Serializable
data class MapPoint(
    val id: String,
    val title: String,
    val type: MapPointType,
    val latitude: Double,
    val longitude: Double,
    val distanceMeters: Int,
    val capacity: String? = null,
    val address: String,
    val statusText: String,
)

@Serializable
enum class FamilySafetyStatus { SAFE, NEED_HELP, UNKNOWN }

@Serializable
data class FamilyMember(
    val id: String,
    val name: String,
    val relation: String,
    val status: FamilySafetyStatus,
    val lastSeenTime: String,
    val locationLabel: String,
    val batteryPercent: Int = 85,
)

@Serializable
data class ChecklistItem(
    val id: String,
    val title: String,
    val category: String,
    val isChecked: Boolean = false,
    val isCrucial: Boolean = true,
)

@Serializable
data class NlpAnalysis(
    val category: IncidentType,
    val locationText: String?,
    val needs: List<String>,
    val urgency: Urgency,
    val confidence: Float,
    val requiresHumanReview: Boolean,
)

@Serializable
data class DamageAssessment(
    val damageGrade: String,
    val confidence: Float,
    val riskScore: Int,
    val recommendation: String,
    val crackDetected: Boolean = true,
    val structuralIssue: Boolean = false,
)

@Serializable
data class RouteOption(
    val id: String,
    val label: String,
    val distanceKm: Double,
    val durationMinutes: Int,
    val riskScore: Int,
    val closedRoads: Int,
    val partialRoads: Int,
    val reliability: String,
    val description: String = "Hasarlı binalar ve dar sokaklar bypass edildi.",
)

@Serializable
data class UserSession(
    val displayName: String,
    val city: String,
    val capabilities: Set<String>,
    val isGuest: Boolean,
    val phone: String = "+90 (532) *** ** 42",
    val bloodType: String = "A Rh+",
    val isVolunteer: Boolean = false,
)

object Capability {
    const val CREATE_INCIDENT = "incident.create"
    const val VERIFY_INCIDENT = "incident.verify"
    const val ASSIGN_TEAM = "incident.assign"
    const val UPDATE_ROAD = "road.update"
    const val VIEW_OPERATIONS = "operations.view"
}

sealed interface UiState<out T> {
    data object Initial : UiState<Nothing>
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Empty(val message: String) : UiState<Nothing>
    data class Error(val message: String, val canRetry: Boolean = true) : UiState<Nothing>
}

sealed interface ApiError {
    data object NoConnection : ApiError
    data object Timeout : ApiError
    data object Unauthorized : ApiError
    data object Forbidden : ApiError
    data object Server : ApiError
    data class Validation(val fields: Map<String, String>) : ApiError
    data object FileTooLarge : ApiError
    data object UnsupportedMedia : ApiError
    data object ModelUnavailable : ApiError
    data object LowConfidence : ApiError
    data object RateLimited : ApiError
    data object Maintenance : ApiError
    data class Unknown(val safeMessage: String) : ApiError
}

@Serializable
data class MediaUploadDraft(
    val id: String,
    val localUri: String,
    val mimeType: String,
    val sizeBytes: Long,
    val incidentLocalId: String,
    val chunkSizeBytes: Int = 512 * 1024,
    val uploadedBytes: Long = 0L,
    val isCompleted: Boolean = false,
)

interface AiInferenceEngine {
    val isModelLoaded: Boolean
    suspend fun loadModel()
    suspend fun unloadModel()
    fun onTrimMemory(level: Int)
}
