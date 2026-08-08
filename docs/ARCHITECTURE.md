# Architecture

## Application layer

SilentiumOS is an Android application using programmatic Java television layouts. Its main components are:

- `SplashActivity` — branded entry point and boot transition
- `MainActivity` — television dashboard
- `GameLibraryActivity` / `GameListActivity` — system and game views
- `ParentPinActivity` / `ParentToolsActivity` — protected configuration area
- `ConsoleGuardService` — foreground monitoring and dashboard recovery
- `HomeRedirectAccessibilityService` — redirects protected Amazon Home back to SilentiumOS
- `BootReceiver` — starts the dashboard after device boot
- `LibraryTestModeReceiver` — temporarily suspends guard behavior for controlled emulator testing

## RetroArch integration

Games launch through `RetroActivityFuture` with explicit Android intent extras for the ROM, private core, config path, data directory, APK path, IME, and storage locations.

Temporary hardware-test ROMs use deterministic SHA-256 filenames without spaces. This avoids ADB shell argument splitting while preserving readable final dashboard names.

## Trust boundary

SilentiumOS does not modify the Fire TV bootloader. Amazon Home remains a protected system package. Console behavior is enforced at the application/accessibility layer.
