package com.quakemind.navigation.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.BluetoothSearching
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.PhoneInTalk
import androidx.compose.material.icons.outlined.Bluetooth
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.ripple
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import com.quakemind.core.designsystem.QuakeMindTheme
import com.quakemind.core.designsystem.Shape12dp
import com.quakemind.core.designsystem.Shape14dp
import com.quakemind.core.designsystem.Shape2dp
import com.quakemind.core.designsystem.isDarkSurface
import com.quakemind.navigation.AlertsRoute
import com.quakemind.navigation.HomeRoute
import com.quakemind.navigation.MapRoute
import com.quakemind.navigation.P2pMeshRoute
import com.quakemind.navigation.SosRoute

data class BottomDestination(
    val label: String,
    val tag: String,
    val activeIcon: ImageVector,
    val inactiveIcon: ImageVector,
    val route: Any,
    val isSos: Boolean = false,
    val isMesh: Boolean = false,
    val matches: (NavDestination?) -> Boolean,
)

private val STATIC_BOTTOM_DESTINATIONS: List<BottomDestination> = listOf(
    BottomDestination(
        label = "Ana Sayfa",
        tag = "home",
        activeIcon = Icons.Filled.Home,
        inactiveIcon = Icons.Outlined.Home,
        route = HomeRoute,
    ) { it?.hasRoute<HomeRoute>() == true },
    BottomDestination(
        label = "Harita",
        tag = "map",
        activeIcon = Icons.Filled.Map,
        inactiveIcon = Icons.Outlined.Map,
        route = MapRoute(),
    ) { it?.hasRoute<MapRoute>() == true },
    BottomDestination(
        label = "SOS",
        tag = "sos",
        activeIcon = Icons.Filled.PhoneInTalk,
        inactiveIcon = Icons.Filled.PhoneInTalk,
        route = SosRoute,
        isSos = true,
    ) { it?.hasRoute<SosRoute>() == true },
    BottomDestination(
        label = "Yakın Ağ",
        tag = "mesh",
        activeIcon = Icons.AutoMirrored.Filled.BluetoothSearching,
        inactiveIcon = Icons.Outlined.Bluetooth,
        route = P2pMeshRoute,
        isMesh = true,
    ) { it?.hasRoute<P2pMeshRoute>() == true },
    BottomDestination(
        label = "Uyarılar",
        tag = "alerts",
        activeIcon = Icons.Filled.Notifications,
        inactiveIcon = Icons.Outlined.Notifications,
        route = AlertsRoute,
    ) { it?.hasRoute<AlertsRoute>() == true },
)

fun defaultBottomDestinations(): List<BottomDestination> = STATIC_BOTTOM_DESTINATIONS

/**
 * Architectural docked bottom navigation bar:
 * - Matte surface with crisp 1dp top hairline (no decorative drop shadow).
 * - Elevated center SOS emergency pill so thumb navigation succeeds under stress.
 * - Dedicated P2P BLE Low Energy ("Yakın Ağ") tab with calm telemetry blue selection.
 * - Full safe-area navigationBars inset handling and >= 56dp touch targets.
 */
@Composable
fun QuakeBottomBar(
    items: List<BottomDestination>,
    destination: NavDestination?,
    onNavigate: (Any) -> Unit,
    modifier: Modifier = Modifier,
    hasUnreadAlerts: Boolean = false,
) {
    val barSurface = if (isDarkSurface()) {
        MaterialTheme.colorScheme.surfaceContainerLow
    } else {
        MaterialTheme.colorScheme.surface
    }

    Surface(
        modifier = modifier.fillMaxWidth(),
        color = barSurface,
        tonalElevation = 0.dp,
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            HorizontalDivider(
                thickness = 1.dp,
                color = MaterialTheme.colorScheme.outlineVariant,
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .windowInsetsPadding(WindowInsets.navigationBars)
                    .padding(horizontal = 8.dp, vertical = 6.dp)
                    .selectableGroup(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(2.dp),
            ) {
                items.forEach { item ->
                    val isSelected = item.matches(destination)
                    if (item.isSos) {
                        SosCenterTab(
                            item = item,
                            isSelected = isSelected,
                            onClick = { if (!isSelected) onNavigate(item.route) },
                            modifier = Modifier.weight(1.05f),
                        )
                    } else {
                        StandardBottomTab(
                            item = item,
                            isSelected = isSelected,
                            showBadgeDot = item.route is AlertsRoute && hasUnreadAlerts && !isSelected,
                            onClick = { if (!isSelected) onNavigate(item.route) },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StandardBottomTab(
    item: BottomDestination,
    isSelected: Boolean,
    showBadgeDot: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val activeAccent = if (item.isMesh) {
        MaterialTheme.colorScheme.tertiary
    } else {
        MaterialTheme.colorScheme.primary
    }
    val activePillBg = if (item.isMesh) {
        MaterialTheme.colorScheme.tertiaryContainer
    } else {
        MaterialTheme.colorScheme.primaryContainer
    }
    val activeIconTint = if (item.isMesh) {
        MaterialTheme.colorScheme.onTertiaryContainer
    } else {
        MaterialTheme.colorScheme.onPrimaryContainer
    }

    val iconTint by animateColorAsState(
        targetValue = if (isSelected) activeIconTint else MaterialTheme.colorScheme.onSurfaceVariant,
        animationSpec = tween(durationMillis = 150),
        label = "tab_icon_${item.tag}",
    )
    val labelColor by animateColorAsState(
        targetValue = if (isSelected) activeAccent else MaterialTheme.colorScheme.onSurfaceVariant,
        animationSpec = tween(durationMillis = 150),
        label = "tab_label_${item.tag}",
    )
    val pillColor by animateColorAsState(
        targetValue = if (isSelected) activePillBg else Color.Transparent,
        animationSpec = tween(durationMillis = 150),
        label = "tab_pill_${item.tag}",
    )

    val interactionSource = remember { MutableInteractionSource() }

    Column(
        modifier = modifier
            .heightIn(min = 58.dp)
            .clip(Shape12dp)
            .clickable(
                interactionSource = interactionSource,
                indication = ripple(bounded = true),
                role = Role.Tab,
                onClick = onClick,
            )
            .semantics { selected = isSelected }
            .padding(vertical = 4.dp)
            .testTag("bottom_nav_${item.tag}"),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(3.dp, Alignment.CenterVertically),
    ) {
        // Subtle top indicator bar for immediate active recognition
        Box(
            modifier = Modifier
                .width(if (isSelected) 20.dp else 0.dp)
                .height(2.5.dp)
                .clip(Shape2dp)
                .background(if (isSelected) activeAccent else Color.Transparent),
        )
        Box(
            modifier = Modifier
                .clip(Shape12dp)
                .background(pillColor)
                .padding(horizontal = 14.dp, vertical = 4.dp),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = if (isSelected) item.activeIcon else item.inactiveIcon,
                contentDescription = null,
                tint = iconTint,
                modifier = Modifier.size(22.dp),
            )
            if (showBadgeDot) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .size(7.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.error),
                )
            }
        }
        Text(
            text = item.label,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium,
            color = labelColor,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun SosCenterTab(
    item: BottomDestination,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val dark = isDarkSurface()
    val containerColor = if (dark) Color(0xFFB82527) else MaterialTheme.colorScheme.error
    val contentColor = Color.White
    val border = if (isSelected) {
        BorderStroke(2.dp, MaterialTheme.colorScheme.onBackground)
    } else if (dark) {
        BorderStroke(1.dp, MaterialTheme.colorScheme.error.copy(alpha = 0.55f))
    } else {
        null
    }

    Box(
        modifier = modifier
            .heightIn(min = 58.dp)
            .padding(horizontal = 4.dp, vertical = 2.dp),
        contentAlignment = Alignment.Center,
    ) {
        Surface(
            onClick = onClick,
            shape = Shape14dp,
            color = containerColor,
            contentColor = contentColor,
            border = border,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 52.dp)
                .semantics { selected = isSelected }
                .testTag("bottom_nav_${item.tag}"),
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(2.dp, Alignment.CenterVertically),
            ) {
                Icon(
                    imageVector = item.activeIcon,
                    contentDescription = null,
                    tint = contentColor,
                    modifier = Modifier.size(20.dp),
                )
                Text(
                    text = item.label,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = contentColor,
                    maxLines = 1,
                    softWrap = false,
                )
            }
        }
    }
}

@Preview(name = "Bottom Bar · Light", showBackground = true)
@Composable
private fun BottomBarLightPreview() {
    QuakeMindTheme(darkTheme = false) {
        QuakeBottomBar(
            items = defaultBottomDestinations(),
            destination = null,
            onNavigate = {},
            hasUnreadAlerts = true,
        )
    }
}

@Preview(name = "Bottom Bar · Dark", showBackground = true)
@Composable
private fun BottomBarDarkPreview() {
    QuakeMindTheme(darkTheme = true) {
        QuakeBottomBar(
            items = defaultBottomDestinations(),
            destination = null,
            onNavigate = {},
            hasUnreadAlerts = true,
        )
    }
}
