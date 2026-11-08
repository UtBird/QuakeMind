package com.quakemind.benchmark

import androidx.benchmark.macro.CompilationMode
import androidx.benchmark.macro.FrameTimingMetric
import androidx.benchmark.macro.StartupMode
import androidx.benchmark.macro.junit4.MacrobenchmarkRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Direction
import androidx.test.uiautomator.Until
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@LargeTest
class HomeReturnBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun homeReturnAndScrollRestoration() = benchmarkRule.measureRepeated(
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
        // 1. Initial scroll down on Home
        val scrollable = device.findObject(By.scrollable(true))
        if (scrollable != null) {
            scrollable.setGestureMargin(device.displayWidth / 5)
            scrollable.fling(Direction.DOWN)
            device.waitForIdle()
        }

        // 2. Navigate away to Map tab
        clickBottomTab("Harita")
        device.wait(Until.hasObject(By.text("Toplanma Alanı")), SHORT_TIMEOUT)
        device.waitForIdle()

        // 3. Return back to Home tab (Instant cached content & scroll position restored)
        clickBottomTab("Ana Sayfa")
        device.wait(Until.hasObject(By.text("AFET")), SHORT_TIMEOUT)
        device.waitForIdle()

        // 4. Perform rapid fling down and up
        if (scrollable != null) {
            scrollable.fling(Direction.DOWN)
            device.waitForIdle()
            scrollable.fling(Direction.UP)
            device.waitForIdle()
        }
    }
}
