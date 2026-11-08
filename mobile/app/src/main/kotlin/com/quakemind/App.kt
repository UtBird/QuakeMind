package com.quakemind

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.quakemind.navigation.AppNavHost
import com.quakemind.navigation.MapRoute
import com.quakemind.navigation.HomeRoute
import com.quakemind.navigation.components.SolidPureWhiteBottomNavBar
import com.quakemind.navigation.components.defaultBottomDestinations

@Composable
fun QuakeMindApp(
    navController: NavHostController = rememberNavController(),
) {
    val entry by navController.currentBackStackEntryAsState()
    val destination = entry?.destination
    val bottomItems = androidx.compose.runtime.remember { defaultBottomDestinations() }
    val showBottomBar = bottomItems.any { it.matches(destination) }
    val isFullScreenMap = destination?.hasRoute<MapRoute>() == true
    val systemNavigationInset = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()
    val bottomContentInset = if (showBottomBar && !isFullScreenMap) {
        80.dp + systemNavigationInset
    } else {
        0.dp
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(if (destination?.hasRoute<HomeRoute>() == true) Color(0xFFF5F6F8) else Color.White)
    ) {
        AppNavHost(
            navController = navController,
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = bottomContentInset),
        )

        if (showBottomBar) {
            SolidPureWhiteBottomNavBar(
                items = bottomItems,
                destination = destination,
                onNavigate = { route ->
                    navController.navigate(route) {
                        popUpTo(com.quakemind.navigation.HomeRoute) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                },
                modifier = Modifier.align(Alignment.BottomCenter),
            )
        }
    }
}
