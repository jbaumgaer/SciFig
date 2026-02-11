from typing import Optional
from src.models.layout.layout_protocols import FreeFormLayoutCapabilities # Import the new protocol

from src.models.layout.layout_config import FreeConfig, Gutters, LayoutConfig, Margins
from src.models.layout.layout_engine import LayoutEngine
from src.models.nodes import PlotNode
from src.shared.types import PlotID, Rect


class FreeLayoutEngine(LayoutEngine, FreeFormLayoutCapabilities): # Inherit from both
    """
    A layout engine for free-form mode.
    Plots maintain their explicit geometries. Provides methods for alignment and distribution.
    """

    def __init__(self):
        super().__init__()
        self.logger.info("FreeLayoutEngine initialized.")

    def calculate_geometries(
        self, plots: list[PlotNode], layout_config: LayoutConfig
    ) -> tuple[dict[PlotID, Rect], Optional[Margins], Optional[Gutters]]:
        """
        In free-form mode, plots retain their current geometries unless explicitly moved/resized.
        This method acts as a pass-through, returning the current geometries.
        It returns None for Margins and Gutters as they are not applicable in Free-Form layout.
        """
        if not isinstance(layout_config, FreeConfig):
            self.logger.error(
                f"FreeLayoutEngine received incompatible config: {type(layout_config).__name__}"
            )
            return {}, None, None  # Return None for Margins and Gutters

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

        geometries: dict[PlotID, list[float]] = {
            plot.id: list(plot.geometry) for plot in plots
        }

        if edge == "left":
            target_x = min(g[0] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[0] = target_x
        elif edge == "right":
            target_x_plus_w = max(g[0] + g[2] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[0] = target_x_plus_w - geom[2]
        elif edge == "top":
            target_y = min(g[1] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[1] = target_y
        elif edge == "bottom":
            target_y_plus_h = max(g[1] + g[3] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[1] = target_y_plus_h - geom[3]
        elif edge == "h_center":
            # Calculate the average center_x of all plots
            center_x = sum(geom[0] + geom[2] / 2 for geom in geometries.values()) / len(
                geometries
            )
            for plot_id, geom in geometries.items():
                geom[0] = center_x - geom[2] / 2
        elif edge == "v_center":
            # Calculate the average center_y of all plots
            center_y = sum(geom[1] + geom[3] / 2 for geom in geometries.values()) / len(
                geometries
            )
            for plot_id, geom in geometries.items():
                geom[1] = center_y - geom[3] / 2
        else:
            self.logger.warning(f"Unknown alignment edge: {edge}")
            return {}

        self.logger.info(f"Performed '{edge}' alignment for {len(plots)} plots.")
        return {plot_id: tuple(geom) for plot_id, geom in geometries.items()}

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

        geometries: dict[PlotID, list[float]] = {
            plot.id: list(plot.geometry) for plot in plots
        }

        plot_id_to_obj: dict[PlotID, PlotNode] = {plot.id: plot for plot in plots}

        if axis == "horizontal":
            sorted_plot_ids = sorted(
                geometries.keys(), key=lambda plot_id: geometries[plot_id][0]
            )
            min_coord = geometries[sorted_plot_ids[0]][0]
            max_coord = (
                geometries[sorted_plot_ids[-1]][0] + geometries[sorted_plot_ids[-1]][2]
            )
            total_width = sum(geometries[plot_id][2] for plot_id in sorted_plot_ids)

            if len(sorted_plot_ids) > 1:
                available_space = max_coord - min_coord - total_width
                if available_space < 0:
                    self.logger.warning(
                        "Plots are overlapping, distribution might not be visually ideal."
                    )
                    individual_width = (max_coord - min_coord) / len(sorted_plot_ids)
                    for i, plot_id in enumerate(sorted_plot_ids):
                        geometries[plot_id][0] = min_coord + i * individual_width
                        geometries[plot_id][2] = individual_width
                else:
                    spacing = available_space / (len(sorted_plot_ids) - 1)
                    current_x = min_coord
                    for plot_id in sorted_plot_ids:
                        geometries[plot_id][0] = current_x
                        current_x += geometries[plot_id][2] + spacing

        elif axis == "vertical":
            sorted_plot_ids = sorted(
                geometries.keys(), key=lambda plot_id: geometries[plot_id][1]
            )
            min_coord = geometries[sorted_plot_ids[0]][1]
            max_coord = (
                geometries[sorted_plot_ids[-1]][1] + geometries[sorted_plot_ids[-1]][3]
            )
            total_height = sum(geometries[plot_id][3] for plot_id in sorted_plot_ids)

            if len(sorted_plot_ids) > 1:
                available_space = max_coord - min_coord - total_height
                if available_space < 0:
                    self.logger.warning(
                        "Plots are overlapping, distribution might not be visually ideal."
                    )
                    individual_height = (max_coord - min_coord) / len(sorted_plot_ids)
                    for i, plot_id in enumerate(sorted_plot_ids):
                        geometries[plot_id][1] = min_coord + i * individual_height
                        geometries[plot_id][3] = individual_height
                else:
                    spacing = available_space / (len(sorted_plot_ids) - 1)
                    current_y = min_coord
                    for plot_id in sorted_plot_ids:
                        geometries[plot_id][1] = current_y
                        current_y += geometries[plot_id][3] + spacing
        else:
            self.logger.warning(f"Unknown distribution axis: {axis}")
            return {}

        self.logger.info(f"Performed '{axis}' distribution for {len(plots)} plots.")
        return {plot_id: tuple(geom) for plot_id, geom in geometries.items()}
