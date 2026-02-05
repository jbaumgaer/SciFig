from __future__ import annotations

import uuid
import logging
from pathlib import Path

from PySide6.QtCore import QObject


class SceneNode(QObject):
    """
    An abstract base class for all objects in the scene graph.
    Inherits from QObject to support Qt's signal/slot mechanism in the future.
    """

    def __init__(
        self, parent: SceneNode | None = None, name: str = "", id: str | None = None
    ):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id or uuid.uuid4().hex
        self._parent = parent
        self._children: list[SceneNode] = []
        self.name = name
        self.visible = True
        self.logger.debug(f"SceneNode initialized: {self.name} (ID: {self.id})")


        if parent:
            parent.add_child(self)

    @property
    def parent(self) -> SceneNode | None:
        return self._parent

    @parent.setter
    def parent(self, new_parent: SceneNode | None):
        """Sets a new parent for this node."""
        self.logger.debug(f"Setting parent for {self.name} (ID: {self.id}) from {self._parent.name if self._parent else 'None'} to {new_parent.name if new_parent else 'None'}.")
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
            self.logger.debug(f"Added child {node.name} (ID: {node.id}) to {self.name} (ID: {self.id}).")

    def remove_child(self, node: SceneNode):
        """Removes a child node."""
        if node in self._children:
            self._children.remove(node)
            node._parent = None
            self.logger.debug(f"Removed child {node.name} (ID: {node.id}) from {self.name} (ID: {self.id}).")

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        """
        Abstract method to check if a position hits this node or any of its children.
        Must be implemented by subclasses.
        """
        self.logger.debug(f"Performing hit test on {self.name} (ID: {self.id}) at position {position}.")
        # Default implementation iterates backwards (top-to-bottom) through children
        for child in reversed(self.children):
            if child.visible:
                hit = child.hit_test(position)
                if hit:
                    self.logger.debug(f"Hit test on {self.name} (ID: {self.id}): Child {child.name} (ID: {child.id}) hit.")
                    return hit
        self.logger.debug(f"Hit test on {self.name} (ID: {self.id}): No child hit.")
        return None

    def all_descendants(self) -> "Generator[SceneNode, None, None]":
        """A generator that yields all nodes in the subtree, including this node."""
        self.logger.debug(f"Getting all descendants starting from {self.name} (ID: {self.id}).")
        yield self
        for child in self.children:
            yield from child.all_descendants()

    def to_dict(self) -> dict:
        """Serializes the node to a dictionary."""
        node_dict = {
            "id": self.id,
            "type": self.__class__.__name__, # Changed class_name to type for consistency
            "name": self.name,
            "visible": self.visible,
            "children": [child.to_dict() for child in self.children],
        }
        self.logger.debug(f"SceneNode '{self.name}' (ID: {self.id}) serialized to dict.")
        return node_dict

    @classmethod
    def from_dict(cls, data: dict, parent: SceneNode | None = None) -> SceneNode:
        """Creates a node from a dictionary."""
        node = cls(parent=parent, name=data["name"], id=data["id"])
        node.visible = data["visible"]
        node.logger.debug(f"SceneNode.from_dict: Created node {node.name} (ID: {node.id}).")
        # Children are handled by the factory
        return node


def node_factory(
    data: dict, parent: SceneNode | None = None, temp_dir: "Path | None" = None
) -> SceneNode:
    """Factory function to create nodes from a dictionary."""
    from . import GroupNode, PlotNode

    # Use "type" from the JSON data
    node_type_str = data.get("type")
    
    # Create a temporary logger for this function, as ConfigService isn't available yet
    logger = logging.getLogger(__name__)
    logger.debug(f"node_factory: Attempting to create node of type: '{node_type_str}'")


    node_class_map = {
        "GroupNode": GroupNode,
        "PlotNode": PlotNode,
        "SceneNode": SceneNode,
    }

    # Get the class based on "type" field, with SceneNode as a fallback
    cls = node_class_map.get(node_type_str, SceneNode)
    if cls == SceneNode and node_type_str not in node_class_map: # Check if fallback was used for unknown type
        logger.warning(f"node_factory: Unknown node type '{node_type_str}'. Falling back to SceneNode.")

    # Pass temp_dir only if the class method accepts it (i.e., for PlotNode)
    if node_type_str == "PlotNode":
        node = cls.from_dict(data, parent=parent, temp_dir=temp_dir)
    else:
        node = cls.from_dict(data, parent=parent)
    
    logger.debug(f"node_factory: Created node {node.name} (ID: {node.id}) of type {type(node).__name__}.")


    # Recursively create children
    child_data = data.get("children", [])
    if child_data:
        logger.debug(f"node_factory: Recursively creating {len(child_data)} children for {node.name}.")
    for child_dict in child_data:
        node_factory(child_dict, parent=node, temp_dir=temp_dir)

    return node
