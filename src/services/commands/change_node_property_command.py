from typing import Any, Optional

from src.models.nodes.scene_node import SceneNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.property_service import PropertyService
from src.shared.events import Events


class PropertyPathError(Exception):
    """Raised when a property path is invalid for a given object."""
    pass


class ChangeNodePropertyCommand(BaseCommand):
    """
    A generic command to change properties of any SceneNode (PlotNode, GridNode, etc.)
    using a path-based system. Publishes PLOT_NODE_PROPERTY_CHANGED for aesthetic sync.
    """

    def __init__(
        self,
        node: SceneNode,
        path: str,
        new_value: Any,
        event_aggregator: EventAggregator,
        property_service: PropertyService,
        description: Optional[str] = None
    ):
        if not description:
            description = f"Change '{path}' of node '{node.name}' to '{new_value}'"
        super().__init__(description, event_aggregator)
        self.node = node
        self.path = path
        self.new_value = new_value
        self._property_service = property_service
        self._expansion_map: dict[str, Any] = {}

    def execute(self, publish: bool = True):
        """Resolves path and applies functional change via PropertyService."""
        # Root calculation remains same
        first_part = self.path.split(".")[0]
        full_path = self.path
        is_plot_prop = False
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            if hasattr(self.node.plot_properties, first_part) or first_part == "artists":
                full_path = f"plot_properties.{self.path}"
                is_plot_prop = True

        concrete_paths = self._property_service.resolve_concrete_paths(self.node, full_path)
        if not concrete_paths:
            raise PropertyPathError(f"Path '{full_path}' not found on {self.node}")

        # Capture old values and apply new ones functionally
        self._expansion_map.clear()
        for path in concrete_paths:
            old_val = self._property_service.get_value(self.node, path)
            self._expansion_map[path] = old_val
            
            # Use return-based set_value
            new_root = self._property_service.set_value(self.node, path, self.new_value)
            # If the path was within plot_properties, re-assign the new tree to the node
            if is_plot_prop:
                self.node.plot_properties = new_root.plot_properties
            # (SceneNode itself is mutable for now, but its children properties are frozen)

        self._finalize_change(publish=publish)

    def undo(self, publish: bool = True):
        """Restores original values using expansion map and re-assignment."""
        first_part = self.path.split(".")[0]
        is_plot_prop = hasattr(self.node, "plot_properties") and (hasattr(self.node.plot_properties, first_part) or first_part == "artists")

        for path, old_value in self._expansion_map.items():
            new_root = self._property_service.set_value(self.node, path, old_value)
            if is_plot_prop:
                self.node.plot_properties = new_root.plot_properties

        self._finalize_change(publish=publish, is_undo=True)

    def _finalize_change(self, publish: bool = True, is_undo: bool = False):
        """Publishes domain-specific events based on the modified property path."""
        if not publish:
            return

        # 2. Determine Domain: Layout (Structural) vs Aesthetic (Ink)
        structural_paths = ("rows", "cols", "margins", "gutters", "grid_position", "geometry")
        first_part = self.path.split(".")[0]
        
        if first_part in structural_paths:
            # Domain: Layout (Structural intent)
            self._event_aggregator.publish(
                Events.NODE_LAYOUT_CHANGED,
                node_id=self.node.id
            )
        else:
            # Domain: Aesthetic (ink/style only)
            self._event_aggregator.publish(
                Events.PLOT_NODE_PROPERTY_CHANGED,
                node_id=self.node.id,
                path=self.path,
                new_value=self.new_value if not is_undo else None,
            )

    def _get_root(self):
        """Redirection logic for PlotProperties."""
        first_part = self.path.split(".")[0]
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            if hasattr(self.node.plot_properties, first_part) or first_part == "artists":
                return self.node.plot_properties
        return self.node
