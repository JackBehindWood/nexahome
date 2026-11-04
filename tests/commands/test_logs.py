"""`nexahome logs`: the host's `docker compose logs` for the stacks it runs, through cli.main."""

from pathlib import Path

import pytest

from nexahome import cli
from nexahome.errors import ExitCode
from nexahome.runner import RunResult

from conftest import DOCKER_HEALTHY, FakeRunner, MakeCheckout, MakeContext, MakeHost, err, out


def logs_argv(checkout: Path, name: str, *extra: str, tail: str = "100") -> tuple[str, ...]:
    return ("docker", "compose", "-f", str(checkout / "stacks" / name / "compose.yaml"), "logs", "--tail", tail, *extra)


def test_one_stack_prints_the_last_hundred_lines_by_default(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"edge": None, "hello": None})
    runner = FakeRunner({**DOCKER_HEALTHY, logs_argv(checkout, "hello"): RunResult(0, "hello-1  | ready\n")})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["logs", "hello"], ctx) == ExitCode.OK
    assert out(ctx) == "hello-1  | ready\n"
    assert logs_argv(checkout, "hello") in runner.calls and logs_argv(checkout, "edge") not in runner.calls


def test_tail_is_passed_on(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"hello": None})
    runner = FakeRunner({**DOCKER_HEALTHY, logs_argv(checkout, "hello", tail="5"): RunResult(0, "x\n")})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["logs", "hello", "--tail", "5"], ctx) == ExitCode.OK and out(ctx) == "x\n"


def test_without_a_stack_every_enabled_service_stack_in_turn_with_a_header(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"actual": None, "backup": None, "edge": None})  # the one-shot backup tool is not a service
    runner = FakeRunner({**DOCKER_HEALTHY, logs_argv(checkout, "edge"): RunResult(0, "e\n"), logs_argv(checkout, "actual"): RunResult(0, "a\n")})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["logs"], ctx) == ExitCode.OK
    assert out(ctx) == "==> edge <==\ne\n\n==> actual <==\na\n"  # core stacks first, as everywhere else
    assert logs_argv(checkout, "backup") not in runner.calls


def test_a_stack_that_is_not_enabled_here_is_refused_with_the_list(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"backup": None, "hello": None})
    runner = FakeRunner(DOCKER_HEALTHY)
    for name in ("backup", "nosuch"):
        ctx = make_context(cwd=checkout, runner=runner)
        assert cli.main(["logs", name], ctx) == ExitCode.NOT_READY
        assert f"{name} is not a stack this host runs" in err(ctx) and err(ctx).endswith("Next: nexahome stacks\n")
    assert not any("logs" in call for call in runner.calls)


def test_no_engine_says_how_to_start_it(make_checkout: MakeCheckout, make_context: MakeContext, make_host: MakeHost) -> None:
    ctx = make_context(host=make_host(system="macos"), cwd=make_checkout({"hello": None}), runner=FakeRunner())
    assert cli.main(["logs", "hello"], ctx) == ExitCode.NOT_READY
    assert "no container runtime running" in err(ctx) and err(ctx).endswith("Next: colima start --cpu 2 --memory 2 --disk 20\n")


def test_follow_streams_one_stack_to_the_terminal(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"hello": None})
    argv = logs_argv(checkout, "hello", "--follow")
    runner = FakeRunner(DOCKER_HEALTHY, streams={argv: 0})
    ctx = make_context(cwd=checkout, runner=runner)
    assert cli.main(["logs", "hello", "--follow"], ctx) == ExitCode.OK
    assert runner.streamed == [argv] and not any(call[-1] == "--follow" for call in runner.calls)  # not captured, not timed out


def test_follow_needs_one_stack_and_names_the_command(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    ctx = make_context(cwd=make_checkout({"edge": None, "hello": None}), runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["logs", "--follow"], ctx) == ExitCode.USAGE
    assert "--follow follows one stack at a time" in err(ctx) and err(ctx).endswith("Next: nexahome logs edge --follow\n")


def test_a_follow_that_fails_ends_in_doctor(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"hello": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner(DOCKER_HEALTHY, streams={logs_argv(checkout, "hello", "--follow"): 1}))
    assert cli.main(["logs", "hello", "--follow"], ctx) == ExitCode.NOT_READY
    assert err(ctx).endswith("Next: nexahome doctor\n")


@pytest.mark.parametrize("tail", ["0", "-3", "many"])
def test_a_bad_tail_is_a_usage_error_with_the_fix(make_checkout: MakeCheckout, make_context: MakeContext, tail: str) -> None:
    ctx = make_context(cwd=make_checkout({"hello": None}), runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["logs", "hello", "--tail", tail], ctx) == ExitCode.USAGE


def test_compose_failing_shows_its_last_line_and_ends_in_doctor(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"hello": None})
    failed = RunResult(1, stderr="warning\nrequired variable HELLO_KEY is missing a value\n")
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, logs_argv(checkout, "hello"): failed}))
    assert cli.main(["logs", "hello"], ctx) == ExitCode.NOT_READY
    assert "could not read the logs of hello: required variable HELLO_KEY is missing a value" in err(ctx)
    assert err(ctx).endswith("Next: nexahome doctor\n")


def test_a_stack_with_no_log_lines_says_so_and_how_to_check(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    checkout = make_checkout({"hello": None})
    ctx = make_context(cwd=checkout, runner=FakeRunner({**DOCKER_HEALTHY, logs_argv(checkout, "hello"): RunResult(0, "")}))
    assert cli.main(["logs", "hello"], ctx) == ExitCode.OK
    assert out(ctx) == "" and "hello: no log lines; is it running? Check with: nexahome stacks" in err(ctx)


def test_no_stacks_at_all_points_at_the_list(make_checkout: MakeCheckout, make_context: MakeContext) -> None:
    ctx = make_context(cwd=make_checkout({}), runner=FakeRunner(DOCKER_HEALTHY))
    assert cli.main(["logs"], ctx) == ExitCode.NOT_READY and err(ctx).endswith("Next: nexahome stacks\n")
