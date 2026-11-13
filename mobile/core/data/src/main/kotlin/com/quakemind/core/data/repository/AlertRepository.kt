package com.quakemind.core.data.repository

import com.quakemind.core.model.Alert
import kotlinx.coroutines.flow.Flow

interface AlertRepository {
    fun alerts(): Flow<List<Alert>>
    fun currentAlerts(): List<Alert> = emptyList()
    suspend fun markAllAlertsRead()
}
