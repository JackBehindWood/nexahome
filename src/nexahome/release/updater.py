"""The logic behind `nexahome update`: update this tool to the newest release. It always checks first and asks
before it installs.

`--available` only reports whether a newer version exists. The release source is the address in
$NEXAHOME_UPDATE_URL, else the "Latest release" project URL of the installed package; it must answer like GitHub's
"latest release" API (tag_name and assets). The wheel is installed only after its SHA256SUMS entry matches.
This updates the tool, not your stacks or data; a checkout is updated with git.
"""

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

from nexahome import __version__
from nexahome.release import versions
from nexahome.context import Context
from nexahome.defaults import (
    ENV_UPDATE_URL,
    FEED_MAX_BYTES,
    FEED_TIMEOUT,
    INSTALL_TIMEOUT,
    UPDATE_JSON_SCHEMA,
    WHEEL_MAX_BYTES,
    WHEEL_TIMEOUT,
)
from nexahome.errors import ExitCode, NexaHomeError
from nexahome.release.net import NetworkError

RETRY = "nexahome update --available"


class Release(NamedTuple):
    """A published version and its downloadable files by name."""

    version: str
    assets: dict[str, str]  # asset name -> https address


def update_source(ctx: Context) -> str | None:
    """The release feed address: `NEXAHOME_UPDATE_URL`, else the package's `Latest release` project URL; `None` when neither exists."""
    import importlib.metadata

    if ctx.env.get(ENV_UPDATE_URL):
        return ctx.env[ENV_UPDATE_URL]
    try:
        entries: list[str] = importlib.metadata.metadata("nexahome").get_all("Project-URL") or []
        for entry in entries:
            label, _, address = entry.partition(",")
            if label.strip() == "Latest release":
                return address.strip()
    except importlib.metadata.PackageNotFoundError:
        pass
    return None


def installed_as_editable() -> bool:
    """True for a development install (a git checkout), which `update` leaves to git."""
    import importlib.metadata

    try:
        text = importlib.metadata.distribution("nexahome").read_text("direct_url.json")
        return bool(text and json.loads(text).get("dir_info", {}).get("editable"))
    except (importlib.metadata.PackageNotFoundError, ValueError):
        return False


def latest_release(ctx: Context) -> Release:
    """Fetch and parse the release feed (https only, size capped)."""
    source = update_source(ctx)
    if source is None:
        raise NexaHomeError("no update source is configured", 'export NEXAHOME_UPDATE_URL="<the release feed address>"')
    try:
        feed: Any = json.loads(ctx.fetch(source, timeout=FEED_TIMEOUT, max_bytes=FEED_MAX_BYTES))
        version = str(feed["tag_name"])
        assets = {str(a["name"]): str(a["browser_download_url"]) for a in feed.get("assets", [])}
        versions.parse(version)
    except NetworkError as error:
        import shlex  # only this failure quotes the address

        # Repeating the failed command repeats the failure; this one shows whether the feed can be reached at all.
        raise NexaHomeError(f"could not read the update source: {error}", f"curl -sSI {shlex.quote(source)}") from error
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise NexaHomeError(f"the update source did not answer with a release I can read ({error})", RETRY) from error
    return Release(version, assets)


def _download(ctx: Context, release: Release, directory: Path) -> Path:
    import hmac

    wheels = [name for name in release.assets if name.startswith("nexahome-") and name.endswith(".whl")]
    if len(wheels) != 1 or "SHA256SUMS" not in release.assets:
        raise NexaHomeError("the release has no single wheel with a SHA256SUMS file; nothing was installed", RETRY)
    name = wheels[0]
    if Path(name).name != name:
        raise NexaHomeError("the release names its wheel with a path; nothing was installed", RETRY)
    path = directory / name
    try:
        sums = ctx.fetch(release.assets["SHA256SUMS"], timeout=FEED_TIMEOUT, max_bytes=FEED_MAX_BYTES).decode(errors="replace")
        actual = ctx.download(release.assets[name], path, timeout=WHEEL_TIMEOUT, max_bytes=WHEEL_MAX_BYTES)  # streamed, hashed
    except NetworkError as error:
        raise NexaHomeError(f"could not download the release: {error}", RETRY) from error
    expected = next((line.split()[0] for line in sums.splitlines() if line.split()[-1:] in ([name], ["*" + name])), "")
    if not hmac.compare_digest(actual, expected.lower()):
        path.unlink(missing_ok=True)
        raise NexaHomeError(f"{name} does not match its SHA256SUMS entry; nothing was installed", RETRY)
    return path


def _install(ctx: Context, wheel: Path, address: str) -> None:
    """Install into the environment this program runs in: pip if it has one, else uv's tool environment."""
    if ctx.runner.run([sys.executable, "-m", "pip", "--version"], timeout=30).ok:
        argv = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--quiet", str(wheel)]
    elif ctx.runner.run(["uv", "--version"], timeout=30).ok:
        argv = ["uv", "tool", "install", "--force", str(wheel)]
    else:
        raise NexaHomeError("neither pip nor uv is available to install the update", f"uv tool install --force {address}")
    done = ctx.runner.run(argv, timeout=INSTALL_TIMEOUT)
    if not done.ok:
        detail = (done.stderr.strip().splitlines() or ["no message"])[-1]
        raise NexaHomeError(f"the installer failed: {detail}", RETRY)


def update(ctx: Context, *, available_only: bool, as_json: bool, assume_yes: bool) -> int:
    """Check for a newer release; unless `available_only`, ask, download, verify against `SHA256SUMS` and install."""
    release = latest_release(ctx)
    newer = versions.is_newer(release.version, __version__)
    if available_only:
        if as_json:
            payload = {"schema": UPDATE_JSON_SCHEMA, "installed": __version__, "latest": release.version, "available": newer}
            print(json.dumps(payload, indent=2), file=ctx.out)
        elif newer:
            print(f"update available: {__version__} -> {release.version}\nRun: nexahome update", file=ctx.out)
        else:
            print(f"up to date ({__version__})", file=ctx.out)
        return ExitCode.OK
    if not newer:
        print(f"already up to date ({__version__}; the newest release is {release.version})", file=ctx.out)
        return ExitCode.OK
    print(f"A newer version is available: {__version__} -> {release.version}", file=ctx.out)
    if installed_as_editable():
        raise NexaHomeError("this is a development install (a git checkout); update does not change it", "git pull --ff-only")
    if not assume_yes:
        answer = ctx.ask(f"Update nexahome from {__version__} to {release.version}? [y/N] ")
        if answer is None:
            raise NexaHomeError("cannot ask for confirmation: input is not a terminal", "nexahome update --yes")
        if not answer:
            print("not updated", file=ctx.out)
            return ExitCode.OK
    import tempfile

    with tempfile.TemporaryDirectory(prefix="nexahome-update-") as temporary:
        wheel = _download(ctx, release, Path(temporary))
        _install(ctx, wheel, release.assets[wheel.name])
    print(f"updated nexahome {__version__} -> {release.version}. Check with: nexahome --version", file=ctx.out)
    return ExitCode.OK
