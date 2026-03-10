import logging
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.coordinate_service import CoordinateService
from src.services.tools.base_tool import BaseTool
from src.shared.constants import IconPath
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace


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
        self._drag_start_phys: Optional[tuple[float, float]] = None
        self._initial_geometries: dict[str, Rect] = {}
        self._resize_handle: Optional[str] = None
        
        # Handle hit threshold in CM (calculated from PX)
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
        phys_coords: tuple[float, float],
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
                handle_id = self._hit_test_handles(node, phys_coords)
                if handle_id:
                    self._mode = InteractionMode.RESIZING
                    self._resize_handle = handle_id
                    self._drag_start_phys = phys_coords
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
                    self._drag_start_phys = phys_coords
                    self._initial_geometries = {
                        n.id: n.geometry for n in self._model.selection if hasattr(n, "geometry")
                    }
                return

        # Clicked empty space
        self._model.set_selection([])
        self._mode = InteractionMode.NONE

    def mouse_move_event(
        self, phys_coords: tuple[float, float], modifiers: Optional[str] = None
    ) -> None:
        """Publishes preview updates based on current interaction mode."""
        if self._mode == InteractionMode.NONE or not self._drag_start_phys:
            return

        dx = phys_coords[0] - self._drag_start_phys[0]
        dy = phys_coords[1] - self._drag_start_phys[1]
        
        previews = []
        
        if self._mode == InteractionMode.MOVING:
            for node_id, initial_rect in self._initial_geometries.items():
                previews.append(initial_rect.moved_by(dx, dy))
                
        elif self._mode == InteractionMode.RESIZING:
            node_id, initial_rect = list(self._initial_geometries.items())[0]
            previews.append(initial_rect.scaled_by(self._resize_handle, dx, dy))
            
        self._event_aggregator.publish(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=previews,
            style="ghost"
        )

    def mouse_release_event(
        self, phys_coords: tuple[float, float], modifiers: Optional[str] = None
    ) -> None:
        """Finalizes the interaction and applies changes."""
        if self._mode == InteractionMode.NONE or not self._drag_start_phys:
            return

        self._event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)

        dx = phys_coords[0] - self._drag_start_phys[0]
        dy = phys_coords[1] - self._drag_start_phys[1]
        
        # Noise reduction (significant if delta > 0.01 cm)
        if abs(dx) > 0.01 or abs(dy) > 0.01:
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
        self._drag_start_phys = None
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

    def _hit_test_handles(self, node: PlotNode, phys_coords: tuple[float, float]) -> Optional[str]:
        """
        Checks if the click was on one of the 8 resize handles.
        """
        geom = node.geometry
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
        
        # Convert 12px threshold to CM using current context
        # We need the canvas width in px and figure width in cm
        canvas_w = self._canvas_widget.width()
        fig_w, _ = self._model.figure_size
        
        threshold_cm = CoordinateService.transform_value(
            self._handle_threshold_px,
            from_space=CoordinateSpace.DISPLAY_PX,
            to_space=CoordinateSpace.PHYSICAL,
            figure_size_cm=fig_w,
            canvas_size_px=float(canvas_w)
        )
        
        for handle_id, pos in handle_map.items():
            dist = ((pos[0] - phys_coords[0])**2 + (pos[1] - phys_coords[1])**2)**0.5
            if dist < threshold_cm:
                return handle_id
        return None
