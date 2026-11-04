"""Which stacks belong to the package and which are the user's own (Proposed, Goal 3).

A stack is the package's when its name ships in this install or is listed in the instance's manifest; every other
folder under `stacks/` is the user's. Reads names with a pattern, not a JSON parser, so listing the stacks stays cheap.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from nexahome.defaults import STACK_FILE_MAX_BYTES

if TYPE_CHECKING:
    from pathlib import Path

MANIFEST_NAME = re.compile(r'"stacks/([^/"]+)/')


def package_owned(instance: Path) -> frozenset[str]:
    """The stack names the package owns: the bundled ones plus any the instance's manifest lists (a stack a newer
    install no longer ships stays the package's)."""
    from nexahome.instance import bundle, manifest

    names: set[str] = set()
    source = bundle.location()
    if source is not None:
        names |= {entry.name for entry in source.iterdir() if entry.is_dir() and bundle.wanted(entry.name)}
    try:
        with open(instance / manifest.PATH, "rb") as handle:
            names |= set(MANIFEST_NAME.findall(handle.read(STACK_FILE_MAX_BYTES).decode(errors="replace")))
    except OSError:
        pass  # a clone, or an instance without a manifest: the bundle alone decides
    return frozenset(names)
