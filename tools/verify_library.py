#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

TARGET = os.environ.get("SILENTIUM_TARGET", "fire-tv-hostname.local:5555")
ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "ELLIOT_GAMES" / "validated_library.json"
REPORT = ROOT / "SILENTIUMOS_HEALTH_REPORT.txt"

REMOTE = {
    "NES": "/sdcard/SilentiumOS/Games/NES",
    "SNES": "/sdcard/SilentiumOS/Games/SNES",
    "GameBoy": "/sdcard/SilentiumOS/Games/GameBoy",
    "GBA": "/sdcard/SilentiumOS/Games/GBA",
    "Sega": "/sdcard/SilentiumOS/Games/Sega",
}

EXTENSIONS = {
    "NES": (".nes",),
    "SNES": (".sfc", ".smc"),
    "GameBoy": (".gb", ".gbc"),
    "GBA": (".gba",),
    "Sega": (".bin", ".gen", ".md", ".sms"),
}

def find_adb() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    candidates = []
    if local:
        candidates.append(
            Path(local)
            / "Android"
            / "Sdk"
            / "platform-tools"
            / "adb.exe"
        )
    found = shutil.which("adb")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("ADB was not found.")

def run(command: list[str], timeout: int = 45):
    try:
        return subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            124,
            stdout="TIMEOUT",
        )

def main() -> int:
    lines = [
        "SILENTIUMOS QUICK LIBRARY CHECK",
        "=" * 45,
    ]

    try:
        if not MANIFEST.exists():
            raise RuntimeError(
                "Local validated-library manifest is missing."
            )

        data = json.loads(
            MANIFEST.read_text(encoding="utf-8")
        )
        expected = int(data.get("validated_games", 0))

        adb = find_adb()
        run([str(adb), "connect", TARGET], timeout=25)

        actual = 0
        for system, remote in REMOTE.items():
            result = run(
                [
                    str(adb),
                    "-s",
                    TARGET,
                    "shell",
                    "find",
                    remote,
                    "-maxdepth",
                    "1",
                    "-type",
                    "f",
                ],
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Could not list {system} games."
                )

            count = sum(
                1
                for line in (result.stdout or "").splitlines()
                if Path(line.strip()).suffix.lower()
                in EXTENSIONS[system]
            )
            actual += count
            lines.append(f"{system}: {count}")

        lines.append("")
        lines.append(f"Expected ROM files: {expected}")
        lines.append(f"Installed ROM files: {actual}")

        if actual != expected:
            raise RuntimeError(
                "Installed file count does not match the "
                "hardware-tested manifest."
            )

        lines.append("RESULT: READY")
        REPORT.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        print("\n".join(lines))
        return 0

    except Exception as error:
        lines.append(f"RESULT: ERROR — {error}")
        REPORT.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        print("\n".join(lines))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
