# Testing guide

## Public-safe checks

Run the repository audit first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\audit-public-release.ps1
```

Parse every Python tool without executing device or network actions:

```powershell
python -c "import ast,pathlib; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in pathlib.Path('tools').glob('*.py')]"
```

## Android build

Set a throwaway local PIN that is not used on a production device:

```powershell
$securePin = Read-Host "Temporary four-digit build PIN" -AsSecureString
$env:SILENTIUM_PARENT_PIN = (New-Object System.Net.NetworkCredential("", $securePin)).Password
gradle clean :app:assembleDebug
Remove-Item Env:SILENTIUM_PARENT_PIN
Remove-Variable securePin
```

Do not commit the resulting APK or `build/` directories.

## Device setup

Set the target only in the current shell:

```powershell
$env:SILENTIUM_TARGET = "fire-tv-hostname.local:5555"
python tools/enable_console_mode.py
```

Use only an authorized device on a trusted development network. Remove the variable after testing:

```powershell
Remove-Item Env:SILENTIUM_TARGET
```

## Manual acceptance checklist

- Splash launches from the leanback launcher.
- Dashboard tiles receive visible controller focus.
- Back does not escape the child-facing dashboard.
- Parent tools reject incorrect PIN input.
- Parent tools open after the locally configured PIN.
- Home redirect returns to SilentiumOS on the tested Fire OS build.
- Console Guard restarts after its temporary test window expires.
- Only legally redistributable test content is used.
- RetroArch launches the requested content and core.
- Closing the emulator returns to SilentiumOS.
- No private identifiers appear in screenshots or reports.

## Publishing evidence

Concept mockups are presentation assets, not test evidence. A real proof package must pair sanitized captures with the build commit, device product model, Fire OS version, and a written checklist result—never with a unique serial number.
