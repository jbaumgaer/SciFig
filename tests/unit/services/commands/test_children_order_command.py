import pytest
from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode
from src.services.commands.change_children_order_command import ChangeChildrenOrderCommand
from src.shared.events import Events


@pytest.fixture
def app_model(mock_event_aggregator):
    """Provides a real ApplicationModel."""
    return ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20.0, 15.0))


@pytest.fixture
def scene_tree(app_model):
    """
    Root
    └── Group (g1)
        ├── Node 0 (n0)
        ├── Node 1 (n1)
        └── Node 2 (n2)
    """
    g1 = GroupNode(name="g1", id="g1")
    n0 = SceneNode(name="n0", id="n0")
    n1 = SceneNode(name="n1", id="n1")
    n2 = SceneNode(name="n2", id="n2")
    
    app_model.scene_root.add_child(g1)
    g1.add_child(n0)
    g1.add_child(n1)
    g1.add_child(n2)
    
    return {"app": app_model, "g1": g1, "n0": n0, "n1": n1, "n2": n2}


class TestChangeChildrenOrderCommand:
    """Unit tests for ChangeChildrenOrderCommand."""

    def test_execute_reorders_children(self, scene_tree, mock_event_aggregator):
        """Verifies that a node is moved from its old index to a new one."""
        app = scene_tree["app"]
        g1 = scene_tree["g1"]
        # Move n0 from index 0 to index 2
        cmd = ChangeChildrenOrderCommand(app, mock_event_aggregator, "g1", "n0", 0, 2)
        
        cmd.execute()
        
        assert g1.children == [scene_tree["n1"], scene_tree["n2"], scene_tree["n0"]]
        mock_event_aggregator.publish.assert_called_with(
            Events.NODE_ORDER_CHANGED_IN_SCENE,
            parent_id="g1",
            new_ordered_child_ids=["n1", "n2", "n0"]
        )

    def test_undo_restores_original_order(self, scene_tree, mock_event_aggregator):
        """Verifies that undo reverses the reordering."""
        app = scene_tree["app"]
        g1 = scene_tree["g1"]
        # Move n2 from index 2 to index 0
        cmd = ChangeChildrenOrderCommand(app, mock_event_aggregator, "g1", "n2", 2, 0)
        
        cmd.execute()
        cmd.undo()
        
        assert g1.children == [scene_tree["n0"], scene_tree["n1"], scene_tree["n2"]]
        # Last call should be the undo notification
        mock_event_aggregator.publish.assert_called_with(
            Events.NODE_ORDER_CHANGED_IN_SCENE,
            parent_id="g1",
            new_ordered_child_ids=["n0", "n1", "n2"]
        )

    def test_execute_fails_on_missing_parent(self, scene_tree, mock_event_aggregator, caplog):
        """Verifies that missing parent nodes are handled safely."""
        app = scene_tree["app"]
        cmd = ChangeChildrenOrderCommand(app, mock_event_aggregator, "invalid_parent", "n0", 0, 1)
        
        cmd.execute()
        
        assert "not found" in caplog.text
        # No reordering should have happened in g1
        assert scene_tree["g1"].children[0].id == "n0"

    def test_execute_fails_if_node_not_in_parent(self, scene_tree, mock_event_aggregator, caplog):
        """Verifies that requests for nodes not belonging to the parent are rejected."""
        app = scene_tree["app"]
        # n0 is in g1, but we tell the command it's in the scene_root
        cmd = ChangeChildrenOrderCommand(app, mock_event_aggregator, app.scene_root.id, "n0", 0, 1)
        
        cmd.execute()
        
        assert "not belonging to parent" in caplog.text
