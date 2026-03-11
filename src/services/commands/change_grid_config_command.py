from typing import Any, Optional

from src.models.nodes.grid_node import GridNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.property_service import PropertyService
from src.shared.events import Events


class ChangeGridConfigCommand(BaseCommand):
    """
    A specialized command to change properties of a GridNode (rows, cols, gutters, etc.)
    using a path-based system. Publishes GRID_COMPONENT_CHANGED to trigger layout sync
    """

    def __init__(
        self,
        grid_node: GridNode,
        path: str,
        new_value: Any,
        event_aggregator: EventAggregator,
        property_service: PropertyService,
        description: Optional[str] = None
    ):
        if not description:
            description = f"Change grid '{path}' to '{new_value}'"
        super().__init__(description, event_aggregator)
        self.grid_node = grid_node
        self.path = path
        self.new_value = new_value
        self._property_service = property_service
        self._expansion_map: dict[str, Any] = {}

    def execute(self):
        """Resolves path, captures old state, and applies change via PropertyService."""
        concrete_paths = self._property_service.resolve_concrete_paths(self.grid_node, self.path)

        for path in concrete_paths:
            old_val = self._property_service.get_value(self.grid_node, path)
            self._expansion_map[path] = old_val
            self._property_service.set_value(self.grid_node, path, self.new_value)

        self._finalize_change()

    def undo(self):
        """Restores the original values using the expansion map."""
        for path, old_value in self._expansion_map.items():
            self._property_service.set_value(self.grid_node, path, old_value)

        self._finalize_change(is_undo=True)

    def _finalize_change(self, is_undo: bool = False):
        """Triggers granular grid notifications and scene graph refresh."""
        # 1. Notify the LayoutManager specifically
        self._event_aggregator.publish(
            Events.GRID_COMPONENT_CHANGED,
            node_id=self.grid_node.id,
            path=self.path,
            new_value=self.new_value if not is_undo else None,
        )
        
        # 2. Trigger general scene graph refresh
        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
