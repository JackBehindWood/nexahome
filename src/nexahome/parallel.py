"""Run independent, slow calls (docker subprocesses) side by side, returning results in input order."""

from collections.abc import Callable, Iterable

from nexahome.defaults import MAX_WORKERS


def map_ordered[T, R](function: Callable[[T], R], items: Iterable[T], *, limit: int = MAX_WORKERS) -> list[R]:
    """function over items, in threads when there is more than one item. The thread pool is only imported then."""
    work = list(items)
    if len(work) <= 1:
        return [function(item) for item in work]
    from concurrent.futures import ThreadPoolExecutor  # imported here: most runs never need it

    with ThreadPoolExecutor(max_workers=min(limit, len(work))) as pool:
        return list(pool.map(function, work))
