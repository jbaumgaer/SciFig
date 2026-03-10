import logging
from typing import Any

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import (
    GridConfig,
    Margins,
    Gutters
)
from src.models.nodes.plot_node import PlotNode
from src.services.commands.apply_grid_command import ApplyGridCommand
from src.services.commands.batch_change_plot_geometry_command import (
    BatchChangePlotGeometryCommand,
)
from src.services.commands.change_grid_parameters_command import (
    ChangeGridParametersCommand,
)
from src.services.commands.command_manager import CommandManager
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.shared.geometry import Rect


class LayoutController:
    """
    Manages user interactions related to layout, translating UI events into
    commands that modify the ApplicationModel's layout state.

    This controller ensures that all user-initiated layout changes, including
    modifications to grid parameters, alignment, and distribution, are
    encapsulated as commands. These commands are then executed via the
    CommandManager, enabling a consistent and predictable undo/redo history.
    Even if a parameter change results in the same value (a "no-op" change),
    a command is still created and pushed to the undo stack to accurately
    reflect the user's interaction history and maintain undo/redo integrity.
    """

    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        layout_manager: LayoutManager,
        event_aggregator: EventAggregator,
    ):
        self.model = model
        self.command_manager = command_manager
        self._layout_manager = layout_manager
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutController initialized.")

        self._subscribe_to_events()

    def _subscribe_to_events(self):
        """Subscribes to layout-related request events."""
        self._event_aggregator.subscribe(
            Events.ALIGN_PLOTS_REQUESTED, self._handle_align_plots_request
        )
        self._event_aggregator.subscribe(
            Events.DISTRIBUTE_PLOTS_REQUESTED, self._handle_distribute_plots_request
        )
        self._event_aggregator.subscribe(
            Events.INFER_GRID_PARAMETERS_REQUESTED,
            self._handle_infer_grid_parameters_request,
        )
        self._event_aggregator.subscribe(
            Events.APPLY_GRID_REQUESTED, self._handle_apply_grid_request
        )
        self._event_aggregator.subscribe(
            Events.OPTIMIZE_LAYOUT_REQUESTED, self._handle_optimize_layout_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_GRID_PARAMETER_REQUESTED,
            self._handle_change_grid_parameter_request,
        )
        self._event_aggregator.subscribe(
            Events.BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED,
            self._on_batch_change_geometry_request,
        )

    def _handle_apply_grid_request(self, grid_config: GridConfig):
        """
        Applies a specific GridConfig to the model via an undoable command.
        """
        self.logger.info("LayoutController received request to apply grid.")
        command = ApplyGridCommand(
            model=self.model,
            event_aggregator=self._event_aggregator,
            layout_manager=self._layout_manager,
            new_grid_config=grid_config
        )
        self.command_manager.execute_command(command)
        self.logger.debug("Executed ApplyGridCommand.")

    def _on_batch_change_geometry_request(self, geometries: dict[str, Rect]):
        """
        Handles requests to change the geometries of multiple plots at once.
        Encapsulates the changes in a single undoable command.
        """
        if not geometries:
            return

        command = BatchChangePlotGeometryCommand(
            model=self.model,
            event_aggregator=self._event_aggregator,
            new_geometries=geometries,
            description="Move Plots"
        )
        self.command_manager.execute_command(command)
        self.logger.info(f"Executed BatchChangePlotGeometryCommand for {len(geometries)} plots.")

    def set_layout_mode(self, mode: LayoutMode):
        """
        Sets the UI selected layout mode in the LayoutManager.
        This does NOT immediately change the active layout in the application.
        """
        self.logger.info(
            f"LayoutController received request to set UI selected layout mode to: {mode.value}"
        )
        self._layout_manager.ui_selected_layout_mode = mode

    def toggle_layout_mode(self, checked: bool):
        """
        Toggles the UI selected layout mode between GRID and FREE_FORM based on the checked state
        of a UI element (e.g., a QAction).
        """
        if checked:
            self.set_layout_mode(LayoutMode.GRID)
            self.logger.info("UI selected layout mode toggled to GRID.")
        else:
            self.set_layout_mode(LayoutMode.FREE_FORM)
            self.logger.info("UI selected layout mode toggled to FREE_FORM.")

    def get_ui_selected_layout_mode(self) -> LayoutMode:
        """
        Returns the layout mode currently selected in the UI, as managed by the LayoutManager.
        This provides a public getter for the View components.
        """
        return self._layout_manager.ui_selected_layout_mode

    def _handle_align_plots_request(self, edge: str):
        """
        Aligns the currently selected plots based on an event request.
        """
        self.logger.info(
            f"LayoutController received request to align selected plots to: {edge}"
        )
        selected_plots = [
            node for node in self.model.selection if isinstance(node, PlotNode)
        ]
        if not selected_plots:
            self.logger.warning("No plots selected for alignment.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_align(selected_plots, edge)
        if new_geometries:
            # Wrap changes in a command for undo/redo
            command = BatchChangePlotGeometryCommand(
                self.model, self._event_aggregator, new_geometries, "Align Plots"
            )
            self.command_manager.execute_command(command)
            self.logger.debug(
                f"Executed BatchChangePlotGeometryCommand for aligning plots to {edge}."
            )
        else:
            self.logger.info("No geometry changes after alignment calculation.")

    def _handle_distribute_plots_request(self, axis: str):
        """
        Distributes the currently selected plots based on an event request.
        """
        self.logger.info(
            f"LayoutController received request to distribute selected plots along: {axis}"
        )
        selected_plots = [
            node for node in self.model.selection if isinstance(node, PlotNode)
        ]
        if not selected_plots:
            self.logger.warning("No plots selected for distribution.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_distribute(selected_plots, axis)
        if new_geometries:
            command = BatchChangePlotGeometryCommand(
                self.model, self._event_aggregator, new_geometries, "Distribute Plots"
            )
            self.command_manager.execute_command(command)
            self.logger.debug(
                f"Executed BatchChangePlotGeometryCommand for distributing plots along {axis}."
            )
        else:
            self.logger.info("No geometry changes after distribution calculation.")

    def snap_free_plots_to_grid_action(self):
        """
        Snaps selected free-form plots to a grid.
        This action is typically only available in FREE_FORM mode.
        It triggers a mode switch to GRID, which internally handles snapping.
        TODO: I think this method is now redundant since the "Optimize Layout" button in the UI
        directly calls the optimize_layout_action in the LayoutManager, which applies the grid layout
          without needing to switch modes. Consider removing this method if it's no longer used.
        """
        self.logger.info(
            "LayoutController received request to snap free plots to grid."
        )
        self._layout_manager.set_layout_mode(LayoutMode.GRID)
        self.logger.debug("Switched layout mode to GRID to snap plots.")

    def _handle_change_grid_parameter_request(
        self, param_name: str, value: Any
    ):
        """
        Handles changes from granular UI controls for grid layout parameters.
        Collects changes and dispatches a ChangeGridParametersCommand.
        """
        self.logger.debug(f"Grid layout param changed: {param_name} = {value}")

        if self._layout_manager.get_last_grid_config() is None:
            self.logger.warning(
                "on_grid_layout_param_changed called when _last_grid_config is None. This should not happen in GRID mode."
            )
            return

        current_grid_config: GridConfig = self._layout_manager.get_last_grid_config()
        self.logger.debug(
            f"on_grid_layout_param_changed: current_grid_config (from _last_grid_config) = {current_grid_config}"
        )
        old_grid_config = current_grid_config  # Store for undo

        # Initialize new_config_params with current values
        new_rows = current_grid_config.rows
        new_cols = current_grid_config.cols
        new_margins = current_grid_config.margins
        new_gutters = current_grid_config.gutters

        if param_name == "rows":
            try:
                new_rows = int(value)
                if new_rows <= 0:
                    raise ValueError("Rows must be positive")

            except ValueError:
                self.logger.warning(f"Invalid value for rows: {value}")
                return
        elif param_name == "cols":
            try:
                new_cols = int(value)
                if new_cols <= 0:
                    raise ValueError("Cols must be positive")

            except ValueError:
                self.logger.warning(f"Invalid value for cols: {value}")
                return
        elif param_name.startswith("margin_"):
            try:
                margin_value = float(value)
                if not (0.0 <= margin_value <= 5.0): # TODO: This makes no sense and should be in relative coordinates
                    raise ValueError("Margin must be between 0.0 and 5.0 cm")

                # Create a new Margins object for immutability
                temp_margins_dict = new_margins.to_dict()
                temp_margins_dict[param_name.replace("margin_", "")] = margin_value
                new_margins = Margins.from_dict(temp_margins_dict)

            except ValueError:
                self.logger.warning(f"Invalid value for {param_name}: {value}")
                return
        elif param_name == "hspace":
            try:
                # Interpret empty string as empty list for hspace
                new_hspace = (
                    [
                        float(x.strip()) for x in str(value).split(",") if x.strip()
                    ]  # Cast value to str for split
                    if value
                    else []
                )
                new_gutters = Gutters(
                    hspace=new_hspace, wspace=new_gutters.wspace
                )

            except ValueError:
                self.logger.warning(
                    f"Invalid value for hspace: {value}. Must be comma-separated numbers."
                )
                return
        elif param_name == "wspace":
            try:
                # Interpret empty string as empty list for wspace
                new_wspace = (
                    [
                        float(x.strip()) for x in str(value).split(",") if x.strip()
                    ]  # Cast value to str for split
                    if value
                    else []
                )
                new_gutters = Gutters(
                    hspace=new_gutters.hspace, wspace=new_wspace
                )

            except ValueError:
                self.logger.warning(
                    f"Invalid value for wspace: {value}. Must be comma-separated numbers."
                )
                return
        else:
            self.logger.warning(f"Unknown grid parameter: {param_name}")
            return

        new_grid_config = GridConfig(
            rows=new_rows,
            cols=new_cols,
            row_ratios=current_grid_config.row_ratios,
            col_ratios=current_grid_config.col_ratios,
            margins=new_margins,
            gutters=new_gutters,
        )
        self.logger.debug(
            f"Creating ChangeGridParametersCommand with new_grid_config margins: {new_grid_config.margins}"
        )
        self.logger.debug(
            f"Creating ChangeGridParametersCommand with new_grid_config gutters: {new_grid_config.gutters}"
        )
        command = ChangeGridParametersCommand(
            self.model,
            self._event_aggregator,
            self._layout_manager,
            old_grid_config,
            new_grid_config,
        )
        self.command_manager.execute_command(command)
        self.logger.debug(
            f"Executed ChangeGridParametersCommand for {param_name} change."
        )

    def _handle_infer_grid_parameters_request(self):
        """
        Triggers the LayoutManager to infer grid parameters from the current free-form plot positions.
        This action is typically called by a UI button.
        """
        self.logger.info("LayoutController received request to infer grid parameters.")
        self._layout_manager.infer_grid_parameters()

    def _handle_optimize_layout_request(self):
        """
        Triggers the LayoutManager to optimize the current grid layout.
        This action is encapsulated in a command for undo/redo support.
        """
        self.logger.info("LayoutController received request to optimize layout.")

        # 1. Get current (old) grid config
        old_grid_config = self._layout_manager.get_last_grid_config()

        # 2. Get optimized (new) grid config
        new_grid_config = self._layout_manager.get_optimized_grid_config()

        if new_grid_config:
            # 3. Encapsulate in command
            command = ChangeGridParametersCommand(
                self.model,
                self._event_aggregator,
                self._layout_manager,
                old_grid_config,
                new_grid_config,
                description="Optimize Layout",
            )
            self.command_manager.execute_command(command)
            self.logger.info("Executed ChangeGridParametersCommand for layout optimization.")
        else:
            self.logger.warning("Could not calculate optimized grid config. No command executed.")
