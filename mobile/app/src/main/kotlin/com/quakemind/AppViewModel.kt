package com.quakemind

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.QuakeMindRepository
import com.quakemind.core.network.monitor.NetworkMonitor
import com.quakemind.core.model.Alert
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.Urgency
import com.quakemind.core.model.UserSession
import com.quakemind.core.ui.state.AppUiState
import com.quakemind.sync.scheduler.SyncScheduler
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

private data class CoreData(
    val session: UserSession?,
    val earthquakes: List<Earthquake>,
    val incidents: List<Incident>,
    val alerts: List<Alert>,
    val pending: Int,
)

private data class FeatureData(
    val mapPoints: List<MapPoint>,
    val familyMembers: List<FamilyMember>,
    val checklistItems: List<ChecklistItem>,
)

@HiltViewModel
class AppViewModel @Inject constructor(
    private val repository: QuakeMindRepository,
    private val syncScheduler: SyncScheduler,
    private val networkMonitor: NetworkMonitor,
) : ViewModel() {

    private val coreFlow = combine(
        repository.session(),
        repository.earthquakes(),
        repository.incidents(),
        repository.alerts(),
        repository.pendingCount(),
    ) { session, earthquakes, incidents, alerts, pending ->
        CoreData(session, earthquakes, incidents, alerts, pending)
    }

    private val featureFlow = combine(
        repository.mapPoints(),
        repository.familyMembers(),
        repository.checklistItems(),
    ) { mapPoints, familyMembers, checklistItems ->
        FeatureData(mapPoints, familyMembers, checklistItems)
    }

    val state: StateFlow<AppUiState> = combine(
        coreFlow,
        featureFlow,
        networkMonitor.isOnline,
    ) { core, feature, isOnline ->
        AppUiState(
            session = core.session,
            earthquakes = core.earthquakes,
            incidents = core.incidents,
            alerts = core.alerts,
            pendingCount = core.pending,
            online = isOnline,
            mapPoints = feature.mapPoints,
            familyMembers = feature.familyMembers,
            checklistItems = feature.checklistItems,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AppUiState())

    val analysis = MutableStateFlow<NlpAnalysis?>(null)
    val damageAssessment = MutableStateFlow<DamageAssessment?>(null)
    val routes = MutableStateFlow<List<RouteOption>>(emptyList())
    val lastTrackingCode = MutableStateFlow<String?>(null)
    val safetyConfirmation = MutableStateFlow<String?>(null)
    val isAnalyzingDamage = MutableStateFlow(false)

    fun submitIncident(
        description: String,
        type: IncidentType = IncidentType.BUILDING_DAMAGE,
        urgency: Urgency = Urgency.HIGH,
        location: GeoPoint? = null,
        peopleCount: Int = 0,
        injuredCount: Int = 0,
    ) {
        if (description.isBlank()) return
        viewModelScope.launch {
            val id = "QM-${UUID.randomUUID().toString().take(8).uppercase()}"
            repository.saveIncident(
                IncidentDraft(
                    localId = id,
                    type = type,
                    description = description.trim(),
                    location = location,
                    peopleCount = peopleCount,
                    injuredCount = injuredCount,
                    urgency = urgency,
                    idempotencyKey = UUID.randomUUID().toString(),
                ),
            )
            lastTrackingCode.value = id
            syncScheduler.scheduleIncidentSync()
        }
    }

    fun analyze(text: String) {
        if (text.isBlank()) return
        viewModelScope.launch {
            analysis.value = repository.analyzeText(text)
        }
    }

    fun assessDamage(imageDesc: String = "") {
        viewModelScope.launch {
            isAnalyzingDamage.value = true
            damageAssessment.value = repository.assessDamage(imageDesc)
            isAnalyzingDamage.value = false
        }
    }

    fun loadRoutes() {
        viewModelScope.launch {
            routes.value = repository.routeOptions()
        }
    }

    fun updateSafety(status: String) {
        viewModelScope.launch {
            repository.updateSafetyStatus(status)
            safetyConfirmation.value = status
        }
    }

    fun markAllRead() {
        viewModelScope.launch {
            repository.markAllAlertsRead()
        }
    }

    fun toggleChecklistItem(id: String) {
        viewModelScope.launch {
            repository.toggleChecklistItem(id)
        }
    }

    fun updateFamilyMemberStatus(memberId: String, status: String) {
        viewModelScope.launch {
            repository.updateFamilyMemberStatus(memberId, status)
        }
    }
}
