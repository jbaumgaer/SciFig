import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QKeyEvent

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.event_aggregator import EventAggregator
from src.services.tool_service import ToolService
from src.shared.events import Events
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
        """Subscribes to relevant events from the aggregator."""
        self._event_aggregator.subscribe(
            Events.APPLY_DATA_FILE_REQUESTED, self._on_apply_data_file_request
        )

    def _get_fig_coords(self, event) -> tuple[float, float]:
        """
        Calculates normalized figure coordinates (0-1) from a Matplotlib event.
        """
        if event.x is None or event.y is None:
            return (0.0, 0.0)
            
        fig = self._view.figure_canvas.figure
        inv = fig.transFigure.inverted()
        fig_coords = inv.transform((event.x, event.y))
        return (float(fig_coords[0]), float(fig_coords[1]))

    def _map_mpl_button_to_qt(self, mpl_button: int) -> Qt.MouseButton:
        """
        Maps Matplotlib button integers to Qt MouseButton enums.
        """
        if mpl_button == 1:
            return Qt.MouseButton.LeftButton
        elif mpl_button == 2:
            return Qt.MouseButton.MiddleButton
        elif mpl_button == 3:
            return Qt.MouseButton.RightButton
        return Qt.MouseButton.NoButton

    def _on_mouse_press(self, event):
        """Translates Matplotlib press event into tool service dispatch."""
        fig_coords = self._get_fig_coords(event)
        
        # Perform hit test
        hit_node = self._model.scene_root.hit_test(fig_coords)
        node_id = hit_node.id if hit_node else None
        
        qt_button = self._map_mpl_button_to_qt(event.button)
        
        self.logger.debug(f"Mouse press at {fig_coords}, hit: {node_id}, button: {qt_button}")
        self._tool_service.dispatch_mouse_press_event(node_id, fig_coords, qt_button)

    def _on_mouse_move(self, event):
        """Translates Matplotlib move event."""
        fig_coords = self._get_fig_coords(event)
        self._tool_service.dispatch_mouse_move_event(fig_coords)

    def _on_mouse_release(self, event):
        """Translates Matplotlib release event."""
        fig_coords = self._get_fig_coords(event)
        self._tool_service.dispatch_mouse_release_event(fig_coords)

    def _on_key_pressed(self, event: QKeyEvent):
        """Dispatches keyboard events to the tool service."""
        self._tool_service.dispatch_key_press_event(event)

    def _on_canvas_double_clicked(self, scene_pos: QPointF):

        """
        Handles double-click on the canvas by performing a hit test
        and triggering selection/properties update.
        """
        fig_coords = self._view.map_to_figure(scene_pos)
        self.logger.debug(f"Canvas double-clicked at figure coords: {fig_coords}")

        hit_node = self._model.scene_root.hit_test(fig_coords)
        if hit_node:
            self.logger.info(f"Hit node: {hit_node.name} (ID: {hit_node.id})")
            self._model.set_selection([hit_node])
        else:
            self._model.set_selection([])

    def _on_file_dropped(self, file_path: str, scene_pos: QPointF):
        """
        Handles data file drops by identifying the target node
        and initiating the data loading workflow.
        """
        fig_coords = self._view.map_to_figure(scene_pos)
        node = self._model.scene_root.hit_test(fig_coords)

        if node and isinstance(node, PlotNode):
            self.logger.info(f"File {file_path} dropped onto node {node.id}")
            # Trigger data load via event-driven command workflow
            self._event_aggregator.publish(
                Events.APPLY_DATA_FILE_REQUESTED,
                node_id=node.id,
                file_path=Path(file_path),
            )

    def _on_apply_data_file_request(self, node_id: str, file_path: Path):
        """Forwards the data file request to the NodeController."""
        self._event_aggregator.publish(
            Events.APPLY_DATA_TO_NODE_REQUESTED, node_id=node_id, file_path=file_path
        )
        self.logger.debug(f"Forwarded data apply request for node {node_id}")
        
    @property
    def view(self):
        return self._view
