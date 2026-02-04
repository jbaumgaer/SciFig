from unittest.mock import MagicMock, patch

import pytest
from matplotlib.figure import Figure
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView, QScrollBar

from src.views.canvas_widget import CanvasWidget


@pytest.fixture
def mock_figure():
    """Provides a real matplotlib Figure for tests."""
    fig = Figure(figsize=(5, 4), dpi=100)
    return fig


@pytest.fixture
def canvas_widget(qtbot, mock_figure):
    """Provides a CanvasWidget instance for tests."""
    widget = CanvasWidget(figure=mock_figure)
    qtbot.addWidget(widget)
    widget.show()  # Ensure widget is shown for event processing
    return widget


@pytest.fixture
def mock_mime_data_with_urls():
    """Provides a mock QMimeData with URLs."""
    mime_data = MagicMock(spec=QMimeData)
    mime_data.hasUrls.return_value = True
    mock_url = MagicMock(spec=QUrl)
    mock_url.isLocalFile.return_value = True
    mock_url.toLocalFile.return_value = "/path/to/test.csv"
    mime_data.urls.return_value = [mock_url]
    return mime_data


@pytest.fixture
def mock_mime_data_without_urls():
    """Provides a mock QMimeData without URLs."""
    mime_data = MagicMock(spec=QMimeData)
    mime_data.hasUrls.return_value = False
    return mime_data


# --- Test Drag and Drop Events ---


def test_drag_enter_event_with_urls(canvas_widget, mock_mime_data_with_urls):
    """Test dragEnterEvent accepts action when URLs are present."""
    mock_event = MagicMock(spec=QDragEnterEvent)
    mock_event.mimeData.return_value = mock_mime_data_with_urls

    canvas_widget.dragEnterEvent(mock_event)
    mock_event.acceptProposedAction.assert_called_once()


def test_drag_enter_event_without_urls(canvas_widget, mock_mime_data_without_urls):
    """Test dragEnterEvent defers to super class when no URLs are present."""
    mock_event = MagicMock(spec=QDragEnterEvent)
    mock_event.mimeData.return_value = mock_mime_data_without_urls

    with patch.object(QGraphicsView, "dragEnterEvent") as super_drag_enter_event:
        canvas_widget.dragEnterEvent(mock_event)
        super_drag_enter_event.assert_called_once_with(mock_event)
        mock_event.acceptProposedAction.assert_not_called()


def test_drag_move_event_with_urls(canvas_widget, mock_mime_data_with_urls):
    """Test dragMoveEvent accepts action when URLs are present."""
    mock_event = MagicMock(spec=QDragMoveEvent)
    mock_event.mimeData.return_value = mock_mime_data_with_urls

    canvas_widget.dragMoveEvent(mock_event)
    mock_event.acceptProposedAction.assert_called_once()


def test_drag_move_event_without_urls(canvas_widget, mock_mime_data_without_urls):
    """Test dragMoveEvent defers to super class when no URLs are present."""
    mock_event = MagicMock(spec=QDragMoveEvent)
    mock_event.mimeData.return_value = mock_mime_data_without_urls

    with patch.object(QGraphicsView, "dragMoveEvent") as super_drag_move_event:
        canvas_widget.dragMoveEvent(mock_event)
        super_drag_move_event.assert_called_once_with(mock_event)
        mock_event.acceptProposedAction.assert_not_called()


def test_drop_event_with_local_file_url(canvas_widget, mock_mime_data_with_urls):
    """Test dropEvent emits signal and accepts action for local file URLs."""
    mock_event = MagicMock(spec=QDropEvent)
    mock_event.mimeData.return_value = mock_mime_data_with_urls
    mock_event.position.return_value = QPointF(
        100.0, 50.0
    )  # Ensure QPointF is returned

    # Mock mapToScene to control scene position conversion
    with patch.object(
        canvas_widget, "mapToScene", return_value=QPointF(10.0, 5.0)
    ) as mock_map_to_scene:
        # Connect to the signal to check if it's emitted
        mock_slot = MagicMock()
        canvas_widget.fileDropped.connect(mock_slot)

        canvas_widget.dropEvent(mock_event)

        mock_event.acceptProposedAction.assert_called_once()
        mock_map_to_scene.assert_called_once_with(
            mock_event.position().toPoint()
        )  # Pass QPoint to mapToScene
        mock_slot.assert_called_once_with("/path/to/test.csv", QPointF(10.0, 5.0))


def test_drop_event_without_urls(canvas_widget, mock_mime_data_without_urls):
    """Test dropEvent defers to super class when no URLs are present."""
    mock_event = MagicMock(spec=QDropEvent)
    mock_event.mimeData.return_value = mock_mime_data_without_urls
    mock_event.position.return_value = QPointF(0.0, 0.0)  # Add QPointF here too

    with patch.object(QGraphicsView, "dropEvent") as super_drop_event:
        canvas_widget.dropEvent(mock_event)
        super_drop_event.assert_called_once_with(mock_event)
        mock_event.acceptProposedAction.assert_not_called()


# --- Test Wheel Events ---


@pytest.fixture
def mock_wheel_event(request):
    """Provides a mock QWheelEvent with configurable angleDelta and modifiers."""
    delta_y, modifiers = request.param
    mock_event = MagicMock(spec=QWheelEvent)
    mock_angle_delta = MagicMock(spec=QPoint)
    mock_angle_delta.y.return_value = delta_y
    mock_event.angleDelta.return_value = mock_angle_delta
    mock_event.modifiers.return_value = modifiers
    mock_event.position.return_value = QPointF(
        50.0, 50.0
    )  # A consistent QPointF position
    return mock_event


@pytest.mark.parametrize("mock_wheel_event", [(120, Qt.ControlModifier)], indirect=True)
def test_wheel_event_zoom_in(canvas_widget, mock_wheel_event):
    """Test wheelEvent zooms in with Ctrl + Scroll Up."""
    with (
        patch.object(canvas_widget, "scale") as mock_scale,
        patch.object(canvas_widget, "translate") as mock_translate,
        patch.object(
            canvas_widget, "mapToScene", side_effect=[QPointF(5, 5), QPointF(5.5, 5.5)]
        ) as mock_map_to_scene,
    ):

        canvas_widget.wheelEvent(mock_wheel_event)

        mock_scale.assert_called_once_with(pytest.approx(1.15), pytest.approx(1.15))
        mock_translate.assert_called_once()
        mock_map_to_scene.assert_called_with(
            mock_wheel_event.position().toPoint()
        )  # Called twice, ensure with QPoint


@pytest.mark.parametrize(
    "mock_wheel_event", [(-120, Qt.ControlModifier)], indirect=True
)
def test_wheel_event_zoom_out(canvas_widget, mock_wheel_event):
    """Test wheelEvent zooms out with Ctrl + Scroll Down."""
    with (
        patch.object(canvas_widget, "scale") as mock_scale,
        patch.object(canvas_widget, "translate") as mock_translate,
        patch.object(
            canvas_widget, "mapToScene", side_effect=[QPointF(5, 5), QPointF(4.5, 4.5)]
        ) as mock_map_to_scene,
    ):

        canvas_widget.wheelEvent(mock_wheel_event)

        mock_scale.assert_called_once_with(
            pytest.approx(1 / 1.15), pytest.approx(1 / 1.15)
        )
        mock_translate.assert_called_once()
        mock_map_to_scene.assert_called_with(
            mock_wheel_event.position().toPoint()
        )  # Called twice, ensure with QPoint


@pytest.mark.parametrize("mock_wheel_event", [(120, Qt.ShiftModifier)], indirect=True)
def test_wheel_event_horizontal_scroll(canvas_widget, mock_wheel_event):
    """Test wheelEvent scrolls horizontally with Shift + Scroll."""
    mock_h_bar = MagicMock(spec=QScrollBar)
    mock_h_bar.value.return_value = 500
    with patch.object(
        canvas_widget, "horizontalScrollBar", return_value=mock_h_bar
    ) as mock_get_h_bar:

        canvas_widget.wheelEvent(mock_wheel_event)

        mock_get_h_bar.assert_called_once()
        mock_h_bar.setValue.assert_called_once_with(mock_h_bar.value() - 120)


@pytest.mark.parametrize("mock_wheel_event", [(120, Qt.NoModifier)], indirect=True)
def test_wheel_event_vertical_scroll(canvas_widget, mock_wheel_event):
    """Test wheelEvent scrolls vertically with plain Scroll."""
    mock_v_bar = MagicMock(spec=QScrollBar)
    mock_v_bar.value.return_value = 500
    with patch.object(
        canvas_widget, "verticalScrollBar", return_value=mock_v_bar
    ) as mock_get_v_bar:

        canvas_widget.wheelEvent(mock_wheel_event)

        mock_get_v_bar.assert_called_once()
        mock_v_bar.setValue.assert_called_once_with(mock_v_bar.value() - 120)
