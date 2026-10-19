"""Small dependency-free progress updates for sequential network operations."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable


def run_with_progress(
    items, 
    operation: Callable, 
    *, 
    label: str, 
    enabled: bool = True
):
    """Run an operation per item, reporting item-level progress to stderr."""
    total = len(items)
    results = []
    started = time.monotonic()

    for index, item in enumerate(items, start=1):
        if enabled:
            elapsed = time.monotonic() - started
            print(f"\r{label}: {index}/{total} in progress ({elapsed:.1f}s elapsed)",
                  end="", file=sys.stderr, flush=True)

        result = operation(item)
        results.append(result)

        if enabled:
            elapsed = time.monotonic() - started
            print(f"\r{label}: {index}/{total} complete ({elapsed:.1f}s elapsed)",
                  end="\n" if index == total else "", file=sys.stderr, flush=True)

    if enabled and total == 0:
        print(f"{label}: no items", file=sys.stderr, flush=True)

    return results


__all__ = ["run_with_progress"]
