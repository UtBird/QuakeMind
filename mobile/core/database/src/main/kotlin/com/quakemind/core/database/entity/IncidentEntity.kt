package com.quakemind.core.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.quakemind.core.model.SyncStatus

@Entity(
    tableName = "incident_queue",
    indices = [
        Index(value = ["syncStatus", "createdAt"], name = "index_incident_queue_syncStatus_createdAt"),
        Index(value = ["idempotencyKey"], unique = false, name = "index_incident_queue_idempotencyKey"),
    ],
)
data class IncidentEntity(
    @PrimaryKey val localId: String,
    val serverId: String?,
    val type: String,
    val description: String,
    val latitude: Double?,
    val longitude: Double?,
    val createdAt: Long,
    val updatedAt: Long,
    val syncStatus: SyncStatus,
    val retryCount: Int,
    val version: Long,
    val conflict: Boolean,
    val idempotencyKey: String,
)
