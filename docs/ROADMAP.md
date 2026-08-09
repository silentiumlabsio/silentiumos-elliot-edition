# Roadmap

This roadmap describes likely public-safe improvements. It is not a release promise.

## Near term

- Capture clean, sanitized on-device dashboard proof.
- Add Gradle Wrapper files so builds do not depend on a separately installed Gradle command.
- Add Android lint and instrumentation-test configuration beyond the current pure Java contract suite.
- Verify the privileged ADB control permission on the target Fire OS build.
- Add a user-visible setup screen for initial PIN provisioning.
- Replace build-time PIN configuration with Android Keystore-backed local provisioning.
- Add focused-state accessibility labels and color-contrast review.

## Library experience

- Add deterministic cover placeholders for homebrew without artwork.
- Add library search, favorites, and recently played views.
- Add per-system empty states and troubleshooting guidance.
- Expand validation reports without including local paths or private content names.

## Reliability

- Add bounded service-restart backoff.
- Add clearer recovery when RetroArch or a core is unavailable.
- Test cold boot, locked boot, app update, storage removal, and controller disconnect cases.
- Add a documented uninstall and Fire OS restoration procedure.

## Public presentation

- Replace concept UI images with sanitized device captures when available.
- Add a short demonstration video with all device and household metadata removed.
- Publish a versioned compatibility table for tested Fire OS releases.
