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
import com.quakemind.core.model.Urgency
import com.quakemind.core.network.real.BackendException
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.io.IOException
import kotlinx.coroutines.CancellationException

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

        val batchSize = 50

        while (true) {
            // 2. Atomically claim up to 50 pending/failed items and mark as UPLOADING
            val batch = incidentDao.claimPendingBatch(limit = batchSize)
            if (batch.isEmpty()) break

            for ((index, item) in batch.withIndex()) {
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
                        urgency = item.urgency?.let(Urgency::valueOf) ?: Urgency.HIGH,
                        peopleCount = item.peopleCount ?: 0,
                        injuredCount = item.injuredCount ?: 0,
                        locationSource = item.locationSource ?: "manuel",
                        locationAccuracyMetres = item.locationAccuracyMetres,
                        legacyPayload = item.urgency == null,
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
                } catch (cancel: CancellationException) {
                    throw cancel
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
                        val remaining = batch.drop(index + 1).map { it.localId }
                        if (remaining.isNotEmpty()) {
                            incidentDao.updateStatusBatch(remaining, SyncStatus.PENDING, System.currentTimeMillis())
                        }
                        return Result.retry()
                    }
                }
            }
        }

        return Result.success()
    }

    private fun isRecoverableError(e: Exception): Boolean {
        return when (e) {
            is BackendException -> e.statusCode == 401 || e.statusCode == 408 ||
                e.statusCode == 429 || e.statusCode in 500..599
            is IOException -> true
            else -> false
        }
    }
}
