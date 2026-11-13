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
class ChecklistInteractionBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun checklistScrollAndToggle() = benchmarkRule.measureRepeated(
        packageName = TARGET_PACKAGE,
        metrics = listOf(FrameTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.WARM,
        compilationMode = CompilationMode.DEFAULT,
        setupBlock = {
            pressHome()
            navigateToHome()
            clickBottomTab("Çanta")
            device.wait(Until.hasObject(By.text("Afet ve Acil Durum Çantası")), SHORT_TIMEOUT)
        },
    ) {
        // Toggle first visible checklist item
        val item1 = device.findObject(By.text("Düdük ve Yüksek Sesli Alarm"))
        item1?.click()
        device.waitForIdle()

        // Toggle another item
        val item2 = device.findObject(By.text("Kişi Başı En Az 2 Litre Şişe Su"))
        item2?.click()
        device.waitForIdle()

        // Scroll list
        scrollFeed()
    }
}
