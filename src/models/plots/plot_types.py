from enum import Enum


class PlotType(str, Enum):
    """
    An enumeration for the different types of plots available.
    Inherits from str to be easily serializable.
    """

    LINE = "line"
    SCATTER = "scatter"
