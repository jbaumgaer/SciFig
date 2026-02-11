from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode


class TestGroupNode:

    def test_group_node_to_dict(self):
        """Tests the serialization of a GroupNode with children."""
        root = GroupNode(name="root")
        child1 = SceneNode(parent=root, name="child1")
        child2 = SceneNode(parent=root, name="child2")

        root_dict = root.to_dict()

        assert root_dict["type"] == "GroupNode"
        assert len(root_dict["children"]) == 2
        assert root_dict["children"][0]["name"] == "child1"
        assert root_dict["children"][1]["name"] == "child2"

    def test_group_node_from_dict(self):
        """Tests the deserialization of a GroupNode."""
        data = {
            "id": "group1",
            "type": "GroupNode",
            "name": "LoadedGroup",
            "visible": True,
            "children": [],
        }
        node = GroupNode.from_dict(data)

        assert node.id == "group1"
        assert node.name == "LoadedGroup"
        assert node.visible is True
        assert node.children == []
