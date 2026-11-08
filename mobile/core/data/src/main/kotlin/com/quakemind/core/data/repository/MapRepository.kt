package com.quakemind.core.data.repository

import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.GeoPoint
import kotlinx.coroutines.flow.Flow

interface MapRepository {
    fun mapPoints(): Flow<List<MapPoint>>
    fun currentMapPoints(): List<MapPoint> = emptyList()
    suspend fun refresh(location: GeoPoint) {}
}
