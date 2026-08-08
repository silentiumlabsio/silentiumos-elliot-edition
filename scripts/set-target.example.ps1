# Copy this file to set-target.ps1 and edit the address.
$env:SILENTIUM_TARGET = "fire-tv-hostname.local:5555"

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb connect $env:SILENTIUM_TARGET
