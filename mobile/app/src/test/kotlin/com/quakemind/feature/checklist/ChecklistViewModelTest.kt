package com.quakemind.feature.checklist

import com.quakemind.core.data.repository.PreparednessRepository
import com.quakemind.core.model.ChecklistItem
import com.quakemind.feature.preparedness.checklist.ChecklistViewModel
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
class ChecklistViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private val preparednessRepo = mockk<PreparednessRepository>(relaxed = true)

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun checklistViewModel_calculatesProgressCorrectly() = runTest(testDispatcher) {
        val items = listOf(
            ChecklistItem("chk-1", "Duduk", "Guvenlik", isChecked = true),
            ChecklistItem("chk-2", "Su", "Gida", isChecked = false),
        )
        every { preparednessRepo.checklistItems() } returns flowOf(items)

        val viewModel = ChecklistViewModel(preparednessRepo)
        testScheduler.advanceUntilIdle()

        val state = viewModel.state.first { it.items.isNotEmpty() }
        assertEquals(2, state.items.size)
        assertEquals(1, state.completedCount)
        assertEquals(0.5f, state.progress)
    }

    @Test
    fun toggleChecklistItem_delegatesToRepository() = runTest(testDispatcher) {
        every { preparednessRepo.checklistItems() } returns flowOf(emptyList())

        val viewModel = ChecklistViewModel(preparednessRepo)
        viewModel.toggleChecklistItem("chk-1")
        testScheduler.advanceUntilIdle()

        coVerify { preparednessRepo.toggleChecklistItem("chk-1") }
    }
}
