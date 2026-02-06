from typing import TypeAlias

PlotID: TypeAlias = str
"""
Type alias for a Plot ID, which is a unique string identifier for a PlotNode.
This improves type hint clarity and indicates that a string is not arbitrary,
but specifically refers to a plot identifier.
"""
