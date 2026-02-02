from .tools.base_tool import BaseTool


class ToolManager:
    """
    Manages all available tools and tracks the currently active one.
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._active_tool: BaseTool | None = None

    def add_tool(self, name: str, tool: BaseTool):
        """Adds a tool to the manager."""
        if name in self._tools:
            raise ValueError(f"Tool with name '{name}' already exists.")
        self._tools[name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Retrieves a tool by its name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"No tool with name '{name}' found.")
        return tool

    def set_active_tool(self, name: str):
        """Sets the active tool by its name."""
        if self._active_tool:
            self._active_tool.deactivate()

        tool = self.get_tool(name)
        self._active_tool = tool
        self._active_tool.activate()

    def get_active_tool(self) -> BaseTool | None:
        """Returns the currently active tool."""
        return self._active_tool
