# Copy this file to set-target.ps1. The local copy is ignored by Git.
$env:SILENTIUM_TARGET = Read-Host "Authorized ADB hostname and port"

if (-not $env:SILENTIUM_TARGET) {
    throw "SILENTIUM_TARGET is required."
}

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb connect $env:SILENTIUM_TARGET
