from collections.abc import Callable

import pytest

from nexahome.runner import SubprocessRunner

from conftest import FakeDocker


def test_runs_the_program_and_captures_output(fake_docker: Callable[..., FakeDocker]) -> None:
    shim = fake_docker({"info": (0, "27.1.0")})
    result = SubprocessRunner().run(["docker", "info"], timeout=5)
    assert result.ok and result.stdout.strip() == "27.1.0"
    assert shim.calls == ["info"]


def test_a_failing_program_is_a_result_not_an_exception(fake_docker: Callable[..., FakeDocker]) -> None:
    fake_docker({"info": (1, "")})
    result = SubprocessRunner().run(["docker", "info"], timeout=5)
    assert not result.ok and result.returncode == 1 and not result.missing


@pytest.mark.usefixtures("no_docker")
def test_a_missing_program_is_reported_as_missing() -> None:
    result = SubprocessRunner().run(["docker", "info"], timeout=5)
    assert result.missing and not result.ok and result.returncode == 127


def test_a_hanging_program_times_out(fake_docker: Callable[..., FakeDocker]) -> None:
    fake_docker({"info": (0, "")}, hang="info")
    result = SubprocessRunner().run(["docker", "info"], timeout=0.5)
    assert result.timed_out and not result.ok


def test_stream_writes_to_the_terminal_itself_and_returns_the_exit_code(capfd: pytest.CaptureFixture[str]) -> None:
    import sys

    code = SubprocessRunner().stream([sys.executable, "-c", "print('live'); raise SystemExit(3)"])
    assert code == 3 and capfd.readouterr().out == "live\n"  # inherited, not captured by the runner


@pytest.mark.usefixtures("no_docker")
def test_stream_of_a_missing_program_is_127() -> None:
    assert SubprocessRunner().stream(["docker", "compose", "logs"]) == 127
