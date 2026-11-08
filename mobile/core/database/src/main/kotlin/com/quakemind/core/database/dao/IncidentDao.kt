package com.quakemind.core.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.model.SyncStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface IncidentDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun enqueue(entity: IncidentEntity): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun enqueueAll(entities: List<IncidentEntity>): List<Long>

    @Query("SELECT * FROM incident_queue WHERE syncStatus IN ('PENDING', 'FAILED') ORDER BY createdAt ASC LIMIT :limit")
    suspend fun getPendingBatch(limit: Int = 50): List<IncidentEntity>

    @Query("SELECT * FROM incident_queue WHERE syncStatus IN ('PENDING', 'FAILED') ORDER BY createdAt ASC")
    suspend fun pending(): List<IncidentEntity>

    @Query("SELECT COUNT(*) FROM incident_queue WHERE syncStatus != 'SYNCED'")
    fun observePendingCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM incident_queue WHERE syncStatus != 'SYNCED'")
    suspend fun getPendingCount(): Int

    @Query("UPDATE incident_queue SET syncStatus = :status, retryCount = :retryCount, updatedAt = :updatedAt WHERE localId = :localId")
    suspend fun updateSync(localId: String, status: SyncStatus, retryCount: Int, updatedAt: Long)

    @Query("UPDATE incident_queue SET syncStatus = :status, updatedAt = :updatedAt WHERE localId IN (:localIds)")
    suspend fun updateStatusBatch(localIds: List<String>, status: SyncStatus, updatedAt: Long)

    @Query("UPDATE incident_queue SET syncStatus = 'PENDING', updatedAt = :updatedAt WHERE syncStatus = 'UPLOADING'")
    suspend fun resetStaleUploading(updatedAt: Long = System.currentTimeMillis()): Int

    @Query("SELECT * FROM incident_queue WHERE localId = :localId LIMIT 1")
    suspend fun getById(localId: String): IncidentEntity?

    @Query("SELECT * FROM incident_queue WHERE idempotencyKey = :key LIMIT 1")
    suspend fun getByIdempotencyKey(key: String): IncidentEntity?

    @Transaction
    suspend fun claimPendingBatch(limit: Int = 50, now: Long = System.currentTimeMillis()): List<IncidentEntity> {
        val items = getPendingBatch(limit)
        if (items.isNotEmpty()) {
            updateStatusBatch(items.map { it.localId }, SyncStatus.UPLOADING, now)
        }
        return items
    }
}
