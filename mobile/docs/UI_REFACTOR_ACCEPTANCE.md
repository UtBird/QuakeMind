# Mobile UI refactor — 13 November 2026

## Implemented

Shared semantic light/dark palette and native typography; content-sized task headers;
flat reusable cards; native bottom-navigation semantics and measured insets; immediate
tab switches; a Home organized around reporting, safety, catalogue records and resources.
SOS, safety and damage screens receive state/events from feature routes. Report inputs
survive saved-state restoration. Checklist rows expose checkbox semantics. Unsupported
profile switches, identity claims and duplicated safety state were removed.

Design references: local Eon component structure; Impeccable; Android UI Engineering;
Jetpack Compose Performance; Unslop by Damir Sokolovsky, https://github.com/heydamir/unslop
(CC BY 4.0). Unslop was installed in the user's Codex skills directory, not as an app dependency.

## Verification evidence and limits

- Debug APK and Android test APK built; Android lint passed (existing warnings remain).
- 10 existing JUnit tests passed using an ASCII drive mapping of this checkout. The normal
  Unicode checkout path produced ClassNotFoundException in Gradle's test worker; no
  ineffective production workaround was retained.
- Initial Vivo V2205 device run: 15 UI tests passed. Expanded final device suite is recorded
  separately in the task output. Screenshots live under `.impeccable/review/ui-review/`.
- Screenshots prompted correction of the default dark foreground; a further shared-field
  audit corrected hardcoded light text-field containers and the high-urgency badge.
- Debug scrolling + tab-switch sample: 499 frames, 34 missed deadlines (6.81%); frame-time
  histogram p50 16 ms, p95 40 ms, p99 73 ms. This mixed debug sample includes cold map
  work, is not a release benchmark, and cannot prove a speedup without a comparable baseline.
- A 20-second Perfetto trace was captured, but it lacks app FrameTimeline rows and reports
  13 dropped negative timestamps. It is not used to assert per-screen timing.
- Tablet emulator launch was blocked by insufficient host disk space. Tablet visual
  acceptance and a release-mode performance gate remain open. No emergency report, SOS
  or SMS was submitted during manual checks.

## Files changed in this pass

- `mobile/app/src/androidTest/kotlin/com/quakemind/OnboardingTest.kt`
- `mobile/app/src/androidTest/kotlin/com/quakemind/visual/GoldenScreenshotRegressionTest.kt`
- `mobile/app/src/main/kotlin/com/quakemind/App.kt`
- `mobile/app/src/main/kotlin/com/quakemind/MainActivity.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/alerts/AlertDetailScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/alerts/AlertsScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/analysis/damage/DamageRoute.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/auth/AuthScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/checklist/ChecklistScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/checklist/RiskScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/damage/DamageScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/damage/NlpScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/emergency/safety/SafetyRoute.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/emergency/safety/SafetyUiState.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/emergency/safety/SafetyViewModel.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/emergency/sos/SosRoute.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/home/HomeScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/map/MapScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/map/OsmMapPanel.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/onboarding/OnboardingScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/operations/OperationsScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/profile/ProfileRoute.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/profile/ProfileScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/profile/ProfileUiState.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/report/ReportScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/routing/RoutingScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/safety/SafetyScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/sos/SosScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/feature/splash/SplashScreen.kt`
- `mobile/app/src/main/kotlin/com/quakemind/navigation/AppNavHost.kt`
- `mobile/app/src/main/kotlin/com/quakemind/navigation/components/BottomNavigation.kt`
- `mobile/core/designsystem/src/main/kotlin/com/quakemind/core/designsystem/Components.kt`
- `mobile/core/designsystem/src/main/kotlin/com/quakemind/core/designsystem/Theme.kt`

Additional files: PRODUCT.md, DESIGN.md, .impeccable/design.json, ScreenHeader.kt,
MobileDesignRegressionTest.kt, this report, and the two Android style resources.
Pre-existing backend, database, network and deployment changes were preserved.

## Final review disposition

Final debug APK, Android test APK, lint and 10 unit tests passed. On Vivo, the
expanded suite ran 20 tests: 19 screen tests passed; the entry integration test
did not reach Home. On retry, localhost:8000 refused connections (the previously
running development API was no longer listening). No offline authentication bypass
was added. A transient missing Compose hierarchy in the entry test was corrected
with the test API's optional-root polling; the backend dependency remains explicit.

Independent Impeccable finish review: **recapture**, not full acceptance. Phone
captures support the direction. Expanded navigation still needs a rail/drawer;
actual shell/system-bar/IME captures and tablet acceptance remain required. Some
interaction captures contain ripples. Release smoothness is not established.

Latest design tools: Unslop installed from heydamir/unslop and its signs/craft pass
applied to heading weight, AI icon treatment and native light/dark input surfaces.
