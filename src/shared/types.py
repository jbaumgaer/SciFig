from typing import TypeAlias, Union, List, Any
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
)

@dataclass(frozen=True)
class Margins:
    """Represents figure margins (in figure fractions)."""
    top: float = 0.05
    bottom: float = 0.05
    left: float = 0.05
    right: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        return {"top": self.top, "bottom": self.bottom, "left": self.left, "right": self.right}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Margins":
        return Margins(
            top=data.get("top", 0.05),
            bottom=data.get("bottom", 0.05),
            left=data.get("left", 0.05),
            right=data.get("right", 0.05)
        )

PlotID: TypeAlias = str
"""
Type alias for a Plot ID, which is a unique string identifier for a PlotNode.
"""

Rect: TypeAlias = tuple[float, float, float, float]
"""
Type alias for a rectangle, represented as a tuple of four floats: (left, bottom, width, height).
"""

@dataclass(frozen=True)
class Gutters:
    """
    Represents spacing between subplots (in figure fractions).
    Can be single float for global spacing or lists for per-row/column spacing.
    """
    hspace: List[float] = field(default_factory=list)  # Horizontal space between rows
    wspace: List[float] = field(default_factory=list)  # Vertical space between columns

    def to_dict(self) -> dict[str, Any]:
        return {"hspace": self.hspace, "wspace": self.wspace}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Gutters":
        return Gutters(
            hspace=data.get("hspace", []),
            wspace=data.get("wspace", [])
        )

Layout: TypeAlias = Union[QVBoxLayout, QFormLayout, QHBoxLayout]
"""Type alias for a Qt Layout, which can be a QVBoxLayout, QFormLayout, or QHBoxLayout."""
