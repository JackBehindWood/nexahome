"""`nexahome check`: the Compose policy over the stacks, through cli.main with injected docker answers."""

import json
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult, SubprocessRunner

from conftest import REPO, FakeRunner, MakeCheckout, MakeContext, MakeHost, err, has_compose, out


def config_argv(checkout: Path, name: str) -> tuple[str, ...]:
    return ("docker", "compose", "-f", str(checkout / "stacks" / name / "compose.yaml"), "config", "--format", "json")


GOOD_CONFIG = json.dumps(
    {"name": "nexahome-demo", "services": {"app": {"image": "x/y:1", "healthcheck": {}, "restart": "always", "user": "1000", "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"], "read_only": True}}}
)


def test_check_passes_and_prints_the_originals_line(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout()
    ctx = make_context(cwd=checkout, runner=FakeRunner({config_argv(checkout, "demo"): RunResult(0, GOOD_CONFIG)}))
    assert cli.main(["check"], ctx) == ExitCode.OK
    assert out(ctx) == "stacks/demo/compose.yaml: ok\n"


def test_check_fails_with_exit_1_on_a_policy_problem(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    bad = json.dumps({"name": "nexahome-demo", "services": {"app": {**json.loads(GOOD_CONFIG)["services"]["app"], "privileged": True}}})
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


def test_check_without_the_compose_plugin_ends_in_the_install_command(
    make_checkout: MakeCheckout, make_context: MakeContext, make_host: MakeHost
) -> None:
    from nexahome import platform as host_platform

    checkout = make_checkout()
    host = make_host(system="macos")
    runner = FakeRunner(
        {
            config_argv(checkout, "demo"): RunResult(1, stderr="unknown shorthand flag: 'f' in -f"),  # A-01: docker without the plugin
            ("docker", "compose", "version"): RunResult(1, stderr="docker: 'compose' is not a docker command"),
        }
    )
    ctx = make_context(host=host, cwd=checkout, runner=runner)
    assert cli.main(["check"], ctx) == ExitCode.NOT_READY
    assert err(ctx) == f"FAIL  the Docker Compose plugin is not installed; cannot validate stacks\nNext: {host_platform.compose_install_fix(host)}\n"
    assert "unknown shorthand" not in err(ctx)


def test_a_policy_failure_ends_with_the_file_to_edit(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    bad = json.dumps({"name": "nexahome-demo", "services": {"app": {**json.loads(GOOD_CONFIG)["services"]["app"], "privileged": True}}})
    checkout = make_checkout()
    ctx = make_context(cwd=checkout, runner=FakeRunner({config_argv(checkout, "demo"): RunResult(0, bad)}))
    assert cli.main(["check"], ctx) == ExitCode.FAILED
    assert err(ctx) == "Next: ${EDITOR:-vi} stacks/demo/compose.yaml\n"  # A-08


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


def test_check_shows_an_absolute_path_for_a_folder_outside_the_working_directory(
    make_checkout: MakeCheckout, make_context: MakeContext, tmp_path: Path
) -> None:
    other = make_checkout(root=tmp_path / "other")
    work = tmp_path / "work"
    work.mkdir()
    ctx = make_context(cwd=work, runner=FakeRunner({config_argv(other, "demo"): RunResult(0, GOOD_CONFIG)}))
    assert cli.main(["check", "--stacks", str(other / "stacks")], ctx) == ExitCode.OK
    assert out(ctx) == f"{other / 'stacks' / 'demo' / 'compose.yaml'}: ok\n"
