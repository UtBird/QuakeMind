package com.quakemind.feature.emergency.safety

import com.quakemind.core.model.FamilyMember

data class SafetyUiState(
    val confirmation: String? = null,
    val familyMembers: List<FamilyMember> = emptyList(),
)
