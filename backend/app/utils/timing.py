import time


class Stopwatch:
    """`with Stopwatch() as sw: ...` then read `sw.elapsed_ms` afterward.

    Used to populate the scan tables' `duration_ms` column for real,
    measured durations — never fabricated for historical rows.
    """

    def __enter__(self) -> "Stopwatch":
        self._start = time.perf_counter()
        self.elapsed_ms: int | None = None
        return self

    def __exit__(self, *exc_info) -> None:
        self.elapsed_ms = int((time.perf_counter() - self._start) * 1000)
