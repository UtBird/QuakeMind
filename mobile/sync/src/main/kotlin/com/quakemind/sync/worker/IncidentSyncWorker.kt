package com.quakemind.sync.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.SyncStatus
import com.quakemind.core.network.api.IncidentService
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.io.IOException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

@HiltWorker
class IncidentSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val incidentDao: IncidentDao,
    private val incidentService: IncidentService,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        // 1. Crash recovery: Reset any records stuck in UPLOADING from previous worker kill
        incidentDao.resetStaleUploading()

        var hasRecoverableError = false
        val batchSize = 50

        while (true) {
            // 2. Atomically claim up to 50 pending/failed items and mark as UPLOADING
            val batch = incidentDao.claimPendingBatch(limit = batchSize)
            if (batch.isEmpty()) break

            for (item in batch) {
                try {
                    val draft = IncidentDraft(
                        localId = item.localId,
                        type = try {
                            IncidentType.valueOf(item.type)
                        } catch (e: Exception) {
                            IncidentType.OTHER
                        },
                        description = item.description,
                        location = run {
                            val lat = item.latitude
                            val lng = item.longitude
                            if (lat != null && lng != null) GeoPoint(lat, lng) else null
                        },
                        idempotencyKey = item.idempotencyKey,
                    )

                    // 3. Call remote service with unchanging idempotencyKey
                    incidentService.create(draft, item.idempotencyKey)

                    // 4. Update to SYNCED
                    incidentDao.updateSync(
                        localId = item.localId,
                        status = SyncStatus.SYNCED,
                        retryCount = item.retryCount,
                        updatedAt = System.currentTimeMillis(),
                    )
                } catch (e: Exception) {
                    val isRecoverable = isRecoverableError(e)
                    val newStatus = if (isRecoverable) SyncStatus.FAILED else SyncStatus.CONFLICT
                    val newRetryCount = item.retryCount + 1

                    incidentDao.updateSync(
                        localId = item.localId,
                        status = newStatus,
                        retryCount = newRetryCount,
                        updatedAt = System.currentTimeMillis(),
                    )

                    if (isRecoverable) {
                        hasRecoverableError = true
                    }
                }
            }
        }

        return if (hasRecoverableError) {
            Result.retry()
        } else {
            Result.success()
        }
    }

    private fun isRecoverableError(e: Exception): Boolean {
        return when (e) {
            is IOException,
            is SocketTimeoutException,
            is UnknownHostException -> true
            else -> false
        }
    }
}
