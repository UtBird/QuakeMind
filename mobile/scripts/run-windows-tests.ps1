# AGP 9.3/Gradle 9.5 on Windows may fail to load compiled JUnit classes when
# the project directory contains non-ASCII characters (e.g. "Yazılım").
# SUBST provides an ASCII-only path without moving or copying the repository.
# The drive alias is removed in finally, including when the test run fails.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$drive = 'Q:'
$driveRoot = 'Q:\'

if (Test-Path -LiteralPath $driveRoot) {
    throw "$drive is already in use. Refusing to change an existing drive."
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'gradlew.bat'))) {
    throw "Android Gradle wrapper was not found in $projectRoot"
}

$sdkPath = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
if (-not (Test-Path -LiteralPath $sdkPath)) {
    throw "Android SDK not found at $sdkPath; install it or use Android Studio."
}

$previousAndroidHome = [Environment]::GetEnvironmentVariable('ANDROID_HOME', 'Process')
$driveCreated = $false
$locationPushed = $false

try {
    & subst $drive $projectRoot
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $driveRoot 'gradlew.bat'))) {
        throw "Failed to create the temporary $drive drive alias."
    }
    $driveCreated = $true
    $env:ANDROID_HOME = $sdkPath
    Push-Location -LiteralPath $driveRoot
    $locationPushed = $true

    & .\gradlew.bat :core:data:testDebugUnitTest :app:testDebugUnitTest --offline --no-build-cache '-Pkotlin.incremental=false' --console=plain
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle unit tests failed (exit code $LASTEXITCODE)."
    }
} finally {
    if ($locationPushed) { Pop-Location }
    [Environment]::SetEnvironmentVariable('ANDROID_HOME', $previousAndroidHome, 'Process')
    if ($driveCreated) {
        & subst $drive /D
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove $drive. Run: subst $drive /D"
        }
    }
}
