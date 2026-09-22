"""The worksheet's quality contract, expressed as data.

Colour references are token names wherever the token system covers them, so a
palette edit re-points the check rather than silently invalidating it.
Illustration colours are given as literals because they sit outside that system
on purpose.

Where a colour is set by a CSS rule, the surface names that rule. The binding
gate then proves the contract still describes the document: restyle ``.ask`` to
a different token and the check fails, instead of quietly asserting a pairing
that no longer exists.
"""

from dataclasses import dataclass
from typing import Final

__all__ = [
    "ARTWORK_CHECKS",
    "CONTRAST_CHECKS",
    "EXPECTED_PAGES",
    "GRAPHIC_MIN",
    "TEXT_MIN",
    "ArtworkCheck",
    "ContrastCheck",
    "Surface",
]

# WCAG 2.2: 4.5:1 for body text, 3:1 for large text, UI components and
# graphical objects.
TEXT_MIN: Final = 4.5
GRAPHIC_MIN: Final = 3.0

EXPECTED_PAGES: Final = 4


@dataclass(frozen=True, slots=True)
class Surface:
    """A colour, and optionally the CSS rule that is expected to declare it."""

    token: str
    selector: str | None = None
    prop: str = "color"

    @property
    def is_bound(self) -> bool:
        """Whether this surface claims a specific CSS rule."""
        return self.selector is not None


def fg(token: str, selector: str | None = None) -> Surface:
    """A foreground colour, set by ``color``."""
    return Surface(token, selector, "color")


def bg(token: str, selector: str | None = None) -> Surface:
    """A background colour, set by ``background``."""
    return Surface(token, selector, "background")


@dataclass(frozen=True, slots=True)
class ContrastCheck:
    """A foreground/background pair that must clear ``minimum``."""

    label: str
    foreground: Surface
    background: Surface
    minimum: float


@dataclass(frozen=True, slots=True)
class ArtworkCheck:
    """An outlined shape, legible through *either* of its two channels.

    A filled shape with a contrasting outline is distinguishable even when the
    fill matches its background, and the reverse holds too. Demanding both
    would fail correct artwork: gold on cream cannot reach 3:1 at any value,
    yet the dark outline makes the shape perfectly clear. The shield crest is
    the mirror case, passing on fill while its outline disappears.
    """

    label: str
    fill: str
    stroke: str
    background: str
    minimum: float = GRAPHIC_MIN


# Backgrounds without a selector are the page itself or an unpainted parent,
# which no single rule owns.
CONTRAST_CHECKS: Final[tuple[ContrastCheck, ...]] = (
    ContrastCheck("body text", fg("ink", "body"), bg("paper1"), TEXT_MIN),
    ContrastCheck("directive", fg("red", ".ask"), bg("paper1"), TEXT_MIN),
    ContrastCheck(
        "directive on quest", fg("red", ".ask"), bg("tint", ".quest"), TEXT_MIN
    ),
    ContrastCheck("math value", fg("green", ".q .big"), bg("paper1"), TEXT_MIN),
    ContrastCheck("table value", fg("green", "td"), bg("paper3", "td.fill"), TEXT_MIN),
    ContrastCheck("secondary text", fg("ink2", ".mini .pg"), bg("paper1"), TEXT_MIN),
    ContrastCheck(
        "sub-question label", fg("label", ".sub2 .lbl"), bg("paper1"), TEXT_MIN
    ),
    ContrastCheck(
        "answer-key rationale", fg("ink2", ".key .why"), bg("paper3", ".keybox"), TEXT_MIN
    ),
    ContrastCheck(
        "answer-key value", fg("green", ".key .a"), bg("paper3", ".keybox"), TEXT_MIN
    ),
    ContrastCheck(
        "word-bank chip", fg("ink", ".bank .chip"), bg("paper3", ".bank .chip"), TEXT_MIN
    ),
    ContrastCheck("badge numeral", fg("#FFFFFF"), bg("title", ".badge"), TEXT_MIN),
    ContrastCheck("table header", fg("title", "th"), bg("paper2", "th"), TEXT_MIN),
    ContrastCheck("card value", fg("green", ".card"), bg("#FFFFFF"), TEXT_MIN),
    ContrastCheck("dotted rule on white", fg("rule"), bg("#FFFFFF"), GRAPHIC_MIN),
    ContrastCheck("dotted rule on paper", fg("rule"), bg("paper1"), GRAPHIC_MIN),
    ContrastCheck("work pad on white", fg("rule"), bg("#FFFFFF"), GRAPHIC_MIN),
    ContrastCheck("work pad on tint", fg("rule"), bg("tint", ".quest"), GRAPHIC_MIN),
    ContrastCheck("card border", fg("rule"), bg("paper1"), GRAPHIC_MIN),
    ContrastCheck("ingredient card", fg("rule"), bg("tint", ".quest"), GRAPHIC_MIN),
    ContrastCheck("final-answer box", fg("green"), bg("tint", ".quest"), GRAPHIC_MIN),
    ContrastCheck("badge ring", fg("gold-hi"), bg("title", ".badge"), GRAPHIC_MIN),
)

ARTWORK_CHECKS: Final[tuple[ArtworkCheck, ...]] = (
    ArtworkCheck("Triforce", "gold-hi", "#8A6512", "paper1"),
    ArtworkCheck("shield rim", "#C9CDD4", "#4A4F58", "paper1"),
    ArtworkCheck("shield field", "#1F4E8C", "#153663", "paper1"),
    ArtworkCheck("shield crest", "gold-hi", "#8A6512", "#1F4E8C"),
    ArtworkCheck("sword blade", "#CBD3DC", "#5A636E", "paper1"),
    ArtworkCheck("sword guard", "gold-hi", "#8A6512", "paper1"),
    ArtworkCheck("sword grip", "#3B6FC4", "#1F4E8C", "paper1"),
    ArtworkCheck("sword pommel", "#6FC6E8", "#1F4E8C", "paper1"),
)
