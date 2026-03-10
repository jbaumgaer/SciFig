import pytest
from unittest.mock import MagicMock
from src.services.commands.delete_node_command import DeleteNodeCommand
from src.models.application_model import ApplicationModel
from src.models.nodes.scene_node import SceneNode
from src.shared.events import Events


@pytest.fixture
def app_model(mock_event_aggregator):
    """Provides a real ApplicationModel with a mock event aggregator."""
    return ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20.0, 15.0))


@pytest.fixture
def scene_tree(app_model):
    """
    Root
    ├── Node 1 (n1)
    └── Node 2 (n2)
    """
    n1 = SceneNode(name="n1", id="n1")
    n2 = SceneNode(name="n2", id="n2")
    app_model.scene_root.add_child(n1)
    app_model.scene_root.add_child(n2)
    return {"app": app_model, "n1": n1, "n2": n2}


class TestDeleteNodeCommand:
    """Unit tests for DeleteNodeCommand."""

    def test_execute_removes_node_and_publishes_events(self, scene_tree, mock_event_aggregator):
        """Verifies that node is removed and events are fired."""
        app = scene_tree["app"]
        cmd = DeleteNodeCommand(app, mock_event_aggregator, "n1")
        
        cmd.execute()
        
        assert app.scene_root.find_node_by_id("n1") is None
        assert scene_tree["n1"] not in app.scene_root.children
        
        # Verify events
        mock_event_aggregator.publish.assert_any_call(
            Events.NODE_REMOVED_FROM_SCENE, 
            parent_id=app.scene_root.id, 
            removed_node_id="n1"
        )
        mock_event_aggregator.publish.assert_any_call(Events.SCENE_GRAPH_CHANGED)

    def test_undo_restores_node_at_correct_index(self, scene_tree, mock_event_aggregator):
        """Verifies that undo puts the node back exactly where it was."""
        app = scene_tree["app"]
        n1 = scene_tree["n1"]
        n2 = scene_tree["n2"]
        
        # Initial order: [n1, n2]
        cmd = DeleteNodeCommand(app, mock_event_aggregator, "n1")
        
        cmd.execute()
        assert app.scene_root.children == [n2]
        
        cmd.undo()
        assert app.scene_root.children == [n1, n2]
        assert n1.parent is app.scene_root

    def test_delete_fails_gracefully_on_missing_node(self, scene_tree, mock_event_aggregator, caplog):
        """Ensures that attempting to delete a non-existent node doesn't crash."""
        app = scene_tree["app"]
        cmd = DeleteNodeCommand(app, mock_event_aggregator, "non_existent")
        
        cmd.execute()
        assert "not found" in caplog.text
        assert len(app.scene_root.children) == 2

    def test_delete_root_is_prevented(self, app_model, mock_event_aggregator, caplog):
        """Ensures the root node itself cannot be deleted."""
        root_id = app_model.scene_root.id
        cmd = DeleteNodeCommand(app_model, mock_event_aggregator, root_id)
        
        cmd.execute()
        assert "no parent" in caplog.text
        assert app_model.scene_root is not None
