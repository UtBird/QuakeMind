package com.quakemind.feature.report

import com.quakemind.core.data.repository.IncidentRepository
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.Urgency
import com.quakemind.sync.scheduler.SyncScheduler
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ReportViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private val incidentRepo = mockk<IncidentRepository>(relaxed = true)
    private val syncScheduler = mockk<SyncScheduler>(relaxed = true)

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun submitIncident_savesDraftAndSchedulesSync() = runTest(testDispatcher) {
        coEvery { incidentRepo.saveIncident(any()) } returns "QM-12345678"

        val viewModel = ReportViewModel(incidentRepo, syncScheduler)
        viewModel.submitIncident(
            description = "Enkaz altında 2 kişi",
            type = IncidentType.DEBRIS,
            urgency = Urgency.CRITICAL,
        )

        testScheduler.advanceUntilIdle()

        coVerify { incidentRepo.saveIncident(any()) }
        verify { syncScheduler.scheduleIncidentSync() }
        assertNotNull(viewModel.state.value.lastTrackingCode)
    }
}
