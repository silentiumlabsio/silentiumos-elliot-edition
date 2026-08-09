# Development guide

## Supported toolchain

- Android Studio with Android SDK 36
- JDK 17 or newer for the dependency-free Java contract suite
- Gradle 8.13 for command-line Android builds
- Python 3.10 or newer for public tools and release auditing
- PowerShell 7 for the cross-platform CI commands

The Android application remains Java 8 source-compatible because the target is
the Fire OS 7 / Android 9 device class. Development tools may use newer language
features when they do not enter the Android application artifact.

## Local checks

Run the pure Java catalog tests without Android or third-party test libraries:

```powershell
$env:JAVA_HOME = "path-to-a-local-jdk"
./scripts/test-java.ps1
```

Run both public-source audits:

```powershell
./scripts/audit-public-release.ps1
python tools/audit_public_release.py .
python -m unittest discover -s tests -v
```

Build with a private throwaway PIN supplied only in the current shell:

```powershell
$securePin = Read-Host "Temporary four-digit PIN" -AsSecureString
$env:SILENTIUM_PARENT_PIN = (
    New-Object System.Net.NetworkCredential("", $securePin)
).Password
gradle :app:assembleDebug
Remove-Item Env:SILENTIUM_PARENT_PIN
Remove-Variable securePin
```

Delete or move generated build outputs before running the release audits. APKs,
reports, caches, local properties, and generated metadata are never release
inputs.

## Source boundaries

- Activities render state and handle television navigation.
- Pure Java classes own library discovery, filtering, and deterministic naming.
- Android services own console-guard behavior and external-app windows.
- Developer tools require an explicitly supplied target and write only ignored local outputs.
- Documentation and concept images must contain invented or sanitized state.

No application component should add analytics, advertising, account tracking,
remote configuration, crash-reporting, or an Internet permission without an
explicit public design review.

## Java conventions

- Prefer immutable value objects and dependency injection for filesystem paths.
- Keep I/O bounded by size, count, depth, or timeout.
- Treat external files, intent extras, and marker contents as untrusted input.
- Do not log file paths, network details, account state, or device identifiers.
- Keep Android framework dependencies out of domain classes where practical.
- Add a contract test for every new filtering or traversal rule.

## Review checklist

1. Confirm the change belongs in the public repository.
2. Review new permissions and exported Android components.
3. Run Java, Python, and public-release checks.
4. Build with temporary local configuration.
5. Inspect the exact staged file list and diff.
6. Confirm the public manifest matches the working tree.
7. Verify the GitHub Public safety workflow after pushing.
