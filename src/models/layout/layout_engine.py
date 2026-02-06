import logging
import math
from abc import ABC, abstractmethod

from src.services.config_service import ConfigService
from src.models.layout.layout_config import FreeConfig, GridConfig, LayoutConfig
from src.models.nodes import PlotNode
from src.shared.types import PlotID, Rect


class LayoutEngine(ABC):
    """
    Abstract base class for all layout engines.
    Defines the interface for calculating plot geometries based on a layout configuration.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def calculate_geometries(self, plots: list[PlotNode], layout_config: LayoutConfig) -> dict[PlotID, Rect]:
        """
        Calculates and returns the target (left, bottom, width, height) geometry for each PlotNode.
        This method is stateless; all necessary parameters are passed via layout_config.

        Args:
            plots: A list of PlotNode objects to arrange.
            layout_config: The configuration object specific to this layout engine.

        Returns:
            A dictionary mapping each PlotNode to its calculated geometry.
        """
        pass


class FreeLayoutEngine(LayoutEngine):
    """
    A layout engine for free-form mode.
    Plots maintain their explicit geometries. Provides methods for alignment and distribution.
    """

    def __init__(self):
        super().__init__()
        self.logger.info("FreeLayoutEngine initialized.")

    def calculate_geometries(self, plots: list[PlotNode], layout_config: LayoutConfig) -> dict[PlotID, Rect]:
        """
        In free-form mode, plots retain their current geometries unless explicitly moved/resized.
        This method acts as a pass-through, returning the current geometries.
        """
        if not isinstance(layout_config, FreeConfig):
            self.logger.error(f"FreeLayoutEngine received incompatible config: {type(layout_config).__name__}")
            return {}

        geometries = {plot.id: plot.geometry for plot in plots}
        self.logger.debug(f"FreeLayoutEngine calculated geometries for {len(plots)} plots (pass-through).")
        return geometries

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

        geometries = {plot.id: list(plot.geometry) for plot in plots} # Use list for mutability

        if edge == "left":
            target_x = min(g[0] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[0] = target_x
        elif edge == "right":
            target_x_plus_w = max(g[0] + g[2] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[0] = target_x_plus_w - geom[2]
        elif edge == "top":
            target_y_plus_h = max(g[1] + g[3] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[1] = target_y_plus_h - geom[3]
        elif edge == "bottom":
            target_y = min(g[1] for g in geometries.values())
            for plot_id, geom in geometries.items():
                geom[1] = target_y
        elif edge == "h_center":
            # This part needs to map plot_ids back to plot objects to access their original geometries
            # This is not straightforward as we only have plot_id in geometries.items()
            # Re-evaluate the logic here.
            # For alignment, we need to iterate over the *original* plots to get their full geometry
            # and then update the specific plot.id's geometry in the geometries dict.
            # Let's assume for simplicity we still have access to original plot objects within the loop
            # This is where the PlotID change forces a re-think.

            # Revert geometries back to mapping PlotNode to list(geometry) for the loop
            geometries = {plot: list(plot.geometry) for plot in plots}
            center_x = sum(g[0] + g[2] / 2 for g in geometries.values()) / len(plots)
            for plot, geom in geometries.items():
                geom[0] = center_x - geom[2] / 2
            return {plot.id: tuple(geom) for plot, geom in geometries.items()} # Convert back to PlotID:Rect for return

        elif edge == "v_center":
            geometries = {plot: list(plot.geometry) for plot in plots}
            center_y = sum(g[1] + g[3] / 2 for g in geometries.values()) / len(plots)
            for plot, geom in geometries.items():
                geom[1] = center_y - geom[3] / 2
            return {plot.id: tuple(geom) for plot, geom in geometries.items()} # Convert back to PlotID:Rect for return
        else:
            self.logger.warning(f"Unknown alignment edge: {edge}")
            return {}

        self.logger.info(f"Performed '{edge}' alignment for {len(plots)} plots.")
        return {plot_id: tuple(geom) for plot_id, geom in geometries.items()}


    def perform_distribute(self, plots: list[PlotNode], axis: str) -> dict[PlotID, Rect]:
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

        geometries = {plot.id: list(plot.geometry) for plot in plots} # Use list for mutability

        # Need to sort plots by their actual position, not just their IDs
        # To do this, we temporarily map plot IDs back to plot objects for sorting,
        # then use the sorted IDs to update geometries.
        plot_id_to_obj = {plot.id: plot for plot in plots}

        # Sort plots by the relevant coordinate for consistent distribution
        if axis == "horizontal":
            sorted_plot_ids = sorted(geometries.keys(), key=lambda plot_id: geometries[plot_id][0])
            min_coord = geometries[sorted_plot_ids[0]][0]
            max_coord = geometries[sorted_plot_ids[-1]][0] + geometries[sorted_plot_ids[-1]][2]
            total_width = sum(geometries[plot_id][2] for plot_id in sorted_plot_ids)

            if len(sorted_plot_ids) > 1:
                available_space = max_coord - min_coord - total_width
                if available_space < 0: # Plots are overlapping
                    self.logger.warning("Plots are overlapping, distribution might not be visually ideal.")
                    # Fallback to equal spacing within min/max bounds if plots overlap
                    individual_width = (max_coord - min_coord) / len(sorted_plot_ids)
                    for i, plot_id in enumerate(sorted_plot_ids):
                        geometries[plot_id][0] = min_coord + i * individual_width
                        geometries[plot_id][2] = individual_width # Resize to fit
                else:
                    spacing = available_space / (len(sorted_plot_ids) - 1)
                    current_x = min_coord
                    for plot_id in sorted_plot_ids:
                        geometries[plot_id][0] = current_x
                        current_x += geometries[plot_id][2] + spacing

        elif axis == "vertical":
            sorted_plot_ids = sorted(geometries.keys(), key=lambda plot_id: geometries[plot_id][1])
            min_coord = geometries[sorted_plot_ids[0]][1]
            max_coord = geometries[sorted_plot_ids[-1]][1] + geometries[sorted_plot_ids[-1]][3]
            total_height = sum(geometries[plot_id][3] for plot_id in sorted_plot_ids)

            if len(sorted_plot_ids) > 1:
                available_space = max_coord - min_coord - total_height
                if available_space < 0: # Plots are overlapping
                    self.logger.warning("Plots are overlapping, distribution might not be visually ideal.")
                    individual_height = (max_coord - min_coord) / len(sorted_plot_ids)
                    for i, plot_id in enumerate(sorted_plot_ids):
                        geometries[plot_id][1] = min_coord + i * individual_height
                        geometries[plot_id][3] = individual_height # Resize to fit
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


class GridLayoutEngine(LayoutEngine):
    """
    A layout engine for grid-based mode.
    Calculates geometries based on a GridConfig.
    """

    def __init__(self, config_service: ConfigService):
        super().__init__()
        self._config_service = config_service
        self.logger.info("GridLayoutEngine initialized.")

    def calculate_geometries(self, plots: list[PlotNode], layout_config: LayoutConfig) -> dict[PlotID, Rect]:
        """
        Calculates and returns the target (left, bottom, width, height) geometry for each PlotNode
        based on the provided GridConfig.
        """
        self.logger.debug(f"GridLayoutEngine.calculate_geometries called with {len(plots)} plots.")
        self.logger.debug(f"Layout Config received: {layout_config}")
        if not isinstance(layout_config, GridConfig):
            self.logger.error(f"GridLayoutEngine received incompatible config: {type(layout_config).__name__}")
            return {}

        grid_config: GridConfig = layout_config
        num_plots = len(plots)

        # Determine actual rows and cols, allowing for dynamic calculation if not specified
        rows = grid_config.rows if grid_config.rows > 0 else (math.ceil(num_plots**0.5) if num_plots > 0 else 1)
        cols = grid_config.cols if grid_config.cols > 0 else (math.ceil(num_plots / rows) if num_plots > 0 else 1)

        if num_plots == 0:
            return {}
        if rows == 0 or cols == 0: # Should not happen with above logic, but safety check
            self.logger.warning("Cannot calculate grid for 0 rows or columns.")
            return {}

        # Use explicitly provided ratios or distribute equally
        row_ratios = grid_config.row_ratios if grid_config.row_ratios and len(grid_config.row_ratios) == rows else [1.0 / rows] * rows
        col_ratios = grid_config.col_ratios if grid_config.col_ratios and len(grid_config.col_ratios) == cols else [1.0 / cols] * cols

        # Normalize ratios to sum to 1.0 (if they don't already)
        sum_row_ratios = sum(row_ratios)
        if sum_row_ratios != 0:
            row_ratios = [r / sum_row_ratios for r in row_ratios]
        else: # Fallback to equal if sum is 0
            row_ratios = [1.0 / rows] * rows

        sum_col_ratios = sum(col_ratios)
        if sum_col_ratios != 0:
            col_ratios = [r / sum_col_ratios for r in col_ratios]
        else: # Fallback to equal if sum is 0
            col_ratios = [1.0 / cols] * cols

        margin = grid_config.margin
        gutter = grid_config.gutter

        # Calculate effective area for plots (excluding figure margins)
        effective_width = 1.0 - 2 * margin
        effective_height = 1.0 - 2 * margin

        # Calculate total gutter space
        total_gutter_width = (cols - 1) * gutter
        total_gutter_height = (rows - 1) * gutter

        # Calculate space available for plot cells after removing gutters
        plot_area_width = effective_width - total_gutter_width
        plot_area_height = effective_height - total_gutter_height

        if plot_area_width <= 0 or plot_area_height <= 0:
            self.logger.warning("Plot area is zero or negative after accounting for margins and gutters. Layout will be squeezed.")
            # Adjust effective width/height if gutters are too large
            if effective_width <= total_gutter_width: effective_width = total_gutter_width + 0.01
            if effective_height <= total_gutter_height: effective_height = total_gutter_height + 0.01
            plot_area_width = effective_width - total_gutter_width
            plot_area_height = effective_height - total_gutter_height
            if plot_area_width <= 0 or plot_area_height <= 0: # Still problematic
                self.logger.error("Could not resolve negative plot area. Returning empty geometries.")
                return {plot: (0.0, 0.0, 0.0, 0.0) for plot in plots}


        geometries: dict[PlotNode, Rect] = {}
        plot_index = 0

        # Sort plots for consistent assignment to grid cells (top-to-bottom, then left-to-right)
        # Matplotlib y-coords are bottom-up, so sort by y-desc, then x-asc
        sorted_plots = sorted(plots, key=lambda p: (-p.geometry[1], p.geometry[0]))


        for r_idx in range(rows):
            for c_idx in range(cols):
                if plot_index >= num_plots:
                    break

                plot = sorted_plots[plot_index]

                # Calculate width and height of the current cell based on ratios
                cell_width_ratio = col_ratios[c_idx]
                cell_height_ratio = row_ratios[rows - 1 - r_idx] # Matplotlib y-axis is bottom-up

                current_plot_width = plot_area_width * cell_width_ratio
                current_plot_height = plot_area_height * cell_height_ratio

                # Calculate left position
                left = margin + sum(col_ratios[i] * plot_area_width for i in range(c_idx)) + c_idx * gutter

                # Calculate bottom position
                # Cumulative height of rows above this one + margin + gutters
                bottom = margin + sum(row_ratios[i] * plot_area_height for i in range(rows - 1 - r_idx)) + (rows - 1 - r_idx) * gutter


                # Matplotlib's add_axes expects [left, bottom, width, height]
                geometries[plot.id] = (left, bottom, current_plot_width, current_plot_height)
                plot_index += 1
            if plot_index >= num_plots:
                break

        self.logger.info(f"GridLayoutEngine calculated geometries for {len(plots)} plots using GridConfig.")
        return geometries


    def snap_plots_to_grid(self, plots: list[PlotNode], current_grid_config: GridConfig) -> GridConfig:
        """
        Analyzes the current positions of plots (presumably in free-form) and infers
        a new GridConfig that would best represent them, or defaults to a simple grid.

        This implements the "Smart Re-Gridding with Heuristics" logic.

        Args:
            plots: The list of PlotNode objects to analyze.
            current_grid_config: The current GridConfig which might provide default rows/cols/ratios.

        Returns:
            A new GridConfig object.
        """
        self.logger.info(f"Snapping {len(plots)} plots to grid.")
        if not plots:
            return current_grid_config # No plots, return current config

        # --- Heuristic 1: Determine target rows/cols ---
        # If no explicit rows/cols in current_grid_config, infer from number of plots
        if current_grid_config.rows == 0 and current_grid_config.cols == 0:
            num_plots = len(plots)
            # Simple squarish grid heuristic
            inferred_rows = max(1, round(num_plots**0.5))
            inferred_cols = (num_plots + inferred_rows - 1) // inferred_rows
        elif current_grid_config.rows > 0 and current_grid_config.cols == 0:
            inferred_rows = current_grid_config.rows
            inferred_cols = (len(plots) + inferred_rows - 1) // inferred_rows
        elif current_grid_config.cols > 0 and current_grid_config.rows == 0:
            inferred_cols = current_grid_config.cols
            inferred_rows = (len(plots) + inferred_cols - 1) // inferred_cols
        else:
            inferred_rows = current_grid_config.rows
            inferred_cols = current_grid_config.cols

        # Ensure at least 1x1 grid
        inferred_rows = max(1, inferred_rows)
        inferred_cols = max(1, inferred_cols)

        # --- Heuristic 2: Sort plots for consistent assignment ---
        # Sort plots top-to-bottom, then left-to-right
        # Matplotlib y-coords are bottom-up, so sort by y-desc, then x-asc
        sorted_plots = sorted(plots, key=lambda p: (-p.geometry[1], p.geometry[0]))

        # --- Heuristic 3: Infer ratios (simple: equal distribution) ---
        # For simplicity, initially assume equal ratios.
        # More advanced: analyze clusters of plots to infer non-uniform ratios.
        inferred_row_ratios = [1.0 / inferred_rows] * inferred_rows
        inferred_col_ratios = [1.0 / inferred_cols] * inferred_cols

        # Create new GridConfig with inferred parameters
        new_grid_config = GridConfig(
            rows=inferred_rows,
            cols=inferred_cols,
            row_ratios=inferred_row_ratios,
            col_ratios=inferred_col_ratios,
            margin=current_grid_config.margin,
            gutter=current_grid_config.gutter
        )
        self.logger.debug(f"Inferred GridConfig: Rows={inferred_rows}, Cols={inferred_cols}")
        return new_grid_config
