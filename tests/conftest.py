"""Shared test doubles: injected hosts and contexts, a fake runner, and a fake `docker` on PATH."""

import io
import os
import shlex
import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from nexahome.context import Context
from nexahome.platform import Host
from nexahome.runner import RunResult, Runner

MakeHost = Callable[..., Host]
MakeContext = Callable[..., Context]


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
