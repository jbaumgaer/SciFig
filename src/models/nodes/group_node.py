from .scene_node import SceneNode


class GroupNode(SceneNode):
    """
    A simple container node that groups other scene nodes.
    It has no visual representation itself but is useful for organization.
    """

    def __init__(self, parent: SceneNode | None = None, name: str = "Group"):
        super().__init__(parent, name)

    # Uses default `hit_test` from SceneNode (checks children).
