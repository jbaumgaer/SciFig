import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.services.event_aggregator import EventAggregator
from src.services.tools.base_tool import BaseTool
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.constants import IconPath, ToolName


class AddPlotTool(BaseTool):
    """
    A tool for interactively adding new plots to the canvas.
    Supports rubber-band dragging for custom geometry or single-click for a dialog.
    """

    def __init__(
        self,
        model: ApplicationModel,
        canvas_widget,
        event_aggregator: EventAggregator,
    ):
        super().__init__(model, canvas_widget, event_aggregator)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Interaction state
        self._is_pressed = False
        self._start_pos_fig: Optional[tuple[float, float]] = None
        self._last_pos_fig: Optional[tuple[float, float]] = None
        
        # Noise threshold for distinguishing click from drag (in figure units)
        self._click_threshold = 0.005 

    @property
    def name(self) -> str:
        return ToolName.PLOT.value

    @property
    def icon_path(self) -> str:
        # TODO: Define specific plot creation icon in config
        return IconPath.get_path("tool_icons.plot")

    def mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        """Starts the plot creation interaction."""
        if button == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._start_pos_fig = fig_coords
            self._last_pos_fig = fig_coords
            self.logger.debug(f"AddPlotTool: Press at {fig_coords}")

    def mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        """Updates the rubber-band preview."""
        if not self._is_pressed or not self._start_pos_fig:
            return

        self._last_pos_fig = fig_coords
        
        # Calculate rubber-band geometry
        rect = self._calculate_rect(self._start_pos_fig, fig_coords)
        
        # Request preview update
        self._event_aggregator.publish(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED,
            geometries=[rect],
            style="rubber_band"
        )

    def mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        """Finalizes the creation or requests a dialog."""
        if not self._is_pressed or not self._start_pos_fig:
            return

        # 1. Clear preview
        self._event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)

        # 2. Determine interaction type
        final_rect = self._calculate_rect(self._start_pos_fig, fig_coords)
        
        if final_rect.width < self._click_threshold and final_rect.height < self._click_threshold:
            # Interpret as a Click -> Show Dialog
            self.logger.info("AddPlotTool: Click detected. Requesting Add Plot dialog.")
            self._event_aggregator.publish(
                Events.SHOW_ADD_PLOT_DIALOG_REQUESTED,
                center_pos=self._start_pos_fig
            )
        else:
            # Interpret as a Drag -> Direct Creation
            self.logger.info(f"AddPlotTool: Drag detected. Requesting new plot with geometry {final_rect}")
            self._event_aggregator.publish(
                Events.ADD_PLOT_REQUESTED,
                geometry=final_rect
            )

        # Reset state
        self._is_pressed = False
        self._start_pos_fig = None
        self._last_pos_fig = None

    def key_press_event(self, event: QKeyEvent) -> None:
        """Escape cancels the current interaction."""
        if event.key() == Qt.Key.Key_Escape and self._is_pressed:
            self._is_pressed = False
            self._start_pos_fig = None
            self._event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)
            self.logger.info("AddPlotTool: Interaction cancelled by Escape.")

    def paint_event(self, painter: QPainter) -> None:
        """No direct painting needed; we use the Overlay Layer via events."""
        pass

    def _calculate_rect(self, p1: tuple[float, float], p2: tuple[float, float]) -> Rect:
        """Helper to create a Rect from two points."""
        x = min(p1[0], p2[0])
        y = min(p1[1], p2[1])
        w = abs(p1[0] - p2[0])
        h = abs(p1[1] - p2[1])
        return Rect(x, y, w, h)
