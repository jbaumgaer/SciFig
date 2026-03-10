# tests/unit/conftest.py
import uuid
from unittest.mock import MagicMock, Mock, create_autospec
from pathlib import Path

import matplotlib.figure
import pandas as pd
import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.controllers.canvas_controller import CanvasController
from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import (
    PlotProperties,
    TextProperties,
    FontProperties,
    Cartesian2DProperties,
    AxisProperties,
    TickProperties,
    LineArtistProperties,
    LineProperties,
    SpineProperties,
)
from src.models.plots.plot_types import (
    AutolimitMode,
    SpinePosition,
    TickDirection,
)
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.event_aggregator import EventAggregator
from src.services.layout_manager import LayoutManager
from src.services.property_service import PropertyService
from src.services.tool_service import ToolService
from src.services.tools.selection_tool import SelectionTool
from src.shared.events import Events
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.ui.renderers.figure_renderer import FigureRenderer
from src.ui.widgets.canvas_widget import CanvasWidget
from src.ui.windows.main_window import MainWindow


class MockSignals(QObject):
    """A QObject containing real signals for mock model testing."""
    layoutConfigChanged = Signal()
    modelChanged = Signal()
    selectionChanged = Signal(list)


@pytest.fixture(scope="function")
def mock_qapplication():
    """Provides a mock QApplication."""
    return MagicMock(spec=QApplication)


@pytest.fixture(scope="function")
def mock_figure():
    """Provides a mock matplotlib figure."""
    return create_autospec(matplotlib.figure.Figure)


@pytest.fixture(scope="function")
def mock_event_aggregator():
    """Provides a mock EventAggregator instance."""
    return MagicMock(spec=EventAggregator)


@pytest.fixture(scope="function")
def mock_property_service():
    """Provides a mock PropertyService instance."""
    return MagicMock(spec=PropertyService)


@pytest.fixture(scope="function")
def real_event_aggregator():
    """Provides a real EventAggregator instance."""
    return EventAggregator()


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
        "tool.default_active_tool": "selection",
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
        "ui.default_layout_mode": "free_form",
    }.get(key, default)
    config_service.get_required.side_effect = lambda key: {
        "figure.default_width": 5.0,
        "figure.default_height": 3.0,
        "figure.default_dpi": 200,
        "figure.default_facecolor": "blue",
    }.get(key)
    return config_service


@pytest.fixture(scope="function")
def mock_application_model(mock_event_aggregator):
    """Fixture for a mock ApplicationModel with real signals."""
    model = MagicMock(spec=ApplicationModel)
    model.figure = Mock()
    mock_scene_root_instance = MagicMock(spec=GroupNode)
    mock_scene_root_instance.children = []
    model.scene_root = mock_scene_root_instance
    model.selection = []
    model.figure_size = (20.0, 15.0)
    model._event_aggregator = mock_event_aggregator

    # Use a QObject with real signals
    signals = MockSignals()
    model.layoutConfigChanged = signals.layoutConfigChanged
    model.modelChanged = signals.modelChanged
    model.selectionChanged = signals.selectionChanged

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
    controller = MagicMock(spec=LayoutController)
    controller._layout_manager = MagicMock(spec=LayoutManager)
    controller._layout_manager.apply_default_grid_layout = MagicMock()
    return controller


@pytest.fixture
def mock_node_controller():
    """Fixture for a mock NodeController."""
    controller = MagicMock(spec=NodeController)
    controller.set_selection = MagicMock()
    return controller


@pytest.fixture
def mock_renderer():
    """Fixture for a mock Renderer."""
    renderer = MagicMock(spec=FigureRenderer)
    renderer.plotting_strategies = {"line": Mock()}
    renderer.render = MagicMock()
    return renderer


@pytest.fixture
def mock_selection_tool():
    """Fixture for a mock SelectionTool."""
    return MagicMock(spec=SelectionTool)


@pytest.fixture
def mock_tool_manager(mock_selection_tool):
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
def mock_plot_properties_ui_factory():
    """Fixture for a mock PlotPropertiesUIFactory."""
    return MagicMock(spec=PlotPropertiesUIFactory)


@pytest.fixture(scope="function")
def mock_canvas_widget():
    """Provides a mock CanvasWidget."""
    canvas_widget = MagicMock(spec=CanvasWidget)
    mock_figure_canvas = MagicMock()
    mock_figure_canvas.mpl_connect = MagicMock()
    mock_figure_canvas.width.return_value = 1000
    mock_figure_canvas.height.return_value = 800
    canvas_widget.figure_canvas = mock_figure_canvas
    return canvas_widget


@pytest.fixture
def mock_canvas_controller():
    """Fixture for a mock CanvasController."""
    return MagicMock(spec=CanvasController)


@pytest.fixture
def sample_dataframe():
    """Provides a sample DataFrame with multiple columns."""
    return pd.DataFrame(
        {"Time": [1, 2, 3], "Voltage": [10, 20, 15], "Current": [1, 2, 1.5]}
    )


# --- Scene Node Fixtures ---

@pytest.fixture(scope="function")
def mock_scene_node():
    """Provides a mock SceneNode."""
    mock = create_autospec(SceneNode, instance=True)
    mock.id = str(uuid.uuid4())
    mock.name = "MockNode"
    mock.visible = True
    mock.locked = False
    mock.to_dict.return_value = {
        "id": mock.id,
        "name": mock.name,
        "type": "SceneNode",
        "children": [],
        "visible": True,
        "locked": False
    }
    return mock


@pytest.fixture(scope="function")
def mock_group_node():
    """Provides a mock GroupNode."""
    mock = create_autospec(GroupNode, instance=True)
    mock.id = str(uuid.uuid4())
    mock.name = "MockGroup"
    mock.children = []
    mock.visible = True
    mock.locked = False
    mock.add_child.side_effect = lambda node: mock.children.append(node)
    mock.to_dict.return_value = {
        "id": mock.id,
        "name": mock.name,
        "type": "GroupNode",
        "children": [],
        "visible": True,
        "locked": False
    }
    mock.hit_test.return_value = None
    return mock


@pytest.fixture
def mock_plot_node():
    """Provides a mock PlotNode with basic properties in physical CM."""
    plot_node = MagicMock(spec=PlotNode)
    plot_node.id = "test_plot_id"
    plot_node.data = MagicMock(spec=pd.DataFrame)
    plot_node.plot_properties = MagicMock()
    plot_node.plot_properties.to_dict.return_value = {"plot_type": "line"}
    plot_node.geometry = Rect(2.0, 2.0, 8.0, 8.0)
    return plot_node


@pytest.fixture
def minimal_plot_dict():
    """Provides a minimal serialized PlotNode dictionary in physical CM."""
    return {
        "id": "p1",
        "type": "PlotNode",
        "name": "Minimal",
        "visible": True,
        "locked": False,
        "children": [],
        "geometry": {"x": 2.0, "y": 2.0, "width": 8.0, "height": 8.0}
    }


# --- Plot Property Fixtures ---

@pytest.fixture
def sample_font():
    return FontProperties(
        family="Arial", style="normal", variant="normal", weight="normal", stretch="normal", size=10
    )


@pytest.fixture
def sample_text(sample_font):
    return TextProperties(text="Test", color="black", font=sample_font)


@pytest.fixture
def sample_ticks():
    return TickProperties(
        major_size=5,
        minor_size=2,
        major_width=1,
        minor_width=0.5,
        major_pad=3,
        minor_pad=3,
        direction=TickDirection.OUT,
        color="black",
        labelcolor="black",
        labelsize=10,
        minor_visible=True,
        minor_ndivs=2,
    )


@pytest.fixture
def sample_axis(sample_ticks, sample_text):
    return AxisProperties(
        ticks=sample_ticks,
        margin=0.05,
        autolimit_mode=AutolimitMode.DATA,
        use_offset=True,
        offset_threshold=4,
        scientific_limits=(-4, 5),
        label=sample_text,
        limits=(None, None),
    )


@pytest.fixture
def sample_plot_properties(sample_axis, sample_text):
    """Provides a complete, versioned PlotProperties tree."""
    return PlotProperties(
        titles={
            "left": sample_text,
            "center": sample_text,
            "right": sample_text,
        },
        coords=Cartesian2DProperties(
            xaxis=sample_axis,
            yaxis=sample_axis,
            spines={
                "left": SpineProperties(True, "black", 1.0, SpinePosition.LEFT),
                "bottom": SpineProperties(True, "black", 1.0, SpinePosition.BOTTOM),
            },
            facecolor="white",
            axis_below=True,
            prop_cycle=["C0", "C1"],
        ),
        legend={},
        artists=[
            LineArtistProperties(
                visible=True,
                zorder=1,
                visuals=LineProperties(1.0, "-", "C0", "None", "C0", "black", 0.5, 5.0),
            )
        ],
        _version=1,
    )
