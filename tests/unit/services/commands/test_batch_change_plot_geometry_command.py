import pytest
from unittest.mock import MagicMock
from src.services.commands.batch_change_plot_geometry_command import BatchChangePlotGeometryCommand
from src.models.nodes.plot_node import PlotNode
from src.shared.events import Events


class TestBatchChangePlotGeometryCommand:

    def test_initialization_captures_current_state(self, mock_application_model, mock_event_aggregator):
        """Verifies that the command captures current geometries during init."""
        p1 = PlotNode(id="p1")
        p1.geometry = (0, 0, 0.5, 0.5)
        mock_application_model.scene_root.all_descendants.return_value = [p1]
        
        new_geoms = {"p1": (0.1, 0.1, 0.4, 0.4)}
        command = BatchChangePlotGeometryCommand(
            mock_application_model, mock_event_aggregator, new_geoms, "Move p1"
        )
        
        assert command._old_geometries["p1"] == (0, 0, 0.5, 0.5)

    def test_execute_applies_new_geometries_and_publishes(self, mock_application_model, mock_event_aggregator):
        """Tests applying changes to multiple nodes."""
        p1 = PlotNode(id="p1"); p1.name = "P1"
        p2 = PlotNode(id="p2"); p2.name = "P2"
        mock_application_model.scene_root.all_descendants.return_value = [p1, p2]
        
        # Helper for find_node_by_id logic in execute
        def find_side_effect(node_id):
            return {"p1": p1, "p2": p2}.get(node_id)
        mock_application_model.scene_root.find_node_by_id.side_effect = find_side_effect
        
        new_geoms = {
            "p1": (0.1, 0.1, 0.1, 0.1),
            "p2": (0.2, 0.2, 0.2, 0.2)
        }
        command = BatchChangePlotGeometryCommand(
            mock_application_model, mock_event_aggregator, new_geoms, "Batch Move"
        )
        
        command.execute()
        
        assert p1.geometry == (0.1, 0.1, 0.1, 0.1)
        assert p2.geometry == (0.2, 0.2, 0.2, 0.2)
        mock_event_aggregator.publish.assert_called_with(Events.SCENE_GRAPH_CHANGED)

    def test_undo_reverts_state(self, mock_application_model, mock_event_aggregator):
        """Verifies that undo restores the captured geometries."""
        p1 = PlotNode(id="p1")
        p1.geometry = (0.5, 0.5, 0.5, 0.5)
        mock_application_model.scene_root.all_descendants.return_value = [p1]
        mock_application_model.scene_root.find_node_by_id.return_value = p1
        
        new_geoms = {"p1": (0, 0, 1, 1)}
        command = BatchChangePlotGeometryCommand(
            mock_application_model, mock_event_aggregator, new_geoms, "Full Size"
        )
        
        command.execute()
        assert p1.geometry == (0, 0, 1, 1)
        
        command.undo()
        assert p1.geometry == (0.5, 0.5, 0.5, 0.5)
        assert mock_event_aggregator.publish.call_count == 2 # 1 for execute, 1 for undo

    def test_missing_node_is_handled_gracefully(self, mock_application_model, mock_event_aggregator, caplog):
        """Ensures command logs a warning but doesn't crash if a node is missing."""
        mock_application_model.scene_root.all_descendants.return_value = []
        mock_application_model.scene_root.find_node_by_id.return_value = None
        
        new_geoms = {"ghost": (0, 0, 1, 1)}
        command = BatchChangePlotGeometryCommand(
            mock_application_model, mock_event_aggregator, new_geoms, "Ghost Move"
        )
        
        with caplog.at_level("WARNING"):
            command.execute()
            
        assert "Could not find PlotNode with ID ghost" in caplog.text

    def test_empty_request_is_safe(self, mock_application_model, mock_event_aggregator):
        """Tests that empty geometry dict is a safe no-op."""
        command = BatchChangePlotGeometryCommand(
            mock_application_model, mock_event_aggregator, {}, "No-op"
        )
        command.execute()
        command.undo()
        # Should not crash
