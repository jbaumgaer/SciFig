import pytest
import pandas as pd
import logging
from pathlib import Path
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


# --- Fixtures ---

@pytest.fixture
def sample_font():
    return FontProperties(
        family="Arial", style="normal", variant="normal", weight="normal", stretch="normal", size=10
    )

@pytest.fixture
def sample_text(sample_font):
    return TextProperties(text="Test", color="black", font=sample_font)

@pytest.fixture
def sample_plot_properties(sample_text):
    """Provides a complete, versioned PlotProperties tree."""
    ticks = TickProperties(5, 2, 1, 0.5, 3, 3, TickDirection.OUT, "black", "black", 10, True, 2)
    axis = AxisProperties(ticks, 0.05, AutolimitMode.DATA, True, 4, (-4, 5), sample_text, (None, None))
    return PlotProperties(
        titles={"left": sample_text, "center": sample_text, "right": sample_text},
        coords=Cartesian2DProperties(
            xaxis=axis, yaxis=axis,
            spines={"left": SpineProperties(True, "black", 1.0, SpinePosition.LEFT)},
            facecolor="white", axis_below=True, prop_cycle=["C0"]
        ),
        legend={},
        artists=[LineArtistProperties(True, 1, LineProperties(1.0, "-", "C0", "None", "C0", "black", 0.5, 5.0))],
        _version=1
    )

@pytest.fixture
def minimal_plot_dict():
    return {
        "id": "p1",
        "type": "PlotNode",
        "name": "Minimal",
        "visible": True,
        "locked": False,
        "children": [],
        "geometry": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8}
    }


class TestPlotNode:

    # --- Initialization Tests ---

    def test_initialization_defaults(self):
        """Verifies default state of PlotNode."""
        node = PlotNode()
        assert node.name == "Plot"
        assert node.geometry == (0.1, 0.1, 0.8, 0.8)
        assert node.plot_properties is None
        assert node.data is None
        assert node.data_file_path is None
        assert node.visible is True
        assert node.locked is False

    def test_initialization_with_parent(self):
        """Verifies PlotNode correctly integrates into scene hierarchy."""
        parent = SceneNode(name="Parent")
        node = PlotNode(parent=parent, name="Child")
        assert node.parent is parent
        assert node in parent.children

    # --- Hit Testing ---

    def test_hit_test_coordinates(self):
        """Tests hit testing in normalized figure coordinates."""
        node = PlotNode()
        node.geometry = (0.2, 0.2, 0.4, 0.4)
        assert node.hit_test((0.3, 0.3)) is node
        assert node.hit_test((0.1, 0.1)) is None

    # --- Serialization (to_dict) ---

    def test_to_dict_full_state(self, sample_plot_properties):
        """Tests serialization with all components populated."""
        node = PlotNode(name="FullPlot", id="test_id")
        node.geometry = (0, 0, 1, 1)
        node.plot_properties = sample_plot_properties
        node.data_file_path = Path("/abs/path/data.csv")
        node.locked = True

        d = node.to_dict()

        assert d["id"] == "test_id"
        assert d["type"] == "PlotNode"
        assert d["geometry"] == {"x": 0, "y": 0, "width": 1, "height": 1}
        assert d["plot_properties"]["_version"] == 1
        assert d["data_file_path"] == str(Path("/abs/path/data.csv"))
        assert d["locked"] is True

    def test_to_dict_sparse_state(self):
        """Tests serialization when properties are still a dictionary (template state)."""
        node = PlotNode()
        node.plot_properties = {"plot_type": "scatter"}
        d = node.to_dict()
        assert d["plot_properties"] == {"plot_type": "scatter"}

    def test_to_dict_null_components(self):
        """Ensures serialization doesn't crash with None values."""
        node = PlotNode()
        node.plot_properties = None
        node.data_file_path = None
        d = node.to_dict()
        assert d["plot_properties"] is None
        assert d["data_file_path"] is None

    def test_to_dict_exclude_geometry(self):
        """Tests the exclusion flag used for state extraction."""
        node = PlotNode()
        d = node.to_dict(exclude_geometry=True)
        assert "geometry" not in d

    # --- Deserialization (from_dict) ---

    def test_from_dict_geometry_reconstruction(self, minimal_plot_dict):
        """Tests that geometry is correctly mapped from x/y/width/height dict."""
        node = PlotNode.from_dict(minimal_plot_dict)
        assert node.geometry == (0.1, 0.1, 0.8, 0.8)

    def test_from_dict_hierarchy_and_inherited_state(self, minimal_plot_dict):
        """Tests that from_dict correctly handles parent and SceneNode attributes."""
        parent = SceneNode(name="Parent")
        data = minimal_plot_dict.copy()
        data["locked"] = True
        data["visible"] = False
        
        node = PlotNode.from_dict(data, parent=parent)
        
        assert node.parent is parent
        assert node in parent.children
        assert node.locked is True
        assert node.visible is False

    def test_from_dict_strict_vs_sparse_properties(self, minimal_plot_dict, sample_plot_properties):
        """Tests the logic that distinguishes between deferred hydration and full reconstruction."""
        # Case 1: Strict (has _version)
        strict_data = minimal_plot_dict.copy()
        strict_data["plot_properties"] = sample_plot_properties.to_dict()
        node_strict = PlotNode.from_dict(strict_data)
        assert isinstance(node_strict.plot_properties, PlotProperties)
        
        # Case 2: Sparse (no _version)
        sparse_data = minimal_plot_dict.copy()
        sparse_data["plot_properties"] = {"plot_type": "line"}
        node_sparse = PlotNode.from_dict(sparse_data)
        assert isinstance(node_sparse.plot_properties, dict)

    # --- Data Loading Logic ---

    def test_from_dict_data_loading_absolute_path(self, tmp_path, minimal_plot_dict):
        """Tests that absolute paths bypass temp_dir logic."""
        csv_file = tmp_path / "abs_data.csv"
        pd.DataFrame({"A": [1]}).to_csv(csv_file, sep=";", index=False)
        
        data = minimal_plot_dict.copy()
        data["data_file_path"] = str(csv_file)
        
        # Even if temp_dir is provided, absolute path should win
        node = PlotNode.from_dict(data, temp_dir=Path("/some/other/dir"))
        assert node.data is not None
        assert node.data_file_path == csv_file

    def test_from_dict_data_loading_relative_path(self, tmp_path, minimal_plot_dict):
        """Tests that relative paths are resolved against temp_dir."""
        temp_dir = tmp_path / "project"
        temp_dir.mkdir()
        csv_file = temp_dir / "rel_data.csv"
        pd.DataFrame({"B": [2]}).to_csv(csv_file, sep=";", index=False)
        
        data = minimal_plot_dict.copy()
        data["data_file_path"] = "rel_data.csv"
        
        node = PlotNode.from_dict(data, temp_dir=temp_dir)
        assert node.data is not None
        assert node.data["B"].iloc[0] == 2

    def test_from_dict_unsupported_extension(self, tmp_path, minimal_plot_dict, caplog):
        """Verifies that unknown extensions log a warning but don't crash."""
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("not a csv")
        
        data = minimal_plot_dict.copy()
        data["data_file_path"] = str(txt_file)
        
        with caplog.at_level(logging.WARNING):
            node = PlotNode.from_dict(data)
        
        assert node.data is None
        assert "Data not loaded" in caplog.text

    def test_from_dict_missing_file(self, minimal_plot_dict, caplog):
        """Verifies that missing files are handled gracefully."""
        data = minimal_plot_dict.copy()
        data["data_file_path"] = "non_existent.csv"
        
        with caplog.at_level(logging.WARNING):
            node = PlotNode.from_dict(data)
            
        assert node.data is None
        assert "Data file not found" in caplog.text

    # --- Edge Cases ---

    def test_from_dict_missing_geometry_raises_keyerror(self, minimal_plot_dict):
        """
        Documents the current brittle behavior: missing geometry key raises KeyError.
        This serves as a marker for future robustness improvements.
        """
        data = minimal_plot_dict.copy()
        del data["geometry"]
        with pytest.raises(KeyError):
            PlotNode.from_dict(data)
