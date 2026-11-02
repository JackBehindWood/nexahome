"""What every command module provides (modules whose names start with an underscore are not commands)."""

import argparse
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from nexahome.context import Context

type Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]


@runtime_checkable
class Command(Protocol):
    """Command modules satisfy this structurally: a NAME, register() and run()."""

    NAME: str
    register: Callable[[Subparsers], None]
    run: Callable[[argparse.Namespace, Context], int]
