"""Per-stack .env files: placeholders, generated secrets, and the bootstrap from .env.example.

This is the file part of `make up` (the Makefile stays the caller until the run path moves, PK7). Values are
never returned for printing; only key names are.
"""

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

PLACEHOLDER = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=CHANGE_ME", re.MULTILINE)
GENERATE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=GENERATE$", re.MULTILINE)
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SECRET_LENGTH = 48


def placeholders(text: str) -> list[str]:
    """Keys whose value is still CHANGE_ME."""
    return PLACEHOLDER.findall(text)


def new_secret() -> str:
    import secrets  # imports random, hashlib and more: only a run that generates a secret pays for it

    return "".join(secrets.choice(ALPHABET) for _ in range(SECRET_LENGTH))


def generate_secrets(text: str, make: Callable[[], str] = new_secret) -> tuple[str, list[str]]:
    """Replace every KEY=GENERATE line by a fresh secret. Returns the new text and the keys, never the values."""
    keys: list[str] = []

    def fill(match: re.Match[str]) -> str:
        keys.append(match.group(1))
        return f"{match.group(1)}={make()}"

    return GENERATE.sub(fill, text), keys


def read_value(text: str, key: str) -> str | None:
    """The value of the first KEY=value line, without surrounding quotes."""
    match = re.search(rf"^{re.escape(key)}=(.*)$", text, re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else None


class EnvResult(NamedTuple):
    path: Path
    created: bool  # copied from .env.example
    generated: tuple[str, ...]  # keys that received a generated secret
    pending: tuple[str, ...]  # keys still CHANGE_ME: the user must set them


def _write_new(path: Path, text: str) -> None:
    """Create a private file; never overwrite."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)


def _replace_private(path: Path, text: str) -> None:
    import tempfile

    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".env.")  # created mode 600
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def prepare(stack_dir: Path, *, dry_run: bool = False, make: Callable[[], str] = new_secret) -> EnvResult | None:
    """Create .env from .env.example when absent, then generate secrets once no CHANGE_ME is left.

    Safe to repeat: an existing .env is only rewritten to fill GENERATE lines. None when the stack has no
    .env and no .env.example."""
    env, example = stack_dir / ".env", stack_dir / ".env.example"
    created = False
    if env.exists():
        text = env.read_text()
    elif example.is_file():
        created, text = True, example.read_text()
        if not dry_run:
            _write_new(env, text)
    else:
        return None
    pending = placeholders(text)
    generated: list[str] = []
    if not pending and GENERATE.search(text):
        text, generated = generate_secrets(text, make)
        if not dry_run:
            _replace_private(env, text)
    return EnvResult(env, created, tuple(generated), tuple(pending))
