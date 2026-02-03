from __future__ import annotations
import uuid

from PySide6.QtCore import QObject


class SceneNode(QObject):
    """
    An abstract base class for all objects in the scene graph.
    Inherits from QObject to support Qt's signal/slot mechanism in the future.
    """

    def __init__(self, parent: SceneNode | None = None, name: str = "", id: str | None = None):
        super().__init__()
        self.id = id or uuid.uuid4().hex
        self._parent = parent
        self._children: list[SceneNode] = []
        self.name = name
        self.visible = True

        if parent:
            parent.add_child(self)

    @property
    def parent(self) -> SceneNode | None:
        return self._parent

    @parent.setter
    def parent(self, new_parent: SceneNode | None):
        """Sets a new parent for this node."""
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

    def remove_child(self, node: SceneNode):
        """Removes a child node."""
        if node in self._children:
            self._children.remove(node)
            node._parent = None

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        """
        Abstract method to check if a position hits this node or any of its children.
        Must be implemented by subclasses.
        """
        # Default implementation iterates backwards (top-to-bottom) through children
        for child in reversed(self.children):
            if child.visible:
                hit = child.hit_test(position)
                if hit:
                    return hit
        return None

    def all_descendants(self) -> "Generator[SceneNode, None, None]":
        """A generator that yields all nodes in the subtree, including this node."""
        yield self
        for child in self.children:
            yield from child.all_descendants()

    def to_dict(self) -> dict:
        """Serializes the node to a dictionary."""
        return {
            "id": self.id,
            "class_name": self.__class__.__name__,
            "name": self.name,
            "visible": self.visible,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict, parent: SceneNode | None = None) -> SceneNode:
        """Creates a node from a dictionary."""
        node = cls(parent=parent, name=data["name"], id=data["id"])
        node.visible = data["visible"]
        # Children are handled by the factory
        return node


def node_factory(data: dict, parent: SceneNode | None = None, temp_dir: "Path | None" = None) -> SceneNode:
    """Factory function to create nodes from a dictionary."""
    from . import GroupNode, PlotNode

    class_name = data.get("class_name")
    
    node_class_map = {
        "GroupNode": GroupNode,
        "PlotNode": PlotNode,
        "SceneNode": SceneNode,
    }
    
    cls = node_class_map.get(class_name, SceneNode)

    # Pass temp_dir only if the class method accepts it (i.e., for PlotNode)
    if class_name == "PlotNode":
        node = cls.from_dict(data, parent=parent, temp_dir=temp_dir)
    else:
        node = cls.from_dict(data, parent=parent)
    
    # Recursively create children
    child_data = data.get("children", [])
    for child_dict in child_data:
        node_factory(child_dict, parent=node, temp_dir=temp_dir)
        
    return node
