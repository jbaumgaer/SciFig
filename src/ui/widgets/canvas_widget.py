from typing import Optional
import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QPainter, QMouseEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget


# Ensure the backend is set for PySide6
matplotlib.use("QtAgg")


class CanvasWidget(QGraphicsView):
    """
    The main canvas widget that hosts the Matplotlib figure.
    It uses a QGraphicsView to allow for Illustrator-like panning and zooming,
    and it handles drag-and-drop events for data files.
    TODO: Remove the signals and move to events
    """

    # Signal emitted when a file is dropped onto the canvas
    # Emits file path (str) and drop position (QPointF) in scene coordinates.
    fileDropped = Signal(str, QPointF)
    canvasDoubleClicked = Signal(QPointF)  # New Signal

    def __init__(self, figure: Figure, parent: QWidget) -> None:
        #TODO: Check if I actually initiate this with a parent
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)

        # Use the figure passed from the model
        self.figure_canvas = FigureCanvasQTAgg(figure)
        self.scene.addWidget(self.figure_canvas)

        # Configure the Graphics View for better interaction
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setInteractive(True)

    def map_to_figure(self, scene_pos: QPointF) -> tuple[float, float]:
        """
        Translates a Qt scene position into normalized 0-1 figure coordinates.
        This handles the transformation from the QGraphicsView/Scene space 
        to the Matplotlib Figure space.
        """
        # 1. Map from Scene to the FigureCanvas widget coordinates (pixels)
        view_pos = self.mapFromScene(scene_pos)
        
        # 2. Get the figure and its transform
        fig = self.figure_canvas.figure
        inv = fig.transFigure.inverted()
        
        # 3. Use Matplotlib's inverse transform to get figure coordinates (0-1)
        # Note: We must invert the Y axis because Qt and Matplotlib have opposite Y origins
        height = self.figure_canvas.height()
        fig_coords = inv.transform((view_pos.x(), height - view_pos.y()))
        
        return tuple(fig_coords)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Overrides the mouse double-click event to perform hit-testing on PlotNodes
        and update the application model's selection.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert mouse position from widget coordinates to scene coordinates
            scene_pos = self.mapToScene(event.position().toPoint())

            # The CanvasController or a Tool (e.g., SelectionTool) is responsible for model interaction.
            # We'll emit a signal that the CanvasController can connect to.
            # For now, let's assume the CanvasController (or tool) will query the model.
            # This widget's role is primarily to emit the event with necessary info.

            # This signal will be connected to CanvasController.handle_canvas_double_click
            self.canvasDoubleClicked.emit(scene_pos)

            # We also need to call the parent's event to allow default behavior (e.g., zooming if interactive)
            super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        """Handles the event when a drag enters the widget."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Handles the event when a drag is moved over the widget."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Handles the event when a drop occurs."""
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                # Convert drop position from widget coordinates to scene coordinates
                scene_pos = self.mapToScene(event.position().toPoint())
                self.fileDropped.emit(file_path, scene_pos)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def wheelEvent(self, event):
        """
        Overrides the default wheel event to provide more intuitive navigation.
        - Ctrl + Scroll: Zooms the view.
        - Shift + Scroll: Scrolls horizontally.
        - Scroll: Scrolls vertically.
        """
        modifiers = event.modifiers()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            # --- Zooming ---
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
            # --- Horizontal Scrolling ---
            h_bar = self.horizontalScrollBar()
            h_bar.setValue(h_bar.value() - event.angleDelta().y())

        else:
            # --- Vertical Scrolling ---
            v_bar = self.verticalScrollBar()
            v_bar.setValue(v_bar.value() - event.angleDelta().y())
