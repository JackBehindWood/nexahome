"""The registered commands. To add one: a module here with NAME, register() and run(), one line in COMMANDS."""

import argparse
from collections.abc import Callable
from typing import Protocol

from nexahome.context import Context

type Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]


class Command(Protocol):
    """What a command module provides (modules satisfy this structurally)."""

    NAME: str
    register: Callable[[Subparsers], None]
    run: Callable[[argparse.Namespace, Context], int]


COMMANDS: tuple[Command, ...] = ()
