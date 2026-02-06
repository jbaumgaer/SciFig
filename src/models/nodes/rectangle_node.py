from src.models.nodes.scene_node import SceneNode


class RectangleNode(SceneNode):
    """
    A node representing a rectangle.
    """

    def __init__(self, name: str):
        super().__init__(name)
