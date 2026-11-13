package com.quakemind.core.designsystem

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val LightColors = lightColorScheme(
    primary = Color(0xFF176758), onPrimary = Color.White,
    primaryContainer = Color(0xFFE0EFE8), onPrimaryContainer = Color(0xFF154C40),
    secondary = Color(0xFF4E635B), onSecondary = Color.White,
    secondaryContainer = Color(0xFFE4ECE7), onSecondaryContainer = Color(0xFF253C33),
    tertiary = Color(0xFF305F82), onTertiary = Color.White,
    tertiaryContainer = Color(0xFFE2EDF7), onTertiaryContainer = Color(0xFF214563),
    background = Color(0xFFF4F6F3), onBackground = Color(0xFF192D25),
    surface = Color(0xFFFEFFFC), onSurface = Color(0xFF192D25),
    surfaceVariant = Color(0xFFE5EBE4), onSurfaceVariant = Color(0xFF536159),
    surfaceDim = Color(0xFFDCE3DA), surfaceBright = Color(0xFFFEFFFC),
    surfaceContainerLowest = Color.White, surfaceContainerLow = Color(0xFFF6F8F3),
    surfaceContainer = Color(0xFFEDF1EA), surfaceContainerHigh = Color(0xFFE6ECE3),
    surfaceContainerHighest = Color(0xFFDFE6DC),
    outline = Color(0xFF77877C), outlineVariant = Color(0xFFD4DDD2),
    error = Color(0xFFAB302F), onError = Color.White,
    errorContainer = Color(0xFFFFEDEA), onErrorContainer = Color(0xFF8D2425),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFA1D5BD), onPrimary = Color(0xFF0D382C),
    primaryContainer = Color(0xFF204D3D), onPrimaryContainer = Color(0xFFD0F0DF),
    secondary = Color(0xFFB6CBBE), onSecondary = Color(0xFF21382C),
    secondaryContainer = Color(0xFF354D40), onSecondaryContainer = Color(0xFFD7EADC),
    tertiary = Color(0xFFA6CBE9), onTertiary = Color(0xFF14354D),
    tertiaryContainer = Color(0xFF294C66), onTertiaryContainer = Color(0xFFD5E9FA),
    background = Color(0xFF101A16), onBackground = Color(0xFFE0E9DF),
    surface = Color(0xFF17231D), onSurface = Color(0xFFE0E9DF),
    surfaceVariant = Color(0xFF2B3B31), onSurfaceVariant = Color(0xFFB5C5B7),
    surfaceDim = Color(0xFF101A16), surfaceBright = Color(0xFF344239),
    surfaceContainerLowest = Color(0xFF0C1510), surfaceContainerLow = Color(0xFF142019),
    surfaceContainer = Color(0xFF1C2921), surfaceContainerHigh = Color(0xFF26332B),
    surfaceContainerHighest = Color(0xFF303E34),
    outline = Color(0xFF879A8B), outlineVariant = Color(0xFF3B4B40),
    error = Color(0xFFFFB4AC), onError = Color(0xFF641C1B),
    errorContainer = Color(0xFF4A2320), onErrorContainer = Color(0xFFFFDAD4),
)

// Existing feature tokens resolve to semantic roles so every screen follows the theme.
val AfetAccent: Color @Composable get() = MaterialTheme.colorScheme.primary
val AfetAccentMuted: Color @Composable get() = MaterialTheme.colorScheme.primaryContainer
val AfetAccentBorder: Color @Composable get() = MaterialTheme.colorScheme.outlineVariant
val AfetCrimson: Color @Composable get() = MaterialTheme.colorScheme.error
val AfetCrimsonMuted: Color @Composable get() = MaterialTheme.colorScheme.errorContainer
val AfetCrimsonBorder: Color @Composable get() = MaterialTheme.colorScheme.outlineVariant
val AfetRed: Color @Composable get() = MaterialTheme.colorScheme.error
val AfetRedMuted: Color @Composable get() = MaterialTheme.colorScheme.errorContainer
val AfetRedBorder: Color @Composable get() = MaterialTheme.colorScheme.outlineVariant
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
val AfetCrimsonDark = Color(0xFF7B2928)
val AfetGreen: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF9ED5B5) else Color(0xFF237052)
val AfetGreenMuted: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF213C2D) else Color(0xFFE8F4EA)
val AfetGreenBorder: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF45614D) else Color(0xFFBED9C6)
val AfetBlue: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFFA6CBE9) else Color(0xFF305F82)
val AfetBlueMuted: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF20394D) else Color(0xFFE2EDF7)
val AfetBlueBorder: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF3D586B) else Color(0xFFC5D9E8)
val AfetAmber: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFFEBC17E) else Color(0xFF86520C)
val AfetAmberMuted: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF40331C) else Color(0xFFFBF0DC)
val AfetAmberBorder: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFF655238) else Color(0xFFE7D3AD)
val AfetOrange: Color @Composable get() = if (MaterialTheme.colorScheme.background.luminance() < .5f) Color(0xFFF4B18E) else Color(0xFFA34920)

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
        headlineLarge = base.headlineLarge.copy(fontSize = 32.sp, lineHeight = 38.sp, fontWeight = FontWeight.Medium, letterSpacing = (-.8).sp),
        headlineMedium = base.headlineMedium.copy(fontSize = 28.sp, lineHeight = 34.sp, fontWeight = FontWeight.Medium, letterSpacing = (-.6).sp),
        headlineSmall = base.headlineSmall.copy(fontSize = 24.sp, lineHeight = 30.sp, fontWeight = FontWeight.Medium, letterSpacing = (-.4).sp),
        titleLarge = base.titleLarge.copy(fontSize = 22.sp, lineHeight = 28.sp, fontWeight = FontWeight.Medium),
        titleMedium = base.titleMedium.copy(fontSize = 16.sp, lineHeight = 23.sp, fontWeight = FontWeight.SemiBold),
        bodyLarge = base.bodyLarge.copy(fontSize = 16.sp, lineHeight = 24.sp),
        bodyMedium = base.bodyMedium.copy(fontSize = 14.sp, lineHeight = 21.sp),
        bodySmall = base.bodySmall.copy(fontSize = 12.sp, lineHeight = 18.sp),
        labelLarge = base.labelLarge.copy(fontWeight = FontWeight.SemiBold),
    )
}

private val QuakeShapes = Shapes(
    extraSmall = Shape6dp, small = Shape8dp, medium = Shape12dp,
    large = Shape16dp, extraLarge = Shape20dp,
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
