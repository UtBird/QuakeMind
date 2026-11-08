package com.quakemind.core.data.repository

/**
 * Aggregate repository interface providing a unified contract for components
 * or tests that require complete access across bounded contexts.
 */
interface QuakeMindRepository :
    SessionRepository,
    EarthquakeRepository,
    IncidentRepository,
    AlertRepository,
    MapRepository,
    PreparednessRepository,
    RoutingRepository,
    SafetyRepository,
    AiAnalysisRepository
