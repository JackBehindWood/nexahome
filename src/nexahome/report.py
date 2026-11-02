"""Check results shared by every command that reports on the host (doctor now, smoke later).

JSON, schema 1 (`--json`):
    {"schema": 1, "ok": true|false,
     "checks": [{"id": str, "status": "ok"|"warn"|"fail"|"skip", "summary": str, "fix": str|null}]}
`ok` is false when any check is "fail". `fix` is one exact command and is set for "warn" and "fail" only.
Check ids are a public contract: they are added, never renamed.
"""

from collections.abc import Sequence
from enum import StrEnum
from typing import NamedTuple

SCHEMA = 1


class Status(StrEnum):
    """The result of one check; `SKIP` means a prerequisite failed."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"  # not run because a prerequisite failed


class _CheckFields(NamedTuple):
    id: str
    status: Status
    summary: str
    fix: str | None = None


class Check(_CheckFields):
    """One finding. A warn or fail carries one fix command; the other statuses carry none."""

    __slots__ = ()

    def __new__(cls, id: str, status: Status, summary: str, fix: str | None = None) -> "Check":
        needs_fix = status in (Status.WARN, Status.FAIL)
        if needs_fix and not (fix and fix.strip()):
            raise ValueError(f"check {id}: a {status} needs a fix command")
        if not needs_fix and fix is not None:
            raise ValueError(f"check {id}: only a warn or fail carries a fix")
        return super().__new__(cls, id, status, summary, fix)


def passed(checks: Sequence[Check]) -> bool:
    """True unless some check failed; warnings do not fail a run."""
    return all(check.status != Status.FAIL for check in checks)


def render_text(checks: Sequence[Check]) -> str:
    """One line per check, `fix:` lines under problems, and a last line that ends in the next command to run."""
    lines = []
    for check in checks:
        lines.append(f"{check.status:<6}{check.id:<12}{check.summary}")
        if check.fix:
            lines.append(f"      fix: {check.fix}")
    problems = [c for c in checks if c.status == Status.FAIL]
    warnings = [c for c in checks if c.status == Status.WARN]
    if problems:
        count = len(problems)
        lines.append(f"{count} problem{'s' * (count != 1)}. Next: {problems[0].fix}")
    elif warnings:
        count = len(warnings)
        lines.append(f"ok with {count} warning{'s' * (count != 1)}. Next: {warnings[0].fix}")
    else:
        lines.append("all checks passed")
    return "\n".join(lines)


def render_json(checks: Sequence[Check]) -> str:
    """The checks as JSON, schema 1: `{schema, ok, checks: [{id, status, summary, fix}]}`."""
    import json  # only a --json run needs it

    rows = [{"id": c.id, "status": c.status, "summary": c.summary, "fix": c.fix} for c in checks]
    return json.dumps({"schema": SCHEMA, "ok": passed(checks), "checks": rows}, indent=2)
