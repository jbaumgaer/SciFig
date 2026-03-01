from typing import Protocol

from src.models.nodes.scene_node import SceneNode


class NodeSelectionInterface(Protocol):
    """
    Interface for managing node selection in the scene graph.
    """

    def get_selected_nodes(self) -> list[SceneNode]:
        """
        Returns a list of currently selected nodes.
        """
        raise NotImplementedError

    def select_node(self, node: SceneNode):
        """
        Selects a given node.
        """
        raise NotImplementedError

    def deselect_node(self, node: SceneNode):
        """
        Deselects a given node.
        """
        raise NotImplementedError

    def clear_selection(self):
        """
        Clears all selected nodes.
        """
        raise NotImplementedError
