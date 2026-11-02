"""Which stacks exist and which this host runs (mirrors the Makefile's ALL and STACKS; PK7 will own it)."""

from pathlib import Path

CORE = ("edge", "identity")  # started first, as the Makefile does
NOT_SERVICES = ("_template", "backup")  # the template, and the one-shot backup tool


def all_stacks(checkout: Path) -> list[str]:
    """Every directory under stacks/ with a compose.yaml, except the template."""
    found = sorted(d.name for d in (checkout / "stacks").iterdir() if (d / "compose.yaml").is_file())
    return [name for name in found if name != "_template"]


def enabled(checkout: Path) -> list[str]:
    """The stacks this host runs: the names in .config/stacks (this host only) if it lists any, else every
    stack except the template and the backup tool; core stacks first."""
    names: list[str] = []
    try:
        names = (checkout / ".config" / "stacks").read_text().split()
    except OSError:
        pass
    if not names:
        names = [n for n in all_stacks(checkout) if n not in NOT_SERVICES]
    return [n for n in names if n in CORE] + [n for n in names if n not in CORE]


def compose_file(checkout: Path, name: str) -> Path:
    return checkout / "stacks" / name / "compose.yaml"
