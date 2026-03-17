from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QApplication

from src.controllers.canvas_controller import CanvasController
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.data_service import DataService
from src.services.event_aggregator import EventAggregator
from src.services.layout_service import LayoutService
from src.services.property_service import PropertyService
from src.services.style_service import StyleService
from src.services.tool_service import ToolService
from src.services.tools.add_plot_tool import AddPlotTool
from src.services.tools.selection_tool import SelectionTool
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.renderers.overlay_renderer import OverlayRenderer
from src.ui.renderers.figure_renderer import FigureRenderer
from src.ui.windows.main_window import MainWindow

if TYPE_CHECKING:
    from src.core.composition_root import CompositionRoot


@dataclass
class ApplicationComponents:
    """
    A dataclass to hold all core components of the application after assembly.
    This provides a clear, type-hinted return type for the ApplicationAssembler.
    """

    composition_root: "CompositionRoot"
    app: QApplication
    event_aggregator: "EventAggregator"
    application_model: "ApplicationModel"
    property_service: "PropertyService"
    command_manager: "CommandManager"
    project_controller: "ProjectController"
    layout_controller: "LayoutController"
    node_controller: "NodeController"
    canvas_controller: "CanvasController"
    view: "MainWindow"
    selection_tool: "SelectionTool"
    add_plot_tool: "AddPlotTool"
    tool_manager: "ToolService"
    main_menu_actions: "MainMenuActions"
    tool_bar_actions: "ToolBarActions"
    config_service: "ConfigService"
    style_service: "StyleService"
    data_service: "DataService"
    layout_manager: "LayoutService"
    layout_ui_factory: "LayoutUIFactory"
    figure_renderer: "FigureRenderer"
    overlay_renderer: "OverlayRenderer"
