package com.quakemind.benchmark

import androidx.benchmark.macro.MacrobenchmarkScope
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Direction
import androidx.test.uiautomator.Until

internal const val SHORT_TIMEOUT = 5_000L
internal const val LONG_TIMEOUT = 10_000L

/**
 * Ensures the app navigates through splash, onboarding, or auth to land on the Home screen.
 */
fun MacrobenchmarkScope.navigateToHome() {
    startActivityAndWait()
    device.waitForIdle()

    // 1. If splash is visible, wait for splash delay to pass (1.2s + transition)
    val onSkip = device.wait(Until.findObject(By.text("Atla")), SHORT_TIMEOUT)
    if (onSkip != null) {
        onSkip.click()
        device.waitForIdle()
    }

    // 2. If Auth screen is visible, click guest button
    val guestBtn = device.wait(
        Until.findObject(By.text("Giriş Yapmadan Devam Et (Acil Mod)")),
        SHORT_TIMEOUT,
    )
    if (guestBtn != null) {
        guestBtn.click()
        device.waitForIdle()
    }

    // 3. Confirm Home screen loaded
    device.wait(Until.hasObject(By.text("AFET")), LONG_TIMEOUT)
    device.waitForIdle()
}

/**
 * Clicks a bottom navigation item by label.
 */
fun MacrobenchmarkScope.clickBottomTab(label: String) {
    val tab = device.wait(Until.findObject(By.text(label)), SHORT_TIMEOUT)
        ?: device.findObject(By.desc(label))
    tab?.click()
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
        // Fallback screen drag
        val centerX = device.displayWidth / 2
        val startY = (device.displayHeight * 0.75).toInt()
        val endY = (device.displayHeight * 0.25).toInt()
        device.swipe(centerX, startY, centerX, endY, 20)
        device.waitForIdle()
        device.swipe(centerX, endY, centerX, startY, 20)
        device.waitForIdle()
    }
}
