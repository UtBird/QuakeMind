package com.quakemind.core.testing.fixtures

import com.quakemind.core.model.Alert
import com.quakemind.core.model.AlertSeverity
import com.quakemind.core.model.Capability
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.FamilySafetyStatus
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.model.Urgency
import com.quakemind.core.model.UserSession

object TestFixtures {

    val SampleUserSession = UserSession(
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

    val SampleEarthquakes = listOf(
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
    )

    val SampleIncidents = listOf(
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
    )

    val SampleAlerts = listOf(
        Alert(
            id = "a-1",
            title = "4.4 Marmara Denizi Depremi",
            detail = "Silivri açıklarında 4.4 büyüklüğünde sarsıntı kaydedilmiştir.",
            category = "Deprem",
            occurredAt = "Bugün 13:42",
            isRead = false,
            severity = AlertSeverity.CRITICAL,
            location = "Marmara / İstanbul Geneli",
        ),
    )

    val SampleMapPoints = listOf(
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
    )

    val SampleFamilyMembers = listOf(
        FamilyMember(
            id = "fm-1",
            name = "Ayşe Kaya",
            relation = "Anne",
            status = FamilySafetyStatus.SAFE,
            lastSeenTime = "4 dk önce",
            locationLabel = "Kadıköy, Caferağa (Ev)",
            batteryPercent = 88,
        ),
    )

    val SampleChecklistItems = listOf(
        ChecklistItem("chk-1", "Düdük ve Yüksek Sesli Alarm", "Kişisel Güvenlik", isChecked = true, isCrucial = true),
        ChecklistItem("chk-2", "Kişi Başı En Az 2 Litre Şişe Su", "Gıda & Su", isChecked = true, isCrucial = true),
    )

    val SampleRouteOptions = listOf(
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
    )
}
