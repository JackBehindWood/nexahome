"""`nexahome.toml`: the settings of an instance (schema 1: which stacks this host runs).

Read strictly and written whole, atomically, by `nexahome config` (PK6-13). The standard library reads TOML but does
not write it; this schema has three value types, so the writer is a few lines here instead of a dependency.
"""

from __future__ import annotations

from nexahome import __version__
from nexahome.instance import SCHEMA

DEFAULT_STACKS = ("hello",)  # a fresh instance runs the demo; more stacks are added with `nexahome config set stacks`
HEADER = "# Managed by `nexahome config`. Comments added by hand are not kept when it rewrites this file.\n"


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(stacks: tuple[str, ...] | list[str], created_by: str | None = None) -> str:
    """The file text, keys in a fixed order."""
    names = ", ".join(_quote(name) for name in stacks)
    return f"{HEADER}schema = {SCHEMA}\ncreated_by = {_quote(created_by or f'nexahome {__version__}')}\nstacks = [{names}]\n"
