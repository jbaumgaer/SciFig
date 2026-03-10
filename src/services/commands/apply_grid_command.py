import logging
from typing import Optional

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
from src.models.nodes.plot_node import PlotNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import PlotID


class ApplyGridCommand(BaseCommand):
    """
    A command that applies a new GridConfig to the model.
    Encapsulates the transition from FREE_FORM to GRID mode.
    Supports Undo by restoring the previous LayoutConfig and geometries.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        layout_manager: LayoutManager,
        new_grid_config: GridConfig,
        description: str = "Apply Grid Layout",
    ):
        super().__init__(description, event_aggregator)
        self._model = model
        self._layout_manager = layout_manager
        
        self._new_config = new_grid_config
        self._old_config = model.current_layout_config
        
        self._new_geometries: dict[PlotID, Rect] = {}
        self._old_geometries: dict[PlotID, Rect] = {}

        # 1. Calculate target geometries immediately to ensure command integrity
        all_plots = list(self._model.scene_root.all_descendants(of_type=PlotNode))
        if all_plots:
            self._new_geometries, _, _ = self._layout_manager._grid_engine.calculate_geometries(
                all_plots, self._new_config, self._model.figure_size
            )
            # 2. Capture old geometries for undo
            for plot in all_plots:
                self._old_geometries[plot.id] = plot.geometry

    def execute(self):
        self.logger.info(f"Executing: {self.description}")
        
        # 1. Update Model Config
        self._model.current_layout_config = self._new_config
        
        # 2. Update Node Geometries
        for pid, rect in self._new_geometries.items():
            node = self._model.scene_root.find_node_by_id(pid)
            if node:
                node.geometry = rect
        
        # 3. Notify System
        self._event_aggregator.publish(Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=self._new_config.mode)
        self._event_aggregator.publish(Events.LAYOUT_CONFIG_CHANGED, config=self._new_config)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self):
        self.logger.info(f"Undoing: {self.description}")
        
        # 1. Restore Config
        self._model.current_layout_config = self._old_config
        
        # 2. Restore Geometries
        for pid, rect in self._old_geometries.items():
            node = self._model.scene_root.find_node_by_id(pid)
            if node:
                node.geometry = rect
                
        # 3. Notify System
        self._event_aggregator.publish(Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=self._old_config.mode)
        self._event_aggregator.publish(Events.LAYOUT_CONFIG_CHANGED, config=self._old_config)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
