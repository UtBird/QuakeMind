package com.quakemind.feature.alerts

import com.quakemind.core.data.repository.AlertRepository
import com.quakemind.core.model.Alert
import io.mockk.coVerify
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
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AlertsViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private val alertRepo = mockk<AlertRepository>(relaxed = true)

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun alertsViewModel_emitsAlerts() = runTest(testDispatcher) {
        val alerts = listOf(
            Alert("al-1", "Deprem Uyarisi", "Detay", "Deprem", "13:00"),
        )
        every { alertRepo.alerts() } returns flowOf(alerts)

        val viewModel = AlertsViewModel(alertRepo)
        testScheduler.advanceUntilIdle()

        val state = viewModel.state.first { it.alerts.isNotEmpty() }
        assertEquals(1, state.alerts.size)
    }

    @Test
    fun markAllRead_callsRepository() = runTest(testDispatcher) {
        every { alertRepo.alerts() } returns flowOf(emptyList())

        val viewModel = AlertsViewModel(alertRepo)
        viewModel.markAllRead()
        testScheduler.advanceUntilIdle()

        coVerify { alertRepo.markAllAlertsRead() }
    }
}
