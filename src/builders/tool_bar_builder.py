from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar

from src.controllers.tool_manager import ToolManager
from src.constants import ToolName, IconPath


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

    def __init__(self, tool_manager: ToolManager): # Removed parent_window
        super().__init__() # Removed parent_window
        self._tool_manager = tool_manager
        self._actions: Dict[str, QAction] = {}  # To store actions by tool name

    def build(self) -> Tuple[QToolBar, ToolBarActions]:
        """
        Constructs the QToolBar and its actions.
        """
        tool_bar = QToolBar("Tools") # Created without parent
        tool_bar.setMovable(False)
        tool_bar.setFloatable(False)
        # Removed self._parent_window.addToolBar(Qt.LeftToolBarArea, tool_bar)

        tool_definitions = {
            ToolName.SELECTION: {"icon": IconPath.SELECT_TOOL, "tooltip": "Selection Tool"},
            ToolName.DIRECT_SELECTION: {"icon": IconPath.DIRECT_SELECT_TOOL, "tooltip": "Direct Selection Tool"},
            ToolName.EYEDROPPER: {"icon": IconPath.EYEDROPPER_TOOL, "tooltip": "Eyedropper Tool"},
            ToolName.PLOT: {"icon": IconPath.PLOT_TOOL, "tooltip": "Plot Tool"},
            ToolName.TEXT: {"icon": IconPath.TEXT_TOOL, "tooltip": "Text Tool"},
            ToolName.ZOOM: {"icon": IconPath.ZOOM_TOOL, "tooltip": "Zoom Tool"},
        }

        # Dynamically create actions for each tool
        for tool_name, props in tool_definitions.items():
            icon_path = Path(props["icon"]) # IconPath constants are already str
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
