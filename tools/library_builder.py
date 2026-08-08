#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

TARGET = os.environ.get("SILENTIUM_TARGET", "fire-tv-hostname.local:5555")
SILENTIUM_PACKAGE = "com.silentiumlabs.silentiumos"
SILENTIUM_SPLASH = (
    "com.silentiumlabs.silentiumos/.SplashActivity"
)
RETROARCH_PACKAGE = "com.retroarch.ra32"
RETROARCH_ACTIVITY = (
    "com.retroarch.ra32/"
    "com.retroarch.browser.retroactivity."
    "RetroActivityFuture"
)

ROOT = Path(__file__).resolve().parent
CACHE_ROOT = ROOT / "LEGAL_LIBRARY_SOURCE_CACHE"
WORK_ROOT = ROOT / "LARGE_LIBRARY_WORK"
EXISTING_BACKUP = ROOT / "GAME_LIBRARY_BACKUP_BEFORE_0.7"
PASSED_ROOT = ROOT / "ELLIOT_GAMES"
FAILED_ROOT = ROOT / "GAME_TEST_FAILURES"
SCREENSHOT_ROOT = FAILED_ROOT / "screenshots"
REPORT = ROOT / "ELLIOT_LIBRARY_TEST_REPORT.txt"
MANIFEST = PASSED_ROOT / "validated_library.json"
CREDITS = PASSED_ROOT / "VALIDATED_LIBRARY_CREDITS.txt"

REMOTE_ROOT = "/sdcard/SilentiumOS/Games"
REMOTE_TEST_ROOT = "/sdcard/SilentiumOS/LibraryTest"
REMOTE_CORES_MARKER = "/sdcard/SilentiumOS/System/cores.ready"

SYSTEMS = {
    "NES": {
        "extensions": (".nes",),
        "core": "fceumm_libretro_android.so",
        "remote": REMOTE_ROOT + "/NES",
        "cap": 110,
    },
    "SNES": {
        "extensions": (".sfc", ".smc"),
        "core": "snes9x2010_libretro_android.so",
        "remote": REMOTE_ROOT + "/SNES",
        "cap": 50,
    },
    "GameBoy": {
        "extensions": (".gb", ".gbc"),
        "core": "gambatte_libretro_android.so",
        "remote": REMOTE_ROOT + "/GameBoy",
        "cap": 90,
    },
    "GBA": {
        "extensions": (".gba",),
        "core": "mgba_libretro_android.so",
        "remote": REMOTE_ROOT + "/GBA",
        "cap": 110,
    },
    "Sega": {
        "extensions": (".bin", ".gen", ".md", ".sms"),
        "core": "genesis_plus_gx_libretro_android.so",
        "remote": REMOTE_ROOT + "/Sega",
        "cap": 150,
    },
}

ARCADE_CORES = {
    "2048": "2048_libretro_android.so",
    "MR. BOOM": "mrboom_libretro_android.so",
    "CRAFT BLOCK WORLD": "craft_libretro_android.so",
}

COLLECTIONS = (
    (
        "RetroBrews NES Collection",
        "https://codeload.github.com/"
        "retrobrews/nes-games/zip/refs/heads/master",
        "NES",
    ),
    (
        "RetroBrews SNES Collection",
        "https://codeload.github.com/"
        "retrobrews/snes-games/zip/refs/heads/master",
        "SNES",
    ),
    (
        "RetroBrews Game Boy Color Collection",
        "https://codeload.github.com/"
        "retrobrews/gbc-games/zip/refs/heads/master",
        "GameBoy",
    ),
    (
        "RetroBrews GBA Collection",
        "https://codeload.github.com/"
        "retrobrews/gba-games/zip/refs/heads/master",
        "GBA",
    ),
    (
        "RetroBrews Mega Drive Collection",
        "https://codeload.github.com/"
        "retrobrews/md-games/zip/refs/heads/master",
        "Sega",
    ),
    (
        "RetroBrews Master System Collection",
        "https://codeload.github.com/"
        "retrobrews/sms-games/zip/refs/heads/master",
        "Sega",
    ),
)

USER_AGENT = "SilentiumOS-Elliot-Edition/0.7.5"

# Elliot's library is intentionally conservative. These terms are checked
# against the ROM filename and the collection's accompanying text metadata.
MATURE_OR_UNSUITABLE_TERMS = (
    "adult",
    "nsfw",
    "erotic",
    "sexual",
    "nude",
    "nudity",
    "porn",
    "hentai",
    "casino",
    "gambling",
    "poker",
    "slot machine",
    "blood",
    "gore",
    "slasher",
    "horror",
    "nightmare",
    "hell",
    "demon",
    "devil",
    "satan",
    "zombie",
    "murder",
    "suicide",
    "drug",
    "cocaine",
    "marijuana",
    "weed",
    "beer",
    "whiskey",
    "vodka",
)

COMMERCIAL_IP_TERMS = (
    "mario",
    "pokemon",
    "pokémon",
    "zelda",
    "sonic",
    "megaman",
    "mega man",
    "metroid",
    "kirby",
    "donkey kong",
    "pac man",
    "pac-man",
    "castlevania",
    "contra",
    "final fantasy",
    "dragon quest",
    "street fighter",
    "mortal kombat",
    "teenage mutant ninja turtles",
    "tmnt",
)

NON_GAME_OR_UNFINISHED_TERMS = (
    "benchmark",
    "bios",
    "bootrom",
    "debug",
    "diagnostic",
    "emulator test",
    "hardware test",
    "music cart",
    "music cartridge",
    "sound test",
    "tech demo",
    "technical demo",
    "tracker",
    "utility",
    "multicart",
    "31 in 1",
    "31in1",
)

LOW_PRIORITY_VARIANT_TERMS = (
    " alpha",
    " beta",
    " demo",
    " prototype",
    " test",
    " web",
    " compat",
    " old",
)

FATAL_LOG_PATTERNS = (
    "failed to load content",
    "failed to open libretro core",
    "failed to load libretro core",
    "core failed to load",
    "content failed to load",
    "could not load content",
    "libretro core failed",
)
MAX_TOTAL_GAMES = 340
MIN_FREE_SPACE_AFTER_INSTALL = 650 * 1024 * 1024
MAX_LIBRARY_BYTES = 700 * 1024 * 1024
TEST_ENGINE_VERSION = "0.7.5-safe-test-path-v1"
RESULT_CACHE = ROOT / "GAME_TEST_RESULTS_0.7.5.jsonl"
RETROARCH_RUNTIME: dict[str, str] = {}


@dataclass
class Candidate:
    title: str
    system: str
    source_name: str
    source_url: str
    local_path: Path
    metadata: str
    sha256: str
    size: int
    quality_score: int
    existing: bool = False


def run_text(
        command: list[str],
        *,
        timeout: int = 60,
        capture: bool = False) -> subprocess.CompletedProcess[str]:
    printable = " ".join(
        f'"{part}"' if " " in part else part
        for part in command
    )
    print("+", printable)
    try:
        return subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(
            command,
            124,
            stdout=(
                (error.stdout or "")
                + f"\nTIMEOUT after {timeout} seconds"
            ),
        )


def run_bytes(
        command: list[str],
        *,
        timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            124,
            stdout=b"",
            stderr=b"TIMEOUT",
        )


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


def adb_output(
        adb: Path,
        *arguments: str,
        timeout: int = 60) -> str:
    result = run_text(
        [str(adb), "-s", TARGET, *arguments],
        timeout=timeout,
        capture=True,
    )
    return (result.stdout or "").strip()


def connect(adb: Path) -> None:
    run_text([str(adb), "connect", TARGET], timeout=30)

    if adb_output(adb, "get-state", timeout=20) != "device":
        raise RuntimeError(
            "Fire TV is not connected or authorized through ADB."
        )


def safe_filename(value: str) -> str:
    value = value.replace("&", " and ")
    value = re.sub(r"[^A-Za-z0-9._() -]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or "Homebrew Game"


def display_title_from_stem(stem: str) -> str:
    value = re.sub(r"[_-]+", " ", stem)
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return "Homebrew Game"

    small_words = {"and", "of", "the", "for", "to", "in"}
    words = []
    for index, word in enumerate(value.split()):
        if word.isupper() or any(char.isdigit() for char in word):
            words.append(word)
        elif index > 0 and word.lower() in small_words:
            words.append(word.lower())
        else:
            words.append(word.capitalize())
    return " ".join(words)


def normalized_title_key(value: str) -> str:
    value = value.lower()
    value = re.sub(
        r"\b(v|ver|version|rev|revision)\s*\d+"
        r"(?:[._-]\d+)*\b",
        " ",
        value,
    )
    value = re.sub(
        r"\b(alpha|beta|demo|prototype|test|web|compat|old)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while True:
            block = source.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def text_is_allowed(filename: str, metadata: str) -> tuple[bool, str]:
    filename_text = (
        filename.replace("_", " ").replace("-", " ")
    ).lower()

    for term in MATURE_OR_UNSUITABLE_TERMS:
        if term in filename_text:
            return False, f"kid-safe filename filter matched '{term}'"

    for term in COMMERCIAL_IP_TERMS:
        if term in filename_text:
            return False, f"commercial-IP filename filter matched '{term}'"

    for term in NON_GAME_OR_UNFINISHED_TERMS:
        if term in filename_text:
            return False, f"non-game filename filter matched '{term}'"

    explicit_metadata_patterns = (
        r"\bnsfw\b",
        r"\badult[- ]only\b",
        r"\b18\+\b",
        r"\bexplicit sexual content\b",
        r"\bcontains nudity\b",
        r"\bpornographic\b",
    )
    metadata_lower = metadata.lower()[:3000]

    for pattern in explicit_metadata_patterns:
        if re.search(pattern, metadata_lower):
            return False, (
                "explicit mature-content metadata matched "
                f"{pattern!r}"
            )

    return True, "allowed"

def bytes_are_not_blank(data: bytes) -> bool:
    if not data:
        return False

    sample = data[: min(len(data), 65536)]
    unique = len(set(sample))
    return unique >= 4 and any(byte != 0 for byte in sample)


def validate_candidate_file(
        path: Path,
        system: str) -> tuple[bool, str]:
    try:
        size = path.stat().st_size
        data = path.read_bytes()
    except OSError as error:
        return False, f"read error: {error}"

    if not bytes_are_not_blank(data):
        return False, "file is empty or nearly blank"

    if system == "NES":
        if size < 16 + 4096 or size > 16 * 1024 * 1024:
            return False, "NES size is outside practical limits"
        if data[:4] != b"NES\x1a":
            return False, "missing iNES header"
        prg_banks = data[4]
        chr_banks = data[5]
        trainer = 512 if (data[6] & 0x04) else 0
        expected = (
            16
            + trainer
            + prg_banks * 16384
            + chr_banks * 8192
        )
        if prg_banks == 0 or size < expected:
            return False, "incomplete iNES payload"
        return True, "valid iNES structure"

    if system == "SNES":
        if size < 16384 or size > 16 * 1024 * 1024:
            return False, "SNES size is outside practical limits"
        copier = 512 if size % 32768 == 512 else 0
        body_size = size - copier
        if body_size < 16384 or body_size % 8192 != 0:
            return False, "SNES image is not ROM-aligned"
        return True, "trusted SNES collection and aligned image"

    if system == "GameBoy":
        if size < 8192 or size > 16 * 1024 * 1024:
            return False, "Game Boy size is outside practical limits"
        return True, "trusted Game Boy collection image"

    if system == "GBA":
        if size < 192 or size > 64 * 1024 * 1024:
            return False, "GBA size is outside practical limits"
        return True, "trusted GBA collection image"

    if system == "Sega":
        if size < 512 or size > 16 * 1024 * 1024:
            return False, "Sega image is outside practical limits"
        return True, (
            "trusted Sega collection image; "
            "final decision comes from the hardware test"
        )

    return False, "unsupported system"


def quality_score(
        title: str,
        filename: str,
        metadata: str,
        existing: bool) -> int:
    score = 100
    combined = (
        title + " " + filename + " " + metadata[:500]
    ).lower()

    if existing:
        score += 25

    for term in LOW_PRIORITY_VARIANT_TERMS:
        if term in " " + combined:
            score -= 30

    if "final" in combined:
        score += 5
    if "full game" in combined:
        score += 8
    if "complete" in combined:
        score += 5

    return score


def download_collection(
        source_name: str,
        source_url: str) -> Path:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    slug = safe_filename(source_name).replace(" ", "_")
    destination = CACHE_ROOT / f"{slug}.zip"

    if destination.exists() and destination.stat().st_size > 1000:
        print(f"Using cached collection: {destination.name}")
        return destination

    reusable_roots: list[Path] = []

    for reusable_root in reusable_roots:
        reusable = reusable_root / destination.name
        if reusable.exists() and reusable.stat().st_size > 1000:
            shutil.copy2(reusable, destination)
            print(
                "Reused previously downloaded collection: "
                f"{reusable}"
            )
            return destination

    partial = destination.with_suffix(".zip.part")
    if partial.exists():
        partial.unlink()

    request = urllib.request.Request(
        source_url,
        headers={"User-Agent": USER_AGENT},
    )

    print(f"Downloading {source_name}...")
    with urllib.request.urlopen(
            request,
            timeout=180) as response:
        with partial.open("wb") as output:
            shutil.copyfileobj(response, output)

    if partial.stat().st_size < 1000:
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            f"{source_name} download was incomplete."
        )

    partial.replace(destination)
    return destination

def adjacent_metadata(path: Path) -> str:
    candidates = [
        path.with_suffix(".txt"),
        path.parent / (path.stem.lower() + ".txt"),
        path.parent / (path.stem.upper() + ".txt"),
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                return candidate.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                pass
    return ""


def collect_from_archive(
        archive: Path,
        source_name: str,
        source_url: str,
        system: str) -> list[Candidate]:
    candidates = []
    extraction = WORK_ROOT / (
        "extract_" + safe_filename(source_name).replace(" ", "_")
    )

    if extraction.exists():
        shutil.rmtree(extraction)
    extraction.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extraction)

    extensions = SYSTEMS[system]["extensions"]

    for path in sorted(extraction.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue

        metadata = adjacent_metadata(path)
        allowed, reason = text_is_allowed(path.name, metadata)
        if not allowed:
            print(f"  SKIP {path.name}: {reason}")
            continue

        valid, validation = validate_candidate_file(path, system)
        if not valid:
            print(f"  REJECT {path.name}: {validation}")
            continue

        title = display_title_from_stem(path.stem)
        candidates.append(
            Candidate(
                title=title,
                system=system,
                source_name=source_name,
                source_url=source_url,
                local_path=path,
                metadata=metadata,
                sha256=hash_file(path),
                size=path.stat().st_size,
                quality_score=quality_score(
                    title,
                    path.name,
                    metadata,
                    False,
                ),
            )
        )

    return candidates


def pull_existing_library(adb: Path) -> list[Candidate]:
    print("\nBacking up and collecting the existing library...")

    if EXISTING_BACKUP.exists():
        shutil.rmtree(EXISTING_BACKUP)
    EXISTING_BACKUP.mkdir(parents=True, exist_ok=True)

    result = run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "pull",
            REMOTE_ROOT + "/.",
            str(EXISTING_BACKUP),
        ],
        timeout=240,
        capture=True,
    )

    print(result.stdout or "")
    existing = []

    for system, config in SYSTEMS.items():
        folder = EXISTING_BACKUP / system
        if not folder.exists():
            continue

        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in config["extensions"]:
                continue

            valid, reason = validate_candidate_file(path, system)
            if not valid:
                print(
                    f"  Existing file rejected: {path.name}: {reason}"
                )
                continue

            title = display_title_from_stem(path.stem)
            existing.append(
                Candidate(
                    title=title,
                    system=system,
                    source_name="Existing SilentiumOS library",
                    source_url="local-existing-library",
                    local_path=path,
                    metadata="Previously installed and now retested.",
                    sha256=hash_file(path),
                    size=path.stat().st_size,
                    quality_score=quality_score(
                        title,
                        path.name,
                        "",
                        True,
                    ),
                    existing=True,
                )
            )

    return existing


def deduplicate_and_limit(
        candidates: list[Candidate]) -> list[Candidate]:
    by_hash: dict[str, Candidate] = {}
    for candidate in candidates:
        current = by_hash.get(candidate.sha256)
        if (
            current is None
            or candidate.quality_score > current.quality_score
        ):
            by_hash[candidate.sha256] = candidate

    by_title: dict[tuple[str, str], Candidate] = {}
    for candidate in by_hash.values():
        key = (
            candidate.system,
            normalized_title_key(candidate.title),
        )
        current = by_title.get(key)
        if current is None:
            by_title[key] = candidate
            continue

        candidate_rank = (
            candidate.quality_score,
            candidate.size,
            candidate.local_path.name.lower(),
        )
        current_rank = (
            current.quality_score,
            current.size,
            current.local_path.name.lower(),
        )

        if candidate_rank > current_rank:
            by_title[key] = candidate

    grouped: dict[str, list[Candidate]] = {
        system: []
        for system in SYSTEMS
    }

    for candidate in by_title.values():
        grouped[candidate.system].append(candidate)

    selected = []
    for system, items in grouped.items():
        items.sort(
            key=lambda item: (
                -item.quality_score,
                item.title.lower(),
            )
        )
        selected.extend(items[: SYSTEMS[system]["cap"]])

    # Interleave systems so no single collection consumes all global slots.
    queues = {
        system: sorted(
            [
                candidate
                for candidate in selected
                if candidate.system == system
            ],
            key=lambda item: (
                -item.quality_score,
                item.title.lower(),
            ),
        )
        for system in SYSTEMS
    }

    ordered = []
    systems = list(SYSTEMS)
    while len(ordered) < MAX_TOTAL_GAMES:
        added = False
        for system in systems:
            queue = queues[system]
            if queue:
                ordered.append(queue.pop(0))
                added = True
                if len(ordered) >= MAX_TOTAL_GAMES:
                    break
        if not added:
            break

    return ordered


def remote_free_bytes(adb: Path) -> int | None:
    output = adb_output(
        adb,
        "shell",
        "df",
        "-k",
        "/sdcard",
        timeout=30,
    )

    lines = [
        line
        for line in output.splitlines()
        if line.strip()
    ]
    if len(lines) < 2:
        return None

    fields = lines[-1].split()
    if len(fields) < 4:
        return None

    try:
        return int(fields[3]) * 1024
    except ValueError:
        return None


def enforce_storage_limit(
        adb: Path,
        candidates: list[Candidate]) -> list[Candidate]:
    available = remote_free_bytes(adb)
    budget = MAX_LIBRARY_BYTES

    if available is not None:
        budget = min(
            budget,
            max(
                30 * 1024 * 1024,
                available - MIN_FREE_SPACE_AFTER_INSTALL,
            ),
        )

    kept = []
    total = 0

    for candidate in candidates:
        if total + candidate.size > budget:
            continue
        kept.append(candidate)
        total += candidate.size

    print(
        f"Library candidate size: "
        f"{total / (1024 * 1024):.1f} MB"
    )
    if available is not None:
        print(
            f"Fire TV free space before testing: "
            f"{available / (1024 * 1024):.1f} MB"
        )

    return kept


def top_package(adb: Path) -> str:
    activity = adb_output(
        adb,
        "shell",
        "dumpsys",
        "activity",
        "activities",
        timeout=30,
    )

    patterns = (
        r"mResumedActivity:.*?\su\d+\s+([A-Za-z0-9._]+)/",
        r"topResumedActivity=.*?\su\d+\s+([A-Za-z0-9._]+)/",
        r"mFocusedActivity:.*?\su\d+\s+([A-Za-z0-9._]+)/",
        r"ResumedActivity:.*?\su\d+\s+([A-Za-z0-9._]+)/",
        r"mResumedActivity:.*?\s([A-Za-z0-9._]+)/",
        r"topResumedActivity=.*?\s([A-Za-z0-9._]+)/",
    )

    for pattern in patterns:
        match = re.search(pattern, activity)
        if match:
            return match.group(1)

    window = adb_output(
        adb,
        "shell",
        "dumpsys",
        "window",
        "windows",
        timeout=30,
    )

    for pattern in (
        r"mCurrentFocus=.*?\s([A-Za-z0-9._]+)/",
        r"mFocusedApp=.*?\s([A-Za-z0-9._]+)/",
    ):
        match = re.search(pattern, window)
        if match:
            return match.group(1)

    return "unknown"

def paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)

    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png_metrics(data: bytes) -> dict[str, float | int]:
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise ValueError("ADB screenshot is not a PNG.")

    offset = len(signature)
    width = height = bit_depth = color_type = None
    interlace = 0
    compressed = bytearray()

    while offset + 8 <= len(data):
        length = struct.unpack(
            ">I",
            data[offset:offset + 4],
        )[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                _compression,
                _filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if (
        width is None
        or height is None
        or bit_depth != 8
        or interlace != 0
    ):
        raise ValueError(
            "Unsupported screenshot PNG format."
        )

    channels_by_type = {
        0: 1,
        2: 3,
        4: 2,
        6: 4,
    }
    channels = channels_by_type.get(color_type)
    if channels is None:
        raise ValueError(
            f"Unsupported PNG color type {color_type}."
        )

    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    expected = height * (stride + 1)
    if len(raw) < expected:
        raise ValueError("Screenshot PNG data is incomplete.")

    rows = []
    previous = bytearray(stride)
    position = 0

    for _row_index in range(height):
        filter_type = raw[position]
        position += 1
        encoded = raw[position:position + stride]
        position += stride
        decoded = bytearray(stride)

        for index, value in enumerate(encoded):
            left = decoded[index - channels] if index >= channels else 0
            up = previous[index]
            up_left = (
                previous[index - channels]
                if index >= channels
                else 0
            )

            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 0xFF
            elif filter_type == 2:
                result = (value + up) & 0xFF
            elif filter_type == 3:
                result = (
                    value + ((left + up) // 2)
                ) & 0xFF
            elif filter_type == 4:
                result = (
                    value
                    + paeth_predictor(left, up, up_left)
                ) & 0xFF
            else:
                raise ValueError(
                    f"Unsupported PNG filter {filter_type}."
                )

            decoded[index] = result

        rows.append(decoded)
        previous = decoded

    total_pixels = width * height
    target_samples = 45000
    step = max(
        1,
        int(math.sqrt(total_pixels / target_samples)),
    )

    luminances = []
    non_black = 0
    quantized_colors = set()

    for y in range(0, height, step):
        row = rows[y]
        for x in range(0, width, step):
            index = x * channels

            if color_type in (0, 4):
                red = green = blue = row[index]
            else:
                red = row[index]
                green = row[index + 1]
                blue = row[index + 2]

            luma = (
                0.2126 * red
                + 0.7152 * green
                + 0.0722 * blue
            )
            luminances.append(luma)

            if max(red, green, blue) > 18:
                non_black += 1

            quantized_colors.add(
                (red >> 4, green >> 4, blue >> 4)
            )

    count = max(1, len(luminances))
    mean = sum(luminances) / count
    variance = sum(
        (value - mean) ** 2
        for value in luminances
    ) / count

    return {
        "width": width,
        "height": height,
        "samples": count,
        "mean_luma": mean,
        "luma_stddev": math.sqrt(variance),
        "non_black_ratio": non_black / count,
        "unique_colors": len(quantized_colors),
    }


def screenshot_is_visible(metrics: dict[str, float | int]) -> bool:
    non_black = float(metrics["non_black_ratio"])
    mean_luma = float(metrics["mean_luma"])
    stddev = float(metrics["luma_stddev"])
    unique = int(metrics["unique_colors"])

    # A black background with a small amount of white title text still
    # counts as visible. A nearly uniform black frame does not.
    return (
        non_black >= 0.0015
        and mean_luma >= 0.45
        and (
            unique >= 3
            or stddev >= 1.8
        )
    )


def capture_screen(adb: Path) -> tuple[bytes, dict[str, float | int]]:
    result = run_bytes(
        [
            str(adb),
            "-s",
            TARGET,
            "exec-out",
            "screencap",
            "-p",
        ],
        timeout=25,
    )

    if result.returncode != 0 or not result.stdout:
        raise RuntimeError("Fire TV screenshot failed.")

    return result.stdout, decode_png_metrics(result.stdout)


def safe_test_remote_name(candidate: Candidate) -> str:
    suffix = candidate.local_path.suffix.lower()

    if not re.fullmatch(r"\.[a-z0-9]{1,5}", suffix):
        raise RuntimeError(
            f"Unsafe ROM extension: {candidate.local_path.suffix}"
        )

    # The hash is deterministic, shell-safe, unique for the ROM content,
    # and reusable across interrupted test runs.
    return f"g_{candidate.sha256[:20]}{suffix}"

def sanitize_remote_name(candidate: Candidate) -> str:
    suffix = candidate.local_path.suffix.lower()
    title = safe_filename(candidate.title)

    # Final dashboard files may contain spaces because SilentiumOS launches
    # them through an Android Intent, not through adb shell. Add a short hash
    # only when needed to prevent two different ROMs from overwriting one
    # another after title cleanup.
    return f"{title} [{candidate.sha256[:8]}]{suffix}"

def prepare_retroarch_runtime(adb: Path) -> None:
    path_output = adb_output(
        adb,
        "shell",
        "pm",
        "path",
        RETROARCH_PACKAGE,
        timeout=25,
    )

    apk_paths = [
        line.split("package:", 1)[1].strip()
        for line in path_output.splitlines()
        if line.strip().startswith("package:")
    ]

    apk_path = next(
        (
            path
            for path in apk_paths
            if path.endswith("/base.apk")
        ),
        apk_paths[0] if apk_paths else "",
    )

    if not apk_path:
        raise RuntimeError(
            "The installed RetroArch APK path could not be resolved."
        )

    ime = adb_output(
        adb,
        "shell",
        "settings",
        "get",
        "secure",
        "default_input_method",
        timeout=20,
    ).strip()

    if ime.lower() in ("", "null", "none"):
        ime = ""

    core_listing = adb_output(
        adb,
        "shell",
        "run-as",
        RETROARCH_PACKAGE,
        "ls",
        "-l",
        "cores",
        timeout=30,
    )

    required_cores = sorted(
        {
            config["core"]
            for config in SYSTEMS.values()
        }
    )

    missing = [
        core
        for core in required_cores
        if core not in core_listing
    ]
    if missing:
        raise RuntimeError(
            "Required private RetroArch cores are missing: "
            + ", ".join(missing)
        )

    RETROARCH_RUNTIME.clear()
    RETROARCH_RUNTIME.update({
        "APK": apk_path,
        "IME": ime,
        "DATADIR": f"/data/user/0/{RETROARCH_PACKAGE}",
        "SDCARD": "/storage/emulated/0",
        "EXTERNAL": (
            "/storage/emulated/0/Android/data/"
            f"{RETROARCH_PACKAGE}/files"
        ),
        "DOWNLOADS": "/storage/emulated/0/Download",
        "SCREENSHOTS": (
            "/storage/emulated/0/Android/data/"
            f"{RETROARCH_PACKAGE}/files/screenshots"
        ),
    })

    print()
    print("RetroArch runtime prepared:")
    print(f"  APK={RETROARCH_RUNTIME['APK']}")
    print(
        "  IME="
        + (
            RETROARCH_RUNTIME["IME"]
            if RETROARCH_RUNTIME["IME"]
            else "(none)"
        )
    )
    print(
        f"  private cores confirmed: "
        f"{len(required_cores)} required system cores"
    )


def launch_content(
        adb: Path,
        *,
        core: str,
        remote_rom: str | None) -> subprocess.CompletedProcess[str]:
    if not RETROARCH_RUNTIME.get("APK"):
        raise RuntimeError(
            "RetroArch runtime extras were not prepared."
        )

    command = [
        str(adb),
        "-s",
        TARGET,
        "shell",
        "am",
        "start",
        "-W",
        "-n",
        RETROARCH_ACTIVITY,
        "-e",
        "LIBRETRO",
        (
            f"/data/user/0/{RETROARCH_PACKAGE}/"
            f"cores/{core}"
        ),
        "-e",
        "CONFIGFILE",
        (
            "/storage/emulated/0/Android/data/"
            f"{RETROARCH_PACKAGE}/files/retroarch.cfg"
        ),
        "-e",
        "DATADIR",
        RETROARCH_RUNTIME["DATADIR"],
        "-e",
        "APK",
        RETROARCH_RUNTIME["APK"],
        "-e",
        "SDCARD",
        RETROARCH_RUNTIME["SDCARD"],
        "-e",
        "EXTERNAL",
        RETROARCH_RUNTIME["EXTERNAL"],
        "-e",
        "DOWNLOADS",
        RETROARCH_RUNTIME["DOWNLOADS"],
        "-e",
        "SCREENSHOTS",
        RETROARCH_RUNTIME["SCREENSHOTS"],
        "--activity-clear-task",
        "--activity-clear-top",
    ]

    if RETROARCH_RUNTIME.get("IME"):
        command.extend([
            "-e",
            "IME",
            RETROARCH_RUNTIME["IME"],
        ])

    if remote_rom is not None:
        command.extend([
            "-e",
            "ROM",
            remote_rom,
        ])

    return run_text(
        command,
        timeout=40,
        capture=True,
    )

def stop_game_and_return(adb: Path) -> None:
    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "force-stop",
            RETROARCH_PACKAGE,
        ],
        timeout=20,
    )
    time.sleep(0.35)

def set_library_test_mode(
        adb: Path,
        enabled: bool) -> None:
    mode = "enable" if enabled else "disable"

    command = [
        str(adb),
        "-s",
        TARGET,
        "shell",
        "am",
        "broadcast",
        "--include-stopped-packages",
        "-n",
        (
            f"{SILENTIUM_PACKAGE}/"
            "com.silentiumlabs.silentiumos."
            "LibraryTestModeReceiver"
        ),
        "--es",
        "mode",
        mode,
    ]

    if enabled:
        command.extend([
            "--el",
            "duration_ms",
            str(6 * 60 * 60 * 1000),
        ])

    result = run_text(
        command,
        timeout=30,
        capture=True,
    )
    print(result.stdout or "")

    if (
        result.returncode != 0
        or "Broadcast completed" not in (result.stdout or "")
    ):
        raise RuntimeError(
            "SilentiumOS library-test mode could not be changed."
        )


def suspend_console_takeover(adb: Path) -> None:
    print()
    print(
        "Suspending SilentiumOS Home redirect and Console Guard "
        "for controlled emulator testing..."
    )

    set_library_test_mode(adb, True)

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "stopservice",
            "-n",
            (
                f"{SILENTIUM_PACKAGE}/"
                ".ConsoleGuardService"
            ),
        ],
        timeout=25,
        capture=True,
    )

    # This cancels pending SplashActivity callbacks and removes the dashboard
    # from the foreground. The private test-mode preference remains stored.
    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "force-stop",
            SILENTIUM_PACKAGE,
        ],
        timeout=25,
    )

    time.sleep(1.2)

    current = top_package(adb)
    if current == SILENTIUM_PACKAGE:
        raise RuntimeError(
            "SilentiumOS remained in front after test-mode suspension."
        )

    print(
        "Console takeover suspended. "
        f"Foreground is now: {current}"
    )


def restore_console_takeover(adb: Path) -> None:
    print()
    print(
        "Restoring SilentiumOS dashboard, Home redirect, "
        "and Console Guard..."
    )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "force-stop",
            RETROARCH_PACKAGE,
        ],
        timeout=20,
    )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start",
            "-n",
            SILENTIUM_SPLASH,
        ],
        timeout=25,
    )

    time.sleep(3.2)

    try:
        set_library_test_mode(adb, False)
    except Exception as error:
        print(
            "WARNING: Automatic console lock restoration "
            f"reported: {error}"
        )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start-foreground-service",
            "-n",
            (
                f"{SILENTIUM_PACKAGE}/"
                ".ConsoleGuardService"
            ),
        ],
        timeout=25,
        capture=True,
    )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start",
            "-n",
            SILENTIUM_SPLASH,
        ],
        timeout=25,
    )

    time.sleep(1.5)


def retroarch_processes(adb: Path) -> dict[str, str]:
    processes: dict[str, str] = {}

    pidof_output = adb_output(
        adb,
        "shell",
        "pidof",
        RETROARCH_PACKAGE,
        timeout=20,
    )
    for pid in re.findall(r"\b\d+\b", pidof_output):
        processes[pid] = RETROARCH_PACKAGE

    ps_output = adb_output(
        adb,
        "shell",
        "ps",
        "-A",
        timeout=25,
    )

    for line in ps_output.splitlines():
        if RETROARCH_PACKAGE not in line:
            continue

        fields = line.split()
        if len(fields) < 2:
            continue

        pid = next(
            (
                field
                for field in fields[1:5]
                if field.isdigit()
            ),
            None,
        )
        if pid is None:
            continue

        processes[pid] = fields[-1]

    for pid in list(processes):
        cmdline = adb_output(
            adb,
            "shell",
            "run-as",
            RETROARCH_PACKAGE,
            "cat",
            f"/proc/{pid}/cmdline",
            timeout=20,
        ).replace("\x00", " ").strip()

        if cmdline:
            processes[pid] = cmdline

    return processes


def retro_activity_is_active(adb: Path) -> tuple[bool, str, str]:
    activity = adb_output(
        adb,
        "shell",
        "dumpsys",
        "activity",
        "activities",
        timeout=30,
    )
    foreground = top_package(adb)

    relevant_lines = "\n".join(
        line.strip()
        for line in activity.splitlines()
        if (
            RETROARCH_PACKAGE in line
            or "RetroActivityFuture" in line
        )
    )

    has_game_activity = (
        "RetroActivityFuture" in relevant_lines
        and RETROARCH_PACKAGE in relevant_lines
    )

    return (
        foreground == RETROARCH_PACKAGE and has_game_activity,
        foreground,
        relevant_lines[-1800:],
    )


def mapped_core_processes(
        adb: Path,
        processes: dict[str, str],
        core: str,
) -> tuple[list[str], str]:
    matched: list[str] = []
    evidence_parts: list[str] = []

    for pid, process_name in processes.items():
        maps = adb_output(
            adb,
            "shell",
            "run-as",
            RETROARCH_PACKAGE,
            "cat",
            f"/proc/{pid}/maps",
            timeout=30,
        )

        if core.lower() in maps.lower():
            matched.append(pid)
            evidence_parts.append(
                f"PID {pid} ({process_name}) mapped {core}"
            )
        elif maps:
            error_line = next(
                (
                    line
                    for line in maps.splitlines()
                    if (
                        "permission denied" in line.lower()
                        or "not found" in line.lower()
                    )
                ),
                "",
            )
            if error_line:
                evidence_parts.append(
                    f"PID {pid}: {error_line}"
                )

    return matched, "\n".join(evidence_parts)


def retroarch_process_logs(
        adb: Path,
        processes: dict[str, str],
        core: str,
        remote_rom: str | None,
) -> str:
    collected: list[str] = []

    for pid in processes:
        output = adb_output(
            adb,
            "shell",
            "logcat",
            "-d",
            f"--pid={pid}",
            "-t",
            "700",
            timeout=35,
        )

        if (
            "unknown option" not in output.lower()
            and "unrecognized option" not in output.lower()
        ):
            collected.append(output)

    if collected:
        return "\n".join(collected)

    complete = adb_output(
        adb,
        "shell",
        "logcat",
        "-d",
        "-t",
        "1600",
        timeout=35,
    )

    search_terms = {
        RETROARCH_PACKAGE.lower(),
        "retroarch",
        "libretro",
        core.lower(),
    }

    if remote_rom is not None:
        search_terms.add(Path(remote_rom).name.lower())

    filtered = [
        line
        for line in complete.splitlines()
        if any(term in line.lower() for term in search_terms)
    ]
    return "\n".join(filtered)


def explicit_fatal_pattern(logs: str) -> str | None:
    lower_logs = logs.lower()

    return next(
        (
            pattern
            for pattern in FATAL_LOG_PATTERNS
            if pattern in lower_logs
        ),
        None,
    )
def restore_all_verified_core_markers(adb: Path) -> None:
    all_cores = sorted(
        {
            config["core"]
            for config in SYSTEMS.values()
        }.union(ARCADE_CORES.values())
    )

    marker = ROOT / "cores.ready"
    marker.write_text(
        "\n".join(all_cores) + "\n",
        encoding="ascii",
    )
    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "push",
            str(marker),
            REMOTE_CORES_MARKER,
        ],
        timeout=30,
    )


def test_launch(
        adb: Path,
        *,
        label: str,
        core: str,
        remote_rom: str | None,
        failed_screenshot_name: str) -> tuple[bool, dict]:
    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "force-stop",
            RETROARCH_PACKAGE,
        ],
        timeout=20,
    )
    time.sleep(0.45)

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "logcat",
            "-c",
        ],
        timeout=20,
    )

    result = launch_content(
        adb,
        core=core,
        remote_rom=remote_rom,
    )

    launch_output = result.stdout or ""
    lower_launch = launch_output.lower()

    if (
        result.returncode != 0
        or "error type 3" in lower_launch
        or "does not exist" in lower_launch
        or "permission denial" in lower_launch
    ):
        stop_game_and_return(adb)
        return False, {
            "reason": "activity launch failed",
            "launch_output": launch_output[-1800:],
        }

    time.sleep(3.2)

    first_processes = retroarch_processes(adb)
    (
        first_active,
        first_foreground,
        first_activity_evidence,
    ) = retro_activity_is_active(adb)
    (
        first_core_pids,
        first_core_evidence,
    ) = mapped_core_processes(
        adb,
        first_processes,
        core,
    )

    for keycode in (96, 108):
        run_text(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "input",
                "keyevent",
                str(keycode),
            ],
            timeout=15,
        )

    time.sleep(2.8)

    second_processes = retroarch_processes(adb)
    (
        second_active,
        second_foreground,
        second_activity_evidence,
    ) = retro_activity_is_active(adb)
    (
        second_core_pids,
        second_core_evidence,
    ) = mapped_core_processes(
        adb,
        second_processes,
        core,
    )

    logs = retroarch_process_logs(
        adb,
        second_processes or first_processes,
        core,
        remote_rom,
    )
    fatal = explicit_fatal_pattern(logs)

    process_stable = bool(first_processes and second_processes)
    activity_stable = first_active and second_active
    mapped_pids = sorted(
        set(first_core_pids) | set(second_core_pids)
    )
    core_loaded = bool(mapped_pids)

    passed = (
        process_stable
        and activity_stable
        and core_loaded
        and fatal is None
    )

    details = {
        "test_engine": TEST_ENGINE_VERSION,
        "label": label,
        "first_processes": first_processes,
        "second_processes": second_processes,
        "first_foreground": first_foreground,
        "second_foreground": second_foreground,
        "process_stable": process_stable,
        "activity_stable": activity_stable,
        "mapped_core_pids": mapped_pids,
        "core_loaded_in_process": core_loaded,
        "fatal_pattern": fatal,
        "launch_output": launch_output[-1800:],
        "first_activity_evidence": first_activity_evidence,
        "second_activity_evidence": second_activity_evidence,
        "core_map_evidence": (
            second_core_evidence or first_core_evidence
        ),
        "retroarch_logs": logs[-3000:],
    }

    if not passed:
        if not process_stable:
            details["reason"] = (
                "RetroArch process did not remain alive"
            )
        elif not activity_stable:
            details["reason"] = (
                "RetroArch game activity was not confirmed "
                "in the foreground"
            )
        elif not core_loaded:
            details["reason"] = (
                "requested core was not found in any "
                "RetroArch process map"
            )
        elif fatal is not None:
            details["reason"] = (
                f"explicit RetroArch load error: {fatal}"
            )

        try:
            raw, screenshot_metrics = capture_screen(adb)
            SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)
            screenshot_path = (
                SCREENSHOT_ROOT
                / f"{safe_filename(failed_screenshot_name)}.png"
            )
            screenshot_path.write_bytes(raw)
            details["diagnostic_screenshot"] = str(screenshot_path)
            details["screenshot_metrics"] = screenshot_metrics
        except Exception as error:
            details["screenshot_error"] = str(error)

    stop_game_and_return(adb)
    return passed, details

def stage_candidate(
        adb: Path,
        candidate: Candidate) -> str:
    # IMPORTANT: adb shell joins arguments into a remote shell command.
    # Human-readable ROM names containing spaces were split by Fire OS,
    # causing RetroArch to receive a damaged ROM path. Test files therefore
    # always use deterministic hash names containing no spaces.
    remote_folder = (
        f"{REMOTE_TEST_ROOT}/{candidate.system}"
    )
    remote_name = safe_test_remote_name(candidate)
    remote_path = remote_folder + "/" + remote_name

    if re.search(r"[^A-Za-z0-9_./-]", remote_path):
        raise RuntimeError(
            f"Unsafe remote test path was generated: {remote_path}"
        )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "mkdir",
            "-p",
            remote_folder,
        ],
        timeout=20,
    )

    result = run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "push",
            str(candidate.local_path),
            remote_path,
        ],
        timeout=90,
        capture=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "ROM staging upload failed: "
            + (result.stdout or "")[-500:]
        )

    verify = adb_output(
        adb,
        "shell",
        "stat",
        "-c",
        "%s",
        remote_path,
        timeout=25,
    )

    remote_size_match = re.search(r"\b\d+\b", verify)
    if (
        remote_size_match is None
        or int(remote_size_match.group(0)) != candidate.size
    ):
        raise RuntimeError(
            "Staged ROM size did not match the local candidate."
        )

    return remote_path

def clear_work_folders() -> None:
    for folder in (
        WORK_ROOT,
        PASSED_ROOT,
        FAILED_ROOT,
    ):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    for system in SYSTEMS:
        (PASSED_ROOT / system).mkdir(
            parents=True,
            exist_ok=True,
        )


def load_result_cache() -> dict[str, dict]:
    cache: dict[str, dict] = {}

    if not RESULT_CACHE.exists():
        return cache

    for line in RESULT_CACHE.read_text(
            encoding="utf-8",
            errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        key = entry.get("cache_key")
        if (
            isinstance(key, str)
            and entry.get("test_engine") == TEST_ENGINE_VERSION
        ):
            cache[key] = entry

    return cache


def cache_key_for_candidate(candidate: Candidate) -> str:
    core = SYSTEMS[candidate.system]["core"]
    return (
        f"{TEST_ENGINE_VERSION}:"
        f"{candidate.sha256}:"
        f"{core}"
    )


def append_result_cache(entry: dict) -> None:
    with RESULT_CACHE.open(
            "a",
            encoding="utf-8",
            newline="\n") as output:
        output.write(json.dumps(entry, sort_keys=True) + "\n")


def restore_cached_pass(
        candidate: Candidate,
        cached: dict,
) -> dict:
    filename = sanitize_remote_name(candidate)
    destination = PASSED_ROOT / candidate.system / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate.local_path, destination)

    return {
        "title": candidate.title,
        "filename": filename,
        "system": candidate.system,
        "source_name": candidate.source_name,
        "source_url": candidate.source_url,
        "sha256": candidate.sha256,
        "size": candidate.size,
        "existing": candidate.existing,
        "status": "PASS",
        "launch_test": cached.get("launch_test", {}),
        "reused_test_result": True,
    }


def preflight_test_framework(
        adb: Path,
        candidates: list[Candidate],
) -> None:
    preferred: list[Candidate] = []

    for system in ("NES", "GameBoy", "Sega"):
        match = next(
            (
                candidate
                for candidate in candidates
                if candidate.system == system and candidate.existing
            ),
            None,
        )
        if match is not None:
            preferred.append(match)

    if not preferred:
        preferred = candidates[:3]

    selected = preferred[:3]

    print()
    print("===================================================")
    print("PREFLIGHTING THE TEST ENGINE")
    print("===================================================")
    print(
        "Known/current games are checked first. "
        "The full run will not start unless the tester "
        "produces a real pass."
    )

    pass_count = 0

    for index, candidate in enumerate(selected, start=1):
        print()
        print(
            f"[PREFLIGHT {index}/{len(selected)}] "
            f"{candidate.system}: {candidate.title}"
        )

        remote_path = stage_candidate(adb, candidate)
        print(f"  safe_test_path={remote_path}")

        if " " in remote_path:
            raise RuntimeError(
                "Preflight generated a test path containing spaces."
            )

        passed, details = test_launch(
            adb,
            label=(
                f"Preflight / {candidate.system} / "
                f"{candidate.title}"
            ),
            core=SYSTEMS[candidate.system]["core"],
            remote_rom=remote_path,
            failed_screenshot_name=(
                f"Preflight_{candidate.system}_{candidate.title}"
            ),
        )

        print(f"  processes={details.get('second_processes')}")
        print(f"  foreground={details.get('second_foreground')}")
        print(f"  mapped_core_pids={details.get('mapped_core_pids')}")
        print(f"  fatal_pattern={details.get('fatal_pattern')}")
        if not passed:
            print(
                "  launch_output="
                + str(details.get("launch_output", ""))
                .replace("\n", " | ")
            )
            print(
                "  core_map_evidence="
                + str(details.get("core_map_evidence", ""))
                .replace("\n", " | ")
            )

        if passed:
            pass_count += 1
            print("  PREFLIGHT PASS")
        else:
            print(
                "  PREFLIGHT FAIL: "
                f"{details.get('reason', 'unknown')}"
            )

    if pass_count == 0:
        raise RuntimeError(
            "The test engine failed every preflight game. "
            "The full 240-game run was canceled before "
            "changing the live library."
        )

    print()
    print(
        f"Preflight passed {pass_count}/{len(selected)}. "
        "Beginning the full test."
    )

def test_candidates(
        adb: Path,
        candidates: list[Candidate]) -> tuple[list[dict], list[dict]]:
    passed_entries = []
    failed_entries = []
    result_cache = load_result_cache()

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "rm",
            "-rf",
            REMOTE_TEST_ROOT,
        ],
        timeout=30,
    )

    total = len(candidates)
    estimated_minutes = max(
        1,
        math.ceil(total * 5.5 / 60),
    )

    print()
    print("===================================================")
    print("TESTING EVERY GAME ON ELLIOT'S FIRE STICK")
    print("===================================================")
    print(f"Candidates selected for complete hardware testing: {total}")
    print(
        f"Estimated time: about {estimated_minutes}-"
        f"{estimated_minutes + 12} minutes"
    )
    print(
        "Completed 0.7.5 results are cached, so an "
        "interrupted rerun resumes instead of starting over."
    )

    for index, candidate in enumerate(candidates, start=1):
        print()
        print(
            f"[{index}/{total}] {candidate.system}: "
            f"{candidate.title}"
        )

        key = cache_key_for_candidate(candidate)
        cached = result_cache.get(key)

        if cached is not None:
            if cached.get("status") == "PASS":
                entry = restore_cached_pass(candidate, cached)
                passed_entries.append(entry)
                print("  PASS — reused cached hardware test")
                continue

            if cached.get("status") == "FAIL":
                failed_entry = {
                    "title": candidate.title,
                    "filename": sanitize_remote_name(candidate),
                    "system": candidate.system,
                    "source_name": candidate.source_name,
                    "source_url": candidate.source_url,
                    "sha256": candidate.sha256,
                    "size": candidate.size,
                    "existing": candidate.existing,
                    "status": "FAIL",
                    "launch_test": cached.get("launch_test", {}),
                    "reused_test_result": True,
                }
                failed_entries.append(failed_entry)
                print(
                    "  FAIL — reused cached hardware test: "
                    f"{failed_entry['launch_test'].get('reason', 'unknown')}"
                )
                continue

        try:
            remote_path = stage_candidate(adb, candidate)
            passed, test_details = test_launch(
                adb,
                label=f"{candidate.system} / {candidate.title}",
                core=SYSTEMS[candidate.system]["core"],
                remote_rom=remote_path,
                failed_screenshot_name=(
                    f"{candidate.system}_{candidate.title}"
                ),
            )
        except Exception as error:
            passed = False
            test_details = {
                "test_engine": TEST_ENGINE_VERSION,
                "reason": str(error),
            }

        entry = {
            "title": candidate.title,
            "filename": sanitize_remote_name(candidate),
            "system": candidate.system,
            "source_name": candidate.source_name,
            "source_url": candidate.source_url,
            "sha256": candidate.sha256,
            "size": candidate.size,
            "existing": candidate.existing,
            "launch_test": test_details,
        }

        cache_entry = {
            "cache_key": key,
            "test_engine": TEST_ENGINE_VERSION,
            "status": "PASS" if passed else "FAIL",
            "launch_test": test_details,
        }
        append_result_cache(cache_entry)
        result_cache[key] = cache_entry

        if passed:
            destination = (
                PASSED_ROOT
                / candidate.system
                / entry["filename"]
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate.local_path, destination)
            entry["status"] = "PASS"
            passed_entries.append(entry)
            print(
                "  PASS — process stable, activity foreground, "
                "requested core mapped"
            )
        else:
            entry["status"] = "FAIL"
            failed_entries.append(entry)
            print(
                "  FAIL — hidden from dashboard: "
                f"{test_details.get('reason', 'unknown')}"
            )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "rm",
            "-rf",
            REMOTE_TEST_ROOT,
        ],
        timeout=30,
    )

    return passed_entries, failed_entries

def test_arcade_cores(adb: Path) -> tuple[list[str], list[dict]]:
    restore_all_verified_core_markers(adb)

    passed_optional = []
    results = []

    print()
    print("Testing Silentium Arcade games...")

    for title, core in ARCADE_CORES.items():
        print(f"  Testing {title}...")
        passed, details = test_launch(
            adb,
            label=f"Silentium Arcade / {title}",
            core=core,
            remote_rom=None,
            failed_screenshot_name=f"Arcade_{title}",
        )

        result = {
            "title": title,
            "core": core,
            "status": "PASS" if passed else "RETAINED",
            "launch_test": details,
        }
        results.append(result)

        if passed:
            passed_optional.append(core)
            print(f"  PASS: {title}")
        else:
            print(
                f"  RETAINED: {title} core was already "
                "byte-verified; review the smoke-test report."
            )

    restore_all_verified_core_markers(adb)
    return passed_optional, results

def rebuild_live_library(
        adb: Path,
        passed_entries: list[dict]) -> None:
    print()
    print("Installing only games that passed...")

    for system, config in SYSTEMS.items():
        remote = config["remote"]
        run_text(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "rm",
                "-rf",
                remote,
            ],
            timeout=30,
        )
        run_text(
            [
                str(adb),
                "-s",
                TARGET,
                "shell",
                "mkdir",
                "-p",
                remote,
            ],
            timeout=20,
        )

        local_folder = PASSED_ROOT / system
        for path in sorted(local_folder.iterdir()):
            if not path.is_file():
                continue
            result = run_text(
                [
                    str(adb),
                    "-s",
                    TARGET,
                    "push",
                    str(path),
                    remote + "/",
                ],
                timeout=90,
                capture=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Final upload failed for {path.name}."
                )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "push",
            str(MANIFEST),
            REMOTE_ROOT + "/validated_library.json",
        ],
        timeout=30,
    )
    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "push",
            str(CREDITS),
            REMOTE_ROOT + "/VALIDATED_LIBRARY_CREDITS.txt",
        ],
        timeout=30,
    )

    run_text(
        [
            str(adb),
            "-s",
            TARGET,
            "shell",
            "am",
            "start",
            "-n",
            SILENTIUM_SPLASH,
        ],
        timeout=20,
    )


def write_outputs(
        passed_entries: list[dict],
        failed_entries: list[dict],
        arcade_results: list[dict]) -> None:
    per_system = {
        system: 0
        for system in SYSTEMS
    }
    for entry in passed_entries:
        per_system[entry["system"]] += 1

    manifest_data = {
        "format": 2,
        "edition": "SilentiumOS Elliot Edition 0.7.5",
        "test_method": (
            "ROM structure check, SHA-256, real Fire TV launch, "
            "two process-stability checks, foreground activity, "
            "mapped emulator core, fatal-log scan; "
            "ADB screenshot is diagnostic only"
        ),
        "validated_games": len(passed_entries),
        "rejected_games": len(failed_entries),
        "system_counts": per_system,
        "games": passed_entries,
        "arcade": arcade_results,
    }

    MANIFEST.write_text(
        json.dumps(
            manifest_data,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    credit_lines = [
        "SILENTIUMOS ELLIOT EDITION 0.7.5",
        "LARGE TESTED LEGAL LIBRARY",
        "",
        (
            "Every displayed ROM kept RetroArch alive and in front, "
            "mapped the requested emulator core into the process, "
            "and avoided fatal loading errors on Elliot's Fire TV."
        ),
        (
            "ADB screenshots are retained only as diagnostics because "
            "Fire OS can return black captures for a working OpenGL "
            "game surface. This smoke test cannot prove every level, "
            "ending, save feature, or multiplayer mode."
        ),
        "",
        "Primary legal collections:",
        "- retrobrews/nes-games",
        "- retrobrews/snes-games",
        "- retrobrews/gbc-games",
        "- retrobrews/gba-games",
        "- retrobrews/md-games",
        "- retrobrews/sms-games",
        "",
        (
            "Commercial Nintendo, Sega and other retail ROMs are "
            "not included."
        ),
        (
            "Mature/questionable titles, commercial-IP names, "
            "tests, utilities, demos and multicarts are filtered."
        ),
        "",
        "Passed games:",
    ]

    for system in SYSTEMS:
        credit_lines.append("")
        credit_lines.append(
            f"{system}: {per_system[system]}"
        )
        for entry in sorted(
                (
                    item
                    for item in passed_entries
                    if item["system"] == system
                ),
                key=lambda item: item["title"].lower()):
            credit_lines.append(
                f"- {entry['title']} "
                f"({entry['source_name']})"
            )

    CREDITS.write_text(
        "\n".join(credit_lines) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "SILENTIUMOS ELLIOT EDITION 0.7.5",
        "LARGE LIBRARY HARDWARE TEST REPORT",
        "=" * 55,
        "",
        f"PASSED ROM GAMES: {len(passed_entries)}",
        f"REJECTED/FAILED: {len(failed_entries)}",
        "",
    ]

    for system in SYSTEMS:
        report_lines.append(
            f"{system}: {per_system[system]} passed"
        )

    report_lines.extend([
        "",
        "SILENTIUM ARCADE:",
    ])

    for item in arcade_results:
        report_lines.append(
            f"- {item['title']}: {item['status']}"
        )

    report_lines.extend([
        "",
        "FAILED OR FILTERED AT RUNTIME:",
    ])

    for entry in failed_entries:
        reason = entry.get(
            "launch_test",
            {},
        ).get(
            "reason",
            entry.get(
                "launch_test",
                {},
            ).get(
                "fatal_pattern",
                "launch/screen test failed",
            ),
        )
        report_lines.append(
            f"- {entry['system']} / "
            f"{entry['title']}: {reason}"
        )

    REPORT.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )


def quick_verify_final_hashes(
        adb: Path,
        passed_entries: list[dict]) -> None:
    print()
    print("Checking final installed file count...")

    expected = len(passed_entries)
    actual = 0

    for system, config in SYSTEMS.items():
        output = adb_output(
            adb,
            "shell",
            "find",
            config["remote"],
            "-maxdepth",
            "1",
            "-type",
            "f",
            timeout=30,
        )
        actual += len(
            [
                line
                for line in output.splitlines()
                if line.strip()
                and Path(line.strip()).suffix.lower()
                in config["extensions"]
            ]
        )

    if actual != expected:
        raise RuntimeError(
            "Final library file-count mismatch: "
            f"expected {expected}, found {actual}."
        )

    print(
        f"Final installed ROM count verified: {actual}"
    )


def main() -> int:
    adb: Path | None = None
    takeover_suspended = False

    try:
        clear_work_folders()

        adb = find_adb()
        connect(adb)
        restore_all_verified_core_markers(adb)

        all_candidates = pull_existing_library(adb)

        print()
        print("Downloading curated legal collections...")

        for source_name, source_url, system in COLLECTIONS:
            try:
                archive = download_collection(
                    source_name,
                    source_url,
                )
                found = collect_from_archive(
                    archive,
                    source_name,
                    source_url,
                    system,
                )
                all_candidates.extend(found)
                print(
                    f"  {source_name}: "
                    f"{len(found)} eligible candidates"
                )
            except Exception as error:
                print(
                    f"  COLLECTION SKIPPED: "
                    f"{source_name}: {error}"
                )

        candidates = deduplicate_and_limit(
            all_candidates
        )
        candidates = enforce_storage_limit(
            adb,
            candidates,
        )

        if not candidates:
            raise RuntimeError(
                "No legal game candidates were available."
            )

        prepare_retroarch_runtime(adb)
        suspend_console_takeover(adb)
        takeover_suspended = True

        preflight_test_framework(
            adb,
            candidates,
        )

        passed_entries, failed_entries = test_candidates(
            adb,
            candidates,
        )

        passed_arcade, arcade_results = test_arcade_cores(
            adb
        )

        if not passed_entries:
            raise RuntimeError(
                "No ROM games passed the Fire TV launch test. "
                "The existing library backup was preserved."
            )

        write_outputs(
            passed_entries,
            failed_entries,
            arcade_results,
        )
        rebuild_live_library(
            adb,
            passed_entries,
        )
        quick_verify_final_hashes(
            adb,
            passed_entries,
        )

        print()
        print("===================================================")
        print("ELLIOT'S LARGE TESTED LIBRARY IS READY")
        print("===================================================")
        print(
            f"ROM games shown on dashboard: "
            f"{len(passed_entries)}"
        )
        print(
            f"Silentium Arcade games passed: "
            f"{len(passed_arcade)}"
        )
        print(
            f"Rejected or hidden: "
            f"{len(failed_entries)}"
        )
        print()
        print(
            "Only games that kept RetroArch alive and in front, "
            "loaded the requested core into the process, and "
            "avoided explicit loading errors were installed."
        )
        print(f"Report: {REPORT}")
        return 0

    except Exception as error:
        print()
        print(f"ERROR: {error}")
        print(
            "The previous library backup remains at:"
        )
        print(EXISTING_BACKUP)
        return 1

    finally:
        if adb is not None:
            try:
                restore_console_takeover(adb)
            except Exception as restore_error:
                print(
                    "WARNING: Console-mode restoration encountered: "
                    f"{restore_error}"
                )

if __name__ == "__main__":
    raise SystemExit(main())
