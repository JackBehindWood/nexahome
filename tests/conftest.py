"""Shared test doubles: injected hosts and contexts, a fake runner, and a fake `docker` on PATH."""

import io
import os
import shlex
import shutil
import stat
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.context import Context
from nexahome.errors import ExitCode
from nexahome.instance import config
from nexahome.platform import Host
from nexahome.runner import RunResult, Runner

MakeHost = Callable[..., Host]
MakeContext = Callable[..., Context]


@pytest.fixture
def real_ports() -> None:
    """Ask for this fixture to let `stacks new` probe the real host ports."""


@pytest.fixture(autouse=True)
def host_ports_are_free(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """A test never depends on what is listening on the machine running it: every port reads as free."""
    if "real_ports" not in request.fixturenames:
        from nexahome.release import net

        monkeypatch.setattr(net, "port_is_busy", lambda port: False)


@pytest.fixture
def make_host(tmp_path: Path) -> MakeHost:
    def make(
        system: str = "linux",
        machine: str = "amd64",
        python: tuple[int, int, int] = (3, 13, 0),
        home: Path | None = None,
        debian_like: bool = False,
    ) -> Host:
        return Host(system, machine, python, home or tmp_path, debian_like)

    return make


class FakeRunner:
    """Answers by exact argv; anything not listed behaves like a program that is not installed."""

    def __init__(self, responses: dict[tuple[str, ...], RunResult] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: Sequence[str], *, timeout: float) -> RunResult:
        key = tuple(argv)
        self.calls.append(key)
        return self.responses.get(key, RunResult(127, missing=True))


@pytest.fixture
def make_context(make_host: MakeHost, tmp_path: Path) -> MakeContext:
    def make(
        host: Host | None = None,
        runner: Runner | None = None,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> Context:
        return Context(
            host=host or make_host(),
            runner=runner or FakeRunner(),
            env=env or {},
            cwd=cwd or tmp_path,
            out=io.StringIO(),
            err=io.StringIO(),
        )

    return make


def out(ctx: object) -> str:
    """What a command wrote to its `out` stream (the context from `make_context` holds StringIOs)."""
    return ctx.out.getvalue()  # type: ignore[attr-defined]


def err(ctx: object) -> str:
    return ctx.err.getvalue()  # type: ignore[attr-defined]


def make_instance(root: Path, stacks: tuple[str, ...] = ("demo",)) -> Path:
    """What `nexahome init` leaves, by hand: nexahome.toml and stacks/<name>/compose.yaml, no Makefile."""
    (root / "stacks").mkdir(parents=True)
    for name in stacks:
        (root / "stacks" / name).mkdir()
        (root / "stacks" / name / "compose.yaml").write_text("")
    (root / "nexahome.toml").write_text(config.render(stacks))
    return root


def ps_running_argv(compose_file: Path) -> tuple[str, ...]:
    """The `docker compose ps` call that tells whether one stack runs."""
    return ("docker", "compose", "-f", str(compose_file), "ps", "--status", "running", "-q")


@pytest.fixture
def instance(make_context: MakeContext, tmp_path: Path) -> Path:
    """A real instance made by `nexahome init` from the bundled stacks. A module may override it with a smaller one."""
    target = tmp_path / "made"
    assert cli.main(["init", str(target)], make_context(cwd=tmp_path, runner=FakeRunner())) == ExitCode.OK
    return target


@dataclass
class FakeDocker:
    log_file: Path

    @property
    def calls(self) -> list[str]:
        return self.log_file.read_text().splitlines() if self.log_file.exists() else []


@pytest.fixture
def fake_docker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., FakeDocker]:
    """Put a `docker` shell script first on PATH. answers maps "arguments" to (exit code, stdout);
    anything else exits 1. `hang` names the arguments that never return (a stuck VM)."""

    def install(answers: dict[str, tuple[int, str]] | None = None, *, hang: str | None = None) -> FakeDocker:
        bin_dir = tmp_path / "shim-bin"
        bin_dir.mkdir(exist_ok=True)
        log = tmp_path / "docker-calls.log"
        lines = ["#!/bin/sh", f'printf "%s\\n" "$*" >> {shlex.quote(str(log))}', 'case "$*" in']
        for arguments, (code, out) in (answers or {}).items():
            body = "exec sleep 5" if arguments == hang else f"printf '%s\\n' {shlex.quote(out)}; exit {code}"
            lines.append(f"  {shlex.quote(arguments)}) {body};;")
        lines += ["  *) exit 1;;", "esac", ""]
        script = bin_dir / "docker"
        script.write_text("\n".join(lines))
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        return FakeDocker(log)

    return install


@pytest.fixture
def no_docker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A PATH on which no program exists."""
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))


REPO = Path(__file__).resolve().parents[1]


type MakeCheckout = Callable[..., Path]


@pytest.fixture
def make_checkout(tmp_path: Path) -> MakeCheckout:
    """A minimal NexaHome checkout: stacks/<name>/compose.yaml (+ .env.example) and a Makefile."""

    def make(stacks: dict[str, str | None] | None = None, root: Path | None = None) -> Path:
        base = root or tmp_path / "repo"
        (base / "stacks").mkdir(parents=True)
        (base / "Makefile").write_text("")
        for name, example in (stacks if stacks is not None else {"demo": None}).items():
            (base / "stacks" / name).mkdir()
            (base / "stacks" / name / "compose.yaml").write_text("")
            if example is not None:
                (base / "stacks" / name / ".env.example").write_text(example)
        return base

    return make


DOCKER_HEALTHY = {
    ("docker", "--version"): RunResult(0, "Docker version 27.1.0, build abc123\n"),
    ("docker", "compose", "version"): RunResult(0, "Docker Compose version v2.29.0\n"),
    ("docker", "info", "--format", "{{.ServerVersion}}"): RunResult(0, "27.1.0\n"),
}


def has_compose() -> bool:
    """True when this machine has the Docker CLI with the Compose plugin (no engine needed)."""
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0
