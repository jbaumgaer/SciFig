import logging
from pathlib import Path
from typing import Optional
from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication, QMenuBar, QToolBar

from src.controllers.canvas_controller import CanvasController
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.core.application_components import ApplicationComponents
from src.models.application_model import ApplicationModel
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.plots.plot_types import PlotType
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.layout_manager import LayoutManager
from src.services.tool_service import ToolService
from src.services.tools import MockTool
from src.services.tools.selection_tool import SelectionTool
from src.shared.constants import IconPath, ToolName
from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.ui.builders.tool_bar_builder import ToolBarActions, ToolBarBuilder
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import (
    PlotPropertiesUIFactory,
    _build_line_plot_ui_widgets,
    _build_scatter_plot_ui_widgets,
)
from src.ui.renderers.renderer import Renderer
from src.ui.windows.main_window import MainWindow


class CompositionRoot:
    """
    Orchestrates the assembly of all application components,
    acting as the composition root.
    """

    def __init__(self, app: QApplication, config_service: ConfigService):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("CompositionRoot initialized.")

        self._app = app
        self._config_service = config_service
        self._application_model: Optional[ApplicationModel] = None
        self._command_manager: Optional[CommandManager] = None
        self._project_controller: Optional[ProjectController] = None
        self._layout_controller: Optional[LayoutController] = None
        self._node_controller: Optional[NodeController] = None
        self._canvas_controller: Optional[CanvasController] = None
        self._view: Optional[MainWindow] = None
        self._menu_bar: Optional[QMenuBar] = None
        self._main_menu_actions: Optional[MainMenuActions] = None
        self._tool_bar: Optional[QToolBar] = None
        self._tool_bar_actions: Optional[ToolBarActions] = None
        self._layout_ui_factory: Optional[LayoutUIFactory] = None
        self._plot_properties_ui_factory: Optional[PlotPropertiesUIFactory] = None
        self._tool_manager: Optional[ToolService] = None
        self._selection_tool: Optional[SelectionTool] = None
        self._layout_manager: Optional[LayoutManager] = None

        self.logger.debug(
            f"ConfigService provided with path: {self._config_service.get('config_path', 'Not Provided')}"
        )
        IconPath.set_config_service(self._config_service)

    def _assemble_core_components(self):
        """Assemble core models, managers, and controllers."""
        self.logger.info(
            "Assembling core components: Model, CommandManager, MainController, Renderer."
        )
        figure_width = self._config_service.get_required("figure.default_width")
        figure_height = self._config_service.get_required("figure.default_height")
        figure_dpi = self._config_service.get_required("figure.default_dpi")
        figure_facecolor = self._config_service.get_required("figure.default_facecolor")
        figure = Figure(
            figsize=(figure_width, figure_height),
            dpi=figure_dpi,
            facecolor=figure_facecolor,
        )
        self.logger.debug(
            f"Figure created with dimensions: {figure_width}x{figure_height} @ {figure_dpi}dpi, Facecolor: {figure_facecolor}"
        )

        self._application_model = ApplicationModel(figure=figure)
        self._command_manager = CommandManager(model=self._application_model)

        self._layout_manager = LayoutManager(
            application_model=self._application_model,
            free_engine=FreeLayoutEngine(),
            grid_engine=GridLayoutEngine(),
            config_service=self._config_service,
        )
        # CHANGE: Pass template_dir to ProjectController
        template_dir_path = Path(self._config_service.get_required("paths.layout_templates_dir"))
        max_recent_files = self._config_service.get_required("layout.max_recent_files")
        self._project_controller = ProjectController(
            lifecycle=self._application_model,
            command_manager=self._command_manager,
            layout_manager=self._layout_manager,
            template_dir=template_dir_path,
            max_recent_files=max_recent_files,
        )
        self._layout_controller = LayoutController(
            model=self._application_model,
            command_manager=self._command_manager,
            layout_manager=self._layout_manager,
        )
        self._node_controller = NodeController(
            model=self._application_model,
            command_manager=self._command_manager,
            project_controller=self._project_controller,
        )

        self._layout_ui_factory = LayoutUIFactory(
            layout_manager=self._layout_manager,
        )
        self._renderer = Renderer(
            layout_manager=self._layout_manager, application_model=self._application_model
        )
        self._plot_types = list(self._renderer.plotting_strategies.keys())
        self._plot_properties_ui_factory = PlotPropertiesUIFactory(
            node_controller=self._node_controller
        )

        self._plot_properties_ui_factory.register_builder(
            PlotType.LINE, _build_line_plot_ui_widgets
        )
        self._plot_properties_ui_factory.register_builder(
            PlotType.SCATTER, _build_scatter_plot_ui_widgets
        )

    def _assemble_menus(self):
        """Assemble the menu bar and its actions."""
        self.logger.info("Assembling menus.")
        menu_builder = MenuBarBuilder(
            recent_files_provider=self._project_controller
        )
        self._menu_bar, self._main_menu_actions = menu_builder.build()

    def _assemble_tooling(self):
        """Assemble the tool manager, individual tools, and the toolbar."""
        self.logger.info("Assembling tooling: ToolManager, SelectionTool, MockTools.")
        self._tool_manager = ToolService(model=self._application_model, command_manager=self._command_manager)
        self._selection_tool = SelectionTool(model=self._application_model, command_manager=self._command_manager, canvas_widget=None)
        self._tool_manager.add_tool(self._selection_tool)
        default_active_tool_name = self._config_service.get("tool.default_active_tool", ToolName.SELECTION.value)
        self._tool_manager.set_active_tool(default_active_tool_name)
        self.logger.debug(f"Default active tool set to: {default_active_tool_name}")
        self._tool_manager.add_tool(MockTool(self._config_service.get("tool.direct_selection.name", ToolName.DIRECT_SELECTION.value), IconPath.get_path("tool_icons.direct_select"), self._application_model, self._command_manager, None))
        self._tool_manager.add_tool(MockTool(self._config_service.get("tool.eyedropper.name", ToolName.EYEDROPPER.value), IconPath.get_path("tool_icons.eyedropper"), self._application_model, self._command_manager, None))
        self._tool_manager.add_tool(MockTool(self._config_service.get("tool.plot.name", ToolName.PLOT.value), IconPath.get_path("tool_icons.plot"), self._application_model, self._command_manager, None))
        self._tool_manager.add_tool(MockTool(self._config_service.get("tool.text.name", ToolName.TEXT.value), IconPath.get_path("tool_icons.text"), self._application_model, self._command_manager, None))
        self._tool_manager.add_tool(MockTool(self._config_service.get("tool.zoom.name", ToolName.ZOOM.value), IconPath.get_path("tool_icons.zoom"), self._application_model, self._command_manager, None))
        tool_bar_builder = ToolBarBuilder(tool_manager=self._tool_manager)
        self._tool_bar, self._tool_bar_actions = tool_bar_builder.build()

    def _assemble_main_window(self):
        """Assemble the main application window."""
        self.logger.info("Assembling main window.")
        # The instantiation of MainWindow and the setter injection
        # remain the same as the previous, correct step.
        self._view = MainWindow(
            model=self._application_model,
            project_actions=self._project_controller,
            project_controller=self._project_controller,
            layout_controller=self._layout_controller,
            node_controller=self._node_controller,
            command_manager=self._command_manager,
            plot_types=self._plot_types,
            menu_bar=self._menu_bar,
            main_menu_actions=self._main_menu_actions,
            tool_bar=self._tool_bar,
            tool_bar_actions=self._tool_bar_actions,
            plot_properties_ui_factory=self._plot_properties_ui_factory,
            layout_ui_factory=self._layout_ui_factory,
        )
        self._project_controller.set_view(self._view)

        self._selection_tool._canvas_widget = self._view.canvas_widget
        for tool in self._tool_manager._tools.values():
            tool._canvas_widget = self._view.canvas_widget

    def _assemble_canvas_controller(self):
        """Assemble the canvas controller. TODO: It makes no sense that this gets its own method"""
        self._canvas_controller = CanvasController(
            model=self._application_model,
            canvas_widget=self._view.canvas_widget,
            tool_manager=self._tool_manager,
            command_manager=self._command_manager,
            layout_controller=self._layout_controller,
        )

    def _connect_signals(self):
        """Connect all application-wide signals to their slots."""
        self.logger.debug("Connecting signals.")
        main_menu = self._view.main_menu_actions
        
        # Original I/O connections are now correctly pointed at the new handlers
        main_menu.new_file_action.triggered.connect(self._project_controller.handle_new_project)
        main_menu.new_file_from_template_action.triggered.connect(
            self._project_controller.handle_new_from_template # No partial needed anymore
        )
        main_menu.open_project_action.triggered.connect(self._project_controller.handle_open_project)
        main_menu.save_project_action.triggered.connect(self._project_controller.handle_save_project)
        main_menu.save_copy_action.triggered.connect(self._project_controller.handle_save_as_project)
        
        # Add connections for Edit Menu actions, now that the builder is decoupled
        main_menu.undo_action.triggered.connect(self._command_manager.undo)
        main_menu.redo_action.triggered.connect(self._command_manager.redo)

        # Presenter slot for model changes
        self._application_model.modelChanged.connect(self._project_controller.on_model_changed)
        self._application_model.projectReset.connect(self._layout_manager.on_model_reset)

        # Original connections for redraw and tools
        self._application_model.modelChanged.connect(self._redraw_canvas_callback)
        self._application_model.selectionChanged.connect(self._redraw_canvas_callback)
        self._application_model.layoutConfigChanged.connect(self._redraw_canvas_callback) #TODO: Consider if this is necessary or if specific layout changes should trigger redraws instead of all config changes.
        self._selection_tool.plot_double_clicked.connect(self._view.show_side_panel)

    def _redraw_canvas_callback(self):
        """Callback to trigger canvas redraw."""
        self.logger.debug("ApplicationAssembler._redraw_canvas_callback called")
        self._renderer.render(
            self._view.canvas_widget.figure,
            self._application_model.scene_root,
            self._application_model.selection,
        )
        self._view.canvas_widget.figure_canvas.draw()

    def assemble(self) -> ApplicationComponents:
        """Assembles and wires all components of the application."""
        self._assemble_core_components()
        self._assemble_menus()
        self._assemble_tooling()
        self._assemble_main_window()
        self._assemble_canvas_controller()
        self._connect_signals()
        self.logger.info("Application assembly complete.")

        return ApplicationComponents(
            composition_root=self,
            app=self._app,
            application_model=self._application_model,
            command_manager=self._command_manager,
            project_controller=self._project_controller,
            layout_controller=self._layout_controller,
            node_controller=self._node_controller,
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
