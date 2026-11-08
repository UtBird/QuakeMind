package com.quakemind.core.data.repository

import com.quakemind.core.data.datasource.local.AlertLocalDataSource
import com.quakemind.core.data.datasource.local.ChecklistLocalDataSource
import com.quakemind.core.data.datasource.local.EarthquakeLocalDataSource
import com.quakemind.core.data.datasource.local.IncidentLocalDataSource
import com.quakemind.core.data.datasource.local.MapLocalDataSource
import com.quakemind.core.data.datasource.local.SafetyLocalDataSource
import com.quakemind.core.data.datasource.local.SessionLocalDataSource
import com.quakemind.core.data.datasource.remote.AiRemoteDataSource
import com.quakemind.core.data.datasource.remote.AlertRemoteDataSource
import com.quakemind.core.data.datasource.remote.EarthquakeRemoteDataSource
import com.quakemind.core.data.datasource.remote.IncidentRemoteDataSource
import com.quakemind.core.data.datasource.remote.RoutingRemoteDataSource
import com.quakemind.core.data.datasource.remote.SafetyRemoteDataSource
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.model.Alert
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.model.UserSession
import com.quakemind.core.network.real.BackendClient
import com.quakemind.core.network.real.mapProfile
import com.quakemind.core.network.api.MapService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.emitAll
import javax.inject.Inject
import javax.inject.Singleton

import kotlinx.coroutines.flow.map

@Singleton
class OfflineFirstIncidentRepository @Inject constructor(
    private val localDataSource: IncidentLocalDataSource,
    private val remoteDataSource: IncidentRemoteDataSource,
) : IncidentRepository {

    override fun incidents(): Flow<List<Incident>> = flow {
        // The remote endpoint is authoritative. A failed fetch never produces fake incidents.
        val online = runCatching { remoteDataSource.getNearbyIncidents() }.getOrElse { emptyList() }
        emitAll(localDataSource.observePendingCount().map { online })
    }

    override fun pendingCount(): Flow<Int> = localDataSource.observePendingCount()

    override suspend fun saveIncident(draft: IncidentDraft): String {
        val location = requireNotNull(draft.location) { "İhbar gönderimi için doğrulanmış konum gerekli." }
        val now = System.currentTimeMillis()
        localDataSource.enqueue(
            IncidentEntity(
                localId = draft.localId,
                serverId = null,
                type = draft.type.name,
                description = draft.description,
                latitude = location.latitude,
                longitude = location.longitude,
                createdAt = now,
                updatedAt = now,
                syncStatus = SyncStatus.PENDING,
                retryCount = 0,
                version = 1,
                conflict = false,
                idempotencyKey = draft.idempotencyKey,
            ),
        )
        return draft.localId
    }
}

@Singleton
class DefaultEarthquakeRepository @Inject constructor(
    private val localDataSource: EarthquakeLocalDataSource,
    private val remoteDataSource: EarthquakeRemoteDataSource,
) : EarthquakeRepository {
    override fun earthquakes(): Flow<List<Earthquake>> = flow {
        runCatching { remoteDataSource.getNearbyEarthquakes() }
            .onSuccess { localDataSource.setEarthquakes(it) }
        emitAll(localDataSource.observeEarthquakes())
    }
    override fun currentEarthquakes(): List<Earthquake> = localDataSource.getEarthquakes()
}

@Singleton
class DefaultAlertRepository @Inject constructor(
    private val localDataSource: AlertLocalDataSource,
    private val remoteDataSource: AlertRemoteDataSource,
) : AlertRepository {
    override fun alerts(): Flow<List<Alert>> = flow {
        runCatching { remoteDataSource.getAlerts() }
            .onSuccess { localDataSource.setAlerts(it) }
        emitAll(localDataSource.observeAlerts())
    }
    override fun currentAlerts(): List<Alert> = localDataSource.getAlerts()
    override suspend fun markAllAlertsRead() {
        localDataSource.markAllAlertsRead()
    }
}

@Singleton
class DefaultRoutingRepository @Inject constructor(
    private val remoteDataSource: RoutingRemoteDataSource,
) : RoutingRepository {
    // No origin/destination is supplied by this old screen. Do not fabricate a real route.
    override suspend fun routeOptions(): List<RouteOption> = emptyList()
    override suspend fun routeOptions(origin: GeoPoint, destination: GeoPoint): List<RouteOption> =
        remoteDataSource.getRouteOptions(origin, destination)
}

@Singleton
class DefaultMapRepository @Inject constructor(
    private val localDataSource: MapLocalDataSource,
    private val remote: MapService? = null,
) : MapRepository {
    override fun mapPoints(): Flow<List<MapPoint>> = localDataSource.observeMapPoints()
    override fun currentMapPoints(): List<MapPoint> = localDataSource.getMapPoints()
    override suspend fun refresh(location: GeoPoint) {
        val service = remote ?: return
        localDataSource.setMapPoints(service.nearby(location))
    }
}

@Singleton
class DefaultPreparednessRepository @Inject constructor(
    private val localDataSource: ChecklistLocalDataSource,
) : PreparednessRepository {
    override fun checklistItems(): Flow<List<ChecklistItem>> = localDataSource.observeChecklistItems()
    override fun currentChecklistItems(): List<ChecklistItem> = localDataSource.getChecklistItems()
    override suspend fun toggleChecklistItem(id: String) {
        localDataSource.toggleChecklistItem(id)
    }
}

@Singleton
class DefaultSafetyRepository @Inject constructor(
    private val localDataSource: SafetyLocalDataSource,
    private val remoteDataSource: SafetyRemoteDataSource,
) : SafetyRepository {
    override fun familyMembers(): Flow<List<FamilyMember>> = localDataSource.observeFamilyMembers()
    override fun currentFamilyMembers(): List<FamilyMember> = localDataSource.getFamilyMembers()

    override suspend fun updateSafetyStatus(status: String) {
        localDataSource.updateSafetyStatus(status)
        remoteDataSource.updateSafetyStatus(status)
    }

    override suspend fun updateFamilyMemberStatus(memberId: String, status: String) {
        localDataSource.updateFamilyMemberStatus(memberId, status)
    }
}

@Singleton
class DefaultSessionRepository @Inject constructor(
    private val backend: BackendClient,
) : SessionRepository {
    override fun session(): Flow<UserSession> = backend.profiles.map { profile ->
        profile?.let(::mapProfile) ?: UNAUTHENTICATED_SESSION
    }
    override fun currentSession(): UserSession = backend.savedProfile()?.let(::mapProfile) ?: UNAUTHENTICATED_SESSION
}

private val UNAUTHENTICATED_SESSION = UserSession(
    displayName = "Oturum açılmadı",
    city = "",
    capabilities = emptySet(),
    isGuest = true,
    phone = "",
    bloodType = "",
)

@Singleton
class DefaultAiAnalysisRepository @Inject constructor(
    private val remoteDataSource: AiRemoteDataSource,
) : AiAnalysisRepository {
    override suspend fun analyzeText(text: String): NlpAnalysis = remoteDataSource.analyzeText(text)
    override suspend fun assessDamage(imageDesc: String): DamageAssessment = remoteDataSource.assessDamage(imageDesc)
}

@Singleton
class DefaultQuakeMindRepository @Inject constructor(
    private val sessionRepo: SessionRepository,
    private val earthquakeRepo: EarthquakeRepository,
    private val incidentRepo: IncidentRepository,
    private val alertRepo: AlertRepository,
    private val mapRepo: MapRepository,
    private val preparednessRepo: PreparednessRepository,
    private val routingRepo: RoutingRepository,
    private val safetyRepo: SafetyRepository,
    private val aiAnalysisRepo: AiAnalysisRepository,
) : QuakeMindRepository,
    SessionRepository by sessionRepo,
    EarthquakeRepository by earthquakeRepo,
    IncidentRepository by incidentRepo,
    AlertRepository by alertRepo,
    MapRepository by mapRepo,
    PreparednessRepository by preparednessRepo,
    RoutingRepository by routingRepo,
    SafetyRepository by safetyRepo,
    AiAnalysisRepository by aiAnalysisRepo
