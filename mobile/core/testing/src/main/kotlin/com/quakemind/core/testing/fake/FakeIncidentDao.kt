package com.quakemind.core.testing.fake

import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.model.SyncStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeIncidentDao : IncidentDao {
    val items = mutableListOf<IncidentEntity>()
    private val pending = MutableStateFlow(0)

    override suspend fun enqueue(entity: IncidentEntity): Long {
        if (items.none { it.idempotencyKey == entity.idempotencyKey }) {
            items += entity
        }
        updateCount()
        return items.size.toLong()
    }

    override suspend fun enqueueAll(entities: List<IncidentEntity>): List<Long> {
        val results = mutableListOf<Long>()
        for (entity in entities) {
            results.add(enqueue(entity))
        }
        return results
    }

    override suspend fun getPendingBatch(limit: Int): List<IncidentEntity> =
        items.filter { it.syncStatus == SyncStatus.PENDING || it.syncStatus == SyncStatus.FAILED }
            .sortedBy { it.createdAt }
            .take(limit)

    override suspend fun pending(): List<IncidentEntity> =
        items.filter { it.syncStatus == SyncStatus.PENDING || it.syncStatus == SyncStatus.FAILED }
            .sortedBy { it.createdAt }

    override fun observePendingCount() = pending.asStateFlow()

    override suspend fun getPendingCount(): Int =
        items.count { it.syncStatus != SyncStatus.SYNCED }

    override suspend fun updateSync(localId: String, status: SyncStatus, retryCount: Int, updatedAt: Long) {
        val index = items.indexOfFirst { it.localId == localId }
        if (index >= 0) {
            items[index] = items[index].copy(
                syncStatus = status,
                retryCount = retryCount,
                updatedAt = updatedAt,
            )
        }
        updateCount()
    }

    override suspend fun updateStatusBatch(localIds: List<String>, status: SyncStatus, updatedAt: Long) {
        val set = localIds.toSet()
        for (i in items.indices) {
            if (items[i].localId in set) {
                items[i] = items[i].copy(syncStatus = status, updatedAt = updatedAt)
            }
        }
        updateCount()
    }

    override suspend fun resetStaleUploading(updatedAt: Long): Int {
        var count = 0
        for (i in items.indices) {
            if (items[i].syncStatus == SyncStatus.UPLOADING) {
                items[i] = items[i].copy(syncStatus = SyncStatus.PENDING, updatedAt = updatedAt)
                count++
            }
        }
        updateCount()
        return count
    }

    override suspend fun getById(localId: String): IncidentEntity? =
        items.find { it.localId == localId }

    override suspend fun getByIdempotencyKey(key: String): IncidentEntity? =
        items.find { it.idempotencyKey == key }

    private fun updateCount() {
        pending.value = items.count { it.syncStatus != SyncStatus.SYNCED }
    }
}
