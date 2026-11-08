package com.quakemind.feature.profile

import com.quakemind.core.model.UserSession

data class ProfileUiState(
    val session: UserSession? = null,
    val highSensSms: Boolean = true,
    val offlineMapOffline: Boolean = true,
    val volunteerActive: Boolean = false,
)
