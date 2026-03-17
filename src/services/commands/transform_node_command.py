from typing import Any, Optional, Union

from src.models.nodes.scene_node import SceneNode
from src.models.nodes.grid_position import GridPosition
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect


class TransformNodeCommand(BaseCommand):
    """
    An atomic command for spatial transformations of a single node.
    Handles updates to 'grid_position' (Grid Mode) or 'geometry' (Free-form).
    Increments _geometry_version to trigger visual updates.
    """

    def __init__(
        self,
        node: SceneNode,
        new_spatial_value: Union[GridPosition, Rect],
        event_aggregator: EventAggregator,
        description: str
    ):
        super().__init__(description, event_aggregator)
        self.node = node
        self.new_value = new_spatial_value
        
        # Auto-detect path
        if isinstance(new_spatial_value, GridPosition):
            self.path = "grid_position"
        elif isinstance(new_spatial_value, Rect):
            self.path = "geometry"
        else:
            raise ValueError(f"TransformNodeCommand: Unsupported spatial value type {type(new_spatial_value)}")

        self.old_value = getattr(node, self.path, None)

    def execute(self, publish: bool = True):
        """Applies the spatial change and increments geometry version."""
        setattr(self.node, self.path, self.new_value)
        self._finalize(publish=publish)

    def undo(self, publish: bool = True):
        """Restores the original spatial state and increments geometry version."""
        setattr(self.node, self.path, self.old_value)
        self._finalize(publish=publish)

    def _finalize(self, publish: bool = True):
        """Increments version and signals the Layout Domain."""
        # Increment version to pass the FigureRenderer version-gate
        self.node._geometry_version += 1
        
        self.logger.debug(f"TransformNodeCommand: '{self.node.name}' {self.path} updated. Version: {self.node._geometry_version}")

        if not publish:
            return

        # Signal LayoutManager to recalculate or acknowledge the shift
        self._event_aggregator.publish(
            Events.NODE_LAYOUT_CHANGED,
            node_id=self.node.id
        )
