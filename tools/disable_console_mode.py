#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

TARGET = os.environ.get("SILENTIUM_TARGET", "fire-tv-hostname.local:5555")
PACKAGE = "com.silentiumlabs.silentiumos"
ACCESSIBILITY_COMPONENT = (
    "com.silentiumlabs.silentiumos/"
    "com.silentiumlabs.silentiumos."
    "HomeRedirectAccessibilityService"
)

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

def run(command: list[str], capture: bool = False):
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )

def adb_output(adb: Path, *arguments: str) -> str:
    result = run(
        [str(adb), "-s", TARGET, *arguments],
        capture=True,
    )
    return (result.stdout or "").strip()

def main() -> int:
    try:
        adb = find_adb()
        run([str(adb), "connect", TARGET])

        raw = adb_output(
            adb,
            "shell",
            "settings",
            "get",
            "secure",
            "enabled_accessibility_services",
        )

        services = []
        if raw.lower() not in ("", "null", "none"):
            services = [
                value.strip()
                for value in raw.split(":")
                if value.strip()
            ]

        remaining = [
            service
            for service in services
            if service.lower()
            != ACCESSIBILITY_COMPONENT.lower()
        ]

        run(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "settings",
                "put",
                "secure",
                "enabled_accessibility_services",
                ":".join(remaining),
            ]
        )

        if not remaining:
            run(
                [
                    str(adb),
                    "-s",
                    TARGET,
                    "shell",
                    "settings",
                    "put",
                    "secure",
                    "accessibility_enabled",
                    "0",
                ]
            )

        run(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "am",
                "force-stop",
                PACKAGE,
            ]
        )
        run(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "monkey",
                "-p",
                "com.amazon.tv.launcher",
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ]
        )

        print(
            "SilentiumOS Home Redirect disabled. "
            "Amazon Home restored."
        )
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
