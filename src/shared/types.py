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

Layout: TypeAlias = Union[QVBoxLayout, QFormLayout, QHBoxLayout]
"""Type alias for a Qt Layout, which can be a QVBoxLayout, QFormLayout, or QHBoxLayout."""
