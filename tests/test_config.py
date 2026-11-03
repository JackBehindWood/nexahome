"""nexahome config and the strict reader behind it (PK6-7, PK6-8, PK6-13)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from nexahome import cli
from nexahome.stacks import catalogue as stacks
from nexahome.errors import ExitCode, NexaHomeError
from nexahome.instance import config
from nexahome.runner import RunResult

from conftest import DOCKER_HEALTHY, FakeRunner, MakeCheckout, MakeContext, MakeHost
from test_instance import make_instance


def out(ctx: object) -> str:
    return ctx.out.getvalue()  # type: ignore[attr-defined]


def err(ctx: object) -> str:
    return ctx.err.getvalue()  # type: ignore[attr-defined]


@pytest.fixture
def instance(tmp_path: Path) -> Path:
    root = make_instance(tmp_path / "made", ("hello", "actual", "edge", "identity"))
    (root / "nexahome.toml").write_text(config.render(("hello",)))  # four stacks exist, one is enabled, as after init
    return root


def run(make_context: MakeContext, root: Path, *words: str) -> tuple[int, object]:
    ctx = make_context(cwd=root, runner=FakeRunner())
    return cli.main(["config", *words], ctx), ctx


def test_list_shows_every_setting_and_marks_the_read_only_ones(make_context: MakeContext, instance: Path) -> None:
    (instance / "nexahome.toml").write_text(config.render(("hello", "actual"), "nexahome 9.9"))
    code, ctx = run(make_context, instance)
    assert code == ExitCode.OK
    assert out(ctx).splitlines() == ["schema      1  (read-only)", "created_by  nexahome 9.9  (read-only)", "stacks      hello actual"]


def test_get_prints_the_value_alone(make_context: MakeContext, instance: Path) -> None:
    code, ctx = run(make_context, instance, "get", "stacks")
    assert code == ExitCode.OK and out(ctx) == "hello\n"


def test_set_stacks_round_trips_and_keeps_created_by(make_context: MakeContext, instance: Path) -> None:
    (instance / "nexahome.toml").write_text(config.render(("hello",), "nexahome 9.9"))
    code, ctx = run(make_context, instance, "set", "stacks", "hello", "actual", "hello")  # a repeat is dropped
    assert code == ExitCode.OK and out(ctx) == "stacks hello actual\nNext: nexahome env\n"
    settings = config.read(instance)
    assert settings == config.Settings(1, "nexahome 9.9", ("hello", "actual"))
    assert (instance / "nexahome.toml").stat().st_mode & 0o777 == 0o644
    assert [p.name for p in instance.iterdir() if p.name.startswith(".nexahome.toml")] == []  # no temporary file left


@pytest.mark.parametrize(
    ("words", "fragment", "fix"),
    [
        (("set", "stacks"), "at least one stack", "nexahome stacks"),
        (("set", "stacks", "nope"), "no stack called 'nope'", "nexahome stacks"),
        (("set", "stacks", "../x"), "not a stack name", "nexahome stacks"),
        (("set", "schema", "2"), "read-only", "nexahome config list"),
        (("set", "colour", "red"), "unknown setting 'colour'", "nexahome config list"),
        (("set",), "needs a setting", "nexahome config list"),
        (("get", "colour"), "unknown setting", "nexahome config list"),
    ],
)
def test_a_wrong_setting_or_value_is_refused_with_exit_2_and_changes_nothing(
    make_context: MakeContext, instance: Path, words: tuple[str, ...], fragment: str, fix: str
) -> None:
    before = (instance / "nexahome.toml").read_text()
    code, ctx = run(make_context, instance, *words)
    assert code == ExitCode.USAGE and fragment in err(ctx) and err(ctx).endswith(f"Next: {fix}\n")
    assert (instance / "nexahome.toml").read_text() == before


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ("stacks = [", "not valid TOML"),
        ('schema = "one"\nstacks = ["hello"]\n', "schema must be a number"),
        ('schema = 0\nstacks = ["hello"]\n', "schema must be a number"),
        ('schema = -5\nstacks = ["hello"]\n', "schema must be a number"),
        ('schema = 1\nstacks = ["hello"]\ncolour = "red"\n', "unknown key colour"),
        ('schema = 1\nstacks = "hello"\n', "stacks a list"),
        ("schema = 1\nstacks = []\n", "at least one stack"),
        ('schema = 1\nstacks = ["gone"]\n', "no stack called 'gone'"),
        ('schema = 1\nstacks = ["../hello"]\n', "not a stack name"),
    ],
)
def test_a_broken_file_is_refused_with_the_command_that_opens_it(make_context: MakeContext, instance: Path, text: str, fragment: str) -> None:
    (instance / "nexahome.toml").write_text(text)
    code, ctx = run(make_context, instance)
    assert code == ExitCode.NOT_READY and fragment in err(ctx) and "Next: ${EDITOR:-vi} " in err(ctx) and "nexahome.toml" in err(ctx)


def test_a_newer_schema_is_refused_with_the_update_command(make_context: MakeContext, instance: Path) -> None:
    (instance / "nexahome.toml").write_text('schema = 2\nstacks = ["hello"]\nfuture = true\n')
    code, ctx = run(make_context, instance)
    assert code == ExitCode.NOT_READY and "schema 2" in err(ctx) and err(ctx).endswith("Next: nexahome update --available\n")


def test_set_repairs_a_file_that_cannot_be_read(make_context: MakeContext, instance: Path) -> None:
    (instance / "nexahome.toml").write_text("stacks = [")
    assert run(make_context, instance, "set", "stacks", "hello")[0] == ExitCode.OK
    assert config.read(instance) is not None


def test_a_failed_replace_leaves_the_old_file_and_no_temporary(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, instance: Path) -> None:
    before = (instance / "nexahome.toml").read_text()

    def broken(source: str, target: object) -> None:
        raise OSError(5, "I/O error")

    monkeypatch.setattr(os, "replace", broken)
    with pytest.raises(OSError):
        config.write(instance, ("hello", "actual"))
    assert (instance / "nexahome.toml").read_text() == before
    assert [p.name for p in instance.iterdir() if p.name.startswith(".nexahome.toml")] == []


def test_a_clone_is_pointed_at_the_file_the_makefile_reads(make_context: MakeContext, make_checkout: MakeCheckout) -> None:
    code, ctx = run(make_context, make_checkout())
    assert code == ExitCode.NOT_READY and "git clone" in err(ctx) and err(ctx).endswith("Next: ${EDITOR:-vi} .config/stacks\n")


def test_outside_any_instance_the_command_says_how_to_make_one(make_context: MakeContext, tmp_path: Path) -> None:
    code, ctx = run(make_context, tmp_path)
    assert code == ExitCode.NOT_READY and err(ctx).endswith("Next: nexahome init\n")


def test_enabled_stacks_come_from_nexahome_toml_core_first(instance: Path) -> None:
    (instance / "nexahome.toml").write_text(config.render(("hello", "edge", "identity")))
    assert stacks.enabled(instance) == ["edge", "identity", "hello"]


def test_a_clone_still_reads_dot_config_stacks(make_checkout: MakeCheckout, tmp_path: Path) -> None:
    clone = make_checkout({"a": None, "b": None})
    (clone / ".config").mkdir()
    (clone / ".config" / "stacks").write_text("b\n")
    assert stacks.enabled(clone) == ["b"]


def test_env_in_an_instance_prepares_only_the_enabled_stacks_and_ends_in_commands(make_context: MakeContext, instance: Path) -> None:
    for name in ("hello", "actual"):
        (instance / "stacks" / name / ".env.example").write_text("PORT=1\n")
    (instance / "nexahome.toml").write_text(config.render(("hello",)))
    ctx = make_context(cwd=instance, runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["env"], ctx) == ExitCode.OK
    assert (instance / "stacks" / "hello" / ".env").is_file() and not (instance / "stacks" / "actual" / ".env").exists()
    assert (instance / "stacks" / "hello" / ".env").stat().st_mode & 0o777 == 0o600
    assert "Next: docker network inspect nexahome-edge" in out(ctx) and "docker compose -f stacks/hello/compose.yaml up -d --wait" in out(ctx)
    assert "make up" not in out(ctx)


def test_doctor_checks_the_mount_for_an_instance_outside_the_home_directory(make_context: MakeContext, make_host: MakeHost, tmp_path: Path) -> None:
    user_home = tmp_path / "user"
    user_home.mkdir()
    host = make_host(system="macos", home=user_home)
    inside = make_instance(user_home / "nexahome")
    outside = make_instance(tmp_path / "elsewhere")
    runner = FakeRunner({**DOCKER_HEALTHY, ("docker", "info", "--format", "{{.ServerVersion}}"): RunResult(0, "27.1.0\n")})
    ok = cli.main(["doctor", "--json"], make_context(host=host, cwd=inside, runner=runner))
    warn = make_context(host=host, cwd=outside, runner=runner)
    cli.main(["doctor", "--json"], warn)
    assert ok in (ExitCode.OK, ExitCode.NOT_READY)
    assert '"id": "mount"' in out(warn) and '"status": "warn"' in out(warn) and 'mv ' in out(warn)


def test_config_needs_no_network_modules(instance: Path) -> None:
    code = (
        "import sys; from nexahome.cli import main; rc = main(['--home', sys.argv[1], 'config']); "
        "print(rc, sorted(m for m in ('urllib', 'ssl', 'socket', 'http.client') if m in sys.modules))"
    )
    done = subprocess.run([sys.executable, "-I", "-c", code, str(instance)], capture_output=True, text=True)
    assert done.stdout.strip().endswith("0 []"), done.stdout + done.stderr
