#!/usr/bin/env python3
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALUES = ROOT / "app" / "src" / "main" / "res" / "values"
STRINGS = VALUES / "strings.xml"

VALID_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="home_redirect_accessibility_description">Returns Amazon Home to the SilentiumOS dashboard for Elliot.</string>
</resources>
"""

def main() -> int:
    try:
        VALUES.mkdir(parents=True, exist_ok=True)
        STRINGS.write_text(
            VALID_XML,
            encoding="utf-8",
            newline="\n",
        )

        tree = ET.parse(STRINGS)
        root = tree.getroot()

        if root.tag != "resources":
            raise RuntimeError(
                "strings.xml does not have a resources root."
            )

        matches = [
            item
            for item in root.findall("string")
            if item.get("name")
            == "home_redirect_accessibility_description"
        ]

        if len(matches) != 1:
            raise RuntimeError(
                "Accessibility description resource is missing "
                "or duplicated."
            )

        value = matches[0].text or ""
        if "\\" in value:
            raise RuntimeError(
                "Accessibility description contains an invalid "
                "escape character."
            )

        print(
            "Accessibility string resource is valid and ready."
        )
        return 0

    except Exception as error:
        print(f"ERROR: {error}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
