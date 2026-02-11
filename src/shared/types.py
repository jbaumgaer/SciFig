from typing import TypeAlias, Union

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
)

PlotID: TypeAlias = str
"""
Type alias for a Plot ID, which is a unique string identifier for a PlotNode.
"""

Rect: TypeAlias = tuple[float, float, float, float]
"""
Type alias for a rectangle, represented as a tuple of four floats: (left, bottom, width, height).
"""

Layout: TypeAlias = Union[QVBoxLayout, QFormLayout, QHBoxLayout]
"""Type alias for a Qt Layout, which can be a QVBoxLayout, QFormLayout, or QHBoxLayout."""
