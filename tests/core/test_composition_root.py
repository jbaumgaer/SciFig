from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMenuBar
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.core.composition_root import CompositionRoot
from src.services.commands.command_manager import CommandManager

from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.tool_bar_builder import (
    ToolBarActions,  # Assuming ToolBarActions is also a dataclass
)
from src.services.config_service import ConfigService
from src.controllers.canvas_controller import CanvasController
from src.services.tool_service import ToolService
from src.services.tools.selection_tool import SelectionTool
from src.core.application_components import ApplicationComponents
from src.models.layout.layout_engine import FreeLayoutEngine, GridLayoutEngine
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.properties_ui_factory import PropertiesUIFactory
from src.ui.windows.main_window import MainWindow
from src.ui.renderers.renderer import Renderer


@pytest.fixture
def mock_qapplication():
    """Fixture for a mock QApplication."""
    return MagicMock(spec=QApplication)

@pytest.fixture
def mock_model():
    """Fixture for a mock ApplicationModel."""
    model = MagicMock(spec=ApplicationModel)
    model.figure = Mock() # Mock the figure attribute as it's accessed
    # Mock layoutConfigChanged signal
    model.layoutConfigChanged = MagicMock()
    # Mock current_layout_config for initial state checks
    model.current_layout_config = FreeConfig()
    return model

@pytest.fixture
def mock_command_manager():
    """Fixture for a mock CommandManager."""
    return MagicMock(spec=CommandManager)

@pytest.fixture
def mock_project_controller():
    """Fixture for a mock ProjectController."""
    return MagicMock(spec=ProjectController)

@pytest.fixture
def mock_layout_controller():
    """Fixture for a mock LayoutController."""
    return MagicMock(spec=LayoutController)

@pytest.fixture
def mock_node_controller():
    """Fixture for a mock NodeController."""
    return MagicMock(spec=NodeController)

@pytest.fixture
def mock_renderer():
    """Fixture for a mock Renderer."""
    renderer = MagicMock(spec=Renderer)
    renderer.plotting_strategies = {'line': Mock()} # Mock attribute accessed by assembler
    return renderer

@pytest.fixture
def mock_selection_tool():
    """Fixture for a mock SelectionTool."""
    return MagicMock(spec=SelectionTool)

@pytest.fixture
def mock_tool_manager(mock_selection_tool):
    """Fixture for a mock ToolManager."""
    tool_manager = MagicMock(spec=ToolService)
    # Mock add_tool to avoid errors when MockTool is added
    tool_manager.add_tool.return_value = None
    tool_manager._tools = {'selection': mock_selection_tool} # Mock internal state used by assembler
    return tool_manager

@pytest.fixture
def mock_main_window():
    """Fixture for a mock MainWindow."""
    main_window = MagicMock(spec=MainWindow)
    main_window.canvas_widget = Mock() # Mock canvas_widget as it's accessed
    # Mock signals/actions that are connected
    main_window.new_layout_action = MagicMock()
    main_window.save_project_action = MagicMock()
    main_window.open_project_action = MagicMock()
    return main_window

@pytest.fixture
def mock_config_service():
    """Fixture for a mock ConfigService."""
    config_service = MagicMock(spec=ConfigService)
    # Configure mock to return specific values for testing figure creation
    config_service.get.side_effect = lambda key, default=None: {
        "figure.default_width": 5.0,
        "figure.default_height": 3.0,
        "figure.default_dpi": 200,
        "figure.default_facecolor": "blue",
        "tool.default_active_tool": "selection", # Ensure this matches ToolName.SELECTION.value
        "paths.icon_base_dir": "mock/icons",
        "paths.tool_icons.select": "mock_select.svg",
        "paths.tool_icons.direct_select": "mock_direct_select.svg",
        "paths.tool_icons.eyedropper": "mock_eyedropper.svg",
        "paths.tool_icons.plot": "mock_plot.svg",
        "paths.tool_icons.text": "mock_text.svg",
        "paths.tool_icons.zoom": "mock_zoom.svg",
        "organization": "TestOrg",
        "app_name": "TestApp",
        "layout.default_margin": 0.1,
        "layout.default_gutter": 0.08,
        "layout.max_recent_files": 5,
        "ui.default_layout_mode": "free_form", # Added for LayoutManager initialization
    }.get(key, default)
    return config_service

@pytest.fixture
def mock_free_layout_engine():
    """Fixture for a mock FreeLayoutEngine."""
    return MagicMock(spec=FreeLayoutEngine)

@pytest.fixture
def mock_grid_layout_engine():
    """Fixture for a mock GridLayoutEngine."""
    return MagicMock(spec=GridLayoutEngine)

@pytest.fixture
def mock_layout_manager():
    """Fixture for a mock LayoutManager."""
    manager = MagicMock(spec=LayoutManager)
    manager.layoutModeChanged = MagicMock() # Mock the signal
    return manager

@pytest.fixture
def mock_layout_ui_factory():
    """Fixture for a mock LayoutUIFactory."""
    return MagicMock(spec=LayoutUIFactory)

@pytest.fixture
def mock_properties_ui_factory():
    """Fixture for a mock PropertiesUIFactory."""
    return MagicMock(spec=PropertiesUIFactory)

@pytest.fixture
def mock_canvas_controller():
    """Fixture for a mock CanvasController."""
    return MagicMock(spec=CanvasController)


@pytest.fixture
def assembler(
    mock_qapplication,
    mock_model,
    mock_command_manager,
    mock_project_controller,
    mock_layout_controller,
    mock_node_controller,
    mock_renderer,
    mock_tool_manager,
    mock_selection_tool,
    mock_main_window,
    mock_config_service,
    mock_free_layout_engine,
    mock_grid_layout_engine,
    mock_layout_manager,
    mock_layout_ui_factory,
    mock_properties_ui_factory
    mock_canvas_controller,
):
    """Fixture for an ApplicationAssembler instance with mocked dependencies."""
    # Patch the ConfigService __new__ method so it always returns our mock
    with patch('src.composition_root.ConfigService', return_value=mock_config_service), \
         patch('src.composition_root.ApplicationModel', return_value=mock_model), \
         patch('src.composition_root.CommandManager', return_value=mock_command_manager), \
         patch('src.composition_root.ProjectController', return_value=mock_project_controller), \
         patch('src.composition_root.LayoutController', return_value=mock_layout_controller), \
         patch('src.composition_root.NodeController', return_value=mock_node_controller), \
         patch('src.composition_root.LayoutManager', return_value=mock_layout_manager), \
         patch('src.composition_root.FreeLayoutEngine', return_value=mock_free_layout_engine), \
         patch('src.composition_root.GridLayoutEngine', return_value=mock_grid_layout_engine), \
         patch('src.composition_root.LayoutUIFactory', return_value=mock_layout_ui_factory), \
         patch('src.composition_root.PropertiesUIFactory', return_value=mock_properties_ui_factory), \
         patch('src.composition_root.Renderer', return_value=mock_renderer), \
         patch('src.composition_root.ToolManager', return_value=mock_tool_manager), \
         patch('src.composition_root.SelectionTool', return_value=mock_selection_tool), \
         patch('src.composition_root.MainWindow', return_value=mock_main_window), \
         patch('src.composition_root.CanvasController', return_value=mock_canvas_controller), \
         patch('src.composition_root.MenuBarBuilder'), \
         patch('src.composition_root.ToolBarBuilder'), \
         patch('src.constants.IconPath.set_config_service') as mock_set_icon_config:

        composition_root_instance = CompositionRoot(mock_qapplication, mock_config_service)
        composition_root_instance._model = mock_model # Ensure internal reference is the mock
        composition_root_instance._command_manager = mock_command_manager
        composition_root_instance._project_controller = mock_project_controller
        composition_root_instance._layout_controller = mock_layout_controller
        composition_root_instance._node_controller = mock_node_controller
        composition_root_instance._layout_manager = mock_layout_manager
        composition_root_instance._free_layout_engine = mock_free_layout_engine
        composition_root_instance._grid_layout_engine = mock_grid_layout_engine
        composition_root_instance._layout_ui_factory = mock_layout_ui_factory
        composition_root_instance._view = mock_main_window
        composition_root_instance._properties_ui_factory = mock_properties_ui_factory
        composition_root_instance._canvas_controller = mock_canvas_controller
        composition_root_instance._tool_manager = mock_tool_manager
        composition_root_instance._selection_tool = mock_selection_tool
        composition_root_instance._renderer = mock_renderer

        mock_set_icon_config.assert_called_once_with(mock_config_service)

    return composition_root_instance



        # Core components
        self._model: ApplicationModel | None = None
        self._command_manager: CommandManager | None = None
        # self._main_controller: MainController | None = None # Removed
        self._project_controller: ProjectController | None = None
        self._layout_controller: LayoutController | None = None
        self._node_controller: NodeController | None = None
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

# Test for the fix in _assemble_menus
def test_assemble_menus_assigns_correctly(assembler, mock_main_controller, mock_command_manager):
    """
    Test that _assemble_menus correctly assigns _menu_bar and _main_menu_actions
    from the MenuBarBuilder's build() method.
    """
    # Create a mock MainMenuActions object that MenuBarBuilder.build() would return
    mock_menu_bar = Mock(spec=QMenuBar)
    mock_main_menu_actions = MainMenuActions(
        menu_bar=mock_menu_bar,
        file_menu=Mock(), new_layout_action=Mock(), new_file_action=Mock(),
        new_file_from_template_action=Mock(), open_project_action=Mock(),
        open_recent_projects_menu=Mock(), close_action=Mock(), save_project_action=Mock(),
        save_copy_action=Mock(), export_figure_menu=Mock(), export_vector_menu=Mock(),
        export_raster_menu=Mock(), export_svg_action=Mock(), export_pdf_action=Mock(),
        export_eps_action=Mock(), export_png_action=Mock(), export_tiff_action=Mock(),
        export_python_action=Mock(), exit_action=Mock(), edit_menu=Mock(),
        undo_action=Mock(), redo_action=Mock(), cut_action=Mock(), copy_action=Mock(),
        paste_action=Mock(), colors_action=Mock(), settings_action=Mock()
    )

    # Mock the MenuBarBuilder to return our specific mock_main_menu_actions
    with (\
        patch('src.composition_root.MenuBarBuilder') as MockMenuBarBuilder, \
        patch('src.composition_root.MainMenuActions') as MockMainMenuActions\
    ):

        # Configure the mock builder to return the mock MainMenuActions
        MockMenuBarBuilder.return_value.build.return_value = mock_main_menu_actions

        # Call the method under test
        assembler._assemble_menus()

        # Assertions
        assert assembler._menu_bar is mock_menu_bar
        assert assembler._main_menu_actions is mock_main_menu_actions

        # Optionally, verify MenuBarBuilder was called correctly
        MockMenuBarBuilder.assert_called_once_with(
            main_controller=mock_main_controller,
            command_manager=mock_command_manager
        )

# Test for the full assemble method (integration-like)
def test_assemble_returns_application_components(assembler, mock_main_window):
    """
    Test that the full assemble() method runs without error and returns
    a fully populated ApplicationComponents object.
    """
    # Mock dependencies that are created/used in assemble but not yet mocked in fixtures
    # (e.g., ToolBarBuilder.build() which is called inside _assemble_tooling)
    mock_toolbar = Mock(spec=QToolBar)
    mock_toolbar_actions = MagicMock(spec=ToolBarActions)

    with (\
        patch('src.composition_root.MenuBarBuilder'), \
        patch('src.composition_root.ToolBarBuilder') as MockToolBarBuilder, \
        patch('src.composition_root.MainMenuActions'), \
        patch('src.composition_root.MainWindow') as MockMainWindow \
    ):
        # Configure mocks for builders
        # MockMenuBarBuilder.return_value.build.return_value = MainMenuActions(
        #     menu_bar=Mock(spec=QMenuBar), # Needs a QMenuBar instance
        #     file_menu=Mock(), new_layout_action=Mock(), new_file_action=Mock(),
        #     new_file_from_template_action=Mock(), open_project_action=Mock(),
        #     open_recent_projects_menu=Mock(), close_action=Mock(), save_project_action=Mock(),
        #     save_copy_action=Mock(), export_figure_menu=Mock(), export_vector_menu=Mock(),
        #     export_raster_menu=Mock(), export_svg_action=Mock(), export_pdf_action=Mock(),
        #     export_eps_action=Mock(), export_png_action=Mock(), export_tiff_action=Mock(),
        #     export_python_action=Mock(), exit_action=Mock(), edit_menu=Mock(),
        #     undo_action=Mock(), redo_action=Mock(), cut_action=Mock(), copy_action=Mock(),
        #     paste_action=Mock(), colors_action=Mock(), settings_action=Mock()
        # )
        MockToolBarBuilder.return_value.build.return_value = (mock_toolbar, mock_toolbar_actions)
        MockMainWindow.return_value = mock_main_window # Ensure it returns the fixture's mock

        # Call the full assemble method
        components = assembler.assemble()

        # Assertions
        assert isinstance(components, ApplicationComponents)
        assert components.app is assembler._app
        assert components.model is assembler._model
        assert components.command_manager is assembler._command_manager
        assert components.main_controller is assembler._main_controller
        assert components.canvas_controller is assembler._canvas_controller
        assert components.view is assembler._view
        assert components.selection_tool is assembler._selection_tool
        assert components.tool_manager is assembler._tool_manager
        assert components.main_menu_actions is not None
        assert components.tool_bar_actions is not None

def test_assemble_core_components_uses_config_for_figure(assembler, mock_model, mock_config_service):
    """
    Test that _assemble_core_components uses values from ConfigService for Figure creation.
    """
    # Assert that the figure attributes reflect config values
    # mock_model.figure.get_figwidth.assert_called_with(mock_config_service.get("figure.default_width"))
    # mock_model.figure.get_figheight.assert_called_with(mock_config_service.get("figure.default_height"))
    # mock_model.figure.set_dpi.assert_called_with(mock_config_service.get("figure.default_dpi"))
    # mock_model.figure.set_facecolor.assert_called_with(mock_config_service.get("figure.default_facecolor"))
    pass

def test_assemble_main_window_receives_config_service(assembler, mock_main_window, mock_config_service):
    """
    Test that MainWindow.__init__ receives the ConfigService instance.
    """
    # This check will be part of a broader integration test for assembler.assemble()
    pass

def test_main_controller_receives_config_service(assembler, mock_main_controller, mock_config_service):
    """
    Test that MainController.__init__ receives the ConfigService instance.
    """
    # This check will be part of a broader integration test for assembler.assemble()
    pass

def test_icon_path_config_service_is_set(assembler, mock_config_service):
    """
    Test that ConfigService is correctly set on the IconPath class.
    """
    # This assertion is now part of the assembler fixture's patch for IconPath.set_config_service
    pass

def test_composition_root_layout_component_wiring(assembler, mock_model, mock_command_manager,
                                                    mock_config_service, mock_free_layout_engine,
                                                    mock_grid_layout_engine, mock_layout_manager,
                                                    mock_layout_ui_factory, mock_main_controller,
                                                    mock_main_window, mock_renderer, mock_tool_manager,
                                                    mock_canvas_controller):
    """
    Test that ApplicationAssembler successfully instantiates and wires up all new layout components
    (FreeLayoutEngine, GridLayoutEngine, LayoutManager, LayoutUIFactory) with correct dependencies,
    and passes LayoutManager to MainController and Renderer, and LayoutUIFactory to MainWindow.
    """
    # Ensure that all component factories are reset before calling assemble
    ApplicationModel.reset_mock()
    CommandManager.reset_mock()
    MainController.reset_mock()
    FreeLayoutEngine.reset_mock()
    GridLayoutEngine.reset_mock()
    LayoutManager.reset_mock()
    LayoutUIFactory.reset_mock()
    Renderer.reset_mock()
    ToolService.reset_mock()
    SelectionTool.reset_mock()
    MainWindow.reset_mock()
    CanvasController.reset_mock()


    # Call assemble to trigger all instantiations and wiring
    components = assembler.assemble()

    # Verify FreeLayoutEngine instantiation
    FreeLayoutEngine.assert_called_once_with(config_service=mock_config_service)
    assert components.layout_manager._free_engine is mock_free_layout_engine

    # Verify GridLayoutEngine instantiation
    GridLayoutEngine.assert_called_once_with(config_service=mock_config_service)
    assert components.layout_manager._grid_engine is mock_grid_layout_engine

    # Verify LayoutManager instantiation
    LayoutManager.assert_called_once_with(
        application_model=mock_model,
        free_engine=mock_free_layout_engine,
        grid_engine=mock_grid_layout_engine,
        config_service=mock_config_service,
    )
    assert components.layout_manager is mock_layout_manager

    # Verify MainController receives LayoutManager
    MainController.assert_called_once_with(
        model=mock_model,
        config_service=mock_config_service,
        layout_manager=mock_layout_manager,
        command_manager=mock_command_manager
    )
    assert components.main_controller is mock_main_controller

    # Verify LayoutUIFactory instantiation
    LayoutUIFactory.assert_called_once_with(
        main_controller=mock_main_controller,
        layout_manager=mock_layout_manager,
        application_model=mock_model,
    )
    assert components.layout_ui_factory is mock_layout_ui_factory

    # Verify Renderer receives LayoutManager
    Renderer.assert_called_once_with(layout_manager=mock_layout_manager, application_model=mock_model)
    assert components.canvas_controller.model._renderer is mock_renderer # Renderer is set in canvas_controller.model

    # Verify MainWindow receives LayoutUIFactory and LayoutManager
    MainWindow.assert_called_once_with(
        model=mock_model,
        main_controller=mock_main_controller,
        command_manager=mock_command_manager,
        plot_types=mock_renderer.plotting_strategies.keys(), # Assumes plot_types is derived from renderer
        menu_bar=assembler._menu_bar, # Cannot mock this easily without further patching
        main_menu_actions=assembler._main_menu_actions,
        tool_bar=assembler._tool_bar,
        tool_bar_actions=assembler._tool_bar_actions,
        properties_ui_factory=assembler._properties_ui_factory,
        config_service=mock_config_service,
        layout_ui_factory=mock_layout_ui_factory,
        layout_manager=mock_layout_manager,
    )
    assert components.view is mock_main_window

    # Verify CanvasController receives LayoutManager and MainController
    CanvasController.assert_called_once_with(
        model=mock_model,
        canvas_widget=mock_main_window.canvas_widget,
        tool_manager=mock_tool_manager,
        command_manager=mock_command_manager,
        layout_manager=mock_layout_manager,
        main_controller=mock_main_controller,
    )
    assert components.canvas_controller is mock_canvas_controller

def test_composition_root_initial_layout_mode_reflection(assembler, mock_model, mock_main_window):
    """
    Test that the initial layout mode (from ConfigService) is correctly set in the ApplicationModel
    and reflected in the UI (via MainWindow's initial update slot if applicable).
    """
    # TODO: Implement test logic
    pass
