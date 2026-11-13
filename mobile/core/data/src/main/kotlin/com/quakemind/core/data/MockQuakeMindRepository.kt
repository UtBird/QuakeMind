package com.quakemind.core.data

import com.quakemind.core.data.repository.QuakeMindRepository
import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Capability
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.FamilySafetyStatus
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.model.Urgency
import com.quakemind.core.model.UserSession
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MockQuakeMindRepository @Inject constructor(
    private val incidentDao: IncidentDao,
) : QuakeMindRepository {

    private val earthquakesFlow = MutableStateFlow(
        listOf(
            Earthquake(
                id = "eq-1",
                magnitude = 4.4,
                depthKm = 7.2,
                epicenter = "Marmara Denizi - Silivri Açıkları",
                occurredAt = "Bugün 13:42",
                distanceKm = 34.0,
                source = "Kandilli Rasathanesi",
                latitude = 40.91,
                longitude = 28.32,
                feltCount = 284,
            ),
            Earthquake(
                id = "eq-2",
                magnitude = 3.8,
                depthKm = 10.4,
                epicenter = "Çanakkale - Ayvacık",
                occurredAt = "Bugün 11:15",
                distanceKm = 210.0,
                source = "AFAD Deprem Dairesi",
                latitude = 39.58,
                longitude = 26.41,
                feltCount = 92,
            ),
            Earthquake(
                id = "eq-3",
                magnitude = 4.1,
                depthKm = 11.0,
                epicenter = "İzmir - Seferihisar Açıkları",
                occurredAt = "Bugün 08:30",
                distanceKm = 320.0,
                source = "Kandilli Rasathanesi",
                latitude = 38.19,
                longitude = 26.83,
                feltCount = 176,
            ),
            Earthquake(
                id = "eq-4",
                magnitude = 3.2,
                depthKm = 8.1,
                epicenter = "Kahramanmaraş - Pazarcık",
                occurredAt = "Dün 23:48",
                distanceKm = 820.0,
                source = "AFAD Deprem Dairesi",
                latitude = 37.49,
                longitude = 37.28,
                feltCount = 54,
            ),
            Earthquake(
                id = "eq-5",
                magnitude = 3.6,
                depthKm = 6.5,
                epicenter = "Malatya - Yeşilyurt",
                occurredAt = "Dün 19:12",
                distanceKm = 790.0,
                source = "AFAD Deprem Dairesi",
                latitude = 38.31,
                longitude = 38.25,
                feltCount = 68,
            ),
        ),
    )

    private val localIncidents = MutableStateFlow(
        listOf(
            Incident(
                id = "i-1",
                title = "Hasarlı Bina & Kısmi Çatlak",
                type = IncidentType.BUILDING_DAMAGE,
                locationLabel = "Kadıköy, Moda Caddesi · 1.4 km",
                urgency = Urgency.HIGH,
                confidence = 0.94f,
                status = "Saha Ekibi Yolda",
                timestamp = "8 dk önce",
                latitude = 40.985,
                longitude = 29.028,
            ),
            Incident(
                id = "i-2",
                title = "Kısmen Kapanan Yan Yol",
                type = IncidentType.ROAD_CLOSURE,
                locationLabel = "D100 Acıbadem Yan Yol · 2.1 km",
                urgency = Urgency.MEDIUM,
                confidence = 0.91f,
                status = "Doğrulandı / Kontrollü",
                timestamp = "15 dk önce",
                latitude = 41.002,
                longitude = 29.045,
            ),
            Incident(
                id = "i-3",
                title = "Acil Temiz Su Dağıtım Noktası",
                type = IncidentType.WATER,
                locationLabel = "Ataşehir, Mimar Sinan Parkı · 4.8 km",
                urgency = Urgency.LOW,
                confidence = 0.88f,
                status = "Aktif Dağıtımda",
                timestamp = "42 dk önce",
                latitude = 40.992,
                longitude = 29.112,
            ),
        ),
    )

    private val alertItems = MutableStateFlow(
        listOf(
            Alert(
                id = "a-1",
                title = "4.4 Marmara Denizi Depremi",
                detail = "Silivri açıklarında 4.4 büyüklüğünde ve 7.2 km derinlikte hafif şiddette bir sarsıntı kaydedilmiştir. Şu ana kadar olumsuz bir ihbar bulunmamaktadır.",
                category = "Deprem",
                occurredAt = "Bugün 13:42",
                isRead = false,
                severity = AlertSeverity.CRITICAL,
                location = "Marmara / İstanbul Geneli",
            ),
            Alert(
                id = "a-2",
                title = "Kuvvetli Rüzgar ve Fırtına Uyarısı",
                detail = "Marmara Bölgesi genelinde hızının 60-80 km/s bulması beklenen fırtına nedeniyle çatı uçması ve ağaç devrilmelerine karşı dikkatli olunmalıdır.",
                category = "Hava Durumu",
                occurredAt = "Bugün 10:15",
                isRead = false,
                severity = AlertSeverity.WARNING,
                location = "İstanbul & Çevre İller",
            ),
            Alert(
                id = "a-3",
                title = "D-100 Köprülü Kavşak Kontrollü Geçiş",
                detail = "Bakım ve güvenlik incelemesi sebebiyle sağ şerit trafiğe kapatılmıştır. Alternatif güzergahları kullanmanız önerilir.",
                category = "Yol Durumu",
                occurredAt = "Bugün 08:30",
                isRead = true,
                severity = AlertSeverity.INFO,
                location = "Kadıköy / Acıbadem",
            ),
            Alert(
                id = "a-4",
                title = "Toplanma Alanları Çadır Kurulumu",
                detail = "AFAD koordinasyonunda Validebağ ve Selami Ali toplanma alanlarında lojistik sahra merkezleri hazır hale getirilmiştir.",
                category = "Duyuru",
                occurredAt = "Dün 16:20",
                isRead = true,
                severity = AlertSeverity.INFO,
                location = "Üsküdar / İstanbul",
            ),
        ),
    )

    private val mapPointsFlow = MutableStateFlow(
        listOf(
            MapPoint(
                id = "mp-1",
                title = "Selami Ali Spor Salonu Açık Alanı",
                type = MapPointType.ASSEMBLY_AREA,
                latitude = 41.025,
                longitude = 29.022,
                distanceMeters = 340,
                capacity = "2.500 Kişi",
                address = "Selami Ali Mah., Gazi Cad. No:14, Üsküdar",
                statusText = "Açık ve Güvenli",
            ),
            MapPoint(
                id = "mp-2",
                title = "Validebağ Korusu Ana Toplanma Sahası",
                type = MapPointType.ASSEMBLY_AREA,
                latitude = 41.012,
                longitude = 29.041,
                distanceMeters = 820,
                capacity = "15.000 Kişi",
                address = "Altunizade, Koşuyolu Cad., Üsküdar",
                statusText = "Lojistik Çadırlar Kurulu",
            ),
            MapPoint(
                id = "mp-3",
                title = "Haydarpaşa Numune Sahra Hastanesi",
                type = MapPointType.SAHRA_HOSPITAL,
                latitude = 41.006,
                longitude = 29.025,
                distanceMeters = 1450,
                capacity = "120 Yatak / Acil Servis",
                address = "Tıbbiye Cad. No:23, Kadıköy",
                statusText = "7/24 Triyaj & İlk Yardım Aktif",
            ),
            MapPoint(
                id = "mp-4",
                title = "Kadıköy Rıhtım Geçici Barınma Çadırları",
                type = MapPointType.SHELTER_TENT,
                latitude = 40.993,
                longitude = 29.022,
                distanceMeters = 2100,
                capacity = "650 Çadır / Isıtmalı",
                address = "Rıhtım Meydanı, Kadıköy",
                statusText = "Sıcak Çorba ve Çadır Dağıtımı",
            ),
            MapPoint(
                id = "mp-5",
                title = "Acıbadem D100 Yan Yol Kapanması",
                type = MapPointType.CLOSED_ROAD,
                latitude = 41.004,
                longitude = 29.048,
                distanceMeters = 1800,
                capacity = null,
                address = "Acıbadem Köprülü Kavşağı",
                statusText = "Kısmi Heyelan Sebebiyle Kapalı",
            ),
        ),
    )

    private val familyMembersFlow = MutableStateFlow(
        listOf(
            FamilyMember(
                id = "fm-1",
                name = "Ayşe Kaya",
                relation = "Anne",
                status = FamilySafetyStatus.SAFE,
                lastSeenTime = "4 dk önce",
                locationLabel = "Kadıköy, Caferağa (Ev)",
                batteryPercent = 88,
            ),
            FamilyMember(
                id = "fm-2",
                name = "Mehmet Kaya",
                relation = "Baba",
                status = FamilySafetyStatus.SAFE,
                lastSeenTime = "12 dk önce",
                locationLabel = "Üsküdar, Altunizade (İş Yeri)",
                batteryPercent = 94,
            ),
            FamilyMember(
                id = "fm-3",
                name = "Zeynep Kaya",
                relation = "Kız Kardeş",
                status = FamilySafetyStatus.UNKNOWN,
                lastSeenTime = "28 dk önce",
                locationLabel = "Beşiktaş, Yıldız Kampüsü",
                batteryPercent = 39,
            ),
            FamilyMember(
                id = "fm-4",
                name = "Emre Kaya",
                relation = "Ağabey",
                status = FamilySafetyStatus.SAFE,
                lastSeenTime = "1 sa önce",
                locationLabel = "Ataşehir, Batı Ataşehir",
                batteryPercent = 76,
            ),
        ),
    )

    private val checklistItemsFlow = MutableStateFlow(
        listOf(
            ChecklistItem("chk-1", "Düdük ve Yüksek Sesli Alarm", "Kişisel Güvenlik", isChecked = true, isCrucial = true),
            ChecklistItem("chk-2", "Kişi Başı En Az 2 Litre Şişe Su", "Gıda & Su", isChecked = true, isCrucial = true),
            ChecklistItem("chk-3", "İlk Yardım Çantası (Sargı bezi, dezenfektan)", "Sağlık", isChecked = true, isCrucial = true),
            ChecklistItem("chk-4", "LED El Feneri ve Dolu Powerbank", "Enerji & Işık", isChecked = true, isCrucial = true),
            ChecklistItem("chk-5", "Pilli Acil Durum Radyosu & Yedek Pil", "Haberleşme", isChecked = false, isCrucial = true),
            ChecklistItem("chk-6", "Yüksek Kalorili Dayanıklı Konserve/Bisküvi", "Gıda & Su", isChecked = false, isCrucial = false),
            ChecklistItem("chk-7", "Önemli Evrak Fotokopileri ve Nakit Para", "Evrak & Finans", isChecked = true, isCrucial = false),
            ChecklistItem("chk-8", "N95 Toz Maskesi ve Koruyucu İş Eldiveni", "Kişisel Güvenlik", isChecked = false, isCrucial = true),
            ChecklistItem("chk-9", "Termal Battaniye ve Yağmurluk", "Barınma", isChecked = true, isCrucial = false),
            ChecklistItem("chk-10", "Sürekli Kullanılan Reçeteli İlaçlar", "Sağlık", isChecked = true, isCrucial = true),
        ),
    )

    override fun session(): Flow<UserSession> = MutableStateFlow(
        UserSession(
            displayName = "Ahmet Yılmaz",
            city = "İstanbul / Üsküdar",
            capabilities = setOf(
                Capability.CREATE_INCIDENT,
                Capability.VERIFY_INCIDENT,
                Capability.VIEW_OPERATIONS,
            ),
            isGuest = false,
            phone = "+90 (532) 789 12 34",
            bloodType = "0 Rh+",
            isVolunteer = true,
        ),
    )

    override fun earthquakes(): Flow<List<Earthquake>> = earthquakesFlow

    override fun incidents(): Flow<List<Incident>> = combine(
        localIncidents,
        incidentDao.observePendingCount(),
    ) { remote, pending ->
        if (pending == 0) remote else listOf(
            Incident(
                id = "local-pending",
                title = "Gönderim Bekleyen Yerel İhbar",
                type = IncidentType.OTHER,
                locationLabel = "Yerel Cihaz Hafızası",
                urgency = Urgency.HIGH,
                confidence = 1.0f,
                status = "Kuyrukta Bekliyor",
                syncStatus = SyncStatus.PENDING,
                timestamp = "Az önce",
            ),
        ) + remote
    }

    override fun alerts(): Flow<List<Alert>> = alertItems
    override fun pendingCount(): Flow<Int> = incidentDao.observePendingCount()
    override fun mapPoints(): Flow<List<MapPoint>> = mapPointsFlow
    override fun familyMembers(): Flow<List<FamilyMember>> = familyMembersFlow
    override fun checklistItems(): Flow<List<ChecklistItem>> = checklistItemsFlow

    override suspend fun saveIncident(draft: IncidentDraft): String {
        val now = System.currentTimeMillis()
        incidentDao.enqueue(
            IncidentEntity(
                localId = draft.localId,
                serverId = null,
                type = draft.type.name,
                description = draft.description,
                latitude = draft.location?.latitude ?: 41.0082,
                longitude = draft.location?.longitude ?: 28.9784,
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

    override suspend fun analyzeText(text: String): NlpAnalysis {
        delay(400)
        val textLower = text.lowercase()
        val category = when {
            "yol" in textLower || "köprü" in textLower -> IncidentType.ROAD_CLOSURE
            "yaralı" in textLower || "mahsur" in textLower || "enkaz" in textLower -> IncidentType.INJURED
            "yangın" in textLower || "duman" in textLower || "gaz" in textLower -> IncidentType.FIRE
            "su" in textLower || "içecek" in textLower -> IncidentType.WATER
            "çadır" in textLower || "barınak" in textLower -> IncidentType.SHELTER
            else -> IncidentType.BUILDING_DAMAGE
        }
        val urgency = if ("acil" in textLower || "enkaz" in textLower || "yangın" in textLower) Urgency.CRITICAL else Urgency.HIGH
        return NlpAnalysis(
            category = category,
            locationText = "Üsküdar / Kadıköy Bölgesi",
            needs = listOf("Arama-Kurtarma", "İlk Yardım Ekibi", "Saha Tahliyesi"),
            urgency = urgency,
            confidence = 0.92f,
            requiresHumanReview = true,
        )
    }

    override suspend fun assessDamage(imageDesc: String): DamageAssessment {
        delay(650)
        return DamageAssessment(
            damageGrade = "Orta / Ağır Hasar Riski",
            confidence = 0.89f,
            riskScore = 78,
            recommendation = "Taşıyıcı kolon ve kirişlerde kılcal ve diagonal çatlaklar tespit edildi. Binaya giriş yapılmamalı, AFAD/Belediye mühendisleri tarafından incelenmelidir.",
            crackDetected = true,
            structuralIssue = true,
        )
    }

    override suspend fun routeOptions(): List<RouteOption> = listOf(
        RouteOption(
            id = "safe-primary",
            label = "En Güvenli Tahliye Rotası (Önerilen)",
            distanceKm = 4.2,
            durationMinutes = 14,
            riskScore = 12,
            closedRoads = 0,
            partialRoads = 0,
            reliability = "%98 Yüksek Güvenilirlik",
            description = "Geniş ana caddeler ve toplanma koridorları üzerinden risksiz güzergah.",
        ),
        RouteOption(
            id = "safe-alternative",
            label = "Alternatif Sahil Güzergahı",
            distanceKm = 5.8,
            durationMinutes = 19,
            riskScore = 28,
            closedRoads = 1,
            partialRoads = 1,
            reliability = "%84 Orta Güvenilirlik",
            description = "Sahil yolu üzerinden açık alan rotası. Kısmi trafik yoğunluğu mevcut.",
        ),
    )

    override suspend fun updateSafetyStatus(status: String) {
        delay(250)
    }

    override suspend fun markAllAlertsRead() {
        alertItems.update { list -> list.map { it.copy(isRead = true) } }
    }

    override suspend fun toggleChecklistItem(id: String) {
        checklistItemsFlow.update { list ->
            list.map { if (it.id == id) it.copy(isChecked = !it.isChecked) else it }
        }
    }

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
}
