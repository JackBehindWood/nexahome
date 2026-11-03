"""`nexahome.toml`: the settings of an instance (schema 1: which stacks this host runs).

Read strictly and written whole, atomically, by `nexahome config`. The standard library reads TOML but does
not write it; this schema has three value types, so the writer is a few lines here instead of a dependency.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from nexahome import __version__
from nexahome.errors import ExitCode, NexaHomeError
from nexahome.defaults import CONFIG_MAX_BYTES, INSTANCE_SCHEMA, PUBLIC_FILE_MODE
from nexahome.instance import CONFIG_NAME

if TYPE_CHECKING:
    from collections.abc import Sequence

HEADER = "# Managed by `nexahome config`. Comments added by hand are not kept when it rewrites this file.\n"


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(stacks: tuple[str, ...] | list[str], created_by: str | None = None) -> str:
    """The file text, keys in a fixed order."""
    names = ", ".join(_quote(name) for name in stacks)
    return f"{HEADER}schema = {INSTANCE_SCHEMA}\ncreated_by = {_quote(created_by or f'nexahome {__version__}')}\nstacks = [{names}]\n"


class Settings(NamedTuple):
    schema: int
    created_by: str
    stacks: tuple[str, ...]


KEYS = ("schema", "created_by", "stacks")
SETTABLE = ("stacks",)  # schema and created_by describe the file; only `nexahome init` writes them
STACK_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*")  # also keeps a name from being a path


def _editor_fix(path: Path) -> str:
    import shlex

    return f"${{EDITOR:-vi}} {shlex.quote(str(path))}"


def validate_stacks(directory: Path, names: Sequence[object], fix: str, exit_code: ExitCode = ExitCode.NOT_READY) -> tuple[str, ...]:
    """The names as a tuple: at least one, each a stack under directory/stacks, no repeats. `fix` is the command
    named when one is wrong."""
    if not names:
        raise NexaHomeError("stacks must name at least one stack (an empty list would mean 'use the default')", fix, exit_code)
    clean: list[str] = []
    for name in names:
        if not isinstance(name, str) or not STACK_NAME.fullmatch(name):
            raise NexaHomeError(f"stacks: {name!r} is not a stack name (lower-case letters, digits, - and _)", fix, exit_code)
        if not (directory / "stacks" / name / "compose.yaml").is_file():
            raise NexaHomeError(f"stacks: there is no stack called {name!r} in {directory / 'stacks'}", fix, exit_code)
        if name not in clean:
            clean.append(name)
    return tuple(clean)


def read(directory: Path) -> Settings | None:
    """The settings of the instance in `directory`; None when it has no nexahome.toml (a clone). Strict: an unknown
    key, a wrong type, bad TOML, an unknown stack or a newer schema raises NexaHomeError naming one command."""
    import tomllib  # about 5 ms: only a command that reads the settings pays for it

    path = directory / CONFIG_NAME
    try:
        with open(path, "rb") as handle:
            raw = handle.read(CONFIG_MAX_BYTES + 1)
    except FileNotFoundError:
        return None
    edit = _editor_fix(path)
    if len(raw) > CONFIG_MAX_BYTES:
        raise NexaHomeError(f"{CONFIG_NAME} is larger than {CONFIG_MAX_BYTES} bytes", edit)
    try:
        data = tomllib.loads(raw.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise NexaHomeError(f"{CONFIG_NAME} is not valid TOML: {error}", edit) from error
    schema = data.get("schema")
    if not isinstance(schema, int) or isinstance(schema, bool) or schema < 1:
        raise NexaHomeError(f"{CONFIG_NAME}: schema must be a number (this version writes {INSTANCE_SCHEMA})", edit)
    if schema > INSTANCE_SCHEMA:
        raise NexaHomeError(f"{CONFIG_NAME} has schema {schema}; this nexahome understands up to {INSTANCE_SCHEMA}", "nexahome update --available")
    unknown = sorted(set(data) - set(KEYS))
    if unknown:
        raise NexaHomeError(f"{CONFIG_NAME}: unknown key {', '.join(unknown)} (schema {INSTANCE_SCHEMA} has {', '.join(KEYS)})", edit)
    created_by = data.get("created_by", "")
    stacks = data.get("stacks")
    if not isinstance(created_by, str) or not isinstance(stacks, list):
        raise NexaHomeError(f"{CONFIG_NAME}: created_by must be text and stacks a list of names", edit)
    return Settings(schema, created_by, validate_stacks(directory, stacks, edit))


def write(directory: Path, stacks: Sequence[str]) -> None:
    """Replace nexahome.toml with `stacks` (names already validated), keeping created_by. All or nothing: the new text
    is written beside the file and renamed over it."""
    import tempfile

    try:
        current = read(directory)
    except NexaHomeError:
        current = None  # a file that cannot be read is replaced whole; that is how `config set` repairs it
    text = render(stacks, current.created_by if current and current.created_by else None)
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=f".{CONFIG_NAME}.")
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
        os.chmod(temporary, PUBLIC_FILE_MODE)
        os.replace(temporary, directory / CONFIG_NAME)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
