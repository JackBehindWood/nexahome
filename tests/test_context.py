from pathlib import Path

import pytest

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
