import logging
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.tools.base_tool import BaseTool
from src.shared.constants import IconPath
from src.shared.events import Events
from src.shared.geometry import Rect


class InteractionMode(Enum):
    NONE = auto()
    MOVING = auto()
    RESIZING = auto()


class SelectionTool(BaseTool):
    """
    A tool for selecting, moving, and resizing nodes.
    Supports high-performance ghosting and handle-based resizing.
    """

    plot_double_clicked = Signal(PlotNode)

    def __init__(
        self,
        model: ApplicationModel,
        canvas_widget,
        event_aggregator,
    ):
        super().__init__(model, canvas_widget, event_aggregator)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Interaction State
        self._mode = InteractionMode.NONE
        self._drag_start_fig: Optional[tuple[float, float]] = None
        self._initial_geometries: dict[str, Rect] = {}
        self._resize_handle: Optional[str] = None
        
        # Handle hit threshold (in pixels, will be converted to fig units)
        self._handle_threshold_px = 12

    @property
    def name(self) -> str:
        return "selection"

    @property
    def icon_path(self) -> str:
        return IconPath.get_path("tool_icons.select")

    def mouse_press_event(
        self,
        node_id: Optional[str],
        fig_coords: tuple[float, float],
        button: int,
        modifiers: Optional[str] = None,
    ) -> None:
        """Handles selection, move, or resize initialization."""
        if button != Qt.MouseButton.LeftButton:
            return

        # 1. Check for Resize Handles First (only if single selection)
        if len(self._model.selection) == 1:
            node = self._model.selection[0]
            if isinstance(node, PlotNode):
                handle_id = self._hit_test_handles(node, fig_coords)
                if handle_id:
                    self._mode = InteractionMode.RESIZING
                    self._resize_handle = handle_id
                    self._drag_start_fig = fig_coords
                    self._initial_geometries = {node.id: node.geometry}
                    self.logger.debug(f"SelectionTool: Starting RESIZE with handle {handle_id}")
                    return

        # 2. Handle Selection & Move
        if node_id:
            node = self._model.scene_root.find_node_by_id(node_id)
            if node:
                # Handle Multi-Selection logic (Shift-Click)
                if modifiers == "shift":
                    current_selection = list(self._model.selection)
                    if node in current_selection:
                        current_selection.remove(node)
                    else:
                        current_selection.append(node)
                    self._model.set_selection(current_selection)
                else:
                    # If clicking a node not in current selection, replace selection
                    if node not in self._model.selection:
                        self._model.set_selection([node])
                
                # Only initiate MOVING if selection is not empty after click
                if self._model.selection:
                    self._mode = InteractionMode.MOVING
                    self._drag_start_fig = fig_coords
                    self._initial_geometries = {
                        n.id: n.geometry for n in self._model.selection if hasattr(n, "geometry")
                    }
                return

        # Clicked empty space
        self._model.set_selection([])
        self._mode = InteractionMode.NONE

    def mouse_move_event(
        self, fig_coords: tuple[float, float], modifiers: Optional[str] = None
    ) -> None:
        """Publishes preview updates based on current interaction mode."""
        if self._mode == InteractionMode.NONE or not self._drag_start_fig:
            return

        dx = fig_coords[0] - self._drag_start_fig[0]
        dy = fig_coords[1] - self._drag_start_fig[1]
        
        previews = []
        
        if self._mode == InteractionMode.MOVING:
            for node_id, initial_rect in self._initial_geometries.items():
                previews.append(initial_rect.moved_by(dx, dy))
                
        elif self._mode == InteractionMode.RESIZING:
            # We only support single-node resize
            node_id, initial_rect = list(self._initial_geometries.items())[0]
            # Use the specialized scaling math in Rect
            previews.append(initial_rect.scaled_by(self._resize_handle, dx, dy))
            
        self._event_aggregator.publish(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=previews,
            style="ghost"
        )

    def mouse_release_event(
        self, fig_coords: tuple[float, float], modifiers: Optional[str] = None
    ) -> None:
        """Finalizes the interaction and applies changes."""
        if self._mode == InteractionMode.NONE or not self._drag_start_fig:
            return

        self._event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)

        dx = fig_coords[0] - self._drag_start_fig[0]
        dy = fig_coords[1] - self._drag_start_fig[1]
        
        # Apply changes if delta is significant (noise reduction)
        if abs(dx) > 0.0005 or abs(dy) > 0.0005:
            new_geoms = {}
            if self._mode == InteractionMode.MOVING:
                for node_id, initial_rect in self._initial_geometries.items():
                    new_geoms[node_id] = initial_rect.moved_by(dx, dy)
            elif self._mode == InteractionMode.RESIZING:
                node_id, initial_rect = list(self._initial_geometries.items())[0]
                new_geoms[node_id] = initial_rect.scaled_by(self._resize_handle, dx, dy)
            
            self._event_aggregator.publish(
                Events.BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED,
                geometries=new_geoms
            )

        # Reset State
        self._mode = InteractionMode.NONE
        self._drag_start_fig = None
        self._initial_geometries = {}
        self._resize_handle = None

    def key_press_event(self, event: QKeyEvent) -> None:
        """Handles key presses for selection manipulation."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selection = self._model.selection
            if not selection:
                return

            node_ids = [node.id for node in selection]
            self.logger.info(f"SelectionTool: Requesting deletion of nodes: {node_ids}")
            self._event_aggregator.publish(Events.DELETE_NODES_REQUESTED, node_ids=node_ids)

    def paint_event(self, painter: QPainter) -> None:
        pass

    def _hit_test_handles(self, node: PlotNode, fig_coords: tuple[float, float]) -> Optional[str]:
        """
        Checks if the click was on one of the 8 resize handles.
        Returns the handle identifier (e.g., 'top-left') or None.
        """
        geom = node.geometry
        # Define handle positions in figure coordinates (consistent with OverlayRenderer)
        handle_map = {
            "bottom-left": (geom.x, geom.y),
            "bottom": (geom.x + geom.width / 2, geom.y),
            "bottom-right": (geom.x + geom.width, geom.y),
            "right": (geom.x + geom.width, geom.y + geom.height / 2),
            "top-right": (geom.x + geom.width, geom.y + geom.height),
            "top": (geom.x + geom.width / 2, geom.y + geom.height),
            "top-left": (geom.x, geom.y + geom.height),
            "left": (geom.x, geom.y + geom.height / 2),
        }
        
        # Calculate dynamic threshold based on figure pixels
        # TODO: Get actual canvas size for precise 12px thresholding
        # For now, use a reasonable figure-unit approximation (0.02)
        threshold = 0.02 
        
        for handle_id, pos in handle_map.items():
            dist = ((pos[0] - fig_coords[0])**2 + (pos[1] - fig_coords[1])**2)**0.5
            if dist < threshold:
                return handle_id
        return None
