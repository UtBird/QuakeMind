package com.quakemind.feature.map

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.FilterList
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material.icons.outlined.Remove
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.ui.draw.clip
import com.quakemind.core.designsystem.AfetCrimson
import com.quakemind.core.designsystem.AfetCrimsonMuted
import com.quakemind.core.designsystem.BorderZinc200
import com.quakemind.core.designsystem.Zinc100
import com.quakemind.core.designsystem.Zinc400
import com.quakemind.core.designsystem.Zinc500
import com.quakemind.core.designsystem.Zinc600
import com.quakemind.core.designsystem.Zinc700
import com.quakemind.core.designsystem.Zinc800
import com.quakemind.core.designsystem.Zinc900
import com.quakemind.core.designsystem.Zinc950
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import com.quakemind.core.ui.state.AppUiState
import com.quakemind.feature.location.distanceMetres
import de.afarber.openmapview.CameraPosition
import de.afarber.openmapview.CameraUpdateFactory
import de.afarber.openmapview.LatLng
import de.afarber.openmapview.compose.rememberCameraPositionState
import java.util.Locale

private val mapFilters = listOf("Tümü", "Depremler", "Yakındakiler", "Toplanma", "Sağlık", "Eczane", "İtfaiye", "Polis")
private const val nearbyRadiusMeters = 5_000f
private val MapBackground = Color(0xFFF4F6F8)
private val TurkishLocale = Locale.forLanguageTag("tr-TR")
private val DefaultMapCenter = LatLng(40.65, 35.83)

@Composable
fun MapScreen(state: AppUiState, onIncident: (String) -> Unit) {
    MapScreen(
        state = MapUiState(
            mapPoints = state.mapPoints,
            earthquakes = state.earthquakes,
        ),
        onIncident = onIncident,
    )
}

@Composable
fun MapScreen(
    state: MapUiState,
    onIncident: (String) -> Unit,
    onRequestLocation: (() -> Unit)? = null,
) {
    val context = LocalContext.current
    val systemTopInset = WindowInsets.statusBars.asPaddingValues().calculateTopPadding()
    val systemBottomInset = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()
    val navigationClearance = systemBottomInset + 82.dp
    val listPanelMaxHeight = (LocalConfiguration.current.screenHeightDp.dp * 0.42f).coerceAtMost(350.dp)

    var selectedFilter by rememberSaveable { mutableStateOf("Tümü") }
    var searchQuery by rememberSaveable { mutableStateOf("") }
    var selectedPointId by rememberSaveable { mutableStateOf<String?>(null) }
    var selectedEarthquakeId by rememberSaveable { mutableStateOf<String?>(null) }
    var showFilters by rememberSaveable { mutableStateOf(true) }
    var showPointList by rememberSaveable { mutableStateOf(false) }
    var hasAutoCenteredOnLocation by rememberSaveable { mutableStateOf(false) }

    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition(DefaultMapCenter, 6.5f)
    }

    val normalizedQuery = searchQuery.trim()
    val filteredEarthquakes = remember(state.earthquakes, selectedFilter, normalizedQuery) {
        if (selectedFilter !in setOf("Tümü", "Depremler")) {
            emptyList()
        } else {
            state.earthquakes.filter { earthquake ->
                normalizedQuery.isBlank() ||
                    earthquake.epicenter.contains(normalizedQuery, ignoreCase = true) ||
                    earthquake.source.contains(normalizedQuery, ignoreCase = true) ||
                    magnitudeLabel(earthquake.magnitude).contains(normalizedQuery, ignoreCase = true)
            }
        }
    }
    val validPoints = remember(state.mapPoints) { state.mapPoints.filter(::isValidCoordinate) }
    val filteredPoints = remember(validPoints, state.deviceLocation, selectedFilter, normalizedQuery) {
        validPoints.filter { point ->
            val categoryMatches = when (selectedFilter) {
                "Depremler" -> false
                "Toplanma" -> point.type == MapPointType.ASSEMBLY_AREA
                "Sağlık" -> point.type == MapPointType.SAHRA_HOSPITAL || point.type == MapPointType.HEALTH_FACILITY
                "Eczane" -> point.type == MapPointType.PHARMACY
                "İtfaiye" -> point.type == MapPointType.FIRE_STATION
                "Polis" -> point.type == MapPointType.POLICE_STATION
                "Yakındakiler" -> state.deviceLocation?.let { distanceMetres(it, point) <= nearbyRadiusMeters } ?: false
                else -> true
            }
            categoryMatches && (normalizedQuery.isBlank() ||
                point.title.contains(normalizedQuery, ignoreCase = true) ||
                point.address.contains(normalizedQuery, ignoreCase = true) ||
                pointTypeLabel(point.type).contains(normalizedQuery, ignoreCase = true))
        }.let { points ->
            state.deviceLocation?.let { location -> points.sortedBy { distanceMetres(location, it) } }
                ?: points.sortedBy(MapPoint::title)
        }
    }
    val selectedPoint = remember(filteredPoints, selectedPointId) {
        filteredPoints.firstOrNull { it.id == selectedPointId }
    }
    val selectedEarthquake = remember(filteredEarthquakes, selectedEarthquakeId) {
        filteredEarthquakes.firstOrNull { it.id == selectedEarthquakeId }
    }
    val hasSelection = selectedPoint != null || selectedEarthquake != null
    val errorMessage = state.locationError ?: state.pointsError
    val topMapInset = systemTopInset + if (showFilters) 126.dp else 92.dp
    val bottomMapInset = navigationClearance + when {
        showPointList -> listPanelMaxHeight + 30.dp
        hasSelection -> 190.dp
        else -> 20.dp
    }

    LaunchedEffect(state.deviceLocation) {
        val location = state.deviceLocation ?: return@LaunchedEffect
        if (!hasAutoCenteredOnLocation) {
            hasAutoCenteredOnLocation = true
            cameraPositionState.animate(
                CameraUpdateFactory.newLatLngZoom(LatLng(location.latitude, location.longitude), 12f),
                durationMs = 650,
            )
        }
    }

    fun focusOn(latitude: Double, longitude: Double, zoom: Float = 13f) {
        cameraPositionState.position = CameraPosition(LatLng(latitude, longitude), zoom)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MapBackground)
            .testTag("osm_map_screen"),
    ) {
        OsmMapPanel(
            earthquakes = filteredEarthquakes,
            mapPoints = filteredPoints,
            location = state.deviceLocation,
            cameraPositionState = cameraPositionState,
            contentPadding = PaddingValues(top = topMapInset, bottom = bottomMapInset),
            modifier = Modifier.fillMaxSize().testTag("osm_map"),
            onPointSelected = { point ->
                selectedPointId = point.id
                selectedEarthquakeId = null
                showPointList = false
                focusOn(point.latitude, point.longitude)
            },
            onEarthquakeSelected = { earthquake ->
                selectedEarthquakeId = earthquake.id
                selectedPointId = null
                showPointList = false
                focusOn(earthquake.latitude, earthquake.longitude)
            },
            onMapTapped = {
                selectedPointId = null
                selectedEarthquakeId = null
            },
        )

        Column(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .statusBarsPadding()
                .padding(horizontal = 16.dp)
                .padding(top = 8.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp),
        ) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                color = Color.White,
                border = BorderStroke(1.dp, Zinc100),
                shadowElevation = 8.dp,
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().height(58.dp).padding(start = 14.dp, end = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Icon(Icons.Outlined.Search, contentDescription = null, tint = Zinc600, modifier = Modifier.size(21.dp))
                    Box(Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                        if (searchQuery.isBlank()) {
                            Text("Yer, adres veya deprem ara", color = Zinc500, fontSize = 13.sp, maxLines = 1)
                        }
                        BasicTextField(
                            value = searchQuery,
                            onValueChange = { searchQuery = it },
                            singleLine = true,
                            textStyle = TextStyle(color = Zinc950, fontSize = 13.sp),
                            modifier = Modifier.fillMaxWidth().semantics {
                                contentDescription = "Yer, adres veya deprem ara"
                            },
                        )
                    }
                    if (searchQuery.isNotBlank()) {
                        IconButton(onClick = { searchQuery = "" }, modifier = Modifier.size(48.dp)) {
                            Icon(Icons.Outlined.Close, contentDescription = "Aramayı temizle", tint = Zinc600)
                        }
                    }
                    IconButton(
                        onClick = { showFilters = !showFilters },
                        modifier = Modifier.size(48.dp).semantics { contentDescription = "Harita filtrelerini göster" },
                    ) {
                        Icon(
                            if (showFilters) Icons.Outlined.Tune else Icons.Outlined.FilterList,
                            contentDescription = null,
                            tint = if (showFilters) AfetCrimson else Zinc700,
                        )
                    }
                }
            }

            if (showFilters) {
                androidx.compose.foundation.lazy.LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(7.dp),
                    contentPadding = PaddingValues(horizontal = 1.dp),
                ) {
                    items(items = mapFilters, key = { it }, contentType = { "map_filter" }) { filter ->
                        FilterChip(
                            selected = selectedFilter == filter,
                            onClick = { selectedFilter = filter },
                            label = { Text(filter, fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                            shape = RoundedCornerShape(30.dp),
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = AfetCrimson,
                                selectedLabelColor = Color.White,
                                containerColor = Color.White,
                                labelColor = Zinc700,
                            ),
                            border = FilterChipDefaults.filterChipBorder(
                                enabled = true,
                                selected = selectedFilter == filter,
                                borderColor = Zinc100,
                                selectedBorderColor = AfetCrimson,
                            ),
                        )
                    }
                }
            }

            errorMessage?.let { message ->
                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = Color.White.copy(alpha = 0.96f),
                    border = BorderStroke(1.dp, AfetCrimsonMuted),
                ) {
                    Text(
                        text = message,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                        color = AfetCrimson,
                        fontSize = 11.sp,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
        }

        if (showPointList) {
            PointListPanel(
                points = filteredPoints,
                location = state.deviceLocation,
                refreshing = state.isRefreshingPoints,
                maxHeight = listPanelMaxHeight,
                onClose = { showPointList = false },
                onSelect = { point ->
                    selectedPointId = point.id
                    selectedEarthquakeId = null
                    showPointList = false
                    focusOn(point.latitude, point.longitude)
                },
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp)
                    .padding(bottom = navigationClearance + 10.dp),
            )
        } else {
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp)
                    .padding(bottom = navigationClearance + 10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Surface(
                        modifier = Modifier.clickable {
                            if (filteredPoints.isNotEmpty()) showPointList = true
                        }
                            .semantics { contentDescription = "${filteredPoints.size} afet noktası, listeyi aç" },
                        shape = RoundedCornerShape(16.dp),
                        color = Color.White,
                        shadowElevation = 6.dp,
                    ) {
                        Row(
                            modifier = Modifier.height(48.dp).padding(horizontal = 12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            Icon(Icons.Outlined.LocationOn, contentDescription = null, tint = AfetCrimson, modifier = Modifier.size(17.dp))
                            Text("Noktalar", color = Zinc900, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                            Text(filteredPoints.size.toString(), color = AfetCrimson, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                    if (!hasSelection) MapControls(
                        onMyLocation = {
                            val location = state.deviceLocation
                            if (location == null) onRequestLocation?.invoke()
                            else focusOn(location.latitude, location.longitude, zoom = 14f)
                        },
                        onZoomIn = {
                            val current = cameraPositionState.position
                            cameraPositionState.position = current.copy(zoom = (current.zoom + 1f).coerceAtMost(19f))
                        },
                        onZoomOut = {
                            val current = cameraPositionState.position
                            cameraPositionState.position = current.copy(zoom = (current.zoom - 1f).coerceAtLeast(5f))
                        },
                        onRequestLocation = onRequestLocation,
                        isLocating = state.isLocating,
                        modifier = Modifier.padding(bottom = 34.dp),
                    )
                }
                if (hasSelection) {
                    SelectedMapItemCard(
                        point = selectedPoint,
                        earthquake = selectedEarthquake,
                        onDismiss = {
                            selectedPointId = null
                            selectedEarthquakeId = null
                        },
                        onOpenExternal = { latitude, longitude, title ->
                            openExternalMap(context, latitude, longitude, title)
                        },
                        onIncident = onIncident,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }
    }
}

@Composable
private fun MapControls(
    onMyLocation: () -> Unit,
    onZoomIn: () -> Unit,
    onZoomOut: () -> Unit,
    onRequestLocation: (() -> Unit)?,
    isLocating: Boolean,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Surface(
            modifier = Modifier.size(54.dp).clickable(onClick = onMyLocation)
                .semantics { contentDescription = if (onRequestLocation == null) "Konumum" else "Konumuma git" },
            shape = CircleShape,
            color = Color.White,
            border = BorderStroke(1.dp, Zinc100),
            shadowElevation = 7.dp,
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    Icons.Outlined.MyLocation,
                    contentDescription = null,
                    tint = if (isLocating) Zinc400 else AfetCrimson,
                    modifier = Modifier.size(22.dp),
                )
            }
        }
        Surface(
            modifier = Modifier.width(48.dp),
            shape = RoundedCornerShape(17.dp),
            color = Color.White,
            border = BorderStroke(1.dp, Zinc100),
            shadowElevation = 5.dp,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                IconButton(onClick = onZoomIn, modifier = Modifier.size(48.dp)) {
                    Icon(Icons.Outlined.Add, contentDescription = "Yakınlaştır", tint = Zinc800)
                }
                Box(Modifier.width(48.dp).height(1.dp).background(Zinc100))
                IconButton(onClick = onZoomOut, modifier = Modifier.size(48.dp)) {
                    Icon(Icons.Outlined.Remove, contentDescription = "Uzaklaştır", tint = Zinc800)
                }
            }
        }
    }
}

@Composable
private fun PointListPanel(
    points: List<MapPoint>,
    location: GeoPoint?,
    refreshing: Boolean,
    maxHeight: androidx.compose.ui.unit.Dp,
    onClose: () -> Unit,
    onSelect: (MapPoint) -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.heightIn(max = maxHeight).testTag("map_points_panel"),
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp, bottomStart = 22.dp, bottomEnd = 22.dp),
        color = Color.White,
        border = BorderStroke(1.dp, Zinc100),
        shadowElevation = 18.dp,
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
            Box(
                modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 10.dp).size(width = 34.dp, height = 4.dp)
                    .clip(CircleShape).background(Zinc100),
            )
            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 11.dp, bottom = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text("Afet noktaları", color = Zinc950, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                    Text(
                        if (refreshing) "Konumuna göre güncelleniyor…" else "${points.size} kayıt · kuş uçuşu sıralı",
                        color = Zinc500,
                        fontSize = 11.sp,
                    )
                }
                IconButton(onClick = onClose, modifier = Modifier.size(48.dp)) {
                    Icon(Icons.Outlined.Close, contentDescription = "Listeyi kapat", tint = Zinc600)
                }
            }
            if (points.isEmpty()) {
                Text(
                    "Bu arama ve filtrelerle eşleşen afet noktası bulunamadı.",
                    modifier = Modifier.fillMaxWidth().padding(vertical = 22.dp),
                    color = Zinc600,
                    fontSize = 12.sp,
                )
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxWidth().heightIn(max = maxHeight - 80.dp).testTag("map_points_list"),
                    contentPadding = PaddingValues(bottom = 10.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    items(items = points, key = { it.id }, contentType = { "map_point" }) { point ->
                        val distance = location?.let { distanceMetres(it, point) }
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onSelect(point) }
                                .padding(horizontal = 2.dp, vertical = 5.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp),
                        ) {
                            Surface(shape = CircleShape, color = AfetCrimsonMuted) {
                                Icon(
                                    Icons.Outlined.LocationOn,
                                    contentDescription = null,
                                    tint = AfetCrimson,
                                    modifier = Modifier.padding(9.dp).size(17.dp),
                                )
                            }
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                Text(point.title, color = Zinc900, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                Text(pointTypeLabel(point.type), color = Zinc500, fontSize = 10.5.sp, maxLines = 1)
                            }
                            distance?.let { Text(formatDistance(it), color = Zinc700, fontSize = 10.sp, fontWeight = FontWeight.Medium) }
                            Icon(Icons.Outlined.ChevronRight, contentDescription = null, tint = Zinc400, modifier = Modifier.size(17.dp))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SelectedMapItemCard(
    point: MapPoint?,
    earthquake: Earthquake?,
    onDismiss: () -> Unit,
    onOpenExternal: (Double, Double, String) -> Unit,
    onIncident: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val title = point?.title ?: earthquake?.epicenter.orEmpty()
    val latitude = point?.latitude ?: earthquake?.latitude ?: return
    val longitude = point?.longitude ?: earthquake?.longitude ?: return

    Surface(
        modifier = modifier.testTag("map_selected_item"),
        shape = RoundedCornerShape(22.dp),
        color = Color.White,
        border = BorderStroke(1.dp, Zinc100),
        shadowElevation = 16.dp,
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Surface(shape = CircleShape, color = if (earthquake != null) AfetCrimsonMuted else Color(0xFFE2F4F1)) {
                    Icon(
                        if (earthquake != null) Icons.Outlined.MyLocation else Icons.Outlined.LocationOn,
                        contentDescription = null,
                        tint = if (earthquake != null) AfetCrimson else Color(0xFF147D72),
                        modifier = Modifier.padding(9.dp).size(18.dp),
                    )
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(
                        text = title,
                        color = Zinc950,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = point?.let { pointTypeLabel(it.type) }
                            ?: earthquake?.let { "M ${magnitudeLabel(it.magnitude)} · ${it.depthKm.toInt()} km derinlik" }.orEmpty(),
                        color = Zinc600,
                        fontSize = 10.5.sp,
                        maxLines = 1,
                    )
                }
                IconButton(onClick = onDismiss, modifier = Modifier.size(48.dp)) {
                    Icon(Icons.Outlined.Close, contentDescription = "Ayrıntıyı kapat", tint = Zinc500)
                }
            }

            Text(
                text = point?.address?.takeIf(String::isNotBlank)
                    ?: earthquake?.let { "${compactTimestamp(it.occurredAt)} · ${it.source}" }.orEmpty(),
                color = Zinc600,
                fontSize = 11.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = { onOpenExternal(latitude, longitude, title) },
                    modifier = Modifier.weight(1f).height(42.dp),
                    shape = RoundedCornerShape(13.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AfetCrimson),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                ) {
                    Text("Harici haritada aç", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)
                }
                if (point?.type == MapPointType.INCIDENT) {
                    OutlinedButton(
                        onClick = { onIncident(point.id) },
                        modifier = Modifier.weight(1f).height(42.dp),
                        shape = RoundedCornerShape(13.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
                    ) {
                        Text("İhbarı aç", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)
                    }
                }
            }
        }
    }
}

private fun openExternalMap(context: android.content.Context, latitude: Double, longitude: Double, title: String) {
    val uri = Uri.parse("geo:0,0?q=$latitude,$longitude(${Uri.encode(title)})")
    try {
        context.startActivity(Intent(Intent.ACTION_VIEW, uri))
    } catch (_: ActivityNotFoundException) {
        Toast.makeText(context, "Harita uygulaması bulunamadı.", Toast.LENGTH_SHORT).show()
    } catch (_: SecurityException) {
        Toast.makeText(context, "Harita uygulaması açılamadı.", Toast.LENGTH_SHORT).show()
    }
}

private fun isValidCoordinate(point: MapPoint): Boolean =
    point.latitude.isFinite() && point.longitude.isFinite() &&
        point.latitude in -90.0..90.0 && point.longitude in -180.0..180.0

private fun distanceMetres(origin: GeoPoint, point: MapPoint): Float =
    distanceMetres(origin, GeoPoint(point.latitude, point.longitude))

private fun formatDistance(metres: Float): String =
    if (metres < 1_000) "${metres.toInt()} m · kuş uçuşu"
    else String.format(TurkishLocale, "%.1f km · kuş uçuşu", metres / 1_000)

private fun magnitudeLabel(magnitude: Double): String = String.format(TurkishLocale, "%.1f", magnitude)

private fun compactTimestamp(value: String): String = value
    .replace("T", " ")
    .substringBefore(".")
    .take(16)

private fun pointTypeLabel(type: MapPointType): String = when (type) {
    MapPointType.ASSEMBLY_AREA -> "Toplanma alanı"
    MapPointType.SHELTER_TENT -> "Geçici barınma alanı"
    MapPointType.SAHRA_HOSPITAL -> "Sahra hastanesi"
    MapPointType.CLOSED_ROAD -> "Yol kapanışı bildirimi"
    MapPointType.INCIDENT -> "İhbar"
    MapPointType.HEALTH_FACILITY -> "Sağlık kuruluşu"
    MapPointType.PHARMACY -> "Eczane"
    MapPointType.FIRE_STATION -> "İtfaiye"
    MapPointType.POLICE_STATION -> "Polis"
}
