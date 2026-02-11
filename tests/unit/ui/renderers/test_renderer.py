from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import AxesLimits, LinePlotProperties, PlotMapping
from src.models.plots.plot_types import PlotType
from src.services.layout_manager import LayoutManager
from src.ui.renderers.renderer import Renderer


class TestNode(SceneNode):
    pass


# Mock the Signal class as it's a Qt object and can't be instantiated outside a QApplication
class MockSignal:
    def __init__(self, *args, **kwargs):
        pass

    def emit(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass


@pytest.fixture
def mock_application_model():
    """Mocks ApplicationModel with necessary attributes."""
    model = MagicMock(spec=ApplicationModel)
    model.scene_root = Mock(spec=SceneNode)
    model.selection = []
    model.layoutConfigChanged = MockSignal()  # Mock the signal
    model.scene_root.all_descendants.return_value = []  # Default empty list
    model.current_layout_config = FreeConfig()  # Default layout config
    return model


@pytest.fixture
def mock_layout_manager(mock_application_model):
    """Mocks LayoutManager with necessary attributes."""
    manager = Mock(spec=LayoutManager)
    # Default behavior for get_current_layout_geometries
    manager.get_current_layout_geometries.return_value = {}
    return manager


@pytest.fixture
def sample_data():
    """Create a sample Pandas DataFrame for testing."""
    return pd.DataFrame(
        {
            "x_axis": [1, 2, 3],
            "y_axis": [10, 20, 30],
        }
    )


@pytest.fixture
def plot_node(sample_data):
    """Create a PlotNode with sample data and default properties."""
    node = PlotNode(name="Test Plot")
    node.id = "test_plot_id"  # Assign an ID for dictionary lookups
    node.geometry = (0.1, 0.1, 0.8, 0.8)  # Assign a default geometry
    node.data = sample_data
    node.plot_properties = LinePlotProperties(
        title="Test Title",
        xlabel="X",
        ylabel="Y",
        plot_type=PlotType.LINE,
        plot_mapping=PlotMapping(x="x_axis", y=["y_axis"]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )
    return node


@patch("src.views.renderer.LinePlotStrategy")
@patch("src.views.renderer.ScatterPlotStrategy")
def test_renderer_switches_strategy(
    mock_scatter_class,
    mock_line_class,
    plot_node,
    mock_layout_manager,
    mock_application_model,
):
    """
    Test that the Renderer correctly uses the strategy specified by the PlotNode's plot_type.
    """
    # 1. Arrange
    # Instantiate mocks from the mock classes
    mock_line_strategy = mock_line_class.return_value
    mock_scatter_strategy = mock_scatter_class.return_value

    renderer = Renderer(
        layout_manager=mock_layout_manager, application_model=mock_application_model
    )

    # We need to manually replace the instances in the renderer's dictionary
    # with our mocks to track calls.
    renderer.plotting_strategies[PlotType.LINE] = mock_line_strategy
    renderer.plotting_strategies[PlotType.SCATTER] = mock_scatter_strategy

    mock_figure = Mock()
    mock_ax = mock_figure.add_axes.return_value

    # Configure mock_application_model to return the plot_node
    mock_application_model.scene_root.all_descendants.return_value = [plot_node]
    # Configure mock_layout_manager to return the geometry for the plot_node
    mock_layout_manager.get_current_layout_geometries.return_value = {
        plot_node.id: plot_node.geometry
    }

    # --- Test 1: Verify Line Plot Strategy is Called ---
    plot_node.plot_properties.plot_type = PlotType.LINE

    # 2. Act
    renderer.render(
        mock_figure, mock_application_model.scene_root, mock_application_model.selection
    )

    # 3. Assert
    mock_line_strategy.plot.assert_called_once_with(
        mock_ax,
        plot_node.data,
        plot_node.plot_properties.plot_mapping.x,
        plot_node.plot_properties.plot_mapping.y,
    )
    mock_scatter_strategy.plot.assert_not_called()
    mock_figure.add_axes.assert_called_once_with(plot_node.geometry)

    # --- Reset mocks for the next test ---
    mock_line_strategy.reset_mock()
    mock_scatter_strategy.reset_mock()
    mock_figure.reset_mock()
    mock_figure.add_axes.return_value = Mock()  # Re-acquire mock_ax after reset
    mock_application_model.scene_root.all_descendants.reset_mock()
    mock_layout_manager.get_current_layout_geometries.reset_mock()

    # --- Test 2: Verify Scatter Plot Strategy is Called ---
    plot_node.plot_properties.plot_type = PlotType.SCATTER
    mock_application_model.scene_root.all_descendants.return_value = [plot_node]
    mock_layout_manager.get_current_layout_geometries.return_value = {
        plot_node.id: plot_node.geometry
    }

    # 2. Act
    renderer.render(
        mock_figure, mock_application_model.scene_root, mock_application_model.selection
    )

    # 3. Assert
    mock_scatter_strategy.plot.assert_called_once_with(
        mock_ax,
        plot_node.data,
        plot_node.plot_properties.plot_mapping.x,
        plot_node.plot_properties.plot_mapping.y,
    )
    mock_line_strategy.plot.assert_not_called()
    mock_figure.add_axes.assert_called_once_with(plot_node.geometry)


def test_renderer_calls_correct_render_function_for_node_type(
    mock_layout_manager, mock_application_model
):
    """
    Test that the Renderer correctly calls the render function based on the node's type.
    This test focuses on non-PlotNode types rendered via _render_other_nodes.
    """
    # 1. Arrange
    renderer = Renderer(
        layout_manager=mock_layout_manager, application_model=mock_application_model
    )
    mock_figure = Mock()

    # Create a mock render function for our custom test node
    mock_render_test_node = Mock()

    # Add the new strategy to the renderer
    renderer._render_strategies[TestNode] = mock_render_test_node

    test_node = TestNode(name="MyTestNode")

    # Configure mock_application_model to return an empty list for plot nodes
    # so _render_plots doesn't interfere, and pass the root node with our test_node
    mock_application_model.scene_root.all_descendants.return_value = [
        test_node
    ]  # Include test_node for _render_other_nodes

    # 2. Act
    renderer.render(
        mock_figure, mock_application_model.scene_root, mock_application_model.selection
    )

    # 3. Assert
    # Check that our custom render function was called with the correct arguments
    mock_render_test_node.assert_called_once_with(mock_figure, test_node)
    # Ensure add_axes was not called as this is not a PlotNode
    mock_figure.add_axes.assert_not_called()


def test_renderer_render_free_mode(
    mock_layout_manager, mock_application_model, plot_node
):
    """
    Test that the renderer correctly renders plots in Free-Form mode.
    - Verifies that add_axes is called with the correct geometries provided by LayoutManager.
    - Ensures set_constrained_layout(True) is NOT called for Free-Form mode.
    """
    # TODO: Implement test logic
    pass


def test_renderer_render_grid_mode(
    mock_layout_manager, mock_application_model, plot_node
):
    """
    Test that the renderer correctly renders plots in Grid mode.
    - Verifies that add_axes is called with the correct geometries provided by LayoutManager.
    - Ensures set_constrained_layout(True) IS called for Grid mode.
    """
    # TODO: Implement test logic
    pass


def test_renderer_render_no_plots(mock_layout_manager, mock_application_model):
    """
    Test that the renderer handles an empty list of plots gracefully.
    - No calls to add_axes should occur.
    - No crashes or errors should be raised.
    """
    # TODO: Implement test logic
    pass
