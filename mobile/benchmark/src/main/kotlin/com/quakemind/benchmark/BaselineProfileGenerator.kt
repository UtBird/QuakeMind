package com.quakemind.benchmark

import androidx.benchmark.macro.junit4.BaselineProfileRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Until
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@LargeTest
class BaselineProfileGenerator {
    @get:Rule
    val baselineProfileRule = BaselineProfileRule()

    @Test
    fun generateBaselineProfile() = baselineProfileRule.collect(
        packageName = TARGET_PACKAGE,
        includeInStartupProfile = true,
    ) {
        pressHome()
        startActivityAndWait()
        device.waitForIdle()

        // 1. Traverse through initial splash/onboarding/auth to Home
        val onSkip = device.wait(Until.findObject(By.text("Atla")), SHORT_TIMEOUT)
        if (onSkip != null) {
            onSkip.click()
            device.waitForIdle()
        }

        val guestBtn = device.wait(
            Until.findObject(By.text("Giriş Yapmadan Devam Et (Acil Mod)")),
            SHORT_TIMEOUT,
        )
        if (guestBtn != null) {
            guestBtn.click()
            device.waitForIdle()
        }

        device.wait(Until.hasObject(By.text("AFET")), LONG_TIMEOUT)
        device.waitForIdle()

        // 2. Home Feed Scroll
        scrollFeed()

        // 3. Journey: Home -> Map -> Home
        clickBottomTab("Harita")
        device.wait(Until.hasObject(By.text("Toplanma Alanı")), SHORT_TIMEOUT)
        device.waitForIdle()
        clickBottomTab("Ana Sayfa")
        device.wait(Until.hasObject(By.text("AFET")), SHORT_TIMEOUT)
        device.waitForIdle()

        // 4. Journey: Home -> Alerts -> Home
        clickBottomTab("Uyarılar")
        device.wait(Until.hasObject(By.text("Bölgesel Bildirimler & Uyarılar")), SHORT_TIMEOUT)
        scrollFeed()
        clickBottomTab("Ana Sayfa")
        device.wait(Until.hasObject(By.text("AFET")), SHORT_TIMEOUT)
        device.waitForIdle()

        // 5. Journey: Home -> Checklist -> Home
        clickBottomTab("Çanta")
        device.wait(Until.hasObject(By.text("Afet ve Acil Durum Çantası")), SHORT_TIMEOUT)
        scrollFeed()
        clickBottomTab("Ana Sayfa")
        device.wait(Until.hasObject(By.text("AFET")), SHORT_TIMEOUT)
        device.waitForIdle()

        // 6. Journey: Earthquake list scroll & filter
        scrollFeed()

        // 7. Journey: Report open & return
        val reportTile = device.findObject(By.text("Acil İhbar Bildir"))
        if (reportTile != null) {
            reportTile.click()
            device.wait(Until.hasObject(By.text("Acil Durum İhbar Masası")), SHORT_TIMEOUT)
            device.pressBack()
            device.waitForIdle()
        }
    }
}
