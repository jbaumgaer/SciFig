import pandas as pd
import pytest
from unittest.mock import Mock, patch

from src.views.renderer import Renderer
from src.models.nodes import PlotNode, SceneNode
from src.models.nodes.plot_properties import LinePlotProperties, PlotMapping, AxesLimits
from src.models.nodes.plot_types import PlotType


class TestNode(SceneNode):
    pass


@pytest.fixture
def sample_data():
    """Create a sample Pandas DataFrame for testing."""
    return pd.DataFrame({
        'x_axis': [1, 2, 3],
        'y_axis': [10, 20, 30],
    })

@pytest.fixture
def plot_node(sample_data):
    """Create a PlotNode with sample data and default properties."""
    node = PlotNode(name="Test Plot")
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

@patch('src.views.renderer.LinePlotStrategy')
@patch('src.views.renderer.ScatterPlotStrategy')
def test_renderer_switches_strategy(mock_scatter_class, mock_line_class, plot_node):
    """
    Test that the Renderer correctly uses the strategy specified by the PlotNode's plot_type.
    """
    # 1. Arrange
    # Instantiate mocks from the mock classes
    mock_line_strategy = mock_line_class.return_value
    mock_scatter_strategy = mock_scatter_class.return_value

    renderer = Renderer()
    
    # We need to manually replace the instances in the renderer's dictionary
    # with our mocks to track calls.
    renderer.plotting_strategies[PlotType.LINE] = mock_line_strategy
    renderer.plotting_strategies[PlotType.SCATTER] = mock_scatter_strategy

    mock_figure = Mock()
    mock_ax = mock_figure.add_axes.return_value

    # --- Test 1: Verify Line Plot Strategy is Called ---
    plot_node.plot_properties.plot_type = PlotType.LINE

    # 2. Act
    renderer.render(mock_figure, plot_node, [])

    # 3. Assert
    mock_line_strategy.plot.assert_called_once_with(
        mock_ax,
        plot_node.data,
        plot_node.plot_properties.plot_mapping.x,
        plot_node.plot_properties.plot_mapping.y
    )
    mock_scatter_strategy.plot.assert_not_called()

    # --- Reset mocks for the next test ---
    mock_line_strategy.reset_mock()
    mock_scatter_strategy.reset_mock()
    mock_figure.reset_mock()
    mock_ax = mock_figure.add_axes.return_value # Re-acquire mock_ax

    # --- Test 2: Verify Scatter Plot Strategy is Called ---
    plot_node.plot_properties.plot_type = PlotType.SCATTER

    # 2. Act
    renderer.render(mock_figure, plot_node, [])

    # 3. Assert
    mock_scatter_strategy.plot.assert_called_once_with(
        mock_ax,
        plot_node.data,
        plot_node.plot_properties.plot_mapping.x,
        plot_node.plot_properties.plot_mapping.y
    )
    mock_line_strategy.plot.assert_not_called()


def test_renderer_calls_correct_render_function_for_node_type():
    """
    Test that the Renderer correctly calls the render function based on the node's type.
    """
    # 1. Arrange
    renderer = Renderer()
    mock_figure = Mock()

    # Create a mock render function for our custom test node
    mock_render_test_node = Mock()

    # Add the new strategy to the renderer
    renderer._render_strategies[TestNode] = mock_render_test_node

    test_node = TestNode(name="MyTestNode")
    root_node = SceneNode(name="Root")
    root_node.add_child(test_node)

    # 2. Act
    renderer.render(mock_figure, root_node, [])

    # 3. Assert
    # Check that our custom render function was called with the correct arguments
    mock_render_test_node.assert_called_once_with(mock_figure, test_node)