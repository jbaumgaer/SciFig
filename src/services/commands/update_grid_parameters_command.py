import logging
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class UpdateGridParametersCommand(BaseCommand):
    """
    A consolidated command to update all structural parameters of a GridNode
    (rows, cols, ratios, margins, gutters) using a GridConfig proposal.
    Enforces SSoT by targeting the GridNode directly and triggering the 
    Layout domain via the standard handshake.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        new_grid_config: GridConfig,
        description: str = "Update Grid Parameters",
    ):
        super().__init__(description, event_aggregator)
        self._model = model
        self._new_config = new_grid_config
        self._backup_state: dict = {}

    def execute(self):
        self.logger.info(f"Executing: {self.description}")
        grid = self._model.get_active_grid()
        if not grid:
            self.logger.warning("UpdateGridParametersCommand: No active GridNode found.")
            return

        # 1. Capture backup for undo
        if not self._backup_state:
            self._backup_state = {
                "rows": grid.rows,
                "cols": grid.cols,
                "row_ratios": list(grid.row_ratios),
                "col_ratios": list(grid.col_ratios),
                "margins": grid.margins,
                "gutters": grid.gutters
            }

        # 2. Apply new parameters from the proposal
        # Note: GridNode setters handle the resizing of internal lists
        grid.rows = self._new_config.rows
        grid.cols = self._new_config.cols
        grid.row_ratios = list(self._new_config.row_ratios)
        grid.col_ratios = list(self._new_config.col_ratios)
        grid.margins = self._new_config.margins
        grid.gutters = self._new_config.gutters

        # 3. Finalize
        # The 'Zero-Logic Handshake': Just signal that layout intent has changed.
        self._event_aggregator.publish(Events.NODE_LAYOUT_CHANGED, node_id=grid.id)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self):
        self.logger.info(f"Undoing: {self.description}")
        grid = self._model.get_active_grid()
        if not grid or not self._backup_state:
            return

        # 1. Restore from backup
        grid.rows = self._backup_state["rows"]
        grid.cols = self._backup_state["cols"]
        grid.row_ratios = self._backup_state["row_ratios"]
        grid.col_ratios = self._backup_state["col_ratios"]
        grid.margins = self._backup_state["margins"]
        grid.gutters = self._backup_state["gutters"]

        # 2. Finalize
        self._event_aggregator.publish(Events.NODE_LAYOUT_CHANGED, node_id=grid.id)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
