import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter

from src.shared.constants import IconPath
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.tools.base_tool import BaseTool

if TYPE_CHECKING:
    from src.services.commands.command_manager import CommandManager
    from src.ui.widgets.canvas_widget import CanvasWidget


class SelectionTool(BaseTool):
    """
    A tool for selecting, deselecting, and (eventually) moving nodes.
    """

    plot_double_clicked = Signal(PlotNode)

    def __init__(
        self,
        model: ApplicationModel,
        command_manager: "CommandManager",
        canvas_widget: "CanvasWidget",
    ):
        super().__init__(model, command_manager, canvas_widget)
        self.logger = logging.getLogger(self.__class__.__name__) # Added logger
        self.logger.info("SelectionTool initialized.") # Added log

    @property
    def name(self) -> str:
        return "selection"

    @property
    def icon_path(self) -> str:
        # Get icon path from ConfigService via IconPath class
        return IconPath.get_path("tool_icons.select") # Modified to use ConfigService


    def on_activated(self):
        self.logger.info("SelectionTool activated.") # Changed print to log

    def on_deactivated(self):
        self.logger.info("SelectionTool deactivated.") # Changed print to log

    def mouse_press_event(self, event: QMouseEvent):
        """Handles single clicks to select or deselect nodes."""
        self.logger.debug(f"Mouse press event at: ({event.xdata}, {event.ydata})") # Added log
        # Ignore clicks outside of any axes
        if event.xdata is None or event.ydata is None:
            # Deselect if clicking outside
            self._model.set_selection([])
            self.logger.debug("Click outside axes. Deselecting all.") # Added log
            return

        # TODO: Maybe refactor this to a utility function later or give this a more descriptive name
        fig_coords = (
            self._canvas_widget.figure_canvas.figure.transFigure.inverted().transform(
                (event.x, event.y)
            )
        )
        node_hit = self._model.get_node_at(fig_coords)
        self.logger.debug(f"Node hit: {node_hit.name if node_hit else 'None'} at figure coords: {fig_coords}") # Added log


        if event.dblclick:
            if node_hit and isinstance(node_hit, PlotNode):
                self.plot_double_clicked.emit(node_hit)
                self.logger.info(f"Double-clicked on PlotNode '{node_hit.name}'. Emitting plot_double_clicked signal.") # Added log
        else:
            if node_hit:
                self._model.set_selection([node_hit])
                self.logger.info(f"Selected PlotNode '{node_hit.name}'.") # Added log
            else:
                self._model.set_selection([])
                self.logger.info("Clicked on empty space. Deselecting all.") # Added log


    def mouse_move_event(self, event: QMouseEvent):
        # To be implemented later (for dragging)
        pass

    def mouse_release_event(self, event: QMouseEvent):
        # To be implemented later (for dragging)
        pass

    def key_press_event(self, event: QKeyEvent) -> None:
        pass

    def paint_event(self, painter: QPainter) -> None:
        pass
