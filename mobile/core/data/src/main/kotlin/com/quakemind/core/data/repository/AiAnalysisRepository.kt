package com.quakemind.core.data.repository

import com.quakemind.core.model.DamageAssessment
import com.quakemind.core.model.NlpAnalysis

interface AiAnalysisRepository {
    suspend fun analyzeText(text: String): NlpAnalysis
    suspend fun assessDamage(imageDesc: String = ""): DamageAssessment
}
