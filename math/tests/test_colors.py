"""The contrast maths underpins every print gate, so it is pinned here.

If these are wrong, a worksheet can pass the audit and still be illegible on
paper, which is the one failure the gates exist to prevent.
"""

import pytest

from worksheet.colors import Color, contrast_ratio

BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("#FFFFFF", WHITE),
        ("ffffff", WHITE),
        ("#fff", WHITE),
        ("  #000000  ", BLACK),
        ("#1F6B36", Color(31, 107, 54)),
    ],
)
def test_parses_hex_in_every_accepted_form(text, expected):
    assert Color.from_hex(text) == expected


@pytest.mark.parametrize("text", ["", "#", "#12", "#12345", "#gggggg", "red"])
def test_rejects_malformed_hex(text):
    with pytest.raises(ValueError, match="not a hex colour"):
        Color.from_hex(text)


def test_rejects_out_of_range_channel():
    with pytest.raises(ValueError, match=r"must be in 0\.\.255"):
        Color(256, 0, 0)


def test_luminance_spans_black_to_white():
    assert BLACK.relative_luminance == pytest.approx(0.0)
    assert WHITE.relative_luminance == pytest.approx(1.0)


def test_green_dominates_the_luminance_coefficients():
    red = Color(255, 0, 0).relative_luminance
    green = Color(0, 255, 0).relative_luminance
    blue = Color(0, 0, 255).relative_luminance
    assert green > red > blue


def test_greyscale_of_a_neutral_is_itself():
    assert Color(128, 128, 128).greyscale == 128


def test_hex_round_trips():
    assert Color.from_hex("#1F6B36").hex == "#1F6B36"


def test_contrast_spans_the_full_range():
    assert contrast_ratio(BLACK, WHITE) == pytest.approx(21.0)
    assert contrast_ratio(WHITE, WHITE) == pytest.approx(1.0)


def test_contrast_is_symmetric():
    a, b = Color.from_hex("#3B2A18"), Color.from_hex("#FDF6E3")
    assert contrast_ratio(a, b) == pytest.approx(contrast_ratio(b, a))


def test_contrast_matches_a_known_wcag_value():
    """#767676 on white is the canonical 4.54:1 boundary case."""
    ratio = contrast_ratio(Color.from_hex("#767676"), WHITE)
    assert ratio == pytest.approx(4.54, abs=0.01)


@pytest.mark.parametrize("shade", range(0, 256, 17))
def test_contrast_never_leaves_the_valid_range(shade):
    assert 1.0 <= contrast_ratio(Color(shade, shade, shade), WHITE) <= 21.0
