package com.quakemind.core.designsystem

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

// ---------------------------------------------------------------------------
// BRAND COLOR PALETTE (User Theme: #800E13 Crimson Lacquer on Pure White #FFFFFF)
// ---------------------------------------------------------------------------
val AfetCrimson = Color(0xFF800E13)         // Primary Brand Crimson (#800E13)
val AfetCrimsonDark = Color(0xFF5E0A0E)     // Deep Crimson
val AfetCrimsonMuted = Color(0xFFFDF4F4)    // Subtle blush tint for badges/surfaces
val AfetCrimsonBorder = Color(0xFFF5D6D8)   // 1px Border tint for active states

val AfetRed = AfetCrimson
val AfetRedMuted = AfetCrimsonMuted
val AfetRedBorder = AfetCrimsonBorder

// shadcn Zinc / Neutral Palette
val Zinc950 = Color(0xFF09090B)
val Zinc900 = Color(0xFF18181B)
val Zinc800 = Color(0xFF27272A)
val Zinc700 = Color(0xFF3F3F46)
val Zinc600 = Color(0xFF52525B)
val Zinc500 = Color(0xFF71717A)
val Zinc400 = Color(0xFFA1A1AA)
val Zinc300 = Color(0xFFD4D4D8)
val Zinc200 = Color(0xFFE4E4E7)
val Zinc100 = Color(0xFFF4F4F5)
val Zinc50 = Color(0xFFFAFAFA)

// Semantic Accents (Refined, Elegant, High-Contrast)
val AfetGreen = Color(0xFF059669)     // Emerald 600
val AfetGreenMuted = Color(0xFFECFDF5)
val AfetGreenBorder = Color(0xFFA7F3D0)

val AfetBlue = Color(0xFF0284C7)      // Sky 600
val AfetBlueMuted = Color(0xFFF0F9FF)
val AfetBlueBorder = Color(0xFFBAE6FD)

val AfetAmber = Color(0xFFD97706)     // Amber 600
val AfetAmberMuted = Color(0xFFFFFBEB)
val AfetAmberBorder = Color(0xFFFDE68A)

val AfetOrange = Color(0xFFC2410C)

val AfetNavy = Zinc900
val AfetNavyDark = Zinc950

// Pure White & Crimson Theme
private val ShadcnWhiteColorScheme = lightColorScheme(
    primary = AfetCrimson,
    onPrimary = Color.White,
    primaryContainer = AfetCrimsonMuted,
    onPrimaryContainer = AfetCrimson,
    secondary = Zinc900,
    onSecondary = Color.White,
    secondaryContainer = Zinc100,
    onSecondaryContainer = Zinc900,
    tertiary = AfetBlue,
    onTertiary = Color.White,
    background = Color.White,
    onBackground = Zinc950,
    surface = Color.White,
    onSurface = Zinc950,
    surfaceVariant = Zinc50,
    onSurfaceVariant = Zinc500,
    outline = Zinc200,
    outlineVariant = Zinc100,
    error = AfetCrimson,
    onError = Color.White,
    errorContainer = AfetCrimsonMuted,
    onErrorContainer = AfetCrimson,
)

// Sharp, Refined Shadcn Radius System
private val ShadcnShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(20.dp),
)

// ---------------------------------------------------------------------------
// PRE-ALLOCATED CACHED SHAPES & BORDERS (Zero-Allocation Scroll Performance)
// ---------------------------------------------------------------------------
val Shape2dp = RoundedCornerShape(2.dp)
val Shape4dp = RoundedCornerShape(4.dp)
val Shape5dp = RoundedCornerShape(5.dp)
val Shape6dp = RoundedCornerShape(6.dp)
val Shape8dp = RoundedCornerShape(8.dp)
val Shape9dp = RoundedCornerShape(9.dp)
val Shape10dp = RoundedCornerShape(10.dp)
val Shape12dp = RoundedCornerShape(12.dp)
val Shape16dp = RoundedCornerShape(16.dp)
val Shape20dp = RoundedCornerShape(20.dp)

val BorderZinc100 = androidx.compose.foundation.BorderStroke(1.dp, Zinc100)
val BorderZinc200 = androidx.compose.foundation.BorderStroke(1.dp, Zinc200)
val BorderZinc300 = androidx.compose.foundation.BorderStroke(1.dp, Zinc300)
val BorderAfetCrimsonBorder = androidx.compose.foundation.BorderStroke(1.dp, AfetCrimsonBorder)
val BorderAfetAmberBorder = androidx.compose.foundation.BorderStroke(1.dp, AfetAmberBorder)
val BorderAfetGreenBorder = androidx.compose.foundation.BorderStroke(1.dp, AfetGreenBorder)
val BorderAfetBlueBorder = androidx.compose.foundation.BorderStroke(1.dp, AfetBlueBorder)
val BorderAfetCrimson1_5 = androidx.compose.foundation.BorderStroke(1.5.dp, AfetCrimson)
val BorderAfetCrimsonBorder1_5 = androidx.compose.foundation.BorderStroke(1.5.dp, AfetCrimsonBorder)
val BorderZinc400_1_5 = androidx.compose.foundation.BorderStroke(1.5.dp, Zinc400)

/**
 * Fast magnitude formatting that avoids heavy Java String.format reflection/locale regex allocations.
 */
fun Double.formatMagnitude(): String {
    val rounded = (this * 10.0 + 0.5).toLong()
    val whole = rounded / 10
    val frac = rounded % 10
    return "$whole.$frac"
}

@Composable
fun QuakeMindTheme(
    darkTheme: Boolean = false,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = ShadcnWhiteColorScheme,
        shapes = ShadcnShapes,
        content = content,
    )
}
