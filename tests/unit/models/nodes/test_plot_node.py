import dataclasses
from unittest.mock import MagicMock

import matplotlib.axes
import pandas as pd
import pytest

from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode  # For type hinting
from src.models.plots.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    PlotType,
    ScatterPlotProperties,
)

# --- Fixtures ---


@pytest.fixture
def mock_axes():
    """Provides a MagicMock for matplotlib.axes.Axes."""
    mock_fig = MagicMock()
    mock_axes_obj = MagicMock(spec=matplotlib.axes.Axes)
    mock_axes_obj.figure = mock_fig
    # Mock get_window_extent and transformed for hit_test
    mock_bbox = MagicMock()
    mock_bbox.x0, mock_bbox.y0, mock_bbox.x1, mock_bbox.y1 = (
        0.1,
        0.1,
        0.9,
        0.9,
    )  # Default bbox covering most of figure
    mock_axes_obj.get_window_extent.return_value = mock_bbox
    mock_fig.transFigure.inverted.return_value = MagicMock()  # Ensure this is callable
    mock_bbox.transformed.return_value = (
        mock_bbox  # Ensure transformed bbox retains attributes
    )

    return mock_axes_obj


@pytest.fixture
def simple_plot_node():
    """Provides a basic PlotNode instance."""
    node = PlotNode(name="SimplePlot", id="simple_id")
    return node


@pytest.fixture
def plot_node_with_properties():
    """Provides a PlotNode with basic plot properties."""
    node = PlotNode(name="PropsPlot", id="props_id")
    node.plot_properties = LinePlotProperties(
        title="Test Line Plot",
        xlabel="X Data",
        plot_mapping=PlotMapping(x="col1", y=["col2"]),
        axes_limits=AxesLimits(xlim=(0, 10), ylim=(0, 100)),
    )
    return node


@pytest.fixture
def plot_node_with_data(tmp_path):
    """
    Provides a PlotNode with data saved to a temporary parquet file.
    Returns the node and the path to the data file.
    """
    node = PlotNode(name="DataPlot", id="data_id")
    df = pd.DataFrame({"time": [1, 2, 3], "value": [10, 20, 30]})

    # Create temp_dir for data saving
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    data_file_path = data_dir / f"{node.id}.parquet"
    df.to_parquet(data_file_path)

    node.data = df
    return node, data_file_path


# --- Tests for PlotNode ---


class TestPlotNode:

    def test_initialization_defaults(self, simple_plot_node):
        """Test default initialization of PlotNode."""
        node = simple_plot_node
        assert isinstance(node, PlotNode)
        assert node.name == "SimplePlot"
        assert node.id == "simple_id"
        assert node.parent is None
        assert node.children == []
        assert node.geometry == (0.1, 0.1, 0.8, 0.8)
        assert node.plot_properties is None
        assert node.data is None
        assert node.axes is None

    def test_initialization_with_parent_and_custom_geometry(self):
        """Test initialization with parent and custom geometry."""
        parent_node = SceneNode(name="parent")
        node = PlotNode(parent=parent_node, name="CustomPlot", id="custom_plot_id")
        node.geometry = (0.2, 0.2, 0.6, 0.6)
        assert node.parent is parent_node
        assert node.name == "CustomPlot"
        assert node.id == "custom_plot_id"
        assert node.geometry == (0.2, 0.2, 0.6, 0.6)

    @pytest.mark.parametrize(
        "position, expected_hit",
        [
            ((0.5, 0.5), True),  # Inside bbox
            ((0.1, 0.1), True),  # Bottom-left boundary
            ((0.9, 0.9), True),  # Top-right boundary
            ((0.05, 0.5), False),  # Outside x
            ((0.5, 0.05), False),  # Outside y
        ],
    )
    def test_hit_test_with_axes(
        self, simple_plot_node, mock_axes, position, expected_hit
    ):
        """
        Test hit_test when axes are present and position is within/outside bounds.
        The mock_axes bbox is (0.1, 0.1, 0.9, 0.9)
        """
        node = simple_plot_node
        node.axes = mock_axes

        hit_result = node.hit_test(position)
        if expected_hit:
            assert hit_result is node
        else:
            assert hit_result is None

        mock_axes.get_window_extent.assert_called_once()

    def test_hit_test_no_axes(self, simple_plot_node):
        """Test hit_test when axes are None."""
        node = simple_plot_node
        node.axes = None
        assert node.hit_test((0.5, 0.5)) is None

    def test_to_dict_no_properties_no_data(self, simple_plot_node):
        """Test serialization of a basic PlotNode without properties or data."""
        node = simple_plot_node
        node_dict = node.to_dict()

        assert node_dict["id"] == "simple_id"
        assert node_dict["type"] == "PlotNode"
        assert node_dict["name"] == "SimplePlot"
        assert node_dict["visible"] is True
        assert node_dict["geometry"] == {
            "x": 0.1,
            "y": 0.1,
            "width": 0.8,
            "height": 0.8,
        }
        assert node_dict["plot_properties"] is None
        assert node_dict["data_path"] is None
        assert node_dict["children"] == []

    def test_to_dict_with_properties_and_data(
        self, plot_node_with_properties, plot_node_with_data
    ):
        """Test serialization of PlotNode with both properties and data."""
        node_props = plot_node_with_properties
        node_data, data_file_path = plot_node_with_data

        # Combine them for a full test case
        node_data.plot_properties = node_props.plot_properties
        node_to_serialize = node_data

        node_dict = node_to_serialize.to_dict()

        assert node_dict["id"] == node_to_serialize.id
        assert node_dict["type"] == "PlotNode"
        assert node_dict["name"] == "DataPlot"
        assert node_dict["geometry"] == {
            "x": 0.1,
            "y": 0.1,
            "width": 0.8,
            "height": 0.8,
        }
        assert node_dict["plot_properties"] == dataclasses.asdict(
            node_to_serialize.plot_properties
        )
        assert node_dict["data_path"] == f"data/{node_to_serialize.id}.parquet"
        assert node_dict["children"] == []

    def test_to_dict_exclude_geometry(self, simple_plot_node):
        """Test to_dict with exclude_geometry=True."""
        node = simple_plot_node
        node_dict = node.to_dict(exclude_geometry=True)

        assert "geometry" not in node_dict
        assert node_dict["id"] == "simple_id"
        assert node_dict["plot_properties"] is None

    @pytest.mark.parametrize(
        "plot_type_str, expected_prop_class",
        [("line", LinePlotProperties), ("scatter", ScatterPlotProperties)],
    )
    def test_from_dict_with_plot_properties(
        self, tmp_path, plot_type_str, expected_prop_class
    ):
        """
        Test deserialization of PlotNode with various plot_properties,
        including type conversion and nested dataclass reconstruction.
        """
        plot_dict = {
            "id": "plot_from_dict_props",
            "type": "PlotNode",
            "name": "DeserializedPlotProps",
            "visible": True,
            "geometry": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6},
            "plot_properties": {
                "plot_type": plot_type_str,
                "title": f"Loaded {plot_type_str.capitalize()} Plot",
                "xlabel": "X-data",
                "plot_mapping": {"x": "colA", "y": ["colB", "colC"]},
                "axes_limits": {"xlim": [0.0, 100.0], "ylim": [-10.0, 10.0]},
                "marker_size": (
                    25 if plot_type_str == "scatter" else None
                ),  # Specific to scatter
            },
            "children": [],
        }

        node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)

        assert node.id == "plot_from_dict_props"
        assert node.name == "DeserializedPlotProps"
        assert node.visible is True
        assert node.geometry == (0.2, 0.2, 0.6, 0.6)

        assert isinstance(node.plot_properties, expected_prop_class)
        assert node.plot_properties.plot_type == PlotType(plot_type_str)
        assert node.plot_properties.title == f"Loaded {plot_type_str.capitalize()} Plot"
        assert node.plot_properties.xlabel == "X-data"
        assert node.plot_properties.plot_mapping.x == "colA"
        assert node.plot_properties.plot_mapping.y == ["colB", "colC"]
        assert node.plot_properties.axes_limits.xlim == (0.0, 100.0)
        assert node.plot_properties.axes_limits.ylim == (-10.0, 10.0)
        if plot_type_str == "scatter":
            assert node.plot_properties.marker_size == 25
        else:
            assert not hasattr(node.plot_properties, "marker_size")

    def test_from_dict_with_data_loading(self, tmp_path):
        """Test deserialization with data loading from a parquet file."""
        df_original = pd.DataFrame({"colA": [10, 20], "colB": [30, 40]})

        # Manually create the expected data directory structure and file
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        data_file_name = "plot_with_data_id.parquet"
        data_file_path = data_dir / data_file_name
        df_original.to_parquet(data_file_path)

        plot_dict = {
            "id": "plot_with_data_id",
            "type": "PlotNode",
            "name": "PlotWithData",
            "visible": True,
            "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            "plot_properties": None,
            "data_path": f"data/{data_file_name}",
            "children": [],
        }

        node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)
        pd.testing.assert_frame_equal(node.data, df_original)

    def test_from_dict_no_data_path(self, tmp_path):
        """Test from_dict when no data_path is present."""
        plot_dict = {
            "id": "plot_no_data_path",
            "type": "PlotNode",
            "name": "NoDataPathPlot",
            "visible": True,
            "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            "plot_properties": None,
            "children": [],
        }
        node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)
        assert node.data is None

    def test_from_dict_data_path_but_no_temp_dir(self):
        """Test from_dict when data_path is present but temp_dir is None."""
        plot_dict = {
            "id": "plot_data_path_no_temp_dir",
            "type": "PlotNode",
            "name": "DataPathNoTempDirPlot",
            "visible": True,
            "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            "plot_properties": None,
            "data_path": "data/some_file.parquet",
            "children": [],
        }
        node = PlotNode.from_dict(plot_dict, temp_dir=None)
        assert node.data is None  # Data should not be loaded

    def test_from_dict_data_path_not_found(self, tmp_path):
        """Test from_dict when data_path points to a non-existent file."""
        plot_dict = {
            "id": "plot_data_not_found",
            "type": "PlotNode",
            "name": "DataNotFoundPlot",
            "visible": True,
            "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            "plot_properties": None,
            "data_path": "data/non_existent.parquet",
            "children": [],
        }
        node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)
        assert node.data is None  # Data should not be loaded

    def test_from_dict_missing_plot_properties(self, simple_plot_node, tmp_path):
        """Test from_dict when plot_properties are missing from the dictionary."""
        plot_dict = {
            "id": simple_plot_node.id,
            "type": "PlotNode",
            "name": "PlotNoProps",
            "visible": True,
            "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            "children": [],
        }
        node = PlotNode.from_dict(plot_dict, temp_dir=tmp_path)
        assert node.plot_properties is None
