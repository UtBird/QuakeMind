package com.quakemind.feature.home

import androidx.compose.runtime.Immutable
import com.quakemind.core.model.Alert
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.UserSession

@Immutable
data class HomeUiState(
    val session: UserSession? = null,
    val earthquakes: List<Earthquake> = emptyList(),
    val alerts: List<Alert> = emptyList(),
    val pendingCount: Int = 0,
    val online: Boolean = true,
    val deviceLocation: GeoPoint? = null,
    val accuracyMetres: Float? = null,
    val isLocating: Boolean = false,
    val locationError: String? = null,
)
