import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from src.services.tools.selection_tool import SelectionTool
from src.shared.events import Events
from src.shared.constants import LayoutMode
from src.models.nodes.grid_node import GridNode, GridPosition
from src.models.nodes.plot_node import PlotNode
from src.shared.geometry import Rect


@pytest.fixture
def tool(mock_application_model, mock_canvas_widget, mock_event_aggregator):
    """Provides a fresh SelectionTool instance."""
    return SelectionTool(
        model=mock_application_model,
        canvas_widget=mock_canvas_widget,
        event_aggregator=mock_event_aggregator
    )


class TestSelectionTool:
    """Unit tests for SelectionTool."""

    def test_mouse_press_selects_node(self, tool, mock_application_model):
        """Verifies that clicking on a node ID selects it in the model."""
        mock_node = MagicMock()
        mock_node.name = "Test Node"
        mock_application_model.scene_root.find_node_by_id.return_value = mock_node
        
        tool.mouse_press_event("node_1", (0.5, 0.5), Qt.MouseButton.LeftButton)
        
        mock_application_model.set_selection.assert_called_once_with([mock_node])

    def test_mouse_press_empty_space_clears_selection(self, tool, mock_application_model):
        """Verifies that clicking on empty space (no node_id) clears selection."""
        tool.mouse_press_event(None, (0.5, 0.5), Qt.MouseButton.LeftButton)
        
        mock_application_model.set_selection.assert_called_once_with([])

    def test_delete_key_publishes_event(self, tool, mock_application_model, mock_event_aggregator):
        """Verifies that pressing Delete publishes a deletion request."""
        node1 = MagicMock()
        node1.id = "n1"
        node2 = MagicMock()
        node2.id = "n2"
        mock_application_model.selection = [node1, node2]
        
        # Mock event
        mock_event = MagicMock()
        mock_event.key.return_value = Qt.Key.Key_Delete
        
        tool.key_press_event(mock_event)
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.DELETE_NODES_REQUESTED,
            node_ids=["n1", "n2"]
        )

    def test_delete_key_with_no_selection_is_no_op(self, tool, mock_application_model, mock_event_aggregator):
        """Ensures Delete key does nothing if no nodes are selected."""
        mock_application_model.selection = []
        
        mock_event = MagicMock()
        mock_event.key.return_value = Qt.Key.Key_Delete
        
        tool.key_press_event(mock_event)
        
        mock_event_aggregator.publish.assert_not_called()

    def test_mouse_drag_publishes_preview(self, tool, mock_application_model, mock_event_aggregator):
        """Verifies that dragging a selected node publishes preview events."""
        from src.shared.geometry import Rect
        from src.services.tools.selection_tool import InteractionMode
        node = MagicMock()
        node.id = "p1"
        node.geometry = Rect(0.1, 0.1, 0.2, 0.2)
        mock_application_model.selection = [node]
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # 1. Press on node
        tool.mouse_press_event("p1", (0.15, 0.15), Qt.MouseButton.LeftButton)
        assert tool._mode == InteractionMode.MOVING
        
        # 2. Drag
        tool.mouse_move_event((0.25, 0.25))
        
        # Delta is (0.1, 0.1). New geom should be Rect(0.2, 0.2, 0.2, 0.2)
        mock_event_aggregator.publish.assert_any_call(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=[Rect(0.2, 0.2, 0.2, 0.2)],
            style="ghost"
        )

    def test_mouse_release_publishes_move_request(self, tool, mock_application_model, mock_event_aggregator):
        """Verifies that releasing the mouse after a drag publishes a geometry change request."""
        from src.shared.geometry import Rect
        node = MagicMock()
        node.id = "p1"
        node.geometry = Rect(0.1, 0.1, 0.2, 0.2)
        mock_application_model.selection = [node]
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        tool.mouse_press_event("p1", (0.1, 0.1), Qt.MouseButton.LeftButton)
        tool.mouse_release_event((0.2, 0.3)) # dx=0.1, dy=0.2
        
        # Should clear preview
        mock_event_aggregator.publish.assert_any_call(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)
        
        # Should publish batch geometry change
        expected_geoms = {"p1": Rect(0.2, 0.3, 0.2, 0.2)}
        mock_event_aggregator.publish.assert_any_call(
            Events.BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED,
            geometries=expected_geoms
        )

    def test_shift_click_multi_select(self, tool, mock_application_model):
        """Verifies that Shift-clicking appends or removes nodes from selection."""
        node1 = MagicMock()
        node1.id = "n1"
        node2 = MagicMock()
        node2.id = "n2"
        
        # 1. First click (no shift) selects node 1
        mock_application_model.scene_root.find_node_by_id.side_effect = lambda id: node1 if id == "n1" else node2
        mock_application_model.selection = []
        
        tool.mouse_press_event("n1", (0.5, 0.5), Qt.MouseButton.LeftButton)
        mock_application_model.set_selection.assert_called_with([node1])
        
        # 2. Shift-click node 2 appends it
        mock_application_model.selection = [node1]
        tool.mouse_press_event("n2", (0.5, 0.5), Qt.MouseButton.LeftButton, modifiers="shift")
        mock_application_model.set_selection.assert_called_with([node1, node2])
        
        # 3. Shift-click node 1 removes it
        mock_application_model.selection = [node1, node2]
        tool.mouse_press_event("n1", (0.5, 0.5), Qt.MouseButton.LeftButton, modifiers="shift")
        mock_application_model.set_selection.assert_called_with([node2])

    def test_grid_snapping_and_collision(self, mock_application_model, mock_canvas_widget, mock_event_aggregator):
        """Verifies snapping and collision handling in GRID mode."""
        # 1. Setup Grid Environment
        mock_application_model.current_layout_config.mode = LayoutMode.GRID
        
        # Instantiate tool MANUALLY to ensure it sees the updated mock state
        tool = SelectionTool(
            model=mock_application_model,
            canvas_widget=mock_canvas_widget,
            event_aggregator=mock_event_aggregator
        )
        
        root = GridNode(id="root_grid", parent=mock_application_model.scene_root, rows=2, cols=2)
        root.geometry = Rect(0, 0, 10, 10)
        
        # P1: Occupies (0,0)
        p1 = PlotNode(id="p1", parent=root)
        p1.grid_position = GridPosition(0, 0)
        p1.geometry = Rect(0, 0, 4.5, 4.5)
        
        # P2: Occupies (1,1)
        p2 = PlotNode(id="p2", parent=root)
        p2.grid_position = GridPosition(1, 1)
        p2.geometry = Rect(5.5, 5.5, 4.5, 4.5)
        
        mock_application_model.scene_root.find_node_by_id.side_effect = lambda id: p1 if id == "p1" else p2
        mock_application_model.selection = [p1]
        mock_application_model.figure_size = (10, 10)

        # 2. Start Drag on P1 (mouse down at center of 0,0)
        tool.mouse_press_event("p1", (2.25, 2.25), Qt.MouseButton.LeftButton)
        
        # 3. Move over P2 (center of 1,1 is roughly 7.75, 7.75)
        # Mouse coords at (7.75, 7.75) should snap P1's ghost to (1,1)
        tool.mouse_move_event((7.75, 7.75))
        
        # Verify preview style is 'blocked' because P2 is there
        mock_event_aggregator.publish.assert_called_with(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=[Rect(5.5, 5.5, 4.5, 4.5)], # Snapped to (1,1)
            style="blocked"
        )
        
        # 4. Release while blocked
        tool.mouse_release_event((7, 7))
        
        # Verify no property change was published
        # (It would have been BATCH_CHANGE_PLOT_PROPERTY_REQUESTED)
        calls = [c for c in mock_event_aggregator.publish.call_args_list if c[0][0] == Events.BATCH_CHANGE_PLOT_PROPERTY_REQUESTED]
        assert len(calls) == 0
