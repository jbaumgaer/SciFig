from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter

from src.models import ApplicationModel, PlotNode
from .base_tool import BaseTool

if TYPE_CHECKING:
    from src.commands.command_manager import CommandManager
    from src.views.canvas_widget import CanvasWidget


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

    @property
    def name(self) -> str:
        return "selection"

    @property
    def icon_path(self) -> str:
        return "src/assets/icons/toolbar/Select.svg"

    def on_activated(self):
        print("SelectionTool activated")

    def on_deactivated(self):
        print("SelectionTool deactivated")

    def mouse_press_event(self, event: QMouseEvent):
        """Handles single clicks to select or deselect nodes."""
        # Ignore clicks outside of any axes
        if event.xdata is None or event.ydata is None:
            # Deselect if clicking outside
            self._model.set_selection([])
            return

        # TODO: Maybe refactor this to a utility function later or give this a more descriptive name
        fig_coords = (
            self._canvas_widget.figure_canvas.figure.transFigure.inverted().transform(
                (event.x, event.y)
            )
        )
        node_hit = self._model.get_node_at(fig_coords)

        if event.dblclick:
            if node_hit and isinstance(node_hit, PlotNode):
                self.plot_double_clicked.emit(node_hit)
        else:
            if node_hit:
                self._model.set_selection([node_hit])
            else:
                self._model.set_selection([])

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
