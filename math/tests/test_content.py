"""The content layer is the worksheet's maths, independent of its markup.

These check the arithmetic itself. Whether the printed key agrees with it is a
separate gate, in test_audit.
"""

from decimal import Decimal

import pytest

from worksheet.content import ANSWERS, ELIXIR, IDENTITIES, RUPEES


def test_every_printed_identity_is_actually_true():
    """A worksheet that prints a false equation teaches the wrong thing."""
    untrue = [i.name for i in IDENTITIES if not i.holds]
    assert not untrue, f"these equations are false: {untrue}"


def test_the_four_named_properties_are_covered():
    assert {i.name for i in IDENTITIES} == {
        "Associative",
        "Commutative",
        "Distributive",
        "Identity",
    }


def test_the_elixir_sums_to_a_clean_three_decimal_answer():
    assert sum(ELIXIR) == Decimal("7.490")


def test_the_elixir_has_five_addends_with_ragged_precision():
    """The point of the question is aligning decimal points, not adding."""
    assert len(ELIXIR) == 5
    precisions = {v.as_tuple().exponent for v in ELIXIR}
    assert len(precisions) > 1


def test_the_rupees_regroup_into_two_hundreds():
    """The question only rewards the property if the pairs are friendly."""
    assert RUPEES[0] + RUPEES[2] == 100
    assert RUPEES[1] + RUPEES[3] == 100
    assert sum(RUPEES) == 200


def test_every_answer_has_a_question_number_and_a_value():
    assert ANSWERS
    for answer in ANSWERS:
        assert 1 <= answer.question <= 12
        assert answer.value.strip()


def test_answers_cover_every_question():
    assert {a.question for a in ANSWERS} == set(range(1, 13))


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (1, "1,986"),
        (3, "300,000"),
        (8, "5,480,279"),
        (9, "3.045 < 3.05 < 3.4 < 3.405"),
        (12, "7.490 lb"),
    ],
)
def test_spot_check_derived_values(question, expected):
    """Pin a few by hand, so a broken derivation cannot quietly agree with itself."""
    assert expected in {a.value for a in ANSWERS if a.question == question}
