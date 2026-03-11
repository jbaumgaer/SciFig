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

        self.rows = rows
        self.cols = cols
        self.row_ratios: list[float] = [1.0] * rows #TODO: DOn't have default values like this
        self.col_ratios: list[float] = [1.0] * cols
        self.gutters = Gutters(hspace=[0.5] * max(0, rows - 1), wspace=[0.5] * max(0, cols - 1))
        #TODO: Where is the 0.5 coming from? We shouldn't hardcode this value
        self.margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)

        # Transient storage for the atomic M x N grid lattice.
        # Populated by GridLayoutEngine; used by SelectionTool and OverlayRenderer.
        self.cell_geometries: list[list[Rect]] = []

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
        node.row_ratios = data.get("row_ratios", [1.0] * node.rows)
        node.col_ratios = data.get("col_ratios", [1.0] * node.cols)
        
        gutters_data = data.get("gutters")
        if gutters_data:
            node.gutters = Gutters.from_dict(gutters_data)
            
        margins_data = data.get("margins")
        if margins_data:
            node.margins = Margins.from_dict(margins_data)
            
        return node
