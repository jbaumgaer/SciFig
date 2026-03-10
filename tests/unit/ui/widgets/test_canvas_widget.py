import pytest
from unittest.mock import MagicMock, patch
from matplotlib.figure import Figure
from pathlib import Path
from PySide6.QtCore import QPointF, Qt, QUrl, QMimeData, QPoint, QEvent, QRectF
from PySide6.QtGui import (
    QMouseEvent, 
    QWheelEvent, 
    QDragEnterEvent, 
    QDragMoveEvent, 
    QDropEvent
)
from PySide6.QtWidgets import QGraphicsView, QScrollBar, QWidget, QGraphicsRectItem

from src.ui.widgets.canvas_widget import CanvasWidget
from src.shared.geometry import Rect


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
        
        # Patch CoordinateService to return a known normalized value
        with patch("src.ui.widgets.canvas_widget.CoordinateService.transform_value") as mock_transform:
            mock_transform.return_value = 0.5
            
            coords = canvas_widget.map_to_figure(scene_pos)
            
            assert coords == (0.5, 0.5)
            # Verify the service was called
            assert mock_transform.called

    def test_map_from_figure_logic(self, canvas_widget):
        """Verifies translation from figure coordinates back to scene coordinates."""
        fig_pos = (0.5, 0.5)
        
        # Patch CoordinateService to return known pixel values
        with patch("src.ui.widgets.canvas_widget.CoordinateService.transform_value") as mock_transform:
            mock_transform.return_value = 200.0
            
            scene_pos = canvas_widget.map_from_figure(fig_pos)
            
            assert isinstance(scene_pos, QPointF)
            assert mock_transform.called

    def test_map_rect_from_figure(self, canvas_widget):
        """Verifies Rect to QRectF translation."""
        fig_rect = Rect(0.1, 0.1, 0.2, 0.2)
        
        # We don't need detailed math here, just that it returns a QRectF
        with patch.object(canvas_widget, "map_from_figure") as mock_map:
            mock_map.side_effect = [QPointF(10, 10), QPointF(30, 30)]
            
            mapped_rect = canvas_widget.map_rect_from_figure(fig_rect)
            
            assert isinstance(mapped_rect, QRectF)
            assert mapped_rect.width() == pytest.approx(20)
            assert mapped_rect.height() == pytest.approx(20)

    # --- Preview Overlays ---

    def test_draw_preview_rect(self, canvas_widget):
        """Verifies adding preview items to the scene."""
        rect = QRectF(0, 0, 100, 100)
        
        item = canvas_widget.draw_preview_rect(rect, style="ghost")
        
        assert isinstance(item, QGraphicsRectItem)
        assert item in canvas_widget.scene.items()
        assert item in canvas_widget._preview_items
        assert item.zValue() == 1000

    def test_draw_handle(self, canvas_widget):
        """Verifies adding a resize handle to the scene."""
        pos = QPointF(50, 50)
        item = canvas_widget.draw_handle(pos)
        
        assert isinstance(item, QGraphicsRectItem)
        assert item.zValue() == 1100
        assert item.rect().center() == pos

    def test_draw_guide_line(self, canvas_widget):
        """Verifies adding a guide line to the scene."""
        p1, p2 = QPointF(0, 0), QPointF(100, 100)
        item = canvas_widget.draw_guide_line(p1, p2)
        
        from PySide6.QtWidgets import QGraphicsLineItem
        assert isinstance(item, QGraphicsLineItem)
        assert item.zValue() == 1050

    def test_clear_previews(self, canvas_widget):
        """Verifies cleanup of preview items."""
        canvas_widget.draw_preview_rect(QRectF(0, 0, 10, 10))
        canvas_widget.draw_handle(QPointF(20, 20))
        canvas_widget.draw_guide_line(QPointF(0, 0), QPointF(10, 10))
        
        assert len(canvas_widget._preview_items) == 3
        
        canvas_widget.clear_previews()
        
        assert len(canvas_widget._preview_items) == 0

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
