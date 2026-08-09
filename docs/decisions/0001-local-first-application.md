# 0001: Keep the Android application local-first

- Status: accepted
- Date: 2026-08-08

## Context

SilentiumOS is a household television launcher. Its core functions—navigation,
parent gating, library browsing, and game launching—do not require a project
account or remote service. Networked application features would expand the
privacy, reliability, and credential-management surface.

## Decision

The Android application remains local-first and does not request the Internet
permission. It does not include analytics, advertising, telemetry, account,
remote-configuration, or crash-reporting SDKs. Public developer tools may use
HTTPS for allowlisted sources and ADB for a target explicitly supplied by the
operator.

## Consequences

- Core launcher operation does not depend on service availability.
- Device and household state stay outside the public repository.
- A future networked feature requires a new decision record, privacy review,
  permission review, and a public explanation of stored or transmitted data.
