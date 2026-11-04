"""`nexahome stacks new` and `nexahome stacks remove`, and who owns a stack (Goal 3: G1 to G3, G6, G11)."""

import json
import os
import stat
import tomllib
from pathlib import Path

import pytest

from nexahome import cli, files
from nexahome.errors import ExitCode
from nexahome.instance import bundle
from nexahome.runner import RunResult
from nexahome.stacks import ownership

from nexahome.runner import SubprocessRunner

from conftest import REPO, FakeRunner, MakeCheckout, MakeContext, err, has_compose, ps_running_argv, out


def running(instance: Path, name: str, state: str) -> dict[tuple[str, ...], RunResult]:
    argv = ps_running_argv(instance / "stacks" / name / "compose.yaml")
    return {argv: RunResult(0, "abc\n" if state == "running" else "")}


def enabled(instance: Path) -> list[str]:
    return tomllib.loads((instance / "nexahome.toml").read_text())["stacks"]


def run(make_context: MakeContext, instance: Path, *arguments: str, runner: FakeRunner | None = None, answer: bool | None = None) -> tuple[int, object]:
    ctx = make_context(cwd=instance, runner=runner or FakeRunner())
    ctx.ask = lambda question: answer  # type: ignore[assignment,misc]
    return cli.main(["stacks", *arguments], ctx), ctx


# --- the template ships a README (the only one) -------------------------------------------------------------
def test_only_the_template_readme_is_bundled() -> None:
    assert bundle.wanted("README.md") is False  # still dropped everywhere ...
    _, files = bundle.walk(REPO / "stacks")
    assert [f for f in files if f.endswith("README.md")] == ["_template/README.md"]  # ... except the template's


# --- ownership ---------------------------------------------------------------------------------------------
def test_bundled_stack_names_are_package_owned(instance: Path) -> None:
    owned = ownership.package_owned(instance)
    assert {"hello", "edge", "_template"} <= owned
    assert "mine" not in owned


def test_the_manifest_adds_names_the_bundle_no_longer_has(instance: Path) -> None:
    manifest = instance / ".nexahome" / "manifest.json"
    data = json.loads(manifest.read_text())
    data["files"]["stacks/retired/compose.yaml"] = "0" * 64
    manifest.write_text(json.dumps(data))
    assert "retired" in ownership.package_owned(instance)


def test_a_folder_without_a_manifest_is_owned_only_by_the_bundle(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"demo": None, "hello": None})
    assert ownership.package_owned(checkout) >= {"hello"}
    assert "demo" not in ownership.package_owned(checkout)


# --- stacks new --------------------------------------------------------------------------------------------
def test_new_writes_the_three_files_renamed_and_enables_the_stack(make_context: MakeContext, instance: Path) -> None:
    code, ctx = run(make_context, instance, "new", "mine")
    assert code == ExitCode.OK, err(ctx)
    folder = instance / "stacks" / "mine"
    assert sorted(p.name for p in folder.iterdir()) == [".env.example", "README.md", "compose.yaml"]
    compose = (folder / "compose.yaml").read_text()
    assert "name: nexahome-mine" in compose and "MINE_PORT" in compose
    example = (folder / ".env.example").read_text()
    assert "MINE_PORT=" in example and "=CHANGE_ME" not in example  # the stack starts as generated
    for text in (compose, example, (folder / "README.md").read_text()):
        assert "TEMPLATE" not in text and "_template" not in text
    assert enabled(instance) == ["hello", "mine"]
    assert stat.S_IMODE((folder / "compose.yaml").stat().st_mode) == 0o644
    assert "docker compose -f stacks/mine/compose.yaml up -d --wait" in out(ctx)


def test_new_in_an_instance_never_tells_the_runner_to_use_make(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "mine")
    for name in ("README.md", "compose.yaml", ".env.example"):
        assert "make " not in (instance / "stacks" / "mine" / name).read_text()


def test_new_in_a_clone_keeps_make_and_leaves_the_list_alone(make_context: MakeContext, tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    (clone / "stacks").mkdir(parents=True)
    (clone / "Makefile").write_text("")
    code, ctx = run(make_context, clone, "new", "mine")
    assert code == ExitCode.OK, err(ctx)
    assert "make up STACK=mine" in (clone / "stacks" / "mine" / "README.md").read_text()
    assert not (clone / "nexahome.toml").exists()


def test_the_second_stack_gets_the_next_free_port(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "one")
    run(make_context, instance, "new", "two")
    assert "MINE" not in (instance / "stacks" / "two" / "compose.yaml").read_text()
    ports = [
        (instance / "stacks" / n / ".env.example").read_text().split("_PORT=")[1].split()[0] for n in ("one", "two")
    ]
    assert ports == ["8081", "8082"]


@pytest.mark.parametrize("name", ["Mine", "_mine", "a/b", "..", "has space", ""])
def test_new_refuses_a_bad_name_with_one_next_command(make_context: MakeContext, instance: Path, name: str) -> None:
    code, ctx = run(make_context, instance, "new", name)
    assert code == ExitCode.NOT_READY
    assert "is not a stack name" in err(ctx) and "\nNext: nexahome stacks new " in err(ctx)
    assert sorted(p.name for p in (instance / "stacks").iterdir() if p.name == name.strip()) == []


def test_new_refuses_a_package_name_and_an_existing_folder(make_context: MakeContext, instance: Path) -> None:
    code, ctx = run(make_context, instance, "new", "hello")
    assert code == ExitCode.NOT_READY and "part of NexaHome" in err(ctx) and err(ctx).endswith("Next: nexahome stacks new hello-2\n")
    (instance / "stacks" / "mine").mkdir()
    code, ctx = run(make_context, instance, "new", "mine")
    assert code == ExitCode.NOT_READY and "already exists" in err(ctx) and "Next: nexahome stacks\n" in err(ctx)


def test_new_without_an_instance_says_how_to_make_one(make_context: MakeContext, tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    code, ctx = run(make_context, tmp_path / "empty", "new", "mine")
    assert code == ExitCode.NOT_READY and err(ctx).endswith("Next: nexahome init\n")


def test_a_failed_write_leaves_no_folder_and_the_list_unchanged(
    make_context: MakeContext, instance: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = files.create_exclusive
    calls: list[Path] = []

    def flaky(path: Path, data: bytes, mode: int, created: list[Path] | None = None) -> None:
        calls.append(path)
        if len(calls) == 2:
            raise OSError("disk full")
        real(path, data, mode, created)

    monkeypatch.setattr(files, "create_exclusive", flaky)
    code, ctx = run(make_context, instance, "new", "mine")
    assert code == ExitCode.NOT_READY and "disk full" in err(ctx)
    assert not (instance / "stacks" / "mine").exists()
    assert enabled(instance) == ["hello"]


@pytest.mark.skipif(not has_compose(), reason="needs the Docker CLI with the Compose plugin (no engine)")
def test_the_generated_stack_passes_the_policy(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "mine")
    ctx = make_context(cwd=instance, runner=SubprocessRunner())
    assert cli.main(["check"], ctx) == ExitCode.OK, out(ctx) + err(ctx)
    assert "stacks/mine/compose.yaml: ok" in out(ctx)


# --- stacks (the list) -------------------------------------------------------------------------------------
def test_the_list_says_who_owns_each_stack(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "mine")
    code, ctx = run(make_context, instance)
    assert code == ExitCode.OK
    lines = out(ctx).splitlines()
    assert lines[0].split() == ["stack", "enabled", "owner", "state"]
    assert next(line for line in lines if line.startswith("mine")).split()[:3] == ["mine", "yes", "user"]
    assert next(line for line in lines if line.startswith("hello")).split()[:3] == ["hello", "yes", "package"]


def test_the_json_list_adds_an_owner_and_keeps_schema_1(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "mine")
    code, ctx = run(make_context, instance, "--json")
    rows = {row["name"]: row for row in json.loads(out(ctx))["stacks"]}
    assert json.loads(out(ctx))["schema"] == 1
    assert rows["mine"]["owner"] == "user" and rows["hello"]["owner"] == "package"
    assert set(rows["mine"]) == {"name", "enabled", "owner", "state"}


# --- stacks remove -----------------------------------------------------------------------------------------
def make_mine(make_context: MakeContext, instance: Path) -> None:
    run(make_context, instance, "new", "mine")
    (instance / "stacks" / "mine" / ".env").write_text("MINE_PORT=8081\n")


def test_remove_deletes_the_folder_and_the_list_entry_after_a_yes(make_context: MakeContext, instance: Path) -> None:
    make_mine(make_context, instance)
    code, ctx = run(make_context, instance, "remove", "mine", runner=FakeRunner(running(instance, "mine", "stopped")), answer=True)
    assert code == ExitCode.OK, err(ctx)
    assert not (instance / "stacks" / "mine").exists() and enabled(instance) == ["hello"]
    text = out(ctx)
    assert "stacks/mine/.env" in text  # the secrets file is named before it goes
    assert "docker volume ls --filter label=com.docker.compose.project=nexahome-mine" in text  # volumes are never deleted


def test_remove_says_no_when_declined_and_changes_nothing(make_context: MakeContext, instance: Path) -> None:
    make_mine(make_context, instance)
    code, ctx = run(make_context, instance, "remove", "mine", runner=FakeRunner(running(instance, "mine", "stopped")), answer=False)
    assert code == ExitCode.OK and "nothing was removed" in out(ctx)
    assert (instance / "stacks" / "mine").is_dir() and enabled(instance) == ["hello", "mine"]


def test_remove_without_a_terminal_needs_yes(make_context: MakeContext, instance: Path) -> None:
    make_mine(make_context, instance)
    runner = FakeRunner(running(instance, "mine", "stopped"))
    code, ctx = run(make_context, instance, "remove", "mine", runner=runner, answer=None)
    assert code == ExitCode.NOT_READY and err(ctx).endswith("Next: nexahome stacks remove mine --yes\n")
    assert (instance / "stacks" / "mine").is_dir()
    code, ctx = run(make_context, instance, "remove", "mine", "--yes", runner=runner, answer=None)
    assert code == ExitCode.OK and not (instance / "stacks" / "mine").exists()


def test_remove_refuses_a_running_stack(make_context: MakeContext, instance: Path) -> None:
    make_mine(make_context, instance)
    code, ctx = run(make_context, instance, "remove", "mine", "--yes", runner=FakeRunner(running(instance, "mine", "running")))
    assert code == ExitCode.NOT_READY and "is running" in err(ctx)
    assert err(ctx).endswith(f"Next: docker compose -f stacks/mine/compose.yaml down\n")
    assert (instance / "stacks" / "mine").is_dir()


def test_remove_goes_ahead_when_docker_cannot_say_after_the_same_yes(make_context: MakeContext, instance: Path) -> None:
    make_mine(make_context, instance)
    code, ctx = run(make_context, instance, "remove", "mine", runner=FakeRunner(), answer=True)  # docker "not installed": state unknown
    assert code == ExitCode.OK and not (instance / "stacks" / "mine").exists()
    assert "could not tell whether it is running" in out(ctx)


def test_remove_refuses_a_package_stack_and_a_missing_one(make_context: MakeContext, instance: Path) -> None:
    code, ctx = run(make_context, instance, "remove", "hello", "--yes")
    assert code == ExitCode.NOT_READY and "part of NexaHome" in err(ctx) and (instance / "stacks" / "hello").is_dir()
    assert err(ctx).endswith("Next: nexahome config get stacks\n")
    code, ctx = run(make_context, instance, "remove", "ghost", "--yes")
    assert code == ExitCode.NOT_READY and "no such stack: ghost" in err(ctx) and err(ctx).endswith("Next: nexahome stacks\n")


def test_remove_refuses_a_folder_with_a_link_in_it(make_context: MakeContext, instance: Path, tmp_path: Path) -> None:
    make_mine(make_context, instance)
    target = tmp_path / "precious"
    target.mkdir()
    (target / "keep.txt").write_text("keep")
    os.symlink(target, instance / "stacks" / "mine" / "link")
    code, ctx = run(make_context, instance, "remove", "mine", "--yes", runner=FakeRunner(running(instance, "mine", "stopped")))
    assert code == ExitCode.NOT_READY and "link" in err(ctx) and err(ctx).endswith("Next: ls -la stacks/mine\n")
    assert (target / "keep.txt").read_text() == "keep" and (instance / "stacks" / "mine").is_dir()


def test_remove_will_not_leave_the_list_empty(make_context: MakeContext, instance: Path) -> None:
    (instance / "stacks" / "solo").mkdir()
    (instance / "stacks" / "solo" / "compose.yaml").write_text("name: nexahome-solo\n")
    from nexahome.instance import config

    config.write(instance, ["solo"])
    code, ctx = run(make_context, instance, "remove", "solo", "--yes", runner=FakeRunner(running(instance, "solo", "stopped")))
    assert code == ExitCode.NOT_READY and "only stack" in err(ctx) and err(ctx).endswith("Next: nexahome config set stacks hello\n")
    assert (instance / "stacks" / "solo").is_dir() and enabled(instance) == ["solo"]


def test_remove_in_a_clone_points_at_git_or_rm(make_context: MakeContext, tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    (clone / "stacks" / "mine").mkdir(parents=True)
    (clone / "stacks" / "mine" / "compose.yaml").write_text("")
    (clone / "Makefile").write_text("")
    code, ctx = run(make_context, clone, "remove", "mine", "--yes")
    assert code == ExitCode.NOT_READY and "clone" in err(ctx) and err(ctx).endswith("Next: rm -r stacks/mine\n")
    assert (clone / "stacks" / "mine").is_dir()
