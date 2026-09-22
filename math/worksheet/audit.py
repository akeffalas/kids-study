"""Quality gates: answers, contract binding, print contrast, tokens, pagination."""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pypdf import PdfReader

from .colors import contrast_ratio
from .content import ANSWERS, GIVENS, IDENTITIES
from .document import Document
from .spec import ARTWORK_CHECKS, CONTRAST_CHECKS, EXPECTED_PAGES
from .stylesheet import Stylesheet

__all__ = ["Finding", "Report", "Status", "audit"]


class Status(StrEnum):
    """Whether a single gate held."""

    PASS = "pass"  # noqa: S105 - a gate outcome, not a credential
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class Finding:
    """One evaluated gate."""

    group: str
    label: str
    status: Status
    detail: str

    @property
    def failed(self) -> bool:
        """True when this gate did not hold."""
        return self.status is Status.FAIL


@dataclass(frozen=True, slots=True)
class Report:
    """Every gate evaluated in one run."""

    findings: tuple[Finding, ...]

    @property
    def failures(self) -> tuple[Finding, ...]:
        """Only the gates that did not hold."""
        return tuple(f for f in self.findings if f.failed)

    @property
    def ok(self) -> bool:
        """True when nothing failed."""
        return not self.failures

    def by_group(self) -> dict[str, list[Finding]]:
        """Findings bucketed by group, in the order they were evaluated."""
        grouped: dict[str, list[Finding]] = {}
        for finding in self.findings:
            grouped.setdefault(finding.group, []).append(finding)
        return grouped


def _verdict(passed: bool) -> Status:
    return Status.PASS if passed else Status.FAIL


def _check_answers(doc: Document) -> Iterator[Finding]:
    """Every computed answer must appear in the printed answer key."""
    for answer in ANSWERS:
        found = doc.key_contains(answer.value)
        yield Finding(
            group="answers",
            label=f"Q{answer.question} {answer.label}",
            status=_verdict(found),
            detail=answer.value if found else f"{answer.value!r} missing from the key",
        )


def _check_givens(doc: Document) -> Iterator[Finding]:
    """Every number a question is built from must actually be printed on it."""
    for given in GIVENS:
        found = doc.contains(given.value)
        yield Finding(
            group="givens",
            label=f"Q{given.question} {given.label}",
            status=_verdict(found),
            detail=given.value if found else f"{given.value!r} not on the worksheet",
        )


def _check_identities(doc: Document) -> Iterator[Finding]:
    """Each printed property equation must be a true statement."""
    for identity in IDENTITIES:
        shown = doc.contains(identity.shown)
        yield Finding(
            group="answers",
            label=f"{identity.name} equation",
            status=_verdict(identity.holds and shown),
            detail=(
                identity.shown
                if identity.holds and shown
                else f"holds={identity.holds} printed={shown}"
            ),
        )


def _check_bindings(sheet: Stylesheet) -> Iterator[Finding]:
    """Each bound surface must still be declared by the rule it names."""
    seen: set[tuple[str, str, str]] = set()
    for check in CONTRAST_CHECKS:
        for surface in (check.foreground, check.background):
            if not surface.is_bound or surface.token.startswith("#"):
                continue
            key = (surface.selector or "", surface.prop, surface.token)
            if key in seen:
                continue
            seen.add(key)
            declared = sheet.declares(*key)
            yield Finding(
                group="binding",
                label=f"{key[0]} {{ {key[1]} }}",
                status=_verdict(declared),
                detail=(
                    f"var(--{surface.token})"
                    if declared
                    else f"no longer sets var(--{surface.token})"
                ),
            )


def _check_contrast(sheet: Stylesheet) -> Iterator[Finding]:
    """Evaluate every text and UI-graphic contrast pair."""
    for check in CONTRAST_CHECKS:
        front = sheet.resolve(check.foreground.token)
        back = sheet.resolve(check.background.token)
        ratio = contrast_ratio(front, back)
        yield Finding(
            group="contrast",
            label=check.label,
            status=_verdict(ratio >= check.minimum),
            detail=(
                f"{ratio:5.2f}:1 (need {check.minimum}:1) "
                f"grey {front.greyscale}/{back.greyscale}"
            ),
        )


def _check_artwork(sheet: Stylesheet) -> Iterator[Finding]:
    """Evaluate outlined shapes, which pass on fill or on stroke."""
    for check in ARTWORK_CHECKS:
        back = sheet.resolve(check.background)
        via_fill = contrast_ratio(sheet.resolve(check.fill), back)
        via_stroke = contrast_ratio(sheet.resolve(check.stroke), back)
        best, channel = max((via_fill, "fill"), (via_stroke, "stroke"))
        yield Finding(
            group="artwork",
            label=check.label,
            status=_verdict(best >= check.minimum),
            detail=f"{best:5.2f}:1 via {channel} (need {check.minimum}:1)",
        )


def _check_tokens(sheet: Stylesheet) -> Iterator[Finding]:
    """Evaluate whether any rule bypassed the token system."""
    stray = sheet.untokenised_colors()
    yield Finding(
        group="tokens",
        label="all rule colours reference a token",
        status=_verdict(not stray),
        detail="clean" if not stray else f"{len(stray)} literal(s): {', '.join(stray)}",
    )

    literals = sheet.hardcoded_font_sizes()
    yield Finding(
        group="tokens",
        label="all font sizes reference a token",
        status=_verdict(not literals),
        detail="clean" if not literals else f"{len(literals)}: {', '.join(literals)}",
    )


def _check_pdf(pdf: Path) -> Iterator[Finding]:
    """Evaluate the built PDF's page count."""
    if not pdf.is_file():
        yield Finding(
            group="output",
            label="page count",
            status=Status.FAIL,
            detail=f"{pdf.name} not built",
        )
        return
    pages = len(PdfReader(pdf).pages)
    yield Finding(
        group="output",
        label="page count",
        status=_verdict(pages == EXPECTED_PAGES),
        detail=f"{pages} (expected {EXPECTED_PAGES})",
    )


def audit(source: Path, pdf: Path | None = None) -> Report:
    """Run every gate against ``source``, and against ``pdf`` when supplied."""
    doc = Document.from_path(source)
    sheet = doc.stylesheet
    findings = [
        *_check_givens(doc),
        *_check_answers(doc),
        *_check_identities(doc),
        *_check_tokens(sheet),
        *_check_bindings(sheet),
        *_check_contrast(sheet),
        *_check_artwork(sheet),
    ]
    if pdf is not None:
        findings.extend(_check_pdf(pdf))
    return Report(tuple(findings))
