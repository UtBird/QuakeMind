package com.quakemind.feature.map

import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.Earthquake

data class MapUiState(
    val mapPoints: List<MapPoint> = emptyList(),
    val earthquakes: List<Earthquake> = emptyList(),
    val selectedFilter: String = "Tümü",
    val selectedPoint: MapPoint? = null,
    val deviceLocation: GeoPoint? = null,
    val accuracyMetres: Float? = null,
    val isLocating: Boolean = false,
    val isRefreshingPoints: Boolean = false,
    val locationError: String? = null,
    val pointsError: String? = null,
)
