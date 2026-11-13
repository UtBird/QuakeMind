package com.quakemind.benchmark

import androidx.benchmark.macro.MacrobenchmarkScope
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Direction
import androidx.test.uiautomator.BySelector
import androidx.test.uiautomator.StaleObjectException
import androidx.test.uiautomator.Until

internal const val SHORT_TIMEOUT = 5_000L
internal const val LONG_TIMEOUT = 10_000L

/**
 * Ensures the app navigates through splash, onboarding, or auth to land on the Home screen.
 */
fun MacrobenchmarkScope.navigateToHome() {
    startActivityAndWait()
    device.waitForIdle()

    clickSetupControl(By.text("Atla"))
    clickSetupControl(By.text("Misafir Oturumu Aç (Acil Mod)"))

    // 3. Confirm Home screen loaded
    check(device.wait(Until.hasObject(By.text("Ana Sayfa")), LONG_TIMEOUT)) { "Home was not reached; authentication or backend unavailable" }
    device.waitForIdle()
}

/**
 * Clicks a bottom navigation item by label.
 */
fun MacrobenchmarkScope.clickBottomTab(label: String) {
    val tab = device.wait(Until.findObject(By.text(label)), SHORT_TIMEOUT)
        ?: device.findObject(By.desc(label))
    checkNotNull(tab) { "Navigation tab not found: $label" }.click()
    device.waitForIdle()
}

/**
 * Performs fling/scroll on a scrollable container.
 */
fun MacrobenchmarkScope.scrollFeed(scrollableTag: String? = null) {
    val scrollable = if (scrollableTag != null) {
        device.findObject(By.res(scrollableTag)) ?: device.findObject(By.scrollable(true))
    } else {
        device.findObject(By.scrollable(true))
    }

    if (scrollable != null) {
        scrollable.setGestureMargin(device.displayWidth / 5)
        scrollable.fling(Direction.DOWN)
        device.waitForIdle()
        scrollable.fling(Direction.UP)
        device.waitForIdle()
    } else {
        error("Scrollable feed not found: $scrollableTag")
    }
}

/** Reacquire nodes replaced by a startup composition; never reuse stale setup handles. */
private fun MacrobenchmarkScope.clickSetupControl(selector: BySelector) {
    repeat(3) {
        val control = device.wait(Until.findObject(selector), SHORT_TIMEOUT) ?: return
        try {
            control.click()
            device.waitForIdle()
            return
        } catch (_: StaleObjectException) {
            device.waitForIdle()
        }
    }
    error("Startup control kept being replaced: $selector")
}
