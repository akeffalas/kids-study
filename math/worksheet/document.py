"""The worksheet document: its stylesheet, and its text as a reader sees it.

Answers are checked against rendered text rather than raw markup, so a value
split by a tag or written as an entity still matches.
"""

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

from .stylesheet import Stylesheet

__all__ = ["Document"]

_TAG: Final = re.compile(r"<[^>]+>")
_WHITESPACE: Final = re.compile(r"\s+")
_ANSWER_KEY: Final = re.compile(
    r'<div class="keybox">(?P<body>.*?)</div>\s*</div>', re.DOTALL
)


def _visible_text(markup: str) -> str:
    """Strip tags, decode entities and collapse runs of whitespace."""
    return _WHITESPACE.sub(" ", html.unescape(_TAG.sub(" ", markup))).strip()


@dataclass(frozen=True, slots=True)
class Document:
    """A parsed worksheet."""

    html: str
    stylesheet: Stylesheet

    @classmethod
    def from_html(cls, markup: str) -> Self:
        """Parse a worksheet from markup.

        Raises:
            StylesheetError: If the document has no usable stylesheet.
        """
        return cls(html=markup, stylesheet=Stylesheet.from_html(markup))

    @classmethod
    def from_path(cls, path: Path) -> Self:
        """Parse the worksheet at ``path``."""
        return cls.from_html(path.read_text(encoding="utf-8"))

    @property
    def text(self) -> str:
        """The whole document as visible text."""
        return _visible_text(self.html)

    @property
    def answer_key_text(self) -> str:
        """Visible text of the answer key, or the whole document if absent.

        Falling back to the whole document keeps a missing key from silently
        passing every answer check; the answers would have to appear somewhere.
        """
        match = _ANSWER_KEY.search(self.html)
        return _visible_text(match.group("body")) if match else self.text

    def contains(self, value: str) -> bool:
        """Whether ``value`` appears in the document's visible text."""
        return _visible_text(value) in self.text

    def key_contains(self, value: str) -> bool:
        """Whether ``value`` appears in the answer key's visible text."""
        return _visible_text(value) in self.answer_key_text
