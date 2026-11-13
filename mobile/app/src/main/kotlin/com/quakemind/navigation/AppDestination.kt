package com.quakemind.navigation

import kotlinx.serialization.Serializable

@Serializable data object SplashRoute
@Serializable data object OnboardingRoute
@Serializable data object AuthRoute
@Serializable data object HomeRoute
@Serializable data class MapRoute(val lat: Double? = null, val lng: Double? = null)
@Serializable data object ReportRoute
@Serializable data object AlertsRoute
@Serializable data object ProfileRoute
@Serializable data object SosRoute
@Serializable data object NlpRoute
@Serializable data object DamageRoute
@Serializable data object RoutingRoute
@Serializable data object RiskRoute
@Serializable data object SafetyRoute
@Serializable data object ChecklistRoute
@Serializable data object OperationsRoute
@Serializable data class IncidentDetailRoute(val id: String)
