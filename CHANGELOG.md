# Changelog

## 0.7.7-public-source

- Extracted game discovery from `GameListActivity` into a pure Java catalog.
- Added canonical containment checks and symbolic-link rejection.
- Capped library depth, directory count, game count, and core-marker input.
- Added dependency-free Java catalog contract tests and CI execution.
- Added a development guide, architecture decisions, and release checklist.

## 0.7.6-public-source

- Added original Elliot Edition device, banner, and dashboard concept visuals.
- Added device compatibility, security audit, privacy, testing, brand, and roadmap documentation.
- Removed the built-in public parent PIN; builds now require explicit local configuration.
- Replaced the generated plaintext PIN constant with a SHA-256 digest.
- Restricted exported ADB-control components with `android.permission.DUMP`.
- Disabled cleartext application traffic.
- Required explicit local ADB targets in public utilities.
- Added automated public-release safety checks and contribution templates.

## 0.7.5-public-source

- Initial public source release of SilentiumOS — Elliot Edition.
