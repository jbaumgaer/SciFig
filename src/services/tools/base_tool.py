"""
This module defines the abstract base class for all interactive tools in the application.
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtGui import QKeyEvent, QPainter

from src.models.application_model import ApplicationModel
from src.ui.widgets.canvas_widget import CanvasWidget


# Python 3: metaclass conflict with QObject and ABCMeta
# Solution: Create a custom metaclass that inherits from both
class ToolMeta(type(QObject), ABCMeta):
    pass


class BaseTool(QObject, ABC, metaclass=ToolMeta):
    """
    Abstract base class for all tools that interact with the canvas.

    Each tool is a stateful object that handles user input (mouse, keyboard)
    to perform a specific function (e.g., selecting, drawing, zooming).
    """

    def __init__(
        self,
        model: ApplicationModel,
        canvas_widget: CanvasWidget,
    ):
        """
        Initializes the tool.

        Args:
            model: The application model.
            canvas_widget: The canvas widget the tool will interact with.
        """
        super().__init__()
        self._model = model
        self._canvas_widget = canvas_widget

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique identifier name for the tool (e.g., 'selection_tool')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def icon_path(self) -> str:
        """The path to the tool's icon file."""
        raise NotImplementedError

    def on_activated(self) -> None:
        """Called by the ToolManager when the tool becomes active."""

    def on_deactivated(self) -> None:
        """Called by the ToolManager when the tool is deactivated."""

    def mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        """Handles the mouse press event on the canvas."""

    def mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        """Handles the mouse move event on the canvas."""

    def mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        """Handles the mouse release event on the canvas."""

    def key_press_event(self, event: QKeyEvent) -> None:
        """Handles key press events on the canvas."""

    def paint_event(self, painter: QPainter) -> None:
        """
        Allows the tool to paint temporary overlays on the canvas.
        This is called by the canvas widget during its paint event.
        """
