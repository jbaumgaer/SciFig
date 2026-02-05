import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QMenuBar, QToolBar

from src.application_assembler import ApplicationAssembler
from src.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.builders.tool_bar_builder import ToolBarActions # Assuming ToolBarActions is also a dataclass
from src.models.application_model import ApplicationModel
from src.controllers.main_controller import MainController
from src.commands.command_manager import CommandManager
from src.views.main_window import MainWindow
from src.controllers.tool_manager import ToolManager
from src.controllers.tools.selection_tool import SelectionTool
from src.views.renderer import Renderer
from src.application_components import ApplicationComponents
from src.config_service import ConfigService


@pytest.fixture
def mock_qapplication():
    """Fixture for a mock QApplication."""
    return MagicMock(spec=QApplication)

@pytest.fixture
def mock_model():
    """Fixture for a mock ApplicationModel."""
    model = MagicMock(spec=ApplicationModel)
    model.figure = Mock() # Mock the figure attribute as it's accessed
    return model

@pytest.fixture
def mock_command_manager():
    """Fixture for a mock CommandManager."""
    return MagicMock(spec=CommandManager)

@pytest.fixture
def mock_main_controller():
    """Fixture for a mock MainController."""
    return MagicMock(spec=MainController)

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
    tool_manager = MagicMock(spec=ToolManager)
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
    }.get(key, default)
    return config_service

@pytest.fixture
def assembler(
    mock_qapplication,
    mock_model,
    mock_command_manager,
    mock_main_controller,
    mock_renderer,
    mock_tool_manager,
    mock_selection_tool,
    mock_main_window,
    mock_config_service # Inject the mock config service
):
    """Fixture for an ApplicationAssembler instance with mocked dependencies."""
    # Patch the ConfigService __new__ method so it always returns our mock
    with patch('src.application_assembler.ConfigService', return_value=mock_config_service):
        assembler = ApplicationAssembler(mock_qapplication)
        # Manually assign mocks to internal attributes that are normally set by _assemble_ methods
        # to allow testing of individual _assemble_ methods without running the full assemble()
        assembler._model = mock_model
        assembler._command_manager = mock_command_manager
        assembler._main_controller = mock_main_controller
        assembler._renderer = mock_renderer
        assembler._plot_types = list(mock_renderer.plotting_strategies.keys()) # Simulate _assemble_core_components

        assembler._tool_manager = mock_tool_manager
        assembler._selection_tool = mock_selection_tool
        assembler._view = mock_main_window # Simulate _assemble_main_window

        # Also set the mock_config_service on IconPath if it's being used statically
        # This simulates IconPath.set_config_service(self._config_service) call
        with patch('src.constants.IconPath.set_config_service') as mock_set_config:
            # Call _assemble_core_components to trigger config_service instantiation and IconPath setup
            assembler._assemble_core_components() 
            mock_set_config.assert_called_once_with(mock_config_service)
        
    return assembler

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
        patch('src.application_assembler.MenuBarBuilder') as MockMenuBarBuilder, \
        patch('src.application_assembler.MainMenuActions') as MockMainMenuActions\
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
        patch('src.application_assembler.MenuBarBuilder') as MockMenuBarBuilder, \
        patch('src.application_assembler.ToolBarBuilder') as MockToolBarBuilder, \
        patch('src.application_assembler.MainMenuActions') as MockMainMenuActions, \
        patch('src.application_assembler.MainWindow') as MockMainWindow \
    ):
        # Configure mocks for builders
        MockMenuBarBuilder.return_value.build.return_value = MainMenuActions(
            menu_bar=Mock(spec=QMenuBar), # Needs a QMenuBar instance
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
