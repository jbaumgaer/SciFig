import pytest
from src.services.commands.add_plot_command import AddPlotCommand
from src.models.application_model import ApplicationModel
from src.shared.geometry import Rect
from src.shared.events import Events


@pytest.fixture
def app_model(mock_event_aggregator):
    return ApplicationModel(event_aggregator=mock_event_aggregator, figure_size=(20.0, 15.0))


class TestAddPlotCommand:
    """Unit tests for AddPlotCommand."""

    def test_execute_adds_node_and_publishes_events(self, app_model, mock_event_aggregator):
        """Verifies successful node addition."""
        geom = Rect(0.1, 0.1, 0.5, 0.5)
        cmd = AddPlotCommand(app_model, mock_event_aggregator, geom, node_name="TestPlot")
        
        cmd.execute()
        
        node = cmd.node
        assert node is not None
        assert node.name == "TestPlot"
        assert node.geometry == geom
        assert node in app_model.scene_root.children
        
        # Verify events
        mock_event_aggregator.publish.assert_any_call(Events.SCENE_GRAPH_CHANGED)
        mock_event_aggregator.publish.assert_any_call(
            Events.NODE_ADDED_TO_SCENE,
            parent_id=app_model.scene_root.id,
            new_node_id=node.id,
            index=0
        )

    def test_undo_removes_node(self, app_model, mock_event_aggregator):
        """Verifies that undo correctly removes the added node."""
        geom = Rect(0, 0, 1, 1)
        cmd = AddPlotCommand(app_model, mock_event_aggregator, geom)
        
        cmd.execute()
        assert len(app_model.scene_root.children) == 1
        node_id = cmd.node.id
        
        cmd.undo()
        assert len(app_model.scene_root.children) == 0
        mock_event_aggregator.publish.assert_any_call(
            Events.NODE_REMOVED_FROM_SCENE,
            parent_id=app_model.scene_root.id,
            removed_node_id=node_id
        )

    def test_redo_reuses_original_node(self, app_model, mock_event_aggregator):
        """Ensures that redoing doesn't create a new node but reuses the first one."""
        cmd = AddPlotCommand(app_model, mock_event_aggregator, Rect(0,0,1,1))
        
        cmd.execute()
        first_node = cmd.node
        
        cmd.undo()
        cmd.execute()
        
        assert cmd.node is first_node
        assert len(app_model.scene_root.children) == 1
