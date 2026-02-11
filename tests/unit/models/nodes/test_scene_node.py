import pytest

from src.models.nodes.scene_node import SceneNode, node_factory

# --- Fixtures ---


class MockSceneNode(SceneNode):
    """
    A mock SceneNode with a defined size and position for hit testing.
    This concrete implementation is needed for testing the abstract SceneNode's
    hit_test method's recursive behavior.
    """

    def __init__(self, parent=None, name="", id=None, pos=(0, 0), size=(10, 10)):
        super().__init__(parent, name, id)
        self.pos = pos
        self.size = size

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        x, y = position
        node_x, node_y = self.pos
        node_w, node_h = self.size
        if node_x <= x <= node_x + node_w and node_y <= y <= node_y + node_h:
            # If this node's bounds are hit, then check its children (top-to-bottom)
            for child in reversed(self.children):
                if child.visible:
                    hit = child.hit_test(position)
                    if hit:
                        return hit
            # If no children are hit, then this node itself is the hit target
            if self.visible:
                return self
        return None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["pos"] = self.pos
        d["size"] = self.size
        return d

    @classmethod
    def from_dict(cls, data: dict, parent: SceneNode | None = None) -> "MockSceneNode":
        node = super().from_dict(data, parent)
        node.pos = data.get("pos", (0, 0))
        node.size = data.get("size", (10, 10))
        return node


@pytest.fixture
def root_node():
    """Provides a fresh root SceneNode for tests."""
    return MockSceneNode(name="root", id="root_id", pos=(0, 0), size=(30, 30))


@pytest.fixture
def setup_tree(root_node):
    """
    Sets up a sample tree structure for testing traversal and ID lookup.
    root
    ├── child1 (pos: 0,0, size: 10,10)
    │   └── nested_child1_1 (pos: 2,2, size: 5,5)
    ├── child2 (pos: 10,0, size: 10,10)
    └── child3 (pos: 0,10, size: 10,10, visible: False)
    """
    child1 = MockSceneNode(
        parent=root_node, name="child1", id="child1_id", pos=(0, 0), size=(10, 10)
    )
    MockSceneNode(
        parent=child1,
        name="nested_child1_1",
        id="nested1_1_id",
        pos=(2, 2),
        size=(5, 5),
    )
    MockSceneNode(
        parent=root_node, name="child2", id="child2_id", pos=(10, 0), size=(10, 10)
    )
    child3 = MockSceneNode(
        parent=root_node, name="child3", id="child3_id", pos=(0, 10), size=(10, 10)
    )
    child3.visible = False  # For testing visibility
    return root_node


@pytest.fixture
def patch_node_factory_for_mock_scene_node(mocker):
    """
    Patches the node_factory function to use a test-specific node_class_map
    that includes MockSceneNode for testing purposes.
    """

    # Define a custom node_factory for testing
    def custom_node_factory(data, parent=None, temp_dir=None):
        import src.models.nodes.group_node
        import src.models.nodes.plot_node
        import src.models.nodes.scene_node

        node_type_str = data.get("type")

        # Use a test-specific map that includes MockSceneNode
        _test_node_class_map = {
            "GroupNode": src.models.nodes.group_node.GroupNode,
            "PlotNode": src.models.nodes.plot_node.PlotNode,
            "SceneNode": src.models.nodes.scene_node.SceneNode,
            "MockSceneNode": MockSceneNode,
        }

        cls = _test_node_class_map.get(node_type_str)

        if cls is None:
            raise ValueError(
                f"Unknown node type '{node_type_str}' for custom_node_factory."
            )

        if node_type_str == "PlotNode":
            node = cls.from_dict(data, parent=parent, temp_dir=temp_dir)
        else:
            node = cls.from_dict(data, parent=parent)

        child_data = data.get("children", [])
        for child_dict in child_data:
            custom_node_factory(
                child_dict, parent=node, temp_dir=temp_dir
            )  # Recursive call uses custom factory

        return node

    # Patch the node_factory function that is imported into test_scene_node.py
    mocker.patch("test_scene_node.node_factory", side_effect=custom_node_factory)


# --- Tests for SceneNode ---


class TestSceneNode:

    def test_initialization_defaults(self):
        """Test default initialization of SceneNode."""
        node = SceneNode()
        assert node.parent is None
        assert node.children == []
        assert len(node.id) == 32  # UUID hex string length
        assert node.name == ""
        assert node.visible is True

    def test_initialization_with_custom_values(self):
        """Test initialization with custom name, ID, and parent."""
        parent = SceneNode(name="ParentNode")
        node = SceneNode(parent=parent, name="ChildNode", id="custom_id")
        assert node.parent is parent
        assert node.name == "ChildNode"
        assert node.id == "custom_id"
        assert node in parent.children

    def test_add_child(self, root_node):
        """Test adding a child to a node."""
        child = MockSceneNode(name="child")
        root_node.add_child(child)
        assert child in root_node.children
        assert child.parent is root_node

    def test_add_child_idempotent(self, root_node):
        """Test that adding the same child twice does not result in duplicates."""
        child = MockSceneNode(name="child")
        root_node.add_child(child)
        root_node.add_child(child)
        assert root_node.children.count(child) == 1
        assert len(root_node.children) == 1

    def test_remove_child(self, root_node):
        """Test removing a child from a node."""
        child = MockSceneNode(name="child", parent=root_node)
        assert child in root_node.children
        root_node.remove_child(child)
        assert child not in root_node.children
        assert child.parent is None

    def test_remove_non_existent_child(self, root_node):
        """Test removing a child that is not present."""
        child1 = MockSceneNode(name="child1", parent=root_node)
        child2 = MockSceneNode(name="child2")
        initial_children_count = len(root_node.children)
        root_node.remove_child(child2)  # Try removing child2 which is not in root_node
        assert len(root_node.children) == initial_children_count
        assert child1 in root_node.children
        assert child2.parent is None

    def test_parent_setter_reparents_correctly(self, root_node):
        """Test the parent property setter for reparenting."""
        old_parent = root_node
        child = MockSceneNode(name="child", parent=old_parent)
        new_parent = MockSceneNode(name="new_parent")

        assert child in old_parent.children
        assert child.parent is old_parent
        assert child not in new_parent.children

        child.parent = new_parent

        assert child not in old_parent.children
        assert child in new_parent.children
        assert child.parent is new_parent

    def test_parent_setter_to_none(self, root_node):
        """Test setting the parent property to None."""
        child = MockSceneNode(name="child", parent=root_node)
        assert child in root_node.children
        assert child.parent is root_node

        child.parent = None
        assert child not in root_node.children
        assert child.parent is None

    def test_hit_test_no_children(self, root_node):
        """Test hit_test on a node with no children (should return None as SceneNode is abstract by default)."""
        # For a SceneNode (abstract), hit_test should not return itself unless implemented by a concrete class
        # Here we use MockSceneNode which has a concrete hit_test.
        assert root_node.hit_test((5, 5)) is root_node  # MockSceneNode is hit

    def test_hit_test_miss(self, setup_tree):
        """Test a hit test that misses all children (should return root_node for MockSceneNode)."""
        # (15, 15) misses child1 (0,0,10,10), child2 (10,0,10,10) and child3 (0,10,10,10, invisible)
        # but hits the root_node (0,0,10,10 - assuming default mock size if not set otherwise)
        # Let's ensure root_node's effective bounding box covers the children
        # In setup_tree, child1 is at 0,0 size 10,10, child2 at 10,0 size 10,10, child3 at 0,10 size 10,10.
        # A hit at (15,15) would only hit child2 if it's visible, but it's not (10,0,10,10).
        # We need to explicitly define the root_node's hit_test area for this test.
        # For setup_tree, root_node has name "root", and children are spread out.
        # Let's assume the root_node itself would be hit if no children are hit AND position is within root's area.
        # The MockSceneNode's hit_test for parent ensures this.
        assert setup_tree.hit_test((15, 15)) is setup_tree

    def test_hit_test_hit_single_child(self, setup_tree):
        """Test a hit test that hits a single child."""
        child1 = setup_tree.find_node_by_id("child1_id")
        assert setup_tree.hit_test((5, 5)) == setup_tree.find_node_by_id("nested1_1_id")

    def test_hit_test_hits_topmost_child(self, root_node):
        """Test that hit_test returns the topmost child when children overlap."""
        # Children are iterated in reverse order (last added first)
        MockSceneNode(
            parent=root_node,
            name="child_back",
            id="child_back_id",
            pos=(0, 0),
            size=(10, 10),
        )
        child_front = MockSceneNode(
            parent=root_node,
            name="child_front",
            id="child_front_id",
            pos=(0, 0),
            size=(10, 10),
        )
        assert root_node.hit_test((5, 5)) == child_front

    def test_hit_test_nested_children(self, setup_tree):
        """Test hit testing with nested children."""
        nested_child = setup_tree.find_node_by_id("nested1_1_id")
        assert setup_tree.hit_test((3, 3)) == nested_child  # Should hit nested child

    def test_hit_test_invisible_child(self, setup_tree):
        """Test that invisible children are ignored by hit_test."""
        child3 = setup_tree.find_node_by_id(
            "child3_id"
        )  # This child is set to invisible in fixture
        assert child3.visible is False
        assert setup_tree.hit_test((5, 15)) is setup_tree

    def test_all_descendants_empty_tree(self, root_node):
        """Test all_descendants on an empty tree."""
        descendants = list(root_node.all_descendants())
        assert descendants == [root_node]

    def test_all_descendants_simple_tree(self, setup_tree):
        """Test all_descendants on a simple tree structure."""
        descendants = list(setup_tree.all_descendants())
        # Order of children depends on add_child order, but all should be present
        assert len(descendants) == 5  # root + child1 + nested1_1 + child2 + child3
        ids = {node.id for node in descendants}
        assert ids == {"root_id", "child1_id", "nested1_1_id", "child2_id", "child3_id"}
        assert setup_tree in descendants

    def test_all_descendants_filter_by_type(self, setup_tree):
        """Test all_descendants with type filtering."""
        # Only return MockSceneNode instances, which all nodes in setup_tree are
        descendants = list(setup_tree.all_descendants(of_type=MockSceneNode))
        assert len(descendants) == 5
        ids = {node.id for node in descendants}
        assert ids == {"root_id", "child1_id", "nested1_1_id", "child2_id", "child3_id"}

        # If we had another type, it should not be included
        class AnotherNode(SceneNode):
            def hit_test(self, position):
                return None

        another_node = AnotherNode(parent=setup_tree.children[0])  # Add it to child1

        filtered_descendants = list(setup_tree.all_descendants(of_type=MockSceneNode))
        assert len(filtered_descendants) == 5  # AnotherNode should not be included
        assert another_node not in filtered_descendants

    def test_find_node_by_id_root(self, setup_tree):
        """Test finding the root node by ID."""
        found = setup_tree.find_node_by_id("root_id")
        assert found is setup_tree

    def test_find_node_by_id_direct_child(self, setup_tree):
        """Test finding a direct child by ID."""
        found = setup_tree.find_node_by_id("child1_id")
        assert found is setup_tree.children[0]

    def test_find_node_by_id_nested_child(self, setup_tree):
        """Test finding a nested child by ID."""
        found = setup_tree.find_node_by_id("nested1_1_id")
        assert found is setup_tree.children[0].children[0]

    def test_find_node_by_id_non_existent(self, setup_tree):
        """Test finding a non-existent ID."""
        found = setup_tree.find_node_by_id("non_existent_id")
        assert found is None

    def test_to_dict_simple_node(self, root_node):
        """Test serialization of a simple SceneNode."""
        node_dict = root_node.to_dict()
        assert node_dict["id"] == "root_id"
        assert node_dict["type"] == "MockSceneNode"
        assert node_dict["name"] == "root"
        assert node_dict["visible"] is True
        assert node_dict["children"] == []

    def test_to_dict_nested_nodes(self, setup_tree):
        """Test serialization of a nested SceneNode tree."""
        tree_dict = setup_tree.to_dict()
        assert tree_dict["id"] == "root_id"
        assert len(tree_dict["children"]) == 3
        # Check one child's details
        child1_dict = tree_dict["children"][0]
        assert child1_dict["id"] == "child1_id"
        assert len(child1_dict["children"]) == 1
        nested_child_dict = child1_dict["children"][0]
        assert nested_child_dict["id"] == "nested1_1_id"
        assert nested_child_dict["children"] == []

    def test_scene_node_from_dict(self):
        """Tests the deserialization of a basic SceneNode."""
        data = {
            "id": "12345",
            "type": "SceneNode",
            "name": "LoadedNode",
            "visible": False,
            "children": [],
        }
        node = SceneNode.from_dict(data)

        assert node.id == "12345"
        assert node.name == "LoadedNode"
        assert node.visible is False
        assert node.children == []

    def test_node_factory_simple_node(self):
        """Test node_factory for creating a simple node."""
        data = {
            "id": "new_node_id",
            "type": "MockSceneNode",
            "name": "NewNode",
            "visible": False,
            "children": [],
            "pos": (1, 1),
            "size": (5, 5),
        }
        node = node_factory(data)
        assert isinstance(node, MockSceneNode)
        assert node.id == "new_node_id"
        assert node.name == "NewNode"
        assert node.visible is False
        assert node.pos == (1, 1)
        assert node.size == (5, 5)
        assert node.children == []

    def test_node_factory_nested_nodes(self):
        """Test node_factory for creating a nested node tree."""
        data = {
            "id": "parent_id",
            "type": "MockSceneNode",
            "name": "Parent",
            "visible": True,
            "pos": (0, 0),
            "size": (20, 20),
            "children": [
                {
                    "id": "child_a_id",
                    "type": "MockSceneNode",
                    "name": "ChildA",
                    "visible": True,
                    "children": [],
                    "pos": (1, 1),
                    "size": (5, 5),
                },
                {
                    "id": "child_b_id",
                    "type": "MockSceneNode",
                    "name": "ChildB",
                    "visible": True,
                    "children": [
                        {
                            "id": "grandchild_id",
                            "type": "MockSceneNode",
                            "name": "Grandchild",
                            "visible": True,
                            "children": [],
                            "pos": (2, 2),
                            "size": (3, 3),
                        }
                    ],
                    "pos": (10, 10),
                    "size": (8, 8),
                },
            ],
        }
        root = node_factory(data)
        assert isinstance(root, MockSceneNode)
        assert root.id == "parent_id"
        assert len(root.children) == 2

        child_a = root.children[0]
        assert isinstance(child_a, MockSceneNode)
        assert child_a.id == "child_a_id"
        assert child_a.parent is root
        assert child_a.pos == (1, 1)

        child_b = root.children[1]
        assert isinstance(child_b, MockSceneNode)
        assert child_b.id == "child_b_id"
        assert child_b.parent is root
        assert child_b.pos == (10, 10)
        assert len(child_b.children) == 1

        grandchild = child_b.children[0]
        assert isinstance(grandchild, MockSceneNode)
        assert grandchild.id == "grandchild_id"
        assert grandchild.parent is child_b
        assert grandchild.pos == (2, 2)
