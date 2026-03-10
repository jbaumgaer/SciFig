from enum import Enum, auto
from typing import TypeAlias, Union

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
)


class CoordinateSpace(Enum):
    """
    Defines the reference basis for a coordinate value.
    """
    PHYSICAL = auto()      # Absolute distance in Centimeters (The Model's Canonical Truth)
    FRACTIONAL_FIG = auto() # 0.0 to 1.0 relative to the total Figure size
    FRACTIONAL_LOCAL = auto() # 0.0 to 1.0 relative to the immediate parent (e.g., subplot spacing)
    DISPLAY_PX = auto()    # Device pixels relative to the Canvas viewport


PlotID: TypeAlias = str
"""
Type alias for a Plot ID, which is a unique string identifier for a PlotNode.
"""

Layout: TypeAlias = Union[QVBoxLayout, QFormLayout, QHBoxLayout]
"""Type alias for a Qt Layout, which can be a QVBoxLayout, QFormLayout, or QHBoxLayout."""
