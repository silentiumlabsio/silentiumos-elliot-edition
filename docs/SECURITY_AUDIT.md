# Public security audit

## Snapshot

This checklist describes the public-release review performed on the repository snapshot dated 2026-08-08. It is a release-hygiene audit, not a penetration test or security certification.

## Controls in this snapshot

- No production parent PIN is stored in source or documentation.
- Builds fail unless `SILENTIUM_PARENT_PIN` is supplied locally.
- Only a SHA-256 digest of the configured PIN is generated into `BuildConfig`.
- The Console Guard service and library-test receiver require `android.permission.DUMP`, limiting external invocation to privileged/system callers such as an authorized ADB shell.
- The library-test window is capped at six hours.
- Cleartext application network traffic is disabled in the Android manifest.
- Android backup is disabled.
- Parent, library, and dashboard activities are not exported.
- The accessibility service is protected by `android.permission.BIND_ACCESSIBILITY_SERVICE`.
- Public utilities require `SILENTIUM_TARGET`; no device address is built into the repository.
- Release automation rejects prohibited binary formats and sensitive directory names.

## Data and artifact checks

The public audit checks for:

- ROM, BIOS, emulator-core, APK, AAB, archive, and signing-key extensions
- Runtime logs, caches, reports, captures, and device-state folders
- RFC 1918 private IPv4 addresses
- MAC-address-shaped values
- Local Windows, macOS, and Linux user paths
- Private-key headers
- Common GitHub and AWS credential formats
- Hardcoded four-digit parent PIN assignments
- Common device-serial assignments

## Important limitation

A four-digit PIN has only 10,000 possible values. Hashing prevents the plaintext value from appearing directly in a built APK, but it does not turn the parental gate into high-assurance cryptography. The PIN protects household navigation; it should not protect financial, identity, or enterprise secrets.

## Release procedure

1. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\audit-public-release.ps1`.
2. Review the complete staged filename list.
3. Run Python syntax checks for every tool.
4. Build with a throwaway local PIN and a clean Android SDK environment.
5. Confirm that generated APKs, build folders, reports, and logs remain untracked.
6. Inspect any new screenshots manually.
7. Review the final commit diff before pushing.

## Reporting

Report security concerns privately to **silentiumlabsio@gmail.com**. Do not include production PINs, credentials, private network information, copyrighted ROMs, or personal device data in a public issue.
