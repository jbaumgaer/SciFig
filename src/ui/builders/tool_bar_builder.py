from dataclasses import dataclass

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar

from src.shared.constants import IconPath, ToolName
from src.services.tool_service import ToolService


@dataclass
class ToolBarActions:
    """Dataclass to hold references to all QActions in the toolbar."""
    selection: QAction
    direct_selection: QAction
    eyedropper: QAction
    plot: QAction
    text: QAction
    zoom: QAction


class ToolBarBuilder(QObject):
    """
    Builds the main application toolbar and manages its state based on the ToolManager.
    """

    def __init__(self, tool_manager: ToolService): # Removed parent_window
        super().__init__() # Removed parent_window
        self._tool_manager = tool_manager
        self._actions: dict[str, QAction] = {}  # To store actions by tool name

    def build(self) -> tuple[QToolBar, ToolBarActions]:
        """
        Constructs the QToolBar and its actions.
        """
        tool_bar = QToolBar("Tools") # Created without parent
        tool_bar.setMovable(False)
        tool_bar.setFloatable(False)
        # Removed self._parent_window.addToolBar(Qt.LeftToolBarArea, tool_bar)

        tool_definitions = {
            ToolName.SELECTION: {"icon": IconPath.get_path("tool_icons.select"), "tooltip": "Selection Tool"},
            ToolName.DIRECT_SELECTION: {"icon": IconPath.get_path("tool_icons.direct_select"), "tooltip": "Direct Selection Tool"},
            ToolName.EYEDROPPER: {"icon": IconPath.get_path("tool_icons.eyedropper"), "tooltip": "Eyedropper Tool"},
            ToolName.PLOT: {"icon": IconPath.get_path("tool_icons.plot"), "tooltip": "Plot Tool"},
            ToolName.TEXT: {"icon": IconPath.get_path("tool_icons.text"), "tooltip": "Text Tool"},
            ToolName.ZOOM: {"icon": IconPath.get_path("tool_icons.zoom"), "tooltip": "Zoom Tool"},
        }

        # Dynamically create actions for each tool
        for tool_name, props in tool_definitions.items():
            icon_path = props["icon"]
            action = QAction(QIcon(str(icon_path)), props["tooltip"], tool_bar) # Parent QAction to tool_bar
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked, name=tool_name: self._tool_manager.set_active_tool(name)
            )
            tool_bar.addAction(action)
            self._actions[tool_name.value] = action # Use tool_name.value for dict key

        # Connect tool manager signal to update toolbar state
        self._tool_manager.active_tool_changed.connect(self._update_tool_bar_state)

        # Return a ToolBarActions dataclass for easy access to specific actions
        toolbar_actions = ToolBarActions(
            selection=self._actions[ToolName.SELECTION.value],
            direct_selection=self._actions[ToolName.DIRECT_SELECTION.value],
            eyedropper=self._actions[ToolName.EYEDROPPER.value],
            plot=self._actions[ToolName.PLOT.value],
            text=self._actions[ToolName.TEXT.value],
            zoom=self._actions[ToolName.ZOOM.value],
        )

        return tool_bar, toolbar_actions

    def _update_tool_bar_state(self, active_tool_name: str) -> None:
        """
        Updates the checked state of the toolbar actions based on the active tool.
        """
        for tool_name, action in self._actions.items():
            action.setChecked(tool_name == active_tool_name)
