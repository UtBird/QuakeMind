package com.quakemind.core.data.datasource.local

import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.model.SyncStatus
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

interface IncidentLocalDataSource {
    fun observePendingCount(): Flow<Int>
    suspend fun getPendingBatch(limit: Int): List<IncidentEntity>
    suspend fun enqueue(entity: IncidentEntity): Long
    suspend fun updateSync(localId: String, status: SyncStatus, retryCount: Int, updatedAt: Long)
    suspend fun claimPendingBatch(limit: Int): List<IncidentEntity>
    suspend fun resetStaleUploading(): Int
}

@Singleton
class RoomIncidentLocalDataSource @Inject constructor(
    private val dao: IncidentDao,
) : IncidentLocalDataSource {
    override fun observePendingCount(): Flow<Int> = dao.observePendingCount()
    override suspend fun getPendingBatch(limit: Int): List<IncidentEntity> = dao.getPendingBatch(limit)
    override suspend fun enqueue(entity: IncidentEntity): Long = dao.enqueue(entity)
    override suspend fun updateSync(localId: String, status: SyncStatus, retryCount: Int, updatedAt: Long) =
        dao.updateSync(localId, status, retryCount, updatedAt)
    override suspend fun claimPendingBatch(limit: Int): List<IncidentEntity> = dao.claimPendingBatch(limit)
    override suspend fun resetStaleUploading(): Int = dao.resetStaleUploading()
}
