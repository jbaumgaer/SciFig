from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Union
import matplotlib.colors as mcolors

@dataclass(frozen=True)
class Color:
    """
    An immutable Value Object representing a color in RGBA space.
    Encapsulates color validation and multi-format conversion.
    """
    r: float
    g: float
    b: float
    a: float = 1.0

    def __post_init__(self):
        """Validates that all components are within the [0, 1] range."""
        for name, val in [("r", self.r), ("g", self.g), ("b", self.b), ("a", self.a)]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Color component '{name}' must be between 0 and 1, got {val}")

    @classmethod
    def from_mpl(cls, val: Any) -> Color:
        """
        Factory method to create a Color from any format Matplotlib accepts 
        (named colors, hex strings, RGB/RGBA tuples).
        """
        try:
            rgba = mcolors.to_rgba(val)
            return cls(r=rgba[0], g=rgba[1], b=rgba[2], a=rgba[3])
        except Exception as e:
            raise ValueError(f"Invalid Matplotlib color format: {val}. Error: {e}")

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        """Factory method to create a Color from a CSS-style hex string."""
        return cls.from_mpl(hex_str)

    def to_mpl(self) -> tuple[float, float, float, float]:
        """Returns the color as a standard Matplotlib-compatible RGBA tuple."""
        return (self.r, self.g, self.b, self.a)

    def to_hex(self) -> str:
        """Returns the color as a standard CSS-style hex string (#RRGGBBAA)."""
        return mcolors.to_hex(self.to_mpl(), keep_alpha=True)

    def with_alpha(self, alpha: float) -> Color:
        """Returns a new Color instance with the specified alpha value."""
        return Color(self.r, self.g, self.b, alpha)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return False
        # Use a small epsilon for float comparison to handle precision issues
        return all(abs(a - b) < 1e-7 for a, b in zip(self.to_mpl(), other.to_mpl()))

    def __repr__(self) -> str:
        return f"Color({self.r:.3f}, {self.g:.3f}, {self.b:.3f}, {self.a:.3f})"

    def __iter__(self):
        """Allows unpacking: r, g, b, a = color"""
        return iter(self.to_mpl())
