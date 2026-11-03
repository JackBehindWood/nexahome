"""Which stacks exist and which this host runs (mirrors the Makefile's ALL and STACKS; PK7 will own it)."""

from pathlib import Path

from nexahome.defaults import CORE_STACKS, NON_SERVICE_STACKS
from nexahome.instance import CONFIG_NAME



def all_stacks(checkout: Path) -> list[str]:
    """Every directory under stacks/ with a compose.yaml, except the template."""
    found = sorted(d.name for d in (checkout / "stacks").iterdir() if (d / "compose.yaml").is_file())
    return [name for name in found if name != "_template"]


def enabled(checkout: Path) -> list[str]:
    """The stacks this host runs: the list in nexahome.toml (an instance), else the names in .config/stacks (a clone,
    this host only) if it lists any, else every stack except the template and the backup tool; core stacks first."""
    names: list[str] = []
    if (checkout / CONFIG_NAME).is_file():  # an instance made by `nexahome init`: its settings name the stacks
        from nexahome.instance import config

        settings = config.read(checkout)
        names = list(settings.stacks) if settings else []
    else:
        try:
            names = (checkout / ".config" / "stacks").read_text().split()
        except OSError:
            pass
    if not names:
        names = [n for n in all_stacks(checkout) if n not in NON_SERVICE_STACKS]
    return [n for n in names if n in CORE_STACKS] + [n for n in names if n not in CORE_STACKS]


def compose_file(checkout: Path, name: str) -> Path:
    return checkout / "stacks" / name / "compose.yaml"
