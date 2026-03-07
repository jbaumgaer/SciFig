import logging
from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.tools.base_tool import BaseTool
from src.shared.constants import IconPath
from src.shared.events import Events
from src.shared.geometry import Rect


class SelectionTool(BaseTool):
    """
    A tool for selecting and moving nodes.
    Supports high-performance ghosting during drag operations.
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
        self._is_dragging = False
        self._drag_start_fig: Optional[tuple[float, float]] = None
        self._initial_geometries: dict[str, Rect] = {}

    @property
    def name(self) -> str:
        return "selection"

    @property
    def icon_path(self) -> str:
        return IconPath.get_path("tool_icons.select")

    def mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        """Handles selection and starts move interaction."""
        if button != Qt.MouseButton.LeftButton:
            return

        # 1. Handle Selection
        if node_id:
            node = self._model.scene_root.find_node_by_id(node_id)
            if node:
                # If clicking a new node, select only it
                if node not in self._model.selection:
                    self._model.set_selection([node])
                
                # 2. Start Move Interaction
                self._is_dragging = True
                self._drag_start_fig = fig_coords
                self._initial_geometries = {
                    n.id: n.geometry for n in self._model.selection if hasattr(n, "geometry")
                }
                return

        # Clicked empty space
        self._model.set_selection([])
        self._is_dragging = False

    def mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        """Publishes preview updates during dragging."""
        if not self._is_dragging or not self._drag_start_fig:
            return

        # Calculate delta from ORIGINAL press point to avoid jitter
        dx = fig_coords[0] - self._drag_start_fig[0]
        dy = fig_coords[1] - self._drag_start_fig[1]
        
        # Generate proposed geometries
        previews = []
        for node_id, initial_rect in self._initial_geometries.items():
            previews.append(initial_rect.moved_by(dx, dy))
            
        # Request UI overlay update
        self._event_aggregator.publish(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=previews,
            style="ghost"
        )

    def mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        """Finalizes the move and executes commands."""
        if not self._is_dragging or not self._drag_start_fig:
            return

        # 1. Clear preview
        self._event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)

        # 2. Calculate final delta
        dx = fig_coords[0] - self._drag_start_fig[0]
        dy = fig_coords[1] - self._drag_start_fig[1]
        
        # 3. Request Batch Move Command if delta is significant
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            new_geoms = {}
            for node_id, initial_rect in self._initial_geometries.items():
                new_geoms[node_id] = initial_rect.moved_by(dx, dy)
            
            self._event_aggregator.publish(
                Events.BATCH_CHANGE_PLOT_GEOMETRY_REQUESTED,
                geometries=new_geoms
            )

        # Reset State
        self._is_dragging = False
        self._drag_start_fig = None
        self._initial_geometries = {}

    def key_press_event(self, event: QKeyEvent) -> None:
        """Handles key presses for selection manipulation (e.g., Delete)."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            selection = self._model.selection
            if not selection:
                return

            node_ids = [node.id for node in selection]
            self.logger.info(f"SelectionTool: Requesting deletion of nodes: {node_ids}")
            self._event_aggregator.publish(Events.DELETE_NODES_REQUESTED, node_ids=node_ids)

    def paint_event(self, painter: QPainter) -> None:
        pass
