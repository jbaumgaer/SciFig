from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Final, Union

class Unit(Enum):
    """Supported physical and logical units for dimensions."""
    CM = "cm"
    INCH = "inch"
    PT = "pt"
    PX = "px"

    @property
    def conversion_to_cm(self) -> float:
        """Standard conversion factors to the canonical Centimeter (CM)."""
        factors: Final = {
            Unit.CM: 1.0,
            Unit.INCH: 2.54,
            Unit.PT: 2.54 / 72.0,
            Unit.PX: 2.54 / 96.0,  # Assuming standard 96 DPI for logical pixels
        }
        return factors[self]

@dataclass(frozen=True)
class Dimension:
    """
    An immutable Value Object representing a physical measurement.
    Encapsulates both the magnitude and the unit to prevent 'Primitive Obsession'.
    """
    value: float
    unit: Unit = Unit.CM

    def to_unit(self, target_unit: Unit) -> float:
        """Converts the dimension value to the target unit."""
        if self.unit == target_unit:
            return self.value
        
        # Convert to CM first (canonical)
        value_in_cm = self.value * self.unit.conversion_to_cm
        # Then to target
        return value_in_cm / target_unit.conversion_to_cm

    @property
    def cm(self) -> float:
        return self.to_unit(Unit.CM)

    @property
    def inch(self) -> float:
        return self.to_unit(Unit.INCH)

    @property
    def pt(self) -> float:
        return self.to_unit(Unit.PT)

    def __add__(self, other: Dimension) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        # Result inherits the unit of the left-hand side
        return Dimension(self.value + other.to_unit(self.unit), self.unit)

    def __sub__(self, other: Dimension) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(self.value - other.to_unit(self.unit), self.unit)

    def __mul__(self, other: float) -> Dimension:
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Dimension(self.value * other, self.unit)

    def __rmul__(self, other: float) -> Dimension:
        return self.__mul__(other)

    def __truediv__(self, other: Union[float, Dimension]) -> Union[float, Dimension]:
        if isinstance(other, (int, float)):
            return Dimension(self.value / other, self.unit)
        if isinstance(other, Dimension):
            # Dividing two dimensions results in a unitless ratio (float)
            return self.cm / other.cm
        return NotImplemented

    def __neg__(self) -> Dimension:
        return Dimension(-self.value, self.unit)

    def __abs__(self) -> Dimension:
        return Dimension(abs(self.value), self.unit)

    def __lt__(self, other: Dimension) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self.cm < other.cm

    def __le__(self, other: Dimension) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self.cm <= other.cm

    def __gt__(self, other: Dimension) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self.cm > other.cm

    def __ge__(self, other: Dimension) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self.cm >= other.cm

    def __repr__(self) -> str:
        return f"Dimension({self.value:.4f}, {self.unit.name})"
