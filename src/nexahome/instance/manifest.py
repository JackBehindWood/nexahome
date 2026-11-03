"""`.nexahome/manifest.json`: the hash of every package-owned file an instance was made with.

`init` writes it; the future `upgrade` reads it to tell a file the user edited from one that is still as shipped.
It lists the stacks only: `nexahome.toml`, every `.env` and `data/` belong to the user.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.defaults import INSTANCE_SCHEMA

if TYPE_CHECKING:
    from collections.abc import Mapping

PATH = ".nexahome/manifest.json"


def render(version: str, files: Mapping[str, str]) -> str:
    """The manifest text for `files` (instance-relative path -> sha256 hex digest)."""
    import json  # only a command that writes or reads the manifest pays for it

    return json.dumps({"schema": INSTANCE_SCHEMA, "created_by": f"nexahome {version}", "files": dict(sorted(files.items()))}, indent=2) + "\n"
