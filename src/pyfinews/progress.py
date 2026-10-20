
"""Small dependency-free progress updates for sequential network operations."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def run_with_progress(
    items: Sequence[T],
    operation: Callable[[T], R],
    *,
    label: str,
    enabled: bool = True,
) -> list[R]:
    """Run an operation per item and report progress to stderr.

    Progress is rendered in-place on interactive terminals. When stderr is
    redirected, completed items are reported as separate lines.

    Exceptions from ``operation`` are reported and then re-raised.
    Results preserve the input order.
    """
    total = len(items)
    results: list[R] = []
    started = time.monotonic()

    if total == 0:
        if enabled:
            print(f"{label}: no items", file=sys.stderr, flush=True)

        return results

    interactive = enabled and sys.stderr.isatty()
    previous_width = 0

    def report(message: str, *, final: bool = False) -> None:
        nonlocal previous_width

        if not enabled:
            return

        if interactive:
            # Pad shorter updates to overwrite remnants of the previous line.
            padding = " " * max(0, previous_width - len(message))
            sys.stderr.write("\r" + message + padding)

            if final:
                sys.stderr.write("\n")

            sys.stderr.flush()
            previous_width = 0 if final else max(previous_width, len(message))
        else:
            # Avoid carriage-return progress artifacts in logs and CI output.
            print(message, file=sys.stderr, flush=True)

    for index, item in enumerate(items, start=1):
        if interactive:
            elapsed = time.monotonic() - started
            report(
                f"{label}: {index}/{total} in progress "
                f"({elapsed:.1f}s elapsed)"
            )

        try:
            result = operation(item)
        except Exception as exc:
            elapsed = time.monotonic() - started
            report(
                f"{label}: {index}/{total} failed "
                f"({elapsed:.1f}s elapsed; "
                f"{type(exc).__name__}: {exc})",
                final=True,
            )

            raise

        results.append(result)

        elapsed = time.monotonic() - started
        report(
            f"{label}: {index}/{total} complete "
            f"({elapsed:.1f}s elapsed)",
            final=(index == total),
        )

    return results


__all__ = ["run_with_progress"]
