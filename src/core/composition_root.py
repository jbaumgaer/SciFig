import logging

from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication, QMenuBar, QToolBar

from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.ui.builders.tool_bar_builder import ToolBarActions, ToolBarBuilder
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.shared.constants import IconPath, ToolName
from src.controllers.canvas_controller import CanvasController
from src.controllers.main_controller import MainController
from src.services.tool_service import ToolService
from src.services.tools import MockTool
from src.services.tools.selection_tool import SelectionTool
from src.core.application_components import ApplicationComponents
from src.models.layout.layout_engine import FreeLayoutEngine, GridLayoutEngine
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.plots.plot_types import PlotType
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.windows.main_window import MainWindow
from src.ui.factories.properties_ui_factory import (
    PropertiesUIFactory,
    _build_line_plot_ui_widgets,
    _build_scatter_plot_ui_widgets,
)
from src.ui.renderers.renderer import Renderer


class CompositionRoot:
    """
    Orchestrates the assembly of all application components,
    acting as the composition root.
    """

    def __init__(self, app: QApplication, config_service: ConfigService):
        self._app = app
        self._config_service = config_service # Stored config_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("CompositionRoot initialized.")
        self.logger.debug("ConfigService provided with path: configs/default_config.yaml")

        IconPath.set_config_service(self._config_service)

        # Core components
        self._model: ApplicationModel | None = None
        self._command_manager: CommandManager | None = None
        self._main_controller: MainController | None = None
        self._renderer: Renderer | None = None
        self._plot_types: list = []
        self._layout_manager: LayoutManager | None = None # New
        self._free_layout_engine: FreeLayoutEngine | None = None # New
        self._grid_layout_engine: GridLayoutEngine | None = None # New
        self._layout_ui_factory: LayoutUIFactory | None = None # New

        # UI components
        self._menu_bar: QMenuBar | None = None
        self._main_menu_actions: MainMenuActions | None = None
        self._tool_bar: QToolBar | None = None
        self._tool_bar_actions: ToolBarActions | None = None
        self._view: MainWindow | None = None
        self._properties_ui_factory: PropertiesUIFactory | None = None

        # Tooling components
        self._tool_manager: ToolService | None = None
        self._selection_tool: SelectionTool | None = None

        # Other controllers
        self._canvas_controller: CanvasController | None = None

    def _assemble_core_components(self):
        """Assemble core models, managers, and controllers."""
        self.logger.info("Assembling core components: Model, CommandManager, MainController, Renderer.")
        figure_width = self._config_service.get("figure.default_width", 8.5)
        figure_height = self._config_service.get("figure.default_height", 6)
        figure_dpi = self._config_service.get("figure.default_dpi", 150)
        figure_facecolor = self._config_service.get("figure.default_facecolor", "white")
        figure = Figure(figsize=(figure_width, figure_height), dpi=figure_dpi, facecolor=figure_facecolor)
        self.logger.debug(f"Figure created with dimensions: {figure_width}x{figure_height} @ {figure_dpi}dpi, Facecolor: {figure_facecolor}")

        self._model = ApplicationModel(figure=figure, config_service=self._config_service) # Pass config_service
        self._command_manager = CommandManager(model=self._model)

        # Instantiate layout components
        self._free_layout_engine = FreeLayoutEngine()
        self._grid_layout_engine = GridLayoutEngine(config_service=self._config_service)
        self._layout_manager = LayoutManager(
            application_model=self._model,
            free_engine=self._free_layout_engine,
            grid_engine=self._grid_layout_engine,
            config_service=self._config_service,
        )
        # Pass ConfigService and LayoutManager to MainController
        self._main_controller = MainController(model=self._model, config_service=self._config_service, layout_manager=self._layout_manager, command_manager=self._command_manager)

        self._layout_ui_factory = LayoutUIFactory(
            config_service=self._config_service,
            layout_manager=self._layout_manager, # Pass layout_manager
        )
        # Pass layout_manager and application_model to Renderer
        self._renderer = Renderer(layout_manager=self._layout_manager, application_model=self._model)
        self._plot_types = list(self._renderer.plotting_strategies.keys())
        self._properties_ui_factory = PropertiesUIFactory()

        # Register plot-specific UI builders
        self._properties_ui_factory.register_builder(
            PlotType.LINE, _build_line_plot_ui_widgets
        )
        self._properties_ui_factory.register_builder(
            PlotType.SCATTER, _build_scatter_plot_ui_widgets
        )

    def _assemble_menus(self):
        """Assemble the menu bar and its actions."""
        self.logger.info("Assembling menus.")
        menu_builder = MenuBarBuilder(
            main_controller=self._main_controller,
            command_manager=self._command_manager,
            # ConfigService might be needed here if menu items are configurable
        )
        assembled_menu_actions = menu_builder.build()
        self._menu_bar = assembled_menu_actions.menu_bar
        self._main_menu_actions = assembled_menu_actions

    def _assemble_tooling(self):
        """Assemble the tool manager, individual tools, and the toolbar."""
        self.logger.info("Assembling tooling: ToolManager, SelectionTool, MockTools.")

        self._tool_manager = ToolService(
            model=self._model, command_manager=self._command_manager
        )

        # Create SelectionTool
        self._selection_tool = SelectionTool(
            model=self._model,
            command_manager=self._command_manager,
            canvas_widget=None,  # Will be set after MainWindow is available
            # ConfigService might be needed here if tool defaults are loaded from config
        )
        self._tool_manager.add_tool(self._selection_tool)

        # Use config for default active tool
        default_active_tool_name = self._config_service.get("tool.default_active_tool", ToolName.SELECTION.value)
        self._tool_manager.set_active_tool(default_active_tool_name)
        self.logger.debug(f"Default active tool set to: {default_active_tool_name}")

        # Placeholder tools for toolbar (not yet implemented)
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.direct_selection.name", ToolName.DIRECT_SELECTION.value),
                IconPath.get_path("tool_icons.direct_select"),
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.eyedropper.name", ToolName.EYEDROPPER.value),
                IconPath.get_path("tool_icons.eyedropper"),
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.plot.name", ToolName.PLOT.value),
                IconPath.get_path("tool_icons.plot"),
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.text.name", ToolName.TEXT.value),
                IconPath.get_path("tool_icons.text"),
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.zoom.name", ToolName.ZOOM.value),
                IconPath.get_path("tool_icons.zoom"),
                self._model,
                self._command_manager,
                None,
            )
        )

        # Build the toolbar
        tool_bar_builder = ToolBarBuilder(tool_manager=self._tool_manager)
        self._tool_bar, self._tool_bar_actions = tool_bar_builder.build()

    def _assemble_main_window(self):
        """Assemble the main application window."""
        self.logger.info("Assembling main window.")
        self._view = MainWindow(
            model=self._model,
            main_controller=self._main_controller,
            command_manager=self._command_manager,
            plot_types=self._plot_types,
            menu_bar=self._menu_bar,
            main_menu_actions=self._main_menu_actions,
            tool_bar=self._tool_bar,
            tool_bar_actions=self._tool_bar_actions,
            properties_ui_factory=self._properties_ui_factory,
            config_service=self._config_service,
            layout_ui_factory=self._layout_ui_factory, # Pass LayoutUIFactory
            layout_manager=self._layout_manager, # Pass LayoutManager
        )

        # Now that MainWindow exists, set its canvas_widget for tools
        self._selection_tool._canvas_widget = self._view.canvas_widget
        for tool_name, tool in self._tool_manager._tools.items():
            # Update canvas_widget for all tools
            tool._canvas_widget = self._view.canvas_widget

    def _assemble_canvas_controller(self):
        """Assemble the canvas controller."""
        self._canvas_controller = CanvasController(
            model=self._model,
            canvas_widget=self._view.canvas_widget,
            tool_manager=self._tool_manager,
            command_manager=self._command_manager,
            layout_manager=self._layout_manager,
            main_controller=self._main_controller,
        )

    def _connect_signals(self):
        """Connect all application-wide signals to their slots."""
        self.logger.debug("Connecting signals.")
        # Main Window actions to Main Controller
        self._view.new_layout_action.triggered.connect(
            self._main_controller.create_new_layout
        )
        self._view.save_project_action.triggered.connect(
            lambda: self._main_controller.save_project(parent=self._view)
        )
        self._view.open_project_action.triggered.connect(
            lambda: self._main_controller.open_project(parent=self._view)
        )

        # Model changes to redraw
        self._model.modelChanged.connect(self._redraw_canvas_callback)
        self._model.selectionChanged.connect(self._redraw_canvas_callback)
        self._model.layoutConfigChanged.connect(self._redraw_canvas_callback)

        # Tool-specific signals
        self._selection_tool.plot_double_clicked.connect(self._view.show_properties_panel)

    def _redraw_canvas_callback(self):
        """Callback to trigger canvas redraw."""
        self.logger.debug("ApplicationAssembler._redraw_canvas_callback called")
        self._renderer.render(
            self._view.canvas_widget.figure,
            self._model.scene_root,
            self._model.selection,
        )
        self._view.canvas_widget.figure_canvas.draw()

    def assemble(self) -> ApplicationComponents:
        """
        Assembles and wires all components of the application.
        """
        self._assemble_core_components()
        self._assemble_menus()
        self._assemble_tooling()
        self._assemble_main_window()
        self._assemble_canvas_controller()
        self._connect_signals()
        self.logger.info("Application assembly complete.")

        return ApplicationComponents(
            app=self._app,
            model=self._model,
            command_manager=self._command_manager,
            main_controller=self._main_controller,
            canvas_controller=self._canvas_controller,
            view=self._view,
            selection_tool=self._selection_tool,
            tool_manager=self._tool_manager,
            main_menu_actions=self._main_menu_actions,
            tool_bar_actions=self._tool_bar_actions,
            config_service=self._config_service,
            layout_manager=self._layout_manager,
            layout_ui_factory=self._layout_ui_factory,
        )
