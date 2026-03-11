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
from src.models.nodes.grid_node import GridNode
from src.services.coordinate_service import CoordinateService
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace
from src.shared.constants import LayoutMode


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
        self._grid_items: list[QGraphicsItem] = []  # Track grid lattice items
        
        # Style Definitions
        #TODO: Move styles to a config or theme system
        self._ghost_pen = QPen(QColor(0, 120, 215), 1)
        self._ghost_brush = QBrush(QColor(0, 120, 215, 60))
        self._rubber_band_pen = QPen(QColor(100, 100, 100), 1, Qt.DashLine)
        
        self._handle_pen = QPen(QColor(0, 120, 215), 1)
        self._handle_brush = QBrush(Qt.white)
        
        self._selection_pen = QPen(QColor(100, 149, 237), 4)
        self._selection_brush = QBrush(Qt.NoBrush)
        
        self._guide_pen = QPen(QColor(255, 0, 255), 1, Qt.DashLine)

        # Grid Styles (New for Grid 2.0)
        self._gutter_brush = QBrush(QColor(150, 150, 150, 40))
        self._gutter_pen = QPen(Qt.NoPen)
        self._divider_pen = QPen(QColor(100, 100, 100, 150), 3) # Increased to 3px thickness
        self._ink_box_pen = QPen(QColor(100, 100, 100, 80), 1, Qt.DotLine)

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
        # Refresh overlays on structural, geometry, or mode changes
        self._event_aggregator.subscribe(
            Events.SCENE_GRAPH_CHANGED, self._on_scene_graph_changed
        )
        self._event_aggregator.subscribe(
            Events.NODE_LAYOUT_RECONCILED, self._on_scene_graph_changed
        )

    def _on_scene_graph_changed(self, *args, **kwargs):
        """Refreshes all overlays to ensure they align with updated model geometries."""
        selected_ids = [node.id for node in self._model.selection]
        self._on_selection_changed(selected_ids)

    def _on_selection_changed(self, selected_node_ids: list[str]):
        """Reactive handler for drawing highlights and handles."""
        self.clear_handles()
        self.clear_highlights()
        self.clear_grid_items()
        
        # 1. Recursive Grid Overlay
        if self._model.layout_mode == LayoutMode.GRID:
            for node in self._model.scene_root.all_descendants(of_type=GridNode):
                self._draw_grid_overlay(node)

        # 2. Draw Highlights and Ink-Box Ghosts for selected nodes
        for node_id in selected_node_ids:
            node = self._model.scene_root.find_node_by_id(node_id)
            if isinstance(node, PlotNode):
                self._draw_highlight_for_node(node)
                self._draw_ink_box_ghost(node)
        
        # 3. Draw Handles only for single selection
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
        self.clear_grid_items()

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

    def clear_grid_items(self):
        """Clears all grid lattice and gutter items."""
        for item in self._grid_items:
            if item.scene():
                self._scene.removeItem(item)
        self._grid_items.clear()

    def _draw_highlight_for_node(self, node: PlotNode):
        """Draws a selection outline around the node."""
        scene_rect = self._fig_rect_to_scene(node.geometry)
        item = QGraphicsRectItem(scene_rect)
        item.setZValue(990)
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
        size = 12
        rect = QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
        item = QGraphicsRectItem(rect)
        item.setZValue(1100)
        item.setPen(self._handle_pen)
        item.setBrush(self._handle_brush)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(item)
        self._handle_items.append(item)

    def _draw_grid_overlay(self, grid_node: GridNode):
        """Draws the visual lattice, gutter bands, and interactive dividers using cached geometries."""
        cells = grid_node.cell_geometries
        if not cells or not cells[0]:
            return

        num_rows = len(cells)
        num_cols = len(cells[0])
        
        # Use grid_node geometry as the reference for top-level bounds
        geom = grid_node.geometry

        # 1. Draw Gutter Zones (Grey Bands)
        # Vertical Gutters
        for c in range(num_cols - 1):
            left_cell = cells[0][c]
            right_cell = cells[0][c+1]
            gutter_x = left_cell.x + left_cell.width
            gutter_w = right_cell.x - gutter_x
            if gutter_w > 0.001:
                gutter_rect = Rect(gutter_x, geom.y, gutter_w, geom.height)
                self._add_grid_item(QGraphicsRectItem(self._fig_rect_to_scene(gutter_rect).normalized()), is_gutter=True)

        # Horizontal Gutters
        for r in range(num_rows - 1):
            top_cell = cells[r][0]
            bottom_cell = cells[r+1][0]
            gutter_y = bottom_cell.y + bottom_cell.height
            gutter_h = top_cell.y - gutter_y
            if gutter_h > 0.001:
                gutter_rect = Rect(geom.x, gutter_y, geom.width, gutter_h)
                self._add_grid_item(QGraphicsRectItem(self._fig_rect_to_scene(gutter_rect).normalized()), is_gutter=True)

        # 2. Draw Divider Lines (Center of gutters)
        for c in range(num_cols - 1):
            x = cells[0][c].x + cells[0][c].width + (grid_node.gutters.wspace[c] / 2 if c < len(grid_node.gutters.wspace) else 0.25)
            p1 = self._fig_to_scene((x, geom.y))
            p2 = self._fig_to_scene((x, geom.y + geom.height))
            self._add_grid_item(QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y()), is_divider=True)

        for r in range(num_rows - 1):
            y = cells[r+1][0].y + cells[r+1][0].height + (grid_node.gutters.hspace[r] / 2 if r < len(grid_node.gutters.hspace) else 0.25)
            p1 = self._fig_to_scene((geom.x, y))
            p2 = self._fig_to_scene((geom.x + geom.width, y))
            self._add_grid_item(QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y()), is_divider=True)

        # 3. Outer Border
        scene_rect = self._fig_rect_to_scene(geom)
        self._add_grid_item(QGraphicsRectItem(scene_rect), is_divider=True)

    def _add_grid_item(self, item: QGraphicsItem, is_gutter: bool = False, is_divider: bool = False):
        """Helper to style and track grid visual items with high Z-Order."""
        if is_gutter:
            item.setPen(self._gutter_pen)
            item.setBrush(self._gutter_brush)
            item.setZValue(2000) # Ensure on top
        elif is_divider:
            item.setPen(self._divider_pen)
            item.setZValue(2010) # Ensure dividers are on top of gutters
            
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(item)
        self._grid_items.append(item)

    def _draw_ink_box_ghost(self, node: PlotNode):
        """Draws a faint dotted rectangle representing the total ink extent."""
        geom = node.geometry
        ink_geom = Rect(
            x=geom.x - geom.width * 0.1,
            y=geom.y - geom.height * 0.1,
            width=geom.width * 1.2,
            height=geom.height * 1.2
        )
        
        scene_rect = self._fig_rect_to_scene(ink_geom)
        item = QGraphicsRectItem(scene_rect)
        item.setPen(self._ink_box_pen)
        item.setBrush(Qt.NoBrush)
        item.setZValue(985)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._scene.addItem(item)
        self._grid_items.append(item)
