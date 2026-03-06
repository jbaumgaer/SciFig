import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from PySide6.QtCore import QPointF

from src.controllers.canvas_controller import CanvasController
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.group_node import GroupNode
from src.shared.events import Events


@pytest.fixture
def mock_mpl_event():
    """Provides a mock Matplotlib event object."""
    event = MagicMock()
    event.x = 100
    event.y = 100
    event.button = 1
    event.inaxes = MagicMock()
    event.xdata = 0.5
    event.ydata = 0.5
    return event


@pytest.fixture
def canvas_controller(mock_application_model, mock_event_aggregator, mock_canvas_widget, mock_tool_manager):
    """Provides a CanvasController instance with mocked dependencies."""
    # Mock figure transformation for coordinate conversion
    mock_fig = mock_canvas_widget.figure_canvas.figure
    mock_inv = MagicMock()
    mock_inv.transform.return_value = (0.5, 0.5)
    mock_fig.transFigure.inverted.return_value = mock_inv
    
    return CanvasController(
        model=mock_application_model,
        event_aggregator=mock_event_aggregator,
        canvas_widget=mock_canvas_widget,
        tool_manager=mock_tool_manager
    )


class TestCanvasController:

    # --- Initialization ---

    def test_initialization_connects_backend_events(self, mock_canvas_widget):
        """Verifies that the controller connects to Matplotlib and Qt signals."""
        mock_canvas = mock_canvas_widget.figure_canvas
        CanvasController(MagicMock(), MagicMock(), mock_canvas_widget, MagicMock())
        
        # Verify Matplotlib connections
        expected_signals = ["button_press_event", "motion_notify_event", "button_release_event", "pick_event"]
        connected_signals = [call[0][0] for call in mock_canvas.mpl_connect.call_args_list]
        for signal in expected_signals:
            assert signal in connected_signals
            
        # Verify Qt connections
        mock_canvas_widget.fileDropped.connect.assert_called_once()

    # --- Mouse Event Translation ---

    def test_on_mouse_press_resolves_node_and_dispatches(self, canvas_controller, mock_application_model, 
                                                       mock_tool_manager, mock_mpl_event):
        """Tests that mouse press resolves the correct node and notifies tool manager."""
        mock_node = MagicMock(id="node_123")
        mock_application_model.get_node_at.return_value = mock_node
        
        canvas_controller._on_mouse_press(mock_mpl_event)
        
        # Verify resolution
        mock_application_model.get_node_at.assert_called_once_with((0.5, 0.5))
        # Verify dispatch to headless tool service
        mock_tool_manager.dispatch_mouse_press_event.assert_called_once_with(
            "node_123", (0.5, 0.5), mock_mpl_event.button
        )

    def test_on_mouse_press_outside_clears_selection(self, canvas_controller, mock_event_aggregator, mock_mpl_event):
        """Tests that clicking in empty space clears the global selection."""
        mock_mpl_event.inaxes = None
        mock_mpl_event.xdata = None
        
        canvas_controller._on_mouse_press(mock_mpl_event)
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SELECTION_CHANGED, selected_node_ids=[]
        )

    def test_on_mouse_move_dispatches(self, canvas_controller, mock_tool_manager, mock_mpl_event):
        """Verifies move events are passed to tool manager."""
        canvas_controller._on_mouse_move(mock_mpl_event)
        mock_tool_manager.dispatch_mouse_move_event.assert_called_once_with((0.5, 0.5))

    def test_on_mouse_release_dispatches(self, canvas_controller, mock_tool_manager, mock_mpl_event):
        """Verifies release events are passed to tool manager."""
        canvas_controller._on_mouse_release(mock_mpl_event)
        mock_tool_manager.dispatch_mouse_release_event.assert_called_once_with((0.5, 0.5))

    # --- Pick Logic (Sub-selections) ---

    def test_on_pick_publishes_sub_component_event(self, canvas_controller, mock_application_model, 
                                                  mock_event_aggregator, mock_mpl_event):
        """Tests picking a specific artist (like an axis) within a plot."""
        mock_pick_event = MagicMock()
        mock_pick_event.artist.get_gid.return_value = "xaxis.label"
        mock_pick_event.mouseevent = mock_mpl_event
        
        mock_node = MagicMock(id="p1")
        mock_application_model.get_node_at.return_value = mock_node
        
        canvas_controller._on_pick(mock_pick_event)
        
        mock_event_aggregator.publish.assert_called_once_with(
            Events.SUB_COMPONENT_SELECTED, node_id="p1", path="xaxis.label"
        )

    def test_on_pick_no_gid_ignored(self, canvas_controller, mock_event_aggregator):
        """Verifies that picking generic artists without GIDs is ignored."""
        mock_pick_event = MagicMock()
        mock_pick_event.artist.get_gid.return_value = None
        
        canvas_controller._on_pick(mock_pick_event)
        mock_event_aggregator.publish.assert_not_called()

    # --- Drag and Drop ---

    def test_on_file_dropped_onto_plot_node(self, canvas_controller, mock_application_model, 
                                           mock_event_aggregator, mock_canvas_widget):
        """Tests dropping a file onto a PlotNode."""
        mock_canvas_widget.map_to_figure.return_value = (0.3, 0.3)
        plot_node = PlotNode(id="p1", name="Target")
        mock_application_model.get_node_at.return_value = plot_node
        
        canvas_controller.on_file_dropped("data.csv", QPointF(10, 10))
        mock_event_aggregator.publish.assert_called_once_with(
            Events.APPLY_DATA_FILE_REQUESTED,
            node_id="p1",
            file_path=Path("data.csv")
        )

    def test_on_file_dropped_onto_group_node_ignored(self, canvas_controller, mock_application_model, 
                                                    mock_event_aggregator, mock_canvas_widget):
        """Verifies that dropping files onto GroupNodes (not PlotNodes) does nothing."""
        mock_canvas_widget.map_to_figure.return_value = (0.3, 0.3)
        group_node = GroupNode(name="Group")
        mock_application_model.get_node_at.return_value = group_node
        
        canvas_controller.on_file_dropped("data.csv", QPointF(10, 10))
        mock_event_aggregator.publish.assert_not_called()

    def test_on_file_dropped_onto_empty_space_ignored(self, canvas_controller, mock_application_model, 
                                                     mock_event_aggregator, mock_canvas_widget):
        """Verifies that dropping files outside plot nodes does nothing."""
        mock_canvas_widget.map_to_figure.return_value = (0.9, 0.9)
        mock_application_model.get_node_at.return_value = None # Empty space
        
        canvas_controller.on_file_dropped("data.csv", QPointF(10, 10))
        mock_event_aggregator.publish.assert_not_called()

    # --- Robustness ---

    def test_on_mouse_press_inside_axes_but_no_node(self, canvas_controller, mock_application_model, 
                                                   mock_tool_manager, mock_mpl_event):
        """Tests clicking on background area of an axes (node_id should be None)."""
        mock_application_model.get_node_at.return_value = None
        
        canvas_controller._on_mouse_press(mock_mpl_event)
        
        # Verify dispatch with None node_id
        mock_tool_manager.dispatch_mouse_press_event.assert_called_once_with(
            None, (0.5, 0.5), mock_mpl_event.button
        )

    def test_on_pick_but_no_node_at_coordinates(self, canvas_controller, mock_application_model, 
                                               mock_event_aggregator, mock_mpl_event):
        """Verifies that picking an artist in 'no-man's land' does nothing."""
        mock_pick_event = MagicMock()
        mock_pick_event.artist.get_gid.return_value = "some_path"
        mock_pick_event.mouseevent = mock_mpl_event
        
        # Hit test fails despite pick (e.g. picking a non-PlotNode artist)
        mock_application_model.get_node_at.return_value = None
        
        canvas_controller._on_pick(mock_pick_event)
        mock_event_aggregator.publish.assert_not_called()
