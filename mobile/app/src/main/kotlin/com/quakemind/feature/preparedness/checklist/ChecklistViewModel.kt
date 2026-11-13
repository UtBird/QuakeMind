package com.quakemind.feature.preparedness.checklist

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.PreparednessRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChecklistViewModel @Inject constructor(
    private val preparednessRepository: PreparednessRepository,
) : ViewModel() {

    private val initialItems = preparednessRepository.currentChecklistItems()
    private val initialCompleted = initialItems.count { it.isChecked }
    private val initialProgress = if (initialItems.isNotEmpty()) initialCompleted.toFloat() / initialItems.size else 0f

    val state: StateFlow<ChecklistUiState> = preparednessRepository.checklistItems().map { list ->
        val completed = list.count { it.isChecked }
        val progress = if (list.isNotEmpty()) completed.toFloat() / list.size else 0f
        ChecklistUiState(
            items = list,
            completedCount = completed,
            progress = progress,
        )
    }.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        ChecklistUiState(
            items = initialItems,
            completedCount = initialCompleted,
            progress = initialProgress,
        ),
    )

    fun toggleChecklistItem(id: String) {
        viewModelScope.launch {
            preparednessRepository.toggleChecklistItem(id)
        }
    }
}
