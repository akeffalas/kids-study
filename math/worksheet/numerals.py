"""Ways of naming and decomposing numbers.

Everything the answer key asserts about a number is computed here rather than
transcribed. A worksheet whose key is typed by hand can print a wrong answer
and no test will notice; that is the one bug this project cannot afford.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Final

__all__ = [
    "PLACES",
    "decimal_digit_at",
    "decimal_place_value",
    "digit_at",
    "from_roman",
    "place_value",
    "round_to_place",
    "spell_decimal",
    "spell_integer",
    "to_roman",
]

# --------------------------------------------------------------------------
# Roman numerals
# --------------------------------------------------------------------------

_ROMAN_VALUES: Final = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)

_ROMAN_MAX: Final = 3999


def to_roman(number: int) -> str:
    """Convert 1-3999 to Roman numerals.

    Raises:
        ValueError: If the number is outside the representable range.
    """
    if not 1 <= number <= _ROMAN_MAX:
        raise ValueError(f"cannot write {number} in Roman numerals")
    out: list[str] = []
    remainder = number
    for value, glyph in _ROMAN_VALUES:
        count, remainder = divmod(remainder, value)
        out.append(glyph * count)
    return "".join(out)


def from_roman(numeral: str) -> int:
    """Convert a Roman numeral to an integer.

    Round-trips with :func:`to_roman`, so a malformed numeral such as ``IIII``
    is rejected rather than quietly accepted.

    Raises:
        ValueError: If the numeral is empty or not in canonical form.
    """
    text = numeral.strip().upper()
    if not text:
        raise ValueError("empty Roman numeral")

    singles = {glyph: value for value, glyph in _ROMAN_VALUES if len(glyph) == 1}
    total = 0
    previous = 0
    for char in reversed(text):
        if char not in singles:
            raise ValueError(f"not a Roman numeral: {numeral!r}")
        value = singles[char]
        total += -value if value < previous else value
        previous = max(previous, value)

    if to_roman(total) != text:
        raise ValueError(f"{numeral!r} is not canonical; {total} is {to_roman(total)}")
    return total


# --------------------------------------------------------------------------
# Place value
# --------------------------------------------------------------------------

# Exponent of ten for each place the worksheet names.
PLACES: Final = {
    "millions": 6,
    "hundred-thousands": 5,
    "ten-thousands": 4,
    "thousands": 3,
    "hundreds": 2,
    "tens": 1,
    "ones": 0,
    "tenths": -1,
    "hundredths": -2,
    "thousandths": -3,
}


def digit_at(number: int, place: int) -> int:
    """Return the digit of ``number`` at the given power-of-ten place."""
    return int(abs(number) // 10**place % 10)


def place_value(number: int, place: int) -> int:
    """Return what the digit at ``place`` is worth, e.g. 300000 not 3."""
    return int(digit_at(number, place) * 10**place)


def decimal_digit_at(value: Decimal, place: int) -> int:
    """Return the digit of ``value`` at the given place, which may be negative."""
    return int(value.scaleb(-place)) % 10


def decimal_place_value(value: Decimal, place: int) -> Decimal:
    """Return what the digit at ``place`` is worth, e.g. 0.02 not 2."""
    return Decimal(decimal_digit_at(value, place)).scaleb(place)


def round_to_place(value: Decimal, place: int) -> Decimal:
    """Round to a power-of-ten place, half away from zero.

    Schools teach half-up; Python's default banker's rounding would make
    2.5 round to 2 and quietly contradict the lesson.
    """
    return value.quantize(Decimal(1).scaleb(place), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# Number names
# --------------------------------------------------------------------------

_ONES: Final = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)  # fmt: skip
_TENS: Final = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
)  # fmt: skip

_SPELL_MAX: Final = 999
_SCORE: Final = 20
_HUNDRED: Final = 100
_DECIMAL_PLACE_NAMES: Final = {1: "tenths", 2: "hundredths", 3: "thousandths"}


def spell_integer(number: int) -> str:
    """Spell 0-999 in words, as a fifth grader would write it.

    Raises:
        ValueError: If the number is outside 0-999.
    """
    if not 0 <= number <= _SPELL_MAX:
        raise ValueError(f"can only spell 0..{_SPELL_MAX}, got {number}")
    if number < _SCORE:
        return _ONES[number]
    if number < _HUNDRED:
        tens, ones = divmod(number, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    hundreds, rest = divmod(number, _HUNDRED)
    head = f"{_ONES[hundreds]} hundred"
    return f"{head} {spell_integer(rest)}" if rest else head


def spell_decimal(value: Decimal) -> str:
    """Spell a decimal in words, e.g. ``five and forty-seven thousandths``.

    Raises:
        ValueError: If the value has more than three decimal places.
    """
    # Decimal reports a string exponent ("n", "N", "F") for NaN and Infinity,
    # so this narrows a value, not a type: the caller did pass a Decimal.
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        raise ValueError(f"expected a finite decimal, got {value}")  # noqa: TRY004
    places = -exponent
    if places not in _DECIMAL_PLACE_NAMES:
        raise ValueError(f"expected 1-3 decimal places, got {value}")

    whole = int(value)
    fraction = int(value.scaleb(places)) % 10**places
    spoken = f"{spell_integer(fraction)} {_DECIMAL_PLACE_NAMES[places]}"
    return f"{spell_integer(whole)} and {spoken}" if whole else spoken
