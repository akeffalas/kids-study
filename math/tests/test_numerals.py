"""The answer key is derived from these functions, so they carry the maths.

A wrong answer on a child's worksheet is the worst bug this project can ship,
and it would come from here.
"""

from decimal import Decimal

import pytest

from worksheet.numerals import (
    PLACES,
    decimal_digit_at,
    decimal_place_value,
    digit_at,
    from_roman,
    place_value,
    round_to_place,
    spell_decimal,
    spell_integer,
    to_roman,
)


@pytest.mark.parametrize(
    ("number", "numeral"),
    [
        (1, "I"),
        (4, "IV"),
        (9, "IX"),
        (44, "XLIV"),
        (95, "XCV"),
        (249, "CCXLIX"),
        (360, "CCCLX"),
        (1712, "MDCCXII"),
        (1986, "MCMLXXXVI"),
        (3999, "MMMCMXCIX"),
    ],
)
def test_roman_conversion_both_ways(number, numeral):
    assert to_roman(number) == numeral
    assert from_roman(numeral) == number


@pytest.mark.parametrize("number", range(1, 4000, 137))
def test_roman_round_trips(number):
    assert from_roman(to_roman(number)) == number


@pytest.mark.parametrize("number", [0, -1, 4000])
def test_roman_rejects_unrepresentable_numbers(number):
    with pytest.raises(ValueError, match="Roman numerals"):
        to_roman(number)


@pytest.mark.parametrize("numeral", ["", "  ", "ABC", "12"])
def test_roman_rejects_nonsense(numeral):
    with pytest.raises(ValueError, match="Roman numeral"):
        from_roman(numeral)


@pytest.mark.parametrize("numeral", ["IIII", "VV", "IC", "XXXX"])
def test_roman_rejects_non_canonical_forms(numeral):
    """IIII reads as 4 but is not how 4 is written, so it must not pass."""
    with pytest.raises(ValueError, match="canonical"):
        from_roman(numeral)


def test_digit_and_place_value_for_a_seven_digit_number():
    census = 8_364_572
    assert digit_at(census, PLACES["millions"]) == 8
    assert digit_at(census, PLACES["ten-thousands"]) == 6
    assert place_value(census, PLACES["hundred-thousands"]) == 300_000


def test_decimal_digit_and_place_value():
    meter = Decimal("9.628")
    assert decimal_digit_at(meter, PLACES["thousandths"]) == 8
    assert decimal_digit_at(meter, PLACES["tenths"]) == 6
    assert decimal_place_value(meter, PLACES["hundredths"]) == Decimal("0.02")


@pytest.mark.parametrize(
    ("value", "place", "expected"),
    [
        ("8.476", "tenths", "8.5"),
        ("8.476", "hundredths", "8.48"),
        ("8.476", "ones", "8"),
        ("2.97", "tenths", "3.0"),
        ("0.5", "ones", "1"),
        ("2.5", "ones", "3"),
    ],
)
def test_rounding(value, place, expected):
    assert round_to_place(Decimal(value), PLACES[place]) == Decimal(expected)


def test_rounding_carries_out_of_the_tenths_place():
    """2.97 to the nearest tenth is 3.0, not 2.10. This is the classic slip."""
    assert str(round_to_place(Decimal("2.97"), PLACES["tenths"])) == "3.0"


def test_rounding_is_half_up_not_bankers():
    """Schools teach half-up; Python's default would make 2.5 round to 2."""
    assert round_to_place(Decimal("2.5"), PLACES["ones"]) == Decimal("3")


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "zero"),
        (7, "seven"),
        (15, "fifteen"),
        (20, "twenty"),
        (47, "forty-seven"),
        (90, "ninety"),
        (100, "one hundred"),
        (315, "three hundred fifteen"),
        (999, "nine hundred ninety-nine"),
    ],
)
def test_spelling_integers(number, words):
    assert spell_integer(number) == words


@pytest.mark.parametrize("number", [-1, 1000])
def test_spelling_rejects_out_of_range(number):
    with pytest.raises(ValueError, match="can only spell"):
        spell_integer(number)


@pytest.mark.parametrize(
    ("value", "words"),
    [
        ("5.047", "five and forty-seven thousandths"),
        ("0.315", "three hundred fifteen thousandths"),
        ("0.5", "five tenths"),
        ("12.06", "twelve and six hundredths"),
    ],
)
def test_spelling_decimals(value, words):
    assert spell_decimal(Decimal(value)) == words


@pytest.mark.parametrize("value", ["1", "1.0001"])
def test_spelling_rejects_unsupported_precision(value):
    with pytest.raises(ValueError, match="decimal places"):
        spell_decimal(Decimal(value))
