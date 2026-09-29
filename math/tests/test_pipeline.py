"""End-to-end: build the PDF, then gate the artefact that was built.

These need Chrome and so skip on CI, where the HTML-only gates still run. They
are the only tests that exercise the page-count check against a real PDF.
"""

import shutil
from pathlib import Path

import pytest

from worksheet.__main__ import EXIT_OK, main
from worksheet.audit import Status, audit
from worksheet.render import BUNDLE_PATHS, render_pdf
from worksheet.spec import EXPECTED_PAGES

SOURCE = Path(__file__).resolve().parent.parent / "chapter-1" / "hyrule-math-review.html"

needs_chrome = pytest.mark.skipif(
    not (
        any(Path(p).is_file() for p in BUNDLE_PATHS)
        or shutil.which("chromium")
        or shutil.which("google-chrome")
    ),
    reason="no Chromium-family browser on this machine",
)


@pytest.fixture(scope="module")
def built_pdf(tmp_path_factory):
    out = tmp_path_factory.mktemp("build") / "worksheet.pdf"
    return render_pdf(SOURCE, out)


@needs_chrome
def test_the_built_pdf_has_the_expected_page_count(built_pdf):
    page_check = next(f for f in audit(SOURCE, built_pdf).findings if f.group == "output")
    assert page_check.status is Status.PASS
    assert str(EXPECTED_PAGES) in page_check.detail


@needs_chrome
def test_a_wrong_page_count_fails_the_gate(monkeypatch, built_pdf):
    """Pin the failure direction too, so the check cannot silently pass."""
    monkeypatch.setattr("worksheet.audit.EXPECTED_PAGES", EXPECTED_PAGES + 1)
    page_check = next(f for f in audit(SOURCE, built_pdf).findings if f.group == "output")
    assert page_check.status is Status.FAIL


@needs_chrome
def test_check_builds_then_gates(tmp_path, capsys):
    code = main(
        [
            "check",
            "--source",
            str(SOURCE),
            "--output",
            str(tmp_path / "out.pdf"),
        ]
    )
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "built" in out
    assert "checks passed" in out
