import pytest
from unittest.mock import MagicMock, ANY
from src.services.tools.add_plot_tool import AddPlotTool
from src.shared.events import Events
from src.shared.geometry import Rect


@pytest.fixture
def mock_model():
    return MagicMock()


@pytest.fixture
def tool(mock_model, mock_canvas_widget, mock_event_aggregator):
    return AddPlotTool(mock_model, mock_canvas_widget, mock_event_aggregator)


class TestAddPlotTool:
    """Unit tests for AddPlotTool."""

    def test_mouse_drag_publishes_preview(self, tool, mock_event_aggregator):
        """Verifies that dragging publishes rubber-band preview events."""
        tool.mouse_press_event((0.1, 0.1))
        tool.mouse_move_event((0.3, 0.4))
        
        mock_event_aggregator.publish.assert_any_call(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=[Rect(0.1, 0.1, 0.2, 0.3)],
            style="rubber_band"
        )

    def test_mouse_release_large_drag_requests_plot(self, tool, mock_event_aggregator):
        """Verifies that a large drag results in an ADD_PLOT_REQUESTED event."""
        tool.mouse_press_event((0.1, 0.1))
        tool.mouse_release_event((0.5, 0.5))
        
        # Should clear preview first
        mock_event_aggregator.publish.assert_any_call(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)
        
        # Should request plot creation
        mock_event_aggregator.publish.assert_any_call(
            Events.ADD_PLOT_REQUESTED,
            geometry=Rect(0.1, 0.1, 0.4, 0.4)
        )

    def test_mouse_release_small_click_requests_dialog(self, tool, mock_event_aggregator):
        """Verifies that a near-zero drag results in a SHOW_ADD_PLOT_DIALOG_REQUESTED event."""
        tool.mouse_press_event((0.1, 0.1))
        # Very small movement
        tool.mouse_release_event((0.1001, 0.1001))
        
        mock_event_aggregator.publish.assert_any_call(
            Events.SHOW_ADD_PLOT_DIALOG_REQUESTED,
            center_pos=(0.1, 0.1)
        )

    def test_escape_cancels_interaction(self, tool, mock_event_aggregator):
        """Verifies that pressing Escape cancels the current dragging operation."""
        tool.mouse_press_event((0.1, 0.1))
        tool.mouse_move_event((0.5, 0.5))
        
        # Mock escape key event
        from PySide6.QtCore import Qt
        mock_event = MagicMock()
        mock_event.key.return_value = Qt.Key.Key_Escape
        
        tool.key_press_event(mock_event)
        
        assert not tool._is_pressed
        mock_event_aggregator.publish.assert_any_call(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)
        
        # Subsequent release should do nothing
        mock_event_aggregator.publish.reset_mock()
        tool.mouse_release_event((0.5, 0.5))
        mock_event_aggregator.publish.assert_not_called()
