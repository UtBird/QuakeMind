package com.quakemind.core.data.datasource.remote

import com.quakemind.core.model.Alert
import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.UserSession
import com.quakemind.core.network.api.AuthService
import com.quakemind.core.network.api.DamageDetectionService
import com.quakemind.core.network.api.EarthquakeService
import com.quakemind.core.network.api.IncidentService
import com.quakemind.core.network.api.NlpAnalysisService
import com.quakemind.core.network.api.NotificationService
import com.quakemind.core.network.api.RoutingService
import com.quakemind.core.network.api.UserSafetyService
import javax.inject.Inject
import javax.inject.Singleton

interface EarthquakeRemoteDataSource {
    suspend fun getNearbyEarthquakes(location: GeoPoint? = null): List<Earthquake>
}

@Singleton
class DefaultEarthquakeRemoteDataSource @Inject constructor(
    private val service: EarthquakeService,
) : EarthquakeRemoteDataSource {
    override suspend fun getNearbyEarthquakes(location: GeoPoint?): List<Earthquake> =
        service.nearby(location)
}

interface IncidentRemoteDataSource {
    suspend fun createIncident(draft: IncidentDraft, idempotencyKey: String): Incident
    suspend fun getNearbyIncidents(location: GeoPoint? = null): List<Incident>
}

@Singleton
class DefaultIncidentRemoteDataSource @Inject constructor(
    private val service: IncidentService,
) : IncidentRemoteDataSource {
    override suspend fun createIncident(draft: IncidentDraft, idempotencyKey: String): Incident =
        service.create(draft, idempotencyKey)

    override suspend fun getNearbyIncidents(location: GeoPoint?): List<Incident> =
        service.nearby(location)
}

interface AlertRemoteDataSource {
    suspend fun getAlerts(): List<Alert>
}

@Singleton
class DefaultAlertRemoteDataSource @Inject constructor(
    private val service: NotificationService,
) : AlertRemoteDataSource {
    override suspend fun getAlerts(): List<Alert> = service.inbox()
}

interface RoutingRemoteDataSource {
    suspend fun getRouteOptions(origin: GeoPoint, destination: GeoPoint): List<RouteOption>
}

@Singleton
class DefaultRoutingRemoteDataSource @Inject constructor(
    private val service: RoutingService,
) : RoutingRemoteDataSource {
    override suspend fun getRouteOptions(origin: GeoPoint, destination: GeoPoint): List<RouteOption> =
        service.routes(origin, destination, "WALK")
}

interface SafetyRemoteDataSource {
    suspend fun updateSafetyStatus(status: String)
}

@Singleton
class DefaultSafetyRemoteDataSource @Inject constructor(
    private val service: UserSafetyService,
) : SafetyRemoteDataSource {
    override suspend fun updateSafetyStatus(status: String) {
        service.updateStatus(status, null, null)
    }
}

interface AiRemoteDataSource {
    suspend fun analyzeText(text: String): NlpAnalysis
    suspend fun assessDamage(imageDesc: String): DamageAssessment
}

@Singleton
class DefaultAiRemoteDataSource @Inject constructor(
    private val nlpService: NlpAnalysisService,
    private val damageService: DamageDetectionService,
) : AiRemoteDataSource {
    override suspend fun analyzeText(text: String): NlpAnalysis = nlpService.analyze(text)

    override suspend fun assessDamage(imageDesc: String): DamageAssessment {
        require(imageDesc.length > 100) { "Lütfen gerçek bir fotoğraf seçin." }
        val result = damageService.analyze(imageDesc, "ikisi")
        return DamageAssessment(
            damageGrade = result.type,
            confidence = result.confidence,
            riskScore = result.riskScore,
            recommendation = if (result.riskScore > 0) "Görüntüde model tespiti var. Bu ön inceleme yapı güvenliği kararı değildir."
                else "Model görüntüde hasar işaretlemedi. Bu sonuç yapının güvenli olduğu anlamına gelmez.",
            crackDetected = result.riskScore > 0,
            structuralIssue = false,
        )
    }
}
