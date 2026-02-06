from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.commands.command_manager import CommandManager
from src.controllers.canvas_controller import CanvasController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)
from src.views.canvas_widget import CanvasWidget
from src.layout_manager import LayoutManager # New import
from src.constants import LayoutMode # New import
from src.controllers.main_controller import MainController # New import


@pytest.fixture
def mock_model():
    """Provides a mock ApplicationModel."""
    model = MagicMock(spec=ApplicationModel)
    # Correctly mock scene_root and its children attribute
    mock_scene_root = MagicMock()
    mock_scene_root.children = []
    model.scene_root = mock_scene_root
    model.modelChanged = MagicMock() # Ensure this is mocked
    return model


@pytest.fixture
def mock_canvas_widget():
    """Provides a mock CanvasWidget."""
    canvas_widget = MagicMock(spec=CanvasWidget)
    # Correctly mock figure_canvas and its mpl_connect method
    mock_figure_canvas = MagicMock()
    mock_figure_canvas.mpl_connect = MagicMock()
    canvas_widget.figure_canvas = mock_figure_canvas
    return canvas_widget


@pytest.fixture
def mock_tool_manager():
    """Provides a mock ToolManager."""
    return MagicMock()


@pytest.fixture
def mock_command_manager():
    """Provides a mock CommandManager."""
    return MagicMock(spec=CommandManager)

@pytest.fixture
def mock_layout_manager():
    """Provides a mock LayoutManager."""
    manager = MagicMock()
    manager.layout_mode = LayoutMode.FREE_FORM # Default to Free Form
    return manager

@pytest.fixture
def mock_main_controller():
    """Provides a mock MainController."""
    controller = MagicMock(spec=MainController)
    controller.apply_default_grid_layout = MagicMock() # Mock the method
    return controller


@pytest.fixture
def canvas_controller(
    mock_model, mock_canvas_widget, mock_tool_manager, mock_command_manager, mock_layout_manager, mock_main_controller
):
    """Provides a CanvasController instance."""
    return CanvasController(
        model=mock_model,
        canvas_widget=mock_canvas_widget,
        tool_manager=mock_tool_manager,
        command_manager=mock_command_manager,
        layout_manager=mock_layout_manager,
        main_controller=mock_main_controller,
    )


@pytest.fixture
def sample_dataframe():
    """Provides a sample DataFrame with multiple columns."""
    return pd.DataFrame(
        {"Time": [1, 2, 3], "Voltage": [10, 20, 15], "Current": [1, 2, 1.5]}
    )


@pytest.fixture
def plot_node_empty_props():
    """Provides a PlotNode with empty plot_properties."""
    node = PlotNode()
    return node


@pytest.fixture
def plot_node_with_mapping():
    """Provides a PlotNode with an existing plot_mapping."""
    node = PlotNode()
    node.plot_properties = LinePlotProperties(
        title="Existing Title",
        xlabel="Existing X Label",
        ylabel="Existing Y Label",
        plot_mapping=PlotMapping(x="ExistingX", y=["ExistingY"]),
        axes_limits=AxesLimits(xlim=(0, 1), ylim=(0, 1)),
    )
    return node


# --- Test Cases ---


def test_on_data_ready_sets_default_properties_for_new_data(
    canvas_controller,
    mock_model,
    mock_command_manager,
    sample_dataframe,
    plot_node_empty_props,
):
    """
    Verifies that on_data_ready sets default plot_mapping, xlabel, and ylabel
    when data is loaded into a plot with no pre-existing mapping.
    """
    plot_node_empty_props.name = "Test Plot"  # Give it a name for context

    # Add node to model's children so the if condition passes in on_data_ready
    mock_model.scene_root.children.append(plot_node_empty_props)

    canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

    # Assert node.data was set
    pd.testing.assert_frame_equal(plot_node_empty_props.data, sample_dataframe)

    # Assert plot_properties was created
    assert isinstance(plot_node_empty_props.plot_properties, LinePlotProperties)
    assert plot_node_empty_props.plot_properties.title == "Test Plot"
    assert plot_node_empty_props.plot_properties.xlabel == "Time"
    assert plot_node_empty_props.plot_properties.ylabel == "Voltage"
    assert plot_node_empty_props.plot_properties.plot_mapping.x == "Time"
    assert plot_node_empty_props.plot_properties.plot_mapping.y == ["Voltage"]

    # Assert modelChanged signal was emitted
    mock_model.modelChanged.emit.assert_called_once()


def test_on_data_ready_does_not_overwrite_existing_properties(
    canvas_controller,
    mock_model,
    mock_command_manager,
    sample_dataframe,
    plot_node_with_mapping,
):
    """
    Verifies that on_data_ready does not overwrite plot_mapping or labels
    if they already exist on the plot node.
    """
    mock_model.scene_root.children.append(plot_node_with_mapping)

    canvas_controller.on_data_ready(sample_dataframe, plot_node_with_mapping)

    # Assert node.data was set
    pd.testing.assert_frame_equal(plot_node_with_mapping.data, sample_dataframe)

    # Assert that plot_properties are unchanged
    assert plot_node_with_mapping.plot_properties.title == "Existing Title"
    assert plot_node_with_mapping.plot_properties.plot_mapping.x == "ExistingX"

    # Assert modelChanged signal was emitted
    mock_model.modelChanged.emit.assert_called_once()


def test_on_data_ready_with_insufficient_columns(
    canvas_controller, mock_model, mock_command_manager, plot_node_empty_props
):
    """
    Verifies that on_data_ready does not set default properties if the dataframe
    has fewer than two columns.
    """
    dataframe_one_col = pd.DataFrame({"Time": [1, 2, 3]})
    mock_model.scene_root.children.append(plot_node_empty_props)

    canvas_controller.on_data_ready(dataframe_one_col, plot_node_empty_props)

    # Assert node.data was set
    pd.testing.assert_frame_equal(plot_node_empty_props.data, dataframe_one_col)

    # Assert no commands were executed for properties (this test doesn't use command_manager anyway for this part)
    # mock_command_manager.execute_command.assert_not_called()

    # Assert modelChanged signal was emitted
    mock_model.modelChanged.emit.assert_called_once()


def test_on_data_ready_node_not_in_scene(
    canvas_controller,
    mock_model,
    mock_command_manager,
    sample_dataframe,
    plot_node_empty_props,
):
    """
    Verifies that on_data_ready does nothing if the target node is not
    present in the model's scene graph (e.g., deleted during async load).
    """
    # Do NOT add plot_node_empty_props to mock_model.scene_root.children
    initial_data = plot_node_empty_props.data  # Should be None

    canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

    # Assert node.data was NOT set
    assert plot_node_empty_props.data is initial_data

    # Assert no commands were executed
    mock_command_manager.execute_command.assert_not_called()

    # Assert modelChanged signal was NOT emitted
    mock_model.modelChanged.emit.assert_not_called()


def test_on_data_ready_in_free_form_mode(
    canvas_controller,
    mock_model,
    mock_layout_manager,
    mock_main_controller,
    sample_dataframe,
    plot_node_empty_props,
):
    """
    Test that on_data_ready does NOT call apply_default_grid_layout when in FREE_FORM mode.
    """
    mock_layout_manager.layout_mode = LayoutMode.FREE_FORM
    mock_model.scene_root.children.append(plot_node_empty_props)

    canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

    mock_main_controller.apply_default_grid_layout.assert_not_called()
    mock_model.modelChanged.emit.assert_called_once()


def test_on_data_ready_in_grid_mode(
    canvas_controller,
    mock_model,
    mock_layout_manager,
    mock_main_controller,
    sample_dataframe,
    plot_node_empty_props,
):
    """
    Test that on_data_ready calls apply_default_grid_layout when in GRID mode.
    """
    mock_layout_manager.layout_mode = LayoutMode.GRID
    mock_model.scene_root.children.append(plot_node_empty_props)

    canvas_controller.on_data_ready(sample_dataframe, plot_node_empty_props)

    mock_main_controller.apply_default_grid_layout.assert_called_once()
    mock_model.modelChanged.emit.assert_called_once()