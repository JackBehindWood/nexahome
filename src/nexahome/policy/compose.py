"""Validate stacks/*/compose.yaml against the project's Compose policy (port of scripts/check_compose.py).

Policy: pinned image tag, health check, restart policy, published ports bound to 127.0.0.1, no host
networking, not privileged; every named volume labelled nexahome.backup "true" or "false"; project name
nexahome-<directory>; no cap_add except NET_BIND_SERVICE; no Docker socket mount; the only external network
is nexahome-edge. A service labelled nexahome.oneshot "true" is exempt from the health check and restart
rules only. The pure functions take the output of `docker compose config --format json`; check_stack runs it
(the Docker CLI is needed, a running engine is not).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nexahome.runner import Runner

SHARED_NETWORK = "nexahome-edge"
ALLOWED_CAP_ADD = {"NET_BIND_SERVICE"}  # Caddy's file capability (ADR 0011)
CONFIG_TIMEOUT = 60  # seconds per stack

type Config = Mapping[str, Any]


def check_service(name: str, svc: Config) -> list[str]:
    problems = []
    oneshot = (svc.get("labels") or {}).get("nexahome.oneshot") == "true"
    image = svc.get("image", "")
    tag = image.rsplit("/", 1)[-1].partition(":")[2]
    if not tag or tag == "latest":
        problems.append(f"{name}: image '{image}' must have a pinned tag")
    if not oneshot and "healthcheck" not in svc:
        problems.append(f"{name}: missing healthcheck")
    if not oneshot and "restart" not in svc:
        problems.append(f"{name}: missing restart policy")
    if svc.get("network_mode") == "host":
        problems.append(f"{name}: host networking is not allowed")
    if svc.get("privileged"):
        problems.append(f"{name}: privileged is not allowed")
    for port in svc.get("ports", []):
        if port.get("host_ip") != "127.0.0.1":
            problems.append(f"{name}: port {port.get('published')} must bind to 127.0.0.1")
    extra = set(svc.get("cap_add") or []) - ALLOWED_CAP_ADD
    if extra:
        problems.append(f"{name}: cap_add {sorted(extra)} is not allowed (only {sorted(ALLOWED_CAP_ADD)})")
    for volume in svc.get("volumes") or []:
        if "docker.sock" in str(volume.get("source", "")):
            problems.append(f"{name}: the Docker socket must not be mounted")
    return problems


def check_project(directory: str, config: Config) -> list[str]:
    problems = []
    expected = f"nexahome-{directory}"
    if config.get("name") != expected:
        problems.append(f"project name must be '{expected}', found '{config.get('name')}'")
    for network, spec in (config.get("networks") or {}).items():
        if (spec or {}).get("external") and spec.get("name") != SHARED_NETWORK:
            problems.append(f"network {network}: the only external network allowed is '{SHARED_NETWORK}'")
    for volume, spec in (config.get("volumes") or {}).items():
        if (spec or {}).get("labels", {}).get("nexahome.backup") not in ("true", "false"):
            problems.append(f"volume {volume}: label nexahome.backup must be \"true\" or \"false\"")
    return problems


def check_config(directory: str, config: Config) -> list[str]:
    """Every problem in one stack's resolved configuration, project first."""
    problems = check_project(directory, config)
    for name, svc in config.get("services", {}).items():
        problems += check_service(name, svc)
    return problems


@dataclass(frozen=True)
class StackResult:
    compose: Path
    problems: tuple[str, ...] = ()
    error: str | None = None  # the check could not run (no Docker CLI, or `docker compose config` failed)
    docker_missing: bool = False

    def lines(self) -> list[str]:
        """What the original script printed on stdout for this stack."""
        if self.error is not None:
            return []
        return [f"{self.compose}: {p}" for p in self.problems] or [f"{self.compose}: ok"]


def check_stack(runner: Runner, compose: Path, shown: Path | None = None) -> StackResult:
    """Check one stack. `compose` is used to run and read; `shown` (default: the same) is what messages print."""
    label = shown or compose
    env_example = compose.parent / ".env.example"
    argv = ["docker", "compose", "-f", str(compose)]
    if env_example.is_file():
        argv += ["--env-file", str(env_example)]
    result = runner.run([*argv, "config", "--format", "json"], timeout=CONFIG_TIMEOUT)
    if result.missing:
        return StackResult(label, error="docker CLI not found; cannot validate stacks", docker_missing=True)
    if not result.ok:
        return StackResult(label, error=f"{label}: docker compose config failed\n{result.stderr}")
    try:
        config = json.loads(result.stdout)
    except ValueError:
        return StackResult(label, error=f"{label}: docker compose config did not return JSON")
    return StackResult(label, tuple(check_config(compose.parent.name, config)))


def check_stacks(runner: Runner, root: Path = Path("stacks"), shown_root: Path | None = None) -> list[StackResult]:
    """Check every stack under root. Messages print paths under shown_root (default: root itself)."""
    return [
        check_stack(runner, compose, shown_root / compose.relative_to(root) if shown_root else None)
        for compose in sorted(root.glob("*/compose.yaml"))
    ]
