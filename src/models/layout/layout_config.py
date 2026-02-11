from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar

from src.shared.constants import LayoutMode

# Using a TypeVar for the static method's return type hint
T = TypeVar("T", bound="LayoutConfig")


@dataclass(frozen=True)
class Margins:
    """Represents figure margins (in figure fractions)."""

    top: float
    bottom: float
    left: float
    right: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Margins":
        return Margins(
            top=data["top"],
            bottom=data["bottom"],
            left=data["left"],
            right=data["right"],
        )


@dataclass(frozen=True)
class Gutters:
    """
    Represents spacing between subplots (in figure fractions).
    Can be single float for global spacing or lists for per-row/column spacing.
    TODO: This makes no sense for a 1x1 grid
    """

    hspace: list[float]
    wspace: list[float]

    def to_dict(self) -> dict[str, Any]:
        return {"hspace": self.hspace, "wspace": self.wspace}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Gutters":
        return Gutters(hspace=data["hspace"], wspace=data["wspace"])


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
    def from_dict(data: dict[str, Any]) -> T:  # Modified to use TypeVar
        """Deserializes a dictionary into a concrete LayoutConfig instance."""
        mode_str = data.get("mode")
        if not mode_str:
            raise ValueError("LayoutConfig data is missing 'mode' field.")

        mode = LayoutMode(mode_str)  # Convert string to Enum

        if mode == LayoutMode.FREE_FORM:
            return FreeConfig.from_dict(data)  # Delegate to concrete class
        elif mode == LayoutMode.GRID:
            return GridConfig.from_dict(data)  # Delegate to concrete class
        else:
            raise ValueError(f"Unknown LayoutMode '{mode_str}' during deserialization.")


@dataclass(frozen=True)  # frozen=True makes it immutable, good for configs
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
        return FreeConfig()  # No additional state to deserialize


@dataclass(frozen=True)  # frozen=True makes it immutable, good for configs
class GridConfig(LayoutConfig):
    """
    Configuration for grid-based layout mode.
    """

    rows: int
    cols: int
    row_ratios: list[float]
    col_ratios: list[float]
    margins: Margins
    gutters: Gutters

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
            rows=data["rows"],
            cols=data["cols"],
            row_ratios=data["row_ratios"],
            col_ratios=data["col_ratios"],
            margins=Margins.from_dict(data["margins"]),
            gutters=Gutters.from_dict(data["gutters"]),
        )


# Sentinel values for Margins and Gutters when they are not applicable or empty
NO_MARGINS = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
NO_GUTTERS = Gutters(hspace=[], wspace=[])
