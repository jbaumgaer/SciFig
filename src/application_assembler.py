from matplotlib.figure import Figure

from PySide6.QtWidgets import QApplication, QToolBar, QMenuBar

from src.application_components import ApplicationComponents
from src.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.builders.tool_bar_builder import ToolBarActions, ToolBarBuilder
from src.commands.command_manager import CommandManager
from src.controllers.canvas_controller import CanvasController
from src.controllers.main_controller import MainController
from src.controllers.tool_manager import ToolManager
from src.controllers.tools import MockTool
from src.controllers.tools.selection_tool import SelectionTool
from src.constants import IconPath, ToolName
from src.models.application_model import ApplicationModel
from src.views.main_window import MainWindow
from src.views.renderer import Renderer


class ApplicationAssembler:
    """
    Orchestrates the assembly of all application components,
    acting as the composition root.
    """

    def __init__(self, app: QApplication):
        self._app = app
        # Core components
        self._model: ApplicationModel | None = None
        self._command_manager: CommandManager | None = None
        self._main_controller: MainController | None = None
        self._renderer: Renderer | None = None
        self._plot_types: list = []

        # UI components
        self._menu_bar: QMenuBar | None = None
        self._main_menu_actions: MainMenuActions | None = None
        self._tool_bar: QToolBar | None = None
        self._tool_bar_actions: ToolBarActions | None = None
        self._view: MainWindow | None = None

        # Tooling components
        self._tool_manager: ToolManager | None = None
        self._selection_tool: SelectionTool | None = None

        # Other controllers
        self._canvas_controller: CanvasController | None = None

    def _assemble_core_components(self):
        """Assemble core models, managers, and controllers."""
        figure = Figure(figsize=(8.5, 6), dpi=150) # TODO: Use ConfigService here later
        self._model = ApplicationModel(figure=figure)
        self._command_manager = CommandManager(model=self._model)
        self._main_controller = MainController(model=self._model)
        self._renderer = Renderer()
        self._plot_types = list(self._renderer.plotting_strategies.keys())

    def _assemble_menus(self):
        """Assemble the menu bar and its actions."""
        menu_builder = MenuBarBuilder(
            main_controller=self._main_controller,
            command_manager=self._command_manager,
        )
        assembled_menu_actions = menu_builder.build()
        self._menu_bar = assembled_menu_actions.menu_bar
        self._main_menu_actions = assembled_menu_actions

    def _assemble_tooling(self):
        """Assemble the tool manager, individual tools, and the toolbar."""
        self._tool_manager = ToolManager(
            model=self._model, command_manager=self._command_manager
        )

        # Create SelectionTool
        self._selection_tool = SelectionTool(
            model=self._model,
            command_manager=self._command_manager,
            canvas_widget=None,  # Will be set after MainWindow is available
        )
        self._tool_manager.add_tool(self._selection_tool)
        self._tool_manager.set_active_tool(ToolName.SELECTION.value)

        # Placeholder tools for toolbar (not yet implemented)
        self._tool_manager.add_tool(
            MockTool(
                ToolName.DIRECT_SELECTION.value,
                IconPath.DIRECT_SELECT_TOOL,
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                ToolName.EYEDROPPER.value,
                IconPath.EYEDROPPER_TOOL,
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                ToolName.PLOT.value,
                IconPath.PLOT_TOOL,
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                ToolName.TEXT.value,
                IconPath.TEXT_TOOL,
                self._model,
                self._command_manager,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                ToolName.ZOOM.value,
                IconPath.ZOOM_TOOL,
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
        self._view = MainWindow(
            model=self._model,
            main_controller=self._main_controller,
            command_manager=self._command_manager,
            plot_types=self._plot_types,
            menu_bar=self._menu_bar,
            main_menu_actions=self._main_menu_actions,
            tool_bar=self._tool_bar,
            tool_bar_actions=self._tool_bar_actions,
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
        )

    def _connect_signals(self):
        """Connect all application-wide signals to their slots."""
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

        # Tool-specific signals
        self._selection_tool.plot_double_clicked.connect(self._view.show_properties_panel)

    def _redraw_canvas_callback(self):
        """Callback to trigger canvas redraw."""
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
        )
