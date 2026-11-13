package com.quakemind.core.data.repository

import com.quakemind.core.model.ChecklistItem
import kotlinx.coroutines.flow.Flow

interface PreparednessRepository {
    fun checklistItems(): Flow<List<ChecklistItem>>
    fun currentChecklistItems(): List<ChecklistItem> = emptyList()
    suspend fun toggleChecklistItem(id: String)
}
