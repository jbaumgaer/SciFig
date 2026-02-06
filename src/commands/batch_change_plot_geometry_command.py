from typing import Dict, Tuple

from src.commands.base_command import BaseCommand
from src.models import ApplicationModel
from src.models.nodes import PlotNode
from src.layout_engine import Rect # Assuming Rect is defined here
from src.types import PlotID


class BatchChangePlotGeometryCommand(BaseCommand):
    """
    Command to change the geometries of multiple PlotNodes in a single operation,
    supporting undo/redo.
    """

    def __init__(self, model: ApplicationModel, new_geometries: Dict[PlotID, Rect], description: str):
        super().__init__(description)
        self._model = model
        self._new_geometries = new_geometries
        self._old_geometries: Dict[PlotID, Rect] = {}
        
        # Capture current geometries at the time of command creation
        for node in self._model.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.id in self._new_geometries:
                self._old_geometries[node.id] = node.geometry
        
        self.logger.debug(f"BatchChangePlotGeometryCommand initialized for {len(new_geometries)} plots. Captured {len(self._old_geometries)} old geometries.")

    def execute(self):
        """
        Applies the new geometries to the PlotNodes.
        The _old_geometries are already captured in __init__.
        """
        self.logger.info(f"Executing BatchChangePlotGeometryCommand: {self.description}")
        # No need to reset _old_geometries here, it was captured in __init__
        
        # Iterate over the plots for which we have new geometries
        for plot_id, new_rect in self._new_geometries.items():
            # Find the actual PlotNode object by its ID
            target_node = self._model.scene_root.find_node_by_id(plot_id) # Assuming find_node_by_id exists
            if isinstance(target_node, PlotNode):
                target_node.geometry = new_rect # Apply new geometry
                self.logger.debug(f"  PlotNode {target_node.name} (ID: {target_node.id}) geometry changed to {target_node.geometry}")
            else:
                self.logger.warning(f"  Could not find PlotNode with ID {plot_id} to apply new geometry.")
        
        self._model.modelChanged.emit() # Notify observers of changes
        self.logger.debug("BatchChangePlotGeometryCommand executed. Model updated.")


    def undo(self):
        """
        Reverts the geometries of the PlotNodes to their previous state.
        """
        self.logger.info(f"Undoing BatchChangePlotGeometryCommand: {self.description}")
        if not self._old_geometries:
            self.logger.warning("No old geometries to restore for undo operation.")
            return

        for node in self._model.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.id in self._old_geometries:
                node.geometry = self._old_geometries[node.id] # Restore old geometry
                self.logger.debug(f"  PlotNode {node.name} (ID: {node.id}) geometry reverted to {node.geometry}")
        
        self._model.modelChanged.emit() # Notify observers of changes
        self.logger.debug("BatchChangePlotGeometryCommand undone. Model reverted.")
