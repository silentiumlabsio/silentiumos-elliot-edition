# Privacy model

SilentiumOS is designed as a local television launcher. The public Android source does not include analytics SDKs, advertising SDKs, account systems, telemetry endpoints, crash-reporting services, cloud databases, API keys, or embedded credentials.

## Local data

The launcher may read locally stored game-library metadata and files that the device owner places on the Fire TV. Those files remain under the owner's control and are not included in this repository.

The public tools may create temporary local reports, work folders, downloaded homebrew staging files, or ADB state files while testing. `.gitignore` excludes those outputs. Operators should remove them after testing and must not upload them to issues or pull requests.

## Network activity

The Android launcher itself has no declared Internet permission and disallows cleartext application traffic.

The in-app About & Privacy screen uses fixed public project facts and the public
application version. It does not query hardware identifiers, account state,
network addresses, Wi-Fi details, installed packages, or the game library.

Separate developer tools can use:

- ADB to communicate with a target explicitly supplied through `SILENTIUM_TARGET`.
- HTTPS to retrieve allowlisted public homebrew source archives.
- HTTPS to retrieve RetroArch cores from the official libretro buildbot for local installation.

These tools do not contain authentication tokens. Operators remain responsible for reviewing third-party licenses and downloaded content before use.

## Data that must never be published

- Private IP addresses or hostnames tied to a household
- Device serial numbers, MAC addresses, advertising IDs, or account IDs
- Wi-Fi names, Bluetooth names, notifications, or household names
- ADB authorization material
- Production parent PINs or PIN hashes from production builds
- Signing keys, certificates, passwords, tokens, or environment files
- Local filesystem paths containing usernames
- ROMs, BIOS files, APKs, emulator cores, or private game-library manifests
- Logs, screenshots, or reports containing any of the above

## Screenshots

Repository concept images contain invented interface state only. Real device captures require manual review under the [screenshot policy](SCREENSHOTS.md).
