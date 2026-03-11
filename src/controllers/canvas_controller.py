import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QKeyEvent

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.coordinate_service import CoordinateService
from src.services.event_aggregator import EventAggregator
from src.services.tool_service import ToolService
from src.shared.events import Events
from src.shared.types import CoordinateSpace
from src.ui.widgets.canvas_widget import CanvasWidget


class CanvasController(QObject):
    """
    Orchestrates interactions between the CanvasWidget (View) and the model/tools.
    Translates raw UI events into meaningful application intents.
    """

    def __init__(
        self,
        view: CanvasWidget,
        model: ApplicationModel,
        tool_service: ToolService,
        event_aggregator: EventAggregator,
    ):
        super().__init__()
        self._view = view
        self._model = model
        self._tool_service = tool_service
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)

        self._connect_view_signals()
        self._connect_backend_events()
        self._subscribe_to_events()
        self.logger.info("CanvasController initialized.")

    def _connect_view_signals(self):
        """Connects signals from the CanvasWidget to controller handlers."""
        self._view.canvasDoubleClicked.connect(self._on_canvas_double_clicked)
        self._view.fileDropped.connect(self._on_file_dropped)
        self._view.keyPressed.connect(self._on_key_pressed)

    def _connect_backend_events(self):
        """Connects Matplotlib backend events to controller handlers."""
        canvas = self._view.figure_canvas
        canvas.mpl_connect("button_press_event", self._on_mouse_press)
        canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        canvas.mpl_connect("button_release_event", self._on_mouse_release)

    def _subscribe_to_events(self):
        """Subscribes to application-level events."""
        pass

    def _get_physical_coords(self, event) -> tuple[float, float]:
        """
        Calculates physical figure coordinates (cm) from a Matplotlib event.
        """
        if event.x is None or event.y is None:
            return (0.0, 0.0)
            
        fig = self._view.figure_canvas.figure
        inv = fig.transFigure.inverted()
        normalized = inv.transform((event.x, event.y))
        
        fig_w, fig_h = self._model.figure_size
        cm_x = CoordinateService.transform_value(
            normalized[0],
            from_space=CoordinateSpace.FRACTIONAL_FIG,
            to_space=CoordinateSpace.PHYSICAL,
            figure_size_cm=fig_w
        )
        cm_y = CoordinateService.transform_value(
            normalized[1],
            from_space=CoordinateSpace.FRACTIONAL_FIG,
            to_space=CoordinateSpace.PHYSICAL,
            figure_size_cm=fig_h
        )
        return (cm_x, cm_y)

    def _map_mpl_button_to_qt(self, mpl_button: int) -> Qt.MouseButton:
        if mpl_button == 1:
            return Qt.MouseButton.LeftButton
        elif mpl_button == 2:
            return Qt.MouseButton.MiddleButton
        elif mpl_button == 3:
            return Qt.MouseButton.RightButton
        return Qt.MouseButton.NoButton

    def _on_mouse_press(self, event):
        phys_coords = self._get_physical_coords(event)
        hit_node = self._model.scene_root.hit_test(phys_coords)
        node_id = hit_node.id if hit_node else None
        qt_button = self._map_mpl_button_to_qt(event.button)
        
        self.logger.debug(f"Mouse press at {phys_coords}, hit: {node_id}, button: {qt_button}, key: {event.key}")
        self._tool_service.dispatch_mouse_press_event(
            node_id, phys_coords, qt_button, modifiers=event.key
        )

    def _on_mouse_move(self, event):
        phys_coords = self._get_physical_coords(event)
        self._tool_service.dispatch_mouse_move_event(phys_coords, modifiers=event.key)

    def _on_mouse_release(self, event):
        phys_coords = self._get_physical_coords(event)
        self._tool_service.dispatch_mouse_release_event(phys_coords, modifiers=event.key)

    def _on_key_pressed(self, event: QKeyEvent):
        self._tool_service.dispatch_key_press_event(event)

    def _on_canvas_double_clicked(self, scene_pos: QPointF):
        """
        Handles double-click on the canvas by performing a hit test
        and triggering selection/properties update.
        """
        norm_coords = self._view.map_to_figure(scene_pos)
        fig_w, fig_h = self._model.figure_size
        phys_coords = (norm_coords[0] * fig_w, norm_coords[1] * fig_h)
        self.logger.debug(f"Canvas double-clicked at figure coords: {phys_coords}")

        
        hit_node = self._model.scene_root.hit_test(phys_coords)
        if hit_node:
            self.logger.info(f"Hit node: {hit_node.name} (ID: {hit_node.id})")
            self._model.set_selection([hit_node])
        else:
            self._model.set_selection([])

    def _on_file_dropped(self, file_path: str, scene_pos: QPointF):
        """
        Handles data file drops by identifying the target node and
        requesting an application-level data apply operation.
        """
        norm_coords = self._view.map_to_figure(scene_pos)
        fig_w, fig_h = self._model.figure_size
        phys_coords = (norm_coords[0] * fig_w, norm_coords[1] * fig_h)
        
        node = self._model.scene_root.hit_test(phys_coords)
        if node and isinstance(node, PlotNode):
            self.logger.info(f"File {file_path} dropped onto node {node.id}")
            # Request high-level data application (handled by NodeController)
            self._event_aggregator.publish(
                Events.APPLY_DATA_TO_NODE_REQUESTED,
                node_id=node.id,
                file_path=Path(file_path),
            )

    @property
    def view(self):
        return self._view
