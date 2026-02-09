# tests/unit/conftest.py
import pytest
from unittest.mock import MagicMock, create_autospec, Mock
import matplotlib.figure
from PySide6.QtWidgets import QApplication
import uuid

# Import classes that are being mocked
from src.services.config_service import ConfigService
from src.models.application_model import ApplicationModel
from src.models.nodes.scene_node import SceneNode
from src.models.nodes.group_node import GroupNode
from src.services.commands.command_manager import CommandManager
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.ui.renderers.renderer import Renderer
from src.services.tools.selection_tool import SelectionTool
from src.services.tool_service import ToolService
from src.ui.windows.main_window import MainWindow
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.services.layout_manager import LayoutManager
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.properties_ui_factory import PropertiesUIFactory
from src.controllers.canvas_controller import CanvasController


@pytest.fixture(scope="function")
def mock_qapplication():
    """Provides a mock QApplication."""
    return MagicMock(spec=QApplication)

@pytest.fixture(scope="function")
def mock_figure():
    """Provides a mock matplotlib figure."""
    return create_autospec(matplotlib.figure.Figure)

@pytest.fixture(scope="function")
def mock_config_service():
    """
    Provides a comprehensive mock ConfigService, configurable with default values
    for figure, tools, and layout.
    """
    config_service = MagicMock(spec=ConfigService)
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
    config_service.get_required.side_effect = lambda key: {
        "figure.default_width": 5.0,
        "figure.default_height": 3.0,
        "figure.default_dpi": 200,
        "figure.default_facecolor": "blue",
    }.get(key)
    return config_service

@pytest.fixture(scope="function")
def mock_application_model(): # Renamed from mock_model for clarity
    """Fixture for a mock ApplicationModel."""
    model = MagicMock(spec=ApplicationModel)
    model.figure = Mock() # Mock the figure attribute as it's accessed
    model.scene_root = Mock() # Add scene_root attribute for _redraw_canvas_callback
    model.selection = Mock() # Add selection attribute for _redraw_canvas_callback
    # Mock signals
    model.layoutConfigChanged = MagicMock()
    model.modelChanged = MagicMock()
    model.selectionChanged = MagicMock()
    return model

@pytest.fixture(scope="function")
def mock_scene_node():
    """Provides a mock SceneNode."""
    mock = create_autospec(SceneNode, instance=True)
    mock.id = str(uuid.uuid4())
    mock.name = "MockNode"
    mock.to_dict.return_value = {"id": mock.id, "name": mock.name, "type": "SceneNode", "children": [], "visible": True}
    return mock

@pytest.fixture(scope="function")
def mock_group_node():
    """Provides a mock GroupNode."""
    mock = create_autospec(GroupNode, instance=True)
    mock.id = str(uuid.uuid4())
    mock.name = "MockGroup"
    mock.children = []
    mock.add_child.side_effect = lambda node: mock.children.append(node)
    mock.to_dict.return_value = {"id": mock.id, "name": mock.name, "type": "GroupNode", "children": [], "visible": True}
    mock.hit_test.return_value = None
    return mock

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
    renderer.plotting_strategies = {'line': Mock()}
    renderer.render = MagicMock()
    return renderer

@pytest.fixture
def mock_selection_tool():
    """Fixture for a mock SelectionTool."""
    return MagicMock(spec=SelectionTool)

@pytest.fixture
def mock_tool_manager(mock_selection_tool): # This fixture depends on mock_selection_tool
    """Fixture for a mock ToolManager."""
    tool_manager = MagicMock(spec=ToolService)
    tool_manager._tools = {}
    def mock_add_tool(tool):
        tool_manager._tools[tool.name] = tool
    tool_manager.add_tool.side_effect = mock_add_tool
    tool_manager.set_active_tool = MagicMock()
    return tool_manager

@pytest.fixture
def mock_main_window():
    """Fixture for a mock MainWindow."""
    main_window = MagicMock(spec=MainWindow)
    main_window.canvas_widget = Mock()
    main_window.canvas_widget.figure_canvas = MagicMock()
    main_window.canvas_widget.figure_canvas.draw = MagicMock()
    main_window.new_layout_action = MagicMock()
    main_window.new_layout_action.triggered = MagicMock()
    main_window.save_project_action = MagicMock()
    main_window.save_project_action.triggered = MagicMock()
    main_window.open_project_action = MagicMock()
    main_window.open_project_action.triggered = MagicMock()
    main_window.show_properties_panel = MagicMock()
    return main_window

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
    manager.layoutModeChanged = MagicMock()
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
