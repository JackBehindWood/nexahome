import json
import socket
from collections.abc import Callable
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.commands import doctor
from nexahome.errors import ExitCode
from nexahome.report import Status
from nexahome.runner import RunResult, SubprocessRunner

from conftest import FakeDocker, FakeRunner, MakeContext, MakeHost

CLI = ("docker", "--version")
COMPOSE = ("docker", "compose", "version")
INFO = ("docker", "info", "--format", "{{.ServerVersion}}")
HEALTHY = {
    CLI: RunResult(0, "Docker version 27.1.0, build abc123\n"),
    COMPOSE: RunResult(0, "Docker Compose version v2.29.0\n"),
    INFO: RunResult(0, "27.1.0\n"),
}
GIB = 1024**3


def without(*keys: tuple[str, ...]) -> dict[tuple[str, ...], RunResult]:
    return {k: v for k, v in HEALTHY.items() if k not in keys}


def checks_of(ctx_runner: FakeRunner, make_context: MakeContext, **kwargs: object) -> dict[str, tuple[Status, str | None]]:
    ctx = make_context(runner=ctx_runner, **kwargs)  # type: ignore[arg-type]
    return {c.id: (c.status, c.fix) for c in doctor.run_probes(ctx)}


def test_a_healthy_host_passes(make_context: MakeContext) -> None:
    results = checks_of(FakeRunner(HEALTHY), make_context)
    assert {i: s for i, (s, _) in results.items()} == {
        "platform": Status.OK, "python": Status.OK, "docker-cli": Status.OK,
        "compose": Status.OK, "engine": Status.OK, "disk": Status.OK,
    }


# PK-I2: each failing environment names the exact next command.
@pytest.mark.parametrize(
    ("name", "system", "debian", "responses", "check_id", "status", "fix"),
    [
        ("docker absent, macOS", "macos", False, {}, "docker-cli", Status.FAIL, "brew install colima docker docker-compose"),
        ("docker absent, Debian", "linux", True, {}, "docker-cli", Status.FAIL, "sudo apt-get install docker.io docker-compose-v2"),
        ("docker absent, other Linux", "linux", False, {}, "docker-cli", Status.FAIL, "https://docs.docker.com/engine/install/"),
        ("cascade: compose skipped", "linux", False, {}, "compose", Status.SKIP, None),
        ("cascade: engine skipped", "linux", False, {}, "engine", Status.SKIP, None),
        ("compose absent, Debian", "linux", True, without(COMPOSE), "compose", Status.FAIL, "sudo apt-get install docker-compose-v2"),
        ("engine down, macOS", "macos", False, {**HEALTHY, INFO: RunResult(1)}, "engine", Status.FAIL, "colima start --cpu 2 --memory 2 --disk 20"),
        ("engine down, Linux", "linux", False, {**HEALTHY, INFO: RunResult(1)}, "engine", Status.FAIL, "sudo systemctl start docker"),
        ("engine hangs, macOS", "macos", False, {**HEALTHY, INFO: RunResult(124, timed_out=True)}, "engine", Status.FAIL, "colima restart"),
        ("native Windows", "windows", False, HEALTHY, "platform", Status.FAIL, "wsl --install"),
    ],
)
def test_each_failure_names_one_exact_command(
    make_context: MakeContext, make_host: MakeHost, name: str, system: str, debian: bool,
    responses: dict[tuple[str, ...], RunResult], check_id: str, status: Status, fix: str | None,
) -> None:
    host = make_host(system=system, debian_like=debian)
    assert checks_of(FakeRunner(responses), make_context, host=host)[check_id] == (status, fix)


def test_low_disk_is_a_warning_with_a_command(make_context: MakeContext) -> None:
    ctx = make_context(runner=FakeRunner(HEALTHY))
    ctx.disk_free = lambda path: 1 * GIB
    disk = next(c for c in doctor.run_probes(ctx) if c.id == "disk")
    assert (disk.status, disk.fix) == (Status.WARN, "df -h .")


def make_checkout(root: Path) -> Path:
    (root / "stacks" / "demo").mkdir(parents=True)
    (root / "Makefile").write_text("")
    return root


def test_checkout_outside_home_on_macos_warns(make_context: MakeContext, make_host: MakeHost, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repo = make_checkout(tmp_path / "elsewhere")
    host = make_host(system="macos", home=home)
    at_root = {c.id: c for c in doctor.run_probes(make_context(host=host, cwd=repo, runner=FakeRunner(HEALTHY)))}
    assert (at_root["mount"].status, at_root["mount"].fix) == (Status.WARN, 'mv "$PWD" "$HOME/"')
    inside = repo / "stacks"
    deeper = {c.id: c for c in doctor.run_probes(make_context(host=host, cwd=inside, runner=FakeRunner(HEALTHY)))}
    assert deeper["mount"].fix == f'mv {repo} "$HOME/"'


def test_checkout_under_home_is_fine_and_linux_has_no_mount_probe(
    make_context: MakeContext, make_host: MakeHost, tmp_path: Path
) -> None:
    repo = make_checkout(tmp_path / "repo")
    mac = {c.id: c.status for c in doctor.run_probes(make_context(host=make_host(system="macos", home=tmp_path), cwd=repo))}
    linux = {c.id for c in doctor.run_probes(make_context(cwd=repo))}
    assert mac["mount"] == Status.OK and "mount" not in linux


def test_placeholders_are_named_by_key_and_values_are_never_printed(
    make_context: MakeContext, tmp_path: Path
) -> None:
    repo = make_checkout(tmp_path / "repo")
    (repo / "stacks" / "demo" / ".env").write_text("TOKEN=CHANGE_ME\nOTHER=plainvalue\n")
    ctx = make_context(cwd=repo, runner=FakeRunner(HEALTHY))
    assert cli.main(["doctor"], ctx) == ExitCode.OK  # a warning does not fail the run
    out = ctx.out.getvalue()  # type: ignore[attr-defined]
    assert "demo/TOKEN" in out and "${EDITOR:-vi} stacks/demo/.env" in out
    assert "plainvalue" not in out and str(tmp_path) not in out


def test_a_broken_probe_is_reported_and_the_others_still_run(
    monkeypatch: pytest.MonkeyPatch, make_context: MakeContext
) -> None:
    def broken(ctx: object, prior: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(doctor, "PROBES", (("python", broken), *doctor.PROBES[2:3]))
    checks = doctor.run_probes(make_context(runner=FakeRunner(HEALTHY)))
    assert [(c.id, c.status) for c in checks] == [("python", Status.FAIL), ("docker-cli", Status.OK)]
    assert checks[0].fix


def test_exit_codes_and_json(make_context: MakeContext, capsys: pytest.CaptureFixture[str]) -> None:
    ok_ctx = make_context(runner=FakeRunner(HEALTHY))
    assert cli.main(["doctor", "--json"], ok_ctx) == ExitCode.OK
    payload = json.loads(ok_ctx.out.getvalue())  # type: ignore[attr-defined]
    assert payload["schema"] == 1 and payload["ok"] is True
    assert all(set(c) == {"id", "status", "summary", "fix"} for c in payload["checks"])
    bad_ctx = make_context(runner=FakeRunner({}))
    assert cli.main(["doctor", "--json"], bad_ctx) == ExitCode.NOT_READY
    assert json.loads(bad_ctx.out.getvalue())["ok"] is False  # type: ignore[attr-defined]


def test_doctor_is_offline(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("doctor opened a socket")

    monkeypatch.setattr(socket, "socket", no_network)
    assert cli.main(["doctor"], make_context(runner=FakeRunner(HEALTHY))) == ExitCode.OK


# The same flows through the real subprocess runner and a `docker` shell script on PATH.
SHIM_HEALTHY = {
    "--version": (0, "Docker version 27.1.0, build abc123"),
    "compose version": (0, "Docker Compose version v2.29.0"),
    "info --format {{.ServerVersion}}": (0, "27.1.0"),
}


def test_end_to_end_with_the_shim_is_read_only(
    fake_docker: Callable[..., FakeDocker], make_context: MakeContext
) -> None:
    shim = fake_docker(SHIM_HEALTHY)
    ctx = make_context(runner=SubprocessRunner())
    assert cli.main(["doctor"], ctx) == ExitCode.OK
    assert shim.calls == ["--version", "compose version", "info --format {{.ServerVersion}}"]


def test_end_to_end_engine_down(fake_docker: Callable[..., FakeDocker], make_context: MakeContext) -> None:
    fake_docker({**SHIM_HEALTHY, "info --format {{.ServerVersion}}": (1, "")})
    ctx = make_context(runner=SubprocessRunner())
    assert cli.main(["doctor"], ctx) == ExitCode.NOT_READY
    assert ctx.out.getvalue().endswith("Next: sudo systemctl start docker\n")  # type: ignore[attr-defined]


def test_end_to_end_stuck_engine_times_out(
    monkeypatch: pytest.MonkeyPatch, fake_docker: Callable[..., FakeDocker], make_context: MakeContext
) -> None:
    fake_docker(SHIM_HEALTHY, hang="info --format {{.ServerVersion}}")
    monkeypatch.setattr(doctor, "ENGINE_TIMEOUT", 0.5)
    ctx = make_context(runner=SubprocessRunner())
    assert cli.main(["doctor"], ctx) == ExitCode.NOT_READY
    assert "did not answer" in ctx.out.getvalue()  # type: ignore[attr-defined]


@pytest.mark.usefixtures("no_docker")
def test_end_to_end_without_docker(make_context: MakeContext) -> None:
    ctx = make_context(runner=SubprocessRunner())
    assert cli.main(["doctor"], ctx) == ExitCode.NOT_READY
    assert "docker-cli" in ctx.out.getvalue() and "skip  compose" in ctx.out.getvalue()  # type: ignore[attr-defined]
