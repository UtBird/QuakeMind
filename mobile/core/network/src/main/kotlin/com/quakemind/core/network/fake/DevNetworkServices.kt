package com.quakemind.core.network.fake

import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Capability
import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.model.Urgency
import com.quakemind.core.model.UserSession
import com.quakemind.core.network.api.AuthService
import com.quakemind.core.network.api.DamageDetectionService
import com.quakemind.core.network.api.DamageResult
import com.quakemind.core.network.api.EarthquakeService
import com.quakemind.core.network.api.IncidentService
import com.quakemind.core.network.api.NlpAnalysisService
import com.quakemind.core.network.api.NotificationService
import com.quakemind.core.network.api.RiskAssessmentService
import com.quakemind.core.network.api.RiskResult
import com.quakemind.core.network.api.RoadSegment
import com.quakemind.core.network.api.RoadStatusService
import com.quakemind.core.network.api.RoutingService
import com.quakemind.core.network.api.UploadService
import com.quakemind.core.network.api.UploadTicket
import com.quakemind.core.network.api.UserSafetyService
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DevAuthService @Inject constructor() : AuthService {
    override suspend fun createGuestSession(): UserSession = UserSession(
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
    )

    override suspend fun refreshSession(refreshToken: String): UserSession = createGuestSession()
}

@Singleton
class DevEarthquakeService @Inject constructor() : EarthquakeService {
    private val staticEarthquakes = listOf(
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
    )

    override suspend fun nearby(location: GeoPoint?): List<Earthquake> = staticEarthquakes

    override fun liveEvents(): Flow<Earthquake> = flow {
        emit(staticEarthquakes.first())
    }
}

@Singleton
class DevIncidentService @Inject constructor() : IncidentService {
    override suspend fun create(draft: IncidentDraft, idempotencyKey: String): Incident {
        return Incident(
            id = "srv-${UUID.randomUUID().toString().take(8)}",
            title = draft.description.take(30),
            type = draft.type,
            locationLabel = "Kadıköy / Saha İhbarı",
            urgency = draft.urgency,
            confidence = 1.0f,
            status = "Kayıt Alındı",
            syncStatus = SyncStatus.SYNCED,
            latitude = draft.location?.latitude ?: 41.0,
            longitude = draft.location?.longitude ?: 29.0,
            timestamp = "Az önce",
        )
    }

    override suspend fun nearby(location: GeoPoint?): List<Incident> = listOf(
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
    )
}

@Singleton
class DevNlpAnalysisService @Inject constructor() : NlpAnalysisService {
    override suspend fun analyze(text: String): NlpAnalysis {
        delay(300)
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
}

@Singleton
class DevDamageDetectionService @Inject constructor() : DamageDetectionService {
    override suspend fun analyze(uploadId: String, analysisType: String): DamageResult {
        delay(400)
        return DamageResult(
            type = "Ağır Çatlak / Kolon Hasarı",
            confidence = 0.89f,
            risk = "Yüksek Risk",
        )
    }
}

@Singleton
class DevRoadStatusService @Inject constructor() : RoadStatusService {
    override suspend fun roadSegments(bounds: String): List<RoadSegment> = listOf(
        RoadSegment("rs-1", "OPEN", "Bugün 12:00"),
        RoadSegment("rs-2", "CLOSED", "Bugün 13:00"),
    )
}

@Singleton
class DevRoutingService @Inject constructor() : RoutingService {
    override suspend fun routes(origin: GeoPoint, destination: GeoPoint, vehicle: String): List<RouteOption> = listOf(
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
}

@Singleton
class DevRiskAssessmentService @Inject constructor() : RiskAssessmentService {
    override suspend fun regionalRisk(location: GeoPoint): RiskResult = RiskResult(
        score = 42,
        factors = listOf("Zemin sıvılaşma riski: Düşük", "Bina yoğunluğu: Orta"),
        updatedAt = "Bugün 14:00",
    )
}

@Singleton
class DevNotificationService @Inject constructor() : NotificationService {
    override suspend fun inbox(): List<Alert> = listOf(
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
    )

    override suspend fun registerPushToken(token: String) {}
}

@Singleton
class DevUserSafetyService @Inject constructor() : UserSafetyService {
    override suspend fun updateStatus(status: String, location: GeoPoint?, note: String?) {
        delay(200)
    }
}

@Singleton
class DevUploadService @Inject constructor() : UploadService {
    override suspend fun createUpload(fileName: String, contentLength: Long): UploadTicket =
        UploadTicket(id = "ticket-${UUID.randomUUID().toString().take(8)}", uploadUrl = "https://storage.quakemind.local/upload")

    override suspend fun cancel(uploadId: String) {}
}
