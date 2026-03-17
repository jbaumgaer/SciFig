import logging
from typing import Any

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode
from src.services.commands.apply_grid_command import ApplyGridLayoutCommand
from src.services.commands.batch_change_plot_geometry_command import (
    BatchChangePlotGeometryCommand,
)
from src.services.commands.change_grid_parameters_command import (
    ChangeGridParametersCommand,
)
from src.services.commands.command_manager import CommandManager
from src.services.event_aggregator import EventAggregator
from src.services.layout_service import LayoutService
from src.services.property_service import PropertyService
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
        layout_manager: LayoutService,
        event_aggregator: EventAggregator,
        property_service: PropertyService,
    ):
        self.model = model
        self.command_manager = command_manager
        self._layout_manager = layout_manager
        self._event_aggregator = event_aggregator
        self._property_service = property_service
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

    def _handle_apply_grid_request(self, values: dict[str, Any]):
        """
        Receives pre-parsed values from the UI Factory and applies a new 
        GridNode structure to the model via an undoable command.
        """
        self.logger.info("LayoutController received request to apply grid.")
        
        try:
            # 1. Get fallback values from a minimal proposal for anything missing
            fallback = self._layout_manager._create_minimal_grid_config()

            # 2. Construct the Proposal using values directly (already parsed by Factory)
            rows = values.get("rows", fallback.rows)
            cols = values.get("cols", fallback.cols)
            
            margins = Margins(
                top=values.get("margin_top", fallback.margins.top),
                bottom=values.get("margin_bottom", fallback.margins.bottom),
                left=values.get("margin_left", fallback.margins.left),
                right=values.get("margin_right", fallback.margins.right)
            )
            
            gutters = Gutters(
                hspace=values.get("hspace", fallback.gutters.hspace),
                wspace=values.get("wspace", fallback.gutters.wspace)
            )

            proposal = GridConfig(
                rows=rows,
                cols=cols,
                row_ratios=[1.0] * rows,
                col_ratios=[1.0] * cols,
                margins=margins,
                gutters=gutters
            )

            # 3. Execute Command
            command = ApplyGridLayoutCommand(
                model=self.model,
                event_aggregator=self._event_aggregator,
                new_grid_config=proposal
            )
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed ApplyGridLayoutCommand with proposal: {proposal}")

        except Exception as e:
            self.logger.error(f"LayoutController: Failed to parse Apply Grid request: {e}", exc_info=True)

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
        Harvests the current grid state into a proposal, modifies it, and 
        dispatches a single consolidated UpdateGridParametersCommand.
        """
        self.logger.debug(f"Grid layout param change requested: {param_name} = {value}")

        proposal = self._layout_manager.get_last_grid_config()
        if not proposal:
            self.logger.warning("LayoutController: No active grid to update.")
            return

        # 2. Modify Proposal via fluent helpers
        if param_name == "rows":
            proposal = proposal.with_rows(int(value))
        elif param_name == "cols":
            proposal = proposal.with_cols(int(value))
        elif param_name == "margin_top":
            proposal = proposal.with_margins(top=float(value))
        elif param_name == "margin_bottom":
            proposal = proposal.with_margins(bottom=float(value))
        elif param_name == "margin_left":
            proposal = proposal.with_margins(left=float(value))
        elif param_name == "margin_right":
            proposal = proposal.with_margins(right=float(value))
        elif param_name == "hspace":
            if isinstance(value, str):
                vals = [float(x.strip()) for x in value.split(",") if x.strip()]
            else:
                vals = value
            proposal = proposal.with_gutters(hspace=vals)
        elif param_name == "wspace":
            if isinstance(value, str):
                vals = [float(x.strip()) for x in value.split(",") if x.strip()]
            else:
                vals = value
            proposal = proposal.with_gutters(wspace=vals)
        else:
            self.logger.warning(f"Unknown grid parameter: {param_name}")
            return

        command = ChangeGridParametersCommand(
            model=self.model,
            event_aggregator=self._event_aggregator,
            new_grid_config=proposal,
            description=f"Change Grid {param_name}"
        )
        self.command_manager.execute_command(command)
        self.logger.debug(f"Executed UpdateGridParametersCommand for {param_name}.")

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

        # 1. Get optimized (new) grid config proposal
        new_grid_config = self._layout_manager.get_optimized_grid_config()

        if new_grid_config:
            # 2. Encapsulate in the consolidated command
            command = ChangeGridParametersCommand(
                self.model,
                self._event_aggregator,
                new_grid_config,
                description="Optimize Layout",
            )
            self.command_manager.execute_command(command)
            self.logger.info("Executed UpdateGridParametersCommand for layout optimization.")
        else:
            self.logger.warning("Could not calculate optimized grid config. No command executed.")
