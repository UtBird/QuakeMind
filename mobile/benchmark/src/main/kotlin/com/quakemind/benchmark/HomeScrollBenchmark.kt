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
class HomeScrollBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun homeFeedScroll() = benchmarkRule.measureRepeated(
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
        val scrollable = androidx.test.uiautomator.By.scrollable(true)
        val feed = device.findObject(scrollable)
        if (feed != null) {
            feed.setGestureMargin(device.displayWidth / 5)
            // 1. Fast scroll down
            feed.fling(androidx.test.uiautomator.Direction.DOWN)
            device.waitForIdle()
            // 2. Fast scroll up
            feed.fling(androidx.test.uiautomator.Direction.UP)
            device.waitForIdle()
            // 3. Fast scroll down again
            feed.fling(androidx.test.uiautomator.Direction.DOWN)
            device.waitForIdle()
        } else {
            scrollFeed()
        }
    }
}
