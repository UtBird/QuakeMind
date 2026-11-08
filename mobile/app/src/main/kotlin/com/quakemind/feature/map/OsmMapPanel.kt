package com.quakemind.feature.map

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.quakemind.core.designsystem.AfetCrimson
import com.quakemind.core.model.Earthquake
import com.quakemind.core.model.GeoPoint
import com.quakemind.core.model.MapPoint
import com.quakemind.core.model.MapPointType
import de.afarber.openmapview.CameraPosition
import de.afarber.openmapview.LatLng
import de.afarber.openmapview.MapType
import de.afarber.openmapview.clustering.ClusterItem
import de.afarber.openmapview.compose.CameraPositionState
import de.afarber.openmapview.compose.Circle
import de.afarber.openmapview.compose.Clustering
import de.afarber.openmapview.compose.ComposeMapColorScheme
import de.afarber.openmapview.compose.MapProperties
import de.afarber.openmapview.compose.MapUiSettings
import de.afarber.openmapview.compose.OpenMap
import de.afarber.openmapview.compose.rememberCameraPositionState

private val DefaultMapCenter = LatLng(40.65, 35.83)
private const val MAX_EARTHQUAKE_MARKERS = 500

@Composable
fun OsmMapPanel(
    earthquakes: List<Earthquake>,
    mapPoints: List<MapPoint>,
    location: GeoPoint?,
    cameraPositionState: CameraPositionState,
    modifier: Modifier = Modifier,
    contentPadding: PaddingValues = PaddingValues(),
    onPointSelected: (MapPoint) -> Unit = {},
    onEarthquakeSelected: (Earthquake) -> Unit = {},
    onMapTapped: () -> Unit = {},
) {
    val markerItems = remember(earthquakes, mapPoints) {
        buildList {
            earthquakes.asSequence()
                .filter { it.latitude.isValidLatitude() && it.longitude.isValidLongitude() }
                .take(MAX_EARTHQUAKE_MARKERS)
                .forEach { add(it.toMarkerItem()) }
            mapPoints.asSequence()
                .filter { it.latitude.isValidLatitude() && it.longitude.isValidLongitude() }
                .forEach { add(it.toMarkerItem()) }
        }
    }

    OpenMap(
        modifier = modifier,
        cameraPositionState = cameraPositionState,
        properties = MapProperties(
            mapType = MapType.STANDARD,
            minZoomPreference = 5f,
            maxZoomPreference = 19f,
        ),
        uiSettings = MapUiSettings(
            zoomControlsEnabled = false,
            myLocationButtonEnabled = false,
            compassEnabled = false,
        ),
        contentPadding = contentPadding,
        mapColorScheme = ComposeMapColorScheme.LIGHT,
        onMapClick = { onMapTapped() },
    ) {
        Clustering(
            items = markerItems,
            onClusterItemClick = { item ->
                item.earthquake?.let(onEarthquakeSelected)
                item.point?.let(onPointSelected)
                true
            },
        )

        location?.let { point ->
            val center = LatLng(point.latitude, point.longitude)
            Circle(
                center = center,
                radius = 24f,
                strokeColor = AfetCrimson.copy(alpha = 0.24f),
                strokeWidth = 1.5f,
                fillColor = AfetCrimson.copy(alpha = 0.12f),
                zIndex = 1f,
            )
            Circle(
                center = center,
                radius = 7f,
                strokeColor = Color.White,
                strokeWidth = 2.5f,
                fillColor = AfetCrimson,
                zIndex = 2f,
            )
        }
    }
}

@Composable
fun OsmMapPreview(
    earthquakes: List<Earthquake>,
    mapPoints: List<MapPoint>,
    location: GeoPoint?,
    modifier: Modifier = Modifier,
    selectedPoint: MapPoint? = null,
) {
    val target = selectedPoint?.let { GeoPoint(it.latitude, it.longitude) } ?: location
    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition(
            target = target?.toLatLng() ?: DefaultMapCenter,
            zoom = if (target == null) 6.5f else 12f,
        )
    }

    LaunchedEffect(target) {
        if (target != null) {
            cameraPositionState.position = CameraPosition(target = target.toLatLng(), zoom = 12f)
        }
    }

    OsmMapPanel(
        earthquakes = earthquakes,
        mapPoints = mapPoints,
        location = location,
        cameraPositionState = cameraPositionState,
        modifier = modifier,
    )
}

private data class MapOverlayItem(
    val label: String,
    val details: String?,
    val coordinate: LatLng,
    val earthquake: Earthquake? = null,
    val point: MapPoint? = null,
) : ClusterItem {
    override fun getPosition(): LatLng = coordinate

    override fun getTitle(): String = label

    override fun getSnippet(): String? = details
}

private fun Earthquake.toMarkerItem() = MapOverlayItem(
    label = "M ${String.format(java.util.Locale.US, "%.1f", magnitude)} · $epicenter",
    details = "${depthKm.toInt()} km derinlik · $occurredAt",
    coordinate = LatLng(latitude, longitude),
    earthquake = this,
)

private fun MapPoint.toMarkerItem() = MapOverlayItem(
    label = title,
    details = listOf(pointTypeLabel(type), address).filter(String::isNotBlank).joinToString(" · "),
    coordinate = LatLng(latitude, longitude),
    point = this,
)

private fun pointTypeLabel(type: MapPointType): String = when (type) {
    MapPointType.ASSEMBLY_AREA -> "Toplanma alanı"
    MapPointType.SHELTER_TENT -> "Geçici barınma alanı"
    MapPointType.SAHRA_HOSPITAL -> "Sahra hastanesi"
    MapPointType.CLOSED_ROAD -> "Yol kapanışı"
    MapPointType.INCIDENT -> "İhbar"
    MapPointType.HEALTH_FACILITY -> "Sağlık kuruluşu"
    MapPointType.PHARMACY -> "Eczane"
    MapPointType.FIRE_STATION -> "İtfaiye"
    MapPointType.POLICE_STATION -> "Polis"
}

private fun GeoPoint.toLatLng() = LatLng(latitude, longitude)

private fun Double.isValidLatitude(): Boolean = isFinite() && this in -90.0..90.0

private fun Double.isValidLongitude(): Boolean = isFinite() && this in -180.0..180.0
