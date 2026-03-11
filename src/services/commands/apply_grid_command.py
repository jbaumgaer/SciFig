import logging
from typing import Optional

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode, GridPosition
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import PlotID


class ApplyGridCommand(BaseCommand):
    """
    A command that applies a new GridNode structure to the Scene Graph.
    Encapsulates the transition from FREE_FORM to GRID mode by moving 
    top-level siblings into a GridNode container.
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
        self._old_mode = model.layout_mode
        
        # Track original parents and positions for undo
        self._original_hierarchy: dict[str, dict] = {} 
        self._transient_grid_id: Optional[str] = None

    def execute(self):
        self.logger.info(f"Executing: {self.description}")
        
        # 1. Capture Current State for Undo
        all_plots = [n for n in self._model.scene_root.children if isinstance(n, PlotNode)]
        for plot in all_plots:
            self._original_hierarchy[plot.id] = {
                "parent": plot.parent,
                "grid_position": plot.grid_position,
                "geometry": plot.geometry
            }

        # 2. Create the Root GridNode
        grid = GridNode(
            parent=self._model.scene_root,
            rows=self._new_config.rows,
            cols=self._new_config.cols,
            name="Main Grid"
        )
        grid.margins = self._new_config.margins
        grid.gutters = self._new_config.gutters
        self._transient_grid_id = grid.id

        # 3. Move Plots into the Grid
        # Sort spatially (Top-to-Bottom, Left-to-Right)
        sorted_plots = sorted(all_plots, key=lambda p: (-p.geometry.y, p.geometry.x))
        
        idx = 0
        for r in range(grid.rows):
            for c in range(grid.cols):
                if idx >= len(sorted_plots):
                    break
                
                plot = sorted_plots[idx]
                plot.parent = grid
                plot.grid_position = GridPosition(row=r, col=c)
                idx += 1

        # 4. Finalize
        self._model.layout_mode = LayoutMode.GRID
        self._layout_manager.sync_layout()
        self._event_aggregator.publish(Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=LayoutMode.GRID)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self):
        self.logger.info(f"Undoing: {self.description}")
        
        # 1. Restore original parent and grid positions
        for node_id, state in self._original_hierarchy.items():
            node = self._model.scene_root.find_node_by_id(node_id)
            if node:
                node.parent = state["parent"]
                node.grid_position = state["grid_position"]
                node.geometry = state["geometry"]
        
        # 2. Remove the GridNode
        if self._transient_grid_id:
            grid = self._model.scene_root.find_node_by_id(self._transient_grid_id)
            if grid:
                self._model.scene_root.remove_child(grid)

        # 3. Restore Mode
        self._model.layout_mode = self._old_mode
        self._event_aggregator.publish(Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=self._old_mode)
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
