package com.quakemind.core.data.repository

import com.quakemind.core.model.RouteOption
import com.quakemind.core.model.GeoPoint

interface RoutingRepository {
    suspend fun routeOptions(): List<RouteOption>
    suspend fun routeOptions(origin: GeoPoint, destination: GeoPoint): List<RouteOption> = emptyList()
}
