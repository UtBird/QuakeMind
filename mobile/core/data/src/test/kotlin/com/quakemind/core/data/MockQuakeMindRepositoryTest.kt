package com.quakemind.core.data

import com.quakemind.core.data.datasource.local.MemoryAlertLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryChecklistLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryEarthquakeLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryMapLocalDataSource
import com.quakemind.core.data.datasource.local.MemorySafetyLocalDataSource
import com.quakemind.core.data.datasource.local.RoomIncidentLocalDataSource
import com.quakemind.core.data.datasource.remote.DefaultAiRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultAlertRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultIncidentRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultRoutingRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultSafetyRemoteDataSource
import com.quakemind.core.data.datasource.remote.EarthquakeRemoteDataSource
import com.quakemind.core.data.repository.DefaultAiAnalysisRepository
import com.quakemind.core.data.repository.DefaultAlertRepository
import com.quakemind.core.data.repository.DefaultEarthquakeRepository
import com.quakemind.core.data.repository.DefaultMapRepository
import com.quakemind.core.data.repository.DefaultPreparednessRepository
import com.quakemind.core.data.repository.DefaultQuakeMindRepository
import com.quakemind.core.data.repository.DefaultRoutingRepository
import com.quakemind.core.data.repository.DefaultSafetyRepository
import com.quakemind.core.data.repository.DefaultSessionRepository
import com.quakemind.core.data.repository.OfflineFirstIncidentRepository
import com.quakemind.core.model.Capability
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.model.Urgency
import com.quakemind.core.network.fake.DevDamageDetectionService
import com.quakemind.core.network.fake.DevIncidentService
import com.quakemind.core.network.fake.DevNlpAnalysisService
import com.quakemind.core.network.fake.DevNotificationService
import com.quakemind.core.network.fake.DevRoutingService
import com.quakemind.core.network.fake.DevUserSafetyService
import com.quakemind.core.network.real.BackendClient
import com.quakemind.core.testing.fake.FakeIncidentDao
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MockQuakeMindRepositoryTest {
    private val dao = FakeIncidentDao()
    private val localDataSource = RoomIncidentLocalDataSource(dao)
    private val remoteDataSource = DefaultIncidentRemoteDataSource(DevIncidentService())
    private val incidentRepository = OfflineFirstIncidentRepository(localDataSource, remoteDataSource)

    // The session repository now reads the same profile state as BackendClient.
    // Mock that authenticated profile source, without Android preferences or network I/O.
    private val backendProfiles = MutableStateFlow<JsonObject?>(null)
    private val backendClient = mockk<BackendClient> {
        every { profiles } returns backendProfiles.asStateFlow()
        every { savedProfile() } answers { backendProfiles.value }
    }
    private val sessionRepo = DefaultSessionRepository(backendClient)

    // Empty remote catalog is a real supported state. Fixtures are installed by each
    // test that needs them; an initial screen must not invent earthquakes.
    private var remoteEvents = emptyList<Earthquake>()
    private val earthquakeRemote = object : EarthquakeRemoteDataSource {
        override suspend fun getNearbyEarthquakes(location: GeoPoint?): List<Earthquake> = remoteEvents
    }
    private val earthquakeLocal = MemoryEarthquakeLocalDataSource()
    private val earthquakeRepo = DefaultEarthquakeRepository(earthquakeLocal, earthquakeRemote)
    private val alertRepo = DefaultAlertRepository(MemoryAlertLocalDataSource(), DefaultAlertRemoteDataSource(DevNotificationService()))
    private val mapRepo = DefaultMapRepository(MemoryMapLocalDataSource())
    private val prepRepo = DefaultPreparednessRepository(MemoryChecklistLocalDataSource())
    private val routeRepo = DefaultRoutingRepository(DefaultRoutingRemoteDataSource(DevRoutingService()))
    private val safetyRepo = DefaultSafetyRepository(MemorySafetyLocalDataSource(), DefaultSafetyRemoteDataSource(DevUserSafetyService()))
    private val aiRepo = DefaultAiAnalysisRepository(DefaultAiRemoteDataSource(DevNlpAnalysisService(), DevDamageDetectionService()))

    private val repository = DefaultQuakeMindRepository(
        sessionRepo = sessionRepo,
        earthquakeRepo = earthquakeRepo,
        incidentRepo = incidentRepository,
        alertRepo = alertRepo,
        mapRepo = mapRepo,
        preparednessRepo = prepRepo,
        routingRepo = routeRepo,
        safetyRepo = safetyRepo,
        aiAnalysisRepo = aiRepo,
    )

    @Test
    fun saveIncident_persistsIdempotentPendingRecord() = runTest {
        // Test coordinates are explicit sample input, never a production default.
        val selectedLocation = GeoPoint(latitude = 40.123, longitude = 29.456)
        val draft = IncidentDraft(
            localId = "QM-1234",
            type = IncidentType.DEBRIS,
            description = "İki kişi enkaz altında",
            location = selectedLocation,
            peopleCount = 2,
            injuredCount = 0,
            urgency = Urgency.HIGH,
            idempotencyKey = "stable-key",
        )

        val trackingCode = repository.saveIncident(draft)

        assertEquals("QM-1234", trackingCode)
        assertEquals(SyncStatus.PENDING, dao.items.single().syncStatus)
        assertEquals("stable-key", dao.items.single().idempotencyKey)
        assertEquals(selectedLocation.latitude, requireNotNull(dao.items.single().latitude), 0.0)
        assertEquals(selectedLocation.longitude, requireNotNull(dao.items.single().longitude), 0.0)
        assertEquals(1, repository.pendingCount().first())
    }

    @Test
    fun saveIncident_withoutLocation_doesNotQueueFabricatedCoordinates() = runTest {
        val draft = IncidentDraft(
            localId = "QM-NO-GPS",
            type = IncidentType.DEBRIS,
            description = "Test ihbarı",
            location = null,
            idempotencyKey = "no-location-key",
        )

        val failure = runCatching { repository.saveIncident(draft) }.exceptionOrNull()

        assertTrue(failure is IllegalArgumentException)
        assertTrue(dao.items.isEmpty())
        assertEquals(0, repository.pendingCount().first())
    }

    @Test
    fun analyzeText_marksAiOutputForHumanReview() = runTest {
        val result = repository.analyzeText("Cadde üzerinde yol tamamen kapalı")

        assertEquals(IncidentType.ROAD_CLOSURE, result.category)
        assertTrue(result.requiresHumanReview)
        assertTrue(result.confidence in 0f..1f)
    }

    @Test
    fun earthquakes_withoutBackendEvents_doesNotInventEarthquakes() = runTest {
        val list = repository.earthquakes().first()
        assertTrue(list.isEmpty())
        assertTrue(repository.currentEarthquakes().isEmpty())
    }

    @Test
    fun earthquakes_cachesExactlyWhatRemoteReturned() = runTest {
        val sample = Earthquake(
            id = "fixture-earthquake-1",
            magnitude = 4.7,
            depthKm = 12.5,
            epicenter = "Test kayıt bölgesi",
            occurredAt = "2026-11-07T10:00:00Z",
            distanceKm = 25.0,
            source = "test-fixture",
            latitude = 40.123,
            longitude = 29.456,
            feltCount = 0,
        )
        remoteEvents = listOf(sample)

        assertEquals(listOf(sample), repository.earthquakes().first())
        assertEquals(listOf(sample), repository.currentEarthquakes())
    }

    @Test
    fun session_usesAuthenticatedBackendProfile() = runTest {
        backendProfiles.value = buildJsonObject {
            put("adSoyad", "Test Kullanıcı")
            put("sehir", "Konya")
            put("rol", "afetzede")
            put("misafir", false)
        }

        val active = repository.session().first()
        assertEquals("Test Kullanıcı", active.displayName)
        assertEquals("Konya", active.city)
        assertFalse(active.isGuest)
        assertTrue(Capability.CREATE_INCIDENT in active.capabilities)
        assertEquals(active, repository.currentSession())
    }

    @Test
    fun session_withoutAuthenticatedProfile_doesNotExposeFakeUser() = runTest {
        val active = repository.session().first()

        assertEquals("Oturum açılmadı", active.displayName)
        assertTrue(active.isGuest)
        assertTrue(active.capabilities.isEmpty())
        assertEquals(active, repository.currentSession())
    }
}
