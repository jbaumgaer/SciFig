from typing import Optional

from src.models.layout.layout_config import Gutters, Margins
from src.models.layout.layout_engine import LayoutEngine
from src.models.layout.layout_protocols import (
    FreeFormLayoutCapabilities,  # Import the new protocol
)
from src.models.nodes import PlotNode
from src.shared.geometry import Rect
from src.shared.types import PlotID


class FreeLayoutEngine(LayoutEngine, FreeFormLayoutCapabilities):  # Inherit from both
    """
    A layout engine for free-form mode.
    Plots maintain their explicit geometries. Provides methods for alignment and distribution.
    """

    def __init__(self):
        super().__init__()
        self.logger.info("FreeLayoutEngine initialized.")

    def calculate_geometries(
        self,
        plots: list[PlotNode],
        figure_size_cm: tuple[float, float],
    ) -> tuple[dict[PlotID, Rect], Optional[Margins], Optional[Gutters]]:
        """
        In free-form mode, plots retain their current geometries unless explicitly moved/resized.
        This method acts as a pass-through, returning the current geometries.
        """
        geometries = {plot.id: plot.geometry for plot in plots}
        self.logger.debug(
            f"FreeLayoutEngine calculated geometries for {len(plots)} plots (pass-through)."
        )
        return geometries, None, None  # Return None for Margins and Gutters

    def perform_align(self, plots: list[PlotNode], edge: str) -> dict[PlotID, Rect]:
        """
        Calculates new geometries to align selected plots to a common edge.

        Args:
            plots: A list of PlotNode objects to align.
            edge: The edge to align to ("left", "right", "top", "bottom", "h_center", "v_center").

        Returns:
            A dictionary mapping each PlotNode to its new calculated geometry.
        """
        if not plots:
            return {}

        # Source of truth is the current Rect geometries
        geometries: dict[PlotID, Rect] = {plot.id: plot.geometry for plot in plots}

        if edge == "left":
            target_x = min(r.x for r in geometries.values())
            return {pid: Rect(target_x, r.y, r.width, r.height) for pid, r in geometries.items()}

        elif edge == "right":
            target_right = max(r.x + r.width for r in geometries.values())
            return {
                pid: Rect(target_right - r.width, r.y, r.width, r.height)
                for pid, r in geometries.items()
            }

        elif edge == "top":
            target_top = max(r.y + r.height for r in geometries.values())
            return {
                pid: Rect(r.x, target_top - r.height, r.width, r.height)
                for pid, r in geometries.items()
            }

        elif edge == "bottom":
            target_y = min(r.y for r in geometries.values())
            return {pid: Rect(r.x, target_y, r.width, r.height) for pid, r in geometries.items()}

        elif edge == "h_center":
            center_x = sum(r.x + r.width / 2 for r in geometries.values()) / len(geometries)
            return {
                pid: Rect(center_x - r.width / 2, r.y, r.width, r.height)
                for pid, r in geometries.items()
            }

        elif edge == "v_center":
            center_y = sum(r.y + r.height / 2 for r in geometries.values()) / len(geometries)
            return {
                pid: Rect(r.x, center_y - r.height / 2, r.width, r.height)
                for pid, r in geometries.items()
            }

        else:
            self.logger.warning(f"Unknown alignment edge: {edge}")
            return {}

    def perform_distribute(
        self, plots: list[PlotNode], axis: str
    ) -> dict[PlotID, Rect]:
        """
        Calculates new geometries to distribute selected plots evenly along an axis.

        Args:
            plots: A list of PlotNode objects to distribute.
            axis: The axis to distribute along ("horizontal", "vertical").

        Returns:
            A dictionary mapping each PlotNode to its new calculated geometry.
        """
        if len(plots) < 2:
            return {}

        # Work with a list of (id, Rect) for sorting
        items = [(plot.id, plot.geometry) for plot in plots]

        if axis == "horizontal":
            # Sort by x coordinate
            items.sort(key=lambda x: x[1].x)
            
            min_x = items[0][1].x
            max_right = max(r.x + r.width for pid, r in items)
            total_plot_width = sum(r.width for pid, r in items)
            
            spacing = (max_right - min_x - total_plot_width) / (len(items) - 1)
            
            new_geoms = {}
            current_x = min_x
            for pid, rect in items:
                new_geoms[pid] = Rect(current_x, rect.y, rect.width, rect.height)
                current_x += rect.width + spacing
            return new_geoms

        elif axis == "vertical":
            # Sort by y coordinate
            items.sort(key=lambda x: x[1].y)
            
            min_y = items[0][1].y
            max_top = max(r.y + r.height for pid, r in items)
            total_plot_height = sum(r.height for pid, r in items)
            
            spacing = (max_top - min_y - total_plot_height) / (len(items) - 1)
            
            new_geoms = {}
            current_y = min_y
            for pid, rect in items:
                new_geoms[pid] = Rect(rect.x, current_y, rect.width, rect.height)
                current_y += rect.height + spacing
            return new_geoms

        else:
            self.logger.warning(f"Unknown distribution axis: {axis}")
            return {}
