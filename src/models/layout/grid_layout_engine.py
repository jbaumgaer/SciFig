import logging
import math
from abc import ABC, abstractmethod
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox

from src.models.layout.layout_engine import LayoutEngine
from src.services.config_service import ConfigService
from src.models.layout.layout_config import GridConfig, LayoutConfig, Margins, Gutters
from src.models.nodes import PlotNode
from src.shared.types import PlotID, Rect


class GridLayoutEngine(LayoutEngine):
    """
    A layout engine for grid-based mode.
    Calculates geometries based on a GridConfig.
    """

    def __init__(self, config_service: ConfigService):
        super().__init__()
        self._config_service = config_service
        self.logger.info("GridLayoutEngine initialized.")


    def calculate_geometries(self, plots: list[PlotNode], layout_config: LayoutConfig, use_constrained_optimization: bool = False) -> tuple[dict[PlotID, Rect], Margins, Gutters]:
        """
        Calculates and returns the target (left, bottom, width, height) geometry for each PlotNode
        based on the provided layout_config and chosen layout strategy.

        Args:
            plots: A list of PlotNode objects to arrange.
            layout_config: The configuration object specific to this layout engine (expected GridConfig).
            use_constrained_optimization: If True, uses Matplotlib's constrained_layout for adaptive optimization.
                                          If False, uses a fixed grid layout respecting explicit margins/gutters.

        Returns:
            A tuple containing:
                - A dictionary mapping each PlotNode to its calculated geometry (Rect).
                - A Margins object representing the effective margins after layout.
                - A Gutters object representing the effective gutters after layout.
        """
        
        calculated_margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
        calculated_gutters = Gutters(hspace=[], wspace=[])
        if not isinstance(layout_config, GridConfig):
            self.logger.error(f"GridLayoutEngine received incompatible config: {type(layout_config).__name__}")
            return {}, calculated_margins, calculated_gutters
        if not plots:
            return {}, calculated_margins, calculated_gutters

        temp_fig = plt.figure(figsize=(8, 6)) # Create a temporary figure
        final_plot_geometries: dict[PlotID, Rect] = {}

        try:
            if use_constrained_optimization:
                _, final_plot_geometries, calculated_margins, calculated_gutters = self._apply_constrained_layout(temp_fig, plots, layout_config)
                self.logger.debug(f"GridLayoutEngine calculated geometries for {len(plots)} plots using constrained layout optimization.")
            else:
                _, final_plot_geometries, calculated_margins, calculated_gutters = self._apply_fixed_layout(temp_fig, plots, layout_config)
                self.logger.debug(f"GridLayoutEngine calculated geometries for {len(plots)} plots using fixed layout.")
        except Exception as e:
            self.logger.error(f"Error calculating geometries using {'constrained' if use_constrained_optimization else 'fixed'} layout: {e}")
            # Fallback to current config's margins/gutters if layout calculation fails
            calculated_margins = layout_config.margins
            calculated_gutters = layout_config.gutters
        finally:
            plt.close(temp_fig) # Ensure the temporary figure is closed

        return final_plot_geometries, calculated_margins, calculated_gutters
    

    def _apply_constrained_layout(self, figure: Figure, plot_nodes: list[PlotNode], grid_config: GridConfig) -> tuple[dict[PlotID, Axes], dict[PlotID, Rect], Margins, Gutters]:
        """
        Applies a grid layout to the given Matplotlib Figure using GridSpec and constrained_layout.
        It configures the layout based on GridConfig, triggers the layout calculation,
        and then returns the created Matplotlib Axes objects, their final calculated geometries,
        and the effective margins/gutters.

        Args:
            figure: The Matplotlib Figure object to apply the layout to.
            plot_nodes: A list of PlotNode objects to be arranged within the grid.
            grid_config: The GridConfig defining the desired layout.

        Returns:
            A tuple containing:
                - A dictionary mapping PlotID to the created Matplotlib Axes object.
                - A dictionary mapping PlotID to its final calculated geometry (Rect in figure fractions).
                - A Margins object (top, bottom, left, right in figure fraction).
                - A Gutters object (hspace, wspace in figure fraction).
        """
        self.logger.debug(f"Applying Matplotlib grid layout to figure with {len(plot_nodes)} plots.")

        if not isinstance(grid_config, GridConfig):
            self.logger.error(f"apply_matplotlib_grid_layout received incompatible config: {type(grid_config).__name__}")
            raise ValueError("Invalid layout_config type for Matplotlib grid layout.")

        num_plots = len(plot_nodes)
        rows = grid_config.rows if grid_config.rows > 0 else (math.ceil(num_plots**0.5) if num_plots > 0 else 1)
        cols = grid_config.cols if grid_config.cols > 0 else (math.ceil(num_plots / rows) if num_plots > 0 else 1)

        if num_plots == 0:
            return {}, {}, Margins(0.0, 0.0, 0.0, 0.0), Gutters([], [])
        if rows == 0 or cols == 0:
            self.logger.warning("Cannot create Matplotlib grid for 0 rows or columns.")
            raise ValueError("Rows or columns cannot be zero for Matplotlib grid layout.")

        row_ratios = grid_config.row_ratios if grid_config.row_ratios and len(grid_config.row_ratios) == rows else [1.0] * rows
        col_ratios = grid_config.col_ratios if grid_config.col_ratios and len(grid_config.col_ratios) == cols else [1.0] * cols

        gs_hspace_val = None
        if grid_config.gutters.hspace: # If the list is not empty
            if len(grid_config.gutters.hspace) == 1:
                gs_hspace_val = grid_config.gutters.hspace[0] # Use the single float value
            elif len(grid_config.gutters.hspace) == (rows - 1):
                gs_hspace_val = grid_config.gutters.hspace # Use the list
            else:
                self.logger.warning(f"Invalid hspace list length ({len(grid_config.gutters.hspace)}) for {rows} rows. Expected 1 or {rows-1}. Using default.")

        gs_wspace_val = None
        if grid_config.gutters.wspace: # If the list is not empty
            if len(grid_config.gutters.wspace) == 1:
                gs_wspace_val = grid_config.gutters.wspace[0] # Use the single float value
            elif len(grid_config.gutters.wspace) == (cols - 1):
                gs_wspace_val = grid_config.gutters.wspace # Use the list
            else:
                self.logger.warning(f"Invalid wspace list length ({len(grid_config.gutters.wspace)}) for {cols} cols. Expected 1 or {cols-1}. Using default.")
        self.logger.debug(f"[apply_matplotlib_grid_layout] gs_hspace_val: {gs_hspace_val}, Type: {type(gs_hspace_val)}")
        self.logger.debug(f"[apply_matplotlib_grid_layout] gs_wspace_val: {gs_wspace_val}, Type: {type(gs_wspace_val)}")

        gs = gridspec.GridSpec(
            nrows=rows,
            ncols=cols,
            figure=figure,
            height_ratios=row_ratios,
            width_ratios=col_ratios,
            hspace=gs_hspace_val,
            wspace=gs_wspace_val
        )

        figure.clear()

        mpl_axes_map: dict[PlotID, Axes] = {}
        sorted_plot_nodes = sorted(plot_nodes, key=lambda p: (-p.geometry[1], p.geometry[0]))

        plot_index = 0
        for r_idx in range(rows):
            for c_idx in range(cols):
                if plot_index >= num_plots:
                    break
                plot_node = sorted_plot_nodes[plot_index]
                ax = figure.add_subplot(gs[r_idx, c_idx])
                mpl_axes_map[plot_node.id] = ax
                plot_index += 1

        figure_width_in = figure.get_figwidth()
        figure_height_in = figure.get_figheight()

        constrained_w_space = self._config_service.get("layout.constrained_w_space", 0.02)
        constrained_h_space = self._config_service.get("layout.constrained_h_space", 0.02)

        figure.set_constrained_layout_pads(
            w_pad=grid_config.margins.left * figure_width_in,
            h_pad=grid_config.margins.bottom * figure_height_in,
            w_space=constrained_w_space * figure_width_in,
            h_space=constrained_h_space * figure_height_in,
        )
        figure.set_layout_engine('constrained')

        final_plot_geometries: dict[PlotID, Rect] = {}
        for plot_id, ax in mpl_axes_map.items():
            bbox = ax.get_position()
            final_plot_geometries[plot_id] = (bbox.x0, bbox.y0, bbox.width, bbox.height)

        calculated_margins = Margins(top=0.0, bottom=0.0, left=0.0, right=0.0)
        if all_axes_bboxes := [ax.get_position() for ax in mpl_axes_map.values()]:
            all_plots_bbox = Bbox.union(all_axes_bboxes)

            calculated_margins = Margins(
                top=1.0 - all_plots_bbox.y1,
                bottom=all_plots_bbox.y0,
                left=all_plots_bbox.x0,
                right=1.0 - all_plots_bbox.x1
            )

        # Ensure hspace and wspace are always lists
        if isinstance(gs_hspace_val, float):
            final_hspace = [gs_hspace_val]
        elif gs_hspace_val is not None:
            final_hspace = gs_hspace_val
        else:
            final_hspace = []

        if isinstance(gs_wspace_val, float):
            final_wspace = [gs_wspace_val]
        elif gs_wspace_val is not None:
            final_wspace = gs_wspace_val
        else:
            final_wspace = []
        calculated_gutters = Gutters(hspace=final_hspace, wspace=final_wspace)

        self.logger.info(f"Matplotlib constrained_layout applied. Final calculated margins: {calculated_margins}, Gutters: {calculated_gutters}")

        return mpl_axes_map, final_plot_geometries, calculated_margins, calculated_gutters


    def _apply_fixed_layout(self, figure: Figure, plot_nodes: list[PlotNode], grid_config: GridConfig) -> tuple[dict[PlotID, Axes], dict[PlotID, Rect], Margins, Gutters]:
        """
        Applies a grid layout to the given Matplotlib Figure using GridSpec with fixed fractional margins.
        This method avoids constrained_layout to provide strict adherence to user-defined margins.

        Args:
            figure: The Matplotlib Figure object to apply the layout to.
            plot_nodes: A list of PlotNode objects to be arranged within the grid.
            grid_config: The GridConfig defining the desired layout, with explicit margins and gutters.

        Returns:
            A tuple containing:
                - A dictionary mapping PlotID to the created Matplotlib Axes object.
                - A dictionary mapping PlotID to its final calculated geometry (Rect in figure fractions).
                - A Margins object (top, bottom, left, right in figure fraction) - these are the input margins.
                - A Gutters object (hspace, wspace in figure fraction) - these are the input gutters.
        """
        self.logger.debug(f"Applying Matplotlib fixed grid layout to figure with {len(plot_nodes)} plots.")

        if not isinstance(grid_config, GridConfig):
            self.logger.error(f"_apply_fixed_grid_layout received incompatible config: {type(grid_config).__name__}")
            raise ValueError("Invalid layout_config type for Matplotlib fixed grid layout.")

        num_plots = len(plot_nodes)
        rows = grid_config.rows if grid_config.rows > 0 else (math.ceil(num_plots**0.5) if num_plots > 0 else 1)
        cols = grid_config.cols if grid_config.cols > 0 else (math.ceil(num_plots / rows) if num_plots > 0 else 1)

        if num_plots == 0:
            return {}, {}, grid_config.margins, grid_config.gutters # Return input margins/gutters
        if rows == 0 or cols == 0:
            self.logger.warning("Cannot create Matplotlib grid for 0 rows or columns.")
            raise ValueError("Rows or columns cannot be zero for Matplotlib grid layout.")

        row_ratios = grid_config.row_ratios if grid_config.row_ratios and len(grid_config.row_ratios) == rows else [1.0] * rows
        col_ratios = grid_config.col_ratios if grid_config.col_ratios and len(grid_config.col_ratios) == cols else [1.0] * cols

        gs_hspace_val = None
        if grid_config.gutters.hspace:
            if len(grid_config.gutters.hspace) == 1:
                gs_hspace_val = grid_config.gutters.hspace[0]
            elif len(grid_config.gutters.hspace) == (rows - 1):
                gs_hspace_val = grid_config.gutters.hspace
            else:
                self.logger.warning(f"Invalid hspace list length ({len(grid_config.gutters.hspace)}) for {rows} rows. Expected 1 or {rows-1}. Using default.")

        gs_wspace_val = None
        if grid_config.gutters.wspace:
            if len(grid_config.gutters.wspace) == 1:
                gs_wspace_val = grid_config.gutters.wspace[0]
            elif len(grid_config.gutters.wspace) == (cols - 1):
                gs_wspace_val = grid_config.gutters.wspace
            else:
                self.logger.warning(f"Invalid wspace list length ({len(grid_config.gutters.wspace)}) for {cols} cols. Expected 1 or {cols-1}. Using default.")

        gs = gridspec.GridSpec(
            nrows=rows,
            ncols=cols,
            figure=figure,
            height_ratios=row_ratios,
            width_ratios=col_ratios,
            hspace=gs_hspace_val,
            wspace=gs_wspace_val,
            left=grid_config.margins.left,
            right=1.0 - grid_config.margins.right,
            top=1.0 - grid_config.margins.top,
            bottom=grid_config.margins.bottom
        )

        figure.clear()

        mpl_axes_map: dict[PlotID, Axes] = {}
        sorted_plot_nodes = sorted(plot_nodes, key=lambda p: (-p.geometry[1], p.geometry[0]))

        plot_index = 0
        for r_idx in range(rows):
            for c_idx in range(cols):
                if plot_index >= num_plots:
                    break
                plot_node = sorted_plot_nodes[plot_index]
                ax = figure.add_subplot(gs[r_idx, c_idx])
                mpl_axes_map[plot_node.id] = ax
                plot_index += 1

        # No figure.set_constrained_layout_pads or figure.set_layout_engine('constrained') here.
        # Margins are strictly defined by GridSpec parameters.

        final_plot_geometries: dict[PlotID, Rect] = {}
        for plot_id, ax in mpl_axes_map.items():
            bbox = ax.get_position()
            final_plot_geometries[plot_id] = (bbox.x0, bbox.y0, bbox.width, bbox.height)

        self.logger.info(f"Matplotlib fixed grid layout applied. Margins: {grid_config.margins}, Gutters: {grid_config.gutters}")

        return mpl_axes_map, final_plot_geometries, grid_config.margins, grid_config.gutters

