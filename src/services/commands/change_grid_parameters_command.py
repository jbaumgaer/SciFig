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
        layout_manager: LayoutManager,  # Pass layout_manager to interact with its config
        old_grid_config: GridConfig,
        new_grid_config: GridConfig,
        description: str = "Change Grid Parameters",
    ):
        super().__init__(description, event_aggregator)
        self.model = model
        self.layout_manager = layout_manager
        self.old_grid_config = old_grid_config
        self.new_grid_config = new_grid_config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(
            f"Initialized {description} with old config: {old_grid_config}, new config: {new_grid_config}"
        )

    def execute(self):
        self.logger.info(f"Executing command: {self.description}")
        # Update the layout manager's internal grid config
        # The layout manager will then calculate and apply the new geometries
        new_geometries = self.layout_manager.update_grid_config_and_apply(
            self.new_grid_config
        )
        self.logger.debug(
            f"ChangeGridParametersCommand.execute: After update_grid_config_and_apply, model.current_layout_config.rows: {self.model.current_layout_config.rows}"
        )
        if new_geometries:
            for plot_id, rect in new_geometries.items():
                plot_node = self.model.scene_root.find_node_by_id(plot_id)
                if plot_node:
                    plot_node.geometry = rect
            self._event_aggregator.publish(Events.LAYOUT_CONFIG_CHANGED)
            self.logger.debug(
                "New grid parameters applied and plot geometries updated."
            )
        else:
            self.logger.warning(
                "No new geometries were generated after applying new grid config."
            )

    def undo(self):
        self.logger.info(f"Undoing command: {self.description}")
        # Revert to the old grid config
        old_geometries = self.layout_manager.update_grid_config_and_apply(
            self.old_grid_config
        )

        if old_geometries:
            for plot_id, rect in old_geometries.items():
                plot_node = self.model.scene_root.find_node_by_id(plot_id)
                if plot_node:
                    plot_node.geometry = rect
            self._event_aggregator.publish(Events.LAYOUT_CONFIG_CHANGED)
            self.logger.debug(
                "Old grid parameters restored and plot geometries reverted."
            )
        else:
            self.logger.warning(
                "No old geometries were generated after reverting to old grid config."
            )
