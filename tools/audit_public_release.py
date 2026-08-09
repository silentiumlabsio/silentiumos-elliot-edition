#!/usr/bin/env python3
"""Audit a SilentiumOS public-source tree without third-party packages."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


MANIFEST_NAME = "PUBLIC_IMPORT_MANIFEST.json"
MAX_PUBLIC_FILE_BYTES = 25 * 1024 * 1024

BLOCKED_EXTENSIONS = {
    ".7z", ".aab", ".apk", ".apks", ".bin", ".cer", ".chd",
    ".crt", ".cue", ".der", ".dll", ".dmp", ".dylib", ".gb",
    ".gba", ".gbc", ".gen", ".gz", ".iso", ".jks", ".jsonl",
    ".key", ".keystore", ".log", ".nes", ".p12", ".pem", ".pfx",
    ".rar", ".rom", ".sfc", ".smc", ".sms", ".so", ".tar",
    ".tgz", ".xapk", ".zip",
}

BLOCKED_DIRECTORY_NAMES = {
    ".gradle", ".idea", ".secrets", ".vscode", "__pycache__", "bios",
    "cache", "caches", "captures", "core", "cores", "logs", "rom",
    "roms", "runtime", "state",
}

TEXT_EXTENSIONS = {
    ".gradle", ".java", ".json", ".md", ".pro", ".properties", ".ps1",
    ".py", ".txt", ".xml", ".yaml", ".yml",
}

CONTENT_RULES = (
    (
        "private-ipv4",
        re.compile(
            r"(?<!\d)(?:10\.(?:\d{1,3}\.){2}\d{1,3}|"
            r"192\.168\.(?:\d{1,3}\.)\d{1,3}|"
            r"172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3})(?!\d)"
        ),
    ),
    (
        "mac-address",
        re.compile(
            r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
        ),
    ),
    (
        "local-user-path",
        re.compile(
            r"(?i)(?:[a-z]:\\" + "Users" + r"\\[^\\\s]+|/"
            + "home" + r"/[^/\s]+|/" + "Users" + r"/[^/\s]+)"
        ),
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "github-token",
        re.compile(r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9_]{20,}"),
    ),
    (
        "aws-access-key",
        re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
    ),
    ("google-api-key", re.compile(r"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}")),
    ("slack-token", re.compile(r"(?<![A-Za-z0-9])xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("stripe-live-key", re.compile(r"(?<![A-Za-z0-9])(?:sk|rk)_live_[0-9A-Za-z]{16,}")),
    ("gitlab-token", re.compile(r"(?<![A-Za-z0-9])glpat-[0-9A-Za-z_-]{20,}")),
    ("npm-token", re.compile(r"(?<![A-Za-z0-9])npm_[0-9A-Za-z]{20,}")),
    (
        "url-credentials",
        re.compile(r"(?i)https?://[^/\s:@]+:[^/\s@]+@"),
    ),
    (
        "hardcoded-secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)\b"
            r"\s*[:=]\s*['\"][^'\"\r\n]{8,}['\"]"
        ),
    ),
    (
        "hardcoded-parent-pin",
        re.compile(
            r"(?i)(?:SILENTIUM_PARENT_PIN|PARENT_PIN)\s*[:=]\s*['\"]\d{4}['\"]"
        ),
    ),
    (
        "device-serial-assignment",
        re.compile(r"(?i)(?:ANDROID_SERIAL|ro\.serialno|device[_ -]?serial)\s*[:=]\s*\S+"),
    ),
)


@dataclass(frozen=True, order=True)
class AuditIssue:
    rule: str
    path: str

    def format(self) -> str:
        return f"[{self.rule}] {self.path}"


def repository_entries(root: Path) -> Iterable[Path]:
    """Yield files and symlinks in deterministic order without entering .git."""
    for directory, child_directories, filenames in os.walk(root, followlinks=False):
        child_directories[:] = sorted(
            name for name in child_directories if name != ".git"
        )

        for name in tuple(child_directories):
            candidate = Path(directory, name)
            if candidate.is_symlink():
                child_directories.remove(name)
                yield candidate

        for name in sorted(filenames):
            yield Path(directory, name)


def relative_name(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def build_manifest_entries(root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in repository_entries(root):
        relative = relative_name(root, path)
        if relative == MANIFEST_NAME or path.is_symlink() or not path.is_file():
            continue
        entries.append({"path": relative, "bytes": path.stat().st_size})
    return entries


def audit_manifest(root: Path) -> list[AuditIssue]:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return [AuditIssue("manifest-missing", MANIFEST_NAME)]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [AuditIssue("manifest-invalid", MANIFEST_NAME)]

    declared = data.get("files") if isinstance(data, dict) else None
    if not isinstance(declared, list):
        return [AuditIssue("manifest-invalid", MANIFEST_NAME)]

    issues: list[AuditIssue] = []
    declared_sizes: dict[str, int] = {}
    for entry in declared:
        if not isinstance(entry, dict):
            issues.append(AuditIssue("manifest-invalid-entry", MANIFEST_NAME))
            continue
        path = entry.get("path")
        size = entry.get("bytes")
        if not isinstance(path, str) or not isinstance(size, int):
            issues.append(AuditIssue("manifest-invalid-entry", MANIFEST_NAME))
            continue
        if path in declared_sizes:
            issues.append(AuditIssue("manifest-duplicate", path))
        declared_sizes[path] = size

    actual_sizes = {
        str(entry["path"]): int(entry["bytes"])
        for entry in build_manifest_entries(root)
    }
    for path in sorted(actual_sizes.keys() - declared_sizes.keys()):
        issues.append(AuditIssue("manifest-file-missing", path))
    for path in sorted(declared_sizes.keys() - actual_sizes.keys()):
        issues.append(AuditIssue("manifest-file-extra", path))
    for path in sorted(actual_sizes.keys() & declared_sizes.keys()):
        if actual_sizes[path] != declared_sizes[path]:
            issues.append(AuditIssue("manifest-size-mismatch", path))
    return issues


def audit_repository(root: Path) -> list[AuditIssue]:
    root = root.resolve()
    issues: list[AuditIssue] = []

    for path in repository_entries(root):
        relative = relative_name(root, path)
        lower_parts = tuple(part.lower() for part in Path(relative).parts)

        if path.is_symlink():
            issues.append(AuditIssue("symlink", relative))
            continue
        if not path.is_file():
            continue

        if path.name == ".env" or path.name.startswith(".env."):
            issues.append(AuditIssue("blocked-environment-file", relative))
        if path.suffix.lower() in BLOCKED_EXTENSIONS:
            issues.append(AuditIssue("blocked-extension", relative))
        if any(part in BLOCKED_DIRECTORY_NAMES for part in lower_parts):
            issues.append(AuditIssue("blocked-path", relative))
        if "reports" in lower_parts and "private" in lower_parts:
            issues.append(AuditIssue("blocked-path", relative))
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            issues.append(AuditIssue("file-too-large", relative))

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            issues.append(AuditIssue("invalid-public-text", relative))
            continue
        for rule, pattern in CONTENT_RULES:
            if pattern.search(content):
                issues.append(AuditIssue(rule, relative))

    issues.extend(audit_manifest(root))
    return sorted(set(issues))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of tools)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    issues = audit_repository(args.root)
    if issues:
        print("Public-release audit failed:")
        for issue in issues:
            print(issue.format())
        return 1

    checked = sum(1 for entry in repository_entries(args.root.resolve()) if entry.is_file())
    print(f"Public-release audit passed. Files checked: {checked}")
    print("No blocked artifacts, manifest drift, or sensitive public-text patterns were found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
