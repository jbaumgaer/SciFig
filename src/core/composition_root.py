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
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.data_service import DataService
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.services.style_service import StyleService
from src.services.tool_service import ToolService
from src.services.tools import MockTool
from src.services.tools.selection_tool import SelectionTool
from src.shared.constants import IconPath, ToolName
from src.shared.events import Events
from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.ui.builders.tool_bar_builder import ToolBarActions, ToolBarBuilder
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import (
    PlotPropertiesUIFactory,
)
from src.ui.panels.layers_tab import LayersTab
from src.ui.panels.layout_tab import LayoutTab
from src.ui.panels.properties_tab import PropertiesTab
from src.ui.panels.side_panel import SidePanel
from src.ui.renderers.renderer import Renderer
from src.ui.widgets.canvas_widget import CanvasWidget
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
        self._style_service: Optional[StyleService] = None
        self._data_service: Optional[DataService] = None
        self._application_model: Optional[ApplicationModel] = None
        self._view: Optional[MainWindow] = None
        self._project_controller: Optional[ProjectController] = None
        self._layout_controller: Optional[LayoutController] = None
        self._node_controller: Optional[NodeController] = None
        self._canvas_controller: Optional[CanvasController] = None
        self._command_manager: Optional[CommandManager] = None
        self._layout_manager: Optional[LayoutManager] = None
        self._event_aggregator: Optional[EventAggregator] = None
        self._menu_bar: Optional[QMenuBar] = None
        self._main_menu_actions: Optional[MainMenuActions] = None
        self._tool_bar: Optional[QToolBar] = None
        self._tool_bar_actions: Optional[ToolBarActions] = None
        self._layout_ui_factory: Optional[LayoutUIFactory] = None
        self._plot_properties_ui_factory: Optional[PlotPropertiesUIFactory] = None
        self._tool_manager: Optional[ToolService] = None
        self._selection_tool: Optional[SelectionTool] = None
        self._figure: Optional[Figure] = None

        self.logger.debug(
            f"ConfigService provided with path: {self._config_service.get('config_path', 'Not Provided')}"
        )
        IconPath.set_config_service(self._config_service)

    def _assemble_core_components(self):
        """Assemble core models, managers, and controllers."""
        self.logger.info("Assembling core components.")

        self._event_aggregator = EventAggregator()

        figure_width = self._config_service.get_required("figure.default_width")
        figure_height = self._config_service.get_required("figure.default_height")
        figure_dpi = self._config_service.get_required("figure.default_dpi")
        figure_facecolor = self._config_service.get_required("figure.default_facecolor")
        self._figure = Figure(
            figsize=(figure_width, figure_height),
            dpi=figure_dpi,
            facecolor=figure_facecolor,
        )
        self.logger.debug(
            f"Figure created with dimensions: {figure_width}x{figure_height} @ {figure_dpi}dpi, Facecolor: {figure_facecolor}"
        )

        self._application_model = ApplicationModel(
            event_aggregator=self._event_aggregator
        )
        self._command_manager = CommandManager(
            model=self._application_model, event_aggregator=self._event_aggregator
        )
        self._style_service = StyleService(event_aggregator=self._event_aggregator)
        self._data_service = DataService(
            model=self._application_model, event_aggregator=self._event_aggregator
        )
        self._layout_manager = LayoutManager(
            application_model=self._application_model,
            free_engine=FreeLayoutEngine(),
            grid_engine=GridLayoutEngine(),
            config_service=self._config_service,
            event_aggregator=self._event_aggregator,
        )
        self._layout_controller = LayoutController(
            model=self._application_model,
            command_manager=self._command_manager,
            layout_manager=self._layout_manager,
            event_aggregator=self._event_aggregator,
        )
        self._node_controller = NodeController(
            model=self._application_model,
            command_manager=self._command_manager,
            event_aggregator=self._event_aggregator,
        )
        self._renderer = Renderer(
            layout_manager=self._layout_manager,
            application_model=self._application_model,
        )

    def _assemble_project_controller(self):
        """Assemble the project controller."""
        template_dir_path = Path(
            self._config_service.get_required("paths.layout_templates_dir")
        )
        max_recent_files = self._config_service.get_required("layout.max_recent_files")
        self._project_controller = ProjectController(
            lifecycle=self._application_model,
            command_manager=self._command_manager,
            template_dir=template_dir_path,
            max_recent_files=max_recent_files,
            event_aggregator=self._event_aggregator,
        )

    def _assemble_menus(self):
        """Assemble the menu bar and its actions."""
        self.logger.info("Assembling menus.")
        menu_builder = MenuBarBuilder(event_aggregator=self._event_aggregator)
        self._menu_bar, self._main_menu_actions = menu_builder.build()

    def _assemble_tooling(self):
        """Assemble the tool manager, individual tools, and the toolbar."""
        self.logger.info("Assembling tooling.")
        self._tool_manager = ToolService(event_aggregator=self._event_aggregator)
        self._selection_tool = SelectionTool(
            model=self._application_model, canvas_widget=None
        )
        self._tool_manager.add_tool(self._selection_tool)
        default_active_tool_name = self._config_service.get(
            "tool.default_active_tool", ToolName.SELECTION.value
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get(
                    "tool.direct_selection.name", ToolName.DIRECT_SELECTION.value
                ),
                IconPath.get_path("tool_icons.direct_select"),
                self._application_model,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get(
                    "tool.eyedropper.name", ToolName.EYEDROPPER.value
                ),
                IconPath.get_path("tool_icons.eyedropper"),
                self._application_model,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.plot.name", ToolName.PLOT.value),
                IconPath.get_path("tool_icons.plot"),
                self._application_model,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.text.name", ToolName.TEXT.value),
                IconPath.get_path("tool_icons.text"),
                self._application_model,
                None,
            )
        )
        self._tool_manager.add_tool(
            MockTool(
                self._config_service.get("tool.zoom.name", ToolName.ZOOM.value),
                IconPath.get_path("tool_icons.zoom"),
                self._application_model,
                None,
            )
        )
        tool_bar_builder = ToolBarBuilder(
            tool_service=self._tool_manager, event_aggregator=self._event_aggregator
        )
        self._tool_manager.set_active_tool(default_active_tool_name)
        self.logger.debug(f"Default active tool set to: {default_active_tool_name}")
        self._tool_bar, self._tool_bar_actions = tool_bar_builder.build()

    def _assemble_side_panel(self):
        """Assemble the side panel. TODO: This is currently not used and should be integrated into the MainWindow assembly once refactored."""
        self.logger.info("Assembling side panel.")
        self._layout_ui_factory = LayoutUIFactory(
            layout_manager=self._layout_manager,
            event_aggregator=self._event_aggregator,
        )
        self._plot_properties_ui_factory = PlotPropertiesUIFactory(
            event_aggregator=self._event_aggregator,
        )
        self._side_panel = SidePanel(event_aggregator=self._event_aggregator)
        properties_tab = PropertiesTab(
            model=self._application_model,
            event_aggregator=self._event_aggregator,
            plot_properties_ui_factory=self._plot_properties_ui_factory,
            parent=self._side_panel,
        )
        layout_tab = LayoutTab(
            layout_controller=self._layout_controller,
            layout_ui_factory=self._layout_ui_factory,
            event_aggregator=self._event_aggregator,
            parent=self._side_panel,
        )
        layers_tab = LayersTab(
            model=self._application_model,
            event_aggregator=self._event_aggregator,
            parent=self._side_panel,
        )
        self._side_panel.add_tab("properties", properties_tab, "Properties")
        self._side_panel.add_tab("layout", layout_tab, "Layout")
        self._side_panel.add_tab("layers", layers_tab, "Layers")

    def _assemble_main_window(self):
        """Assemble the main application window."""
        self.logger.info("Assembling main window.")
        self._view = MainWindow(
            menu_bar=self._menu_bar,
            main_menu_actions=self._main_menu_actions,
            tool_bar=self._tool_bar,
            tool_bar_actions=self._tool_bar_actions,
            side_panel=self._side_panel,
            event_aggregator=self._event_aggregator,
        )

    def _assemble_canvas_widget(self):
        """Assemble the canvas widget."""
        self._canvas_widget = CanvasWidget(figure=self._figure, parent=self._view)
        self._selection_tool._canvas_widget = (
            self._canvas_widget
        )  # TODO: Why is the canvas_widget having these tool?
        self._view.set_canvas_widget(self._canvas_widget)
        for tool in self._tool_manager._tools.values():
            tool._canvas_widget = self._canvas_widget

    def _assemble_canvas_controller(self):
        """Assemble the canvas controller."""
        self._canvas_controller = CanvasController(
            model=self._application_model,
            event_aggregator=self._event_aggregator,
            canvas_widget=self._canvas_widget,
            tool_manager=self._tool_manager,
        )

    def _connect_signals(self):
        """Connect all application-wide Qt signals to their slots."""
        self.logger.debug("Connecting Qt signals.")
        self._main_menu_actions.exit_action.triggered.connect(self._app.quit)

    def _subscribe_to_events(self):
        """Subscribe handlers to events via the EventAggregator.
        TODO: Unify handle and on naming convention"""
        self.logger.debug("Subscribing to application events.")

        # --- Project Lifecycle Requests ---
        self._event_aggregator.subscribe(
            Events.NEW_PROJECT_REQUESTED, self._project_controller.handle_new_project
        )
        self._event_aggregator.subscribe(
            Events.NEW_PROJECT_FROM_TEMPLATE_REQUESTED,
            self._project_controller.handle_new_from_template_request,
        )
        self._event_aggregator.subscribe(
            Events.OPEN_PROJECT_REQUESTED,
            self._project_controller.handle_open_project_request,
        )
        self._event_aggregator.subscribe(
            Events.SAVE_PROJECT_REQUESTED, self._project_controller.handle_save_project
        )
        self._event_aggregator.subscribe(
            Events.SAVE_PROJECT_AS_REQUESTED,
            self._project_controller.handle_save_as_project_request,
        )
        self._event_aggregator.subscribe(
            Events.OPEN_RECENT_PROJECT_REQUESTED,
            self._project_controller.handle_open_recent_project,
        )

        # --- UI Dialog Responses ---
        self._event_aggregator.subscribe(
            Events.PATH_PROVIDED_FOR_OPEN,
            self._project_controller.on_open_path_provided,
        )
        self._event_aggregator.subscribe(
            Events.PATH_PROVIDED_FOR_SAVE_AS,
            self._project_controller.on_save_as_path_provided,
        )
        self._event_aggregator.subscribe(
            Events.TEMPLATE_PROVIDED_FOR_NEW,
            self._project_controller.on_template_provided,
        )

        # --- Edit Menu Requests ---
        self._event_aggregator.subscribe(
            Events.UNDO_REQUESTED, self._command_manager.undo
        )
        self._event_aggregator.subscribe(
            Events.REDO_REQUESTED, self._command_manager.redo
        )

        # --- NodeController Request Subscriptions ---
        self._event_aggregator.subscribe(
            Events.SUBPLOT_SELECTION_IN_UI_CHANGED,
            self._node_controller._on_subplot_selection_request,
        )
        self._event_aggregator.subscribe(
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
            self._node_controller._on_select_data_file_request,
        )
        self._event_aggregator.subscribe(
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN,
            self._node_controller._on_data_file_path_provided,
        )
        self._event_aggregator.subscribe(
            Events.APPLY_DATA_TO_NODE_REQUESTED,
            self._node_controller._on_apply_data_request,
        )
        self._event_aggregator.subscribe(
            Events.NODE_DATA_LOADED, self._node_controller._on_data_loaded
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_TYPE_REQUESTED,
            self._node_controller._on_plot_type_change_request,
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            self._node_controller._on_generic_property_change_request,
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_VISIBILITY_REQUESTED,
            self._node_controller._on_node_visibility_request,
        )
        self._event_aggregator.subscribe(
            Events.RENAME_NODE_REQUESTED, self._node_controller._on_rename_node_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_LOCKED_REQUESTED,
            self._node_controller._on_node_locked_request,
        )

        # --- DataService Subscriptions ---
        self._event_aggregator.subscribe(
            Events.APPLY_DATA_FILE_REQUESTED, self._data_service.handle_load_request
        )

        # --- MainWindow Subscriptions (for node data dialogs) ---
        self._event_aggregator.subscribe(
            Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED,
            self._view._prompt_for_open_path_for_node_data,
        )

        # --- Renderer Subscriptions (Lifecycle) ---
        self._event_aggregator.subscribe(
            Events.NODE_REMOVED_FROM_SCENE, self._renderer.handle_node_removal
        )

        # --- LayoutManager Subscriptions ---
        self._event_aggregator.subscribe(
            Events.PROJECT_WAS_RESET, self._layout_manager.on_model_reset
        )

        # --- Redraw Canvas Callbacks (Consolidated Generic Events) ---
        self._event_aggregator.subscribe(
            Events.SCENE_GRAPH_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.SELECTION_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.PROJECT_OPENED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.PROJECT_WAS_RESET, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_VISIBILITY_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_LOCKED_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_POSITION_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_SIZE_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.PLOT_COMPONENT_CHANGED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_DATA_FILE_PATH_UPDATED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_DATA_LOADED, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_ADDED_TO_SCENE, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_REMOVED_FROM_SCENE, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_REPARENTED_IN_SCENE, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.NODE_ORDER_CHANGED_IN_SCENE, self._redraw_canvas_callback
        )
        self._event_aggregator.subscribe(
            Events.LAYOUT_CONFIG_CHANGED, self._redraw_canvas_callback
        )

    def _redraw_canvas_callback(self, *args, **kwargs):
        """Callback to trigger canvas redraw."""
        self.logger.debug("CompositionRoot._redraw_canvas_callback called")
        self._renderer.render(
            self._figure,
            self._application_model.scene_root,
            self._application_model.selection,
        )
        self._canvas_widget.figure_canvas.draw()

    def assemble(self) -> ApplicationComponents:
        """Assembles and wires all components of the application."""
        self._assemble_core_components()
        self._assemble_project_controller()  # Must be assembled after core, before menus/main_window
        self._assemble_menus()
        self._assemble_tooling()
        self._assemble_side_panel()
        self._assemble_main_window()
        self._assemble_canvas_widget()
        self._assemble_canvas_controller()
        self._connect_signals()
        self._subscribe_to_events()
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
            style_service=self._style_service,
            data_service=self._data_service,
            layout_manager=self._layout_manager,
            layout_ui_factory=self._layout_ui_factory,
            event_aggregator=self._event_aggregator,
        )
