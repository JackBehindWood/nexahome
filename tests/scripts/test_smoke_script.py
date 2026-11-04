"""Golden tests for scripts/smoke.sh: its exit codes, its FAIL lines and its drift detector, with stub `docker` and `curl`.

Characterisation, for the port to the package (PK7, ADR 0018 PK-C3). The three config files it reads are copied from the
real stacks, so a host added to one of them and not the others fails here as it fails `make smoke`.
To reproduce by hand: `make smoke VERBOSE=1`.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from script_harness import REPO, Rule, install_stub, make_tree, run_script

DOMAIN = "nexahome.localhost"
PORT = "8088"
HOSTS = ("actual", "gatus", "hello", "home", "id")  # the edge's Caddyfile blocks, which are also its network aliases
FILES = ("edge/Caddyfile", "portal/config/services.yaml", "gatus/config/config.yaml")


def container_line(project: str, *, user: str = "65532", readonly: str = "true", capdrop: str = "[ALL]", capadd: str = "[]", health: str = "healthy", restarts: str = "0", mounts: str = "", ports: str = "127.0.0.1 ") -> str:
    return f"/{project}-1|{project}|{user}|{readonly}|{capdrop}|{capadd}|{health}|{restarts}|{mounts}|{ports}"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    root = make_tree(tmp_path, ("smoke.sh",))
    for name in FILES:
        target = root / "stacks" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / "stacks" / name, target)
    return root


def docker_rules(lines: dict[str, str], *, aliases: tuple[str, ...] = HOSTS) -> list[Rule]:
    """Containers by id (`edge1` is the edge) and the answers the script reads from the edge."""
    rules: list[Rule] = [
        ("ps -q --filter label=com.docker.compose.project", 0, "\n".join(lines)),
        ("inspect --format *Config.Env* edge1", 0, f"NEXAHOME_DOMAIN={DOMAIN}\nEDGE_PORT={PORT}"),
        ("inspect --format *Aliases* edge1", 0, "\n".join(f"{h}.{DOMAIN}" for h in aliases)),
    ]
    rules += [(f"inspect --format *RestartCount* {cid}", 0, line) for cid, line in lines.items()]
    rules += [("logs --tail 3 *", 0, "last log line")]
    return rules


def curl_rules(*, health: str = "ok", foreign: str = "404", named: str = "200", tile: str = "200", headers: str = "X-Content-Type-Options: nosniff\nX-Frame-Options: DENY", page: str = "<html>portal</html>") -> list[Rule]:
    base = f"{DOMAIN}:{PORT}"
    return [
        (f"*http://127.0.0.1:{PORT}/health", 0, health),
        ("*Host: other.example*", 0, foreign),
        ("-sI *", 0, headers),
        (f"*siteMonitor", 0, f'{{"status":{tile}}}'),
        (f"*home.{base}/api/services", 0, "[]"),
        (f"-s --max-time 10 http://home.{base}/", 0, page),
        ("*%{http_code}*", 0, named),
    ]


def smoke(root: Path, tmp_path: Path, docker: list[Rule], curl: list[Rule] | None = None) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    install_stub(bin_dir, "docker", docker)
    install_stub(bin_dir, "curl", curl if curl is not None else curl_rules())
    return run_script(root, "smoke.sh", bin_dir=bin_dir, env={"WAIT": "0"})


HEALTHY = {"edge1": container_line("nexahome-edge"), "hello1": container_line("nexahome-hello")}


def fails(done: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in done.stdout.splitlines() if line.startswith("FAIL")]


def test_everything_in_order_passes_with_exit_0(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, docker_rules(HEALTHY))
    assert (done.returncode, fails(done)) == (0, []), done.stdout
    lines = done.stdout.splitlines()
    assert "ok    edge healthy" in lines and "ok    hello healthy" in lines
    assert "ok    contract (add-a-stack steps)" in lines
    assert lines[-1] == "smoke: all checks passed"
    assert sum(line.startswith("ok    tile dot") for line in lines) == 4  # Sign in, Health, Actual Budget, Hello


def test_no_container_runtime_is_exit_2(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, [])
    assert (done.returncode, done.stdout.splitlines()) == (2, ["no container runtime running (start it as in the README)", "smoke: nothing to check"])


def test_no_running_stack_is_exit_2(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, [("ps -q *", 0, "")])
    assert (done.returncode, done.stdout.splitlines()) == (2, ["no stacks are running", "smoke: nothing to check"])


def test_containers_that_are_not_nexahome_stacks_are_ignored(tree: Path, tmp_path: Path) -> None:
    lines = {**HEALTHY, "other1": container_line("someone-else", user="0", readonly="false")}
    done = smoke(tree, tmp_path, docker_rules(lines))
    assert done.returncode == 0 and "someone-else" not in done.stdout


def test_without_the_edge_it_fails_and_says_which_command_starts_it(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, docker_rules({"hello1": container_line("nexahome-hello")}))
    assert done.returncode == 1
    assert "FAIL  edge: not running; named URLs and the portal are unreachable. fix: make up STACK=edge" in done.stdout
    assert done.stdout.splitlines()[-1] == "smoke: 1 check(s) failed"


PROBLEMS: list[tuple[dict[str, str], str]] = [
    ({"health": "unhealthy"}, "health: unhealthy. logs: last log line "),
    ({"health": ""}, "health: no healthcheck. logs: last log line "),
    ({"restarts": "3"}, "restarts: 3 (see docker logs nexahome-{stack}-1)"),
    ({"user": "0"}, "hardening:  runs as root;"),
    ({"user": ""}, "hardening:  runs as root;"),
    ({"readonly": "false"}, "hardening:  root filesystem writable;"),
    ({"capdrop": "[]"}, "hardening:  capabilities not dropped;"),
    ({"capadd": "[SYS_ADMIN]"}, "hardening:  cap_add [SYS_ADMIN];"),
    ({"mounts": "/var/run/docker.sock "}, "hardening:  Docker socket mounted;"),
    ({"ports": "ANY "}, "hardening:  port on 'ANY';"),
    ({"ports": "0.0.0.0 "}, "hardening:  port on '0.0.0.0';"),
]


def test_each_hardening_and_health_problem_is_one_fail_line(tree: Path, tmp_path: Path) -> None:
    """One container per problem, one run (a run costs about half a second of process starts)."""
    lines = {"edge1": HEALTHY["edge1"]}
    expected = []
    for n, (changes, text) in enumerate(PROBLEMS):
        stack = f"case{n}"
        lines[f"c{n}"] = container_line(f"nexahome-{stack}", **changes)
        expected.append(f"FAIL  {stack} {text.format(stack=stack)}")
    done = smoke(tree, tmp_path, docker_rules(lines))
    assert done.returncode == 1
    assert fails(done) == expected, done.stdout
    assert done.stdout.splitlines()[-1] == f"smoke: {len(PROBLEMS)} check(s) failed"


def test_edge_and_portal_problems_each_give_their_own_fail_line(tree: Path, tmp_path: Path) -> None:
    """Independent checks, one run: the edge's answers, its named URLs, the portal's assets, secrets and tile dots."""
    page = '<script src="https://cdn.example.org/x.js"></script> client_secret=abc'
    curl = curl_rules(health="", foreign="200", headers="Server: caddy", named="502", tile="500", page=page)
    done = smoke(tree, tmp_path, docker_rules(HEALTHY), curl)
    assert fails(done) == [
        f"FAIL  edge /health: no 'ok' on 127.0.0.1:{PORT}",
        "FAIL  edge foreign Host: got 200, want 404",
        *[f"FAIL  named URL {h}: http 502. fix: is the stack running and on the network?" for h in HOSTS],
        "FAIL  edge headers: hardening headers missing",
        'FAIL  portal remote assets: src="https://cdn.example.org/x.js"',
        "FAIL  portal secrets: client_secret=abc",
        *[f"FAIL  tile dot {name}: monitor status 500 (red). fix: is the stack running and on the edge?" for name in ("Sign in", "Health", "Actual Budget", "Hello")],
    ], done.stdout


def test_an_empty_portal_page_names_the_command_that_starts_it(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, docker_rules(HEALTHY), curl_rules(page=""))
    assert "FAIL  portal page: empty. fix: make up STACK=portal" in fails(done)


def test_an_alias_without_a_caddyfile_block_or_tile_is_contract_drift(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, docker_rules(HEALTHY, aliases=(*HOSTS, "extra")))
    (drift,) = [line for line in fails(done) if "contract" in line]
    assert "extra.(alias without Caddyfile block: step 2);" in drift and "extra.(alias without tile: step 4);" in drift


def test_a_block_missing_from_the_aliases_is_contract_drift(tree: Path, tmp_path: Path) -> None:
    done = smoke(tree, tmp_path, docker_rules(HEALTHY, aliases=("actual", "gatus", "home", "id")))  # hello has block, tile and target, no alias
    (drift,) = [line for line in fails(done) if "contract" in line]
    assert "hello.(Caddyfile block without alias: step 1);" in drift and "hello.(tile without alias: step 1);" in drift


def test_a_tile_without_a_health_target_is_contract_drift(tree: Path, tmp_path: Path) -> None:
    config = tree / "stacks" / "gatus" / "config" / "config.yaml"
    config.write_text("".join(line for line in config.read_text().splitlines(keepends=True) if "hello." not in line))
    done = smoke(tree, tmp_path, docker_rules(HEALTHY))
    (drift,) = [line for line in fails(done) if "contract" in line]
    assert "hello.(tile without health target: stacks/gatus/config/config.yaml);" in drift
