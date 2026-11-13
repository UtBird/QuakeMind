package com.quakemind.navigation.components

import androidx.compose.foundation.layout.heightIn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import com.quakemind.navigation.AlertsRoute
import com.quakemind.navigation.ChecklistRoute
import com.quakemind.navigation.HomeRoute
import com.quakemind.navigation.MapRoute
import com.quakemind.navigation.SosRoute

data class BottomDestination(
    val label: String,
    val activeIcon: ImageVector,
    val inactiveIcon: ImageVector,
    val route: Any,
    val isSos: Boolean = false,
    val matches: (NavDestination?) -> Boolean,
)

private val STATIC_BOTTOM_DESTINATIONS: List<BottomDestination> = listOf(
    BottomDestination(
        label = "Ana Sayfa",
        activeIcon = Icons.Filled.Home,
        inactiveIcon = Icons.Outlined.Home,
        route = HomeRoute,
    ) { it?.hasRoute<HomeRoute>() == true },
    BottomDestination(
        label = "Harita",
        activeIcon = Icons.Filled.Map,
        inactiveIcon = Icons.Outlined.Map,
        route = MapRoute(),
    ) { it?.hasRoute<MapRoute>() == true },
    BottomDestination(
        label = "SOS",
        activeIcon = Icons.Filled.PhoneInTalk,
        inactiveIcon = Icons.Filled.PhoneInTalk,
        route = SosRoute,
        isSos = true,
    ) { it?.hasRoute<SosRoute>() == true },
    BottomDestination(
        label = "Uyarılar",
        activeIcon = Icons.Filled.NotificationsActive,
        inactiveIcon = Icons.Outlined.NotificationsActive,
        route = AlertsRoute,
    ) { it?.hasRoute<AlertsRoute>() == true },
    BottomDestination(
        label = "Çanta",
        activeIcon = Icons.Filled.Backpack,
        inactiveIcon = Icons.Outlined.Backpack,
        route = ChecklistRoute,
    ) { it?.hasRoute<ChecklistRoute>() == true },
)

fun defaultBottomDestinations(): List<BottomDestination> = STATIC_BOTTOM_DESTINATIONS


/** Native tab semantics, ripple feedback and system navigation insets. */
@Composable
fun QuakeBottomBar(
    items: List<BottomDestination>,
    destination: NavDestination?,
    onNavigate: (Any) -> Unit,
    modifier: Modifier = Modifier,
) {
    NavigationBar(
        modifier = modifier,
        containerColor = MaterialTheme.colorScheme.surface,
        tonalElevation = 0.dp,
    ) {
        items.forEach { item ->
            val selected = item.matches(destination)
            val tag = when {
                item.isSos -> "sos"
                item.route is HomeRoute -> "home"
                item.route is MapRoute -> "map"
                item.route is AlertsRoute -> "alerts"
                else -> "checklist"
            }
            NavigationBarItem(
                selected = selected,
                onClick = { if (!selected) onNavigate(item.route) },
                icon = {
                    Icon(if (selected) item.activeIcon else item.inactiveIcon, contentDescription = null)
                },
                label = {
                    Text(item.label, style = MaterialTheme.typography.labelSmall,
                        fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium)
                },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = if (item.isSos) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onPrimaryContainer,
                    selectedTextColor = if (item.isSos) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                    indicatorColor = if (item.isSos) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.primaryContainer,
                    unselectedIconColor = if (item.isSos) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant,
                    unselectedTextColor = if (item.isSos) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant,
                ),
                modifier = Modifier.heightIn(min = 64.dp).testTag("bottom_nav_$tag"),
            )
        }
    }
}
