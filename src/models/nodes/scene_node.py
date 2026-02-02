from __future__ import annotations

from PySide6.QtCore import QObject


class SceneNode(QObject):
    """
    An abstract base class for all objects in the scene graph.
    Inherits from QObject to support Qt's signal/slot mechanism in the future.
    """

    def __init__(self, parent: SceneNode | None = None, name: str = ""):
        super().__init__()
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
