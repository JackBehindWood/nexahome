#!/usr/bin/env python3
"""Validate every stacks/*/compose.yaml against the project's Compose policy.

Policy: pinned image tag, health check, restart policy, published ports bound to
127.0.0.1, no host networking, not privileged. Uses `docker compose config`, which
needs the docker CLI but no running engine.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path


def check_service(name: str, svc: dict) -> list[str]:
    problems = []
    image = svc.get("image", "")
    tag = image.rsplit("/", 1)[-1].partition(":")[2]
    if not tag or tag == "latest":
        problems.append(f"{name}: image '{image}' must have a pinned tag")
    if "healthcheck" not in svc:
        problems.append(f"{name}: missing healthcheck")
    if "restart" not in svc:
        problems.append(f"{name}: missing restart policy")
    if svc.get("network_mode") == "host":
        problems.append(f"{name}: host networking is not allowed")
    if svc.get("privileged"):
        problems.append(f"{name}: privileged is not allowed")
    for port in svc.get("ports", []):
        if port.get("host_ip") != "127.0.0.1":
            problems.append(f"{name}: port {port.get('published')} must bind to 127.0.0.1")
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
        problems = []
        for name, svc in json.loads(result.stdout).get("services", {}).items():
            problems += check_service(name, svc)
        for problem in problems:
            print(f"{compose}: {problem}")
        failures += len(problems)
        if not problems:
            print(f"{compose}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
