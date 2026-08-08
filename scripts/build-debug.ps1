$ErrorActionPreference = "Stop"

if (-not $env:ANDROID_HOME) {
    $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
}

if (-not $env:SILENTIUM_PARENT_PIN) {
    throw "Set SILENTIUM_PARENT_PIN locally before building."
}

$gradle = Get-Command gradle -ErrorAction SilentlyContinue
if (-not $gradle) {
    throw "Gradle was not found. Open the project in Android Studio or install Gradle."
}

gradle clean :app:assembleDebug
