from unittest.mock import MagicMock, call, patch

import matplotlib.figure
import pandas as pd
import pytest

from src.models.nodes import PlotNode, SceneNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    PlotMapping,
    PlotProperties,
)
from src.views.renderer import Renderer


@pytest.fixture
def renderer():
    """Fixture for a Renderer instance."""
    return Renderer()


@pytest.fixture
def mock_figure():
    """Fixture for a mocked Matplotlib Figure."""
    # We use a real figure object as a spec for the mock to ensure
    # that the mock behaves like a real figure.
    fig = matplotlib.figure.Figure()
    mock_fig = MagicMock(spec=fig)
    mock_fig.transFigure = "mock_transform"  # Mock the transform attribute
    return mock_fig


@pytest.fixture
def root_node():
    """Fixture for a root SceneNode."""
    return SceneNode(name="root")


def test_render_clears_figure_and_calls_helpers(renderer, mock_figure, root_node):
    """Test that render() calls clear, _render_node, and _render_highlights."""
    selection = [PlotNode(name="selected_plot")]

    # Mock the internal methods to isolate the render method's logic
    renderer._render_node = MagicMock()
    renderer._render_highlights = MagicMock()

    renderer.render(mock_figure, root_node, selection)

    mock_figure.clear.assert_called_once()
    renderer._render_node.assert_called_once_with(mock_figure, root_node)
    renderer._render_highlights.assert_called_once_with(mock_figure, selection)


def test_render_node_handles_invisible_node(renderer, mock_figure, root_node):
    """Test that an invisible node is not rendered."""
    root_node.visible = False
    renderer._render_node(mock_figure, root_node)
    # If the node is invisible, no rendering calls should be made.
    mock_figure.add_axes.assert_not_called()


@patch("matplotlib.patches.Rectangle")
def test_render_highlights(mock_rectangle, renderer, mock_figure):
    """Test that _render_highlights creates a rectangle for a selected PlotNode."""
    plot_node = PlotNode(name="p1")
    plot_node.geometry = (0.1, 0.2, 0.3, 0.4)
    selection = [plot_node]

    renderer._render_highlights(mock_figure, selection)

    # Check that a Rectangle patch was created with the correct properties
    mock_rectangle.assert_called_once_with(
        (0.1, 0.2),
        0.3,
        0.4,
        facecolor="none",
        edgecolor="cornflowerblue",
        linewidth=2,
        transform=mock_figure.transFigure,
        clip_on=False,
        zorder=1000,
    )

    # Check that the created patch was added to the figure
    mock_figure.add_artist.assert_called_once_with(mock_rectangle.return_value)


def test_render_plot_node_no_data(renderer, mock_figure):
    """Test rendering a PlotNode that has no data."""
    plot_node = PlotNode()
    mock_axes = MagicMock()
    mock_figure.add_axes.return_value = mock_axes

    renderer._render_node(mock_figure, plot_node)

    mock_figure.add_axes.assert_called_once_with(plot_node.geometry)
    mock_axes.tick_params.assert_called_once()
    mock_axes.plot.assert_not_called()


def test_render_plot_node_with_data_and_mapping(renderer, mock_figure):
    """Test rendering a PlotNode with data and a specific plot_mapping."""
    df = pd.DataFrame(
        {"time": [1, 2, 3], "temp": [20, 22, 19], "humidity": [50, 55, 52]}
    )
    plot_node = PlotNode()
    plot_node.data = df
    plot_node.plot_properties = PlotProperties(
        plot_mapping=PlotMapping(x="time", y=["temp", "humidity"]),
        title="Test Data",
        xlabel="Time",
        ylabel="Value",
        axes_limits=AxesLimits(xlim=(0, 4), ylim=(15, 60)),
    )

    mock_axes = MagicMock()
    mock_figure.add_axes.return_value = mock_axes

    renderer._render_node(mock_figure, plot_node)

    # Check axes was created
    mock_figure.add_axes.assert_called_once_with(plot_node.geometry)

    # Check that plot was called twice, once for each y-column
    assert mock_axes.plot.call_count == 2

    # Check legend is called because there are multiple y-columns
    mock_axes.legend.assert_called_once()

    # Check labels and limits
    mock_axes.set_title.assert_called_once_with("Test Data")
    mock_axes.set_xlabel.assert_called_once_with("Time")
    mock_axes.set_ylabel.assert_called_once_with("Value")
    mock_axes.set_xlim.assert_called_once_with((0, 4))
    mock_axes.set_ylim.assert_called_once_with((15, 60))


def test_render_plot_node_with_data_default_plot(renderer, mock_figure):
    """Test rendering a PlotNode with data but no mapping (default plot)."""
    df = pd.DataFrame({"colA": [10, 20], "colB": [30, 40]})
    plot_node = PlotNode()
    plot_node.data = df
    plot_node.plot_properties = PlotProperties(
        title="",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )

    mock_axes = MagicMock()
    mock_figure.add_axes.return_value = mock_axes

    renderer._render_node(mock_figure, plot_node)

    # Check that plot was called once with the first two columns
    mock_axes.plot.assert_called_once()
    # Check that the first argument to plot is indeed the first column
    pd.testing.assert_series_equal(mock_axes.plot.call_args[0][0], df["colA"])
    # Check that the second argument to plot is indeed the second column
    pd.testing.assert_series_equal(mock_axes.plot.call_args[0][1], df["colB"])

    mock_axes.legend.assert_not_called()


def test_render_recursive_calls(renderer, mock_figure):
    """Test that _render_node recursively calls itself for children."""
    root = SceneNode(name="root")
    child1 = PlotNode(parent=root, name="p1")
    child2 = PlotNode(parent=root, name="p2")

    # Mock the method to spy on its calls
    renderer._render_node = MagicMock()
    # But we need the original implementation for the recursive call to work,
    # so we assign it to side_effect.
    renderer._render_node.side_effect = renderer.__class__._render_node.__get__(
        renderer, renderer.__class__
    )

    renderer._render_node(mock_figure, root)

    # Expect 3 calls: one for the root, and one for each child.
    assert renderer._render_node.call_count == 3
    # Check the call arguments
    expected_calls = [
        call(mock_figure, root),
        call(mock_figure, child1),
        call(mock_figure, child2),
    ]
    renderer._render_node.assert_has_calls(expected_calls, any_order=True)
