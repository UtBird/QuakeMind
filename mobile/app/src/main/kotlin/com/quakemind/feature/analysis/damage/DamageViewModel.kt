package com.quakemind.feature.analysis.damage

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.AiAnalysisRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DamageViewModel @Inject constructor(
    private val aiAnalysisRepository: AiAnalysisRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(DamageUiState())
    val state: StateFlow<DamageUiState> = _state.asStateFlow()

    fun assessDamage(imageDesc: String = "") {
        viewModelScope.launch {
            _state.update { it.copy(isAnalyzing = true) }
            val assessment = aiAnalysisRepository.assessDamage(imageDesc)
            _state.update { it.copy(isAnalyzing = false, assessment = assessment) }
        }
    }
}
