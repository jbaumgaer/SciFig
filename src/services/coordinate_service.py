import logging
from typing import Optional, Union

from src.shared.types import CoordinateSpace


class CoordinateService:
    """
    A stateless service providing a unified API for coordinate transformations
    and unit mapping. 
    Canonical Unit: Centimeters (cm).
    """

    CM_PER_INCH = 2.54

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def transform_value(
        cls,
        value: float,
        from_space: CoordinateSpace,
        to_space: CoordinateSpace,
        figure_size_cm: Optional[float] = None,
        canvas_size_px: Optional[float] = None,
        parent_size_cm: Optional[float] = None,
    ) -> float:
        """
        Transforms a single scalar value from one coordinate space to another.
        """
        if from_space == to_space:
            return value

        # 1. Special Case: Direct DISPLAY <-> FRACTIONAL_FIG (Pure geometric ratio)
        if (from_space == CoordinateSpace.DISPLAY_PX and to_space == CoordinateSpace.FRACTIONAL_FIG) or \
           (from_space == CoordinateSpace.FRACTIONAL_FIG and to_space == CoordinateSpace.DISPLAY_PX):
            if canvas_size_px is None:
                raise ValueError("canvas_size_px required for Display <-> Fractional mapping")
            
            if to_space == CoordinateSpace.FRACTIONAL_FIG:
                return value / canvas_size_px
            else:
                return value * canvas_size_px

        # 2. General Case: Convert source to PHYSICAL (Canonical CM)
        physical_cm = value
        if from_space == CoordinateSpace.FRACTIONAL_FIG:
            if figure_size_cm is None:
                raise ValueError("figure_size_cm required for FRACTIONAL_FIG transformation")
            physical_cm = value * figure_size_cm
        elif from_space == CoordinateSpace.FRACTIONAL_LOCAL:
            if parent_size_cm is None:
                raise ValueError("parent_size_cm required for FRACTIONAL_LOCAL transformation")
            physical_cm = value * parent_size_cm
        elif from_space == CoordinateSpace.DISPLAY_PX:
            if canvas_size_px is None or figure_size_cm is None:
                raise ValueError("canvas_size_px and figure_size_cm required for DISPLAY_PX transformation")
            physical_cm = (value / canvas_size_px) * figure_size_cm

        # 3. Convert PHYSICAL to target
        if to_space == CoordinateSpace.PHYSICAL:
            return physical_cm
        elif to_space == CoordinateSpace.FRACTIONAL_FIG:
            if figure_size_cm is None:
                raise ValueError("figure_size_cm required for transformation to FRACTIONAL_FIG")
            return physical_cm / figure_size_cm
        elif to_space == CoordinateSpace.FRACTIONAL_LOCAL:
            if parent_size_cm is None:
                raise ValueError("parent_size_cm required for transformation to FRACTIONAL_LOCAL")
            return physical_cm / parent_size_cm
        elif to_space == CoordinateSpace.DISPLAY_PX:
            if canvas_size_px is None or figure_size_cm is None:
                raise ValueError("canvas_size_px and figure_size_cm required for transformation to DISPLAY_PX")
            return (physical_cm / figure_size_cm) * canvas_size_px

        return physical_cm

    @classmethod
    def to_canonical(cls, value: float, from_unit: str) -> float:
        """Converts any physical unit to the internal CM standard."""
        unit = from_unit.lower().strip()
        if unit in ("inch", "inches", "in", "\""):
            return value * cls.CM_PER_INCH
        if unit in ("mm", "millimeter", "millimeters"):
            return value / 10.0
        if unit in ("pt", "point", "points"):
            return value * (cls.CM_PER_INCH / 72.0)
        return value

    @classmethod
    def from_canonical(cls, value_cm: float, to_unit: str) -> float:
        """Converts internal CM to a target physical unit."""
        unit = to_unit.lower().strip()
        if unit in ("inch", "inches", "in", "\""):
            return value_cm / cls.CM_PER_INCH
        if unit in ("mm", "millimeter", "millimeters"):
            return value_cm * 10.0
        if unit in ("pt", "point", "points"):
            return value_cm / (cls.CM_PER_INCH / 72.0)
        return value_cm

    @classmethod
    def format_for_display(cls, value_cm: float, unit: str, precision: int = 3) -> str:
        """Converts to target unit and returns a formatted string."""
        val = cls.from_canonical(value_cm, unit)
        return f"{val:.{precision}f}"
