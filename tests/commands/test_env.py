"""`nexahome env`: create each stack's .env, generate secrets, run doctor, through cli.main."""

import stat

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult

from conftest import DOCKER_HEALTHY, FakeRunner, MakeCheckout, MakeContext, err, out

INFO = ("docker", "info", "--format", "{{.ServerVersion}}")


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
