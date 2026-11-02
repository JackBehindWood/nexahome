"""What every command module provides."""

import argparse
from collections.abc import Callable
from typing import Protocol

from nexahome.context import Context

type Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]


class Command(Protocol):
    """Command modules satisfy this structurally: a NAME, register() and run()."""

    NAME: str
    register: Callable[[Subparsers], None]
    run: Callable[[argparse.Namespace, Context], int]
