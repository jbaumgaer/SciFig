from typing import Any, Optional, Union

from src.models.nodes.scene_node import SceneNode
from src.models.nodes.grid_position import GridPosition
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect


class MoveNodeCommand(BaseCommand):
    """
    A specialized command for structural layout shifts.
    Handles updates to 'grid_position' or free-form 'geometry' and 
    publishes NODE_LAYOUT_CHANGED to trigger the mathematical engine.
    """

    def __init__(
        self,
        node: SceneNode,
        new_value: Union[GridPosition, Rect, dict[str, Rect]],
        event_aggregator: EventAggregator,
        path: str = "grid_position",
        description: Optional[str] = None
    ):
        if not description:
            description = f"Move node '{node.name}' to '{new_value}'"
        super().__init__(description, event_aggregator)
        self.node = node
        self.path = path
        self.new_value = new_value
        self.old_value = getattr(node, path, None)

    def execute(self):
        """Applies the layout shift and signals the Layout Domain."""
        setattr(self.node, self.path, self.new_value)
        self._finalize()

    def undo(self):
        """Restores the original layout state."""
        setattr(self.node, self.path, self.old_value)
        self._finalize()

    def _finalize(self):
        """Publishes the domain-specific layout change event."""
        # Domain: Layout (Structural intent)
        # This signals the LayoutManager to run the math engine
        self._event_aggregator.publish(
            Events.NODE_LAYOUT_CHANGED,
            node_id=self.node.id
        )
