# Security policy

## Supported snapshot

Security reports are accepted for the latest public source snapshot on `main`.

## Private reporting

Email **silentiumlabsio@gmail.com** with:

- A clear description of the issue
- The affected file or component
- Reproduction steps using sanitized data
- Expected impact
- Suggested remediation, when available

Do not publish a proof containing production PINs, PIN hashes from production builds, credentials, private IP addresses, household hostnames, device serials, MAC addresses, account data, signing material, private logs, APKs, cores, or non-public game files.

## Public repository rules

This repository intentionally excludes:

- Production credentials, PINs, and environment files
- Signing keys and certificates
- Private network addresses and household hostnames
- Device and account identifiers
- ROMs, BIOS files, emulator cores, APKs, and AABs
- Runtime logs, caches, reports, and private captures

Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\audit-public-release.ps1` before publishing a change. See [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) for the snapshot controls and limitations.

## Security boundaries

- The parent PIN is a household navigation control, not a high-assurance secret store.
- ADB tooling assumes an owned, authorized device on a trusted development network.
- Accessibility and usage-access capabilities are powerful Android permissions and should be enabled only for the intended managed-device setup.
- SilentiumOS does not replace Fire OS security, the bootloader, or Amazon's protected launcher.
