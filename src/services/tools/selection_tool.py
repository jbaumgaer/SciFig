import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.tools.base_tool import BaseTool
from src.shared.constants import IconPath


class SelectionTool(BaseTool):
    """
    A tool for selecting and deselecting nodes.
    Operates on backend-neutral identifiers and coordinates.
    """

    plot_double_clicked = Signal(PlotNode)

    def __init__(
        self,
        model: ApplicationModel,
        canvas_widget=None,  # Keep for base class compatibility but unused here
    ):
        super().__init__(model, canvas_widget)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("SelectionTool initialized.")

    @property
    def name(self) -> str:
        return "selection"

    @property
    def icon_path(self) -> str:
        return IconPath.get_path("tool_icons.select")

    def on_activated(self):
        self.logger.info("SelectionTool activated.")

    def on_deactivated(self):
        self.logger.info("SelectionTool deactivated.")

    def mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        """Handles single clicks to select or deselect nodes based on node_id."""
        self.logger.debug(
            f"SelectionTool: Mouse press at {fig_coords}, node_id: {node_id}"
        )

        if node_id:
            node = self._model.scene_root.find_node_by_id(node_id)
            if node:
                self._model.set_selection([node])
                self.logger.info(f"Selected Node '{node.name}'.")
                return

        # If no node_id or node not found, clear selection
        self._model.set_selection([])
        self.logger.info("Clicked on empty space. Deselecting all.")

    def mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        pass

    def mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        pass

    def key_press_event(self, event: QKeyEvent) -> None:
        pass

    def paint_event(self, painter: QPainter) -> None:
        pass
