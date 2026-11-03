"""Validate stacks/*/compose.yaml against the project's Compose policy.

Policy: pinned image tag or digest, health check, restart policy, published ports bound to 127.0.0.1, no host
networking (no host pid, ipc or user namespace, no joining another service's network), not privileged, no
devices, no unconfined seccomp or apparmor; non-root user, cap_drop ALL, no-new-privileges, read-only root; every named volume labelled nexahome.backup "true" or "false"; project name
nexahome-<directory>; no cap_add except NET_BIND_SERVICE; no Docker socket mount; the only external network
is nexahome-edge. A service labelled nexahome.oneshot "true" is exempt from the health check and restart
rules only. The pure functions take the output of `docker compose config --format json`; check_stack runs it
(the Docker CLI is needed, a running engine is not).
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple

from nexahome.docker import EDGE_NETWORK
from nexahome.docker import compose as docker_compose
from nexahome.parallel import map_ordered
from nexahome.runner import Runner

ALLOWED_CAP_ADD = {"NET_BIND_SERVICE"}  # Caddy's file capability (ADR 0011)

type Config = Mapping[str, Any]


def _is_pinned(image: str) -> bool:
    """A tag other than `latest`, or a digest. The registry's port colon (`host:5000/app`) is not a tag."""
    if "@sha256:" in image:
        return True  # a digest is the strongest pin; with or without a tag
    tag = image.rsplit("/", 1)[-1].partition(":")[2]
    return bool(tag) and tag != "latest"


def _runs_as_root(user: object) -> bool:
    """No user, or user 0 or root (with or without a group)."""
    return str(user or "").split(":")[0] in ("", "0", "root")


def check_service(name: str, svc: Config) -> list[str]:
    """The policy problems of one Compose service, as sentences."""
    problems = []
    oneshot = (svc.get("labels") or {}).get("nexahome.oneshot") == "true"
    image = svc.get("image", "")
    if not _is_pinned(image):
        problems.append(f"{name}: image '{image}' must have a pinned tag")
    if not oneshot and "healthcheck" not in svc:
        problems.append(f"{name}: missing healthcheck")
    if not oneshot and "restart" not in svc:
        problems.append(f"{name}: missing restart policy")
    if svc.get("network_mode") == "host":
        problems.append(f"{name}: host networking is not allowed")
    mode = str(svc.get("network_mode") or "")
    if mode.startswith(("container:", "service:")):
        problems.append(f"{name}: network_mode {mode} is not allowed (it joins another service's network)")
    for key in ("pid", "ipc", "userns_mode"):
        if svc.get(key) == "host":
            problems.append(f"{name}: {key}: host is not allowed")
    if svc.get("privileged"):
        problems.append(f"{name}: privileged is not allowed")
    if svc.get("devices"):
        problems.append(f"{name}: devices are not allowed")
    options = [str(option) for option in svc.get("security_opt") or []]
    if any("unconfined" in option for option in options):
        problems.append(f"{name}: seccomp or apparmor unconfined is not allowed")
    if not any(option.replace("=", ":").startswith("no-new-privileges") and not option.endswith("false") for option in options):
        problems.append(f"{name}: security_opt needs no-new-privileges:true")
    if _runs_as_root(svc.get("user")):
        problems.append(f"{name}: must run as a non-root user (set user)")
    if "ALL" not in [str(capability).upper() for capability in svc.get("cap_drop") or []]:
        problems.append(f"{name}: must drop all capabilities (cap_drop: [ALL])")
    if svc.get("read_only") is not True:
        problems.append(f"{name}: the root filesystem must be read-only (read_only: true)")
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
    """The policy problems of one stack's project: its name and networks."""
    problems = []
    expected = f"nexahome-{directory}"
    if config.get("name") != expected:
        problems.append(f"project name must be '{expected}', found '{config.get('name')}'")
    for network, spec in (config.get("networks") or {}).items():
        if (spec or {}).get("external") and spec.get("name") != EDGE_NETWORK:
            problems.append(f"network {network}: the only external network allowed is '{EDGE_NETWORK}'")
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


class StackResult(NamedTuple):
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
    result = docker_compose.config_json(runner, compose)
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
    """Check every stack under root, side by side (each is a separate `docker compose config`). Messages print
    paths under shown_root (default: root itself)."""
    return map_ordered(
        lambda compose: check_stack(runner, compose, shown_root / compose.relative_to(root) if shown_root else None),
        sorted(root.glob("*/compose.yaml")),
    )
