"""`nexahome status`: stack health and the backup summary, through cli.main."""

from pathlib import Path

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult

from conftest import DOCKER_HEALTHY, FakeRunner, MakeCheckout, MakeContext, MakeHost, make_instance, out


def test_status_prints_compose_ps_and_the_backup_summary(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"edge": None})
    ps = ("docker", "compose", "-f", str(checkout / "stacks" / "edge" / "compose.yaml"), "ps")
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, ps: RunResult(0, "NAME  STATUS\nedge  healthy\n")}))
    assert cli.main(["status"], ctx) == ExitCode.OK
    assert out(ctx).splitlines()[:2] == ["NAME  STATUS", "edge  healthy"]
    assert f"backup: no repository at {checkout / 'data' / 'backup'} (in a git clone: make backup-init)" in out(ctx)


def test_status_in_an_instance_does_not_send_the_user_to_make(make_context: MakeContext, tmp_path: Path) -> None:
    root = make_instance(tmp_path / "made", ("hello",))  # what `nexahome init` leaves: nexahome.toml, no Makefile
    ctx = make_context(cwd=root, runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["status"], ctx) == ExitCode.OK
    assert "make backup" not in out(ctx) and "not available in an instance yet" in out(ctx)


def test_status_without_an_engine_says_how_to_start_it(make_checkout: MakeCheckout, make_context: MakeContext, make_host: MakeHost) -> None:
    ctx = make_context(host=make_host(system="macos"), cwd=make_checkout(), runner=FakeRunner())
    assert cli.main(["status"], ctx) == ExitCode.OK
    assert out(ctx).startswith("no container runtime running; start it with: colima start --cpu 2 --memory 2 --disk 20\n")
