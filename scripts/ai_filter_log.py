#!/usr/bin/env python3
"""Print a concise tail of a failed command log."""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

EXPECTED_ARG_COUNT = 2
TAIL_LINE_COUNT = 120
FAILURE_LINE_COUNT = 40
FAILURE_MARKERS = ("error", "failed", "failure", "traceback")


def is_failure_line(line: str) -> bool:
    """Return whether a log line is useful in a failure summary."""
    lowered = line.lower()
    return any(marker in lowered for marker in FAILURE_MARKERS)


def main() -> int:
    """Print the final log lines for quick agent feedback."""
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        print("usage: ai_filter_log.py LOG", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"log file not found: {path}", file=sys.stderr)
        return 1

    tail: deque[tuple[int, str]] = deque(maxlen=TAIL_LINE_COUNT)
    failures: deque[tuple[int, str]] = deque(maxlen=FAILURE_LINE_COUNT)
    total_lines = 0
    with path.open(encoding="utf-8", errors="replace") as log_file:
        for total_lines, raw_line in enumerate(log_file, start=1):
            line = raw_line.rstrip("\r\n")
            tail.append((total_lines, line))
            if is_failure_line(line):
                failures.append((total_lines, line))

    tail_start = total_lines - len(tail) + 1
    earlier_failures = [
        (line_number, line) for line_number, line in failures if line_number < tail_start
    ]
    if earlier_failures:
        print("Earlier failure lines:")
        for line_number, line in earlier_failures:
            print(f"{line_number}: {line}")
        print("Log tail:")

    for _, line in tail:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
