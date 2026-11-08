package com.quakemind.core.network.real

import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Capability
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.NlpAnalysis
import com.quakemind.core.model.RouteOption
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
import com.quakemind.core.network.api.SosService
import com.quakemind.core.network.api.MapService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.max
import kotlin.math.roundToInt

private fun JsonObject.entriesList(name: String): List<JsonObject> =
    (this[name] ?: this["_items"]).array().mapNotNull { it.obj() }

private fun JsonObject.text(name: String, fallback: String = ""): String =
    this[name].string() ?: fallback

fun mapProfile(profile: JsonObject): UserSession {
    val role = profile.text("rol", "afetzede")
    val capabilities = mutableSetOf<String>()
    if (role in setOf("afetzede", "saha", "koordinator", "yonetici")) {
        capabilities += Capability.CREATE_INCIDENT
    }
    if (role in setOf("saha", "koordinator", "yonetici")) {
        capabilities += Capability.VERIFY_INCIDENT
        capabilities += Capability.VIEW_OPERATIONS
        capabilities += Capability.UPDATE_ROAD
    }
    if (role in setOf("koordinator", "yonetici")) capabilities += Capability.ASSIGN_TEAM
    return UserSession(
        displayName = profile.text("adSoyad", "Kullanıcı"),
        city = profile.text("sehir", "Konum belirtilmedi"),
        capabilities = capabilities,
        isGuest = profile["misafir"].bool(),
        phone = "",
        bloodType = "",
        isVolunteer = role != "afetzede",
    )
}

@Singleton
class BackendAuthService @Inject constructor(
    private val client: BackendClient,
) : AuthService {
    override suspend fun createGuestSession(): UserSession =
        mapProfile(client.session("api/oturum/misafir")["kullanici"].obj()
            ?: throw IOException("Misafir oturumu alınamadı."))

    override suspend fun login(email: String, password: String): UserSession {
        val answer = client.session("api/oturum/giris", buildJsonObject {
            put("eposta", email.trim())
            put("sifre", password)
        })
        return mapProfile(answer["kullanici"].obj() ?: throw IOException("Profil yanıtı eksik."))
    }

    override suspend fun register(email: String, fullName: String, password: String): UserSession {
        val answer = client.session("api/oturum/kayit", buildJsonObject {
            put("eposta", email.trim())
            put("adSoyad", fullName.trim())
            put("sifre", password)
        })
        return mapProfile(answer["kullanici"].obj() ?: throw IOException("Profil yanıtı eksik."))
    }

    override suspend fun refreshSession(refreshToken: String): UserSession {
        val answer = client.renew()
        return mapProfile(answer["kullanici"].obj() ?: throw IOException("Profil yanıtı eksik."))
    }

    override suspend fun logout() = client.closeSession()
}

@Singleton
class BackendEarthquakeService @Inject constructor(
    private val client: BackendClient,
) : EarthquakeService {
    override suspend fun nearby(location: GeoPoint?): List<Earthquake> {
        // This catalog is public; the operational /api/katman/depremler is staff-only.
        val data = client.request("GET", "api/risk/all_quakes", params = mapOf("limit" to "100")).obj()
            ?: return emptyList()
        return data.entriesList("quakes").mapIndexedNotNull { index, quake ->
            val lat = quake["latitude"].number() ?: return@mapIndexedNotNull null
            val lon = quake["longitude"].number() ?: return@mapIndexedNotNull null
            val magnitude = quake["magnitude"].number() ?: return@mapIndexedNotNull null
            Earthquake(
                id = quake.text("time") + ":" + index,
                magnitude = magnitude,
                depthKm = quake["depth"].number() ?: 0.0,
                epicenter = quake.text("place", "Konum belirtilmedi"),
                occurredAt = quake.text("time"),
                distanceKm = if (location == null) 0.0 else distanceKm(location, GeoPoint(lat, lon)),
                source = quake.text("source", "Deprem kataloğu"),
                latitude = lat,
                longitude = lon,
                feltCount = 0,
            )
        }
    }

    // The backend does not currently publish a dedicated earthquake SSE event. This
    // is a one-shot initial emission; updates use the shared event stream when added.
    override fun liveEvents(): Flow<Earthquake> = flow {
        nearby(null).forEach { emit(it) }
    }
}

private fun distanceKm(a: GeoPoint, b: GeoPoint): Double {
    val r = 6371.0
    val dLat = Math.toRadians(b.latitude - a.latitude)
    val dLon = Math.toRadians(b.longitude - a.longitude)
    val h = kotlin.math.sin(dLat / 2).let { it * it } +
        kotlin.math.cos(Math.toRadians(a.latitude)) *
        kotlin.math.cos(Math.toRadians(b.latitude)) *
        kotlin.math.sin(dLon / 2).let { it * it }
    return 2 * r * kotlin.math.asin(kotlin.math.sqrt(h.coerceIn(0.0, 1.0)))
}

@Singleton
class BackendIncidentService @Inject constructor(
    private val client: BackendClient,
) : IncidentService {
    override suspend fun create(draft: IncidentDraft, idempotencyKey: String): Incident {
        val location = draft.location ?: throw IllegalArgumentException("İhbar konumu seçilmedi.")
        val needs = when (draft.type) {
            IncidentType.WATER -> "su"
            IncidentType.FOOD -> "gida"
            IncidentType.SHELTER -> "barinma"
            IncidentType.MEDICAL -> "ilac"
            else -> null
        }
        val body = buildJsonObject {
            put("tur", if (needs != null) "ihtiyac" else "metin")
            put("metin", draft.description)
            put("lon", location.longitude)
            put("lat", location.latitude)
            put("konumKaynagi", draft.locationSource)
            if (needs != null) {
                put("ihtiyaclar", kotlinx.serialization.json.buildJsonArray { add(kotlinx.serialization.json.JsonPrimitive(needs)) })
                if (draft.peopleCount > 0) put("kisiSayisi", draft.peopleCount)
            }
        }
        val data = client.request(
            method = "POST",
            path = "api/ihbarlar",
            payload = body,
            idempotencyKey = idempotencyKey,
        ).obj() ?: throw IOException("İhbar sonucu okunamadı.")
        return toIncident(data)
    }

    override suspend fun nearby(location: GeoPoint?): List<Incident> =
        client.request("GET", "api/ihbarlar", params = mapOf("sinir" to "100")).obj()
            ?.entriesList("_items")
            ?.filter { it["lat"].number() != null && it["lon"].number() != null }
            ?.map { toIncident(it) }
            ?.let { results ->
                if (location == null) results else results.sortedBy {
                    distanceKm(location, GeoPoint(it.latitude, it.longitude))
                }
            } ?: emptyList()

    private fun toIncident(data: JsonObject): Incident {
        val type = when (data.text("tur")) {
            "fotograf" -> IncidentType.BUILDING_DAMAGE
            "ihtiyac" -> IncidentType.OTHER
            else -> IncidentType.OTHER
        }
        val score = data["skor"].number()
        val urgency = when {
            score == null -> Urgency.MEDIUM
            score >= 0.85 -> Urgency.CRITICAL
            score >= 0.6 -> Urgency.HIGH
            score >= 0.3 -> Urgency.MEDIUM
            else -> Urgency.LOW
        }
        return Incident(
            id = data.text("id"),
            title = data.text("etiket").ifBlank { data.text("metin").take(80).ifBlank { "İhbar" } },
            type = type,
            locationLabel = data.text("mahalle", "Konum kaydı"),
            urgency = urgency,
            confidence = (data["guven"].number() ?: 0.0).toFloat(),
            status = data.text("durum", "yeni"),
            latitude = data["lat"].number() ?: throw IOException("İhbarın koordinatı eksik."),
            longitude = data["lon"].number() ?: throw IOException("İhbarın koordinatı eksik."),
            timestamp = data["zaman"].string().orEmpty(),
        )
    }
}

@Singleton
class BackendNlpService @Inject constructor(private val client: BackendClient) : NlpAnalysisService {
    override suspend fun analyze(text: String): NlpAnalysis {
        val data = client.request("POST", "api/afetzede/metin-analiz", buildJsonObject {
            put("metin", text)
        }).obj() ?: throw IOException("Metin analizi yanıtı boş.")
        val category = data.text("kategori").lowercase()
        val incidentType = when {
            category.contains("enkaz") || category.contains("gocuk") -> IncidentType.DEBRIS
            category.contains("saglik") || category.contains("yarali") -> IncidentType.INJURED
            category.contains("yangin") -> IncidentType.FIRE
            category.contains("su") -> IncidentType.WATER
            category.contains("gida") -> IncidentType.FOOD
            category.contains("barin") -> IncidentType.SHELTER
            else -> IncidentType.OTHER
        }
        val priority = data["aciliyet"].number()
        val confidence = (data["guven"].number() ?: 0.0).toFloat()
        return NlpAnalysis(
            category = incidentType,
            locationText = data["konumMetin"].string(),
            needs = emptyList(),
            urgency = when {
                priority == null -> Urgency.MEDIUM
                priority >= 4 -> Urgency.CRITICAL
                priority >= 3 -> Urgency.HIGH
                priority >= 2 -> Urgency.MEDIUM
                else -> Urgency.LOW
            },
            confidence = confidence,
            requiresHumanReview = data["ilgisiz"].bool() || confidence < 0.75f,
        )
    }
}

@Singleton
class BackendDamageDetectionService @Inject constructor(
    private val client: BackendClient,
) : DamageDetectionService {
    override suspend fun analyze(uploadId: String, analysisType: String): DamageResult {
        require(uploadId.length > 100) { "Gerçek bir JPEG/PNG görüntüsü seçilmedi." }
        val model = when (analysisType.lowercase()) {
            "catlak" -> "catlak"
            "bina" -> "bina"
            else -> "ikisi"
        }
        val data = client.request("POST", "api/afetzede/fotograf-analiz", buildJsonObject {
            put("imageBase64", uploadId)
            put("model", model)
        }).obj() ?: throw IOException("Görsel analiz yanıtı eksik.")
        val detection = data.entriesList("tespitler")
            .filter { it["hasar"].bool() }
            .maxByOrNull { it["skor"].number() ?: 0.0 }
        return if (detection != null) {
            DamageResult(
                type = detection.text("ad", "Model tespiti"),
                confidence = (detection["guven"].number() ?: 0.0).toFloat(),
                risk = "Ön inceleme: hasar işaretlendi",
                riskScore = ((detection["skor"].number() ?: 0.0) * 100).roundToInt(),
            )
        } else {
            DamageResult(type = "Model hasar işaretlemedi", confidence = 0f, risk = "Tespit yok", riskScore = 0)
        }
    }
}

@Singleton
class BackendRoadStatusService @Inject constructor(private val client: BackendClient) : RoadStatusService {
    override suspend fun roadSegments(bounds: String): List<RoadSegment> {
        val params = if (bounds.isBlank()) emptyMap() else mapOf("kutu" to bounds)
        val data = client.request("GET", "api/katman/kapanmalar", params = params).obj()
            ?: return emptyList()
        return data.entriesList("kayitlar").map { row ->
            RoadSegment(
                id = row.text("id"),
                status = "CLOSED",
                updatedAt = row.text("zaman"),
            )
        }
    }
}

@Singleton
class BackendMapService @Inject constructor(private val client: BackendClient) : MapService {
    override suspend fun nearby(location: GeoPoint, radiusKm: Double): List<MapPoint> {
        require(location.latitude in -90.0..90.0 && location.longitude in -180.0..180.0) {
            "Harita için geçerli konum gerekli."
        }
        val response = client.request("GET", "api/yakin-yerler", params = mapOf(
            "lat" to location.latitude.toString(),
            "lon" to location.longitude.toString(),
            "yaricapKm" to radiusKm.coerceIn(0.1, 25.0).toString(),
            "sinir" to "30",
        )).obj() ?: throw IOException("Yakındaki yerler yanıtı alınamadı.")
        val buckets = response["yerler"].obj()
            ?: throw IOException("Yakındaki yerler yanıtında liste bulunamadı.")
        return buckets.flatMap { (kind, items) ->
            val type = when (kind) {
                "toplanma" -> MapPointType.ASSEMBLY_AREA
                "hastane", "saglik" -> MapPointType.HEALTH_FACILITY
                "eczane" -> MapPointType.PHARMACY
                "itfaiye" -> MapPointType.FIRE_STATION
                "polis" -> MapPointType.POLICE_STATION
                else -> null
            } ?: return@flatMap emptyList()
            items.array().mapNotNull { entry ->
                val record = entry.obj() ?: return@mapNotNull null
                val lat = record["lat"].number() ?: return@mapNotNull null
                val lon = record["lon"].number() ?: return@mapNotNull null
                MapPoint(
                    id = record.text("id"),
                    title = record.text("ad").ifBlank { kind },
                    type = type,
                    latitude = lat,
                    longitude = lon,
                    distanceMeters = record["mesafeM"].int() ?: 0,
                    capacity = null,
                    address = record.text("adres"),
                    statusText = when (type) {
                        MapPointType.ASSEMBLY_AREA -> "AFAD toplanma alanı"
                        MapPointType.HEALTH_FACILITY -> "Sağlık hizmeti"
                        MapPointType.PHARMACY -> "Eczane"
                        MapPointType.FIRE_STATION -> "İtfaiye"
                        MapPointType.POLICE_STATION -> "Polis"
                        else -> "Kayıtlı hizmet noktası"
                    },
                )
            }
        }
    }
}

@Singleton
class BackendRoutingService @Inject constructor(private val client: BackendClient) : RoutingService {
    override suspend fun routes(origin: GeoPoint, destination: GeoPoint, vehicle: String): List<RouteOption> {
        require(origin != destination) { "Rota başlangıcı ve hedefi aynı olamaz." }
        require(vehicle == "WALK") { "Bu rota servisi yalnız yaya ulaşımını destekliyor." }
        val result = client.request("POST", "api/afetzede/rota", buildJsonObject {
            put("baslangicLat", origin.latitude)
            put("baslangicLon", origin.longitude)
            put("hedefLat", destination.latitude)
            put("hedefLon", destination.longitude)
        }).obj() ?: throw IOException("Rota sonucu alınamadı.")
        val distanceMeters = result["uzunlukM"].number()
            ?: throw IOException("Rota uzunluğu sunucu yanıtında yok.")
        val damage = result["hasar"].obj()
        val dangerousMeters = damage?.get("rotadaRiskliM").number()
        val riskShare = if (dangerousMeters == null || distanceMeters <= 0) 0
            else (100.0 * dangerousMeters / distanceMeters).coerceIn(0.0, 100.0).roundToInt()
        val numClosures = damage?.get("rotadaKapanma").int() ?: 0
        return listOf(
            RouteOption(
                id = result.text("algoritma", "afetzede-yaya"),
                label = "Yol ağı üzerinden yaya rotası",
                distanceKm = distanceMeters / 1000.0,
                durationMinutes = result["yuruyusDk"].int() ?: max(1, (distanceMeters / 80).roundToInt()),
                // Percentage of route length with *recorded* hazards, not an earthquake risk probability.
                riskScore = riskShare,
                closedRoads = numClosures,
                partialRoads = 0,
                reliability = "Kaydedilmiş yol hasarı oranı",
                description = result.text("uyari").ifBlank {
                    "Rota bilinen engellerden türetilmiştir; bilinmeyen kapalı yollar bulunabilir."
                },
            ),
        )
    }
}

@Singleton
class BackendRiskAssessmentService @Inject constructor(private val client: BackendClient) : RiskAssessmentService {
    override suspend fun regionalRisk(location: GeoPoint): RiskResult {
        val data = client.request("POST", "api/risk/predict", buildJsonObject {
            put("city", "Türkiye")
            put("manualLatitude", location.latitude)
            put("manualLongitude", location.longitude)
            put("refreshData", false)
        }).obj() ?: throw IOException("Risk verisi okunamadı.")
        val score = data["riskScore"].number() ?: data["risk_score"].number()
            ?: throw IOException("Risk modelinin puan alanı bu sürümle eşleşmiyor.")
        return RiskResult(
            score = score.roundToInt(),
            factors = emptyList(),
            updatedAt = data.text("lastUpdate"),
        )
    }
}

@Singleton
class BackendNotificationService @Inject constructor(private val client: BackendClient) : NotificationService {
    override suspend fun inbox(): List<Alert> {
        val result = client.request("GET", "api/bildirimler/aktif").obj()
            ?: return emptyList()
        return result.entriesList("_items").map { data ->
            val priority = when (data.text("onem")) {
                "kritik" -> AlertSeverity.CRITICAL
                "bilgi" -> AlertSeverity.INFO
                else -> AlertSeverity.WARNING
            }
            Alert(
                id = data.text("id"),
                title = data.text("baslik"),
                detail = data.text("metin"),
                category = "Resmî duyuru",
                occurredAt = data.text("zaman"),
                isRead = false,
                severity = priority,
                location = data.text("konum", "Bölge belirtilmedi"),
            )
        }
    }

    override suspend fun registerPushToken(token: String): Unit =
        throw UnsupportedOperationException("Backend henüz push token kaydı sunmuyor.")
}

@Singleton
class BackendUserSafetyService @Inject constructor(private val client: BackendClient) : UserSafetyService {
    override suspend fun updateStatus(status: String, location: GeoPoint?, note: String?) {
        require(status in setOf("SAFE", "NEED_HELP", "UNKNOWN")) { "Geçersiz güvenlik durumu." }
        client.request("POST", "api/afetzede/guvende-durumu", buildJsonObject {
            put("status", status)
            if (location != null) {
                put("latitude", location.latitude)
                put("longitude", location.longitude)
            }
            if (!note.isNullOrBlank()) put("note", note.take(500))
        })
    }
}

@Singleton
class BackendSosService @Inject constructor(private val client: BackendClient) : SosService {
    override suspend fun send(
        location: GeoPoint,
        priority: String,
        message: String?,
        peopleCount: Int?,
    ): String {
        require(location.latitude in -90.0..90.0 && location.longitude in -180.0..180.0) {
            "Geçerli GPS konumu gerekli."
        }
        require(priority in setOf("kritik", "yuksek", "orta")) { "Geçersiz öncelik." }
        val response = client.request("POST", "api/sos", buildJsonObject {
            put("lon", location.longitude)
            put("lat", location.latitude)
            put("oncelik", priority)
            put("kanal", "android")
            put("konumKaynagi", "gps")
            put("durumSecildi", priority != "kritik")
            if (!message.isNullOrBlank()) put("metin", message.take(500))
            if (peopleCount != null) put("kisiSayisi", peopleCount)
        }).obj() ?: throw IOException("SOS sunucu yanıtı okunamadı.")
        return response["id"].string()?.takeIf { it.isNotBlank() }
            ?: throw IOException("SOS için sunucu kayıt numarası döndürmedi.")
    }
}

@Singleton
class BackendUploadService @Inject constructor(private val client: BackendClient) : UploadService {
    override suspend fun createUpload(fileName: String, contentLength: Long): UploadTicket =
        throw UnsupportedOperationException("Sunucu henüz iki aşamalı dosya yükleme bileti sunmuyor.")

    override suspend fun cancel(uploadId: String): Unit =
        throw UnsupportedOperationException("Sunucu henüz yükleme iptali sunmuyor.")
}
