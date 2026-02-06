from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from src.ui.builders.menu_bar_builder import MainMenuActions
    from src.ui.builders.tool_bar_builder import ToolBarActions
    from src.services.commands.command_manager import CommandManager
    from src.services.config_service import ConfigService
    from src.controllers.canvas_controller import CanvasController
    from src.controllers.main_controller import MainController
    from src.services.tool_service import ToolService
    from src.services.tools.selection_tool import SelectionTool
    from src.services.layout_manager import LayoutManager
    from src.models.application_model import ApplicationModel
    from src.ui.factories.layout_ui_factory import LayoutUIFactory
    from src.ui.windows.main_window import MainWindow


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
    tool_manager: "ToolService"
    main_menu_actions: "MainMenuActions"
    tool_bar_actions: "ToolBarActions"
    config_service: "ConfigService"
    layout_manager: "LayoutManager" # New field
    layout_ui_factory: "LayoutUIFactory" # New field
