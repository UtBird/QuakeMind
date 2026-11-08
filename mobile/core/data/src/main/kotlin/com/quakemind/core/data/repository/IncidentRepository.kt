package com.quakemind.core.data.repository

import com.quakemind.core.model.Incident
import com.quakemind.core.model.IncidentDraft
import kotlinx.coroutines.flow.Flow

interface IncidentRepository {
    fun incidents(): Flow<List<Incident>>
    fun pendingCount(): Flow<Int>
    suspend fun saveIncident(draft: IncidentDraft): String
}
