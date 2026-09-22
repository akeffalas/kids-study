"""Parsing the palette out of the document is what keeps the gates honest.

If a token silently fails to parse, every check that references it either
vanishes or resolves to the wrong colour.
"""

import textwrap

import pytest

from worksheet.colors import Color
from worksheet.stylesheet import Stylesheet, StylesheetError

MINIMAL = textwrap.dedent(
    """
    :root {
      --t-sm: 13px;
      --ink:   #3B2A18;
      --paper: #FDF6E3;
    }
    .q { color: var(--ink); font-size: var(--t-sm); }
    """
)


def build_html(css: str) -> str:
    return f"<!doctype html><html><head><style>{css}</style></head><body></body></html>"


@pytest.fixture
def sheet():
    return Stylesheet.from_html(build_html(MINIMAL))


def test_collects_colour_tokens_and_skips_the_rest(sheet):
    """Spacing and type tokens share the block and must not be treated as colours."""
    assert sheet.palette == {
        "ink": Color.from_hex("#3B2A18"),
        "paper": Color.from_hex("#FDF6E3"),
    }


def test_requires_a_style_block():
    with pytest.raises(StylesheetError, match="no <style> block"):
        Stylesheet.from_html("<html><body>nothing</body></html>")


def test_requires_a_root_block():
    with pytest.raises(StylesheetError, match="no :root block"):
        Stylesheet.from_html(build_html(".q { color: red; }"))


def test_requires_at_least_one_colour_token():
    with pytest.raises(StylesheetError, match="no colour tokens"):
        Stylesheet.from_html(build_html(":root { --s1: 4px; }"))


def test_reads_from_a_path(tmp_path):
    path = tmp_path / "doc.html"
    path.write_text(build_html(MINIMAL), encoding="utf-8")
    assert Stylesheet.from_path(path).palette["ink"] == Color.from_hex("#3B2A18")


def test_resolves_a_token_name(sheet):
    assert sheet.resolve("ink") == Color.from_hex("#3B2A18")


def test_resolves_a_literal(sheet):
    assert sheet.resolve("#FFFFFF") == Color(255, 255, 255)


def test_unknown_token_names_the_alternatives(sheet):
    with pytest.raises(KeyError, match="unknown colour token"):
        sheet.resolve("nope")


def test_a_clean_sheet_reports_no_violations(sheet):
    assert sheet.untokenised_colors() == []
    assert sheet.hardcoded_font_sizes() == []


def test_flags_a_literal_colour_in_a_rule():
    css = MINIMAL + ".stray { color: #ABCDEF; }"
    assert Stylesheet.from_html(build_html(css)).untokenised_colors() == ["#ABCDEF"]


def test_flags_a_hardcoded_font_size():
    css = MINIMAL + ".stray { font-size: 12.5px; }"
    sizes = Stylesheet.from_html(build_html(css)).hardcoded_font_sizes()
    assert sizes == ["font-size: 12.5px"]


def test_root_definitions_are_not_themselves_violations(sheet):
    """The tokens are literals by definition; flagging them would be unfixable."""
    assert sheet.untokenised_colors() == []
