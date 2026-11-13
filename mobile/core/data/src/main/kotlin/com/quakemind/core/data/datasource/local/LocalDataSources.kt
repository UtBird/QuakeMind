package com.quakemind.core.data.datasource.local

import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Capability
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.FamilySafetyStatus
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.model.UserSession
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

interface EarthquakeLocalDataSource {
    fun observeEarthquakes(): Flow<List<Earthquake>>
    fun getEarthquakes(): List<Earthquake> = emptyList()
    suspend fun setEarthquakes(earthquakes: List<Earthquake>)
}

@Singleton
class MemoryEarthquakeLocalDataSource @Inject constructor() : EarthquakeLocalDataSource {
    private val earthquakesFlow = MutableStateFlow(emptyList<Earthquake>())

    override fun observeEarthquakes(): Flow<List<Earthquake>> = earthquakesFlow.asStateFlow()
    override fun getEarthquakes(): List<Earthquake> = earthquakesFlow.value
    override suspend fun setEarthquakes(earthquakes: List<Earthquake>) {
        earthquakesFlow.value = earthquakes
    }
}

interface AlertLocalDataSource {
    fun observeAlerts(): Flow<List<Alert>>
    fun getAlerts(): List<Alert> = emptyList()
    suspend fun setAlerts(alerts: List<Alert>)
    suspend fun markAllAlertsRead()
}

@Singleton
class MemoryAlertLocalDataSource @Inject constructor() : AlertLocalDataSource {
    private val alertItems = MutableStateFlow(emptyList<Alert>())

    override fun observeAlerts(): Flow<List<Alert>> = alertItems.asStateFlow()
    override fun getAlerts(): List<Alert> = alertItems.value
    override suspend fun setAlerts(alerts: List<Alert>) {
        alertItems.value = alerts
    }
    override suspend fun markAllAlertsRead() {
        alertItems.update { list -> list.map { it.copy(isRead = true) } }
    }
}

interface MapLocalDataSource {
    fun observeMapPoints(): Flow<List<MapPoint>>
    fun getMapPoints(): List<MapPoint> = emptyList()
    suspend fun setMapPoints(points: List<MapPoint>) {}
}

@Singleton
class MemoryMapLocalDataSource @Inject constructor() : MapLocalDataSource {
    private val mapPointsFlow = MutableStateFlow(emptyList<MapPoint>())

    override fun observeMapPoints(): Flow<List<MapPoint>> = mapPointsFlow.asStateFlow()
    override fun getMapPoints(): List<MapPoint> = mapPointsFlow.value
    override suspend fun setMapPoints(points: List<MapPoint>) {
        mapPointsFlow.value = points
    }
}

interface SafetyLocalDataSource {
    fun observeFamilyMembers(): Flow<List<FamilyMember>>
    fun getFamilyMembers(): List<FamilyMember> = emptyList()
    suspend fun updateFamilyMemberStatus(memberId: String, status: String)
    suspend fun updateSafetyStatus(status: String)
}

@Singleton
class MemorySafetyLocalDataSource @Inject constructor() : SafetyLocalDataSource {
    private val familyMembersFlow = MutableStateFlow(emptyList<FamilyMember>())

    override fun observeFamilyMembers(): Flow<List<FamilyMember>> = familyMembersFlow.asStateFlow()
    override fun getFamilyMembers(): List<FamilyMember> = familyMembersFlow.value

    override suspend fun updateFamilyMemberStatus(memberId: String, status: String) {
        familyMembersFlow.update { list ->
            list.map {
                if (it.id == memberId) {
                    val newStatus = if (status == "SAFE") FamilySafetyStatus.SAFE else FamilySafetyStatus.NEED_HELP
                    it.copy(status = newStatus, lastSeenTime = "Az önce")
                } else it
            }
        }
    }

    override suspend fun updateSafetyStatus(status: String) {
        // Local safety state update
    }
}

interface ChecklistLocalDataSource {
    fun observeChecklistItems(): Flow<List<ChecklistItem>>
    fun getChecklistItems(): List<ChecklistItem> = emptyList()
    suspend fun toggleChecklistItem(id: String)
}

@Singleton
class MemoryChecklistLocalDataSource @Inject constructor() : ChecklistLocalDataSource {
    private val checklistItemsFlow = MutableStateFlow(
        listOf(
            ChecklistItem("chk-1", "Düdük ve Yüksek Sesli Alarm", "Kişisel Güvenlik", isChecked = false, isCrucial = true),
            ChecklistItem("chk-2", "Kişi Başı En Az 2 Litre Şişe Su", "Gıda & Su", isChecked = false, isCrucial = true),
            ChecklistItem("chk-3", "İlk Yardım Çantası (Sargı bezi, dezenfektan)", "Sağlık", isChecked = false, isCrucial = true),
            ChecklistItem("chk-4", "LED El Feneri ve Dolu Powerbank", "Enerji & Işık", isChecked = false, isCrucial = true),
            ChecklistItem("chk-5", "Pilli Acil Durum Radyosu & Yedek Pil", "Haberleşme", isChecked = false, isCrucial = true),
            ChecklistItem("chk-6", "Yüksek Kalorili Dayanıklı Konserve/Bisküvi", "Gıda & Su", isChecked = false, isCrucial = false),
            ChecklistItem("chk-7", "Önemli Evrak Fotokopileri ve Nakit Para", "Evrak & Finans", isChecked = false, isCrucial = false),
            ChecklistItem("chk-8", "N95 Toz Maskesi ve Koruyucu İş Eldiveni", "Kişisel Güvenlik", isChecked = false, isCrucial = true),
            ChecklistItem("chk-9", "Termal Battaniye ve Yağmurluk", "Barınma", isChecked = false, isCrucial = false),
            ChecklistItem("chk-10", "Sürekli Kullanılan Reçeteli İlaçlar", "Sağlık", isChecked = false, isCrucial = true),
        ),
    )

    override fun observeChecklistItems(): Flow<List<ChecklistItem>> = checklistItemsFlow.asStateFlow()
    override fun getChecklistItems(): List<ChecklistItem> = checklistItemsFlow.value

    override suspend fun toggleChecklistItem(id: String) {
        checklistItemsFlow.update { list ->
            list.map { if (it.id == id) it.copy(isChecked = !it.isChecked) else it }
        }
    }
}

interface SessionLocalDataSource {
    fun observeSession(): Flow<UserSession>
    fun getSession(): UserSession? = null
}

@Singleton
class MemorySessionLocalDataSource @Inject constructor() : SessionLocalDataSource {
    private val sessionFlow = MutableStateFlow(
        UserSession(
            displayName = "Oturum açılmadı",
            city = "",
            capabilities = emptySet(),
            isGuest = true,
            phone = "",
            bloodType = "",
        ),
    )

    override fun observeSession(): Flow<UserSession> = sessionFlow.asStateFlow()
    override fun getSession(): UserSession? = sessionFlow.value
}
