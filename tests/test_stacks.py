"""Which stacks exist and run (`stacks.catalogue`) and the `nexahome stacks` listing, through cli.main."""

import json
from pathlib import Path

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult
from nexahome.stacks import catalogue as stacks

from conftest import FakeRunner, MakeCheckout, MakeContext, out, ps_running_argv


def test_all_stacks_skips_the_template_and_directories_without_compose(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"_template": None, "actual": None, "backup": None, "edge": None})
    (checkout / "stacks" / "notes").mkdir()
    assert stacks.all_stacks(checkout) == ["actual", "backup", "edge"]


def test_default_enabled_drops_the_backup_tool_and_puts_core_first(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"_template": None, "actual": None, "backup": None, "edge": None, "identity": None, "zeta": None})
    assert stacks.enabled(checkout) == ["edge", "identity", "actual", "zeta"]


def test_the_host_list_overrides_the_default(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"actual": None, "edge": None, "hello": None})
    (checkout / ".config").mkdir()
    (checkout / ".config" / "stacks").write_text("hello\nedge\n")
    assert stacks.enabled(checkout) == ["edge", "hello"]
    (checkout / ".config" / "stacks").write_text("\n  \n")  # blank means: use the default
    assert stacks.enabled(checkout) == ["edge", "actual", "hello"]


def test_compose_file(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"demo": None})
    assert stacks.compose_file(checkout, "demo") == Path(checkout) / "stacks" / "demo" / "compose.yaml"


STATE_UNKNOWN = "state unknown: Docker did not answer; start it, or run: nexahome doctor"


def ps_q(checkout: Path, name: str) -> tuple[str, ...]:
    return ps_running_argv(checkout / "stacks" / name / "compose.yaml")


def test_stacks_lists_enabled_and_state(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"actual": None, "backup": None, "edge": None})
    runner = FakeRunner({ps_q(checkout, "edge"): RunResult(0, "abc123\n"), ps_q(checkout, "actual"): RunResult(0, "")})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["stacks"], ctx) == ExitCode.OK
    assert out(ctx).splitlines() == [
        "stack   enabled  owner    state",
        "actual  yes      package  stopped",
        "backup  no       package  unknown",
        "edge    yes      package  running",
        STATE_UNKNOWN,
    ]


def test_stacks_without_an_unknown_state_has_no_footer(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    """A-07: the footer appears only when a state could not be read."""
    checkout = make_checkout({"edge": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner({ps_q(checkout, "edge"): RunResult(0, "abc123\n")}))
    assert cli.main(["stacks"], ctx) == ExitCode.OK
    assert "unknown" not in out(ctx)


def test_stacks_says_why_a_state_is_unknown(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    ctx = make_context(cwd=make_checkout({"edge": None}), runner=FakeRunner())  # Docker answers nothing
    assert cli.main(["stacks"], ctx) == ExitCode.OK
    assert out(ctx).splitlines()[-1] == STATE_UNKNOWN
    ctx = make_context(cwd=make_checkout({"edge": None}, root=ctx.cwd.parent / "again"), runner=FakeRunner())
    assert cli.main(["stacks", "--json"], ctx) == ExitCode.OK
    assert STATE_UNKNOWN not in out(ctx)  # the JSON already says "unknown"; no prose in it


def test_stacks_json(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"edge": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner({ps_q(checkout, "edge"): RunResult(0, "id\n")}))
    assert cli.main(["stacks", "--json"], ctx) == ExitCode.OK
    assert json.loads(out(ctx)) == {"schema": 1, "stacks": [{"name": "edge", "enabled": True, "owner": "package", "state": "running"}]}
