# Architecture

## Application layer

SilentiumOS is an Android application using programmatic Java television layouts. Its main components are:

- `SplashActivity` — branded leanback and Home entry point
- `MainActivity` — controller-first television dashboard
- `GameLibraryActivity` / `GameListActivity` — system and game views
- `GameCatalog` / `GameEntry` — read-only library discovery and launchable item model
- `ParentPinActivity` / `ParentToolsActivity` — protected household configuration area
- `PublicSystemInfoActivity` — public build and privacy facts without device identifiers
- `ConsoleGuardService` — foreground monitoring and dashboard recovery
- `HomeRedirectAccessibilityService` — redirects protected Amazon Home back to SilentiumOS
- `BootReceiver` — starts the dashboard after boot broadcasts
- `LibraryTestModeReceiver` — temporarily suspends guard behavior for controlled emulator testing

## Component boundaries

- Parent, library, dashboard, and system-information activities are not exported.
- `SplashActivity` is exported because it is the leanback launcher and optional Home activity.
- `BootReceiver` accepts only Android boot actions and verifies the received action in code.
- The accessibility service is protected by `android.permission.BIND_ACCESSIBILITY_SERVICE`.
- The guard service and test receiver remain callable from an authorized ADB shell but require the privileged `android.permission.DUMP` permission, which ordinary third-party apps do not hold.
- The application disables Android backup and cleartext application traffic.

## Parent gate

Every build requires a locally supplied four-digit PIN. Gradle validates the input and generates only its SHA-256 digest into `BuildConfig`; source control contains neither a default value nor the production PIN.

The four-digit space is small and remains brute-forceable. This mechanism is a parental navigation gate for a managed household device, not a credential vault.

## RetroArch integration

Games launch through `RetroActivityFuture` with explicit Android intent extras for the ROM, private core, config path, data directory, APK path, IME, and storage locations.

Temporary hardware-test ROMs use deterministic SHA-256 filenames without spaces. This avoids ADB shell argument splitting while preserving readable final dashboard names.

RetroArch, cores, APKs, and ROMs are external runtime dependencies and are not distributed in the repository.

## Library boundary

`GameCatalog` contains the filesystem and filtering rules; Activities only
render catalog snapshots and launch selected entries. The catalog accepts an
injected library root and core marker so its behavior can be tested without an
Android device.

Library traversal is iterative and read-only. It rejects symbolic links,
requires canonical paths to remain under the selected system directory, and
caps directory depth, directories visited, games returned, marker size, and
marker line count. A truncated snapshot is surfaced in the game-list footer.

## Trust boundary

SilentiumOS does not modify the Fire TV bootloader. Amazon Home remains a protected system package. Console behavior is enforced at the application and accessibility layers on an owned, managed device.
