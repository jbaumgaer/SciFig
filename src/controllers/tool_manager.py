"""
This module defines the ToolManager, which is responsible for managing the
state of all interactive tools in the application.
"""

from typing import TYPE_CHECKING, Dict

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter

from src.controllers.tools.base_tool import BaseTool

if TYPE_CHECKING:  # Avoid circular imports during type checking
    from src.commands.command_manager import CommandManager
    from src.models.application_model import ApplicationModel


class ToolManager(QObject):
    """
    Manages all available tools and tracks the currently active one.

    This class acts as the central hub for tool-based interactions. It holds a
    registry of all tools, manages the active tool state, and dispatches
    canvas events to the currently active tool.
    """

    active_tool_changed = Signal(str)

    def __init__(
        self,
        model: "ApplicationModel",
        command_manager: "CommandManager",
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._model = model
        self._command_manager = command_manager
        self._tools: Dict[str, BaseTool] = {}
        self._active_tool_name: str | None = None

    @property
    def active_tool(self) -> BaseTool | None:
        """Returns the instance of the currently active tool."""
        if self._active_tool_name:
            return self._tools.get(self._active_tool_name)
        return None

    def add_tool(self, tool: BaseTool) -> None:
        """Adds and registers a tool instance."""
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' already exists.")
        self._tools[tool.name] = tool

    def set_active_tool(self, tool_name: str) -> None:
        """Sets the active tool by its unique name."""
        if tool_name not in self._tools:
            raise ValueError(f"No tool with name '{tool_name}' found.")

        if self._active_tool_name == tool_name:
            return  # Do nothing if the tool is already active

        if self.active_tool:
            self.active_tool.on_deactivated()

        self._active_tool_name = tool_name
        if self.active_tool:
            self.active_tool.on_activated()

        self.active_tool_changed.emit(tool_name)

    def dispatch_mouse_press_event(self, event: QMouseEvent) -> None:
        """Dispatches the mouse press event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_press_event(event)

    def dispatch_mouse_move_event(self, event: QMouseEvent) -> None:
        """Dispatches the mouse move event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_move_event(event)

    def dispatch_mouse_release_event(self, event: QMouseEvent) -> None:
        """Dispatches the mouse release event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_release_event(event)

    def dispatch_key_press_event(self, event: QKeyEvent) -> None:
        """Dispatches the key press event to the active tool."""
        if self.active_tool:
            self.active_tool.key_press_event(event)

    def dispatch_paint_event(self, painter: QPainter) -> None:
        """Dispatches the paint event to the active tool for overlays."""
        if self.active_tool:
            self.active_tool.paint_event(painter)
