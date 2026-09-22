"""The worksheet's maths, computed rather than transcribed.

Every value here is derived from the question's own numbers, then checked
against the printed answer key. Editing a quantity in the worksheet without
updating the key therefore fails the build, instead of shipping a wrong answer
to a ten-year-old.

The display strings are built from the same numbers that the arithmetic uses,
so the printed equation and the checked equation cannot disagree.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from .numerals import (
    PLACES,
    decimal_digit_at,
    decimal_place_value,
    digit_at,
    from_roman,
    place_value,
    round_to_place,
    spell_decimal,
    to_roman,
)

__all__ = ["ANSWERS", "GIVENS", "IDENTITIES", "Answer", "Given", "Identity"]


@dataclass(frozen=True, slots=True)
class Answer:
    """A value that must appear in the printed answer key."""

    question: int
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class Given:
    """A value that must appear in the printed question.

    Answers alone are not enough. If the worksheet's own numbers are edited and
    this module is not, the derived answers stay self-consistent and the key
    keeps passing while the printed question has moved underneath it. Checking
    the givens too closes that loop in both directions.
    """

    question: int
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class Identity:
    """An equation printed on the worksheet, and whether it is actually true."""

    name: str
    shown: str
    holds: bool


def _thousands(number: int) -> str:
    """Format with commas, matching how the worksheet prints large numbers."""
    return f"{number:,}"


# --------------------------------------------------------------------------
# The questions' own numbers. Everything below is derived from these.
# --------------------------------------------------------------------------

TEMPLE_NUMERAL: Final = "MCMLXXXVI"
CHEST_TO_ROMAN: Final = (44, 360)
CHEST_TO_ARABIC: Final = ("XCV", "MDCCXII")

CENSUS: Final = 8_364_572
METER: Final = Decimal("9.628")
SHRINE_RUN: Final = Decimal("8.476")
NEXT_RUN: Final = Decimal("2.97")

WORD_FORM_VALUE: Final = Decimal("5.047")
DIGIT_FORM_VALUE: Final = Decimal("0.315")

POTIONS: Final = (
    (Decimal("0.7"), Decimal("0.68")),
    (Decimal("4.320"), Decimal("4.32")),
    (Decimal("2.109"), Decimal("2.19")),
)
HOARDS: Final = (5_408_297, 5_480_279)
RUNES: Final = (Decimal("3.4"), Decimal("3.045"), Decimal("3.405"), Decimal("3.05"))

ASSOCIATIVE_FACTORS: Final = (7, 25, 4)
COMMUTATIVE_FACTORS: Final = (6, 43)
DISTRIBUTIVE_PARTS: Final = (8, 50, 3)
IDENTITY_ADDEND: Final = 348

RUPEES: Final = (25, 78, 75, 22)
QUIVERS: Final = 7
ARROWS: Final = 104
ARROWS_SPLIT: Final = (100, 4)

ELIXIR: Final = (
    Decimal("2.375"),
    Decimal("0.84"),
    Decimal("1.006"),
    Decimal("3.25"),
    Decimal("0.019"),
)


def _deciding_place(left: int, right: int) -> str:
    """Name the highest place where two numbers differ.

    This is the reasoning Q8 asks the student to articulate, so it is computed
    the same way they would: walk down from the biggest place.
    """
    for name, exponent in PLACES.items():
        if exponent >= 0 and digit_at(left, exponent) != digit_at(right, exponent):
            return name
    raise ValueError(f"{left} and {right} do not differ")


def _compare(left: Decimal, right: Decimal) -> str:
    """Return the symbol the student should write between two decimals."""
    if left > right:
        return ">"
    return "<" if left < right else "="


def _build_answers() -> tuple[Answer, ...]:
    """Derive every answer-key value from the question data above."""
    larger = max(HOARDS)
    ordered = sorted(RUNES)
    friendly = (RUPEES[0] + RUPEES[2], RUPEES[1] + RUPEES[3])

    return (
        Answer(1, "Roman to standard", _thousands(from_roman(TEMPLE_NUMERAL))),
        *(Answer(2, f"{n} to Roman", to_roman(n)) for n in CHEST_TO_ROMAN),
        *(
            Answer(2, f"{n} to standard", _thousands(from_roman(n)))
            for n in CHEST_TO_ARABIC
        ),
        Answer(
            3,
            "value of the 3",
            _thousands(place_value(CENSUS, PLACES["hundred-thousands"])),
        ),
        Answer(3, "ten-thousands digit", str(digit_at(CENSUS, PLACES["ten-thousands"]))),
        Answer(3, "millions digit", str(digit_at(CENSUS, PLACES["millions"]))),
        Answer(
            4, "thousandths digit", str(decimal_digit_at(METER, PLACES["thousandths"]))
        ),
        Answer(
            4, "value of the 2", str(decimal_place_value(METER, PLACES["hundredths"]))
        ),
        Answer(
            5, "rounded to a tenth", str(round_to_place(SHRINE_RUN, PLACES["tenths"]))
        ),
        Answer(
            5,
            "rounded to a hundredth",
            str(round_to_place(SHRINE_RUN, PLACES["hundredths"])),
        ),
        Answer(5, "carry into the ones", str(round_to_place(NEXT_RUN, PLACES["tenths"]))),
        Answer(6, "words to standard form", str(WORD_FORM_VALUE)),
        Answer(6, "standard form to words", spell_decimal(DIGIT_FORM_VALUE)),
        *(
            Answer(7, f"{left} vs {right}", f"{left} {_compare(left, right)} {right}")
            for left, right in POTIONS
        ),
        Answer(8, "larger hoard", _thousands(larger)),
        Answer(8, "deciding place", _deciding_place(*HOARDS)),
        Answer(9, "least to greatest", " < ".join(str(r) for r in ordered)),
        *(
            Answer(10, f"property {identity.name.lower()}", identity.name)
            for identity in IDENTITIES
        ),
        Answer(
            11,
            "friendly pairs",
            f"= {friendly[0]} + {friendly[1]} = {sum(RUPEES)}",
        ),
        Answer(
            11,
            "distributive shortcut",
            f"= {QUIVERS * ARROWS_SPLIT[0]} + {QUIVERS * ARROWS_SPLIT[1]} "
            f"= {QUIVERS * ARROWS}",
        ),
        Answer(12, "elixir total", f"{sum(ELIXIR)} lb"),
    )


def _build_identities() -> tuple[Identity, ...]:
    """Build each printed equation and its truth from the same numbers.

    Deriving ``shown`` rather than typing it is the point: a transcription slip
    would otherwise print one equation while the build verified another.
    """
    a, b, c = ASSOCIATIVE_FACTORS
    d, e = COMMUTATIVE_FACTORS
    f, g, h = DISTRIBUTIVE_PARTS
    n = IDENTITY_ADDEND
    return (
        Identity(
            "Associative",
            f"({a} × {b}) × {c} = {a} × ({b} × {c})",
            (a * b) * c == a * (b * c),
        ),
        Identity("Commutative", f"{d} × {e} = {e} × {d}", d * e == e * d),
        Identity(
            "Distributive",
            f"{f} × ({g} + {h}) = ({f} × {g}) + ({f} × {h})",
            f * (g + h) == (f * g) + (f * h),
        ),
        Identity("Identity", f"{n} + 0 = {n}", n + 0 == n),
    )


def _build_givens() -> tuple[Given, ...]:
    """List the numbers each question must actually print."""
    return (
        Given(1, "temple numeral", TEMPLE_NUMERAL),
        *(Given(2, "chest row", str(n)) for n in CHEST_TO_ROMAN),
        *(Given(2, "chest row", n) for n in CHEST_TO_ARABIC),
        Given(3, "census", _thousands(CENSUS)),
        Given(4, "energy meter", str(METER)),
        Given(5, "shrine run", str(SHRINE_RUN)),
        Given(5, "next run", str(NEXT_RUN)),
        Given(6, "decimal to spell", str(DIGIT_FORM_VALUE)),
        *(Given(7, "potion", str(value)) for pair in POTIONS for value in pair),
        *(Given(8, "hoard", _thousands(n)) for n in HOARDS),
        *(Given(9, "rune", str(r)) for r in RUNES),
        Given(11, "rupees", " + ".join(str(r) for r in RUPEES)),
        Given(11, "quivers", f"{QUIVERS} quivers"),
        Given(11, "arrows", f"{ARROWS} arrows"),
        *(Given(12, "ingredient", f"{w} lb") for w in ELIXIR),
    )


IDENTITIES: Final[tuple[Identity, ...]] = _build_identities()

ANSWERS: Final[tuple[Answer, ...]] = _build_answers()

GIVENS: Final[tuple[Given, ...]] = _build_givens()
