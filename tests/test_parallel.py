"""nexahome.parallel.run_waiting: tasks run side by side, may wait for each other, and keep their order."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from nexahome.parallel import Earlier, run_waiting


def test_a_task_waits_for_the_slower_one_listed_before_it() -> None:
    import time

    def slow(earlier: Mapping[str, str]) -> str:
        time.sleep(0.05)
        return "first"

    def second(earlier: Mapping[str, str]) -> str:
        return earlier["first"] + "+second"

    assert run_waiting([("first", slow), ("second", second)]) == ["first", "first+second"]


def test_results_keep_input_order_and_none_is_left_out() -> None:
    tasks = [("a", lambda earlier: "A"), ("b", lambda earlier: None), ("c", lambda earlier: "C")]
    assert run_waiting(tasks) == ["A", "C"]


def test_a_task_that_did_not_apply_is_hidden_from_the_others() -> None:
    def reads(earlier: Mapping[str, str]) -> str:
        try:
            return earlier["b"]
        except KeyError:
            return "missing"

    assert run_waiting([("b", lambda earlier: None), ("a", reads)]) == ["missing"]


def test_earlier_raises_key_error_for_a_task_that_did_not_apply() -> None:
    from concurrent.futures import Future

    skipped: Future[str | None] = Future()
    skipped.set_result(None)
    done: Future[str | None] = Future()
    done.set_result("x")
    earlier = Earlier({"done": done, "skipped": skipped})
    assert earlier["done"] == "x" and list(earlier) == ["done", "skipped"] and len(earlier) == 2
    with pytest.raises(KeyError):
        earlier["skipped"]


def test_no_tasks_is_an_empty_result() -> None:
    assert run_waiting([]) == []


def test_more_waiters_than_the_worker_limit_do_not_deadlock() -> None:
    from nexahome.defaults import MAX_WORKERS

    def waiter(earlier: Mapping[str, int]) -> int:
        return earlier["root"] + 1

    tasks = [("root", lambda earlier: 1)] + [(f"w{n}", waiter) for n in range(MAX_WORKERS * 2)]
    assert run_waiting(tasks) == [1] + [2] * (MAX_WORKERS * 2)
