"""Golden parity (PK-C3): the port gives the same answers as scripts/check_compose.py."""

import json
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from nexahome.policy import compose
from nexahome.runner import RunResult, SubprocessRunner

from conftest import REPO, FakeRunner, load_script

GOOD: dict[str, Any] = {
    "image": "example/app:1.2.3",
    "healthcheck": {"test": ["CMD", "true"]},
    "restart": "unless-stopped",
    "ports": [{"host_ip": "127.0.0.1", "published": "8080"}],
}


def service(**changes: Any) -> dict[str, Any]:
    merged = {**GOOD, **changes}
    return {k: v for k, v in merged.items() if v is not None}


# (name, service, text the message must contain)
SERVICES: list[tuple[str, dict[str, Any], str]] = [
    ("good", service(), ""),
    ("no tag", service(image="example/app"), "must have a pinned tag"),
    ("latest tag", service(image="example/app:latest"), "must have a pinned tag"),
    ("registry port is not a tag", service(image="registry:5000/app"), "must have a pinned tag"),
    ("no healthcheck", service(healthcheck=None), "missing healthcheck"),
    ("no restart", service(restart=None), "missing restart policy"),
    ("host network", service(network_mode="host"), "host networking is not allowed"),
    ("privileged", service(privileged=True), "privileged is not allowed"),
    ("open port", service(ports=[{"host_ip": "0.0.0.0", "published": "9"}]), "must bind to 127.0.0.1"),
    ("port without host ip", service(ports=[{"published": "9"}]), "must bind to 127.0.0.1"),
    ("extra capability", service(cap_add=["SYS_ADMIN", "NET_BIND_SERVICE"]), "cap_add ['SYS_ADMIN'] is not allowed"),
    ("allowed capability", service(cap_add=["NET_BIND_SERVICE"]), ""),
    ("docker socket", service(volumes=[{"source": "/var/run/docker.sock"}]), "Docker socket must not be mounted"),
    ("one-shot job", service(healthcheck=None, restart=None, labels={"nexahome.oneshot": "true"}), ""),
    ("one-shot still needs a tag", service(image="job", labels={"nexahome.oneshot": "true"}), "pinned tag"),
]

# (name, directory, config, text the message must contain)
PROJECTS: list[tuple[str, str, dict[str, Any], str]] = [
    ("good", "demo", {"name": "nexahome-demo"}, ""),
    ("wrong name", "demo", {"name": "other"}, "project name must be 'nexahome-demo', found 'other'"),
    ("no name", "demo", {}, "found 'None'"),
    ("foreign external network", "demo", {"name": "nexahome-demo", "networks": {"n": {"external": True, "name": "x"}}}, "only external network allowed"),
    ("shared network", "demo", {"name": "nexahome-demo", "networks": {"n": {"external": True, "name": "nexahome-edge"}}}, ""),
    ("empty network spec", "demo", {"name": "nexahome-demo", "networks": {"n": None}}, ""),
    ("unlabelled volume", "demo", {"name": "nexahome-demo", "volumes": {"v": {}}}, "label nexahome.backup"),
    ("null volume spec", "demo", {"name": "nexahome-demo", "volumes": {"v": None}}, "label nexahome.backup"),
    ("labelled true", "demo", {"name": "nexahome-demo", "volumes": {"v": {"labels": {"nexahome.backup": "true"}}}}, ""),
    ("labelled false", "demo", {"name": "nexahome-demo", "volumes": {"v": {"labels": {"nexahome.backup": "false"}}}}, ""),
    ("bad label value", "demo", {"name": "nexahome-demo", "volumes": {"v": {"labels": {"nexahome.backup": "yes"}}}}, "label nexahome.backup"),
]


@pytest.mark.parametrize(("name", "svc", "expected"), SERVICES, ids=[s[0] for s in SERVICES])
def test_service_rules_match_the_original(name: str, svc: Mapping[str, Any], expected: str) -> None:
    got = compose.check_service("app", svc)
    assert got == load_script("check_compose").check_service("app", svc)
    assert (expected in " ".join(got)) if expected else got == []


@pytest.mark.parametrize(("name", "directory", "config", "expected"), PROJECTS, ids=[p[0] for p in PROJECTS])
def test_project_rules_match_the_original(name: str, directory: str, config: Mapping[str, Any], expected: str) -> None:
    got = compose.check_project(directory, config)
    assert got == load_script("check_compose").check_project(directory, config)
    assert (expected in " ".join(got)) if expected else got == []


def test_check_config_puts_project_problems_before_service_problems() -> None:
    problems = compose.check_config("demo", {"name": "wrong", "services": {"app": service(privileged=True)}})
    assert [p.split(":")[0] for p in problems] == ["project name must be 'nexahome-demo', found 'wrong'".split(":")[0], "app"]


def make_stack(root: Path, with_env_example: bool) -> Path:
    stack = root / "demo"
    stack.mkdir(parents=True)
    (stack / "compose.yaml").write_text("")
    if with_env_example:
        (stack / ".env.example").write_text("")
    return stack / "compose.yaml"


def argv_for(compose_file: Path, *extra: str) -> tuple[str, ...]:
    return ("docker", "compose", "-f", str(compose_file), *extra, "config", "--format", "json")


def test_check_stack_runs_compose_config_with_the_example_env(tmp_path: Path) -> None:
    config = json.dumps({"name": "nexahome-demo", "services": {"app": service()}})
    for with_env in (True, False):
        stack = make_stack(tmp_path / str(with_env), with_env)
        extra = ("--env-file", str(stack.parent / ".env.example")) if with_env else ()
        runner = FakeRunner({argv_for(stack, *extra): RunResult(0, config)})
        result = compose.check_stack(runner, stack)
        assert result.lines() == [f"{stack}: ok"] and runner.calls == [argv_for(stack, *extra)]


def test_check_stack_reports_problems_with_the_original_line_format(tmp_path: Path) -> None:
    stack = make_stack(tmp_path, False)
    config = json.dumps({"name": "nexahome-demo", "services": {"app": service(privileged=True)}})
    result = compose.check_stack(FakeRunner({argv_for(stack): RunResult(0, config)}), stack)
    assert result.lines() == [f"{stack}: app: privileged is not allowed"]


def test_check_stack_errors_when_docker_is_missing_or_compose_fails(tmp_path: Path) -> None:
    stack = make_stack(tmp_path, False)
    assert compose.check_stack(FakeRunner(), stack).error == "docker CLI not found; cannot validate stacks"
    failed = compose.check_stack(FakeRunner({argv_for(stack): RunResult(1, stderr="bad yaml")}), stack)
    assert failed.error == f"{stack}: docker compose config failed\nbad yaml" and failed.lines() == []


def has_compose() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0


@pytest.mark.skipif(not has_compose(), reason="needs the Docker CLI with the Compose plugin (no engine)")
def test_the_real_stacks_give_the_same_output_as_the_original(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(REPO)
    code = load_script("check_compose").main()
    original = capsys.readouterr().out.splitlines()
    results = compose.check_stacks(SubprocessRunner())
    assert [line for r in results for line in r.lines()] == original
    assert (code == 0) == all(not r.problems and r.error is None for r in results)
