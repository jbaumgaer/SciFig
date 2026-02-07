import logging

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.models.nodes.plot_node import PlotNode
from src.models.layout.layout_config import GridConfig # Added import for isinstance check


class LayoutController(QObject):
    def __init__(self, model: ApplicationModel, command_manager: CommandManager, layout_manager: LayoutManager):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self._layout_manager = layout_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutController initialized.")

    def set_layout_mode(self, mode: LayoutMode):
        """
        Sets the application's layout mode via the LayoutManager.
        """
        self.logger.info(f"LayoutController received request to set layout mode to: {mode.value}")
        self._layout_manager.set_layout_mode(mode)

    def toggle_layout_mode(self, checked: bool):
        """
        Toggles the layout mode between GRID and FREE_FORM based on the checked state
        of a UI element (e.g., a QAction).
        """
        if checked:
            self.set_layout_mode(LayoutMode.GRID)
            self.logger.info("Layout mode toggled to GRID.")
        else:
            self.set_layout_mode(LayoutMode.FREE_FORM)
            self.logger.info("Layout mode toggled to FREE_FORM.")

    def align_selected_plots(self, edge: str):
        """
        Aligns the currently selected plots.
        """
        self.logger.info(f"LayoutController received request to align selected plots to: {edge}")
        selected_plots = [node for node in self.model.selection if isinstance(node, PlotNode)]
        if not selected_plots:
            self.logger.warning("No plots selected for alignment.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_align(selected_plots, edge)
        if new_geometries:
            # Wrap changes in a command for undo/redo
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, "Align Plots")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for aligning plots to {edge}.")
        else:
            self.logger.info("No geometry changes after alignment calculation.")

    def distribute_selected_plots(self, axis: str):
        """
        Distributes the currently selected plots.
        """
        self.logger.info(f"LayoutController received request to distribute selected plots along: {axis}")
        selected_plots = [node for node in self.model.selection if isinstance(node, PlotNode)]
        if not selected_plots:
            self.logger.warning("No plots selected for distribution.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_distribute(selected_plots, axis)
        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, "Distribute Plots")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for distributing plots along {axis}.")
        else:
            self.logger.info("No geometry changes after distribution calculation.")

    def apply_grid_layout_from_ui(self, rows: int, cols: int, margin: float, gutter: float):
        """
        Applies a new grid layout with specified rows, columns, margin, and gutter.
        This is typically called from the UI.
        """
        self.logger.info(f"LayoutController received request to apply grid layout from UI: {rows}x{cols}, Margin: {margin}, Gutter: {gutter}")
        # The actual logic for applying the layout is now in update_grid_parameters
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=rows, cols=cols, margin=margin, gutter=gutter)

        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, f"Apply {rows}x{cols} Grid Layout")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for {rows}x{cols} grid layout.")
        else:
            self.logger.info("No geometry changes after applying grid layout.")

    def snap_free_plots_to_grid_action(self):
        """
        Snaps selected free-form plots to a grid.
        This action is typically only available in FREE_FORM mode.
        It triggers a mode switch to GRID, which internally handles snapping.
        """
        self.logger.info("LayoutController received request to snap free plots to grid.")
        self._layout_manager.set_layout_mode(LayoutMode.GRID)
        self.logger.debug("Switched layout mode to GRID to snap plots.")

    def update_grid_parameters(self, rows: int, cols: int, margin: float, gutter: float):
        """
        Updates the grid layout parameters and applies the layout.
        This method is designed to be called by debounced UI signals.
        """
        self.logger.info(f"Updating grid parameters: Rows={rows}, Cols={cols}, Margin={margin}, Gutter={gutter}")

        # Call the layout manager's method directly with individual parameters
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=rows, cols=cols, margin=margin, gutter=gutter)

        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, f"Update Grid Layout ({rows}x{cols})")
            self.command_manager.execute_command(command)
            self.logger.debug("Executed BatchChangePlotGeometryCommand for updating grid layout with new parameters.")
        else:
            self.logger.info("No geometry changes after updating grid parameters.")

    def apply_default_grid_layout(self):
        """
        Applies a default grid layout to all plots in the scene.
        This is typically called when a new plot is added in GRID mode,
        or when the grid layout needs to be refreshed with default parameters.
        """
        self.logger.info("LayoutController received request to apply default grid layout.")
        all_plots = [node for node in self.model.scene_root.all_descendants() if isinstance(node, PlotNode)]
        if not all_plots:
            self.logger.warning("No plots in scene to apply default grid layout.")
            return

        # Call update_grid_parameters with None for rows/cols to trigger inference
        # and use default margin/gutter from config.
        # This implicitly uses the defaults from _create_default_grid_config
        # and infers rows/cols if needed.
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=None, cols=None)

        if new_geometries:
            # The description for the command should reflect that it's a default application
            current_grid_config = self._layout_manager.current_layout_config # Get the config after update
            if isinstance(current_grid_config, GridConfig): # Fix: import GridConfig
                description = f"Apply Default Grid Layout ({current_grid_config.rows}x{current_grid_config.cols})"
            else:
                description = "Apply Default Grid Layout (FreeForm fallback)"

            command = BatchChangePlotGeometryCommand(self.model, new_geometries, description)
            self.command_manager.execute_command(command)
            self.logger.debug("Executed BatchChangePlotGeometryCommand for default grid layout.")
        else:
            self.logger.info("No geometry changes after applying default grid layout.")