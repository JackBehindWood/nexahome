from pathlib import Path

from nexahome import stacks

from conftest import MakeCheckout


def test_all_stacks_skips_the_template_and_directories_without_compose(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"_template": None, "actual": None, "backup": None, "edge": None})
    (checkout / "stacks" / "notes").mkdir()
    assert stacks.all_stacks(checkout) == ["actual", "backup", "edge"]


def test_default_enabled_drops_the_backup_tool_and_puts_core_first(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"_template": None, "actual": None, "backup": None, "edge": None, "identity": None, "zeta": None})
    assert stacks.enabled(checkout) == ["edge", "identity", "actual", "zeta"]


def test_the_host_list_overrides_the_default(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"actual": None, "edge": None, "hello": None})
    (checkout / ".config").mkdir()
    (checkout / ".config" / "stacks").write_text("hello\nedge\n")
    assert stacks.enabled(checkout) == ["edge", "hello"]
    (checkout / ".config" / "stacks").write_text("\n  \n")  # blank means: use the default
    assert stacks.enabled(checkout) == ["edge", "actual", "hello"]


def test_compose_file(make_checkout: MakeCheckout) -> None:
    checkout = make_checkout({"demo": None})
    assert stacks.compose_file(checkout, "demo") == Path(checkout) / "stacks" / "demo" / "compose.yaml"
