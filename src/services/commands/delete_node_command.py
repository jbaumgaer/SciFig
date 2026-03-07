import logging
from typing import Optional

from src.models.application_model import ApplicationModel
from src.models.nodes.scene_node import SceneNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class DeleteNodeCommand(BaseCommand):
    """
    A command that removes a node from the scene graph.
    Supports Undo by re-inserting the node at its original position.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        node_id: str,
    ):
        description = f"Delete node {node_id}"
        super().__init__(description, event_aggregator)
        self.model = model
        self.node_id = node_id
        
        # Captured state for undo
        self.node: Optional[SceneNode] = None
        self.parent: Optional[SceneNode] = None
        self.original_index: int = -1

    def execute(self, publish: bool = True):
        """Removes the node from its parent."""
        self.node = self.model.scene_root.find_node_by_id(self.node_id)
        if not self.node:
            self.logger.error(f"DeleteNodeCommand: Node {self.node_id} not found.")
            return

        self.parent = self.node.parent
        if not self.parent:
            self.logger.error(f"DeleteNodeCommand: Node {self.node_id} has no parent (root cannot be deleted).")
            return

        self.original_index = self.parent.children.index(self.node)
        self.parent.remove_child(self.node)

        if publish:
            # Notify renderer to cleanup artists
            self._event_aggregator.publish(
                Events.NODE_REMOVED_FROM_SCENE, 
                parent_id=self.parent.id, 
                removed_node_id=self.node_id
            )
            self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self, publish: bool = True):
        """Restores the node to its original parent and index."""
        if not self.node or not self.parent or self.original_index == -1:
            self.logger.error("DeleteNodeCommand: Cannot undo, state not captured.")
            return

        self.parent.insert_child(self.original_index, self.node)

        if publish:
            self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
