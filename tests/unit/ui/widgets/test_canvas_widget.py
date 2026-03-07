import pytest
from unittest.mock import MagicMock, patch
from matplotlib.figure import Figure
from pathlib import Path
from PySide6.QtCore import QPointF, Qt, QUrl, QMimeData, QPoint, QEvent
from PySide6.QtGui import (
    QMouseEvent, 
    QWheelEvent, 
    QDragEnterEvent, 
    QDragMoveEvent, 
    QDropEvent
)
from PySide6.QtWidgets import QGraphicsView, QScrollBar, QWidget

from src.ui.widgets.canvas_widget import CanvasWidget


@pytest.fixture
def mock_figure():
    """Provides a real matplotlib Figure for tests."""
    return Figure(figsize=(5, 4), dpi=100)


@pytest.fixture
def canvas_widget(qtbot, mock_figure):
    """Provides a fresh CanvasWidget instance."""
    canvas = CanvasWidget(figure=mock_figure, parent=None)
    qtbot.addWidget(canvas)
    canvas.show()
    return canvas


class TestCanvasWidget:
    """
    Unit tests for CanvasWidget.
    Verifies interaction logic, signal emission, and coordinate transformations.
    """

    # --- Initialization & Structure ---

    def test_initialization(self, canvas_widget):
        """Verifies that the widget initializes with correct properties."""
        assert canvas_widget.acceptDrops()
        assert canvas_widget.dragMode() == QGraphicsView.DragMode.ScrollHandDrag
        assert canvas_widget.isInteractive()
        assert canvas_widget.scene is not None

    # --- Double-Click Events ---

    def test_mouse_double_click_emits_signal(self, canvas_widget, qtbot):
        """Verifies that double-clicking the canvas emits the canvasDoubleClicked signal."""
        # Create a double-click event
        pos = QPoint(50, 50)
        event = QMouseEvent(
            QEvent.Type.MouseButtonDblClick,
            QPointF(pos),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # Connect to signal
        with qtbot.waitSignal(canvas_widget.canvasDoubleClicked, timeout=1000) as blocker:
            canvas_widget.mouseDoubleClickEvent(event)
            
        # Verify signal payload (scene coordinates)
        scene_pos = blocker.args[0]
        assert isinstance(scene_pos, QPointF)

    # --- Drag and Drop Events ---

    def test_drag_enter_event_accepts_urls(self, canvas_widget):
        """Verifies that dragEnterEvent accepts URL mime data."""
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("test.csv")])
        
        event = QDragEnterEvent(
            QPoint(0, 0), 
            Qt.DropAction.CopyAction, 
            mime_data, 
            Qt.MouseButton.LeftButton, 
            Qt.KeyboardModifier.NoModifier
        )
        
        event.acceptProposedAction = MagicMock()
        canvas_widget.dragEnterEvent(event)
        event.acceptProposedAction.assert_called_once()

    def test_drop_event_emits_file_dropped_signal(self, canvas_widget, qtbot):
        """Verifies that dropping a file emits the fileDropped signal."""
        file_path = "C:/test_data.csv"
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])
        
        pos = QPoint(100, 100)
        event = QDropEvent(
            QPointF(pos),
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        with qtbot.waitSignal(canvas_widget.fileDropped, timeout=1000) as blocker:
            canvas_widget.dropEvent(event)
            
        dropped_path, scene_pos = blocker.args
        assert "test_data.csv" in dropped_path.replace("\\", "/")
        assert isinstance(scene_pos, QPointF)

    # --- Coordinate Mapping ---

    def test_map_to_figure_logic(self, canvas_widget):
        """Verifies translation from scene coordinates to normalized figure coordinates."""
        scene_pos = QPointF(10, 10)
        
        with patch.object(canvas_widget.figure_canvas.figure.transFigure, "inverted") as mock_inv_cls:
            mock_inv = MagicMock()
            mock_inv_cls.return_value = mock_inv
            mock_inv.transform.return_value = [0.5, 0.5]
            
            coords = canvas_widget.map_to_figure(scene_pos)
            
            assert coords == (0.5, 0.5)
            # Verify the transform was called
            assert mock_inv.transform.called

    # --- Wheel Events (Navigation) ---

    @pytest.mark.parametrize("delta, expected_scale", [
        (120, 1.15),      # Zoom In
        (-120, 1/1.15),   # Zoom Out
    ])
    def test_wheel_event_zoom(self, canvas_widget, delta, expected_scale):
        """Verifies zooming with Ctrl + Scroll."""
        event = QWheelEvent(
            QPointF(50, 50),
            QPointF(50, 50),
            QPoint(0, 0),
            QPoint(0, delta),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        
        with patch.object(canvas_widget, "scale") as mock_scale:
            with patch.object(canvas_widget, "translate"):
                canvas_widget.wheelEvent(event)
                mock_scale.assert_called_with(pytest.approx(expected_scale), pytest.approx(expected_scale))

    def test_wheel_event_horizontal_scroll(self, canvas_widget):
        """Verifies horizontal scrolling with Shift + Scroll."""
        event = QWheelEvent(
            QPointF(50, 50),
            QPointF(50, 50),
            QPoint(0, 0),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ShiftModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        
        mock_bar = MagicMock(spec=QScrollBar)
        mock_bar.value.return_value = 500
        
        with patch.object(canvas_widget, "horizontalScrollBar", return_value=mock_bar):
            canvas_widget.wheelEvent(event)
            mock_bar.setValue.assert_called_with(500 - 120)

    def test_wheel_event_vertical_scroll(self, canvas_widget):
        """Verifies vertical scrolling with plain Scroll."""
        event = QWheelEvent(
            QPointF(50, 50),
            QPointF(50, 50),
            QPoint(0, 0),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        
        mock_bar = MagicMock(spec=QScrollBar)
        mock_bar.value.return_value = 500
        
        with patch.object(canvas_widget, "verticalScrollBar", return_value=mock_bar):
            canvas_widget.wheelEvent(event)
            mock_bar.setValue.assert_called_with(500 - 120)
