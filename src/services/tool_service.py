from typing import Optional

from src.services.event_aggregator import EventAggregator
from src.services.tools.base_tool import BaseTool
from src.shared.events import Events


class ToolService:
    """
    Manages all available tools and tracks the currently active one.

    This class acts as the central hub for tool-based interactions. It holds a
    registry of all tools, manages the active tool state, and dispatches
    canvas events to the currently active tool.
    """

    def __init__(self, event_aggregator: EventAggregator):
        self._event_aggregator = event_aggregator
        self._tools: dict[str, BaseTool] = {}
        self._active_tool_name: Optional[str] = None

    @property
    def active_tool(self) -> Optional[BaseTool]:
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

        self._event_aggregator.publish(Events.ACTIVE_TOOL_CHANGED, tool_name=tool_name)

    def dispatch_mouse_press_event(
        self, node_id: Optional[str], fig_coords: tuple[float, float], button: int
    ) -> None:
        """Dispatches a backend-neutral mouse press event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_press_event(node_id, fig_coords, button)

    def dispatch_mouse_move_event(self, fig_coords: tuple[float, float]) -> None:
        """Dispatches a backend-neutral mouse move event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_move_event(fig_coords)

    def dispatch_mouse_release_event(self, fig_coords: tuple[float, float]) -> None:
        """Dispatches a backend-neutral mouse release event to the active tool."""
        if self.active_tool:
            self.active_tool.mouse_release_event(fig_coords)

    def dispatch_key_press_event(self, fig_coords: tuple[float, float]) -> None:
        """Dispatches the key press event to the active tool."""
        if self.active_tool:
            self.active_tool.key_press_event(fig_coords)

    def dispatch_paint_event(self, fig_coords: tuple[float, float]) -> None:
        """Dispatches the paint event to the active tool for overlays."""
        if self.active_tool:
            self.active_tool.paint_event(fig_coords)
