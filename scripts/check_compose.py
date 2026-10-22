#!/usr/bin/env python3
"""Validate every stacks/*/compose.yaml against the project's Compose policy.

Policy: pinned image tag, health check, restart policy, published ports bound to
127.0.0.1, no host networking, not privileged; every named volume labelled
nexahome.backup "true" or "false"; project name nexahome-<directory>; no cap_add except
NET_BIND_SERVICE; no Docker socket mount; the only external network is nexahome-edge. A service
labelled nexahome.oneshot "true" (a job run by a script, such as the backup) is
exempt from the health check and restart rules only. Uses
`docker compose config`, which needs the docker CLI but no running engine.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

SHARED_NETWORK = "nexahome-edge"
ALLOWED_CAP_ADD = {"NET_BIND_SERVICE"}  # Caddy's file capability (ADR 0011)


def check_service(name: str, svc: dict) -> list[str]:
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


def check_project(directory: str, config: dict) -> list[str]:
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


def main() -> int:
    stacks = sorted(Path("stacks").glob("*/compose.yaml"))
    if not stacks:
        print("no stacks found; nothing to check")
        return 0
    if shutil.which("docker") is None:
        print("docker CLI not found; cannot validate stacks", file=sys.stderr)
        return 1
    failures = 0
    for compose in stacks:
        env_example = compose.parent / ".env.example"
        cmd = ["docker", "compose", "-f", str(compose)]
        if env_example.is_file():
            cmd += ["--env-file", str(env_example)]
        result = subprocess.run(cmd + ["config", "--format", "json"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{compose}: docker compose config failed\n{result.stderr}", file=sys.stderr)
            failures += 1
            continue
        config = json.loads(result.stdout)
        problems = check_project(compose.parent.name, config)
        for name, svc in config.get("services", {}).items():
            problems += check_service(name, svc)
        for problem in problems:
            print(f"{compose}: {problem}")
        failures += len(problems)
        if not problems:
            print(f"{compose}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
