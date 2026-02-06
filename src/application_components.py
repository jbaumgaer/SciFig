from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QToolBar, QMenuBar

# Avoid circular imports with type checking
if TYPE_CHECKING:
    from src.models.application_model import ApplicationModel
    from src.commands.command_manager import CommandManager
    from src.controllers.main_controller import MainController
    from src.controllers.canvas_controller import CanvasController
    from src.controllers.tool_manager import ToolManager
    from src.controllers.tools.selection_tool import SelectionTool
    from src.views.main_window import MainWindow
    from src.builders.menu_bar_builder import MainMenuActions
    from src.builders.tool_bar_builder import ToolBarActions
    from src.config_service import ConfigService
    from src.layout_manager import LayoutManager # New import
    from src.views.layout_ui_factory import LayoutUIFactory # New import


@dataclass
class ApplicationComponents:
    """
    A dataclass to hold all core components of the application after assembly.
    This provides a clear, type-hinted return type for the ApplicationAssembler.
    """
    app: QApplication
    model: "ApplicationModel"
    command_manager: "CommandManager"
    main_controller: "MainController"
    canvas_controller: "CanvasController"
    view: "MainWindow"
    selection_tool: "SelectionTool"
    tool_manager: "ToolManager"
    main_menu_actions: "MainMenuActions"
    tool_bar_actions: "ToolBarActions"
    config_service: "ConfigService"
    layout_manager: "LayoutManager" # New field
    layout_ui_factory: "LayoutUIFactory" # New field
