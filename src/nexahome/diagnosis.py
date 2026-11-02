"""The probes behind `nexahome doctor` and `nexahome setup`: read-only diagnosis of this host.
Every warning and failure ends in one exact command.

To add a probe: write a function (ctx, prior) -> Check | None, add (id, function) to PROBES, add a row to
tests/test_doctor.py. A probe returns None when it does not apply, and SKIP when a prerequisite failed.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING
from pathlib import Path

from nexahome import envfile
from nexahome import platform as host_platform
from nexahome.context import Context
from nexahome.errors import NexaHomeError
from nexahome.report import Check, Status

ENGINE_TIMEOUT = 10  # seconds; a stuck VM must not hang the command
LOW_DISK_BYTES = 5 * 1024**3

type Probe = Callable[[Context, Mapping[str, Check]], Check | None]

if TYPE_CHECKING:
    from concurrent.futures import Future


def _skip(check_id: str, needs: str) -> Check:
    return Check(check_id, Status.SKIP, f"needs {needs}")


def probe_platform(ctx: Context, prior: Mapping[str, Check]) -> Check:
    try:
        host_platform.require_supported(ctx.host)
    except NexaHomeError as error:
        return Check("platform", Status.FAIL, error.message, error.fix)
    note = "" if host_platform.is_supported_machine(ctx.host) else " (untested architecture)"
    return Check("platform", Status.OK, host_platform.describe(ctx.host) + note)


def probe_python(ctx: Context, prior: Mapping[str, Check]) -> Check:
    return Check("python", Status.OK, ".".join(str(part) for part in ctx.host.python) + " (information)")


def probe_docker_cli(ctx: Context, prior: Mapping[str, Check]) -> Check:
    result = ctx.runner.run(["docker", "--version"], timeout=ENGINE_TIMEOUT)
    if not result.ok:
        return Check("docker-cli", Status.FAIL, "Docker CLI not found", host_platform.docker_install_fix(ctx.host))
    return Check("docker-cli", Status.OK, result.stdout.strip().splitlines()[0] if result.stdout.strip() else "found")


def probe_compose(ctx: Context, prior: Mapping[str, Check]) -> Check:
    if prior["docker-cli"].status != Status.OK:
        return _skip("compose", "docker-cli")
    result = ctx.runner.run(["docker", "compose", "version"], timeout=ENGINE_TIMEOUT)
    if not result.ok:
        return Check("compose", Status.FAIL, "Compose plugin not found", host_platform.compose_install_fix(ctx.host))
    return Check("compose", Status.OK, result.stdout.strip().splitlines()[0] if result.stdout.strip() else "found")


def probe_engine(ctx: Context, prior: Mapping[str, Check]) -> Check:
    if prior["docker-cli"].status != Status.OK:
        return _skip("engine", "docker-cli")
    result = ctx.runner.run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=ENGINE_TIMEOUT)
    if result.timed_out:
        return Check(
            "engine",
            Status.FAIL,
            f"the container runtime did not answer within {ENGINE_TIMEOUT} s",
            host_platform.engine_restart_fix(ctx.host),
        )
    if not result.ok:
        return Check("engine", Status.FAIL, "no container runtime running", host_platform.engine_start_fix(ctx.host))
    return Check("engine", Status.OK, f"running, server {result.stdout.strip() or 'version unknown'}")


def probe_disk(ctx: Context, prior: Mapping[str, Check]) -> Check:
    free = ctx.disk_free(ctx.cwd)
    summary = f"{free / 1024**3:.1f} GiB free where you are working"
    if free < LOW_DISK_BYTES:
        return Check("disk", Status.WARN, summary + " (under 5 GiB)", "df -h .")
    return Check("disk", Status.OK, summary)


def probe_mount(ctx: Context, prior: Mapping[str, Check]) -> Check | None:
    checkout = ctx.checkout()
    if checkout is None or not host_platform.colima_mount_applies(ctx.host):
        return None
    if checkout.is_relative_to(ctx.host.home):
        return Check("mount", Status.OK, "the checkout is under the home directory, which Colima mounts")
    import shlex  # only the warning branch quotes a path

    source = '"$PWD"' if checkout == ctx.cwd else shlex.quote(str(checkout))
    return Check(
        "mount",
        Status.WARN,
        "the checkout is outside the home directory, which the Colima VM does not mount",
        f'mv {source} "$HOME/"',
    )


def probe_env(ctx: Context, prior: Mapping[str, Check]) -> Check | None:
    checkout = ctx.checkout()
    if checkout is None:
        return None
    found: list[tuple[Path, str]] = []  # (the .env file, the key); values are never read into the output
    for env_file in sorted(checkout.glob("stacks/*/.env")):
        try:
            text = env_file.read_text()
        except OSError:
            continue
        found += [(env_file, key) for key in envfile.placeholders(text)]
    if not found:
        return Check("env", Status.OK, "no .env value is still CHANGE_ME")
    names = ", ".join(f"{path.parent.name}/{key}" for path, key in found)
    return Check(
        "env", Status.WARN, f"{len(found)} value(s) still CHANGE_ME: {names}", f"${{EDITOR:-vi}} {ctx.display(found[0][0])}"
    )


PROBES: tuple[tuple[str, Probe], ...] = (
    ("platform", probe_platform),
    ("python", probe_python),
    ("docker-cli", probe_docker_cli),
    ("compose", probe_compose),
    ("engine", probe_engine),
    ("disk", probe_disk),
    ("mount", probe_mount),
    ("env", probe_env),
)


class _Prior(Mapping[str, Check]):
    """The results of the other probes. Reading one waits until that probe has finished, so independent probes
    (three docker calls) run side by side and a dependent one (compose needs docker-cli) still sees its input."""

    def __init__(self, futures: "dict[str, Future[Check | None]]") -> None:
        self._futures = futures

    def __getitem__(self, probe_id: str) -> Check:
        check = self._futures[probe_id].result()
        if check is None:  # that probe did not apply
            raise KeyError(probe_id)
        return check

    def __iter__(self) -> Iterator[str]:
        return iter(self._futures)

    def __len__(self) -> int:
        return len(self._futures)


def _run_probe(probe_id: str, probe: Probe, ctx: Context, prior: Mapping[str, Check]) -> Check | None:
    try:
        return probe(ctx, prior)
    except Exception as error:  # a broken probe must not hide the others
        return Check(probe_id, Status.FAIL, f"the probe raised {type(error).__name__}", "nexahome doctor --json")


def run_probes(ctx: Context) -> list[Check]:
    from concurrent.futures import ThreadPoolExecutor

    futures: "dict[str, Future[Check | None]]" = {}
    prior = _Prior(futures)
    with ThreadPoolExecutor(max_workers=len(PROBES)) as pool:  # one thread per probe: none waits for a free worker
        for probe_id, probe in PROBES:
            futures[probe_id] = pool.submit(_run_probe, probe_id, probe, ctx, prior)
    results = (futures[probe_id].result() for probe_id, _ in PROBES)
    return [check for check in results if check is not None]
