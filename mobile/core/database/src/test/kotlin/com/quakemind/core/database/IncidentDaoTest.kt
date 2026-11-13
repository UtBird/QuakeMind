package com.quakemind.core.database

import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.database.entity.IncidentEntity
import com.quakemind.core.database.migrations.DatabaseMigrations
import com.quakemind.core.model.SyncStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IncidentDaoTest {

    @Test
    fun migration_1_to_2_definition_is_valid() {
        val migration = DatabaseMigrations.MIGRATION_1_2
        assertEquals(1, migration.startVersion)
        assertEquals(2, migration.endVersion)
        assertNotNull(migration)
    }

    @Test
    fun batch_operations_and_status_transitions() = runTest {
        val testDao = object : IncidentDao {
            val records = mutableListOf<IncidentEntity>()
            val countFlow = MutableStateFlow(0)

            override suspend fun enqueue(entity: IncidentEntity): Long {
                records.add(entity)
                countFlow.value = records.count { it.syncStatus != SyncStatus.SYNCED }
                return records.size.toLong()
            }

            override suspend fun enqueueAll(entities: List<IncidentEntity>): List<Long> {
                records.addAll(entities)
                countFlow.value = records.count { it.syncStatus != SyncStatus.SYNCED }
                return entities.map { records.size.toLong() }
            }

            override suspend fun getPendingBatch(limit: Int): List<IncidentEntity> =
                records.filter { it.syncStatus == SyncStatus.PENDING || it.syncStatus == SyncStatus.FAILED }
                    .take(limit)

            override suspend fun pending(): List<IncidentEntity> =
                records.filter { it.syncStatus == SyncStatus.PENDING || it.syncStatus == SyncStatus.FAILED }

            override fun observePendingCount(): Flow<Int> = countFlow

            override suspend fun getPendingCount(): Int =
                records.count { it.syncStatus != SyncStatus.SYNCED }

            override suspend fun updateSync(localId: String, status: SyncStatus, retryCount: Int, updatedAt: Long) {
                val index = records.indexOfFirst { it.localId == localId }
                if (index >= 0) {
                    records[index] = records[index].copy(
                        syncStatus = status,
                        retryCount = retryCount,
                        updatedAt = updatedAt,
                    )
                }
                countFlow.value = records.count { it.syncStatus != SyncStatus.SYNCED }
            }

            override suspend fun updateStatusBatch(localIds: List<String>, status: SyncStatus, updatedAt: Long) {
                val set = localIds.toSet()
                for (i in records.indices) {
                    if (records[i].localId in set) {
                        records[i] = records[i].copy(syncStatus = status, updatedAt = updatedAt)
                    }
                }
                countFlow.value = records.count { it.syncStatus != SyncStatus.SYNCED }
            }

            override suspend fun resetStaleUploading(updatedAt: Long): Int {
                var resetCount = 0
                for (i in records.indices) {
                    if (records[i].syncStatus == SyncStatus.UPLOADING) {
                        records[i] = records[i].copy(syncStatus = SyncStatus.PENDING, updatedAt = updatedAt)
                        resetCount++
                    }
                }
                countFlow.value = records.count { it.syncStatus != SyncStatus.SYNCED }
                return resetCount
            }

            override suspend fun getById(localId: String): IncidentEntity? =
                records.find { it.localId == localId }

            override suspend fun getByIdempotencyKey(key: String): IncidentEntity? =
                records.find { it.idempotencyKey == key }
        }

        val entity = IncidentEntity(
            localId = "local-1",
            serverId = null,
            type = "BUILDING_DAMAGE",
            description = "Hasarlı bina",
            latitude = 41.0,
            longitude = 29.0,
            createdAt = 1000L,
            updatedAt = 1000L,
            syncStatus = SyncStatus.PENDING,
            retryCount = 0,
            version = 1,
            conflict = false,
            idempotencyKey = "key-1",
        )

        testDao.enqueue(entity)
        assertEquals(1, testDao.observePendingCount().first())

        // Test claimPendingBatch default implementation
        val claimed = testDao.claimPendingBatch(limit = 10)
        assertEquals(1, claimed.size)
        assertEquals(SyncStatus.UPLOADING, testDao.getById("local-1")?.syncStatus)

        // Test resetStaleUploading
        val reset = testDao.resetStaleUploading()
        assertEquals(1, reset)
        assertEquals(SyncStatus.PENDING, testDao.getById("local-1")?.syncStatus)
    }
}
