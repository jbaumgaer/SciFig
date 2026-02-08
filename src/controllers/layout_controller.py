import logging

from PySide6.QtCore import QObject

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

import logging
from typing import Any, List, Optional
from PySide6.QtCore import QObject

from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.models.nodes.plot_node import PlotNode
from src.models.layout.layout_config import GridConfig, Margins # Added import for isinstance check and Margins
from src.services.commands.change_grid_parameters_command import ChangeGridParametersCommand # Import new command


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

    def snap_free_plots_to_grid_action(self):
        """
        Snaps selected free-form plots to a grid.
        This action is typically only available in FREE_FORM mode.
        It triggers a mode switch to GRID, which internally handles snapping.
        """
        self.logger.info("LayoutController received request to snap free plots to grid.")
        self._layout_manager.set_layout_mode(LayoutMode.GRID)
        self.logger.debug("Switched layout mode to GRID to snap plots.")

    def on_grid_layout_param_changed(self, param_name: str, value: Any):
        """
        Handles changes from granular UI controls for grid layout parameters.
        Collects changes and dispatches a ChangeGridParametersCommand.
        TODO: This is doing redundante work to some of the validators in other parts of the program because I'm also validating input here
        """
        self.logger.debug(f"Grid layout param changed: {param_name} = {value}")

        current_grid_config: GridConfig = self._layout_manager._last_grid_config
        old_grid_config = current_grid_config # Store for undo

        # Initialize new_config_params with current values
        new_rows = current_grid_config.rows
        new_cols = current_grid_config.cols
        new_margins = current_grid_config.margins
        new_gutters = current_grid_config.gutters

        changed = False

        if param_name == "rows":
            try:
                new_rows = int(value)
                if new_rows <= 0: raise ValueError("Rows must be positive")
                changed = new_rows != current_grid_config.rows
            except ValueError:
                self.logger.warning(f"Invalid value for rows: {value}")
                return
        elif param_name == "cols":
            try:
                new_cols = int(value)
                if new_cols <= 0: raise ValueError("Cols must be positive")
                changed = new_cols != current_grid_config.cols
            except ValueError:
                self.logger.warning(f"Invalid value for cols: {value}")
                return
        elif param_name.startswith("margin_"):
            try:
                margin_value = float(value)
                if not (0.0 <= margin_value <= 0.5): raise ValueError("Margin must be between 0.0 and 0.5")
                
                # Create a new Margins object for immutability
                temp_margins_dict = new_margins.to_dict()
                temp_margins_dict[param_name.replace("margin_", "")] = margin_value
                new_margins = Margins.from_dict(temp_margins_dict)
                changed = new_margins != current_grid_config.margins
            except ValueError:
                self.logger.warning(f"Invalid value for {param_name}: {value}")
                return
        elif param_name == "hspace":
            try:
                # Interpret empty string as empty list for hspace
                new_hspace = [float(x.strip()) for x in value.split(',') if x.strip()] if value else []
                new_gutters = new_gutters.from_dict({"hspace": new_hspace, "wspace": new_gutters.wspace})
                changed = new_gutters.hspace != current_grid_config.gutters.hspace
            except ValueError:
                self.logger.warning(f"Invalid value for hspace: {value}. Must be comma-separated numbers.")
                return
        elif param_name == "wspace":
            try:
                # Interpret empty string as empty list for wspace
                new_wspace = [float(x.strip()) for x in value.split(',') if x.strip()] if value else []
                new_gutters = new_gutters.from_dict({"hspace": new_gutters.hspace, "wspace": new_wspace})
                changed = new_gutters.wspace != current_grid_config.gutters.wspace
            except ValueError:
                self.logger.warning(f"Invalid value for wspace: {value}. Must be comma-separated numbers.")
                return
        else:
            self.logger.warning(f"Unknown grid parameter: {param_name}")
            return

        if changed:
            new_grid_config = GridConfig(
                rows=new_rows,
                cols=new_cols,
                row_ratios=current_grid_config.row_ratios, # Preserve for now
                col_ratios=current_grid_config.col_ratios, # Preserve for now
                margins=new_margins,
                gutters=new_gutters
            )
            self.logger.debug(f"Creating ChangeGridParametersCommand with new_grid_config margins: {new_grid_config.margins}")
            self.logger.debug(f"Creating ChangeGridParametersCommand with new_grid_config gutters: {new_grid_config.gutters}")
            command = ChangeGridParametersCommand(self.model, self._layout_manager, old_grid_config, new_grid_config)
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed ChangeGridParametersCommand for {param_name} change.")
        else:
            self.logger.debug(f"Parameter {param_name} did not change or value was invalid.")

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

        # Get the default grid config
        default_grid_config = self._layout_manager._create_default_grid_config()

        # If current mode is not GRID, setting it will apply the default config
        if self._layout_manager.layout_mode != LayoutMode.GRID:
            self._layout_manager.set_layout_mode(LayoutMode.GRID)
            # The set_layout_mode will implicitly apply the _last_grid_config (which is now default_grid_config)
        else:
            # If already in GRID mode, apply the default config explicitly
            current_grid_config = self._layout_manager._last_grid_config
            command = ChangeGridParametersCommand(self.model, self._layout_manager, current_grid_config, default_grid_config, "Apply Default Grid Layout")
            self.command_manager.execute_command(command)
            self.logger.debug("Executed ChangeGridParametersCommand for default grid layout.")