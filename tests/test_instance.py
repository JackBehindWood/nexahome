"""Where an instance is: the resolution order shared by every command (PK6-6), including a folder made by init."""

from pathlib import Path

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.instance import home

from conftest import FakeRunner, MakeCheckout, MakeContext


def make_instance(root: Path, stacks: tuple[str, ...] = ("demo",)) -> Path:
    """What `nexahome init` leaves: nexahome.toml and stacks/, no Makefile."""
    (root / "stacks").mkdir(parents=True)
    (root / "nexahome.toml").write_text("schema = 1\n")
    for name in stacks:
        (root / "stacks" / name).mkdir()
        (root / "stacks" / name / "compose.yaml").write_text("")
    return root


def test_what_counts_as_an_instance(make_checkout: MakeCheckout, tmp_path: Path) -> None:
    assert home.is_instance(make_checkout(root=tmp_path / "clone"))  # stacks/ and a Makefile
    assert home.is_instance(make_instance(tmp_path / "made"))  # nexahome.toml
    (tmp_path / "bare" / "stacks").mkdir(parents=True)
    assert not home.is_instance(tmp_path / "bare")  # stacks/ alone is not enough


def test_an_instance_is_found_from_inside_it(tmp_path: Path) -> None:
    root = make_instance(tmp_path / "made")
    assert home.find(root / "stacks" / "demo", None, tmp_path / "nowhere") == root
    assert home.find(tmp_path, None, tmp_path / "nowhere") is None  # a parent of the instance is not one


def test_an_explicit_home_is_not_searched_upwards(tmp_path: Path) -> None:
    root = make_instance(tmp_path / "made")
    assert home.find(tmp_path, str(root), tmp_path) == root
    assert home.find(root, str(root / "stacks"), tmp_path) is None
    assert home.find(tmp_path, "made", tmp_path) == root  # relative to the working directory


def test_the_default_folder_counts_only_when_it_holds_nexahome_toml(tmp_path: Path) -> None:
    user_home, elsewhere = tmp_path / "user", tmp_path / "elsewhere"
    (user_home / "nexahome").mkdir(parents=True)
    elsewhere.mkdir()
    assert home.find(elsewhere, None, user_home) is None  # an empty ~/nexahome is not an instance
    make_instance(user_home / "nexahome")
    assert home.find(elsewhere, None, user_home) == user_home / "nexahome"
    assert home.find(elsewhere, str(elsewhere), user_home) is None  # an explicit setting is never replaced by the default


def test_every_command_finds_an_instance_without_a_makefile(make_context: MakeContext, tmp_path: Path) -> None:
    root = make_instance(tmp_path / "made")
    ctx = make_context(cwd=root / "stacks", runner=FakeRunner())
    assert ctx.checkout() == root
    assert cli.main(["stacks"], ctx) == ExitCode.OK and "demo" in ctx.out.getvalue()  # type: ignore[attr-defined]


def test_the_home_option_is_the_same_setting_as_the_variable(make_context: MakeContext, tmp_path: Path) -> None:
    root = make_instance(tmp_path / "made")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    ctx = make_context(cwd=elsewhere, runner=FakeRunner())
    assert cli.main(["--home", str(root), "stacks"], ctx) == ExitCode.OK and "demo" in ctx.out.getvalue()  # type: ignore[attr-defined]
    assert cli.main(["--home", str(elsewhere), "stacks"], make_context(cwd=root)) == ExitCode.NOT_READY
