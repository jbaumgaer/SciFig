import pytest

from src.models.nodes.scene_node import SceneNode


class MockSceneNode(SceneNode):
    """A mock SceneNode with a defined size for hit testing."""

    def __init__(self, parent=None, name="", pos=(0, 0), size=(10, 10)):
        super().__init__(parent, name)
        self.pos = pos
        self.size = size

    def hit_test(self, position: tuple[float, float]) -> SceneNode | None:
        x, y = position
        node_x, node_y = self.pos
        node_w, node_h = self.size
        if node_x <= x <= node_x + node_w and node_y <= y <= node_y + node_h:
            # First check children
            hit = super().hit_test(position)
            if hit:
                return hit
            # If no children hit, return self
            return self
        return None


@pytest.fixture
def parent_node():
    """Fixture for a parent SceneNode."""
    return SceneNode(name="parent")


@pytest.fixture
def child_node():
    """Fixture for a child SceneNode."""
    return SceneNode(name="child")


def test_add_child(parent_node, child_node):
    """Test adding a child to a node."""
    parent_node.add_child(child_node)
    assert child_node in parent_node.children
    assert child_node.parent == parent_node


def test_add_child_idempotent(parent_node, child_node):
    """Test that adding the same child twice does not result in duplicates."""
    parent_node.add_child(child_node)
    parent_node.add_child(child_node)
    assert parent_node.children.count(child_node) == 1


def test_remove_child(parent_node, child_node):
    """Test removing a child from a node."""
    parent_node.add_child(child_node)
    parent_node.remove_child(child_node)
    assert child_node not in parent_node.children
    assert child_node.parent is None


def test_parent_setter(parent_node, child_node):
    """Test the parent property setter."""
    new_parent = SceneNode(name="new_parent")
    child_node.parent = parent_node
    assert child_node in parent_node.children
    child_node.parent = new_parent
    assert child_node not in parent_node.children
    assert child_node in new_parent.children
    assert child_node.parent == new_parent


def test_hit_test_no_children(parent_node):
    """Test hit_test on a node with no children."""
    assert parent_node.hit_test((5, 5)) is None


def test_hit_test_miss(parent_node):
    """Test a hit test that misses all children."""
    MockSceneNode(parent=parent_node, name="child1", pos=(0, 0), size=(10, 10))
    assert parent_node.hit_test((15, 15)) is None


def test_hit_test_hit_single_child(parent_node):
    """Test a hit test that hits a single child."""
    child = MockSceneNode(parent=parent_node, name="child1", pos=(0, 0), size=(10, 10))
    assert parent_node.hit_test((5, 5)) == child


def test_hit_test_hits_topmost_child(parent_node):
    """Test that hit_test returns the topmost child when children overlap."""
    MockSceneNode(parent=parent_node, name="child1", pos=(0, 0), size=(10, 10))
    child2 = MockSceneNode(parent=parent_node, name="child2", pos=(5, 5), size=(10, 10))
    # child2 was added last, so it's on top (rendered last, tested first)
    assert parent_node.hit_test((8, 8)) == child2


def test_hit_test_nested_children(parent_node):
    """Test hit testing with nested children."""
    child1 = MockSceneNode(parent=parent_node, name="child1", pos=(0, 0), size=(20, 20))
    nested_child = MockSceneNode(
        parent=child1, name="nested", pos=(5, 5), size=(10, 10)
    )
    assert parent_node.hit_test((10, 10)) == nested_child
    assert parent_node.hit_test((2, 2)) == child1


def test_hit_test_invisible_child(parent_node):
    """Test that invisible children are ignored by hit_test."""
    child = MockSceneNode(parent=parent_node, name="child1", pos=(0, 0), size=(10, 10))
    child.visible = False
    assert parent_node.hit_test((5, 5)) is None
