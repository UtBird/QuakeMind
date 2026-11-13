package com.quakemind.core.ui.state

import com.quakemind.core.model.Alert
import com.quakemind.core.model.ChecklistItem
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.FamilyMember
import com.quakemind.core.model.Incident
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.UserSession

sealed interface UiState<out T> {
    data object Initial : UiState<Nothing>
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Empty(val message: String) : UiState<Nothing>
    data class Error(val message: String, val canRetry: Boolean = true) : UiState<Nothing>
}

/**
 * Backward compatibility state model for root shell and visual regression tests.
 */
data class AppUiState(
    val session: UserSession? = null,
    val earthquakes: List<Earthquake> = emptyList(),
    val incidents: List<Incident> = emptyList(),
    val alerts: List<Alert> = emptyList(),
    val mapPoints: List<MapPoint> = emptyList(),
    val familyMembers: List<FamilyMember> = emptyList(),
    val checklistItems: List<ChecklistItem> = emptyList(),
    val pendingCount: Int = 0,
    val online: Boolean = true,
)
