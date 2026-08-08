#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

TARGET = os.environ.get("SILENTIUM_TARGET", "").strip()
PACKAGE = "com.silentiumlabs.silentiumos"
HOME_COMPONENT = f"{PACKAGE}/.SplashActivity"
GUARD_COMPONENT = f"{PACKAGE}/.ConsoleGuardService"
ACCESSIBILITY_COMPONENT = (
    "com.silentiumlabs.silentiumos/"
    "com.silentiumlabs.silentiumos."
    "HomeRedirectAccessibilityService"
)
ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "CONSOLE_MODE_STATE.txt"

def find_adb() -> Path:
    candidates = []
    local = os.environ.get("LOCALAPPDATA")
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

def run(
        command: list[str],
        *,
        capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(
        f'"{part}"' if " " in part else part
        for part in command
    ))
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

def connect(adb: Path) -> None:
    if not TARGET:
        raise RuntimeError(
            "Set SILENTIUM_TARGET to an authorized ADB host before running."
        )
    run([str(adb), "connect", TARGET])
    if adb_output(adb, "get-state") != "device":
        raise RuntimeError(
            "Fire TV is not connected or authorized."
        )

def package_exists(adb: Path, package: str) -> bool:
    return "package:" in adb_output(
        adb,
        "shell",
        "pm",
        "path",
        package,
    )

def top_package(adb: Path) -> str:
    activity = adb_output(
        adb,
        "shell",
        "dumpsys",
        "activity",
        "activities",
    )

    for pattern in (
        r"mResumedActivity:.*?\s([A-Za-z0-9._]+)/",
        r"topResumedActivity=.*?\s([A-Za-z0-9._]+)/",
    ):
        match = re.search(pattern, activity)
        if match:
            return match.group(1)

    window = adb_output(
        adb,
        "shell",
        "dumpsys",
        "window",
        "windows",
    )
    match = re.search(
        r"mCurrentFocus=.*?\s([A-Za-z0-9._]+)/",
        window,
    )
    return match.group(1) if match else "unknown"

def enabled_accessibility_services(adb: Path) -> list[str]:
    raw = adb_output(
        adb,
        "shell",
        "settings",
        "get",
        "secure",
        "enabled_accessibility_services",
    )

    if raw.lower() in ("", "null", "none"):
        return []

    return [
        service.strip()
        for service in raw.split(":")
        if service.strip()
    ]

def enable_accessibility_redirect(adb: Path) -> None:
    services = enabled_accessibility_services(adb)

    normalized = {
        service.lower(): service
        for service in services
    }
    if ACCESSIBILITY_COMPONENT.lower() not in normalized:
        services.append(ACCESSIBILITY_COMPONENT)

    joined = ":".join(services)

    result = run(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "settings",
            "put",
            "secure",
            "enabled_accessibility_services",
            joined,
        ],
        capture=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Fire OS rejected the accessibility-service setting."
        )

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
            "1",
        ]
    )

    time.sleep(3)

    verify = enabled_accessibility_services(adb)
    if not any(
            service.lower()
            == ACCESSIBILITY_COMPONENT.lower()
            for service in verify):
        raise RuntimeError(
            "SilentiumOS Home Redirect was not enabled."
        )

def configure_app(adb: Path) -> None:
    commands = [
        (
            "shell", "appops", "set",
            PACKAGE, "GET_USAGE_STATS", "allow",
        ),
        (
            "shell", "appops", "set",
            PACKAGE, "RUN_IN_BACKGROUND", "allow",
        ),
        (
            "shell", "appops", "set",
            PACKAGE, "RUN_ANY_IN_BACKGROUND", "allow",
        ),
        (
            "shell", "dumpsys", "deviceidle",
            "whitelist", f"+{PACKAGE}",
        ),
        (
            "shell", "settings", "put",
            "global", "window_animation_scale", "0",
        ),
        (
            "shell", "settings", "put",
            "global", "transition_animation_scale", "0",
        ),
        (
            "shell", "settings", "put",
            "global", "animator_duration_scale", "0",
        ),
        (
            "shell", "cmd", "package",
            "set-home-activity",
            "--user", "0", HOME_COMPONENT,
        ),
    ]

    for command in commands:
        run([str(adb), "-s", TARGET, *command])

def start_services_and_dashboard(adb: Path) -> None:
    guard = run(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start-foreground-service",
            "-n",
            GUARD_COMPONENT,
        ],
        capture=True,
    )
    print(guard.stdout or "")

    if (
        guard.returncode != 0
        or "Requires permission not exported" in (
            guard.stdout or "")
    ):
        raise RuntimeError(
            "SilentiumOS Console Guard could not start."
        )

    start = run(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start",
            "-W",
            "-n",
            HOME_COMPONENT,
        ],
        capture=True,
    )
    print(start.stdout or "")

    if start.returncode != 0:
        raise RuntimeError(
            "SilentiumOS dashboard could not start."
        )

def verify_home_redirect(adb: Path) -> bool:
    for attempt in range(1, 4):
        print(
            f"Testing Fire TV Home redirect "
            f"(attempt {attempt}/3)..."
        )
        run(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "input",
                "keyevent",
                "HOME",
            ]
        )

        # Amazon Home may appear first; accessibility should take it back.
        time.sleep(3)
        foreground = top_package(adb)
        print(
            "Foreground package after redirect: "
            f"{foreground}"
        )

        if foreground == PACKAGE:
            return True

        run(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "am",
                "start",
                "-n",
                HOME_COMPONENT,
            ]
        )
        time.sleep(2)

    return False

def main() -> int:
    try:
        adb = find_adb()
        connect(adb)

        if not package_exists(adb, PACKAGE):
            raise RuntimeError("SilentiumOS is not installed.")

        configure_app(adb)
        enable_accessibility_redirect(adb)
        start_services_and_dashboard(adb)

        if not verify_home_redirect(adb):
            raise RuntimeError(
                "The accessibility redirect was enabled, "
                "but Fire OS still kept Amazon Home in front."
            )

        STATE_FILE.write_text(
            "SilentiumOS Elliot Edition console mode\n"
            "mode=accessibility_home_redirect\n"
            f"home={HOME_COMPONENT}\n"
            f"accessibility={ACCESSIBILITY_COMPONENT}\n"
            "amazon_launcher=protected_and_retained\n",
            encoding="utf-8",
        )

        print()
        print("===================================================")
        print("SILENTIUMOS ACCESSIBILITY CONSOLE MODE ENABLED")
        print("===================================================")
        print(
            "Amazon Home remains protected underneath Fire OS."
        )
        print(
            "Pressing Home now redirects back to SilentiumOS."
        )
        print(
            "A brief Amazon Home flash may be visible."
        )
        return 0

    except Exception as error:
        print()
        print(f"ERROR: {error}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
