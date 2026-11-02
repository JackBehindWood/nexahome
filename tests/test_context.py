import io
from pathlib import Path

import pytest

from nexahome import context
from nexahome.context import Context
from nexahome.errors import NexaHomeError

from conftest import MakeCheckout, MakeContext


def test_checkout_is_found_from_a_subdirectory(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout()
    deep = checkout / "stacks" / "demo"
    assert make_context(cwd=deep).checkout() == checkout
    assert make_context(cwd=checkout.parent).checkout() is None  # a parent of the checkout is not one


def test_an_explicit_home_is_not_searched_upwards(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout()
    inside = checkout / "stacks" / "demo"
    assert make_context(cwd=checkout.parent, env={"NEXAHOME_HOME": str(checkout)}).checkout() == checkout
    assert make_context(cwd=checkout, env={"NEXAHOME_HOME": str(inside)}).checkout() is None
    assert make_context(cwd=checkout, env={"NEXAHOME_HOME": "stacks"}).checkout() is None  # relative to cwd, not a checkout


def test_require_checkout_names_the_way_out(make_context: MakeContext, tmp_path: Path) -> None:
    with pytest.raises(NexaHomeError) as raised:
        make_context(cwd=tmp_path / "x").require_checkout()
    assert raised.value.fix == "cd /path/to/nexahome"


def test_display_is_relative_inside_the_working_directory_and_quoted(make_context: MakeContext, tmp_path: Path) -> None:
    ctx = make_context(cwd=tmp_path)
    assert ctx.display(tmp_path / "stacks" / "a b" / ".env") == "'stacks/a b/.env'"
    assert ctx.display(Path("/elsewhere/.env")) == "/elsewhere/.env"


def test_the_default_context_describes_the_real_process() -> None:
    ctx = Context.default()
    assert ctx.cwd == Path.cwd() and ctx.host.python[0] == 3 and ctx.now() > 0 and ctx.disk_free(ctx.cwd) > 0


def test_asking_without_a_terminal_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))  # a StringIO is not a terminal
    assert context.ask_on_terminal("ok? ") is None


@pytest.mark.parametrize(("typed", "answer"), [("y", True), ("YES", True), (" yes ", True), ("n", False), ("", False), ("maybe", False)])
def test_asking_on_a_terminal(monkeypatch: pytest.MonkeyPatch, typed: str, answer: bool) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr("sys.stdin", Terminal())
    monkeypatch.setattr("builtins.input", lambda prompt: typed)
    assert context.ask_on_terminal("ok? ") is answer


def test_end_of_input_counts_as_no(monkeypatch: pytest.MonkeyPatch) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    def closed(prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("sys.stdin", Terminal())
    monkeypatch.setattr("builtins.input", closed)
    assert context.ask_on_terminal("ok? ") is False
