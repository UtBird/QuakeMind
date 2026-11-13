package com.quakemind.feature.safety

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.network.api.UserSafetyService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SafetyStatusUiState(
    val confirmedStatus: String? = null,
    val isSending: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class SafetyStatusViewModel @Inject constructor(
    private val safetyService: UserSafetyService,
) : ViewModel() {
    private val _state = MutableStateFlow(SafetyStatusUiState())
    val state = _state.asStateFlow()

    fun sendStatus(status: String) {
        if (status != "SAFE" && status != "NEED_HELP") return
        if (_state.value.isSending) return
        viewModelScope.launch {
            _state.update { it.copy(isSending = true, confirmedStatus = null, error = null) }
            try {
                safetyService.updateStatus(status, null, null)
                _state.update { it.copy(isSending = false, confirmedStatus = status) }
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isSending = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(
                        isSending = false,
                        error = "Durum bilgisi sunucuya kaydedilemedi. SMS veya paylaşım seçeneklerini kullanabilirsiniz.",
                    )
                }
            }
        }
    }
}
