import logging
from typing import Optional, Union

from src.shared.types import CoordinateSpace
from src.shared.units import Dimension, Unit


class CoordinateService:
    """
    A stateless service providing a unified API for coordinate transformations
    and unit mapping. 
    Canonical Unit: Centimeters (cm).
    """

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
    def to_canonical(cls, value: float, from_unit: Union[str, Unit]) -> float:
        """Converts any physical unit to the internal CM standard via Dimension VO."""
        if isinstance(from_unit, str):
            # Map legacy string units to Unit Enum
            unit_map = {
                "inch": Unit.INCH, "inches": Unit.INCH, "in": Unit.INCH, "\"": Unit.INCH,
                "pt": Unit.PT, "point": Unit.PT, "points": Unit.PT,
                "cm": Unit.CM, "centimeter": Unit.CM,
                "mm": Unit.CM, # Handled below
            }
            unit = unit_map.get(from_unit.lower().strip(), Unit.CM)
            if from_unit.lower() == "mm":
                return value / 10.0
        else:
            unit = from_unit

        return Dimension(value, unit).cm

    @classmethod
    def from_canonical(cls, value_cm: float, to_unit: Union[str, Unit]) -> float:
        """Converts internal CM to a target physical unit via Dimension VO."""
        if isinstance(to_unit, str):
            unit_map = {
                "inch": Unit.INCH, "inches": Unit.INCH, "in": Unit.INCH, "\"": Unit.INCH,
                "pt": Unit.PT, "point": Unit.PT, "points": Unit.PT,
                "cm": Unit.CM,
                "mm": Unit.CM,
            }
            unit = unit_map.get(to_unit.lower().strip(), Unit.CM)
            if to_unit.lower() == "mm":
                return value_cm * 10.0
        else:
            unit = to_unit

        return Dimension(value_cm, Unit.CM).to_unit(unit)

    @classmethod
    def format_for_display(cls, value_cm: float, unit: Union[str, Unit], precision: int = 3) -> str:
        """Converts to target unit and returns a formatted string."""
        val = cls.from_canonical(value_cm, unit)
        return f"{val:.{precision}f}"
