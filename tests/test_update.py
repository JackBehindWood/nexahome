"""`nexahome update`: feed, checksum, confirmation and installer choice, all with replaced network and installer."""

import hashlib
import importlib.metadata
import json
import sys
import threading
from collections.abc import Callable, Iterator, Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from nexahome import __version__, cli
from nexahome.release import updater as update
from nexahome.errors import ExitCode
from nexahome.release.net import NetworkError
from nexahome.runner import RunResult

from conftest import MakeContext

FEED_URL = "https://releases.example/latest"
WHEEL = b"pretend wheel bytes"
WHEEL_NAME = "nexahome-9.9.0-py3-none-any.whl"
WHEEL_URL = f"https://releases.example/{WHEEL_NAME}"
SUMS_URL = "https://releases.example/SHA256SUMS"
SUMS = f"{hashlib.sha256(WHEEL).hexdigest()}  {WHEEL_NAME}\n".encode()


def feed(tag: str = "v9.9.0", assets: dict[str, str] | None = None) -> bytes:
    named = {WHEEL_NAME: WHEEL_URL, "SHA256SUMS": SUMS_URL} if assets is None else assets
    return json.dumps({"tag_name": tag, "assets": [{"name": n, "browser_download_url": u} for n, u in named.items()]}).encode()


class Net:
    """A replacement for the network: answers by address, records what was asked."""

    def __init__(self, answers: dict[str, bytes | Exception]) -> None:
        self.answers, self.asked = answers, []  # type: ignore[var-annotated]

    def __call__(self, url: str, *, timeout: float, max_bytes: int) -> bytes:
        self.asked.append(url)
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        return answer

    def download(self, url: str, destination: Path, *, timeout: float, max_bytes: int) -> str:
        """Like net.http_download: write the file, return its SHA-256."""
        data = self(url, timeout=timeout, max_bytes=max_bytes)
        destination.write_bytes(data)
        return hashlib.sha256(data).hexdigest()


class Installer:
    """A runner that accepts everything, remembers the commands and what the wheel file held at install time."""

    def __init__(self, pip: bool = True, uv: bool = True, install_ok: bool = True) -> None:
        self.pip, self.uv, self.install_ok = pip, uv, install_ok
        self.calls: list[tuple[str, ...]] = []
        self.installed_bytes: bytes | None = None

    def run(self, argv: Sequence[str], *, timeout: float) -> RunResult:
        self.calls.append(tuple(argv))
        if argv[-1] == "--version":
            return RunResult(0) if (self.pip if "pip" in argv else self.uv) else RunResult(127, missing=True)
        self.installed_bytes = Path(argv[-1]).read_bytes()
        return RunResult(0) if self.install_ok else RunResult(1, stderr="boom\nno space left")


def make(make_context: MakeContext, answers: dict[str, bytes | Exception], runner: Installer | None = None,
         ask: Callable[[str], bool | None] | None = None, env: dict[str, str] | None = None) -> tuple:  # type: ignore[type-arg]
    ctx = make_context(runner=runner or Installer(), env={"NEXAHOME_UPDATE_URL": FEED_URL, **(env or {})})
    ctx.fetch = Net(answers)
    ctx.download = ctx.fetch.download
    ctx.ask = ask or (lambda question: True)
    return ctx, ctx.fetch


@pytest.fixture(autouse=True)
def not_editable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(update, "installed_as_editable", lambda: False)


def text(ctx: object, stream: str = "out") -> str:
    return getattr(ctx, stream).getvalue()


GOOD = {FEED_URL: feed(), SUMS_URL: SUMS, WHEEL_URL: WHEEL}


def test_available_says_so_and_installs_nothing(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, network = make(make_context, GOOD, installer)
    assert cli.main(["update", "--available"], ctx) == ExitCode.OK
    assert text(ctx) == f"update available: {__version__} -> v9.9.0\nRun: nexahome update\n"
    assert network.asked == [FEED_URL] and installer.calls == []


def test_available_when_up_to_date_and_as_json(make_context: MakeContext) -> None:
    ctx, _ = make(make_context, {FEED_URL: feed(tag=__version__)})
    assert cli.main(["update", "--available"], ctx) == ExitCode.OK and text(ctx) == f"up to date ({__version__})\n"
    ctx2, _ = make(make_context, GOOD)
    cli.main(["update", "--available", "--json"], ctx2)
    assert json.loads(text(ctx2)) == {"schema": 1, "installed": __version__, "latest": "v9.9.0", "available": True}


def test_update_checks_first_and_stops_when_current(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, _ = make(make_context, {FEED_URL: feed(tag="0.0.1")}, installer, ask=lambda q: pytest.fail("must not ask"))
    assert cli.main(["update"], ctx) == ExitCode.OK
    assert "already up to date" in text(ctx) and installer.calls == []


def test_update_asks_and_installs_the_verified_wheel_with_pip(make_context: MakeContext) -> None:
    installer, questions = Installer(), []
    ctx, _ = make(make_context, GOOD, installer, ask=lambda q: questions.append(q) or True)
    assert cli.main(["update"], ctx) == ExitCode.OK
    assert questions == [f"Update nexahome from {__version__} to v9.9.0? [y/N] "]
    assert installer.calls[0] == (sys.executable, "-m", "pip", "--version")
    assert installer.calls[1][:6] == (sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--quiet")
    assert installer.installed_bytes == WHEEL
    assert text(ctx).endswith(f"updated nexahome {__version__} -> v9.9.0. Check with: nexahome --version\n")


def test_without_pip_it_uses_the_uv_tool_environment(make_context: MakeContext) -> None:
    installer = Installer(pip=False)
    ctx, _ = make(make_context, GOOD, installer)
    assert cli.main(["update", "--yes"], ctx) == ExitCode.OK
    assert installer.calls[-1][:4] == ("uv", "tool", "install", "--force")


def test_without_pip_or_uv_the_error_ends_in_a_command(make_context: MakeContext) -> None:
    ctx, _ = make(make_context, GOOD, Installer(pip=False, uv=False))
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY
    assert text(ctx, "err").endswith(f"Next: uv tool install --force {WHEEL_URL}\n")


def test_declining_changes_nothing(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, network = make(make_context, GOOD, installer, ask=lambda q: False)
    assert cli.main(["update"], ctx) == ExitCode.OK
    assert text(ctx).endswith("not updated\n") and installer.calls == [] and network.asked == [FEED_URL]


def test_yes_skips_the_question(make_context: MakeContext) -> None:
    ctx, _ = make(make_context, GOOD, ask=lambda q: pytest.fail("must not ask"))
    assert cli.main(["update", "--yes"], ctx) == ExitCode.OK


def test_no_terminal_and_no_yes_is_an_error_with_the_fix(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, _ = make(make_context, GOOD, installer, ask=lambda q: None)
    assert cli.main(["update"], ctx) == ExitCode.NOT_READY
    assert text(ctx, "err") == "FAIL  cannot ask for confirmation: input is not a terminal\nNext: nexahome update --yes\n"
    assert installer.calls == []


def test_a_wrong_checksum_installs_nothing(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, _ = make(make_context, {**GOOD, WHEEL_URL: WHEEL + b"tampered"}, installer)
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY
    assert "does not match its SHA256SUMS entry; nothing was installed" in text(ctx, "err") and installer.calls == []


@pytest.mark.parametrize(
    "assets",
    [{WHEEL_NAME: WHEEL_URL}, {"SHA256SUMS": SUMS_URL}, {WHEEL_NAME: WHEEL_URL, "nexahome-1.0.0-py3-none-any.whl": WHEEL_URL, "SHA256SUMS": SUMS_URL},
     {"../x/nexahome-9.9.0-py3-none-any.whl": WHEEL_URL, "SHA256SUMS": SUMS_URL}],
    ids=["no sums", "no wheel", "two wheels", "path in name"],
)
def test_an_incomplete_release_installs_nothing(make_context: MakeContext, assets: dict[str, str]) -> None:
    installer = Installer()
    ctx, _ = make(make_context, {**GOOD, FEED_URL: feed(assets=assets)}, installer)
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY and installer.calls == []


def test_an_installer_failure_is_reported_with_its_last_line(make_context: MakeContext) -> None:
    ctx, _ = make(make_context, GOOD, Installer(install_ok=False))
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY
    assert "the installer failed: no space left" in text(ctx, "err")


def test_a_development_install_is_left_to_git_and_not_asked(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    monkeypatch.setattr(update, "installed_as_editable", lambda: True)
    ctx, _ = make(make_context, GOOD, ask=lambda q: pytest.fail("must not ask"))
    assert cli.main(["update"], ctx) == ExitCode.NOT_READY
    assert text(ctx, "err").endswith("Next: git pull --ff-only\n")
    ctx2, _ = make(make_context, GOOD)
    assert cli.main(["update", "--available"], ctx2) == ExitCode.OK  # asking is always allowed


def test_no_source_configured(make_context: MakeContext) -> None:
    ctx = make_context(env={})
    assert cli.main(["update", "--available"], ctx) == ExitCode.NOT_READY
    assert text(ctx, "err").startswith("FAIL  no update source is configured\nNext: export NEXAHOME_UPDATE_URL=")


@pytest.mark.parametrize(
    "answer",
    [NetworkError("connection refused"), b"not json", b"[]", b'{"tag_name": "latest"}', b'{"assets": []}'],
    ids=["unreachable", "not json", "wrong shape", "unreadable tag", "no tag"],
)
def test_a_bad_feed_is_an_error_that_retries_with_available(make_context: MakeContext, answer: bytes | Exception) -> None:
    ctx, _ = make(make_context, {FEED_URL: answer})
    assert cli.main(["update", "--available"], ctx) == ExitCode.NOT_READY
    assert text(ctx, "err").endswith("Next: nexahome update --available\n")


def test_a_download_failure_installs_nothing(make_context: MakeContext) -> None:
    installer = Installer()
    ctx, _ = make(make_context, {**GOOD, WHEEL_URL: NetworkError("timed out")}, installer)
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY
    assert "could not download the release: timed out" in text(ctx, "err") and installer.calls == []


def test_the_source_can_come_from_the_installed_package_metadata(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    monkeypatch.setattr(importlib.metadata, "metadata", lambda name: type("M", (), {"get_all": lambda self, key: ["Docs, https://x.example/d", "Latest release, https://x.example/feed"]})())
    assert update.update_source(make_context(env={})) == "https://x.example/feed"
    assert update.update_source(make_context(env={"NEXAHOME_UPDATE_URL": "https://y.example/f"})) == "https://y.example/f"


# The same flow over a real local HTTP server and the real fetcher; only the installer is replaced.
class Release(BaseHTTPRequestHandler):
    files: dict[str, bytes] = {}

    def do_GET(self) -> None:  # noqa: N802
        body = self.files.get(self.path)
        if body is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def release_server() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Release)
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    Release.files = {
        "/latest": feed(assets={WHEEL_NAME: f"{base}/{WHEEL_NAME}", "SHA256SUMS": f"{base}/SHA256SUMS"}),
        "/SHA256SUMS": SUMS,
        f"/{WHEEL_NAME}": WHEEL,
    }
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield base
    httpd.shutdown()
    httpd.server_close()
    thread.join(5)


def test_end_to_end_over_a_local_server(release_server: str, make_context: MakeContext) -> None:
    installer = Installer()
    ctx = make_context(runner=installer, env={"NEXAHOME_UPDATE_URL": f"{release_server}/latest"})
    ctx.ask = lambda question: True
    assert cli.main(["update"], ctx) == ExitCode.OK
    assert installer.installed_bytes == WHEEL


class FakeDistribution:
    def __init__(self, direct_url: str | None) -> None:
        self.direct_url = direct_url

    def read_text(self, name: str) -> str | None:
        return self.direct_url if name == "direct_url.json" else None


@pytest.mark.parametrize(
    ("direct_url", "editable"),
    [('{"url": "file:///x", "dir_info": {"editable": true}}', True), ('{"url": "file:///x", "dir_info": {}}', False), (None, False), ("not json", False)],
)
def test_editable_installs_are_recognised_from_the_install_record(monkeypatch: pytest.MonkeyPatch, direct_url: str | None, editable: bool) -> None:
    monkeypatch.undo()  # drop the autouse stub so the real function runs
    monkeypatch.setattr(importlib.metadata, "distribution", lambda name: FakeDistribution(direct_url))
    assert update.installed_as_editable() is editable


def test_a_missing_package_record_is_not_editable_and_has_no_source(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    monkeypatch.undo()

    def missing(name: str) -> object:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "distribution", missing)
    monkeypatch.setattr(importlib.metadata, "metadata", missing)
    assert update.installed_as_editable() is False
    assert update.update_source(make_context(env={})) is None


def test_a_wheel_name_with_a_path_is_refused(make_context: MakeContext) -> None:
    sneaky = "nexahome-1/../../evil.whl"
    installer = Installer()
    ctx, _ = make(make_context, {**GOOD, FEED_URL: feed(assets={sneaky: WHEEL_URL, "SHA256SUMS": SUMS_URL})}, installer)
    assert cli.main(["update", "--yes"], ctx) == ExitCode.NOT_READY
    assert "names its wheel with a path" in text(ctx, "err") and installer.calls == []
