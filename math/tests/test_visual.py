r"""Pixel comparison against committed reference pages.

The output of this project is a visual artifact, so the other gates miss the
failures that matter most. Several real bugs during development were invisible
to every non-visual check: sub-question labels sitting above their baseline, a
measure narrow enough to orphan single words like "box." onto their own line,
and a layout change that silently pushed the worksheet onto a fifth page. Only
the page count was gated; the rest were caught by looking.

The references are rasterised in greyscale, which is also how the worksheet is
printed, so a reference image doubles as a record of what comes out of a mono
laser.

This needs Chrome and ImageMagick and is sensitive to the host's fonts, so it
skips when they are missing rather than failing. The references were generated
on macOS.

Regenerate deliberately, after checking the change is wanted:

    UPDATE_REFERENCE=1 uv run pytest tests/test_visual.py
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from worksheet.render import ChromeNotFoundError, find_chrome, render_pdf
from worksheet.spec import EXPECTED_PAGES

SOURCE = Path(__file__).resolve().parent.parent / "chapter-1" / "hyrule-math-review.html"
REFERENCE = Path(__file__).resolve().parent.parent / "chapter-1" / "reference"
UPDATING = os.environ.get("UPDATE_REFERENCE") == "1"

# Chrome's antialiasing varies slightly between runs of identical input, so an
# exact match is too strict. Measured run-to-run noise is well under 0.1%.
PIXEL_BUDGET = 0.002

RASTER_DPI = "100"


def tools_available() -> bool:
    if shutil.which("magick") is None:
        return False
    try:
        find_chrome()
    except ChromeNotFoundError:
        return False
    return True


# The references carry macOS font metrics, so the comparison is only meaningful
# on macOS. Skipping on that basis, rather than on a missing tool, keeps a CI
# image that happens to ship ImageMagick from failing on font rendering.
on_reference_platform = pytest.mark.skipif(
    sys.platform != "darwin", reason="references carry macOS font metrics"
)
needs_tools = pytest.mark.skipif(
    not tools_available(), reason="needs Chrome and ImageMagick"
)


def rasterise(pdf: Path, into: Path) -> list[Path]:
    """Render each PDF page to a greyscale PNG, as it would be printed."""
    subprocess.run(
        [
            "magick",
            "-density", RASTER_DPI,
            str(pdf),
            "-background", "white",
            "-alpha", "remove",
            "-alpha", "off",
            "-colorspace", "Gray",
            str(into / "page.png"),
        ],
        check=True,
        capture_output=True,
    )  # fmt: skip
    return sorted(into.glob("page-*.png"))


def differing_fraction(expected: Path, actual: Path) -> float:
    """Fraction of pixels that differ, via ImageMagick's absolute-error metric."""
    result = subprocess.run(
        ["magick", "compare", "-metric", "AE", str(expected), str(actual), "null:"],
        capture_output=True,
        text=True,
        check=False,  # compare exits non-zero whenever the images differ at all
    )
    # `compare` reports "<count> (<fraction>)" on stderr, so the return code is
    # not an error signal here.
    match = re.search(r"\(([\d.e-]+)\)", result.stderr)
    if match is None:
        raise AssertionError(f"could not read compare output: {result.stderr!r}")
    return float(match.group(1))


@on_reference_platform
@needs_tools
def test_pages_match_reference(tmp_path):
    """Catches what the other gates cannot: how the page actually looks."""
    pdf = render_pdf(SOURCE, tmp_path / "worksheet.pdf")
    pages = rasterise(pdf, tmp_path)
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} pages, rendered {len(pages)}"
    )

    if UPDATING:
        REFERENCE.mkdir(exist_ok=True)
        for page in pages:
            shutil.copy(page, REFERENCE / page.name)
        pytest.skip("reference updated")

    for page in pages:
        expected = REFERENCE / page.name
        assert expected.exists(), f"no reference for {page.name}"
        drift = differing_fraction(expected, page)
        assert drift <= PIXEL_BUDGET, (
            f"{page.name} differs from the reference by {drift:.4%} of pixels "
            f"(budget {PIXEL_BUDGET:.2%}); if the change is intended, rerun "
            f"with UPDATE_REFERENCE=1"
        )


@needs_tools
def test_a_reference_exists_for_every_page():
    """A missing reference would make the comparison silently vacuous."""
    if UPDATING:
        pytest.skip("references are being regenerated")
    committed = sorted(REFERENCE.glob("page-*.png"))
    assert len(committed) == EXPECTED_PAGES, (
        f"{len(committed)} reference pages committed, expected {EXPECTED_PAGES}"
    )
