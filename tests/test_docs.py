"""The documentation set stays true to the repository (PK-A1): headers, links, labels, commands, Dependabot."""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
pytestmark = pytest.mark.skipif(not DOCS.is_dir(), reason="the docs are not in this tree (an sdist ships tests without them)")

# Files that carry the version header and the one-line changelog (docs/README.md, Conventions).
HEADERED = sorted([*DOCS.glob("*.md"), *(DOCS / "runbooks").glob("*.md")])
HEADERED = [p for p in HEADERED if p.name != "session-log.md"]
LABELS = re.compile(r"\b(?:Confirmed|Proposed)\b")  # "Open" is also an ordinary verb, so it is not checked
LABEL_HOMES = {"project.md", "session-log.md", "README.md"}  # README.md states the rule itself
ROOT_DOCS = [REPO / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md")]  # CLAUDE.md is local only
MARKDOWN = sorted([*ROOT_DOCS, *DOCS.rglob("*.md"), *(REPO / "stacks").glob("*/README.md")])
# ADRs and the log record what was planned, rejected or cut, so they may name commands that do not exist.
CURRENT = [p for p in MARKDOWN if p.parent != DOCS / "adr" and p.name != "session-log.md"]


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


@pytest.mark.parametrize("path", HEADERED, ids=rel)
def test_header_and_changelog_dates_agree(path: Path) -> None:
    text = path.read_text()
    header = re.search(r"^Version 0\.1 · Last reviewed (\d{4}-\d\d-\d\d)$", text, re.M)
    last = text.rstrip("\n").splitlines()[-1]
    assert header, f"{rel(path)}: no 'Version 0.1 · Last reviewed <date>' line"
    assert last.startswith("Changelog: "), f"{rel(path)}: the last line is not the changelog"
    newest = re.search(r"\((\d{4}-\d\d-\d\d)\)", last)
    assert newest and newest.group(1) == header.group(1), f"{rel(path)}: header {header.group(1)}, newest changelog entry {newest and newest.group(1)}"


def test_status_labels_appear_only_in_the_register_and_the_adrs() -> None:
    found = []
    for path in MARKDOWN:
        if path.name in LABEL_HOMES or path.parent == DOCS / "adr":
            continue
        found += [f"{rel(path)}:{n}" for n, line in enumerate(path.read_text().splitlines(), 1) if LABELS.search(line)]
    assert found == []


LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


@pytest.mark.parametrize("path", MARKDOWN, ids=rel)
def test_relative_links_resolve(path: Path) -> None:
    broken = []
    for target in LINK.findall(path.read_text()):
        if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue  # a URL or an anchor in the same file
        if not (path.parent / target.split("#", 1)[0]).exists():
            broken.append(target)
    assert broken == [], f"{rel(path)}: links that do not resolve"


# Named in the docs on purpose before they exist (planned) or after being cut (with a trigger). Remove an entry
# when the command is built or the sentence goes.
PLANNED_OR_CUT = {"nexahome up", "make upgrade", "make mini-check"}  # `nexahome up`: PK7, named in the runner quick start


def test_documented_make_and_nexahome_commands_exist() -> None:
    makefile = (REPO / "Makefile").read_text()
    targets = set(re.findall(r"^([a-z][a-z-]*):", makefile, re.M))
    commands = {p.stem for p in (REPO / "src" / "nexahome" / "commands").glob("*.py") if not p.stem.startswith("_")}
    missing = []
    for path in CURRENT:
        for n, line in enumerate(path.read_text().splitlines(), 1):
            for span in re.findall(r"`([^`]+)`", line):
                words = span.split()
                if span in PLANNED_OR_CUT:
                    continue
                if len(words) >= 2 and words[0] == "make" and re.fullmatch(r"[a-z][a-z-]*", words[1]) and words[1] not in targets:
                    missing.append(f"{rel(path)}:{n}: {span}")
                if len(words) >= 2 and words[0] == "nexahome" and re.fullmatch(r"[a-z][a-z-]*", words[1]) and words[1] not in commands:
                    missing.append(f"{rel(path)}:{n}: {span}")
    assert missing == []


def test_every_stack_has_a_dependabot_entry() -> None:
    config = (REPO / ".github" / "dependabot.yml").read_text()
    covered = set(re.findall(r"directory: /stacks/([\w-]+)", config))
    stacks = {p.parent.name for p in (REPO / "stacks").glob("*/compose.yaml") if p.parent.name != "_template"}
    assert stacks - covered == set()
