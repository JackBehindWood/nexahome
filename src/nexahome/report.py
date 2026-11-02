"""Check results shared by every command that reports on the host (doctor now, smoke later).

JSON, schema 1 (`--json`):
    {"schema": 1, "ok": true|false,
     "checks": [{"id": str, "status": "ok"|"warn"|"fail"|"skip", "summary": str, "fix": str|null}]}
`ok` is false when any check is "fail". `fix` is one exact command and is set for "warn" and "fail" only.
Check ids are a public contract: they are added, never renamed.
"""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum

SCHEMA = 1


class Status(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"  # not run because a prerequisite failed


@dataclass(frozen=True)
class Check:
    id: str
    status: Status
    summary: str
    fix: str | None = None

    def __post_init__(self) -> None:
        needs_fix = self.status in (Status.WARN, Status.FAIL)
        if needs_fix and not (self.fix and self.fix.strip()):
            raise ValueError(f"check {self.id}: a {self.status} needs a fix command")
        if not needs_fix and self.fix is not None:
            raise ValueError(f"check {self.id}: only a warn or fail carries a fix")


def passed(checks: Sequence[Check]) -> bool:
    return all(check.status != Status.FAIL for check in checks)


def render_text(checks: Sequence[Check]) -> str:
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
    payload = {"schema": SCHEMA, "ok": passed(checks), "checks": [asdict(check) for check in checks]}
    return json.dumps(payload, indent=2)
