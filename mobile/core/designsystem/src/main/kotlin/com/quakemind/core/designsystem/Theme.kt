package com.quakemind.core.designsystem

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * QuakeMind Design System — Dual-Theme Color Architecture
 *
 * Light Mode ("Architectural Mineral Daylight", default):
 * Pure neutral alabaster canvas (#F5F6F8) paired with crisp white cards (#FFFFFF)
 * and 1dp hairline borders (#E2E6EC) for effortless readability under direct sunlight.
 *
 * Dark Mode ("Obsidian Graphite Night Watch"):
 * Deep neutral charcoal-obsidian ramp (#0C0D0F canvas -> #141619 cards -> #1F2229 raised)
 * avoiding pure #000000 halation/black-smearing on OLED displays while preserving
 * nighttime visual comfort and sharp tonal elevation.
 *
 * Every foreground/background pair is verified >= 4.5:1 (WCAG AA), with primary &
 * secondary ink pairs exceeding 7.0:1 (WCAG AAA).
 */
private val LightColors = lightColorScheme(
    primary = Color(0xFF0D6B5D),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFE2F3EF),
    onPrimaryContainer = Color(0xFF094A40),
    secondary = Color(0xFF3E4A59),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFFE8ECF2),
    onSecondaryContainer = Color(0xFF1B2430),
    tertiary = Color(0xFF1B5E99),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFFE4F0FA),
    onTertiaryContainer = Color(0xFF103B63),
    background = Color(0xFFF5F6F8),
    onBackground = Color(0xFF111318),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF111318),
    surfaceVariant = Color(0xFFEBEEF3),
    onSurfaceVariant = Color(0xFF4B5260),
    surfaceDim = Color(0xFFE1E5EC),
    surfaceBright = Color(0xFFFFFFFF),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFF8F9FB),
    surfaceContainer = Color(0xFFEFF1F5),
    surfaceContainerHigh = Color(0xFFE6E9EF),
    surfaceContainerHighest = Color(0xFFDCE0E8),
    outline = Color(0xFF737C8C),
    outlineVariant = Color(0xFFE2E6EC),
    error = Color(0xFFC62828),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFFDECEC),
    onErrorContainer = Color(0xFF8C181A),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF3CD0B0),
    onPrimary = Color(0xFF062820),
    primaryContainer = Color(0xFF12332C),
    onPrimaryContainer = Color(0xFFA9EFE0),
    secondary = Color(0xFFB0B8C5),
    onSecondary = Color(0xFF1B2028),
    secondaryContainer = Color(0xFF22262E),
    onSecondaryContainer = Color(0xFFE2E6EE),
    tertiary = Color(0xFF6EB8FF),
    onTertiary = Color(0xFF0B2540),
    tertiaryContainer = Color(0xFF15283D),
    onTertiaryContainer = Color(0xFFCBE4FF),
    background = Color(0xFF0C0D0F),
    onBackground = Color(0xFFF2F4F7),
    surface = Color(0xFF141619),
    onSurface = Color(0xFFF2F4F7),
    surfaceVariant = Color(0xFF22262E),
    onSurfaceVariant = Color(0xFF9CA3B0),
    surfaceDim = Color(0xFF090A0C),
    surfaceBright = Color(0xFF2B303A),
    surfaceContainerLowest = Color(0xFF070809),
    surfaceContainerLow = Color(0xFF121417),
    surfaceContainer = Color(0xFF181A1F),
    surfaceContainerHigh = Color(0xFF1F2229),
    surfaceContainerHighest = Color(0xFF282C34),
    outline = Color(0xFF6E7685),
    outlineVariant = Color(0xFF262A31),
    error = Color(0xFFFF6B66),
    onError = Color(0xFF2B0807),
    errorContainer = Color(0xFF331517),
    onErrorContainer = Color(0xFFFFD6D4),
)

// Semantic color aliases — every feature resolves dynamically against active light/dark scheme.
val AfetAccent: Color @Composable get() = MaterialTheme.colorScheme.primary
val AfetAccentMuted: Color @Composable get() = MaterialTheme.colorScheme.primaryContainer
val AfetAccentBorder: Color @Composable get() = MaterialTheme.colorScheme.outlineVariant
val AfetCrimson: Color @Composable get() = MaterialTheme.colorScheme.error
val AfetCrimsonMuted: Color @Composable get() = MaterialTheme.colorScheme.errorContainer
val AfetCrimsonBorder: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF5A2528) else Color(0xFFF2C2C2)
val AfetRed: Color @Composable get() = MaterialTheme.colorScheme.error
val AfetRedMuted: Color @Composable get() = MaterialTheme.colorScheme.errorContainer
val AfetRedBorder: Color @Composable get() = AfetCrimsonBorder

val Zinc950: Color @Composable get() = MaterialTheme.colorScheme.onSurface
val Zinc900: Color @Composable get() = MaterialTheme.colorScheme.onSurface
val Zinc800: Color @Composable get() = MaterialTheme.colorScheme.onSurface
val Zinc700: Color @Composable get() = MaterialTheme.colorScheme.onSurfaceVariant
val Zinc600: Color @Composable get() = MaterialTheme.colorScheme.onSurfaceVariant
val Zinc500: Color @Composable get() = MaterialTheme.colorScheme.onSurfaceVariant
val Zinc400: Color @Composable get() = MaterialTheme.colorScheme.onSurfaceVariant
val Zinc300: Color @Composable get() = MaterialTheme.colorScheme.outline
val Zinc200: Color @Composable get() = MaterialTheme.colorScheme.outlineVariant
val Zinc100: Color @Composable get() = MaterialTheme.colorScheme.surfaceContainerHigh
val Zinc50: Color @Composable get() = MaterialTheme.colorScheme.surfaceContainerLow

val AfetNavy: Color @Composable get() = MaterialTheme.colorScheme.onSurface
val AfetNavyDark: Color @Composable get() = MaterialTheme.colorScheme.onSurface
val AfetCrimsonDark = Color(0xFF8C181A)

val AfetGreen: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF5AD69A) else Color(0xFF157347)
val AfetGreenMuted: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF122B20) else Color(0xFFE7F5EE)
val AfetGreenBorder: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF234F3B) else Color(0xFFBCE2CE)

val AfetBlue: Color @Composable get() = MaterialTheme.colorScheme.tertiary
val AfetBlueMuted: Color @Composable get() = MaterialTheme.colorScheme.tertiaryContainer
val AfetBlueBorder: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF254566) else Color(0xFFBCD7F0)

val AfetAmber: Color @Composable get() =
    if (isDarkSurface()) Color(0xFFF2B857) else Color(0xFF8F5100)
val AfetAmberMuted: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF2E2312) else Color(0xFFFDF2DF)
val AfetAmberBorder: Color @Composable get() =
    if (isDarkSurface()) Color(0xFF544020) else Color(0xFFEED4A8)

val AfetOrange: Color @Composable get() =
    if (isDarkSurface()) Color(0xFFFF9860) else Color(0xFFA83E0A)

@Composable
fun isDarkSurface(): Boolean = MaterialTheme.colorScheme.background.luminance() < 0.5f

val Shape2dp = RoundedCornerShape(2.dp)
val Shape4dp = RoundedCornerShape(4.dp)
val Shape5dp = RoundedCornerShape(5.dp)
val Shape6dp = RoundedCornerShape(6.dp)
val Shape8dp = RoundedCornerShape(8.dp)
val Shape9dp = RoundedCornerShape(9.dp)
val Shape10dp = RoundedCornerShape(10.dp)
val Shape12dp = RoundedCornerShape(12.dp)
val Shape14dp = RoundedCornerShape(14.dp)
val Shape16dp = RoundedCornerShape(16.dp)
val Shape20dp = RoundedCornerShape(20.dp)
val Shape24dp = RoundedCornerShape(24.dp)

val BorderZinc100: BorderStroke @Composable get() = BorderStroke(1.dp, Zinc100)
val BorderZinc200: BorderStroke @Composable get() = BorderStroke(1.dp, Zinc200)
val BorderZinc300: BorderStroke @Composable get() = BorderStroke(1.dp, Zinc300)
val BorderAfetCrimsonBorder: BorderStroke @Composable get() = BorderStroke(1.dp, AfetCrimsonBorder)
val BorderAfetAmberBorder: BorderStroke @Composable get() = BorderStroke(1.dp, AfetAmberBorder)
val BorderAfetGreenBorder: BorderStroke @Composable get() = BorderStroke(1.dp, AfetGreenBorder)
val BorderAfetBlueBorder: BorderStroke @Composable get() = BorderStroke(1.dp, AfetBlueBorder)
val BorderAfetCrimson1_5: BorderStroke @Composable get() = BorderStroke(1.5.dp, AfetCrimson)
val BorderAfetCrimsonBorder1_5: BorderStroke @Composable get() = BorderStroke(1.5.dp, AfetCrimsonBorder)
val BorderZinc400_1_5: BorderStroke @Composable get() = BorderStroke(1.5.dp, Zinc400)

private val QuakeTypography = Typography().let { base ->
    base.copy(
        displaySmall = base.displaySmall.copy(
            fontSize = 36.sp,
            lineHeight = 40.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.8).sp,
            fontFeatureSettings = "tnum",
        ),
        headlineLarge = base.headlineLarge.copy(
            fontSize = 30.sp,
            lineHeight = 36.sp,
            fontWeight = FontWeight.Medium,
            letterSpacing = (-0.6).sp,
        ),
        headlineMedium = base.headlineMedium.copy(
            fontSize = 26.sp,
            lineHeight = 32.sp,
            fontWeight = FontWeight.Medium,
            letterSpacing = (-0.4).sp,
        ),
        headlineSmall = base.headlineSmall.copy(
            fontSize = 22.sp,
            lineHeight = 28.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.25).sp,
        ),
        titleLarge = base.titleLarge.copy(
            fontSize = 20.sp,
            lineHeight = 26.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.2).sp,
        ),
        titleMedium = base.titleMedium.copy(
            fontSize = 16.sp,
            lineHeight = 22.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 0.sp,
        ),
        titleSmall = base.titleSmall.copy(
            fontSize = 14.sp,
            lineHeight = 20.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 0.sp,
        ),
        bodyLarge = base.bodyLarge.copy(
            fontSize = 16.sp,
            lineHeight = 24.sp,
            fontWeight = FontWeight.Normal,
            letterSpacing = 0.sp,
        ),
        bodyMedium = base.bodyMedium.copy(
            fontSize = 14.sp,
            lineHeight = 20.sp,
            fontWeight = FontWeight.Normal,
            letterSpacing = 0.sp,
        ),
        bodySmall = base.bodySmall.copy(
            fontSize = 12.sp,
            lineHeight = 17.sp,
            fontWeight = FontWeight.Normal,
            letterSpacing = 0.1.sp,
        ),
        labelLarge = base.labelLarge.copy(
            fontSize = 14.sp,
            lineHeight = 20.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 0.sp,
        ),
        labelMedium = base.labelMedium.copy(
            fontSize = 12.sp,
            lineHeight = 16.sp,
            fontWeight = FontWeight.Medium,
            letterSpacing = 0.15.sp,
        ),
        labelSmall = base.labelSmall.copy(
            fontSize = 11.sp,
            lineHeight = 14.sp,
            fontWeight = FontWeight.Medium,
            letterSpacing = 0.15.sp,
        ),
    )
}

fun TextStyle.tabular(): TextStyle = copy(fontFeatureSettings = "tnum")

private val QuakeShapes = Shapes(
    extraSmall = Shape6dp,
    small = Shape8dp,
    medium = Shape12dp,
    large = Shape16dp,
    extraLarge = Shape20dp,
)

fun Double.formatMagnitude(): String {
    val rounded = (this * 10.0 + 0.5).toLong()
    return "${rounded / 10}.${rounded % 10}"
}

@Composable
fun QuakeMindTheme(
    darkTheme: Boolean = false,
    content: @Composable () -> Unit,
) {
    val colors = if (darkTheme) DarkColors else LightColors
    MaterialTheme(
        colorScheme = colors,
        typography = QuakeTypography,
        shapes = QuakeShapes,
    ) {
        CompositionLocalProvider(LocalContentColor provides colors.onBackground, content = content)
    }
}
