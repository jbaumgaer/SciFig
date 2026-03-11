from dataclasses import dataclass, field
from src.shared.constants import LayoutMode


@dataclass(frozen=True)
class Margins:
    """Represents figure margins in physical centimeters (cm)."""
    top: float
    bottom: float
    left: float
    right: float

    def to_dict(self) -> dict[str, float]:
        return {
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }

    @staticmethod
    def from_dict(data: dict[str, float]) -> "Margins":
        return Margins(
            top=data["top"],
            bottom=data["bottom"],
            left=data["left"],
            right=data["right"],
        )


@dataclass(frozen=True)
class Gutters:
    """Represents spacing between subplots in physical centimeters (cm).
    TODO: This makes no sense for a 1x1 grid
    """
    hspace: list[float]
    wspace: list[float]

    def to_dict(self) -> dict[str, list[float]]:
        return {"hspace": self.hspace, "wspace": self.wspace}

    @staticmethod
    def from_dict(data: dict[str, list[float]]) -> "Gutters":
        return Gutters(hspace=data["hspace"], wspace=data["wspace"])


@dataclass(frozen=True)
class GridConfig:
    """
    A Data Transfer Object (DTO) used to transport grid parameters 
    between the UI, Controllers, and the GridNode.
    """
    rows: int
    cols: int
    row_ratios: list[float]
    col_ratios: list[float]
    margins: Margins
    gutters: Gutters

    mode: LayoutMode = field(default=LayoutMode.GRID, init=False)

    def to_dict(self) -> dict[str, any]:
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
    def from_dict(data: dict[str, any]) -> "GridConfig":
        return GridConfig(
            rows=data["rows"],
            cols=data["cols"],
            row_ratios=data["row_ratios"],
            col_ratios=data["col_ratios"],
            margins=Margins.from_dict(data["margins"]),
            gutters=Gutters.from_dict(data["gutters"]),
        )


# Sentinel values
NO_MARGINS = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
NO_GUTTERS = Gutters(hspace=[], wspace=[])
