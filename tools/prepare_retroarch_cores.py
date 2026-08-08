#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

TARGET = os.environ.get("SILENTIUM_TARGET", "").strip()
PACKAGE = "com.retroarch.ra32"
USER_AGENT = "SilentiumOS-Elliot-Edition/0.7.6"

ROOT = Path(__file__).resolve().parent
CORE_DIR = ROOT / "RETROARCH_CORES"
REMOTE_STAGING = "/sdcard/Download/SilentiumOS_Cores"
REMOTE_MARKER = "/sdcard/SilentiumOS/System/cores.ready"

REQUIRED_CORES = [
    "fceumm_libretro_android.so",
    "snes9x2010_libretro_android.so",
    "gambatte_libretro_android.so",
    "mgba_libretro_android.so",
    "genesis_plus_gx_libretro_android.so",
]

OPTIONAL_CORES = [
    "2048_libretro_android.so",
    "mrboom_libretro_android.so",
    "craft_libretro_android.so",
]

def find_adb() -> Path:
    candidates = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(
            Path(local) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        )
    found = shutil.which("adb")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("ADB was not found.")

def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(f'"{part}"' if " " in part else part for part in command))
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )

def adb_output(adb: Path, *arguments: str) -> str:
    result = run([str(adb), "-s", TARGET, *arguments], capture=True)
    return (result.stdout or "").strip()

def connect(adb: Path) -> None:
    if not TARGET:
        raise RuntimeError(
            "Set SILENTIUM_TARGET to an authorized ADB host before running."
        )
    run([str(adb), "connect", TARGET])
    if adb_output(adb, "get-state") != "device":
        raise RuntimeError("Fire TV is not connected or authorized.")

def verify_run_as(adb: Path) -> None:
    identity = adb_output(adb, "shell", "run-as", PACKAGE, "id")
    if "uid=" not in identity:
        raise RuntimeError(
            "RetroArch is not the Silentium debuggable RA32 engine. "
            "Run INSTALL_RETROARCH_ENGINE.py first."
        )

def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 1000:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists():
        partial.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        with partial.open("wb") as output:
            shutil.copyfileobj(response, output)
    partial.replace(destination)

def prepare_core(core: str) -> Path:
    CORE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = CORE_DIR / (core + ".zip")
    core_path = CORE_DIR / core
    url = (
        "https://buildbot.libretro.com/nightly/android/"
        "latest/armeabi-v7a/" + core + ".zip"
    )

    download(url, archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(core)]
        if not matches:
            raise RuntimeError(f"{core} was not found in its archive.")
        with archive.open(matches[0]) as source:
            with core_path.open("wb") as output:
                shutil.copyfileobj(source, output)

    with core_path.open("rb") as source:
        header = source.read(4)

    if header != b"\x7fELF":
        raise RuntimeError(f"{core} is not a valid ELF core library.")
    if core_path.stat().st_size < 8_000:
        raise RuntimeError(f"{core} appears incomplete.")

    return core_path

def install_core(adb: Path, local_core: Path) -> tuple[bool, str]:
    core = local_core.name
    remote = REMOTE_STAGING + "/" + core

    push = run([str(adb), "-s", TARGET, "push", str(local_core), remote])
    if push.returncode != 0:
        return False, "staging upload failed"

    shell_command = (
        f"cat '{remote}' | "
        f"run-as {PACKAGE} sh -c "
        f"'cat > cores/{core} && chmod 700 cores/{core}'"
    )
    copied = run(
        [str(adb), "-s", TARGET, "shell", shell_command],
        capture=True,
    )
    if copied.returncode != 0:
        return False, "private core copy failed: " + (copied.stdout or "").strip()

    listing = adb_output(
        adb, "shell", "run-as", PACKAGE, "ls", "-l", f"cores/{core}"
    )
    if core not in listing:
        return False, "private core file was not found"

    size_text = adb_output(
        adb, "shell", "run-as", PACKAGE,
        "stat", "-c", "%s", f"cores/{core}"
    )
    try:
        remote_size = int(size_text.strip())
    except ValueError:
        remote_size = -1

    local_size = local_core.stat().st_size
    if remote_size != local_size:
        return False, f"private core size mismatch ({remote_size} != {local_size})"

    return True, f"{remote_size} bytes verified"

def main() -> int:
    try:
        adb = find_adb()
        connect(adb)
        verify_run_as(adb)

        run([
            str(adb), "-s", TARGET, "shell",
            "mkdir", "-p", REMOTE_STAGING, "/sdcard/SilentiumOS/System",
        ])
        run([
            str(adb), "-s", TARGET, "shell",
            "run-as", PACKAGE, "mkdir", "-p", "cores",
        ])

        installed = []
        failed_required = []
        failed_optional = []

        for core in REQUIRED_CORES + OPTIONAL_CORES:
            print()
            print(f"Preparing {core}...")
            try:
                local_core = prepare_core(core)
                success, detail = install_core(adb, local_core)
            except Exception as error:
                success = False
                detail = str(error)

            if success:
                installed.append(core)
                print(f"READY: {core} — {detail}")
            elif core in REQUIRED_CORES:
                failed_required.append(core)
                print(f"FAILED REQUIRED: {core} — {detail}")
            else:
                failed_optional.append(core)
                print(f"SKIPPED OPTIONAL: {core} — {detail}")

        marker = ROOT / "cores.ready"
        marker.write_text(
            "\n".join(installed) + ("\n" if installed else ""),
            encoding="ascii",
        )
        run([
            str(adb), "-s", TARGET, "push",
            str(marker), REMOTE_MARKER,
        ])

        print()
        print(f"Installed and verified cores: {len(installed)}")

        if failed_optional:
            print("Optional cores unavailable:")
            for core in failed_optional:
                print(f"  {core}")

        if failed_required:
            raise RuntimeError(
                "Required cores failed: " + ", ".join(failed_required)
            )

        print("All required cores are ready.")
        return 0
    except Exception as error:
        print()
        print(f"ERROR: {error}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
