"""Turn the worksheet HTML into a PDF.

Chrome does the rendering because the layout leans on flexbox, CSS custom
properties and paged-media rules that the lightweight Python renderers do not
implement faithfully. Nothing else on a Mac reliably honours ``@page``.
"""

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Final

__all__ = ["ChromeNotFoundError", "RenderError", "find_chrome", "render_pdf"]

# Bundled macOS installs are not on PATH, so they are probed explicitly.
BUNDLE_PATHS: Final = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
PATH_COMMANDS: Final = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
)

RENDER_TIMEOUT_SECONDS: Final = 120


class ChromeNotFoundError(RuntimeError):
    """No Chromium-family browser could be located."""


class RenderError(RuntimeError):
    """Chrome ran but produced no PDF."""


def find_chrome(override: Path | None = None) -> Path:
    """Locate a Chromium-family browser, preferring an explicit override.

    Raises:
        ChromeNotFoundError: If no browser is found.
    """
    if override is not None:
        if not override.is_file():
            raise ChromeNotFoundError(f"no browser at {override}")
        return override

    for command in PATH_COMMANDS:
        if found := shutil.which(command):
            return Path(found)
    for candidate in BUNDLE_PATHS:
        path = Path(candidate)
        if path.is_file():
            return path

    raise ChromeNotFoundError(
        "no Chromium-family browser found; tried "
        + ", ".join(PATH_COMMANDS)
        + " on PATH and:\n  "
        + "\n  ".join(BUNDLE_PATHS)
    )


def build_command(chrome: Path, source: Path, output: Path) -> Sequence[str]:
    """Assemble the headless-Chrome argv for one render."""
    return (
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        # Without this, backgrounds and borders can be dropped and the
        # worksheet loses every box and rule.
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=4000",
        f"--print-to-pdf={output}",
        source.resolve().as_uri(),
    )


def render_pdf(source: Path, output: Path, chrome: Path | None = None) -> Path:
    """Render ``source`` to ``output`` and return the written path.

    Raises:
        FileNotFoundError: If ``source`` does not exist.
        ChromeNotFoundError: If no browser is available.
        RenderError: If Chrome timed out or wrote no PDF.
    """
    if not source.is_file():
        raise FileNotFoundError(source)
    browser = find_chrome(chrome)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell, no user input
            build_command(browser, source, output),
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
            check=False,  # the written file is inspected below instead
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"Chrome timed out after {RENDER_TIMEOUT_SECONDS}s") from exc

    # Chrome reports success on stderr and can exit non-zero on unrelated
    # sandbox warnings, so the written file is the only reliable signal.
    if not output.is_file():
        detail = (result.stderr or result.stdout or "no output").strip()
        raise RenderError(f"Chrome produced no PDF: {detail}")
    return output
