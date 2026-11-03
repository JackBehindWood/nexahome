"""Version numbers, compared without the `packaging` library: N(.N)* with an optional dev, a, b or rc suffix."""

import re

_PATTERN = re.compile(r"^v?(\d+(?:\.\d+)*)(?:\.?(dev|a|b|rc)(\d+))?$")
_STAGE = {"dev": 0, "a": 1, "b": 2, "rc": 3}
_FINAL = 4

type Key = tuple[tuple[int, ...], int, int]


def parse(text: str) -> Key:
    """A sortable key. Raises ValueError for anything else (post-releases and local versions are not used)."""
    match = _PATTERN.match(text.strip())
    if match is None:
        raise ValueError(f"not a version number: {text!r}")
    release = [int(part) for part in match.group(1).split(".")]
    while len(release) > 1 and release[-1] == 0:  # 1.0 == 1.0.0
        release.pop()
    if match.group(2) is None:
        return tuple(release), _FINAL, 0
    return tuple(release), _STAGE[match.group(2)], int(match.group(3))


def is_newer(candidate: str, installed: str) -> bool:
    return parse(candidate) > parse(installed)
