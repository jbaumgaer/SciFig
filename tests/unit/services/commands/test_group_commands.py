import pytest
from unittest.mock import MagicMock
from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode
from src.services.commands.group_nodes_command import GroupNodesCommand
from src.services.commands.ungroup_nodes_command import UngroupNodesCommand
from src.shared.events import Events


@pytest.fixture
def app_model(mock_event_aggregator):
    """Provides a real ApplicationModel with a mock event aggregator."""
    return ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20.0, 15.0))


@pytest.fixture
def scene_tree(app_model):
    """
    Sets up a sample scene tree:
    Root
    ├── Node 1 (n1)
    ├── Node 2 (n2)
    └── Group A (g1)
        ├── Node 3 (n3)
        └── Node 4 (n4)
    """
    n1 = SceneNode(name="n1", id="n1")
    n2 = SceneNode(name="n2", id="n2")
    g1 = GroupNode(name="g1", id="g1")
    n3 = SceneNode(name="n3", id="n3")
    n4 = SceneNode(name="n4", id="n4")
    
    app_model.scene_root.add_child(n1)
    app_model.scene_root.add_child(n2)
    app_model.scene_root.add_child(g1)
    g1.add_child(n3)
    g1.add_child(n4)
    
    return {"app": app_model, "n1": n1, "n2": n2, "g1": g1, "n3": n3, "n4": n4}


class TestGroupNodesCommand:
    """Unit tests for GroupNodesCommand."""

    def test_execute_groups_nodes_under_new_parent(self, scene_tree, mock_event_aggregator):
        """Verifies that selected nodes are moved into a new GroupNode."""
        app = scene_tree["app"]
        cmd = GroupNodesCommand(app, mock_event_aggregator, ["n1", "n2"], group_name="NewGroup")
        
        cmd.execute()
        
        # Verify new group creation
        new_group_id = cmd.group_id
        assert new_group_id is not None
        new_group = app.scene_root.find_node_by_id(new_group_id)
        assert isinstance(new_group, GroupNode)
        assert new_group.name == "NewGroup"
        
        # Verify nodes moved
        assert scene_tree["n1"].parent is new_group
        assert scene_tree["n2"].parent is new_group
        assert scene_tree["n1"] in new_group.children
        assert scene_tree["n2"] in new_group.children
        
        # Verify old parent (root) no longer has them
        assert scene_tree["n1"] not in app.scene_root.children
        assert scene_tree["n2"] not in app.scene_root.children
        
        mock_event_aggregator.publish.assert_called_with(Events.SCENE_GRAPH_CHANGED)

    def test_undo_restores_original_hierarchy(self, scene_tree, mock_event_aggregator):
        """Verifies that undo moves nodes back to their original parents."""
        app = scene_tree["app"]
        cmd = GroupNodesCommand(app, mock_event_aggregator, ["n3", "n4"], group_name="SubGroup")
        
        cmd.execute()
        cmd.undo()
        
        # Verify nodes moved back to original parent (g1)
        assert scene_tree["n3"].parent is scene_tree["g1"]
        assert scene_tree["n4"].parent is scene_tree["g1"]
        assert scene_tree["n3"] in scene_tree["g1"].children
        
        # Verify the temporary group is removed
        assert app.scene_root.find_node_by_id(cmd.group_id) is None

    def test_grouping_mixed_parents_defaults_to_root(self, scene_tree, mock_event_aggregator):
        """Verifies that grouping nodes with different parents moves the group to the root."""
        app = scene_tree["app"]
        # n1 is in root, n3 is in g1
        cmd = GroupNodesCommand(app, mock_event_aggregator, ["n1", "n3"])
        
        cmd.execute()
        
        new_group = app.scene_root.find_node_by_id(cmd.group_id)
        assert new_group.parent is app.scene_root
        assert scene_tree["n1"].parent is new_group
        assert scene_tree["n3"].parent is new_group


class TestUngroupNodesCommand:
    """Unit tests for UngroupNodesCommand."""

    def test_execute_moves_children_to_parent_and_removes_group(self, scene_tree, mock_event_aggregator):
        """Verifies that ungrouping moves children up one level."""
        app = scene_tree["app"]
        g1 = scene_tree["g1"]
        cmd = UngroupNodesCommand(app, mock_event_aggregator, "g1")
        
        cmd.execute()
        
        # Verify children moved to root (g1's parent)
        assert scene_tree["n3"].parent is app.scene_root
        assert scene_tree["n4"].parent is app.scene_root
        assert scene_tree["n3"] in app.scene_root.children
        
        # Verify group is gone
        assert app.scene_root.find_node_by_id("g1") is None
        assert g1.parent is None

    def test_undo_recreates_group_and_reclaims_children(self, scene_tree, mock_event_aggregator):
        """Verifies that undo restores the group and its content."""
        app = scene_tree["app"]
        cmd = UngroupNodesCommand(app, mock_event_aggregator, "g1")
        
        cmd.execute()
        cmd.undo()
        
        # Verify group is back
        new_g1 = app.scene_root.find_node_by_id("g1")
        assert isinstance(new_g1, GroupNode)
        assert new_g1.parent is app.scene_root
        
        # Verify children are back inside
        assert scene_tree["n3"].parent is new_g1
        assert scene_tree["n4"].parent is new_g1
        assert scene_tree["n3"] in new_g1.children
