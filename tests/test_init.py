"""nexahome init: a new folder from the bundled stacks (PK6-2 to PK6-4, PK6-14, PK6-15)."""

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.instance import REINSTALL, bundle, create, manifest
from nexahome.runner import SubprocessRunner

from conftest import REPO, FakeRunner, MakeCheckout, MakeContext, has_compose


def out(ctx: object) -> str:
    return ctx.out.getvalue()  # type: ignore[attr-defined]


def err(ctx: object) -> str:
    return ctx.err.getvalue()  # type: ignore[attr-defined]


def listing(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))


def init(make_context: MakeContext, target: Path, **options: object) -> tuple[int, object]:
    ctx = make_context(cwd=target.parent, runner=FakeRunner(), **options)  # type: ignore[arg-type]
    return cli.main(["init", str(target)], ctx), ctx


def test_the_summary_counts_services_not_the_template_or_the_backup_tool(make_context: MakeContext, tmp_path: Path) -> None:
    code, ctx = init(make_context, tmp_path / "made")
    services = [p for p in (REPO / "stacks").iterdir() if p.is_dir() and p.name not in ("_template", "backup")]  # P-28
    assert code == ExitCode.OK and f": {len(services)} stacks," in out(ctx)


def test_the_stacks_are_found_without_a_wheel_or_a_makefile() -> None:
    assert bundle.location() in (REPO / "stacks", Path(bundle.__file__).resolve().parents[1] / "_stacks")


def test_init_copies_what_the_wheel_ships_and_nothing_else(make_context: MakeContext, tmp_path: Path) -> None:
    root = tmp_path / "made"
    code, ctx = init(make_context, root)
    assert code == ExitCode.OK
    _, files = bundle.walk(bundle.location())  # type: ignore[arg-type]
    expected = {f"stacks/{name}" for name in files} | {"nexahome.toml", ".nexahome/manifest.json"}
    assert {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} == expected
    assert not [p for p in root.rglob("*") if p.name == ".env" or p.name == "README.md" or p.name == "data"]
    assert "Next: cd " in out(ctx) and "nexahome doctor" in out(ctx)


def test_nexahome_toml_and_the_manifest_describe_the_copy(make_context: MakeContext, tmp_path: Path) -> None:
    root = tmp_path / "made"
    init(make_context, root)
    settings = tomllib.loads((root / "nexahome.toml").read_text())
    assert settings["schema"] == 1 and settings["stacks"] == ["hello"] and settings["created_by"].startswith("nexahome ")
    recorded = json.loads((root / manifest.PATH).read_text())
    assert recorded["schema"] == 1 and "stacks/hello/compose.yaml" in recorded["files"]
    assert "nexahome.toml" not in recorded["files"] and manifest.PATH not in recorded["files"]  # the user's file, and itself
    for name, digest in recorded["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("mask", [0o022, 0o077])
def test_package_files_are_readable_by_container_users_whatever_the_umask(make_context: MakeContext, tmp_path: Path, mask: int) -> None:
    root = tmp_path / f"made-{mask:o}"
    previous = os.umask(mask)
    try:
        init(make_context, root)
    finally:
        os.umask(previous)
    modes = {p: p.stat().st_mode & 0o777 for p in [root, *root.rglob("*")]}
    assert {m for p, m in modes.items() if p.is_dir()} == {0o755}
    assert {m for p, m in modes.items() if p.is_file()} == {0o644}


def test_an_empty_existing_folder_is_filled_and_stays(make_context: MakeContext, tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    assert init(make_context, root)[0] == ExitCode.OK and (root / "nexahome.toml").is_file()


def test_missing_parents_are_created(make_context: MakeContext, tmp_path: Path) -> None:
    assert init(make_context, tmp_path / "a" / "b" / "made")[0] == ExitCode.OK and (tmp_path / "a" / "b" / "made" / "nexahome.toml").is_file()


@pytest.mark.parametrize("what", ["non-empty folder", "file", "instance itself", "inside an instance", "inside a clone"])
def test_init_refuses_and_writes_nothing(make_context: MakeContext, make_checkout: MakeCheckout, tmp_path: Path, what: str) -> None:
    base = tmp_path / "base"
    base.mkdir()
    if what == "non-empty folder":
        target = base / "full"
        target.mkdir()
        (target / "mine.txt").write_text("keep")
    elif what == "file":
        target = base / "afile"
        target.write_text("keep")
    elif what == "instance itself":
        target = base / "inst"
        assert init(make_context, target)[0] == ExitCode.OK
    elif what == "inside an instance":
        assert init(make_context, base / "inst")[0] == ExitCode.OK
        target = base / "inst" / "stacks" / "new"
    else:
        target = make_checkout(root=base / "clone") / "mine"
    before = listing(base)
    code, ctx = init(make_context, target)
    assert code == ExitCode.NOT_READY
    assert err(ctx).startswith("FAIL  ") and "\nNext: " in err(ctx)
    assert listing(base) == before
    if what == "inside a clone":
        assert err(ctx).endswith("Next: git pull --ff-only\n")


def test_a_failed_write_removes_only_what_this_run_made(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, tmp_path: Path) -> None:
    root = tmp_path / "made"
    root.mkdir()  # exists and empty: init may fill it, and must leave it standing
    real, calls = create._write, []

    def failing(path: Path, data: bytes, created: list[Path]) -> None:
        calls.append(path)
        if len(calls) == 5:
            raise OSError(28, "No space left on device")
        real(path, data, created)

    monkeypatch.setattr(create, "_write", failing)
    code, ctx = init(make_context, root)
    assert code == ExitCode.NOT_READY and "No space left" in err(ctx) and f"Next: nexahome init {root}" in err(ctx)
    assert root.is_dir() and listing(root) == []


def test_a_failed_write_removes_a_folder_it_created(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, tmp_path: Path) -> None:
    def failing(path: Path, data: bytes, created: list[Path]) -> None:
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(create, "_write", failing)
    assert init(make_context, tmp_path / "x" / "made")[0] == ExitCode.NOT_READY
    assert not (tmp_path / "x").exists()


def test_the_default_folder_is_nexahome_under_the_home_directory(make_context: MakeContext, make_host, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    user_home = tmp_path / "user"
    user_home.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    ctx = make_context(host=make_host(home=user_home), cwd=elsewhere, runner=FakeRunner())
    assert cli.main(["init"], ctx) == ExitCode.OK and (user_home / "nexahome" / "nexahome.toml").is_file()


def test_the_home_setting_names_the_folder(make_context: MakeContext, tmp_path: Path) -> None:
    ctx = make_context(cwd=tmp_path, runner=FakeRunner(), env={"NEXAHOME_HOME": "via-env"})
    assert cli.main(["init"], ctx) == ExitCode.OK and (tmp_path / "via-env" / "nexahome.toml").is_file()
    ctx = make_context(cwd=tmp_path, runner=FakeRunner())
    assert cli.main(["--home", "via-option", "init"], ctx) == ExitCode.OK and (tmp_path / "via-option" / "nexahome.toml").is_file()


def test_init_without_bundled_stacks_ends_in_one_command(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, tmp_path: Path) -> None:
    monkeypatch.setattr(bundle, "location", lambda: None)
    code, ctx = init(make_context, tmp_path / "made")
    assert code == ExitCode.NOT_READY and err(ctx).endswith(f"Next: {REINSTALL}\n") and not (tmp_path / "made").exists()
    assert "reinstall nexahome" not in REINSTALL  # P-01: no PyPI project of this name is ours; install from the wheel


def test_the_filter_keeps_local_secrets_and_readmes_out(tmp_path: Path) -> None:
    source = tmp_path / "stacks"
    for name in ["app/compose.yaml", "app/.env.example", "app/.env", "app/.env.prod", "app/README.md", "app/tls.key", "app/data/db", "app/www/index.html"]:
        (source / name).parent.mkdir(parents=True, exist_ok=True)
        (source / name).write_text("x")
    directories, files = bundle.walk(source)
    assert files == ["app/.env.example", "app/compose.yaml", "app/www/index.html"]
    assert directories == ["app", "app/www"]


def test_init_needs_no_network_modules(tmp_path: Path) -> None:
    """PK6-3: a fresh process that runs init has not imported anything that can reach the network."""
    code = (
        "import sys; from nexahome.cli import main; rc = main(['init', sys.argv[1]]); "
        "bad = sorted(m for m in ('urllib', 'urllib.request', 'http.client', 'ssl', 'socket') if m in sys.modules); "
        "bad += sorted(m for m in sys.modules if m.endswith('.net') and m.startswith('nexahome')); "
        "print(rc, bad)"
    )
    done = subprocess.run([sys.executable, "-I", "-c", code, str(tmp_path / "made")], capture_output=True, text=True, cwd=tmp_path)
    assert done.stdout.strip().endswith("0 []"), done.stdout + done.stderr


@pytest.mark.skipif(not has_compose(), reason="needs the Docker CLI with the Compose plugin (no engine)")
def test_init_output_passes_nexahome_check(make_context: MakeContext, tmp_path: Path) -> None:
    """PK6-4: what init makes satisfies the Compose policy, run for real against the copied files."""
    root = tmp_path / "made"
    assert init(make_context, root)[0] == ExitCode.OK
    ctx = make_context(cwd=root, runner=SubprocessRunner())
    names = sorted(p.parent.name for p in (root / "stacks").glob("*/compose.yaml"))
    assert cli.main(["check"], ctx) == ExitCode.OK
    assert out(ctx) == "".join(f"stacks/{n}/compose.yaml: ok\n" for n in names)


def test_the_commands_init_prints_are_the_ones_the_readme_gives(make_context: MakeContext, tmp_path: Path) -> None:
    """PK6-18: one owner for the run commands (init, built from the docker package); the README repeats them verbatim."""
    code, ctx = init(make_context, tmp_path / "made")
    printed = [line.strip() for line in out(ctx).splitlines() if line.startswith("  docker ")]
    assert code == ExitCode.OK and len(printed) == 3
    readme = (REPO / "README.md").read_text()
    assert [line for line in printed if line not in readme] == []
