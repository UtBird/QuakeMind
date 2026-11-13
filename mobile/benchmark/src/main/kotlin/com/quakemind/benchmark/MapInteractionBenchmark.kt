package com.quakemind.benchmark

import androidx.benchmark.macro.CompilationMode
import androidx.benchmark.macro.FrameTimingMetric
import androidx.benchmark.macro.StartupMode
import androidx.benchmark.macro.junit4.MacrobenchmarkRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Until
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@LargeTest
class MapInteractionBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun mapInteractionAndFilters() = benchmarkRule.measureRepeated(
        packageName = TARGET_PACKAGE,
        metrics = listOf(FrameTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.WARM,
        compilationMode = CompilationMode.DEFAULT,
        setupBlock = {
            pressHome()
            navigateToHome()
            clickBottomTab("Harita")
            device.wait(Until.hasObject(By.text("Toplanma Alanı")), SHORT_TIMEOUT)
        },
    ) {
        // 1. Click filter chips
        val filterChip1 = device.findObject(By.text("Toplanma Alanı"))
        filterChip1?.click()
        device.waitForIdle()

        val filterChip2 = device.findObject(By.text("Yakındakiler"))
        filterChip2?.click()
        device.waitForIdle()

        // 2. Tap center of map Canvas to trigger pin tap calculation
        val centerX = device.displayWidth / 2
        val centerY = device.displayHeight / 2
        device.click(centerX, centerY)
        device.waitForIdle()

        // 3. Reset filter
        val filterAll = device.findObject(By.text("Tümü"))
        filterAll?.click()
        device.waitForIdle()
    }
}
