"""sRGB colour maths for the print-contrast gate.

The worksheet is printed in greyscale. A luminance-based greyscale conversion
preserves relative luminance, and WCAG contrast is defined purely in terms of
relative luminance, so a pair that clears its WCAG threshold in colour also
clears it on a monochrome laser. That equivalence is why this module computes
WCAG ratios instead of simulating a printer.
"""

import math
import re
from dataclasses import dataclass
from typing import Final, Self

__all__ = ["Color", "contrast_ratio"]

_HEX_PATTERN: Final = re.compile(r"\A#?(?P<digits>[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")

# WCAG 2.2 relative-luminance coefficients (Rec. 709 primaries).
_LUMA_R: Final = 0.2126
_LUMA_G: Final = 0.7152
_LUMA_B: Final = 0.0722

# Offset in the WCAG contrast formula, modelling veiling glare.
_GLARE: Final = 0.05

_CHANNEL_MAX: Final = 255


def _to_linear(channel: int) -> float:
    """Undo the sRGB transfer function for one 0-255 channel."""
    c = channel / _CHANNEL_MAX
    if c <= 0.04045:  # noqa: PLR2004 - the sRGB piecewise breakpoint
        return c / 12.92
    # math.pow rather than ** : the operator is typed as returning Any, because
    # a negative base with a fractional exponent yields a complex number.
    return math.pow((c + 0.055) / 1.055, 2.4)


@dataclass(frozen=True, slots=True)
class Color:
    """An opaque 8-bit sRGB colour."""

    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        """Reject channels outside 0-255.

        Raises:
            ValueError: If any channel is out of range.
        """
        for name, value in (
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
        ):
            if not 0 <= value <= _CHANNEL_MAX:
                raise ValueError(f"{name} must be in 0..{_CHANNEL_MAX}, got {value}")

    @classmethod
    def from_hex(cls, value: str) -> Self:
        """Parse ``#rgb`` or ``#rrggbb``; the leading ``#`` is optional.

        Raises:
            ValueError: If the string is not a hex colour.
        """
        match = _HEX_PATTERN.match(value.strip())
        if match is None:
            raise ValueError(f"not a hex colour: {value!r}")
        digits = match.group("digits")
        if len(digits) == 3:  # noqa: PLR2004 - shorthand form
            digits = "".join(d * 2 for d in digits)
        return cls(int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))

    @property
    def hex(self) -> str:
        """The colour as an uppercase ``#RRGGBB`` string."""
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}"

    @property
    def relative_luminance(self) -> float:
        """WCAG relative luminance, 0.0 (black) to 1.0 (white)."""
        return (
            _LUMA_R * _to_linear(self.red)
            + _LUMA_G * _to_linear(self.green)
            + _LUMA_B * _to_linear(self.blue)
        )

    @property
    def greyscale(self) -> int:
        """The 0-255 grey a luminance-preserving conversion would produce.

        Reported next to each ratio so a failure reads as ink on paper rather
        than as an abstract number.
        """
        value = _LUMA_R * self.red + _LUMA_G * self.green + _LUMA_B * self.blue
        return round(value)

    def __str__(self) -> str:
        """Render as the hex string."""
        return self.hex


def contrast_ratio(one: Color, other: Color) -> float:
    """Return the WCAG contrast ratio between two colours, from 1.0 to 21.0.

    Symmetric: argument order does not matter.
    """
    lighter, darker = sorted(
        (one.relative_luminance, other.relative_luminance), reverse=True
    )
    return (lighter + _GLARE) / (darker + _GLARE)
