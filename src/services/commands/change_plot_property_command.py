from typing import Any

from src.models.nodes.plot_node import PlotNode
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class PropertyPathError(Exception):  # TODO: Errors should be bundled together
    """Raised when a property path is invalid for a given object."""

    pass


class ChangePlotPropertyCommand(BaseCommand):
    """
    A generic command to change properties of a SceneNode or its internal components
    using a path-based system (e.g., 'coords.xaxis.label.text').
    Supports wildcards (e.g., 'coords.spines.*.visible') for bulk updates.
    """

    def __init__(
        self,
        node: PlotNode,
        path: str,
        new_value: Any,
        event_aggregator: EventAggregator,
    ):
        description = f"Change '{path}' of node '{node.name}' to '{new_value}'"
        super().__init__(description, event_aggregator)
        self.node = node
        self.path = path
        self.new_value = new_value
        # expansion_map: concrete_path -> old_value
        self._expansion_map: dict[str, Any] = {}

    def execute(self):
        """Resolves the path (expanding wildcards), captures old state, and applies the change."""
        root = self._get_root()
        concrete_paths = self._resolve_concrete_paths(root, self.path)

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
                old_val = self._get_value_by_path(root, path)
                self._expansion_map[path] = old_val
                self._set_value_by_path(root, path, self.new_value)
            except (AttributeError, KeyError, IndexError, ValueError) as e:
                self.logger.error(
                    f"Failed to set value for concrete path '{path}': {e}"
                )
                continue

        # Increment version for render optimization if we modified plot properties
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            self.node.plot_properties._version += 1

        self._event_aggregator.publish(
            Events.PLOT_COMPONENT_CHANGED,
            node_id=self.node.id,
            path=self.path,
            new_value=self.new_value,
        )

    def undo(self):
        """Restores the original values using the expansion map."""
        root = self._get_root()
        for path, old_value in self._expansion_map.items():
            try:
                self._set_value_by_path(root, path, old_value)
            except (AttributeError, KeyError, IndexError, ValueError) as e:
                self.logger.error(
                    f"Failed to restore value for concrete path '{path}': {e}"
                )

        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            self.node.plot_properties._version += 1

        # We publish the path change with the last restored value (if multiple, we use the original intent path)
        self._event_aggregator.publish(
            Events.PLOT_COMPONENT_CHANGED,
            node_id=self.node.id,
            path=self.path,
            new_value=None,  # Indicates a bulk or complex revert
        )

    def _get_root(self):
        """Determines if the path starts from the node or its plot properties."""
        first_part = self.path.split(".")[0]
        if hasattr(self.node, "plot_properties") and self.node.plot_properties:
            # Check if it's a known root attribute of PlotProperties
            if (
                hasattr(self.node.plot_properties, first_part)
                or first_part == "artists"
            ):
                return self.node.plot_properties
        return self.node

    def _resolve_concrete_paths(self, obj: Any, path: str) -> list[str]:
        """Expands wildcards into concrete paths."""
        parts = path.split(".")
        return list(self._recursive_resolve(obj, parts, ""))

    def _recursive_resolve(self, obj: Any, parts: list[str], current_path: str):
        if not parts:
            yield current_path.strip(".")
            return

        part = parts[0]
        remaining = parts[1:]

        if part == "*":
            # Expand dictionary keys or list indices
            if isinstance(obj, dict):
                for key in obj.keys():
                    yield from self._recursive_resolve(
                        obj[key], remaining, f"{current_path}.{key}"
                    )
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    yield from self._recursive_resolve(
                        obj[i], remaining, f"{current_path}.{i}"
                    )
        else:
            # Handle normal attribute or dict access
            try:
                if isinstance(obj, dict) and part in obj:
                    yield from self._recursive_resolve(
                        obj[part], remaining, f"{current_path}.{part}"
                    )
                elif isinstance(obj, list):
                    idx = int(part)
                    if 0 <= idx < len(obj):
                        yield from self._recursive_resolve(
                            obj[idx], remaining, f"{current_path}.{part}"
                        )
                elif hasattr(obj, part):
                    yield from self._recursive_resolve(
                        getattr(obj, part), remaining, f"{current_path}.{part}"
                    )
            except (ValueError, TypeError):
                pass

    def _get_value_by_path(self, obj: Any, path: str) -> Any:
        """Helper to navigate a concrete path and return the value."""
        curr = obj
        for part in path.split("."):
            if isinstance(curr, dict):
                curr = curr[part]
            elif isinstance(curr, list):
                curr = curr[int(part)]
            else:
                curr = getattr(curr, part)
        return curr

    def _set_value_by_path(self, obj: Any, path: str, value: Any):
        """Helper to navigate a concrete path and set the value."""
        parts = path.split(".")
        target = obj
        # Traverse to the parent of the leaf attribute
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target[part]
            elif isinstance(target, list):
                target = target[int(part)]
            else:
                target = getattr(target, part)

        last_part = parts[-1]
        # Set the value on the leaf
        if isinstance(target, dict):
            target[last_part] = value
        elif isinstance(target, list):
            target[int(last_part)] = value
        else:
            setattr(target, last_part, value)
