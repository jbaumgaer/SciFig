import logging

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.shared.events import Events


class ChangeGridParametersCommand(BaseCommand):
    """
    A command to change the parameters of the GridConfig and apply the new layout.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        layout_manager: LayoutManager,
        old_grid_config: GridConfig,
        new_grid_config: GridConfig,
        description: str = "Change Grid Parameters",
    ):
        super().__init__(description, event_aggregator)
        self.model = model
        self.layout_manager = layout_manager
        self.old_grid_config = old_grid_config
        self.new_grid_config = new_grid_config
        self._backup_state: dict = {}

    def execute(self):
        self.logger.info(f"Executing: {self.description}")
        grid = self.model.get_active_grid()
        if not grid:
            self.logger.warning("ChangeGridParametersCommand: No active GridNode found.")
            return

        # 1. Capture backup for undo (if not already done)
        if not self._backup_state:
            self._backup_state = {
                "rows": grid.rows,
                "cols": grid.cols,
                "row_ratios": list(grid.row_ratios),
                "col_ratios": list(grid.col_ratios),
                "margins": grid.margins,
                "gutters": grid.gutters
            }

        # 2. Apply new parameters
        grid.rows = self.new_grid_config.rows
        grid.cols = self.new_grid_config.cols
        grid.row_ratios = list(self.new_grid_config.row_ratios)
        grid.col_ratios = list(self.new_grid_config.col_ratios)
        grid.margins = self.new_grid_config.margins
        grid.gutters = self.new_grid_config.gutters

        # 3. Finalize
        self.model.current_layout_config = self.new_grid_config
        self.layout_manager.sync_layout()
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self):
        self.logger.info(f"Undoing: {self.description}")
        grid = self.model.get_active_grid()
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
        self.model.current_layout_config = self.old_grid_config
        self.layout_manager.sync_layout()
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
