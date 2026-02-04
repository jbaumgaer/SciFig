from unittest.mock import MagicMock
import pandas as pd
import pytest

from src.models.nodes.plot_node import PlotNode


def _setup_mock_axes(node: PlotNode):
    """Helper function to set up mock axes for a PlotNode."""
    mock_axes = MagicMock()
    mock_figure = MagicMock()
    mock_trans_figure = MagicMock()

    mock_axes.figure = mock_figure
    mock_figure.transFigure = mock_trans_figure
    mock_trans_figure.inverted.return_value = MagicMock()

    def mock_transformed(transform_obj):
        mock_bbox = MagicMock()
        mock_bbox.x0 = node.geometry[0]
        mock_bbox.y0 = node.geometry[1]
        mock_bbox.x1 = node.geometry[0] + node.geometry[2]
        mock_bbox.y1 = node.geometry[1] + node.geometry[3]
        return mock_bbox

    mock_axes.get_window_extent.return_value.transformed.side_effect = mock_transformed
    node.axes = mock_axes


@pytest.fixture
def sample_plot_node():
    """Fixture for a PlotNode with default geometry and mocked axes."""
    node = PlotNode()
    _setup_mock_axes(node)
    return node


def test_plot_node_init(sample_plot_node):
    """Test the initialization of a PlotNode."""
    assert sample_plot_node.name == "Plot"
    assert sample_plot_node.geometry == (0.1, 0.1, 0.8, 0.8)
    assert sample_plot_node.plot_properties is None
    assert sample_plot_node.data is None
    assert sample_plot_node.parent is None
    assert sample_plot_node.children == []


def test_plot_node_init_with_parent():
    """Test initializing a PlotNode with a parent."""
    from src.models.nodes.scene_node import SceneNode

    parent = SceneNode()
    plot_node = PlotNode(parent=parent, name="MyPlot")
    assert plot_node.parent == parent
    assert plot_node in parent.children
    assert plot_node.name == "MyPlot"


# Test cases for the hit_test method
# Format: (position_to_test, expected_result_is_self)
hit_test_cases = [
    # Hits
    ((0.1, 0.1), True),  # Bottom-left corner
    ((0.9, 0.9), True),  # Top-right corner
    ((0.5, 0.5), True),  # Center
    ((0.1, 0.5), True),  # Left edge, center
    ((0.9, 0.5), True),  # Right edge, center
    ((0.5, 0.1), True),  # Bottom edge, center
    ((0.5, 0.9), True),  # Top edge, center
    # Misses
    ((0.0, 0.0), False),  # Outside, below and left
    ((1.0, 1.0), False),  # Outside, above and right
    ((0.09, 0.5), False),  # Just left of the boundary
    ((0.91, 0.5), False),  # Just right of the boundary
    ((0.5, 0.09), False),  # Just below the boundary
    ((0.5, 0.91), False),  # Just above the boundary
    ((-0.1, -0.1), False),  # Negative coordinates
]


@pytest.mark.parametrize("position, should_hit", hit_test_cases)
def test_hit_test(sample_plot_node, position, should_hit):
    """Test the hit_test method for various positions."""
    hit_result = sample_plot_node.hit_test(position)
    if should_hit:
        assert (
            hit_result is sample_plot_node
        ), f"Expected hit at {position}, but missed."
    else:
        assert hit_result is None, f"Expected miss at {position}, but hit."


def test_hit_test_with_custom_geometry():
    """Test hit_test with non-default geometry."""
    plot_node = PlotNode()
    plot_node.geometry = [0.25, 0.25, 0.5, 0.5]  # A centered 0.5x0.5 square
    _setup_mock_axes(plot_node) # Set up mock axes for this new plot_node

    # Hit
    assert plot_node.hit_test((0.5, 0.5)) is plot_node

    # Miss
    assert plot_node.hit_test((0.2, 0.2)) is None


def test_data_property():
    """Test assigning data to the PlotNode."""
    plot_node = PlotNode()
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    plot_node.data = df
    pd.testing.assert_frame_equal(plot_node.data, df)
