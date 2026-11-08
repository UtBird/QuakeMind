package com.quakemind.navigation

import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navDeepLink
import androidx.navigation.toRoute
import com.quakemind.feature.alerts.AlertDetailRoute
import com.quakemind.feature.alerts.AlertsRoute
import com.quakemind.feature.analysis.damage.DamageRoute
import com.quakemind.feature.analysis.nlp.NlpRoute
import com.quakemind.feature.analysis.routing.RoutingRoute
import com.quakemind.feature.auth.login.AuthRoute
import com.quakemind.feature.auth.onboarding.OnboardingRoute
import com.quakemind.feature.auth.splash.SplashRoute
import com.quakemind.feature.emergency.safety.SafetyRoute
import com.quakemind.feature.emergency.sos.SosRoute
import com.quakemind.feature.home.HomeRoute
import com.quakemind.feature.map.MapRoute
import com.quakemind.feature.operations.OperationsRoute
import com.quakemind.feature.preparedness.checklist.ChecklistRoute
import com.quakemind.feature.preparedness.risk.RiskRoute
import com.quakemind.feature.profile.ProfileRoute
import com.quakemind.feature.report.ReportRoute

@Composable
fun AppNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = SplashRoute,
        modifier = modifier,
        enterTransition = {
            slideIntoContainer(
                towards = AnimatedContentTransitionScope.SlideDirection.Start,
                animationSpec = tween(durationMillis = 200, easing = FastOutSlowInEasing),
            ) + fadeIn(animationSpec = tween(200))
        },
        exitTransition = {
            slideOutOfContainer(
                towards = AnimatedContentTransitionScope.SlideDirection.Start,
                animationSpec = tween(durationMillis = 200, easing = FastOutSlowInEasing),
            ) + fadeOut(animationSpec = tween(200))
        },
        popEnterTransition = {
            slideIntoContainer(
                towards = AnimatedContentTransitionScope.SlideDirection.End,
                animationSpec = tween(durationMillis = 200, easing = FastOutSlowInEasing),
            ) + fadeIn(animationSpec = tween(200))
        },
        popExitTransition = {
            slideOutOfContainer(
                towards = AnimatedContentTransitionScope.SlideDirection.End,
                animationSpec = tween(durationMillis = 200, easing = FastOutSlowInEasing),
            ) + fadeOut(animationSpec = tween(200))
        },
    ) {
        composable<SplashRoute> {
            SplashRoute(
                onFinished = {
                    navController.navigate(OnboardingRoute) {
                        popUpTo(SplashRoute) { inclusive = true }
                    }
                },
            )
        }

        composable<OnboardingRoute> {
            OnboardingRoute(
                onContinue = { navController.navigate(AuthRoute) },
                onSkip = { navController.navigate(AuthRoute) },
            )
        }

        composable<AuthRoute> {
            AuthRoute(
                onSuccess = {
                    navController.navigate(HomeRoute) { popUpTo(OnboardingRoute) { inclusive = true } }
                },
            )
        }

        composable<HomeRoute> {
            HomeRoute(
                onMap = { navController.navigate(MapRoute()) },
                onReport = { navController.navigate(ReportRoute) },
                onSos = { navController.navigate(SosRoute) },
                onSafety = { navController.navigate(SafetyRoute) },
                onAlerts = { navController.navigate(AlertsRoute) },
                onRouting = { navController.navigate(RoutingRoute) },
                onDamage = { navController.navigate(DamageRoute) },
                onNlp = { navController.navigate(NlpRoute) },
                onRisk = { navController.navigate(RiskRoute) },
                onChecklist = { navController.navigate(ChecklistRoute) },
                onOperations = { navController.navigate(OperationsRoute) },
                onProfile = { navController.navigate(ProfileRoute) },
                onIncident = { navController.navigate(IncidentDetailRoute(it)) },
            )
        }

        composable<MapRoute>(
            deepLinks = listOf(navDeepLink<MapRoute>(basePath = "quakemind://app/map")),
        ) {
            MapRoute(
                onIncident = { navController.navigate(IncidentDetailRoute(it)) },
            )
        }

        composable<ReportRoute> {
            ReportRoute(
                onBack = { navController.popBackStack() },
            )
        }

        composable<AlertsRoute> {
            AlertsRoute(
                onSelectAlert = { navController.navigate(IncidentDetailRoute(it)) },
            )
        }

        composable<SosRoute> {
            SosRoute(onBack = { navController.popBackStack() })
        }

        composable<ProfileRoute> {
            ProfileRoute(
                onOperations = { navController.navigate(OperationsRoute) },
            )
        }

        composable<ChecklistRoute> {
            ChecklistRoute(
                onBack = { navController.popBackStack() },
            )
        }

        composable<NlpRoute> {
            NlpRoute(
                onBack = { navController.popBackStack() },
                onReport = { navController.navigate(ReportRoute) },
            )
        }

        composable<DamageRoute> {
            DamageRoute(
                onBack = { navController.popBackStack() },
                onReport = { navController.navigate(ReportRoute) },
            )
        }

        composable<RoutingRoute> {
            RoutingRoute(
                onBack = { navController.popBackStack() },
            )
        }

        composable<RiskRoute> {
            RiskRoute(onBack = { navController.popBackStack() })
        }

        composable<SafetyRoute> {
            SafetyRoute(
                onBack = { navController.popBackStack() },
            )
        }

        composable<OperationsRoute> {
            OperationsRoute(
                onBack = { navController.popBackStack() },
            )
        }

        composable<IncidentDetailRoute>(
            deepLinks = listOf(navDeepLink<IncidentDetailRoute>(basePath = "quakemind://app/incident")),
        ) { backStack ->
            val route = backStack.toRoute<IncidentDetailRoute>()
            AlertDetailRoute(
                id = route.id,
                onBack = { navController.popBackStack() },
                onSafety = { navController.navigate(SafetyRoute) },
                onMap = { navController.navigate(MapRoute()) },
            )
        }
    }
}
