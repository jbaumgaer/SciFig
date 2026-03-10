import logging
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
)
from matplotlib.figure import Figure

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.coordinate_service import CoordinateService
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace


class OverlayRenderer:
    """
    The Interaction Layer Renderer.
    Passively listens for selection and tool-interaction events to draw
    transient Qt GraphicsItems (handles, ghosts, guides, highlights) onto a QGraphicsScene.
    """

    def __init__(
        self, 
        scene: QGraphicsScene, 
        figure: Figure, 
        model: ApplicationModel, 
        event_aggregator: EventAggregator
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._scene = scene
        self._figure = figure
        self._model = model
        self._event_aggregator = event_aggregator
        
        # Track persistent items
        self._ghost_items: list[QGraphicsRectItem] = []
        self._handle_items: list[QGraphicsRectItem] = []
        self._guide_items: list[QGraphicsLineItem] = []
        self._highlight_items: list[QGraphicsRectItem] = []
        
        # Style Definitions
        #TODO: Move styles to a config or theme system
        self._ghost_pen = QPen(QColor(0, 120, 215), 1)
        self._ghost_brush = QBrush(QColor(0, 120, 215, 60))
        self._rubber_band_pen = QPen(QColor(100, 100, 100), 1, Qt.DashLine)
        
        self._handle_pen = QPen(QColor(0, 120, 215), 1)
        self._handle_brush = QBrush(Qt.white)
        
        self._selection_pen = QPen(QColor(100, 149, 237), 4) # Doubled from 2
        self._selection_brush = QBrush(Qt.NoBrush)
        
        self._guide_pen = QPen(QColor(255, 0, 255), 1, Qt.DashLine)

        self._subscribe_to_events()

    def _subscribe_to_events(self):
        """Wires the renderer to the application event bus."""
        self._event_aggregator.subscribe(
            Events.SELECTION_CHANGED, self._on_selection_changed
        )
        self._event_aggregator.subscribe(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED, self._on_update_previews_request
        )
        self._event_aggregator.subscribe(
            Events.CLEAR_INTERACTION_PREVIEW_REQUESTED, self.clear_previews
        )
        # Refresh overlays on structural or geometry changes
        self._event_aggregator.subscribe(
            Events.SCENE_GRAPH_CHANGED, self._on_scene_graph_changed
        )

    def _on_scene_graph_changed(self, *args, **kwargs):
        """
        Refreshes all overlays to ensure they align with updated model geometries.
        """
        # We use the existing selection handler to perform the redraw
        selected_ids = [node.id for node in self._model.selection]
        self._on_selection_changed(selected_ids)

    def _on_selection_changed(self, selected_node_ids: list[str]):
        """Reactive handler for drawing highlights and handles."""
        self.clear_handles()
        self.clear_highlights()
        
        # 1. Draw Highlights for all selected nodes
        for node_id in selected_node_ids:
            node = self._model.scene_root.find_node_by_id(node_id)
            if isinstance(node, PlotNode):
                self._draw_highlight_for_node(node)
        
        # 2. Draw Handles only for single selection
        if len(selected_node_ids) == 1:
            node = self._model.scene_root.find_node_by_id(selected_node_ids[0])
            if isinstance(node, PlotNode):
                self._draw_handles_for_node(node)

    def _on_update_previews_request(self, geometries: list[Rect], style: str = "ghost"):
        """Reactive handler for drawing ghosts/rubber-bands."""
        self.clear_previews()
        
        for geom in geometries:
            scene_rect = self._fig_rect_to_scene(geom)
            item = QGraphicsRectItem(scene_rect)
            item.setZValue(1000)
            item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            
            if style == "ghost":
                item.setPen(self._ghost_pen)
                item.setBrush(self._ghost_brush)
            elif style == "rubber_band":
                item.setPen(self._rubber_band_pen)
                item.setBrush(Qt.NoBrush)
                
            self._scene.addItem(item)
            self._ghost_items.append(item)

    def clear_all(self, *args, **kwargs):
        """Removes all interaction items from the scene."""
        self.clear_handles()
        self.clear_highlights()
        self.clear_previews()
        self.clear_guides()

    def clear_handles(self):
        for item in self._handle_items:
            if item.scene():
                self._scene.removeItem(item)
        self._handle_items.clear()

    def clear_highlights(self):
        for item in self._highlight_items:
            if item.scene():
                self._scene.removeItem(item)
        self._highlight_items.clear()

    def clear_previews(self, *args, **kwargs):
        for item in self._ghost_items:
            if item.scene():
                self._scene.removeItem(item)
        self._ghost_items.clear()

    def clear_guides(self):
        for item in self._guide_items:
            if item.scene():
                self._scene.removeItem(item)
        self._guide_items.clear()

    def _draw_highlight_for_node(self, node: PlotNode):
        """Draws a selection outline around the node."""
        scene_rect = self._fig_rect_to_scene(node.geometry)
        item = QGraphicsRectItem(scene_rect)
        item.setZValue(990) # Just below ghosts
        item.setPen(self._selection_pen)
        item.setBrush(self._selection_brush)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(item)
        self._highlight_items.append(item)

    def _draw_handles_for_node(self, node: PlotNode):
        """Draws 8 resize handles around the given node's bounding box."""
        geom = node.geometry
        handle_points = [
            (geom.x, geom.y),
            (geom.x + geom.width / 2, geom.y),
            (geom.x + geom.width, geom.y),
            (geom.x + geom.width, geom.y + geom.height / 2),
            (geom.x + geom.width, geom.y + geom.height),
            (geom.x + geom.width / 2, geom.y + geom.height),
            (geom.x, geom.y + geom.height),
            (geom.x, geom.y + geom.height / 2),
        ]
        
        for p in handle_points:
            scene_p = self._fig_to_scene(p)
            self._add_handle(scene_p)

    def _fig_to_scene(self, phys_pos: tuple[float, float]) -> QPointF:
        """Maps physical CM figure coordinates to scene pixels."""
        fig_w_cm, fig_h_cm = self._model.figure_size
        canvas_w, canvas_h = self._figure.canvas.get_width_height()
        
        px_x = CoordinateService.transform_value(
            phys_pos[0],
            from_space=CoordinateSpace.PHYSICAL,
            to_space=CoordinateSpace.DISPLAY_PX,
            figure_size_cm=fig_w_cm,
            canvas_size_px=float(canvas_w)
        )
        # Matplotlib Y is bottom-up (0 at bottom), 
        # Qt Scene Y is top-down (0 at top).
        px_y_bottom_up = CoordinateService.transform_value(
            phys_pos[1],
            from_space=CoordinateSpace.PHYSICAL,
            to_space=CoordinateSpace.DISPLAY_PX,
            figure_size_cm=fig_h_cm,
            canvas_size_px=float(canvas_h)
        )
        px_y = canvas_h - px_y_bottom_up
        
        return QPointF(px_x, px_y)

    def _fig_rect_to_scene(self, fig_rect: Rect) -> QRectF:
        """Maps a physical figure Rect to a Qt Scene QRectF."""
        p1 = self._fig_to_scene((fig_rect.x, fig_rect.y))
        p2 = self._fig_to_scene((fig_rect.x + fig_rect.width, fig_rect.y + fig_rect.height))
        return QRectF(p1, p2).normalized()

    def _add_handle(self, pos: QPointF):
        #TODO: Move styles to a config or theme system
        size = 12 # Doubled from 6
        rect = QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
        item = QGraphicsRectItem(rect)
        item.setZValue(1100)
        item.setPen(self._handle_pen)
        item.setBrush(self._handle_brush)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(item)
        self._handle_items.append(item)
