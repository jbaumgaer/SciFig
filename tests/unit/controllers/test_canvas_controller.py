import pytest
from unittest.mock import MagicMock, ANY
from pathlib import Path
from PySide6.QtCore import QPointF

from src.controllers.canvas_controller import CanvasController
from src.models.nodes.plot_node import PlotNode
from src.shared.events import Events


@pytest.fixture
def canvas_controller(mock_application_model, mock_event_aggregator, mock_canvas_widget, mock_tool_manager):
    """Provides a CanvasController instance with mocked dependencies."""
    return CanvasController(
        view=mock_canvas_widget,
        model=mock_application_model,
        tool_service=mock_tool_manager,
        event_aggregator=mock_event_aggregator
    )


class TestCanvasController:
    """
    Unit tests for CanvasController.
    Verifies signal orchestration and coordinate mapping between View and Model.
    """

    # --- Initialization ---

    def test_initialization_connects_view_signals(self, mock_canvas_widget):
        """Verifies that the controller connects to the CanvasWidget signals."""
        mock_tool_manager = MagicMock()
        mock_event_aggregator = MagicMock()
        controller = CanvasController(
            view=mock_canvas_widget,
            model=MagicMock(),
            tool_service=mock_tool_manager,
            event_aggregator=mock_event_aggregator
        )
        
        mock_canvas_widget.canvasDoubleClicked.connect.assert_called_once_with(controller._on_canvas_double_clicked)
        mock_canvas_widget.fileDropped.connect.assert_called_once_with(controller._on_file_dropped)

    def test_initialization_subscribes_to_events(self, mock_event_aggregator, mock_canvas_widget):
        """Verifies that the controller subscribes to relevant notification events."""
        controller = CanvasController(
            view=mock_canvas_widget,
            model=MagicMock(),
            tool_service=MagicMock(),
            event_aggregator=mock_event_aggregator
        )
        
        # Current implementation only subscribes to data apply requests
        mock_event_aggregator.subscribe.assert_any_call(Events.APPLY_DATA_FILE_REQUESTED, ANY)

    # --- Interaction Logic ---

    def test_on_canvas_double_clicked_resolves_node_and_selects(self, canvas_controller, mock_canvas_widget, mock_application_model):
        """Verifies that double-clicking selects the hit node."""
        scene_pos = QPointF(100, 100)
        fig_coords = (0.5, 0.5)
        mock_canvas_widget.map_to_figure.return_value = fig_coords
        
        mock_node = MagicMock(spec=PlotNode)
        mock_node.name = "TestPlot"
        mock_node.id = "p1"
        mock_application_model.scene_root.hit_test.return_value = mock_node
        
        canvas_controller._on_canvas_double_clicked(scene_pos)
        
        mock_canvas_widget.map_to_figure.assert_called_once_with(scene_pos)
        mock_application_model.scene_root.hit_test.assert_called_once_with(fig_coords)
        mock_application_model.set_selection.assert_called_once_with([mock_node])

    def test_on_file_dropped_onto_plot_node(self, canvas_controller, mock_canvas_widget, mock_application_model, mock_event_aggregator):
        """Verifies that dropping a file onto a node publishes a load request."""
        scene_pos = QPointF(50, 50)
        mock_canvas_widget.map_to_figure.return_value = (0.2, 0.2)
        
        mock_node = MagicMock(spec=PlotNode)
        mock_node.id = "p1"
        mock_application_model.scene_root.hit_test.return_value = mock_node
        
        canvas_controller._on_file_dropped("data.csv", scene_pos)
        
        mock_event_aggregator.publish.assert_any_call(
            Events.APPLY_DATA_FILE_REQUESTED,
            node_id="p1",
            file_path=Path("data.csv")
        )

    def test_on_apply_data_file_request_forwards_to_node_controller(self, canvas_controller, mock_event_aggregator):
        """Verifies that the internal data file request is forwarded to the application bus."""
        file_path = Path("data.csv")
        canvas_controller._on_apply_data_file_request("p1", file_path)
        
        mock_event_aggregator.publish.assert_called_with(
            Events.APPLY_DATA_TO_NODE_REQUESTED,
            node_id="p1",
            file_path=file_path
        )
