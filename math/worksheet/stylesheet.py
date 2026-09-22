"""Extract the design-token palette from the worksheet's embedded stylesheet.

The gates resolve their colour pairs through the tokens declared in ``:root``
rather than through literals of their own. Editing a token therefore re-points
every check at the new value, instead of letting the contract drift away from
what the document actually renders.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

from .colors import Color

__all__ = ["Stylesheet", "StylesheetError"]

_STYLE_BLOCK: Final = re.compile(r"<style\b[^>]*>(?P<css>.*?)</style>", re.DOTALL | re.I)
_ROOT_BLOCK: Final = re.compile(r":root\s*\{(?P<body>[^}]*)\}", re.DOTALL)
_TOKEN_DECL: Final = re.compile(r"--(?P<name>[\w-]+)\s*:\s*(?P<value>[^;]+);")
_HEX_LITERAL: Final = re.compile(r"#[0-9a-fA-F]{6}\b")
_FONT_SIZE_LITERAL: Final = re.compile(r"font-size\s*:\s*[0-9.]+px")
_COMMENT: Final = re.compile(r"/\*.*?\*/", re.DOTALL)


class StylesheetError(RuntimeError):
    """The document contained no stylesheet we could parse."""


@dataclass(frozen=True, slots=True)
class Stylesheet:
    """The parsed ``<style>`` block of a worksheet document."""

    css: str
    root_body: str
    palette: dict[str, Color]

    @classmethod
    def from_html(cls, html: str) -> Self:
        """Parse the first ``<style>`` block out of an HTML document.

        Raises:
            StylesheetError: If there is no stylesheet, no ``:root`` block, or
                no colour tokens in it.
        """
        match = _STYLE_BLOCK.search(html)
        if match is None:
            raise StylesheetError("no <style> block found")
        # str() rather than a cast: Match.group is typed `str | Any` because a
        # group may be optional, and these patterns make theirs mandatory.
        css = str(match.group("css"))

        root = _ROOT_BLOCK.search(css)
        if root is None:
            raise StylesheetError("no :root block found; design tokens are required")
        root_body = str(root.group("body"))

        palette: dict[str, Color] = {}
        for decl in _TOKEN_DECL.finditer(root_body):
            value = str(decl.group("value")).strip()
            # Only colour tokens take part in the contrast gate; the spacing and
            # type tokens share the block and are skipped here.
            if _HEX_LITERAL.fullmatch(value):
                palette[str(decl.group("name"))] = Color.from_hex(value)
        if not palette:
            raise StylesheetError(":root declared no colour tokens")
        return cls(css=css, root_body=root_body, palette=palette)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        """Parse the stylesheet out of the document at ``path``."""
        return cls.from_html(path.read_text(encoding="utf-8"))

    def resolve(self, ref: str) -> Color:
        """Resolve a token name (``"ink"``) or a literal (``"#3B2A18"``).

        Literals are allowed so the contract can cover illustration colours,
        which sit outside the token system by design.

        Raises:
            KeyError: If a token name is not declared in ``:root``.
        """
        if ref.startswith("#"):
            return Color.from_hex(ref)
        try:
            return self.palette[ref]
        except KeyError:
            raise KeyError(
                f"unknown colour token {ref!r}; declared: {sorted(self.palette)}"
            ) from None

    def untokenised_colors(self) -> list[str]:
        """Return hex literals used in rules instead of through a token.

        Colours inside ``:root`` are the definitions themselves, so they are
        excluded; flagging them would make a clean sheet impossible to write.
        """
        rules = self.css.replace(self.root_body, "")
        return sorted({m.group(0).upper() for m in _HEX_LITERAL.finditer(rules)})

    def hardcoded_font_sizes(self) -> list[str]:
        """Return ``font-size`` declarations written in px, not a type token."""
        return sorted({m.group(0) for m in _FONT_SIZE_LITERAL.finditer(self.css)})

    def rule_bodies(self, selector: str) -> list[str]:
        """Return the declaration blocks of every rule with this selector.

        Selectors are compared after stripping, so ``th, td { ... }`` is found
        by either name. Comments are removed first: a comment sitting directly
        above a rule otherwise gets absorbed into its selector.
        """
        bodies: list[str] = []
        for chunk in _COMMENT.sub("", self.css).split("}"):
            head, sep, body = chunk.partition("{")
            if not sep:
                continue
            if selector in (part.strip() for part in head.split(",")):
                bodies.append(body)
        return bodies

    def declares(self, selector: str, prop: str, token: str) -> bool:
        """Whether ``selector`` sets ``prop`` to ``var(--token)``.

        This is what binds the quality contract to the document: a check can
        name the rule it models, and drift becomes a build failure rather than
        a stale assertion that keeps passing.
        """
        pattern = re.compile(rf"\b{re.escape(prop)}\s*:[^;]*var\(--{re.escape(token)}\)")
        return any(pattern.search(body) for body in self.rule_bodies(selector))
