package com.quakemind

import android.os.Bundle
import android.graphics.Color
import android.os.Build
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.graphics.luminance
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.quakemind.core.designsystem.QuakeMindTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val preferences = getSharedPreferences("appearance_and_onboarding", MODE_PRIVATE)
        val onboardingCompleted = preferences.getBoolean("onboarding_completed", false)
        var darkTheme by mutableStateOf(preferences.getBoolean("dark_theme", false))
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.isNavigationBarContrastEnforced = false
            window.isStatusBarContrastEnforced = false
        }
        setContent {
            QuakeMindTheme(darkTheme = darkTheme) {
                val lightBars = MaterialTheme.colorScheme.background.luminance() > .5f
                SideEffect {
                    WindowInsetsControllerCompat(window, window.decorView).apply {
                        isAppearanceLightStatusBars = lightBars
                        isAppearanceLightNavigationBars = lightBars
                    }
                }
                QuakeMindApp(
                    onboardingCompleted = onboardingCompleted,
                    onOnboardingCompleted = {
                        preferences.edit().putBoolean("onboarding_completed", true).apply()
                    },
                    darkTheme = darkTheme,
                    onDarkThemeChange = { enabled ->
                        preferences.edit().putBoolean("dark_theme", enabled).apply()
                        darkTheme = enabled
                    },
                )
            }
        }
    }
}
