import json

import pytest

from nexahome.report import Check, Status, passed, render_json, render_text


def test_warn_and_fail_need_a_fix() -> None:
    for status in (Status.WARN, Status.FAIL):
        with pytest.raises(ValueError):
            Check("x", status, "broken")
        with pytest.raises(ValueError):
            Check("x", status, "broken", "  ")


def test_ok_and_skip_carry_no_fix() -> None:
    for status in (Status.OK, Status.SKIP):
        with pytest.raises(ValueError):
            Check("x", status, "fine", "echo hi")


def test_text_rendering_names_the_first_fix() -> None:
    checks = [
        Check("platform", Status.OK, "Linux amd64"),
        Check("engine", Status.FAIL, "no container runtime running", "colima start"),
        Check("compose", Status.SKIP, "needs docker-cli"),
        Check("disk", Status.WARN, "low", "df -h ."),
    ]
    assert render_text(checks).splitlines() == [
        "ok    platform    Linux amd64",
        "fail  engine      no container runtime running",
        "      fix: colima start",
        "skip  compose     needs docker-cli",
        "warn  disk        low",
        "      fix: df -h .",
        "1 problem. Next: colima start",
    ]


def test_text_rendering_summaries() -> None:
    assert render_text([Check("a", Status.OK, "fine")]).splitlines()[-1] == "all checks passed"
    warned = [Check("a", Status.WARN, "meh", "true"), Check("b", Status.WARN, "meh", "false")]
    assert render_text(warned).splitlines()[-1] == "ok with 2 warnings. Next: true"


def test_json_schema_1() -> None:
    checks = [Check("platform", Status.OK, "Linux amd64"), Check("engine", Status.FAIL, "down", "colima start")]
    payload = json.loads(render_json(checks))
    assert payload == {
        "schema": 1,
        "ok": False,
        "checks": [
            {"id": "platform", "status": "ok", "summary": "Linux amd64", "fix": None},
            {"id": "engine", "status": "fail", "summary": "down", "fix": "colima start"},
        ],
    }
    assert passed(checks[:1]) and not passed(checks)
