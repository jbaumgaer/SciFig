import logging
from typing import Optional

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import PlotProperties
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect


class AddPlotCommand(BaseCommand):
    """
    A command that adds a new PlotNode to the scene graph.
    Supports Undo by removing the added node.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        geometry: Rect,
        properties: Optional[PlotProperties] = None,
        parent_id: Optional[str] = None,
        node_name: str = "New Plot",
    ):
        description = f"Add new plot '{node_name}'"
        super().__init__(description, event_aggregator)
        self.model = model
        self.geometry = geometry
        self.properties = properties
        self.parent_id = parent_id or self.model.scene_root.id
        self.node_name = node_name
        
        # Created node instance
        self.node: Optional[PlotNode] = None

    def execute(self, publish: bool = True):
        """Creates and adds the PlotNode."""
        parent = self.model.scene_root.find_node_by_id(self.parent_id)
        if not parent:
            self.logger.error(f"AddPlotCommand: Parent {self.parent_id} not found.")
            return

        if not self.node:
            # First execution: create the node
            self.node = PlotNode(name=self.node_name)
            self.node.geometry = self.geometry
            self.node.plot_properties = self.properties
        
        parent.add_child(self.node)

        if publish:
            self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
            self._event_aggregator.publish(
                Events.NODE_ADDED_TO_SCENE,
                parent_id=parent.id,
                new_node_id=self.node.id,
                index=parent.children.index(self.node)
            )

    def undo(self, publish: bool = True):
        """Removes the added node."""
        if not self.node or not self.node.parent:
            return

        parent = self.node.parent
        parent.remove_child(self.node)

        if publish:
            self._event_aggregator.publish(
                Events.NODE_REMOVED_FROM_SCENE,
                parent_id=parent.id,
                removed_node_id=self.node.id
            )
            self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
