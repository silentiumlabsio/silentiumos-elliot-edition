#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = {
    # Xbox View is RetroPad Select (6); Xbox Menu is RetroPad Start (7).
    "input_enable_hotkey_btn": '"6"',
    "input_exit_emulator_btn": '"7"',
    "quit_press_twice": '"false"',
    "confirm_quit": '"false"',
    "menu_show_quit_retroarch": '"true"',
    "config_save_on_exit": '"false"',
    "savestate_auto_save": '"true"',
    "savestate_auto_load": '"true"',
    "autosave_interval": '"10"',
    "video_driver": '"gl"',
    "video_threaded": '"true"',
    "audio_driver": '"opensl"',
    "input_autodetect_enable": '"true"',
    "all_users_control_menu": '"true"',
    "pause_nonactive": '"false"',
    "menu_pause_libretro": '"true"',
    "menu_driver": '"rgui"',
    "log_verbosity": '"true"',
    "log_to_file": '"true"',
}

def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: PATCH_RETROARCH_RETURN.py <retroarch.cfg>")
        return 2

    path = Path(sys.argv[1])
    lines = (
        path.read_text(encoding="utf-8", errors="replace").splitlines()
        if path.exists()
        else []
    )

    wanted = set(SETTINGS)
    output = []

    for line in lines:
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
        if key in wanted:
            continue
        output.append(line)

    output.extend([
        "",
        "# SilentiumOS Elliot Edition plug-and-play configuration",
        "# Hold Xbox VIEW + MENU together to exit directly to SilentiumOS.",
    ])

    for key, value in SETTINGS.items():
        output.append(f"{key} = {value}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(output).rstrip() + "\n",
        encoding="utf-8",
    )

    print("RetroArch configured for Fire TV:")
    print("  GL video driver")
    print("  Xbox View + Menu exits")
    print("  Automatic save/load state")
    print("  Verbose file logging")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
