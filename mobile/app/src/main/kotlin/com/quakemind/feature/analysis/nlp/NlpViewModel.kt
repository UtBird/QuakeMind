package com.quakemind.feature.analysis.nlp

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.data.repository.AiAnalysisRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class NlpViewModel @Inject constructor(
    private val aiAnalysisRepository: AiAnalysisRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(NlpUiState())
    val state: StateFlow<NlpUiState> = _state.asStateFlow()

    fun analyze(text: String) {
        if (text.isBlank() || _state.value.isAnalyzing) return
        viewModelScope.launch {
            _state.update { it.copy(isAnalyzing = true, analysis = null, error = null) }
            try {
                val result = aiAnalysisRepository.analyzeText(text.trim())
                _state.update { it.copy(isAnalyzing = false, analysis = result) }
            } catch (cancel: CancellationException) {
                throw cancel
            } catch (_: Exception) {
                _state.update { it.copy(isAnalyzing = false, error = "Metin analizi sunucuya ulaşılamadığı veya model hazır olmadığı için tamamlanamadı.") }
            }
        }
    }
}
