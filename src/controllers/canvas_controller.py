import logging
from pathlib import Path

from PySide6.QtCore import QObject, QPointF

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.event_aggregator import EventAggregator
from src.services.tool_service import ToolService
from src.shared.events import Events
from src.ui.widgets.canvas_widget import CanvasWidget


class CanvasController(QObject):
    """
    Acts as a Sanitizer between the coupled View/Backend and the headless Tools.
    Translates Matplotlib/Qt events into backend-neutral SciFig messages.
    """

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
        canvas_widget: CanvasWidget,
        tool_manager: ToolService,
    ):
        super().__init__()
        self.model = model
        self._event_aggregator = event_aggregator
        self.view = canvas_widget
        self.tool_manager = tool_manager
        self.logger = logging.getLogger(self.__class__.__name__)

        self._connect_events()
        self.logger.info("CanvasController initialized.")

    def _connect_events(self):
        """
        Connects backend signals to sanitizer handlers.
        """
        self.logger.debug("Connecting canvas events.")
        canvas = (
            self.view.figure_canvas
        )  # TODO: I don't think the canvas controller should have such knowledge of the view's internal representation of a figure

        # 1. Matplotlib Event Translation
        canvas.mpl_connect("button_press_event", self._on_mouse_press)
        canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        canvas.mpl_connect("button_release_event", self._on_mouse_release)
        canvas.mpl_connect("pick_event", self._on_pick)

        # 2. Qt View Signal Translation
        self.view.fileDropped.connect(self.on_file_dropped)

    def _on_mouse_press(self, event):
        """Translates Matplotlib button press into a headless tool call."""
        if event.inaxes is None and event.xdata is None:
            # Click outside figure - clear selection
            self._event_aggregator.publish(
                Events.SELECTION_CHANGED, selected_node_ids=[]
            )
            return

        fig_coords = self._get_fig_coords(event)
        node = self.model.get_node_at(fig_coords)
        node_id = node.id if node else None

        # Pass backend-neutral data to the tool manager
        self.tool_manager.dispatch_mouse_press_event(node_id, fig_coords, event.button)

    def _on_mouse_move(self, event):
        """Translates Matplotlib motion into a headless tool call."""
        fig_coords = self._get_fig_coords(event)
        self.tool_manager.dispatch_mouse_move_event(fig_coords)

    def _on_mouse_release(self, event):
        """Translates Matplotlib release into a headless tool call."""
        fig_coords = self._get_fig_coords(event)
        self.tool_manager.dispatch_mouse_release_event(fig_coords)

    def _on_pick(self, event):
        """Translates Matplotlib picking into a sub-selection event."""
        artist = event.artist
        path = artist.get_gid()
        if not path:
            return

        # Identify which node this artist belongs to
        fig_coords = self._get_fig_coords(event.mouseevent)
        node = self.model.get_node_at(fig_coords)

        if node:
            self.logger.info(f"Sub-component picked: {path} on node {node.id}")
            self._event_aggregator.publish(
                Events.SUB_COMPONENT_SELECTED, node_id=node.id, path=path
            )

    def _get_fig_coords(self, event) -> tuple[float, float]:
        """Safely extracts 0-1 figure coordinates from a Matplotlib event."""
        fig = self.view.figure_canvas.figure
        inv = fig.transFigure.inverted()
        # Matplotlib's event.x and event.y are in display (pixel) coordinates
        return tuple(inv.transform((event.x, event.y)))

    def on_file_dropped(self, file_path: str, scene_pos: QPointF):
        """Handles file drop by resolving the target node and requesting data load."""
        fig_coords = self.view.map_to_figure(scene_pos)
        node = self.model.get_node_at(fig_coords)

        if node and isinstance(node, PlotNode):
            self.logger.info(f"File dropped onto PlotNode '{node.name}'.")
            # Request data load via event-driven command workflow
            self._event_aggregator.publish(
                Events.APPLY_DATA_FILE_REQUESTED,
                node_id=node.id,
                file_path=Path(file_path),
            )
