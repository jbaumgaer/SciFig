from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar, List
from src.shared.types import Margins, Gutters # Import new types

from src.shared.constants import LayoutMode

# Using a TypeVar for the static method's return type hint
T = TypeVar('T', bound='LayoutConfig')


class LayoutConfig(ABC):
    """
    Abstract base class for all layout configurations.
    Subclasses define specific parameters for different layout modes.
    """

    @property
    @abstractmethod
    def mode(self) -> LayoutMode:
        """
        The layout mode associated with this configuration.
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serializes the LayoutConfig to a dictionary."""
        pass

    @staticmethod
    def from_dict(data: dict[str, Any]) -> T: # Modified to use TypeVar
        """Deserializes a dictionary into a concrete LayoutConfig instance."""
        mode_str = data.get("mode")
        if not mode_str:
            raise ValueError("LayoutConfig data is missing 'mode' field.")

        mode = LayoutMode(mode_str) # Convert string to Enum

        if mode == LayoutMode.FREE_FORM:
            return FreeConfig.from_dict(data) # Delegate to concrete class
        elif mode == LayoutMode.GRID:
            return GridConfig.from_dict(data) # Delegate to concrete class
        else:
            raise ValueError(f"Unknown LayoutMode '{mode_str}' during deserialization.")


@dataclass(frozen=True) # frozen=True makes it immutable, good for configs
class FreeConfig(LayoutConfig):
    """
    Configuration for free-form layout mode.
    Minimal state, as plots manage their own geometries independently.
    """
    mode: LayoutMode = field(default=LayoutMode.FREE_FORM, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode.value}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "FreeConfig":
        return FreeConfig() # No additional state to deserialize


@dataclass(frozen=True) # frozen=True makes it immutable, good for configs
class GridConfig(LayoutConfig):
    """
    Configuration for grid-based layout mode.
    TODO: Have these in a config file
    """
    rows: int = 2
    cols: int = 2
    row_ratios: list[float] = field(default_factory=list) # Empty means equal distribution
    col_ratios: List[float] = field(default_factory=list) # Empty means equal distribution
    margins: Margins = field(default_factory=Margins)
    gutters: Gutters = field(default_factory=Gutters)


    mode: LayoutMode = field(default=LayoutMode.GRID, init=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "rows": self.rows,
            "cols": self.cols,
            "row_ratios": self.row_ratios,
            "col_ratios": self.col_ratios,
            "margins": self.margins.to_dict(),
            "gutters": self.gutters.to_dict(),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "GridConfig":
        return GridConfig(
            rows=data.get("rows", 2),
            cols=data.get("cols", 2),
            row_ratios=data.get("row_ratios", []),
            col_ratios=data.get("col_ratios", []),
            margins=Margins.from_dict(data.get("margins", {})),
            gutters=Gutters.from_dict(data.get("gutters", {})),
        )
