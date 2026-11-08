package com.quakemind.feature.emergency.safety

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.SafetyRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SafetyViewModel @Inject constructor(
    private val safetyRepository: SafetyRepository,
) : ViewModel() {

    private val confirmation = MutableStateFlow<String?>(null)

    val state: StateFlow<SafetyUiState> = combine(
        confirmation,
        safetyRepository.familyMembers(),
    ) { conf, members ->
        SafetyUiState(
            confirmation = conf,
            familyMembers = members,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), SafetyUiState())

    fun updateSafety(status: String) {
        viewModelScope.launch {
            safetyRepository.updateSafetyStatus(status)
            confirmation.value = status
        }
    }

    fun updateFamilyMemberStatus(memberId: String, status: String) {
        viewModelScope.launch {
            safetyRepository.updateFamilyMemberStatus(memberId, status)
        }
    }
}
