from typing import Optional

from src.models.nodes.scene_node import SceneNode


class GroupNode(SceneNode):
    """
    A simple container node that groups other scene nodes.
    It has no visual representation itself but is useful for organization.
    """

    def __init__(
        self,
        parent: Optional[SceneNode] = None,
        name: str = "Group",
        id: Optional[str] = None,
    ):
        super().__init__(parent, name, id)

    # Uses default `hit_test` from SceneNode (checks children).

    def to_dict(self) -> dict:
        """Serializes the group node to a dictionary."""
        # For now, GroupNode has no special properties, so we just call the base implementation.
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict, parent: Optional[SceneNode] = None) -> "GroupNode":
        """Creates a GroupNode from a dictionary."""
        # For now, GroupNode has no special properties, so we just call the base implementation.
        return super().from_dict(data, parent)
