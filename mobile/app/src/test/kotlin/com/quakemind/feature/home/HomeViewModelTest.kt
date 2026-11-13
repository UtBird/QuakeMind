package com.quakemind.feature.home

import com.quakemind.core.data.repository.AlertRepository
import com.quakemind.core.data.repository.EarthquakeRepository
import com.quakemind.core.data.repository.IncidentRepository
import com.quakemind.core.data.repository.SessionRepository
import com.quakemind.core.model.Alert
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.UserSession
import com.quakemind.core.network.monitor.NetworkMonitor
import com.quakemind.feature.location.DeviceLocationProvider
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private val sessionRepo = mockk<SessionRepository>()
    private val earthquakeRepo = mockk<EarthquakeRepository>()
    private val alertRepo = mockk<AlertRepository>()
    private val incidentRepo = mockk<IncidentRepository>()
    private val networkMonitor = mockk<NetworkMonitor>()
    private val deviceLocationProvider = mockk<DeviceLocationProvider>()

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun homeViewModel_combinesScopedFlowsIntoHomeUiState() = runTest(testDispatcher) {
        val sampleSession = UserSession("Test User", "Istanbul", emptySet(), false)
        val sampleEarthquakes = listOf(
            Earthquake("eq-1", 4.5, 10.0, "Silivri", "12:00", 30.0, "Kandilli"),
        )
        val sampleAlerts = listOf(
            Alert("al-1", "Deprem Uyarisi", "Detay", "Deprem", "12:00"),
        )

        every { sessionRepo.currentSession() } returns sampleSession
        every { earthquakeRepo.currentEarthquakes() } returns sampleEarthquakes
        every { alertRepo.currentAlerts() } returns sampleAlerts

        every { sessionRepo.session() } returns flowOf(sampleSession)
        every { earthquakeRepo.earthquakes() } returns flowOf(sampleEarthquakes)
        every { alertRepo.alerts() } returns flowOf(sampleAlerts)
        every { incidentRepo.pendingCount() } returns flowOf(0)
        every { networkMonitor.isOnline } returns flowOf(true)

        val viewModel = HomeViewModel(
            sessionRepository = sessionRepo,
            earthquakeRepository = earthquakeRepo,
            alertRepository = alertRepo,
            incidentRepository = incidentRepo,
            networkMonitor = networkMonitor,
            deviceLocationProvider = deviceLocationProvider,
        )

        // Verify initial state is populated synchronously (Frame 0 data)
        assertEquals("Test User", viewModel.state.value.session?.displayName)
        assertEquals(1, viewModel.state.value.earthquakes.size)
        assertEquals(1, viewModel.state.value.alerts.size)

        testScheduler.advanceUntilIdle()

        val state = viewModel.state.first { it.session != null }
        assertEquals("Test User", state.session?.displayName)
        assertEquals(1, state.earthquakes.size)
        assertEquals(1, state.alerts.size)
        assertTrue(state.online)
    }
}
