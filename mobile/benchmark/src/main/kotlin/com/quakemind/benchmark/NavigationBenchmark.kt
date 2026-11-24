package com.quakemind.benchmark

import androidx.benchmark.macro.CompilationMode
import androidx.benchmark.macro.FrameTimingMetric
import androidx.benchmark.macro.StartupMode
import androidx.benchmark.macro.junit4.MacrobenchmarkRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@LargeTest
class NavigationBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun bottomNavigationTransitions() = benchmarkRule.measureRepeated(
        packageName = TARGET_PACKAGE,
        metrics = listOf(FrameTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.WARM,
        compilationMode = CompilationMode.DEFAULT,
        setupBlock = {
            pressHome()
            navigateToHome()
        },
    ) {
        // Transition: Home -> Map
        clickBottomTab("Harita")
        // Transition: Map -> P2P Mesh
        clickBottomTab("Yakın Ağ")
        // Transition: P2P Mesh -> Alerts
        clickBottomTab("Uyarılar")
        // Transition: Alerts -> Home
        clickBottomTab("Ana Sayfa")
    }
}
