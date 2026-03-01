from typing import Protocol

from src.models.nodes.scene_node import SceneNode


class NodeHierarchyInterface(Protocol):
    """
    Interface for managing a hierarchy of nodes in the application.
    This interface defines methods for adding, removing, and retrieving nodes,
    as well as managing the relationships between parent and child nodes.
    """

    def add_node(self, node: SceneNode, parent: SceneNode = None) -> None:
        """
        Add a node to the hierarchy under the specified parent.
        If no parent is provided, the node is added to the root level.
        """
        raise NotImplementedError

    def remove_node(self, node: SceneNode) -> None:
        """
        Remove a node from the hierarchy. This should also handle
        reassigning or removing any child nodes as necessary.
        """
        raise NotImplementedError

    def find_node(self, node_id: str) -> SceneNode:
        """
        Retrieve a node by its unique identifier.
        """
        raise NotImplementedError

    def get_children(self, parent: SceneNode) -> list[SceneNode]:
        """
        Get a list of child nodes for the specified parent node.
        """
        raise NotImplementedError

    def get_parent(self, child: SceneNode) -> SceneNode:
        """
        Get the parent node of the specified child node.
        """
        raise NotImplementedError

    def get_all_nodes(self) -> list[SceneNode]:
        """
        Get a list of all nodes in the hierarchy.
        """
        raise NotImplementedError
