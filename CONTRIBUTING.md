# Contributing

This is a public source-available portfolio repository maintained by Silentium Labs.

Before opening an issue or pull request:

1. Read `SECURITY.md`, `docs/PRIVACY.md`, and `docs/LEGAL_LIBRARY.md`.
2. Run the PowerShell and Python public audits described in `docs/DEVELOPMENT.md`.
3. Do not include commercial ROMs, BIOS files, cores, APKs, AABs, archives, or copyrighted game assets.
4. Remove private addresses, household hostnames, device IDs, accounts, usernames, credentials, production PIN material, signing files, logs, and local paths.
5. Keep platform claims accurate: this Android source targets the 2024 Fire OS 7 device class, not the 2026 Vega OS model.
6. Explain how the change was tested on Android TV or Fire TV hardware.
7. Keep child-facing navigation and parent-tool protections intact.
8. Label generated interface or device artwork as a concept until it is replaced by sanitized physical-device proof.

For Java changes, run `scripts/test-java.ps1` and an Android debug build with a
throwaway local PIN. Keep filesystem work in `GameCatalog` or another testable
data component rather than adding it directly to an Activity.

Submission does not grant a license to the rest of the project. Any accepted contribution must be original or legally redistributable.
