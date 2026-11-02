"""Flag personal or environment-specific data in text files (port of scripts/check_personal_data.py).

Flags private IPv4 addresses, home-directory paths with a user name, `.local` hostnames, and any term
in the optional, gitignored `.personal-denylist` (one per line, case-insensitive). A line containing
`personal-data: ok` is allowed.
"""

import re
from collections.abc import Iterable, Sequence
from pathlib import Path

PATTERNS = {
    "private IPv4 address": re.compile(
        r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"
    ),
    "home directory path with a user name": re.compile(r"/(?:Users|home)/[A-Za-z0-9][A-Za-z0-9._-]*"),
    "local hostname": re.compile(r"\b[a-z0-9-]+\.local\b(?!\.(?:md|json))", re.IGNORECASE),
}
ALLOW_MARKER = "personal-data: ok"
DENYLIST = Path(".personal-denylist")


def load_denylist(path: Path = DENYLIST) -> list[str]:
    if not path.is_file():
        return []
    lines = (line.strip().lower() for line in path.read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def scan_text(name: str, text: str, denylist: Sequence[str] = ()) -> list[str]:
    """One "name:line: reason" entry per finding, in the order the original script printed them."""
    findings: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append(f"{name}:{number}: {label}")
        lowered = line.lower()
        for term in denylist:
            if term in lowered:
                findings.append(f"{name}:{number}: term from .personal-denylist")
    return findings


def scan_files(names: Iterable[str], denylist: Sequence[str] | None = None) -> list[str]:
    """Scan files; unreadable and binary files are skipped, as before."""
    terms = load_denylist() if denylist is None else denylist
    findings: list[str] = []
    for name in names:
        try:
            text = Path(name).read_text()
        except (UnicodeDecodeError, OSError):
            continue
        findings += scan_text(name, text, terms)
    return findings
