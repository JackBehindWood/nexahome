import pytest

from nexahome.release import versions


@pytest.mark.parametrize(
    ("candidate", "installed", "newer"),
    [
        ("0.2.0", "0.1.0", True),
        ("v0.1.1", "0.1.0", True),
        ("0.1.0", "0.1.0.dev0", True),  # a release is newer than its development version
        ("0.1.0", "0.1.0", False),
        ("0.1.0.dev0", "0.1.0", False),
        ("0.1.0", "0.1", False),  # trailing zeros do not count
        ("0.1.0a1", "0.1.0.dev9", True),
        ("0.1.0rc1", "0.1.0b2", True),
        ("0.1.0", "0.1.0rc1", True),
        ("0.9.0", "0.10.0", False),  # numbers, not strings
        ("1.0", "0.99.99", True),
        ("0.1.0.1", "0.1.0", True),
    ],
)
def test_ordering(candidate: str, installed: str, newer: bool) -> None:
    assert versions.is_newer(candidate, installed) is newer


@pytest.mark.parametrize("bad", ["", "latest", "1.x", "1.0.post1", "1.0+local", "v", "1..0"])
def test_unreadable_versions_are_refused(bad: str) -> None:
    with pytest.raises(ValueError):
        versions.parse(bad)
