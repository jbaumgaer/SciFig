import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QPointF, Qt, Signal, QRectF
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QBrush, QColor, QKeyEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from src.services.coordinate_service import CoordinateService
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace

# Ensure the backend is set for PySide6
matplotlib.use("QtAgg")


class CanvasWidget(QGraphicsView):
    """
    The main canvas widget that hosts the Matplotlib figure.
    It uses a QGraphicsView to allow for Illustrator-like panning and zooming.
    """

    fileDropped = Signal(str, QPointF)
    canvasDoubleClicked = Signal(QPointF)
    keyPressed = Signal(QKeyEvent)

    def __init__(self, figure: Figure, parent: QWidget) -> None:
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        
        # Ensure the widget can receive focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 1. Initialize FigureCanvas
        self.figure_canvas = FigureCanvasQTAgg(figure)
        # Ensure no internal Qt margins interfere with Matplotlib's geometry
        self.figure_canvas.setContentsMargins(0, 0, 0, 0)
        
        # 2. Add to scene and align origin
        proxy = self.scene.addWidget(self.figure_canvas)
        proxy.setPos(0, 0)
        
        # 3. Size the scene to match the figure exactly
        self.scene.setSceneRect(0, 0, self.figure_canvas.width(), self.figure_canvas.height())

        # Configure the Graphics View for better interaction
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setInteractive(True)

        # Track preview items for easy cleanup
        self._preview_items: list[QGraphicsItem] = []

    def map_to_figure(self, scene_pos: QPointF) -> tuple[float, float]:
        """
        Translates a Qt scene position into normalized 0-1 figure coordinates.
        Delegates math to CoordinateService.
        """
        view_pos = self.mapFromScene(scene_pos)
        width, height = self.figure_canvas.get_width_height()
        
        if width == 0 or height == 0:
            return (0.0, 0.0)

        fig_x = CoordinateService.transform_value(
            view_pos.x(),
            from_space=CoordinateSpace.DISPLAY_PX,
            to_space=CoordinateSpace.FRACTIONAL_FIG,
            canvas_size_px=float(width)
        )
        # Convert top-down Qt Y to bottom-up Normalized Y
        px_y_bottom_up = height - view_pos.y()
        fig_y = CoordinateService.transform_value(
            px_y_bottom_up,
            from_space=CoordinateSpace.DISPLAY_PX,
            to_space=CoordinateSpace.FRACTIONAL_FIG,
            canvas_size_px=float(height)
        )
        return (float(fig_x), float(fig_y))

    def map_from_figure(self, fig_pos: tuple[float, float]) -> QPointF:
        """
        Translates normalized 0-1 figure coordinates back to Qt scene coordinates.
        Delegates math to CoordinateService.
        """
        width, height = self.figure_canvas.get_width_height()
        
        px_x = CoordinateService.transform_value(
            fig_pos[0],
            from_space=CoordinateSpace.FRACTIONAL_FIG,
            to_space=CoordinateSpace.DISPLAY_PX,
            canvas_size_px=float(width)
        )
        px_y_bottom_up = CoordinateService.transform_value(
            fig_pos[1],
            from_space=CoordinateSpace.FRACTIONAL_FIG,
            to_space=CoordinateSpace.DISPLAY_PX,
            canvas_size_px=float(height)
        )
        # Convert bottom-up Normalized Y to top-down Qt Y
        view_y = height - px_y_bottom_up
        
        return self.mapToScene(px_x, view_y)

    def map_rect_from_figure(self, fig_rect: Rect) -> QRectF:
        """
        Converts a normalized figure Rect into a Qt Scene QRectF.
        """
        p1 = self.map_from_figure((fig_rect.x, fig_rect.y))
        p2 = self.map_from_figure((fig_rect.x + fig_rect.width, fig_rect.y + fig_rect.height))
        return QRectF(p1, p2).normalized()

    def draw_preview_rect(self, rect: QRectF, style: str = "ghost") -> QGraphicsRectItem:
        item = QGraphicsRectItem(rect)
        item.setZValue(1000)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        
        if style == "ghost":
            item.setPen(QPen(QColor(0, 120, 215), 1))
            item.setBrush(QBrush(QColor(0, 120, 215, 60)))
        elif style == "rubber_band":
            pen = QPen(QColor(100, 100, 100), 1, Qt.DashLine)
            item.setPen(pen)
            item.setBrush(QBrush(Qt.NoBrush))
            
        self.scene.addItem(item)
        self._preview_items.append(item)
        return item

    def draw_handle(self, pos: QPointF) -> QGraphicsRectItem:
        """Draws a resize handle. Size remains 12px as requested."""
        size = 12
        rect = QRectF(pos.x() - size / 2, pos.y() - size / 2, size, size)
        item = QGraphicsRectItem(rect)
        item.setZValue(1100)
        item.setBrush(QBrush(Qt.white))
        item.setPen(QPen(QColor(0, 120, 215), 1))
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.scene.addItem(item)
        self._preview_items.append(item)
        return item

    def draw_guide_line(self, p1: QPointF, p2: QPointF) -> QGraphicsLineItem:
        item = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
        item.setZValue(1050)
        item.setPen(QPen(QColor(255, 0, 255), 1, Qt.DashLine))
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.scene.addItem(item)
        self._preview_items.append(item)
        return item

    def clear_previews(self) -> None:
        for item in self._preview_items:
            if item.scene():
                self.scene.removeItem(item)
        self._preview_items.clear()

    def keyPressEvent(self, event: QKeyEvent):
        """Captures and emits keyboard events."""
        self.keyPressed.emit(event)
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.canvasDoubleClicked.emit(scene_pos)
            super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                scene_pos = self.mapToScene(event.position().toPoint())
                self.fileDropped.emit(file_path, scene_pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.15
            zoom_out_factor = 1 / zoom_in_factor
            old_pos = self.mapToScene(event.position().toPoint())
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            h_bar = self.horizontalScrollBar()
            h_bar.setValue(h_bar.value() - event.angleDelta().y())
        else:
            v_bar = self.verticalScrollBar()
            v_bar.setValue(v_bar.value() - event.angleDelta().y())
