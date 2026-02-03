from .scene_node import SceneNode


class GroupNode(SceneNode):
    """
    A simple container node that groups other scene nodes.
    It has no visual representation itself but is useful for organization.
    """

    def __init__(self, parent: SceneNode | None = None, name: str = "Group"):
        super().__init__(parent, name)

    # Uses default `hit_test` from SceneNode (checks children).

    def to_dict(self) -> dict:
        """Serializes the group node to a dictionary."""
        # For now, GroupNode has no special properties, so we just call the base implementation.
        return super().to_dict()
