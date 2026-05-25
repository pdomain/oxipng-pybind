#!/usr/bin/env python3
"""Print a concise tail of a failed command log."""

from __future__ import annotations

import sys
from pathlib import Path

EXPECTED_ARG_COUNT = 2


def main() -> int:
    """Print the final log lines for quick agent feedback."""
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        print("usage: ai_filter_log.py LOG", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"log file not found: {path}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-120:]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
