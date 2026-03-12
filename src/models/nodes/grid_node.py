import logging
from dataclasses import dataclass
from typing import Any, Optional

from src.models.layout.layout_config import Gutters, Margins
from src.models.nodes.grid_position import GridPosition
from src.models.nodes.scene_node import SceneNode
from src.shared.geometry import Rect


class GridNode(SceneNode):
    """
    A recursive container node that manages the layout of its children 
    using a strict grid policy.
    """

    def __init__(
        self,
        parent: Optional[SceneNode] = None,
        name: str = "Grid",
        id: Optional[str] = None,
        rows: int = 1,
        cols: int = 1,
    ):
        super().__init__(parent, name, id)
        self.logger = logging.getLogger(self.__class__.__name__)

        self._rows = rows
        self._cols = cols
        self.row_ratios: list[float] = [1.0] * rows
        self.col_ratios: list[float] = [1.0] * cols
        self.gutters = Gutters(
            hspace=[0.5] * max(0, rows - 1), 
            wspace=[0.5] * max(0, cols - 1)
        )
        self.margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)

        # Transient storage for the atomic M x N grid lattice.
        self.cell_geometries: list[list[Rect]] = []

    @property
    def rows(self) -> int:
        return self._rows

    @rows.setter
    def rows(self, value: int):
        """Sets rows and automatically synchronizes ratios and gutters."""
        if self._rows != value:
            self._rows = value
            # Auto-sync ratios
            if len(self.row_ratios) != value:
                self.row_ratios = [1.0] * value
            
            # Auto-sync gutters (hspace)
            num_hspace = max(0, value - 1)
            if len(self.gutters.hspace) != num_hspace:
                self.gutters = Gutters(
                    hspace=[0.5] * num_hspace,
                    wspace=self.gutters.wspace
                )
            self.logger.debug(f"GridNode {self.id}: Synchronized rows to {value}")

    @property
    def cols(self) -> int:
        return self._cols

    @cols.setter
    def cols(self, value: int):
        """Sets cols and automatically synchronizes ratios and gutters."""
        if self._cols != value:
            self._cols = value
            # Auto-sync ratios
            if len(self.col_ratios) != value:
                self.col_ratios = [1.0] * value
                
            # Auto-sync gutters (wspace)
            num_wspace = max(0, value - 1)
            if len(self.gutters.wspace) != num_wspace:
                self.gutters = Gutters(
                    hspace=self.gutters.hspace,
                    wspace=[0.5] * num_wspace
                )
            self.logger.debug(f"GridNode {self.id}: Synchronized cols to {value}")

    def to_dict(self) -> dict[str, Any]:
        """Serializes the GridNode and its layout parameters."""
        node_dict = super().to_dict()
        node_dict.update({
            "rows": self.rows,
            "cols": self.cols,
            "row_ratios": self.row_ratios,
            "col_ratios": self.col_ratios,
            "gutters": self.gutters.to_dict(),
            "margins": self.margins.to_dict(),
        })
        return node_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any], parent: Optional[SceneNode] = None) -> "GridNode":
        """Creates a GridNode from a dictionary."""
        node = cls(
            parent=parent,
            name=data.get("name", "Grid"),
            id=data.get("id"),
            rows=data.get("rows", 1),
            cols=data.get("cols", 1)
        )
        node.visible = data.get("visible", True)
        node.locked = data.get("locked", False)
        
        # Explicitly set ratios and configs if present, bypassing the auto-sync defaults
        if "row_ratios" in data:
            node.row_ratios = data["row_ratios"]
        if "col_ratios" in data:
            node.col_ratios = data["col_ratios"]
            
        gutters_data = data.get("gutters")
        if gutters_data:
            node.gutters = Gutters.from_dict(gutters_data)
            
        margins_data = data.get("margins")
        if margins_data:
            node.margins = Margins.from_dict(margins_data)
            
        return node
