"""The commands, found automatically: every module here that provides NAME, register() and run().

To add a command, add a module to this folder named after the command (see doctor.py); nothing is registered by
hand. A module whose name starts with an underscore is a helper, not a command. Commands are loaded one at a time:
running `nexahome doctor` imports doctor.py only, so a command pays for its own imports and no other.
"""

from __future__ import annotations

import importlib
import os
from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nexahome.commands._base import Command


def names() -> tuple[str, ...]:
    """The command names, from the file names, without importing anything."""
    folder = os.path.dirname(__file__)
    return tuple(sorted(f[:-3] for f in os.listdir(folder) if f.endswith(".py") and not f.startswith("_")))


@cache
def load(name: str) -> "Command":
    module = importlib.import_module(f"{__name__}.{name}")
    if not all(hasattr(module, attribute) for attribute in ("NAME", "register", "run")) or module.NAME != name:
        raise TypeError(
            f"commands/{name}.py must define NAME = {name!r}, register() and run(); rename it _{name}.py if it is a helper"
        )
    command: "Command" = module  # a module with these attributes satisfies Command
    return command


def load_all() -> "tuple[Command, ...]":
    return tuple(load(name) for name in names())


def __getattr__(attribute: str) -> "tuple[Command, ...]":
    if attribute == "COMMANDS":  # loaded on first use, not on import
        return load_all()
    raise AttributeError(f"module {__name__!r} has no attribute {attribute!r}")
