"""The check, env, stacks and status commands, through cli.main with injected docker answers."""

import json
import stat
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult, SubprocessRunner

from conftest import DOCKER_HEALTHY, REPO, FakeRunner, MakeCheckout, MakeContext, MakeHost, has_compose

INFO = ("docker", "info", "--format", "{{.ServerVersion}}")


def out(ctx: object) -> str:
    return ctx.out.getvalue()  # type: ignore[attr-defined]


def err(ctx: object) -> str:
    return ctx.err.getvalue()  # type: ignore[attr-defined]


# --- check -------------------------------------------------------------------------------------------------
def config_argv(checkout: Path, name: str) -> tuple[str, ...]:
    return ("docker", "compose", "-f", str(checkout / "stacks" / name / "compose.yaml"), "config", "--format", "json")


GOOD_CONFIG = json.dumps(
    {"name": "nexahome-demo", "services": {"app": {"image": "x/y:1", "healthcheck": {}, "restart": "always"}}}
)


def test_check_passes_and_prints_the_originals_line(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout()
    ctx = make_context(cwd=checkout, runner=FakeRunner({config_argv(checkout, "demo"): RunResult(0, GOOD_CONFIG)}))
    assert cli.main(["check"], ctx) == ExitCode.OK
    assert out(ctx) == "stacks/demo/compose.yaml: ok\n"


def test_check_fails_with_exit_1_on_a_policy_problem(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    bad = json.dumps({"name": "nexahome-demo", "services": {"app": {"image": "x/y:1", "healthcheck": {}, "restart": "always", "privileged": True}}})
    checkout = make_checkout()
    ctx = make_context(cwd=checkout, runner=FakeRunner({config_argv(checkout, "demo"): RunResult(0, bad)}))
    assert cli.main(["check"], ctx) == ExitCode.FAILED
    assert out(ctx) == "stacks/demo/compose.yaml: app: privileged is not allowed\n"


def test_check_reports_a_compose_failure_and_exits_1(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout()
    ctx = make_context(cwd=checkout, runner=FakeRunner({config_argv(checkout, "demo"): RunResult(1, stderr="bad yaml")}))
    assert cli.main(["check"], ctx) == ExitCode.FAILED
    assert "docker compose config failed\nbad yaml" in err(ctx)


def test_check_without_docker_ends_in_an_install_command(make_checkout: MakeCheckout, make_context: MakeContext, make_host: MakeHost) -> None:
    ctx = make_context(host=make_host(system="macos"), cwd=make_checkout(), runner=FakeRunner())
    assert cli.main(["check"], ctx) == ExitCode.NOT_READY
    assert err(ctx) == "FAIL  docker CLI not found; cannot validate stacks\nNext: brew install colima docker docker-compose\n"


def test_check_with_no_stacks_has_nothing_to_check(make_context: MakeContext, tmp_path: Path) -> None:
    ctx = make_context(cwd=tmp_path / "empty")  # no stacks/ here
    assert cli.main(["check"], ctx) == ExitCode.NOT_READY
    assert err(ctx).startswith("FAIL  no stacks found in ") and err(ctx).endswith("; nothing to check\nNext: nexahome init\n")


def test_check_takes_another_stacks_folder(make_checkout: MakeCheckout, make_context: MakeContext, tmp_path: Path) -> None:
    other = make_checkout(root=tmp_path / "other")
    ctx = make_context(cwd=tmp_path, runner=FakeRunner({config_argv(other, "demo"): RunResult(0, GOOD_CONFIG)}))
    assert cli.main(["check", "--stacks", "other/stacks"], ctx) == ExitCode.OK
    assert out(ctx) == "other/stacks/demo/compose.yaml: ok\n"


@pytest.mark.skipif(not has_compose(), reason="needs the Docker CLI with the Compose plugin (no engine)")
def test_check_passes_on_the_real_stacks(make_context: MakeContext) -> None:
    ctx = make_context(cwd=REPO, runner=SubprocessRunner())
    names = sorted(p.parent.name for p in (REPO / "stacks").glob("*/compose.yaml"))
    assert cli.main(["check"], ctx) == ExitCode.OK
    assert out(ctx) == "".join(f"stacks/{n}/compose.yaml: ok\n" for n in names)


# --- env ---------------------------------------------------------------------------------------------------
def test_env_creates_env_files_generates_secrets_and_lists_what_the_user_must_set(
    make_checkout: MakeCheckout, make_context: MakeContext
) -> None:
    checkout = make_checkout({"demo": "TOKEN=GENERATE\nPORT=8080\n", "actual": "NAME=CHANGE_ME\nKEY=GENERATE\n", "plain": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["env"], ctx) == ExitCode.NOT_READY  # actual still needs a value
    text = out(ctx)
    assert "created stacks/demo/.env from .env.example" in text
    assert "generated secrets in stacks/demo/.env (not shown); copy them to your password manager" in text
    assert "stacks/actual/.env: set a real value for each of these, then run nexahome env again:\n  NAME\n" in text
    token = (checkout / "stacks" / "demo" / ".env").read_text().splitlines()[0].split("=", 1)[1]
    assert len(token) == 48 and token not in text and token not in err(ctx)
    assert stat.S_IMODE((checkout / "stacks" / "demo" / ".env").stat().st_mode) == 0o600
    assert "GENERATE" in (checkout / "stacks" / "actual" / ".env").read_text()  # waits for NAME
    assert not (checkout / "stacks" / "plain" / ".env").exists()


def test_env_succeeds_once_nothing_is_pending_and_is_then_idempotent(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"demo": "TOKEN=GENERATE\n"})
    first = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["env"], first) == ExitCode.OK and out(first).endswith("Next: make up\n")
    before = (checkout / "stacks" / "demo" / ".env").read_text()
    second = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["env"], second) == ExitCode.OK
    assert "ok    stacks/demo/.env is ready" in out(second)
    assert (checkout / "stacks" / "demo" / ".env").read_text() == before


def test_env_dry_run_writes_nothing(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"demo": "TOKEN=GENERATE\n"})
    ctx = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY))
    cli.main(["env", "--dry-run"], ctx)
    assert "would create stacks/demo/.env from .env.example" in out(ctx)
    assert "would generate 1 secret(s) in stacks/demo/.env" in out(ctx)
    assert not (checkout / "stacks" / "demo" / ".env").exists()


def test_env_refuses_to_write_secrets_where_git_would_commit_them(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"demo": "TOKEN=GENERATE\n"})
    check_ignore = ("git", "-C", str(checkout), "check-ignore", "-q", "stacks/demo/.env")
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, check_ignore: RunResult(1)}))
    assert cli.main(["env"], ctx) == ExitCode.NOT_READY
    assert err(ctx) == "FAIL  stacks/demo/.env is not gitignored; refusing to write secrets there\nNext: git check-ignore -v stacks/demo/.env\n"
    assert not (checkout / "stacks" / "demo" / ".env").exists()
    ignored = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, check_ignore: RunResult(0)}))
    assert cli.main(["env"], ignored) == ExitCode.OK


def test_env_one_stack_and_an_unknown_one(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"demo": "A=1\n", "other": "B=2\n"})
    ctx = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY))
    cli.main(["env", "--stack", "demo"], ctx)
    assert (checkout / "stacks" / "demo" / ".env").exists() and not (checkout / "stacks" / "other" / ".env").exists()
    bad = make_context(cwd=checkout)
    assert cli.main(["env", "--stack", "nope"], bad) == ExitCode.NOT_READY
    assert err(bad) == "FAIL  no such stack: nope\nNext: nexahome stacks\n"


def test_env_reports_a_stopped_engine_through_doctor(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"demo": "A=1\n"})
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, INFO: RunResult(1)}))
    assert cli.main(["env"], ctx) == ExitCode.NOT_READY
    assert "Next: sudo systemctl start docker" in out(ctx) and "Next: make up" not in out(ctx)


# --- commands that need a checkout -------------------------------------------------------------------------
@pytest.mark.parametrize("command", ["env", "stacks", "status"])
def test_commands_outside_a_checkout_say_so(command: str, make_context: MakeContext, tmp_path: Path) -> None:
    ctx = make_context(cwd=tmp_path)
    assert cli.main([command], ctx) == ExitCode.NOT_READY
    assert err(ctx).startswith("FAIL  no NexaHome instance here") and err(ctx).endswith("\nNext: nexahome init\n")


def test_nexahome_home_selects_the_checkout_from_anywhere(make_checkout: MakeCheckout, make_context: MakeContext, tmp_path: Path) -> None:
    checkout = make_checkout({"demo": None})
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    ctx = make_context(cwd=elsewhere, env={"NEXAHOME_HOME": str(checkout)}, runner=FakeRunner())
    assert cli.main(["stacks"], ctx) == ExitCode.OK and "demo" in out(ctx)
    wrong = make_context(cwd=checkout, env={"NEXAHOME_HOME": str(elsewhere)})
    assert cli.main(["stacks"], wrong) == ExitCode.NOT_READY
    assert err(wrong).startswith("FAIL  NEXAHOME_HOME does not point at a NexaHome instance or clone") and 'Next: ls "$NEXAHOME_HOME"' in err(wrong)


# --- stacks ------------------------------------------------------------------------------------------------
def ps_q(checkout: Path, name: str) -> tuple[str, ...]:
    return ("docker", "compose", "-f", str(checkout / "stacks" / name / "compose.yaml"), "ps", "--status", "running", "-q")


def test_stacks_lists_enabled_and_state(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"actual": None, "backup": None, "edge": None})
    runner = FakeRunner({ps_q(checkout, "edge"): RunResult(0, "abc123\n"), ps_q(checkout, "actual"): RunResult(0, "")})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["stacks"], ctx) == ExitCode.OK
    assert out(ctx).splitlines() == [
        "stack   enabled  state",
        "actual  yes      stopped",
        "backup  no       unknown",
        "edge    yes      running",
    ]


def test_stacks_json(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"edge": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner({ps_q(checkout, "edge"): RunResult(0, "id\n")}))
    assert cli.main(["stacks", "--json"], ctx) == ExitCode.OK
    assert json.loads(out(ctx)) == {"schema": 1, "stacks": [{"name": "edge", "enabled": True, "state": "running"}]}


# --- status ------------------------------------------------------------------------------------------------
def test_status_prints_compose_ps_and_the_backup_summary(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"edge": None})
    ps = ("docker", "compose", "-f", str(checkout / "stacks" / "edge" / "compose.yaml"), "ps")
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, ps: RunResult(0, "NAME  STATUS\nedge  healthy\n")}))
    assert cli.main(["status"], ctx) == ExitCode.OK
    assert out(ctx).splitlines()[:2] == ["NAME  STATUS", "edge  healthy"]
    assert f"backup: no repository at {checkout / 'data' / 'backup'} (make backup-init)" in out(ctx)


def test_status_without_an_engine_says_how_to_start_it(make_checkout: MakeCheckout, make_context: MakeContext, make_host: MakeHost) -> None:
    ctx = make_context(host=make_host(system="macos"), cwd=make_checkout(), runner=FakeRunner())
    assert cli.main(["status"], ctx) == ExitCode.OK
    assert out(ctx).startswith("no container runtime running; start it with: colima start --cpu 2 --memory 2 --disk 20\n")


def test_check_shows_an_absolute_path_for_a_folder_outside_the_working_directory(
    make_checkout: MakeCheckout, make_context: MakeContext, tmp_path: Path
) -> None:
    other = make_checkout(root=tmp_path / "other")
    work = tmp_path / "work"
    work.mkdir()
    ctx = make_context(cwd=work, runner=FakeRunner({config_argv(other, "demo"): RunResult(0, GOOD_CONFIG)}))
    assert cli.main(["check", "--stacks", str(other / "stacks")], ctx) == ExitCode.OK
    assert out(ctx) == f"{other / 'stacks' / 'demo' / 'compose.yaml'}: ok\n"
