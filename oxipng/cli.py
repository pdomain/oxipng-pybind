"""Command-line entry point for optimizing PNG files.

Flags follow a subset of the upstream `oxipng` CLI so existing commands keep
working.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

import oxipng

if TYPE_CHECKING:
    from collections.abc import Sequence

MAX_LEVEL = 6
INTERLACE_VALUES = {"0": oxipng.Interlacing.off, "1": oxipng.Interlacing.on, "keep": None}


def _level(value: str) -> int:
    if value == "max":
        return MAX_LEVEL
    if value.isdigit() and int(value) <= MAX_LEVEL:
        return int(value)
    msg = f"expected 0-{MAX_LEVEL} or max, got {value!r}"
    raise argparse.ArgumentTypeError(msg)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the `oxipng` command."""
    parser = argparse.ArgumentParser(prog="oxipng", description="Optimize PNG files in place.")
    parser.add_argument("files", nargs="+", metavar="FILE", help="PNG files to optimize")
    parser.add_argument(
        "-o", "--opt", type=_level, default=2, metavar="LEVEL", help="0-6 or max (default: 2)"
    )
    parser.add_argument("--out", metavar="FILE", help="write output here instead of in place")
    parser.add_argument(
        "-s", dest="strip", action="store_const", const="safe", help="same as --strip safe"
    )
    parser.add_argument("--strip", choices=["safe", "all"], help="strip metadata chunks")
    parser.add_argument(
        "-i",
        "--interlace",
        choices=list(INTERLACE_VALUES),
        default="keep",
        help="0 = off, 1 = on, keep = unchanged (default: keep)",
    )
    parser.add_argument("-a", "--alpha", action="store_true", help="optimize transparent pixels")
    parser.add_argument("-Z", "--zopfli", action="store_true", help="use slower Zopfli compression")
    parser.add_argument("-p", "--preserve", action="store_true", help="keep file attributes")
    parser.add_argument("--fast", action="store_true", help="use fast filter evaluation")
    parser.add_argument("--fix", action="store_true", help="try to fix PNG decode errors")
    parser.add_argument("--force", action="store_true", help="write output even if larger")
    parser.add_argument("--timeout", type=float, metavar="SECONDS", help="per-file time limit")
    return parser


def _optimize(path: str, args: argparse.Namespace) -> bool:
    try:
        oxipng.optimize(
            path,
            args.out,
            level=args.opt,
            interlace=INTERLACE_VALUES[args.interlace],
            strip=args.strip,
            deflate=oxipng.Deflater.zopfli if args.zopfli else None,
            fix_errors=args.fix,
            force=args.force,
            preserve_attrs=args.preserve,
            optimize_alpha=args.alpha or None,
            fast_evaluation=args.fast or None,
            timeout=args.timeout,
        )
    except (OSError, ValueError, oxipng.PngError) as exc:
        sys.stderr.write(f"oxipng: {path}: {exc}\n")
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Optimize each file and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.out is not None and len(args.files) > 1:
        parser.error("--out needs exactly one input file")

    results = [_optimize(path, args) for path in args.files]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
