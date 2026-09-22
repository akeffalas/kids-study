"""Chrome discovery and the failure paths around it.

The render itself needs a browser, so those two tests skip where there is
none. Everything else here runs everywhere, including CI.
"""

import shutil
from pathlib import Path

import pytest

from worksheet.render import (
    BUNDLE_PATHS,
    ChromeNotFoundError,
    RenderError,
    build_command,
    find_chrome,
    render_pdf,
)

SOURCE = Path(__file__).resolve().parent.parent / "hyrule-math-review.html"
FAKE_CHROME = Path("/bin/chrome")


def chrome_available() -> bool:
    return any(Path(p).is_file() for p in BUNDLE_PATHS) or bool(
        shutil.which("chromium") or shutil.which("google-chrome")
    )


needs_chrome = pytest.mark.skipif(
    not chrome_available(), reason="no Chromium-family browser on this machine"
)


def test_an_explicit_override_wins(tmp_path):
    fake = tmp_path / "browser"
    fake.touch()
    assert find_chrome(fake) == fake


def test_a_missing_override_is_rejected(tmp_path):
    with pytest.raises(ChromeNotFoundError, match="no browser at"):
        find_chrome(tmp_path / "absent")


def test_a_directory_is_not_a_browser(tmp_path):
    with pytest.raises(ChromeNotFoundError):
        find_chrome(tmp_path)


def test_the_error_names_everything_it_tried(monkeypatch):
    monkeypatch.setattr("worksheet.render.PATH_COMMANDS", ())
    monkeypatch.setattr("worksheet.render.BUNDLE_PATHS", ())
    with pytest.raises(ChromeNotFoundError, match="no Chromium-family browser"):
        find_chrome()


@needs_chrome
def test_discovers_an_installed_browser():
    assert find_chrome().is_file()


def test_the_source_is_passed_as_a_file_uri(tmp_path):
    argv = build_command(FAKE_CHROME, SOURCE, tmp_path / "out.pdf")
    assert argv[-1].startswith("file://")


def test_the_output_path_is_bound_to_the_flag(tmp_path):
    out = tmp_path / "out.pdf"
    assert f"--print-to-pdf={out}" in build_command(FAKE_CHROME, SOURCE, out)


def test_backgrounds_are_forced(tmp_path):
    """Without this flag Chrome drops every box and rule from the PDF."""
    argv = build_command(FAKE_CHROME, SOURCE, tmp_path / "o.pdf")
    assert "--run-all-compositor-stages-before-draw" in argv


def test_a_missing_source_raises_before_launching_chrome(tmp_path):
    with pytest.raises(FileNotFoundError):
        render_pdf(tmp_path / "absent.html", tmp_path / "out.pdf")


def test_a_browser_that_writes_nothing_is_an_error(tmp_path):
    """Chrome can exit zero and still produce no file, so the file is the signal."""
    stub = tmp_path / "stub"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    with pytest.raises(RenderError, match="produced no PDF"):
        render_pdf(SOURCE, tmp_path / "out.pdf", chrome=stub)


@needs_chrome
def test_renders_a_pdf(tmp_path):
    out = render_pdf(SOURCE, tmp_path / "out.pdf")
    assert out.is_file()
    assert out.read_bytes().startswith(b"%PDF-")
