from typing import Any, Optional

from src.models.nodes.plot_node import PlotNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.services.property_service import PropertyService
from src.shared.events import Events


class PropertyPathError(Exception):  # TODO: Errors should be bundled together
    """Raised when a property path is invalid for a given object."""
    pass


class ChangePlotPropertyCommand(BaseCommand):
    """
    A generic command to change properties of a SceneNode or its internal components
    using a path-based system. Delegates navigation logic to PropertyService.
    """

    def __init__(
        self,
        node: PlotNode,
        path: str,
        new_value: Any,
        event_aggregator: EventAggregator,
        property_service: PropertyService,
    ):
        description = f"Change '{path}' of node '{node.name}' to '{new_value}'"
        super().__init__(description, event_aggregator)
        self.node = node
        self.path = path
        self.new_value = new_value
        self._property_service = property_service
        # expansion_map: concrete_path -> old_value
        self._expansion_map: dict[str, Any] = {}

    def execute(self, publish: bool = True):
        """Resolves path, captures old state, and applies change via PropertyService."""
        root = self._get_root()
        concrete_paths = self._property_service.resolve_concrete_paths(root, self.path)

        if not concrete_paths:
            self.logger.error(
                f"PropertyPathError: Path '{self.path}' did not resolve to any attributes on {self.node}"
            )
            raise PropertyPathError(
                f"Path '{self.path}' did not resolve to any attributes on {self.node}"
            )

        self._expansion_map.clear()
        for path in concrete_paths:
            try:
                old_val = self._property_service.get_value(root, path)
                self._expansion_map[path] = old_val
                self._property_service.set_value(root, path, self.new_value)
            except (AttributeError, KeyError, IndexError, ValueError) as e:
                self.logger.error(
                    f"Failed to set value for concrete path '{path}': {e}"
                )
                continue

        # Increment version for render optimization
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            self.node.plot_properties._version += 1

        if publish:
            self._event_aggregator.publish(
                Events.PLOT_NODE_PROPERTY_CHANGED,
                node_id=self.node.id,
                path=self.path,
                new_value=self.new_value,
            )

    def undo(self, publish: bool = True):
        """Restores the original values using the expansion map."""
        root = self._get_root()
        for path, old_value in self._expansion_map.items():
            try:
                self._property_service.set_value(root, path, old_value)
            except (AttributeError, KeyError, IndexError, ValueError) as e:
                self.logger.error(
                    f"Failed to restore value for concrete path '{path}': {e}"
                )

        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            self.node.plot_properties._version += 1

        if publish:
            self._event_aggregator.publish(
                Events.PLOT_NODE_PROPERTY_CHANGED,
                node_id=self.node.id,
                path=self.path,
                new_value=None,  # Indicates a bulk or complex revert
            )

    def _get_root(self):
        """Determines if the path starts from the node or its plot properties."""
        first_part = self.path.split(".")[0]
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            if (
                hasattr(self.node.plot_properties, first_part)
                or first_part == "artists"
            ):
                return self.node.plot_properties
        return self.node
