"""Run slow calls (docker subprocesses) side by side, returning results in input order."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from typing import TYPE_CHECKING

from nexahome.defaults import MAX_WORKERS

if TYPE_CHECKING:
    from concurrent.futures import Future


def map_ordered[T, R](function: Callable[[T], R], items: Iterable[T], *, limit: int = MAX_WORKERS) -> list[R]:
    """function over items, in threads when there is more than one item. The thread pool is only imported then."""
    work = list(items)
    if len(work) <= 1:
        return [function(item) for item in work]
    from concurrent.futures import ThreadPoolExecutor  # imported here: most runs never need it

    with ThreadPoolExecutor(max_workers=min(limit, len(work))) as pool:
        return list(pool.map(function, work))


class Earlier[R](Mapping[str, R]):
    """The results of the other tasks of `run_waiting`, by name. Reading one waits until that task has finished;
    a task that returned None did not apply and is missing (KeyError)."""

    def __init__(self, futures: dict[str, Future[R | None]]) -> None:
        self._futures = futures

    def __getitem__(self, name: str) -> R:
        result = self._futures[name].result()
        if result is None:
            raise KeyError(name)
        return result

    def __iter__(self) -> Iterator[str]:
        return iter(self._futures)

    def __len__(self) -> int:
        return len(self._futures)


def run_waiting[R](tasks: Sequence[tuple[str, Callable[[Mapping[str, R]], R | None]]]) -> list[R]:
    """Run named tasks side by side; a task may read the results of the tasks listed before it by name and then waits for them.
    Returns the results in input order, leaving out the tasks that returned None. A waiting task holds its thread,
    so every task gets its own (no cap): with fewer threads than tasks, waiters could starve the tasks they wait for."""
    from concurrent.futures import ThreadPoolExecutor

    futures: dict[str, Future[R | None]] = {}
    earlier = Earlier(futures)
    with ThreadPoolExecutor(max_workers=max(len(tasks), 1)) as pool:
        for name, task in tasks:
            futures[name] = pool.submit(task, earlier)
    results = (futures[name].result() for name, _ in tasks)
    return [result for result in results if result is not None]
