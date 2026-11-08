package com.quakemind.core.data.repository

import com.quakemind.core.model.Earthquake
import kotlinx.coroutines.flow.Flow

interface EarthquakeRepository {
    fun earthquakes(): Flow<List<Earthquake>>
    fun currentEarthquakes(): List<Earthquake> = emptyList()
}
