package com.quakemind.feature.report

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.IncidentRepository
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.IncidentDraft
import com.quakemind.core.model.IncidentType
import com.quakemind.core.model.Urgency
import com.quakemind.sync.scheduler.SyncScheduler
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class ReportViewModel @Inject constructor(
    private val incidentRepository: IncidentRepository,
    private val syncScheduler: SyncScheduler,
) : ViewModel() {

    private val _state = MutableStateFlow(ReportUiState())
    val state: StateFlow<ReportUiState> = _state.asStateFlow()

    fun submitIncident(
        description: String,
        type: IncidentType = IncidentType.BUILDING_DAMAGE,
        urgency: Urgency = Urgency.HIGH,
        location: GeoPoint? = null,
        peopleCount: Int = 0,
        injuredCount: Int = 0,
    ) {
        if (description.isBlank()) {
            _state.update { it.copy(submissionError = "Durumu açıklayan bir metin girin.") }
            return
        }
        if (_state.value.isSubmitting || _state.value.lastTrackingCode != null) return
        viewModelScope.launch {
            _state.update { it.copy(isSubmitting = true, submissionError = null) }
            val id = "QM-${UUID.randomUUID().toString().take(8).uppercase()}"
            try {
                val savedId = incidentRepository.saveIncident(
                    IncidentDraft(
                        localId = id,
                        type = type,
                        description = description.trim(),
                        location = location,
                        peopleCount = peopleCount,
                        injuredCount = injuredCount,
                        urgency = urgency,
                        idempotencyKey = UUID.randomUUID().toString(),
                    ),
                )
                _state.update { it.copy(isSubmitting = false, lastTrackingCode = savedId) }
                try {
                    syncScheduler.scheduleIncidentSync()
                } catch (cancel: CancellationException) {
                    throw cancel
                } catch (_: Exception) {
                    _state.update { it.copy(syncWarning = "İhbar cihazda kayıtlı, otomatik gönderim başlatılamadı. Bağlantıyı kontrol edin.") }
                }
            } catch (cancel: CancellationException) {
                throw cancel
            } catch (_: Exception) {
                _state.update { it.copy(isSubmitting = false, submissionError = "İhbar kaydedilemedi. Tekrar deneyin.") }
            }
        }
    }
}
