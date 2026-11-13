package com.quakemind

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.quakemind.navigation.AppNavHost
import com.quakemind.navigation.MapRoute
import com.quakemind.navigation.components.QuakeBottomBar
import com.quakemind.navigation.components.defaultBottomDestinations

@Composable
fun QuakeMindApp(
    onboardingCompleted: Boolean,
    onOnboardingCompleted: () -> Unit,
    darkTheme: Boolean,
    onDarkThemeChange: (Boolean) -> Unit,
    navController: NavHostController = rememberNavController(),
) {
    val entry by navController.currentBackStackEntryAsState()
    val destination = entry?.destination
    val bottomItems = remember { defaultBottomDestinations() }
    val showBottomBar = bottomItems.any { it.matches(destination) }
    val fullScreenMap = destination?.hasRoute<MapRoute>() == true
    val systemBottom = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        bottomBar = {
            if (showBottomBar) QuakeBottomBar(bottomItems, destination, onNavigate = { route ->
                navController.navigate(route) {
                    popUpTo(com.quakemind.navigation.HomeRoute) { saveState = true }
                    launchSingleTop = true
                    restoreState = true
                }
            })
        },
    ) { padding ->
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
            AppNavHost(
                navController = navController,
                onboardingCompleted = onboardingCompleted,
                onOnboardingCompleted = onOnboardingCompleted,
                darkTheme = darkTheme,
                onDarkThemeChange = onDarkThemeChange,
                modifier = Modifier
                    .then(if (fullScreenMap) Modifier else Modifier.widthIn(max = 840.dp))
                    .fillMaxSize()
                    .padding(bottom = if (fullScreenMap) 0.dp else if (showBottomBar) padding.calculateBottomPadding() else systemBottom)
                    .imePadding(),
            )
        }
    }
}
