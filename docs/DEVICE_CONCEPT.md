# Device concept and compatibility

## What the repository image represents

`docs/assets/silentiumos-elliot-hero.png` is an original proof-of-concept visualization of the intended living-room setup: an HDMI streaming stick and remote in front of a television running the SilentiumOS dashboard.

It is deliberately **not** a copied retailer photograph. The render omits Amazon branding, app-service logos, serial labels, network information, accounts, and other device-specific data. It should be described as a concept visualization, not as photographic evidence of an installed build.

## Supported hardware baseline

The public Android source is aligned with the **Fire TV Stick HD with Alexa Voice Remote (2024)**.

| Device | Public platform data | SilentiumOS status |
| --- | --- | --- |
| Fire TV Stick HD with Alexa Voice Remote (2024) | Fire OS 7, Android 9 / API 28, 32-bit ABI, Full HD class | Intended target for this snapshot |
| Fire TV Stick HD (2026) | Vega OS 1.1, non-Android application platform | Not supported by this Android project as-is |

Amazon maintains the authoritative specifications in its [Fire TV streaming-media-player device table](https://developer.amazon.com/docs/device-specs/device-specifications-fire-tv-streaming-media-player.html?v=ftvstickhd.md).

Public model names and platform identifiers above are product specifications, not unique device serial numbers.

## What would count as real device proof

A future on-device proof package should include only sanitized captures of:

1. The dashboard after boot.
2. Controller focus moving across system tiles.
3. Parent tools opening after local PIN entry, with the keypad value hidden.
4. A legally redistributable homebrew title launching through RetroArch.
5. Automatic return to SilentiumOS after the emulator closes.

Before publishing, crop or blur all status bars, notifications, ADB windows, local paths, account names, Wi-Fi names, IP addresses, MAC addresses, device names, and serial numbers.

## Independence statement

SilentiumOS is an independent source-available project. Amazon, Fire TV, Fire OS, and Alexa are trademarks of their respective owner. The hardware reference and compatibility notes do not imply sponsorship, certification, or endorsement.
