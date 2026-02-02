import matplotlib.figure
from PySide6.QtCore import QObject, Signal

from .nodes import GroupNode, SceneNode


class ApplicationModel(QObject):
    """
    The central model for the entire application. It is the single source of truth,
    holding the state of the scene graph.
    """

    modelChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, figure: matplotlib.figure.Figure):
        super().__init__()
        self.figure = figure
        self.scene_root = GroupNode(name="root")
        self.selection: list[SceneNode] = []

    def add_node(self, node: SceneNode, parent: SceneNode | None = None):
        """Adds a node to the scene graph."""
        if parent is None:
            parent = self.scene_root
        parent.add_child(node)
        self.modelChanged.emit()

    def clear_scene(self):
        """Removes all nodes from the scene."""
        self.scene_root.children.clear()
        self.set_selection([])
        self.modelChanged.emit()

    def set_selection(self, nodes: list[SceneNode]):
        """Sets the selection and emits the selectionChanged signal."""
        self.selection = nodes
        self.selectionChanged.emit()

    def get_node_at(self, position: tuple[float, float]) -> SceneNode | None:
        """Finds the topmost node at the given figure coordinates."""
        return self.scene_root.hit_test(position)
