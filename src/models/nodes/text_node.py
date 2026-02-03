from .scene_node import SceneNode


class TextNode(SceneNode):
    """
    A node representing a text object.
    """

    def __init__(self, name: str):
        super().__init__(name)
