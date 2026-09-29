"""The gates run against the real worksheet, not a fixture.

A synthetic document would let the shipped file drift while the suite stayed
green, which is exactly the failure these checks exist to catch.
"""

from pathlib import Path

import pytest

from worksheet.audit import Status, audit
from worksheet.content import ANSWERS, GIVENS, IDENTITIES
from worksheet.spec import ARTWORK_CHECKS, CONTRAST_CHECKS

SOURCE = Path(__file__).resolve().parent.parent / "chapter-1" / "hyrule-math-review.html"
TOKEN_GATES = 2


def bound_surfaces() -> set[tuple[str | None, str, str]]:
    """Re-derive the binding set independently of the auditor's own loop."""
    return {
        (surface.selector, surface.prop, surface.token)
        for check in CONTRAST_CHECKS
        for surface in (check.foreground, check.background)
        if surface.is_bound and not surface.token.startswith("#")
    }


@pytest.fixture(scope="module")
def report():
    return audit(SOURCE)


def test_the_worksheet_is_present():
    assert SOURCE.is_file(), f"missing worksheet at {SOURCE}"


def test_every_declared_check_is_evaluated(report):
    expected = (
        len(GIVENS)
        + len(ANSWERS)
        + len(IDENTITIES)
        + TOKEN_GATES
        + len(bound_surfaces())
        + len(CONTRAST_CHECKS)
        + len(ARTWORK_CHECKS)
    )
    assert len(report.findings) == expected


def test_the_worksheet_is_greyscale_ready(report):
    failures = [f"{f.label}: {f.detail}" for f in report.failures]
    assert not failures, "greyscale gate failed:\n" + "\n".join(failures)


def test_the_spec_references_only_declared_tokens(report):
    """resolve() raises on an unknown token, so a clean run proves no drift."""
    assert report.ok


def test_groups_are_stable(report):
    assert set(report.by_group()) == {
        "givens",
        "answers",
        "tokens",
        "binding",
        "contrast",
        "artwork",
    }


def test_every_computed_answer_appears_in_the_printed_key(report):
    """The gate that makes a wrong answer key impossible to ship."""
    missing = [f.label for f in report.by_group()["answers"] if f.failed]
    assert not missing, f"answer key disagrees with the maths: {missing}"


def test_every_question_prints_the_numbers_it_was_built_from(report):
    """Guards the other direction: editing a question but not the content layer."""
    missing = [f.label for f in report.by_group()["givens"] if f.failed]
    assert not missing, f"worksheet no longer shows these givens: {missing}"


def test_the_contract_still_describes_the_document(report):
    stale = [f.label for f in report.by_group()["binding"] if f.failed]
    assert not stale, f"spec no longer matches the stylesheet: {stale}"


def test_ok_matches_the_absence_of_failures(report):
    assert report.ok is (len(report.failures) == 0)


def test_the_pdf_gate_is_skipped_when_no_pdf_is_given(report):
    assert "output" not in report.by_group()


def test_a_missing_pdf_is_a_failure_not_a_crash(tmp_path):
    result = audit(SOURCE, tmp_path / "absent.pdf")
    page_check = next(f for f in result.findings if f.group == "output")
    assert page_check.status is Status.FAIL
    assert "not built" in page_check.detail


def test_a_lightened_rule_token_trips_the_contrast_gate(tmp_path):
    """A gate that cannot fail is decoration, so prove this one fires."""
    broken = tmp_path / "broken.html"
    broken.write_text(
        SOURCE.read_text(encoding="utf-8").replace(
            "--rule:    #A8863F;", "--rule:    #E8DCC0;", 1
        ),
        encoding="utf-8",
    )
    result = audit(broken)
    assert not result.ok
    assert any(f.label == "dotted rule on white" for f in result.failures)


def test_a_stray_literal_trips_the_token_gate(tmp_path):
    broken = tmp_path / "broken.html"
    broken.write_text(
        SOURCE.read_text(encoding="utf-8").replace(
            "  .amp {", "  .regression { color: #ABCDEF; }\n  .amp {", 1
        ),
        encoding="utf-8",
    )
    result = audit(broken)
    assert not result.ok
    assert any("#ABCDEF" in f.detail for f in result.failures)
