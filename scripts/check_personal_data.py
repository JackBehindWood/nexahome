#!/usr/bin/env python3
"""Fail if files contain personal or environment-specific data.

Flags private IPv4 addresses, home-directory paths with a user name, `.local`
hostnames, and any term listed (one per line, case-insensitive) in the optional,
gitignored `.personal-denylist`. Add `personal-data: ok` to a line to allow it.
"""
import re
import sys
from pathlib import Path

PATTERNS = {
    "private IPv4 address": re.compile(
        r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"
    ),
    "home directory path with a user name": re.compile(r"/(?:Users|home)/[A-Za-z0-9][A-Za-z0-9._-]*"),
    "local hostname": re.compile(r"\b[a-z0-9-]+\.local\b(?!\.(?:md|json))", re.IGNORECASE),
}
ALLOW_MARKER = "personal-data: ok"


def load_denylist() -> list[str]:
    path = Path(".personal-denylist")
    if not path.is_file():
        return []
    lines = (line.strip().lower() for line in path.read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def main(files: list[str]) -> int:
    denylist = load_denylist()
    failures = 0
    for name in files:
        try:
            text = Path(name).read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    print(f"{name}:{number}: {label}")
                    failures += 1
            lowered = line.lower()
            for term in denylist:
                if term in lowered:
                    print(f"{name}:{number}: term from .personal-denylist")
                    failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
