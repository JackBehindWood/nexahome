"""The commands, found automatically: every module here that provides NAME, register() and run().

To add a command, add a module to this folder (see doctor.py); nothing else is registered by hand.
A module whose name starts with an underscore is a helper, not a command. Commands are listed in
alphabetical order of their module name.
"""

import importlib
import pkgutil

from nexahome.commands._base import Command


def discover() -> tuple[Command, ...]:
    found: list[Command] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda module: module.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        if not isinstance(module, Command):
            raise TypeError(f"commands/{info.name}.py must define NAME, register() and run(); rename it _{info.name}.py if it is a helper")
        found.append(module)
    return tuple(found)


COMMANDS: tuple[Command, ...] = discover()
