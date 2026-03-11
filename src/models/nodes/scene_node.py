from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Generator, Optional, Type

from src.models.nodes.grid_position import GridPosition
from src.shared.geometry import Rect


class SceneNode:
    """
    An abstract base class for all objects in the scene graph.
    A pure Python data structure with zero dependencies on UI frameworks.
    """

    def __init__(
        self,
        parent: Optional[SceneNode] = None,
        name: str = "",
        id: Optional[str] = None,
    ):
        self.logger = logging.getLogger(
            self.__class__.__name__
        )
        self.id = id or uuid.uuid4().hex
        self._parent = parent
        self._children: list[SceneNode] = []
        self.name = name
        self.visible = True
        self.locked = False  # New attribute
        self._geometry_version = 0  # Version-gating for structural sync
        self._property_version = 0  # Version-gating for aesthetic sync
        self.grid_position: Optional[GridPosition] = None  # Position within a GridNode
        
        # Geometry in physical centimeters (cm).
        self.geometry: Rect = Rect(0.0, 0.0, 0.0, 0.0)

        self.logger.debug(f"SceneNode initialized: {self.name} (ID: {self.id})")

        if parent:
            parent.add_child(self)

    @property
    def parent(self) -> Optional[SceneNode]:
        return self._parent

    @parent.setter
    def parent(self, new_parent: Optional[SceneNode]):
        """Sets a new parent for this node."""
        self.logger.debug(
            f"Setting parent for {self.name} (ID: {self.id}) from {self._parent.name if self._parent else 'None'} to {new_parent.name if new_parent else 'None'}."
        )
        if self._parent:
            self._parent._children.remove(self)
        self._parent = new_parent
        if new_parent:
            new_parent.add_child(self)

    @property
    def children(self) -> list[SceneNode]:
        return self._children

    def add_child(self, node: SceneNode):
        """Adds a child node."""
        if node not in self._children:
            self._children.append(node)
            node._parent = self
            self.logger.debug(
                f"Added child {node.name} (ID: {node.id}) to {self.name} (ID: {self.id})."
            )

    def insert_child(self, index: int, node: SceneNode):
        """Inserts a child node at a specific index."""
        if node not in self._children:
            self._children.insert(index, node)
            node._parent = self
            self.logger.debug(
                f"Inserted child {node.name} (ID: {node.id}) at index {index} into {self.name} (ID: {self.id})."
            )

    def remove_child(self, node: SceneNode):
        """Removes a child node."""
        if node in self._children:
            self._children.remove(node)
            node._parent = None
            self.logger.debug(
                f"Removed child {node.name} (ID: {node.id}) from {self.name} (ID: {self.id})."
            )

    def increment_property_version(self):
        """Increments the node's aesthetic property version to trigger re-rendering."""
        self._property_version += 1
        self.logger.debug(
            f"Node '{self.name}' (ID: {self.id}) property version incremented to {self._property_version}."
        )

    def hit_test(self, position: tuple[float, float]) -> Optional[SceneNode]:
        """
        Abstract method to check if a position hits this node or any of its children.
        Must be implemented by subclasses.
        """
        self.logger.debug(
            f"Performing hit test on {self.name} (ID: {self.id}) at position {position}."
        )
        # Default implementation iterates backwards (top-to-bottom) through children
        for child in reversed(self.children):
            if child.visible:
                hit = child.hit_test(position)
                if hit:
                    self.logger.debug(
                        f"Hit test on {self.name} (ID: {self.id}): Child {child.name} (ID: {child.id}) hit."
                    )
                    return hit
        self.logger.debug(f"Hit test on {self.name} (ID: {self.id}): No child hit.")
        return None

    def all_descendants(
        self, of_type: Optional[Type[SceneNode]] = None
    ) -> Generator[SceneNode, None, None]:
        """
        A generator that yields all nodes in the subtree, including this node.
        If 'of_type' is provided, only nodes of that type (or subclasses) are yielded.
        """
        self.logger.debug(
            f"Getting all descendants starting from {self.name} (ID: {self.id})."
        )

        # Yield self if it matches the type or no type is specified
        if of_type is None or isinstance(self, of_type):
            yield self

        for child in self.children:
            yield from child.all_descendants(of_type)  # Pass of_type recursively

    def find_node_by_id(self, node_id: str) -> Optional[SceneNode]:
        """
        Recursively finds a node within this node's subtree by its ID.
        """
        if self.id == node_id:
            return self
        for child in self.children:
            found_node = child.find_node_by_id(node_id)
            if found_node:
                return found_node
        return None

    def to_dict(self) -> dict:
        """Serializes the node to a dictionary."""
        node_dict = {
            "id": self.id,
            "type": self.__class__.__name__,  # Changed class_name to type for consistency
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,  # New attribute
            "geometry_version": self._geometry_version,
            "property_version": self._property_version,
            "grid_position": self.grid_position.to_dict() if self.grid_position else None,
            "geometry": {
                "x": self.geometry.x,
                "y": self.geometry.y,
                "width": self.geometry.width,
                "height": self.geometry.height,
            },
            "children": [child.to_dict() for child in self.children],
        }
        self.logger.debug(
            f"SceneNode '{self.name}' (ID: {self.id}) serialized to dict."
        )
        return node_dict

    @classmethod
    def from_dict(cls, data: dict, parent: Optional[SceneNode] = None) -> SceneNode:
        """Creates a node from a dictionary."""
        node = cls(parent=parent, name=data["name"], id=data["id"])
        node.visible = data["visible"]
        node.locked = data.get("locked", False)  # New attribute with default
        node._geometry_version = data.get("geometry_version", 0)
        node._property_version = data.get("property_version", 0)
        
        # Geometry reconstruction (Physical CM)
        geom_data = data.get("geometry", {})
        node.geometry = Rect(
            x=geom_data.get("x", 0.0),
            y=geom_data.get("y", 0.0),
            width=geom_data.get("width", 0.0),
            height=geom_data.get("height", 0.0),
        )

        # GridPosition reconstruction
        grid_pos_data = data.get("grid_position")
        if grid_pos_data:
            node.grid_position = GridPosition.from_dict(grid_pos_data)

        node.logger.debug(
            f"SceneNode.from_dict: Created node {node.name} (ID: {node.id})."
        )
        # Children are handled by the factory
        return node


def node_factory(
    data: dict, parent: Optional[SceneNode] = None, temp_dir: Optional[Path] = None
) -> SceneNode:
    """Factory function to create nodes from a dictionary."""
    from .grid_node import GridNode
    from .group_node import GroupNode
    from .plot_node import PlotNode

    # Use "type" from the JSON data
    node_type_str = data.get("type")

    # Create a temporary logger for this function, as ConfigService isn't available yet
    logger = logging.getLogger(__name__)
    logger.debug(f"node_factory: Attempting to create node of type: '{node_type_str}'")

    node_class_map = {
        "GroupNode": GroupNode,
        "PlotNode": PlotNode,
        "GridNode": GridNode,
        "SceneNode": SceneNode,
    }

    # Get the class based on "type" field, with SceneNode as a fallback
    cls = node_class_map.get(node_type_str, SceneNode)
    if (
        cls == SceneNode and node_type_str not in node_class_map
    ):  # Check if fallback was used for unknown type
        logger.warning(
            f"node_factory: Unknown node type '{node_type_str}'. Falling back to SceneNode."
        )

    # Pass temp_dir only if the class method accepts it (i.e., for PlotNode)
    if node_type_str == "PlotNode":
        node = cls.from_dict(data, parent=parent, temp_dir=temp_dir)
    else:
        node = cls.from_dict(data, parent=parent)

    logger.debug(
        f"node_factory: Created node {node.name} (ID: {node.id}) of type {type(node).__name__}."
    )

    # Recursively create children
    child_data = data.get("children", [])
    if child_data:
        logger.debug(
            f"node_factory: Recursively creating {len(child_data)} children for {node.name}."
        )
    for child_dict in child_data:
        node_factory(child_dict, parent=node, temp_dir=temp_dir)

    return node
