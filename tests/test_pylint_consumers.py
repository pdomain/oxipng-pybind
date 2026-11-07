"""Consumer lint compatibility tests."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import oxipng

# Standard Ebooks injects this release into the toolset environment.
# It resolves to Astroid 4.0.4, the same line as the original workaround.
_EXTERNAL_PYLINT_VERSIONS = ("4.0.6",)

_ASTROID_RECURSION_MARKERS = (
    "Astroid was unable to transform",
    "system recursion limit is lifted",
)

# Confirms the isolated environment loaded the requested Pylint before linting.
# A leaked project environment would otherwise report a clean run of the wrong release.
_ISOLATED_RUNNER = """\
import importlib.metadata as metadata
import subprocess
import sys

expected = sys.argv[1]
consumer = sys.argv[2]
actual = metadata.version("pylint")
if actual != expected:
    print(f"expected pylint {expected}, found {actual}", file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(subprocess.call([sys.executable, "-m", "pylint", "--exit-zero", consumer]))
"""

_CONSUMER_SOURCE = """\
from oxipng import (
    BitDepth,
    ColorType,
    Deflater,
    Deflaters,
    FilterStrategy,
    Interlacing,
    OptimizationResult,
    PngError,
    RawImage,
    RowFilter,
    StripChunks,
    analyze,
    optimize,
    optimize_from_memory,
)


def run(path: str, data: bytes) -> bytes:
    interlace = Interlacing.keep
    deprecated_interlace = (Interlacing.Off, Interlacing.Adam7)
    strip = StripChunks.keep(["tEXt"])
    stripped = StripChunks.strip(["iTXt"])
    strip_factory = StripChunks.safe()
    deflater = Deflaters.libdeflater(12)
    zopfli = Deflaters.zopfli(15)
    deflater_member = Deflater.libdeflater
    filters = FilterStrategy.predefined(["none", "sub"])
    row_filters = (
        RowFilter.none,
        RowFilter.sub,
        RowFilter.up,
        RowFilter.average,
        RowFilter.paeth,
        RowFilter.minsum,
        RowFilter.entropy,
        RowFilter.bigrams,
        RowFilter.bigent,
        RowFilter.brute,
        RowFilter.NoOp,
        RowFilter.Sub,
        RowFilter.Up,
        RowFilter.Average,
        RowFilter.Paeth,
        RowFilter.MinSum,
        RowFilter.Entropy,
        RowFilter.Bigrams,
        RowFilter.BigEnt,
        RowFilter.Brute,
    )
    color_types = (
        ColorType.rgb((255, 0, 0)),
        ColorType.rgba(),
        ColorType.indexed([(255, 0, 0)]),
        ColorType.grayscale(None),
        ColorType.grayscale_alpha(),
    )
    raw = RawImage(1, 1, ColorType.rgba, BitDepth.eight, bytes([255, 0, 0, 255]))
    raw.add_png_chunk(b"tEXt", b"Comment\\x00hello")
    raw.add_icc_profile(b"profile")
    raw_png = raw.create_optimized_png(filter=(FilterStrategy.none, "sub"))
    result = analyze(path, interlace=interlace, strip=strip, deflate=deflater, filter=filters)
    assert isinstance(result, OptimizationResult)
    try:
        optimize(path, level=2, strip=stripped, deflate=zopfli, filter=[FilterStrategy.none])
    except PngError:
        pass
    _ = (
        deprecated_interlace,
        strip_factory,
        deflater_member,
        row_filters,
        color_types,
        raw_png,
    )
    return optimize_from_memory(data, filter=(FilterStrategy.none, "sub"))
"""

PUBLIC_API_NAMES = {
    "BitDepth",
    "ColorType",
    "Deflater",
    "Deflaters",
    "FilterStrategy",
    "Interlacing",
    "OptimizationResult",
    "PngError",
    "RawImage",
    "RowFilter",
    "StripChunks",
    "analyze",
    "optimize",
    "optimize_from_memory",
}


def _write_consumer(tmp_path: Path) -> Path:
    consumer = tmp_path / "consumer.py"
    consumer.write_text(_CONSUMER_SOURCE, encoding="utf-8")
    return consumer


def _assert_no_astroid_recursion(
    result: subprocess.CompletedProcess[str],
    version: str,
) -> None:
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"pylint {version} exited {result.returncode}\n{output}"
    for marker in _ASTROID_RECURSION_MARKERS:
        assert marker not in output, f"pylint {version} reported {marker!r}\n{output}"


def _native_extension_dir() -> Path:
    spec = importlib.util.find_spec("_oxipng")
    if spec is None:
        message = "_oxipng extension is not installed"
        raise RuntimeError(message)
    locations = spec.submodule_search_locations
    if locations:
        return Path(next(iter(locations)))
    if spec.origin is None:
        message = "_oxipng extension origin is missing"
        raise RuntimeError(message)
    return Path(spec.origin).parent


def _run_project_pylint(consumer: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed command exercises consumer Pylint.
        [sys.executable, "-m", "pylint", "--exit-zero", str(consumer)],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_isolated_pylint(
    consumer: Path,
    version: str,
    work: Path,
) -> subprocess.CompletedProcess[str]:
    """Run one Pylint release without replacing the locked test environment."""
    native_root = work / "native"
    native_root.mkdir()
    (native_root / "_oxipng").symlink_to(_native_extension_dir(), target_is_directory=True)
    runner = work / "run_pylint.py"
    runner.write_text(_ISOLATED_RUNNER, encoding="utf-8")
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    # The project site-packages contains the locked Pylint. Keep it off the path
    # so this release cannot be shadowed, while the extension stays importable.
    env["PYTHONPATH"] = os.pathsep.join((str(repo), str(native_root)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    uv = shutil.which("uv")
    if uv is None:
        message = "uv is required to run an isolated Pylint release"
        raise RuntimeError(message)
    return subprocess.run(  # noqa: S603 - fixed command exercises one Pylint release.
        [
            uv,
            "run",
            "--isolated",
            "--python",
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "--with",
            f"pylint=={version}",
            "python",
            str(runner),
            version,
            str(consumer),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        timeout=120,
    )


def test_pylint_consumer_public_facade_has_no_astroid_transform_warnings(
    tmp_path: Path,
) -> None:
    """The locked Pylint can inspect the public facade without Astroid recursion warnings."""
    assert set(oxipng.__all__) == PUBLIC_API_NAMES

    result = _run_project_pylint(_write_consumer(tmp_path))
    _assert_no_astroid_recursion(result, "locked")


@pytest.mark.parametrize("pylint_version", _EXTERNAL_PYLINT_VERSIONS)
def test_external_pylint_consumer_public_facade_has_no_astroid_transform_warnings(
    tmp_path: Path,
    pylint_version: str,
) -> None:
    """Pinned external Pylint releases can inspect the public facade."""
    result = _run_isolated_pylint(_write_consumer(tmp_path), pylint_version, tmp_path)
    _assert_no_astroid_recursion(result, pylint_version)
