package com.quakemind.navigation.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Backpack
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.PhoneInTalk
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Backpack
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.NotificationsActive
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import com.quakemind.core.designsystem.AfetCrimson
import com.quakemind.core.designsystem.Zinc200
import com.quakemind.core.designsystem.Zinc600
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

private val DockShape = RoundedCornerShape(22.dp)

@Composable
fun SolidPureWhiteBottomNavBar(
    items: List<BottomDestination>,
    destination: NavDestination?,
    onNavigate: (Any) -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth().navigationBarsPadding()
            .padding(horizontal = 12.dp, vertical = 8.dp)
            .shadow(12.dp, DockShape),
        shape = DockShape,
        color = Color.White,
        border = BorderStroke(1.dp, Zinc200),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().height(64.dp).padding(horizontal = 6.dp, vertical = 5.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            items.forEach { item ->
                if (item.isSos) {
                    SosFloatingButton(item = item, onNavigate = onNavigate, modifier = Modifier.weight(1f))
                } else {
                    BottomNavItemView(
                        item = item,
                        selected = item.matches(destination),
                        onNavigate = onNavigate,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun SosFloatingButton(
    item: BottomDestination,
    onNavigate: (Any) -> Unit,
    modifier: Modifier = Modifier,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()

    val buttonScale by animateFloatAsState(
        targetValue = if (isPressed) 0.90f else 1.0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessMedium,
        ),
        label = "sosScaleAnim",
    )

    Box(
        modifier = modifier
            .testTag("bottom_nav_sos")
            .graphicsLayer {
                scaleX = buttonScale
                scaleY = buttonScale
            }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                onClick = { onNavigate(item.route) }
            ),
        contentAlignment = Alignment.Center,
    ) {
        Surface(
            modifier = Modifier.size(width = 50.dp, height = 50.dp),
            shape = RoundedCornerShape(15.dp),
            color = AfetCrimson,
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(AfetCrimson, RoundedCornerShape(15.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Icon(
                        imageVector = Icons.Filled.PhoneInTalk,
                        contentDescription = "SOS",
                        tint = Color.White,
                        modifier = Modifier.size(20.dp),
                    )
                    Spacer(Modifier.height(1.dp))
                    Text(
                        text = "SOS",
                        color = Color.White,
                        fontWeight = FontWeight.Black,
                        fontSize = 10.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun BottomNavItemView(
    item: BottomDestination,
    selected: Boolean,
    onNavigate: (Any) -> Unit,
    modifier: Modifier = Modifier,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()

    val buttonScale by animateFloatAsState(
        targetValue = if (isPressed) 0.92f else 1.0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessMedium,
        ),
        label = "scaleAnim",
    )

    val contentColor by animateColorAsState(
        targetValue = if (selected) AfetCrimson else Zinc600,
        label = "colorAnim",
    )
    val icon = if (selected) item.activeIcon else item.inactiveIcon
    val tabTag = "bottom_nav_" + when (item.label) {
        "Ana Sayfa" -> "home"
        "Harita" -> "map"
        "Uyarılar" -> "alerts"
        "Çanta" -> "checklist"
        else -> item.label.lowercase().replace(" ", "_")
    }

    Box(
        modifier = modifier
            .fillMaxHeight()
            .testTag(tabTag)
            .semantics {
                role = Role.Tab
                this.selected = selected
            }
            .graphicsLayer {
                scaleX = buttonScale
                scaleY = buttonScale
            }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                onClick = { onNavigate(item.route) }
            ),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(top = 1.dp),
        ) {
            Surface(
                shape = RoundedCornerShape(11.dp),
                color = if (selected) AfetCrimson.copy(alpha = 0.10f) else Color.Transparent,
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    modifier = Modifier.size(width = 42.dp, height = 27.dp).padding(vertical = 3.dp),
                    tint = contentColor,
                )
            }
            Spacer(Modifier.height(1.dp))
            Text(
                text = item.label,
                fontSize = 10.sp,
                color = contentColor,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.SemiBold,
                maxLines = 1,
            )
        }
    }
}
