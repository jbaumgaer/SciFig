from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GridPosition:
    """Defines the location and span of a node within a GridNode."""
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1

    def to_dict(self) -> dict[str, int]:
        return {
            "row": self.row,
            "col": self.col,
            "rowspan": self.rowspan,
            "colspan": self.colspan,
        }

    @staticmethod
    def from_dict(data: dict[str, int]) -> "GridPosition":
        return GridPosition(
            row=data["row"],
            col=data["col"],
            rowspan=data.get("rowspan", 1),
            colspan=data.get("colspan", 1),
        )
